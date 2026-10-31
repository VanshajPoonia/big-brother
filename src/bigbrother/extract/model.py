"""Talking to the model, plus a replay model for tests and `--replay`.

Two ways to reach it: Ollama's own API (the default) or the /v1/chat/completions API that
llama.cpp's llama-server, vLLM, LM Studio and Ollama all serve. Either way the model is open-weight
and runs on this machine: `local_only` refuses any other host before a request is sent.
"""

from __future__ import annotations

import ipaddress
import json
import os
import time
from pathlib import Path
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from bigbrother.schema import ModelCall

DEFAULT_MODEL = "qwen3:4b"
MAX_RETRIES = 2

T = TypeVar("T", bound=BaseModel)


class ModelError(Exception):
    pass


class Model(Protocol):
    name: str

    def chat_json(self, step: str, messages: list[dict], schema: type[T]) -> tuple[T, ModelCall]: ...


def local_only(url: str) -> str:
    """Return `url` if it points at this machine, so issue text never leaves the laptop."""
    host = httpx.URL(url).host
    try:
        ip = ipaddress.ip_address(host)
        local = ip.is_loopback or ip.is_unspecified
    except ValueError:
        local = host == "localhost"
    if not local:
        raise ModelError(f"the model must run on this machine, refusing {url or 'an empty host'}")
    return url


def _local_client(base_url: str, client: httpx.Client | None) -> httpx.Client:
    # trust_env=False so a proxy setting can't route the call off the machine. httpx doesn't
    # follow redirects unless asked, so a local server can't bounce us elsewhere either.
    client = client or httpx.Client(base_url=base_url, timeout=300, trust_env=False)
    local_only(str(client.base_url))
    return client


def ollama_host() -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    return host if host.startswith(("http://", "https://")) else f"http://{host}"


def _post(client: httpx.Client, path: str, request: dict) -> dict:
    try:
        response = client.post(path, json=request)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ModelError(f"model request failed: {exc}") from exc


class _RetryingModel:
    """Asks for JSON that matches `schema`, and retries with the error if it doesn't."""

    name: str

    def _send(self, messages: list[dict], schema: type[BaseModel]) -> tuple[dict, dict, str, dict]:
        raise NotImplementedError

    def chat_json(self, step: str, messages: list[dict], schema: type[T]) -> tuple[T, ModelCall]:
        messages = list(messages)
        last_error = ""
        for attempt in range(1, MAX_RETRIES + 2):
            request, data, content, usage = self._send(messages, schema)
            try:
                parsed = schema.model_validate_json(content)
            except ValidationError as exc:
                last_error = str(exc)
                messages += [
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": f"That JSON doesn't match the schema:\n{exc}\nReply again with valid JSON only."},
                ]
                continue
            call = ModelCall(
                step=step,
                model=data.get("model", self.name),
                request=request,
                response=data,
                attempts=attempt,
                **usage,
            )
            return parsed, call

        raise ModelError(f"no valid {schema.__name__} after {MAX_RETRIES + 1} attempts: {last_error}")


class OllamaModel(_RetryingModel):
    def __init__(self, name: str | None = None, client: httpx.Client | None = None):
        self.name = name or os.environ.get("BIGBROTHER_MODEL", DEFAULT_MODEL)
        self.client = _local_client(ollama_host(), client)

    def _send(self, messages, schema):
        request = {
            "model": self.name,
            "messages": messages,
            "format": schema.model_json_schema(),
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "seed": 42},
        }
        data = _post(self.client, "/api/chat", request)
        content = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count"),
            "output_tokens": data.get("eval_count"),
            "duration_s": data["total_duration"] / 1e9 if "total_duration" in data else None,
        }
        return request, data, content, usage


class LlamaServerModel(_RetryingModel):
    """Any server on this machine with llama.cpp's /v1/chat/completions endpoint, running an open-weight model."""

    def __init__(self, name: str | None = None, base_url: str | None = None, client: httpx.Client | None = None):
        self.name = name or os.environ.get("BIGBROTHER_MODEL", DEFAULT_MODEL)
        base_url = base_url or os.environ.get("BIGBROTHER_BASE_URL", f"{ollama_host()}/v1")
        self.client = _local_client(base_url, client)

    def _send(self, messages, schema):
        request = {
            "model": self.name,
            "messages": messages,
            "temperature": 0,
            "seed": 42,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema(), "strict": True},
            },
        }
        started = time.monotonic()
        data = _post(self.client, "/chat/completions", request)
        choices = data.get("choices") or [{}]
        content = choices[0].get("message", {}).get("content") or ""
        usage = data.get("usage") or {}
        return request, data, content, {
            "prompt_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
            "duration_s": round(time.monotonic() - started, 3),
        }


def default_model() -> Model:
    """Pick the client from BIGBROTHER_API: `ollama` (default) or `llamacpp` for any llama.cpp-style server."""
    api = os.environ.get("BIGBROTHER_API", "ollama")
    if api == "ollama":
        return OllamaModel()
    if api == "llamacpp":
        return LlamaServerModel()
    raise ModelError(f"unknown BIGBROTHER_API {api!r}, use ollama or llamacpp")


class ReplayModel:
    """Replays saved model calls instead of asking a server. Parses them exactly like real ones."""

    def __init__(self, calls: list[ModelCall]):
        self.calls = {call.step: call for call in calls}
        self.name = calls[0].model if calls else DEFAULT_MODEL

    @classmethod
    def from_files(cls, *paths: Path) -> ReplayModel:
        return cls([ModelCall.model_validate(json.loads(Path(p).read_text())) for p in paths])

    def chat_json(self, step: str, messages: list[dict], schema: type[T]) -> tuple[T, ModelCall]:
        if step not in self.calls:
            raise ModelError(f"no saved response for step {step!r}")
        call = self.calls[step]
        content = call.response.get("message", {}).get("content", "")
        if not content and call.response.get("choices"):
            content = call.response["choices"][0].get("message", {}).get("content") or ""
        try:
            return schema.model_validate_json(content), call
        except ValidationError as exc:
            raise ModelError(f"saved {step} response doesn't match {schema.__name__}: {exc}") from exc
