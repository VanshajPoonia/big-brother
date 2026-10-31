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

We are building **Big Brother**, which watches incoming issues and pull requests, breaks them into individual technical claims, and checks each claim against the real code: static checks, git history, and reproduction inside an isolated sandbox. Maintainers get an evidence-backed verdict for every claim, and Big Brother says "unverified" whenever the evidence is not strong enough.

## Models we use and why
- Qwen3 8B (`qwen3:8b`, Apache-2.0), run locally with Ollama: reads issue and PR text, splits it into checkable claims, and drives our own agent harness through tool calls (reading code, searching git history, writing reproduction scripts for the sandbox). It has reliable tool calling and is small enough to run on a 16 GB laptop next to Docker.

The model never decides a verdict on its own. Verdicts come from deterministic rules over the evidence it gathers.
