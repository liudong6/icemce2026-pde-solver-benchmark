from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import NullFormatter

from pdescale.convergence import estimate_order
from pdescale.difficulty_analysis import DESCRIPTOR_LABELS, RESPONSE_LABELS

FIGURE_DPI = 300

plt.rcParams.update(
    {
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.labelsize": 8.8,
        "xtick.labelsize": 7.8,
        "ytick.labelsize": 7.8,
        "legend.fontsize": 7.5,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.5,
        "lines.markersize": 4.2,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    }
)


def _load_rows(csv_path: str | Path) -> list[dict[str, str]]:
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _pretty_case_name(name: str) -> str:
    labels = {
        "smooth_constant": "Constant coefficient",
        "smooth_variable": "Smooth variable coefficient",
        "smooth_variable_solver": "Smooth variable",
        "high_contrast_solver": "High contrast",
    }
    return labels.get(name, name.replace("_solver", "").replace("_", " ").title())


def _pretty_method_name(name: str) -> str:
    labels = {
        "cg": "CG",
        "jacobi-pcg": "Jacobi-PCG",
        "amg-pcg": "AMG-PCG",
        "direct": "Direct",
    }
    return labels.get(name, name.upper())


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def plot_convergence_l2(csv_path: str | Path, output_path: str | Path) -> None:
    rows = _load_rows(csv_path)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_name"]].append(row)

    fig, ax = plt.subplots(figsize=(6.0, 4.2), dpi=FIGURE_DPI)
    for case_name, case_rows in sorted(grouped.items()):
        case_rows = sorted(case_rows, key=lambda r: float(r["h"]), reverse=True)
        h = [float(r["h"]) for r in case_rows]
        l2 = [float(r["l2_error"]) for r in case_rows]
        order = estimate_order(h, l2)
        ax.loglog(h, l2, marker="o", linewidth=1.8, label=f"{_pretty_case_name(case_name)}, p={order:.2f}")

    ax.invert_xaxis()
    ax.set_xlabel("Grid spacing h")
    ax.set_ylabel("Discrete L2 error")
    ax.set_title("Manufactured-solution convergence")
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def _plot_solver_metric(
    csv_path: str | Path,
    output_path: str | Path,
    *,
    metric: str,
    ylabel: str,
    title: str,
    include_zero: bool = False,
) -> None:
    rows = _load_rows(csv_path)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        value = float(row[metric])
        if value > 0.0 or include_zero:
            grouped[(row["case"], row["method"])].append(row)
    if not grouped:
        raise ValueError(f"no rows available for solver metric: {metric}")

    fig, ax = plt.subplots(figsize=(7.0, 4.3), dpi=FIGURE_DPI)
    for (case_name, method), case_rows in sorted(grouped.items()):
        case_rows = sorted(case_rows, key=lambda r: int(r["n_unknowns"]))
        x = [int(r["n_unknowns"]) for r in case_rows]
        y = [float(r[metric]) for r in case_rows]
        label = f"{_pretty_case_name(case_name)} / {_pretty_method_name(method)}"
        ax.loglog(x, y, marker="o", linewidth=1.7, label=label)

    ax.set_xlabel("Interior unknowns")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(frameon=False, fontsize=7.5, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_solver_runtime(csv_path: str | Path, output_path: str | Path) -> None:
    _plot_solver_metric(
        csv_path,
        output_path,
        metric="total_seconds",
        ylabel="Setup + solve time (s)",
        title="Solver runtime scaling",
    )


def plot_solver_iterations(csv_path: str | Path, output_path: str | Path) -> None:
    _plot_solver_metric(
        csv_path,
        output_path,
        metric="iterations",
        ylabel="CG iterations",
        title="Preconditioner iteration scaling",
    )


def _scaling_label(row: dict[str, str]) -> str:
    method = row["method"]
    if method == "numpy-vectorized":
        return "NumPy"
    if method == "numba-serial":
        return "Numba serial"
    if method == "numba-parallel":
        return f"Numba parallel ({row['threads']} threads)"
    return method


def plot_cpu_scaling(csv_path: str | Path, output_path: str | Path) -> None:
    rows = _load_rows(csv_path)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_scaling_label(row)].append(row)
    if not grouped:
        raise ValueError("no rows available for CPU scaling plot")

    fig, ax = plt.subplots(figsize=(7.0, 4.3), dpi=FIGURE_DPI)
    for label, label_rows in sorted(grouped.items()):
        label_rows = sorted(label_rows, key=lambda r: int(r["n_unknowns"]))
        x = [int(r["n_unknowns"]) for r in label_rows]
        y = [float(r["estimated_gbytes_per_second"]) for r in label_rows]
        ax.semilogx(x, y, marker="o", linewidth=1.7, label=label)

    ax.set_yscale("log")
    ax.set_xlabel("Interior unknowns")
    ax.set_ylabel("Estimated stencil bandwidth (GB/s)")
    ax.set_title("CPU stencil throughput scaling")
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.legend(frameon=False, fontsize=7.5, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_gpu_crossover(csv_path: str | Path, output_path: str | Path) -> None:
    rows = [row for row in _load_rows(csv_path) if row["method"] == "cuda-kernel"]
    if not rows:
        raise ValueError("no CUDA rows available for GPU crossover plot")
    rows = sorted(rows, key=lambda r: int(r["n_unknowns"]))

    x = [int(row["n_unknowns"]) for row in rows]
    speedup = [float(row["speedup_vs_cpu"]) for row in rows]

    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=FIGURE_DPI)
    ax.semilogx(x, speedup, marker="o", linewidth=1.8, label="CUDA kernel / CPU Numba")
    ax.axhline(2.0, color="0.35", linestyle="--", linewidth=1.0, label="2x inclusion threshold")
    ax.set_xlabel("Interior unknowns")
    ax.set_ylabel("Kernel-only speedup vs CPU")
    ax.set_title("CUDA Jacobi stencil crossover")
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.legend(frameon=False, fontsize=8.0)
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_solver_decision_map(csv_path: str | Path, output_path: str | Path) -> None:
    rows = [row for row in _load_rows(csv_path) if _as_bool(row["is_best"])]
    if not rows:
        raise ValueError("no best-solver rows available for decision map")

    method_order = ["cg", "jacobi-pcg", "amg-pcg", "direct"]
    methods = [method for method in method_order if any(row["method"] == method for row in rows)]
    methods.extend(sorted({row["method"] for row in rows} - set(methods)))
    method_to_value = {method: index for index, method in enumerate(methods)}

    x_values = sorted({float(row["contrast_target"]) for row in rows})
    y_keys = sorted({(row["family"], int(row["n"])) for row in rows}, key=lambda item: (item[0], item[1]))
    matrix = np.full((len(y_keys), len(x_values)), np.nan)

    for row in rows:
        y_index = y_keys.index((row["family"], int(row["n"])))
        x_index = x_values.index(float(row["contrast_target"]))
        matrix[y_index, x_index] = method_to_value[row["method"]]

    colors = plt.get_cmap("tab10").colors[: max(len(methods), 1)]
    cmap = ListedColormap(colors).with_extremes(bad="white")

    fig_width = max(6.2, 1.0 + 0.7 * len(x_values))
    fig_height = max(4.0, 1.4 + 0.36 * len(y_keys))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=FIGURE_DPI)
    ax.imshow(np.ma.masked_invalid(matrix), aspect="auto", cmap=cmap, vmin=0, vmax=max(len(methods) - 1, 1))
    ax.set_xticks(range(len(x_values)), [f"{value:g}" for value in x_values])
    ax.set_yticks(range(len(y_keys)), [f"{family}, N={n}" for family, n in y_keys])
    ax.set_xlabel("Target coefficient contrast")
    ax.set_ylabel("Coefficient family and grid")
    ax.set_title("Fastest solver by setup-plus-solve time")
    ax.set_xticks(np.arange(-0.5, len(x_values), 1.0), minor=True)
    ax.set_yticks(np.arange(-0.5, len(y_keys), 1.0), minor=True)
    ax.grid(which="minor", color="0.85", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    handles = [
        Patch(facecolor=colors[index], edgecolor="none", label=_pretty_method_name(method))
        for index, method in enumerate(methods)
    ]
    ax.legend(handles=handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_conditioning(csv_path: str | Path, output_path: str | Path) -> None:
    rows = _load_rows(csv_path)
    if not rows:
        raise ValueError("no rows available for conditioning plot")

    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["family"], int(row["n"]))].append(row)

    fig, ax = plt.subplots(figsize=(6.4, 4.1), dpi=FIGURE_DPI)
    for (family, n), group_rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        group_rows = sorted(group_rows, key=lambda row: float(row["contrast_target"]))
        x = [float(row["contrast_target"]) for row in group_rows]
        y = [float(row["condition_estimate"]) for row in group_rows]
        ax.loglog(x, y, marker="o", linewidth=1.7, label=f"{family}, N={n}")

    ax.set_xlabel("Target coefficient contrast")
    ax.set_ylabel("Estimated condition number")
    ax.set_title("Conditioning response to coefficient difficulty")
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(frameon=False, fontsize=7.5, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_difficulty_relationships(csv_path: str | Path, output_path: str | Path) -> None:
    rows = _load_rows(csv_path)
    pooled_rows = [row for row in rows if row["n_group"] == "all"]
    fixed_rows = [row for row in rows if row["n_group"] != "all"]
    if not pooled_rows:
        raise ValueError("no all-grid rows available for difficulty relationship plot")

    descriptor_order = [
        "contrast_observed",
        "grad_logk_inf",
        "total_variation_proxy",
        "condition_estimate",
    ]
    descriptors = [
        descriptor
        for descriptor in descriptor_order
        if any(row["descriptor"] == descriptor for row in pooled_rows)
    ]
    if not descriptors:
        raise ValueError("no descriptor rows available for difficulty relationship plot")

    pooled_values = {
        (row["descriptor"], row["response"]): float(row["spearman_rho"])
        for row in pooled_rows
    }
    fixed_values: dict[tuple[str, str], float] = {}
    for descriptor in descriptors:
        for response in ("cg_iterations", "selected_speedup_vs_cg"):
            values = [
                float(row["spearman_rho"])
                for row in fixed_rows
                if row["descriptor"] == descriptor and row["response"] == response
            ]
            if values:
                bounded = np.clip(np.asarray(values, dtype=float), -0.999999, 0.999999)
                fixed_values[(descriptor, response)] = float(np.tanh(np.mean(np.arctanh(bounded))))

    x = np.arange(len(descriptors), dtype=float)
    width = 0.22
    series = [
        ("cg_iterations", "pooled", pooled_values, "#2a6fbb"),
        ("cg_iterations", "fixed-N mean", fixed_values, "#78a8d8"),
        ("selected_speedup_vs_cg", "pooled", pooled_values, "#c96b2c"),
        ("selected_speedup_vs_cg", "fixed-N mean", fixed_values, "#e0a06c"),
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=FIGURE_DPI)
    for index, (response, group_label, value_map, color) in enumerate(series):
        offset = (index - 1.5) * width
        y = [value_map.get((descriptor, response), np.nan) for descriptor in descriptors]
        ax.bar(
            x + offset,
            y,
            width=width,
            color=color,
            label=f"{RESPONSE_LABELS.get(response, response)}, {group_label}",
        )

    short_labels = {
        "contrast_observed": "$C_k$",
        "grad_logk_inf": "$G_k^{(h)}$",
        "total_variation_proxy": "$V_k$",
        "condition_estimate": "$\\kappa(A)$",
    }
    ax.axhline(0.0, color="0.35", linewidth=0.8)
    ax.set_ylim(-1.0, 1.0)
    ax.set_xticks(x, [short_labels.get(item, DESCRIPTOR_LABELS.get(item, item)) for item in descriptors])
    ax.set_ylabel("Spearman rank correlation")
    ax.set_title("Pooled and fixed-grid descriptor correlations")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.7)
    ax.legend(frameon=False, fontsize=7.2, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_timing_stability(csv_path: str | Path, output_path: str | Path) -> None:
    rows = _load_rows(csv_path)
    if not rows:
        raise ValueError("no rows available for timing stability plot")

    preferred = [
        ("constant", 64),
        ("smooth_c30", 256),
        ("inclusion_c100", 256),
        ("layered_c100", 256),
        ("checkerboard_c100", 256),
    ]
    selected: list[dict[str, str]] = []
    for case, n in preferred:
        row = next(
            (
                item
                for item in rows
                if item["coefficient_case"] == case and int(float(item["n"])) == n
            ),
            None,
        )
        if row is not None:
            selected.append(row)
    if not selected:
        selected = sorted(rows, key=lambda item: (int(float(item["n"])), item["coefficient_case"]))

    labels = [f"{row['coefficient_case'].replace('_', ' ')}\nN={int(float(row['n']))}" for row in selected]
    speedups = [float(row["median_speedup_vs_cg"]) for row in selected]
    rel_iqr = [float(row["selected_rel_iqr"]) for row in selected]
    stable = [_as_bool(row["decision_stable"]) for row in selected]
    colors = ["#2a6fbb" if item else "#c96b2c" for item in stable]
    x = np.arange(len(selected), dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=FIGURE_DPI)
    ax.bar(x, speedups, color=colors, width=0.62)
    for index, (speedup, variability) in enumerate(zip(speedups, rel_iqr)):
        ax.text(
            index,
            speedup,
            f"IQR {100.0 * variability:.1f}%",
            ha="center",
            va="bottom",
            fontsize=7.5,
        )
    ax.set_xticks(x, labels)
    ax.set_ylabel("Median selected speedup vs CG")
    ax.set_title("Repeated timing stability of solver decisions")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.7)
    handles = [
        Patch(facecolor="#2a6fbb", edgecolor="none", label="stable median/vote"),
        Patch(facecolor="#c96b2c", edgecolor="none", label="variable decision"),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8.0)
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def plot_hardware_crossover_model(
    gpu_csv_path: str | Path,
    model_csv_path: str | Path,
    output_path: str | Path,
) -> None:
    gpu_rows = _load_rows(gpu_csv_path)
    model_rows = _load_rows(model_csv_path)
    if not gpu_rows or not model_rows:
        raise ValueError("GPU observations and model rows are required")

    cpu_model = next(row for row in model_rows if row["model_component"] == "cpu")
    gpu_model = next(row for row in model_rows if row["model_component"] == "cuda")
    crossover = next(row for row in model_rows if row["model_component"] == "crossover")

    fig, ax = plt.subplots(figsize=(6.4, 4.1), dpi=FIGURE_DPI)
    for method, label in [
        ("numba-parallel-cpu", "CPU Numba observed"),
        ("cuda-kernel", "CUDA observed"),
    ]:
        rows = sorted([row for row in gpu_rows if row["method"] == method], key=lambda row: int(row["n_unknowns"]))
        x = np.asarray([float(row["n_unknowns"]) for row in rows])
        y = np.asarray([float(row["seconds_per_step"]) for row in rows])
        ax.loglog(x, y, marker="o", linestyle="", label=label)

    all_x = np.asarray([float(row["n_unknowns"]) for row in gpu_rows])
    model_x = np.geomspace(max(float(np.min(all_x)), 1.0), float(np.max(all_x)), 160)
    for model, label in [(cpu_model, "CPU fitted"), (gpu_model, "CUDA fitted")]:
        alpha = float(model["alpha_seconds"])
        beta = float(model["beta_seconds_per_unknown"])
        model_y = alpha + beta * model_x
        positive = model_y > 0.0
        if np.any(positive):
            ax.loglog(model_x[positive], model_y[positive], linewidth=1.6, label=label)

    crossover_n = float(crossover["crossover_n_unknowns"])
    if crossover_n > 0.0 and np.isfinite(crossover_n):
        ax.axvline(crossover_n, color="0.35", linestyle="--", linewidth=1.0, label="fitted crossover")

    ax.set_xlabel("Interior unknowns")
    ax.set_ylabel("Seconds per Jacobi step")
    ax.set_title("CPU/CUDA kernel crossover model")
    ax.grid(True, which="both", linestyle=":", linewidth=0.7)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
