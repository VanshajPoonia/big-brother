# perf: reduce Console and RichHandler import time by deferring unused imports

https://github.com/Textualize/rich/pull/4070

**partly tested**: some functions this PR changes are used in a test the PR adds or changes, others aren't

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_console.py, tests/test_syntax.py fail at the PR's head in the sandbox (6 failed, 118 passed in 0.91s). That can be the PR, or a dependency version different from the project's own CI, so it doesn't decide the label
- `_emoji_replace` (rich/_emoji_replace.py:9) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- `Console.render` (rich/console.py:1293) changed, and no test this PR adds or changes uses it. Older tests do, like tests/render.py:10, but they were written before this change
- `Console._collect_renderables` (rich/console.py:1499) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- `Console._caller_frame_info` (rich/console.py:1905) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_log.py:49, but they were written before this change
- `Console.log` (rich/console.py:1943) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:282, but they were written before this change
- `Console.input` (rich/console.py:2152) changed, and a test this PR adds or changes uses it at tests/test_console.py:407
- `Console.export_html` (rich/console.py:2234) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:516, but they were written before this change
- `Console.export_svg` (rich/console.py:2342) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:539, but they were written before this change
- `Emoji.__init__` (rich/emoji.py:25) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_emoji.py:10, but they were written before this change
- `RichHandler.emit` (rich/logging.py:138) changed, and no test uses it at all
- `RichHandler.render_message` (rich/logging.py:190) changed, and no test uses it at all
- `RichHandler.render` (rich/logging.py:215) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_logging.py:55, but they were written before this change
- `rich_cast` (rich/protocol.py:18) changed, and no test uses it at all
- `auto` (rich/repr.py:36) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:128, but they were written before this change
- `Theme.from_file` (rich/theme.py:38) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_theme.py:29, but they were written before this change
- the PR changes 2 test files: tests/test_console.py, tests/test_syntax.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `_emoji_replace` | [rich/_emoji_replace.py:9](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/_emoji_replace.py#L9) | none |
| `Console.render` | [rich/console.py:1293](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L1293) | older test: [tests/render.py:10](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/render.py#L10) `def replace_link_ids(render: str) -> str:` |
| `Console._collect_renderables` | [rich/console.py:1499](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L1499) | none |
| `Console._caller_frame_info` | [rich/console.py:1905](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L1905) | older test: [tests/test_log.py:49](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_log.py#L49) `assert Console._caller_frame_info(i) == Console._caller_frame_info(` |
| `Console.log` | [rich/console.py:1943](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L1943) | older test: [tests/test_console.py:282](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_console.py#L282) `console.log("foo", style="red")` |
| `Console.input` | [rich/console.py:2152](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L2152) | in this PR: [tests/test_console.py:407](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_console.py#L407) `user_input = console.input(prompt="foo:", password=True)` |
| `Console.export_html` | [rich/console.py:2234](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L2234) | older test: [tests/test_console.py:516](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_console.py#L516) `html = console.export_html()` |
| `Console.export_svg` | [rich/console.py:2342](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/console.py#L2342) | older test: [tests/test_console.py:539](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_console.py#L539) `svg = console.export_svg()` |
| `Emoji.__init__` | [rich/emoji.py:25](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/emoji.py#L25) | older test: [tests/test_emoji.py:10](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_emoji.py#L10) `Emoji("ambivalent_bunny")` |
| `RichHandler.emit` | [rich/logging.py:138](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/logging.py#L138) | none |
| `RichHandler.render_message` | [rich/logging.py:190](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/logging.py#L190) | none |
| `RichHandler.render` | [rich/logging.py:215](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/logging.py#L215) | older test: [tests/test_logging.py:55](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_logging.py#L55) `render = handler_with_tracebacks.console.file.getvalue()` |
| `rich_cast` | [rich/protocol.py:18](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/protocol.py#L18) | none |
| `auto` | [rich/repr.py:36](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/repr.py#L36) | older test: [tests/test_console.py:128](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_console.py#L128) `console = Console(color_system="auto")` |
| `Theme.from_file` | [rich/theme.py:38](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/rich/theme.py#L38) | older test: [tests/test_theme.py:29](https://github.com/Textualize/rich/blob/6729c6f6c4ee24a13a94d825cb7ce66b52206db2/tests/test_theme.py#L29) `load_theme = Theme.from_file(text_file)` |

## Changed outside functions
- rich/_emoji_replace.py: 2 changed lines outside any function
- rich/console.py: 6 changed lines outside any function
- rich/emoji.py: 7 changed lines outside any function
- rich/logging.py: 14 changed lines outside any function
- rich/protocol.py: 1 changed line outside any function
- rich/repr.py: 1 changed line outside any function
- rich/segment.py: 2 changed lines outside any function
- rich/syntax.py: 5 changed lines outside any function
- rich/theme.py: 1 changed line outside any function

<details><summary>Tests at the head, with the change: 6 failed, 118 passed in 0.91s</summary>

```
E         ?           ^^^^^^^^^^^                                                                              ...
E         
E         ...Full output truncated, use '-vv' to show

tests/test_syntax.py:302: AssertionError
----------------------------- Captured stdout call -----------------------------
'\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 1 \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34md\x1b[0m\x1b[53;38;2;102;217;239;48;2;39;40;34me\x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mf\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;166;226;46;48;2;39;40;34mloop_\x1b[0m\x1b[4;38;2;166;226;46;48;2;39;40;34mfirst\x1b[0m\x1b[1;4;38;2;166;226;46;48;2;39;40;34m_last\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m(\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mvalues\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m:\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mIterable\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m[\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mT\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m]\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m)\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;255;70;137;48;2;39;40;34m-\x1b[0m\x1b[1;38;2;255;70;137;48;2;39;40;34m>\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mIterable\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m[\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mTuple\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m[\x1b[0m\x1b[1;38;2;166;226;46;48;2;39;40;34mbool\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;166;226;46;48;2;39;40;34mbool\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mT\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m]\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m]\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m:\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 2 \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[1;38;2;230;219;116;48;2;39;40;34m"""Iterate and generate a tuple with a flag for first and last value."""\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 3 \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34miter_values\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;255;70;137;48;2;39;40;34m=\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;166;226;46;48;2;39;40;34miter\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m(\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mvalues\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m)\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 4 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mtry\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m:\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 5 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m        \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mprevious_value\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;255;70;137;48;2;39;40;34m=\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;166;226;46;48;2;39;40;34mnext\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m(\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34miter_values\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m)\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 6 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mexcept\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[7;38;2;166;226;46;48;2;39;40;34mStopIteration\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m:\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 7 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m        \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mreturn\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 8 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mfirst\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;255;70;137;48;2;39;40;34m=\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mTrue\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m 9 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mfor\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[9;38;2;248;248;242;48;2;39;40;34mvalue\x1b[0m\x1b[9;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[9;38;2;255;70;137;48;2;39;40;34min\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34miter_values\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m:\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m10 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m        \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34myield\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mfirst\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;102;217;239;48;2;39;40;34mFalse\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[1;38;2;248;248;242;48;2;39;40;34mprevious_value\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m11 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m        \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mfirst\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;255;70;137;48;2;39;40;34m=\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mFalse\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m12 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m        \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mprevious_value\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;255;70;137;48;2;39;40;34m=\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mvalue\x1b[0m\n\x1b[1;38;2;227;227;221;48;2;39;40;34m  \x1b[0m\x1b[38;2;101;102;96;48;2;39;40;34m13 \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m    \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34myield\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mfirst\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;102;217;239;48;2;39;40;34mTrue\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m,\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mprevious_value\x1b[0m\n'
=========================== short test summary info ============================
FAILED tests/test_syntax.py::test_python_render - AssertionError: assert '╭──...
FAILED tests/test_syntax.py::test_python_render_simple - assert '\x1b[38;2;10...
FAILED tests/test_syntax.py::test_python_render_simple_passing_lexer_instance
FAILED tests/test_syntax.py::test_python_render_indent_guides - AssertionErro...
FAILED tests/test_syntax.py::test_option_no_wrap - AssertionError: assert '\x...
FAILED tests/test_syntax.py::test_syntax_highlight_ranges - AssertionError: a...
6 failed, 118 passed in 0.91s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 6729c6f6c4ee24a13a94d825cb7ce66b52206db2`
- `docker volume create bb-d4a54fdccb40-deps`
- `docker run --name bb-d4a54fdccb40-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-zix944be/src,target=/src --mount type=volume,source=bb-d4a54fdccb40-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-656aaab58766454998ea892bf1af95dc; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-d4a54fdccb40-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-zix944be/src,target=/src,readonly --mount type=volume,source=bb-d4a54fdccb40-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_console.py tests/test_syntax.py`
- `docker rm -f bb-d4a54fdccb40-install bb-d4a54fdccb40-tests`
- `docker volume rm -f bb-d4a54fdccb40-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4070`

bigbrother 0.1.0, checked fc41075a3206...6729c6f6c4ee
