from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from pdescale.convergence import estimate_order


DIFFICULTY_DESCRIPTOR_LABELS = {
    "contrast_observed": "$C_k$ contrast",
    "grad_logk_inf": "$G_k^{(h)}$ log-gradient",
    "total_variation_proxy": "$V_k$ TV proxy",
    "condition_estimate": "$\\kappa(A)$ proxy",
}

DIFFICULTY_RESPONSE_LABELS = {
    "cg_iterations": "CG iterations",
    "selected_speedup_vs_cg": "Selected speedup",
}


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sci(value: float, precision: int = 2) -> str:
    if value == 0.0:
        return "$0$"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10.0**exponent)
    return rf"${mantissa:.{precision}f}\times10^{{{exponent}}}$"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")


def method_label(method: str, threads: str | None = None) -> str:
    labels = {
        "cg": "CG",
        "jacobi-pcg": "Jacobi-PCG",
        "amg-pcg": "AMG-PCG",
        "numpy-vectorized": "NumPy",
        "numba-serial": "Numba serial",
        "cuda-kernel": "CUDA kernel",
        "numba-parallel-cpu": "CPU Numba",
        "linear_cpu_vs_cuda": "Illustrative fitted crossover",
    }
    if method == "numba-parallel":
        return f"Numba parallel, {threads} threads"
    return labels.get(method, method)


def bool_value(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def convergence_table(rows: Iterable[dict[str, str]]) -> str:
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_case.setdefault(row["case_name"], []).append(row)

    display_order = [
        ("smooth_constant", "Constant coefficient"),
        ("smooth_variable", "Smooth variable coefficient"),
    ]
    body: list[str] = []
    for case_name, label in display_order:
        case_rows = sorted(by_case[case_name], key=lambda row: int(row["n"]))
        hs = [float(row["h"]) for row in case_rows]
        l2_errors = [float(row["l2_error"]) for row in case_rows]
        linf_errors = [float(row["linf_error"]) for row in case_rows]
        finest = case_rows[-1]
        body.append(
            " & ".join(
                [
                    label,
                    f"{estimate_order(hs, l2_errors):.2f}",
                    f"{estimate_order(hs, linf_errors):.2f}",
                    sci(float(finest["l2_error"])),
                    sci(float(finest["residual_norm"])),
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Manufactured-solution convergence for the finite-difference discretisation.}",
            r"\label{tab:convergence}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{lrrrr}",
            r"\toprule",
            r"Case & $p_{L^2}$ & $p_{\infty}$ & Finest $L^2$ & Residual \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def solver_table(rows: Iterable[dict[str, str]]) -> str:
    rows_256 = [row for row in rows if int(row["n"]) == 256]
    case_labels = {
        "smooth_variable_solver": "Smooth variable",
        "high_contrast_solver": "High contrast",
    }
    methods = ["cg", "jacobi-pcg", "amg-pcg"]
    body: list[str] = []
    for case_name, case_label in case_labels.items():
        for method in methods:
            row = next(
                item
                for item in rows_256
                if item["case"] == case_name and item["method"] == method
            )
            body.append(
                " & ".join(
                    [
                        case_label,
                        method_label(method),
                        row["iterations"],
                        f"{float(row['total_seconds']):.3f}",
                        sci(float(row["residual_norm"])),
                    ]
                )
                + r" \\"
            )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Solver comparison at $N=256$ grid points in each direction.}",
            r"\label{tab:solver}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{llrrr}",
            r"\toprule",
            r"Case & Method & Iter. & Time (s) & Rel. residual \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def performance_table(cpu_rows: Iterable[dict[str, str]], gpu_rows: Iterable[dict[str, str]]) -> str:
    cpu_by_key = {
        (row["method"], row["threads"]): row
        for row in cpu_rows
        if int(row["n"]) == 2048
    }
    cpu_selected = [
        ("CPU stencil", "numpy-vectorized", "1"),
        ("CPU stencil", "numba-serial", "1"),
        ("CPU stencil", "numba-parallel", "4"),
    ]

    body: list[str] = []
    for experiment, method, threads in cpu_selected:
        row = cpu_by_key[(method, threads)]
        body.append(
            " & ".join(
                [
                    experiment,
                    method_label(method, threads),
                    row["n"],
                    f"{float(row['seconds_per_apply']):.4g} s/apply",
                    f"{float(row['estimated_gbytes_per_second']):.2f} GB/s",
                ]
            )
            + r" \\"
        )

    gpu_selected = [
        row for row in gpu_rows if row["method"] == "cuda-kernel" and int(row["n"]) in {2048, 4096}
    ]
    for row in sorted(gpu_selected, key=lambda item: int(item["n"])):
        body.append(
            " & ".join(
                [
                    "GPU crossover",
                    method_label(row["method"]),
                    row["n"],
                    f"{sci(float(row['seconds_per_step']))} s/step",
                    rf"${float(row['speedup_vs_cpu']):.2f}\times$ vs CPU",
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            (
                r"\caption{Representative stencil-throughput measurements. CPU entries use the "
                r"variable-coefficient operator at $N=2048$; CUDA entries use a repeated Jacobi "
                r"kernel-only benchmark.}"
            ),
            r"\label{tab:performance}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{llrrr}",
            r"\toprule",
            r"Experiment & Method & $N$ & Time & Throughput / speedup \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def coefficient_difficulty_table(
    decision_rows: Iterable[dict[str, str]],
    conditioning_rows: Iterable[dict[str, str]],
) -> str:
    decision_rows = list(decision_rows)
    conditioning_rows = list(conditioning_rows)
    max_conditioning_n = max(int(item["n"]) for item in conditioning_rows)
    condition_by_case = {
        row["coefficient_case"]: row
        for row in conditioning_rows
        if int(row["n"]) == max_conditioning_n
    }
    metrics_by_case: dict[str, dict[str, str]] = {}
    for row in decision_rows:
        if int(row["n"]) == 64:
            metrics_by_case[row["coefficient_case"]] = row

    selected: list[dict[str, str]] = []
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in metrics_by_case.values():
        by_family[row["family"]].append(row)
    for family in ["constant", "smooth", "inclusion", "layered", "checkerboard"]:
        candidates = by_family.get(family, [])
        if candidates:
            selected.append(max(candidates, key=lambda row: float(row["contrast_target"])))

    body: list[str] = []
    for row in selected:
        condition = condition_by_case.get(row["coefficient_case"])
        condition_text = (
            sci(float(condition["condition_estimate"]), precision=2) if condition is not None else "-"
        )
        body.append(
            " & ".join(
                [
                    row["coefficient_case"].replace("_", r"\_"),
                    row["family"].title(),
                    f"{float(row['contrast_observed']):.1f}",
                    f"{float(row['grad_logk_inf']):.2f}",
                    f"{float(row['total_variation_proxy']):.2f}",
                    condition_text,
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Representative coefficient-difficulty descriptors. Metrics use $N=64$ for the discrete descriptors; $\kappa(A)$ is the largest available spectral estimate, here $N=128$.}",
            r"\label{tab:difficulty}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{llrrrr}",
            r"\toprule",
            r"Case & Family & $C_k$ & $G_k^{(h)}$ & TV proxy & $\kappa(A)$ \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def decision_summary_table(rows: Iterable[dict[str, str]]) -> str:
    best_rows = [row for row in rows if bool_value(row["is_best"])]
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in best_rows:
        grouped[int(row["n"])].append(row)

    body: list[str] = []
    for n in sorted(grouped):
        group = grouped[n]
        counts = Counter(row["best_method"] for row in group)
        speedups = sorted(float(row["speedup_vs_cg"]) for row in group)
        median = speedups[len(speedups) // 2] if speedups else 0.0
        if len(speedups) % 2 == 0 and speedups:
            median = 0.5 * (speedups[len(speedups) // 2 - 1] + speedups[len(speedups) // 2])
        body.append(
            " & ".join(
                [
                    str(n),
                    str(len(group)),
                    str(counts.get("cg", 0)),
                    str(counts.get("jacobi-pcg", 0)),
                    str(counts.get("amg-pcg", 0)),
                    f"{median:.2f}",
                    f"{max(speedups):.2f}" if speedups else "0.00",
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Setup-inclusive single-solve decision summary over the coefficient-family grid. Counts report the fastest converged method by setup-plus-solve time from one timing pass per cell.}",
            r"\label{tab:decision-summary}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{rrrrrrr}",
            r"\toprule",
            r"$N$ & Cases & CG & Jacobi-PCG & AMG-PCG & Median speedup vs CG & Max speedup vs CG \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def _rho_text(value: float) -> str:
    return f"{value:.2f}"


def _fixed_grid_rho_text(
    rows: list[dict[str, str]],
    descriptor: str,
    response: str,
) -> str:
    values = [
        float(row["spearman_rho"])
        for row in rows
        if row["descriptor"] == descriptor
        and row["response"] == response
        and row["n_group"] != "all"
    ]
    if not values:
        return "-"
    values = sorted(values)
    midpoint = len(values) // 2
    if len(values) % 2 == 0:
        median_value = 0.5 * (values[midpoint - 1] + values[midpoint])
    else:
        median_value = values[midpoint]
    min_value = values[0]
    max_value = values[-1]
    if max_value - min_value < 0.005:
        return _rho_text(median_value)
    return f"{median_value:.2f} ({min_value:.2f}-{max_value:.2f})"


def difficulty_relationship_table(rows: Iterable[dict[str, str]]) -> str:
    rows = list(rows)
    all_rows = [row for row in rows if row["n_group"] == "all"]
    by_descriptor_response = {
        (row["descriptor"], row["response"]): row
        for row in all_rows
    }
    descriptors = [
        "contrast_observed",
        "grad_logk_inf",
        "total_variation_proxy",
        "condition_estimate",
    ]
    responses = ["cg_iterations", "selected_speedup_vs_cg"]

    body: list[str] = []
    for descriptor in descriptors:
        if not any((descriptor, response) in by_descriptor_response for response in responses):
            continue
        cg = by_descriptor_response.get((descriptor, "cg_iterations"))
        speedup = by_descriptor_response.get((descriptor, "selected_speedup_vs_cg"))
        body.append(
            " & ".join(
                [
                    DIFFICULTY_DESCRIPTOR_LABELS[descriptor],
                    _rho_text(float(cg["spearman_rho"])) if cg is not None else "-",
                    _fixed_grid_rho_text(rows, descriptor, "cg_iterations"),
                    _rho_text(float(speedup["spearman_rho"])) if speedup is not None else "-",
                    _fixed_grid_rho_text(rows, descriptor, "selected_speedup_vs_cg"),
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Descriptive Spearman rank correlations linking coefficient-difficulty descriptors to solver behaviour. Pooled columns use all 39 case-size entries and are not treated as independent population samples; fixed-$N$ columns summarise the stratum-specific rank coefficients by median and, when they differ, range. Raw stratum values and case-resampling uncertainty intervals are archived in the supplementary CSV.}",
            r"\label{tab:difficulty-relationships}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{lrrrr}",
            r"\toprule",
            r"Descriptor & CG pooled & CG fixed-$N$ & Speedup pooled & Speedup fixed-$N$ \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def interface_verification_table(rows: Iterable[dict[str, str]]) -> str:
    grouped: dict[tuple[int, str], dict[str, str]] = {}
    for row in rows:
        grouped[(int(row["n"]), row["face_average"])] = row

    body: list[str] = []
    for n in sorted({key[0] for key in grouped}):
        arithmetic = grouped[(n, "arithmetic")]
        harmonic = grouped[(n, "harmonic")]
        body.append(
            " & ".join(
                [
                    str(n),
                    sci(float(arithmetic["l2_error"]), precision=2),
                    sci(float(harmonic["l2_error"]), precision=2),
                    sci(float(arithmetic["flux_error_abs"]), precision=2),
                    sci(float(harmonic["flux_error_abs"]), precision=2),
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Discontinuous-interface verification on a one-dimensional two-material heat-conduction problem. Harmonic face averaging recovers the analytic flux continuity to roundoff in this aligned-interface test.}",
            r"\label{tab:interface-verification}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{rrrrr}",
            r"\toprule",
            r"$N$ & $L^2$ error, arithmetic & $L^2$ error, harmonic & Flux error, arithmetic & Flux error, harmonic \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def averaging_sensitivity_table(rows: Iterable[dict[str, str]]) -> str:
    rows = list(rows)
    by_key = {
        (row["coefficient_case"], int(row["n"]), row["face_average"], row["method"]): row
        for row in rows
    }
    cases = ["inclusion_c100", "layered_c100", "checkerboard_c100"]
    body: list[str] = []
    for case in cases:
        for n in [64, 128, 256]:
            cg_a = by_key[(case, n, "arithmetic", "cg")]
            cg_h = by_key[(case, n, "harmonic", "cg")]
            jac_a = by_key[(case, n, "arithmetic", "jacobi-pcg")]
            jac_h = by_key[(case, n, "harmonic", "jacobi-pcg")]
            amg_a = by_key[(case, n, "arithmetic", "amg-pcg")]
            amg_h = by_key[(case, n, "harmonic", "amg-pcg")]
            best_a = next(row for row in rows if row["coefficient_case"] == case and int(row["n"]) == n and row["face_average"] == "arithmetic" and bool_value(row["is_best"]))
            best_h = next(row for row in rows if row["coefficient_case"] == case and int(row["n"]) == n and row["face_average"] == "harmonic" and bool_value(row["is_best"]))
            body.append(
                " & ".join(
                    [
                        case.replace("_", r"\_"),
                        str(n),
                        f"{float(cg_a['iterations']):.0f}/{float(cg_h['iterations']):.0f}",
                        f"{float(jac_a['iterations']):.0f}/{float(jac_h['iterations']):.0f}",
                        f"{float(amg_a['iterations']):.0f}/{float(amg_h['iterations']):.0f}",
                        f"{method_label(best_a['method'])}/{method_label(best_h['method'])}",
                        f"{float(best_a['speedup_vs_cg']):.2f}/{float(best_h['speedup_vs_cg']):.2f}",
                    ]
                )
                + r" \\"
            )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Arithmetic/harmonic face-averaging sensitivity for discontinuous $C_k=100$ stress cases. Each paired entry reports arithmetic/harmonic values. The full CSV also records $\kappa(A)$ using matched $N$ for 64 and 128 and the $N=128$ proxy for $N=256$.}",
            r"\label{tab:averaging-sensitivity}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{lrrrrlr}",
            r"\toprule",
            r"Case & $N$ & CG it. & Jacobi-PCG it. & AMG-PCG it. & Best solver & Best speedup \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def timing_stability_table(rows: Iterable[dict[str, str]]) -> str:
    rows = list(rows)
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

    body: list[str] = []
    for row in selected:
        status = "stable" if bool_value(row["decision_stable"]) else "variable"
        body.append(
            " & ".join(
                [
                    row["coefficient_case"].replace("_", r"\_"),
                    str(int(float(row["n"]))),
                    method_label(row["best_method_by_median"]),
                    method_label(row["best_method_vote"]),
                    f"{float(row['vote_fraction']):.2f}",
                    f"{float(row['median_speedup_vs_cg']):.2f}",
                    f"{100.0 * float(row['selected_rel_iqr']):.1f}\\%",
                    status,
                ]
            )
            + r" \\"
        )

    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Repeated timing stability check. Rows report the solver selected by median total time across repeats, the per-repeat vote fraction, and the relative interquartile range of the selected method.}",
            r"\label{tab:timing-stability}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{lrllrrrl}",
            r"\toprule",
            r"Case & $N$ & Median best & Vote best & Vote & Speedup & Rel. IQR & Status \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def hardware_model_table(rows: Iterable[dict[str, str]]) -> str:
    rows_by_component = {row["model_component"]: row for row in rows}
    cpu = rows_by_component["cpu"]
    cuda = rows_by_component["cuda"]
    crossover = rows_by_component["crossover"]
    body = [
        " & ".join(
            [
                "CPU Numba",
                str(int(float(cpu["observations"]))),
                sci(float(cpu["beta_seconds_per_unknown"]), precision=3),
                f"{float(cpu['r2']):.3f}",
                "-",
            ]
        )
        + r" \\",
        " & ".join(
            [
                "CUDA kernel",
                str(int(float(cuda["observations"]))),
                sci(float(cuda["beta_seconds_per_unknown"]), precision=3),
                f"{float(cuda['r2']):.3f}",
                "-",
            ]
        )
        + r" \\",
        " & ".join(
            [
                "Illustrative fitted crossover",
                "-",
                "-",
                f"{float(crossover['r2']):.3f}",
                f"{float(crossover['crossover_grid_n']):.0f}",
            ]
        )
        + r" \\",
    ]
    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{Empirical linear CPU/CUDA kernel crossover model fitted over the measured Jacobi-stencil range. The fit is used as a local interpolation of the crossover point, not as a physical launch-overhead model.}",
            r"\label{tab:hardware-model}",
            r"\resizebox{\columnwidth}{!}{%",
            r"\begin{tabular}{lrrrr}",
            r"\toprule",
            r"Component & Observations & $\beta$ (s/unknown) & $R^2$ & Crossover $N$ \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\end{table}",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate manuscript LaTeX tables from raw CSV files.")
    parser.add_argument("--convergence-csv", default="results/raw/convergence.csv")
    parser.add_argument("--solver-csv", default="results/raw/solver_benchmark.csv")
    parser.add_argument("--cpu-scaling-csv", default="results/raw/cpu_scaling.csv")
    parser.add_argument("--gpu-stencil-csv", default="results/raw/gpu_stencil.csv")
    parser.add_argument("--solver-decision-csv", default="results/raw/solver_decision_map.csv")
    parser.add_argument("--conditioning-csv", default="results/raw/conditioning.csv")
    parser.add_argument("--difficulty-relationships-csv", default="results/raw/difficulty_relationships.csv")
    parser.add_argument("--interface-verification-csv", default="results/raw/interface_verification.csv")
    parser.add_argument("--averaging-sensitivity-csv", default="results/raw/averaging_sensitivity.csv")
    parser.add_argument("--timing-stability-csv", default="results/raw/timing_stability.csv")
    parser.add_argument("--hardware-crossover-model-csv", default="results/raw/hardware_crossover_model.csv")
    parser.add_argument("--output-dir", default="paper/tables")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    write_text(output_dir / "convergence_summary.tex", convergence_table(read_rows(args.convergence_csv)))
    write_text(output_dir / "solver_summary.tex", solver_table(read_rows(args.solver_csv)))
    write_text(
        output_dir / "performance_summary.tex",
        performance_table(read_rows(args.cpu_scaling_csv), read_rows(args.gpu_stencil_csv)),
    )
    decision_rows = read_rows(args.solver_decision_csv)
    conditioning_rows = read_rows(args.conditioning_csv)
    write_text(
        output_dir / "coefficient_difficulty_summary.tex",
        coefficient_difficulty_table(decision_rows, conditioning_rows),
    )
    write_text(output_dir / "decision_summary.tex", decision_summary_table(decision_rows))
    write_text(
        output_dir / "difficulty_relationship_summary.tex",
        difficulty_relationship_table(read_rows(args.difficulty_relationships_csv)),
    )
    write_text(
        output_dir / "interface_verification_summary.tex",
        interface_verification_table(read_rows(args.interface_verification_csv)),
    )
    write_text(
        output_dir / "averaging_sensitivity_summary.tex",
        averaging_sensitivity_table(read_rows(args.averaging_sensitivity_csv)),
    )
    write_text(
        output_dir / "timing_stability_summary.tex",
        timing_stability_table(read_rows(args.timing_stability_csv)),
    )
    write_text(
        output_dir / "hardware_model_summary.tex",
        hardware_model_table(read_rows(args.hardware_crossover_model_csv)),
    )


if __name__ == "__main__":
    main()
