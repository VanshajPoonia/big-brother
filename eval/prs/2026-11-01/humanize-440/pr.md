# Drop support for EOL Python 3.10

https://github.com/python-humanize/humanize/pull/440

**partly tested**: some functions this PR changes are used in a test the PR adds or changes, others aren't

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_filesize.py, tests/test_i18n.py, tests/test_time.py pass with and without the change (474 passed, 112 skipped in 1.09s), so they don't show the change is tested
- `_now` (src/humanize/time.py:49) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- `_convert_aware_datetime` (src/humanize/time.py:314) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- `naturalday` (src/humanize/time.py:328) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_benchmarks.py:21, but they were written before this change
- `naturaldate` (src/humanize/time.py:366) changed, and a test this PR adds or changes uses it at tests/test_time.py:329
- the PR changes 3 test files: tests/test_filesize.py, tests/test_i18n.py, tests/test_time.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `_now` | [src/humanize/time.py:49](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/src/humanize/time.py#L49) | none |
| `_convert_aware_datetime` | [src/humanize/time.py:314](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/src/humanize/time.py#L314) | none |
| `naturalday` | [src/humanize/time.py:328](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/src/humanize/time.py#L328) | older test: [tests/test_benchmarks.py:21](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/tests/test_benchmarks.py#L21) `humanize.naturalday(dt.date.today())` |
| `naturaldate` | [src/humanize/time.py:366](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/src/humanize/time.py#L366) | in this PR: [tests/test_time.py:329](https://github.com/python-humanize/humanize/blob/8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2/tests/test_time.py#L329) `"""naturaldate should compare dates in the timezone of the given value."""` |

<details><summary>Tests at the head, with the change: 474 passed, 112 skipped in 1.09s</summary>

```
........................................................................ [ 12%]
....ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 24%]
sssssss......sssssssssssssssssssssssssssssssssssss...................... [ 36%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 73%]
........................................................................ [ 86%]
........................................................................ [ 98%]
..........                                                               [100%]
474 passed, 112 skipped in 1.09s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 8bf85bbcbf3a9086639fdfa3faa0f269e99a63d2`
- `docker volume create bb-b1f07616e595-deps`
- `docker run --name bb-b1f07616e595-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-p5nupgyv/src,target=/src --mount type=volume,source=bb-b1f07616e595-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-41adce7d6c144e33896cebc1557c9253; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-b1f07616e595-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-p5nupgyv/src,target=/src,readonly --mount type=volume,source=bb-b1f07616e595-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_filesize.py tests/test_i18n.py tests/test_time.py`
- `docker rm -f bb-b1f07616e595-install bb-b1f07616e595-tests`
- `docker volume rm -f bb-b1f07616e595-deps`
</details>

<details><summary>Tests at the base, without it: 474 passed, 112 skipped in 1.08s</summary>

```
........................................................................ [ 12%]
....ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 24%]
sssssss......sssssssssssssssssssssssssssssssssssss...................... [ 36%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 73%]
........................................................................ [ 86%]
........................................................................ [ 98%]
..........                                                               [100%]
474 passed, 112 skipped in 1.08s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 1a04966d8dcc1a0b99154cd4e19130d0af58846b`
- `docker volume create bb-aa04d8d245cb-deps`
- `docker run --name bb-aa04d8d245cb-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-ad6lw_kw/src,target=/src --mount type=volume,source=bb-aa04d8d245cb-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-f7a41e0f06b24ab29c98a3fefc906855; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-aa04d8d245cb-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-ad6lw_kw/src,target=/src,readonly --mount type=volume,source=bb-aa04d8d245cb-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_filesize.py tests/test_i18n.py tests/test_time.py`
- `docker rm -f bb-aa04d8d245cb-install bb-aa04d8d245cb-tests`
- `docker volume rm -f bb-aa04d8d245cb-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/440`

bigbrother 0.1.0, checked 1a04966d8dcc...8bf85bbcbf3a
