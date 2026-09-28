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

    words = " ".join(re.sub(r"[^a-z0-9]+", " ", key).split())
    city_matches: dict[str, set[str]] = {}
    for polo in ref.polos:
        match = re.match(r"^(.*?)-([A-Z]{2})\b", polo)
        if match:
            city = search_key(match.group(1))
            if f" {city} " in f" {words} ":
                city_matches.setdefault(city, set()).add(polo)
    # Um município pode conter o nome de outro: prefira a referência completa.
    specific_cities = [
        city
        for city in city_matches
        if not any(city != other and f" {city} " in f" {other} " for other in city_matches)
    ]
    if specific_cities:
        if len(specific_cities) == 1:
            polos = city_matches[specific_cities[0]]
            if len(polos) == 1:
                return next(iter(polos))
        return None

    close = get_close_matches(key, by_key, n=1, cutoff=POLO_FUZZY_CUTOFF)
    return by_key[close[0]] if close else None
