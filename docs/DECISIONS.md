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
