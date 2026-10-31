# fix fonts

https://github.com/Textualize/rich/pull/3944

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_cells.py fails without the change (1 failed, 53 passed in 0.05s) and passes with it (54 passed in 0.04s), so the PR's tests check the change
- `get_character_cell_size` (rich/cells.py:47) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_cells.py:13, but they were written before this change
- the PR changes 1 test file: tests/test_cells.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `get_character_cell_size` | [rich/cells.py:47](https://github.com/Textualize/rich/blob/2e5a5dad304b59d75aa4b4ed6cae031693e3615e/rich/cells.py#L47) | older test: [tests/test_cells.py:13](https://github.com/Textualize/rich/blob/2e5a5dad304b59d75aa4b4ed6cae031693e3615e/tests/test_cells.py#L13) `get_character_cell_size,` |

<details><summary>Tests at the head, with the change: 54 passed in 0.04s</summary>

```
......................................................                   [100%]
54 passed in 0.04s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 2e5a5dad304b59d75aa4b4ed6cae031693e3615e`
- `docker volume create bb-bb815c8351fd-deps`
- `docker run --name bb-bb815c8351fd-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-324sw1pt/src,target=/src --mount type=volume,source=bb-bb815c8351fd-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-3206de815747451792775d58d0aaab00; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-bb815c8351fd-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-324sw1pt/src,target=/src,readonly --mount type=volume,source=bb-bb815c8351fd-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-bb815c8351fd-install bb-bb815c8351fd-tests`
- `docker volume rm -f bb-bb815c8351fd-deps`
</details>

<details><summary>Tests at the base, without it: 1 failed, 53 passed in 0.05s</summary>

```
.....................................................F                   [100%]
=================================== FAILURES ===================================
________________________________ test_nerd_font ________________________________

    def test_nerd_font():
        """Regression test for https://github.com/Textualize/rich/issues/3943"""
        # Not allocated by unicode, but used by nerd fonts
>       assert cell_len("\U000f024d") == 1
E       AssertionError: assert 0 == 1
E        +  where 0 = cell_len('\U000f024d')

tests/test_cells.py:189: AssertionError
=========================== short test summary info ============================
FAILED tests/test_cells.py::test_nerd_font - AssertionError: assert 0 == 1
1 failed, 53 passed in 0.05s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 36fe3f7ca9becca4777861d5e6e625f5a4a37545`
- `docker volume create bb-a34e1f4f81d4-deps`
- `docker run --name bb-a34e1f4f81d4-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-hbbj_8bq/src,target=/src --mount type=volume,source=bb-a34e1f4f81d4-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-f85b5580d66941bc8b685033bdd310e9; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-a34e1f4f81d4-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-hbbj_8bq/src,target=/src,readonly --mount type=volume,source=bb-a34e1f4f81d4-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-a34e1f4f81d4-install bb-a34e1f4f81d4-tests`
- `docker volume rm -f bb-a34e1f4f81d4-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3944`

bigbrother 0.1.0, checked 36fe3f7ca9be...2e5a5dad304b
