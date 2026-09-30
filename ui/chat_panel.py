"""Chat local com propostas que dependem de confirmação explícita."""

import streamlit as st

from core.errors import LLMResponseError, LLMUnavailableError
from core.llm.chat import ChatTurn, ask
from core.llm.client import OllamaClient
from core.models import PatchOrigin
from core.normalize import normalize
from core.reference import Reference
from ui import state, texts


def _apply_selected(indices: list[int], ref: Reference) -> int:
    """Aplica somente propostas válidas selecionadas pela usuária."""
    proposals = st.session_state["chat_proposals"]
    by_id = {record.id: record for record in st.session_state["records"]}
    group = st.session_state["patchlog"].new_group()
    applied = 0
    for index in indices:
        if index < 0 or index >= len(proposals):
            continue
        proposal = proposals[index]
        record = by_id.get(proposal.record_id)
        if not proposal.valid or record is None or record.deleted:
            continue
        preserved = False
        if proposal.field in {"ddd", "telefone"}:
            normalized = normalize(record.input)
            if normalized.ddd_from_phone and not normalized.ddd_conflict:
                for field in ("ddd", "telefone"):
                    patch = st.session_state["patchlog"].set_value(
                        record, field, normalized.values[field], PatchOrigin.CHAT, group
                    )
                    preserved = preserved or patch is not None
        patch = st.session_state["patchlog"].set_value(
            record, proposal.field, proposal.new, PatchOrigin.CHAT, group
        )
        applied += patch is not None or preserved
    st.session_state["chat_proposals"] = []
    if applied:
        state.bump_revision(ref)
    return applied


def render(ref: Reference, client: OllamaClient) -> None:
    """Mostra conversa e alterações propostas sem aplicar nada automaticamente."""
    st.subheader(texts.CHAT_TITLE)
    with st.container(height=420, key="chat_conversation", autoscroll=True):
        for turn in st.session_state["chat_history"]:
            with st.chat_message(turn.role):
                st.write(turn.content)

        proposals = st.session_state["chat_proposals"]
        if proposals:
            st.warning(texts.CHAT_WARNING)
            if st.session_state.get("chat_context_truncated"):
                st.caption(texts.CHAT_CONTEXT_TRUNCATED)
            selected: list[int] = []
            for index, proposal in enumerate(proposals):
                label = texts.CHAT_PROPOSAL.format(
                    record=proposal.record_id,
                    field=texts.FIELD_OPTIONS[proposal.field],
                    current=proposal.current,
                    new=proposal.new,
                )
                if proposal.valid:
                    if st.checkbox(label, value=True, key=f"chat_proposal_{index}"):
                        selected.append(index)
                else:
                    st.caption(label)
                    st.caption(
                        texts.CHAT_INVALID.format(
                            reason=texts.CHAT_REASONS.get(proposal.reason, proposal.reason),
                        )
                    )
            columns = st.columns(2)
            if columns[0].button(texts.CHAT_APPLY, disabled=not selected):
                _apply_selected(selected, ref)
                st.rerun()
            if columns[1].button(texts.CHAT_REJECT):
                st.session_state["chat_proposals"] = []
                st.rerun()

    status = st.session_state["llm_status"]
    available = status is not None and status.online and st.session_state["model"] is not None
    if not available:
        st.caption(texts.CHAT_OFFLINE)
    message = st.chat_input(texts.CHAT_INPUT, disabled=not available)
    if message:
        st.session_state["chat_history"].append(ChatTurn("user", message))
        st.session_state["chat_proposals"] = []
        try:
            response, proposals, truncated = ask(
                client,
                st.session_state["model"],
                st.session_state["chat_history"][:-1],
                message,
                st.session_state["records"],
                state.get_result(ref),
                ref,
            )
        except (LLMResponseError, LLMUnavailableError):
            st.session_state["chat_history"].append(
                ChatTurn("assistant", texts.CHAT_RESPONSE_ERROR)
            )
        else:
            st.session_state["chat_history"].append(ChatTurn("assistant", response))
            st.session_state["chat_proposals"] = proposals
            st.session_state["chat_context_truncated"] = truncated
        st.rerun()
