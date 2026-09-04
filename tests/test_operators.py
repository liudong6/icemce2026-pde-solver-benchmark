def test_assembled_operator_shape():
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator

    g = Grid2D(10, 12)
    A = assemble_operator(g, "constant")
    assert A.shape == ((10 - 2) * (12 - 2), (10 - 2) * (12 - 2))


def test_assembled_operator_is_symmetric_positive_for_smooth_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator

    g = Grid2D(14, 14)
    A = assemble_operator(g, "smooth")
    symmetry_error = (A - A.T).max()
    assert abs(symmetry_error) < 1e-12
    rng = np.random.default_rng(7)
    x = rng.normal(size=A.shape[0])
    assert float(x @ (A @ x)) > 0.0


def test_harmonic_face_coefficient_matches_series_conductivity():
    from pdescale.operators import face_coefficient

    assert face_coefficient(1.0, 100.0, "arithmetic") == 50.5
    assert abs(face_coefficient(1.0, 100.0, "harmonic") - (200.0 / 101.0)) < 1e-12


def test_assembled_operator_accepts_harmonic_average_for_jump_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator

    g = Grid2D(16, 16)
    A = assemble_operator(g, "inclusion_c100", face_average="harmonic")
    symmetry_error = (A - A.T).max()
    assert abs(symmetry_error) < 1e-12
    x = np.ones(A.shape[0])
    assert float(x @ (A @ x)) > 0.0
