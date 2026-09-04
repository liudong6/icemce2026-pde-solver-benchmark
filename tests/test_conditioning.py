import csv


def test_conditioning_estimate_is_positive_for_spd_operator():
    from pdescale.conditioning import CONDITIONING_FIELDS, estimate_conditioning
    from pdescale.grid import Grid2D

    row = estimate_conditioning(Grid2D(12, 12), "constant")

    assert tuple(row.keys()) == CONDITIONING_FIELDS
    assert row["lambda_min"] > 0.0
    assert row["lambda_max"] > row["lambda_min"]
    assert row["condition_estimate"] > 1.0


def test_write_conditioning_csv_uses_schema(tmp_path):
    from pdescale.conditioning import CONDITIONING_FIELDS, run_conditioning_study, write_conditioning_csv

    rows = run_conditioning_study(coefficient_cases=("constant", "smooth_c3"), sizes=(12,))
    output = tmp_path / "conditioning.csv"
    write_conditioning_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == CONDITIONING_FIELDS
    assert len(loaded) == 2
    assert all(float(row["condition_estimate"]) > 1.0 for row in loaded)
