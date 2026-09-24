"""Configuração e arquivos de referência."""

from pathlib import Path

import pytest

from core.errors import ConfigError
from core.reference import load_reference
from core.settings import load_settings


def test_reference_has_expected_polos_and_ddds() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    assert len(ref.polos) == 23
    assert len(ref.ddds) == 67
    assert "ARAGUAÍNA-TO CIMBA" in ref.polos_set
    assert "63" in ref.ddds


@pytest.mark.parametrize(
    ("key", "value"),
    [("OLLAMA_BASE_URL", "http://192.168.0.10:11434"), ("CSV_LINE_ENDING", "XX")],
)
def test_invalid_settings_raise_config_error(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ConfigError) as error:
        load_settings()
    assert error.value.key == key.lower()


def test_repeated_polo_is_rejected(tmp_path: Path) -> None:
    polos_path = tmp_path / "polos.txt"
    polos_path.write_text("ARAGUAÍNA-TO CIMBA\nARAGUAI\u0301NA-TO CIMBA\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="polo repetido"):
        load_reference(polos_path, Path("config/ddds.txt"))


def test_reference_rejects_non_ascii_ddd(tmp_path: Path) -> None:
    ddds_path = tmp_path / "ddds.txt"
    ddds_path.write_text("6²\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="DDD inválido"):
        load_reference(Path("config/polos.txt"), ddds_path)
