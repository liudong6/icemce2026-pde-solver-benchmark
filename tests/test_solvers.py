def test_direct_solver_returns_low_residual_result():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator
    from pdescale.solvers import SolveResult, solve_system

    g = Grid2D(16, 16)
    A = assemble_operator(g, "constant")
    b = np.ones(A.shape[0])
    result = solve_system(A, b, method="direct", tol=1e-10, maxiter=100)
    assert isinstance(result, SolveResult)
    assert result.converged
    assert result.method == "direct"
    assert result.solution.shape == b.shape
    assert result.residual_norm < 1e-10
    assert result.setup_seconds >= 0.0
    assert result.solve_seconds >= 0.0


def test_cg_solves_constant_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator
    from pdescale.solvers import solve_system

    g = Grid2D(32, 32)
    A = assemble_operator(g, "constant")
    b = np.ones(A.shape[0])
    result = solve_system(A, b, method="cg", tol=1e-8, maxiter=5000)
    assert result.converged
    assert result.iterations > 0
    assert result.residual_norm < 1e-8
    assert len(result.residual_history) == result.iterations


def test_jacobi_pcg_converges_and_records_setup_time():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator
    from pdescale.solvers import solve_system

    g = Grid2D(32, 32)
    A = assemble_operator(g, "smooth")
    b = np.ones(A.shape[0])
    result = solve_system(A, b, method="jacobi-pcg", tol=1e-8, maxiter=5000)
    assert result.converged
    assert result.iterations > 0
    assert result.setup_seconds >= 0.0
    assert result.residual_norm < 1e-8


def test_amg_pcg_converges_on_smooth_case():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator
    from pdescale.solvers import solve_system

    g = Grid2D(32, 32)
    A = assemble_operator(g, "smooth")
    b = np.ones(A.shape[0])
    result = solve_system(A, b, method="amg-pcg", tol=1e-8, maxiter=1000)
    assert result.converged
    assert result.iterations > 0
    assert result.setup_seconds > 0.0
    assert result.residual_norm < 1e-8


def test_matrix_free_cg_matches_assembled_direct_solution():
    import numpy as np
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import make_linear_operator
    from pdescale.operators import assemble_operator
    from pdescale.solvers import solve_system

    g = Grid2D(20, 20)
    A = assemble_operator(g, "constant")
    op = make_linear_operator(g, "constant")
    b = np.ones(A.shape[0])
    direct = solve_system(A, b, method="direct", tol=1e-12, maxiter=100)
    iterative = solve_system(op, b, method="cg", tol=1e-10, maxiter=5000)
    rel = np.linalg.norm(iterative.solution - direct.solution) / np.linalg.norm(direct.solution)
    assert iterative.converged
    assert rel < 1e-8


def test_unknown_solver_method_raises_value_error():
    import numpy as np
    import pytest
    from pdescale.grid import Grid2D
    from pdescale.operators import assemble_operator
    from pdescale.solvers import solve_system

    g = Grid2D(8, 8)
    A = assemble_operator(g, "constant")
    b = np.ones(A.shape[0])
    with pytest.raises(ValueError, match="unknown solver method"):
        solve_system(A, b, method="mystery", tol=1e-8, maxiter=100)
