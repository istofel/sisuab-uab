"""Leitura das listas locais de polos e DDDs."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from core.constants import POLO_MAX_LEN
from core.errors import ConfigError


@dataclass(frozen=True, slots=True)
class Reference:
    """Valores válidos carregados de arquivos editáveis."""

    polos: tuple[str, ...]
    polos_set: frozenset[str]
    ddds: frozenset[str]


def _read_lines(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(str(path), "arquivo ausente ou ilegível") from exc
    return [
        unicodedata.normalize("NFC", line.strip()) for line in content.splitlines() if line.strip()
    ]


def load_reference(polos_path: Path, ddds_path: Path) -> Reference:
    """Carrega e valida as listas de referência em UTF-8."""
    polos = _read_lines(polos_path)
    if not polos:
        raise ConfigError(str(polos_path), "lista vazia")
    if any(len(polo) > POLO_MAX_LEN or polo.startswith(("#", ";")) for polo in polos):
        raise ConfigError(str(polos_path), "polo inválido")
    if len(polos) != len(set(polos)):
        raise ConfigError(str(polos_path), "polo repetido")

    ddd_list = _read_lines(ddds_path)
    if not ddd_list:
        raise ConfigError(str(ddds_path), "lista vazia")
    if any(re.fullmatch(r"[0-9]{2}", ddd) is None for ddd in ddd_list):
        raise ConfigError(str(ddds_path), "DDD inválido")
    if len(ddd_list) != len(set(ddd_list)):
        raise ConfigError(str(ddds_path), "DDD repetido")

    return Reference(tuple(polos), frozenset(polos), frozenset(ddd_list))
