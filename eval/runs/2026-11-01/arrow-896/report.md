# Module "arrow.arrow" has no attribute 'get'

https://github.com/arrow-py/arrow/issues/896

**cannot reproduce** (low confidence, rule 5, basis fallback)

## Why
- the report has no steps to run, so the label is the blocked policy (cannot reproduce), not evidence
- checked at b746fedf7286 0.17.0, picked from the tag

## What the report relies on
- symbol `arrow.get`: present at arrow/api.py:16: `def get(*args, **kwargs):`

## What ran
- status: no_steps

## Notes
- the model said the report has steps, but it has no runnable Python block

bigbrother 0.1.0, model qwen3:4b
