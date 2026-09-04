def test_matrix_free_matches_assembled_constant_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import matrix_free_apply
    from pdescale.operators import assemble_operator

    g = Grid2D(20, 18)
    A = assemble_operator(g, "constant")
    rng = np.random.default_rng(42)
    x = rng.normal(size=A.shape[0])
    y_assembled = A @ x
    y_free = matrix_free_apply(x, g, "constant")
    rel = np.linalg.norm(y_assembled - y_free) / np.linalg.norm(y_assembled)
    assert rel < 1e-11


def test_matrix_free_matches_assembled_smooth_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import matrix_free_apply
    from pdescale.operators import assemble_operator

    g = Grid2D(20, 20)
    A = assemble_operator(g, "smooth")
    rng = np.random.default_rng(43)
    x = rng.normal(size=A.shape[0])
    y_assembled = A @ x
    y_free = matrix_free_apply(x, g, "smooth")
    rel = np.linalg.norm(y_assembled - y_free) / np.linalg.norm(y_assembled)
    assert rel < 1e-11


def test_matrix_free_matches_harmonic_assembled_jump_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import matrix_free_apply
    from pdescale.operators import assemble_operator

    g = Grid2D(18, 18)
    A = assemble_operator(g, "layered_c100", face_average="harmonic")
    rng = np.random.default_rng(44)
    x = rng.normal(size=A.shape[0])
    y_assembled = A @ x
    y_free = matrix_free_apply(x, g, "layered_c100", face_average="harmonic")
    rel = np.linalg.norm(y_assembled - y_free) / np.linalg.norm(y_assembled)
    assert rel < 1e-11


def test_linear_operator_has_expected_shape():
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import make_linear_operator

    g = Grid2D(9, 11)
    op = make_linear_operator(g, "constant")
    assert op.shape == ((9 - 2) * (11 - 2), (9 - 2) * (11 - 2))
