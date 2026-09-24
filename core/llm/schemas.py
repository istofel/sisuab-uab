"""Schemas estritos de saída da IA local."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ExtractedRecord(BaseModel):
    """Um registro encontrado em texto livre."""

    model_config = ConfigDict(extra="forbid")

    nome: str
    polo: str
    cpf: str
    situacao: str
    email: str
    ddd: str
    telefone: str
    publico_alvo: str


class ExtractionOut(BaseModel):
    """Lote extraído de um bloco de texto."""

    model_config = ConfigDict(extra="forbid")
    registros: list[ExtractedRecord]


class ColumnMap(BaseModel):
    """Uma coluna associada a campo ou ignorada."""

    model_config = ConfigDict(extra="forbid")
    indice: int
    campo: Literal[
        "polo", "cpf", "situacao", "email", "ddd", "telefone", "publico_alvo", "nome", "ignorar"
    ]


class MappingOut(BaseModel):
    """Proposta de mapeamento da IA."""

    model_config = ConfigDict(extra="forbid")
    colunas: list[ColumnMap]


class ProposedChange(BaseModel):
    """Mudança proposta pelo chat, nunca aplicada sem confirmação."""

    model_config = ConfigDict(extra="forbid")
    registro: int
    campo: Literal["polo", "cpf", "situacao", "email", "ddd", "telefone", "publico_alvo"]
    valor_novo: str


class ChatOut(BaseModel):
    """Resposta e propostas de alteração do chat."""

    model_config = ConfigDict(extra="forbid")
    resposta: str
    alteracoes: list[ProposedChange]
