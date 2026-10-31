# Big Brother

Big Brother tests the claims in a GitHub bug report against the real code and shows the maintainer the evidence.

It labels an issue `confirmed`, `cannot reproduce` or `invalid`. It finds the release the reporter used, checks that the functions and versions they name exist there, and runs their code in an offline Docker sandbox. Fixed rules pick the label from what that shows. A local open-weight model, Qwen3 4B through Ollama, only reads the issue into a fixed form, and either repairs a broken snippet once or writes a short script when the report has none. No cloud AI, and the code refuses to reach a model on any other machine.

For a pull request it says whether a test the PR adds or changes uses each function it changes. As a bot, it comments its report on every new issue and PR in our demo repo.

Built at Hacktoberfest Hack Day Sonipat by Team Daggers.

## For judges

**No install:** read the saved reports.
- [examples/](examples/) has one report for each label, with the issue that went in, and two real pull requests.
- [The demo repo](https://github.com/VanshajPoonia/big-brother-demo/issues?q=is%3Aissue) has the bot's comments on five test reports and two PRs.
- [eval/runs/](eval/runs/) has the hand-checked eval: `results.md` holds the score and every case's report.

**With Python 3.11+ and git:** run the tests, no model or Docker needed. `bigbrother doctor` says what else this machine can run.
```
git clone https://github.com/VanshajPoonia/big-brother
cd big-brother
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

**Also with Python and git only:** check a real pull request. No model, no Docker.
```
bigbrother pr https://github.com/Textualize/rich/pull/3906
```

**With Docker and Ollama too:** check a real issue end to end.
```
ollama pull qwen3:4b
bigbrother check https://github.com/python-humanize/humanize/issues/57 --out out
cat out/report.md
```
It takes about a minute, mostly installing the package at the reporter's version. `bigbrother eval` reruns the whole eval, about 10 minutes.

**With Docker but no model:** rerun any saved report with its saved model answers.
```
bigbrother check https://github.com/python-humanize/humanize/issues/57 --replay examples/humanize-57/report.json --out out
```

## What a report says

From `humanize` #57, "`metric(0)` crashes":
```
**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (ValueError: math domain error) inside the package
- checked at dab62bfbc9ac 4.3.0, picked from the tag

## What the report relies on
- symbol `humanize.metric`: present at src/humanize/number.py:476
```
The maintainers fixed it in 4.4.0.

## How well it works

We hand-checked 11 closed issues from humanize, toolz, arrow, rich and tqdm, reading each thread to the end. The final run, all on the same code, is in [eval/runs/2026-11-01-final/results.md](eval/runs/2026-11-01-final/results.md):

- 9 of 11 right, about 22 seconds per issue. Every label came from evidence, none fell back.
- All 4 real bugs confirmed, and every `confirmed` was a real bug. It never said `invalid` when it wasn't.
- 2 of 4 real `invalid` reports caught. In one, the reporter's script was named `select.py`, hiding Python's own `select` module, and their traceback shows it. In the other, the "missing" `Console.save_svg` had shipped in Rich 12.1.0 months before the report, so their install was older. The other 2 were a misunderstanding and a feature request.

Each mistake is in the table with the reason the tool gave.

## The bot

`bigbrother watch` looks at our demo repo every 30 seconds and comments the report on each new issue and pull request, with its label, like a GitHub App would. The model stays on this laptop. It can only comment on [VanshajPoonia/big-brother-demo](https://github.com/VanshajPoonia/big-brother-demo): that list is fixed in `src/bigbrother/bot.py` and checked before anything runs. `scripts/demo_repo.py` builds the demo repo from our test package, with five test reports and two PRs.
```
gh auth login
bigbrother watch            # or --once to handle what's open and stop
```

## How it works

1. **Read.** Qwen reads the title and body (never comments) into a schema: the claim, the functions and versions it relies on, and the error quoted word for word. Anything it couldn't have read in the issue is dropped. The package name is read from the repo, not trusted from the model.
2. **Revision.** The release the reporter used, from a git tag, PyPI, or the last commit before the issue date.
3. **Premises.** The source at that release is parsed, not run, to check each function and version exists.
4. **Run.** The reporter's own code runs in Docker at that release: no network, read-only, no capabilities, limited memory, processes and time. If it fails with its own mistake, like a missing import, Qwen repairs it once. If the report has no code but quotes an exception, Qwen writes a short script from the description, and its result counts for less.
5. **Decide.** Five fixed rules pick the label and say why. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Limits

- Python packages only.
- Wrong-output bugs confirm at medium at most, and only from the reporter's own code.
- `invalid` means something the report relies on doesn't exist, the reporter's own file hid a real module, or what they call missing had already shipped. Misunderstandings and feature requests aren't caught.
- The PR check reads which tests use a changed function. It doesn't run them, so a test that calls the function may still miss the changed lines.

## Contributing

Read [AGENTS.md](AGENTS.md) first. Every change goes through a pull request. Run `git config core.hooksPath .githooks` once: then every push first runs `scripts/preflight.py`, which is CI's exact test command on the committed code in a fresh install.

## License

MIT
