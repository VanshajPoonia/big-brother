# feat: Traceback - Expose more locals rendering options

https://github.com/Textualize/rich/pull/3906

**no test for this change**: no test the PR adds or changes uses a function it changes

No model and no run: this comes from the PR's diff and the tests at its head.

## Why
- `render_scope` (rich/scope.py:14) changed, and no test uses it at all
- `install` (rich/traceback.py:84) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_traceback.py:24, but they were written before this change
- `Traceback.__init__` (rich/traceback.py:295) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_traceback.py:67, but they were written before this change
- `Traceback.from_exception` (rich/traceback.py:353) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_traceback.py:325, but they were written before this change
- `Traceback.extract` (rich/traceback.py:433) changed, and no test uses it at all
- `Traceback._render_stack` (rich/traceback.py:768) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- the PR changes 0 test files

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `render_scope` | [rich/scope.py:14](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/scope.py#L14) | none |
| `install` | [rich/traceback.py:84](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/traceback.py#L84) | older test: [tests/test_traceback.py:24](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/tests/test_traceback.py#L24) `old_handler = install(console=console)` |
| `Traceback.__init__` | [rich/traceback.py:295](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/traceback.py#L295) | older test: [tests/test_traceback.py:67](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/tests/test_traceback.py#L67) `tb = Traceback()` |
| `Traceback.from_exception` | [rich/traceback.py:353](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/traceback.py#L353) | older test: [tests/test_traceback.py:325](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/tests/test_traceback.py#L325) `trace = Traceback.from_exception(exc_type, exc_value, traceback).trace` |
| `Traceback.extract` | [rich/traceback.py:433](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/traceback.py#L433) | none |
| `Traceback._render_stack` | [rich/traceback.py:768](https://github.com/Textualize/rich/blob/c69f3cc46812036eb0aaf4dd267e0463cbdfe17c/rich/traceback.py#L768) | none |

## Changed outside functions
- rich/scope.py: 1 changed line outside any function
- rich/traceback.py: 3 changed lines outside any function

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3906`

bigbrother 0.1.0, checked 7a4a7a614b48...c69f3cc46812
