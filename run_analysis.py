from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Allows "python run_analysis.py" from project root without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rt_sched.experiment import analyze_datasets, summarize_by_n_tasks
from rt_sched.io_utils import load_datasets_from_paths


def _write_summary_csv(path: str, summary: list[dict]) -> None:
    fieldnames = ["N", "count", "EDF (%)", "DM (%)"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def _write_details_json(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)


def _print_summary_table(summary: list[dict]) -> None:
    if not summary:
        print("Nenhum dataset encontrado.")
        return

    print("N\tEDF (%)\tDM (%)\tcount")
    for row in summary:
        print(f"{row['N']}\t{row['EDF (%)']:.2f}\t{row['DM (%)']:.2f}\t{row['count']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Executa RTA/DM e QPA/EDF em múltiplos task sets JSON "
            "e agrega os resultados por n_tasks."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Arquivos JSON e/ou diretórios contendo JSONs.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Não varrer diretórios recursivamente.",
    )
    parser.add_argument(
        "--summary-csv",
        default="summary_by_n_tasks.csv",
        help="Caminho para salvar tabela agregada em CSV.",
    )
    parser.add_argument(
        "--details-json",
        default="detailed_results.json",
        help="Caminho para salvar resultados detalhados por dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    datasets = load_datasets_from_paths(args.inputs, recursive=not args.no_recursive)
    rows = analyze_datasets(datasets)
    summary = summarize_by_n_tasks(rows)

    _print_summary_table(summary)

    if args.summary_csv:
        _write_summary_csv(args.summary_csv, summary)
    if args.details_json:
        _write_details_json(args.details_json, rows)


if __name__ == "__main__":
    main()
