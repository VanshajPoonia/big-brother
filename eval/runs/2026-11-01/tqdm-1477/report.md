# tqdm fails to work if the main script name is `select.py`

https://github.com/tqdm/tqdm/issues/1477

**cannot reproduce** (low confidence, rule 4, basis evidence)

## Why
- the repro failed with ModuleNotFoundError outside the package, which isn't the reported symptom
- checked at 2efa1e8224d4 origin/master, picked from the issue date

## What the report relies on
- symbol `tqdm`: present at tqdm/__init__.py:1: `from ._monitor import TMonitor, TqdmSynchronisationWarning`

## What ran
- status: ran
- exception: ModuleNotFoundError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C /Users/vanshajpoonia/.cache/bigbrother/repos/tqdm__tqdm archive --format=tar 2efa1e8224d430095cca69287dad19e198c45396`
- `docker volume create bb-a75a20276eae-deps`
- `docker run --name bb-a75a20276eae-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-b5hut9ev/src,target=/src --mount type=volume,source=bb-a75a20276eae-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-1cc397fc51d0432b9e2632ca7f85550d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-a75a20276eae-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-b5hut9ev/src,target=/src,readonly --mount type=volume,source=bb-a75a20276eae-deps,target=/deps,readonly --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-b5hut9ev/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' tqdm bigbrother-1cc397fc51d0432b9e2632ca7f85550d 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-a75a20276eae-install bb-a75a20276eae-run`
- `docker volume rm -f bb-a75a20276eae-deps`

## Notes
- dropped 'select.py', it's from Python's standard library, not this package

bigbrother 0.1.0, model qwen3:4b
