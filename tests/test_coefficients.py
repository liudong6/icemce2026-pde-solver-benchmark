import math


def test_parameterized_smooth_coefficient_matches_target_contrast():
    from pdescale.coefficients import coefficient_field, parse_coefficient_case
    from pdescale.grid import Grid2D

    spec = parse_coefficient_case("smooth_c10")
    grid = Grid2D(129, 129)
    k = coefficient_field(grid.x, grid.y, spec)

    assert spec.family == "smooth"
    assert math.isclose(spec.contrast, 10.0)
    assert math.isclose(float(k.max() / k.min()), 10.0, rel_tol=2e-2)


def test_coefficient_metrics_describe_difficulty_without_solving_pde():
    from pdescale.coefficients import COEFFICIENT_METRIC_FIELDS, coefficient_metrics
    from pdescale.grid import Grid2D

    grid = Grid2D(65, 65)
    metrics = coefficient_metrics(grid, "inclusion_c100")

    assert tuple(metrics.keys()) == COEFFICIENT_METRIC_FIELDS
    assert metrics["family"] == "inclusion"
    assert metrics["n"] == 65
    assert metrics["n_unknowns"] == grid.num_interior
    assert 90.0 <= metrics["contrast_observed"] <= 101.0
    assert metrics["grad_logk_inf"] > 0.0
    assert metrics["total_variation_proxy"] > 0.0


def test_legacy_coefficient_names_still_work():
    from pdescale.coefficients import coefficient_metrics
    from pdescale.grid import Grid2D
    from pdescale.problems import k_field

    grid = Grid2D(33, 33)
    smooth = k_field(grid.x, grid.y, "smooth")
    high = k_field(grid.x, grid.y, "high_contrast")

    assert smooth.min() > 0.49
    assert smooth.max() < 1.51
    assert high.max() / high.min() == 100.0
    assert coefficient_metrics(grid, "high_contrast")["family"] == "inclusion"
