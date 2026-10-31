# Update to markdown styles

https://github.com/Textualize/rich/pull/3942

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_markdown.py, tests/test_markdown_no_hyperlinks.py fail without the change (6 failed, 2 passed in 0.18s) and pass with it (8 passed in 0.16s), so the PR's tests check the change
- `Heading.__rich_console__` (rich/markdown.py:158) changed, and no test uses it at all
- `HorizontalRule.__rich_console__` (rich/markdown.py:223) changed, and no test uses it at all
- `TableElement.__rich_console__` (rich/markdown.py:247) changed, and no test uses it at all
- the PR changes 3 test files: tests/_card_render.py, tests/test_markdown.py, tests/test_markdown_no_hyperlinks.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `Heading.__rich_console__` | [rich/markdown.py:158](https://github.com/Textualize/rich/blob/97b5beacc3d9c1336d4bc6a3d69fec363bfe5d2c/rich/markdown.py#L158) | none |
| `HorizontalRule.__rich_console__` | [rich/markdown.py:223](https://github.com/Textualize/rich/blob/97b5beacc3d9c1336d4bc6a3d69fec363bfe5d2c/rich/markdown.py#L223) | none |
| `TableElement.__rich_console__` | [rich/markdown.py:247](https://github.com/Textualize/rich/blob/97b5beacc3d9c1336d4bc6a3d69fec363bfe5d2c/rich/markdown.py#L247) | none |

## Changed outside functions
- rich/default_styles.py: 11 changed lines outside any function
- rich/markdown.py: 17 changed lines outside any function

<details><summary>Tests at the head, with the change: 8 passed in 0.16s</summary>

```
........                                                                 [100%]
8 passed in 0.16s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 97b5beacc3d9c1336d4bc6a3d69fec363bfe5d2c`
- `docker volume create bb-41c490dcbfe3-deps`
- `docker run --name bb-41c490dcbfe3-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-nh5hzakq/src,target=/src --mount type=volume,source=bb-41c490dcbfe3-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-2b49f9217b3546b2b34dc85c6ece0b0e; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-41c490dcbfe3-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-nh5hzakq/src,target=/src,readonly --mount type=volume,source=bb-41c490dcbfe3-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_markdown.py tests/test_markdown_no_hyperlinks.py`
- `docker rm -f bb-41c490dcbfe3-install bb-41c490dcbfe3-tests`
- `docker volume rm -f bb-41c490dcbfe3-deps`
</details>

<details><summary>Tests at the base, without it: 6 failed, 2 passed in 0.18s</summary>

```
E         + ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━...
E         
E         ...Full output truncated, use '-vv' to show

tests/test_markdown_no_hyperlinks.py:97: AssertionError
----------------------------- Captured stdout call -----------------------------
'┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n┃                                             \x1b[1mHeading\x1b[0m                                              ┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n\n                                            \x1b[1;4mSub-heading\x1b[0m                                             \n\n                                              \x1b[1mHeading\x1b[0m                                               \n\n                                             \x1b[1;2mH4 Heading\x1b[0m                                             \n\n                                             \x1b[4mH5 Heading\x1b[0m                                             \n\n                                             \x1b[3mH6 Heading\x1b[0m                                             \n\nParagraphs are separated by a blank line.                                                           \n\nTwo spaces at the end of a line produces a line break.                                              \n\nText attributes \x1b[3mitalic\x1b[0m, \x1b[1mbold\x1b[0m, \x1b[1;36;40mmonospace\x1b[0m.                                                            \n\nHorizontal rule:                                                                                    \n\n\x1b[33m────────────────────────────────────────────────────────────────────────────────────────────────────\x1b[0m\nBullet list:                                                                                        \n\n\x1b[1;33m • \x1b[0mapples                                                                                           \n\x1b[1;33m • \x1b[0moranges                                                                                          \n\x1b[1;33m • \x1b[0mpears                                                                                            \n\nNumbered list:                                                                                      \n\n\x1b[1;33m 1 \x1b[0mlather                                                                                           \n\x1b[1;33m 2 \x1b[0mrinse                                                                                            \n\x1b[1;33m 3 \x1b[0mrepeat                                                                                           \n\nAn \x1b[94mexample\x1b[0m (\x1b[4;34mhttp://example.com\x1b[0m).                                                                    \n\n\x1b[35m▌ \x1b[0m\x1b[35mMarkdown uses email-style > characters for blockquoting.\x1b[0m\x1b[35m                                        \x1b[0m\n\x1b[35m▌ \x1b[0m\x1b[35mLorem ipsum\x1b[0m\x1b[35m                                                                                     \x1b[0m\n\n🌆 progress                                                                                         \n\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n\x1b[48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34ma=1\x1b[0m\x1b[48;2;39;40;34m                                                                                               \x1b[0m\x1b[48;2;39;40;34m \x1b[0m\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n\x1b[48;2;39;40;34m \x1b[0m\x1b[38;2;255;70;137;48;2;39;40;34mimport\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mthis\x1b[0m\x1b[48;2;39;40;34m                                                                                       \x1b[0m\x1b[48;2;39;40;34m \x1b[0m\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n\x1b[48;2;39;40;34m \x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34mfoobar\x1b[0m\x1b[48;2;39;40;34m                                                                                            \x1b[0m\x1b[48;2;39;40;34m \x1b[0m\n\x1b[48;2;39;40;34m                                                                                                    \x1b[0m\n'
=========================== short test summary info ============================
FAILED tests/test_markdown.py::test_markdown_render - AssertionError: assert ...
FAILED tests/test_markdown.py::test_markdown_table - AssertionError: assert '...
FAILED tests/test_markdown.py::test_inline_styles_in_table - AssertionError: ...
FAILED tests/test_markdown.py::test_inline_styles_with_justification - Assert...
FAILED tests/test_markdown.py::test_partial_table - AssertionError: assert '\...
FAILED tests/test_markdown_no_hyperlinks.py::test_markdown_render - Assertion...
6 failed, 2 passed in 0.18s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar c595fa95068dd2c5095d25446b2f0571bc0b3995`
- `docker volume create bb-f67dcb82c1bb-deps`
- `docker run --name bb-f67dcb82c1bb-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-ok_gzkqy/src,target=/src --mount type=volume,source=bb-f67dcb82c1bb-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-516aef82f3614e76aad69683cb35b30b; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-f67dcb82c1bb-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-ok_gzkqy/src,target=/src,readonly --mount type=volume,source=bb-f67dcb82c1bb-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_markdown.py tests/test_markdown_no_hyperlinks.py`
- `docker rm -f bb-f67dcb82c1bb-install bb-f67dcb82c1bb-tests`
- `docker volume rm -f bb-f67dcb82c1bb-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3942`

bigbrother 0.1.0, checked c595fa95068d...97b5beacc3d9
