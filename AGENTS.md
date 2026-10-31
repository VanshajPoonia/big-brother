# AGENTS.md

Rules for everyone working on Big Brother, people and coding agents alike. Read this, [docs/PLAN.md](docs/PLAN.md) and your lane's issue before writing code.

## What we're building

A tool that labels a GitHub issue `confirmed`, `cannot reproduce` or `invalid`, with evidence. Qwen3 8B (via Ollama) extracts the claims and, when needed, writes a repro script. Labels come from fixed rules over version and symbol checks and a sandboxed run. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Hard rules

- Never push to `main`. Branch, open a PR, get CI green and 1 approval, then merge.
- Every commit message ends with these two lines:
  ```
  Coding agent: <Claude Code / Codex / Copilot / none>
  Models used in project: Qwen3 8B (qwen3:8b via Ollama)
  ```
- Fill in the PR template. Name the coding agent and the models.
- The product only uses `qwen3:8b` through Ollama. No OpenAI, Claude, Gemini or any other cloud AI inside the code. Adding a model means updating `HACKATHON.md` in the same PR.
- No secrets in the repo. Put them in `.env`, which is gitignored.
- Never post issues or comments on real open-source projects. Only on our demo repo.
- Tests must pass without Ollama. Use the fake model in tests.
- Everything is frozen at 6:30 AM. Nothing gets pushed after that.

## Lanes

Only edit your own lane's folders. If you need a change somewhere else, ask that lane's owner or open an issue.

| Lane | Folders |
| --- | --- |
| A Core | `src/bigbrother/schema.py`, `ingest/`, `extract/`, `verdict.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/` |
| B Premises | `src/bigbrother/premises/` |
| C Sandbox | `src/bigbrother/sandbox/` |
| D Proof | `src/bigbrother/report/`, `eval/`, `examples/`, `README.md` |
| 5th account | tests and reviews only, no feature code |

`schema.py` is the contract between lanes. Only Lane A changes it, and says so in the group chat.

Each lane owns the tests for its folder, in `tests/test_<folder>*.py`. New dependencies go through Lane A.

Owners and timeline are in [docs/PLAN.md](docs/PLAN.md). Write down decisions in [docs/DECISIONS.md](docs/DECISIONS.md).

## Writing style

Applies to commits, PRs, issues, comments and docs. Taken from how curl, click and black write.

- Commit subject: imperative, under 60 characters, no period. Prefix with the area when it helps: `sandbox: run repro without network`.
- Commit body: why first, then what. Plain sentences, wrapped at 72.
- PR body: a few sentences per template section. Paste real output in a code block instead of describing it. Link the issue (`Closes #12`).
- Keep it short. If a sentence would fit in any PR, delete it.
- Don't use: emojis, em dashes, "This PR introduces", "comprehensive", "robust", "seamless", "leverage", "delve", "crucial", lists of three adjectives, closing summaries, "Let me know if you have questions".
- Write like you'd explain it to a teammate at the next desk.
