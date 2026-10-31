# tqdm fails to work if the main script name is `select.py`

https://github.com/tqdm/tqdm/issues/1477

**invalid** (medium confidence, rule 2, basis evidence)

## Why
- the report's own traceback shows the reporter's file /Users/universe/Documents/grida/figma-archives/figma_archiver/scripts/select.py loaded in place of the module 'select' (AttributeError: module 'select' has no attribute 'select'), so the error comes from the file name
- checked at 2efa1e8224d4 origin/master, picked from the issue date

## What the report relies on
- symbol `tqdm`: present at tqdm/__init__.py:1: `from ._monitor import TMonitor, TqdmSynchronisationWarning`

## What ran
- status: ran
- exception: ModuleNotFoundError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker build -t bigbrother-sandbox:0.1 '~/Code/Hackathon/Hacktoberfest/Hacktober Newton School/big-brother/docker'`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/tqdm__tqdm archive --format=tar 2efa1e8224d430095cca69287dad19e198c45396`
- `docker volume create bb-579fcaef382b-deps`
- `docker run --name bb-579fcaef382b-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-22nz8ekp/src,target=/src --mount type=volume,source=bb-579fcaef382b-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-021b669b60254a81b16077ae740c9c4a; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-579fcaef382b-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-22nz8ekp/src,target=/src,readonly --mount type=volume,source=bb-579fcaef382b-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-22nz8ekp/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' tqdm bigbrother-021b669b60254a81b16077ae740c9c4a 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-579fcaef382b-install bb-579fcaef382b-run`
- `docker volume rm -f bb-579fcaef382b-deps`

## Notes
- dropped 'select.py', it's from Python's standard library, not this package
- rejected Qwen's repaired script, it doesn't parse: unterminated string literal (detected at line 5)

bigbrother 0.1.0, model qwen3:4b
