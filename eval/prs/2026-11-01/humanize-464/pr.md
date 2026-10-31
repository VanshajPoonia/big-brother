# Translate byte-size labels into Persian

https://github.com/python-humanize/humanize/pull/464

**no function changed**: no function in the package changed

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_i18n.py passes with and without the change (6 passed, 117 skipped in 0.35s), so it doesn't show the change is tested
- no function in the package's code changed, only lines outside functions or no code at all
- the PR changes 1 test file: tests/test_i18n.py

<details><summary>Tests at the head, with the change: 6 passed, 117 skipped in 0.35s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 58%]
ssssssss......sssssssssssssssssssssssssssssssssssss                      [100%]
6 passed, 117 skipped in 0.35s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 5d6f5ed9f34c5bbb400ee7c75160a82030e40b21`
- `docker volume create bb-e45638070013-deps`
- `docker run --name bb-e45638070013-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-c5sge790/src,target=/src --mount type=volume,source=bb-e45638070013-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-282736625039431aac850434458e14b4; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-e45638070013-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-c5sge790/src,target=/src,readonly --mount type=volume,source=bb-e45638070013-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-e45638070013-install bb-e45638070013-tests`
- `docker volume rm -f bb-e45638070013-deps`
</details>

<details><summary>Tests at the base, without it: 6 passed, 117 skipped in 0.38s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 58%]
ssssssss......sssssssssssssssssssssssssssssssssssss                      [100%]
6 passed, 117 skipped in 0.38s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b`
- `docker volume create bb-66e4dae8cdae-deps`
- `docker run --name bb-66e4dae8cdae-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-j2xzaz3l/src,target=/src --mount type=volume,source=bb-66e4dae8cdae-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-ab3b1fdda56e4041b83fa83bd1ab3047; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-66e4dae8cdae-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-j2xzaz3l/src,target=/src,readonly --mount type=volume,source=bb-66e4dae8cdae-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-66e4dae8cdae-install bb-66e4dae8cdae-tests`
- `docker volume rm -f bb-66e4dae8cdae-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/464`

bigbrother 0.1.0, checked 785e5dcc0d03...5d6f5ed9f34c
