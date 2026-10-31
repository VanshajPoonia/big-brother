# Complete and fix the Bengali (bn_BD) translation

https://github.com/python-humanize/humanize/pull/471

**no function changed**: no function in the package changed

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_i18n.py passes with and without the change (6 passed, 122 skipped in 0.25s), so it doesn't show the change is tested
- no function in the package's code changed, only lines outside functions or no code at all
- the PR changes 1 test file: tests/test_i18n.py

<details><summary>Tests at the head, with the change: 6 passed, 122 skipped in 0.25s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 56%]
sssssssssssss......sssssssssssssssssssssssssssssssssssss                 [100%]
6 passed, 122 skipped in 0.25s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar eaabd315c963060f0122703c9006f0a75aec8852`
- `docker volume create bb-206c2c795896-deps`
- `docker run --name bb-206c2c795896-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-1upbosao/src,target=/src --mount type=volume,source=bb-206c2c795896-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-2cd51469fcc94651a509661558181a83; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-206c2c795896-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-1upbosao/src,target=/src,readonly --mount type=volume,source=bb-206c2c795896-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-206c2c795896-install bb-206c2c795896-tests`
- `docker volume rm -f bb-206c2c795896-deps`
</details>

<details><summary>Tests at the base, without it: 6 passed, 122 skipped in 0.32s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 56%]
sssssssssssss......sssssssssssssssssssssssssssssssssssss                 [100%]
6 passed, 122 skipped in 0.32s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b`
- `docker volume create bb-cebae6c9b3f9-deps`
- `docker run --name bb-cebae6c9b3f9-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-c9clwx8y/src,target=/src --mount type=volume,source=bb-cebae6c9b3f9-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-ab83e7eb890e40ea9cb370946006d9c2; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-cebae6c9b3f9-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-c9clwx8y/src,target=/src,readonly --mount type=volume,source=bb-cebae6c9b3f9-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-cebae6c9b3f9-install bb-cebae6c9b3f9-tests`
- `docker volume rm -f bb-cebae6c9b3f9-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/471`

bigbrother 0.1.0, checked 785e5dcc0d03...eaabd315c963
