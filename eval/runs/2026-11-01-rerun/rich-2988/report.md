# [BUG] print does not work well with DefaultDict

https://github.com/Textualize/rich/issues/2988

**cannot reproduce** (low confidence, rule 4, basis evidence)

## Why
- the repro failed with AttributeError outside the package, which isn't the reported symptom
- minor symbol 'Config' is absent (not defined anywhere in rich, tools)
- minor symbol 'chanfig' is absent (not defined anywhere in rich, tools)
- checked at bf3c7c30368b origin/main, picked from the issue date

## What the report relies on
- symbol `rich.print`: present at [rich/__init__.py:53](https://github.com/Textualize/rich/blob/bf3c7c30368b8fb87e88469e65f3b2b7f5671c57/rich/__init__.py#L53): `def print(`
- symbol `Config`: absent
- symbol `chanfig`: absent

## What ran
- status: ran
- exception: AttributeError

<details><summary>The script (written by Qwen)</summary>

```python
from rich import print as pprint

if __name__ == '__main__':
    config = {'hello': 'world'}
    print('print', config)
    pprint('rich.print', config)
    print(config.__rich__)
    print(config.keys())
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/Textualize__rich archive --format=tar bf3c7c30368b8fb87e88469e65f3b2b7f5671c57`
- `docker volume create bb-82b3abdcadc7-deps`
- `docker run --name bb-82b3abdcadc7-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-mavdp7x7/src,target=/src --mount type=volume,source=bb-82b3abdcadc7-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-3823f1287ade42e39bc98e3fe29a2c07; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-82b3abdcadc7-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-mavdp7x7/src,target=/src,readonly --mount type=volume,source=bb-82b3abdcadc7-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-mavdp7x7/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' rich bigbrother-3823f1287ade42e39bc98e3fe29a2c07 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-82b3abdcadc7-install bb-82b3abdcadc7-run`
- `docker volume rm -f bb-82b3abdcadc7-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 7, in <module>
    print(config.__rich__)
          ^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute '__rich__'. Did you mean: '__dir__'?
```
</details>

## Notes
- the reporter's script failed with its own ModuleNotFoundError, so Qwen repaired it once and it ran again

Rerun: `bigbrother check https://github.com/Textualize/rich/issues/2988`

bigbrother 0.1.0, model qwen3:4b
