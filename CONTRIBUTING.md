# Contributing to Big Brother

Thanks for helping. Every change starts as an issue and ends as a pull request, in this order. A pull request without an assigned issue and an agreed plan will be closed, so nobody's work is wasted.

## 1. Open an issue

Search the [open issues](https://github.com/VanshajPoonia/big-brother/issues) first. If nothing covers it, open one with the bug or idea template:

- **A bug:** what you ran, what you expected, what happened, and the version (`bigbrother --version`). Paste the command and its full output.
- **An idea:** the problem it solves for a maintainer, and an example issue or pull request it would get right.

## 2. Ask to be assigned

Comment on the issue that you'd like to work on it. Wait until a maintainer assigns it to you. One person per issue, so two people don't build the same thing. If you go quiet for a week, it may be given to someone else.

## 3. Comment a plan

Before you write code, comment your plan on the issue and wait for a maintainer to agree:

```
Plan
- What changes: the behaviour before and after, in a sentence or two
- Where: the files you'll touch (see the lanes in AGENTS.md)
- How it's tested: the tests you'll add, and a real issue or PR you'll run it on
- What it won't do: anything you're leaving out on purpose
```

Small fixes, like a typo or a broken link, can skip the plan, but still need the issue.

## 4. Open the pull request

1. Fork the repo and branch from `main`. Never push to `main`.
2. Set up once:
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   git config core.hooksPath .githooks
   ```
   The hook runs `scripts/preflight.py` on every push: CI's exact tests on your committed code in a fresh install, plus checks for the commit lines and anything that looks like a secret.
3. Write the tests with the change. They must pass without Ollama or Docker: use the fake model in `tests/`.
4. End every commit message with:
   ```
   Coding agent: <the AI coding assistant you used, or none>
   Models used in project: Qwen3 4B (qwen3:4b via Ollama)
   ```
5. Open the pull request, fill in the template, and link the issue with `Closes #N`. CI must pass and a maintainer must approve it before it's merged.

## Ground rules

- The product only uses open-weight models running on the user's own machine. Don't add a call to a hosted model or a remote API.
- No secrets in the repo. Keep tokens in `.env`, which is gitignored.
- Never point the bot at a real project to try it. Use the demo repo, [VanshajPoonia/big-brother-demo](https://github.com/VanshajPoonia/big-brother-demo).
- Write like you'd explain it to a teammate. [AGENTS.md](AGENTS.md) has the style and the full rules.
