"""Codificações, separadores e cabeçalhos."""

import pytest

from core.ingest.encoding import decode_text, detect_delimiter, detect_header


@pytest.mark.parametrize(
    ("data", "expected_text", "expected_encoding"),
    [
        ("ARAGUAÍNA".encode(), "ARAGUAÍNA", "utf-8"),
        ("ARAGUAÍNA".encode("utf-8-sig"), "ARAGUAÍNA", "utf-8-sig"),
        ("ARAGUAÍNA".encode("utf-16"), "ARAGUAÍNA", "utf-16"),
    ],
)
def test_unicode_decoding(data: bytes, expected_text: str, expected_encoding: str) -> None:
    text, encoding, uncertain = decode_text(data)
    assert (text, encoding, uncertain) == (expected_text, expected_encoding, False)


def test_cp1252_and_latin1_decoding() -> None:
    cp_text, cp_encoding, _ = decode_text("Preço €".encode("cp1252"))
    assert cp_text == "Preço €"
    assert cp_encoding == "cp1252"
    latin_text, latin_encoding, _ = decode_text(b"abc\x81")
    assert latin_text == "abc\x81"
    assert latin_encoding in {"latin_1", "latin-1"}


@pytest.mark.parametrize("delimiter", [";", ",", "\t"])
def test_detect_consistent_delimiter(delimiter: str) -> None:
    text = f"CPF{delimiter}Email\n01234567890{delimiter}aluno@exemplo.com.br\n"
    assert detect_delimiter(text)[0] == delimiter


def test_inconsistent_text_has_no_delimiter() -> None:
    assert detect_delimiter("Um aluno qualquer\nOutro aluno\n") == (None, False)


def test_header_true_false_and_unknown() -> None:
    assert detect_header(["CPF", "E-mail", "Polo"]) is True
    assert detect_header(["01234567890", "aluno@exemplo.com.br"]) is False
    assert detect_header(["Coluna A", "Coluna B"]) is None
