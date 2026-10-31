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
- Qwen3 8B (`qwen3:8b`, Apache-2.0), run locally with Ollama: reads the issue title and body and pulls out the central claim, its premises and the exact symptom, then writes a short reproduction script when the reporter didn't include one. It is good at code and structured JSON, and small enough to run on a 16 GB laptop next to Docker.

The model never picks the label. Fixed rules do, based on what the checks and the sandbox run show.
