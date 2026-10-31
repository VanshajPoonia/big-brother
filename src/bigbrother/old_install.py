"""Spot a report about a missing function that the package already shipped: an old install.

"Console has no attribute save_svg" is a bug report only if Console really lacks save_svg. If the
code the reporter should have had defines it, and git history shows a release with it came out
before the report, the reporter is on an older install. Every step is checked in the repo itself:
the report names the owner, the owner defines the name, and the release dates line up.
"""

from __future__ import annotations

import ast
import re
import subprocess
from datetime import datetime
from pathlib import Path

from bigbrother.schema import OldInstall, Revision

QUOTED = re.compile(
    r"(?:'(?P<obj>\w+)' object|type object '(?P<cls>\w+)'|module '(?P<mod>[\w.]+)') has no attribute '(?P<name>\w+)'"
    r"|cannot import name '(?P<imported>\w+)' from '(?P<frm>[\w.]+)'"
)
# A title like "Console has No attribute save_svg": a CapWords owner, then the name.
BARE = re.compile(r"\b(?P<owner>[A-Z][A-Za-z0-9_]*) [Hh]as [Nn]o [Aa]ttribute [`']?(?P<name>\w+)")
RELEASE = re.compile(r"^v?(\d+(?:\.\d+)*)$")
TIMEOUT = 20


def _git(repo_dir: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo_dir), *args], check=True, capture_output=True, text=True,
                          timeout=TIMEOUT).stdout


def claims(text: str) -> list[tuple[str, str, str]]:
    """(kind, owner, name) for every "X has no Y" in the report. kind is class, module or either."""
    found = []
    for line in text.splitlines():
        if "partially initialized" in line:
            continue  # a circular import, often a shadowing file: not about versions
        for m in QUOTED.finditer(line):
            if m["imported"]:
                found.append(("module", m["frm"], m["imported"]))
            elif m["mod"]:
                found.append(("module", m["mod"], m["name"]))
            else:
                found.append(("class", m["obj"] or m["cls"], m["name"]))
        for m in BARE.finditer(line):
            found.append(("either", m["owner"], m["name"]))
    return list(dict.fromkeys(found))


def _package_dir(repo_dir: Path, sha: str, package: str) -> str | None:
    for prefix in ("", "src/"):
        try:
            _git(repo_dir, "cat-file", "-e", f"{sha}:{prefix}{package}/__init__.py")
            return f"{prefix}{package}"
        except subprocess.CalledProcessError:
            continue
    return None


def _defines(body: list[ast.stmt], name: str) -> ast.stmt | None:
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return node
    return None


def _find_in_class(repo_dir: Path, sha: str, pkg_dir: str, owner: str, name: str) -> tuple[str, ast.stmt] | None:
    try:
        # git grep -E is POSIX regex: no \s or \b.
        pattern = rf"^[[:space:]]*class {owner}([^A-Za-z0-9_]|$)"
        hits = _git(repo_dir, "grep", "-l", "-E", pattern, sha, "--", pkg_dir).splitlines()
    except subprocess.CalledProcessError:
        return None  # git grep exits 1 when nothing matches
    for hit in hits:
        path = hit.split(":", 1)[1]
        tree = ast.parse(_git(repo_dir, "show", f"{sha}:{path}"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == owner and (found := _defines(node.body, name)):
                return path, found
    return None


def _find_in_module(repo_dir: Path, sha: str, pkg_dir: str, package: str, module: str, name: str, follow: int = 1):
    if module.split(".")[0] != package:
        return None
    base = pkg_dir.rsplit(package, 1)[0] + module.replace(".", "/")
    for path in (f"{base}.py", f"{base}/__init__.py"):
        try:
            tree = ast.parse(_git(repo_dir, "show", f"{sha}:{path}"))
        except subprocess.CalledProcessError:
            continue
        if found := _defines(tree.body, name):
            return path, found
        # `from .urls import parse_query` in __init__.py: look where it really lives, one step.
        for node in tree.body:
            if follow and isinstance(node, ast.ImportFrom) and any(a.name == name and a.asname is None for a in node.names):
                here = module if path.endswith("__init__.py") else module.rpartition(".")[0]
                parts = here.split(".")
                source = ".".join(parts[: len(parts) - node.level + 1] + ([node.module] if node.module else [])) if node.level else node.module
                if source and (found := _find_in_module(repo_dir, sha, pkg_dir, package, source, name, follow - 1)):
                    return found
    return None


def _version(text: str) -> tuple[int, ...] | None:
    m = RELEASE.match(text.strip())
    return tuple(int(part) for part in m[1].split(".")) if m else None


def _first_release(repo_dir: Path, sha: str, path: str, needle: str) -> tuple[str, datetime] | None:
    """The earliest release tag containing the commit that added `needle` to `path`."""
    added = _git(repo_dir, "log", "--reverse", "--format=%H", f"-S{needle}", sha, "--", path).split()
    if not added:
        return None
    tags = [t for t in _git(repo_dir, "tag", "--contains", added[0], "--sort=creatordate").split() if _version(t)]
    if not tags:
        return None
    released = datetime.fromisoformat(_git(repo_dir, "log", "-1", "--format=%cI", tags[0]).strip())
    return tags[0], released


def find_old_install(
    text: str,
    repo_dir: Path,
    revision: Revision,
    package: str | None,
    claimed_version: str | None,
    reported_at: datetime,
) -> OldInstall | None:
    """The report's "missing" name, defined in the code the reporter should have had and released
    before the report, if every one of those holds."""
    if not package:
        return None
    pkg_dir = _package_dir(repo_dir, revision.sha, package.split(".")[0])
    if pkg_dir is None:
        return None
    for kind, owner, name in claims(text):
        found = None
        if kind in ("class", "either"):
            found = _find_in_class(repo_dir, revision.sha, pkg_dir, owner, name)
        if found is None and kind in ("module", "either"):
            module = owner if "." in owner or owner == package else f"{package}.{owner}"
            found = _find_in_module(repo_dir, revision.sha, pkg_dir, package, module, name)
        if found is None:
            continue
        path, node = found
        keyword = "class" if isinstance(node, ast.ClassDef) else "def"
        release = _first_release(repo_dir, revision.sha, path, f"{keyword} {name}")
        if release is None:
            continue
        tag, released = release
        if released >= reported_at:
            continue  # it shipped after the report, so the reporter couldn't have had it
        claimed, first = _version(claimed_version or ""), _version(tag)
        if claimed is not None and first is not None and claimed >= first:
            continue  # their version already has it, so this isn't an old install
        line = _git(repo_dir, "show", f"{revision.sha}:{path}").splitlines()[node.lineno - 1].strip()
        return OldInstall(owner=owner, name=name, path=path, line=node.lineno, text=line[:200],
                          added_in=tag, released=released)
    return None
