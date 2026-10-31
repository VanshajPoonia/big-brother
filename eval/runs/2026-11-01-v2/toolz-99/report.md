# Possible bug in `update_in`

https://github.com/pytoolz/toolz/issues/99

**confirmed** (high confidence, rule 1, basis evidence)

## Why
- the repro hit the reported symptom (AttributeError: 'NoneType' object has no attribute 'get') inside the package
- checked at 891a9462ed87 origin/master, picked from the issue date

## What the report relies on
- symbol `update_in`: present at toolz/dicttoolz/core.py:94: `def update_in(d, keys, f):`
- symbol `assoc`: present at toolz/dicttoolz/core.py:78: `def assoc(d, key, value):`

## What ran
- status: ran
- exception: AttributeError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/pytoolz__toolz archive --format=tar 891a9462ed87901395031476b5172091b6205edb`
- `docker volume create bb-4cdd20edcf98-deps`
- `docker run --name bb-4cdd20edcf98-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-0sdjhh9b/src,target=/src --mount type=volume,source=bb-4cdd20edcf98-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-0c81284d08574e1d8757824a57db13c0; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-4cdd20edcf98-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-0sdjhh9b/src,target=/src,readonly --mount type=volume,source=bb-4cdd20edcf98-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-0sdjhh9b/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' toolz bigbrother-0c81284d08574e1d8757824a57db13c0 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-4cdd20edcf98-install bb-4cdd20edcf98-run`
- `docker volume rm -f bb-4cdd20edcf98-deps`

## Notes
- the package is 'toolz' from the repo, not 'update_in' as Qwen read it
- took out toolz.clojure_update_in from Qwen's imports, the package doesn't have them at this revision
- Qwen only added imports or dropped lines, so the code that ran is still the reporter's
- the reporter's script failed with its own NameError, so Qwen repaired it once and it ran again

bigbrother 0.1.0, model qwen3:4b
