# Plan

Build order: version and symbol checks, then one real reproduction, then verdict tests and the public eval, then demo polish.

## What ships at 6:30 AM

`bigbrother check <issue>` gives a label (`confirmed`, `cannot reproduce`, `invalid`) with confidence and saved evidence, as described in [ARCHITECTURE.md](ARCHITECTURE.md). Plus green CI, real tests, `examples/` from real Qwen runs, and eval results on 10 to 15 hand-checked public issues.

## Owners

| Lane | Owner | Owns |
| --- | --- | --- |
| A Core | Vanshaj | `schema.py`, `ingest/`, `extract/`, `verdict.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/` |
| B Premises | Somya (proposed) | `premises/`: revision resolution, version and symbol checks |
| C Sandbox | Abhijeet (proposed) | `sandbox/`: install, run, import check, PR base/head (stretch) |
| D Proof | Radhika (proposed) | `report/`, `eval/`, `examples/`, `README.md`, demo, pitch |
| 5th account | supervised by Vanshaj | tests and reviews only, no feature code |

Each lane owns the tests for its folder. New dependencies go through Lane A. Reviews rotate A → B → C → D → A. Submission owner: Vanshaj.

## Contracts (Lane A, by 9:45 PM)

Pydantic models for issues, claims, premise results, runs, verdicts and reports, the function each lane implements, shared fixtures (a tiny git repo, sample issues) and the fake model. After that, contract changes need Lane A's review and a heads-up in the group chat.

## Timeline

| Time | Done means |
| --- | --- |
| 9:45 PM | Contracts merged. Qwen answers on the demo Mac. Docker works for everyone |
| 11:00 PM | Team on Cadence. Every lane has one real PR merged |
| 12:30 AM | End to end on one public issue with real Qwen and a real sandbox run |
| 2:30 AM | 4 demo cases work. First 8 eval cases run |
| 3:30 AM | First full rehearsal from a clean clone |
| 4:30 AM | Feature freeze. Demo path, backup video, saved evidence, clean rehearsal passes |
| 4:30 to 6:15 | Fixes, tests, CI, README only |
| 6:15 AM | Last merge, CI green |
| 6:30 AM | Frozen |

Sync for 5 minutes at 9:45, 11:00, 12:30, 2:00, 3:30, 4:30 and 5:30: done, next, blocked.

## Demo cases (planted, kept apart from the eval)

1. Real bug report → `confirmed`, traceback inside the package.
2. Report about a function the package never had → `invalid`, with the checks shown.
3. The same real bug with injected instructions → same label as the clean version.
4. Report with no steps → `cannot reproduce`, basis `fallback`.

## Risks

| Risk | Plan |
| --- | --- |
| A laptop can't run `qwen3:8b` | Point `OLLAMA_HOST` at the demo Mac |
| Docker slow on macOS | One small base image, built once |
| Merge conflicts | Folder ownership, contracts first, small PRs |
| Malformed model output | JSON schema, Pydantic validation, 2 retries |
