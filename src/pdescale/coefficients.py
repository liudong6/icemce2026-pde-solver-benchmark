from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np

from pdescale.grid import Grid2D


COEFFICIENT_METRIC_FIELDS: tuple[str, ...] = (
    "coefficient_case",
    "family",
    "contrast_target",
    "contrast_observed",
    "min_k",
    "max_k",
    "mean_k",
    "grad_logk_inf",
    "total_variation_proxy",
    "n",
    "n_unknowns",
)


@dataclass(frozen=True)
class CoefficientSpec:
    family: str
    contrast: float = 1.0
    label: str | None = None

    def __post_init__(self) -> None:
        if self.family not in {"constant", "smooth", "layered", "inclusion", "checkerboard"}:
            raise ValueError(f"unknown coefficient family: {self.family}")
        if self.contrast < 1.0:
            raise ValueError("coefficient contrast must be at least one")


def parse_coefficient_case(case: str | CoefficientSpec) -> CoefficientSpec:
    if isinstance(case, CoefficientSpec):
        return case

    legacy = {
        "constant": CoefficientSpec("constant", 1.0, "constant"),
        "smooth_constant": CoefficientSpec("constant", 1.0, "smooth_constant"),
        "smooth": CoefficientSpec("smooth", 3.0, "smooth"),
        "smooth_variable": CoefficientSpec("smooth", 3.0, "smooth_variable"),
        "high_contrast": CoefficientSpec("inclusion", 100.0, "high_contrast"),
    }
    if case in legacy:
        return legacy[case]

    match = re.fullmatch(
        r"(constant|smooth|layered|inclusion|checkerboard)_c([0-9]+(?:[.p][0-9]+)?)",
        case,
    )
    if match is None:
        raise ValueError(f"unknown coefficient case: {case}")
    family, contrast_text = match.groups()
    contrast = float(contrast_text.replace("p", "."))
    return CoefficientSpec(family, contrast, case)


def coefficient_field(
    x: np.ndarray,
    y: np.ndarray,
    case: str | CoefficientSpec,
    *,
    inclusion_radius: float = 0.15,
    checkerboard_blocks: int = 8,
) -> np.ndarray:
    spec = parse_coefficient_case(case)
    contrast = float(spec.contrast)

    if spec.family == "constant":
        return np.ones_like(x, dtype=float)

    if spec.family == "smooth":
        amplitude = (contrast - 1.0) / (contrast + 1.0)
        return 1.0 + amplitude * np.sin(2.0 * np.pi * x) * np.sin(2.0 * np.pi * y)

    if spec.family == "layered":
        return np.where(y >= 0.5, contrast, 1.0).astype(float)

    if spec.family == "inclusion":
        radius2 = (x - 0.5) ** 2 + (y - 0.5) ** 2
        return np.where(radius2 < inclusion_radius**2, contrast, 1.0).astype(float)

    if spec.family == "checkerboard":
        clipped_x = np.minimum(x, np.nextafter(1.0, 0.0))
        clipped_y = np.minimum(y, np.nextafter(1.0, 0.0))
        ix = np.floor(checkerboard_blocks * clipped_x).astype(int)
        iy = np.floor(checkerboard_blocks * clipped_y).astype(int)
        high = (ix + iy) % 2 == 0
        return np.where(high, contrast, 1.0).astype(float)

    raise ValueError(f"unknown coefficient family: {spec.family}")


def coefficient_metrics(grid: Grid2D, case: str | CoefficientSpec) -> dict[str, Any]:
    spec = parse_coefficient_case(case)
    label = spec.label or f"{spec.family}_c{spec.contrast:g}"
    k = coefficient_field(grid.x, grid.y, spec)
    log_k = np.log(k)
    # This is a grid-level sharpness descriptor; for discontinuous fields it
    # scales with h and should be interpreted at fixed resolution.
    gx, gy = np.gradient(log_k, grid.hx, grid.hy, edge_order=1)
    total_variation = (
        float(np.sum(np.abs(np.diff(k, axis=0)))) / max(k.shape[0] - 1, 1)
        + float(np.sum(np.abs(np.diff(k, axis=1)))) / max(k.shape[1] - 1, 1)
    )

    min_k = float(np.min(k))
    max_k = float(np.max(k))
    return {
        "coefficient_case": label,
        "family": spec.family,
        "contrast_target": float(spec.contrast),
        "contrast_observed": float(max_k / min_k),
        "min_k": min_k,
        "max_k": max_k,
        "mean_k": float(np.mean(k)),
        "grad_logk_inf": float(np.max(np.hypot(gx, gy))),
        "total_variation_proxy": total_variation,
        "n": int(grid.nx),
        "n_unknowns": int(grid.num_interior),
    }
