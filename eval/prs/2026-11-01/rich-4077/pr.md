# proxy isatty

https://github.com/Textualize/rich/pull/4077

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_file_proxy.py fails without the change (1 failed, 3 passed in 0.14s) and passes with it (4 passed in 0.14s), so the PR's tests check the change
- `FileProxy.isatty` (rich/file_proxy.py:59) changed, and a test this PR adds or changes uses it at tests/test_file_proxy.py:41
- the PR changes 1 test file: tests/test_file_proxy.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `FileProxy.isatty` | [rich/file_proxy.py:59](https://github.com/Textualize/rich/blob/494b795031782c694297d2db78bd04fb8c82f590/rich/file_proxy.py#L59) | in this PR: [tests/test_file_proxy.py:41](https://github.com/Textualize/rich/blob/494b795031782c694297d2db78bd04fb8c82f590/tests/test_file_proxy.py#L41) `"""Check isatty is proxied` |

## Changed outside functions
- rich/file_proxy.py: 1 changed line outside any function

<details><summary>Tests at the head, with the change: 4 passed in 0.14s</summary>

```
....                                                                     [100%]
4 passed in 0.14s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 494b795031782c694297d2db78bd04fb8c82f590`
- `docker volume create bb-fd932c9195e0-deps`
- `docker run --name bb-fd932c9195e0-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-yfaag6yl/src,target=/src --mount type=volume,source=bb-fd932c9195e0-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-0b44afc2cf2f40df8d6eada52d69723c; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-fd932c9195e0-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-yfaag6yl/src,target=/src,readonly --mount type=volume,source=bb-fd932c9195e0-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_file_proxy.py`
- `docker rm -f bb-fd932c9195e0-install bb-fd932c9195e0-tests`
- `docker volume rm -f bb-fd932c9195e0-deps`
</details>

<details><summary>Tests at the base, without it: 1 failed, 3 passed in 0.14s</summary>

```
            def isatty(self) -> bool:
                return True
    
        file = TTYFile()
        console = Console()
        file_proxy = FileProxy(console, file)
>       assert file_proxy.isatty()
E       assert False
E        +  where False = <built-in method isatty of FileProxy object at 0xffffaaa1b7f0>()
E        +    where <built-in method isatty of FileProxy object at 0xffffaaa1b7f0> = <rich.file_proxy.FileProxy object at 0xffffaaa1b7f0>.isatty

tests/test_file_proxy.py:54: AssertionError
=========================== short test summary info ============================
FAILED tests/test_file_proxy.py::test_isatty - assert False
1 failed, 3 passed in 0.14s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 58ac15120fe254886c10d6253667733c83604cb4`
- `docker volume create bb-4cfa80abcb2a-deps`
- `docker run --name bb-4cfa80abcb2a-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-b6cysu87/src,target=/src --mount type=volume,source=bb-4cfa80abcb2a-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-8f6ba74c7c9648f1b57bcda08dad9e17; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-4cfa80abcb2a-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-b6cysu87/src,target=/src,readonly --mount type=volume,source=bb-4cfa80abcb2a-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_file_proxy.py`
- `docker rm -f bb-4cfa80abcb2a-install bb-4cfa80abcb2a-tests`
- `docker volume rm -f bb-4cfa80abcb2a-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4077`

bigbrother 0.1.0, checked 58ac15120fe2...494b79503178
