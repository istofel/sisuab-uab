"""Extração por IA local e conferência dos CPFs do texto."""

from pathlib import Path

from core.errors import LLMResponseError
from core.llm.extract import extract_blocks, source_cpfs
from core.llm.schemas import ExtractedRecord, ExtractionOut
from core.models import FileFormat, FileState, SourceFile, TextBlock
from core.pipeline import build_records
from core.reference import load_reference
from core.validate import validate_all


class FakeOllama:
    def __init__(self, outputs: list[ExtractionOut | Exception]) -> None:
        self.outputs = outputs
        self.prompts: list[str] = []

    def chat_structured(self, model: str, system: str, user: str, schema_model):
        self.prompts.append(user)
        result = self.outputs.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def _extracted(cpf: str) -> ExtractedRecord:
    return ExtractedRecord(
        nome="Aluno",
        polo="ARAGUAÍNA-TO CIMBA",
        cpf=cpf,
        situacao="CUR",
        email="aluno@exemplo.com.br",
        ddd="63",
        telefone="987654321",
        publico_alvo="DS",
    )


def _source(text: str) -> SourceFile:
    source = SourceFile("source", "alunos.txt", FileFormat.TXT, len(text))
    source.text_blocks = [TextBlock("linhas 1–2", text, True)]
    return source


def test_invented_cpf_is_blocking_after_confirmation() -> None:
    source = _source("Aluno CPF 012.345.678-90")
    client = FakeOllama([ExtractionOut(registros=[_extracted("12345678909")])])
    extract_blocks(client, "local", source, lambda current, total: None)
    source.state = FileState.CONFIRMADO
    records = build_records(source, 1, 1)
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    result = validate_all(records, {source.id: source}, ref, None, set())
    assert "CPF_NAO_ENCONTRADO_ORIGEM" in {issue.code for issue in result.issues}
    assert records[0].locator == "linhas 1–2 (IA)"


def test_missing_cpf_produces_count_notice() -> None:
    source = _source("CPF 012.345.678-90")
    extract_blocks(
        FakeOllama([ExtractionOut(registros=[])]), "local", source, lambda current, total: None
    )
    assert "ARQ_CONTAGEM_DIVERGENTE" in {notice.code for notice in source.notices}


def test_failed_block_stays_pending_and_non_student_block_is_skipped() -> None:
    source = _source("CPF 012.345.678-90")
    source.text_blocks.append(TextBlock("linhas 3–4", "Introdução", False))
    client = FakeOllama([LLMResponseError("inválido")])
    progress: list[tuple[int, int]] = []
    extract_blocks(
        client, "local", source, lambda current, total: progress.append((current, total))
    )
    assert len(client.prompts) == 1
    assert source.ai_blocks_done == set()
    assert "ARQ_TRECHO_NAO_LIDO" in {notice.code for notice in source.notices}
    assert progress == [(1, 1)]


def test_source_cpf_detection() -> None:
    assert source_cpfs("CPF 012.345.678-90") == frozenset({"01234567890"})
