"""Pick the revision the reporter most likely had, and check the report's premises there.

Files are read straight from git objects with `git ls-tree` and `git show`, so
the working tree is never checked out or changed.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from datetime import timezone
from pathlib import Path

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


def _git(repo_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


# Revision


def _strip_v(version: str) -> str:
    return version[1:] if version[:1] in ("v", "V") else version


def find_tag(repo_dir: Path, version: str) -> str | None:
    """Return the tag for `version`, written as 1.2.3 or v1.2.3, if the repo has one."""
    wanted = _strip_v(version)
    tags = _git(repo_dir, "tag", "--list").splitlines()
    for candidate in (f"v{wanted}", wanted, f"V{wanted}"):
        if candidate in tags:
            return candidate
    return None


def _default_branch(repo_dir: Path) -> str:
    try:
        return _git(repo_dir, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    except subprocess.CalledProcessError:
        return "HEAD"


def resolve_revision(repo_dir: Path, issue: Issue, extraction: Extraction) -> Revision:
    """Use the claimed version's tag if there is one, otherwise the last commit before the issue."""
    claimed = extraction.claimed_version
    if claimed:
        tag = find_tag(repo_dir, claimed)
        if tag:
            sha = _git(repo_dir, "rev-parse", f"{tag}^{{commit}}")
            return Revision(sha=sha, source=RevisionSource.TAG, ref=tag, note=f"tag {tag} matches claimed version {claimed}")

    branch = _default_branch(repo_dir)
    created = issue.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    when = created.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = _git(repo_dir, "rev-list", "-1", f"--before={when}", branch)
    note = f"guess: last commit on {branch} before the issue was opened ({when})"
    if not sha:
        sha = _git(repo_dir, "rev-list", "--max-parents=0", "-1", branch)
        note = f"guess: the issue ({when}) is older than every commit on {branch}, so using the first one"
    if claimed:
        note += f"; no tag matches claimed version {claimed}"
    return Revision(sha=sha, source=RevisionSource.ISSUE_DATE, ref=branch, note=note)


# Symbol index


@dataclass
class Definition:
    path: str
    line: int
    text: str


@dataclass
class Module:
    name: str
    path: str
    defs: dict[str, Definition] = field(default_factory=dict)
    # Local name -> (module it came from, name there), for `from x import y`.
    imports: dict[str, tuple[str, str, Definition]] = field(default_factory=dict)
    exported: dict[str, Definition] = field(default_factory=dict)
    error: str | None = None


class SymbolIndex:
    """Every Python module in the repo at one revision, indexed with `ast`."""

    def __init__(self, repo_dir: Path, sha: str):
        self.repo_dir = repo_dir
        self.sha = sha
        self.modules: dict[str, Module] = {}
        self.packages: set[str] = set()
        paths = _git(repo_dir, "ls-tree", "-r", "-z", "--name-only", sha).split("\0")
        for path in paths:
            name = _module_name(path)
            if name is None:
                continue
            self.modules[name] = self._load(name, path)
            self.packages.add(name.split(".")[0])

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
        """Find `name` in `module`, following `from x import y` re-exports."""
        if name in module.defs:
            return module.defs[name], ""
        head, _, rest = name.partition(".")
        if head in module.imports:
            source, original, line = module.imports[head]
            key = f"{source}:{original}"
            if key not in seen:
                target = self.modules.get(source)
                if target is not None and target.error is None:
                    found = self.lookup(target, f"{original}.{rest}" if rest else original, seen | {key})
                    if found:
                        via = f"re-exported in {line.path}:{line.line}"
                        return found[0], f"{via}; {found[1]}" if found[1] else via
                # `from x import submodule`, then `submodule.name`.
                submodule = self.modules.get(f"{source}.{original}")
                if submodule is not None and rest and submodule.error is None:
                    found = self.lookup(submodule, rest, seen | {key})
                    if found:
                        return found
            if not rest:
                # Imported from outside the repo: the name is still importable here.
                return line, f"imported from {source}"
        if name in module.exported:
            return module.exported[name], "listed in __all__"
        return None


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
        elif isinstance(node, ast.ImportFrom):
            source = _resolve_from(package, node)
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                module.imports.setdefault(local, (source, alias.name, _definition(module.path, node, lines)))
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


def _check_symbol(index: SymbolIndex, premise: Premise) -> PremiseResult:
    value = premise.value
    head = value.split(".")[0]

    split = index.module_for(value) if head in index.packages and "." in value else None
    if split:
        module, rest = split
        if module.error:
            return PremiseResult(premise=premise, state=CheckState.ERROR, detail=module.error)
        if not rest:
            return _present(premise, Definition(module.path, 1, _first_line(index, module)), f"module {module.name}")
        found = index.lookup(module, rest)
        if found:
            return _present(premise, found[0], found[1])
        broken = [m.error for name, m in index.modules.items() if m.error and name.split(".")[0] == head]
        if broken:
            return PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"not found, but {broken[0]}")
        return PremiseResult(premise=premise, state=CheckState.ABSENT, detail=f"{rest} isn't defined in {module.name} ({module.path})")

    if head in index.packages and head in index.modules and "." not in value:
        module = index.modules[head]
        return _present(premise, Definition(module.path, 1, _first_line(index, module)), f"module {module.name}")

    # A bare name, or Class.method: look in every module, real definitions first.
    if not index.modules:
        return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail="no Python package found in the repo")
    matches = [(m, m.defs[value]) for m in index.modules.values() if value in m.defs]
    if matches:
        module, found = min(matches, key=lambda pair: pair[0].path)
        return _present(premise, found, f"defined in {module.name}")
    for module in sorted(index.modules.values(), key=lambda m: m.path):
        found = index.lookup(module, value)
        if found:
            return _present(premise, found[0], found[1])

    if "." in value:
        # Probably someone else's package, like requests.get. We can't say it's missing.
        return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail=f"package {head} isn't in this repo")
    broken = [m.error for m in index.modules.values() if m.error]
    if broken:
        return PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"not found, but {broken[0]}")
    packages = ", ".join(sorted(index.packages))
    return PremiseResult(premise=premise, state=CheckState.ABSENT, detail=f"not defined anywhere in {packages}")


def _first_line(index: SymbolIndex, module: Module) -> str:
    try:
        text = _git(index.repo_dir, "show", f"{index.sha}:{module.path}")
    except subprocess.CalledProcessError:
        return ""
    return (text.splitlines() or [""])[0][:500]


def _check_version(repo_dir: Path, premise: Premise) -> PremiseResult:
    tag = find_tag(repo_dir, premise.value)
    if tag:
        sha = _git(repo_dir, "rev-parse", "--short", f"{tag}^{{commit}}")
        return PremiseResult(premise=premise, state=CheckState.PRESENT, detail=f"tag {tag} at {sha}")
    return PremiseResult(premise=premise, state=CheckState.UNKNOWN, detail="no matching tag; PyPI not checked yet")


def check_premises(repo_dir: Path, revision: Revision, premises: list[Premise]) -> list[PremiseResult]:
    """Return one result per premise, in the same order. Say `unknown` rather than `absent` when unsure."""
    index: SymbolIndex | None = None
    index_error: str | None = None
    results = []
    for premise in premises:
        try:
            if premise.kind == "version":
                results.append(_check_version(repo_dir, premise))
                continue
            if index is None and index_error is None:
                try:
                    index = SymbolIndex(repo_dir, revision.sha)
                except subprocess.CalledProcessError as exc:
                    index_error = f"couldn't read {revision.sha}: {exc.stderr.decode(errors='replace').strip()}"
            if index_error:
                results.append(PremiseResult(premise=premise, state=CheckState.ERROR, detail=index_error))
            else:
                results.append(_check_symbol(index, premise))
        except Exception as exc:  # One bad premise shouldn't sink the others.
            results.append(PremiseResult(premise=premise, state=CheckState.ERROR, detail=f"{type(exc).__name__}: {exc}"))
    return results
