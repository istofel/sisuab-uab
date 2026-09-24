"""Detecção e leitura inicial de arquivos em memória."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

from core.constants import MAX_FILE_MB, SUPPORTED_EXTENSIONS
from core.errors import FileReadError
from core.ingest.documents import read_docx, read_pdf, split_text_blocks
from core.ingest.encoding import decode_text, detect_delimiter
from core.ingest.tabular import read_delimited, read_excel, read_json
from core.messages import file_msg
from core.models import FileFormat, FileNotice, FileState, SourceFile


def detect_format(name: str, data: bytes) -> tuple[FileFormat | None, bool]:
    """Identifica o formato pelo conteúdo e compara com a extensão."""
    extension = Path(name).suffix.lower()
    expected = FileFormat(extension[1:].upper()) if extension in SUPPORTED_EXTENSIONS else None
    detected: FileFormat | None = None
    if data.startswith(b"%PDF"):
        detected = FileFormat.PDF
    elif data.startswith(b"\xd0\xcf\x11\xe0"):
        detected = FileFormat.XLS
    elif zipfile.is_zipfile(io.BytesIO(data)):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
            if any(name.startswith("xl/") for name in names):
                detected = FileFormat.XLSX
            elif any(name.startswith("word/") for name in names):
                detected = FileFormat.DOCX
        except (OSError, zipfile.BadZipFile):
            detected = None
    else:
        try:
            text, _, _ = decode_text(data)
            json.loads(text)
            detected = FileFormat.JSON
        except (UnicodeError, ValueError):
            detected = expected if expected in {FileFormat.CSV, FileFormat.TXT} else None
    return detected, detected is not None and expected is not None and detected != expected


def read_file(name: str, data: bytes) -> SourceFile:
    """Lê um upload e guarda falhas de leitura como aviso no próprio arquivo."""
    file_id = hashlib.sha256(data).hexdigest()
    source = SourceFile(file_id, name, FileFormat.TXT, len(data))

    def reject(code: str) -> SourceFile:
        level, message = file_msg(code, nome=name)
        source.notices.append(FileNotice(level, code, message))
        source.state = FileState.COM_FALHA
        return source

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        return reject("ARQ_MUITO_GRANDE")
    fmt, divergent = detect_format(name, data)
    if fmt is None:
        return reject("ARQ_FORMATO_NAO_SUPORTADO")
    source.fmt = fmt
    if divergent:
        level, message = file_msg(
            "ARQ_EXTENSAO_DIVERGENTE",
            nome=name,
            ext=Path(name).suffix.lower(),
            fmt=fmt.value,
        )
        source.notices.append(FileNotice(level, "ARQ_EXTENSAO_DIVERGENTE", message))
    try:
        if fmt in {FileFormat.XLS, FileFormat.XLSX}:
            source.tables = read_excel(data, fmt)
        elif fmt == FileFormat.JSON:
            source.tables = [read_json(data)]
        elif fmt in {FileFormat.CSV, FileFormat.TXT}:
            text, source.encoding, source.encoding_uncertain = decode_text(data)
            delimiter, _ = detect_delimiter(text)
            source.delimiter = delimiter
            if delimiter or fmt == FileFormat.CSV:
                source.tables = [read_delimited(text, delimiter or ";")]
            else:
                source.text_blocks = split_text_blocks(text, "linhas")
        elif fmt == FileFormat.PDF:
            source.tables, source.text_blocks = read_pdf(data)
        elif fmt == FileFormat.DOCX:
            source.tables, source.text_blocks = read_docx(data)
        else:
            raise FileReadError("ARQ_ILEGIVEL")
    except (FileReadError, UnicodeError, ValueError) as exc:
        return reject(exc.code if isinstance(exc, FileReadError) else "ARQ_ILEGIVEL")

    source.empty_lines = sum(table.empty_lines for table in source.tables)
    source.selected_tables = set(range(len(source.tables)))
    source.has_header = source.tables[0].header is not None if source.tables else None
    if not source.tables and not source.text_blocks:
        code = "ARQ_SEM_TEXTO" if fmt == FileFormat.PDF else "ARQ_VAZIO"
        level, message = file_msg(code, nome=name)
        source.notices.append(FileNotice(level, code, message))
    return source
