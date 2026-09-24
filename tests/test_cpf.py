"""Regras dos dígitos verificadores do CPF."""

import pytest

from core.text_utils import SCI_NOTATION_RE, ascii_digits
from core.validate.cpf import cpf_check_digits_ok, validate_cpf
from tests.factories import make_cpf


def test_valid_cpf_and_leading_zero() -> None:
    assert make_cpf("012345678") == "01234567890"
    assert cpf_check_digits_ok("01234567890")
    assert validate_cpf("01234567890", False) is None


def test_formatted_cpf_is_valid_after_normalization() -> None:
    assert validate_cpf(ascii_digits("012.345.678-90"), False) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", "CPF_AUSENTE"),
        ("01234567891", "CPF_DV_INVALIDO"),
        ("11111111111", "CPF_REPETIDO"),
        ("012345678901", "CPF_TAMANHO"),
        ("0123456789A", "CPF_NAO_NUMERICO"),
    ],
)
def test_invalid_cpf_cases(value: str, expected: str) -> None:
    assert validate_cpf(value, False) == expected


@pytest.mark.parametrize("value", ["3,42E+10", "3.42e10"])
def test_scientific_notation_is_rejected(value: str) -> None:
    assert SCI_NOTATION_RE.fullmatch(value)
    assert validate_cpf(value, True) == "CPF_CIENTIFICO"
