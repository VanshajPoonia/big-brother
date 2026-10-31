# Use Turkish numeric separators

https://github.com/python-humanize/humanize/pull/465

**no function changed**: no function in the package changed

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_i18n.py passes with and without the change (6 passed, 114 skipped in 0.28s), so it doesn't show the change is tested
- no function in the package's code changed, only lines outside functions or no code at all
- the PR changes 1 test file: tests/test_i18n.py

## Changed outside functions
- src/humanize/i18n.py: 2 changed lines outside any function

<details><summary>Tests at the head, with the change: 6 passed, 114 skipped in 0.28s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 60%]
sssss......sssssssssssssssssssssssssssssssssssss                         [100%]
6 passed, 114 skipped in 0.28s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 3abaf89d733af0d33f2475729b0c75951c1d7058`
- `docker volume create bb-9cd62f44db59-deps`
- `docker run --name bb-9cd62f44db59-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-02shkd0v/src,target=/src --mount type=volume,source=bb-9cd62f44db59-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-69e4b547ad114d45a1636ce12df75b9d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-9cd62f44db59-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-02shkd0v/src,target=/src,readonly --mount type=volume,source=bb-9cd62f44db59-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-9cd62f44db59-install bb-9cd62f44db59-tests`
- `docker volume rm -f bb-9cd62f44db59-deps`
</details>

<details><summary>Tests at the base, without it: 6 passed, 114 skipped in 0.45s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 60%]
sssss......sssssssssssssssssssssssssssssssssssss                         [100%]
6 passed, 114 skipped in 0.45s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b`
- `docker volume create bb-ba2dccba3210-deps`
- `docker run --name bb-ba2dccba3210-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-1ymbeaby/src,target=/src --mount type=volume,source=bb-ba2dccba3210-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-0ba99919e6c748c0a32028b89d0fe6f1; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-ba2dccba3210-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-1ymbeaby/src,target=/src,readonly --mount type=volume,source=bb-ba2dccba3210-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-ba2dccba3210-install bb-ba2dccba3210-tests`
- `docker volume rm -f bb-ba2dccba3210-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/465`

bigbrother 0.1.0, checked 785e5dcc0d03...3abaf89d733a
