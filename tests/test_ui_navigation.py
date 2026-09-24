"""Passagem de etapa depende da carga e da validação atual."""

from pathlib import Path
from unittest.mock import patch

from core.models import FileFormat, FileState, ReadMethod, Record, SourceFile
from core.reference import load_reference
from tests.factories import make_cpf
from ui import state


def _session() -> dict:
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": make_cpf("123456781"),
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
    return {
        **state._defaults(),
        "files": {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)},
        "file_order": ["source"],
        "records": [record],
    }


def test_progression_requires_upload_and_review_confirmation() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    session = _session()
    with patch("streamlit.session_state", session):
        session["files"] = {}
        session["file_order"] = []
        assert not state.can_enter_step(ref, 2)
        session["files"] = {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)}
        session["file_order"] = ["source"]
        assert state.can_enter_step(ref, 2)
        assert not state.can_enter_step(ref, 3)
        session["files"]["source"].state = FileState.CONFIRMADO
        assert state.can_enter_step(ref, 3)


def test_download_phase_opens_only_after_errors_and_pending_actions_clear() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    session = _session()
    session["files"]["source"].state = FileState.CONFIRMADO
    with patch("streamlit.session_state", session):
        assert state.can_enter_step(ref, 4)
        session["records"][0].input["telefone"] = "9923503572"
        state.bump_revision(ref)
        assert not state.can_enter_step(ref, 4)
        session["records"][0].input["telefone"] = "923503572"
        state.bump_revision(ref)
        assert state.can_enter_step(ref, 4)
        session["pending_delete"].add(1)
        assert not state.can_enter_step(ref, 4)
        session["pending_delete"].clear()
        session["chat_proposals"] = [object()]
        assert not state.can_enter_step(ref, 4)
        session["chat_proposals"] = []
        assert state.can_enter_step(ref, 4)


def test_navigation_rechecks_direct_phase_selection() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    session = _session()
    session["files"]["source"].state = FileState.CONFIRMADO
    with patch("streamlit.session_state", session):
        session["records"][0].input["email"] = "invalido"
        state.bump_revision(ref)
        session["nav_step"] = "4. Baixar"
        state.on_navigation_change(ref)
        assert session["step"] == 1
        assert session["nav_step"] == "1. Enviar"
        session["records"][0].input["email"] = "aluno@exemplo.com.br"
        state.bump_revision(ref)
        assert state.go_to_step(ref, 4)
        assert session["step"] == 4
        assert session["nav_step"] == "4. Baixar"
