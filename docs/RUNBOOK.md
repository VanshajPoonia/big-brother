# How tonight works

The one guide for tonight. If it disagrees with another doc, this one wins. The prompts to paste into your coding agent are in docs/PROMPTS.md.

Link for the group chat: https://github.com/VanshajPoonia/big-brother/blob/main/docs/RUNBOOK.md

## Judging, 8:30 AM: run the bot

**Before the pitch, on the demo Mac:**
1. Docker is running, and `ollama list` shows `qwen3:4b`.
2. The runner is on: `cd ~/actions-runner/big-brother-demo && ./run.sh`, and it says "Listening for Jobs". Leave that terminal open. On GitHub, the demo repo's **Settings > Actions > Runners** shows `bigbrother-mac` as Idle.
3. `bigbrother doctor` says layer 3.
4. Keep the Mac awake: run `caffeinate -dims` in another terminal and leave it running. A sleeping Mac is the same as an off one.
5. About 5 minutes before you present, comment `/bigbrother check` on any demo issue. Ollama unloads the model when it sits idle, and the first job after that takes about a minute. Warmed up, it answers in about half a minute.

**The live demo**, on https://github.com/VanshajPoonia/big-brother-demo:
1. **New issue**, paste the long URL bug from issue #1. In about half a minute `github-actions` comments "✓ Reproduced on v1.1.0" with the evidence. The **Actions** tab shows the job running on the Mac.
2. Walk through #2 to #5 and PRs #6 and #7, which already have their comments.
3. Comment `/bigbrother check` on any of them: the bot updates its comment. `/bigbrother help` lists the commands.

**If the Mac sleeps or turns off,** nothing is lost. Each job waits in GitHub's queue as "waiting for a runner", and the issue has no bot comment yet. Start `./run.sh` again and the waiting jobs run in order. A job that waits over 24 hours is cancelled, and a job cut off mid-check shows as failed: comment `/bigbrother check` to run either again. To have the runner start by itself at boot, run `./svc.sh install` and then `./svc.sh start` in the runner folder.

**If someone spams `/bigbrother`,** the Mac is fine and the queue gets slower. The runner does one job at a time, each issue or PR keeps at most one job running and one waiting, so repeats collapse to two, and every check is capped at 1 CPU, 1 GB, 128 processes and 60 seconds. If the demo fails, show the comments already on the demo repo, `examples/`, or `bigbrother check ... --replay examples/humanize-57/report.json`.

**Any of us may be asked to explain any part.** Each person knows their part, and everyone reads `src/bigbrother/pipeline.py`, which ties it together:

| Person | Explains | Files |
| --- | --- | --- |
| Somya | Which release the reporter used, and whether the functions and versions they name exist | `ingest/`, `premises/` |
| Abhijeet | The Docker sandbox: install with network, run offline and locked down, and running a PR's tests before and after | `sandbox/`, `docker/` |
| Radhika | The eval: the 11 hand-checked issues, the injection and repeat runs, the 40 PRs | `eval/`, `evaluate.py` |
| Vanshaj | The model's job, the label rules, the bot and the PR check | `extract/`, `verdict.py`, `bot.py`, `pullrequest.py`, `workflow.yml` |

**Numbers to know**, all saved under `eval/`: 9 of 11 real issues right, every label from evidence, 0 called invalid wrongly. 11 of 11 unchanged with a prompt injection, 11 of 11 the same on a second run. On 40 recent merged PRs in humanize and Rich, 8 PRs' own tests fail without the change and pass with it. The bot answers in 16 to 33 seconds on a laptop, with no API and no server.

## Words used here

- **Branch:** your own copy of the code to work on. `main` is the shared one, and nobody pushes to it directly.
- **PR (pull request):** a request to add your branch to `main`. Teammates read it and approve it on GitHub.
- **CI:** GitHub runs all our tests on every PR. A green tick means they passed, a red cross means something broke.
- **Approve:** a teammate says "this looks right". Every PR needs 1 approval before it can merge.
- **Squash and merge:** the button that adds a PR to `main` as one commit. It's the only merge button in our repo.
- **Lane issue:** your to-do list on GitHub: #3 Somya, #4 Abhijeet, #6 Radhika, #2 and #5 Vanshaj.

## Right now, before 11 PM

1. Vanshaj (or Radhika) creates the team on Cadence (https://cadence.devclubxnst.com) with the same 4 people as on MLH. Strict deadline.
2. Radhika approves PR #11, which adds this guide (see "Radhika, step by step", part A).
3. Everyone does the one-time setup below.

## Who does what

| Person | Job | Issue | Tonight |
| --- | --- | --- | --- |
| Somya | Fetch issues, clone repos, check that functions and versions exist | #3 | Phase 1, then phase 2 |
| Abhijeet | The Docker sandbox that runs the reproduction | #4 | Phase 1, then phase 2 |
| Radhika | Eval cases, pitch, Q&A, blog, approving Vanshaj's PRs | #6 | All night |
| Vanshaj | Core: model calls, label rules, the `check` command, the bot and the PR check. Proof: report and metrics | #2, #5 | Back from 2 AM, merged in #23 |

Somya and Abhijeet review and merge each other's PRs. Radhika's eval PR is reviewed by Somya or Abhijeet.

## Rules that cost points if broken

- **Only offline models.** The model runs on the same laptop as the tool, through Ollama, nowhere else. The code refuses any other model host and stops. No cloud AI anywhere in the product, not even as a fallback.
- Going online is fine for GitHub (reading issues, `git clone`) and `pip install` in the install container. The repro run itself has no network.
- Tests never touch the network. Use the fake model for the model and `httpx.MockTransport` for GitHub.
- Every commit message, and every PR description, ends with these two lines:
  ```
  Coding agent: <the agent you used, or none>
  Models used in project: Qwen3 4B (qwen3:4b via Ollama)
  ```
- No direct pushes to `main`. Always a branch and a PR.
- No API keys or passwords in the repo. They go in `.env`, which git ignores.
- Never post issues or comments on real open-source projects.
- Nothing pushed after 6:30 AM.

## One-time setup

Radhika only needs a browser and her GitHub login, so she can skip this part. Somya and Abhijeet, about 10 minutes:

**1. Check Python.** Run `python3 --version`. It must say 3.11 or higher. If it doesn't:
- Mac: `brew install python@3.12`, then use `python3.12` instead of `python3` below.
- Windows: install Python 3.12 from https://www.python.org/downloads/ and tick "Add python.exe to PATH" during install.

**2. Install git and the GitHub command line tool (`gh`).**
- Mac: `brew install git gh`
- Windows: `winget install --id Git.Git` and `winget install --id GitHub.cli`, then open a new terminal.

**3. Log in to GitHub from the terminal.** Run `gh auth login` and answer:
- "Where do you use GitHub?": **GitHub.com**
- "What is your preferred protocol for Git operations on this host?": **HTTPS**
- "Authenticate Git with your GitHub credentials?": **Yes**
- "How would you like to authenticate GitHub CLI?": **Login with a web browser**
- It prints "First copy your one-time code: XXXX-XXXX". Copy it, press Enter, paste the code in the browser page that opens, click **Continue** and then **Authorize github**.
- Check: `gh auth status` says "Logged in to github.com account <your username>".

This also lets `git push` work without asking for a password.

**4. Tell git who you are**, using the email on your GitHub account so commits show your name:
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**5. Get the code and run the tests.**
```
git clone https://github.com/VanshajPoonia/big-brother
cd big-brother
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```
On Windows, the activate line is `.venv\Scripts\activate`. The last line must end with `passed`. Every time you open a new terminal, `cd big-brother` and run the activate line again.

Then turn on the guard that runs before every push:
```
git config core.hooksPath .githooks
```
From now on `git commit` refuses a message without the two lines, and `git push` first runs exactly what CI runs on the committed code. If the push is refused, read the last lines it printed, fix that, and push again.

**6. Abhijeet only: Docker.**
- Install Docker Desktop: `brew install --cask docker-desktop` on a Mac, or the installer from https://www.docker.com/products/docker-desktop/.
- Open Docker Desktop and wait until it says the engine is running.
- Check: `docker info` prints a "Server Version" line.
- If it shows a Rosetta error on a Mac, open Docker Desktop's **Settings** (gear icon), then **General**, untick **Use Rosetta for x86_64/amd64 emulation on Apple Silicon**, and click **Apply & restart**.

**7. Optional: the real model on your own laptop.** You don't need it, because tests use a fake model. If you want to try it (about 2.5 GB download):
```
brew install ollama
brew services start ollama
ollama pull qwen3:4b
```

## Somya and Abhijeet: one task, start to finish

Your branch names and prompts:

| Who | Phase | Branch | Prompt in docs/PROMPTS.md |
| --- | --- | --- | --- |
| Somya | 1 | `premises/revision-and-symbols` | Account 3, Phase 1 |
| Somya | 2 | `premises/versions-and-history` | Account 3, Phase 2 |
| Abhijeet | 1 | `sandbox/install-and-run` | Account 4, Phase 1 |
| Abhijeet | 2 | `sandbox/evidence` | Account 4, Phase 2 |

Start phase 2 only after your phase 1 PR is merged. Below, Somya's phase 1 is the example. Abhijeet swaps in his own branch, issue #4, and Somya as his reviewer.

**Step 1. Start a fresh branch from the latest `main`.**
```
git checkout main
git pull
git checkout -b premises/revision-and-symbols
```

**Step 2. Give your coding agent the prompt.** Copy the whole code block under "Account 3, Phase 1" in docs/PROMPTS.md, paste it into your agent, and let it work. Only files in your own folders should change: check with `git status`.

**Step 3. Run the tests.**
```
pytest -q
```
It must end with `passed`. If anything fails, ask your agent to fix it. Never push red.

**Step 4. Commit.** If your agent already committed, run `git log -1` and check that the message ends with the two lines. If it didn't commit, do it yourself:
```
git add -A
git commit -m "premises: check that named functions exist" -m "Coding agent: <your agent>
Models used in project: Qwen3 4B (qwen3:4b via Ollama)"
```
Press Enter after `<your agent>` and keep typing. The quote closes at the end. If the two lines are missing from the last commit, rerun the same command with `git commit --amend` in place of `git commit`.

**Step 5. Push.**
```
git push -u origin premises/revision-and-symbols
```

**Step 6. Open the PR on GitHub.**
1. Open https://github.com/VanshajPoonia/big-brother. A yellow bar says your branch "had recent pushes". Click **Compare & pull request**.
   No yellow bar? Click the **Pull requests** tab, then **New pull request**, and pick your branch in the **compare** box.
2. At the top, check it says **base: main** and **compare:** your branch.
3. Title: one short line, the same as your commit subject.
4. The description box is already filled with our template. Fill in each part:
   ```
   ## What this PR does
   Adds fetch_issue and ensure_clone. Only the issue title and body are read, never comments.

   ## Models the product uses in this PR
   Qwen3 4B (qwen3:4b via Ollama). This PR doesn't call it.

   ## AI coding assistants that helped write it
   <your agent>

   ## How we tested it
   pytest -q: 61 passed

   Part of #3

   Coding agent: <your agent>
   Models used in project: Qwen3 4B (qwen3:4b via Ollama)
   ```
   Change the template's last line from `Closes #` to `Part of #3`. "Closes" would close your whole lane issue when the PR merges.
5. On the right, click **Reviewers** and pick your partner (Somya picks Abhijeet878, Abhijeet picks somyasingh31).
6. Click the green **Create pull request** button. Don't pick "Create draft pull request" from its arrow, because a draft can't be merged.

**Step 7. Tell your partner in the group chat** and paste the PR link.

**Step 8. Wait for CI.** At the bottom of the PR's **Conversation** tab, the checks show a yellow dot while running (about a minute), then a green tick or a red cross.
- Red cross: click **Details** next to `test` to see what failed. Fix it on your machine, run `pytest -q`, commit and push again. The PR updates by itself, and CI runs again.

**Step 9. Your partner reviews and approves** (see "How to review a PR" below).
- If they choose "Request changes", fix what they asked for, commit and push. Then click the circular arrows next to their name under **Reviewers** to ask again.
- An approval stays even if you push more commits afterwards. Tell your partner anyway if you change something big.

**Step 10. Merge it yourself** once there's a green tick and an approval.
1. On the **Conversation** tab, scroll to the bottom and click **Squash and merge**.
2. A box opens with the commit title and message. Check that the message ends with the two lines (`Coding agent: ...` and `Models used in project: ...`). If not, type them at the end.
3. Click **Confirm squash and merge**. The branch is deleted automatically.

From the terminal, steps 9 and 10 are `gh pr review <number> --approve` (run by your partner) and `gh pr merge <number> --squash`.

**Step 11. Everyone updates.**
```
git checkout main
git pull
```
Then back to step 1 for your next task.

## How to review a PR

Somya and Abhijeet review each other. Radhika reviews Vanshaj's PRs. You can't approve your own PR.

**Check these before you approve:**
- CI has a green tick.
- The template is filled in and ends with `Part of #<issue>` and the two lines.
- Only that person's folders changed (the **Files changed** tab lists every file).
- New code comes with tests, and the change matches what the lane issue asks for.

**In the browser:**
1. Open https://github.com/VanshajPoonia/big-brother/pulls and click the PR.
2. Click the **Files changed** tab and read through the changes.
3. Click **Review changes** (green button, top right).
4. Write one line, like "Read it, tests pass, looks right".
5. Choose **Approve**. Or, if something is wrong, choose **Request changes** and write exactly what to fix.
6. Click **Submit review**.

**From the terminal:**
```
gh pr review <number> --approve --body "Read it, tests pass, looks right"
gh pr review <number> --request-changes --body "fetch_issue still reads comments, please drop that"
```

## What the box at the bottom of a PR means

| You see | What it means | What to do |
| --- | --- | --- |
| A yellow dot, "checks haven't completed" | CI is still running | Wait a minute |
| A red cross on `test` | A test failed | Click **Details**, fix, push again |
| "Review required" | Nobody has approved yet | Ask your partner in the group chat |
| "Code owner review required" or "Waiting on code owner review from VanshajPoonia" | The PR changes a file only Vanshaj can approve | Undo the change to that file, or wait for Vanshaj |
| "This branch has conflicts that must be resolved" | Someone changed the same lines on `main` | See "Merge conflict" below |
| A green **Squash and merge** button | Ready | Merge it (step 10) |

## Radhika, step by step

Everything happens in the browser at https://github.com/VanshajPoonia/big-brother. Your commits and PRs end with:
```
Coding agent: none
Models used in project: Qwen3 4B (qwen3:4b via Ollama)
```

**A. Approve Vanshaj's PRs (PR #11 now).**
1. Open https://github.com/VanshajPoonia/big-brother/pull/11.
2. Check the green tick at the bottom of the **Conversation** tab.
3. Click **Files changed**, then **Review changes**, write "Read it, looks right", choose **Approve**, and click **Submit review**.
4. Don't merge Vanshaj's PRs. He merges them himself.

**B. Add the eval cases (your phase 1 prompt is in PROMPTS.md, Account 5).**
1. On the repo page, click **Add file**, then **Create new file**.
2. In the name box, type `eval/cases.yaml`. Typing the `/` makes the `eval` folder.
3. Paste your cases into the big box, one block per issue:
   ```
   - id: tinylib-12
     issue_url: https://github.com/owner/tinylib/issues/12
     repo: owner/tinylib
     expected: invalid
     checked_by: Radhika
     note: the function in the report doesn't exist, maintainer said so
   ```
   `expected` is one of `confirmed`, `cannot reproduce` or `invalid`. Spaces matter in this format: copy the indentation exactly.
4. Click **Commit changes...** (green, top right).
5. In the box that opens:
   - **Commit message:** `eval: add hand-checked cases`
   - **Extended description:** the two lines above.
   - Choose **Create a new branch for this commit and start a pull request** and name the branch `eval/cases`.
   - Click **Propose changes**.
6. The "Open a pull request" page appears. Fill in the template like in step 6 for Somya and Abhijeet, with `Part of #6` and the two lines at the end. Under **Reviewers**, pick somyasingh31 or Abhijeet878. Click **Create pull request**.
7. Post the link in the group chat. Once it has an approval and a green tick, click **Squash and merge**, then **Confirm squash and merge**.

To add more cases before it merges: on the repo page, click the branch menu (it says **main**) and pick `eval/cases`. Open `eval/cases.yaml`, click the pencil icon (**Edit this file**), make your changes, click **Commit changes...**, choose **Commit directly to the eval/cases branch**, and click **Commit changes**. The PR updates by itself. After it has merged, add more cases on a new branch called `eval/more-cases`.

**C. Pitch and blog (PROMPTS.md, Account 5, "Writing").**
Same steps as B, with files `docs/PITCH.md` and `docs/BLOG.md`, branch `docs/pitch`, and reviewer VanshajPoonia. These wait for Vanshaj, because `docs/` is his. Keep working in the same branch until he's up.

## While Vanshaj sleeps (about 11 PM to 2 AM)

- Vanshaj's lanes (core #2 and proof #5) are paused. Nothing new from him until he's back.
- Somya and Abhijeet work through phase 1, then phase 2, reviewing and merging each other's PRs.
- Radhika does eval cases, then the pitch and blog, and approves Somya's or Abhijeet's PRs if one of them is stuck.
- Don't edit Vanshaj's files: `schema.py`, `contracts.py`, `extract/`, `verdict.py`, `pipeline.py`, `cli.py`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures/`, `docs/`, `.github/`, `AGENTS.md`, `CLAUDE.md`, `HACKATHON.md`. A PR that touches them can't merge until he's up.
- Need something in those files, like a new dependency or a new field? Comment on issue #2 with what you need and why, then keep going with a stand-in inside your own folder. Vanshaj picks it up at 2 AM.
- Not sure about something? Write it in your lane issue and move to the next item.
- Wake Vanshaj only if `main` has a red cross that nobody can fix in 20 minutes, or someone can't work at all.

## Timeline

| Time | Somya | Abhijeet | Radhika | Vanshaj |
| --- | --- | --- | --- | --- |
| 10:45 PM to 12:30 AM | Phase 1 | Phase 1 | Approve #11, eval cases | Cadence, then asleep from 11 |
| 12:30 AM | Group chat check-in: what merged, what's next, what's blocked |
| 12:30 to 2 AM | Phase 2 | Phase 2 | Pitch and blog | Asleep |
| 2 to 3 AM | Fixes from Vanshaj's review | Fixes from Vanshaj's review | Hand-check labels | Back: merges, connects the lanes, runs real issues |
| 3:30 AM | Clean-clone rehearsal, all together. Stretch work only if everything works |
| 4:30 AM | Feature freeze: only fixes from here |
| 6:15 AM | Last merge. CI must be green on `main` |
| 6:30 AM | Repo frozen. Nobody pushes |
| 8:30 AM | Pitch |

## If something goes wrong

- **Tests fail:** don't push. Ask your agent to fix them, then `pytest -q` again.
- **`pytest: command not found`:** you're outside the project's Python. Run `cd big-brother` and `source .venv/bin/activate`.
- **`git push` asks for a password, or says permission denied:** run `gh auth login` again. If that doesn't fix it, check you accepted the invite at https://github.com/VanshajPoonia/big-brother/invitations.
- **Merge conflict:** tell your agent "rebase my branch on origin/main, fix the conflicts keeping both changes, and run pytest -q". By hand:
  ```
  git checkout main
  git pull
  git checkout <your branch>
  git rebase main
  ```
  Git names the files with conflicts. Open each one, keep the right lines, delete the `<<<<<<<`, `=======` and `>>>>>>>` markers, then `git add <file>` and `git rebase --continue`. Run `pytest -q`, then `git push --force-with-lease`. That's the one time a force push is fine, because it only changes your own branch.
- **`main` has a red cross:** whoever merged last fixes it before anyone else merges.
- **The tool says "the model must run on this machine":** `OLLAMA_HOST` or `BIGBROTHER_BASE_URL` points at another computer. Unset it.
- **Stuck for more than 20 minutes:** write it in your issue and move to the next item.
