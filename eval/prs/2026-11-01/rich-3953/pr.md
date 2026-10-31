# Fix ZWJ and edge cases

https://github.com/Textualize/rich/pull/3953

**tested**: every function this PR changes is used in a test the PR adds or changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_cells.py fails without the change (2 failed, 54 passed in 0.06s) and passes with it (56 passed in 0.04s), so the PR's tests check the change
- `get_character_cell_size` (rich/cells.py:47) changed, and no test this PR adds or changes uses it. Older tests do, like tests/test_cells.py:13, but they were written before this change
- `_cell_len` (rich/cells.py:113) changed, and no test uses it at all. It's private, so a test may reach it through a public function
- the PR changes 1 test file: tests/test_cells.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `get_character_cell_size` | [rich/cells.py:47](https://github.com/Textualize/rich/blob/54ae0cfbb8d43ccc8f56bf57019b9a22c252eefa/rich/cells.py#L47) | older test: [tests/test_cells.py:13](https://github.com/Textualize/rich/blob/54ae0cfbb8d43ccc8f56bf57019b9a22c252eefa/tests/test_cells.py#L13) `get_character_cell_size,` |
| `_cell_len` | [rich/cells.py:113](https://github.com/Textualize/rich/blob/54ae0cfbb8d43ccc8f56bf57019b9a22c252eefa/rich/cells.py#L113) | none |

<details><summary>Tests at the head, with the change: 56 passed in 0.04s</summary>

```
........................................................                 [100%]
56 passed in 0.04s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 54ae0cfbb8d43ccc8f56bf57019b9a22c252eefa`
- `docker volume create bb-8343f77883e0-deps`
- `docker run --name bb-8343f77883e0-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-unjuiooz/src,target=/src --mount type=volume,source=bb-8343f77883e0-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-c5e35d45051d4b4c96a5bb22fed2071c; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-8343f77883e0-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-unjuiooz/src,target=/src,readonly --mount type=volume,source=bb-8343f77883e0-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-8343f77883e0-install bb-8343f77883e0-tests`
- `docker volume rm -f bb-8343f77883e0-deps`
</details>

<details><summary>Tests at the base, without it: 2 failed, 54 passed in 0.06s</summary>

```
______________________________ test_non_printable ______________________________

    def test_non_printable():
        """Non printable characters should report a width of 0."""
        for ordinal in range(31):
            character = chr(ordinal)
>           assert cell_len(character) == 0
E           AssertionError: assert 1 == 0
E            +  where 1 = cell_len('\x01')

tests/test_cells.py:206: AssertionError
=========================== short test summary info ============================
FAILED tests/test_cells.py::test_zwj - StopIteration
FAILED tests/test_cells.py::test_non_printable - AssertionError: assert 1 == 0
2 failed, 54 passed in 0.06s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar 1d402e0c59f8765e420a5a4440eb2fca7465d1ae`
- `docker volume create bb-e342638ad7e3-deps`
- `docker run --name bb-e342638ad7e3-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-k3p4rqu4/src,target=/src --mount type=volume,source=bb-e342638ad7e3-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-984170d963c346a5b7bdcd1103affa73; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-e342638ad7e3-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-k3p4rqu4/src,target=/src,readonly --mount type=volume,source=bb-e342638ad7e3-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_cells.py`
- `docker rm -f bb-e342638ad7e3-install bb-e342638ad7e3-tests`
- `docker volume rm -f bb-e342638ad7e3-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/3953`

bigbrother 0.1.0, checked 1d402e0c59f8...54ae0cfbb8d4
