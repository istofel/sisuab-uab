"""Cliente local, filtro de modelos e saída estruturada."""

from unittest.mock import Mock

import pytest
import requests

from core.errors import ConfigError, LLMResponseError, LLMUnavailableError
from core.llm.client import OllamaClient, is_remote_model
from core.llm.schemas import MappingOut


def _response(status: int, payload: dict | None = None, text: str = "") -> Mock:
    response = Mock()
    response.status_code = status
    response.text = text
    response.json.return_value = payload or {}
    response.raise_for_status.side_effect = (
        None if status < 400 else requests.HTTPError(str(status))
    )
    return response


def test_session_ignores_proxy_and_rejects_remote_host() -> None:
    client = OllamaClient("http://localhost:11434", 120)
    assert client._s.trust_env is False
    with pytest.raises(ConfigError):
        OllamaClient("http://192.168.0.10:11434", 120)


def test_cloud_and_remote_models_are_filtered(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient("http://localhost:11434", 120)
    models = [
        {"name": "qwen3.5:9b"},
        {"name": "qwen3.5:cloud"},
        {"name": "x:y-cloud"},
        {"name": "remote:latest", "remote_host": "other"},
    ]
    monkeypatch.setattr(
        client._s, "get", lambda *args, **kwargs: _response(200, {"models": models})
    )
    assert client.list_models() == ["qwen3.5:9b"]
    assert is_remote_model(models[1])
    assert is_remote_model(models[2])
    assert is_remote_model(models[3])


def test_invalid_json_is_retried_once(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient("http://localhost:11434", 120)
    calls: list[dict] = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs["json"])
        content = "not json" if len(calls) == 1 else '{"colunas":[]}'
        return _response(200, {"message": {"content": content}})

    monkeypatch.setattr(client._s, "post", fake_post)
    assert client.chat_structured("qwen3.5:9b", "system", "user", MappingOut).colunas == []
    assert len(calls) == 2


def test_think_400_falls_back_without_think(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient("http://localhost:11434", 120)
    payloads: list[dict] = []

    def fake_post(*args, **kwargs):
        payloads.append(kwargs["json"].copy())
        if len(payloads) == 1:
            return _response(400, text="unknown field think")
        return _response(200, {"message": {"content": '{"colunas":[]}'}})

    monkeypatch.setattr(client._s, "post", fake_post)
    client.chat_structured("qwen3.5:9b", "system", "user", MappingOut)
    assert "think" in payloads[0]
    assert "think" not in payloads[1]


def test_timeout_and_invalid_responses_raise_domain_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient("http://localhost:11434", 120)

    def timeout(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(client._s, "post", timeout)
    with pytest.raises(LLMUnavailableError):
        client.chat_structured("qwen3.5:9b", "system", "user", MappingOut)
    monkeypatch.setattr(
        client._s,
        "post",
        lambda *args, **kwargs: _response(200, {"message": {"content": "{"}}),
    )
    with pytest.raises(LLMResponseError):
        client.chat_structured("qwen3.5:9b", "system", "user", MappingOut)
