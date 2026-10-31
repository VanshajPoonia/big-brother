# [BUG] Cannot access `console` after importing rich

https://github.com/Textualize/rich/issues/3352

**cannot reproduce** (high confidence, rule 3, basis evidence)

## Why
- the reporter's own code ran cleanly, the reported symptom didn't appear
- checked at afaf8cc7e08f v13.4.2, picked from the tag

## What the report relies on
- symbol `rich.console`: present at rich/console.py:1: `import inspect`

## What ran
- status: ran
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar afaf8cc7e08fd47d2c78c953c4b8ea663e05fb90`
- `docker volume create bb-4396850db07d-deps`
- `docker run --name bb-4396850db07d-install -e SETUPTOOLS_SCM_PRETEND_VERSION=13.4.2 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-cevyihkj/src,target=/src --mount type=volume,source=bb-4396850db07d-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-0ad81b9ec39a47928b4e4018bc29773d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-4396850db07d-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-cevyihkj/src,target=/src,readonly --mount type=volume,source=bb-4396850db07d-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-cevyihkj/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' rich bigbrother-0ad81b9ec39a47928b4e4018bc29773d 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-4396850db07d-install bb-4396850db07d-run`
- `docker volume rm -f bb-4396850db07d-deps`

bigbrother 0.1.0, model qwen3:4b
