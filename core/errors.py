"""Exceções de domínio usadas pelo núcleo e pela interface."""


class ImportadorError(Exception):
    """Base de todos os erros do domínio."""


class ConfigError(ImportadorError):
    """Configuração ou lista de referência inválida."""

    def __init__(self, key: str, detail: str = "") -> None:
        self.key = key
        self.detail = detail
        super().__init__(f"{key}: {detail}" if detail else key)


class FileReadError(ImportadorError):
    """Arquivo de entrada não pôde ser lido."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(detail or code)


class LLMUnavailableError(ImportadorError):
    """Ollama indisponível, sem modelo ou fora do prazo."""


class LLMResponseError(ImportadorError):
    """Resposta da IA inválida após as tentativas permitidas."""


class ExportError(ImportadorError):
    """Falha ao gerar ou conferir um CSV já validado."""
