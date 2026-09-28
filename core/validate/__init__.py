"""Validação determinística de registros."""

from core.constants import FIELDS
from core.messages import msg, phone_orientation
from core.models import (
    Counts,
    Issue,
    ReadMethod,
    Record,
    Severity,
    SourceFile,
    Suggestion,
    ValidationResult,
)
from core.normalize import normalize
from core.reference import Reference
from core.validate.context import context_issues
from core.validate.cpf import validate_cpf
from core.validate.duplicates import find_duplicates
from core.validate.fields import (
    validate_ddd,
    validate_email,
    validate_polo,
    validate_publico,
    validate_situacao,
    validate_telefone,
)


def validate_all(
    records: list[Record],
    files: dict[str, SourceFile],
    ref: Reference,
    periodo: int | None,
    dismissed: set[tuple],
) -> ValidationResult:
    """Normaliza, valida e conta todos os registros não excluídos."""
    effective: dict[int, dict[str, str]] = {}
    issues: list[Issue] = []
    suggestions: list[Suggestion] = []
    locators: dict[int, str] = {}

    for record in records:
        if record.deleted:
            continue
        normalized = normalize(record.input)
        values = normalized.values.copy()
        locators[record.id] = f"{record.source_name}, {record.locator}"

        polo_code, polo_suggestion = validate_polo(values["polo"], ref)
        cpf_code = validate_cpf(values["cpf"], normalized.cpf_scientific)
        situacao_code, values["situacao"] = validate_situacao(values["situacao"])
        email_code = validate_email(values["email"])
        ddd_code = validate_ddd(values["ddd"], normalized.ddd_conflict, ref)
        phone_code, phone_suggestion = validate_telefone(
            values["telefone"], normalized.phone_prefixed
        )
        publico_code, values["publico_alvo"] = validate_publico(values["publico_alvo"])

        field_codes = {
            "polo": polo_code,
            "cpf": cpf_code,
            "situacao": situacao_code,
            "email": email_code,
            "ddd": ddd_code,
            "telefone": phone_code,
            "publico_alvo": publico_code,
        }
        for field in FIELDS:
            code = field_codes[field]
            if code is None:
                continue
            kwargs = {"valor": values[field]}
            if code == "POLO_SUGESTAO":
                kwargs["sugestao"] = polo_suggestion or ""
            elif code == "DDD_CONFLITO":
                kwargs["telefone"] = normalized.ddd_from_phone or ""
            elif code == "TEL_8_DIGITOS":
                kwargs["orientacao"] = phone_orientation(phone_suggestion is not None)
            severity, message = msg(code, **kwargs)
            issues.append(Issue(record.id, field, severity, code, message))

        if polo_suggestion:
            suggestions.append(
                Suggestion(
                    record.id,
                    "polo",
                    record.input.get("polo", ""),
                    polo_suggestion,
                    "POLO_SUGESTAO",
                )
            )
        if phone_suggestion and not normalized.ddd_conflict:
            suggestions.append(
                Suggestion(
                    record.id,
                    "telefone",
                    record.input.get("telefone", ""),
                    phone_suggestion,
                    "TEL_8_DIGITOS",
                )
            )

        if (
            record.method == ReadMethod.IA
            and record.input.get("cpf") == record.original.get("cpf")
            and values["cpf"] not in files[record.source_id].ai_source_cpfs
        ):
            severity, message = msg("CPF_NAO_ENCONTRADO_ORIGEM")
            issues.append(Issue(record.id, "cpf", severity, "CPF_NAO_ENCONTRADO_ORIGEM", message))
        issues.extend(context_issues(record.id, values["situacao"], periodo))
        effective[record.id] = values

    issues.extend(find_duplicates(effective, locators))
    suggestions = [suggestion for suggestion in suggestions if suggestion.key not in dismissed]

    by_record: dict[int, list[Issue]] = {record_id: [] for record_id in effective}
    for issue in issues:
        by_record[issue.record_id].append(issue)

    with_error = sum(
        any(issue.severity == Severity.ERRO for issue in row_issues)
        for row_issues in by_record.values()
    )
    only_warning = sum(
        any(issue.severity == Severity.AVISO for issue in row_issues)
        and not any(issue.severity == Severity.ERRO for issue in row_issues)
        for row_issues in by_record.values()
    )
    total = len(effective)
    discarded = sum(len(source.discarded) for source in files.values())
    counts = Counts(total, with_error, only_warning, total - with_error - only_warning, discarded)
    return ValidationResult(effective, issues, by_record, suggestions, counts)


def has_blocking_errors(result: ValidationResult) -> bool:
    """Indica se há erro impeditivo de exportação."""
    return result.counts.with_error > 0
