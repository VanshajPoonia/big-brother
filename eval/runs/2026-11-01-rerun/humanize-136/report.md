# `humanize.intword` Unwanted decimal value

https://github.com/python-humanize/humanize/issues/136

**cannot reproduce** (low confidence, rule 4, basis evidence)

## Why
- the reported symptom showed up, but not from inside the package, so it doesn't count
- checked at 2635e6e4c15a origin/main, picked from the issue date

## What the report relies on
- symbol `humanize.intword`: present at [src/humanize/number.py:193](https://github.com/python-humanize/humanize/blob/2635e6e4c15a9182f2a7273500f7f02b14fde343/src/humanize/number.py#L193): `def intword(value: NumberOrString, format: str = "%.1f") -> str:`

## What ran
- status: ran

<details><summary>The script (written by Qwen)</summary>

```python
from humanize import intword

print(intword(1000))
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 2635e6e4c15a9182f2a7273500f7f02b14fde343`
- `docker volume create bb-8282c7a57379-deps`
- `docker run --name bb-8282c7a57379-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-hecq36j1/src,target=/src --mount type=volume,source=bb-8282c7a57379-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-00d365d229e34536b273b9f1e3e0e3dd; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-8282c7a57379-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-hecq36j1/src,target=/src,readonly --mount type=volume,source=bb-8282c7a57379-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-hecq36j1/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-00d365d229e34536b273b9f1e3e0e3dd 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-8282c7a57379-install bb-8282c7a57379-run`
- `docker volume rm -f bb-8282c7a57379-deps`
</details>

## Notes
- the reporter's script failed with its own NameError, so Qwen repaired it once and it ran again

Rerun: `bigbrother check https://github.com/python-humanize/humanize/issues/136`

bigbrother 0.1.0, model qwen3:4b
