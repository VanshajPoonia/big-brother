import json

import httpx
import pytest

from bigbrother import bot


def recording(responses):
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path, json.loads(request.content) if request.content else None))
        return httpx.Response(200, json=responses.get(request.url.path, {}))

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


@pytest.fixture(autouse=True)
def fake_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    # CI runs inside GitHub Actions for this very repo, which would count as "installed here".
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)


@pytest.mark.parametrize("repo", ["python-humanize/humanize", "Textualize/rich", "daggers/tinylib", "VanshajPoonia/big-brother"])
def test_never_comments_outside_the_demo_repo(repo):
    client, seen = recording({})
    with pytest.raises(bot.NotDemoRepo):
        bot.post(repo, 1, "**confirmed**", "confirmed", client=client)
    with pytest.raises(bot.NotDemoRepo):
        bot.pending(repo, client=client)
    assert seen == []


def test_posts_the_comment_then_the_label():
    client, seen = recording({"/repos/VanshajPoonia/big-brother-demo/issues/3/comments": {"html_url": "https://x/3#c"}})
    link = bot.post("VanshajPoonia/big-brother-demo", 3, "**invalid**", "invalid", client=client)

    assert link == "https://x/3#c"
    assert seen[0][:2] == ("POST", "/repos/VanshajPoonia/big-brother-demo/issues/3/comments")
    assert seen[0][2]["body"].endswith(bot.MARKER + "\n")
    assert seen[1] == ("POST", "/repos/VanshajPoonia/big-brother-demo/issues/3/labels", {"labels": ["invalid"]})


def test_pending_skips_what_already_has_our_label():
    items = [
        {"number": 1, "html_url": "https://github.com/VanshajPoonia/big-brother-demo/issues/1", "labels": [{"name": "confirmed"}]},
        {"number": 2, "html_url": "https://github.com/VanshajPoonia/big-brother-demo/issues/2", "labels": [{"name": "bug"}]},
        {"number": 3, "html_url": "https://github.com/VanshajPoonia/big-brother-demo/pull/3", "labels": [], "pull_request": {}},
    ]
    client, _ = recording({"/repos/VanshajPoonia/big-brother-demo/issues": items})
    assert bot.pending("VanshajPoonia/big-brother-demo", client=client) == [
        ("issue", 2, "https://github.com/VanshajPoonia/big-brother-demo/issues/2"),
        ("pull", 3, "https://github.com/VanshajPoonia/big-brother-demo/pull/3"),
    ]


def test_check_comment_refuses_a_real_project_before_doing_anything(capsys):
    from bigbrother.cli import main

    assert main(["check", "tests/fixtures/issues/real_bug.json", "--comment"]) == 2
    assert "isn't our demo repo" in capsys.readouterr().err


def test_watch_routes_issues_and_prs_once_each_and_always_comments(monkeypatch):
    from bigbrother import cli

    calls = []
    monkeypatch.setattr(bot, "pending", lambda repo: [("issue", 2, "https://github.com/VanshajPoonia/big-brother-demo/issues/2"),
                                                      ("pull", 3, "https://github.com/VanshajPoonia/big-brother-demo/pull/3")])
    monkeypatch.setattr(cli, "run_check", lambda args: calls.append(("check", args.issue, args.comment)) or 0)
    monkeypatch.setattr(cli, "run_pr", lambda args: calls.append(("pr", args.url, args.comment)) or 0)

    assert cli.main(["watch", "--once"]) == 0
    assert calls == [("check", "https://github.com/VanshajPoonia/big-brother-demo/issues/2", True),
                     ("pr", "https://github.com/VanshajPoonia/big-brother-demo/pull/3", True)]


def test_watch_refuses_a_real_project(capsys):
    from bigbrother.cli import main

    assert main(["watch", "--repo", "Textualize/rich", "--once"]) == 2
    assert "isn't our demo repo" in capsys.readouterr().err


def test_a_repo_that_installed_the_bot_can_get_comments_from_its_own_job(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "someone/their-lib")
    bot.require_demo("someone/their-lib")
    with pytest.raises(bot.NotDemoRepo):
        bot.require_demo("python-humanize/humanize")  # a job in one repo never comments on another


def test_the_repo_name_alone_isnt_enough_outside_actions(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", "python-humanize/humanize")
    with pytest.raises(bot.NotDemoRepo):
        bot.require_demo("python-humanize/humanize")
