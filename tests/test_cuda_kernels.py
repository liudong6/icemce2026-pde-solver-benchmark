import numpy as np
import pytest


def _jacobi_reference(u0, steps):
    u = np.asarray(u0, dtype=float).copy()
    work = u.copy()
    for _ in range(steps):
        work[:, :] = u
        work[1:-1, 1:-1] = 0.25 * (
            u[:-2, 1:-1] + u[2:, 1:-1] + u[1:-1, :-2] + u[1:-1, 2:]
        )
        u, work = work, u
    return u


def test_cuda_jacobi_steps_matches_cpu_reference():
    from pdescale.cuda_kernels import cuda_jacobi_steps

    rng = np.random.default_rng(2)
    u0 = np.zeros((256, 256), dtype=np.float64)
    u0[1:-1, 1:-1] = rng.normal(size=(254, 254))

    actual = cuda_jacobi_steps(u0, steps=5)
    expected = _jacobi_reference(u0, steps=5)

    assert np.allclose(actual, expected, rtol=1e-12, atol=1e-12)


def test_cuda_jacobi_steps_rejects_invalid_inputs():
    from pdescale.cuda_kernels import cuda_jacobi_steps

    with pytest.raises(ValueError, match="2D"):
        cuda_jacobi_steps(np.zeros(8), steps=1)
    with pytest.raises(ValueError, match="non-negative"):
        cuda_jacobi_steps(np.zeros((8, 8)), steps=-1)
