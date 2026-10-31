# Decisions

Newest at the bottom. One line on what, one on why.

**31 Oct, 8:00 PM. Problem 2 (issue and PR triage).**
Most room for design, the model does real work, and results can still be tested.

**31 Oct, 8:00 PM. Qwen3 8B via Ollama.**
Good tool calling and it fits a 16 GB laptop next to Docker.

**31 Oct, 8:10 PM. Our own agent loop instead of pi.**
Fewer moving parts, and we can explain every line of it.

**31 Oct, 8:10 PM. Python.**
Target repos are Python, and we want `ast`, `uv` and Hypothesis.

**31 Oct, 8:10 PM. The model never decides a verdict.**
Rules over evidence do. A tricked or wrong model can't fake a sandbox result.

**31 Oct, 8:10 PM. Dual LLM split against prompt injection.**
Issue text is untrusted. The pass that reads it has no tools, and the pass with tools never sees it.

**31 Oct, 8:10 PM. Hardened Docker locally, gVisor in CI.**
macOS can't run gVisor or Firecracker. Firecracker is the production answer, not tonight's.

**31 Oct, 8:50 PM. Scope cut after Codex's review.**
No agent loop, at most 2 structured Qwen calls per issue. Dropped the Dual LLM split, gVisor, OpenVEX, signed evidence, tracing, bisect, Hypothesis, SARIF and the watcher bot.

**31 Oct, 8:50 PM. Always output one of the 3 graded labels.**
The organizers grade on `confirmed`, `cannot reproduce` and `invalid`, so we never abstain. Confidence and basis say how sure we are.

**31 Oct, 8:50 PM. Blocked runs fall back to `cannot reproduce`.**
Maintainers use it when they can't make a bug happen. `invalid` would dismiss real bugs. The report marks it as a fallback.

**31 Oct, 8:50 PM. Judges may not have Ollama.**
`--replay` reruns from saved Qwen responses, and `OLLAMA_HOST` can point anywhere. The model stays `qwen3:8b`.

**31 Oct, 8:50 PM. Stricter evidence.**
The symptom must be quoted from the report, a failure only counts inside the package, and premise checks can say `unknown`.
