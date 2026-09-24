"""Remoção de arquivo e descarte do estado do uploader."""

from pathlib import Path
from unittest.mock import patch

from core.models import FileFormat, PatchOrigin, ReadMethod, Record, SourceFile
from core.patches import PatchLog
from core.reference import load_reference
from ui.step_upload import _remove_file


def test_remove_file_drops_records_patches_and_old_upload_key() -> None:
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
        1, "file", "a.csv", "linha 2", (1, 1), ReadMethod.TABULAR, "", values.copy(), values.copy()
    )
    log = PatchLog()
    log.set_value(record, "ddd", "61", PatchOrigin.EDICAO)
    session = {
        "files": {"file": SourceFile("file", "a.csv", FileFormat.CSV, 100)},
        "file_order": ["file"],
        "records": [record],
        "patchlog": log,
        "pending_delete": {1},
        "uploader_version": 1,
        "revision": 0,
        "periodo_atual": None,
        "dismissed": set(),
        "result": None,
        "result_revision": None,
        "csv_bytes": None,
        "verify_report": None,
        "verified_revision": None,
    }
    with patch("streamlit.session_state", session):
        _remove_file("file", ref)
    assert session["files"] == {}
    assert session["records"] == []
    assert session["file_order"] == []
    assert session["pending_delete"] == set()
    assert session["uploader_version"] == 2
    assert session["revision"] == 1
    assert not log.can_undo()
