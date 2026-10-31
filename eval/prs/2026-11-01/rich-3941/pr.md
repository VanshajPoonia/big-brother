# Fix typing for save_html, save_text, save_svg to accept PathLike

https://github.com/Textualize/rich/pull/3941

**no test for this change**: no test the PR adds or changes uses a function it changes

No model: this comes from the PR's diff and the tests at its head.

## Why
- `Console.save_text` (rich/console.py:2210) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:574, but they were written before this change
- `Console.save_html` (rich/console.py:2299) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:585, but they were written before this change
- `Console.save_svg` (rich/console.py:2581) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:564, but they were written before this change
- the PR changes 0 test files

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `Console.save_text` | [rich/console.py:2210](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/rich/console.py#L2210) | older test: [tests/test_console.py:574](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/tests/test_console.py#L574) `console.save_text(export_path)` |
| `Console.save_html` | [rich/console.py:2299](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/rich/console.py#L2299) | older test: [tests/test_console.py:585](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/tests/test_console.py#L585) `console.save_html(export_path)` |
| `Console.save_svg` | [rich/console.py:2581](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/rich/console.py#L2581) | older test: [tests/test_console.py:564](https://github.com/Textualize/rich/blob/31ce129a915bab47fa7ddc8e15af77480666fefe/tests/test_console.py#L564) `console.save_svg(export_path)` |

## Changed outside functions
- rich/console.py: 1 changed line outside any function

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3941`

bigbrother 0.1.0, checked c595fa95068d...31ce129a915b
