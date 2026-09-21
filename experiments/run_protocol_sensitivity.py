"""Paired residual-monitor/count-only calibration; existing CSVs are never overwritten."""
from pathlib import Path
import argparse,csv,hashlib,itertools,json,sys,time
import numpy as np
import pyamg  # deliberately warm before all setup timers
from scipy.sparse.linalg import cg
from threadpoolctl import threadpool_limits,threadpool_info

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator
from pdescale.benchmark import benchmark_rhs
from pdescale.metadata import capture_metadata
from pdescale.solvers import _jacobi_preconditioner,_amg_preconditioner,_relative_residual

def measured_solve(A,b,method,mode,seed):
    if method not in {'cg','jacobi-pcg','amg-pcg'} or mode not in {'monitored','count-only'}:
        raise ValueError((method,mode))
    np.random.seed(seed)
    start=time.perf_counter()
    M=_jacobi_preconditioner(A) if method=='jacobi-pcg' else _amg_preconditioner(A) if method=='amg-pcg' else None
    setup=time.perf_counter()-start
    history=[];iterations=0
    def monitor(x):
        history.append(_relative_residual(A,b,x))
    def count(x):
        nonlocal iterations
        iterations+=1
    start=time.perf_counter()
    x,info=cg(A,b,M=M,rtol=1e-8,atol=0,maxiter=12000,callback=monitor if mode=='monitored' else count)
    elapsed=time.perf_counter()-start
    residual=_relative_residual(A,b,x)
    return {'setup_seconds':setup,'solve_seconds':elapsed,'total_seconds':setup+elapsed,
            'iterations':len(history) if mode=='monitored' else iterations,'info':int(info),
            'residual_norm':residual,'accepted':bool(info==0 and residual<=1e-8),
            'solution_sha256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/raw/protocol_sensitivity_rerun')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    config={'sizes':[64,128,256],'cases':['constant','inclusion_c100','checkerboard_c100'],
            'methods':['cg','jacobi-pcg','amg-pcg'],'modes':['monitored','count-only'],
            'repeats':7,'face_average':'arithmetic','rhs':'ones','rtol':1e-8,'atol':0,
            'maxiter':12000,'acceptance_residual':1e-8,'order_seed':20092026,'setup_seed':200920,
            'warm_import':True,'blas_threads':1,'measured_count':378,
            'limitations':'One machine; power/thermal/OS activity not controlled; no reconstruction of historical import/thread/order effects.'}
    config['source_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'experiments/protocol_sensitivity.md',ROOT/'src/pdescale/solvers.py',ROOT/'src/pdescale/operators.py',ROOT/'src/pdescale/benchmark.py']}
    (args.output/'environment.json').write_text(json.dumps(capture_metadata(),indent=2)+'\n')
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (args.output/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        warmgrid=Grid2D(16,16);warm=assemble_operator(warmgrid,'constant',face_average='arithmetic');warmb=benchmark_rhs(warmgrid,'constant','ones')
        for method,mode in itertools.product(config['methods'],config['modes']):measured_solve(warm,warmb,method,mode,1)
        systems={}
        for case,n in itertools.product(config['cases'],config['sizes']):
            grid=Grid2D(n,n);systems[case,n]=(assemble_operator(grid,case,face_average='arithmetic'),benchmark_rhs(grid,case,'ones'))
        with (args.output/'timings.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=None
            for repeat in range(config['repeats']):
                jobs=list(itertools.product(config['cases'],config['sizes'],config['methods'],config['modes']));rng.shuffle(jobs)
                for order,(case,n,method,mode) in enumerate(jobs):
                    row={'coefficient_case':case,'n':n,'method':method,'mode':mode,'repeat':repeat,'order':order,'seed':config['setup_seed']+repeat}
                    row.update(measured_solve(*systems[case,n],method,mode,row['seed']))
                    if writer is None:writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader()
                    writer.writerow(row);stream.flush()
                print(f'repeat {repeat+1}/7 complete',flush=True)
    print('all 378 calibration solves recorded',flush=True)

if __name__=='__main__':main()
