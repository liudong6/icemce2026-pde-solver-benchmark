"""Controlled comparison of existing AMG configurations; separate rerun outputs."""
from pathlib import Path
import csv,hashlib,itertools,json,os,sys,time
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(os.environ.get('PDESCALE_COUNTERFACTUAL_OUTPUT',str(ROOT/'results/raw/counterfactual_rerun'))).resolve()
HERE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'experiments/counterfactual'))
os.environ['PDESCALE_COUNTERFACTUAL_OUTPUT']=str(HERE)
import numpy as np
import pyamg
from scipy.sparse.linalg import cg
from threadpoolctl import threadpool_limits,threadpool_info
from pdescale.counterfactual import matched_motif,embed_motif,assemble_field_operator
from pilot import rhs_vector,setup

def prepare(A,method):
    if method!='rs025':return setup(A,method)
    ml=pyamg.ruge_stuben_solver(A,strength=('classical',{'theta':.25}),
        CF=('RS',{'second_pass':False}),interpolation='classical',
        presmoother=('gauss_seidel',{'sweep':'symmetric'}),
        postsmoother=('gauss_seidel',{'sweep':'symmetric'}),
        max_levels=10,max_coarse=10,keep=True,coarse_solver='pinv')
    return ml.aspreconditioner(cycle='V'),ml

def solve(A,b,method,seed):
    np.random.seed(seed)
    t=time.perf_counter();M,ml=prepare(A,method);ts=time.perf_counter()-t
    iterations=0
    def count(x):
        nonlocal iterations
        iterations+=1
    t=time.perf_counter();x,info=cg(A,b,M=M,rtol=1e-9,atol=0,maxiter=8000,callback=count)
    elapsed=time.perf_counter()-t
    residual=float(np.linalg.norm(A@x-b)/np.linalg.norm(b))
    return dict(setup=ts,solve=elapsed,total=ts+elapsed,iterations=iterations,info=int(info),
                residual=residual,accepted=bool(info==0 and residual<=1e-8),
                complexity=float(ml.operator_complexity()) if ml else 0.,levels=len(ml.levels) if ml else 0)

def main():
    dest=HERE/'portfolio.csv'
    if dest.exists():raise FileExistsError(dest)
    config=dict(n=[128,192],contrast=1000.,fields=[['connected',0],['disconnected',0],['disconnected',1]],
                rhs=['odd_x','random'],methods=['jacobi','amg0','amg025','rs025'],repeats=5,
                setup_seed=12401,order_seed=94218,rtol=1e-9,residual_acceptance=1e-8,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                protocol_sha256='ce5ae6865854d51eadadcc0062f7c7de72bb3c45ed45f028558d64240660d171')
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (HERE/'portfolio_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
        checks=[]
        for geometry in ['connected','disconnected']:
            A=assemble_field_operator(embed_motif(matched_motif(geometry),32,1000.))
            for method in config['methods']:
                np.random.seed(42);M,ml=prepare(A,method);B=M@np.eye(A.shape[0])
                asym=float(np.linalg.norm(B-B.T)/np.linalg.norm(B))
                mineig=float(np.linalg.eigvalsh((B+B.T)/2)[0])
                assert asym<1e-10 and mineig>0,(geometry,method,asym,mineig)
                checks.append(dict(geometry=geometry,method=method,relative_asymmetry=asym,min_eigenvalue=mineig))
        (HERE/'portfolio_spd_checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
        warm=assemble_field_operator(np.ones((16,16)))
        for method in config['methods']:solve(warm,rhs_vector(16,'ones'),method,1)
        jobs=list(itertools.product(config['n'],config['fields']));rng.shuffle(jobs)
        with dest.open('w',newline='',encoding='utf-8') as f:
            writer=None
            for n,(geometry,shift) in jobs:
                A=assemble_field_operator(embed_motif(matched_motif(geometry),n,1000.,shift=(shift,0)))
                rhss={'odd_x':rhs_vector(n,'dipole'),'random':rhs_vector(n,'random',991)}
                for repeat in range(config['repeats']):
                    tasks=list(itertools.product(config['rhs'],config['methods']));rng.shuffle(tasks)
                    for order,(rhs,method) in enumerate(tasks):
                        row=dict(n=n,contrast=1000.,geometry=geometry,shift=shift,rhs=rhs,
                                 method=method,repeat=repeat,order=order,seed=config['setup_seed']+repeat)
                        row.update(solve(A,rhss[rhs],method,row['seed']))
                        if writer is None:writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                        writer.writerow(row);f.flush()
                print(n,geometry,shift,'done',flush=True)
    print('portfolio complete',flush=True)

if __name__=='__main__':main()
