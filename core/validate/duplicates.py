"""Detecção de CPF repetido em toda a carga."""

from collections import defaultdict

from core.messages import msg
from core.models import Issue


def find_duplicates(effective: dict[int, dict[str, str]], locators: dict[int, str]) -> list[Issue]:
    """Gera um erro em cada ocorrência de CPF duplicado."""
    groups: dict[str, list[int]] = defaultdict(list)
    for record_id, values in effective.items():
        if values["cpf"]:
            groups[values["cpf"]].append(record_id)

    issues: list[Issue] = []
    for ids in groups.values():
        if len(ids) < 2:
            continue
        for record_id in ids:
            others = [locators[other] for other in ids if other != record_id]
            extra = len(others) - 3
            display = ", ".join(others[:3])
            if extra > 0:
                display += f" e mais {extra}"
            severity, message = msg("CPF_DUPLICADO", outros=display)
            issues.append(Issue(record_id, "cpf", severity, "CPF_DUPLICADO", message))
    return issues
