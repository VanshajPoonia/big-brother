# Module "arrow.arrow" has no attribute 'get'

https://github.com/arrow-py/arrow/issues/896

### ! Not reproduced on 0.17.0

**cannot reproduce** (low confidence, rule 3, basis evidence)

## Why
- a script Qwen wrote ran cleanly, the reported symptom didn't appear
- checked at b746fedf7286 0.17.0, picked from the tag

## What the report relies on
- symbol `arrow.get`: present at [arrow/api.py:16](https://github.com/arrow-py/arrow/blob/b746fedf7286c3755a46f07ab72f4c414cd41fc0/arrow/api.py#L16): `def get(*args, **kwargs):`

## What ran
- status: ran

<details><summary>The script (written by Qwen)</summary>

```python
import arrow
arrow.get('2013-05-11T21:23:58.970460+07:00')
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/arrow-py__arrow archive --format=tar b746fedf7286c3755a46f07ab72f4c414cd41fc0`
- `docker volume create bb-6ca3d584c9fd-deps`
- `docker run --name bb-6ca3d584c9fd-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.17.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-u2z2t4ol/src,target=/src --mount type=volume,source=bb-6ca3d584c9fd-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-8e4d4b5837f34035b37335e97ed8b621; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-6ca3d584c9fd-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-u2z2t4ol/src,target=/src,readonly --mount type=volume,source=bb-6ca3d584c9fd-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-u2z2t4ol/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' arrow bigbrother-8e4d4b5837f34035b37335e97ed8b621 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-6ca3d584c9fd-install bb-6ca3d584c9fd-run`
- `docker volume rm -f bb-6ca3d584c9fd-deps`
</details>

## Notes
- the model said the report has steps, but it has no runnable Python block
- the report has no code, so Qwen wrote a script from its description

Rerun: `bigbrother check https://github.com/arrow-py/arrow/issues/896`

bigbrother 0.1.0, model qwen3:4b
