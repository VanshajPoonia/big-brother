# [BUG] Console has No attribute save_svg

https://github.com/Textualize/rich/issues/2465

**cannot reproduce** (low confidence, rule 5, basis fallback)

## Why
- the report has no steps to run, so the label is the blocked policy (cannot reproduce), not evidence
- checked at 90a7224ee672 origin/main, picked from the issue date

## What the report relies on
- symbol `rich.console.Console`: present at rich/console.py:583: `class Console:`
- symbol `rich.console.Console.save_svg`: present at rich/console.py:2479: `def save_svg(`

## What ran
- status: no_steps

## Notes
- dropped the symptom, its quote isn't in the report: "AttributeError: 'Console' object has no attribute 'save_svg'"
- dropped claimed version '0.18.1', the report doesn't mention it
- the model said the report has steps, but it has no runnable Python block

bigbrother 0.1.0, model qwen3:4b
