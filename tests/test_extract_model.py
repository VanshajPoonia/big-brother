import json
from pathlib import Path

import httpx
import pytest

from bigbrother.extract.model import ModelError, OllamaModel, ReplayModel, ollama_host
from bigbrother.schema import Extraction, GeneratedScript

SAVED = Path(__file__).parent / "fixtures" / "model"

GOOD = {
    "central_claim": "parse_url fails on long URLs",
    "package": "tinylib",
    "claimed_version": "1.1.0",
    "premises": [],
    "symptom": None,
    "has_steps": True,
}
MESSAGES = [{"role": "user", "content": "parse_url crashes on long URLs"}]


def fake_ollama(*replies, status=200):
    sent = []
    queue = iter(replies)

    def handler(request):
        sent.append(json.loads(request.content))
        body = {
            "model": "qwen3:8b",
            "message": {"role": "assistant", "content": next(queue, "")},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "total_duration": 2_000_000_000,
        }
        return httpx.Response(status, json=body)

    client = httpx.Client(base_url="http://ollama.test", transport=httpx.MockTransport(handler))
    return OllamaModel(name="qwen3:8b", client=client), sent


def test_sends_the_schema_and_fixed_sampling():
    model, sent = fake_ollama(json.dumps(GOOD))
    parsed, call = model.chat_json("extract", MESSAGES, Extraction)

    assert parsed.package == "tinylib"
    assert sent[0]["format"] == Extraction.model_json_schema()
    assert sent[0]["think"] is False
    assert sent[0]["options"] == {"temperature": 0, "seed": 42}
    assert (call.prompt_tokens, call.output_tokens, call.duration_s, call.attempts) == (10, 5, 2.0, 1)


def test_retries_with_the_validation_error():
    model, sent = fake_ollama('{"central_claim": ""}', json.dumps(GOOD))
    _, call = model.chat_json("extract", MESSAGES, Extraction)

    assert call.attempts == 2
    assert "doesn't match the schema" in sent[1]["messages"][-1]["content"]


def test_gives_up_after_three_bad_answers():
    model, sent = fake_ollama("nope", "nope", "nope")
    with pytest.raises(ModelError):
        model.chat_json("extract", MESSAGES, Extraction)
    assert len(sent) == 3


def test_http_errors_become_model_errors():
    model, _ = fake_ollama("", status=500)
    with pytest.raises(ModelError):
        model.chat_json("extract", MESSAGES, Extraction)


def test_replay_parses_saved_calls_like_real_ones():
    model = ReplayModel.from_files(SAVED / "real_bug_extract.json")
    parsed, call = model.chat_json("extract", MESSAGES, Extraction)

    assert parsed.symptom.exception_type == "ValueError"
    assert call.model == "qwen3:8b"


def test_replay_fails_loudly_without_a_saved_step():
    model = ReplayModel.from_files(SAVED / "real_bug_extract.json")
    with pytest.raises(ModelError):
        model.chat_json("repro", MESSAGES, GeneratedScript)


def test_ollama_host_adds_a_scheme(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0:11434")
    assert ollama_host() == "http://0.0.0.0:11434"
