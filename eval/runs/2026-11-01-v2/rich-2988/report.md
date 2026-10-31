# [BUG] print does not work well with DefaultDict

https://github.com/Textualize/rich/issues/2988

**cannot reproduce** (low confidence, rule 4, basis evidence)

## Why
- the repro failed with AttributeError outside the package, which isn't the reported symptom
- minor symbol 'Config' is absent (not defined anywhere in rich, tools)
- minor symbol 'chanfig' is absent (not defined anywhere in rich, tools)
- checked at bf3c7c30368b origin/main, picked from the issue date

## What the report relies on
- symbol `rich.print`: present at rich/__init__.py:53: `def print(`
- symbol `Config`: absent
- symbol `chanfig`: absent

## What ran
- status: ran
- exception: AttributeError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C /Users/vanshajpoonia/.cache/bigbrother/repos/Textualize__rich archive --format=tar bf3c7c30368b8fb87e88469e65f3b2b7f5671c57`
- `docker volume create bb-4547f017eefb-deps`
- `docker run --name bb-4547f017eefb-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-egtqidkm/src,target=/src --mount type=volume,source=bb-4547f017eefb-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-cf3cef3b799b4b51b21ce463fbfcc1bd; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-4547f017eefb-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-egtqidkm/src,target=/src,readonly --mount type=volume,source=bb-4547f017eefb-deps,target=/deps,readonly --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-egtqidkm/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' rich bigbrother-cf3cef3b799b4b51b21ce463fbfcc1bd 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-4547f017eefb-install bb-4547f017eefb-run`
- `docker volume rm -f bb-4547f017eefb-deps`

## Notes
- the reporter's script failed with its own ModuleNotFoundError, so Qwen repaired it once and it ran again

bigbrother 0.1.0, model qwen3:4b
