"""Estado de sessão e revisão única dos dados."""

import streamlit as st

from core.models import FileState, ValidationResult
from core.patches import PatchLog
from core.reference import Reference
from core.validate import validate_all
from ui import texts


def _defaults() -> dict:
    return {
        "step": 1,
        "nav_step": texts.STEPS[0],
        "nav_blocked": None,
        "files": {},
        "file_order": [],
        "records": [],
        "next_record_id": 1,
        "patchlog": PatchLog(),
        "dismissed": set(),
        "pending_delete": set(),
        "periodo_atual": None,
        "revision": 0,
        "result": None,
        "result_revision": None,
        "csv_bytes": None,
        "verify_report": None,
        "export_error": False,
        "verified_revision": None,
        "llm_status": None,
        "models": [],
        "model": None,
        "chat_history": [],
        "chat_proposals": [],
        "chat_context_truncated": False,
        "only_errors": False,
        "show_original": False,
        "editor_version": 0,
        "uploader_version": 0,
        "upload_notices": [],
    }


def init() -> None:
    """Inicializa apenas as chaves ainda ausentes."""
    for key, value in _defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset() -> None:
    """Descarta a carga e mantém a escolha e o status da IA local."""
    model = st.session_state.get("model")
    llm_status = st.session_state.get("llm_status")
    for key, value in _defaults().items():
        st.session_state[key] = value
    st.session_state["model"] = model
    st.session_state["llm_status"] = llm_status


def bump_revision(ref: Reference) -> None:
    """Incrementa a revisão, revalida tudo e invalida a verificação anterior."""
    st.session_state["revision"] += 1
    st.session_state["result"] = validate_all(
        st.session_state["records"],
        st.session_state["files"],
        ref,
        st.session_state["periodo_atual"],
        st.session_state["dismissed"],
    )
    st.session_state["result_revision"] = st.session_state["revision"]
    st.session_state["csv_bytes"] = None
    st.session_state["verify_report"] = None
    st.session_state["export_error"] = False
    st.session_state["verified_revision"] = None


def get_result(ref: Reference) -> ValidationResult:
    """Devolve a validação da revisão atual."""
    if st.session_state["result_revision"] != st.session_state["revision"]:
        st.session_state["result"] = validate_all(
            st.session_state["records"],
            st.session_state["files"],
            ref,
            st.session_state["periodo_atual"],
            st.session_state["dismissed"],
        )
        st.session_state["result_revision"] = st.session_state["revision"]
    return st.session_state["result"]


def download_allowed(ref: Reference) -> bool:
    """Autoriza download só com zero erros e bytes verificados na revisão atual."""
    result = get_result(ref)
    report = st.session_state["verify_report"]
    return (
        result.counts.with_error == 0
        and report is not None
        and report.ok
        and st.session_state["verified_revision"] == st.session_state["revision"]
    )


def can_enter_step(ref: Reference, target: int) -> bool:
    """Confere as condições da etapa antes de permitir a navegação."""
    if target == 1:
        return True
    files = st.session_state["files"]
    if not files or not st.session_state["file_order"]:
        return False
    if target == 2:
        return True
    if any(source.state != FileState.CONFIRMADO for source in files.values()):
        return False
    if not any(not record.deleted for record in st.session_state["records"]):
        return False
    if target == 3:
        return True
    if target == 4:
        return (
            get_result(ref).counts.with_error == 0
            and not st.session_state["pending_delete"]
            and not st.session_state["chat_proposals"]
        )
    return False


def go_to_step(ref: Reference, target: int) -> bool:
    """Avança somente quando a validação atual libera a etapa."""
    if not can_enter_step(ref, target):
        st.session_state["nav_blocked"] = target
        st.session_state["nav_step"] = texts.STEPS[st.session_state["step"] - 1]
        return False
    st.session_state["step"] = target
    st.session_state["nav_step"] = texts.STEPS[target - 1]
    st.session_state["nav_blocked"] = None
    return True


def on_navigation_change(ref: Reference) -> None:
    """Valida também a escolha direta na barra de etapas."""
    target = texts.STEPS.index(st.session_state["nav_step"]) + 1
    go_to_step(ref, target)


def phase(ref: Reference) -> str:
    """Deriva o estado da carga sem guardar uma segunda fonte de verdade."""
    if not st.session_state["files"]:
        return "VAZIA"
    if any(
        source.state == FileState.AGUARDANDO_CONFIRMACAO
        for source in st.session_state["files"].values()
    ):
        return "AGUARDANDO_CONFIRMACAO"
    if download_allowed(ref):
        return "PRONTA"
    return "EM_CORRECAO"
