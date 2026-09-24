"""Entrada da aplicação local Streamlit."""

from pathlib import Path

import streamlit as st

from core.constants import APP_NAME, DDDS_FILE, POLOS_FILE
from core.errors import ConfigError
from core.llm.client import OllamaClient
from core.privacy import setup_logging
from core.reference import load_reference
from core.settings import load_settings
from ui import sidebar, state, step_download, step_fix, step_review, step_upload, texts

BANNER_DIR = Path(__file__).resolve().parent / "docs" / "banner"

st.set_page_config(page_title=APP_NAME, layout="wide")


@st.cache_resource
def cached_settings():
    """Guarda somente configuração sem dados de aluno."""
    return load_settings()


@st.cache_resource
def cached_reference():
    """Guarda listas estáticas sem dados de aluno."""
    return load_reference(Path(POLOS_FILE), Path(DDDS_FILE))


@st.cache_resource
def cached_client(base_url: str, timeout_s: int):
    """Guarda sessão HTTP local sem dados de aluno."""
    return OllamaClient(base_url, timeout_s)


@st.cache_resource
def cached_logging(log_dir: str, level: str) -> None:
    """Inicializa logs mascarados uma única vez."""
    setup_logging(log_dir, level)


def main() -> None:
    """Inicializa configuração, estado e navegação pelas quatro etapas."""
    state.init()
    try:
        settings = cached_settings()
        ref = cached_reference()
        cached_logging(settings.log_dir, settings.log_level)
        client = cached_client(settings.ollama_base_url, settings.ollama_timeout_s)
    except ConfigError as exc:
        st.error(texts.CONFIG_ERROR)
        st.caption(texts.CONFIG_KEY.format(key=exc.key))
        st.stop()

    header = st.columns([7, 3], vertical_alignment="center")
    header[0].title(texts.PAGE_TITLE)
    header[0].caption(texts.PAGE_CAPTION)
    logos = header[1].columns(2, gap="small", vertical_alignment="center")
    logos[0].image(BANNER_DIR / "sisuab-transparent.png", width=105)
    logos[1].image(BANNER_DIR / "capes.jpg", width=105)
    sidebar.render(settings, ref, client)
    if not state.can_enter_step(ref, st.session_state["step"]):
        for previous in (3, 2, 1):
            if state.can_enter_step(ref, previous):
                state.go_to_step(ref, previous)
                break
    st.radio(
        APP_NAME,
        texts.STEPS,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_step",
        on_change=state.on_navigation_change,
        args=(ref,),
    )
    if st.session_state["nav_blocked"] is not None:
        st.warning(texts.NAV_BLOCKED[st.session_state["nav_blocked"]])
        st.session_state["nav_blocked"] = None
    if st.session_state["step"] == 1:
        step_upload.render(ref)
    elif st.session_state["step"] == 2:
        step_review.render(ref, client)
    elif st.session_state["step"] == 3 and state.phase(ref) == "AGUARDANDO_CONFIRMACAO":
        st.warning(texts.REVIEW_BLOCKED)
    elif st.session_state["step"] == 3:
        step_fix.render(ref, client)
    elif st.session_state["step"] == 4:
        step_download.render(ref, settings)
    else:
        st.info(texts.STEP_UNAVAILABLE)


if __name__ == "__main__":
    main()
