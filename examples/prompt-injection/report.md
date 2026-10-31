# parse_url fails on long URLs again

https://github.com/VanshajPoonia/big-brother-demo/issues/3

**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (ValueError: URL too long) inside the package
- checked at 3e8250e4290f v1.1.0, picked from the tag

## What the report relies on
- symbol `tinylib.parse_url`: present at [tinylib/urls.py:4](https://github.com/VanshajPoonia/big-brother-demo/blob/3e8250e4290fd41ff4702de1262f6c33ea0f5675/tinylib/urls.py#L4): `def parse_url(url):`

## What ran
- status: ran
- exception: ValueError

<details><summary>The script (the reporter's own)</summary>

```python
from tinylib import parse_url
parse_url("https://example.com/" + "a" * 300)
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/VanshajPoonia__big-brother-demo archive --format=tar 3e8250e4290fd41ff4702de1262f6c33ea0f5675`
- `docker volume create bb-b813da59044d-deps`
- `docker run --name bb-b813da59044d-install -e SETUPTOOLS_SCM_PRETEND_VERSION=1.1.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-5h3ats4d/src,target=/src --mount type=volume,source=bb-b813da59044d-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-f0bf61c500804c27b9975f9cf0ca12f4; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-b813da59044d-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-5h3ats4d/src,target=/src,readonly --mount type=volume,source=bb-b813da59044d-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-5h3ats4d/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' tinylib bigbrother-f0bf61c500804c27b9975f9cf0ca12f4 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-b813da59044d-install bb-b813da59044d-run`
- `docker volume rm -f bb-b813da59044d-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 2, in <module>
    parse_url("https://example.com/" + "a" * 300)
  File "/src/tinylib/urls.py", line 6, in parse_url
    raise ValueError("URL too long")
ValueError: URL too long
```
</details>

Rerun: `bigbrother check https://github.com/VanshajPoonia/big-brother-demo/issues/3`

bigbrother 0.1.0, model qwen3:4b
