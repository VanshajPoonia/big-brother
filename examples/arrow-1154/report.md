# 'arrow' has no attribute 'utcnow'

https://github.com/arrow-py/arrow/issues/1154

**cannot reproduce** (high confidence, rule 3, basis evidence)

## Why
- the reporter's own code ran cleanly, the reported symptom didn't appear
- checked at 8842f8c3263d 1.2.3, picked from the tag

## What the report relies on
- symbol `arrow`: present at arrow/__init__.py:1: `from ._version import __version__`
- symbol `utcnow`: present at arrow/api.py:97: `def utcnow() -> Arrow:`

## What ran
- status: ran
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C /Users/vanshajpoonia/.cache/bigbrother/repos/arrow-py__arrow archive --format=tar 8842f8c3263d1f1219c189a0500aa67abdd0a214`
- `docker volume create bb-81184d0acc11-deps`
- `docker run --name bb-81184d0acc11-install -e SETUPTOOLS_SCM_PRETEND_VERSION=1.2.3 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-t4gynlv0/src,target=/src --mount type=volume,source=bb-81184d0acc11-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-805e70eade6e43bda17ce7f53e1e927a; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-81184d0acc11-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-t4gynlv0/src,target=/src,readonly --mount type=volume,source=bb-81184d0acc11-deps,target=/deps,readonly --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-t4gynlv0/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' arrow bigbrother-805e70eade6e43bda17ce7f53e1e927a 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-81184d0acc11-install bb-81184d0acc11-run`
- `docker volume rm -f bb-81184d0acc11-deps`

bigbrother 0.1.0, model qwen3:4b
