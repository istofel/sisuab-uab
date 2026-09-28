"""Etapa 3: tabela editável, exclusão confirmada e desfazer."""

import pandas as pd
import streamlit as st

from core.constants import FIELDS
from core.llm.client import OllamaClient
from core.models import PatchOrigin, Severity
from core.normalize import normalize
from core.reference import Reference
from core.text_utils import ascii_digits
from ui import chat_panel, state, suggestions_panel, texts

FIELD_TO_LABEL = {field: texts.FIELD_OPTIONS[field] for field in FIELDS}
LABEL_TO_FIELD = {label: field for field, label in FIELD_TO_LABEL.items()}


def _on_editor_change(ref: Reference, editor_key: str, visible_ids: list[int]) -> None:
    edits = st.session_state[editor_key].get("edited_rows", {})
    by_id = {record.id: record for record in st.session_state["records"]}
    group = st.session_state["patchlog"].new_group()
    changed = False
    for position, columns in edits.items():
        index = int(position)
        if index >= len(visible_ids):
            continue
        record = by_id[visible_ids[index]]
        if any(LABEL_TO_FIELD.get(label) in {"ddd", "telefone"} for label in columns):
            normalized = normalize(record.input)
            if normalized.ddd_from_phone and not normalized.ddd_conflict:
                # A edição conserva o outro campo que a tabela já mostrava separado.
                for field in ("ddd", "telefone"):
                    patch = st.session_state["patchlog"].set_value(
                        record, field, normalized.values[field], PatchOrigin.EDICAO, group
                    )
                    changed = changed or patch is not None
        for label, value in columns.items():
            if label == texts.FIX_DELETE_COLUMN:
                if value:
                    st.session_state["pending_delete"].add(record.id)
                else:
                    st.session_state["pending_delete"].discard(record.id)
            elif label in LABEL_TO_FIELD:
                patch = st.session_state["patchlog"].set_value(
                    record,
                    LABEL_TO_FIELD[label],
                    "" if value is None else str(value),
                    PatchOrigin.EDICAO,
                    group,
                )
                changed = changed or patch is not None
    st.session_state["editor_version"] += 1
    if changed:
        state.bump_revision(ref)


@st.dialog(texts.FIX_DELETE_TITLE)
def _confirm_delete(ref: Reference) -> None:
    ids = st.session_state["pending_delete"]
    st.warning(texts.FIX_DELETE_WARNING.format(count=len(ids)))
    if st.button(texts.FIX_DELETE_CONFIRM, type="primary"):
        group = st.session_state["patchlog"].new_group()
        for record in st.session_state["records"]:
            if record.id in ids and not record.deleted:
                st.session_state["patchlog"].delete(record, group)
        ids.clear()
        state.bump_revision(ref)
        st.rerun()
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


@st.dialog(texts.FIX_POLO_TITLE)
def _confirm_file_polo(file_id: str, polo: str, ref: Reference) -> None:
    matching = [
        record
        for record in st.session_state["records"]
        if record.source_id == file_id and not record.deleted
    ]
    st.warning(texts.SUGGEST_ALL_WARNING.format(count=len(matching)))
    if st.button(texts.FIX_POLO_CONFIRM, type="primary"):
        group = st.session_state["patchlog"].new_group()
        for record in matching:
            st.session_state["patchlog"].set_value(record, "polo", polo, PatchOrigin.LOTE, group)
        state.bump_revision(ref)
        st.rerun()
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


def _editor_rows(ref: Reference, visible_ids: list[int]) -> list[dict]:
    result = state.get_result(ref)
    by_id = {record.id: record for record in st.session_state["records"]}
    rows: list[dict] = []
    for record_id in visible_ids:
        record = by_id[record_id]
        issues = result.by_record.get(record_id, [])
        if any(issue.severity == Severity.ERRO for issue in issues):
            status = texts.FIX_STATUS_ERROR
        elif any(issue.severity == Severity.AVISO for issue in issues):
            status = texts.FIX_STATUS_WARNING
        else:
            status = texts.FIX_STATUS_OK
        displayed = record.input.copy()
        for field in ("ddd", "telefone", "situacao", "publico_alvo"):
            displayed[field] = result.effective[record_id][field]
        if any(issue.code == "DDD_CONFLITO" for issue in issues):
            displayed["telefone"] = ascii_digits(record.input.get("telefone", ""))
        row = {
            texts.FIX_NUMBER: record.id,
            texts.FIX_ORIGIN: f"{record.source_name}, {record.locator}",
            texts.FIX_NAME: record.name_ref,
            **{FIELD_TO_LABEL[field]: displayed.get(field, "") for field in FIELDS},
            texts.FIX_STATE: status,
            texts.FIX_ISSUES: " · ".join(
                issue.message for issue in issues if issue.severity != Severity.INFO
            ),
            texts.FIX_INFORMATION: " · ".join(
                issue.message for issue in issues if issue.severity == Severity.INFO
            ),
            texts.FIX_DELETE_COLUMN: record.id in st.session_state["pending_delete"],
        }
        rows.append(row)
    return rows


def render(ref: Reference, client: OllamaClient) -> None:
    """Mostra contadores, filtros, edição e correções confirmadas."""
    st.header(texts.FIX_TITLE)
    records = [record for record in st.session_state["records"] if not record.deleted]
    if not records:
        st.info(texts.FIX_EMPTY)
        return
    result = state.get_result(ref)
    counts = result.counts
    st.write(
        texts.FIX_COUNTS.format(
            total=counts.total,
            errors=counts.with_error,
            warnings=counts.only_warning,
            ok=counts.ok,
            discarded=counts.discarded,
        )
    )
    st.checkbox(texts.FIX_ONLY_ERRORS, key="only_errors")
    st.checkbox(texts.FIX_SHOW_ORIGINAL, key="show_original")
    visible_ids = [
        record.id
        for record in records
        if not st.session_state["only_errors"]
        or any(issue.severity == Severity.ERRO for issue in result.by_record.get(record.id, []))
    ]
    if visible_ids:
        editor_key = f"editor_{st.session_state['editor_version']}"
        frame = pd.DataFrame(_editor_rows(ref, visible_ids))
        st.data_editor(
            frame,
            num_rows="fixed",
            hide_index=True,
            key=editor_key,
            disabled=[
                texts.FIX_NUMBER,
                texts.FIX_ORIGIN,
                texts.FIX_NAME,
                texts.FIX_STATE,
                texts.FIX_ISSUES,
                texts.FIX_INFORMATION,
            ],
            on_change=_on_editor_change,
            args=(ref, editor_key, visible_ids),
        )
        if st.session_state["show_original"]:
            original = pd.DataFrame(
                [
                    {
                        texts.FIX_NUMBER: record.id,
                        **{
                            FIELD_TO_LABEL[field]: record.original.get(field, "")
                            for field in FIELDS
                        },
                    }
                    for record in records
                    if record.id in visible_ids
                ]
            )
            st.dataframe(original, hide_index=True)
        with st.expander(texts.FIX_DETAILS):
            for record_id in visible_ids:
                for issue in result.by_record.get(record_id, []):
                    if issue.severity != Severity.INFO:
                        st.write(
                            f"{record_id} · {texts.FIELD_OPTIONS[issue.field]} · {issue.message}"
                        )
    else:
        st.success(texts.FIX_NO_ERRORS)

    information = [issue for issue in result.issues if issue.severity == Severity.INFO]
    if information:
        with st.expander(texts.FIX_INFORMATION_TITLE):
            for code in dict.fromkeys(issue.code for issue in information):
                matching = [issue for issue in information if issue.code == code]
                st.info(
                    texts.FIX_INFORMATION_SUMMARY.format(
                        count=len(matching), message=matching[0].message
                    )
                )

    columns = st.columns(2)
    if columns[0].button(texts.FIX_DELETE_BUTTON, disabled=not st.session_state["pending_delete"]):
        _confirm_delete(ref)
    if columns[1].button(texts.FIX_UNDO, disabled=not st.session_state["patchlog"].can_undo()):
        by_id = {record.id: record for record in st.session_state["records"]}
        st.session_state["patchlog"].undo_last(by_id)
        state.bump_revision(ref)
        st.session_state["editor_version"] += 1
        st.rerun()

    with st.expander(texts.FIX_FILE_POLO):
        file_ids = st.session_state["file_order"]
        file_labels = {
            f"{st.session_state['files'][file_id].name} · {file_id[:8]}": file_id
            for file_id in file_ids
        }
        selected_label = st.selectbox(texts.FIX_FILE_SELECT, list(file_labels))
        file_id = file_labels.get(selected_label)
        polo = st.selectbox(texts.FIX_POLO_SELECT, ref.polos)
        if st.button(texts.FIX_POLO_APPLY, disabled=not file_id):
            _confirm_file_polo(file_id, polo, ref)
    suggestions_panel.render(ref)
    chat_panel.render(ref, client)
    if counts.with_error:
        st.warning(texts.FIX_BLOCKED.format(errors=counts.with_error))
    else:
        st.success(texts.FIX_ALL_CORRECTED)
    if st.session_state["pending_delete"] or st.session_state["chat_proposals"]:
        st.warning(texts.FIX_PENDING_ACTIONS)
    st.button(
        texts.FIX_CONTINUE,
        disabled=not state.can_enter_step(ref, 4),
        on_click=state.go_to_step,
        args=(ref, 4),
    )
