from pathlib import Path
import csv, json, statistics
from collections import defaultdict, Counter
from pilot import OUT
rows = list(csv.DictReader((OUT/'pilot.csv').open()))
groups = defaultdict(list)
for r in rows:
    groups[tuple(r[k] for k in ['n','contrast','geometry','average','rhs','method'])].append(r)
summary=[]
for key, rr in groups.items():
    summary.append(dict(zip(['n','contrast','geometry','average','rhs','method'],key),
        count=len(rr), iterations=statistics.median(float(r['iterations']) for r in rr),
        median_total=statistics.median(float(r['total']) for r in rr),
        all_accepted=all(r['accepted']=='True' for r in rr),
        max_residual=max(float(r['residual']) for r in rr)))
with (OUT/'pilot_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
lookup = {tuple(r[k] for k in ['n','contrast','geometry','average','rhs','method']):r for r in summary}
pairs=[]
for r in summary:
    if r['geometry']!='connected' or r['method']!='jacobi':continue
    d=lookup[(r['n'],r['contrast'],'disconnected',r['average'],r['rhs'],'jacobi')]
    wins={}
    for g in ['connected','disconnected']:
        candidates=[s for s in summary if all(s[k]==r[k] for k in ['n','contrast','average','rhs']) and s['geometry']==g and s['all_accepted']]
        wins[g]=min(candidates,key=lambda s:s['median_total'])['method'] if candidates else 'none'
    pairs.append(dict(n=r['n'],contrast=r['contrast'],average=r['average'],rhs=r['rhs'],
        connected_iterations=r['iterations'],disconnected_iterations=d['iterations'],
        both_jacobi_accepted=r['all_accepted'] and d['all_accepted'],winners=wins))
report=dict(rows=len(rows),expected=576,groups=len(groups),
    failures=Counter(r['method'] for r in rows if r['accepted']!='True'),
    matched_pairs=pairs, note='Exploratory medians of two runs; not confirmation or final selection policy.')
(OUT/'pilot_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
