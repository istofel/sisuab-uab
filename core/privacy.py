"""Mascaramento de dados pessoais nos logs locais."""

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.constants import LOG_BACKUP_COUNT, LOG_FILE_NAME, LOG_MAX_BYTES
from core.text_utils import CPF_LIKE_RE, PHONE_LIKE_RE, ascii_digits

EMAIL_RE = re.compile(r"[^\s@;,]+@[^\s@;,]+")
LONG_DIGITS_RE = re.compile(r"(?<![0-9])[0-9]{8,14}(?![0-9])")


def mask_cpf(value: str) -> str:
    """Mostra apenas os dois últimos dígitos do CPF."""
    digits = ascii_digits(value)
    return "*" * max(0, len(digits) - 2) + digits[-2:]


def mask_email(value: str) -> str:
    """Mostra apenas a primeira letra do endereço."""
    local = value.split("@", 1)[0]
    return (local[:1] or "*") + "***@***"


def mask_phone(value: str) -> str:
    """Mostra apenas os quatro últimos dígitos do telefone."""
    digits = ascii_digits(value)
    return "*" * max(0, len(digits) - 4) + digits[-4:]


def mask_text(text: str) -> str:
    """Remove dados pessoais em quatro passagens antes de escrever no log."""
    result = EMAIL_RE.sub(lambda match: mask_email(match.group()), text)
    result = CPF_LIKE_RE.sub(lambda match: mask_cpf(match.group()), result)
    result = PHONE_LIKE_RE.sub(lambda match: mask_phone(match.group()), result)
    return LONG_DIGITS_RE.sub(lambda match: mask_phone(match.group()), result)


class MaskingFormatter(logging.Formatter):
    """Mascara mensagens, argumentos e traceback formatados."""

    def format(self, record: logging.LogRecord) -> str:
        """Formata e mascara a linha completa."""
        return mask_text(super().format(record))


def setup_logging(log_dir: str, level: str) -> None:
    """Configura handlers rotativos e stdout uma única vez."""
    logger = logging.getLogger("importador")
    logger.setLevel(level)
    if any(getattr(handler, "_importador_handler", False) for handler in logger.handlers):
        return
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    formatter = MaskingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handlers: list[logging.Handler] = [
        RotatingFileHandler(
            Path(log_dir) / LOG_FILE_NAME,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)
        handler._importador_handler = True
        logger.addHandler(handler)
