# Fix `naturaldelta` doctest

https://github.com/python-humanize/humanize/pull/402

**no test for this change**: no test the PR adds or changes uses a function it changes

No model: this comes from the PR's diff and the tests at its head.

## Why
- `naturaldelta` (src/humanize/time.py:97) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_benchmarks.py:61, but they were written before this change
- the PR changes 0 test files

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `naturaldelta` | [src/humanize/time.py:97](https://github.com/python-humanize/humanize/blob/3829f928aa68cf30ee434975f7aba82849dcd3c2/src/humanize/time.py#L97) | older test: [tests/test_benchmarks.py:61](https://github.com/python-humanize/humanize/blob/3829f928aa68cf30ee434975f7aba82849dcd3c2/tests/test_benchmarks.py#L61) `benchmark(humanize.naturaldelta, dt.timedelta(hours=3, minutes=27))` |

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/402`

bigbrother 0.1.0, checked ffdf407fdfe1...3829f928aa68
