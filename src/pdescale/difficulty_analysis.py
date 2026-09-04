from __future__ import annotations

import csv
import math
import random
import zlib
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import numpy as np


DIFFICULTY_RELATIONSHIP_FIELDS: tuple[str, ...] = (
    "descriptor",
    "response",
    "n_group",
    "spearman_rho",
    "fisher_z_diagnostic_low",
    "fisher_z_diagnostic_high",
    "case_resampling_low",
    "case_resampling_high",
    "permutation_p",
    "n_permutations",
    "n_case_resamples",
    "n_samples",
    "description",
)


DESCRIPTOR_LABELS: dict[str, str] = {
    "contrast_observed": "Observed coefficient contrast",
    "grad_logk_inf": "Discrete maximum log-conductivity gradient",
    "total_variation_proxy": "Discrete total-variation proxy",
    "condition_estimate": "Matched spectral condition estimate",
}


RESPONSE_LABELS: dict[str, str] = {
    "cg_iterations": "Unpreconditioned CG iterations",
    "selected_speedup_vs_cg": "Selected-solver speedup over CG",
}


def _rank_average_ties(values: Sequence[float]) -> list[float]:
    indexed = sorted((float(value), index) for index, value in enumerate(values))
    ranks = [0.0] * len(indexed)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][0] == indexed[start][0]:
            end += 1
        rank = 0.5 * (start + 1 + end)
        for _, index in indexed[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def _pearson(x_values: Sequence[float], y_values: Sequence[float]) -> float:
    if len(x_values) != len(y_values):
        raise ValueError("x and y must have the same length")
    if len(x_values) < 2:
        return 0.0
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_ss = sum((x - x_mean) ** 2 for x in x_values)
    y_ss = sum((y - y_mean) ** 2 for y in y_values)
    if x_ss == 0.0 or y_ss == 0.0:
        return 0.0
    rho = numerator / math.sqrt(x_ss * y_ss)
    if abs(rho - 1.0) < 1e-12:
        return 1.0
    if abs(rho + 1.0) < 1e-12:
        return -1.0
    if abs(rho) < 1e-12:
        return 0.0
    return float(rho)


def spearman_rank_correlation(x_values: Sequence[float], y_values: Sequence[float]) -> float:
    """Return Spearman's rho using average ranks for tied values."""
    if len(x_values) != len(y_values):
        raise ValueError("x and y must have the same length")
    return _pearson(_rank_average_ties(x_values), _rank_average_ties(y_values))


def fisher_z_interval(
    rho: float,
    n_samples: int,
    *,
    z_value: float = 1.959963984540054,
) -> tuple[float, float]:
    """Return a Fisher-z diagnostic interval for a descriptive correlation."""
    if n_samples <= 3:
        return (-1.0, 1.0)
    clipped = min(max(float(rho), -0.999999), 0.999999)
    z_rho = math.atanh(clipped)
    half_width = z_value / math.sqrt(n_samples - 3)
    return (
        math.tanh(z_rho - half_width),
        math.tanh(z_rho + half_width),
    )


def permutation_p_value(
    x_values: Sequence[float],
    y_values: Sequence[float],
    observed_rho: float,
    *,
    n_permutations: int = 4999,
    seed: int = 0,
) -> float:
    """Return a deterministic two-sided permutation p-value for Spearman rho."""
    if len(x_values) != len(y_values):
        raise ValueError("x and y must have the same length")
    if len(x_values) < 3 or len(set(x_values)) < 2 or len(set(y_values)) < 2:
        return 1.0
    rng = random.Random(seed)
    permuted = list(float(value) for value in y_values)
    threshold = abs(float(observed_rho))
    exceedances = 0
    for _ in range(n_permutations):
        rng.shuffle(permuted)
        rho = spearman_rank_correlation(x_values, permuted)
        if abs(rho) >= threshold - 1e-12:
            exceedances += 1
    return float((exceedances + 1) / (n_permutations + 1))


def case_resampling_spearman_interval(
    x_values: Sequence[float],
    y_values: Sequence[float],
    *,
    n_case_resamples: int = 1999,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float] | None:
    """Return a deterministic case-resampling uncertainty interval for Spearman rho."""
    if len(x_values) != len(y_values):
        raise ValueError("x and y must have the same length")
    if len(x_values) < 3 or len(set(x_values)) < 2 or len(set(y_values)) < 2:
        return None
    rng = random.Random(seed)
    n = len(x_values)
    samples: list[float] = []
    for _ in range(n_case_resamples):
        indices = [rng.randrange(n) for _ in range(n)]
        sample_x = [float(x_values[index]) for index in indices]
        sample_y = [float(y_values[index]) for index in indices]
        if len(set(sample_x)) < 2 or len(set(sample_y)) < 2:
            continue
        samples.append(spearman_rank_correlation(sample_x, sample_y))
    if not samples:
        return None
    lower, upper = np.quantile(np.asarray(samples, dtype=float), [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(lower), float(upper)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _conditioning_by_case(conditioning_rows: Sequence[dict[str, object]]) -> dict[str, dict[int, float]]:
    grouped: dict[str, dict[int, float]] = defaultdict(dict)
    for row in conditioning_rows:
        grouped[str(row["coefficient_case"])][int(float(row["n"]))] = float(row["condition_estimate"])
    return dict(grouped)


def _condition_for_decision_n(condition_by_case: dict[str, dict[int, float]], case: str, n: int) -> float | None:
    values = condition_by_case.get(case)
    if not values:
        return None
    if n in values:
        return values[n]
    available = sorted(values)
    lower_or_equal = [value for value in available if value <= n]
    source_n = lower_or_equal[-1] if lower_or_equal else available[-1]
    return values[source_n]


def _decision_observations(
    decision_rows: Sequence[dict[str, object]],
    conditioning_rows: Sequence[dict[str, object]],
) -> list[dict[str, float | int | str]]:
    condition_by_case = _conditioning_by_case(conditioning_rows)
    grouped: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in decision_rows:
        grouped[(str(row["coefficient_case"]), int(float(row["n"])))].append(row)

    observations: list[dict[str, float | int | str]] = []
    for (case, n), rows in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        cg_row = next((row for row in rows if str(row["method"]) == "cg"), None)
        best_row = next((row for row in rows if _as_bool(row["is_best"])), None)
        condition_estimate = _condition_for_decision_n(condition_by_case, case, n)
        if cg_row is None or best_row is None or condition_estimate is None:
            continue
        observations.append(
            {
                "coefficient_case": case,
                "n": n,
                "contrast_observed": float(cg_row["contrast_observed"]),
                "grad_logk_inf": float(cg_row["grad_logk_inf"]),
                "total_variation_proxy": float(cg_row["total_variation_proxy"]),
                "condition_estimate": float(condition_estimate),
                "cg_iterations": float(cg_row["iterations"]),
                "selected_speedup_vs_cg": float(best_row["speedup_vs_cg"]),
            }
        )
    return observations


def analyze_difficulty_relationships(
    decision_rows: Sequence[dict[str, object]],
    conditioning_rows: Sequence[dict[str, object]],
    *,
    n_permutations: int = 4999,
    n_case_resamples: int = 1999,
) -> list[dict[str, object]]:
    observations = _decision_observations(decision_rows, conditioning_rows)
    if not observations:
        return []

    n_groups: list[tuple[str, list[dict[str, float | int | str]]]] = [("all", observations)]
    for n in sorted({int(row["n"]) for row in observations}):
        n_groups.append((str(n), [row for row in observations if int(row["n"]) == n]))

    rows: list[dict[str, object]] = []
    for n_group, group in n_groups:
        for descriptor, descriptor_label in DESCRIPTOR_LABELS.items():
            x_values = [float(row[descriptor]) for row in group]
            if len(set(x_values)) < 2:
                continue
            for response, response_label in RESPONSE_LABELS.items():
                y_values = [float(row[response]) for row in group]
                if len(set(y_values)) < 2:
                    continue
                rho = spearman_rank_correlation(x_values, y_values)
                ci_low, ci_high = fisher_z_interval(rho, len(group))
                seed_text = f"{descriptor}|{response}|{n_group}"
                seed = zlib.crc32(seed_text.encode("utf-8"))
                case_resampling_interval = (
                    case_resampling_spearman_interval(
                        x_values,
                        y_values,
                        n_case_resamples=n_case_resamples,
                        seed=seed,
                    )
                    if n_group != "all"
                    else None
                )
                rows.append(
                    {
                        "descriptor": descriptor,
                        "response": response,
                        "n_group": n_group,
                        "spearman_rho": rho,
                        "fisher_z_diagnostic_low": ci_low,
                        "fisher_z_diagnostic_high": ci_high,
                        "case_resampling_low": "" if case_resampling_interval is None else case_resampling_interval[0],
                        "case_resampling_high": "" if case_resampling_interval is None else case_resampling_interval[1],
                        "permutation_p": permutation_p_value(
                            x_values,
                            y_values,
                            rho,
                            n_permutations=n_permutations,
                            seed=seed,
                        ),
                        "n_permutations": n_permutations,
                        "n_case_resamples": 0 if case_resampling_interval is None else n_case_resamples,
                        "n_samples": len(group),
                        "description": f"{descriptor_label} vs {response_label}",
                    }
                )
    return rows


def write_difficulty_relationship_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIFFICULTY_RELATIONSHIP_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in DIFFICULTY_RELATIONSHIP_FIELDS})
