"""Shared fixtures. Owned by Lane A: ask before changing them."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from bigbrother.schema import Issue

FIXTURES = Path(__file__).parent / "fixtures"

PYPROJECT = """[project]
name = "tinylib"
version = "{version}"
requires-python = ">=3.9"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
"""

URLS_V1 = '''def parse_url(url):
    scheme, _, rest = url.partition("://")
    host, _, path = rest.partition("/")
    return {"scheme": scheme, "host": host, "path": "/" + path}
'''

# 1.1.0 adds parse_query and a real bug: long URLs raise ValueError.
URLS_V2 = '''MAX_LENGTH = 255


def parse_url(url):
    if len(url) > MAX_LENGTH:
        raise ValueError("URL too long")
    scheme, _, rest = url.partition("://")
    host, _, path = rest.partition("/")
    return {"scheme": scheme, "host": host, "path": "/" + path}


def parse_query(query):
    return dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
'''

RELEASES = [
    ("1.0.0", 'from tinylib.urls import parse_url\n\n__all__ = ["parse_url"]\n', URLS_V1, "2026-01-10T10:00:00Z"),
    (
        "1.1.0",
        'from tinylib.urls import parse_query, parse_url\n\n__all__ = ["parse_query", "parse_url"]\n',
        URLS_V2,
        "2026-03-01T10:00:00Z",
    ),
]


@dataclass
class FixtureRepo:
    path: Path
    tags: dict[str, str]


def _git(repo: Path, *args: str, date: str | None = None) -> str:
    env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date} if date else None
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.com", *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def build_tinylib(root: Path) -> FixtureRepo:
    """A tiny installable git repo with two tagged releases."""
    repo = root / "tinylib"
    (repo / "tinylib").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    tags = {}
    for version, init, urls, date in RELEASES:
        (repo / "pyproject.toml").write_text(PYPROJECT.format(version=version))
        (repo / "tinylib" / "__init__.py").write_text(init)
        (repo / "tinylib" / "urls.py").write_text(urls)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", f"Release {version}", date=date)
        _git(repo, "tag", f"v{version}")
        tags[f"v{version}"] = _git(repo, "rev-parse", "HEAD")
    return FixtureRepo(repo, tags)


@pytest.fixture
def tinylib_repo(tmp_path: Path) -> FixtureRepo:
    return build_tinylib(tmp_path)


@pytest.fixture
def load_issue():
    def load(name: str) -> Issue:
        return Issue.model_validate_json((FIXTURES / "issues" / f"{name}.json").read_text())

    return load
