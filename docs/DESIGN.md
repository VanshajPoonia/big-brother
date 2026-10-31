# Design

## The idea

The model proposes, the evidence decides. Qwen3 8B reads reports and digs through code, but it never hands out verdicts. Fixed rules turn evidence into a verdict per claim.

We judge whether a claim is true, not whether an AI wrote the report.

## Pipeline

```
issue / PR
  -> extract claims        (quarantined model pass, JSON schema, no tools)
  -> plan checks           (privileged model pass, tools, never sees raw text)
  -> verify                (static -> history -> sandbox, cheapest first)
  -> verdict rules         (deterministic)
  -> report                (Markdown, SARIF, OpenVEX)
```

## Claims and how we check them

| Claim | Example | First check |
| --- | --- | --- |
| symbol exists | "RCE in `parse_url_v2()`" | symbol index at that version |
| version affected | "crashes on 2.4.1" | git tags |
| behavior | "crash on long URLs" | sandbox repro, then Hypothesis search |
| security | "remote code execution via X" | exists, then reachable, then proof of concept |
| PR fixes | "fixes #120" | new test fails on base, passes on head |
| PR adds tests | "adds tests" | new tests run the changed lines |

History matters: `git log -S` tells "never existed" (probably made up) apart from "removed in 3.0" (outdated report).

## Verdicts

| Verdict | Needs |
| --- | --- |
| `CONFIRMED` | a recorded sandbox run showing the behavior |
| `REFUTED` | proof that doesn't depend on the model, e.g. the symbol never existed |
| `UNVERIFIED` | neither |
| `INSUFFICIENT_INFO` | the report doesn't say enough to test it |

The model's reasoning alone can never produce `REFUTED`. Dismissing a real bug costs more than leaving it open.

Issue level: any core claim refuted means `invalid`, reproduction attempted and not seen means `cannot reproduce`, core claim confirmed means `confirmed`, anything else is `needs maintainer`.

## Prompt injection

Issue text comes from strangers and can say "ignore your instructions". We use the Dual LLM pattern: the pass that reads raw text has no tools and can only return typed claims; the pass that has tools only ever sees those claims. Verdicts come from rules, so even a fooled model can't fake an exit code.

## Sandbox

A fresh container per run: no network, read-only filesystem, no capabilities, non-root, CPU, memory and process limits, timeout, no environment variables. Dependencies install in a separate step that has network; the step that runs untrusted code has none.

Time travel: check out the claimed version and install dependencies with `uv pip install --exclude-newer <issue date>`, so we test what the reporter had.

Docker on laptops, gVisor in Linux CI. Firecracker is the path for a hosted version.

## Evidence

Each piece records the commit, image digest, command, exit code and output hash, and can be re-run. In CI we sign evidence bundles with `actions/attest` (stretch goal).

## Evaluation

Closed public issues labeled `invalid`, `cannot reproduce` and `confirmed`. Two rules: check out the code as it was when the issue was opened, and feed in only the issue body, never the replies. The number we watch is how often `invalid` is right.

## Stack

| Piece | Choice |
| --- | --- |
| Language | Python 3.12 |
| Model | `qwen3:8b` via Ollama, structured outputs |
| Schemas | Pydantic |
| Code index | tree-sitter |
| Sandbox | Docker (gVisor in CI) |
| Environments | `uv` with `--exclude-newer` |
| Behavior search | Hypothesis |
| Culprit commit | `git bisect run` |
| Output | Markdown, SARIF 2.1.0, OpenVEX |
| GitHub | Checks API with annotations |
| Tests | pytest |
