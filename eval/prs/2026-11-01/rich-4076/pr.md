# preserve newlines

https://github.com/Textualize/rich/pull/4076

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_ansi.py fails without the change (4 failed, 20 passed in 0.14s) and passes with it (24 passed in 0.11s), so the PR's tests check the change
- `AnsiDecoder.decode` (rich/ansi.py:126) changed, and a test this PR adds or changes uses it at tests/test_ansi.py:22
- the PR changes 1 test file: tests/test_ansi.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `AnsiDecoder.decode` | [rich/ansi.py:126](https://github.com/Textualize/rich/blob/48293cde887c4f25a7bca022131b56495f370a88/rich/ansi.py#L126) | in this PR: [tests/test_ansi.py:22](https://github.com/Textualize/rich/blob/48293cde887c4f25a7bca022131b56495f370a88/tests/test_ansi.py#L22) `lines = list(decoder.decode(terminal_codes))` |

<details><summary>Tests at the head, with the change: 24 passed in 0.11s</summary>

```
........................                                                 [100%]
24 passed in 0.11s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 48293cde887c4f25a7bca022131b56495f370a88`
- `docker volume create bb-23eecc382197-deps`
- `docker run --name bb-23eecc382197-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-alw5i21y/src,target=/src --mount type=volume,source=bb-23eecc382197-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-750afb24f3424b8da7442605bbc0db00; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-23eecc382197-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-alw5i21y/src,target=/src,readonly --mount type=volume,source=bb-23eecc382197-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_ansi.py`
- `docker rm -f bb-23eecc382197-install bb-23eecc382197-tests`
- `docker volume rm -f bb-23eecc382197-deps`
</details>

<details><summary>Tests at the base, without it: 4 failed, 20 passed in 0.14s</summary>

```
        assert Text.from_ansi("").plain == ""
>       assert Text.from_ansi("\n").plain == "\n"
E       AssertionError: assert '' == '\n'
E         
E         Strings contain only whitespace, escaping them using repr()
E         - '\n'
E         + ''

tests/test_ansi.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_ansi.py::test_decode - AssertionError: assert [<text 'Hello...
FAILED tests/test_ansi.py::test_decode_example - AssertionError: assert '\x1b...
FAILED tests/test_ansi.py::test_decode_issue_2688[\x1b[31mFound 4 errors in 2 files (checked 18 source files)\x1b(B\x1b[m\n-Found 4 errors in 2 files (checked 18 source files)\n]
FAILED tests/test_ansi.py::test_decode_newlines - AssertionError: assert '' =...
4 failed, 20 passed in 0.14s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 9cb198944f8184df92217efc8b20d3fffa4b4fa0`
- `docker volume create bb-1159a8a9cffb-deps`
- `docker run --name bb-1159a8a9cffb-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-orjodnlf/src,target=/src --mount type=volume,source=bb-1159a8a9cffb-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-85eb16d2002c4a20b4648430a2fc967a; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-1159a8a9cffb-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-orjodnlf/src,target=/src,readonly --mount type=volume,source=bb-1159a8a9cffb-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_ansi.py`
- `docker rm -f bb-1159a8a9cffb-install bb-1159a8a9cffb-tests`
- `docker volume rm -f bb-1159a8a9cffb-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4076`

bigbrother 0.1.0, checked 9cb198944f81...48293cde887c
