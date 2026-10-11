"""Check the latest review's reference ratios from the cited BibTeX entries."""
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
tex=(ROOT/'paper/main.tex').read_text(encoding='utf-8')
bib=(ROOT/'paper/references.bib').read_text(encoding='utf-8')
entries={}
for block in re.split(r'(?=@\w+\s*\{)',bib):
 if not block.strip():continue
 entry=re.match(r'@(\w+)\s*\{([^,]+),',block);assert entry,block[:80]
 year=re.search(r'\byear\s*=\s*\{([^}]+)\}',block)[1]
 entries[entry[2]]={'year':year,'type':entry[1].lower(),'preprint':'preprint' in block.lower()}
order=list(dict.fromkeys(k.strip() for m in re.finditer(r'\\cite\{([^}]+)\}',tex) for k in m[1].split(',')))
assert set(order)==set(entries),'Uncited or missing bibliography entries'
recent=[k for k in order if entries[k]['year'].isdigit() and 2022<=int(entries[k]['year'])<=2026]
formal=[k for k in recent if entries[k]['type'] in {'article','inproceedings'} and not entries[k]['preprint']]
preprints=[k for k in order if entries[k]['preprint']]
total=len(order)
assert 2*len(recent)>total,'Recent references must exceed half of all cited entries'
assert 2*len(formal)>total,'Conservative check: recent formal papers must also exceed half'
assert 5*len(preprints)<=total,'Preprint share exceeds 20%'
print(json.dumps({'total':total,'recent_2022_2026':len(recent),'recent_percent':round(100*len(recent)/total,2),'recent_formal_papers':len(formal),'recent_formal_percent':round(100*len(formal)/total,2),'preprints':len(preprints),'preprint_percent':round(100*len(preprints)/total,2),'recent_reference_numbers':[order.index(k)+1 for k in recent],'preprint_reference_numbers':[order.index(k)+1 for k in preprints],'requirements_met':True},indent=2))
