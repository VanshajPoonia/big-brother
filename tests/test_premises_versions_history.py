import os
import subprocess
from pathlib import Path

import httpx
import pytest

from bigbrother import premises as premises_module
from bigbrother.premises import check_premises, fetch_pypi, resolve_revision
from bigbrother.schema import CheckState, Extraction, Issue, Premise, Revision, RevisionSource

PYPI_TINYLIB = {
    "info": {"name": "tinylib"},
    "releases": {
        "1.0.0": [{"upload_time_iso_8601": "2026-01-10T12:00:00.000000Z"}],
        "1.1.0": [{"upload_time_iso_8601": "2026-03-01T12:00:00.000000Z"}],
        # Released on PyPI but never tagged.
        "1.2.0": [
            {"upload_time_iso_8601": "2026-03-20T09:00:00.123456Z"},
            {"upload_time_iso_8601": "2026-03-20T08:00:00.000000Z"},
        ],
    },
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any PyPI call a test didn't mock fails like an unreachable network."""

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("tests never touch the network", request=request)

    monkeypatch.setattr(premises_module, "_new_client", lambda: httpx.Client(transport=httpx.MockTransport(offline)))


def pypi(seen: list[httpx.Request], status: int = 200, payload: dict | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=payload if payload is not None else PYPI_TINYLIB)

    return httpx.Client(transport=httpx.MockTransport(handler))


def issue(created_at: str) -> Issue:
    return Issue(
        url="https://github.com/daggers/tinylib/issues/1",
        repo="daggers/tinylib",
        number=1,
        title="t",
        body="b",
        created_at=created_at,
    )


def at(repo, tag: str) -> Revision:
    return Revision(sha=repo.tags[tag], source=RevisionSource.TAG, ref=tag)


def version(value: str) -> Premise:
    return Premise(kind="version", value=value, central=False)


def symbol(value: str, central: bool = True) -> Premise:
    return Premise(kind="symbol", value=value, central=central)


def commit(repo: Path, files: dict[str, str | None], date: str = "2026-04-01T00:00:00Z") -> str:
    for name, text in files.items():
        path = repo / name
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "change"], check=True, env=env)
    return subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


# Versions


def test_version_on_pypi_only_is_present(tinylib_repo):
    seen: list[httpx.Request] = []
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("1.2.0")], client=pypi(seen))
    assert result.state == CheckState.PRESENT
    assert "PyPI tinylib 1.2.0" in result.detail
    assert "2026-03-20T08:00:00Z" in result.detail
    assert "git tag" not in result.detail
    assert [str(r.url) for r in seen] == ["https://pypi.org/pypi/tinylib/json"]


def test_version_on_tag_and_pypi_names_both(tinylib_repo):
    seen: list[httpx.Request] = []
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("v1.1")], client=pypi(seen))
    assert result.state == CheckState.PRESENT
    assert "git tag v1.1.0" in result.detail
    assert "PyPI tinylib 1.1.0" in result.detail


def test_version_missing_everywhere_is_absent(tinylib_repo):
    seen: list[httpx.Request] = []
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("3.0")], client=pypi(seen))
    assert result.state == CheckState.ABSENT
    assert "3 releases" in result.detail


def test_version_is_unknown_when_pypi_unreachable(tinylib_repo):
    [missing, tagged] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("3.0"), version("1.0.0")])
    assert missing.state == CheckState.UNKNOWN
    assert "couldn't reach PyPI" in missing.detail
    assert tagged.state == CheckState.PRESENT


@pytest.mark.parametrize("status", [404, 503])
def test_version_is_unknown_when_pypi_says_no_or_fails(tinylib_repo, status):
    seen: list[httpx.Request] = []
    [result] = check_premises(
        tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("3.0")], client=pypi(seen, status=status, payload={})
    )
    assert result.state == CheckState.UNKNOWN


def test_pypi_asked_once_and_only_for_versions(tinylib_repo):
    seen: list[httpx.Request] = []
    client = pypi(seen)
    check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("parse_url")], client=client)
    assert seen == []
    check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [version("1.2.0"), version("3.0")], client=client)
    assert len(seen) == 1


def test_pypi_name_comes_from_setup_cfg_or_package(tinylib_repo):
    sha = commit(
        tinylib_repo.path,
        {"pyproject.toml": None, "setup.cfg": "[metadata]\nname = tiny-lib\n"},
    )
    seen: list[httpx.Request] = []
    check_premises(tinylib_repo.path, Revision(sha=sha, source=RevisionSource.ISSUE_DATE), [version("1.2.0")], client=pypi(seen))
    assert str(seen[0].url) == "https://pypi.org/pypi/tiny-lib/json"

    sha = commit(tinylib_repo.path, {"setup.cfg": None})
    seen.clear()
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    check_premises(tinylib_repo.path, revision, [version("1.2.0")], package="tinylib", client=pypi(seen))
    assert str(seen[0].url) == "https://pypi.org/pypi/tinylib/json"


def test_fetch_pypi_rejects_odd_names():
    seen: list[httpx.Request] = []
    info = fetch_pypi("../evil", pypi(seen))
    assert not info.answered
    assert seen == []


# Revision from PyPI


def test_untagged_pypi_version_uses_upload_time(tinylib_repo):
    seen: list[httpx.Request] = []
    extraction = Extraction(central_claim="c", claimed_version="1.2.0", has_steps=False)
    # The issue date alone would pick v1.0.0, so a match on v1.1.0 shows PyPI was used.
    revision = resolve_revision(tinylib_repo.path, issue("2026-02-01T00:00:00Z"), extraction, client=pypi(seen))
    assert revision.source == RevisionSource.PYPI
    assert revision.sha == tinylib_repo.tags["v1.1.0"]
    assert "2026-03-20T08:00:00Z" in revision.note


def test_tag_wins_without_asking_pypi(tinylib_repo):
    seen: list[httpx.Request] = []
    extraction = Extraction(central_claim="c", claimed_version="1.0.0", has_steps=False)
    revision = resolve_revision(tinylib_repo.path, issue("2026-03-05T00:00:00Z"), extraction, client=pypi(seen))
    assert revision.source == RevisionSource.TAG
    assert seen == []


def test_version_missing_from_pypi_falls_back_to_issue_date(tinylib_repo):
    seen: list[httpx.Request] = []
    extraction = Extraction(central_claim="c", claimed_version="9.9.9", has_steps=False)
    revision = resolve_revision(tinylib_repo.path, issue("2026-02-01T00:00:00Z"), extraction, client=pypi(seen))
    assert revision.source == RevisionSource.ISSUE_DATE
    assert revision.sha == tinylib_repo.tags["v1.0.0"]
    assert "9.9.9" in revision.note


# Aliases and star imports

ALIASES = {
    "tinylib/helpers.py": (
        "__all__ = ['slugify']\n\n\ndef slugify(text):\n    return text\n\n\ndef hidden():\n    pass\n"
    ),
    "tinylib/compat.py": (
        "from .helpers import *\n"
        "from .urls import parse_url as urlparse\n"
        "import tinylib.urls as u\n"
        "import json as _json\n"
    ),
}


def test_aliases_and_star_imports(tinylib_repo):
    sha = commit(tinylib_repo.path, ALIASES)
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    results = check_premises(
        tinylib_repo.path,
        revision,
        [
            symbol("tinylib.compat.slugify"),
            symbol("tinylib.compat.urlparse"),
            symbol("tinylib.compat.u.parse_query"),
            symbol("tinylib.compat.hidden"),
            symbol("tinylib.compat._json.loads"),
        ],
    )
    states = [r.state for r in results]
    assert states == [CheckState.PRESENT, CheckState.PRESENT, CheckState.PRESENT, CheckState.ABSENT, CheckState.UNKNOWN]
    assert results[0].excerpt.path == "tinylib/helpers.py"
    assert results[0].excerpt.text == "def slugify(text):"
    assert "star import in tinylib/compat.py:1" in results[0].detail
    assert results[1].excerpt.text == "def parse_url(url):"
    assert results[2].excerpt.text == "def parse_query(query):"


def test_star_import_without_all_skips_private_names(tinylib_repo):
    sha = commit(
        tinylib_repo.path,
        {
            "tinylib/helpers.py": "def shout(text):\n    return text.upper()\n\n\ndef _quiet():\n    pass\n",
            "tinylib/compat.py": "from tinylib.helpers import *\n",
        },
    )
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    results = check_premises(tinylib_repo.path, revision, [symbol("tinylib.compat.shout"), symbol("tinylib.compat._quiet", central=False)])
    assert [r.state for r in results] == [CheckState.PRESENT, CheckState.ABSENT]


# History


URLS_WITHOUT_PARSE_QUERY = '''MAX_LENGTH = 255


def parse_url(url):
    if len(url) > MAX_LENGTH:
        raise ValueError("URL too long")
    scheme, _, rest = url.partition("://")
    host, _, path = rest.partition("/")
    return {"scheme": scheme, "host": host, "path": "/" + path}
'''


def remove_parse_query(repo) -> str:
    return commit(
        repo.path,
        {
            "tinylib/urls.py": URLS_WITHOUT_PARSE_QUERY,
            "tinylib/__init__.py": 'from tinylib.urls import parse_url\n\n__all__ = ["parse_url"]\n',
        },
    )


def test_removed_central_symbol_names_the_commit(tinylib_repo):
    sha = remove_parse_query(tinylib_repo)
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    results = check_premises(tinylib_repo.path, revision, [symbol("parse_query"), symbol("tinylib.parse_query")])
    assert [r.state for r in results] == [CheckState.ABSENT, CheckState.ABSENT]
    assert [r.detail for r in results] == [f"removed in {sha[:12]}"] * 2


def test_history_only_for_central_symbols(tinylib_repo, monkeypatch):
    sha = remove_parse_query(tinylib_repo)
    calls = []
    original = premises_module._removed_in
    monkeypatch.setattr(premises_module, "_removed_in", lambda *args: calls.append(args) or original(*args))
    [result] = check_premises(
        tinylib_repo.path, Revision(sha=sha, source=RevisionSource.ISSUE_DATE), [symbol("parse_query", central=False)]
    )
    assert result.state == CheckState.ABSENT
    assert "removed" not in result.detail
    assert calls == []


def test_never_existed_has_no_removal(tinylib_repo):
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("tinylib.parse_url_v2")])
    assert result.state == CheckState.ABSENT
    assert "removed" not in result.detail


def test_history_not_yet_added_is_not_a_removal(tinylib_repo):
    # parse_query is absent at v1.0.0 because it hadn't been written yet.
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), [symbol("parse_query")])
    assert result.state == CheckState.ABSENT
    assert "removed" not in result.detail


def test_history_timeout_keeps_absent(tinylib_repo, monkeypatch):
    def slow(*args):
        raise subprocess.TimeoutExpired(cmd="git log", timeout=20)

    monkeypatch.setattr(premises_module, "_removed_in", slow)
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("tinylib.parse_url_v2")])
    assert result.state == CheckState.ABSENT
    assert "gave up after 20s" in result.detail
