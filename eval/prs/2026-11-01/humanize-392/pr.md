# Fix intcomma overflow for large Python integers

https://github.com/python-humanize/humanize/pull/392

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_number.py fails without the change (2 failed, 232 passed in 0.15s) and passes with it (234 passed in 0.13s), so the PR's tests check the change
- `intcomma` (src/humanize/number.py:116) changed, and a test this PR adds or changes uses it at tests/test_number.py:90
- the PR changes 1 test file: tests/test_number.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `intcomma` | [src/humanize/number.py:116](https://github.com/python-humanize/humanize/blob/244ac0ed6baeb3d1789be61e1a0f8ef962e716f4/src/humanize/number.py#L116) | in this PR: [tests/test_number.py:90](https://github.com/python-humanize/humanize/blob/244ac0ed6baeb3d1789be61e1a0f8ef962e716f4/tests/test_number.py#L90) `assert humanize.intcomma(value) == expected` |

<details><summary>Tests at the head, with the change: 234 passed in 0.13s</summary>

```
........................................................................ [ 30%]
........................................................................ [ 61%]
........................................................................ [ 92%]
..................                                                       [100%]
234 passed in 0.13s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 244ac0ed6baeb3d1789be61e1a0f8ef962e716f4`
- `docker volume create bb-2b3546ba6769-deps`
- `docker run --name bb-2b3546ba6769-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-6w0qyq3j/src,target=/src --mount type=volume,source=bb-2b3546ba6769-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-0fe4f524a30242e3977448bae19ce2e9; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-2b3546ba6769-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-6w0qyq3j/src,target=/src,readonly --mount type=volume,source=bb-2b3546ba6769-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_number.py`
- `docker rm -f bb-2b3546ba6769-install bb-2b3546ba6769-tests`
- `docker volume rm -f bb-2b3546ba6769-deps`
</details>

<details><summary>Tests at the base, without it: 2 failed, 232 passed in 0.15s</summary>

```
                    return _format_not_finite(float(value))
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            else:
>               if not math.isfinite(float(value)):
                                     ^^^^^^^^^^^^
E               OverflowError: int too large to convert to float

src/humanize/number.py:164: OverflowError
=========================== short test summary info ============================
FAILED tests/test_number.py::test_intcomma_large_integer[1] - OverflowError: ...
FAILED tests/test_number.py::test_intcomma_large_integer[-1] - OverflowError:...
2 failed, 232 passed in 0.15s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 3201e702ed7eae506f793fad0aec204f387aeb4c`
- `docker volume create bb-00b0c371b412-deps`
- `docker run --name bb-00b0c371b412-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-sp27hy69/src,target=/src --mount type=volume,source=bb-00b0c371b412-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e '"'"'/src[tests]'"'"' pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-9729a3f91cbe49638999f34316893e6d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-00b0c371b412-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-sp27hy69/src,target=/src,readonly --mount type=volume,source=bb-00b0c371b412-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_number.py`
- `docker rm -f bb-00b0c371b412-install bb-00b0c371b412-tests`
- `docker volume rm -f bb-00b0c371b412-deps`
</details>

Rerun: `bigbrother pr https://github.com/python-humanize/humanize/pull/392`

bigbrother 0.1.0, checked 3201e702ed7e...244ac0ed6bae
