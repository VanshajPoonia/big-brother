"""Post a report on the issue or pull request it's about, as a bot.

A repo gets comments in two cases only. Our own demo repo, fixed here in the code, not read from
a flag or a setting. Or the repo whose own GitHub Actions job is running the tool: its maintainers
installed the workflow, and the job's token can't write anywhere else. So no typo or setting can
make the tool comment on a project that didn't ask for it.
"""

from __future__ import annotations

import os
import subprocess
from urllib.parse import quote

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
    "tests fail": "b60205",
}


class NotDemoRepo(ValueError):
    pass


def installed_here(repo: str) -> bool:
    """True inside a GitHub Actions job of this same repo, which means its maintainers installed us."""
    return os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_REPOSITORY", "").lower() == repo.lower()


def require_demo(repo: str) -> None:
    if repo.lower() not in DEMO_REPOS and not installed_here(repo):
        raise NotDemoRepo(f"{repo} isn't our demo repo and didn't install the bot. The tool only comments on "
                          f"{', '.join(sorted(DEMO_REPOS))}, or from a repo's own GitHub Actions job")


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


COMMANDS = ("check", "help")
FOOTER = "Comment `/bigbrother check` to run this again, or `/bigbrother help` for what else I can do."
HELP = """I'm Big Brother. I test every new issue and pull request against the code and comment with the evidence.

| Comment | What happens |
| --- | --- |
| `/bigbrother check` | I check this issue or pull request again and update my comment |
| `/bigbrother help` | This list |

On an issue I label it `confirmed`, `cannot reproduce` or `invalid`. On a pull request I say whether its tests check the change.

I run a pull request's tests when the PR's author, or whoever asks with `/bigbrother check`, has write access to this repo.
"""


def parse_command(text: str) -> str | None:
    """"check" or "help" for a comment that starts with /bigbrother, None for any other comment.
    A bare /bigbrother means check, and anything it doesn't know gets the help."""
    words = (text.strip().splitlines() or [""])[0].split()
    if not words or words[0].lower() != "/bigbrother":
        return None
    asked = words[1].lower() if len(words) > 1 else "check"
    return asked if asked in COMMANDS else "help"


def comment_body(markdown: str) -> str:
    return f"{markdown.rstrip()}\n\n{FOOTER}\n{MARKER}\n"


def _ours(comment: dict) -> bool:
    if MARKER not in (comment.get("body") or ""):
        return False
    # Inside Actions only the workflow's own comments count, so nobody else's comment gets edited.
    return os.environ.get("GITHUB_ACTIONS") != "true" or comment["user"]["login"] == "github-actions[bot]"


def post(repo: str, number: int, markdown: str, label: str, client: httpx.Client | None = None) -> str:
    """Comment the report, or update the bot's earlier comment, and swap in its label. Returns the comment's link."""
    require_demo(repo)
    headers = _headers() | {"Authorization": f"Bearer {token()}"}
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        listed = client.get(f"{API}/repos/{repo}/issues/{number}/comments", headers=headers, params={"per_page": 100})
        listed.raise_for_status()
        earlier = [c for c in listed.json() if _ours(c)]
        body = {"body": comment_body(markdown)}
        if earlier:
            response = client.patch(f"{API}/repos/{repo}/issues/comments/{earlier[-1]['id']}", headers=headers, json=body)
        else:
            response = client.post(f"{API}/repos/{repo}/issues/{number}/comments", headers=headers, json=body)
        response.raise_for_status()
        link = response.json()["html_url"]

        current = client.get(f"{API}/repos/{repo}/issues/{number}/labels", headers=headers)
        current.raise_for_status()
        for old in {item["name"] for item in current.json()} & LABEL_COLORS.keys() - {label}:
            client.delete(f"{API}/repos/{repo}/issues/{number}/labels/{quote(old, safe='')}", headers=headers).raise_for_status()
        client.post(f"{API}/repos/{repo}/issues/{number}/labels", headers=headers, json={"labels": [label]}).raise_for_status()
        return link
    finally:
        if owned:
            client.close()


def post_help(repo: str, number: int, client: httpx.Client | None = None) -> str:
    """Reply with the commands. It's a new comment without the marker, so a later check never overwrites it."""
    require_demo(repo)
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.post(f"{API}/repos/{repo}/issues/{number}/comments",
                               headers=_headers() | {"Authorization": f"Bearer {token()}"}, json={"body": HELP})
        response.raise_for_status()
        return response.json()["html_url"]
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
