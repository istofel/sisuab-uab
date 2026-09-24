"""Propostas do chat só alteram registros após a seleção explícita."""

from pathlib import Path
from unittest.mock import patch

from core.llm.chat import ProposedPatch
from core.models import FileFormat, ReadMethod, Record, SourceFile
from core.patches import PatchLog
from core.reference import load_reference
from ui.chat_panel import _apply_selected


def test_apply_only_valid_selected_chat_proposals() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": "01234567890",
        "situacao": "CUR",
        "email": "aluno@exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }
    record = Record(
        1,
        "source",
        "a.csv",
        "linha 1",
        (1, 1),
        ReadMethod.TABULAR,
        "",
        values.copy(),
        values.copy(),
    )
    session = {
        "records": [record],
        "files": {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)},
        "patchlog": PatchLog(),
        "chat_proposals": [
            ProposedPatch(1, "ddd", "61", "63", True, None),
            ProposedPatch(99, "ddd", "62", "", False, "REGISTRO_INEXISTENTE"),
        ],
        "periodo_atual": None,
        "dismissed": set(),
        "revision": 0,
        "result": None,
        "result_revision": None,
        "csv_bytes": None,
        "verify_report": None,
        "verified_revision": None,
    }
    with patch("streamlit.session_state", session):
        assert _apply_selected([0, 1], ref) == 1
    assert record.input["ddd"] == "61"
    assert session["chat_proposals"] == []
    assert session["revision"] == 1
