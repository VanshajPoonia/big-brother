# TypeError: can't subtract offset-naive and offset-aware datetimes

https://github.com/python-humanize/humanize/issues/122

**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (TypeError: can't subtract offset-naive and offset-aware datetimes) inside the package
- checked at fb3322a74bad 4.7.0, picked from the tag

## What the report relies on
- symbol `humanize.naturaltime`: present at [src/humanize/time.py:222](https://github.com/python-humanize/humanize/blob/fb3322a74bad97cda90e601f64959a649bc33001/src/humanize/time.py#L222): `def naturaltime(`
- symbol `humanize.time`: present at [src/humanize/time.py:1](https://github.com/python-humanize/humanize/blob/fb3322a74bad97cda90e601f64959a649bc33001/src/humanize/time.py#L1): `#!/usr/bin/env python`

## What ran
- status: ran
- exception: TypeError

<details><summary>The script (the reporter's own)</summary>

```python
import datetime as dt

import humanize

my_now = dt.datetime.now(tz=dt.timezone.utc)
same_dt = my_now - dt.timedelta(days=3, hours=1)

result = humanize.naturaltime(same_dt, when=my_now)
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar fb3322a74bad97cda90e601f64959a649bc33001`
- `docker volume create bb-2b3dc885310e-deps`
- `docker run --name bb-2b3dc885310e-install -e SETUPTOOLS_SCM_PRETEND_VERSION=4.7.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-ddrm7ost/src,target=/src --mount type=volume,source=bb-2b3dc885310e-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-8594d05dd49d4f3d82b7c3fdf221a8f6; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-2b3dc885310e-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-ddrm7ost/src,target=/src,readonly --mount type=volume,source=bb-2b3dc885310e-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-ddrm7ost/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-8594d05dd49d4f3d82b7c3fdf221a8f6 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-2b3dc885310e-install bb-2b3dc885310e-run`
- `docker volume rm -f bb-2b3dc885310e-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 8, in <module>
    result = humanize.naturaltime(same_dt, when=my_now)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/src/src/humanize/time.py", line 253, in naturaltime
    date, delta = _date_and_delta(value, now=now)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/src/src/humanize/time.py", line 76, in _date_and_delta
    delta = now - value
            ~~~~^~~~~~~
TypeError: can't subtract offset-naive and offset-aware datetimes
```
</details>

## Notes
- dropped 'datetime.datetime', it's from Python's standard library, not this package
- dropped 'datetime.timedelta', it's from Python's standard library, not this package

Rerun: `bigbrother check https://github.com/python-humanize/humanize/issues/122`

bigbrother 0.1.0, model qwen3:4b
