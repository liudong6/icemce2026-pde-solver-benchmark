from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

import numpy as np

from pdescale.operators import face_coefficient

INTERFACE_VERIFICATION_FIELDS: tuple[str, ...] = (
    "n",
    "face_average",
    "k_left",
    "k_right",
    "l2_error",
    "max_error",
    "interface_flux",
    "exact_flux",
    "flux_error_abs",
    "left_flux",
    "right_flux",
    "flux_mismatch_abs",
)


def exact_layer_solution(x: np.ndarray, *, k_left: float, k_right: float) -> np.ndarray:
    if k_left <= 0.0 or k_right <= 0.0:
        raise ValueError("layer conductivities must be positive")
    conductance = 1.0 / (0.5 / k_left + 0.5 / k_right)
    interface_value = conductance * 0.5 / k_left
    return np.where(
        x <= 0.5,
        conductance * x / k_left,
        interface_value + conductance * (x - 0.5) / k_right,
    )


def exact_layer_flux(*, k_left: float, k_right: float) -> float:
    conductance = 1.0 / (0.5 / k_left + 0.5 / k_right)
    return -conductance


def solve_layer_interface(
    n: int,
    *,
    k_left: float = 1.0,
    k_right: float = 100.0,
    face_average: str = "harmonic",
) -> dict[str, object]:
    if n < 4:
        raise ValueError("n must be at least 4")
    if n % 2 != 0:
        raise ValueError("use an even n so the material interface lies midway between grid nodes")

    x = np.linspace(0.0, 1.0, n)
    h = 1.0 / (n - 1)
    k_nodes = np.where(x < 0.5, k_left, k_right)
    num_interior = n - 2
    A = np.zeros((num_interior, num_interior), dtype=float)
    b = np.zeros(num_interior, dtype=float)

    u_left = 0.0
    u_right = 1.0
    for i in range(1, n - 1):
        row = i - 1
        kw = face_coefficient(float(k_nodes[i]), float(k_nodes[i - 1]), face_average)
        ke = face_coefficient(float(k_nodes[i]), float(k_nodes[i + 1]), face_average)
        A[row, row] = (kw + ke) / h**2
        if i - 1 >= 1:
            A[row, row - 1] = -kw / h**2
        else:
            b[row] += kw * u_left / h**2
        if i + 1 <= n - 2:
            A[row, row + 1] = -ke / h**2
        else:
            b[row] += ke * u_right / h**2

    u = np.empty(n, dtype=float)
    u[0] = u_left
    u[-1] = u_right
    u[1:-1] = np.linalg.solve(A, b)

    u_exact = exact_layer_solution(x, k_left=k_left, k_right=k_right)
    error = u - u_exact
    l2_error = float(np.sqrt(np.mean(error**2)))
    max_error = float(np.max(np.abs(error)))

    crossing = int(np.max(np.where(x < 0.5)[0]))
    interface_k = face_coefficient(float(k_nodes[crossing]), float(k_nodes[crossing + 1]), face_average)
    interface_flux = -interface_k * (u[crossing + 1] - u[crossing]) / h
    left_flux = -k_left * (u[crossing] - u[crossing - 1]) / h
    right_flux = -k_right * (u[crossing + 2] - u[crossing + 1]) / h
    exact_flux = exact_layer_flux(k_left=k_left, k_right=k_right)

    return {
        "n": int(n),
        "face_average": face_average,
        "k_left": float(k_left),
        "k_right": float(k_right),
        "l2_error": l2_error,
        "max_error": max_error,
        "interface_flux": float(interface_flux),
        "exact_flux": float(exact_flux),
        "flux_error_abs": float(abs(interface_flux - exact_flux)),
        "left_flux": float(left_flux),
        "right_flux": float(right_flux),
        "flux_mismatch_abs": float(abs(left_flux - right_flux)),
    }


def run_interface_verification(
    *,
    sizes: Sequence[int],
    face_averages: Sequence[str] = ("arithmetic", "harmonic"),
    k_left: float = 1.0,
    k_right: float = 100.0,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n in sizes:
        for face_average in face_averages:
            rows.append(
                solve_layer_interface(
                    int(n),
                    k_left=k_left,
                    k_right=k_right,
                    face_average=str(face_average),
                )
            )
    return rows


def write_interface_verification_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INTERFACE_VERIFICATION_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in INTERFACE_VERIFICATION_FIELDS})
