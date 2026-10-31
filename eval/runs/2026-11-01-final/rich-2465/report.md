# [BUG] Console has No attribute save_svg

https://github.com/Textualize/rich/issues/2465

**invalid** (medium confidence, rule 2, basis evidence)

## Why
- the report says Console has no save_svg, but it's defined at rich/console.py:2479 (`def save_svg(`) and first shipped in v12.1.0 on 03 Apr 2022, before the report, so the reporter's install is older than that
- checked at 90a7224ee672 origin/main, picked from the issue date

## What the report relies on
- symbol `rich.console.Console`: present at [rich/console.py:583](https://github.com/Textualize/rich/blob/90a7224ee672ca7f58399f3c8bec9d38341b1423/rich/console.py#L583): `class Console:`
- symbol `rich.console.Console.save_svg`: present at [rich/console.py:2479](https://github.com/Textualize/rich/blob/90a7224ee672ca7f58399f3c8bec9d38341b1423/rich/console.py#L2479): `def save_svg(`

## Where the missing name is
- `Console.save_svg` at [rich/console.py:2479](https://github.com/Textualize/rich/blob/90a7224ee672ca7f58399f3c8bec9d38341b1423/rich/console.py#L2479), first in v12.1.0

## What ran
- status: no_steps

## Notes
- dropped the symptom, its quote isn't in the report: "AttributeError: 'Console' object has no attribute 'save_svg'"
- dropped claimed version '0.18.1', the report doesn't mention it
- the model said the report has steps, but it has no runnable Python block

Rerun: `bigbrother check https://github.com/Textualize/rich/issues/2465`

bigbrother 0.1.0, model qwen3:4b
