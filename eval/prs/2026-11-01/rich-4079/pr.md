# Inline table code

https://github.com/Textualize/rich/pull/4079

**no test for this change**: no test the PR adds or changes uses a function it changes

No model: it ran the PR's tests in the offline sandbox, and read the PR's diff and the tests at its head.

## Why
- tests/test_markdown.py fails at the PR's head in the sandbox (1 failed, 7 passed in 0.26s). That can be the PR, or a dependency version different from the project's own CI, so it doesn't decide the label
- `TableDataElement.on_text` (rich/markdown.py:333) changed, and no test uses it at all
- the PR changes 1 test file: tests/test_markdown.py

## Changed functions

| Function | Where | A test that uses it |
| --- | --- | --- |
| `TableDataElement.on_text` | [rich/markdown.py:333](https://github.com/Textualize/rich/blob/cf3b5a16f7a76b2e8c4921d3314021bb72a6c5c1/rich/markdown.py#L333) | none |

<details><summary>Tests at the head, with the change: 1 failed, 7 passed in 0.26s</summary>

```
E       AssertionError: assert '\n\x1b[36m  ...    \x1b[0m\n' == '\n\x1b[36m  ...    \x1b[0m\n'
E         
E         Skipping 115 identical leading characters in diff, use -v to show
E         - [0m[38;2;248;248;242;48;2;39;40;34mprint[0m[38;2;248;248;242;48;2;39;40;34m([0m[38;2;230;219;116;48;2;39;40;34m'[0m[38;2;230;219;116;48;2;39;40;34mhello[0m[38;2;230;219;116;48;2;39;40;34m'[0m[38;2;248;248;242;48;2;39;40;34m)[0m[38;2;248;248;242;48;2;39;40;34m;[0m[36m [0m
E         ?           ^^^^^^^^^^^
E         + [0m[38;2;166;226;46;48;2;39;40;34mprint[0m[38;2;248;248;242;48;2;39;40;34m([0m[38;2;230;219;116;48;2;39;40;34m'[0m[38;2;230;219;116;48;2;39;40;34mhello[0m[38;2;230;219;116;48;2;39;40;34m'...
E         
E         ...Full output truncated, use '-vv' to show

tests/test_markdown.py:215: AssertionError
----------------------------- Captured stdout call -----------------------------
"\n\x1b[36m                 \x1b[0m\n\x1b[36m \x1b[0m\x1b[36mCol\x1b[0m\x1b[1m            \x1b[0m\x1b[36m \x1b[0m\n\x1b[36m ─────────────── \x1b[0m\n\x1b[36m \x1b[0m\x1b[38;2;166;226;46;48;2;39;40;34mprint\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m(\x1b[0m\x1b[38;2;230;219;116;48;2;39;40;34m'\x1b[0m\x1b[38;2;230;219;116;48;2;39;40;34mhello\x1b[0m\x1b[38;2;230;219;116;48;2;39;40;34m'\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m)\x1b[0m\x1b[38;2;248;248;242;48;2;39;40;34m;\x1b[0m\x1b[36m \x1b[0m\n\x1b[36m                 \x1b[0m\n"
=========================== short test summary info ============================
FAILED tests/test_markdown.py::test_inline_code_in_table_cells - AssertionErr...
1 failed, 7 passed in 0.26s
```

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar cf3b5a16f7a76b2e8c4921d3314021bb72a6c5c1`
- `docker volume create bb-edea2a5fc59b-deps`
- `docker run --name bb-edea2a5fc59b-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-k6ezdge_/src,target=/src --mount type=volume,source=bb-edea2a5fc59b-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src pytest; status=$?; if [ $status -eq 0 ]; then echo bigbrother-7d4304f52f0f429ab1404fe0e1f65c06; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-edea2a5fc59b-tests --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 -e PYTHONDONTWRITEBYTECODE=1 --mount type=bind,source=$TMPDIR/bigbrother-k6ezdge_/src,target=/src,readonly --mount type=volume,source=bb-edea2a5fc59b-deps,target=/deps,readonly --workdir /src bigbrother-sandbox:0.1 /deps/venv/bin/python -m pytest -q -p no:cacheprovider -o addopts= tests/test_markdown.py`
- `docker rm -f bb-edea2a5fc59b-install bb-edea2a5fc59b-tests`
- `docker volume rm -f bb-edea2a5fc59b-deps`
</details>

Rerun: `bigbrother pr https://github.com/Textualize/rich/pull/4079`

bigbrother 0.1.0, checked 19c67b9a3479...cf3b5a16f7a7
