"""Controles locais de IA, período e limpeza da carga."""

import streamlit as st

from core.llm.client import OllamaClient
from core.reference import Reference
from core.settings import Settings
from ui import state, texts


def _refresh_llm(client: OllamaClient, default_model: str) -> None:
    status = client.status()
    st.session_state["llm_status"] = status
    st.session_state["models"] = client.list_models() if status.online else []
    if st.session_state["model"] not in st.session_state["models"]:
        st.session_state["model"] = (
            default_model
            if default_model in st.session_state["models"]
            else next(iter(st.session_state["models"]), None)
        )


@st.dialog(texts.CLEAR_TITLE)
def _confirm_clear() -> None:
    st.warning(texts.CLEAR_WARNING)
    if st.button(texts.CLEAR_CONFIRM, type="primary"):
        state.reset()
        st.rerun()
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


def render(settings: Settings, ref: Reference, client: OllamaClient) -> None:
    """Renderiza barra lateral sem enviar dados a serviços externos."""
    with st.sidebar:
        st.header(texts.SIDEBAR_TITLE)
        if st.session_state["llm_status"] is None:
            _refresh_llm(client, settings.ollama_model)
        status = st.session_state["llm_status"]
        st.success(texts.OLLAMA_ONLINE) if status.online else st.warning(texts.OLLAMA_OFFLINE)
        if st.button(texts.OLLAMA_RECHECK):
            _refresh_llm(client, settings.ollama_model)
            st.rerun()
        if st.session_state["models"]:
            selected = st.selectbox(
                texts.MODEL_LABEL,
                st.session_state["models"],
                index=st.session_state["models"].index(st.session_state["model"]),
            )
            st.session_state["model"] = selected
        else:
            st.caption(texts.MODEL_UNAVAILABLE)

        period = st.number_input(
            texts.PERIOD_LABEL,
            min_value=1,
            step=1,
            value=st.session_state["periodo_atual"],
        )
        if period != st.session_state["periodo_atual"]:
            st.session_state["periodo_atual"] = period
            state.bump_revision(ref)
        if st.button(texts.CLEAR_LABEL):
            _confirm_clear()
