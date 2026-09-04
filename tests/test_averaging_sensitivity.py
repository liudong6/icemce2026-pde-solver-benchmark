import csv


def test_averaging_sensitivity_records_condition_proxy_and_solver_rows(tmp_path):
    from pdescale.averaging_sensitivity import (
        AVERAGING_SENSITIVITY_FIELDS,
        run_averaging_sensitivity,
        write_averaging_sensitivity_csv,
    )

    rows = run_averaging_sensitivity(
        coefficient_cases=("checkerboard_c10",),
        sizes=(12,),
        face_averages=("arithmetic", "harmonic"),
        methods=("cg", "jacobi-pcg"),
        max_condition_n=12,
    )
    output = tmp_path / "averaging_sensitivity.csv"
    write_averaging_sensitivity_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == AVERAGING_SENSITIVITY_FIELDS
    assert len(loaded) == 4
    assert {row["face_average"] for row in loaded} == {"arithmetic", "harmonic"}
    assert all(float(row["condition_estimate"]) > 0.0 for row in loaded)
