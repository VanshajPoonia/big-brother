# Big Brother

Big Brother is watching your claims.

It reads an issue or pull request, pulls out each technical claim ("crashes on 2.4.1", "fixes #120", "RCE in `parse_url_v2()`") and checks it against the code. You get a verdict per claim with the evidence behind it, or "unverified" when the evidence isn't there.

It runs on a local open-weight model (Qwen3 4B via Ollama). No cloud AI.

Built at Hacktoberfest Hack Day Sonipat by Team Daggers. Work in progress, see [docs/PLAN.md](docs/PLAN.md).

## Install

```
pip install -e ".[dev]"
ollama pull qwen3:4b
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

The model reads the report and writes a repro script when there isn't one, but it never picks the label. Fixed rules do that, based on what version and symbol checks and a sandboxed run actually show. Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

Read [AGENTS.md](AGENTS.md) first. Every change goes through a pull request.

## License

MIT
