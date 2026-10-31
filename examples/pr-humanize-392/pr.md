# Fix intcomma overflow for large Python integers

https://github.com/python-humanize/humanize/pull/392

**tested**: every function this PR changes is used in a test the PR adds or changes

No model and no run: this comes from the PR's diff and the tests at its head.

## Why
- `intcomma` (src/humanize/number.py:116) changed, and a test this PR adds or changes uses it at tests/test_number.py:90
- the PR changes 1 test file: tests/test_number.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `intcomma` | [src/humanize/number.py:116](https://github.com/python-humanize/humanize/blob/244ac0ed6baeb3d1789be61e1a0f8ef962e716f4/src/humanize/number.py#L116) | in this PR: [tests/test_number.py:90](https://github.com/python-humanize/humanize/blob/244ac0ed6baeb3d1789be61e1a0f8ef962e716f4/tests/test_number.py#L90) `assert humanize.intcomma(value) == expected` |

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/392`

bigbrother 0.1.0, checked 3201e702ed7e...244ac0ed6bae
