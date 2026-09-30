"""Normalização pura dos sete campos do SisUAB."""

import re

from core.constants import FIELDS
from core.models import Normalized
from core.text_utils import SCI_NOTATION_RE, ascii_digits, is_ascii_digits, remove_spaces, trim


def normalize(inp: dict[str, str]) -> Normalized:
    """Normaliza um registro sem inventar valores ausentes."""
    values = {field: trim(inp.get(field, "")) for field in FIELDS}
    for field in FIELDS[1:]:
        values[field] = remove_spaces(values[field])

    cpf_scientific = SCI_NOTATION_RE.fullmatch(values["cpf"]) is not None
    if not cpf_scientific:
        values["cpf"] = re.sub(r"[.\-]", "", values["cpf"])
        if is_ascii_digits(values["cpf"]) and len(values["cpf"]) < 11:
            values["cpf"] = values["cpf"].zfill(11)

    values["situacao"] = values["situacao"].upper()
    values["publico_alvo"] = values["publico_alvo"].upper()
    values["ddd"] = ascii_digits(values["ddd"]).lstrip("0")

    values["telefone"] = values["telefone"].split(",", maxsplit=1)[0].strip()
    phone = ascii_digits(values["telefone"])
    phone_prefixed = (len(phone) in {12, 13} and phone.startswith("55")) or (
        len(phone) in {11, 12} and phone.startswith("0")
    )
    ddd_from_phone: str | None = None
    ddd_conflict = False
    explicit_ddd = re.match(r"^\([0-9]{2}\)", values["telefone"]) is not None
    if (len(phone) == 11 or (len(phone) == 10 and explicit_ddd)) and not phone_prefixed:
        ddd_from_phone = phone[:2]
        phone = phone[2:]
        if not values["ddd"]:
            values["ddd"] = ddd_from_phone
        elif values["ddd"] != ddd_from_phone:
            ddd_conflict = True
    values["telefone"] = phone

    return Normalized(values, cpf_scientific, ddd_from_phone, ddd_conflict, phone_prefixed)
