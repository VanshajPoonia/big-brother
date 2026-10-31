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

**31 Oct, 8:50 PM. Scope cut after a second review.**
No agent loop, at most 2 structured Qwen calls per issue. Dropped the Dual LLM split, gVisor, OpenVEX, signed evidence, tracing, bisect, Hypothesis, SARIF and the watcher bot.

**31 Oct, 8:50 PM. Always output one of the 3 graded labels.**
The organizers grade on `confirmed`, `cannot reproduce` and `invalid`, so we never abstain. Confidence and basis say how sure we are.

**31 Oct, 8:50 PM. Blocked runs fall back to `cannot reproduce`.**
Maintainers use it when they can't make a bug happen. `invalid` would dismiss real bugs. The report marks it as a fallback.

**31 Oct, 8:50 PM. Judges may not have Ollama.**
`--replay` reruns from saved Qwen responses, and `OLLAMA_HOST` can point anywhere. The model stays `qwen3:8b`.

**31 Oct, 8:50 PM. Stricter evidence.**
The symptom must be quoted from the report, a failure only counts inside the package, and premise checks can say `unknown`.

**31 Oct, 9:20 PM. Three coders, five accounts.**
Vanshaj runs Core and Proof on two Claude Code accounts, Somya takes ingest and premises, Abhijeet the sandbox. Radhika hand-checks eval cases and reviews. Prompts per phase are in PROMPTS.md.

**31 Oct, 9:20 PM. One fix round for generated scripts.**
Borrowed from Issue2Test: if a script breaks for its own reasons, Qwen gets the error once. At most 3 model calls per issue.

**31 Oct, 9:20 PM. Original plan kept in docs/archive/.**
We read it again at the 3:30 AM checkpoint and pick stretch work only if everything is green.

**31 Oct, 9:25 PM. Switch to qwen3:4b, reachable over any server.**
The model only fills schema-checked JSON and writes one short script, and rules pick the label, so 4B is enough. It's about 2.5 GB and runs on CPU, which matters on machines we don't control. `BIGBROTHER_API=llamacpp` reaches llama.cpp, vLLM, LM Studio or Ollama through llama.cpp's `/v1/chat/completions` API. Replaces the 8:00 PM choice of 8B.

**31 Oct, 9:25 PM. Built so grading rules and machines can't break it.**
Reports store raw facts and derive the label, `--blocked-label` changes the blocked policy without code, eval prints accuracy with and without blocked cases, and the tool works in layers from "no install" to "full model". It never crashes, it always writes a report.
