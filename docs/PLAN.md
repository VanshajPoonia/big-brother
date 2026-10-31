# Plan

v3: owners, phases and how merging works. Prompts for each account are in [PROMPTS.md](PROMPTS.md). Earlier plans are in [archive/](archive/), and we read the original again at the 3:30 AM checkpoint.

Build order: version and symbol checks, then one real reproduction, then verdict tests and the public eval, then demo polish.

## Accounts

| # | Who | Lane | Owns | Issue |
| --- | --- | --- | --- | --- |
| 1 | Vanshaj, Claude Code | A Core | `schema.py`, `contracts.py`, `extract/`, `verdict.py`, `pipeline.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/` | #2 |
| 2 | Vanshaj, Claude Code (second account) | D Proof | `src/bigbrother/report/`, `examples/`, `README.md` | #5 |
| 3 | Somya | B Ingest and premises | `src/bigbrother/ingest/`, `src/bigbrother/premises/` | #3 |
| 4 | Abhijeet | C Sandbox | `src/bigbrother/sandbox/`, `docker/` | #4 |
| 5 | Radhika, writing only | Eval data, writing and reviews | `eval/cases.yaml`, `docs/PITCH.md`, `docs/BLOG.md`, reviews, backup video | #6 |

Each lane owns the tests for its folders.

## Phases

| Phase | Time | 1 Core | 2 Proof | 3 Somya | 4 Abhijeet | 5 Radhika |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | now to 9:45 PM | Merge #1, #7, #8. Ollama and `qwen3:4b` on the demo Mac | Read docs | Read docs | Docker running | Start finding repos |
| 1 | 9:45 PM to 12:30 AM | Extraction, verdict rules, pipeline, `check` | Markdown report, metrics | Fetch issue, clone, revision, symbol index | Image, install, run, traceback | 15 candidate issues |
| 2 | 12:30 to 3:00 AM | Repro script with one fix round, `--replay`, `doctor`, `eval` | Examples, README for judges | PyPI versions, re-exports, targeted history | Import check, environment record, Docker test in CI | Hand-check labels, first eval run |
| 3 | 3:00 to 3:30 AM | Integration fixes | Rehearsal notes | Fixes | Fixes | Clean-clone rehearsal |
| 4 | 3:30 to 4:30 AM | Stretch or harden | SARIF (stretch) | OSV lookup (stretch) | PR fail-to-pass (stretch) | Backup video |
| 5 | 4:30 to 6:15 AM | Fixes only | Regenerate examples, README | Fixes only | Fixes only | Pitch rehearsal |

## Checkpoints

| Time | Done means |
| --- | --- |
| 9:45 PM | Contracts on main. Qwen answers on the demo Mac. Docker works on Abhijeet's machine |
| 11:00 PM | Team on Cadence. Every lane has one real PR merged |
| 12:30 AM | End to end on one real public issue with real Qwen and a real sandbox run |
| 3:30 AM | Clean-clone rehearsal passes. Open [archive/plan-v1-original.md](archive/plan-v1-original.md) and pick at most one stretch per person, only if green |
| 4:30 AM | Feature freeze. Demo path, backup video and saved evidence ready |
| 6:15 AM | Last merge, CI green on main |
| 6:30 AM | Frozen. Nothing pushed after this |

Sync for 5 minutes at 9:45, 11:00, 12:30, 2:00, 3:30, 4:30 and 5:30: done, next, blocked.

## How merging works

1. Start from a fresh main: `git checkout main && git pull && git checkout -b <lane>/<task>`.
2. Write the code and its tests. **Run `pytest -q` before every push. Never push red.**
3. Commit messages end with the two lines from AGENTS.md (coding agent, models).
4. Before pushing: `git fetch && git rebase origin/main`, then run `pytest -q` again.
5. Open the PR with the template filled in and `Part of #<your lane issue>`.
6. Ask for review: Somya and Abhijeet review each other, Vanshaj reviews both, Radhika reviews Vanshaj's PRs.
7. Merge when CI is green and the PR is approved, using squash and delete branch:
   - Only your own folders: the author merges.
   - Anything in `.github/CODEOWNERS`: Vanshaj merges.
8. If main goes red, whoever broke it fixes it first. Nothing else merges until it's green.
9. Contract changes (`schema.py`, `contracts.py`) only come from Lane A, announced in the group chat. Everyone rebases after.
10. No merges after 6:15 AM.

## Risks

| Risk | Plan |
| --- | --- |
| A laptop can't run `qwen3:4b` | Point `OLLAMA_HOST` at the demo Mac, or `BIGBROTHER_API=llamacpp` at any other local server |
| Judges' setup unknown | Layers in ARCHITECTURE.md: reports readable with no install, `--replay` with no model, full run with a model |
| Docker slow on macOS | One small base image, built once |
| Merge conflicts | Folder ownership, contracts first, small PRs |
| Malformed model output | JSON schema, Pydantic validation, 2 retries |
| Lane B or C late | Pipeline accepts any function that fits the contract, so Lane A tests with fakes |
