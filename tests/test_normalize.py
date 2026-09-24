"""Transformações determinísticas dos campos."""

from core.normalize import normalize


def test_spaces_and_case() -> None:
    result = normalize(
        {
            "polo": " ARAGUAÍNA-TO  CIMBA ",
            "cpf": " 012.345.678-90 ",
            "situacao": " cur ",
            "email": " Aluno @Exemplo.com.br ",
            "ddd": " 063 ",
            "telefone": " 98765-4321 ",
            "publico_alvo": " ds ",
        }
    )
    assert result.values == {
        "polo": "ARAGUAÍNA-TO  CIMBA",
        "cpf": "01234567890",
        "situacao": "CUR",
        "email": "Aluno@Exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }


def test_ddd_zero_and_cpf_leading_zero() -> None:
    result = normalize({"ddd": "061", "cpf": "1234567890"})
    assert result.values["ddd"] == "61"
    assert result.values["cpf"] == "01234567890"


def test_phone_with_ddd_is_split_or_flagged() -> None:
    inferred = normalize({"telefone": "(63) 98765-4321"})
    assert inferred.values["ddd"] == "63"
    assert inferred.values["telefone"] == "987654321"
    assert inferred.ddd_from_phone == "63"

    conflict = normalize({"ddd": "61", "telefone": "63987654321"})
    assert conflict.values["ddd"] == "61"
    assert conflict.ddd_conflict


def test_phone_prefixes_and_eight_digits_are_not_corrected() -> None:
    assert normalize({"telefone": "98765432"}).values["telefone"] == "98765432"
    for phone in ("5563987654321", "063987654321"):
        result = normalize({"telefone": phone})
        assert result.phone_prefixed
        assert result.values["telefone"] == phone


def test_scientific_cpf_is_preserved_for_error() -> None:
    result = normalize({"cpf": "3,42E+10"})
    assert result.cpf_scientific
    assert result.values["cpf"] == "3,42E+10"
