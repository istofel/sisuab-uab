"""Modelos em memória do processamento SisUAB."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.llm.schemas import ExtractedRecord


class FileFormat(StrEnum):
    PDF = "PDF"
    CSV = "CSV"
    XLSX = "XLSX"
    XLS = "XLS"
    DOCX = "DOCX"
    JSON = "JSON"
    TXT = "TXT"


class ReadMethod(StrEnum):
    TABULAR = "Tabular"
    TABELA_DOC = "Tabela de documento"
    IA = "IA"


class Severity(StrEnum):
    ERRO = "ERRO"
    AVISO = "AVISO"


class NoticeLevel(StrEnum):
    RECUSADO = "RECUSADO"
    AVISO = "AVISO"


class FileState(StrEnum):
    LIDO = "LIDO"
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    CONFIRMADO = "CONFIRMADO"
    COM_FALHA = "COM_FALHA"


class MappingStrategy(StrEnum):
    CABECALHO = "CABECALHO"
    POSICIONAL = "POSICIONAL"
    CONTEUDO = "CONTEUDO"
    IA = "IA"
    MANUAL = "MANUAL"


class PatchOrigin(StrEnum):
    EDICAO = "EDICAO"
    SUGESTAO = "SUGESTAO"
    CHAT = "CHAT"
    LOTE = "LOTE"
    EXCLUSAO = "EXCLUSAO"
    RESTAURACAO = "RESTAURACAO"


MapTarget = str


@dataclass(slots=True)
class RawTable:
    sheet: str | None
    header: list[str] | None
    rows: list[list[str]]
    row_numbers: list[int]
    method: ReadMethod
    empty_lines: int = 0


@dataclass(slots=True)
class TextBlock:
    locator: str
    text: str
    has_student_hint: bool


@dataclass(slots=True)
class DiscardedLine:
    locator: str
    values: list[str]


@dataclass(slots=True)
class FileNotice:
    level: NoticeLevel
    code: str
    message: str


@dataclass(slots=True)
class MappingProposal:
    mapping: dict[int, MapTarget]
    strategy: MappingStrategy
    ambiguous_fields: set[str]
    needs_confirmation: bool


@dataclass(slots=True)
class SourceFile:
    id: str
    name: str
    fmt: FileFormat
    size: int
    encoding: str | None = None
    encoding_uncertain: bool = False
    delimiter: str | None = None
    has_header: bool | None = None
    tables: list[RawTable] = field(default_factory=list)
    selected_tables: set[int] = field(default_factory=set)
    text_blocks: list[TextBlock] = field(default_factory=list)
    mappings: dict[int, MappingProposal] = field(default_factory=dict)
    polo_default: str | None = None
    discarded: list[DiscardedLine] = field(default_factory=list)
    empty_lines: int = 0
    notices: list[FileNotice] = field(default_factory=list)
    ai_records: list["ExtractedRecord"] = field(default_factory=list)
    ai_record_locators: list[str] = field(default_factory=list)
    ai_source_cpfs: frozenset[str] = frozenset()
    ai_blocks_done: set[int] = field(default_factory=set)
    state: FileState = FileState.LIDO


@dataclass(slots=True)
class Record:
    id: int
    source_id: str
    source_name: str
    locator: str
    order_key: tuple[int, int]
    method: ReadMethod
    name_ref: str
    original: dict[str, str]
    input: dict[str, str]
    deleted: bool = False


@dataclass(frozen=True, slots=True)
class Normalized:
    values: dict[str, str]
    cpf_scientific: bool
    ddd_from_phone: str | None
    ddd_conflict: bool
    phone_prefixed: bool


@dataclass(frozen=True, slots=True)
class Issue:
    record_id: int
    field: str
    severity: Severity
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class Suggestion:
    record_id: int
    field: str
    current: str
    proposed: str
    code: str

    @property
    def key(self) -> tuple[int, str, str, str]:
        """Identifica a sugestão para aceitar ou recusar."""
        return self.record_id, self.field, self.current, self.proposed


@dataclass(slots=True)
class Counts:
    total: int
    with_error: int
    only_warning: int
    ok: int
    discarded: int


@dataclass(slots=True)
class ValidationResult:
    effective: dict[int, dict[str, str]]
    issues: list[Issue]
    by_record: dict[int, list[Issue]]
    suggestions: list[Suggestion]
    counts: Counts


@dataclass(slots=True)
class Patch:
    seq: int
    group: int
    record_id: int
    field: str | None
    old: str | None
    new: str | None
    origin: PatchOrigin


@dataclass(slots=True)
class VerifyFailure:
    line: int | None
    check: str
    message: str


@dataclass(slots=True)
class VerifyReport:
    ok: bool
    failures: list[VerifyFailure]
    line_count: int
