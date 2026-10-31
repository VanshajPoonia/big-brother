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
`--replay` reruns from saved Qwen responses, and `OLLAMA_HOST` can point anywhere (replaced at 10:30 PM: local only). The model stays `qwen3:8b`.

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

**31 Oct, 10:30 PM. The model only runs on this machine.**
The organizers allow only offline models. The code refuses any model host that isn't localhost, ignores proxy settings and doesn't follow redirects, so a typo or a stray setting can't send issue text out. GitHub, git and pip still use the network. The repro run doesn't.

**1 Nov, 2:00 AM. One repair round for broken reporter scripts.**
Two of 11 real reporters forgot an import, so their code died with NameError before reaching the package. When a script fails with its own NameError or ImportError outside the package, Qwen fixes it once and it runs again. The fix is rejected if it raises, asserts, exits, catches exceptions or contains the reported text.

**1 Nov, 2:20 AM. Tried and dropped: the model tagging feature requests.**
All 4 real invalid reports in the eval were misunderstandings or feature requests, not missing functions. We had Qwen tag each report as a bug, question or feature request, with a rule turning a non-bug into invalid. On the 11 real cases Qwen called every report a bug, including a plain feature request, so the rule never fired. It only added model influence and a risk of false invalids, so it's gone. Invalid still means "something the report relies on doesn't exist".

**1 Nov, 2:20 AM. The package name comes from the repo.**
On toolz #99 Qwen named the package `update_in`, a function. That broke the repair and would have hidden a real crash, because "inside the package" is checked against that name. Now the importable packages are read from the checkout, and Qwen's name is only kept if the repo has it.

**1 Nov, 2:40 AM. A repair can't import what the package doesn't have.**
On toolz #99 Qwen's repair imported `clojure_update_in`, a function the reporter only proposed, so the script died before reaching the real bug. Names a repair adds are now checked against the source at that revision and taken out if they're missing. Only the model's additions are touched. Eval went from 6 to 7 of 11.

**1 Nov, 3:00 AM. Catch a reporter's file hiding a real module.**
On tqdm #1477 the reporter's script was named `select.py`, so Python loaded it instead of the standard `select` module and tqdm looked broken. The report's own traceback shows both facts: a frame from the reporter's `select.py` outside any installed library, and `module 'select' has no attribute 'select'`. Both have to be there, so a hint alone (arrow #1154 says "partially initialized module 'arrow'" but shows no file) isn't enough. It needs no model. A real reproduction still wins. First real invalid caught: 8 of 11.

**1 Nov, 3:15 AM. Catch reports from an old install.**
rich #2465 says "Console has no attribute save_svg". At the code from the issue date, `Console.save_svg` is defined in `rich/console.py`, and git history shows it first shipped in 12.1.0 on 3 Apr 2022, four months before the report. Rich's changelog agrees, and the maintainer told the reporter to upgrade. The check needs every step to hold: the report names the owner, that same class or module defines the name, the release came out before the report, and a version the reporter gave is older than that release. It needs no model, and a real reproduction still wins. 9 of 11.


**1 Nov, 3:35 AM. Qwen writes a script when the report has no code.**
Reports that only describe a bug used to fall back with nothing run. Now, if the report quotes an exception and names the package, Qwen writes a short script from the description. It passes the same safety check as a repair and must import the package. It counts for less than the reporter's own code: confirmed at medium at most, and a clean run is cannot reproduce at low. On arrow #896 Qwen wrote exactly the reporter's two unfenced lines, which ran cleanly at 0.17.0.

**1 Nov, 3:40 AM. The PR check counts only the PR's own tests.**
The first version counted any test naming a changed function, so rich #3915 looked covered because an old test imports `install`. Old tests were written before the change, so they can't show the change is tested. Now only tests the PR adds or changes count, including a new parametrize case. Imports don't count as use, a constructor is found by its class name, and when two modules define the same name the test must name the module. No model, nothing run. Running the PR's tests on its base and head stays on the roadmap.

**1 Nov, 3:45 AM. A bot from the laptop, commenting only on our demo repo.**
The problem asks for a GitHub App. A hosted App needs a public server, and the model has to stay on this machine, so `bigbrother watch` polls a repo and comments like an App would on a webhook. The repos it may comment on are fixed in `bot.py`, not read from a flag, and checked before anything runs, so it can't comment on a real project.

**1 Nov, 4:10 AM. Reports write this machine's folders as ~ and $TMPDIR.**
Reports became public comments, and the recorded commands named the home folder and macOS's per-user temp folder. Placeholders like `<clone>` read like leftover data, so the folders are written the way a shell would, and the commands still read and paste the same. The two tinylib examples ran from a scratch folder, so they were replaced by real runs on the demo repo's issues.

**1 Nov, 4:20 AM. The PR check runs the PR's tests.**
Reading which tests use a function can't show the test checks the change. With `--run-tests` the PR's test files run in the sandbox at its head, then at its base with those files copied in. On humanize #392, #359 and #381 they fail without the fix and pass with it. Running beats reading names, so failing before and passing after makes it `tested`.

**1 Nov, 4:25 AM. The bot is a workflow on the maintainer's own machine.**
A hosted GitHub App needs a public server and would run the model somewhere else. A self-hosted Actions runner pulls work from GitHub, so it needs no server and nothing reaches the machine from outside, and the comments come from `github-actions`. `bigbrother init` installs it in one command. It uses `pull_request_target` so a PR can't change the workflow, and only people with write access get their PR's tests run.
