"""Máscaras de CPF, e-mail e telefone nos logs."""

import logging
import socket
from pathlib import Path

import pytest

from core.privacy import mask_cpf, mask_email, mask_phone, mask_text, setup_logging


def test_masks_remove_complete_personal_data() -> None:
    assert mask_cpf("012.345.678-90") == "*********90"
    assert mask_email("marcia@exemplo.com.br") == "m***@***"
    assert mask_phone("(63) 98765-4321") == "*******4321"
    text = "CPF 012.345.678-90, email marcia@exemplo.com.br, fone (63) 98765-4321"
    masked = mask_text(text)
    assert "012.345.678-90" not in masked
    assert "marcia@exemplo.com.br" not in masked
    assert "98765-4321" not in masked


def test_logs_are_masked_and_setup_is_idempotent(tmp_path: Path, isolated_logger) -> None:
    setup_logging(str(tmp_path), "INFO")
    setup_logging(str(tmp_path), "INFO")
    logger = logging.getLogger("importador")
    assert len(logger.handlers) == 2
    logger.info("CPF %s, email %s, telefone %s", "01234567890", "aluno@exemplo.com.br", "987654321")
    for handler in logger.handlers:
        handler.flush()
    content = (tmp_path / "app.log").read_text(encoding="utf-8")
    for secret in ("01234567890", "aluno@exemplo.com.br", "987654321"):
        assert secret not in content


def test_network_guard_rejects_public_address() -> None:
    with socket.socket() as connection, pytest.raises(RuntimeError, match="rede externa"):
        connection.connect(("1.1.1.1", 53))
