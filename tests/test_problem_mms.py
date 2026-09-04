def test_manufactured_solution_zero_on_boundary():
    from pdescale.grid import Grid2D
    from pdescale.problems import u_exact

    g = Grid2D(16, 16)
    u = u_exact(g.x, g.y)
    assert abs(u[0, :]).max() < 1e-14
    assert abs(u[-1, :]).max() < 1e-14
    assert abs(u[:, 0]).max() < 1e-14
    assert abs(u[:, -1]).max() < 1e-14


def test_smooth_conductivity_is_positive():
    from pdescale.grid import Grid2D
    from pdescale.problems import k_field

    g = Grid2D(32, 32)
    k = k_field(g.x, g.y, "smooth")
    assert k.shape == g.x.shape
    assert k.min() > 0.49
    assert k.max() < 1.51


def test_manufactured_rhs_has_interior_shape():
    from pdescale.grid import Grid2D
    from pdescale.problems import rhs_manufactured

    g = Grid2D(12, 10)
    rhs = rhs_manufactured(g, "constant")
    assert rhs.shape == ((12 - 2) * (10 - 2),)


def test_high_contrast_is_not_a_manufactured_solution_case():
    import pytest
    from pdescale.grid import Grid2D
    from pdescale.problems import rhs_manufactured

    g = Grid2D(12, 12)
    with pytest.raises(NotImplementedError, match="solver-benchmark coefficient case"):
        rhs_manufactured(g, "high_contrast")
