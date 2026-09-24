"""Escrita e conferência independente do CSV."""

from pathlib import Path

import pytest

from core.errors import ExportError
from core.export import export_csv
from core.reference import load_reference
from core.verify import verify_csv
from tests.factories import make_cpf


@pytest.fixture(scope="module")
def ref():
    return load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))


def _row(polo: str = "ARAGUAÍNA-TO CIMBA", cpf: str = "01234567890") -> tuple[str, ...]:
    return polo, cpf, "CUR", "aluno@exemplo.com.br", "63", "987654321", "DS"


@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_valid_csv_is_utf8_without_bom_and_ends_with_newline(ref, ending: str) -> None:
    rows = [
        _row("ARAGUAI\u0301NA-TO CIMBA"),
        _row("XAMBIOÁ-TO CENTRO", make_cpf("987654321")),
    ]
    data = export_csv(rows, ending)
    assert not data.startswith(b"\xef\xbb\xbf")
    assert data.endswith(ending.encode())
    assert "ARAGUAÍNA" in data.decode("utf-8")
    assert "XAMBIOÁ" in data.decode("utf-8")
    assert verify_csv(data, ref, ending).ok


@pytest.mark.parametrize(
    ("rows", "ending"),
    [
        ([], "\n"),
        ([("x",)], "\n"),
        ([_row("#POLO")], "\n"),
        ([_row("POLO;X")], "\n"),
        ([_row("ARAGUAÍNA-TO CIMBA")[:-1] + ('a"b',)], "\n"),
        ([_row()], "XX"),
    ],
)
def test_export_rejects_invalid_rows(rows, ending: str) -> None:
    with pytest.raises(ExportError):
        export_csv(rows, ending)


@pytest.mark.parametrize(
    ("data", "check"),
    [
        (b"\xef\xbb\xbf", "V01"),
        (b"\xff", "V02"),
        (b"", "V03"),
        (b"\n", "V04"),
        (b"a;b;c;d;e;f\n", "V05"),
        (b"Polo;CPF;SITUACAO;EMAIL;DDD;TELEFONE;PUBLICO\n", "V06"),
        (b"POLO;12345678900;CUR;alun'o@exemplo.com.br;63;987654321;DS\n", "V07"),
        (b"#POLO;12345678900;CUR;aluno@exemplo.com.br;63;987654321;DS\n", "V08"),
        (b"POLO;12345678900;CUR;aluno@exemplo.com.br;63;987654321;DS\n", "V09"),
        (b"ARAGUAINA-TO CIMBA;12345678900;CUR;sem_email;63;987654321;DS\n", "V10"),
        (b"ARAGUAINA-TO CIMBA;12345678900;cur;aluno@exemplo.com.br;63;987654321;DS\n", "V12"),
    ],
)
def test_verifier_detects_corruption(ref, data: bytes, check: str) -> None:
    report = verify_csv(data, ref, "\n")
    assert not report.ok
    assert check in {failure.check for failure in report.failures}


def test_verifier_rejects_duplicate_cpf(ref) -> None:
    data = export_csv([_row(), _row("XAMBIOÁ-TO CENTRO")], "\n")
    report = verify_csv(data, ref, "\n")
    assert "V11" in {failure.check for failure in report.failures}
