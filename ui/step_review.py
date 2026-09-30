"""Etapa 2: mapeamento, polo por arquivo e extração confirmada."""

import streamlit as st

from core.llm.client import OllamaClient
from core.llm.extract import extract_blocks
from core.mapping import validate_mapping
from core.models import FileState, SourceFile
from core.pipeline import build_records, rebuild_file
from core.reference import Reference
from ui import state, texts


def _apply_review(
    source: SourceFile,
    ref: Reference,
    selected: set[int],
    mappings: dict[int, dict[int, str]],
    polo_default: str | None,
) -> None:
    old_ids = {record.id for record in st.session_state["records"] if record.source_id == source.id}
    source.selected_tables = selected
    source.polo_default = polo_default
    for index, mapping in mappings.items():
        source.mappings[index].mapping = mapping
        source.mappings[index].needs_confirmation = False
    source.encoding_uncertain = False
    source.state = FileState.CONFIRMADO
    file_pos = st.session_state["file_order"].index(source.id) + 1
    if old_ids:
        st.session_state["records"] = rebuild_file(
            source,
            st.session_state["records"],
            st.session_state["patchlog"],
            file_pos,
            st.session_state["next_record_id"],
        )
        new_count = sum(
            record.id >= st.session_state["next_record_id"]
            for record in st.session_state["records"]
        )
    else:
        records = build_records(source, file_pos, st.session_state["next_record_id"])
        st.session_state["records"].extend(records)
        new_count = len(records)
    st.session_state["next_record_id"] += new_count
    state.bump_revision(ref)
    st.rerun()


@st.dialog(texts.REVIEW_REBUILD_TITLE)
def _confirm_rebuild(
    source: SourceFile,
    ref: Reference,
    selected: set[int],
    mappings: dict[int, dict[int, str]],
    polo_default: str | None,
) -> None:
    st.warning(texts.REVIEW_REBUILD_WARNING)
    if st.button(texts.REVIEW_REBUILD_CONFIRM, type="primary"):
        _apply_review(source, ref, selected, mappings, polo_default)
    if st.button(texts.CLEAR_CANCEL):
        st.rerun()


def _review_file(source: SourceFile, ref: Reference, client: OllamaClient) -> None:
    st.caption(texts.REVIEW_STATE.format(state=source.state.value))
    st.caption(
        texts.REVIEW_ENCODING.format(
            encoding=source.encoding or "—", delimiter=source.delimiter or "—"
        )
    )
    st.caption(
        texts.REVIEW_DISCARDED.format(
            count=len(source.discarded),
            empty=source.empty_lines,
        )
    )
    for notice in source.notices:
        st.warning(notice.message)

    hinted = [block for block in source.text_blocks if block.has_student_hint]
    if hinted:
        pending = len(hinted) - len(source.ai_blocks_done)
        if pending:
            st.warning(texts.REVIEW_AI_PENDING)
        online = st.session_state["llm_status"].online
        if not online:
            st.caption(texts.REVIEW_AI_OFFLINE)
        if st.button(texts.REVIEW_AI_BUTTON, key=f"ai_{source.id}", disabled=not online):
            progress = st.progress(0.0)
            extract_blocks(
                client,
                st.session_state["model"],
                source,
                lambda done, total: progress.progress(done / total),
            )
            source.state = FileState.AGUARDANDO_CONFIRMACAO
            state.bump_revision(ref)
            st.rerun()
        if source.ai_records:
            st.info(texts.REVIEW_AI_FOUND.format(count=len(source.ai_records)))

    with st.form(f"review_{source.id}"):
        selected: set[int] = set()
        mappings: dict[int, dict[int, str]] = {}
        for index, table in enumerate(source.tables):
            st.subheader(
                texts.REVIEW_TABLE.format(
                    sheet=table.sheet or "CSV/TXT",
                    rows=len(table.rows),
                )
            )
            included = st.checkbox(
                texts.REVIEW_SELECT_TABLE,
                value=index in source.selected_tables,
                key=f"table_{source.id}_{index}",
            )
            if included:
                selected.add(index)
            width = max(
                len(table.header or []),
                max((len(row) for row in table.rows), default=0),
            )
            if table.rows:
                st.caption(texts.REVIEW_PREVIEW)
                preview_columns = [
                    texts.REVIEW_MAPPING.format(
                        index=column + 1,
                        name=table.header[column] if table.header else str(column + 1),
                    )
                    for column in range(width)
                ]
                st.dataframe(
                    [
                        dict(zip(preview_columns, row, strict=False))
                        for row in table.rows[:5]
                    ],
                    hide_index=True,
                )
            proposal = source.mappings[index]
            mapping: dict[int, str] = {}
            for column in range(width):
                name = table.header[column] if table.header else str(column + 1)
                options = list(texts.FIELD_OPTIONS)
                current = proposal.mapping.get(column, "ignorar")
                mapping[column] = st.selectbox(
                    texts.REVIEW_MAPPING.format(index=column + 1, name=name),
                    options,
                    index=options.index(current),
                    format_func=lambda value: texts.FIELD_OPTIONS[value],
                    key=f"map_{source.id}_{index}_{column}",
                )
            mappings[index] = mapping

        polo_options = ["", *ref.polos]
        polo_default = (
            st.selectbox(
                texts.REVIEW_POLO_DEFAULT,
                polo_options,
                index=polo_options.index(source.polo_default or ""),
                key=f"polo_{source.id}",
            )
            or None
        )
        confirm = st.form_submit_button(texts.REVIEW_CONFIRM)

    if confirm:
        conflicts = [field for index in selected for field in validate_mapping(mappings[index])]
        if conflicts:
            st.error(texts.REVIEW_CONFLICT.format(fields=", ".join(conflicts)))
            return
        if any("polo" not in mappings[index].values() for index in selected) and not polo_default:
            st.error(texts.REVIEW_MISSING_POLO)
            return
        if hinted and len(source.ai_blocks_done) < len(hinted):
            st.error(texts.REVIEW_AI_PENDING)
            return
        old_records = any(record.source_id == source.id for record in st.session_state["records"])
        changed = (
            selected != source.selected_tables
            or polo_default != source.polo_default
            or any(mappings[index] != source.mappings[index].mapping for index in mappings)
        )
        if old_records and changed:
            _confirm_rebuild(source, ref, selected, mappings, polo_default)
        elif source.state != FileState.CONFIRMADO or changed:
            _apply_review(source, ref, selected, mappings, polo_default)


def render(ref: Reference, client: OllamaClient) -> None:
    """Apresenta detecções e exige confirmação das ambiguidades."""
    st.header(texts.REVIEW_TITLE)
    if not st.session_state["file_order"]:
        st.info(texts.REVIEW_EMPTY)
        st.button(texts.REVIEW_CONTINUE, disabled=True)
        return
    for file_id in st.session_state["file_order"]:
        source = st.session_state["files"][file_id]
        label = texts.REVIEW_FILE.format(
            name=source.name,
            format=source.fmt.value,
            rows=sum(len(table.rows) for table in source.tables),
        )
        with st.expander(label, expanded=source.state == FileState.AGUARDANDO_CONFIRMACAO):
            _review_file(source, ref, client)
    if any(source.state != FileState.CONFIRMADO for source in st.session_state["files"].values()):
        st.warning(texts.REVIEW_BLOCKED)
    elif not state.can_enter_step(ref, 3):
        st.warning(texts.REVIEW_NO_RECORDS)
    st.button(
        texts.REVIEW_CONTINUE,
        disabled=not state.can_enter_step(ref, 3),
        on_click=state.go_to_step,
        args=(ref, 3),
    )
