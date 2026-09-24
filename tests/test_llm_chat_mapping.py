"""Validação de propostas da IA antes da confirmação."""

from pathlib import Path

import pytest

from core.llm.chat import ChatTurn, ask, build_context
from core.llm.mapping_ai import suggest_mapping
from core.llm.schemas import ChatOut, ColumnMap, MappingOut, ProposedChange
from core.models import (
    Counts,
    FileFormat,
    RawTable,
    ReadMethod,
    Record,
    SourceFile,
    ValidationResult,
)
from core.reference import load_reference
from core.validate import validate_all
from tests.factories import make_cpf


class FakeOllama:
    def __init__(self, output) -> None:
        self.output = output
        self.calls = []

    def chat_structured(self, model, system, user, schema_model):
        self.calls.append((model, system, user, schema_model))
        return self.output


class NoOllama:
    def chat_structured(self, *_args):
        raise AssertionError("O pedido explícito deve usar as regras locais")


def _record(record_id: int) -> Record:
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": "01234567890",
        "situacao": "CUR",
        "email": "aluno@exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }
    return Record(
        record_id,
        "source",
        "a.csv",
        "linha 1",
        (1, record_id),
        ReadMethod.TABULAR,
        "",
        values.copy(),
        values.copy(),
    )


def _result(records: list[Record]) -> ValidationResult:
    return ValidationResult(
        {record.id: record.input.copy() for record in records},
        [],
        {record.id: [] for record in records},
        [],
        Counts(len(records), 0, 0, len(records), 0),
    )


def test_mapping_discards_invalid_and_ambiguous_indices() -> None:
    table = RawTable(None, ["CPF", "Email", "Celular"], [], [], ReadMethod.TABULAR)
    fake = FakeOllama(
        MappingOut(
            colunas=[
                ColumnMap(indice=0, campo="cpf"),
                ColumnMap(indice=3, campo="email"),
                ColumnMap(indice=1, campo="telefone"),
                ColumnMap(indice=2, campo="telefone"),
            ]
        )
    )
    assert suggest_mapping(fake, "local", table) == {0: "cpf"}
    assert "<dados>" in fake.calls[0][2]


def test_chat_discards_nonexistent_deleted_and_oversized_values() -> None:
    first, deleted = _record(1), _record(2)
    deleted.deleted = True
    fake = FakeOllama(
        ChatOut(
            resposta="Confira",
            alteracoes=[
                ProposedChange(registro=99, campo="ddd", valor_novo="61"),
                ProposedChange(registro=2, campo="ddd", valor_novo="61"),
                ProposedChange(registro=1, campo="email", valor_novo="x" * 201),
                ProposedChange(registro=1, campo="ddd", valor_novo="61"),
            ],
        )
    )
    response, proposals, truncated = ask(
        fake, "local", [], "corrija", [first, deleted], _result([first, deleted])
    )
    assert response == "Confira"
    assert not truncated
    assert [proposal.valid for proposal in proposals] == [False, False, False, True]


def test_context_truncates_above_150_records() -> None:
    records = [_record(index) for index in range(1, 152)]
    context, truncated = build_context(records, _result(records), only_problem_first=False)
    assert truncated
    assert len(context.splitlines()) == 150


def test_duplicate_proposal_keeps_last_value() -> None:
    record = _record(1)
    fake = FakeOllama(
        ChatOut(
            resposta="Pronto",
            alteracoes=[
                ProposedChange(registro=1, campo="ddd", valor_novo="61"),
                ProposedChange(registro=1, campo="ddd", valor_novo="62"),
            ],
        )
    )
    _, proposals, _ = ask(
        fake, "local", [ChatTurn("user", "Corrija")], "DDD 62", [record], _result([record])
    )
    assert len(proposals) == 1
    assert proposals[0].new == "62"


def _invalid_cpf_record() -> tuple[Record, ValidationResult]:
    record = _record(10)
    good = make_cpf("123456790")
    record.input["cpf"] = good[:-1] + str((int(good[-1]) + 1) % 10)
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    result = validate_all(
        [record], {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)}, ref, None, set()
    )
    return record, result


def test_explicit_formatted_cpf_becomes_unapplied_proposal() -> None:
    record, result = _invalid_cpf_record()
    target = make_cpf("012345678")
    formatted = f"{target[:3]}.{target[3:6]}.{target[6:9]}-{target[9:]}"
    response, proposals, _ = ask(
        NoOllama(),
        "local",
        [],
        f"corrija a linha 10 para o cpf correto: {formatted}",
        [record],
        result,
    )
    assert len(proposals) == 1
    assert (proposals[0].record_id, proposals[0].field, proposals[0].new) == (
        10,
        "cpf",
        target,
    )
    assert proposals[0].valid
    assert record.input["cpf"] != target
    assert "proposta" in response.lower()


def test_explicit_invalid_cpf_is_not_proposed() -> None:
    record, result = _invalid_cpf_record()
    response, proposals, _ = ask(
        NoOllama(), "local", [], "corrija a linha 10 para o cpf 123.456.790-35", [record], result
    )
    assert proposals == []
    assert "inválido" in response.lower()


def test_explanation_uses_actual_validation_message() -> None:
    record, result = _invalid_cpf_record()
    response, proposals, _ = ask(
        NoOllama(), "local", [], "me explique o erro da linha 10 e como corrigir", [record], result
    )
    assert proposals == []
    assert "dígitos verificadores não conferem" in response


@pytest.mark.parametrize(
    ("prompt", "field", "expected"),
    [
        ("corrija a linha 77, polo, para ARAGUATINS-TO CENTRO", "polo", "ARAGUATINS-TO CENTRO"),
        ("corrija a linha 77 para o cpf 012.345.678-90", "cpf", "01234567890"),
        ("altere a situação da linha 77 para CAN", "situacao", "CAN"),
        ("corrija o e-mail da linha 77 para novo@exemplo.com.br", "email", "novo@exemplo.com.br"),
        ("corrija a linha 77, DDD, para 61", "ddd", "61"),
        ("corrija a linha 77, telefone, para 912345678", "telefone", "912345678"),
        ("corrija a linha 77, público-alvo, para PR", "publico_alvo", "PR"),
    ],
)
def test_explicit_change_for_each_field_is_proposed_without_model(
    prompt: str, field: str, expected: str
) -> None:
    record = _record(77)
    record.input["telefone"] = "9912345678"
    before = record.input.copy()
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    response, proposals, _ = ask(
        NoOllama(), "local", [], prompt, [record], _result([record]), ref=ref
    )
    assert "proposta" in response.lower()
    assert [(item.record_id, item.field, item.new, item.valid) for item in proposals] == [
        (77, field, expected, True)
    ]
    assert record.input == before


def test_invalid_explicit_phone_is_rejected_without_model() -> None:
    record = _record(77)
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    response, proposals, _ = ask(
        NoOllama(),
        "local",
        [],
        "corrija a linha 77, telefone, para 9912345678",
        [record],
        _result([record]),
        ref=ref,
    )
    assert proposals == []
    assert "não" in response.lower()


def test_phone_with_new_ddd_is_not_silently_split() -> None:
    record = _record(77)
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    response, proposals, _ = ask(
        NoOllama(),
        "local",
        [],
        "corrija a linha 77, telefone, para 61912345678",
        [record],
        _result([record]),
        ref=ref,
    )
    assert proposals == []
    assert "não" in response.lower()


def test_ambiguous_explicit_change_falls_back_to_model() -> None:
    record = _record(77)
    fake = FakeOllama(ChatOut(resposta="Pedido ambíguo", alteracoes=[]))
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    response, proposals, _ = ask(
        fake,
        "local",
        [],
        "corrija a linha 77, telefone, para 912345678 e email para novo@exemplo.com.br",
        [record],
        _result([record]),
        ref=ref,
    )
    assert response == "Pedido ambíguo"
    assert proposals == []
    assert len(fake.calls) == 1
