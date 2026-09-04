import csv


def test_timing_stability_summary_selects_median_best_and_vote():
    from pdescale.timing_stability import (
        TIMING_STABILITY_FIELDS,
        summarize_timing_repeats,
    )

    rows = []
    for repeat, cg_time, jacobi_time, amg_time, best in [
        (1, 1.0, 0.8, 0.5, "amg-pcg"),
        (2, 1.2, 0.7, 0.6, "amg-pcg"),
        (3, 1.1, 0.75, 0.55, "amg-pcg"),
    ]:
        for method, total_seconds in [
            ("cg", cg_time),
            ("jacobi-pcg", jacobi_time),
            ("amg-pcg", amg_time),
        ]:
            rows.append(
                {
                    "repeat_index": str(repeat),
                    "coefficient_case": "inclusion_c100",
                    "family": "inclusion",
                    "n": "256",
                    "method": method,
                    "converged": "True",
                    "total_seconds": str(total_seconds),
                    "is_best": str(method == best),
                }
            )

    summary = summarize_timing_repeats(rows)

    assert len(summary) == 1
    assert tuple(summary[0].keys()) == TIMING_STABILITY_FIELDS
    assert summary[0]["best_method_by_median"] == "amg-pcg"
    assert summary[0]["best_method_vote"] == "amg-pcg"
    assert summary[0]["vote_fraction"] == 1.0
    assert summary[0]["median_speedup_vs_cg"] == 2.0
    assert summary[0]["decision_stable"] is True


def test_write_timing_stability_csv_uses_schema(tmp_path):
    from pdescale.timing_stability import TIMING_STABILITY_FIELDS, write_timing_stability_csv

    rows = [
        {
            "coefficient_case": "constant",
            "family": "constant",
            "n": 64,
            "best_method_by_median": "jacobi-pcg",
            "best_method_vote": "jacobi-pcg",
            "vote_fraction": 1.0,
            "n_repeats": 3,
            "cg_median_seconds": 0.01,
            "selected_median_seconds": 0.005,
            "median_speedup_vs_cg": 2.0,
            "selected_rel_iqr": 0.1,
            "decision_stable": True,
        }
    ]
    output = tmp_path / "timing_stability.csv"
    write_timing_stability_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == TIMING_STABILITY_FIELDS
    assert loaded[0]["best_method_by_median"] == "jacobi-pcg"
