"""Constantes do leiaute e limites do Importador SisUAB."""

APP_NAME = "Importador SisUAB com IA"

FIELDS: tuple[str, ...] = ("polo", "cpf", "situacao", "email", "ddd", "telefone", "publico_alvo")
FIELD_LABELS = {
    "polo": "Polo",
    "cpf": "CPF",
    "situacao": "Situação",
    "email": "E-mail",
    "ddd": "DDD",
    "telefone": "Telefone",
    "publico_alvo": "Público-alvo",
}
SITUACOES = frozenset({"CUR", "CAN", "TRC", "DES", "FDO", "FAL", "TRA", "DTT", "TCC"})
SITUACAO_PADRAO = "CUR"
PUBLICOS = frozenset({"DS", "PR"})
PUBLICO_PADRAO = "DS"
POLO_MAX_LEN = 80
EMAIL_MAX_LEN = 60
CPF_LEN = 11
DDD_LEN = 2
TELEFONE_LEN = 9
EMAIL_FORBIDDEN_CHARS = ("'", '"', ";")

CSV_SEPARATOR = ";"
CSV_FIELD_COUNT = 7
CSV_FORBIDDEN_CHARS = ('"', "'")
CSV_FORBIDDEN_LINE_START = ("#", ";")
UTF8_BOM = b"\xef\xbb\xbf"
LINE_ENDINGS = {"LF": "\n", "CRLF": "\r\n"}
OUTPUT_FILENAME_PATTERN = "sisuab_%Y%m%d_%H%M.csv"

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".csv", ".xlsx", ".xls", ".docx", ".json", ".txt"})
INPUT_ENCODINGS = ("utf-8", "cp1252", "latin-1")
DELIMITER_CANDIDATES = ";,\t|"
MAX_FILE_MB = 50
MAX_ROWS_PER_FILE = 20_000
MAX_RECORDS_PER_SESSION = 5_000
SNIFF_SAMPLE_CHARS = 20_000

CONTEXT_CAN_MAX_PERIOD = 2
CONTEXT_DES_TRC_TRA_MIN_PERIOD = 3

POLO_FUZZY_CUTOFF = 0.85
TEL_MOBILE_FIRST_DIGITS = "6789"
TEL_LANDLINE_FIRST_DIGITS = "2345"

LLM_PROVIDER_NAME = "Ollama"
LLM_TEMPERATURE = 0
LLM_SEED = 42
LLM_NUM_CTX = 8192
LLM_CONNECT_TIMEOUT_S = 3
LLM_STATUS_TIMEOUT_S = 3
LLM_KEEP_ALIVE = "10m"
LLM_MAX_BLOCK_CHARS = 6_000
LLM_INVALID_RESPONSE_RETRIES = 1
LLM_MAPPING_SAMPLE_ROWS = 5
CHAT_MAX_RECORDS_IN_CONTEXT = 150
CHAT_HISTORY_TURNS = 6
CHAT_MAX_VALUE_LEN = 200
ALLOWED_OLLAMA_HOSTS = frozenset(
    {"localhost", "127.0.0.1", "::1", "host.docker.internal", "ollama"}
)

LOG_FILE_NAME = "app.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3

POLOS_FILE = "config/polos.txt"
DDDS_FILE = "config/ddds.txt"

HEADER_SYNONYMS: dict[str, tuple[str, ...]] = {
    "polo": ("polo", "nomedopolo", "polodeapoio", "polouab", "polodeapoiopresencial"),
    "cpf": ("cpf", "ncpf", "nodocpf", "nrcpf", "numerodocpf", "cpfdoaluno", "cpfaluno"),
    "situacao": ("situacao", "status", "situacaodoaluno", "codigodasituacao", "codsituacao"),
    "email": ("email", "emaildoaluno", "correioeletronico", "enderecodeemail"),
    "ddd": ("ddd", "codigoddd"),
    "telefone": ("telefone", "celular", "fone", "tel", "whatsapp", "telefonecelular", "contato"),
    "publico_alvo": (
        "publicoalvo",
        "publico",
        "tipodevaga",
        "ocupacaodavaga",
        "codigodeocupacaodavaga",
    ),
    "nome": ("nome", "nomedoaluno", "aluno", "nomecompleto", "discente"),
}
