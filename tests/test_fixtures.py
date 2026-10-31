import subprocess

import pytest


def show(repo, tag, path):
    return subprocess.run(
        ["git", "-C", str(repo.path), "show", f"{tag}:{path}"], check=True, capture_output=True, text=True
    ).stdout


def test_tinylib_has_both_releases(tinylib_repo):
    assert set(tinylib_repo.tags) == {"v1.0.0", "v1.1.0"}


def test_parse_query_only_exists_from_1_1_0(tinylib_repo):
    assert "def parse_query" not in show(tinylib_repo, "v1.0.0", "tinylib/urls.py")
    assert "def parse_query" in show(tinylib_repo, "v1.1.0", "tinylib/urls.py")


@pytest.mark.parametrize("name", ["real_bug", "missing_function", "no_steps"])
def test_sample_issues_load(load_issue, name):
    assert load_issue(name).repo == "daggers/tinylib"
