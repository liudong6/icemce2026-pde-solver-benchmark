"""Exploratory matched-geometry screen; never overwrites archived measurements."""
from pathlib import Path
import csv, hashlib, itertools, json, os, platform, sys, time
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import scipy
from scipy import sparse
from scipy.sparse.linalg import cg, LinearOperator
from scipy.ndimage import label
import pyamg
from threadpoolctl import threadpool_limits, threadpool_info
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator

OUT = Path(os.environ.get('PDESCALE_COUNTERFACTUAL_OUTPUT', str(ROOT / 'results/raw/counterfactual_rerun'))).resolve()
OUT.mkdir(parents=True, exist_ok=True)

def field(n, contrast, geometry, *, tiles=1, shift=(0, 0), rotate=False):
    motif = np.zeros((2, 8), dtype=bool)
    if geometry == 'connected':
        motif[0, :4] = True
        motif[1, :] = True
    elif geometry == 'disconnected':
        motif[:, :3] = True
        motif[:, 5:] = True
    else:
        raise ValueError(geometry)
    scale = max(2, n // (16 * tiles))
    block = np.repeat(np.repeat(motif, scale, 0), scale, 1)
    if rotate:
        block = block.T
    mask = np.zeros((n, n), bool)
    for i in range(tiles):
        for j in range(tiles):
            x = (2*i+1)*n//(2*tiles)-block.shape[0]//2+shift[0]
            y = (2*j+1)*n//(2*tiles)-block.shape[1]//2+shift[1]
            if min(x, y) < 2 or x+block.shape[0] > n-2 or y+block.shape[1] > n-2:
                raise ValueError('geometry too near boundary')
            mask[x:x+block.shape[0], y:y+block.shape[1]] |= block
    return np.where(mask, float(contrast), 1.)

def matrix(k, average):
    n = k.shape[0]
    if k.shape != (n, n) or not np.all(np.isfinite(k)) or np.any(k <= 0):
        raise ValueError('positive square field required')
    def face(a, b):
        if average == 'harmonic':
            return 2*a*b/(a+b)
        if average == 'arithmetic':
            return .5*(a+b)
        raise ValueError(average)
    fx = face(k[:-1, :], k[1:, :])*(n-1)**2
    fy = face(k[:, :-1], k[:, 1:])*(n-1)**2
    m = n-2
    ix = np.arange(m*m).reshape(m, m)
    diagonal = fx[:-1, 1:-1]+fx[1:, 1:-1]+fy[1:-1, :-1]+fy[1:-1, 1:]
    a, b = ix[:-1, :].ravel(), ix[1:, :].ravel()
    c, d = ix[:, :-1].ravel(), ix[:, 1:].ravel()
    vx, vy = -fx[1:-1, 1:-1].ravel(), -fy[1:-1, 1:-1].ravel()
    rows = np.concatenate([ix.ravel(), a, b, c, d])
    cols = np.concatenate([ix.ravel(), b, a, d, c])
    vals = np.concatenate([diagonal.ravel(), vx, vx, vy, vy])
    return sparse.coo_matrix((vals, (rows, cols)), shape=(m*m, m*m)).tocsr()

def descriptors(k):
    n = k.shape[0]
    gx, gy = np.gradient(np.log(k), 1/(n-1), 1/(n-1))
    return dict(high_nodes=int(np.count_nonzero(k > 1)), mean=float(k.mean()),
                tv=float((np.abs(np.diff(k, axis=0)).sum()+np.abs(np.diff(k, axis=1)).sum())/(n-1)),
                grad=float(np.hypot(gx, gy).max()), components=int(label(k > 1)[1]))

def rhs_vector(n, kind, seed=991):
    if kind == 'ones':
        b = np.ones((n-2)**2)
    elif kind == 'random':
        b = np.random.default_rng(seed).standard_normal((n-2)**2)
    elif kind == 'dipole':
        x = np.linspace(0, 1, n)[1:-1]
        b = (np.sin(2*np.pi*x[:, None])*np.sin(np.pi*x[None, :])).ravel()
    else:
        raise ValueError(kind)
    return b/np.linalg.norm(b)

def setup(A, method):
    if method == 'cg':
        return None, None
    if method == 'jacobi':
        inv = 1/A.diagonal()
        return LinearOperator(A.shape, matvec=lambda x: inv*x, dtype=float), None
    theta = 0. if method == 'amg0' else .25
    ml = pyamg.smoothed_aggregation_solver(A, strength=('symmetric', {'theta': theta}),
        aggregate='standard', smooth=('jacobi', {'omega': 4./3.}),
        presmoother=('block_gauss_seidel', {'sweep': 'symmetric'}),
        postsmoother=('block_gauss_seidel', {'sweep': 'symmetric'}),
        max_levels=10, max_coarse=10, keep=True)
    return ml.aspreconditioner(cycle='V'), ml

def solve(A, b, method, seed):
    np.random.seed(seed)
    t = time.perf_counter()
    M, ml = setup(A, method)
    tsetup = time.perf_counter()-t
    iterations = 0
    def callback(x):
        nonlocal iterations
        iterations += 1
    t = time.perf_counter()
    x, info = cg(A, b, M=M, rtol=1e-8, atol=0., maxiter=8000, callback=callback)
    tsolve = time.perf_counter()-t
    residual = float(np.linalg.norm(A@x-b)/np.linalg.norm(b))
    return dict(setup=tsetup, solve=tsolve, total=tsetup+tsolve, iterations=iterations,
                info=int(info), residual=residual, accepted=bool(info==0 and residual<=1e-7),
                levels=len(ml.levels) if ml else 0,
                complexity=float(ml.operator_complexity()) if ml else 0.)

def validate():
    from pdescale.coefficients import coefficient_field
    for n in [8, 17]:
        g = Grid2D(n, n)
        for case in ['constant', 'smooth_c3', 'checkerboard_c100']:
            k = coefficient_field(g.x, g.y, case)
            for average in ['arithmetic', 'harmonic']:
                a, b = matrix(k, average), assemble_operator(g, case, face_average=average)
                assert np.allclose(a.toarray(), b.toarray(), rtol=1e-14, atol=1e-10)
                assert np.linalg.eigvalsh(a.toarray())[0] > 0
    for n, contrast in itertools.product([64,128], [100.,1e4,1e6]):
        a,b = [descriptors(field(n,contrast,g)) for g in ['connected','disconnected']]
        for key in ['high_nodes','mean','tv','grad']:
            assert np.isclose(a[key],b[key],rtol=1e-14), (n,key,a,b)
        assert (a['components'],b['components']) == (1,2)

def main():
    validate()
    dest = OUT/'pilot.csv'
    if dest.exists():
        raise FileExistsError('preserve prior run; use a distinct output for a new experiment')
    config = dict(n=[64,128], contrast=[100.,1e4,1e6], geometry=['connected','disconnected'],
        average=['arithmetic','harmonic'], rhs=['ones','random','dipole'], repeats=2,
        methods=['cg','jacobi','amg0','amg025'], seed=20260908,
        thread_limit=1, status='exploratory', python=sys.version, platform=platform.platform(),
        packages=dict(numpy=np.__version__, scipy=scipy.__version__, pyamg=pyamg.__version__),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with threadpool_limits(limits=1):
        config['threadpools'] = threadpool_info()
        (OUT/'pilot_config.json').write_text(json.dumps(config, indent=2)+'\n')
        A = matrix(np.ones((16,16)), 'harmonic')
        for method in config['methods']:
            solve(A, rhs_vector(16,'ones'), method, 731)
        jobs = list(itertools.product(config['n'],config['contrast'],config['geometry'],config['average']))
        rng = np.random.default_rng(config['seed'])
        rng.shuffle(jobs)
        with dest.open('w',newline='') as f:
            writer = None
            for n,contrast,geometry,average in jobs:
                k = field(n,contrast,geometry)
                A = matrix(k,average)
                measurements = list(itertools.product(config['rhs'],range(config['repeats']),config['methods']))
                rng.shuffle(measurements)
                for order,(rhs,repeat,method) in enumerate(measurements):
                    row = dict(n=n, contrast=contrast, geometry=geometry, average=average,
                               rhs=rhs, repeat=repeat, method=method, order=order,
                               seed=731+repeat, **descriptors(k))
                    row.update(solve(A,rhs_vector(n,rhs),method,731+repeat))
                    if writer is None:
                        writer = csv.DictWriter(f,fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    f.flush()
                print(n,contrast,geometry,average,'done',flush=True)
    print('pilot complete',flush=True)

if __name__ == '__main__':
    main()
