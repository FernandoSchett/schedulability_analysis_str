from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

EPS = 1e-12

@dataclass(frozen=True)
class Task:
    C: float
    T: float
    D: float
    J: float = 0.0

    def __post_init__(self) -> None:
        if self.C < 0:
            raise ValueError(f"C must be non-negative, got {self.C}")
        if self.T <= 0:
            raise ValueError(f"T must be positive, got {self.T}")
        if self.D <= 0:
            raise ValueError(f"D must be positive, got {self.D}")
        if self.J < 0:
            raise ValueError(f"J must be non-negative, got {self.J}")


def _safe_floor(x: float) -> int:
    return math.floor(x + EPS)


def _safe_ceil(x: float) -> int:
    return math.ceil(x - EPS)


def _almost_equal(a: float, b: float, eps: float = EPS) -> bool:
    return abs(a - b) <= eps


def normalize_tasks(tasks: Sequence[Task | dict]) -> list[Task]:
    normalized: list[Task] = []
    for task in tasks:
        if isinstance(task, Task):
            normalized.append(task)
            continue

        normalized.append(
            Task(
                C=float(task["C"]),
                T=float(task["T"]),
                D=float(task["D"]),
                J=float(task.get("J", 0.0)),
            )
        )
    return normalized


def _dm_order(tasks: Sequence[Task]) -> list[tuple[int, Task]]:
    indexed = list(enumerate(tasks))
    indexed.sort(key=lambda item: (item[1].D, item[1].T, item[0]))
    return indexed


def rta_deadline_monotonic(
    tasks: Sequence[Task | dict],
    max_iterations: int = 100_000,
) -> dict:
    task_list = normalize_tasks(tasks)
    ordered = _dm_order(task_list)

    response_times: list[dict] = []

    for prio_idx, (original_idx, task_i) in enumerate(ordered):
        deadline_limit = task_i.D
        if deadline_limit < -EPS:
            return {
                "schedulable": False,
                "failed_task_original_index": original_idx,
                "failed_task_dm_priority_index": prio_idx,
                "reason": "D_i < 0",
                "response_times": response_times,
            }

        r_prev = task_i.C

        # Calculo do ponto fixo Audsley et al. (1993)
        for iteration in range(max_iterations):
            interference = 0.0
            for hp_idx in range(prio_idx):
                _, task_j = ordered[hp_idx]
                jobs = _safe_ceil((r_prev + task_j.J) / task_j.T)
                if jobs > 0:
                    interference += jobs * task_j.C

            r_next = task_i.C + interference

            # Criterio de escalonamento
            if r_next > deadline_limit + EPS:
                return {
                    "schedulable": False,
                    "failed_task_original_index": original_idx,
                    "failed_task_dm_priority_index": prio_idx,
                    "reason": "R_i > D_i",
                    "response_times": response_times,
                    "computed_r": r_next,
                    "deadline_limit": deadline_limit,
                }

            if _almost_equal(r_next, r_prev):
                r_prev = r_next
                break

            r_prev = r_next
        else:
            return {
                "schedulable": False,
                "failed_task_original_index": original_idx,
                "failed_task_dm_priority_index": prio_idx,
                "reason": "RTA did not converge within max_iterations",
                "response_times": response_times,
            }

        response_times.append(
            {
                "task_original_index": original_idx,
                "task_dm_priority_index": prio_idx,
                "R": r_prev,
                "J": task_i.J,
                "D": task_i.D,
                "meets_deadline": r_prev <= task_i.D + EPS,
            }
        )

    return {
        "schedulable": True,
        "response_times": response_times,
    }


def dbf(t: float, tasks: Sequence[Task | dict]) -> float:
    if t <= 0:
        return 0.0

    task_list = normalize_tasks(tasks)
    demand = 0.0
    
    # Baruah et al. (1990), Spuri (1996):
    for task in task_list:
        njobs = _safe_floor((t - task.D + task.J) / task.T) + 1
        if njobs > 0:
            demand += njobs * task.C

    return demand


def _previous_critical_point(
    upper: float,
    tasks: Sequence[Task],
    strict: bool,
) -> float | None:
    best: float | None = None

    for task in tasks:
        base = task.D - task.J
        if upper + EPS < base:
            continue

        k = _safe_floor((upper - base) / task.T)
        if strict:
            point = base + k * task.T
            if _almost_equal(point, upper):
                k -= 1

        if k < 0:
            continue

        point = base + k * task.T
        if point < -EPS:
            continue

        if (best is None) or (point > best + EPS):
            best = point

    return best


def count_critical_points_until_lmax(
    tasks: Sequence[Task | dict],
    l_max: float,
) -> int:
    if l_max <= 0:
        return 0

    task_list = normalize_tasks(tasks)
    unique_points = set()

    for task in task_list:
        base = task.D - task.J
        if l_max + EPS < base:
            continue
            
        k_max = _safe_floor((l_max - base) / task.T)
        for k in range(k_max + 1):
            point = base + k * task.T
            if point >= -EPS:
                unique_points.add(round(point, 7))
            
    return len(unique_points)


# Zhang & Burns (2009)
def qpa(
    tasks: Sequence[Task | dict],
    l_max: float,
    max_steps: int = 2_000_000,
) -> dict:
    task_list = normalize_tasks(tasks)

    if l_max <= 0:
        return {
            "schedulable": True,
            "checked_points": 0,
        }

    t = float(l_max)
    checked_points = 0

    for _ in range(max_steps):
        checked_points += 1

        demand_t = dbf(t, task_list)

        if demand_t > t + EPS:
            return {
                "schedulable": False,
                "witness_t": t,
                "dbf_t": demand_t,
                "checked_points": checked_points,
            }

        if _almost_equal(demand_t, t):
            t_next = _previous_critical_point(t, task_list, strict=True)
        else:
            backtracked = demand_t
            t_next = _previous_critical_point(backtracked, task_list, strict=False)

            if t_next is not None and t_next >= t - EPS:
                t_next = _previous_critical_point(t, task_list, strict=True)

        if t_next is None or t_next <= EPS:
            return {
                "schedulable": True,
                "checked_points": checked_points,
            }

        t = t_next

    return {
        "schedulable": False,
        "reason": "QPA reached max_steps without termination",
        "checked_points": checked_points,
    }
