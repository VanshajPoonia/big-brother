# Remote code execution in parse_url_v2()

https://github.com/VanshajPoonia/big-brother-demo/issues/2

**invalid** (high confidence, rule 2, basis evidence)

## Why
- central symbol 'tinylib.parse_url_v2' doesn't exist (parse_url_v2 isn't defined in tinylib (tinylib/__init__.py))
- checked at 3e8250e4290f v1.1.0, picked from the tag

## What the report relies on
- symbol `tinylib.parse_url_v2`: absent
- version `1.1.0`: present

## Notes
- skipped the run, a central premise doesn't exist

Rerun: `bigbrother check https://github.com/VanshajPoonia/big-brother-demo/issues/2`

bigbrother 0.1.0, model qwen3:4b
