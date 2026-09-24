"""Operações de texto usadas em todo o pipeline."""

import re
import unicodedata
from collections.abc import Iterable

CPF_LIKE_RE = re.compile(r"(?<![0-9])[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}(?![0-9])")
PHONE_LIKE_RE = re.compile(r"(?<![0-9])(?:\(?[0-9]{2}\)?\s?)?9?[0-9]{4}-?[0-9]{4}(?![0-9])")
SCI_NOTATION_RE = re.compile(r"^[0-9]+(?:[.,][0-9]+)?[eE][+-]?[0-9]+$")


def nfc(value: str) -> str:
    """Normaliza texto para a forma Unicode NFC."""
    return unicodedata.normalize("NFC", value)


def trim(value: str) -> str:
    """Remove espaços Unicode das pontas."""
    return nfc(value.strip())


def remove_spaces(value: str) -> str:
    """Remove todos os espaços Unicode."""
    return re.sub(r"\s", "", nfc(value))


def ascii_digits(value: str) -> str:
    """Conserva apenas dígitos ASCII."""
    return re.sub(r"[^0-9]", "", value)


def is_ascii_digits(value: str) -> bool:
    """Indica se o texto contém somente dígitos ASCII."""
    return re.fullmatch(r"[0-9]+", value) is not None


def strip_accents(value: str) -> str:
    """Remove marcas combinantes para comparação aproximada."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def search_key(value: str) -> str:
    """Forma de busca sem acentos, caixa ou espaços repetidos."""
    return " ".join(strip_accents(value).casefold().split())


def header_key(value: str) -> str:
    """Forma de busca para títulos de coluna."""
    return re.sub(r"[^a-z0-9]", "", strip_accents(value).casefold())


def looks_like_student_data(values: Iterable[str]) -> bool:
    """Detecta indícios de CPF, e-mail ou telefone em texto livre."""
    return any(
        CPF_LIKE_RE.search(value) is not None
        or "@" in value
        or PHONE_LIKE_RE.search(value) is not None
        for value in values
    )
