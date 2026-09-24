"""Correspondência aproximada de polos."""

from pathlib import Path

import pytest

from core.reference import load_reference
from core.suggest import suggest_polo


@pytest.fixture(scope="module")
def ref():
    return load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))


@pytest.mark.parametrize(
    "value",
    ["ARAGUAINA-TO CIMBA", "araguaína-to cimba", "ARAGUAÍNA-TO  CIMBA", "ARAGUAINA"],
)
def test_equivalent_polos_are_suggestions(value, ref) -> None:
    assert suggest_polo(value, ref) == "ARAGUAÍNA-TO CIMBA"


def test_typo_can_be_suggested(ref) -> None:
    assert suggest_polo("XAMBIOA-TO CENTOR", ref) == "XAMBIOÁ-TO CENTRO"


def test_unrelated_polo_has_no_suggestion(ref) -> None:
    assert suggest_polo("CIDADE INEXISTENTE", ref) is None
