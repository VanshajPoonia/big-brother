# fix for infinite loop in split_graphemes

https://github.com/Textualize/rich/pull/4006

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_cells.py passes at the PR's head (67 passed in 0.08s), but couldn't run at the base: the tests timed out
- `split_graphemes` (rich/cells.py:161) changed, and a test this PR adds or changes uses it at tests/test_cells.py:217
- the PR changes 1 test file: tests/test_cells.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `split_graphemes` | [rich/cells.py:161](https://github.com/Textualize/rich/blob/905b397deb6b5ed59dfd80fa499c90e215f309c8/rich/cells.py#L161) | in this PR: [tests/test_cells.py:217](https://github.com/Textualize/rich/blob/905b397deb6b5ed59dfd80fa499c90e215f309c8/tests/test_cells.py#L217) `spans, cell_length = split_graphemes(text)` |

<details><summary>Tests at the head, with the change: 67 passed in 0.08s</summary>

```
...................................................................      [100%]
67 passed in 0.08s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 905b397deb6b5ed59dfd80fa499c90e215f309c8`
- `docker volume create bb-2de850a6f657-deps`
- `docker run --name bb-2de850a6f657-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-blmrqpic/src,target=/src --mount type=volume,source=bb-2de850a6f657-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-57643c8e3c6545c5b060a035e6433d8a; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-2de850a6f657-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-blmrqpic/src,target=/src,readonly --mount type=volume,source=bb-2de850a6f657-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-2de850a6f657-install bb-2de850a6f657-tests`
- `docker volume rm -f bb-2de850a6f657-deps`
</details>

<details><summary>Tests at the base, without it: the tests timed out</summary>

```
the tests ran longer than 180 seconds
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 27701029082052c6541031b6f139097230253900`
- `docker volume create bb-144fb03bf3ff-deps`
- `docker run --name bb-144fb03bf3ff-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-ixu388dm/src,target=/src --mount type=volume,source=bb-144fb03bf3ff-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-9be99a058c194fe6af22a0769a16d5c8; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-144fb03bf3ff-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-ixu388dm/src,target=/src,readonly --mount type=volume,source=bb-144fb03bf3ff-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker kill bb-144fb03bf3ff-tests`
- `docker rm -f bb-144fb03bf3ff-install bb-144fb03bf3ff-tests`
- `docker volume rm -f bb-144fb03bf3ff-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4006`

bigbrother 0.1.0, checked 277010290820...905b397deb6b
