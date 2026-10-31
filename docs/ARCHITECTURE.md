# Architecture

Big Brother checks whether the claims in a GitHub issue hold up, and labels it `confirmed`, `cannot reproduce` or `invalid`, with the evidence behind the label.

## Flow

```
issue (title + body only, never comments or labels)
  1 revision    tag, PyPI version, or issue-date fallback. Always recorded
  2 extract     Qwen call 1: central claim, premises, symptom quoted from the report.
                The package name is read from the repo, not taken from the model
  3 premises    version and symbol checks: present / absent / unknown / error
  4 reproduce   the reporter's own Python blocks. If they fail on their own mistake
                outside the package (NameError, ImportError), Qwen call 2 repairs
                them once. Install with network, then run offline, both in Docker
  5 decide      fixed rules: label, confidence, basis
  6 output      report.json (with every model answer) and report.md
```

Pull requests (stretch): run the PR's changed tests on the base and head commits.

## Components

| Part | Choice | Why not the alternative |
| --- | --- | --- |
| Model runtime | Ollama by default. `BIGBROTHER_API=llamacpp` talks to any server on this machine with llama.cpp's `/v1/chat/completions` API (llama.cpp, vLLM, LM Studio, Ollama). Any other host is refused | Locking to one server breaks on machines that run another |
| Model | `qwen3:4b` (about 2.5 GB, runs on CPU), thinking off, temperature 0, fixed seed | It only fills small schema-checked JSON and repairs one broken snippet, and rules pick the label. 8B needs about twice the memory |
| Model calls | At most 2 per issue: read the issue, and one repair if the reporter's script breaks on its own. Reports with no code aren't given a model-written script | An agent loop lets the model pick actions. We don't want that, and we don't need it |
| Schemas | Pydantic v2 | One model gives the JSON schema Ollama enforces and validates the answer. Up to 2 retries |
| Issue data | GitHub REST API via `httpx`, optional token in `.env` | Comments contain the answer, so we never read them |
| Repos | Full clones, cached locally | Partial clones fetch missing blobs over the network during history checks |
| Symbols | Python `ast` index at the resolved revision, plus a targeted import check in the sandbox | tree-sitter only matters for other languages. Jedi and pyright are slow to set up per repo |
| Versions | Git tags plus PyPI's release list | A missing tag doesn't mean the release never existed |
| Sandbox | Docker, called with exact flags through `subprocess` | The exact command goes into the evidence. gVisor and Firecracker don't run on macOS |
| Installs | `uv pip install` | Much faster than pip across 15 eval repos |
| Verdict | Fixed Python rules | Explainable and unit-tested. A model or classifier would guess |
| Interface | CLI: `check`, `eval`, `doctor` | A GitHub App needs webhooks, a public URL and auth. It's on the roadmap |
| Tests | pytest, a fake model replaying saved Qwen responses, a real Docker test in CI | Pulling a model in CI is slow and proves nothing the saved runs don't |

## Evidence rules

- The symptom is quoted from the report (it must appear in the title or body) and frozen before any script is written.
- A repaired script is rejected if it raises, asserts, exits, catches exceptions or contains the reported text. If the repair only added imports or dropped lines, the code that ran is still the reporter's, and it's treated that way.
- A failure only counts if the traceback has a frame inside the checked-out package.
- The import check confirms the package comes from the checkout (`__file__` under `/src`).
- Every premise check returns `present`, `absent`, `unknown` or `error`. An import failure is `unknown`, not `absent`.
- `present` needs a source excerpt (file and line).

## Label rules

Applied top to bottom. Every report also records the revision, how it was picked, the execution status and the basis (`evidence` or `fallback`).

| # | Situation | Label | Confidence |
| --- | --- | --- | --- |
| 1 | Repro ran and hit the quoted symptom inside the package | `confirmed` | high |
| 2 | A central premise is `absent` at a revision resolved from a tag or PyPI | `invalid` | high, medium on the date fallback |
| 3 | Repro ran cleanly and exercised what the report describes | `cannot reproduce` | medium, high with the reporter's own code |
| 4 | Repro failed in a different way | `cannot reproduce` | low |
| 5 | Blocked: install failed, timeout or no steps | `cannot reproduce` | low, basis `fallback` |

A wrong minor detail never overrides rule 1, it only gets listed. Known limit: reports that are invalid because of misuse or an unsupported setup aren't detected and usually land in rule 3 or 4. Wrong-output reports are only confirmed (at medium) when the reporter's own code prints the quoted output and that text isn't written in the script, because matching text is otherwise easy to fake.

The label is derived, the facts are stored. Every report keeps the raw facts (execution status, each premise state, what ran, what matched), and the label comes from this table. Rule 5's label is a policy, not a fact: `--blocked-label invalid` changes it without touching code.

## Sandbox contract

- Install: network on, a copy of the repo only, no environment variables, CPU, memory and process limits, 5 minute cap, output capped.
- Run: `--network none --read-only`, dependencies mounted `:ro`, `--tmpfs /tmp:size=64m`, `--cap-drop ALL`, `--security-opt no-new-privileges`, non-root, `--pids-limit 128 --memory 1g --cpus 1`, 60 second cap, output capped at 64 KB. The container is named and removed on timeout.
- Recorded: image digest, Python version, `uv pip freeze`, exact commands.

## Runs anywhere

Each layer works without the one above it. `bigbrother doctor` says which layer a machine is on.

| Layer | Needs | What works |
| --- | --- | --- |
| 0 | A browser | The reports in `examples/`, readable on GitHub |
| 1 | Python and git | Tests and premise checks |
| 2 | Plus Docker | `--replay`: a full check reusing the model answers saved in an earlier report |
| 3 | Plus a model | The full pipeline |

- Never crash. Every stage turns its own failures into `unknown` or `error`, and a report is always written. The CLI only exits non-zero for bad input.
- Every network call and container has a timeout.
- No model reachable: the report says so, nothing is run because there's no quoted symptom to look for, and the label is a fallback.
- `OLLAMA_HOST`, `BIGBROTHER_API`, `BIGBROTHER_BASE_URL` and `BIGBROTHER_MODEL` pick the server and model, but the server must be on this machine. Whatever runs, its name and digest go into the report.

## What goes online

| Step | Network |
| --- | --- |
| Model calls | Never. `local_only` in `extract/model.py` refuses any host that isn't localhost before a request is sent. Proxy settings are ignored and redirects aren't followed |
| Reading the issue | GitHub REST API, title and body only |
| Repo | `git clone` from GitHub, then cached |
| Install container | PyPI, to install the package at the checked revision |
| Repro run | Never. `--network none` |
| Tests and CI | Never. Fake model and `httpx.MockTransport` |

## Metrics

`bigbrother eval` reports accuracy twice, once counting blocked cases as wrong and once leaving them out, so the number is honest whichever way it's graded. Plus per-label precision and recall, a confusion matrix, false `invalid`s, blocked rate, seconds and tokens per issue, and the model name and digest. It runs on 10 to 15 hand-checked public issues, kept apart from the 4 demo cases.

## Not now

Watcher bot, SARIF, agent loop, full history scans, OpenVEX, signed evidence, tracing, gVisor, bisect, Hypothesis. Roadmap: GitHub App, Firecracker, other languages via tree-sitter.
