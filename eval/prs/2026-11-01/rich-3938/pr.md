# fix background style with soft wrap

https://github.com/Textualize/rich/pull/3938

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_segment.py, tests/test_text.py fail without the change (3 failed, 171 passed in 0.26s) and pass with it (174 passed in 0.24s), so the PR's tests check the change
- `Console.print` (rich/console.py:1648) changed, and a test this PR adds or changes uses it at tests/test_text.py:1122
- `Segment.split_lines_terminator` (rich/segment.py:279) changed, and a test this PR adds or changes uses it at tests/test_segment.py:39
- `Segment.split_and_crop_lines` (rich/segment.py:310) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_segment.py:54, but they were written before this change
- the PR changes 2 test files: tests/test_segment.py, tests/test_text.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `Console.print` | [rich/console.py:1648](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/rich/console.py#L1648) | in this PR: [tests/test_text.py:1122](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/tests/test_text.py#L1122) `console.print("soft wrap is on", style="blue on white", soft_wrap=True)` |
| `Segment.split_lines_terminator` | [rich/segment.py:279](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/rich/segment.py#L279) | in this PR: [tests/test_segment.py:39](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/tests/test_segment.py#L39) `assert list(Segment.split_lines_terminator(lines)) == [` |
| `Segment.split_and_crop_lines` | [rich/segment.py:310](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/rich/segment.py#L310) | older test: [tests/test_segment.py:54](https://github.com/Textualize/rich/blob/2c247e6da72dfa69dd6148f1a0657e2440d1ebe9/tests/test_segment.py#L54) `Segment.split_and_crop_lines([Segment("Hello\nWorld!\n"), Segment("foo")], 4)` |

## Changed outside functions
- rich/segment.py: 1 changed line outside any function

<details><summary>Tests at the head, with the change: 174 passed in 0.24s</summary>

```
........................................................................ [ 41%]
........................................................................ [ 82%]
..............................                                           [100%]
174 passed in 0.24s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 2c247e6da72dfa69dd6148f1a0657e2440d1ebe9`
- `docker volume create bb-14f5f55f905c-deps`
- `docker run --name bb-14f5f55f905c-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-qacrdh3x/src,target=/src --mount type=volume,source=bb-14f5f55f905c-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-f4d2fe9d7ab3423a9d2454be0fb9fc54; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-14f5f55f905c-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-qacrdh3x/src,target=/src,readonly --mount type=volume,source=bb-14f5f55f905c-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_segment.py tests/test_text.py`
- `docker rm -f bb-14f5f55f905c-install bb-14f5f55f905c-tests`
- `docker volume rm -f bb-14f5f55f905c-deps`
</details>

<details><summary>Tests at the base, without it: 3 failed, 171 passed in 0.26s</summary>

```
E         - [34;47msoft wrap is on[0m
E         + [34;47msoft wrap is on[0m[34;47m
E         ?                            ++++++++
E         - Next line
E         + [0mNext line
E         ? ++++

tests/test_text.py:1129: AssertionError
----------------------------- Captured stdout call -----------------------------
'\x1b[34;47msoft wrap is on\x1b[0m\x1b[34;47m\n\x1b[0mNext line\n'
=========================== short test summary info ============================
FAILED tests/test_segment.py::test_split_lines_terminator - AttributeError: t...
FAILED tests/test_segment.py::test_split_lines_terminator_single_line - Attri...
FAILED tests/test_text.py::test_soft_wrap_styled - AssertionError: assert '\x...
3 failed, 171 passed in 0.26s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 05ff970926cbd0b5d0acb6fc18cdbd1fc971e582`
- `docker volume create bb-eb20a017934e-deps`
- `docker run --name bb-eb20a017934e-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-emofrxfg/src,target=/src --mount type=volume,source=bb-eb20a017934e-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-bd36de92c32f4d028263b0eee3005d53; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-eb20a017934e-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-emofrxfg/src,target=/src,readonly --mount type=volume,source=bb-eb20a017934e-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_segment.py tests/test_text.py`
- `docker rm -f bb-eb20a017934e-install bb-eb20a017934e-tests`
- `docker volume rm -f bb-eb20a017934e-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3938`

bigbrother 0.1.0, checked 05ff970926cb...2c247e6da72d
