import json
from pathlib import Path

import httpx
import pytest

from bigbrother.extract.model import (
    DEFAULT_MODEL,
    ModelError,
    OllamaModel,
    LlamaServerModel,
    ReplayModel,
    default_model,
    local_only,
    ollama_host,
)
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
            "model": "qwen3:4b",
            "message": {"role": "assistant", "content": next(queue, "")},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "total_duration": 2_000_000_000,
        }
        return httpx.Response(status, json=body)

    client = httpx.Client(base_url="http://localhost:11434", transport=httpx.MockTransport(handler))
    return OllamaModel(name="qwen3:4b", client=client), sent


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
    assert call.model == "qwen3:4b"


def test_replay_fails_loudly_without_a_saved_step():
    model = ReplayModel.from_files(SAVED / "real_bug_extract.json")
    with pytest.raises(ModelError):
        model.chat_json("repro", MESSAGES, GeneratedScript)


def test_ollama_host_adds_a_scheme(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0:11434")
    assert ollama_host() == "http://0.0.0.0:11434"


def test_default_is_the_small_model(monkeypatch):
    monkeypatch.delenv("BIGBROTHER_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert DEFAULT_MODEL == "qwen3:4b"
    assert OllamaModel().name == "qwen3:4b"


def test_llama_cpp_style_servers_work_too():
    sent = []

    def handler(request):
        sent.append((request.url.path, json.loads(request.content)))
        body = {
            "model": "qwen3:4b",
            "choices": [{"message": {"role": "assistant", "content": json.dumps(GOOD)}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 7},
        }
        return httpx.Response(200, json=body)

    client = httpx.Client(base_url="http://127.0.0.1:8080/v1", transport=httpx.MockTransport(handler))
    parsed, call = LlamaServerModel(name="qwen3:4b", client=client).chat_json("extract", MESSAGES, Extraction)

    path, request = sent[0]
    assert path == "/v1/chat/completions"
    assert request["response_format"]["json_schema"]["schema"] == Extraction.model_json_schema()
    assert request["temperature"] == 0
    assert parsed.package == "tinylib"
    assert (call.prompt_tokens, call.output_tokens) == (12, 7)


def test_default_model_follows_the_environment(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("BIGBROTHER_BASE_URL", raising=False)
    monkeypatch.setenv("BIGBROTHER_API", "llamacpp")
    assert isinstance(default_model(), LlamaServerModel)
    monkeypatch.setenv("BIGBROTHER_API", "ollama")
    assert isinstance(default_model(), OllamaModel)
    monkeypatch.setenv("BIGBROTHER_API", "cloud")
    with pytest.raises(ModelError):
        default_model()


@pytest.mark.parametrize("url", ["http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434", "http://0.0.0.0:11434"])
def test_models_on_this_machine_are_allowed(url):
    assert local_only(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com/v1",
        "http://192.168.1.20:11434",
        "http://10.0.0.5:11434",
        "http://localhost.example.com:11434",
        "http://ollama.test",
        "",
    ],
)
def test_models_anywhere_else_are_refused(url):
    with pytest.raises(ModelError, match="must run on this machine"):
        local_only(url)


def test_settings_cannot_send_the_model_off_the_machine(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "192.168.1.20:11434")
    with pytest.raises(ModelError):
        OllamaModel()
    monkeypatch.delenv("OLLAMA_HOST")
    monkeypatch.setenv("BIGBROTHER_BASE_URL", "https://api.example.com/v1")
    with pytest.raises(ModelError):
        LlamaServerModel()


def test_a_passed_in_client_is_checked_too():
    with pytest.raises(ModelError):
        OllamaModel(client=httpx.Client(base_url="https://api.example.com"))


def test_proxies_and_redirects_are_ignored(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.com:3128")
    client = OllamaModel().client
    assert client.trust_env is False
    assert client.follow_redirects is False
