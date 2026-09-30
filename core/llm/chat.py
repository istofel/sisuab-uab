"""Contexto e propostas de correção do chat local."""

import re
from dataclasses import dataclass
from typing import Literal

from core.constants import (
    CHAT_HISTORY_TURNS,
    CHAT_MAX_RECORDS_IN_CONTEXT,
    CHAT_MAX_VALUE_LEN,
    FIELD_LABELS,
    FIELDS,
)
from core.llm.client import OllamaClient
from core.llm.prompts import CHAT_SYSTEM
from core.llm.schemas import ChatOut
from core.messages import chat_msg
from core.models import Normalized, Record, Severity, ValidationResult
from core.normalize import normalize
from core.reference import Reference
from core.text_utils import search_key
from core.validate.cpf import validate_cpf
from core.validate.fields import (
    validate_ddd,
    validate_email,
    validate_polo,
    validate_publico,
    validate_situacao,
    validate_telefone,
)

ROW_REFERENCE_RE = re.compile(r"\b(?:linha|registro)\s+([0-9]+)\b")
CORRECTION_RE = re.compile(
    r"\b(?:corrija|corrigir|altere|alterar|troque|trocar|substitua|"
    r"mude|mudar|atualize|atualizar|coloque|colocar|defina|definir|"
    r"preencha|preencher|complete|completar|insira|inserir|informe|informar|"
    r"ajuste|ajustar|retifique|retificar|atribua|atribuir)\b"
)
EXPLANATION_RE = re.compile(r"\b(?:explique|explicar|entender)\b")
TARGET_RE = re.compile(r"\bpara\b\s*:?[ \t]*(.+)$", re.IGNORECASE | re.DOTALL)
BATCH_SCOPE_RE = re.compile(
    r"\b(?:coluna|campo|linha)\b.*\b(?:erros?|problemas?|pendencias?|invalid[oa]s?|ausentes?|vazios?)\b"
    r"|\b(?:onde|quando)\b.*\b(?:erros?|problemas?|pendencias?|invalid[oa]s?|ausentes?|vazios?)\b"
)
BATCH_TARGET_RE = re.compile(
    r"\b(?:para(?:\s+o\s+valor)?|com\s+(?:o\s+)?valor|pelo\s+valor)"
    r"\s*:?[ \t]*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
FIELD_PATTERNS = {
    "polo": re.compile(r"\bpolo\b"),
    "cpf": re.compile(r"\bcpf\b"),
    "situacao": re.compile(r"\b(?:situacao|status)\b"),
    "email": re.compile(r"\b(?:e-mail|email)\b"),
    "ddd": re.compile(r"\bddd\b"),
    "telefone": re.compile(r"\b(?:telefone|celular|fone)\b"),
    "publico_alvo": re.compile(r"\bpublico(?:[- ]alvo)?\b"),
}
FIELD_NAME_RE = (
    r"(?:polo|cpf|situa[cç][aã]o|status|e-?mail|ddd|"
    r"telefone|celular|fone|p[uú]blico[- ]alvo)"
)
TARGET_LABEL_RE = re.compile(
    rf"^(?:o|a)\s+{FIELD_NAME_RE}(?:\s+correto)?\s*:?[ \t]*|"
    rf"^{FIELD_NAME_RE}(?:\s+correto)?\s*:[ \t]*",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ChatTurn:
    """Uma mensagem da conversa mantida só na sessão."""

    role: Literal["user", "assistant"]
    content: str


@dataclass(slots=True)
class ProposedPatch:
    """Alteração para a usuária revisar antes de aplicar."""

    record_id: int
    field: str
    new: str
    current: str
    valid: bool
    reason: str | None


def _context_cell(value: str) -> str:
    """Mantém cada registro em uma linha sem confundir o separador de campos."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def build_context(
    records: list[Record],
    result: ValidationResult,
    only_problem_first: bool = True,
    focus_ids: set[int] | None = None,
) -> tuple[str, bool]:
    """Lista até 150 registros, priorizando os com problema em cargas grandes."""
    active = [record for record in records if not record.deleted]
    focused = [record for record in active if focus_ids and record.id in focus_ids]
    if focused:
        selected = focused
    elif len(active) > CHAT_MAX_RECORDS_IN_CONTEXT and only_problem_first:
        selected = [
            record
            for record in active
            if any(issue.severity != Severity.INFO for issue in result.by_record.get(record.id, []))
        ]
    else:
        selected = active
    truncated = len(selected) > CHAT_MAX_RECORDS_IN_CONTEXT or (
        not focused and len(selected) < len(active)
    )
    selected = selected[:CHAT_MAX_RECORDS_IN_CONTEXT]
    lines: list[str] = []
    for record in selected:
        values = result.effective.get(record.id, record.input)
        issues = result.by_record.get(record.id, [])
        if focus_ids and record.id in focus_ids:
            issue_codes = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        else:
            issue_codes = ",".join(issue.code for issue in issues)
        cells = [str(record.id), record.name_ref]
        cells.extend(values.get(field, "") for field in FIELDS)
        cells.append(issue_codes)
        lines.append("|".join(_context_cell(cell) for cell in cells))
    return "\n".join(lines), truncated


def _named_matches(message: str, records: list[Record]) -> list[Record]:
    """Localiza nomes completos ou prenomes, preferindo a referência mais específica."""
    normalized = search_key(message)
    target_marker = re.search(r"\bpara\b", normalized)
    if target_marker is not None:
        normalized = normalized[: target_marker.start()]
    matches: list[tuple[bool, Record]] = []
    for record in records:
        if record.deleted or not record.name_ref.strip():
            continue
        name = search_key(record.name_ref)
        first = name.split()[0]
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", normalized):
            matches.append((True, record))
        elif len(first) >= 3 and re.search(rf"(?<!\w){re.escape(first)}(?!\w)", normalized):
            matches.append((False, record))
    full_first_names = {search_key(record.name_ref).split()[0] for full, record in matches if full}
    return [
        record
        for full, record in matches
        if full or search_key(record.name_ref).split()[0] not in full_first_names
    ]


def _candidate_error(field: str, normalized: Normalized, ref: Reference | None) -> str | None:
    """Confere um valor normalizado usando o validador do campo."""
    value = normalized.values[field]
    if field == "cpf":
        return validate_cpf(value, normalized.cpf_scientific)
    if field == "polo":
        return validate_polo(value, ref)[0] if ref else None
    if field == "situacao":
        return validate_situacao(value)[0]
    if field == "email":
        return validate_email(value)
    if field == "ddd":
        return validate_ddd(value, False, ref) if ref else None
    if field == "telefone":
        if normalized.ddd_from_phone is not None:
            return "TEL_TAMANHO"
        return validate_telefone(value, normalized.phone_prefixed)[0]
    return validate_publico(value)[0]


def _target_value(value: str) -> str:
    value = TARGET_LABEL_RE.sub("", value.strip(), count=1)
    value = re.sub(r"^(?:o\s+)?valor\s*:?[ \t]*", "", value, flags=re.IGNORECASE)
    value = re.sub(
        r"\s*(?:[,;]\s*)?(?:por favor|obrigad[oa])\s*[.!?]*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return value.strip().strip("\"' ").strip(".!?; ")


def _local_request(
    message: str, records: list[Record], result: ValidationResult, ref: Reference | None
) -> tuple[str, list[ProposedPatch]] | None:
    """Resolve pedidos inequívocos sem depender da interpretação do modelo."""
    normalized_message = search_key(message)
    if (
        CORRECTION_RE.search(normalized_message)
        and not ROW_REFERENCE_RE.search(normalized_message)
        and BATCH_SCOPE_RE.search(normalized_message)
    ):
        fields = [
            field for field, pattern in FIELD_PATTERNS.items() if pattern.search(normalized_message)
        ]
        target_match = BATCH_TARGET_RE.search(message)
        if len(fields) == 1 and target_match is not None:
            field = fields[0]
            if field in {"polo", "ddd"} and ref is None:
                return None
            matching = [
                record
                for record in records
                if not record.deleted
                and any(
                    issue.field == field and issue.severity == Severity.ERRO
                    for issue in result.by_record.get(record.id, [])
                )
            ]
            if not matching:
                return chat_msg("SEM_ERROS_CAMPO", campo=FIELD_LABELS[field]), []
            raw_value = _target_value(target_match.group(1))
            if not raw_value:
                return None
            normalized = normalize({field: raw_value})
            proposed = normalized.values[field]
            if _candidate_error(field, normalized, ref) is not None:
                return chat_msg("CAMPO_INVALIDO", campo=FIELD_LABELS[field]), []
            patches = [
                ProposedPatch(
                    record.id,
                    field,
                    proposed,
                    record.input.get(field, ""),
                    True,
                    None,
                )
                for record in matching
            ]
            return chat_msg(
                "LOTE_CAMPO_PROPOSTO",
                campo=FIELD_LABELS[field],
                count=str(len(patches)),
                valor=proposed,
            ), patches

    row_matches = ROW_REFERENCE_RE.findall(normalized_message)
    if len(row_matches) > 1:
        return None
    if row_matches:
        record_id = int(row_matches[0])
        record = next((item for item in records if item.id == record_id and not item.deleted), None)
        named = _named_matches(message, records)
        if named and record is not None and record not in named:
            return chat_msg("ALVO_CONFLITANTE"), []
    else:
        matches = _named_matches(message, records)
        if (
            len(matches) > 1
            and len({search_key(item.name_ref).split()[0] for item in matches}) == 1
        ):
            return chat_msg("NOME_AMBIGUO"), []
        if len(matches) != 1:
            return None
        record = matches[0]
        record_id = record.id
    if CORRECTION_RE.search(normalized_message):
        fields = [
            field for field, pattern in FIELD_PATTERNS.items() if pattern.search(normalized_message)
        ]
        target_match = TARGET_RE.search(message)
        if len(fields) == 1 and target_match is not None:
            field = fields[0]
            if field in {"polo", "ddd"} and ref is None:
                return None
            raw_value = _target_value(target_match.group(1))
            if not raw_value:
                return None
            if record is None:
                return chat_msg("REGISTRO_INEXISTENTE", registro=str(record_id)), []
            normalized = normalize({field: raw_value})
            proposed = normalized.values[field]
            if _candidate_error(field, normalized, ref) is not None:
                return chat_msg("CAMPO_INVALIDO", campo=FIELD_LABELS[field]), []
            patch = ProposedPatch(
                record_id, field, proposed, record.input.get(field, ""), True, None
            )
            return chat_msg("CAMPO_PROPOSTO", campo=FIELD_LABELS[field], registro=str(record_id)), [
                patch
            ]
    if EXPLANATION_RE.search(normalized_message) and "erro" in normalized_message:
        if record is None:
            return chat_msg("REGISTRO_INEXISTENTE", registro=str(record_id)), []
        issues = [
            issue
            for issue in result.by_record.get(record_id, [])
            if issue.severity != Severity.INFO
        ]
        if not issues:
            return chat_msg("SEM_ERROS_REGISTRO", registro=str(record_id)), []
        details = " ".join(issue.message for issue in issues)
        return chat_msg("ERROS_REGISTRO", registro=str(record_id), detalhes=details), []
    return None


def ask(
    client: OllamaClient,
    model: str,
    history: list[ChatTurn],
    message: str,
    records: list[Record],
    result: ValidationResult,
    ref: Reference | None = None,
) -> tuple[str, list[ProposedPatch], bool]:
    """Solicita propostas e descarta mudanças fora dos registros válidos."""
    row_ids = {int(match) for match in ROW_REFERENCE_RE.findall(search_key(message))}
    focus_ids = row_ids | {record.id for record in _named_matches(message, records)}
    if not focus_ids:
        for turn in reversed(history[-CHAT_HISTORY_TURNS:]):
            if turn.role == "user":
                previous_rows = {
                    int(match) for match in ROW_REFERENCE_RE.findall(search_key(turn.content))
                }
                focus_ids = previous_rows | {
                    record.id for record in _named_matches(turn.content, records)
                }
                if focus_ids:
                    break
    context, truncated = build_context(records, result, focus_ids=focus_ids)
    local = _local_request(message, records, result, ref)
    if local is not None:
        return *local, truncated
    turns = "\n".join(f"{turn.role}: {turn.content}" for turn in history[-CHAT_HISTORY_TURNS:])
    user = (
        "Colunas dos dados: registro|nome|polo|cpf|situacao|email|ddd|telefone|publico_alvo|erros. "
        "O nome identifica o aluno; registro é o número usado nas alterações.\n"
        f"<dados>\n{context}\n</dados>\nConversa:\n{turns}\nPedido: {message}"
    )
    output = client.chat_structured(model, CHAT_SYSTEM, user, ChatOut)
    if not output.alteracoes and re.search(r"\bpropost\w*\b", search_key(output.resposta)):
        return chat_msg("CHAT_SEM_PROPOSTA"), [], truncated
    by_id = {record.id: record for record in records}
    context_ids = {int(line.split("|", 1)[0]) for line in context.splitlines()}
    proposals: dict[tuple[int, str], ProposedPatch] = {}
    for change in output.alteracoes:
        record = by_id.get(change.registro)
        reason: str | None = None
        if record is None:
            reason = "REGISTRO_INEXISTENTE"
        elif record.deleted:
            reason = "REGISTRO_EXCLUIDO"
        elif change.registro not in context_ids:
            reason = "REGISTRO_FORA_CONTEXTO"
        elif len(change.valor_novo) > CHAT_MAX_VALUE_LEN:
            reason = "VALOR_MUITO_LONGO"
        normalized = normalize({change.campo: change.valor_novo})
        if reason is None and _candidate_error(change.campo, normalized, ref) is not None:
            reason = "VALOR_INVALIDO"
        proposals[(change.registro, change.campo)] = ProposedPatch(
            change.registro,
            change.campo,
            normalized.values[change.campo],
            record.input.get(change.campo, "") if record else "",
            reason is None,
            reason,
        )
    return output.resposta, list(proposals.values()), truncated
