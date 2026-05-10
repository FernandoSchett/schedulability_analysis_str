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
    fieldnames = ["N", "count", "EDF (%)", "DM (%)", "dbf(lmax)/lmax < 0.5 (%)", "practical lmax pessimism (%)"]
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
        "critical_points_count",
        "qpa_checked_points",
        "qpa_reduction_ratio",
        "lmax_low_dbf_ratio",
        "lmax_practical_pessimism",
        "expected_schedulable",
        "edf_schedulable",
        "dm_schedulable",
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
                    "critical_points_count": r.get("critical_points_count"),
                    "qpa_checked_points": r.get("qpa_checked_points"),
                    "qpa_reduction_ratio": r.get("qpa_reduction_ratio"),
                    "lmax_low_dbf_ratio": r.get("lmax_low_dbf_ratio"),
                    "lmax_practical_pessimism": r.get("lmax_practical_pessimism"),
                    "expected_schedulable": r.get("expected_schedulable"),
                    "edf_schedulable": r.get("edf_schedulable"),
                    "dm_schedulable": r.get("dm_schedulable"),
                }
            )


def _write_validation_analysis(path: str, rows: list[dict]) -> None:
    valid_expected_count = 0
    correct_edf_count = 0
    
    for r in rows:
        expected = r.get("expected_schedulable")
        if expected is not None:
            valid_expected_count += 1
            if bool(expected) == bool(r.get("edf_schedulable")):
                correct_edf_count += 1

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("=========================================\n")
        fh.write("  VALIDAÇÃO DO ALGORITMO QPA (EDF) \n")
        fh.write("=========================================\n\n")
        fh.write(f"Total de conjuntos analisados: {len(rows)}\n")
        fh.write(f"Conjuntos que possuíam Ground Truth ('schedulable'): {valid_expected_count}\n")
        
        if valid_expected_count > 0:
            accuracy = (correct_edf_count / valid_expected_count) * 100
            fh.write(f"Acertos do QPA vs Ground Truth: {correct_edf_count} de {valid_expected_count}\n")
            fh.write(f"Acurácia da implementação QPA: {accuracy:.4f}%\n")
            if correct_edf_count == valid_expected_count:
                fh.write("\n-> SUCESSO: A implementação do QPA bateu 100% com a verdade de referência!\n")
            else:
                fh.write("\n-> AVISO: Houve divergências entre o QPA e a verdade de referência.\n")
        else:
            fh.write("\nNenhum conjunto possuía o campo 'schedulable' para verificação de ground truth.\n")


def _write_lmax_analysis(path: str, rows: list[dict]) -> None:
    lmaxs = [r.get("l_max") for r in rows if isinstance(r.get("l_max"), (int, float))]
    if not lmaxs:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("No numeric l_max/dbf data available.\n")
        return

    median_lmax = sorted(lmaxs)[len(lmaxs) // 2]
    low_dbf_count = sum(1 for r in rows if r.get("lmax_low_dbf_ratio"))
    pract_pess_count = sum(1 for r in rows if r.get("lmax_practical_pessimism"))
    
    crit_pts = [r.get("critical_points_count") for r in rows if isinstance(r.get("critical_points_count"), (int, float))]
    checked_pts = [r.get("qpa_checked_points") for r in rows if isinstance(r.get("qpa_checked_points"), (int, float))]
    red_ratios = [r.get("qpa_reduction_ratio") for r in rows if isinstance(r.get("qpa_reduction_ratio"), (int, float))]
    
    avg_crit_pts = sum(crit_pts) / len(crit_pts) if crit_pts else 0.0
    avg_checked_pts = sum(checked_pts) / len(checked_pts) if checked_pts else 0.0
    avg_red_ratio = sum(red_ratios) / len(red_ratios) if red_ratios else 0.0
    
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"Total datasets analyzed: {len(rows)}\n")
        fh.write(f"Median l_max: {median_lmax:.4f}\n\n")
        fh.write(f"Datasets with dbf(l_max)/l_max < 0.5: {low_dbf_count} ({(low_dbf_count/len(rows))*100:.2f}%)\n")
        fh.write(f"Datasets with practical l_max pessimism: {pract_pess_count} ({(pract_pess_count/len(rows))*100:.2f}%)\n\n")
        fh.write(f"Average critical_points_count: {avg_crit_pts:.2f}\n")
        fh.write(f"Average qpa_checked_points: {avg_checked_pts:.2f}\n")
        fh.write(f"Average qpa_reduction_ratio: {avg_red_ratio:.4f}\n")


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
                "low_dbf": 0,
                "pract_pess": 0,
            },
        )
        bucket["Conjuntos"] += 1
        bucket["EDF ok"] += int(bool(row.get("edf_schedulable")))
        bucket["DM ok"] += int(bool(row.get("dm_schedulable")))
        bucket["low_dbf"] += int(bool(row.get("lmax_low_dbf_ratio")))
        bucket["pract_pess"] += int(bool(row.get("lmax_practical_pessimism")))
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
                "dbf(lmax)/lmax < 0.5 (%)": 100.0 * bucket["low_dbf"] / total if total else 0.0,
                "practical lmax pessimism (%)": 100.0 * bucket["pract_pess"] / total if total else 0.0,
            }
        )

    return summary


def _write_results_by_dataset_csv(path: str, rows: list[dict]) -> None:
    summary = _summarize_by_input_file(rows)
    fieldnames = ["Arquivo", "N", "Conjuntos", "EDF (%)", "DM (%)", "dbf(lmax)/lmax < 0.5 (%)", "practical lmax pessimism (%)"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def _write_results_by_dataset_tex(path: str, rows: list[dict]) -> None:
    summary = _summarize_by_input_file(rows)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\\begin{table}[H]\n")
        fh.write("\\centering\n")
        fh.write("\\scriptsize\n")
        fh.write("\\caption{Resultados de escalonabilidade e pessimismo de $l_{max}$ por arquivo.}\n")
        fh.write("\\label{tab:results_by_dataset_pessimism}\n")
        fh.write("\\begin{tabular}{l c c c c c c}\n")
        fh.write("\\hline\n")
        fh.write("\\textbf{Arquivo} & \\textbf{N} & \\textbf{Total} & \\textbf{EDF (\\%)} & \\textbf{DM (\\%)} & \\textbf{dbf/$l_{max}$ < 0.5 (\\%)} & \\textbf{Pessimismo Prático (\\%)} \\\\\n")
        fh.write("\\hline\n")
        for row in summary:
            fh.write(
                f"{_escape_latex(str(row['Arquivo']))} & {row['N']} & {row['Conjuntos']} & {row['EDF (%)']:.2f} & {row['DM (%)']:.2f} & {row['dbf(lmax)/lmax < 0.5 (%)']:.2f} & {row['practical lmax pessimism (%)']:.2f} \\\\\n"
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
        default="resultados/summary_by_n_tasks.csv",
        help="Caminho para salvar tabela agregada em CSV.",
    )
    parser.add_argument(
        "--details-json",
        default="resultados/detailed_results.json",
        help="Caminho para salvar resultados detalhados por dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    datasets = load_datasets_from_paths(args.inputs, recursive=not args.no_recursive)
    rows = analyze_datasets(datasets)
    summary = summarize_by_n_tasks(rows)

    _print_summary_table(summary)

    # ensure output dir exists based on the args
    out_dir = Path(args.summary_csv).parent if args.summary_csv else Path("resultados")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.summary_csv:
        _write_summary_csv(args.summary_csv, summary)
    if args.details_json:
        _write_details_json(args.details_json, rows)
    # per-dataset outputs
    _write_per_dataset_csv(str(out_dir / "per_dataset_results.csv"), rows)
    _write_lmax_analysis(str(out_dir / "lmax_analysis.txt"), rows)
    _write_validation_analysis(str(out_dir / "validation_report.txt"), rows)
    _write_results_by_dataset_csv(str(out_dir / "results_by_dataset.csv"), rows)
    _write_results_by_dataset_tex(str(out_dir / "results_by_dataset.tex"), rows)


if __name__ == "__main__":
    main()
