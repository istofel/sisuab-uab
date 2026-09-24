"""Sugestões de polo sem alteração automática dos dados."""

import re
from difflib import get_close_matches

from core.constants import POLO_FUZZY_CUTOFF
from core.reference import Reference
from core.text_utils import search_key


def suggest_polo(value: str, ref: Reference) -> str | None:
    """Propõe um polo por equivalência ou semelhança do nome."""
    key = search_key(value)
    if not key:
        return None

    by_key = {search_key(polo): polo for polo in ref.polos}
    if key in by_key:
        return by_key[key]

    city_matches: set[str] = set()
    for polo in ref.polos:
        match = re.match(r"^(.*?)-([A-Z]{2})\b", polo)
        if match and key in {search_key(match.group(1)), search_key(match.group(0))}:
            city_matches.add(polo)
    if len(city_matches) == 1:
        return next(iter(city_matches))

    close = get_close_matches(key, by_key, n=1, cutoff=POLO_FUZZY_CUTOFF)
    return by_key[close[0]] if close else None
