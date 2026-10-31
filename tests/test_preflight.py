"""The guard that runs before every push: commit lines and secrets."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("preflight", Path(__file__).parents[1] / "scripts" / "preflight.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

GOOD = "sandbox: run offline\n\nWhy.\n\nCoding agent: Claude Code\nModels used in project: Qwen3 4B (qwen3:4b via Ollama)\n"


@pytest.mark.parametrize("message", [
    GOOD,
    GOOD.replace("Claude Code", "none"),
    GOOD + "Co-authored-by: Somya <232753861+somyasingh31@users.noreply.github.com>\n",
])
def test_good_messages_pass(message):
    assert preflight.message_problems(message) == []


@pytest.mark.parametrize("message, problem", [
    ("fix stuff\n", "Coding agent"),
    ("fix\n\nCoding agent: Claude Code\n", "Models used in project"),
    ("fix\n\nCoding agent:\nModels used in project: Qwen3 4B (qwen3:4b via Ollama)\n", "Coding agent"),
    ("fix\n\nCoding agent: none\nModels used in project: Qwen3 8B (qwen3:8b via Ollama)\n", "costs 5 points"),
])
def test_bad_messages_are_caught(message, problem):
    assert any(problem in p for p in preflight.message_problems(message))


@pytest.mark.parametrize("token", [
    "ghp_" + "a1" * 18,
    "github_pat_" + "x" * 70,
    "AKIA" + "ABCDEFGHIJKLMNOP",
    "sk-" + "z" * 40,
    "-----BEGIN RSA " + "PRIVATE KEY-----",
])
def test_added_secrets_are_caught(token):
    assert preflight.secrets_in(f"+++ b/x.py\n+TOKEN = '{token}'\n")


def test_removed_lines_and_normal_code_are_fine():
    old_token = "ghp_" + "a1" * 18
    assert preflight.secrets_in(f"-TOKEN = '{old_token}'\n+TOKEN = os.environ['GITHUB_TOKEN']\n") == []
