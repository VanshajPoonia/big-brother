# intword() drops the rounding carry for values >= 10^24 (renders '1000.0 sextillion' instead of '1.0 septillion')

https://github.com/python-humanize/humanize/issues/400

**confirmed** (medium confidence, rule 1, basis evidence)

## Why
- the reporter's own code printed the reported output (1000.0 sextillion)
- checked at 3201e702ed7e origin/main, picked from the issue date

## What the report relies on
- symbol `humanize.intword`: present at src/humanize/number.py:196: `def intword(value: NumberOrString, format: str = "%.1f") -> str:`

## What ran
- status: ran
- exception: NameError
- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C /Users/vanshajpoonia/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 3201e702ed7eae506f793fad0aec204f387aeb4c`
- `docker volume create bb-ff5969b86086-deps`
- `docker run --name bb-ff5969b86086-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-tnom2w3b/src,target=/src --mount type=volume,source=bb-ff5969b86086-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-7f3309a662704a01918e90b38e0dcf89; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-ff5969b86086-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-tnom2w3b/src,target=/src,readonly --mount type=volume,source=bb-ff5969b86086-deps,target=/deps,readonly --mount type=bind,source=/var/folders/98/746dt60x5_j8w6hy649kh_640000gn/T/bigbrother-tnom2w3b/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-7f3309a662704a01918e90b38e0dcf89 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-ff5969b86086-install bb-ff5969b86086-run`
- `docker volume rm -f bb-ff5969b86086-deps`

## Notes
- dropped version '4.x', it's a range, not one release

bigbrother 0.1.0, model qwen3:4b
