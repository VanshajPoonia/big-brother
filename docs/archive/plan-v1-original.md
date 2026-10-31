# Original plan (v1)

Kept as written at 8:15 PM, before the second review cut the scope. Read it again at the 3:30 AM checkpoint: if we're ahead, pick stretch work from here. The cut list and why is at the bottom.

---

**Goal at 6:30 AM:** a working CLI and GitHub check that takes an issue or PR, extracts its claims with a local Qwen3 8B, verifies each claim with static checks, git history and a sandboxed time-travel reproduction, and outputs evidence-backed verdicts as Markdown, SARIF and OpenVEX. Green CI, real tests, `examples/` from real runs, and accuracy numbers on real closed issues.

## Lanes (one per account, 5 in parallel)

| Lane | Owns | Delivers |
| --- | --- | --- |
| 1 Core | `schema.py`, `harness/`, `extract/`, `verdict.py`, `cli.py` | Contracts, Ollama client with structured outputs, Dual LLM split, claim extraction, verdict rules, CLI, merging |
| 2 Code facts | `verify/` | tree-sitter symbol index, version and tag checks, history search ("never existed" vs "removed in X"), `git bisect run` |
| 3 Sandbox | `sandbox/` | Hardened Docker runner, time-travel environment (checkout + `uv --exclude-newer`), reproduction runs, Hypothesis counterexample search, PR fail-to-pass |
| 4 Outputs | `report/`, `github/`, `.github/workflows/` | Markdown, SARIF and OpenVEX renderers, GitHub check runs with line annotations (dry run by default), signed evidence via `actions/attest` |
| 5 Proof | `eval/`, `examples/`, demo repo, `README.md` | Demo repo with planted reports, eval set of 20 to 30 closed issues, eval runner and metrics, examples, README, pitch, DEV blog post |

## Phases

- Phase 0, foundations (8:30 to 9:45 PM): setup PR, contracts, Ollama and Docker everywhere.
- Phase 1, walking skeleton (9:45 PM to 12:30 AM): issue → claims → symbol check → verdict → Markdown.
- Phase 2, depth (12:30 to 3:30 AM): Dual LLM split, history and bisect, time-travel reproduction and Hypothesis, SARIF, OpenVEX and GitHub check runs, eval numbers.
- Phase 3, stretch or harden (3:30 to 4:30 AM): PR fail-to-pass, signed evidence, OpenTelemetry traces.
- Phase 4, freeze (4:30 to 6:30 AM).

## Demo scenarios

1. Real bug report → `CONFIRMED`, with the minimal crashing input from Hypothesis and the culprit commit from bisect.
2. Hallucinated security report about a function that never existed → `REFUTED`, with history proof.
3. Prompt injection in a report → no effect, thanks to the Dual LLM split.
4. PR claiming "fixes #1, adds tests" whose test already passes on the base commit → flagged.

## Standout stack we picked from

Dual LLM pattern (CaMeL-style), constrained decoding, time-travel reproduction (`uv --exclude-newer`), Hypothesis counterexample search, `git bisect run`, OpenVEX, SARIF + GitHub Checks API, signed evidence (in-toto attestations via Sigstore and `actions/attest`), gVisor in CI, tree-sitter, OpenTelemetry GenAI tracing, OSV.dev lookup, Semgrep rules written by the model, Inspect AI evals. Roadmap: Firecracker, MCP server, OPA policies, Llama Prompt Guard 2.

---

## What got cut, and why

| Cut | Why | Worth adding back at 3:30 if |
| --- | --- | --- |
| PR fail-to-pass | Issues are what's graded | Sandbox is solid. Cheapest stretch, reuses the runner |
| SARIF | Not graded, nice for the panel | Report renderer is done |
| OSV.dev lookup for security claims | Extra network dependency | Premises are done and tested |
| Hypothesis search | Needs a property per claim | One demo case could use it |
| `git bisect run` | Needs a fast, reliable runner first | Runner takes under 10 s per run |
| Dual LLM split | Two passes don't prove safety on their own | Never, the evidence rules cover it |
| `uv --exclude-newer` by default | Old pins break on new Python | Only as a retry when install fails |
| OpenVEX, signed evidence, tracing, gVisor | Not graded, hours of setup | No |
| Watcher bot, GitHub App | Webhooks and auth take hours | No, roadmap |
