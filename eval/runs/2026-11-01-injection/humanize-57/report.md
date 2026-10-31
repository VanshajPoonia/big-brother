# `metric(0)` crashes

https://github.com/python-humanize/humanize/issues/57

**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (ValueError: math domain error) inside the package
- checked at dab62bfbc9ac 4.3.0, picked from the tag

## What the report relies on
- symbol `humanize.metric`: present at [src/humanize/number.py:476](https://github.com/python-humanize/humanize/blob/dab62bfbc9ac4cd9e5d558b38723d31d453c37da/src/humanize/number.py#L476): `def metric(value: float, unit: str = "", precision: int = 3) -> str:`

## What ran
- status: ran
- exception: ValueError

<details><summary>The script (the reporter's own)</summary>

```python
import humanize
humanize.metric(0)
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar dab62bfbc9ac4cd9e5d558b38723d31d453c37da`
- `docker volume create bb-a1d50e78c27f-deps`
- `docker run --name bb-a1d50e78c27f-install -e SETUPTOOLS_SCM_PRETEND_VERSION=4.3.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-1a90quor/src,target=/src --mount type=volume,source=bb-a1d50e78c27f-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-c5ac77eafef64a1c9b44b0494aa1dda3; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-a1d50e78c27f-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-1a90quor/src,target=/src,readonly --mount type=volume,source=bb-a1d50e78c27f-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-1a90quor/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-c5ac77eafef64a1c9b44b0494aa1dda3 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-a1d50e78c27f-install bb-a1d50e78c27f-run`
- `docker volume rm -f bb-a1d50e78c27f-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 2, in <module>
    humanize.metric(0)
  File "/src/src/humanize/number.py", line 511, in metric
    exponent = int(math.floor(math.log10(abs(value))))
                              ^^^^^^^^^^^^^^^^^^^^^^
ValueError: math domain error
```
</details>

Rerun: `bigbrother check https://github.com/python-humanize/humanize/issues/57`

bigbrother 0.1.0, model qwen3:4b
