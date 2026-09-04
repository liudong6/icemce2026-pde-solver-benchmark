import csv


def test_spearman_rank_correlation_handles_ties_and_order():
    from pdescale.difficulty_analysis import spearman_rank_correlation

    assert spearman_rank_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert spearman_rank_correlation([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0
    assert spearman_rank_correlation([1, 1, 2, 2], [3, 3, 4, 4]) == 1.0


def test_difficulty_relationships_join_decision_and_conditioning_rows():
    from pdescale.difficulty_analysis import (
        DIFFICULTY_RELATIONSHIP_FIELDS,
        analyze_difficulty_relationships,
    )

    decision_rows = []
    for case, family, contrast, grad, tv, n, cg_iter, best_speedup in [
        ("constant", "constant", 1.0, 0.0, 0.0, 64, 20, 1.2),
        ("smooth_c10", "smooth", 10.0, 8.0, 4.0, 64, 80, 2.4),
        ("inclusion_c100", "inclusion", 100.0, 40.0, 20.0, 64, 200, 4.0),
    ]:
        for method in ("cg", "jacobi-pcg", "amg-pcg"):
            decision_rows.append(
                {
                    "coefficient_case": case,
                    "family": family,
                    "contrast_observed": str(contrast),
                    "grad_logk_inf": str(grad),
                    "total_variation_proxy": str(tv),
                    "n": str(n),
                    "method": method,
                    "iterations": str(cg_iter if method == "cg" else 10),
                    "is_best": str(method == "amg-pcg"),
                    "speedup_vs_cg": str(best_speedup if method == "amg-pcg" else 1.0),
                }
            )
    conditioning_rows = [
        {"coefficient_case": "constant", "n": "64", "condition_estimate": "100"},
        {"coefficient_case": "smooth_c10", "n": "64", "condition_estimate": "1000"},
        {"coefficient_case": "inclusion_c100", "n": "64", "condition_estimate": "10000"},
    ]

    rows = analyze_difficulty_relationships(decision_rows, conditioning_rows)

    assert rows
    assert tuple(rows[0].keys()) == DIFFICULTY_RELATIONSHIP_FIELDS
    contrast_cg = next(
        row
        for row in rows
        if row["descriptor"] == "contrast_observed"
        and row["response"] == "cg_iterations"
        and row["n_group"] == "all"
    )
    assert contrast_cg["n_samples"] == 3
    assert contrast_cg["spearman_rho"] == 1.0
    assert contrast_cg["fisher_z_diagnostic_low"] < contrast_cg["spearman_rho"]
    assert contrast_cg["fisher_z_diagnostic_high"] >= contrast_cg["spearman_rho"]
    assert contrast_cg["case_resampling_low"] == ""
    assert contrast_cg["case_resampling_high"] == ""
    assert 0.0 < contrast_cg["permutation_p"] <= 1.0
    assert contrast_cg["n_case_resamples"] == 0


def test_write_difficulty_relationships_csv_uses_schema(tmp_path):
    from pdescale.difficulty_analysis import (
        DIFFICULTY_RELATIONSHIP_FIELDS,
        write_difficulty_relationship_csv,
    )

    rows = [
        {
            "descriptor": "condition_estimate",
            "response": "cg_iterations",
            "n_group": "all",
            "spearman_rho": 0.9,
            "fisher_z_diagnostic_low": 0.3,
            "fisher_z_diagnostic_high": 0.99,
            "case_resampling_low": "",
            "case_resampling_high": "",
            "permutation_p": 0.05,
            "n_permutations": 99,
            "n_case_resamples": 0,
            "n_samples": 13,
            "description": "Condition estimate",
        }
    ]
    output = tmp_path / "difficulty_relationships.csv"
    write_difficulty_relationship_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == DIFFICULTY_RELATIONSHIP_FIELDS
    assert loaded[0]["descriptor"] == "condition_estimate"
    assert loaded[0]["permutation_p"] == "0.05"


def test_conditioning_matches_decision_size_when_available():
    from pdescale.difficulty_analysis import analyze_difficulty_relationships

    decision_rows = []
    for n, cg_iter, best_speedup in [(64, 10, 1.0), (128, 20, 2.0)]:
        for case, contrast in [("low", 1.0), ("high", 10.0)]:
            for method in ("cg", "amg-pcg"):
                decision_rows.append(
                    {
                        "coefficient_case": case,
                        "family": case,
                        "contrast_observed": str(contrast),
                        "grad_logk_inf": str(contrast),
                        "total_variation_proxy": str(contrast),
                        "n": str(n),
                        "method": method,
                        "iterations": str(cg_iter * contrast if method == "cg" else 2),
                        "is_best": str(method == "amg-pcg"),
                        "speedup_vs_cg": str(best_speedup * contrast if method == "amg-pcg" else 1.0),
                    }
                )
    conditioning_rows = [
        {"coefficient_case": "low", "n": "64", "condition_estimate": "1"},
        {"coefficient_case": "high", "n": "64", "condition_estimate": "10"},
        {"coefficient_case": "low", "n": "128", "condition_estimate": "100"},
        {"coefficient_case": "high", "n": "128", "condition_estimate": "1000"},
    ]

    rows = analyze_difficulty_relationships(decision_rows, conditioning_rows, n_permutations=9)

    condition_cg_128 = next(
        row
        for row in rows
        if row["descriptor"] == "condition_estimate"
        and row["response"] == "cg_iterations"
        and row["n_group"] == "128"
    )
    assert condition_cg_128["spearman_rho"] == 1.0
    assert condition_cg_128["n_permutations"] == 9


def test_fixed_grid_relationships_include_case_resampling_interval():
    from pdescale.difficulty_analysis import analyze_difficulty_relationships

    decision_rows = []
    for idx, contrast in enumerate([1.0, 3.0, 10.0, 30.0, 100.0], start=1):
        for method in ("cg", "amg-pcg"):
            decision_rows.append(
                {
                    "coefficient_case": f"case_{idx}",
                    "family": "synthetic",
                    "contrast_observed": str(contrast),
                    "grad_logk_inf": str(contrast),
                    "total_variation_proxy": str(contrast),
                    "n": "64",
                    "method": method,
                    "iterations": str(10 * idx if method == "cg" else 2),
                    "is_best": str(method == "amg-pcg"),
                    "speedup_vs_cg": str(float(idx) if method == "amg-pcg" else 1.0),
                }
            )
    conditioning_rows = [
        {"coefficient_case": f"case_{idx}", "n": "64", "condition_estimate": str(idx)}
        for idx in range(1, 6)
    ]

    rows = analyze_difficulty_relationships(
        decision_rows,
        conditioning_rows,
        n_permutations=9,
        n_case_resamples=19,
    )
    fixed = next(
        row
        for row in rows
        if row["descriptor"] == "contrast_observed"
        and row["response"] == "cg_iterations"
        and row["n_group"] == "64"
    )
    assert fixed["n_case_resamples"] == 19
    assert fixed["case_resampling_low"] != ""
    assert fixed["case_resampling_high"] != ""
