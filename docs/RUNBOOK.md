# How tonight works

The simple version. Details live in PLAN.md and PROMPTS.md.

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

## Timeline

| Time | Somya | Abhijeet | Vanshaj | Radhika |
| --- | --- | --- | --- | --- |
| 10 PM to 1 AM | Phase 1 | Phase 1 | Asleep. Claude accounts keep working | Eval cases, pitch writing |
| 1 AM to 3 AM | Phase 2 | Phase 2 | Merge, integrate, run real issues | Approve PRs, first eval run |
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

## Rules that cost points if broken

- Every commit message ends with:
  ```
  Coding agent: <the agent you used, or none>
  Models used in project: Qwen3 4B (qwen3:4b via Ollama)
  ```
- No direct pushes to main.
- No API keys or passwords in the repo.
- Nothing pushed after 6:30 AM.
