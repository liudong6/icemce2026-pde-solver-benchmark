from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from pdescale.decision import SOLVER_DECISION_FIELDS


TIMING_REPEAT_FIELDS: tuple[str, ...] = ("repeat_index", *SOLVER_DECISION_FIELDS)

TIMING_STABILITY_FIELDS: tuple[str, ...] = (
    "coefficient_case",
    "family",
    "n",
    "best_method_by_median",
    "best_method_vote",
    "vote_fraction",
    "n_repeats",
    "cg_median_seconds",
    "selected_median_seconds",
    "median_speedup_vs_cg",
    "selected_rel_iqr",
    "decision_stable",
)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return 0.5 * (ordered[midpoint - 1] + ordered[midpoint])


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = percentile * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return (1.0 - weight) * ordered[lower] + weight * ordered[upper]


def _relative_iqr(values: Sequence[float]) -> float:
    median = _median(values)
    if median <= 0.0:
        return 0.0
    return float((_percentile(values, 0.75) - _percentile(values, 0.25)) / median)


def _best_vote(rows: Sequence[dict[str, object]]) -> tuple[str, float, int]:
    by_repeat: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_repeat[str(row["repeat_index"])].append(row)

    votes: Counter[str] = Counter()
    for repeat_rows in by_repeat.values():
        marked = [row for row in repeat_rows if _as_bool(row.get("is_best", False))]
        if marked:
            votes[str(marked[0]["method"])] += 1
            continue
        converged = [row for row in repeat_rows if _as_bool(row["converged"])]
        if converged:
            best = min(converged, key=lambda row: float(row["total_seconds"]))
            votes[str(best["method"])] += 1

    n_repeats = len(by_repeat)
    if not votes or n_repeats == 0:
        return "", 0.0, n_repeats
    method, count = votes.most_common(1)[0]
    return method, float(count / n_repeats), n_repeats


def summarize_timing_repeats(rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, int], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["coefficient_case"]), str(row["family"]), int(float(row["n"])))].append(row)

    output: list[dict[str, object]] = []
    for (case, family, n), case_rows in sorted(grouped.items(), key=lambda item: (item[0][2], item[0][0])):
        by_method: dict[str, list[float]] = defaultdict(list)
        for row in case_rows:
            if _as_bool(row["converged"]):
                by_method[str(row["method"])].append(float(row["total_seconds"]))
        if not by_method:
            continue

        method_medians = {method: _median(values) for method, values in by_method.items()}
        best_method_by_median = min(method_medians, key=method_medians.get)
        best_method_vote, vote_fraction, n_repeats = _best_vote(case_rows)
        cg_median = method_medians.get("cg", 0.0)
        selected_median = method_medians[best_method_by_median]
        speedup = float(cg_median / selected_median) if cg_median > 0.0 and selected_median > 0.0 else 0.0
        selected_rel_iqr = _relative_iqr(by_method[best_method_by_median])
        output.append(
            {
                "coefficient_case": case,
                "family": family,
                "n": n,
                "best_method_by_median": best_method_by_median,
                "best_method_vote": best_method_vote,
                "vote_fraction": vote_fraction,
                "n_repeats": n_repeats,
                "cg_median_seconds": cg_median,
                "selected_median_seconds": selected_median,
                "median_speedup_vs_cg": speedup,
                "selected_rel_iqr": selected_rel_iqr,
                "decision_stable": bool(
                    best_method_by_median == best_method_vote and vote_fraction >= (2.0 / 3.0)
                ),
            }
        )
    return output


def write_timing_repeats_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TIMING_REPEAT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in TIMING_REPEAT_FIELDS})


def write_timing_stability_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TIMING_STABILITY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in TIMING_STABILITY_FIELDS})
