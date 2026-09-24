"""CSV, XLSX, XLS, JSON e descarte de linhas."""

import pytest

from core.ingest.discard import split_rows
from core.ingest.tabular import read_delimited, read_excel, read_json
from core.models import FileFormat
from tests.factories import make_csv, make_xls, make_xlsx


def test_csv_header_and_empty_line_count() -> None:
    text = make_csv(
        [["01234567890", "aluno@exemplo.com.br"], ["", ""]],
        header=["CPF", "Email"],
    ).decode()
    table = read_delimited(text, ";")
    assert table.header == ["CPF", "Email"]
    assert table.rows == [["01234567890", "aluno@exemplo.com.br"]]
    assert table.row_numbers == [2]
    assert table.empty_lines == 1


@pytest.mark.parametrize("fmt", [FileFormat.XLSX, FileFormat.XLS])
def test_numeric_cpf_is_preserved_as_text(fmt: FileFormat) -> None:
    rows = [["CPF", "Email"], [1234567890, "aluno@exemplo.com.br"], [None, None]]
    data = make_xlsx({"Alunos": rows}) if fmt == FileFormat.XLSX else make_xls(rows)
    table = read_excel(data, fmt)[0]
    assert table.header == ["CPF", "Email"]
    assert table.rows[0][0] == "1234567890"
    assert all(isinstance(cell, str) for row in table.rows for cell in row)


def test_multiple_xlsx_sheets() -> None:
    data = make_xlsx({"A": [["CPF"], ["01234567890"]], "B": [["CPF"], ["98765432100"]]})
    assert [table.sheet for table in read_excel(data, FileFormat.XLSX)] == ["A", "B"]


@pytest.mark.parametrize("wrapped", [False, True])
def test_json_list_and_wrapped_dict(wrapped: bool) -> None:
    data = (
        b'{"alunos":[{"CPF":1234567890,"Email":null}]}'
        if wrapped
        else b'[{"CPF":1234567890,"Email":null}]'
    )
    table = read_json(data)
    assert table.header == ["CPF", "Email"]
    assert table.rows == [["1234567890", ""]]


def test_discard_summary_line() -> None:
    table = read_delimited("CPF;Email\n01234567890;aluno@exemplo.com.br\nTotal: 35;\n", ";")
    kept, discarded = split_rows(table)
    assert len(kept) == 1
    assert len(discarded) == 1
    assert discarded[0].values == ["Total: 35", ""]
