def test_grid_spacing_for_unit_square():
    from pdescale.grid import Grid2D

    g = Grid2D(8, 8)
    assert g.hx == 1.0 / 7
    assert g.hy == 1.0 / 7
    assert g.x.shape == (8, 8)
    assert g.y.shape == (8, 8)


def test_grid_rejects_too_few_points():
    import pytest
    from pdescale.grid import Grid2D

    with pytest.raises(ValueError, match="at least 3"):
        Grid2D(2, 8)

