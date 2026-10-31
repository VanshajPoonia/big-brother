# Big Brother

Big Brother is watching your claims.

It reads an issue or pull request, pulls out each technical claim ("crashes on 2.4.1", "fixes #120", "RCE in `parse_url_v2()`") and checks it against the code. You get a verdict per claim with the evidence behind it, or "unverified" when the evidence isn't there.

It runs on a local open-weight model (Qwen3 8B via Ollama). No cloud AI.

Built at Hacktoberfest Hack Day Sonipat by Team Daggers. Work in progress, see [docs/PLAN.md](docs/PLAN.md).

## Install

```
pip install -e ".[dev]"
ollama pull qwen3:8b
```

## Run

```
bigbrother --version
```

## Test

```
pytest
```

Tests don't need Ollama running.

## How it works

The model reads the report and digs through the code, but it never hands out verdicts. Fixed rules do that, based on what static checks, git history and a sandboxed reproduction actually show. Details in [docs/DESIGN.md](docs/DESIGN.md).

## Contributing

Read [AGENTS.md](AGENTS.md) first. Every change goes through a pull request.

## License

MIT
