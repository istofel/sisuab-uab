"""Geração do CSV SisUAB em memória."""

import csv
import io
from datetime import datetime

from core.constants import (
    CSV_FIELD_COUNT,
    CSV_FORBIDDEN_CHARS,
    CSV_FORBIDDEN_LINE_START,
    CSV_SEPARATOR,
    OUTPUT_FILENAME_PATTERN,
)
from core.errors import ExportError
from core.text_utils import nfc


def export_csv(rows: list[tuple[str, ...]], line_ending: str) -> bytes:
    """Gera CSV sem BOM, aspas ou escape; falhas indicam erro de programação."""
    if not rows or line_ending not in {"\n", "\r\n"}:
        raise ExportError("Nenhuma linha ou quebra de linha inválida")
    for row in rows:
        if len(row) != CSV_FIELD_COUNT or any(not isinstance(field, str) for field in row):
            raise ExportError("Registro sem sete campos de texto")
        if row[0].startswith(CSV_FORBIDDEN_LINE_START):
            raise ExportError("Polo começa com caractere proibido")
        if any(
            any(char in field for char in (*CSV_FORBIDDEN_CHARS, CSV_SEPARATOR, "\r", "\n"))
            for field in row
        ):
            raise ExportError("Campo contém caractere proibido")

    buffer = io.StringIO(newline="")
    try:
        writer = csv.writer(
            buffer,
            delimiter=CSV_SEPARATOR,
            quoting=csv.QUOTE_NONE,
            escapechar=None,
            lineterminator=line_ending,
        )
        writer.writerows(rows)
    except csv.Error as exc:
        raise ExportError("Falha ao escrever CSV") from exc
    return nfc(buffer.getvalue()).encode("utf-8")


def output_filename(now: datetime) -> str:
    """Nome do arquivo de saída com horário local fornecido."""
    return now.strftime(OUTPUT_FILENAME_PATTERN)
