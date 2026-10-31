# Architecture

Big Brother checks whether the claims in a GitHub issue hold up, and labels it `confirmed`, `cannot reproduce` or `invalid`, with the evidence behind the label.

## Flow

```
issue (title + body only, never comments or labels)
  1 revision    tag, PyPI version, or issue-date fallback. Always recorded
  2 extract     Qwen call 1: central claim, premises, symptom quoted from the report
  3 premises    version and symbol checks: present / absent / unknown / error
  4 reproduce   reporter's code if it runs, else Qwen call 2 writes a script
                from the frozen symptom and source excerpts (one fix round)
                install with network, then run offline, both in Docker
  5 decide      fixed rules: label, confidence, basis
  6 output      report.json, report.md, evidence/
```

Pull requests (stretch): run the PR's changed tests on the base and head commits.

## Components

| Part | Choice | Why not the alternative |
| --- | --- | --- |
| Model runtime | Ollama | llama.cpp needs more setup, LM Studio is a GUI, vLLM needs a GPU |
| Model | `qwen3:8b`, thinking off, temperature 0, fixed seed | Good at code and JSON, fits 16 GB. Others are weaker at JSON or slower |
| Model calls | At most 3 per issue: extract, write a script, and one fix if the script breaks on its own | An agent loop lets the model pick actions. We don't want that, and we don't need it |
| Schemas | Pydantic v2 | One model gives the JSON schema Ollama enforces and validates the answer. Up to 2 retries |
| Issue data | GitHub REST API via `httpx`, optional token in `.env` | Comments contain the answer, so we never read them |
| Repos | Full clones, cached locally | Partial clones fetch missing blobs over the network during history checks |
| Symbols | Python `ast` index at the resolved revision, plus a targeted import check in the sandbox | tree-sitter only matters for other languages. Jedi and pyright are slow to set up per repo |
| Versions | Git tags plus PyPI's release list | A missing tag doesn't mean the release never existed |
| Sandbox | Docker, called with exact flags through `subprocess` | The exact command goes into the evidence. gVisor and Firecracker don't run on macOS |
| Installs | `uv pip install` | Much faster than pip across 15 eval repos |
| Verdict | Fixed Python rules | Explainable and unit-tested. A model or classifier would guess |
| Interface | CLI: `check`, `eval`, `doctor` | A GitHub App needs webhooks, a public URL and auth. It's on the roadmap |
| Tests | pytest, a fake model replaying saved Qwen responses, a real Docker test in CI | Pulling a 5 GB model in CI is too slow |

## Evidence rules

- The symptom is quoted from the report (it must appear in the title or body) and frozen before any script is written.
- Generated scripts can't `raise` or call `sys.exit`. A failure only counts if the traceback has a frame inside the checked-out package.
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

A wrong minor detail never overrides rule 1, it only gets listed. Known limit: reports that are invalid because of misuse or an unsupported setup aren't detected and usually land in rule 3 or 4.

## Sandbox contract

- Install: network on, a copy of the repo only, no environment variables, CPU, memory and process limits, 5 minute cap, output capped.
- Run: `--network none --read-only`, dependencies mounted `:ro`, `--tmpfs /tmp:size=64m`, `--cap-drop ALL`, `--security-opt no-new-privileges`, non-root, `--pids-limit 128 --memory 1g --cpus 1`, 60 second cap, output capped at 64 KB. The container is named and removed on timeout.
- Recorded: image digest, Python version, `uv pip freeze`, exact commands.

## Without a model

`--replay` reruns from saved Qwen responses, so `examples/` and the eval reproduce exactly. If Ollama isn't reachable, the report says so and the label comes from premise checks and the reporter's own code only, at low confidence. `OLLAMA_HOST` points at another Ollama server.

## Metrics

`bigbrother eval` reports accuracy over all cases (blocked ones included), per-label precision and recall, a confusion matrix, false `invalid`s, blocked rate, seconds and tokens per issue, and the model name and digest. It runs on 10 to 15 hand-checked public issues, kept apart from the 4 demo cases.

## Not now

Watcher bot, SARIF, agent loop, full history scans, OpenVEX, signed evidence, tracing, gVisor, bisect, Hypothesis. Roadmap: GitHub App, Firecracker, other languages via tree-sitter.
