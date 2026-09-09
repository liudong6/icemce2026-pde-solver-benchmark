"""Rebuild summaries and a mechanism figure from the controlled experiment CSVs."""
from pathlib import Path
import csv,json,statistics,sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pdescale.counterfactual import matched_motif
RAW=ROOT/'results/raw/counterfactual'
OUT=ROOT/'results/analysis/counterfactual'

def read(name):
    with (RAW/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def write(rows,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def summarise(filename,keys,repeats):
    groups=defaultdict(list)
    raw=read(filename)
    for r in raw:groups[tuple(r[k] for k in keys)].append(r)
    result=[]
    for key,rr in sorted(groups.items()):
        out=dict(zip(keys,key))
        assert len(rr)==2*repeats
        ratios=[]
        for rep in range(repeats):
            block={r['method']:r for r in rr if int(r['repeat'])==rep}
            assert set(block)=={'jacobi','amg0'}
            ratios.append(float(block['jacobi']['total'])/float(block['amg0']['total']))
        for method in ['jacobi','amg0']:
            subset=[r for r in rr if r['method']==method]
            for field in ['setup','solve','total','iterations']:
                out[method+'_'+field]=statistics.median(float(r[field]) for r in subset)
        out.update(accepted=all(r['accepted']=='True' for r in rr),
            max_residual=max(float(r['residual']) for r in rr),
            winner='jacobi' if out['jacobi_total']<out['amg0_total'] else 'amg0',
            jacobi_wins=sum(r<1 for r in ratios),repeats=repeats,
            min_paired_ratio=min(ratios),max_paired_ratio=max(ratios),
            stable=all(r<1 for r in ratios) or all(r>1 for r in ratios))
        result.append(out)
    return result

def translation_floors(summary):
    lookup={tuple(r[k] for k in ['n','geometry','average','rhs','variant']):r for r in summary}
    result=[]
    for r in summary:
        if r['variant']!='centered':continue
        other=lookup[(r['n'],r['geometry'],r['average'],r['rhs'],'shift_x')]
        # These two instances have identical RHS and coefficient invariants,
        # including connectivity and component sizes. Average gives each 1/2 weight.
        costs={m:statistics.mean(x[m+'_total']/min(x['jacobi_total'],x['amg0_total'])
            for x in [r,other]) for m in ['jacobi','amg0']}
        result.append(dict(n=r['n'],geometry=r['geometry'],average=r['average'],rhs=r['rhs'],
            centered_winner=r['winner'],shifted_winner=other['winner'],
            both_stable=r['stable'] and other['stable'],
            empirical_minimum_mean_excess=min(costs.values())-1,
            best_invariant_only_method=min(costs,key=costs.get)))
    return result

def figure(summary):
    lookup={tuple(r[k] for k in ['n','geometry','average','rhs','variant']):r for r in summary}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig=plt.figure(figsize=(7.2,5.5),layout='constrained')
    gs=fig.add_gridspec(2,2,height_ratios=[1,2])
    for j,geometry in enumerate(['connected','disconnected']):
        ax=fig.add_subplot(gs[0,j]);a=matched_motif(geometry)
        ax.imshow(a,cmap='Greys',vmin=0,vmax=1,interpolation='nearest')
        ax.set_title(('(a) Connected' if j==0 else '(b) Disconnected')+' motif')
        ax.set_xticks([]);ax.set_yticks([])
        ax.set_xlabel('12 high cells; 20 interface edges')
    ax=fig.add_subplot(gs[1,:])
    cases=[('connected','centered','dipole_x','Connected\nodd-x source'),
           ('disconnected','centered','dipole_x','Disconnected\nodd-x source'),
           ('disconnected','shift_x','dipole_x','Same shape, shifted by h\nodd-x source'),
           ('disconnected','centered','random','Disconnected\nrandom source')]
    raw=read('confirmation.csv')
    x=np.arange(len(cases));height=.34
    for offset,method,color,name in [(-height/2,'jacobi','#2274A5','Jacobi-PCG'),(height/2,'amg0','#D46A35','AMG-PCG')]:
        data=[lookup[('192',g,'harmonic',rhs,v)] for g,v,rhs,_ in cases]
        times=[[float(r['total'])*1000 for r in raw if r['n']=='192' and r['geometry']==g
                and r['average']=='harmonic' and r['rhs']==rhs and r['variant']==v and r['method']==method]
               for g,v,rhs,_ in cases]
        medians=[r[method+'_total']*1000 for r in data]
        errors=np.array([[m-min(t),max(t)-m] for m,t in zip(medians,times)]).T
        bars=ax.barh(x+offset,medians,height=height,color=color,label=name,xerr=errors,
            error_kw={'elinewidth':.7,'capsize':2,'capthick':.7})
        for bar,r,times_case in zip(bars,data,times):
            ax.text(max(times_case)+1,bar.get_y()+height/2,f"{int(r[method+'_iterations'])} it.",va='center',fontsize=8)
    ax.set_yticks(x,[c[3] for c in cases]);ax.invert_yaxis()
    ax.set_xlabel('Setup + solve time (ms); median and range of five runs')
    ax.set_title('(c) N = 192, contrast = 1000, harmonic faces')
    ax.set_xlim(0,230);ax.legend(loc='lower right',frameon=False)
    for parent in [ROOT/'results/figures',ROOT/'paper/figures']:
        parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(parent/'counterfactual_audit.png',dpi=240)
    plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    confirmation=summarise('confirmation.csv',['n','contrast','geometry','variant','average','rhs'],5)
    heldout=summarise('heldout.csv',['n','contrast','geometry','average','rhs'],5)
    perturbation=summarise('perturbation.csv',['n','contrast','shift_x','shift_y','alpha'],3)
    floors=translation_floors(confirmation)
    for name,rows in [('confirmation',confirmation),('heldout',heldout),('perturbation',perturbation),('translation_floors',floors)]:
        write(rows,OUT/(name+'_summary.csv'))
    figure(confirmation)
    report=dict(confirmation_cells=len(confirmation),heldout_cells=len(heldout),perturbation_cells=len(perturbation),
        all_followup_accepted=all(r['accepted'] for r in confirmation+heldout+perturbation),
        stable_confirmation_cells=sum(r['stable'] for r in confirmation),
        stable_heldout_cells=sum(r['stable'] for r in heldout),
        translation_pairs=len(floors),stable_translation_reversals=sum(r['both_stable'] and r['centered_winner']!=r['shifted_winner'] for r in floors),
        interpretation='Descriptive finite-case audit; empirical regret floors use equal weights and measured medians, not population confidence bounds or an online policy.')
    (OUT/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
