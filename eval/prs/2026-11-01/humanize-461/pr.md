# Fix Persian future-time wording and locale metadata

https://github.com/python-humanize/humanize/pull/461

**no function changed**: no function in the package changed

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_i18n.py passes with and without the change (6 passed, 117 skipped in 0.29s), so it doesn't show the change is tested
- no function in the package's code changed, only lines outside functions or no code at all
- the PR changes 1 test file: tests/test_i18n.py

<details><summary>Tests at the head, with the change: 6 passed, 117 skipped in 0.29s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 58%]
ssssssss......sssssssssssssssssssssssssssssssssssss                      [100%]
6 passed, 117 skipped in 0.29s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 470f2d317e36cb6009496d08e1f016dc183dde29`
- `docker volume create bb-da4291404412-deps`
- `docker run --name bb-da4291404412-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-4enqh070/src,target=/src --mount type=volume,source=bb-da4291404412-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-42d97a88f66e4549b5f5c0ef1327f19e; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-da4291404412-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-4enqh070/src,target=/src,readonly --mount type=volume,source=bb-da4291404412-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-da4291404412-install bb-da4291404412-tests`
- `docker volume rm -f bb-da4291404412-deps`
</details>

<details><summary>Tests at the base, without it: 6 passed, 117 skipped in 0.43s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 58%]
ssssssss......sssssssssssssssssssssssssssssssssssss                      [100%]
6 passed, 117 skipped in 0.43s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b`
- `docker volume create bb-887678504c41-deps`
- `docker run --name bb-887678504c41-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-eds0xxqy/src,target=/src --mount type=volume,source=bb-887678504c41-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-c7f559c9567e49b492e0fa35dacb1136; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-887678504c41-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-eds0xxqy/src,target=/src,readonly --mount type=volume,source=bb-887678504c41-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-887678504c41-install bb-887678504c41-tests`
- `docker volume rm -f bb-887678504c41-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/461`

bigbrother 0.1.0, checked 785e5dcc0d03...470f2d317e36
