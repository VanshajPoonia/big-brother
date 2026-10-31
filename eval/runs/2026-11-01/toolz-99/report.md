# Possible bug in `update_in`

https://github.com/pytoolz/toolz/issues/99

**cannot reproduce** (low confidence, rule 4, basis evidence)

## Why
- the repro failed with NameError outside the package, which isn't the reported symptom
- checked at 891a9462ed87 origin/master, picked from the issue date

## What the report relies on
- symbol `update_in`: present at toolz/dicttoolz/core.py:94: `def update_in(d, keys, f):`
- symbol `assoc`: present at toolz/dicttoolz/core.py:78: `def assoc(d, key, value):`

## What ran
- status: ran
- exception: NameError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C /Users/vanshajpoonia/.cache/bigbrother/repos/pytoolz__toolz archive --format=tar 891a9462ed87901395031476b5172091b6205edb`
- `docker volume create bb-db2f71ca5993-deps`
- `docker run --name bb-db2f71ca5993-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-pcv8cs9_/src,target=/src --mount type=volume,source=bb-db2f71ca5993-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-fb2dc2c7c6c84d328e890b2b909cddf4; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-db2f71ca5993-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-pcv8cs9_/src,target=/src,readonly --mount type=volume,source=bb-db2f71ca5993-deps,target=/deps,readonly --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-pcv8cs9_/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' update_in bigbrother-fb2dc2c7c6c84d328e890b2b909cddf4 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-db2f71ca5993-install bb-db2f71ca5993-run`
- `docker volume rm -f bb-db2f71ca5993-deps`

bigbrother 0.1.0, model qwen3:4b
