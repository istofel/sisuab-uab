"""Etapa 4: exportação em bytes, verificação e download autorizado."""

from datetime import datetime

import streamlit as st

from core.errors import ExportError
from core.export import export_csv, output_filename
from core.pipeline import effective_rows
from core.reference import Reference
from core.settings import Settings
from core.verify import verify_csv
from ui import state, texts


def _verify_current(ref: Reference, settings: Settings) -> None:
    """Gera e relê os bytes da revisão atual antes de liberar o download."""
    result = state.get_result(ref)
    if result.counts.with_error:
        return
    try:
        rows = effective_rows(st.session_state["records"], result)
        data = export_csv(rows, settings.line_ending)
    except ExportError:
        st.session_state["csv_bytes"] = None
        st.session_state["verify_report"] = None
        st.session_state["verified_revision"] = None
        st.session_state["export_error"] = True
        return
    report = verify_csv(data, ref, settings.line_ending)
    st.session_state["csv_bytes"] = data if report.ok else None
    st.session_state["verify_report"] = report
    st.session_state["export_error"] = False
    st.session_state["verified_revision"] = st.session_state["revision"] if report.ok else None


def render(ref: Reference, settings: Settings) -> None:
    """Exibe o conteúdo bruto e habilita download só após conferência válida."""
    st.header(texts.DOWNLOAD_TITLE)
    result = state.get_result(ref)
    if result.counts.total == 0:
        st.info(texts.DOWNLOAD_EMPTY)
        return
    if result.counts.with_error:
        st.error(texts.DOWNLOAD_BLOCKED.format(errors=result.counts.with_error))
    else:
        if result.counts.only_warning:
            st.warning(texts.DOWNLOAD_WARNINGS.format(count=result.counts.only_warning))
        if st.button(texts.DOWNLOAD_VERIFY):
            _verify_current(ref, settings)

    report = st.session_state["verify_report"]
    if st.session_state["export_error"]:
        st.error(texts.DOWNLOAD_FAILURE)
    elif report is not None and not report.ok:
        st.error(texts.DOWNLOAD_FAILURE)
        for failure in report.failures:
            st.caption(texts.DOWNLOAD_FAILURE_REASON.format(reason=failure.message))
    elif state.download_allowed(ref):
        st.success(texts.DOWNLOAD_VERIFIED)
    elif not result.counts.with_error:
        st.caption(texts.DOWNLOAD_STALE)

    data = st.session_state["csv_bytes"]
    if data is not None and state.download_allowed(ref):
        lines = data.decode("utf-8").splitlines(keepends=True)
        st.subheader(texts.DOWNLOAD_PREVIEW)
        st.code("".join(lines[:1000]), language=None)
        st.caption(
            texts.DOWNLOAD_PREVIEW_COUNT.format(
                shown=min(len(lines), 1000),
                total=len(lines),
            )
        )
    st.download_button(
        texts.DOWNLOAD_BUTTON,
        data=data or b"",
        file_name=output_filename(datetime.now()),
        mime="text/csv",
        disabled=not state.download_allowed(ref),
        on_click="ignore",
    )
