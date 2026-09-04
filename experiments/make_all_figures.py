from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from pdescale.plotting import (
    plot_conditioning,
    plot_convergence_l2,
    plot_cpu_scaling,
    plot_difficulty_relationships,
    plot_gpu_crossover,
    plot_hardware_crossover_model,
    plot_solver_decision_map,
    plot_solver_iterations,
    plot_solver_runtime,
    plot_timing_stability,
)


def copy_for_manuscript(path: str, paper_dir: str) -> None:
    source = Path(path)
    target_dir = Path(paper_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    shutil.copy2(source, target)
    print(f"copied {source} -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducible paper figures.")
    parser.add_argument(
        "--only",
        choices=[
            "convergence",
            "solvers",
            "scaling",
            "gpu",
            "decision",
            "conditioning",
            "difficulty-relationships",
            "timing-stability",
            "hardware-model",
            "all",
        ],
        default="all",
    )
    parser.add_argument("--convergence-csv", default="results/raw/convergence.csv")
    parser.add_argument("--convergence-png", default="results/figures/convergence_l2.png")
    parser.add_argument("--solver-csv", default="results/raw/solver_benchmark.csv")
    parser.add_argument("--solver-runtime-png", default="results/figures/solver_runtime.png")
    parser.add_argument("--solver-iterations-png", default="results/figures/solver_iterations.png")
    parser.add_argument("--cpu-scaling-csv", default="results/raw/cpu_scaling.csv")
    parser.add_argument("--cpu-scaling-png", default="results/figures/cpu_scaling.png")
    parser.add_argument("--gpu-stencil-csv", default="results/raw/gpu_stencil.csv")
    parser.add_argument("--gpu-crossover-png", default="results/figures/gpu_crossover.png")
    parser.add_argument("--solver-decision-csv", default="results/raw/solver_decision_map.csv")
    parser.add_argument("--solver-decision-png", default="results/figures/solver_decision_map.png")
    parser.add_argument("--conditioning-csv", default="results/raw/conditioning.csv")
    parser.add_argument("--conditioning-png", default="results/figures/conditioning.png")
    parser.add_argument("--difficulty-relationships-csv", default="results/raw/difficulty_relationships.csv")
    parser.add_argument(
        "--difficulty-relationships-png",
        default="results/figures/difficulty_relationships.png",
    )
    parser.add_argument("--timing-stability-csv", default="results/raw/timing_stability.csv")
    parser.add_argument("--timing-stability-png", default="results/figures/timing_stability.png")
    parser.add_argument("--hardware-crossover-model-csv", default="results/raw/hardware_crossover_model.csv")
    parser.add_argument(
        "--hardware-crossover-model-png",
        default="results/figures/hardware_crossover_model.png",
    )
    parser.add_argument("--paper-figures-dir", default="paper/figures")
    parser.add_argument(
        "--no-copy-to-paper",
        action="store_true",
        help="Skip copying generated PNGs into the manuscript figure directory.",
    )
    args = parser.parse_args()
    generated_paths: list[str] = []

    if args.only in {"convergence", "all"}:
        plot_convergence_l2(args.convergence_csv, args.convergence_png)
        print(f"wrote {args.convergence_png}")
        generated_paths.append(args.convergence_png)
    if args.only in {"solvers", "all"}:
        plot_solver_runtime(args.solver_csv, args.solver_runtime_png)
        print(f"wrote {args.solver_runtime_png}")
        generated_paths.append(args.solver_runtime_png)
        plot_solver_iterations(args.solver_csv, args.solver_iterations_png)
        print(f"wrote {args.solver_iterations_png}")
        generated_paths.append(args.solver_iterations_png)
    if args.only in {"scaling", "all"}:
        plot_cpu_scaling(args.cpu_scaling_csv, args.cpu_scaling_png)
        print(f"wrote {args.cpu_scaling_png}")
        generated_paths.append(args.cpu_scaling_png)
    if args.only in {"gpu", "all"}:
        plot_gpu_crossover(args.gpu_stencil_csv, args.gpu_crossover_png)
        print(f"wrote {args.gpu_crossover_png}")
        generated_paths.append(args.gpu_crossover_png)
    if args.only in {"decision", "all"}:
        plot_solver_decision_map(args.solver_decision_csv, args.solver_decision_png)
        print(f"wrote {args.solver_decision_png}")
        generated_paths.append(args.solver_decision_png)
    if args.only in {"conditioning", "all"}:
        plot_conditioning(args.conditioning_csv, args.conditioning_png)
        print(f"wrote {args.conditioning_png}")
        generated_paths.append(args.conditioning_png)
    if args.only in {"difficulty-relationships", "all"}:
        plot_difficulty_relationships(
            args.difficulty_relationships_csv,
            args.difficulty_relationships_png,
        )
        print(f"wrote {args.difficulty_relationships_png}")
        generated_paths.append(args.difficulty_relationships_png)
    if args.only in {"timing-stability", "all"}:
        plot_timing_stability(args.timing_stability_csv, args.timing_stability_png)
        print(f"wrote {args.timing_stability_png}")
        generated_paths.append(args.timing_stability_png)
    if args.only in {"hardware-model", "all"}:
        plot_hardware_crossover_model(
            args.gpu_stencil_csv,
            args.hardware_crossover_model_csv,
            args.hardware_crossover_model_png,
        )
        print(f"wrote {args.hardware_crossover_model_png}")
        generated_paths.append(args.hardware_crossover_model_png)

    if not args.no_copy_to_paper:
        for path in generated_paths:
            copy_for_manuscript(path, args.paper_figures_dir)


if __name__ == "__main__":
    main()
