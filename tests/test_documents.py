"""Extração determinística de tabelas e blocos de texto."""

from core.ingest import read_file
from core.ingest.documents import read_docx, read_pdf, split_text_blocks
from core.models import FileState, ReadMethod
from tests.factories import make_docx, make_pdf


def test_pdf_table_is_read_without_repeating_it_in_free_text() -> None:
    data = make_pdf(
        [["CPF", "Email"], ["01234567890", "aluno@exemplo.com.br"]],
        "Outro aluno: CPF 987.654.321-00",
    )
    tables, blocks = read_pdf(data)
    assert len(tables) == 1
    assert tables[0].method == ReadMethod.TABELA_DOC
    assert tables[0].rows[0][0] == "01234567890"
    assert any("987.654.321-00" in block.text for block in blocks)
    assert all("01234567890" not in block.text for block in blocks)


def test_docx_table_and_paragraphs() -> None:
    data = make_docx(
        [["CPF", "Email"], ["01234567890", "aluno@exemplo.com.br"]],
        ["Outro aluno: CPF 987.654.321-00"],
    )
    tables, blocks = read_docx(data)
    assert tables[0].rows[0][0] == "01234567890"
    assert blocks[0].has_student_hint
    assert "01234567890" not in blocks[0].text


def test_scanned_pdf_is_reported_as_no_text() -> None:
    source = read_file("scanned.pdf", make_pdf([]))
    assert source.state != FileState.COM_FALHA
    assert source.notices[0].code == "ARQ_SEM_TEXTO"


def test_non_delimited_txt_becomes_blocks() -> None:
    source = read_file("alunos.txt", b"Aluno CPF 012.345.678-90\nOutro texto\n")
    assert source.tables == []
    assert source.text_blocks[0].has_student_hint
    assert split_text_blocks("", "linhas") == []
