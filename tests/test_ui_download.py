"""O download exige verificação da revisão atual."""

from pathlib import Path
from unittest.mock import patch

from core.models import FileFormat, ReadMethod, Record, SourceFile
from core.patches import PatchLog
from core.reference import load_reference
from core.settings import Settings
from ui import state
from ui.step_download import _verify_current


def _session(cpf: str) -> dict:
    values = {
        "polo": "ARAGUAÍNA-TO CIMBA",
        "cpf": cpf,
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
        "records": [record],
        "files": {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)},
        "patchlog": PatchLog(),
        "periodo_atual": None,
        "dismissed": set(),
        "revision": 0,
        "result": None,
        "result_revision": None,
        "csv_bytes": None,
        "verify_report": None,
        "export_error": False,
        "verified_revision": None,
    }


def test_download_needs_zero_errors_and_current_verification() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    session = _session("01234567891")
    with patch("streamlit.session_state", session):
        assert not state.download_allowed(ref)
        _verify_current(ref, Settings())
        assert session["csv_bytes"] is None
        session["records"][0].input["cpf"] = "01234567890"
        state.bump_revision(ref)
        assert not state.download_allowed(ref)
        _verify_current(ref, Settings())
        assert state.download_allowed(ref)
        assert (
            session["csv_bytes"]
            == (
                "ARAGUAÍNA-TO CIMBA;01234567890;CUR;aluno@exemplo.com.br;63;987654321;DS\n"
            ).encode()
        )
        state.bump_revision(ref)
        assert not state.download_allowed(ref)
        assert session["csv_bytes"] is None
