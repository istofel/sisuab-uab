"""Normalização Unicode e identificação de texto."""

from core.messages import msg
from core.models import Severity
from core.text_utils import ascii_digits, header_key, looks_like_student_data, nfc, search_key


def test_nfd_becomes_nfc() -> None:
    assert nfc("ARAGUAI\u0301NA") == "ARAGUAÍNA"


def test_ascii_digits_ignore_unicode_superscript() -> None:
    assert ascii_digits("6²1") == "61"


def test_search_key_ignores_accents_case_and_extra_spaces() -> None:
    assert search_key("Araguaína  ") == search_key("ARAGUAINA")
    assert header_key("Nº do CPF") == "nodocpf"


def test_student_hint_detects_cpf_and_email() -> None:
    assert looks_like_student_data(["CPF: 123.456.789-09"])
    assert looks_like_student_data(["aluno@exemplo.com.br"])
    assert not looks_like_student_data(["Lista de presença"])


def test_message_catalog_formats_severity() -> None:
    assert msg("CPF_AUSENTE") == (Severity.ERRO, "CPF não informado.")
