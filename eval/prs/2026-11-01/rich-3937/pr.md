# don't strip whitespace when soft_wrap is True

https://github.com/Textualize/rich/pull/3937

**partly tested**: some functions this PR changes are used in a test the PR adds or changes, others aren't

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_text.py passes with and without the change (112 passed in 0.20s), so it doesn't show the change is tested
- `Text.__rich_console__` (rich/text.py:689) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_console.py:494, but they were written before this change
- `Text.wrap` (rich/text.py:1201) changed, and a test this PR adds or changes uses it at tests/test_text.py:1100
- the PR changes 1 test file: tests/test_text.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `Text.__rich_console__` | [rich/text.py:689](https://github.com/Textualize/rich/blob/4d0cbb74a8cc5c7dd9af3056499a43efbd13355a/rich/text.py#L689) | older test: [tests/test_console.py:494](https://github.com/Textualize/rich/blob/4d0cbb74a8cc5c7dd9af3056499a43efbd13355a/tests/test_console.py#L494) `def __rich_console__(self, console, options):` |
| `Text.wrap` | [rich/text.py:1201](https://github.com/Textualize/rich/blob/4d0cbb74a8cc5c7dd9af3056499a43efbd13355a/rich/text.py#L1201) | in this PR: [tests/test_text.py:1100](https://github.com/Textualize/rich/blob/4d0cbb74a8cc5c7dd9af3056499a43efbd13355a/tests/test_text.py#L1100) `Soft wrap should not strip trailing whitespace.` |

<details><summary>Tests at the head, with the change: 112 passed in 0.20s</summary>

```
........................................................................ [ 64%]
........................................                                 [100%]
112 passed in 0.20s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 4d0cbb74a8cc5c7dd9af3056499a43efbd13355a`
- `docker volume create bb-f17c83a3b3cc-deps`
- `docker run --name bb-f17c83a3b3cc-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-dm1qviyy/src,target=/src --mount type=volume,source=bb-f17c83a3b3cc-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-d88d713397a54ffc8560fb06532dba60; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-f17c83a3b3cc-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-dm1qviyy/src,target=/src,readonly --mount type=volume,source=bb-f17c83a3b3cc-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_text.py`
- `docker rm -f bb-f17c83a3b3cc-install bb-f17c83a3b3cc-tests`
- `docker volume rm -f bb-f17c83a3b3cc-deps`
</details>

<details><summary>Tests at the base, without it: 112 passed in 0.20s</summary>

```
........................................................................ [ 64%]
........................................                                 [100%]
112 passed in 0.20s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 05a6b9b17a7c778756187f15d6d4bf693db6345f`
- `docker volume create bb-f12f1abecaae-deps`
- `docker run --name bb-f12f1abecaae-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-v250e9uf/src,target=/src --mount type=volume,source=bb-f12f1abecaae-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-076f17b57cfb44e6ad01d52e6921de03; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-f12f1abecaae-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-v250e9uf/src,target=/src,readonly --mount type=volume,source=bb-f12f1abecaae-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_text.py`
- `docker rm -f bb-f12f1abecaae-install bb-f12f1abecaae-tests`
- `docker volume rm -f bb-f12f1abecaae-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3937`

bigbrother 0.1.0, checked 05a6b9b17a7c...4d0cbb74a8cc
