from pathlib import Path
import csv,json,statistics
from collections import defaultdict,Counter
from pilot import OUT
rows=list(csv.DictReader((OUT/'confirmation.csv').open()))
groups=defaultdict(list)
keys=['n','contrast','geometry','variant','average','rhs']
for r in rows:groups[tuple(r[k] for k in keys)].append(r)
summary=[]
for key,rr in groups.items():
    out=dict(zip(keys,key))
    timing={m:statistics.median(float(r['total']) for r in rr if r['method']==m) for m in ['jacobi','amg0']}
    wins=Counter()
    ratios=[]
    for rep in range(5):
        block={r['method']:r for r in rr if int(r['repeat'])==rep}
        assert set(block)=={'jacobi','amg0'}
        wins[min(block,key=lambda m:float(block[m]['total']))]+=1
        ratios.append(float(block['jacobi']['total'])/float(block['amg0']['total']))
    for m in ['jacobi','amg0']:
        out[m+'_seconds']=timing[m]
        out[m+'_iterations']=statistics.median(int(r['iterations']) for r in rr if r['method']==m)
    out.update(winner=min(timing,key=timing.get),jacobi_to_amg=timing['jacobi']/timing['amg0'],
        all_accepted=all(r['accepted']=='True' for r in rr),stable=len(wins)==1,
        jacobi_wins=wins['jacobi'],min_paired_ratio=min(ratios),max_paired_ratio=max(ratios),
        max_residual=max(float(r['residual']) for r in rr))
    summary.append(out)
with (OUT/'confirmation_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
report=dict(rows=len(rows),expected=1440,groups=len(groups),all_accepted=all(r['accepted']=='True' for r in rows),
    max_residual=max(float(r['residual']) for r in rows),
    stable_cells=sum(r['stable'] for r in summary),winners=Counter(r['winner'] for r in summary))
print(json.dumps(report,indent=2))
print('CENTERED HARMONIC')
for r in sorted(summary,key=lambda x:(int(x['n']),x['rhs'],x['geometry'])):
    if r['variant']=='centered' and r['average']=='harmonic':print(r)
(OUT/'confirmation_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
