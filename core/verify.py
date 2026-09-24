"""Conferência independente dos bytes do CSV de saída."""

from core.constants import CSV_FIELD_COUNT, PUBLICOS, SITUACOES, UTF8_BOM
from core.messages import verify_msg
from core.models import VerifyFailure, VerifyReport
from core.reference import Reference
from core.text_utils import is_ascii_digits
from core.validate.cpf import validate_cpf
from core.validate.fields import validate_ddd, validate_email, validate_telefone


def verify_csv(data: bytes, ref: Reference, line_ending: str) -> VerifyReport:
    """Relê bytes sem usar o gerador e devolve todas as falhas encontradas."""
    failures: list[VerifyFailure] = []

    def fail(line: int | None, code: str) -> None:
        failures.append(VerifyFailure(line, code, verify_msg(code)))

    if data.startswith(UTF8_BOM):
        fail(None, "V01")
    try:
        content = data.decode("utf-8", errors="strict")
    except UnicodeError:
        fail(None, "V02")
        return VerifyReport(False, failures, 0)

    if line_ending not in {"\n", "\r\n"}:
        fail(None, "V03")
        return VerifyReport(False, failures, 0)
    if not content or not content.endswith(line_ending):
        fail(None, "V03")
    if line_ending == "\n" and "\r" in content:
        fail(None, "V03")
    if line_ending == "\r\n" and (
        "\n" in content.replace("\r\n", "") or "\r" in content.replace("\r\n", "")
    ):
        fail(None, "V03")

    lines = content.split(line_ending)
    if lines and lines[-1] == "":
        lines.pop()

    seen_cpfs: set[str] = set()
    for number, line in enumerate(lines, start=1):
        if line == "":
            fail(number, "V04")
            continue
        fields = line.split(";")
        if len(fields) != CSV_FIELD_COUNT:
            fail(number, "V05")
            continue
        polo, cpf, situacao, email, ddd, telefone, publico = fields
        if polo not in ref.polos_set or len(cpf) != 11 or not is_ascii_digits(cpf):
            fail(number, "V06")
        if '"' in line or "'" in line:
            fail(number, "V07")
        if line.startswith(("#", ";")):
            fail(number, "V08")
        if polo not in ref.polos_set:
            fail(number, "V09")
        if (
            validate_cpf(cpf, False) is not None
            or validate_email(email) is not None
            or validate_ddd(ddd, False, ref) is not None
            or validate_telefone(telefone, False)[0] is not None
            or situacao not in SITUACOES
            or publico not in PUBLICOS
        ):
            fail(number, "V10")
        if cpf in seen_cpfs:
            fail(number, "V11")
        seen_cpfs.add(cpf)
        if situacao != situacao.upper() or situacao not in SITUACOES:
            fail(number, "V12")
    return VerifyReport(not failures, failures, len(lines))
