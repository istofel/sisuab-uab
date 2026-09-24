"""Separação de linhas sem indício de dados de aluno."""

from core.models import DiscardedLine, RawTable
from core.text_utils import looks_like_student_data


def split_rows(table: RawTable) -> tuple[list[tuple[int, list[str]]], list[DiscardedLine]]:
    """Separa registros com indício de aluno das linhas descartadas."""
    kept: list[tuple[int, list[str]]] = []
    discarded: list[DiscardedLine] = []
    for number, values in zip(table.row_numbers, table.rows, strict=True):
        if looks_like_student_data(values):
            kept.append((number, values))
        else:
            prefix = f"{table.sheet}, " if table.sheet else ""
            discarded.append(DiscardedLine(f"{prefix}linha {number}", values))
    return kept, discarded
