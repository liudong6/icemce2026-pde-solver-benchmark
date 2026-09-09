"""Regenerate the portfolio sensitivity audit; never pool its timing stages."""
from pathlib import Path
from collections import defaultdict
import csv
import json
import statistics

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'results/raw/counterfactual'
OUT = ROOT / 'results/analysis/counterfactual'


def summarise_portfolio(rows, keys, methods, repeats):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    result = []
    for key, vals in sorted(groups.items()):
        out = dict(zip(keys, key))
        assert len(vals) == len(methods) * repeats
        assert len({(r['method'], int(r['repeat'])) for r in vals}) == len(vals)
        valid = all(r['accepted'] in (True, 'True') for r in vals)
        out['accepted'] = valid
        out['max_residual'] = max(float(r['residual']) for r in vals)
        winners = []
        for repeat in range(repeats):
            block = {r['method']: r for r in vals if int(r['repeat']) == repeat}
            assert set(block) == set(methods)
            winners.append(min(methods, key=lambda m: float(block[m]['total'])))
        for method in methods:
            subset = [r for r in vals if r['method'] == method]
            for field in ['setup', 'solve', 'total', 'iterations']:
                out[method + '_' + field] = statistics.median(float(r[field]) for r in subset)
        out['winner'] = min(methods, key=lambda m: out[m + '_total']) if valid else 'acceptance_failure'
        out['winner_repeats'] = sum(m == out['winner'] for m in winners) if valid else 0
        out['repeats'] = repeats
        out['stable'] = valid and len(set(winners)) == 1
        result.append(out)
    return result


def paired_floors(summary, methods):
    groups = defaultdict(dict)
    for row in summary:
        key = (row['n'], row['motif'], row['rhs'])
        shift = int(row['shift'])
        assert shift not in groups[key]
        groups[key][shift] = row
    result = []
    for (n, motif, rhs), pair in sorted(groups.items()):
        assert set(pair) == {0, 1}
        left, right = pair[0], pair[1]
        valid = left['accepted'] and right['accepted']
        ratios = {}
        if valid:
            ratios = {m: statistics.mean(row[m+'_total'] / min(row[x+'_total'] for x in methods)
                                         for row in (left, right)) for m in methods}
        result.append(dict(n=n, motif=motif, rhs=rhs, accepted=valid,
                           centered_winner=left['winner'], shifted_winner=right['winner'],
                           both_stable=left['stable'] and right['stable'],
                           stable_reversal=left['stable'] and right['stable'] and left['winner'] != right['winner'],
                           empirical_minimum_mean_excess=min(ratios.values())-1 if valid else None,
                           best_invariant_only_method=min(ratios, key=ratios.get) if valid else None))
    return result


def write_csv(rows, path):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_portfolio_table(pairs, path):
    """Expose every pair and its stability; do not select only reversals."""
    methods = {'jacobi': 'J', 'amg0': 'SA', 'rs025': 'RS'}
    caption = ('All 12 translated pairs in the interleaved confirmation. Winners use median total time: '
               'J = Jacobi-PCG, RS = classical AMG-PCG; SA was also a candidate. Stable means both positions '
               'retain their respective winner in all seven repeats. E(P) uses measured medians even for '
               'unstable pairs; it is not a confidence bound.')
    lines = [r'\begin{table}[t]', r'\centering', r'\caption{' + caption + '}',
             r'\label{tab:portfolio-audit}', r'\begin{tabular}{rlllllr}', r'\toprule',
             r'$N$ & Motif & Source & Centered & Shifted & Stable & $E(P)$ (\%) \\', r'\midrule']
    for r in pairs:
        assert r['accepted']
        cells = [r['n'], {'two_by_eight': '2x8', 'three_by_six': '3x6'}[r['motif']],
                 {'odd_x': 'Odd-x', 'random': 'Random'}[r['rhs']],
                 methods[r['centered_winner']], methods[r['shifted_winner']],
                 'Yes' if r['both_stable'] else 'No', f"{100*r['empirical_minimum_mean_excess']:.2f}"]
        lines.append(' & '.join(cells) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}', '']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, keys, methods, repeats, count in [
        ('portfolio', ['n','geometry','shift','rhs'], ['jacobi','amg0','amg025','rs025'], 5, 240),
        ('portfolio_confirmation', ['n','motif','shift','rhs'], ['jacobi','amg0','rs025'], 7, 504),
    ]:
        with (RAW/(name+'.csv')).open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == count
        for row in rows:
            assert abs(float(row['total'])-float(row['setup'])-float(row['solve'])) < 1e-12
            assert (row['accepted']=='True') == (int(row['info'])==0 and float(row['residual']) <= 1e-8)
        summary = summarise_portfolio(rows, keys, methods, repeats)
        write_csv(summary, OUT/(name+'_summary.csv'))
        report[name] = dict(solves=len(rows), failed_acceptance=sum(r['accepted']!='True' for r in rows),
                            cells=len(summary), stable_cells=sum(r['stable'] for r in summary),
                            max_residual=max(float(r['residual']) for r in rows))
        if name == 'portfolio_confirmation':
            pairs = paired_floors(summary, methods)
            write_csv(pairs, OUT/'portfolio_translation_floors.csv')
            write_portfolio_table(pairs, ROOT/'paper/tables/portfolio_summary.tex')
            report[name]['pairs'] = pairs
    (OUT/'portfolio_analysis.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
