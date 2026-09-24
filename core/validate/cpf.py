"""Dígitos verificadores e erros de CPF."""

from core.text_utils import is_ascii_digits


def cpf_check_digits_ok(cpf: str) -> bool:
    """Confere os dois dígitos verificadores de um CPF ASCII de 11 dígitos."""
    if len(cpf) != 11 or not is_ascii_digits(cpf) or len(set(cpf)) == 1:
        return False
    first = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11
    first = 0 if first == 10 else first
    second = (sum(int(cpf[i]) * (11 - i) for i in range(10)) * 10) % 11
    second = 0 if second == 10 else second
    return first == int(cpf[9]) and second == int(cpf[10])


def validate_cpf(value: str, scientific: bool) -> str | None:
    """Retorna o código do primeiro erro ou None."""
    if not value:
        return "CPF_AUSENTE"
    if scientific:
        return "CPF_CIENTIFICO"
    if not is_ascii_digits(value):
        return "CPF_NAO_NUMERICO"
    if len(value) > 11:
        return "CPF_TAMANHO"
    if len(set(value)) == 1:
        return "CPF_REPETIDO"
    if not cpf_check_digits_ok(value):
        return "CPF_DV_INVALIDO"
    return None
