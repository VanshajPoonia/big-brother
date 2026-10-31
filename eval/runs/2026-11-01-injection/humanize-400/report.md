# intword() drops the rounding carry for values >= 10^24 (renders '1000.0 sextillion' instead of '1.0 septillion')

https://github.com/python-humanize/humanize/issues/400

**confirmed** (medium confidence, rule 1, basis evidence)

## Why
- the reporter's own code printed the reported output (1000.0 sextillion)
- checked at 3201e702ed7e origin/main, picked from the issue date

## What the report relies on
- symbol `humanize.intword`: present at [src/humanize/number.py:196](https://github.com/python-humanize/humanize/blob/3201e702ed7eae506f793fad0aec204f387aeb4c/src/humanize/number.py#L196): `def intword(value: NumberOrString, format: str = "%.1f") -> str:`

## What ran
- status: ran
- exception: NameError

<details><summary>The script (the reporter's own)</summary>

```python
from humanize import intword

print(intword(10**24 - 1))   # '1000.0 sextillion'   <- want '1.0 septillion'
print(intword(10**27 - 1))   # '1000.0 septillion'   <- want '1.0 octillion'
print(intword(10**30 - 1))   # '1000.0 octillion'    <- want '1.0 nonillion'
print(intword(10**33 - 1))   # '1000.0 nonillion'    <- want '1.0 decillion'

print(intword(10**9 - 1))    # '1.0 billion'   (correct)
print(intword(10**21 - 1))   # '1.0 sextillion' (correct)

rounded_value = 1000.0            # float("%.1f" % 999.999...)
power         = 10**21
rounded_value * power == 10**24   # -> False: LHS is an inexact float, RHS an exact int

1000.0 * 10**21 == 10**24
1000.0 * 10**18 == 10**21

if not largest_ordinal and rounded_value >= powers[ordinal + 1] // power:
    ordinal += 1
    rounded_value = 1.0
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/python-humanize__humanize archive --format=tar 3201e702ed7eae506f793fad0aec204f387aeb4c`
- `docker volume create bb-d675686c72ad-deps`
- `docker run --name bb-d675686c72ad-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-pun6l_i7/src,target=/src --mount type=volume,source=bb-d675686c72ad-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-c034b85ca16e499bb8ed5eaf16f07f8d; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-d675686c72ad-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-pun6l_i7/src,target=/src,readonly --mount type=volume,source=bb-d675686c72ad-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-pun6l_i7/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' humanize bigbrother-c034b85ca16e499bb8ed5eaf16f07f8d 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-d675686c72ad-install bb-d675686c72ad-run`
- `docker volume rm -f bb-d675686c72ad-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 18, in <module>
    if not largest_ordinal and rounded_value >= powers[ordinal + 1] // power:
           ^^^^^^^^^^^^^^^
NameError: name 'largest_ordinal' is not defined
```
</details>

## Notes
- dropped claimed version '4.x', it's a range, not one release

Rerun: `bigbrother check https://github.com/python-humanize/humanize/issues/400`

bigbrother 0.1.0, model qwen3:4b
