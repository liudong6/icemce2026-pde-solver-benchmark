from pathlib import Path
import csv,itertools,json,time,sys
import numpy as np
from threadpoolctl import threadpool_limits,threadpool_info
from pilot import field,matrix,rhs_vector
from confirmation import checked_solve
from pdescale.counterfactual import reflection_audit,embed_motif,matched_motif,assemble_field_operator
from pilot import OUT

def main():
    dest=OUT/'perturbation.csv'
    if dest.exists():raise FileExistsError(dest)
    config=dict(n=[128,192],contrast=1000.,shifts=[(0,0),(1,0),(2,0),(4,0),(0,1),(0,4)],
        alphas=[0.,1e-8,1e-6,1e-4,1e-2,1.],methods=['jacobi','amg0'],repeats=3,
        order_seed=373199,setup_seed=3701,average='harmonic',
        purpose='Prospectively specified symmetry perturbations after confirmation; not held-out policy evaluation.')
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (OUT/'perturbation_config.json').write_text(json.dumps(config,indent=2)+'\n')
        A=matrix(np.ones((16,16)),'harmonic')
        for method in config['methods']:checked_solve(A,rhs_vector(16,'ones'),method,719)
        jobs=[]
        for n in config['n']:
            jobs += [(n,shift,0.) for shift in config['shifts']]
            jobs += [(n,(0,0),alpha) for alpha in config['alphas'] if alpha]
        rng.shuffle(jobs)
        with dest.open('w',newline='') as f:
            writer=None
            for n,shift,alpha in jobs:
                k=field(n,config['contrast'],'disconnected',shift=shift)
                np.testing.assert_array_equal(k,embed_motif(matched_motif('disconnected'),n,config['contrast'],shift=shift))
                A=matrix(k,'harmonic')
                assert (A!=assemble_field_operator(k)).nnz==0
                b=rhs_vector(n,'dipole')+alpha*rhs_vector(n,'ones');b/=np.linalg.norm(b)
                # Offline audit timed separately and never added to baseline solve costs.
                timings=[]
                for _ in range(5):
                    t=time.perf_counter();audit=reflection_audit(A,b);timings.append(time.perf_counter()-t)
                for repeat in range(config['repeats']):
                    methods=config['methods'].copy();rng.shuffle(methods)
                    for order,method in enumerate(methods):
                        row=dict(n=n,contrast=config['contrast'],shift_x=shift[0],shift_y=shift[1],alpha=alpha,
                            repeat=repeat,order=order,method=method,seed=config['setup_seed']+repeat,
                            audit_seconds=float(np.median(timings)),**audit)
                        row.update(checked_solve(A,b,method,row['seed']))
                        if writer is None:writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                        writer.writerow(row);f.flush()
                print(n,shift,alpha,'done',flush=True)
    print('perturbation complete',flush=True)

if __name__=='__main__':main()
