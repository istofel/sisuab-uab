"""Avisos de situação conforme o período informado."""

from core.constants import CONTEXT_CAN_MAX_PERIOD, CONTEXT_DES_TRC_TRA_MIN_PERIOD
from core.messages import context_orientation, msg
from core.models import Issue


def context_issues(record_id: int, situacao: str, periodo: int | None) -> list[Issue]:
    """Retorna avisos contextuais parciais, sem bloquear a exportação."""
    if periodo is None:
        return []
    applicable = (situacao == "CAN" and periodo > CONTEXT_CAN_MAX_PERIOD) or (
        situacao in {"DES", "TRC", "TRA"} and periodo < CONTEXT_DES_TRC_TRA_MIN_PERIOD
    )
    if not applicable:
        return []
    severity, message = msg(
        "SITUACAO_CONTEXTO", orientacao=context_orientation(situacao), periodo=str(periodo)
    )
    return [Issue(record_id, "situacao", severity, "SITUACAO_CONTEXTO", message)]
