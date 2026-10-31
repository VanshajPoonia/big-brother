# Test fixtures

- `issues/`: three made-up issues against the `tinylib` fixture repo (built in `conftest.py`): a real bug, a function that never existed, and a report with no steps.
- `model/`: hand-written stand-ins for Qwen responses so tests run without Ollama. Real Qwen runs live in `examples/` and `eval/runs/`.
