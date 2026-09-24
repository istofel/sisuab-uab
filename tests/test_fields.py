"""Validação dos seis campos além do CPF."""

from pathlib import Path

import pytest

from core.reference import load_reference
from core.validate.fields import (
    validate_ddd,
    validate_email,
    validate_polo,
    validate_publico,
    validate_situacao,
    validate_telefone,
)


@pytest.fixture(scope="module")
def ref():
    return load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))


def test_exact_approximate_and_missing_polo(ref) -> None:
    assert validate_polo("ARAGUAÍNA-TO CIMBA", ref) == (None, None)
    assert validate_polo("ARAGUAINA-TO CIMBA", ref) == ("POLO_SUGESTAO", "ARAGUAÍNA-TO CIMBA")
    assert validate_polo("", ref) == ("POLO_AUSENTE", None)


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("alunó@exemplo.com.br", "EMAIL_NAO_ASCII"),
        ("a'luno@exemplo.com.br", "EMAIL_CARACTERE"),
        ("a" * 47 + "@exemplo.com.br", "EMAIL_TAMANHO"),
        ("aluno@exemplo.com.br", None),
    ],
)
def test_email_rules(value: str, code: str | None) -> None:
    assert validate_email(value) == code


def test_ddd_and_phone_rules(ref) -> None:
    assert validate_ddd("63", False, ref) is None
    assert validate_ddd("63", True, ref) == "DDD_CONFLITO"
    assert validate_telefone("98765432", False) == ("TEL_8_DIGITOS", "998765432")
    assert validate_telefone("34567890", False) == ("TEL_8_DIGITOS", None)
    assert validate_telefone("987654321", False) == (None, None)


def test_defaults_are_returned_for_missing_status_and_publico() -> None:
    assert validate_situacao("") == ("SITUACAO_PADRAO", "CUR")
    assert validate_publico("") == ("PUBLICO_PADRAO", "DS")


def test_invalid_and_missing_fields(ref) -> None:
    assert validate_polo("X" * 81, ref) == ("POLO_TAMANHO", None)
    assert validate_polo("CIDADE INEXISTENTE", ref) == ("POLO_INVALIDO", None)
    assert validate_situacao("XXX") == ("SITUACAO_INVALIDA", "XXX")
    assert validate_email("") == "EMAIL_AUSENTE"
    assert validate_email("sem-arroba") == "EMAIL_INVALIDO"
    assert validate_ddd("", False, ref) == "DDD_AUSENTE"
    assert validate_ddd("00", False, ref) == "DDD_INVALIDO"
    assert validate_telefone("", False) == ("TEL_AUSENTE", None)
    assert validate_telefone("55987654321", True) == ("TEL_TAMANHO", None)
    assert validate_telefone("123", False) == ("TEL_TAMANHO", None)
    assert validate_publico("XX") == ("PUBLICO_INVALIDO", "XX")
