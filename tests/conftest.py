"""Fixtures compartilhadas e bloqueio de rede externa nos testes."""

import socket
from collections.abc import Iterator
from pathlib import Path

import pytest

from core.reference import Reference, load_reference


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Permite conexões somente ao próprio computador."""
    original_connect = socket.socket.connect

    def local_connect(sock: socket.socket, address: tuple) -> None:
        host = address[0]
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise RuntimeError("rede externa bloqueada em teste")
        original_connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", local_connect)


@pytest.fixture(scope="session")
def ref() -> Reference:
    """Carrega as listas reais editáveis usadas pelo MVP."""
    return load_reference(Path("config/polos.txt"), Path("config/ddds.txt"))


@pytest.fixture
def isolated_logger() -> Iterator[None]:
    """Evita que o logger configurado em um teste afete os demais."""
    import logging

    logger = logging.getLogger("importador")
    old_handlers = logger.handlers[:]
    logger.handlers.clear()
    yield
    for handler in logger.handlers:
        handler.close()
    logger.handlers[:] = old_handlers
