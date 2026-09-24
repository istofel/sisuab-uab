"""Etapa 1: envio de arquivos e gestão da lista da carga."""

import streamlit as st

from core.constants import SUPPORTED_EXTENSIONS
from core.models import FileState
from core.pipeline import build_records, ingest_upload
from core.reference import Reference
from ui import state, texts


def _remove_file(file_id: str, ref: Reference) -> None:
    """Remove o arquivo, seus registros e o valor anterior do uploader."""
    removed_ids = {
        record.id for record in st.session_state["records"] if record.source_id == file_id
    }
    st.session_state["records"] = [
        record for record in st.session_state["records"] if record.source_id != file_id
    ]
    st.session_state["patchlog"].drop_records(removed_ids)
    st.session_state["pending_delete"].difference_update(removed_ids)
    st.session_state["files"].pop(file_id, None)
    st.session_state["file_order"].remove(file_id)
    st.session_state["uploader_version"] += 1
    state.bump_revision(ref)


@st.dialog(texts.UPLOAD_REMOVE_TITLE)
def _confirm_remove(file_id: str, ref: Reference) -> None:
    st.warning(texts.UPLOAD_REMOVE_WARNING)
    if st.button(texts.UPLOAD_REMOVE_CONFIRM, type="primary"):
        _remove_file(file_id, ref)
        st.rerun()
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


def render(ref: Reference) -> None:
    """Recebe vários arquivos e adiciona os já confirmados à carga."""
    st.header(texts.UPLOAD_TITLE)
    st.caption(texts.UPLOAD_HELP)
    uploads = st.file_uploader(
        texts.UPLOAD_TITLE,
        type=sorted(extension[1:] for extension in SUPPORTED_EXTENSIONS),
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_version']}",
        label_visibility="collapsed",
    )
    if uploads:
        changed = False
        for upload in uploads:
            source = ingest_upload(
                st.session_state["files"],
                upload.name,
                upload.getvalue(),
                len(st.session_state["records"]),
                ref,
            )
            if source.state == FileState.COM_FALHA:
                st.session_state.setdefault("upload_notices", []).extend(source.notices)
                continue
            st.session_state["file_order"].append(source.id)
            if source.state == FileState.CONFIRMADO:
                records = build_records(
                    source,
                    len(st.session_state["file_order"]),
                    st.session_state["next_record_id"],
                )
                st.session_state["records"].extend(records)
                st.session_state["next_record_id"] += len(records)
            changed = True
        st.session_state["uploader_version"] += 1
        if changed:
            state.bump_revision(ref)
        st.rerun()

    for notice in st.session_state.get("upload_notices", []):
        st.warning(notice.message)
    st.session_state["upload_notices"] = []

    st.subheader(texts.UPLOAD_LOADED)
    if not st.session_state["file_order"]:
        st.info(texts.UPLOAD_EMPTY)
        st.button(texts.UPLOAD_CONTINUE, disabled=True)
        return
    for file_id in st.session_state["file_order"]:
        source = st.session_state["files"][file_id]
        columns = st.columns([4, 1])
        columns[0].write(
            texts.REVIEW_FILE.format(
                name=source.name,
                format=source.fmt.value,
                rows=sum(len(table.rows) for table in source.tables),
            )
        )
        columns[0].caption(texts.REVIEW_STATE.format(state=source.state.value))
        if columns[1].button(texts.UPLOAD_REMOVE, key=f"remove_{file_id}"):
            _confirm_remove(file_id, ref)
        for notice in source.notices:
            st.warning(notice.message)
    st.button(texts.UPLOAD_CONTINUE, on_click=state.go_to_step, args=(ref, 2))
