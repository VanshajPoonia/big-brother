# `metric(0)` crashes

https://github.com/python-humanize/humanize/issues/57

**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (ValueError: math domain error) inside the package
- checked at dab62bfbc9ac 4.3.0, picked from the tag

## What the report relies on
- symbol `humanize.metric`: present at src/humanize/number.py:476: `def metric(value: float, unit: str = "", precision: int = 3) -> str:`

## What ran
- status: ran
- exception: ValueError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar dab62bfbc9ac4cd9e5d558b38723d31d453c37da`
- `docker volume create bb-98638b8496e4-deps`
- `docker run --name bb-98638b8496e4-install -e SETUPTOOLS_SCM_PRETEND_VERSION=4.3.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-r65zrjwp/src,target=/src --mount type=volume,source=bb-98638b8496e4-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-6514c749c1ef4daba565c205885a8712; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-98638b8496e4-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-r65zrjwp/src,target=/src,readonly --mount type=volume,source=bb-98638b8496e4-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-r65zrjwp/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-6514c749c1ef4daba565c205885a8712 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-98638b8496e4-install bb-98638b8496e4-run`
- `docker volume rm -f bb-98638b8496e4-deps`

bigbrother 0.1.0, model qwen3:4b
