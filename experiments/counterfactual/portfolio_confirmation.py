"""Interleaved field/source/method confirmation; all seven repeats are retained."""
from pathlib import Path
import csv,hashlib,itertools,json,sys,time
import portfolio as audit
import numpy as np
from threadpoolctl import threadpool_limits,threadpool_info
from pdescale.counterfactual import matched_motif,embed_motif,assemble_field_operator
from pilot import rhs_vector
HERE=audit.HERE

def main():
    dest=HERE/'portfolio_confirmation.csv'
    if dest.exists():raise FileExistsError(dest)
    anchor=np.zeros((3,6),bool);anchor[:,:2]=True;anchor[:,4:]=True
    motifs={'two_by_eight':matched_motif('disconnected'),'three_by_six':anchor}
    config=dict(n=[128,160,192],contrast=1000.,motifs={name:a.astype(int).tolist() for name,a in motifs.items()},
                shifts=[0,1],rhs=['odd_x','random'],methods=['jacobi','amg0','rs025'],repeats=7,
                order_seed=135171,setup_seed=13401,source_seed=991,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                solver_script_sha256=hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),
                protocol_sha256='47eabb5d43ac62e602e2c36564a6716f7e85ce81d22d629cf965760e71f5fdf3')
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (HERE/'portfolio_confirmation_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
        warm=assemble_field_operator(np.ones((16,16)))
        for method in config['methods']:audit.solve(warm,rhs_vector(16,'ones'),method,1)
        ns=config['n'].copy();rng.shuffle(ns)
        with dest.open('w',newline='',encoding='utf-8') as f:
            writer=None
            for n in ns:
                matrices={(name,shift):assemble_field_operator(embed_motif(a,n,1000.,shift=(shift,0)))
                          for name,a in motifs.items() for shift in config['shifts']}
                rhss={'odd_x':rhs_vector(n,'dipole'),'random':rhs_vector(n,'random',991)}
                for repeat in range(config['repeats']):
                    tasks=list(itertools.product(motifs,config['shifts'],config['rhs'],config['methods']));rng.shuffle(tasks)
                    for order,(motif,shift,rhs,method) in enumerate(tasks):
                        row=dict(n=n,contrast=1000.,motif=motif,shift=shift,rhs=rhs,method=method,
                                 repeat=repeat,order=order,seed=config['setup_seed']+repeat)
                        row.update(audit.solve(matrices[motif,shift],rhss[rhs],method,row['seed']))
                        if writer is None:writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                        writer.writerow(row);f.flush()
                    print(n,'repeat',repeat,'done',flush=True)
    print('interleaved confirmation complete',flush=True)

if __name__=='__main__':main()
