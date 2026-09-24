"""Invariantes de importação e privacidade do projeto."""

import ast
import tomllib
from pathlib import Path


def test_core_has_no_streamlit_or_unapproved_requests_import() -> None:
    for path in Path("core").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [
            node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        modules = [alias.name for node in imports for alias in node.names] + [
            node.module or "" for node in imports if isinstance(node, ast.ImportFrom)
        ]
        assert not any(
            module == "streamlit" or module.startswith("streamlit.") for module in modules
        )
        if path.as_posix() != "core/llm/client.py":
            assert not any(
                module == "requests" or module.startswith("requests.") for module in modules
            )
        assert "tempfile" not in modules


def test_streamlit_privacy_configuration() -> None:
    with Path(".streamlit/config.toml").open("rb") as source:
        config = tomllib.load(source)
    assert config["browser"]["gatherUsageStats"] is False
    assert config["server"]["address"] == "127.0.0.1"
    assert config["client"]["showErrorLinks"] is False
    assert config["client"]["showErrorDetails"] == "none"
