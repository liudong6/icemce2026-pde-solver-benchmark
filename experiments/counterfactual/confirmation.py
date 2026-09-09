from pathlib import Path
import csv, hashlib, itertools, json, platform, sys, time
import numpy as np
from scipy.sparse.linalg import cg
from threadpoolctl import threadpool_limits,threadpool_info
from pilot import field,matrix,descriptors,rhs_vector,setup,solve
from pilot import OUT

def checked_solve(A,b,method,seed):
    np.random.seed(seed)
    t=time.perf_counter();M,ml=setup(A,method);ts=time.perf_counter()-t
    iterations=0
    def callback(x):
        nonlocal iterations
        iterations+=1
    t=time.perf_counter()
    x,info=cg(A,b,M=M,rtol=1e-9,atol=0,maxiter=8000,callback=callback)
    elapsed=time.perf_counter()-t
    residual=float(np.linalg.norm(A@x-b)/np.linalg.norm(b))
    return dict(setup=ts,solve=elapsed,total=ts+elapsed,iterations=iterations,info=int(info),
        residual=residual,accepted=bool(info==0 and residual<=1e-8),
        complexity=float(ml.operator_complexity()) if ml else 0.)

def main():
    dest=OUT/'confirmation.csv'
    if dest.exists():raise FileExistsError(dest)
    config=dict(n=[96,128,192],contrast=1000.,geometry=['connected','disconnected'],
        variants=['centered','transpose','shift_x'],average=['arithmetic','harmonic'],
        rhs=['ones','dipole_x','dipole_y','random'],repeats=5,methods=['jacobi','amg0'],
        setup_seed=1701,order_seed=81173,rtol=1e-9,residual_acceptance=1e-8,
        python=sys.version,platform=platform.platform(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (OUT/'confirmation_config.json').write_text(json.dumps(config,indent=2)+'\n')
        A=matrix(np.ones((16,16)),'harmonic')
        for method in config['methods']:checked_solve(A,rhs_vector(16,'ones'),method,719)
        jobs=list(itertools.product(config['n'],config['geometry'],config['variants'],config['average']))
        rng.shuffle(jobs)
        with dest.open('w',newline='') as f:
            writer=None
            for n,geometry,variant,average in jobs:
                k=field(n,config['contrast'],geometry,shift=(1,0) if variant=='shift_x' else (0,0))
                if variant=='transpose':k=k.T.copy()
                A=matrix(k,average)
                rhss={}
                for rhs in config['rhs']:
                    b=rhs_vector(n, 'dipole' if rhs.startswith('dipole') else rhs).reshape(n-2,n-2)
                    if rhs=='dipole_y':b=b.T
                    if variant=='transpose':b=b.T
                    rhss[rhs]=b.ravel().copy()
                # Repeat is the blocking unit; within each repeat randomise RHS and method order.
                for repeat in range(config['repeats']):
                    tasks=list(itertools.product(config['rhs'],config['methods']));rng.shuffle(tasks)
                    for order,(rhs,method) in enumerate(tasks):
                        row=dict(n=n,contrast=config['contrast'],geometry=geometry,variant=variant,
                            average=average,rhs=rhs,repeat=repeat,order=order,method=method,
                            seed=config['setup_seed']+repeat,**descriptors(k))
                        row.update(checked_solve(A,rhss[rhs],method,row['seed']))
                        if writer is None:
                            writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                        writer.writerow(row);f.flush()
                print(n,geometry,variant,average,'done',flush=True)
    print('confirmation complete',flush=True)

if __name__=='__main__':main()
