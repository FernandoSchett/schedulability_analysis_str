from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

from .analysis import qpa, rta_deadline_monotonic, dbf, count_critical_points_until_lmax


ResultRow = dict


def analyze_datasets(datasets: Iterable[dict]) -> list[ResultRow]:
    rows: list[ResultRow] = []

    for ds in datasets:
        tasks = ds["tasks"]
        l_max = float(ds["l_max"])

        dm_result = rta_deadline_monotonic(tasks)
        edf_result = qpa(tasks, l_max=l_max)
        try:
            dbf_at_lmax = float(dbf(l_max, tasks))
        except Exception:
            dbf_at_lmax = float("nan")
        ratio = dbf_at_lmax / l_max if l_max > 0 else float("nan")

        checked_pts = edf_result.get("checked_points", 0)
        crit_pts = count_critical_points_until_lmax(tasks, l_max)
        red_ratio = (1.0 - (checked_pts / crit_pts)) if crit_pts > 0 else 0.0

        ratio_under_half = bool(ratio < 0.5) if not math.isnan(ratio) else False
        pract_pess = bool(red_ratio >= 0.95)

        rows.append(
            {
                "id": ds.get("id"),
                "n_tasks": int(ds.get("n_tasks", len(tasks))),
                "source_file": ds.get("_source_file"),
                "l_max": l_max,
                "dbf_l_max": dbf_at_lmax,
                "dbf_over_lmax": ratio,
                "critical_points_count": crit_pts,
                "qpa_checked_points": checked_pts,
                "qpa_reduction_ratio": red_ratio,
                "lmax_low_dbf_ratio": ratio_under_half,
                "lmax_practical_pessimism": pract_pess,
                "expected_schedulable": ds.get("schedulable"),
                "edf_schedulable": bool(edf_result["schedulable"]),
                "dm_schedulable": bool(dm_result["schedulable"]),
                "edf_details": edf_result,
                "dm_details": dm_result,
            }
        )

    return rows


def summarize_by_n_tasks(rows: Iterable[ResultRow]) -> list[dict]:
    grouped = defaultdict(lambda: {"total": 0, "edf_ok": 0, "dm_ok": 0, "low_dbf": 0, "pract_pess": 0, "qpa_correct": 0, "valid_gt": 0})

    for row in rows:
        n = int(row["n_tasks"])
        grouped[n]["total"] += 1
        grouped[n]["edf_ok"] += int(bool(row["edf_schedulable"]))
        grouped[n]["dm_ok"] += int(bool(row["dm_schedulable"]))
        grouped[n]["low_dbf"] += int(bool(row.get("lmax_low_dbf_ratio")))
        grouped[n]["pract_pess"] += int(bool(row.get("lmax_practical_pessimism")))
        
        expected = row.get("expected_schedulable")
        if expected is not None:
            grouped[n]["valid_gt"] += 1
            if bool(expected) == bool(row["edf_schedulable"]):
                grouped[n]["qpa_correct"] += 1

    summary: list[dict] = []
    for n in sorted(grouped):
        total = grouped[n]["total"]
        valid_gt = grouped[n]["valid_gt"]
        edf_pct = 100.0 * grouped[n]["edf_ok"] / total if total else 0.0
        dm_pct = 100.0 * grouped[n]["dm_ok"] / total if total else 0.0
        dbf_under_half = 100.0 * grouped[n]["low_dbf"] / total if total else 0.0
        pessimism_pct = 100.0 * grouped[n]["pract_pess"] / total if total else 0.0
        qpa_accuracy = 100.0 * grouped[n]["qpa_correct"] / valid_gt if valid_gt else 0.0

        summary.append(
            {
                "N": n,
                "count": total,
                "EDF (%)": edf_pct,
                "DM (%)": dm_pct,
                "dbf(lmax)/lmax < 0.5 (%)": dbf_under_half,
                "practical lmax pessimism (%)": pessimism_pct,
                "QPA Accuracy (%)": qpa_accuracy,
            }
        )

    return summary
