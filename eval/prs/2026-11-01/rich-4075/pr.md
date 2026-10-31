# empty with end

https://github.com/Textualize/rich/pull/4075

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_console.py fails without the change (1 failed, 99 passed in 0.68s) and passes with it (100 passed in 0.61s), so the PR's tests check the change
- `Console.print` (rich/console.py:1652) changed, and a test this PR adds or changes uses it at tests/test_console.py:197
- `Console.save_text` (rich/console.py:2224) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:580, but they were written before this change
- the PR changes 1 test file: tests/test_console.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `Console.print` | [rich/console.py:1652](https://github.com/Textualize/rich/blob/eccb5945ddb8487d655d2ab54f3443d072ef4247/rich/console.py#L1652) | in this PR: [tests/test_console.py:197](https://github.com/Textualize/rich/blob/eccb5945ddb8487d655d2ab54f3443d072ef4247/tests/test_console.py#L197) `console.print(end="!")` |
| `Console.save_text` | [rich/console.py:2224](https://github.com/Textualize/rich/blob/eccb5945ddb8487d655d2ab54f3443d072ef4247/rich/console.py#L2224) | older test: [tests/test_console.py:580](https://github.com/Textualize/rich/blob/eccb5945ddb8487d655d2ab54f3443d072ef4247/tests/test_console.py#L580) `console.save_text(export_path)` |

## Changed outside functions
- rich/console.py: 2 changed lines outside any function

<details><summary>Tests at the head, with the change: 100 passed in 0.61s</summary>

```
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 0.61s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar eccb5945ddb8487d655d2ab54f3443d072ef4247`
- `docker volume create bb-a2396ed0f973-deps`
- `docker run --name bb-a2396ed0f973-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-hklzuct3/src,target=/src --mount type=volume,source=bb-a2396ed0f973-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-c2388e09f8b84e59ac801057587e607d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-a2396ed0f973-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-hklzuct3/src,target=/src,readonly --mount type=volume,source=bb-a2396ed0f973-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_console.py`
- `docker rm -f bb-a2396ed0f973-install bb-a2396ed0f973-tests`
- `docker volume rm -f bb-a2396ed0f973-deps`
</details>

<details><summary>Tests at the base, without it: 1 failed, 99 passed in 0.68s</summary>

```

    def test_print_empty_with_end() -> None:
        console = Console(file=io.StringIO(), color_system="truecolor")
        console.print(end="!")
>       assert console.file.getvalue() == "!"
E       AssertionError: assert '\n' == '!'
E         
E         Strings contain only whitespace, escaping them using repr()
E         - '!'
E         + '\n'

tests/test_console.py:198: AssertionError
=========================== short test summary info ============================
FAILED tests/test_console.py::test_print_empty_with_end - AssertionError: ass...
1 failed, 99 passed in 0.68s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 1fc7cb210ae52eb099df39818ddb9569e5b14c7b`
- `docker volume create bb-b429134e18c6-deps`
- `docker run --name bb-b429134e18c6-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-hicoj81u/src,target=/src --mount type=volume,source=bb-b429134e18c6-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-7539f284229d48f4b15a1abfa177e934; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-b429134e18c6-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-hicoj81u/src,target=/src,readonly --mount type=volume,source=bb-b429134e18c6-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_console.py`
- `docker rm -f bb-b429134e18c6-install bb-b429134e18c6-tests`
- `docker volume rm -f bb-b429134e18c6-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4075`

bigbrother 0.1.0, checked 1fc7cb210ae5...eccb5945ddb8
