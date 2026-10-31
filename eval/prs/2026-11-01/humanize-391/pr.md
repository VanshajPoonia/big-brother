# Fix translation loss during catalog updates

https://github.com/python-humanize/humanize/pull/391

**partly tested**: some functions this PR changes are used in a test the PR adds or changes, others aren't

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_i18n.py passes with and without the change (6 passed, 112 skipped in 0.35s), so it doesn't show the change is tested
- `_pgettext_noop` (src/humanize/i18n.py:182) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- `ordinal` (src/humanize/number.py:93) changed, and a test this PR adds or changes uses it at tests/test_i18n.py:60
- the PR changes 1 test file: tests/test_i18n.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `_pgettext_noop` | [src/humanize/i18n.py:182](https://github.com/python-humanize/humanize/blob/fd6236be6c7498042cd2ce9ce16c890252f7e2fc/src/humanize/i18n.py#L182) | none |
| `ordinal` | [src/humanize/number.py:93](https://github.com/python-humanize/humanize/blob/fd6236be6c7498042cd2ce9ce16c890252f7e2fc/src/humanize/number.py#L93) | in this PR: [tests/test_i18n.py:60](https://github.com/python-humanize/humanize/blob/fd6236be6c7498042cd2ce9ce16c890252f7e2fc/tests/test_i18n.py#L60) `humanize.ordinal(value, gender=gender)` |

## Changed outside functions
- src/humanize/i18n.py: 2 changed lines outside any function
- src/humanize/number.py: 38 changed lines outside any function

<details><summary>Tests at the head, with the change: 6 passed, 112 skipped in 0.35s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 61%]
sss......sssssssssssssssssssssssssssssssssssss                           [100%]
6 passed, 112 skipped in 0.35s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar fd6236be6c7498042cd2ce9ce16c890252f7e2fc`
- `docker volume create bb-59866cd0a6e1-deps`
- `docker run --name bb-59866cd0a6e1-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-fvvgskrz/src,target=/src --mount type=volume,source=bb-59866cd0a6e1-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-329590ba0c83464aa854460d80926632; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-59866cd0a6e1-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-fvvgskrz/src,target=/src,readonly --mount type=volume,source=bb-59866cd0a6e1-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-59866cd0a6e1-install bb-59866cd0a6e1-tests`
- `docker volume rm -f bb-59866cd0a6e1-deps`
</details>

<details><summary>Tests at the base, without it: 6 passed, 112 skipped in 0.35s</summary>

```
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 61%]
sss......sssssssssssssssssssssssssssssssssssss                           [100%]
6 passed, 112 skipped in 0.35s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar e46732ed235019682b7bfc6c44443e247b332e95`
- `docker volume create bb-60a026868527-deps`
- `docker run --name bb-60a026868527-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-bu9xxfz9/src,target=/src --mount type=volume,source=bb-60a026868527-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-9d7e5b6240ee4f3ab3b8e94cb6a425b7; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-60a026868527-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-bu9xxfz9/src,target=/src,readonly --mount type=volume,source=bb-60a026868527-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_i18n.py`
- `docker rm -f bb-60a026868527-install bb-60a026868527-tests`
- `docker volume rm -f bb-60a026868527-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/391`

bigbrother 0.1.0, checked e46732ed2350...fd6236be6c74
