# How tonight works

The simple version. Details live in PLAN.md and PROMPTS.md. Link for the group chat: https://github.com/VanshajPoonia/big-brother/blob/main/docs/RUNBOOK.md

## Who does what

| Person | Job | Issue |
| --- | --- | --- |
| Somya | Fetch issues, clone repos, check functions and versions exist | #3 |
| Abhijeet | Docker sandbox that runs the reproduction | #4 |
| Vanshaj, Claude account 1 | Core: model calls, label rules, the `check` command | #2 |
| Vanshaj, Claude account 2 | Proof: report, metrics, examples, README | #5 |
| Radhika | Writing (pitch, Q&A, blog), eval cases, approving Vanshaj's PRs | #6 |

## Before anything: by 11:00 PM

Someone creates the team on Cadence (https://cadence.devclubxnst.com) with the same 4 people as on MLH. Strict deadline.

## The offline rule

The organizers allow only offline models. The model runs on the same machine as the tool, nowhere else.

- Ollama on the same laptop, running `qwen3:4b`. The tool refuses any other model host and stops. That's on purpose.
- No cloud AI anywhere in the product. Not as a fallback, not in a test, not in a script.
- Allowed online: GitHub (reading the issue, `git clone`) and `pip install` in the install container. The repro run itself has no network.
- Tests never touch the network. Use the fake model for the model and `httpx.MockTransport` for GitHub.
- No Ollama on your laptop? You don't need it. Tests use the fake model, and real model runs happen on Vanshaj's Mac.

## One-time setup (everyone, 5 minutes)

```
git clone https://github.com/VanshajPoonia/big-brother
cd big-brother
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

The last line must say `passed`. Abhijeet also needs Docker Desktop running.

Optional, to try the real model on your own laptop (about 2.5 GB):
```
brew install ollama
brew services start ollama
ollama pull qwen3:4b
```

## Every task, step by step

Somya's task as the example. Abhijeet's works the same with names swapped.

**Step 1. Somya starts a branch**
```
git checkout main
git pull
git checkout -b premises/revision-and-symbols
```

**Step 2. Somya pastes her prompt into her coding agent** (from PROMPTS.md, Account 3) and lets it work.

**Step 3. Somya checks the tests**
```
pytest -q
```
It must say `passed`. If anything fails, fix it first. Never push red.

**Step 4. Somya pushes and opens the PR**
```
git push -u origin premises/revision-and-symbols
gh pr create --fill
```
Or open the repo on GitHub and click "Compare & pull request". Fill in the template and write `Part of #3`.

**Step 5. GitHub runs the tests (CI).** Wait for the green tick on the PR.

**Step 6. Abhijeet approves**
```
gh pr review <number> --approve
```
Or on GitHub: Files changed, Review changes, Approve.

**Step 7. Somya merges**
```
gh pr merge <number> --squash --delete-branch
```
Or click "Squash and merge" on GitHub.

**Step 8. Everyone updates**
```
git checkout main
git pull
```

## Vanshaj's PRs

Same steps, but Radhika approves (step 6) and Vanshaj merges (step 7) with:
```
gh pr merge <number> --squash --admin --delete-branch
```
`--admin` is needed because these PRs touch core files only Vanshaj owns.

## Radhika's PRs

- `eval/cases.yaml`: Somya or Abhijeet approves, Radhika merges.
- `docs/PITCH.md`, `docs/BLOG.md`: wait for Vanshaj to approve and merge.

## While Vanshaj sleeps (about 11 PM to 2 AM)

- Claude account 1 keeps building core (#2) and opens PRs. Radhika: when CI is green, approve with `gh pr review <number> --approve`. Claude merges it after that.
- Claude account 2 works on proof (#5) the same way. Radhika approves those too.
- Somya and Abhijeet approve and merge each other's PRs as usual.
- Don't edit Vanshaj's files: `schema.py`, `contracts.py`, `extract/`, `verdict.py`, `pipeline.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/`, `docs/`, `.github/`, `AGENTS.md`, `CLAUDE.md`, `HACKATHON.md`. A PR that touches them can't merge until he's up.
- Need something in those files, like a new dependency or a schema field? Comment on #2 with what you need and keep going with a stand-in. Claude account 1 checks #2 between tasks.
- Wake Vanshaj only if main is red and nobody can fix it in 20 minutes, or someone can't work at all. Everything else goes in your issue.

## Timeline

| Time | Somya | Abhijeet | Vanshaj | Radhika |
| --- | --- | --- | --- | --- |
| 10:30 PM to 12:30 AM | Phase 1 | Phase 1 | Asleep from 11. Claude accounts keep working | Eval cases, pitch writing, approve Claude PRs |
| 12:30 AM | One real issue end to end: check where everyone is in the group chat |
| 12:30 to 3 AM | Phase 2 | Phase 2 | Up at 2: merge, integrate, run real issues | Hand-check labels, first eval run |
| 3:30 AM | Clean-clone rehearsal, all together. Open docs/archive/ and pick stretch work only if everything works |
| 4:30 AM | Feature freeze: only fixes from here |
| 6:15 AM | Last merge. CI must be green |
| 6:30 AM | Repo frozen. Nobody pushes |
| 8:30 AM | Pitch |

## If something goes wrong

- Tests fail: don't push. Ask your agent to fix them.
- Merge conflict: `git checkout main && git pull`, then `git checkout <your branch> && git rebase main`, fix, `pytest -q`, push again.
- Main goes red: whoever merged last fixes it before anyone else merges.
- Stuck for more than 20 minutes: write it in your issue and move to the next item.
- The tool says "the model must run on this machine": `OLLAMA_HOST` or `BIGBROTHER_BASE_URL` points somewhere else. Unset it.

## Rules that cost points if broken

- Every commit message ends with:
  ```
  Coding agent: <the agent you used, or none>
  Models used in project: Qwen3 4B (qwen3:4b via Ollama)
  ```
- No direct pushes to main.
- No API keys or passwords in the repo.
- Only offline models. The model never runs on another machine.
- Nothing pushed after 6:30 AM.
