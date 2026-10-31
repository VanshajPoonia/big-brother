# 'arrow' has no attribute 'utcnow'

https://github.com/arrow-py/arrow/issues/1154

**cannot reproduce** (high confidence, rule 3, basis evidence)

## Why
- the reporter's own code ran cleanly, the reported symptom didn't appear
- checked at 8842f8c3263d 1.2.3, picked from the tag

## What the report relies on
- symbol `arrow`: present at [arrow/__init__.py:1](https://github.com/arrow-py/arrow/blob/8842f8c3263d1f1219c189a0500aa67abdd0a214/arrow/__init__.py#L1): `from ._version import __version__`

## What ran
- status: ran

<details><summary>The script (the reporter's own)</summary>

```python
import arrow
utc = arrow.utcnow()
print(utc)
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/arrow-py__arrow archive --format=tar 8842f8c3263d1f1219c189a0500aa67abdd0a214`
- `docker volume create bb-9c1c0f145c17-deps`
- `docker run --name bb-9c1c0f145c17-install -e SETUPTOOLS_SCM_PRETEND_VERSION=1.2.3 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-1rrjm87f/src,target=/src --mount type=volume,source=bb-9c1c0f145c17-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-30d3c53226964fc4ae2e72628bd2bc0f; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-9c1c0f145c17-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-1rrjm87f/src,target=/src,readonly --mount type=volume,source=bb-9c1c0f145c17-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-1rrjm87f/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' arrow bigbrother-30d3c53226964fc4ae2e72628bd2bc0f 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-9c1c0f145c17-install bb-9c1c0f145c17-run`
- `docker volume rm -f bb-9c1c0f145c17-deps`
</details>

Rerun: `bigbrother check https://github.com/arrow-py/arrow/issues/1154`

bigbrother 0.1.0, model qwen3:4b
