"""Unseen 3x6 motif family; generation/selection never examines solver outcomes."""
from pathlib import Path
import csv,hashlib,itertools,json,time
import numpy as np
from scipy.ndimage import label
from threadpoolctl import threadpool_limits,threadpool_info
from pilot import matrix,descriptors,rhs_vector
from confirmation import checked_solve
from pilot import OUT

def motifs():
    bins={1:{},2:{}}
    for high in itertools.combinations(range(18),12):
        a=np.zeros(18,bool);a[list(high)]=1;a=a.reshape(3,6)
        perimeter=4*a.sum()-2*((a[:-1]&a[1:]).sum()+(a[:,:-1]&a[:,1:]).sum())
        count=label(a)[1]
        if perimeter!=20 or count not in bins:continue
        if not all([a[0].any(),a[-1].any(),a[:,0].any(),a[:,-1].any()]):continue
        canonical=min(tuple(x.astype(int).ravel()) for x in [a,a[::-1],a[:,::-1],a[::-1,::-1]])
        bins[count][canonical]=np.array(canonical,dtype=bool).reshape(3,6)
    rng=np.random.default_rng(173219)
    selected=[]
    # Anchor is specified geometrically: two separated 3x2 rectangles.
    anchor=np.zeros((3,6),bool);anchor[:,:2]=1;anchor[:,4:]=1
    selected.append(('islands_symmetric',anchor))
    for count,num in [(1,4),(2,3)]:
        candidates=[a for key,a in sorted(bins[count].items()) if not np.array_equal(a,anchor)]
        for j in rng.choice(len(candidates),num,replace=False):
            selected.append((f'components{count}_{j}',candidates[j]))
    return selected,{str(k):len(v) for k,v in bins.items()}

def embed(a,n,c):
    s=n//16
    block=np.repeat(np.repeat(a,s,0),s,1)
    x=n//2-block.shape[0]//2;y=n//2-block.shape[1]//2
    k=np.ones((n,n));k[x:x+block.shape[0],y:y+block.shape[1]]=np.where(block,c,1.)
    return k

def main():
    dest=OUT/'heldout.csv'
    if dest.exists():raise FileExistsError(dest)
    selected,counts=motifs()
    config=dict(family='3x6,12 occupied cells,20 interface edges',n=[128,192],contrast=1000.,
        average='harmonic',rhs=['ones','dipole_x','dipole_y','random'],repeats=5,
        methods=['jacobi','amg0'],setup_seed=2701,order_seed=914111,
        candidate_counts=counts,motifs={name:a.astype(int).tolist() for name,a in selected},
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        interpretation='Independent motif family after pilot/confirmation; conditional balanced sampling, not a natural population.')
    for n in config['n']:
        checks=[descriptors(embed(a,n,config['contrast'])) for _,a in selected]
        for key in ['high_nodes','mean','tv','grad']:
            assert np.allclose([d[key] for d in checks],checks[0][key],rtol=1e-14)
    rng=np.random.default_rng(config['order_seed'])
    with threadpool_limits(limits=1):
        config['threadpools']=threadpool_info()
        (OUT/'heldout_config.json').write_text(json.dumps(config,indent=2)+'\n')
        A=matrix(np.ones((16,16)),'harmonic')
        for method in config['methods']:checked_solve(A,rhs_vector(16,'ones'),method,731)
        jobs=list(itertools.product(config['n'],range(len(selected))));rng.shuffle(jobs)
        with dest.open('w',newline='') as f:
            writer=None
            for n,index in jobs:
                name,a=selected[index];k=embed(a,n,config['contrast']);A=matrix(k,'harmonic')
                bx=rhs_vector(n,'dipole').reshape(n-2,n-2)
                rhsmap=dict(ones=rhs_vector(n,'ones'),dipole_x=bx.ravel(),dipole_y=bx.T.ravel(),random=rhs_vector(n,'random',seed=18873))
                for repeat in range(config['repeats']):
                    tasks=list(itertools.product(config['rhs'],config['methods']));rng.shuffle(tasks)
                    for order,(rhs,method) in enumerate(tasks):
                        row=dict(n=n,contrast=config['contrast'],geometry=name,average='harmonic',rhs=rhs,
                            repeat=repeat,order=order,method=method,seed=config['setup_seed']+repeat,
                            reflection_x=bool(np.array_equal(k,k[::-1,:])),reflection_y=bool(np.array_equal(k,k[:,::-1])),
                            **descriptors(k))
                        row.update(checked_solve(A,rhsmap[rhs],method,row['seed']))
                        if writer is None:writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                        writer.writerow(row);f.flush()
                print(n,name,'done',flush=True)
    print('heldout complete',flush=True)

if __name__=='__main__':main()
