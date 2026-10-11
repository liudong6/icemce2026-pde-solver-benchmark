"""Plot the compact main-paper counterfactual from archived observations.

Run from any directory with Python, NumPy, SciPy, and Matplotlib installed:
    python tools/plot_compact_counterfactual.py

Only paper/figures/compact_counterfactual.{png,pdf} are written. The original
figure, experimental code, raw CSV, and analysis CSV are read-only. Error bars
span the minimum and maximum of five recorded setup-plus-solve times; they are
not confidence intervals. Motifs come directly from the experiment's function.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pdescale.counterfactual import matched_motif

RAW = ROOT / "results/raw/counterfactual/confirmation.csv"
SUMMARY = ROOT / "results/analysis/counterfactual/confirmation_summary.csv"
MOTIF_SOURCE = ROOT / "src/pdescale/counterfactual.py"
ORIGINAL_FIGURE = ROOT / "paper/figures/counterfactual_audit.png"
OUTPUT = ROOT / "paper/figures/compact_counterfactual"
SIZE_INCHES = (6.15, 2.1)
DPI = 300
CASES = (
    ("centered", "dipole_x", "Centered\nodd-x", 403),
    ("shift_x", "dipole_x", "Shifted by h\nodd-x", 677),
    ("centered", "random", "Centered\nrandom", 949),
)
METHODS = (
    ("jacobi", "Jacobi-PCG", "#2374A4", -0.17),
    ("amg0", "SA-PCG", "#CE6936", 0.17),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected(row: dict[str, str], variant: str, rhs: str) -> bool:
    return (
        int(row["n"]) == 192
        and float(row["contrast"]) == 1000.0
        and row["geometry"] == "disconnected"
        and row["average"] == "harmonic"
        and row["variant"] == variant
        and row["rhs"] == rhs
    )


def load_observations() -> list[dict[str, object]]:
    raw, summary = read_csv(RAW), read_csv(SUMMARY)
    observations = []
    for case_index, (variant, rhs, _, expected_jacobi) in enumerate(CASES):
        archived_summary = [r for r in summary if selected(r, variant, rhs)]
        assert len(archived_summary) == 1
        archived = archived_summary[0]
        for method, _, _, _ in METHODS:
            rows = [r for r in raw if selected(r, variant, rhs) and r["method"] == method]
            assert len(rows) == 5
            assert {int(r["repeat"]) for r in rows} == set(range(5))
            assert all(r["accepted"] == "True" and float(r["residual"]) <= 1e-8 for r in rows)
            times = [float(r["total"]) * 1000 for r in rows]
            median_ms = statistics.median(times)
            iterations = statistics.median(int(r["iterations"]) for r in rows)
            assert np.isclose(median_ms, float(archived[f"{method}_total"]) * 1000, rtol=0, atol=1e-9)
            assert iterations == float(archived[f"{method}_iterations"])
            if method == "jacobi":
                assert iterations == expected_jacobi
            observations.append({
                "case_index": case_index,
                "variant": variant,
                "rhs": rhs,
                "method": method,
                "median_ms": median_ms,
                "min_ms": min(times),
                "max_ms": max(times),
                "median_iterations": int(iterations),
                "repeats": len(rows),
            })
    return observations


def add_motif(fig: plt.Figure, geometry: str, rectangle: list[float]) -> None:
    motif = matched_motif(geometry)
    padded = np.pad(motif.astype(int), 1)
    perimeter = int(np.abs(np.diff(padded, axis=0)).sum() + np.abs(np.diff(padded, axis=1)).sum())
    assert motif.shape == (2, 8) and int(motif.sum()) == 12 and perimeter == 20
    ax = fig.add_axes(rectangle)
    ax.imshow(motif, cmap="Greys", vmin=0, vmax=1, interpolation="nearest", origin="upper")
    ax.set_xticks(np.arange(-0.5, 8, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 2, 1), minor=True)
    ax.grid(which="minor", color="#B3B3B3", linewidth=0.35)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#777777")
        spine.set_linewidth(0.4)


def plot(observations: list[dict[str, object]]) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
    })
    fig = plt.figure(figsize=SIZE_INCHES, facecolor="white")
    fig.text(0.018, 0.94, "(a) Motifs", fontsize=9.5, weight="bold")
    fig.text(0.018, 0.785, "Connected", fontsize=9.5)
    add_motif(fig, "connected", [0.018, 0.625, 0.195, 0.145])
    fig.text(0.018, 0.495, "Disconnected", fontsize=9.5)
    add_motif(fig, "disconnected", [0.018, 0.335, 0.195, 0.145])
    fig.text(0.018, 0.115, "Each: 12 high cells;\n20 interface edges", fontsize=9, linespacing=1.2)

    fig.text(0.25, 0.94, "(b) N = 192, c = 1000; harmonic faces", fontsize=9.5, weight="bold")
    ax = fig.add_axes([0.405, 0.23, 0.58, 0.57])
    for method, label, color, offset in METHODS:
        records = [r for r in observations if r["method"] == method]
        medians = np.array([r["median_ms"] for r in records], dtype=float)
        minima = np.array([r["min_ms"] for r in records], dtype=float)
        maxima = np.array([r["max_ms"] for r in records], dtype=float)
        positions = np.arange(3) + offset
        ax.barh(
            positions, medians, height=0.30, color=color, label=label,
            xerr=np.vstack((medians - minima, maxima - medians)),
            error_kw={"elinewidth": 0.7, "capsize": 2, "capthick": 0.7},
            zorder=3,
        )
        for row, position in zip(records, positions):
            ax.text(float(row["max_ms"]) + 2, position,
                    str(row["median_iterations"]), va="center", fontsize=9, zorder=4)
    ax.set_yticks(np.arange(3), [case[2] for case in CASES])
    ax.set_ylim(2.46, -0.48)
    ax.set_xlim(0, 215)
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.set_xlabel("Setup + solve (ms)", labelpad=2)
    ax.xaxis.grid(True, linewidth=0.4, color="#DDDDDD", zorder=0)
    ax.tick_params(axis="both", length=2.5, width=0.6, pad=3)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper right",
               bbox_to_anchor=(0.992, 0.912), ncol=2, frameon=False,
               fontsize=9, handlelength=1.25, handletextpad=0.4,
               columnspacing=1.2, borderaxespad=0)
    # A fixed canvas, not bbox_inches="tight", preserves the requested dimensions.
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=DPI,
                metadata={"Software": "tools/plot_compact_counterfactual.py"})
    fig.savefig(OUTPUT.with_suffix(".pdf"),
                metadata={"Creator": "tools/plot_compact_counterfactual.py",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


def main() -> None:
    protected = (RAW, SUMMARY, MOTIF_SOURCE, ORIGINAL_FIGURE)
    before = {str(path.relative_to(ROOT)): sha256(path) for path in protected}
    observations = load_observations()
    plot(observations)
    after = {str(path.relative_to(ROOT)): sha256(path) for path in protected}
    assert before == after, "A protected input changed while plotting."
    print(json.dumps({
        "figure_inches": SIZE_INCHES,
        "png_dpi": DPI,
        "outputs": [str(OUTPUT.with_suffix(ext)) for ext in (".png", ".pdf")],
        "error_bars": "minimum to maximum over five repeats",
        "annotations": "median iteration counts",
        "input_sha256": before,
        "observations": observations,
    }, indent=2))


if __name__ == "__main__":
    main()
