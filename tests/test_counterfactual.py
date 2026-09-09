import numpy as np
import pytest
from scipy import sparse
from pdescale.coefficients import coefficient_field
from pdescale.counterfactual import (
    matched_motif, embed_motif, assemble_field_operator, field_descriptors, reflection_audit,
)
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator


@pytest.mark.parametrize("average", ["arithmetic", "harmonic"])
@pytest.mark.parametrize("case", ["constant", "smooth_c3", "checkerboard_c100"])
def test_explicit_field_matches_independent_legacy_assembler(average, case):
    grid = Grid2D(13, 13)
    k = coefficient_field(grid.x, grid.y, case)
    actual = assemble_field_operator(k, face_average=average)
    expected = assemble_operator(grid, case, face_average=average)
    np.testing.assert_allclose(actual.toarray(), expected.toarray(), rtol=1e-14, atol=1e-10)


@pytest.mark.parametrize("average", ["arithmetic", "harmonic"])
def test_matrix_energy_equals_sum_of_face_flux_energies(average):
    rng = np.random.default_rng(381)
    k = np.exp(rng.normal(size=(9, 9)))
    u = np.zeros_like(k)
    u[1:-1, 1:-1] = rng.normal(size=(7, 7))
    v = u[1:-1, 1:-1].ravel()
    def face(a, b):
        return (a+b)/2 if average == "arithmetic" else 2*a*b/(a+b)
    expected = 8**2 * (np.sum(face(k[:-1], k[1:]) * np.diff(u, axis=0)**2)
                        + np.sum(face(k[:, :-1], k[:, 1:]) * np.diff(u, axis=1)**2))
    A = assemble_field_operator(k, face_average=average)
    assert np.isclose(v @ (A @ v), expected, rtol=1e-14)
    assert np.linalg.eigvalsh(A.toarray())[0] > 0


@pytest.mark.parametrize("n", [64, 96, 128, 192])
def test_exact_descriptor_match_and_translation_invariants(n):
    c = 1000.
    s = n//16
    fields = [embed_motif(matched_motif(g), n, c, shift=shift)
              for g in ["connected", "disconnected"] for shift in [(0, 0), (1, 0), (0, 1)]]
    descriptors = [field_descriptors(k) for k in fields]
    for d in descriptors:
        assert d['high_nodes'] == 12*s*s
        assert np.isclose(d['mean_k'], 1+(c-1)*12*s*s/(n*n))
        assert np.isclose(d['total_variation_proxy'], (c-1)*20*s/(n-1))
        assert np.isclose(d['grad_logk_inf'], np.sqrt(2)*(n-1)*np.log(c)/2)
    assert [d['components'] for d in descriptors] == [1, 1, 1, 2, 2, 2]


def test_reflection_invariance_and_krylov_parity_with_translation_control():
    n = 64
    k = embed_motif(matched_motif("disconnected"), n, 1000.)
    A = assemble_field_operator(k)
    x = np.linspace(0, 1, n)[1:-1]
    b = (np.sin(2*np.pi*x[:, None])*np.sin(np.pi*x[None, :])).ravel()
    audit = reflection_audit(A, b)
    assert audit['operator_reflection_defect'] < 1e-15
    assert audit['rhs_even_fraction'] < 1e-28
    assert np.isclose(audit['rhs_even_fraction']+audit['rhs_odd_fraction'], 1.)
    invroot = sparse.diags(1/np.sqrt(A.diagonal()))
    S = invroot @ A @ invroot
    v = invroot @ b
    for _ in range(8):
        v = S @ v
        v /= np.linalg.norm(v)
        reflected = v.reshape(n-2, n-2)[::-1].ravel()
        assert np.linalg.norm(v+reflected) < 1e-12
    shifted = assemble_field_operator(embed_motif(matched_motif("disconnected"), n, 1000., shift=(1, 0)))
    assert reflection_audit(shifted, b)['operator_reflection_defect'] > 0.01


def test_transpose_is_an_operator_and_rhs_permutation():
    n = 64
    k = embed_motif(matched_motif("connected"), n, 1000.)
    A = assemble_field_operator(k)
    rotated = assemble_field_operator(k.T)
    perm = np.arange((n-2)**2).reshape(n-2, n-2).T.ravel()
    difference = rotated - A[perm, :][:, perm]
    assert sparse.linalg.norm(difference) <= 1e-14*sparse.linalg.norm(A)


@pytest.mark.parametrize("kwargs", [{"n": 63}, {"contrast": 1}, {"shift": (100, 0)}, {"scale": 1}])
def test_invalid_geometry_rejected(kwargs):
    values = dict(n=64, contrast=1000.)
    values.update(kwargs)
    with pytest.raises(ValueError):
        embed_motif(matched_motif("connected"), **values)


def test_empirical_invariant_cost_floor_and_units():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'experiments/analyze_counterfactual.py'
    spec = importlib.util.spec_from_file_location('counterfactual_analysis', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = dict(n='192', geometry='disconnected', average='harmonic', rhs='dipole_x', stable=True)
    rows = [dict(base, variant='centered', jacobi_total=3., amg0_total=4., winner='jacobi'),
            dict(base, variant='shift_x', jacobi_total=6., amg0_total=2., winner='amg0')]
    result = module.translation_floors(rows)[0]
    assert np.isclose(result['empirical_minimum_mean_excess'], 1./6.)
    assert result['best_invariant_only_method'] == 'amg0'
    for r in rows:
        r['jacobi_total'] *= 1000
        r['amg0_total'] *= 1000
    assert np.isclose(module.translation_floors(rows)[0]['empirical_minimum_mean_excess'], 1./6.)
    rows[1]['jacobi_total'] = 1000.
    rows[1]['winner'] = 'jacobi'
    assert module.translation_floors(rows)[0]['empirical_minimum_mean_excess'] == 0.
