import csv
import math


def test_solver_benchmark_case_returns_schema_rows():
    from pdescale.benchmark import (
        SOLVER_BENCHMARK_FIELDS,
        SolverBenchmarkCase,
        run_solver_benchmark_case,
    )

    case = SolverBenchmarkCase(
        name="tiny_high_contrast",
        coefficient_case="high_contrast",
        sizes=(16, 24),
        methods=("cg", "jacobi-pcg", "amg-pcg"),
        tolerance=1e-8,
        maxiter=5000,
    )
    rows = run_solver_benchmark_case(case)

    assert len(rows) == 6
    assert {row["method"] for row in rows} == {"cg", "jacobi-pcg", "amg-pcg"}
    for row in rows:
        assert tuple(row.keys()) == SOLVER_BENCHMARK_FIELDS
        assert row["case"] == "tiny_high_contrast"
        assert row["n_unknowns"] == (row["n"] - 2) ** 2
        assert row["total_seconds"] == row["setup_seconds"] + row["solve_seconds"]
        assert row["memory_estimate_mb"] > 0.0
        assert isinstance(row["converged"], bool)
        assert math.isfinite(row["residual_norm"]) or math.isinf(row["residual_norm"])


def test_write_solver_benchmark_csv_uses_schema(tmp_path):
    from pdescale.benchmark import (
        SOLVER_BENCHMARK_FIELDS,
        SolverBenchmarkCase,
        run_solver_benchmark_case,
        write_solver_benchmark_csv,
    )

    case = SolverBenchmarkCase(
        name="tiny_smooth",
        coefficient_case="smooth",
        sizes=(16,),
        methods=("cg",),
        tolerance=1e-8,
        maxiter=5000,
    )
    rows = run_solver_benchmark_case(case)
    csv_path = tmp_path / "solver_benchmark.csv"

    write_solver_benchmark_csv(rows, csv_path)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == SOLVER_BENCHMARK_FIELDS
    assert len(loaded) == 1
    assert loaded[0]["case"] == "tiny_smooth"
