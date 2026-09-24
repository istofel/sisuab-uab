"""Edição e lote exigem revalidação e mantêm desfazer."""

from pathlib import Path
from unittest.mock import patch

from core.models import FileFormat, FileState, ReadMethod, Record, SourceFile, Suggestion
from core.patches import PatchLog
from core.reference import load_reference
from tests.factories import make_cpf
from ui import state, texts
from ui.step_fix import _editor_rows, _on_editor_change
from ui.suggestions_panel import _accept_all


def _record(record_id: int, cpf: str, polo: str = "ARAGUAÍNA-TO CIMBA") -> Record:
    values = {
        "polo": polo,
        "cpf": cpf,
        "situacao": "CUR",
        "email": f"aluno{record_id}@exemplo.com.br",
        "ddd": "63",
        "telefone": "987654321",
        "publico_alvo": "DS",
    }
    return Record(
        record_id,
        "source",
        "a.csv",
        f"linha {record_id}",
        (1, record_id),
        ReadMethod.TABULAR,
        "",
        values.copy(),
        values.copy(),
    )


def _session(records: list[Record]) -> dict:
    return {
        "records": records,
        "files": {"source": SourceFile("source", "a.csv", FileFormat.CSV, 100)},
        "file_order": ["source"],
        "patchlog": PatchLog(),
        "periodo_atual": None,
        "dismissed": set(),
        "revision": 0,
        "result": None,
        "result_revision": None,
        "csv_bytes": None,
        "verify_report": None,
        "verified_revision": None,
        "editor_version": 0,
        "pending_delete": set(),
        "chat_proposals": [],
    }


def test_editor_revalidates_corrected_cpf() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    good = make_cpf("123456781")
    bad = good[:-1] + str((int(good[-1]) + 1) % 10)
    session = _session([_record(1, bad)])
    session["editor_0"] = {"edited_rows": {0: {"CPF": good}}}
    with patch("streamlit.session_state", session):
        _on_editor_change(ref, "editor_0", [1])
    assert session["records"][0].input["cpf"] == good
    assert session["result"].counts.with_error == 0
    assert session["revision"] == 1


def test_each_corrected_issue_disappears_until_no_errors_remain() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    good_cpf = make_cpf("123456781")
    bad_cpf = good_cpf[:-1] + str((int(good_cpf[-1]) + 1) % 10)
    record = _record(1, bad_cpf)
    record.input["telefone"] = "9923503572"
    record.input["email"] = "invalido"
    session = _session([record])
    session["files"]["source"].state = FileState.CONFIRMADO
    with patch("streamlit.session_state", session):
        assert state.get_result(ref).counts.with_error == 1
        assert len(state.get_result(ref).by_record[1]) == 3
        for version, label, value, remaining in [
            (0, "CPF", good_cpf, 2),
            (1, "Telefone", "923503572", 1),
            (2, "E-mail", "aluno1@exemplo.com.br", 0),
        ]:
            key = f"editor_{version}"
            session[key] = {"edited_rows": {0: {label: value}}}
            _on_editor_change(ref, key, [1])
            assert len(state.get_result(ref).by_record[1]) == remaining
            row = _editor_rows(ref, [1])[0]
            if remaining == 0:
                assert row[texts.FIX_ISSUES] == ""
                assert row[texts.FIX_STATE] == texts.FIX_STATUS_OK
        assert state.can_enter_step(ref, 4)


def test_accept_all_and_undo_restores_every_row() -> None:
    ref = load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))
    current = "ARAGUAINA-TO CIMBA"
    records = [
        _record(1, make_cpf("123456781"), current),
        _record(2, make_cpf("123456782"), current),
    ]
    session = _session(records)
    suggestion = Suggestion(1, "polo", current, "ARAGUAÍNA-TO CIMBA", "POLO_SUGESTAO")
    with patch("streamlit.session_state", session):
        assert _accept_all(suggestion, ref) == 2
        assert session["result"].counts.with_error == 0
        assert len(session["patchlog"].undo_last({record.id: record for record in records})) == 2
    assert all(record.input["polo"] == current for record in records)
