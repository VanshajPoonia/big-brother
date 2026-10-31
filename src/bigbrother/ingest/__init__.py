"""Read issues from GitHub and keep a local clone of the repo they're about.

Only the issue's title, body and creation time are used. Comments and labels
are never fetched, so the verdict can't be swayed by what other people said.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import httpx

from bigbrother.schema import Issue

API = "https://api.github.com"
ISSUE_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<name>[\w.-]+)/(?P<kind>issues|pull|pulls)/(?P<number>\d+)/?(?:[?#].*)?$"
)
REPO = re.compile(r"^[\w.-]+/[\w.-]+$")


def parse_issue_url(url: str) -> tuple[str, int]:
    """Return (`owner/name`, number) for a GitHub issue URL. Pull request URLs are rejected."""
    match = ISSUE_URL.match(url.strip())
    if not match:
        raise ValueError(f"{url!r} isn't a GitHub issue URL")
    if match["kind"] != "issues":
        raise ValueError(f"{url!r} is a pull request, not an issue")
    return f"{match['owner']}/{match['name']}", int(match["number"])


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "bigbrother",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_issue(url: str, client: httpx.Client | None = None) -> Issue:
    """Fetch an issue's title, body and creation time. Never comments or labels."""
    repo, number = parse_issue_url(url)
    owned = client is None
    if owned:
        client = httpx.Client(timeout=30)
    try:
        response = client.get(f"{API}/repos/{repo}/issues/{number}", headers=_headers())
        response.raise_for_status()
        data = response.json()
    finally:
        if owned:
            client.close()

    # The issues endpoint also returns pull requests. We only judge issues.
    if data.get("pull_request"):
        raise ValueError(f"{url!r} is a pull request, not an issue")
    return Issue(
        url=f"https://github.com/{repo}/issues/{number}",
        repo=repo,
        number=number,
        title=data["title"],
        body=data.get("body") or "",
        created_at=data["created_at"],
    )


def load_issue_file(path: str | Path) -> Issue:
    """Load an issue saved as JSON, in the same shape as `Issue`."""
    return Issue.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, text=True)


def ensure_clone(repo: str, cache_dir: Path) -> Path:
    """Full clone of `owner/name` into the cache, or fetch new tags if it's already there."""
    if not REPO.match(repo):
        raise ValueError(f"{repo!r} isn't owner/name")
    owner, name = repo.split("/")
    if {owner, name} & {".", ".."}:
        raise ValueError(f"{repo!r} isn't owner/name")
    dest = Path(cache_dir) / f"{owner}__{name}"
    if (dest / ".git").exists():
        _git("-C", str(dest), "fetch", "--tags", "--force", "--quiet", "origin")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--quiet", f"https://github.com/{repo}.git", str(dest))
    return dest
