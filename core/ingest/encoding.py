"""Decodificação e identificação de texto tabular."""

import csv
from collections import Counter

from charset_normalizer import from_bytes

from core.constants import DELIMITER_CANDIDATES, HEADER_SYNONYMS, SNIFF_SAMPLE_CHARS, UTF8_BOM
from core.text_utils import header_key, looks_like_student_data, nfc


def decode_text(data: bytes) -> tuple[str, str, bool]:
    """Lê texto em UTF-8, UTF-16 ou codificações latinas sem perder bytes."""
    if data.startswith(UTF8_BOM):
        return nfc(data.decode("utf-8-sig")), "utf-8-sig", False
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return nfc(data.decode("utf-16")), "utf-16", False
    try:
        return nfc(data.decode("utf-8")), "utf-8", False
    except UnicodeDecodeError:
        best = from_bytes(data, cp_isolation=["cp1252", "latin_1"]).best()
        if best is not None:
            return nfc(str(best)), best.encoding, best.chaos > 0.2
        return nfc(data.decode("latin-1")), "latin-1", True


def detect_delimiter(text: str) -> tuple[str | None, bool]:
    """Escolhe separador apenas quando pelo menos 80% das linhas são consistentes."""
    sample = text[:SNIFF_SAMPLE_CHARS]
    lines = [line for line in sample.splitlines() if line.strip()]
    if not lines:
        return None, False
    candidates: list[str] = []
    for delimiter in DELIMITER_CANDIDATES:
        try:
            counts = [len(next(csv.reader([line], delimiter=delimiter))) for line in lines]
        except csv.Error:
            continue
        common, frequency = Counter(counts).most_common(1)[0]
        if common >= 2 and frequency / len(lines) >= 0.8:
            candidates.append(delimiter)
    if not candidates:
        return None, False
    try:
        sniffed = csv.Sniffer().sniff(sample, delimiters=DELIMITER_CANDIDATES).delimiter
    except csv.Error:
        sniffed = candidates[0]
    return (sniffed if sniffed in candidates else candidates[0]), len(candidates) > 1


def detect_header(first_row: list[str]) -> bool | None:
    """Distingue títulos conhecidos de valores de aluno."""
    if looks_like_student_data(first_row):
        return False
    known = {alias for aliases in HEADER_SYNONYMS.values() for alias in aliases}
    if any(header_key(cell) in known for cell in first_row):
        return True
    return None
