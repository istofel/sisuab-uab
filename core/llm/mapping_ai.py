"""Proposta de mapeamento de colunas pela IA local."""

from core.constants import LLM_MAPPING_SAMPLE_ROWS
from core.llm.client import OllamaClient
from core.llm.prompts import MAPPING_SYSTEM
from core.llm.schemas import MappingOut
from core.mapping import validate_mapping
from core.models import MapTarget, RawTable


def suggest_mapping(client: OllamaClient, model: str, table: RawTable) -> dict[int, MapTarget]:
    """Devolve somente índices existentes e campos sem ambiguidade."""
    width = (
        len(table.header)
        if table.header is not None
        else max((len(row) for row in table.rows), default=0)
    )
    header = " | ".join(table.header) if table.header is not None else "sem cabeçalho"
    sample = "\n".join(" | ".join(row) for row in table.rows[:LLM_MAPPING_SAMPLE_ROWS])
    user = f"<dados>\nCabeçalho: {header}\nLinhas:\n{sample}\n</dados>"
    output = client.chat_structured(model, MAPPING_SYSTEM, user, MappingOut)
    mapping: dict[int, MapTarget] = {
        column.indice: column.campo for column in output.colunas if 0 <= column.indice < width
    }
    for target in validate_mapping(mapping):
        mapping = {index: field for index, field in mapping.items() if field != target}
    return mapping
