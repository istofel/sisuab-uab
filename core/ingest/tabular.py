"""Leitura em memória de CSV, Excel e JSON."""

import csv
import io
import json

import pandas as pd

from core.errors import FileReadError
from core.ingest.encoding import detect_header
from core.models import FileFormat, RawTable, ReadMethod
from core.text_utils import nfc


def _make_table(rows: list[tuple[int, list[str]]], sheet: str | None) -> RawTable:
    """Remove linhas vazias e separa cabeçalho reconhecido."""
    nonempty = [(number, [nfc(cell) for cell in cells]) for number, cells in rows if any(cells)]
    empty_lines = len(rows) - len(nonempty)
    header: list[str] | None = None
    if nonempty and detect_header(nonempty[0][1]) is True:
        _, header = nonempty.pop(0)
    return RawTable(
        sheet=sheet,
        header=header,
        rows=[cells for _, cells in nonempty],
        row_numbers=[number for number, _ in nonempty],
        method=ReadMethod.TABULAR,
        empty_lines=empty_lines,
    )


def read_delimited(text: str, delimiter: str) -> RawTable:
    """Lê linhas delimitadas, preservando a linha física de origem."""
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=False)
        rows = [(reader.line_num, [cell.strip() for cell in cells]) for cells in reader]
    except (csv.Error, ValueError) as exc:
        raise FileReadError("ARQ_ILEGIVEL") from exc
    return _make_table(rows, None)


def read_excel(data: bytes, fmt: FileFormat) -> list[RawTable]:
    """Lê todas as abas de Excel como texto, inclusive CPF numérico."""
    engine = {FileFormat.XLSX: "openpyxl", FileFormat.XLS: "xlrd"}.get(fmt)
    if engine is None:
        raise FileReadError("ARQ_ILEGIVEL")
    try:
        sheets = pd.read_excel(
            io.BytesIO(data),
            sheet_name=None,
            header=None,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
            engine=engine,
        )
    except Exception as exc:
        raise FileReadError("ARQ_ILEGIVEL") from exc
    tables: list[RawTable] = []
    for sheet_name, frame in sheets.items():
        rows = [
            (number, ["" if cell is None else str(cell).strip() for cell in row])
            for number, row in enumerate(frame.itertuples(index=False, name=None), start=1)
        ]
        table = _make_table(rows, sheet_name)
        if table.header is not None or table.rows:
            tables.append(table)
    return tables


def read_json(data: bytes) -> RawTable:
    """Lê lista de objetos ou objeto com uma única lista de objetos."""
    try:
        payload = json.loads(data.decode("utf-8-sig"), parse_float=str, parse_int=str)
        if isinstance(payload, dict) and len(payload) == 1:
            payload = next(iter(payload.values()))
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            raise ValueError("JSON sem lista de objetos")
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FileReadError("ARQ_JSON_FORMATO") from exc

    keys = list(dict.fromkeys(key for item in payload for key in item))
    rows = [
        (number, ["" if item.get(key) is None else str(item[key]) for key in keys])
        for number, item in enumerate(payload, start=1)
    ]
    table = _make_table(rows, None)
    table.header = [nfc(str(key)) for key in keys]
    return table
