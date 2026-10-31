# HACKATHON.md

## Team name
Daggers

## Team members
- Vanshaj Poonia ([@VanshajPoonia](https://github.com/VanshajPoonia))
- Somya ([@somyasingh31](https://github.com/somyasingh31))
- Abhijeet Singh ([@Abhijeet878](https://github.com/Abhijeet878))
- Radhika ([@Radhika-88](https://github.com/Radhika-88))

## Problem statement
Problem 2: Evidence-Based Open Source Issue and Pull Request Triage

We are building **Big Brother**. It reads a GitHub issue, pulls out the technical claims, checks them against the real code (version and symbol checks, then a reproduction in an isolated Docker sandbox) and labels the issue `confirmed`, `cannot reproduce` or `invalid`, with the evidence and a confidence level.

## Models we use and why
- Qwen3 4B (`qwen3:4b`, Apache-2.0), run locally with Ollama: reads the issue title and body and pulls out the central claim, its premises and the exact symptom, then, if the reporter's own code fails on its own mistake like a missing import, repairs it once. When a report has no code but quotes an exception, it writes a short script from the description instead. It is good at structured JSON and short code, and small enough (about 2.5 GB) to run on any laptop, even without a GPU. Its output is checked against a schema, and fixed rules pick the label, so a small model is enough.

The model only runs on the same machine as the tool. The code refuses any model host that isn't localhost, so issue text is never sent to another server.

The model never picks the label. Fixed rules do, based on what the checks and the sandbox run show.
