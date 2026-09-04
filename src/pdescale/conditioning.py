from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from scipy.sparse.linalg import eigsh

from pdescale.coefficients import coefficient_metrics
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator


CONDITIONING_FIELDS: tuple[str, ...] = (
    "coefficient_case",
    "family",
    "contrast_target",
    "contrast_observed",
    "face_average",
    "n",
    "n_unknowns",
    "lambda_min",
    "lambda_max",
    "condition_estimate",
)


def estimate_conditioning(
    grid: Grid2D,
    coefficient_case: str,
    *,
    tol: float = 1e-6,
    face_average: str = "arithmetic",
) -> dict[str, object]:
    A = assemble_operator(grid, coefficient_case, face_average=face_average)
    metrics = coefficient_metrics(grid, coefficient_case)
    lambda_min = float(eigsh(A, k=1, which="SA", return_eigenvectors=False, tol=tol, maxiter=20000)[0])
    lambda_max = float(eigsh(A, k=1, which="LA", return_eigenvectors=False, tol=tol, maxiter=20000)[0])
    return {
        "coefficient_case": coefficient_case,
        "family": metrics["family"],
        "contrast_target": float(metrics["contrast_target"]),
        "contrast_observed": float(metrics["contrast_observed"]),
        "face_average": face_average,
        "n": int(grid.nx),
        "n_unknowns": int(grid.num_interior),
        "lambda_min": lambda_min,
        "lambda_max": lambda_max,
        "condition_estimate": float(lambda_max / lambda_min),
    }


def run_conditioning_study(
    *,
    coefficient_cases: Sequence[str],
    sizes: Sequence[int],
    tol: float = 1e-6,
    face_average: str = "arithmetic",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in coefficient_cases:
        for n in sizes:
            rows.append(
                estimate_conditioning(
                    Grid2D(int(n), int(n)),
                    str(case),
                    tol=tol,
                    face_average=face_average,
                )
            )
    return rows


def write_conditioning_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONDITIONING_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in CONDITIONING_FIELDS})
