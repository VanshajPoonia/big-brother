# Big Brother

Big Brother tests the claims in a GitHub bug report against the real code and shows the maintainer the evidence.

It labels an issue `confirmed`, `cannot reproduce` or `invalid`. It finds the release the reporter used, checks that the functions and versions they name exist there, and runs their code in an offline Docker sandbox. Fixed rules pick the label from what that shows. A local open-weight model, Qwen3 4B through Ollama, only reads the issue into a fixed form and repairs a broken snippet once. No cloud AI, and the code refuses to reach a model on any other machine.

Built at Hacktoberfest Hack Day Sonipat by Team Daggers.

## For judges

**No install:** read the saved reports.
- [examples/](examples/) has one report for each label, with the issue that went in.
- [eval/runs/](eval/runs/) has the hand-checked eval: `results.md` holds the score and every case's report.

**With Python 3.11+ and git:** run the tests, no model or Docker needed. `bigbrother doctor` says what else this machine can run.
```
git clone https://github.com/VanshajPoonia/big-brother
cd big-brother
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
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

We hand-checked 11 closed issues from humanize, toolz, arrow, rich and tqdm, reading each thread to the end. The latest run is in [eval/runs/2026-11-01-v2/results.md](eval/runs/2026-11-01-v2/results.md):

- 6 of 11 right, about a minute per issue.
- Every `confirmed` was a real bug (3 of 3), and it never said `invalid` when it wasn't.
- All 4 real `invalid` reports came back as `cannot reproduce`. They were misunderstandings, an old install and a script named `select.py`, not missing functions.
- One real bug was missed because the reporter's snippet uses a function they only proposed.

Each mistake is in the table with the reason the tool gave.

## How it works

1. **Read.** Qwen reads the title and body (never comments) into a schema: the claim, the functions and versions it relies on, and the error quoted word for word. Anything it couldn't have read in the issue is dropped. The package name is read from the repo, not trusted from the model.
2. **Revision.** The release the reporter used, from a git tag, PyPI, or the last commit before the issue date.
3. **Premises.** The source at that release is parsed, not run, to check each function and version exists.
4. **Run.** The reporter's own code runs in Docker at that release: no network, read-only, no capabilities, limited memory, processes and time. If it fails with its own mistake, like a missing import, Qwen repairs it once.
5. **Decide.** Five fixed rules pick the label and say why. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Limits

- Python packages only.
- Wrong-output bugs confirm at medium at most, and only from the reporter's own code.
- `invalid` only means something the report relies on doesn't exist. Reports that are invalid because of a misunderstanding or an old install aren't caught.
- Pull requests aren't checked yet.

## Contributing

Read [AGENTS.md](AGENTS.md) first. Every change goes through a pull request.

## License

MIT
