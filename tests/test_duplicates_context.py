"""Duplicidade, contexto e supressão de sugestões."""

from pathlib import Path

from core.models import FileFormat, ReadMethod, Record, SourceFile
from core.reference import load_reference
from core.validate import has_blocking_errors, validate_all
from core.validate.context import context_issues


def _record(record_id: int, source: str, cpf: str, situacao: str = "CUR") -> Record:
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": cpf,
        "situacao": situacao,
        "email": f"aluno{record_id}@exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }
    return Record(
        record_id,
        source,
        source,
        "linha 1",
        (record_id, 1),
        ReadMethod.TABULAR,
        "",
        values.copy(),
        values.copy(),
    )


def test_duplicate_cpf_between_files_even_if_identical() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    files = {
        name: SourceFile(name, name, FileFormat.CSV, 10) for name in ("primeiro.csv", "segundo.csv")
    }
    records = [
        _record(1, "primeiro.csv", "012.345.678-90"),
        _record(2, "segundo.csv", "1234567890"),
    ]
    result = validate_all(records, files, ref, None, set())
    assert result.counts.with_error == 2
    assert [issue.record_id for issue in result.issues if issue.code == "CPF_DUPLICADO"] == [1, 2]
    assert "segundo.csv" in result.by_record[1][-1].message


def test_context_only_warns_for_known_cases() -> None:
    assert context_issues(1, "CAN", 3)[0].code == "SITUACAO_CONTEXTO"
    assert context_issues(1, "DES", 2)[0].code == "SITUACAO_CONTEXTO"
    assert context_issues(1, "TCC", 9) == []
    assert context_issues(1, "CAN", None) == []


def test_dismissed_suggestion_does_not_reappear() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    record = _record(1, "a.csv", "01234567890")
    record.input["polo"] = "ARAGUAINA-TO CIMBA"
    files = {"a.csv": SourceFile("a.csv", "a.csv", FileFormat.CSV, 10)}
    first = validate_all([record], files, ref, None, set())
    assert len(first.suggestions) == 1
    dismissed = {first.suggestions[0].key}
    second = validate_all([record], files, ref, None, dismissed)
    assert second.suggestions == []
    assert second.counts.with_error == 1


def test_ai_cpf_not_in_source_and_phone_suggestion() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    record = _record(1, "a.pdf", "01234567890")
    record.method = ReadMethod.IA
    record.input["telefone"] = "98765432"
    files = {"a.pdf": SourceFile("a.pdf", "a.pdf", FileFormat.PDF, 10)}
    result = validate_all([record], files, ref, None, set())
    assert has_blocking_errors(result)
    assert {issue.code for issue in result.issues} == {"CPF_NAO_ENCONTRADO_ORIGEM", "TEL_8_DIGITOS"}
    assert result.suggestions[0].proposed == "998765432"


def test_deleted_record_skipped_and_defaults_warn_only() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    kept = _record(1, "a.csv", "01234567890", "")
    kept.input["publico_alvo"] = ""
    removed = _record(2, "a.csv", "01234567890")
    removed.deleted = True
    files = {"a.csv": SourceFile("a.csv", "a.csv", FileFormat.CSV, 10)}
    result = validate_all([kept, removed], files, ref, None, set())
    assert result.counts.total == 1
    assert result.counts.only_warning == 1
    assert not has_blocking_errors(result)


def test_ddd_conflict_produces_issue() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    record = _record(1, "a.csv", "01234567890")
    record.input["ddd"] = "61"
    record.input["telefone"] = "63987654321"
    files = {"a.csv": SourceFile("a.csv", "a.csv", FileFormat.CSV, 10)}
    result = validate_all([record], files, ref, None, set())
    assert "DDD_CONFLITO" in {issue.code for issue in result.issues}
