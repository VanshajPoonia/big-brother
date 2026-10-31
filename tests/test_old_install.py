import os
import subprocess
from datetime import datetime, timezone

import pytest

from bigbrother.old_install import claims, find_old_install
from bigbrother.schema import Revision, RevisionSource

AFTER_1_1 = datetime(2026, 3, 10, tzinfo=timezone.utc)  # v1.1.0 shipped 1 Mar 2026
MISSING_QUERY = "AttributeError: module 'tinylib' has no attribute 'parse_query'"


def at(repo, tag):
    return Revision(sha=repo.tags[tag], source=RevisionSource.ISSUE_DATE)


@pytest.mark.parametrize("text, expected", [
    ("AttributeError: 'Console' object has no attribute 'save_svg'", [("class", "Console", "save_svg")]),
    ("AttributeError: type object 'tqdm' has no attribute '_lock'", [("class", "tqdm", "_lock")]),
    ("AttributeError: module 'arrow.arrow' has no attribute 'get'", [("module", "arrow.arrow", "get")]),
    ("ImportError: cannot import name 'curry' from 'tlz'", [("module", "tlz", "curry")]),
    ("[BUG] Console has No attribute save_svg", [("either", "Console", "save_svg")]),  # rich #2465's title
    ("AttributeError: partially initialized module 'arrow' has no attribute 'utcnow'", []),  # circular import
    ("parse_url has no effect on long URLs", []),
])
def test_claims(text, expected):
    assert claims(text) == expected


def test_a_released_function_reported_missing_is_an_old_install(tinylib_repo):
    found = find_old_install(MISSING_QUERY, tinylib_repo.path, at(tinylib_repo, "v1.1.0"), "tinylib", None, AFTER_1_1)
    # Followed the re-export in tinylib/__init__.py to where it's defined.
    assert (found.path, found.line, found.text) == ("tinylib/urls.py", 12, "def parse_query(query):")
    assert found.added_in == "v1.1.0"


def test_a_reporter_on_an_older_version_is_still_an_old_install(tinylib_repo):
    assert find_old_install(MISSING_QUERY, tinylib_repo.path, at(tinylib_repo, "v1.1.0"), "tinylib", "1.0.0", AFTER_1_1)


@pytest.mark.parametrize("claimed", ["1.1.0", "v1.1.0", "1.2"])
def test_a_reporter_whose_version_has_it_is_not_an_old_install(tinylib_repo, claimed):
    # Their version should have it, so if it's missing that's worth a real look, not "upgrade".
    assert find_old_install(MISSING_QUERY, tinylib_repo.path, at(tinylib_repo, "v1.1.0"), "tinylib", claimed, AFTER_1_1) is None


def test_released_after_the_report_is_not_an_old_install(tinylib_repo):
    before = datetime(2026, 2, 15, tzinfo=timezone.utc)
    assert find_old_install(MISSING_QUERY, tinylib_repo.path, at(tinylib_repo, "v1.1.0"), "tinylib", None, before) is None


@pytest.mark.parametrize("text", [
    "AttributeError: module 'tinylib' has no attribute 'parse_url_v2'",  # never existed: that's rule 2's absent premise
    "AttributeError: module 'tinylib.urls' has no attribute 'MAX_LENGTH'",  # a constant, set at runtime
    "AttributeError: 'NoneType' object has no attribute 'get'",  # not the package's class
    "AttributeError: module 'select' has no attribute 'select'",  # not the package
])
def test_nothing_to_claim(tinylib_repo, text):
    assert find_old_install(text, tinylib_repo.path, at(tinylib_repo, "v1.1.0"), "tinylib", None, AFTER_1_1) is None


def _git(repo, *args, date=None):
    env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date} if date else {}
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True, env={**os.environ, **env})


def test_a_method_added_to_a_class_later(tmp_path):
    # Like rich #2465: Console gains save_svg in 2.0.0, and the report says it isn't there.
    repo = tmp_path / "richish"
    (repo / "richish").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "richish" / "__init__.py").write_text("")
    for version, body, date in [
        ("1.0.0", "class Console:\n    def print(self):\n        pass\n", "2022-01-01T10:00:00Z"),
        ("2.0.0", "class Console:\n    def print(self):\n        pass\n\n    def save_svg(self, path):\n        pass\n", "2022-04-03T10:00:00Z"),
    ]:
        (repo / "richish" / "console.py").write_text(body)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", version, date=date)
        _git(repo, "tag", f"v{version}")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()

    found = find_old_install("[BUG] Console has No attribute save_svg", repo, Revision(sha=sha, source=RevisionSource.ISSUE_DATE),
                             "richish", None, datetime(2022, 8, 15, tzinfo=timezone.utc))
    assert (found.owner, found.name, found.path, found.line, found.added_in) == ("Console", "save_svg", "richish/console.py", 5, "v2.0.0")
