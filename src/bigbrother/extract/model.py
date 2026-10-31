"""Talking to Qwen through Ollama, plus a replay model for tests and `--replay`."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from bigbrother.schema import ModelCall

DEFAULT_MODEL = "qwen3:8b"
MAX_RETRIES = 2

T = TypeVar("T", bound=BaseModel)


class ModelError(Exception):
    pass


class Model(Protocol):
    name: str

    def chat_json(self, step: str, messages: list[dict], schema: type[T]) -> tuple[T, ModelCall]: ...


def ollama_host() -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    return host if host.startswith(("http://", "https://")) else f"http://{host}"


class OllamaModel:
    """Asks Ollama for JSON that matches `schema`, and retries with the error if it doesn't."""

    def __init__(self, name: str | None = None, client: httpx.Client | None = None):
        self.name = name or os.environ.get("BIGBROTHER_MODEL", DEFAULT_MODEL)
        self.client = client or httpx.Client(base_url=ollama_host(), timeout=300)

    def chat_json(self, step: str, messages: list[dict], schema: type[T]) -> tuple[T, ModelCall]:
        messages = list(messages)
        last_error = ""
        for attempt in range(1, MAX_RETRIES + 2):
            request = {
                "model": self.name,
                "messages": messages,
                "format": schema.model_json_schema(),
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "seed": 42},
            }
            try:
                response = self.client.post("/api/chat", json=request)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ModelError(f"Ollama request failed: {exc}") from exc

            data = response.json()
            content = data.get("message", {}).get("content", "")
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
                prompt_tokens=data.get("prompt_eval_count"),
                output_tokens=data.get("eval_count"),
                duration_s=data["total_duration"] / 1e9 if "total_duration" in data else None,
            )
            return parsed, call

        raise ModelError(f"no valid {schema.__name__} after {MAX_RETRIES + 1} attempts: {last_error}")


class ReplayModel:
    """Replays saved model calls instead of asking Ollama. Parses them exactly like real ones."""

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
        try:
            return schema.model_validate_json(content), call
        except ValidationError as exc:
            raise ModelError(f"saved {step} response doesn't match {schema.__name__}: {exc}") from exc
