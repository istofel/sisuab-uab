"""Associação de colunas e divergência de extensão."""

from pathlib import Path

from core.ingest import detect_format, read_file
from core.mapping import propose_mapping, rows_to_inputs, validate_mapping
from core.models import FileFormat, MappingStrategy, RawTable, ReadMethod
from core.reference import load_reference
from tests.factories import make_xlsx


def _ref():
    return load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))


def test_header_synonyms_and_ambiguous_phone() -> None:
    table = RawTable(None, ["CPF", "E-mail", "Telefone", "Celular"], [], [], ReadMethod.TABULAR)
    proposal = propose_mapping(table, _ref())
    assert proposal.mapping == {0: "cpf", 1: "email", 2: "telefone", 3: "telefone"}
    assert proposal.ambiguous_fields == {"telefone"}
    assert proposal.needs_confirmation
    assert validate_mapping(proposal.mapping) == ["telefone"]


def test_numbered_cpf_header_is_recognized() -> None:
    table = RawTable(None, ["Nº do CPF"], [], [], ReadMethod.TABULAR)
    assert propose_mapping(table, _ref()).mapping == {0: "cpf"}


def test_seven_columns_without_header_are_positional() -> None:
    table = RawTable(None, None, [["x"] * 7], [1], ReadMethod.TABULAR)
    proposal = propose_mapping(table, _ref())
    assert proposal.strategy == MappingStrategy.POSICIONAL
    assert not proposal.needs_confirmation
    assert proposal.mapping[0] == "polo"


def test_content_inference_needs_confirmation() -> None:
    table = RawTable(
        None,
        None,
        [["01234567890", "aluno@exemplo.com.br"]],
        [1],
        ReadMethod.TABULAR,
    )
    proposal = propose_mapping(table, _ref())
    assert proposal.strategy == MappingStrategy.CONTEUDO
    assert proposal.needs_confirmation
    assert proposal.mapping == {0: "cpf", 1: "email"}


def test_rows_to_inputs_applies_file_polo() -> None:
    table = RawTable(
        None, ["CPF", "Email"], [["01234567890", "aluno@exemplo.com.br"]], [2], ReadMethod.TABULAR
    )
    rows = rows_to_inputs(table, {0: "cpf", 1: "email"}, "ARAGUAÍNA-TO CIMBA")
    assert rows[0][1]["polo"] == "ARAGUAÍNA-TO CIMBA"
    assert rows[0][1]["cpf"] == "01234567890"


def test_xlsx_content_with_csv_extension_is_reported() -> None:
    data = make_xlsx({"Alunos": [["CPF"], ["01234567890"]]})
    assert detect_format("alunos.csv", data) == (FileFormat.XLSX, True)
    source = read_file("alunos.csv", data)
    assert source.fmt == FileFormat.XLSX
    assert source.notices[0].code == "ARQ_EXTENSAO_DIVERGENTE"
