"""Verifica a inicialização real do servidor Streamlit."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_streamlit_health() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless=true",
            "--server.address=127.0.0.1",
            f"--server.port={port}",
        ],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f"Streamlit encerrou com código {process.returncode}")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1) as connection:
                    connection.sendall(b"GET /_stcore/health HTTP/1.0\r\nHost: localhost\r\n\r\n")
                    response = connection.recv(1024)
                    if b"200 OK" in response and response.endswith(b"ok"):
                        return
            except OSError:
                time.sleep(0.2)
        pytest.fail("Streamlit não respondeu ao healthcheck em 30 segundos")
    finally:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
