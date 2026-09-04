def test_decision_summary_table_is_generated_from_decision_rows():
    from experiments.make_paper_tables import decision_summary_table

    rows = [
        {
            "n": "64",
            "best_method": "jacobi-pcg",
            "is_best": "True",
            "speedup_vs_cg": "1.5",
        },
        {
            "n": "64",
            "best_method": "jacobi-pcg",
            "is_best": "True",
            "speedup_vs_cg": "2.5",
        },
        {
            "n": "128",
            "best_method": "amg-pcg",
            "is_best": "True",
            "speedup_vs_cg": "6.0",
        },
    ]

    table = decision_summary_table(rows)

    assert "Jacobi-PCG" in table
    assert "AMG-PCG" in table
    assert "2" in table
    assert "6.00" in table


def test_hardware_model_table_reports_crossover_grid():
    from experiments.make_paper_tables import hardware_model_table

    rows = [
        {
            "model_component": "cpu",
            "method": "numba-parallel-cpu",
            "observations": "4",
            "alpha_seconds": "-3.0e-4",
            "beta_seconds_per_unknown": "6.7e-10",
            "r2": "0.999",
            "crossover_n_unknowns": "0.0",
            "crossover_grid_n": "0.0",
            "cpu_alpha_seconds": "-3.0e-4",
            "cpu_beta_seconds_per_unknown": "6.7e-10",
            "gpu_alpha_seconds": "-2.5e-5",
            "gpu_beta_seconds_per_unknown": "1.9e-10",
        },
        {
            "model_component": "cuda",
            "method": "cuda-kernel",
            "observations": "4",
            "alpha_seconds": "-2.5e-5",
            "beta_seconds_per_unknown": "1.9e-10",
            "r2": "0.998",
            "crossover_n_unknowns": "0.0",
            "crossover_grid_n": "0.0",
            "cpu_alpha_seconds": "-3.0e-4",
            "cpu_beta_seconds_per_unknown": "6.7e-10",
            "gpu_alpha_seconds": "-2.5e-5",
            "gpu_beta_seconds_per_unknown": "1.9e-10",
        },
        {
            "model_component": "crossover",
            "method": "linear_cpu_vs_cuda",
            "observations": "4",
            "alpha_seconds": "0.0",
            "beta_seconds_per_unknown": "0.0",
            "r2": "0.998",
            "crossover_n_unknowns": "567000",
            "crossover_grid_n": "755",
            "cpu_alpha_seconds": "-3.0e-4",
            "cpu_beta_seconds_per_unknown": "6.7e-10",
            "gpu_alpha_seconds": "-2.5e-5",
            "gpu_beta_seconds_per_unknown": "1.9e-10",
        },
    ]

    table = hardware_model_table(rows)

    assert "CPU Numba" in table
    assert "CUDA kernel" in table
    assert "755" in table


def test_difficulty_relationship_table_reports_rank_correlations():
    from experiments.make_paper_tables import difficulty_relationship_table

    rows = [
        {
            "descriptor": "contrast_observed",
            "response": "cg_iterations",
            "n_group": "all",
            "spearman_rho": "0.42",
            "n_samples": "39",
            "description": "Observed coefficient contrast vs Unpreconditioned CG iterations",
        },
        {
            "descriptor": "contrast_observed",
            "response": "cg_iterations",
            "n_group": "64",
            "spearman_rho": "0.90",
            "n_samples": "13",
            "description": "Observed coefficient contrast vs Unpreconditioned CG iterations",
        },
        {
            "descriptor": "contrast_observed",
            "response": "cg_iterations",
            "n_group": "128",
            "spearman_rho": "0.92",
            "n_samples": "13",
            "description": "Observed coefficient contrast vs Unpreconditioned CG iterations",
        },
        {
            "descriptor": "condition_estimate",
            "response": "selected_speedup_vs_cg",
            "n_group": "all",
            "spearman_rho": "0.88",
            "n_samples": "39",
            "description": "Matched spectral condition estimate vs Selected-solver speedup over CG",
        },
        {
            "descriptor": "condition_estimate",
            "response": "selected_speedup_vs_cg",
            "n_group": "256",
            "spearman_rho": "0.91",
            "n_samples": "13",
            "description": "Matched spectral condition estimate vs Selected-solver speedup over CG",
        },
    ]

    table = difficulty_relationship_table(rows)

    assert "Spearman" in table
    assert "$\\kappa(A)$ proxy" in table
    assert "0.88" in table
    assert "fixed-$N$" in table
    assert "0.91" in table


def test_timing_stability_table_reports_repeated_decision_summary():
    from experiments.make_paper_tables import timing_stability_table

    rows = [
        {
            "coefficient_case": "constant",
            "family": "constant",
            "n": "64",
            "best_method_by_median": "jacobi-pcg",
            "best_method_vote": "jacobi-pcg",
            "vote_fraction": "1.0",
            "n_repeats": "5",
            "cg_median_seconds": "0.01",
            "selected_median_seconds": "0.005",
            "median_speedup_vs_cg": "2.0",
            "selected_rel_iqr": "0.08",
            "decision_stable": "True",
        },
        {
            "coefficient_case": "inclusion_c100",
            "family": "inclusion",
            "n": "256",
            "best_method_by_median": "amg-pcg",
            "best_method_vote": "amg-pcg",
            "vote_fraction": "1.0",
            "n_repeats": "5",
            "cg_median_seconds": "6.0",
            "selected_median_seconds": "0.3",
            "median_speedup_vs_cg": "20.0",
            "selected_rel_iqr": "0.05",
            "decision_stable": "True",
        },
    ]

    table = timing_stability_table(rows)

    assert "Repeated timing" in table
    assert "inclusion\\_c100" in table
    assert "20.00" in table
    assert "stable" in table


def test_interface_verification_table_reports_averaging_errors():
    from experiments.make_paper_tables import interface_verification_table

    rows = [
        {
            "n": "32",
            "face_average": "arithmetic",
            "l2_error": "1.2e-2",
            "flux_error_abs": "6.0e-2",
        },
        {
            "n": "32",
            "face_average": "harmonic",
            "l2_error": "5.0e-16",
            "flux_error_abs": "6.0e-15",
        },
    ]

    table = interface_verification_table(rows)

    assert "Discontinuous-interface verification" in table
    assert "harmonic" in table
    assert "1.20\\times10^{-2}" in table
    assert "5.00\\times10^{-16}" in table


def test_averaging_sensitivity_table_reports_paired_solver_decisions():
    from experiments.make_paper_tables import averaging_sensitivity_table

    rows = []
    for case in ["inclusion_c100", "layered_c100", "checkerboard_c100"]:
        for n in [64, 128, 256]:
            for face_average in ["arithmetic", "harmonic"]:
                for method, iterations, is_best in [
                    ("cg", "100", "False"),
                    ("jacobi-pcg", "20", str(n == 64)),
                    ("amg-pcg", "10", str(n != 64)),
                ]:
                    rows.append(
                        {
                            "coefficient_case": case,
                            "n": str(n),
                            "face_average": face_average,
                            "method": method,
                            "iterations": iterations,
                            "is_best": is_best,
                            "speedup_vs_cg": "2.5",
                        }
                    )

    table = averaging_sensitivity_table(rows)

    assert "Arithmetic/harmonic face-averaging sensitivity" in table
    assert "inclusion\\_c100" in table
    assert "100/100" in table
    assert "Jacobi-PCG/Jacobi-PCG" in table
    assert "AMG-PCG/AMG-PCG" in table
