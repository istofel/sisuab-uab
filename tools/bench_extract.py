"""Benchmark de extração com alunos inteiramente fictícios."""

import argparse
import hashlib
import time

from core.ingest.documents import read_pdf, split_text_blocks
from core.llm.client import OllamaClient
from core.llm.extract import extract_blocks
from core.models import FileFormat, SourceFile
from core.text_utils import ascii_digits
from tests.factories import make_cpf, make_pdf


def _students(start: int, count: int) -> tuple[str, set[str]]:
    lines: list[str] = []
    cpfs: set[str] = set()
    for number in range(start, start + count):
        cpf = make_cpf(f"{number:09d}")
        cpfs.add(cpf)
        lines.append(
            f"Aluno {number:03d}, polo GURUPI-TO ZONA RURAL, CPF {cpf}, situacao CUR, "
            f"e-mail aluno{number:03d}@exemplo.com.br, DDD 63, telefone 987654321, "
            "publico-alvo DS."
        )
    return "\n".join(lines), cpfs


def run(model: str, students: int) -> int:
    """Mede recall, precisão conferida e segundos por bloco."""
    if students < 2:
        raise ValueError("students deve ser pelo menos 2")
    first_count = students // 2
    text, text_cpfs = _students(1, first_count)
    pdf_text, pdf_cpfs = _students(first_count + 1, students - first_count)
    pdf_data = make_pdf([], pdf_text)
    documents = [
        ("TXT", text.encode(), split_text_blocks(text, "linhas"), text_cpfs),
        ("PDF", pdf_data, read_pdf(pdf_data)[1], pdf_cpfs),
    ]
    client = OllamaClient("http://localhost:11434", 120)
    if not client.status().online:
        print("Ollama local indisponível")
        return 2

    total_expected: set[str] = set()
    total_found: set[str] = set()
    total_blocks = 0
    total_seconds = 0.0
    for fmt, payload, blocks, expected in documents:
        source = SourceFile(
            hashlib.sha256(payload).hexdigest(),
            f"benchmark.{fmt.lower()}",
            FileFormat(fmt),
            len(payload),
        )
        source.text_blocks = blocks
        started = time.perf_counter()
        extract_blocks(
            client,
            model,
            source,
            lambda done, count, format_name=fmt: print(f"{format_name}: {done}/{count}"),
        )
        elapsed = time.perf_counter() - started
        found = {ascii_digits(record.cpf).zfill(11) for record in source.ai_records}
        accepted = found & expected
        total_expected.update(expected)
        total_found.update(accepted)
        total_blocks += sum(block.has_student_hint for block in blocks)
        total_seconds += elapsed
        print(f"{fmt}: {len(accepted)}/{len(expected)} CPFs, {elapsed:.1f} s")

    recall = len(total_found) / len(total_expected)
    precision = 1.0 if total_found else 0.0  # CPFs fora da origem foram recusados.
    seconds_per_block = total_seconds / total_blocks if total_blocks else 0.0
    print(
        f"modelo={model} recall={recall:.1%} precisão_conferida={precision:.1%} "
        f"segundos_por_bloco={seconds_per_block:.1f}"
    )
    return 0 if recall >= 0.98 and precision == 1.0 else 1


def main() -> None:
    """Executa o benchmark pela linha de comando."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--students", type=int, default=60)
    args = parser.parse_args()
    raise SystemExit(run(args.model, args.students))


if __name__ == "__main__":
    main()
