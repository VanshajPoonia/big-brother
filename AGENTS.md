# AGENTS.md

Rules for everyone working on Big Brother, people and coding agents alike. Read this, [docs/PLAN.md](docs/PLAN.md) and your lane's issue before writing code.

## What we're building

A tool that labels a GitHub issue `confirmed`, `cannot reproduce` or `invalid`, with evidence. Qwen3 4B (via Ollama) extracts the claims and repairs a broken reporter snippet once. Labels come from fixed rules over version and symbol checks and a sandboxed run. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Hard rules

- Never push to `main`. Branch, open a PR, get CI green and 1 approval, then merge.
- Every commit message ends with these two lines:
  ```
  Coding agent: <Claude Code, or whichever agent you used, or none>
  Models used in project: Qwen3 4B (qwen3:4b via Ollama)
  ```
- Fill in the PR template. Name the coding agent and the models.
- The product only uses `qwen3:4b` through Ollama. No cloud AI inside the code, only open-weight models running locally. Adding a model means updating `HACKATHON.md` in the same PR.
- The model only runs on this machine. `extract/model.py` refuses any model host that isn't localhost, ignores proxy settings and never follows redirects. Don't add another way to reach a model, and never point `OLLAMA_HOST` or `BIGBROTHER_BASE_URL` at another computer.
- Only the model is offline. Reading issues from GitHub, `git clone` and `pip install` in the install container may use the network. The repro run uses `--network none`.
- No secrets in the repo. Put them in `.env`, which is gitignored.
- Never post issues or comments on real open-source projects. Only on our demo repo.
- Tests must pass without Ollama. Use the fake model in tests.
- Before every push, `python scripts/preflight.py` must pass. It runs CI's exact test command on the committed code in a fresh install, and checks the commit lines and secrets. Turn on the hooks once with `git config core.hooksPath .githooks` and it runs by itself on `git push`. Never skip it with `--no-verify`.
- Everything is frozen at 6:30 AM. Nothing gets pushed after that.

## Lanes

Only edit your own lane's folders. If you need a change somewhere else, ask that lane's owner or open an issue.

| Lane | Folders |
| --- | --- |
| A Core (Vanshaj) | `src/bigbrother/schema.py`, `contracts.py`, `extract/`, `verdict.py`, `pipeline.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/` |
| B Ingest and premises (Somya) | `src/bigbrother/ingest/`, `src/bigbrother/premises/` |
| C Sandbox (Abhijeet) | `src/bigbrother/sandbox/`, `docker/` |
| D Proof (Vanshaj, second Claude Code account) | `src/bigbrother/report/`, `examples/`, `README.md` |
| Eval data (Radhika) | `eval/cases.yaml`, reviews, no feature code |

`schema.py` and `contracts.py` are the contract between lanes. Only Lane A changes them, and says so in the group chat.

Per-phase prompts for every account are in [docs/PROMPTS.md](docs/PROMPTS.md).

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
