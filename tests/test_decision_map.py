import csv


def test_solver_decision_study_marks_fastest_converged_solver():
    from pdescale.decision import (
        SOLVER_DECISION_FIELDS,
        SolverDecisionStudy,
        run_solver_decision_study,
    )

    study = SolverDecisionStudy(
        coefficient_cases=("constant", "inclusion_c10"),
        sizes=(16,),
        methods=("cg", "jacobi-pcg"),
        tolerance=1e-8,
        maxiter=1000,
    )
    rows = run_solver_decision_study(study)

    assert len(rows) == 4
    assert tuple(rows[0].keys()) == SOLVER_DECISION_FIELDS
    for case in ("constant", "inclusion_c10"):
        case_rows = [row for row in rows if row["coefficient_case"] == case]
        assert sum(bool(row["is_best"]) for row in case_rows) == 1
        best = next(row for row in case_rows if row["is_best"])
        assert best["best_method"] == best["method"]
        assert best["total_seconds"] == min(row["total_seconds"] for row in case_rows if row["converged"])


def test_write_solver_decision_csv_uses_schema(tmp_path):
    from pdescale.decision import (
        SOLVER_DECISION_FIELDS,
        SolverDecisionStudy,
        run_solver_decision_study,
        write_solver_decision_csv,
    )

    study = SolverDecisionStudy(
        coefficient_cases=("smooth_c3",),
        sizes=(16,),
        methods=("cg",),
    )
    rows = run_solver_decision_study(study)
    output = tmp_path / "solver_decision_map.csv"
    write_solver_decision_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == SOLVER_DECISION_FIELDS
    assert len(loaded) == 1
    assert loaded[0]["coefficient_case"] == "smooth_c3"
