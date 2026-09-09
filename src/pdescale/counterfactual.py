"""Matched coefficient fields and symmetry diagnostics for controlled solver audits.

These utilities construct counterexamples and test invariant subspaces. They are
not an automatic solver selector or a new discretisation/preconditioner.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.ndimage import label


def matched_motif(geometry: str) -> np.ndarray:
    """Return a 12-cell, perimeter-20 motif with one or two components."""
    motif = np.zeros((2, 8), dtype=bool)
    if geometry == "connected":
        motif[0, :4] = True
        motif[1, :] = True
    elif geometry == "disconnected":
        motif[:, :3] = True
        motif[:, 5:] = True
    else:
        raise ValueError("geometry must be connected or disconnected")
    return motif


def embed_motif(
    motif: np.ndarray,
    n: int,
    contrast: float,
    *,
    scale: int | None = None,
    shift: tuple[int, int] = (0, 0),
) -> np.ndarray:
    """Dilate and center a binary motif, retaining two low boundary-node layers.

    Even grid and block dimensions are required so that an unshifted symmetric
    motif is exactly symmetric about the physical domain center.
    """
    a = np.asarray(motif)
    if a.ndim != 2 or not np.all((a == 0) | (a == 1)) or not a.any():
        raise ValueError("motif must be a nonempty binary 2D array")
    if not isinstance(n, (int, np.integer)) or n < 32 or n % 2:
        raise ValueError("n must be an even integer at least 32")
    if not np.isfinite(contrast) or contrast <= 1:
        raise ValueError("contrast must be finite and greater than one")
    s = n // 16 if scale is None else scale
    if not isinstance(s, (int, np.integer)) or s < 2:
        raise ValueError("scale must be an integer at least two")
    if len(shift) != 2 or any(not isinstance(v, (int, np.integer)) for v in shift):
        raise ValueError("shift must contain two integers")
    block = np.repeat(np.repeat(a.astype(bool), s, 0), s, 1)
    if any(length % 2 for length in block.shape):
        raise ValueError("dilated block dimensions must be even for exact centering")
    x = n // 2 - block.shape[0] // 2 + shift[0]
    y = n // 2 - block.shape[1] // 2 + shift[1]
    if min(x, y) < 2 or x + block.shape[0] > n - 2 or y + block.shape[1] > n - 2:
        raise ValueError("motif violates the two-layer boundary margin")
    k = np.ones((n, n), dtype=float)
    k[x:x + block.shape[0], y:y + block.shape[1]] = np.where(block, contrast, 1.)
    return k


def _positive_square_field(k: np.ndarray) -> np.ndarray:
    k = np.asarray(k, dtype=float)
    if (k.ndim != 2 or k.shape[0] != k.shape[1] or k.shape[0] < 3
            or not np.all(np.isfinite(k)) or np.any(k <= 0)):
        raise ValueError("a finite, positive square coefficient field is required")
    return k


def assemble_field_operator(k: np.ndarray, *, face_average: str = "harmonic") -> sparse.csr_matrix:
    """Assemble the existing conservative nodal operator for an explicit field.

    The domain is the unit square and Dirichlet boundary unknowns are eliminated.
    This vectorised construction is checked against the existing loop assembler.
    """
    k = _positive_square_field(k)
    n = k.shape[0]
    if face_average == "harmonic":
        face = lambda a, b: 2. * a * b / (a + b)
    elif face_average == "arithmetic":
        face = lambda a, b: .5 * (a + b)
    else:
        raise ValueError("face_average must be arithmetic or harmonic")
    fx = face(k[:-1, :], k[1:, :]) * (n - 1)**2
    fy = face(k[:, :-1], k[:, 1:]) * (n - 1)**2
    m = n - 2
    ix = np.arange(m * m).reshape(m, m)
    diagonal = fx[:-1, 1:-1] + fx[1:, 1:-1] + fy[1:-1, :-1] + fy[1:-1, 1:]
    a, b = ix[:-1, :].ravel(), ix[1:, :].ravel()
    c, d = ix[:, :-1].ravel(), ix[:, 1:].ravel()
    vx, vy = -fx[1:-1, 1:-1].ravel(), -fy[1:-1, 1:-1].ravel()
    rows = np.concatenate([ix.ravel(), a, b, c, d])
    cols = np.concatenate([ix.ravel(), b, a, d, c])
    values = np.concatenate([diagonal.ravel(), vx, vx, vy, vy])
    return sparse.coo_matrix((values, (rows, cols)), shape=(m*m, m*m)).tocsr()


def field_descriptors(k: np.ndarray) -> dict[str, float | int]:
    """Return existing scalar descriptors plus explicit component information.

    Components use axis-adjacent (four-neighbour) connectivity and k>min(k).
    Component interpretation is intended for these binary coefficient fields.
    """
    k = _positive_square_field(k)
    n = k.shape[0]
    gx, gy = np.gradient(np.log(k), 1. / (n - 1), 1. / (n - 1), edge_order=1)
    labels, count = label(k > k.min())
    sizes = np.bincount(labels.ravel())[1:]
    return {
        "n": n,
        "contrast": float(k.max() / k.min()),
        "high_nodes": int(np.count_nonzero(labels)),
        "mean_k": float(k.mean()),
        "total_variation_proxy": float((np.abs(np.diff(k, axis=0)).sum()
                                          + np.abs(np.diff(k, axis=1)).sum()) / (n - 1)),
        "grad_logk_inf": float(np.hypot(gx, gy).max()),
        "components": int(count),
        "largest_component_nodes": int(sizes.max()) if count else 0,
    }


def reflection_audit(A: sparse.spmatrix, b: np.ndarray, *, axis: int = 0) -> dict[str, float]:
    """Measure operator reflection invariance and source parity, without a solve.

    The source's even/odd energy fractions sum to one. A zero commutator and
    one zero parity fraction certify a restricted Krylov subspace only in exact
    arithmetic (and for a preconditioner commuting with the same reflection).
    """
    b = np.asarray(b, dtype=float)
    if b.ndim != 1 or not np.all(np.isfinite(b)) or np.linalg.norm(b) == 0:
        raise ValueError("b must be a finite nonzero vector")
    m = int(np.sqrt(b.size))
    if m*m != b.size or A.shape != (b.size, b.size) or axis not in (0, 1):
        raise ValueError("square interior grid and axis 0 or 1 required")
    A = sparse.csr_matrix(A)
    perm = np.flip(np.arange(b.size).reshape(m, m), axis=axis).ravel()
    difference = A[perm, :][:, perm] - A
    norm = float(sparse.linalg.norm(A))
    if not np.isfinite(norm) or norm == 0:
        raise ValueError("A must have a finite nonzero norm")
    reflected = b[perm]
    denominator = float(b @ b)
    return {
        "operator_reflection_defect": float(sparse.linalg.norm(difference) / norm),
        "rhs_even_fraction": float(np.linalg.norm(.5 * (b + reflected))**2 / denominator),
        "rhs_odd_fraction": float(np.linalg.norm(.5 * (b - reflected))**2 / denominator),
    }
