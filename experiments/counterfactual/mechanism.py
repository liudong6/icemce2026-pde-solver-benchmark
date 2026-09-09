"""Offline spectral diagnostics; costs not claimed to be an online selector."""
from pathlib import Path
import csv,json
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh,eigs,LinearOperator,splu
from threadpoolctl import threadpool_limits
from pilot import field,matrix,rhs_vector,setup
from pilot import OUT

def main():
    rows=[]
    with threadpool_limits(limits=1):
        for geometry in ['connected','disconnected']:
            for average in ['arithmetic','harmonic']:
                n=64;contrast=1e4
                A=matrix(field(n,contrast,geometry),average)
                invroot=1/np.sqrt(A.diagonal())
                S=sparse.diags(invroot)@A@sparse.diags(invroot)
                vals,V=eigsh(S,k=8,sigma=0.,which='LM',tol=1e-10,v0=np.random.default_rng(719).normal(size=A.shape[0]))
                ix=np.argsort(vals);vals,V=vals[ix],V[:,ix]
                top=float(eigsh(S,k=1,which='LA',tol=1e-9,return_eigenvectors=False,v0=np.ones(A.shape[0]))[0])
                reflect=lambda v:v.reshape(n-2,n-2)[::-1,:].ravel()
                for j,lam in enumerate(vals):
                    v=V[:,j]
                    row=dict(geometry=geometry,average=average,n=n,contrast=contrast,method='jacobi',mode=j,
                        eigenvalue=float(lam),lambda_max=top,condition=top/vals[0],
                        eigen_residual=float(np.linalg.norm(S@v-lam*v)),reflection_parity=float(v@reflect(v)))
                    for rhs in ['ones','random','dipole']:
                        b=invroot*rhs_vector(n,rhs)
                        row['overlap_'+rhs]=float((v@b)**2/(b@b))
                    rows.append(row)
                np.random.seed(731)
                M,ml=setup(A,'amg0')
                BA=LinearOperator(A.shape,matvec=lambda x:M@(A@x),dtype=float)
                low,U=eigs(BA,k=4,which='SM',tol=1e-8,maxiter=10000,v0=np.ones(A.shape[0]))
                high=eigs(BA,k=1,which='LM',tol=1e-8,maxiter=10000,return_eigenvectors=False,v0=np.ones(A.shape[0]))
                for j,lam in enumerate(low):
                    assert abs(lam.imag)<1e-8
                    v=U[:,j].real
                    row=dict(geometry=geometry,average=average,n=n,contrast=contrast,method='amg0',mode=j,
                        eigenvalue=float(lam.real),lambda_max=float(high[0].real),condition=float(high[0].real/min(low.real)),
                        eigen_residual=float(np.linalg.norm(BA@v-lam.real*v)),reflection_parity=float(v@reflect(v)))
                    rows.append(row)
                # A-energy fraction left after exact first-level Galerkin correction of each inclusion indicator.
                from scipy.ndimage import label
                labels,ncomp=label(field(n,contrast,geometry)[1:-1,1:-1]>1)
                P=ml.levels[0].P
                coarse=splu((P.T@A@P).tocsc())
                for component in range(1,ncomp+1):
                    v=(labels.ravel()==component).astype(float)
                    e=v-P@coarse.solve(np.asarray(P.T@(A@v)))
                    rows.append(dict(geometry=geometry,average=average,n=n,contrast=contrast,method='coarse_energy',mode=component,
                        energy_fraction=float(e@(A@e)/(v@(A@v)))))
                print(geometry,average,'jacobi condition',top/vals[0], 'AMG condition',float(high[0].real/min(low.real)),flush=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/'mechanism.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print('mechanism complete',flush=True)

if __name__=='__main__':main()
