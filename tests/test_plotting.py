def test_plot_convergence_l2_creates_png(tmp_path):
    import csv
    from pdescale.convergence import CONVERGENCE_FIELDS
    from pdescale.plotting import plot_convergence_l2

    csv_path = tmp_path / "convergence.csv"
    rows = [
        {
            "case_name": "constant",
            "coefficient_case": "constant",
            "n": n,
            "n_unknowns": (n - 2) ** 2,
            "h": 1.0 / (n - 1),
            "method": "cg",
            "tol": 1e-11,
            "maxiter": 5000,
            "converged": True,
            "iterations": 10,
            "residual_norm": 1e-12,
            "solve_seconds": 0.01,
            "l2_error": (1.0 / (n - 1)) ** 2,
            "linf_error": 2.0 * (1.0 / (n - 1)) ** 2,
        }
        for n in (16, 32, 64)
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONVERGENCE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "convergence_l2.png"
    plot_convergence_l2(csv_path, png_path)
    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_solver_runtime_and_iterations_create_png(tmp_path):
    import csv
    from pdescale.benchmark import SOLVER_BENCHMARK_FIELDS
    from pdescale.plotting import plot_solver_iterations, plot_solver_runtime

    csv_path = tmp_path / "solver_benchmark.csv"
    rows = []
    for case in ("smooth", "high_contrast"):
        for n in (32, 64):
            for method, scale in (("cg", 1.0), ("jacobi-pcg", 0.8), ("amg-pcg", 0.2)):
                rows.append(
                    {
                        "case": case,
                        "n": n,
                        "n_unknowns": (n - 2) ** 2,
                        "method": method,
                        "tolerance": 1e-8,
                        "converged": True,
                        "iterations": int(scale * n),
                        "setup_seconds": 0.01 * scale,
                        "solve_seconds": 0.02 * scale * n / 32,
                        "total_seconds": 0.01 * scale + 0.02 * scale * n / 32,
                        "residual_norm": 1e-9,
                        "memory_estimate_mb": 1.0,
                    }
                )
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SOLVER_BENCHMARK_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    runtime_png = tmp_path / "solver_runtime.png"
    iterations_png = tmp_path / "solver_iterations.png"
    plot_solver_runtime(csv_path, runtime_png)
    plot_solver_iterations(csv_path, iterations_png)

    assert runtime_png.exists()
    assert runtime_png.stat().st_size > 1000
    assert iterations_png.exists()
    assert iterations_png.stat().st_size > 1000


def test_plot_cpu_scaling_creates_png(tmp_path):
    import csv
    from pdescale.plotting import plot_cpu_scaling
    from pdescale.scaling import CPU_SCALING_FIELDS

    csv_path = tmp_path / "cpu_scaling.csv"
    rows = []
    for n in (256, 512):
        for method, threads, bandwidth in (
            ("numpy-vectorized", 1, 3.0),
            ("numba-serial", 1, 8.0),
            ("numba-parallel", 4, 20.0),
        ):
            rows.append(
                {
                    "n": n,
                    "n_unknowns": (n - 2) ** 2,
                    "coefficient_case": "smooth",
                    "method": method,
                    "threads": threads,
                    "repeats": 3,
                    "seconds_per_apply": 0.01,
                    "applies_per_second": 100.0,
                    "estimated_gbytes_per_second": bandwidth,
                    "max_abs_error": 1e-12,
                }
            )
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CPU_SCALING_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "cpu_scaling.png"
    plot_cpu_scaling(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_gpu_crossover_creates_png(tmp_path):
    import csv
    from pdescale.gpu_scaling import GPU_STENCIL_FIELDS
    from pdescale.plotting import plot_gpu_crossover

    csv_path = tmp_path / "gpu_stencil.csv"
    rows = []
    for n, speedup in ((1024, 1.4), (2048, 2.5)):
        cpu_time = 0.002
        gpu_time = cpu_time / speedup
        rows.extend(
            [
                {
                    "n": n,
                    "n_unknowns": (n - 2) ** 2,
                    "steps": 20,
                    "method": "numba-parallel-cpu",
                    "repeats": 3,
                    "seconds_per_step": cpu_time,
                    "steps_per_second": 1.0 / cpu_time,
                    "estimated_gbytes_per_second": 100.0,
                    "max_abs_error": 0.0,
                    "speedup_vs_cpu": 1.0,
                },
                {
                    "n": n,
                    "n_unknowns": (n - 2) ** 2,
                    "steps": 20,
                    "method": "cuda-kernel",
                    "repeats": 3,
                    "seconds_per_step": gpu_time,
                    "steps_per_second": 1.0 / gpu_time,
                    "estimated_gbytes_per_second": 100.0 * speedup,
                    "max_abs_error": 1e-12,
                    "speedup_vs_cpu": speedup,
                },
            ]
        )
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GPU_STENCIL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "gpu_crossover.png"
    plot_gpu_crossover(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_solver_decision_map_creates_png(tmp_path):
    import csv
    from pdescale.decision import SOLVER_DECISION_FIELDS
    from pdescale.plotting import plot_solver_decision_map

    csv_path = tmp_path / "solver_decision_map.csv"
    rows = []
    for case, family, contrast, n, best in (
        ("constant", "constant", 1.0, 64, "cg"),
        ("smooth_c10", "smooth", 10.0, 64, "jacobi-pcg"),
        ("inclusion_c100", "inclusion", 100.0, 128, "amg-pcg"),
    ):
        for method in ("cg", "jacobi-pcg", "amg-pcg"):
            rows.append(
                {
                    "coefficient_case": case,
                    "family": family,
                    "contrast_target": contrast,
                    "contrast_observed": contrast,
                    "grad_logk_inf": 1.0,
                    "total_variation_proxy": 1.0,
                    "n": n,
                    "n_unknowns": (n - 2) ** 2,
                    "method": method,
                    "tolerance": 1e-8,
                    "converged": True,
                    "iterations": 10,
                    "setup_seconds": 0.01,
                    "solve_seconds": 0.02,
                    "total_seconds": 0.03,
                    "residual_norm": 1e-9,
                    "memory_estimate_mb": 1.0,
                    "best_method": best,
                    "is_best": method == best,
                    "speedup_vs_cg": 1.0,
                }
            )
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SOLVER_DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "solver_decision_map.png"
    plot_solver_decision_map(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_conditioning_creates_png(tmp_path):
    import csv
    from pdescale.conditioning import CONDITIONING_FIELDS
    from pdescale.plotting import plot_conditioning

    csv_path = tmp_path / "conditioning.csv"
    rows = [
        {
            "coefficient_case": "constant",
            "family": "constant",
            "contrast_target": 1.0,
            "contrast_observed": 1.0,
            "n": 32,
            "n_unknowns": 900,
            "lambda_min": 20.0,
            "lambda_max": 8000.0,
            "condition_estimate": 400.0,
        },
        {
            "coefficient_case": "inclusion_c100",
            "family": "inclusion",
            "contrast_target": 100.0,
            "contrast_observed": 100.0,
            "n": 64,
            "n_unknowns": 3844,
            "lambda_min": 20.0,
            "lambda_max": 80000.0,
            "condition_estimate": 4000.0,
        },
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONDITIONING_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "conditioning.png"
    plot_conditioning(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_hardware_crossover_model_creates_png(tmp_path):
    import csv
    from pdescale.crossover import HARDWARE_CROSSOVER_FIELDS
    from pdescale.gpu_scaling import GPU_STENCIL_FIELDS
    from pdescale.plotting import plot_hardware_crossover_model

    gpu_csv = tmp_path / "gpu_stencil.csv"
    gpu_rows = []
    for n, unknowns, cpu_time, gpu_time in (
        (512, 260100, 4.0e-5, 4.5e-5),
        (1024, 1044484, 2.0e-4, 1.4e-4),
        (2048, 4186116, 2.6e-3, 8.0e-4),
    ):
        for method, seconds in (
            ("numba-parallel-cpu", cpu_time),
            ("cuda-kernel", gpu_time),
        ):
            gpu_rows.append(
                {
                    "n": n,
                    "n_unknowns": unknowns,
                    "steps": 20,
                    "method": method,
                    "repeats": 3,
                    "seconds_per_step": seconds,
                    "steps_per_second": 1.0 / seconds,
                    "estimated_gbytes_per_second": 100.0,
                    "max_abs_error": 0.0,
                    "speedup_vs_cpu": 1.0,
                }
            )
    with gpu_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GPU_STENCIL_FIELDS)
        writer.writeheader()
        writer.writerows(gpu_rows)

    model_csv = tmp_path / "hardware_crossover_model.csv"
    model_rows = [
        {
            "model_component": "cpu",
            "method": "numba-parallel-cpu",
            "observations": 3,
            "alpha_seconds": 0.0,
            "beta_seconds_per_unknown": 6.0e-10,
            "r2": 0.99,
            "crossover_n_unknowns": 0.0,
            "crossover_grid_n": 0.0,
            "cpu_alpha_seconds": 0.0,
            "cpu_beta_seconds_per_unknown": 6.0e-10,
            "gpu_alpha_seconds": 3.0e-5,
            "gpu_beta_seconds_per_unknown": 2.0e-10,
        },
        {
            "model_component": "cuda",
            "method": "cuda-kernel",
            "observations": 3,
            "alpha_seconds": 3.0e-5,
            "beta_seconds_per_unknown": 2.0e-10,
            "r2": 0.99,
            "crossover_n_unknowns": 0.0,
            "crossover_grid_n": 0.0,
            "cpu_alpha_seconds": 0.0,
            "cpu_beta_seconds_per_unknown": 6.0e-10,
            "gpu_alpha_seconds": 3.0e-5,
            "gpu_beta_seconds_per_unknown": 2.0e-10,
        },
        {
            "model_component": "crossover",
            "method": "linear_cpu_vs_cuda",
            "observations": 3,
            "alpha_seconds": 0.0,
            "beta_seconds_per_unknown": 0.0,
            "r2": 0.99,
            "crossover_n_unknowns": 75000.0,
            "crossover_grid_n": 276.0,
            "cpu_alpha_seconds": 0.0,
            "cpu_beta_seconds_per_unknown": 6.0e-10,
            "gpu_alpha_seconds": 3.0e-5,
            "gpu_beta_seconds_per_unknown": 2.0e-10,
        },
    ]
    with model_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HARDWARE_CROSSOVER_FIELDS)
        writer.writeheader()
        writer.writerows(model_rows)

    png_path = tmp_path / "hardware_crossover_model.png"
    plot_hardware_crossover_model(gpu_csv, model_csv, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_difficulty_relationships_creates_png(tmp_path):
    import csv
    from pdescale.difficulty_analysis import DIFFICULTY_RELATIONSHIP_FIELDS
    from pdescale.plotting import plot_difficulty_relationships

    csv_path = tmp_path / "difficulty_relationships.csv"
    rows = [
        {
            "descriptor": descriptor,
            "response": response,
            "n_group": "all",
            "spearman_rho": rho,
            "n_samples": 39,
            "description": f"{descriptor} vs {response}",
        }
        for descriptor, rho in (
            ("contrast_observed", 0.3),
            ("grad_logk_inf", 0.5),
            ("total_variation_proxy", 0.7),
            ("condition_estimate", 0.9),
        )
        for response in ("cg_iterations", "selected_speedup_vs_cg")
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIFFICULTY_RELATIONSHIP_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "difficulty_relationships.png"
    plot_difficulty_relationships(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000


def test_plot_timing_stability_creates_png(tmp_path):
    import csv
    from pdescale.plotting import plot_timing_stability
    from pdescale.timing_stability import TIMING_STABILITY_FIELDS

    csv_path = tmp_path / "timing_stability.csv"
    rows = [
        {
            "coefficient_case": case,
            "family": family,
            "n": n,
            "best_method_by_median": method,
            "best_method_vote": method,
            "vote_fraction": 1.0,
            "n_repeats": 5,
            "cg_median_seconds": 1.0,
            "selected_median_seconds": 1.0 / speedup,
            "median_speedup_vs_cg": speedup,
            "selected_rel_iqr": rel_iqr,
            "decision_stable": True,
        }
        for case, family, n, method, speedup, rel_iqr in [
            ("constant", "constant", 64, "jacobi-pcg", 1.3, 0.10),
            ("smooth_c30", "smooth", 256, "amg-pcg", 4.2, 0.08),
            ("inclusion_c100", "inclusion", 256, "amg-pcg", 18.0, 0.05),
        ]
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TIMING_STABILITY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    png_path = tmp_path / "timing_stability.png"
    plot_timing_stability(csv_path, png_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 1000
