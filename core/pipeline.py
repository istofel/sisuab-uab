"""Construção dos registros e ordenação da carga em memória."""

import hashlib

from core.constants import FIELDS, MAX_RECORDS_PER_SESSION
from core.ingest import read_file
from core.ingest.discard import split_rows
from core.mapping import propose_mapping, rows_to_inputs
from core.messages import file_msg
from core.models import (
    FileFormat,
    FileNotice,
    FileState,
    ReadMethod,
    Record,
    SourceFile,
    ValidationResult,
)
from core.patches import PatchLog
from core.reference import Reference


def ingest_upload(
    state_files: dict[str, SourceFile],
    name: str,
    data: bytes,
    current_records: int,
    ref: Reference,
) -> SourceFile:
    """Lê o arquivo, propõe mapeamentos e define se ele exige confirmação."""
    file_id = hashlib.sha256(data).hexdigest()
    if file_id in state_files:
        source = SourceFile(file_id, name, FileFormat.TXT, len(data), state=FileState.COM_FALHA)
        level, message = file_msg("ARQ_REPETIDO", nome=name)
        source.notices.append(FileNotice(level, "ARQ_REPETIDO", message))
        return source

    source = read_file(name, data)
    if source.state == FileState.COM_FALHA:
        return source
    record_count = sum(len(split_rows(table)[0]) for table in source.tables)
    record_count += len(source.ai_records)
    if current_records + record_count > MAX_RECORDS_PER_SESSION:
        level, message = file_msg("ARQ_LIMITE_REGISTROS", nome=name)
        source.notices.append(FileNotice(level, "ARQ_LIMITE_REGISTROS", message))
        source.state = FileState.COM_FALHA
        return source

    pending = source.encoding_uncertain or bool(source.ai_records)
    pending = pending or any(block.has_student_hint for block in source.text_blocks)
    for index, table in enumerate(source.tables):
        source.mappings[index] = propose_mapping(table, ref)
        source.discarded.extend(split_rows(table)[1])
        proposal = source.mappings[index]
        if proposal.needs_confirmation:
            pending = True
        if "polo" not in proposal.mapping.values() and source.polo_default is None:
            pending = True
    source.state = FileState.AGUARDANDO_CONFIRMACAO if pending else FileState.CONFIRMADO
    state_files[file_id] = source
    return source


def build_records(sf: SourceFile, file_pos: int, next_id: int) -> list[Record]:
    """Cria registros de tabelas e extrações já confirmadas."""
    if sf.state != FileState.CONFIRMADO:
        raise ValueError("arquivo ainda não confirmado")
    records: list[Record] = []
    position = 0
    for table_index in sorted(sf.selected_tables):
        table = sf.tables[table_index]
        proposal = sf.mappings[table_index]
        for number, values, name in rows_to_inputs(table, proposal.mapping, sf.polo_default):
            position += 1
            prefix = f"{table.sheet}, " if table.sheet else ""
            records.append(
                Record(
                    next_id,
                    sf.id,
                    sf.name,
                    f"{prefix}linha {number}",
                    (file_pos, position),
                    table.method,
                    name,
                    values.copy(),
                    values.copy(),
                )
            )
            next_id += 1

    for block_index, extracted in enumerate(sf.ai_records, start=1):
        position += 1
        values = {field: getattr(extracted, field) for field in FIELDS}
        locator = (
            sf.ai_record_locators[block_index - 1]
            if block_index <= len(sf.ai_record_locators)
            else f"trecho {block_index} (IA)"
        )
        records.append(
            Record(
                next_id,
                sf.id,
                sf.name,
                locator,
                (file_pos, position),
                ReadMethod.IA,
                extracted.nome,
                values.copy(),
                values.copy(),
            )
        )
        next_id += 1
    return records


def rebuild_file(
    sf: SourceFile, records: list[Record], patchlog: PatchLog, file_pos: int, next_id: int
) -> list[Record]:
    """Recria somente os registros do arquivo e descarta suas correções anteriores."""
    removed_ids = {record.id for record in records if record.source_id == sf.id}
    patchlog.drop_records(removed_ids)
    kept = [record for record in records if record.source_id != sf.id]
    return kept + build_records(sf, file_pos, next_id)


def effective_rows(records: list[Record], result: ValidationResult) -> list[tuple[str, ...]]:
    """Ordena e projeta os sete valores finais para exportação."""
    return [
        tuple(result.effective[record.id][field] for field in FIELDS)
        for record in sorted(records, key=lambda item: item.order_key)
        if not record.deleted and record.id in result.effective
    ]
