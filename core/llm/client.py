"""Único módulo de rede: cliente HTTP do Ollama local."""

import json
from dataclasses import dataclass
from typing import TypeVar
from urllib.parse import urlsplit

import requests
from pydantic import BaseModel, ValidationError

from core.constants import (
    ALLOWED_OLLAMA_HOSTS,
    LLM_CONNECT_TIMEOUT_S,
    LLM_INVALID_RESPONSE_RETRIES,
    LLM_KEEP_ALIVE,
    LLM_NUM_CTX,
    LLM_SEED,
    LLM_STATUS_TIMEOUT_S,
    LLM_TEMPERATURE,
)
from core.errors import ConfigError, LLMResponseError, LLMUnavailableError

T = TypeVar("T", bound=BaseModel)


@dataclass(slots=True)
class LLMStatus:
    """Resultado da verificação do provedor local."""

    online: bool
    version: str | None
    error: str | None


def is_remote_model(model: dict) -> bool:
    """Rejeita modelos hospedados fora da máquina pela metadata ou tag."""
    name = str(model.get("name", ""))
    tag = name.split(":", 1)[1].lower() if ":" in name else "latest"
    return bool(model.get("remote_host") or model.get("remote_model")) or (
        tag == "cloud" or tag.endswith("-cloud")
    )


class OllamaClient:
    """Consulta apenas o Ollama no host local autorizado."""

    def __init__(self, base_url: str, timeout_s: int) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_OLLAMA_HOSTS:
            raise ConfigError("OLLAMA_BASE_URL", "host Ollama não permitido")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self._s = requests.Session()
        self._s.trust_env = False

    def status(self) -> LLMStatus:
        """Consulta a versão local em até três segundos."""
        try:
            response = self._s.get(
                f"{self.base_url}/api/version",
                timeout=(LLM_CONNECT_TIMEOUT_S, LLM_STATUS_TIMEOUT_S),
            )
            response.raise_for_status()
            version = response.json().get("version")
            return LLMStatus(True, str(version) if version is not None else None, None)
        except (requests.RequestException, ValueError):
            return LLMStatus(False, None, "OLLAMA_INDISPONIVEL")

    def list_models(self) -> list[str]:
        """Lista somente modelos locais instalados."""
        try:
            response = self._s.get(
                f"{self.base_url}/api/tags",
                timeout=(LLM_CONNECT_TIMEOUT_S, LLM_STATUS_TIMEOUT_S),
            )
            response.raise_for_status()
            models = response.json().get("models", [])
        except (requests.RequestException, ValueError):
            return []
        return sorted(
            str(model["name"])
            for model in models
            if isinstance(model, dict) and model.get("name") and not is_remote_model(model)
        )

    def chat_structured(self, model: str, system: str, user: str, schema_model: type[T]) -> T:
        """Solicita JSON com schema e valida antes de devolver ao domínio."""
        if is_remote_model({"name": model}):
            raise LLMUnavailableError("modelo remoto não permitido")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": schema_model.model_json_schema(),
            "stream": False,
            "think": False,
            "keep_alive": LLM_KEEP_ALIVE,
            "options": {
                "temperature": LLM_TEMPERATURE,
                "seed": LLM_SEED,
                "num_ctx": LLM_NUM_CTX,
            },
        }
        invalid_attempts = 0
        while invalid_attempts <= LLM_INVALID_RESPONSE_RETRIES:
            try:
                response = self._s.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=(LLM_CONNECT_TIMEOUT_S, self.timeout_s),
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                raise LLMUnavailableError("Ollama indisponível") from exc
            if (
                response.status_code == 400
                and "think" in response.text.lower()
                and "think" in payload
            ):
                payload.pop("think")
                continue
            if response.status_code == 404:
                raise LLMUnavailableError("modelo não instalado")
            try:
                response.raise_for_status()
                content = response.json()["message"]["content"]
                return schema_model.model_validate_json(content)
            except requests.RequestException as exc:
                raise LLMUnavailableError("falha na chamada ao Ollama") from exc
            except (KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError):
                invalid_attempts += 1
        raise LLMResponseError("resposta fora do schema")
