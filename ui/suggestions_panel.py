"""Sugestões determinísticas que exigem aceite explícito."""

import streamlit as st

from core.models import PatchOrigin, Record, Suggestion
from core.normalize import normalize
from core.reference import Reference
from ui import state, texts


def _suggestion_groups(suggestions: list[Suggestion]) -> list[list[Suggestion]]:
    """Reúne variantes de polo com o mesmo destino e mantém os demais campos individuais."""
    groups: dict[tuple, list[Suggestion]] = {}
    for suggestion in suggestions:
        key = (
            (suggestion.field, suggestion.proposed)
            if suggestion.field == "polo"
            else suggestion.key
        )
        groups.setdefault(key, []).append(suggestion)
    return list(groups.values())


def _pending_group(suggestion: Suggestion, ref: Reference) -> list[Suggestion]:
    """Consulta a revisão atual para não aceitar propostas antigas ou recusadas."""
    for group in _suggestion_groups(state.get_result(ref).suggestions):
        if any(item.key == suggestion.key for item in group):
            return group
    return []


def _matching_records(suggestion: Suggestion, ref: Reference) -> list[Record]:
    ids = {item.record_id for item in _pending_group(suggestion, ref)}
    return [
        record for record in st.session_state["records"] if not record.deleted and record.id in ids
    ]


def _accept(suggestion: Suggestion, ref: Reference) -> None:
    if not _pending_group(suggestion, ref):
        return
    record = next(
        record for record in st.session_state["records"] if record.id == suggestion.record_id
    )
    group = st.session_state["patchlog"].new_group()
    if suggestion.field == "telefone":
        normalized = normalize(record.input)
        if normalized.ddd_from_phone and not normalized.ddd_conflict:
            st.session_state["patchlog"].set_value(
                record, "ddd", normalized.values["ddd"], PatchOrigin.SUGESTAO, group
            )
    patch = st.session_state["patchlog"].set_value(
        record, suggestion.field, suggestion.proposed, PatchOrigin.SUGESTAO, group
    )
    if patch is not None:
        state.bump_revision(ref)
    st.rerun()


def _reject(suggestion: Suggestion, ref: Reference) -> None:
    group = _pending_group(suggestion, ref)
    if not group:
        return
    st.session_state["dismissed"].update(item.key for item in group)
    state.bump_revision(ref)
    st.rerun()


def _accept_all(suggestion: Suggestion, ref: Reference) -> int:
    """Aplica um grupo reversível às sugestões de polo com o mesmo destino."""
    matching = _matching_records(suggestion, ref)
    if not matching:
        return 0
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
    matching = _matching_records(suggestion, ref)
    st.warning(
        texts.SUGGEST_POLO_ALL_WARNING.format(count=len(matching), proposed=suggestion.proposed)
    )
    st.dataframe(
        [
            {
                texts.FIX_NUMBER: record.id,
                texts.SUGGEST_CURRENT_POLO: record.input["polo"],
                texts.SUGGEST_PROPOSED_POLO: suggestion.proposed,
            }
            for record in matching
        ],
        hide_index=True,
    )
    if st.button(texts.SUGGEST_ALL_CONFIRM, type="primary", disabled=not matching):
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
    for group in _suggestion_groups(suggestions):
        suggestion = group[0]
        key = f"{suggestion.record_id}_{suggestion.field}_{suggestion.proposed}"
        if suggestion.field == "polo" and len(group) > 1:
            st.write(texts.SUGGEST_GROUP.format(count=len(group), proposed=suggestion.proposed))
            st.caption(
                texts.SUGGEST_GROUP_VALUES.format(
                    values=" · ".join(dict.fromkeys(item.current for item in group))
                )
            )
            columns = st.columns(2)
            if columns[0].button(
                texts.SUGGEST_GROUP_ACCEPT.format(count=len(group)), key=f"all_{key}"
            ):
                _confirm_all(suggestion, ref)
            if columns[1].button(texts.SUGGEST_GROUP_REJECT, key=f"reject_{key}"):
                _reject(suggestion, ref)
            continue
        st.write(
            texts.SUGGEST_ITEM.format(
                record=suggestion.record_id,
                field=texts.FIELD_OPTIONS[suggestion.field],
                current=suggestion.current,
                proposed=suggestion.proposed,
            )
        )
        columns = st.columns(2)
        if columns[0].button(texts.SUGGEST_ACCEPT, key=f"accept_{key}"):
            _accept(suggestion, ref)
        if columns[1].button(texts.SUGGEST_REJECT, key=f"reject_{key}"):
            _reject(suggestion, ref)
