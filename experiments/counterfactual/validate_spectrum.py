from pathlib import Path
import json
import numpy as np
from scipy.sparse.linalg import LinearOperator,eigs
from threadpoolctl import threadpool_limits
from pilot import field,matrix,setup
from pilot import OUT
rows=[]
with threadpool_limits(limits=1):
    for geometry in ['connected','disconnected']:
        for average in ['arithmetic','harmonic']:
            A=matrix(field(32,1e4,geometry),average)
            np.random.seed(731)
            M,ml=setup(A,'amg0')
            B=M@np.eye(A.shape[0])
            symmetry=float(np.linalg.norm(B-B.T)/np.linalg.norm(B))
            assert symmetry < 1e-11
            L=np.linalg.cholesky((B+B.T)/2)
            C=L.T@(A@L)
            vals=np.linalg.eigvalsh((C+C.T)/2)
            assert vals[0]>0
            # Dense B was independently constructed by applying every basis vector.
            # Using its dense BA here isolates ARPACK validation from V-cycle cost.
            dense_BA = B @ A.toarray()
            BA=LinearOperator(A.shape,matvec=lambda v:dense_BA@v,dtype=float)
            starts=[np.ones(A.shape[0]),np.random.default_rng(291).normal(size=A.shape[0])]
            for index,v0 in enumerate(starts):
                low,U=eigs(BA,k=4,which='SM',tol=1e-10,maxiter=10000,v0=v0)
                # The top spectrum is tightly clustered near one. A 1e-10 stopping
                # request failed to converge in the first attempt; use 1e-7 and a
                # larger Arnoldi space, retaining the dense exact comparison.
                high=eigs(BA,k=1,which='LM',tol=1e-7,ncv=60,maxiter=2000,v0=v0,return_eigenvectors=False)
                low_error=abs(float(min(low.real))/vals[0]-1)
                high_error=abs(float(high[0].real)/vals[-1]-1)
                assert low_error<1e-5 and high_error<1e-5
                rows.append(dict(geometry=geometry,average=average,n=32,start=index,
                    B_symmetry_defect=symmetry,dense_min=float(vals[0]),dense_max=float(vals[-1]),
                    low_relative_error=low_error,high_relative_error=high_error))
            print(geometry,average,'dense validation passed',flush=True)
(OUT/'spectrum_validation.json').write_text(json.dumps(rows,indent=2)+'\n')
