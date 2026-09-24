"""Associação de colunas de entrada aos sete campos SisUAB."""

from collections import Counter

from core.constants import FIELDS, HEADER_SYNONYMS, PUBLICOS, SITUACOES
from core.ingest.discard import split_rows
from core.models import MappingProposal, MappingStrategy, MapTarget, RawTable
from core.reference import Reference
from core.text_utils import CPF_LIKE_RE, PHONE_LIKE_RE, header_key, search_key


def _content_target(values: list[str], ref: Reference) -> str:
    nonempty = [value.strip() for value in values if value.strip()]
    if not nonempty:
        return "ignorar"
    polo_keys = {search_key(polo) for polo in ref.polos}
    checks = {
        "cpf": lambda value: CPF_LIKE_RE.fullmatch(value) is not None,
        "email": lambda value: "@" in value,
        "situacao": lambda value: value.upper() in SITUACOES,
        "publico_alvo": lambda value: value.upper() in PUBLICOS,
        "ddd": lambda value: value in ref.ddds or value.lstrip("0") in ref.ddds,
        "telefone": lambda value: PHONE_LIKE_RE.fullmatch(value) is not None,
        "polo": lambda value: search_key(value) in polo_keys,
    }
    for target, check in checks.items():
        if sum(bool(check(value)) for value in nonempty) / len(nonempty) >= 0.8:
            return target
    return "ignorar"


def propose_mapping(table: RawTable, ref: Reference) -> MappingProposal:
    """Propõe mapeamento por título, posição ou conteúdo."""
    width = (
        len(table.header)
        if table.header is not None
        else max((len(row) for row in table.rows), default=0)
    )
    if table.header is not None:
        aliases = {alias: target for target, names in HEADER_SYNONYMS.items() for alias in names}
        mapping = {
            index: aliases.get(header_key(cell), "ignorar")
            for index, cell in enumerate(table.header)
        }
        strategy = MappingStrategy.CABECALHO
    elif width == len(FIELDS):
        mapping = dict(enumerate(FIELDS))
        strategy = MappingStrategy.POSICIONAL
    else:
        mapping = {
            index: _content_target(
                [row[index] if index < len(row) else "" for row in table.rows], ref
            )
            for index in range(width)
        }
        strategy = MappingStrategy.CONTEUDO

    ambiguous = set(validate_mapping(mapping))
    return MappingProposal(
        mapping,
        strategy,
        ambiguous,
        bool(ambiguous) or strategy in {MappingStrategy.CONTEUDO, MappingStrategy.IA},
    )


def validate_mapping(mapping: dict[int, MapTarget]) -> list[str]:
    """Lista campos associados a mais de uma coluna."""
    counts = Counter(target for target in mapping.values() if target != "ignorar")
    return [field for field, count in counts.items() if count > 1]


def rows_to_inputs(
    table: RawTable, mapping: dict[int, MapTarget], polo_default: str | None
) -> list[tuple[int, dict[str, str], str]]:
    """Transforma linhas com indício de aluno em valores de entrada e nome auxiliar."""
    kept, _ = split_rows(table)
    inputs: list[tuple[int, dict[str, str], str]] = []
    for number, row in kept:
        values = dict.fromkeys(FIELDS, "")
        name = ""
        for index, target in mapping.items():
            if index >= len(row):
                continue
            if target in values:
                values[target] = row[index]
            elif target == "nome":
                name = row[index]
        if polo_default is not None:
            values["polo"] = polo_default
        inputs.append((number, values, name))
    return inputs
