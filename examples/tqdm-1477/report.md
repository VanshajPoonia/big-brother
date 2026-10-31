# tqdm fails to work if the main script name is `select.py`

https://github.com/tqdm/tqdm/issues/1477

### ✗ The reporter's own select.py hid Python's select module

**invalid** (medium confidence, rule 2, basis evidence)

## Why
- the report's own traceback shows the reporter's file /Users/universe/Documents/grida/figma-archives/figma_archiver/scripts/select.py loaded in place of the module 'select' (AttributeError: module 'select' has no attribute 'select'), so the error comes from the file name
- checked at 2efa1e8224d4 origin/master, picked from the issue date

## What the report relies on
- symbol `tqdm`: present at [tqdm/__init__.py:1](https://github.com/tqdm/tqdm/blob/2efa1e8224d430095cca69287dad19e198c45396/tqdm/__init__.py#L1): `from ._monitor import TMonitor, TqdmSynchronisationWarning`

## What ran
- status: ran
- exception: ModuleNotFoundError

<details><summary>The script (the reporter's own)</summary>

```python
###
# selects files from a archives to b archives
# python select.py a b --list=keys.txt
# a, b - archive directories with [key].json
###

import os
import click
import shutil
from pathlib import Path
from tqdm import tqdm


@click.command()
@click.argument('a', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('b', type=click.Path(exists=False))
@click.option('--list', 'list_file', help='list file (txt, line separated) containing file keys - read & select from [a]', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--link', help='use symlink to sync files (default: False)', is_flag=True)
def main(a, b, list_file, link):
    a = Path(a)
    b = Path(b)

    try:
        b.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        click.echo(f"🚨 '{b}' is not empty.")
        return

    # read lines (remove empty lines)
    target_keys = open(list_file, 'r').read().splitlines()
    target_keys = [k for k in target_keys if k != '']

    tqdm.write(f"📦 {len(target_keys)} files to be copied from {a} to {b}.")

    success = 0
    for key in tqdm(target_keys):
        origin = a / f"{key}.json"
        target = b / f"{key}.json"
        # check if key exists in a
        if origin.exists():
            if link:
                # link to b
                os.symlink(origin, target)
            else:
                # copy to b
                shutil.copy(origin, target)
            tqdm.write(f"📦 {origin} → {target}")
            success += 1
        else:
            tqdm.write(f"❌ {key}.json")

    msg = f"📦 {success}/{len(target_keys)} files copied from '{a}' to '{b}'"
    # tqdm.write(msg)
    print(msg)


if __name__ == '__main__':
    main()
```
</details>

<details><summary>Every command it ran</summary>

- `docker image inspect bigbrother-sandbox:0.1`
- `docker image inspect --format '{{.Id}} {{json .Config.Env}}' bigbrother-sandbox:0.1`
- `git -C ~/.cache/bigbrother/repos/tqdm__tqdm archive --format=tar 2efa1e8224d430095cca69287dad19e198c45396`
- `docker volume create bb-f7aa23cf51f4-deps`
- `docker run --name bb-f7aa23cf51f4-install -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 --cpus 1 --memory 1g --pids-limit 256 --mount type=bind,source=$TMPDIR/bigbrother-8af5xfe3/src,target=/src --mount type=volume,source=bb-f7aa23cf51f4-deps,target=/deps bigbrother-sandbox:0.1 sh -c 'uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src; status=$?; if [ $status -eq 0 ]; then echo bigbrother-507b77ac11c24195a4993651191d3d4b; uv pip freeze --python /deps/venv/bin/python; fi; chmod -R a+rwX /src 2>/dev/null; exit $status'`
- `docker run --name bb-f7aa23cf51f4-run --network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 128 --memory 1g --cpus 1 --mount type=bind,source=$TMPDIR/bigbrother-8af5xfe3/src,target=/src,readonly --mount type=volume,source=bb-f7aa23cf51f4-deps,target=/deps,readonly --mount type=bind,source=$TMPDIR/bigbrother-8af5xfe3/repro.py,target=/repro.py,readonly --workdir /tmp bigbrother-sandbox:0.1 sh -c '/deps/venv/bin/python -c '"'"'import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
'"'"' tqdm bigbrother-507b77ac11c24195a4993651191d3d4b 2>/dev/null; exec /deps/venv/bin/python /repro.py'`
- `docker rm -f bb-f7aa23cf51f4-install bb-f7aa23cf51f4-run`
- `docker volume rm -f bb-f7aa23cf51f4-deps`
</details>

<details><summary>Last lines of its output</summary>

```
Traceback (most recent call last):
  File "/repro.py", line 8, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```
</details>

## Notes
- dropped 'select.py', it's from Python's standard library, not this package
- rejected Qwen's repaired script, it doesn't parse: unterminated string literal (detected at line 5)

Rerun: `bigbrother check https://github.com/tqdm/tqdm/issues/1477`

bigbrother 0.1.0, model qwen3:4b
