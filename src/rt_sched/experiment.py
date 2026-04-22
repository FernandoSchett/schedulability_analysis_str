from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .analysis import qpa, rta_deadline_monotonic


ResultRow = dict


def analyze_datasets(datasets: Iterable[dict]) -> list[ResultRow]:
    rows: list[ResultRow] = []

    for ds in datasets:
        tasks = ds["tasks"]
        l_max = float(ds["l_max"])

        dm_result = rta_deadline_monotonic(tasks)
        edf_result = qpa(tasks, l_max=l_max)

        rows.append(
            {
                "id": ds.get("id"),
                "n_tasks": int(ds.get("n_tasks", len(tasks))),
                "source_file": ds.get("_source_file"),
                "expected_schedulable": ds.get("schedulable"),
                "edf_schedulable": bool(edf_result["schedulable"]),
                "dm_schedulable": bool(dm_result["schedulable"]),
                "edf_details": edf_result,
                "dm_details": dm_result,
            }
        )

    return rows


def summarize_by_n_tasks(rows: Iterable[ResultRow]) -> list[dict]:
    grouped = defaultdict(lambda: {"total": 0, "edf_ok": 0, "dm_ok": 0})

    for row in rows:
        n = int(row["n_tasks"])
        grouped[n]["total"] += 1
        grouped[n]["edf_ok"] += int(bool(row["edf_schedulable"]))
        grouped[n]["dm_ok"] += int(bool(row["dm_schedulable"]))

    summary: list[dict] = []
    for n in sorted(grouped):
        total = grouped[n]["total"]
        edf_pct = 100.0 * grouped[n]["edf_ok"] / total if total else 0.0
        dm_pct = 100.0 * grouped[n]["dm_ok"] / total if total else 0.0

        summary.append(
            {
                "N": n,
                "count": total,
                "EDF (%)": edf_pct,
                "DM (%)": dm_pct,
            }
        )

    return summary
