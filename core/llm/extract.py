"""Extração assistida de texto livre e conferência com CPFs de origem."""

from collections.abc import Callable

from core.errors import LLMResponseError, LLMUnavailableError
from core.llm.client import OllamaClient
from core.llm.prompts import EXTRACTION_SYSTEM
from core.llm.schemas import ExtractionOut
from core.messages import file_msg
from core.models import FileNotice, SourceFile
from core.text_utils import CPF_LIKE_RE, ascii_digits


def source_cpfs(text: str) -> frozenset[str]:
    """Coleta CPFs visíveis no texto original."""
    return frozenset(ascii_digits(match.group()).zfill(11) for match in CPF_LIKE_RE.finditer(text))


def extract_blocks(
    client: OllamaClient,
    model: str,
    sf: SourceFile,
    on_progress: Callable[[int, int], None],
) -> None:
    """Lê blocos ainda pendentes; preserva falhas para tentar novamente."""
    hinted = [
        (index, block) for index, block in enumerate(sf.text_blocks) if block.has_student_hint
    ]
    sf.ai_source_cpfs = frozenset(cpf for _, block in hinted for cpf in source_cpfs(block.text))
    sf.notices = [
        notice
        for notice in sf.notices
        if notice.code not in {"ARQ_TRECHO_NAO_LIDO", "ARQ_CONTAGEM_DIVERGENTE"}
    ]
    for done, (index, block) in enumerate(hinted, start=1):
        if index not in sf.ai_blocks_done:
            try:
                output = client.chat_structured(
                    model,
                    EXTRACTION_SYSTEM,
                    f"<documento>\n{block.text}\n</documento>",
                    ExtractionOut,
                )
            except (LLMResponseError, LLMUnavailableError):
                pass
            else:
                sf.ai_records.extend(output.registros)
                sf.ai_record_locators.extend(f"{block.locator} (IA)" for _ in output.registros)
                sf.ai_blocks_done.add(index)
        on_progress(done, len(hinted))

    extracted_cpfs = {ascii_digits(record.cpf).zfill(11) for record in sf.ai_records}
    missing = sorted(sf.ai_source_cpfs - extracted_cpfs)
    if missing:
        level, message = file_msg(
            "ARQ_CONTAGEM_DIVERGENTE", n=str(len(missing)), lista=", ".join(missing)
        )
        sf.notices.append(FileNotice(level, "ARQ_CONTAGEM_DIVERGENTE", message))
    pending = len(hinted) - len(sf.ai_blocks_done.intersection(index for index, _ in hinted))
    if pending:
        level, message = file_msg("ARQ_TRECHO_NAO_LIDO", n=str(pending), nome=sf.name)
        sf.notices.append(FileNotice(level, "ARQ_TRECHO_NAO_LIDO", message))
