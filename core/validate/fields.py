"""Validação dos campos além do CPF."""

from email_validator import EmailNotValidError
from email_validator import validate_email as check_email

from core.constants import (
    EMAIL_FORBIDDEN_CHARS,
    EMAIL_MAX_LEN,
    PUBLICO_PADRAO,
    PUBLICOS,
    SITUACAO_PADRAO,
    SITUACOES,
    TEL_MOBILE_FIRST_DIGITS,
    TELEFONE_LEN,
)
from core.reference import Reference
from core.suggest import suggest_polo
from core.text_utils import is_ascii_digits


def validate_polo(value: str, ref: Reference) -> tuple[str | None, str | None]:
    """Retorna erro e possível sugestão de polo."""
    if not value:
        return "POLO_AUSENTE", None
    if value in ref.polos_set:
        return None, None
    if len(value) > 80:
        return "POLO_TAMANHO", None
    suggestion = suggest_polo(value, ref)
    if suggestion:
        return "POLO_SUGESTAO", suggestion
    return "POLO_INVALIDO", None


def validate_situacao(value: str) -> tuple[str | None, str]:
    """Valida a situação e aplica o padrão somente ao valor efetivo."""
    if not value:
        return "SITUACAO_PADRAO", SITUACAO_PADRAO
    if value not in SITUACOES:
        return "SITUACAO_INVALIDA", value
    return None, value


def validate_email(value: str) -> str | None:
    """Valida e-mail sem DNS e sem alterar o texto original."""
    if not value:
        return "EMAIL_AUSENTE"
    if any(char in value for char in EMAIL_FORBIDDEN_CHARS):
        return "EMAIL_CARACTERE"
    if not value.isascii():
        return "EMAIL_NAO_ASCII"
    if len(value) > EMAIL_MAX_LEN:
        return "EMAIL_TAMANHO"
    try:
        check_email(value, check_deliverability=False, allow_smtputf8=False)
    except EmailNotValidError:
        return "EMAIL_INVALIDO"
    return None


def validate_ddd(value: str, conflict: bool, ref: Reference) -> str | None:
    """Confere DDD normalizado com a lista editável."""
    if not value:
        return "DDD_AUSENTE"
    if conflict:
        return "DDD_CONFLITO"
    if len(value) != 2 or not is_ascii_digits(value) or value not in ref.ddds:
        return "DDD_INVALIDO"
    return None


def validate_telefone(value: str, prefixed: bool) -> tuple[str | None, str | None]:
    """Confere celular de nove dígitos e propõe correção apenas quando cabível."""
    if not value:
        return "TEL_AUSENTE", None
    if prefixed:
        return "TEL_TAMANHO", None
    if len(value) == 8:
        proposal = "9" + value if value[0] in TEL_MOBILE_FIRST_DIGITS else None
        return "TEL_8_DIGITOS", proposal
    if len(value) != TELEFONE_LEN or not is_ascii_digits(value):
        return "TEL_TAMANHO", None
    return None, None


def validate_publico(value: str) -> tuple[str | None, str]:
    """Valida público-alvo e aplica o padrão só ao valor efetivo."""
    if not value:
        return "PUBLICO_PADRAO", PUBLICO_PADRAO
    if value not in PUBLICOS:
        return "PUBLICO_INVALIDO", value
    return None, value
