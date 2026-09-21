"""Regenerate the paired callback calibration and complete face-sensitivity tables."""
from pathlib import Path
import csv, json, itertools
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/analysis/protocol_sensitivity'
CASES=['constant','inclusion_c100','checkerboard_c100']
METHODS=['cg','jacobi-pcg','amg-pcg']
LABEL={'cg':'CG','jacobi-pcg':'J','amg-pcg':'SA'}

def read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def write(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def table(name,caption,label,headers,rows):
    text='\\begin{table}[htbp]\n\\centering\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\small\n\\begin{tabular}{'+'l'*len(headers)+'}\n\\toprule\n'
    text+=' & '.join(headers)+' \\\\\n\\midrule\n'
    text+=''.join(' & '.join(map(str,row))+' \\\\\n' for row in rows)
    text+='\\bottomrule\n\\end{tabular}\n\\end{table}\n'
    (ROOT/'paper/tables'/name).write_text(text,encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=read(ROOT/'results/raw/protocol_sensitivity/timings.csv')
    expected=set(itertools.product(CASES,[64,128,256],METHODS,['monitored','count-only'],range(7)))
    indexed={(r['coefficient_case'],int(r['n']),r['method'],r['mode'],int(r['repeat'])):r for r in rows}
    assert len(rows)==len(indexed)==378 and set(indexed)==expected
    assert all(r['accepted']=='True' and int(r['info'])==0 and float(r['residual_norm'])<=1e-8 for r in rows)
    pairs=[];summaries=[];decisions=[]
    for case,n,method in itertools.product(CASES,[64,128,256],METHODS):
        for rep in range(7):
            a=indexed[case,n,method,'monitored',rep];b=indexed[case,n,method,'count-only',rep]
            assert a['iterations']==b['iterations'] and a['solution_sha256']==b['solution_sha256']
            pairs.append(dict(coefficient_case=case,n=n,method=method,repeat=rep,
                solve_ratio=float(a['solve_seconds'])/float(b['solve_seconds']),
                total_ratio=float(a['total_seconds'])/float(b['total_seconds'])))
        for mode in ['monitored','count-only']:
            group=[indexed[case,n,method,mode,rep] for rep in range(7)]
            s=dict(coefficient_case=case,n=n,method=method,mode=mode)
            for field in ['setup_seconds','solve_seconds','total_seconds','iterations']:
                vals=[float(r[field]) for r in group]
                for suffix,q in [('q25',.25),('median',.5),('q75',.75)]:s[field+'_'+suffix]=float(np.quantile(vals,q))
            summaries.append(s)
    for case,n in itertools.product(CASES,[64,128,256]):
        d=dict(coefficient_case=case,n=n)
        for mode in ['monitored','count-only']:
            group=[s for s in summaries if s['coefficient_case']==case and s['n']==n and s['mode']==mode]
            win=min(group,key=lambda s:s['total_seconds_median'])
            votes=sum(min(METHODS,key=lambda m:float(indexed[case,n,m,mode,rep]['total_seconds']))==win['method'] for rep in range(7))
            d[mode+'_winner']=win['method'];d[mode+'_votes']=votes
            d[mode+'_median_ms']=1000*win['total_seconds_median']
        decisions.append(d)
    write('pairs.csv',pairs);write('method_summary.csv',summaries);write('decisions.csv',decisions)
    ranges={m:[float(min(np.median([p['solve_ratio'] for p in pairs if p['coefficient_case']==c and p['n']==n and p['method']==m]) for c,n in itertools.product(CASES,[64,128,256]))),float(max(np.median([p['solve_ratio'] for p in pairs if p['coefficient_case']==c and p['n']==n and p['method']==m]) for c,n in itertools.product(CASES,[64,128,256])))] for m in METHODS}
    audit=dict(solves=len(rows),identical_solution_pairs=len(pairs),max_residual=max(float(r['residual_norm']) for r in rows),median_solve_ratio_ranges=ranges,changed_median_winners=sum(d['monitored_winner']!=d['count-only_winner'] for d in decisions))
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    view=[]
    for d in decisions:
        c=d['coefficient_case'];n=d['n'];v=[c.split('_')[0].capitalize(),n]
        for mode in ['monitored','count-only']:v.append(f"{LABEL[d[mode+'_winner']]} {d[mode+'_median_ms']:.2f} ({d[mode+'_votes']}/7)")
        for m in METHODS:v.append(f"{np.median([p['solve_ratio'] for p in pairs if p['coefficient_case']==c and p['n']==n and p['method']==m]):.2f}")
        view.append(v)
    write('table_rows.csv',[dict(zip(['Case','N','Monitored','Count-only','CG','J','SA'],v)) for v in view])
    table('protocol_sensitivity.tex','Paired callback calibration. Winner entries give method, median total milliseconds and votes out of seven. Last columns give median paired monitored/count-only solve-time ratios. J = Jacobi-PCG; SA = AMG-PCG.','tab:protocol',['Case','$N$','Monitored','Count-only','CG','J','SA'],view)
    a=read(ROOT/'results/raw/averaging_sensitivity.csv');face=[]
    for c,n in itertools.product(['inclusion_c100','layered_c100','checkerboard_c100'],[64,128,256]):
        v=[c.split('_')[0].capitalize(),n]
        for m in METHODS:
            v.append('/'.join(next(r['iterations'] for r in a if r['coefficient_case']==c and int(r['n'])==n and r['method']==m and r['face_average']==f) for f in ['arithmetic','harmonic']))
        v.append('/'.join(LABEL[next(r['method'] for r in a if r['coefficient_case']==c and int(r['n'])==n and r['is_best']=='True' and r['face_average']==f)] for f in ['arithmetic','harmonic']))
        face.append(v)
    write('face_table_rows.csv',[dict(zip(['Case','N','CG','J','SA','Winner'],v)) for v in face])
    table('face_sensitivity_main.tex','Complete contrast-100 face-averaging check under the historical monitored protocol. Entries are arithmetic/harmonic iteration counts and setup-inclusive winners (J = Jacobi-PCG, SA = AMG-PCG). These are single timing passes, not uncertainty estimates.','tab:face-main',['Case','$N$','CG','J','SA','Winner'],face)
    print(json.dumps(audit,indent=2));print(json.dumps(decisions,indent=2))

if __name__=='__main__':main()
