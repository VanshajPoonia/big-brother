"""Pick the revision the reporter most likely had, and check the report's premises there.

Files are read straight from git objects with `git ls-tree` and `git show`, so
the working tree is never checked out or changed.
"""

from __future__ import annotations

import ast
import configparser
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

from bigbrother.schema import (
    CheckState,
    Excerpt,
    Extraction,
    Issue,
    Premise,
    PremiseResult,
    Revision,
    RevisionSource,
)

# Folders whose code isn't the package, so a name found only there doesn't count.
SKIP_DIRS = {"tests", "test", "testing", "docs", "doc", "examples", "example", "benchmarks", ".github"}
SKIP_FILES = {"setup.py", "conftest.py", "noxfile.py", "tasks.py"}
PYPI = "https://pypi.org/pypi/{name}/json"
DIST_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HISTORY_TIMEOUT = 20


def _git(repo_dir: Path, *args: str, timeout: float | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        capture_output=True,
        timeout=timeout,
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


def _show(repo_dir: Path, ref: str, path: str) -> str | None:
    try:
        return _git(repo_dir, "show", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        return None


# Versions: tags and PyPI


def _norm(version: str) -> str:
    """1.2.0, v1.2 and V1.2.0 are the same release."""
    version = version.strip().lower()
    if version.startswith("v"):
        version = version[1:]
    return re.sub(r"(\.0+)+$", "", version)


def find_tag(repo_dir: Path, version: str) -> str | None:
    """Return the tag for `version`, written as 1.2.3 or v1.2.3, if the repo has one."""
    wanted = version[1:] if version[:1] in ("v", "V") else version
    tags = _git(repo_dir, "tag", "--list").splitlines()
    for candidate in (f"v{wanted}", wanted, f"V{wanted}"):
        if candidate in tags:
            return candidate
    for tag in tags:
        if _norm(tag) == _norm(version):
            return tag
    return None


@dataclass
class PyPIRelease:
    version: str
    uploaded: datetime | None


@dataclass
class PyPIInfo:
    """What PyPI said. `answered` is False when it couldn't be reached or didn't know the name."""

    name: str
    answered: bool
    releases: dict[str, PyPIRelease] = field(default_factory=dict)
    detail: str = ""

    def find(self, version: str) -> PyPIRelease | None:
        for key, release in self.releases.items():
            if _norm(key) == _norm(version):
                return release
        return None


def _new_client() -> httpx.Client:
    return httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "bigbrother"})


def fetch_pypi(name: str, client: httpx.Client | None = None) -> PyPIInfo:
    """Ask PyPI which releases `name` has and when each was uploaded."""
    if not DIST_NAME.match(name):
        return PyPIInfo(name, answered=False, detail=f"{name!r} isn't a PyPI project name")
    owned = client is None
    client = client or _new_client()
    try:
        response = client.get(PYPI.format(name=name))
    except httpx.HTTPError as exc:
        return PyPIInfo(name, answered=False, detail=f"couldn't reach PyPI: {type(exc).__name__}")
    finally:
        if owned:
            client.close()
    if response.status_code == 404:
        # Maybe it's published under another name, so this proves nothing.
        return PyPIInfo(name, answered=False, detail=f"PyPI has no project named {name}")
    if response.status_code != 200:
        return PyPIInfo(name, answered=False, detail=f"PyPI answered HTTP {response.status_code}")
    try:
        data = response.json()
        releases = {}
        for version, files in data["releases"].items():
            times = [_parse_time(f["upload_time_iso_8601"]) for f in files if f.get("upload_time_iso_8601")]
            releases[version] = PyPIRelease(version, min(times) if times else None)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return PyPIInfo(name, answered=False, detail=f"couldn't read PyPI's answer: {exc}")
    return PyPIInfo(name, answered=True, releases=releases)


def _parse_time(value: str) -> datetime:
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def project_name(repo_dir: Path, ref: str) -> str | None:
    """The PyPI name from pyproject.toml, setup.cfg or setup.py at `ref`."""
    text = _show(repo_dir, ref, "pyproject.toml")
    if text:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            data = {}
        name = data.get("project", {}).get("name") or data.get("tool", {}).get("poetry", {}).get("name")
        if isinstance(name, str):
            return name
    text = _show(repo_dir, ref, "setup.cfg")
    if text:
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(text)
            name = parser.get("metadata", "name", fallback=None)
        except configparser.Error:
            name = None
        if name:
            return name.strip()
    text = _show(repo_dir, ref, "setup.py")
    if text:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                        return keyword.value.value
    return None


# Revision


def _default_branch(repo_dir: Path) -> str:
    try:
        return _git(repo_dir, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    except subprocess.CalledProcessError:
        return "HEAD"


def _utc(when: datetime) -> str:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_revision(
    repo_dir: Path,
    issue: Issue,
    extraction: Extraction,
    client: httpx.Client | None = None,
) -> Revision:
    """Use the claimed version's tag, else its PyPI upload time, else the last commit before the issue."""
    claimed = extraction.claimed_version
    branch = _default_branch(repo_dir)
    missed = ""
    if claimed:
        tag = find_tag(repo_dir, claimed)
        if tag:
            sha = _git(repo_dir, "rev-parse", f"{tag}^{{commit}}")
            return Revision(sha=sha, source=RevisionSource.TAG, ref=tag, note=f"tag {tag} matches claimed version {claimed}")

        name = project_name(repo_dir, branch) or extraction.package
        info = fetch_pypi(name, client) if name else None
        release = info.find(claimed) if info and info.answered else None
        if release and release.uploaded:
            when = _utc(release.uploaded)
            sha = _git(repo_dir, "rev-list", "-1", f"--before={when}", branch)
            if sha:
                note = f"no tag for {claimed}; last commit on {branch} before {name} {release.version} was uploaded to PyPI ({when})"
                return Revision(sha=sha, source=RevisionSource.PYPI, ref=branch, note=note)
        if info is None:
            missed = f"; no tag matches claimed version {claimed} and no project name to look up on PyPI"
        elif release is None:
            reason = info.detail or f"PyPI has no {name} {claimed}"
            missed = f"; no tag matches claimed version {claimed}, and {reason}"
        else:
            missed = f"; no tag matches claimed version {claimed}, and PyPI has no upload time for it"

    when = _utc(issue.created_at)
    sha = _git(repo_dir, "rev-list", "-1", f"--before={when}", branch)
    note = f"guess: last commit on {branch} before the issue was opened ({when})"
    if not sha:
        sha = _git(repo_dir, "rev-list", "--max-parents=0", "-1", branch)
        note = f"guess: the issue ({when}) is older than every commit on {branch}, so using the first one"
    return Revision(sha=sha, source=RevisionSource.ISSUE_DATE, ref=branch, note=note + missed)


# Symbol index


@dataclass
class Definition:
    path: str
    line: int
    text: str


@dataclass
class Import:
    source: str  # Module the name comes from.
    original: str | None  # Name in that module, or None when the name is the module itself.
    at: Definition


@dataclass
class Module:
    name: str
    path: str
    defs: dict[str, Definition] = field(default_factory=dict)
    imports: dict[str, Import] = field(default_factory=dict)
    stars: list[Import] = field(default_factory=list)
    exported: dict[str, Definition] = field(default_factory=dict)
    error: str | None = None

    def public(self, name: str) -> bool:
        """Would `from module import *` bring `name` along?"""
        if "__all__" in self.defs:
            return name in self.exported
        return not name.startswith("_")


class Unverifiable(Exception):
    """The name leads into code outside the repo, so we can't say either way."""


class SymbolIndex:
    """Every Python module in the repo at one revision, indexed with `ast`."""

    def __init__(self, repo_dir: Path, sha: str):
        self.repo_dir = repo_dir
        self.sha = sha
        self.modules: dict[str, Module] = {}
        self.package_dirs: dict[str, str] = {}
        paths = _git(repo_dir, "ls-tree", "-r", "-z", "--name-only", sha).split("\0")
        for path in paths:
            name = _module_name(path)
            if name is None:
                continue
            self.modules[name] = self._load(name, path)
            top = name.split(".")[0]
            prefix = "src/" if path.startswith("src/") else ""
            self.package_dirs.setdefault(top, f"{prefix}{top}" if "/" in path[len(prefix):] else path)

    @property
    def packages(self) -> set[str]:
        return set(self.package_dirs)

    def _load(self, name: str, path: str) -> Module:
        module = Module(name=name, path=path)
        try:
            raw = subprocess.run(
                ["git", "-C", str(self.repo_dir), "show", f"{self.sha}:{path}"],
                check=True,
                capture_output=True,
            ).stdout
            source = raw.decode("utf-8", errors="replace")
            tree = ast.parse(source, filename=path)
        except (subprocess.CalledProcessError, SyntaxError, ValueError) as exc:
            module.error = f"couldn't parse {path}: {exc}"
            return module
        lines = source.splitlines()
        package = name if path.endswith("__init__.py") else name.rpartition(".")[0]
        _index_body(module, tree.body, "", lines, package)
        return module

    def module_for(self, dotted: str) -> tuple[Module, str] | None:
        """Split `pkg.mod.name` into the longest module prefix and the rest."""
        parts = dotted.split(".")
        for cut in range(len(parts), 0, -1):
            module = self.modules.get(".".join(parts[:cut]))
            if module is not None:
                return module, ".".join(parts[cut:])
        return None

    def lookup(self, module: Module, name: str, seen: frozenset[str] = frozenset()) -> tuple[Definition, str] | None:
        """Find `name` in `module`, following imports, aliases and star imports.

        Raises Unverifiable when the trail leaves the repo before the name is found.
        """
        if name in module.defs:
            return module.defs[name], ""
        head, _, rest = name.partition(".")
        outside = False

        if head in module.imports:
            imp = module.imports[head]
            key = f"{module.name}:{head}"
            if key not in seen:
                seen = seen | {key}
                via = f"imported in {imp.at.path}:{imp.at.line}"
                if imp.original is None:
                    # `import x` or `import x as y`: the name is the module x.
                    target = self.modules.get(imp.source)
                    if target is None:
                        if not rest:
                            return imp.at, f"imports {imp.source}"
                        raise Unverifiable(f"{head} is {imp.source}, which isn't in this repo")
                    if not rest:
                        return Definition(target.path, 1, ""), f"module {target.name}, {via}"
                    found = self._follow(target, rest, seen)
                    return (found[0], _join(via, found[1])) if found else None
                target = self.modules.get(imp.source)
                if target is not None:
                    found = self._follow(target, f"{imp.original}.{rest}" if rest else imp.original, seen)
                    if found:
                        return found[0], _join(via, found[1])
                # `from package import submodule`, then `submodule.name`.
                submodule = self.modules.get(f"{imp.source}.{imp.original}")
                if submodule is not None:
                    if not rest:
                        return imp.at, f"module {submodule.name}"
                    found = self._follow(submodule, rest, seen)
                    if found:
                        return found[0], _join(via, found[1])
                if target is None and submodule is None:
                    if not rest:
                        return imp.at, f"imported from {imp.source}"
                    outside = True

        for star in module.stars:
            key = f"{module.name}:*{star.source}"
            if key in seen:
                continue
            target = self.modules.get(star.source)
            if target is None:
                outside = True
                continue
            if target.error is None and target.public(head):
                found = self._follow(target, name, seen | {key})
                if found:
                    return found[0], _join(f"star import in {star.at.path}:{star.at.line}", found[1])

        if not rest and name in module.exported:
            return module.exported[name], "listed in __all__"
        if outside:
            raise Unverifiable(f"{name} may come from a package outside this repo")
        return None

    def _follow(self, module: Module, name: str, seen: frozenset[str]) -> tuple[Definition, str] | None:
        if module.error:
            return None
        return self.lookup(module, name, seen)


def _join(first: str, second: str) -> str:
    return f"{first}; {second}" if second else first


def _module_name(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    parts = path[:-3].split("/")
    if parts[0] == "src":
        parts = parts[1:]
    if not parts or any(part in SKIP_DIRS or part.startswith(".") for part in parts[:-1]):
        return None
    if len(parts) == 1 and f"{parts[0]}.py" in SKIP_FILES:
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or not all(part.isidentifier() for part in parts):
        return None
    return ".".join(parts)


def _definition(path: str, node: ast.AST, lines: list[str]) -> Definition:
    line = getattr(node, "lineno", 1)
    text = lines[line - 1].strip() if 0 < line <= len(lines) else ""
    return Definition(path=path, line=line, text=text[:500])


def _resolve_from(package: str, node: ast.ImportFrom) -> str:
    if not node.level:
        return node.module or ""
    base = package.split(".") if package else []
    if node.level > 1:
        base = base[: len(base) - (node.level - 1)]
    if node.module:
        base.append(node.module)
    return ".".join(base)


def _index_body(module: Module, body: list[ast.stmt], prefix: str, lines: list[str], package: str) -> None:
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            module.defs.setdefault(prefix + node.name, _definition(module.path, node, lines))
            if isinstance(node, ast.ClassDef):
                _index_body(module, node.body, f"{prefix}{node.name}.", lines, package)
        elif prefix:
            continue  # Inside a class only methods and nested classes count.
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name_node in ast.walk(target):
                    if isinstance(name_node, ast.Name):
                        module.defs.setdefault(name_node.id, _definition(module.path, node, lines))
                        if name_node.id == "__all__":
                            _index_all(module, node, lines)
        elif isinstance(node, ast.Import):
            at = _definition(module.path, node, lines)
            for alias in node.names:
                if alias.asname:
                    module.imports.setdefault(alias.asname, Import(alias.name, None, at))
                else:
                    top = alias.name.split(".")[0]
                    module.imports.setdefault(top, Import(top, None, at))
        elif isinstance(node, ast.ImportFrom):
            source = _resolve_from(package, node)
            at = _definition(module.path, node, lines)
            for alias in node.names:
                if alias.name == "*":
                    module.stars.append(Import(source, None, at))
                else:
                    module.imports.setdefault(alias.asname or alias.name, Import(source, alias.name, at))
        elif isinstance(node, (ast.If, ast.Try)):
            # Names defined under `if TYPE_CHECKING:` or `try: import ... except`.
            blocks = [node.body, node.orelse]
            if isinstance(node, ast.Try):
                blocks += [handler.body for handler in node.handlers] + [node.finalbody]
            for block in blocks:
                _index_body(module, block, prefix, lines, package)


def _index_all(module: Module, node: ast.stmt, lines: list[str]) -> None:
    value = getattr(node, "value", None)
    if isinstance(value, (ast.List, ast.Tuple)):
        for element in value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                module.exported.setdefault(element.value, _definition(module.path, node, lines))


# Premise checks


def _present(premise: Premise, found: Definition, detail: str) -> PremiseResult:
    excerpt = Excerpt(path=found.path, line=found.line, text=found.text)
    return PremiseResult(premise=premise, state=CheckState.PRESENT, excerpt=excerpt, detail=detail)


def _first_line(index: SymbolIndex, module: Module) -> str:
    text = _show(index.repo_dir, index.sha, module.path) or ""
    return (text.splitlines() or [""])[0][:500]


def _module_result(index: SymbolIndex, premise: Premise, found: Definition, detail: str) -> PremiseResult:
    if not found.text and found.line == 1:
        module = next((m for m in index.modules.values() if m.path == found.path), None)
        if module is not None:
            found = Definition(found.path, 1, _first_line(index, module))
    return _present(premise, found, detail)


def _check_symbol(index: SymbolIndex, premise: Premise) -> PremiseResult:
    value = premise.value
    head = value.split(".")[0]
    try:
        split = index.module_for(value) if head in index.packages else None
        if split:
            module, rest = split
            if module.error:
                return PremiseResult(premise=premise, state=CheckState.ERROR, detail=module.error)
            if not rest:
                return _module_result(index, premise, Definition(module.path, 1, ""), f"module {module.name}")
            found = index.lookup(module, rest)
            if found:
                return _module_result(index, premise, found[0], found[1])
            broken = [m.error for name, m in index.modules.items() if m.error and name.split(".")[0] == head]
            if broken:
                return PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"not found, but {broken[0]}")
            return PremiseResult(premise=premise, state=CheckState.ABSENT, detail=f"{rest} isn't defined in {module.name} ({module.path})")

        # A bare name, or Class.method: look in every module, real definitions first.
        if not index.modules:
            return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail="no Python package found in the repo")
        matches = [(m, m.defs[value]) for m in index.modules.values() if value in m.defs]
        if matches:
            module, found = min(matches, key=lambda pair: pair[0].path)
            return _present(premise, found, f"defined in {module.name}")
        outside = None
        for module in sorted(index.modules.values(), key=lambda m: m.path):
            if module.error:
                continue
            try:
                found = index.lookup(module, value)
            except Unverifiable as exc:
                outside = outside or str(exc)
                continue
            if found:
                return _module_result(index, premise, found[0], found[1])
    except Unverifiable as exc:
        return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail=str(exc))

    if "." in value:
        # Probably someone else's package, like requests.get. We can't say it's missing.
        return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail=f"package {head} isn't in this repo")
    broken = [m.error for m in index.modules.values() if m.error]
    if broken:
        return PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"not found, but {broken[0]}")
    if outside:
        return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail=outside)
    packages = ", ".join(sorted(index.packages))
    return PremiseResult(premise=premise, state=CheckState.ABSENT, detail=f"not defined anywhere in {packages}")


def _removed_in(index: SymbolIndex, premise: Premise) -> str | None:
    """If an absent symbol used to be defined, return the commit that removed it."""
    value = premise.value
    head = value.split(".")[0]
    dirs = [index.package_dirs[head]] if head in index.package_dirs else sorted(index.package_dirs.values())
    if not dirs:
        return None
    needle = value.rsplit(".", 1)[-1]
    log = _git(
        index.repo_dir, "log", f"-S{needle}", "--format=%H", index.sha, "--", *dirs, timeout=HISTORY_TIMEOUT
    ).split()
    if not log:
        return None
    newest = log[0]
    try:
        parent = _git(index.repo_dir, "rev-parse", f"{newest}^")
    except subprocess.CalledProcessError:
        return None  # The first commit added it, so nothing removed it.
    before = _check_symbol(SymbolIndex(index.repo_dir, parent), premise)
    return newest[:12] if before.state == CheckState.PRESENT else None


def _check_version(repo_dir: Path, revision: Revision, premise: Premise, pypi: _PyPICache) -> PremiseResult:
    found = []
    tag = find_tag(repo_dir, premise.value)
    if tag:
        sha = _git(repo_dir, "rev-parse", "--short", f"{tag}^{{commit}}")
        found.append(f"git tag {tag} at {sha}")
    info = pypi.get()
    release = info.find(premise.value) if info and info.answered else None
    if release:
        when = f", uploaded {_utc(release.uploaded)}" if release.uploaded else ""
        found.append(f"PyPI {info.name} {release.version}{when} (https://pypi.org/project/{info.name}/{release.version}/)")
    if found:
        return PremiseResult(premise=premise, state=CheckState.PRESENT, detail="; ".join(found))
    if info and info.answered:
        return PremiseResult(
            premise=premise,
            state=CheckState.ABSENT,
            detail=f"no git tag matches {premise.value}, and PyPI lists {len(info.releases)} releases of {info.name} without it",
        )
    reason = info.detail if info else "no project name in pyproject.toml, setup.cfg or setup.py"
    return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail=f"no git tag matches {premise.value}; {reason}")


class _PyPICache:
    """Ask PyPI at most once per check, and only if a version premise needs it."""

    def __init__(self, repo_dir: Path, revision: Revision, package: str | None, client: httpx.Client | None):
        self.repo_dir, self.revision, self.package, self.client = repo_dir, revision, package, client
        self.done = False
        self.info: PyPIInfo | None = None

    def get(self) -> PyPIInfo | None:
        if not self.done:
            self.done = True
            name = project_name(self.repo_dir, self.revision.sha) or self.package
            self.info = fetch_pypi(name, self.client) if name else None
        return self.info


def check_premises(
    repo_dir: Path,
    revision: Revision,
    premises: list[Premise],
    package: str | None = None,
    client: httpx.Client | None = None,
) -> list[PremiseResult]:
    """Return one result per premise, in the same order. Say `unknown` rather than `absent` when unsure.

    `package` is only used to look up PyPI when the repo doesn't name its project.
    """
    index: SymbolIndex | None = None
    index_error: str | None = None
    pypi = _PyPICache(repo_dir, revision, package, client)
    results = []
    for premise in premises:
        try:
            if premise.kind == "version":
                results.append(_check_version(repo_dir, revision, premise, pypi))
                continue
            if index is None and index_error is None:
                try:
                    index = SymbolIndex(repo_dir, revision.sha)
                except subprocess.CalledProcessError as exc:
                    index_error = f"couldn't read {revision.sha}: {exc.stderr.decode(errors='replace').strip()}"
            if index_error:
                results.append(PremiseResult(premise=premise, state=CheckState.ERROR, detail=index_error))
                continue
            result = _check_symbol(index, premise)
            if result.state == CheckState.ABSENT and premise.central:
                try:
                    sha = _removed_in(index, premise)
                except subprocess.TimeoutExpired:
                    sha = None
                    result.detail += f"; history check gave up after {HISTORY_TIMEOUT}s"
                except subprocess.CalledProcessError:
                    sha = None
                if sha:
                    result.detail = f"removed in {sha}"
            results.append(result)
        except Exception as exc:  # One bad premise shouldn't sink the others.
            results.append(PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"{type(exc).__name__}: {exc}"))
    return results
