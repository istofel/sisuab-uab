"""Sugestões determinísticas que exigem aceite explícito."""

import streamlit as st

from core.models import PatchOrigin, Suggestion
from core.reference import Reference
from ui import state, texts


def _accept(suggestion: Suggestion, ref: Reference) -> None:
    record = next(
        record for record in st.session_state["records"] if record.id == suggestion.record_id
    )
    patch = st.session_state["patchlog"].set_value(
        record, suggestion.field, suggestion.proposed, PatchOrigin.SUGESTAO
    )
    if patch is not None:
        state.bump_revision(ref)
    st.rerun()


def _reject(suggestion: Suggestion, ref: Reference) -> None:
    st.session_state["dismissed"].add(suggestion.key)
    state.bump_revision(ref)
    st.rerun()


def _accept_all(suggestion: Suggestion, ref: Reference) -> int:
    """Aplica um único grupo a todas as linhas com o mesmo valor atual."""
    matching = [
        record
        for record in st.session_state["records"]
        if not record.deleted and record.input.get(suggestion.field) == suggestion.current
    ]
    group = st.session_state["patchlog"].new_group()
    for record in matching:
        st.session_state["patchlog"].set_value(
            record, suggestion.field, suggestion.proposed, PatchOrigin.LOTE, group
        )
    if matching:
        state.bump_revision(ref)
    return len(matching)


@st.dialog(texts.SUGGEST_ALL_TITLE)
def _confirm_all(suggestion: Suggestion, ref: Reference) -> None:
    matching = [
        record
        for record in st.session_state["records"]
        if not record.deleted and record.input.get(suggestion.field) == suggestion.current
    ]
    st.warning(texts.SUGGEST_ALL_WARNING.format(count=len(matching)))
    if st.button(texts.SUGGEST_ALL_CONFIRM, type="primary"):
        _accept_all(suggestion, ref)
        st.rerun()
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


def render(ref: Reference) -> None:
    """Mostra alterações propostas sem modificar registros automaticamente."""
    st.subheader(texts.SUGGEST_TITLE)
    suggestions = state.get_result(ref).suggestions
    if not suggestions:
        st.caption(texts.SUGGEST_EMPTY)
        return
    for suggestion in suggestions:
        st.write(
            texts.SUGGEST_ITEM.format(
                record=suggestion.record_id,
                field=texts.FIELD_OPTIONS[suggestion.field],
                current=suggestion.current,
                proposed=suggestion.proposed,
            )
        )
        columns = st.columns(3)
        key = f"{suggestion.record_id}_{suggestion.field}_{suggestion.proposed}"
        if columns[0].button(texts.SUGGEST_ACCEPT, key=f"accept_{key}"):
            _accept(suggestion, ref)
        if columns[1].button(texts.SUGGEST_REJECT, key=f"reject_{key}"):
            _reject(suggestion, ref)
        if suggestion.field == "polo" and columns[2].button(
            texts.SUGGEST_ACCEPT_ALL, key=f"all_{key}"
        ):
            _confirm_all(suggestion, ref)
