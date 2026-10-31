import os
import subprocess
from datetime import datetime

import pytest

from bigbrother.premises import check_premises, resolve_revision
from bigbrother.schema import CheckState, Extraction, Issue, Premise, Revision, RevisionSource


def issue(created_at: str) -> Issue:
    return Issue(
        url="https://github.com/daggers/tinylib/issues/1",
        repo="daggers/tinylib",
        number=1,
        title="t",
        body="b",
        created_at=created_at,
    )


def extraction(version: str | None = None) -> Extraction:
    return Extraction(central_claim="parse_url fails", claimed_version=version, has_steps=False)


def at(repo, tag: str) -> Revision:
    return Revision(sha=repo.tags[tag], source=RevisionSource.TAG, ref=tag)


def symbol(value: str) -> Premise:
    return Premise(kind="symbol", value=value, central=True)


def test_claimed_version_resolves_to_tag(tinylib_repo):
    revision = resolve_revision(tinylib_repo.path, issue("2026-03-05T12:00:00Z"), extraction("1.1.0"))
    assert revision.source == RevisionSource.TAG
    assert revision.ref == "v1.1.0"
    assert revision.sha == tinylib_repo.tags["v1.1.0"]


def test_claimed_version_with_v_prefix(tinylib_repo):
    revision = resolve_revision(tinylib_repo.path, issue("2026-03-05T12:00:00Z"), extraction("v1.0.0"))
    assert revision.sha == tinylib_repo.tags["v1.0.0"]


def test_no_version_falls_back_to_issue_date(tinylib_repo):
    revision = resolve_revision(tinylib_repo.path, issue("2026-02-01T00:00:00Z"), extraction())
    assert revision.source == RevisionSource.ISSUE_DATE
    assert revision.sha == tinylib_repo.tags["v1.0.0"]
    assert "guess" in revision.note


def test_unknown_version_falls_back_to_issue_date(tinylib_repo):
    revision = resolve_revision(tinylib_repo.path, issue("2026-03-05T12:00:00Z"), extraction("7.0.0"))
    assert revision.source == RevisionSource.ISSUE_DATE
    assert revision.sha == tinylib_repo.tags["v1.1.0"]
    assert "7.0.0" in revision.note


def test_naive_issue_date_is_treated_as_utc(tinylib_repo):
    created = Issue(
        url="https://github.com/daggers/tinylib/issues/1",
        repo="daggers/tinylib",
        number=1,
        title="t",
        body="b",
        created_at=datetime(2026, 2, 1),
    )
    revision = resolve_revision(tinylib_repo.path, created, extraction())
    assert revision.sha == tinylib_repo.tags["v1.0.0"]


def test_parse_query_absent_then_present(tinylib_repo):
    [old] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), [symbol("parse_query")])
    assert old.state == CheckState.ABSENT
    assert old.excerpt is None

    [new] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("parse_query")])
    assert new.state == CheckState.PRESENT
    assert new.excerpt.path == "tinylib/urls.py"
    assert new.excerpt.text == "def parse_query(query):"
    assert new.excerpt.line == 12


def test_dotted_name_through_init_reexport(tinylib_repo):
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), [symbol("tinylib.parse_url")])
    assert result.state == CheckState.PRESENT
    assert result.excerpt.path == "tinylib/urls.py"
    assert result.excerpt.text == "def parse_url(url):"
    assert "tinylib/__init__.py" in result.detail


def test_full_module_path_and_constant(tinylib_repo):
    results = check_premises(
        tinylib_repo.path,
        at(tinylib_repo, "v1.1.0"),
        [symbol("tinylib.urls.parse_url"), symbol("tinylib.urls.MAX_LENGTH"), symbol("tinylib.urls")],
    )
    assert [r.state for r in results] == [CheckState.PRESENT] * 3
    assert results[1].excerpt.text == "MAX_LENGTH = 255"


def test_missing_dotted_name_is_absent(tinylib_repo):
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("tinylib.parse_url_v2")])
    assert result.state == CheckState.ABSENT


def test_other_package_is_unknown(tinylib_repo):
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol("requests.get")])
    assert result.state == CheckState.UNKNOWN


def test_versions_use_tags(tinylib_repo):
    results = check_premises(
        tinylib_repo.path,
        at(tinylib_repo, "v1.1.0"),
        [Premise(kind="version", value="1.1.0", central=False), Premise(kind="version", value="2.0", central=False)],
    )
    assert [r.state for r in results] == [CheckState.PRESENT, CheckState.UNKNOWN]
    assert "v1.1.0" in results[0].detail


def test_results_keep_premise_order(tinylib_repo):
    premises = [symbol("parse_query"), Premise(kind="version", value="1.0.0", central=False), symbol("parse_url")]
    results = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), premises)
    assert [r.premise for r in results] == premises
    assert [r.state for r in results] == [CheckState.ABSENT, CheckState.PRESENT, CheckState.PRESENT]


def commit(repo, files: dict[str, str]) -> str:
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-04-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-04-01T00:00:00Z"}
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "change"], check=True, env=env)
    return subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def test_parse_failure_is_error_not_absent(tinylib_repo):
    sha = commit(tinylib_repo.path, {"tinylib/broken.py": "def oops(:\n"})
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    results = check_premises(tinylib_repo.path, revision, [symbol("missing_name"), symbol("tinylib.missing_name"), symbol("parse_url")])
    assert [r.state for r in results] == [CheckState.ERROR, CheckState.ERROR, CheckState.PRESENT]


def test_methods_aliases_and_all(tinylib_repo):
    sha = commit(
        tinylib_repo.path,
        {
            "tinylib/client.py": "class Client:\n    def get(self):\n        pass\n",
            "tinylib/__init__.py": (
                "from tinylib.urls import parse_url\n"
                "from .client import Client as HttpClient\n"
                "__all__ = ['parse_url', 'HttpClient']\n"
            ),
            "tests/test_only.py": "def only_in_tests():\n    pass\n",
        },
    )
    revision = Revision(sha=sha, source=RevisionSource.ISSUE_DATE)
    results = check_premises(
        tinylib_repo.path,
        revision,
        [symbol("Client.get"), symbol("tinylib.HttpClient"), symbol("tinylib.HttpClient.get"), symbol("only_in_tests")],
    )
    assert [r.state for r in results] == [CheckState.PRESENT, CheckState.PRESENT, CheckState.PRESENT, CheckState.ABSENT]
    assert results[2].excerpt.text == "def get(self):"


def test_checks_never_touch_working_tree(tinylib_repo):
    head = (tinylib_repo.path / "tinylib" / "urls.py").read_text()
    check_premises(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), [symbol("parse_query")])
    assert (tinylib_repo.path / "tinylib" / "urls.py").read_text() == head


def test_bad_revision_is_error(tinylib_repo):
    revision = Revision(sha="0" * 40, source=RevisionSource.TAG)
    [result] = check_premises(tinylib_repo.path, revision, [symbol("parse_url")])
    assert result.state == CheckState.ERROR


@pytest.mark.parametrize("value", ["tinylib", "tinylib.urls"])
def test_modules_are_present(tinylib_repo, value):
    [result] = check_premises(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), [symbol(value)])
    assert result.state == CheckState.PRESENT
