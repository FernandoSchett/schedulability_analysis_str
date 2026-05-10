from __future__ import annotations

import argparse
import csv
import json
import re
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


def _write_per_dataset_csv(path: str, rows: list[dict]) -> None:
    fieldnames = [
        "id",
        "n_tasks",
        "source_file",
        "l_max",
        "dbf_l_max",
        "dbf_over_lmax",
        "expected_schedulable",
        "edf_schedulable",
        "dm_schedulable",
        "edf_checked_points",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.get("id"),
                    "n_tasks": r.get("n_tasks"),
                    "source_file": r.get("source_file"),
                    "l_max": r.get("l_max"),
                    "dbf_l_max": r.get("dbf_l_max"),
                    "dbf_over_lmax": r.get("dbf_over_lmax"),
                    "expected_schedulable": r.get("expected_schedulable"),
                    "edf_schedulable": r.get("edf_schedulable"),
                    "dm_schedulable": r.get("dm_schedulable"),
                    "edf_checked_points": r.get("edf_details", {}).get("checked_points"),
                }
            )


def _write_lmax_analysis(path: str, rows: list[dict]) -> None:
    # Basic heuristics to flag potentially conservative l_max
    ratios = [r.get("dbf_over_lmax") for r in rows if isinstance(r.get("dbf_over_lmax"), (int, float))]
    lmaxs = [r.get("l_max") for r in rows if isinstance(r.get("l_max"), (int, float))]
    if not ratios or not lmaxs:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("No numeric l_max/dbf data available.\n")
        return

    median_lmax = sorted(lmaxs)[len(lmaxs) // 2]
    conservative_count = 0
    small_checked_but_large_lmax = 0
    for r in rows:
        ratio = r.get("dbf_over_lmax")
        lmax = r.get("l_max")
        checked = r.get("edf_details", {}).get("checked_points")
        if isinstance(ratio, (int, float)) and ratio < 0.1:
            conservative_count += 1
        if isinstance(lmax, (int, float)) and lmax > median_lmax and isinstance(checked, int) and checked <= 10:
            small_checked_but_large_lmax += 1

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"Total datasets: {len(rows)}\n")
        fh.write(f"Median l_max: {median_lmax}\n")
        fh.write(f"Datasets with dbf(l_max)/l_max < 0.1: {conservative_count}\n")
        fh.write(
            "Datasets with l_max > median but QPA solved with <=10 checked points: %d\n" % small_checked_but_large_lmax
        )
        fh.write("\nGuidance:\n")
        fh.write(
            "- If dbf(l_max)/l_max << 1 then l_max may be overly conservative for that dataset.\n"
        )
        fh.write(
            "- If l_max is large but QPA solved with few checked points, then l_max is conservative in worst-case but QPA's backtracking reduced practical cost.\n"
        )


def _escape_latex(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("$", r"\$")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _summarize_by_input_file(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}

    for row in rows:
        source_file = str(row.get("source_file") or "")
        key = Path(source_file).name if source_file else "unknown"
        bucket = grouped.setdefault(
            key,
            {
                "Arquivo": key,
                "N": row.get("n_tasks"),
                "Conjuntos": 0,
                "EDF ok": 0,
                "DM ok": 0,
            },
        )
        bucket["Conjuntos"] += 1
        bucket["EDF ok"] += int(bool(row.get("edf_schedulable")))
        bucket["DM ok"] += int(bool(row.get("dm_schedulable")))
        if bucket["N"] is None:
            bucket["N"] = row.get("n_tasks")

    def sort_key(item: str) -> tuple[int, int, str]:
        match = re.search(r"n(\d+)_([a-z]+)\.json$", item)
        n_value = int(match.group(1)) if match else 10**9
        difficulty = match.group(2) if match else item
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 99)
        return (n_value, difficulty_order, item)

    summary: list[dict] = []
    for key in sorted(grouped, key=sort_key):
        bucket = grouped[key]
        total = bucket["Conjuntos"]
        summary.append(
            {
                "Arquivo": bucket["Arquivo"],
                "N": bucket["N"],
                "Conjuntos": total,
                "EDF (%)": 100.0 * bucket["EDF ok"] / total if total else 0.0,
                "DM (%)": 100.0 * bucket["DM ok"] / total if total else 0.0,
            }
        )

    return summary


def _write_results_by_dataset_csv(path: str, rows: list[dict]) -> None:
    summary = _summarize_by_input_file(rows)
    fieldnames = ["Arquivo", "N", "Conjuntos", "EDF (%)", "DM (%)"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def _write_results_by_dataset_tex(path: str, rows: list[dict]) -> None:
    summary = _summarize_by_input_file(rows)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\\begin{table}[H]\n")
        fh.write("\\centering\n")
        fh.write("\\caption{Resultados de escalonabilidade por arquivo de entrada.}\n")
        fh.write("\\label{tab:results_by_dataset}\n")
        fh.write("\\begin{tabular}{l c c c c}\n")
        fh.write("\\hline\n")
        fh.write("\\textbf{Arquivo} & \\textbf{N} & \\textbf{Conjuntos} & \\textbf{EDF (\\%)} & \\textbf{DM (\\%)} \\\\\n")
        fh.write("\\hline\n")
        for row in summary:
            fh.write(
                f"{_escape_latex(str(row['Arquivo']))} & {row['N']} & {row['Conjuntos']} & {row['EDF (%)']:.2f} & {row['DM (%)']:.2f} \\\\\n"
            )
        fh.write("\\hline\n")
        fh.write("\\end{tabular}\n")
        fh.write("\\end{table}\n")


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
    # per-dataset CSV
    _write_per_dataset_csv("per_dataset_results.csv", rows)
    _write_lmax_analysis("lmax_analysis.txt", rows)
    _write_results_by_dataset_csv("results_by_dataset.csv", rows)
    _write_results_by_dataset_tex("results_by_dataset.tex", rows)


if __name__ == "__main__":
    main()
