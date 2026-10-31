import json

import httpx
import pytest

from bigbrother import bot


def recording(responses):
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path, json.loads(request.content) if request.content else None))
        answer = responses.get(request.url.path, {})
        if request.method != "GET":
            # A write answers with the comment it made, not a list.
            answer = {"html_url": "https://x", **answer} if isinstance(answer, dict) else {"html_url": "https://x"}
        return httpx.Response(200, json=answer)

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


def _returning(method, data):
    """Wrap client.post so its response carries `data`."""
    def call(*args, **kwargs):
        response = method(*args, **kwargs)
        return httpx.Response(200, json=data, request=response.request)
    return call


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


DEMO = "/repos/VanshajPoonia/big-brother-demo/issues/3"


def test_a_first_report_is_a_new_comment_then_its_label():
    client, seen = recording({f"{DEMO}/comments": [], f"{DEMO}/labels": []})
    client.post = _returning(client.post, {"html_url": "https://x/3#c"})
    link = bot.post("VanshajPoonia/big-brother-demo", 3, "**invalid**", "invalid", client=client)

    assert link == "https://x/3#c"
    assert [s[:2] for s in seen] == [("GET", f"{DEMO}/comments"), ("POST", f"{DEMO}/comments"), ("GET", f"{DEMO}/labels"),
                                     ("POST", f"{DEMO}/labels")]
    assert seen[1][2]["body"].endswith(bot.FOOTER + "\n" + bot.MARKER + "\n")
    assert seen[3][2] == {"labels": ["invalid"]}


def test_a_rerun_updates_the_bots_comment_and_swaps_the_label():
    comments = [{"id": 11, "body": "a person", "user": {"login": "someone"}},
                {"id": 12, "body": "**confirmed**\n" + bot.MARKER, "user": {"login": "github-actions[bot]"}}]
    client, seen = recording({f"{DEMO}/comments": comments, f"{DEMO}/labels": [{"name": "bug"}, {"name": "confirmed"}]})
    bot.post("VanshajPoonia/big-brother-demo", 3, "**invalid**", "invalid", client=client)

    methods = [(m, path) for m, path, _ in seen]
    assert ("PATCH", "/repos/VanshajPoonia/big-brother-demo/issues/comments/12") in methods
    assert ("DELETE", f"{DEMO}/labels/confirmed") in methods  # the old label goes, someone's "bug" stays
    assert not any(m == "DELETE" and path.endswith("/bug") for m, path in methods)
    assert ("POST", f"{DEMO}/comments") not in methods


def test_inside_actions_only_the_workflows_own_comment_is_edited(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "VanshajPoonia/big-brother-demo")
    pasted = [{"id": 13, "body": "look: " + bot.MARKER, "user": {"login": "someone"}}]
    client, seen = recording({f"{DEMO}/comments": pasted, f"{DEMO}/labels": []})
    bot.post("VanshajPoonia/big-brother-demo", 3, "**invalid**", "invalid", client=client)
    assert ("POST", f"{DEMO}/comments") in [(m, p) for m, p, _ in seen]


@pytest.mark.parametrize("text, asked", [
    ("/bigbrother check", "check"),
    ("/bigbrother", "check"),
    ("/BigBrother help\nthanks", "help"),
    ("/bigbrother dance", "help"),
    ("thanks /bigbrother check", None),
    ("/bigbrothers check", None),
    ("", None),
])
def test_parse_command(text, asked):
    assert bot.parse_command(text) == asked


def test_help_is_a_new_comment_a_check_never_overwrites():
    client, seen = recording({f"{DEMO}/comments": {"html_url": "https://x/3#h"}})
    bot.post_help("VanshajPoonia/big-brother-demo", 3, client=client)
    assert seen[0][0] == "POST" and bot.MARKER not in seen[0][2]["body"] and "/bigbrother check" in seen[0][2]["body"]


def test_command_routes_to_the_right_check(monkeypatch):
    from bigbrother import cli

    calls = []
    monkeypatch.setattr(cli, "run_check", lambda args: calls.append(("check", args.issue)) or 0)
    monkeypatch.setattr(cli, "run_pr", lambda args: calls.append(("pr", args.url, args.run_tests)) or 0)
    monkeypatch.setattr(cli, "_post_help", lambda repo, number: calls.append(("help", repo, number)) or 0)
    base = "https://github.com/VanshajPoonia/big-brother-demo"
    assert cli.main(["command", f"{base}/issues/2", "--text", "/bigbrother check"]) == 0
    assert cli.main(["command", f"{base}/pull/7", "--text", "/bigbrother", "--run-tests"]) == 0
    assert cli.main(["command", f"{base}/issues/2", "--text", "/bigbrother help"]) == 0
    assert cli.main(["command", f"{base}/issues/2", "--text", "nice work"]) == 0
    assert calls == [("check", f"{base}/issues/2"), ("pr", f"{base}/pull/7", True), ("help", "VanshajPoonia/big-brother-demo", 2)]


def test_command_never_answers_on_a_real_project(capsys):
    from bigbrother.cli import main

    assert main(["command", "https://github.com/Textualize/rich/issues/1", "--text", "/bigbrother help"]) == 2
    assert "isn't our demo repo" in capsys.readouterr().err


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
