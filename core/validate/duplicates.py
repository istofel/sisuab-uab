"""Detecção de CPF e e-mail repetidos em toda a carga."""

from collections import defaultdict

from core.messages import msg
from core.models import Issue


def find_duplicates(effective: dict[int, dict[str, str]], locators: dict[int, str]) -> list[Issue]:
    """Sinaliza CPFs repetidos e e-mails compartilhados por CPFs diferentes."""
    issues: list[Issue] = []
    for field, code in (("cpf", "CPF_DUPLICADO"), ("email", "EMAIL_DUPLICADO")):
        groups: dict[str, list[int]] = defaultdict(list)
        for record_id, values in effective.items():
            if values[field]:
                groups[values[field].casefold()].append(record_id)
        for ids in groups.values():
            if len(ids) < 2:
                continue
            if field == "email" and len({effective[i]["cpf"] for i in ids}) < 2:
                continue
            for record_id in ids:
                others = [locators[other] for other in ids if other != record_id]
                extra = len(others) - 3
                display = ", ".join(others[:3])
                if extra > 0:
                    display += f" e mais {extra}"
                severity, message = msg(code, outros=display)
                issues.append(Issue(record_id, field, severity, code, message))
    return issues
