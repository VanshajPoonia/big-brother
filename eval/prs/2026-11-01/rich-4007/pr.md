# Add regression tests for VS16 after zero-width chars in split_graphemes

https://github.com/Textualize/rich/pull/4007

**no function changed**: no function in the package changed

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_cells.py passes with and without the change (69 passed in 0.06s), so it doesn't show the change is tested
- no function in the package's code changed, only lines outside functions or no code at all
- the PR changes 1 test file: tests/test_cells.py

<details><summary>Tests at the head, with the change: 69 passed in 0.06s</summary>

```
.....................................................................    [100%]
69 passed in 0.06s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar f07a3fc5f5f4d5bfc0152cca4b103369934cd8b6`
- `docker volume create bb-4671a3c91d76-deps`
- `docker run --name bb-4671a3c91d76-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-mwpwiuac/src,target=/src --mount type=volume,source=bb-4671a3c91d76-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-f4408bd5540b444fbcacb415b8544ffb; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-4671a3c91d76-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-mwpwiuac/src,target=/src,readonly --mount type=volume,source=bb-4671a3c91d76-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-4671a3c91d76-install bb-4671a3c91d76-tests`
- `docker volume rm -f bb-4671a3c91d76-deps`
</details>

<details><summary>Tests at the base, without it: 69 passed in 0.05s</summary>

```
.....................................................................    [100%]
69 passed in 0.05s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 7338cb9dafd0d0e916585f191ae505b3e602bb51`
- `docker volume create bb-133117bb8fce-deps`
- `docker run --name bb-133117bb8fce-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-skfzuklx/src,target=/src --mount type=volume,source=bb-133117bb8fce-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-912f7bbfaf4342f7bc73c1878aeebf8b; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-133117bb8fce-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-skfzuklx/src,target=/src,readonly --mount type=volume,source=bb-133117bb8fce-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-133117bb8fce-install bb-133117bb8fce-tests`
- `docker volume rm -f bb-133117bb8fce-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4007`

bigbrother 0.1.0, checked 7338cb9dafd0...f07a3fc5f5f4
