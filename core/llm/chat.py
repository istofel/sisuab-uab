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
from core.models import Normalized, Record, ValidationResult
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
CORRECTION_RE = re.compile(r"\b(?:corrija|corrigir|altere|alterar|troque|trocar|substitua)\b")
EXPLANATION_RE = re.compile(r"\b(?:explique|explicar|entender)\b")
TARGET_RE = re.compile(r"\bpara\b\s*:?[ \t]*(.+)$", re.IGNORECASE | re.DOTALL)
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


def build_context(
    records: list[Record], result: ValidationResult, only_problem_first: bool = True
) -> tuple[str, bool]:
    """Lista até 150 registros, priorizando os com problema em cargas grandes."""
    active = [record for record in records if not record.deleted]
    if len(active) > CHAT_MAX_RECORDS_IN_CONTEXT and only_problem_first:
        selected = [record for record in active if result.by_record.get(record.id)]
    else:
        selected = active
    truncated = len(selected) > CHAT_MAX_RECORDS_IN_CONTEXT or len(selected) < len(active)
    selected = selected[:CHAT_MAX_RECORDS_IN_CONTEXT]
    lines: list[str] = []
    for record in selected:
        values = result.effective.get(record.id, record.input)
        issue_codes = ",".join(issue.code for issue in result.by_record.get(record.id, []))
        lines.append(
            "|".join([str(record.id), *(values.get(field, "") for field in FIELDS), issue_codes])
        )
    return "\n".join(lines), truncated


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


def _local_request(
    message: str, records: list[Record], result: ValidationResult, ref: Reference | None
) -> tuple[str, list[ProposedPatch]] | None:
    """Resolve pedidos inequívocos sem depender da interpretação do modelo."""
    normalized_message = search_key(message)
    row_match = ROW_REFERENCE_RE.search(normalized_message)
    if row_match is None:
        return None
    record_id = int(row_match.group(1))
    record = next((item for item in records if item.id == record_id and not item.deleted), None)
    if CORRECTION_RE.search(normalized_message):
        fields = [
            field for field, pattern in FIELD_PATTERNS.items() if pattern.search(normalized_message)
        ]
        target_match = TARGET_RE.search(message)
        if len(fields) == 1 and target_match is not None:
            field = fields[0]
            if field in {"polo", "ddd"} and ref is None:
                return None
            raw_value = TARGET_LABEL_RE.sub("", target_match.group(1).strip(), count=1)
            raw_value = raw_value.strip().strip("\"'").strip()
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
        issues = result.by_record.get(record_id, [])
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
    context, truncated = build_context(records, result)
    local = _local_request(message, records, result, ref)
    if local is not None:
        return *local, truncated
    turns = "\n".join(f"{turn.role}: {turn.content}" for turn in history[-CHAT_HISTORY_TURNS:])
    user = f"<dados>\n{context}\n</dados>\nConversa:\n{turns}\nPedido: {message}"
    output = client.chat_structured(model, CHAT_SYSTEM, user, ChatOut)
    by_id = {record.id: record for record in records}
    proposals: dict[tuple[int, str], ProposedPatch] = {}
    for change in output.alteracoes:
        record = by_id.get(change.registro)
        reason: str | None = None
        if record is None:
            reason = "REGISTRO_INEXISTENTE"
        elif record.deleted:
            reason = "REGISTRO_EXCLUIDO"
        elif len(change.valor_novo) > CHAT_MAX_VALUE_LEN:
            reason = "VALOR_MUITO_LONGO"
        proposals[(change.registro, change.campo)] = ProposedPatch(
            change.registro,
            change.campo,
            change.valor_novo,
            record.input.get(change.campo, "") if record else "",
            reason is None,
            reason,
        )
    return output.resposta, list(proposals.values()), truncated
