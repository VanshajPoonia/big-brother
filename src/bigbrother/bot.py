"""Post a report on the issue or pull request it's about, the way a GitHub App would.

Comments only ever go to our own demo repo. The list is fixed here in the code, not read from a
flag or a setting, so no typo can make the tool comment on a real project.
"""

from __future__ import annotations

import os
import subprocess

import httpx

from bigbrother.ingest import API, _headers

DEMO_REPOS = frozenset({"vanshajpoonia/big-brother-demo"})
MARKER = "<!-- bigbrother -->"
# Every label the bot puts on: issue labels first, then pull request labels.
LABEL_COLORS = {
    "confirmed": "d73a4a",
    "cannot reproduce": "fbca04",
    "invalid": "e4e669",
    "tested": "0e8a16",
    "partly tested": "fbca04",
    "no test for this change": "d93f0b",
    "no function changed": "c5def5",
}


class NotDemoRepo(ValueError):
    pass


def require_demo(repo: str) -> None:
    if repo.lower() not in DEMO_REPOS:
        raise NotDemoRepo(f"{repo} isn't our demo repo. The tool only comments on {', '.join(sorted(DEMO_REPOS))}")


def token() -> str:
    """GITHUB_TOKEN, or the token `gh auth login` saved."""
    found = os.environ.get("GITHUB_TOKEN", "")
    if not found:
        try:
            found = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            found = ""
    if not found:
        raise ValueError("posting needs GITHUB_TOKEN in the environment, or `gh auth login`")
    return found


def comment_body(markdown: str) -> str:
    return f"{markdown.rstrip()}\n\n{MARKER}\n"


def post(repo: str, number: int, markdown: str, label: str, client: httpx.Client | None = None) -> str:
    """Comment the report and add its label. Returns the comment's link."""
    require_demo(repo)
    headers = _headers() | {"Authorization": f"Bearer {token()}"}
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.post(f"{API}/repos/{repo}/issues/{number}/comments", headers=headers,
                               json={"body": comment_body(markdown)})
        response.raise_for_status()
        link = response.json()["html_url"]
        client.post(f"{API}/repos/{repo}/issues/{number}/labels", headers=headers,
                    json={"labels": [label]}).raise_for_status()
        return link
    finally:
        if owned:
            client.close()


def pending(repo: str, client: httpx.Client | None = None) -> list[tuple[str, int, str]]:
    """Open issues and pull requests without one of our labels, as (kind, number, link), oldest first.

    Labels are read only to skip what's already done. They never reach the verdict.
    """
    require_demo(repo)
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.get(f"{API}/repos/{repo}/issues", headers=_headers() | {"Authorization": f"Bearer {token()}"},
                              params={"state": "open", "per_page": 100, "sort": "created", "direction": "asc"})
        response.raise_for_status()
        items = response.json()
    finally:
        if owned:
            client.close()
    found = []
    for item in items:
        if {label["name"] for label in item.get("labels", [])} & LABEL_COLORS.keys():
            continue
        kind = "pull" if "pull_request" in item else "issue"
        found.append((kind, item["number"], item["html_url"]))
    return found
