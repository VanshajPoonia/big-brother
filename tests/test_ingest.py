import json
import subprocess
from pathlib import Path

import httpx
import pytest

from bigbrother import ingest
from bigbrother.ingest import ensure_clone, fetch_issue, load_issue_file, parse_issue_url

ISSUE = {
    "title": "parse_url crashes on long URLs",
    "body": None,
    "created_at": "2026-03-05T12:00:00Z",
    "labels": [{"name": "bug"}],
    "comments": 4,
}


def client_for(payload: dict, seen: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_issue_reads_only_the_issue(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    seen: list[httpx.Request] = []
    issue = fetch_issue("https://github.com/daggers/tinylib/issues/1", client=client_for(ISSUE, seen))

    assert [str(r.url) for r in seen] == ["https://api.github.com/repos/daggers/tinylib/issues/1"]
    assert not any("comments" in str(r.url) or "labels" in str(r.url) for r in seen)
    assert "authorization" not in seen[0].headers
    assert issue.repo == "daggers/tinylib"
    assert issue.number == 1
    assert issue.body == ""
    assert issue.created_at.year == 2026


def test_fetch_issue_sends_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    seen: list[httpx.Request] = []
    fetch_issue("https://github.com/daggers/tinylib/issues/1", client=client_for(ISSUE, seen))
    assert seen[0].headers["authorization"] == "Bearer secret"


@pytest.mark.parametrize(
    "url",
    ["https://github.com/daggers/tinylib/pull/5", "https://github.com/daggers/tinylib/pulls/5"],
)
def test_fetch_issue_rejects_pull_request_url(url):
    seen: list[httpx.Request] = []
    with pytest.raises(ValueError, match="pull request"):
        fetch_issue(url, client=client_for(ISSUE, seen))
    assert seen == []


def test_fetch_issue_rejects_pull_request_behind_issue_url():
    seen: list[httpx.Request] = []
    payload = {**ISSUE, "pull_request": {"url": "https://api.github.com/repos/daggers/tinylib/pulls/1"}}
    with pytest.raises(ValueError, match="pull request"):
        fetch_issue("https://github.com/daggers/tinylib/issues/1", client=client_for(payload, seen))


def test_parse_issue_url():
    assert parse_issue_url("https://github.com/a/b.c/issues/12/") == ("a/b.c", 12)
    assert parse_issue_url("https://github.com/a/b/issues/3#issuecomment-1") == ("a/b", 3)
    with pytest.raises(ValueError):
        parse_issue_url("https://gitlab.com/a/b/issues/3")


def test_load_issue_file(tmp_path: Path):
    path = tmp_path / "issue.json"
    path.write_text(
        json.dumps(
            {
                "url": "https://github.com/daggers/tinylib/issues/1",
                "repo": "daggers/tinylib",
                "number": 1,
                "title": "t",
                "body": "b",
                "created_at": "2026-03-05T12:00:00Z",
            }
        )
    )
    assert load_issue_file(path).title == "t"


def test_ensure_clone_clones_into_cache(tmp_path: Path, monkeypatch):
    calls = []
    monkeypatch.setattr(ingest, "_git", lambda *args: calls.append(args))
    dest = ensure_clone("daggers/tinylib", tmp_path)
    assert dest == tmp_path / "daggers__tinylib"
    assert calls == [("clone", "--quiet", "https://github.com/daggers/tinylib.git", str(dest))]


def test_ensure_clone_fetches_tags_when_cached(tmp_path: Path, tinylib_repo):
    dest = tmp_path / "cache" / "daggers__tinylib"
    subprocess.run(["git", "clone", "-q", str(tinylib_repo.path), str(dest)], check=True)
    subprocess.run(["git", "-C", str(tinylib_repo.path), "tag", "v9.9.9"], check=True)

    assert ensure_clone("daggers/tinylib", tmp_path / "cache") == dest
    tags = subprocess.run(["git", "-C", str(dest), "tag"], capture_output=True, text=True, check=True).stdout
    assert "v9.9.9" in tags.split()


def test_ensure_clone_rejects_bad_repo(tmp_path: Path):
    with pytest.raises(ValueError):
        ensure_clone("../etc", tmp_path)


def test_a_spent_rate_limit_says_how_to_fix_it():
    import httpx
    import pytest

    from bigbrother.ingest import RATE_LIMITED, fetch_issue

    def handler(request):
        return httpx.Response(403, headers={"x-ratelimit-remaining": "0"}, json={"message": "API rate limit exceeded"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client, pytest.raises(ValueError, match="gh auth login"):
        fetch_issue("https://github.com/a/b/issues/1", client=client)
    assert "60 an hour" in RATE_LIMITED
