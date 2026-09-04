def test_estimate_order_recovers_second_order_sequence():
    import numpy as np
    from pdescale.convergence import estimate_order

    h = np.array([1.0 / 16, 1.0 / 32, 1.0 / 64, 1.0 / 128])
    errors = 3.0 * h**2
    assert 1.99 < estimate_order(h, errors) < 2.01


def test_run_convergence_case_returns_verifiable_rows():
    from pdescale.convergence import ConvergenceCase, estimate_order, run_convergence_case

    case = ConvergenceCase(
        name="constant_test",
        coefficient_case="constant",
        sizes=(16, 32, 64),
        method="cg",
        tol=1e-11,
        maxiter=5000,
    )
    rows = run_convergence_case(case)
    assert len(rows) == 3
    for row in rows:
        assert row["case_name"] == "constant_test"
        assert row["coefficient_case"] == "constant"
        assert row["method"] == "cg"
        assert row["converged"] is True
        assert row["residual_norm"] < 1e-8
        assert row["l2_error"] > 0.0
        assert row["linf_error"] > 0.0
        assert row["n_unknowns"] == (row["n"] - 2) ** 2

    order = estimate_order(
        [row["h"] for row in rows],
        [row["l2_error"] for row in rows],
    )
    assert 1.8 <= order <= 2.3


def test_write_convergence_csv_uses_stable_schema(tmp_path):
    import csv
    from pdescale.convergence import CONVERGENCE_FIELDS, write_convergence_csv

    rows = [
        {
            "case_name": "constant",
            "coefficient_case": "constant",
            "n": 16,
            "n_unknowns": 196,
            "h": 1.0 / 15,
            "method": "cg",
            "tol": 1e-11,
            "maxiter": 5000,
            "converged": True,
            "iterations": 20,
            "residual_norm": 1e-12,
            "solve_seconds": 0.01,
            "l2_error": 0.1,
            "linf_error": 0.2,
        }
    ]
    path = tmp_path / "convergence.csv"
    write_convergence_csv(rows, path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == list(CONVERGENCE_FIELDS)
        loaded = list(reader)
    assert loaded[0]["case_name"] == "constant"

