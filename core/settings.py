"""Configuração local da aplicação."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.constants import ALLOWED_OLLAMA_HOSTS, LINE_ENDINGS
from core.errors import ConfigError


class Settings(BaseSettings):
    """Preferências da aplicação, carregadas de ambiente e .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:2b"
    ollama_timeout_s: int = Field(120, ge=10, le=900)
    app_port: int = Field(8501, ge=1024, le=65535)
    csv_line_ending: Literal["LF", "CRLF"] = "LF"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_dir: str = "logs"

    @field_validator("ollama_base_url")
    @classmethod
    def _local_only(cls, value: str) -> str:
        """Aceita apenas URLs HTTP(S) com host local autorizado."""
        candidate = value.strip().rstrip("/")
        try:
            parsed = urlsplit(candidate)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("URL inválida") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in ALLOWED_OLLAMA_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or port == 0
        ):
            raise ValueError("host Ollama não permitido")
        return candidate

    @property
    def line_ending(self) -> str:
        """Retorna a quebra de linha selecionada para o CSV."""
        return LINE_ENDINGS[self.csv_line_ending]


def load_settings() -> Settings:
    """Carrega a configuração e identifica a chave inválida."""
    try:
        return Settings()
    except ValidationError as exc:
        error = exc.errors()[0]
        key = str(error["loc"][0]) if error["loc"] else "config"
        raise ConfigError(key, str(error["msg"])) from exc
