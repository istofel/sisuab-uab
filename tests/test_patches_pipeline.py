"""Correções reversíveis e construção da carga."""

from pathlib import Path

from core.export import export_csv
from core.models import (
    FileFormat,
    FileState,
    MappingProposal,
    MappingStrategy,
    PatchOrigin,
    RawTable,
    ReadMethod,
    Record,
    SourceFile,
)
from core.patches import PatchLog
from core.pipeline import build_records, effective_rows, ingest_upload, rebuild_file
from core.reference import load_reference
from core.validate import validate_all
from core.verify import verify_csv
from tests.factories import make_cpf, make_csv


def _record(record_id: int) -> Record:
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": f"0123456789{record_id}",
        "situacao": "CUR",
        "email": f"aluno{record_id}@exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }
    return Record(
        record_id,
        "source",
        "a.csv",
        f"linha {record_id}",
        (1, record_id),
        ReadMethod.TABULAR,
        "",
        values.copy(),
        values.copy(),
    )


def test_grouped_undo_reverts_all_records() -> None:
    first, second = _record(1), _record(2)
    log = PatchLog()
    group = log.new_group()
    log.set_value(first, "ddd", "61", PatchOrigin.LOTE, group)
    log.set_value(second, "ddd", "61", PatchOrigin.LOTE, group)
    assert first.input["ddd"] == second.input["ddd"] == "61"
    assert len(log.undo_last({1: first, 2: second})) == 2
    assert first.input["ddd"] == second.input["ddd"] == "63"
    assert not log.can_undo()


def test_delete_restore_and_undo() -> None:
    record = _record(1)
    log = PatchLog()
    log.delete(record)
    assert record.deleted
    log.restore(record)
    assert not record.deleted
    log.undo_last({1: record})
    assert record.deleted
    log.undo_last({1: record})
    assert not record.deleted


def test_noop_edit_does_not_enter_history() -> None:
    record = _record(1)
    log = PatchLog()
    assert log.set_value(record, "ddd", "63", PatchOrigin.EDICAO) is None
    assert not log.can_undo()


def test_build_records_export_rows_and_rebuild() -> None:
    table = RawTable(
        "Alunos",
        ["Polo", "CPF", "Situação", "E-mail", "DDD", "Telefone", "Público"],
        [
            [
                "ARAGUAÍNA-TO CIMBA",
                "01234567890",
                "CUR",
                "aluno@exemplo.com.br",
                "63",
                "987654321",
                "DS",
            ]
        ],
        [2],
        ReadMethod.TABULAR,
    )
    source = SourceFile("source", "a.csv", FileFormat.CSV, 100)
    source.tables = [table]
    source.selected_tables = {0}
    source.mappings = {
        0: MappingProposal(
            dict(
                enumerate(("polo", "cpf", "situacao", "email", "ddd", "telefone", "publico_alvo"))
            ),
            MappingStrategy.CABECALHO,
            set(),
            False,
        )
    }
    source.state = FileState.CONFIRMADO
    records = build_records(source, 1, 1)
    assert len(records) == 1
    assert records[0].locator == "Alunos, linha 2"
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    result = validate_all(records, {source.id: source}, ref, None, set())
    assert effective_rows(records, result) == [
        (
            "ARAGUAÍNA-TO CIMBA",
            "01234567890",
            "CUR",
            "aluno@exemplo.com.br",
            "63",
            "987654321",
            "DS",
        )
    ]
    log = PatchLog()
    log.set_value(records[0], "ddd", "61", PatchOrigin.EDICAO)
    rebuilt = rebuild_file(source, records, log, 1, 2)
    assert rebuilt[0].id == 2
    assert rebuilt[0].input["ddd"] == "63"
    assert not log.can_undo()


def test_three_csv_files_export_without_header_and_pass_final_verification() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    files: dict[str, SourceFile] = {}
    records: list[Record] = []
    header = ["Polo", "CPF", "Situação", "E-mail", "DDD", "Telefone", "Público"]
    for index, city in enumerate(
        ("ARAGUAÍNA-TO CIMBA", "XAMBIOÁ-TO CENTRO", "GURUPI-TO ZONA RURAL"), start=1
    ):
        cpf = make_cpf(f"12345678{index}")
        row = [city, cpf, "CUR", f"aluno{index}@exemplo.com.br", "63", "987654321", "DS"]
        payload = make_csv([row], header=header)
        source = ingest_upload(files, f"alunos{index}.csv", payload, len(records), ref)
        assert source.state == FileState.CONFIRMADO
        records.extend(build_records(source, index, len(records) + 1))
    assert len(records) == 3
    result = validate_all(records, files, ref, None, set())
    assert result.counts.with_error == 0
    data = export_csv(effective_rows(records, result), "\n")
    assert verify_csv(data, ref, "\n").ok
    assert b"Polo;CPF" not in data


def test_repeated_file_and_session_limit_are_rejected() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    payload = make_csv(
        [
            [
                "ARAGUAÍNA-TO CIMBA",
                "01234567890",
                "CUR",
                "aluno@exemplo.com.br",
                "63",
                "987654321",
                "DS",
            ]
        ]
    )
    files: dict[str, SourceFile] = {}
    first = ingest_upload(files, "a.csv", payload, 0, ref)
    assert first.state == FileState.CONFIRMADO
    repeat = ingest_upload(files, "b.csv", payload, 0, ref)
    assert repeat.state == FileState.COM_FALHA
    assert repeat.notices[0].code == "ARQ_REPETIDO"
    limited = ingest_upload({}, "a.csv", payload, 5000, ref)
    assert limited.state == FileState.COM_FALHA
    assert limited.notices[0].code == "ARQ_LIMITE_REGISTROS"
