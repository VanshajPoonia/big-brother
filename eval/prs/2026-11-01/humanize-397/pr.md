# Defer importing `math` in `filesize.py`

https://github.com/python-humanize/humanize/pull/397

**no test for this change**: no test the PR adds or changes uses a function it changes

No model: this comes from the PR's diff and the tests at its head.

## Why
- `naturalsize` (src/humanize/filesize.py:38) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_benchmarks.py:65, but they were written before this change
- the PR changes 0 test files

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `naturalsize` | [src/humanize/filesize.py:38](https://github.com/python-humanize/humanize/blob/d6913190a3097cd7bf4f22a4e7e45a9599383c37/src/humanize/filesize.py#L38) | older test: [tests/test_benchmarks.py:65](https://github.com/python-humanize/humanize/blob/d6913190a3097cd7bf4f22a4e7e45a9599383c37/tests/test_benchmarks.py#L65) `benchmark(humanize.naturalsize, 1_234_567_890)` |

## Changed outside functions
- src/humanize/filesize.py: 1 changed line outside any function

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/397`

bigbrother 0.1.0, checked 3201e702ed7e...d6913190a309
