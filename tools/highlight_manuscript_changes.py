"""Highlight inserted/replaced text against a previous DOCX without changing content."""
from pathlib import Path
from copy import deepcopy
from difflib import SequenceMatcher
import argparse,json,re,zipfile
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W,'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def tag(s):return '{'+W+'}'+s
def text(el):return ''.join(el.xpath('.//w:t/text() | .//m:t/text()',namespaces=NS))
def yellow(run):
    pr=run.find(tag('rPr'))
    if pr is None:pr=E.Element(tag('rPr'));run.insert(0,pr)
    h=pr.find(tag('highlight'))
    if h is None:h=E.SubElement(pr,tag('highlight'))
    h.set(tag('val'),'yellow')
def mark(paragraph,old=None):
    current=''.join(paragraph.xpath('.//w:t/text()',namespaces=NS))
    if not current:return 0
    if old is None:spans=[(0,len(current))]
    else:
        pattern=r'\w+|\s+|[^\w\s]'
        a=re.findall(pattern,old);b=re.findall(pattern,current)
        offsets=[0]
        for token in b:offsets.append(offsets[-1]+len(token))
        spans=[(offsets[j],offsets[k]) for op,i,h,j,k in SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if op in {'insert','replace'} and current[offsets[j]:offsets[k]].strip()]
    position=0
    for run in list(paragraph.iter(tag('r'))):
        nodes=run.findall(tag('t'));s=''.join(n.text or '' for n in nodes)
        if not s:continue
        begin=position;position+=len(s)
        cuts={0,len(s)}
        for lo,hi in spans:
            if lo<position and hi>begin:cuts.update([max(0,lo-begin),min(len(s),hi-begin)])
        cuts=sorted(cuts)
        if not any(lo<position and hi>begin for lo,hi in spans):continue
        # Text-only runs can be split while retaining font, superscript and other properties.
        assert all(child.tag in {tag('rPr'),tag('t')} for child in run), 'Unsupported mixed-content changed run'
        parent=run.getparent();idx=parent.index(run)
        for left,right in zip(cuts,cuts[1:]):
            new=deepcopy(run)
            for node in list(new):
                if node.tag==tag('t'):new.remove(node)
            node=E.SubElement(new,tag('t'));node.set('{http://www.w3.org/XML/1998/namespace}space','preserve');node.text=s[left:right]
            if any(lo<begin+right and hi>begin+left for lo,hi in spans):yellow(new)
            parent.insert(idx,new);idx+=1
        parent.remove(run)
    return len(spans)

def highlight(baseline,current,output,report):
    with zipfile.ZipFile(baseline) as z:old=E.fromstring(z.read('word/document.xml'))
    with zipfile.ZipFile(current) as z:entries={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(entries['word/document.xml']);original_text=text(root)
    math_before=[E.tostring(x) for x in root.xpath('//m:oMath',namespaces=NS)]
    a=list(old.find(tag('body')));b=list(root.find(tag('body')))
    aa=[text(x) for x in a];bb=[text(x) for x in b];changes=[]
    for op,i,h,j,k in SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes():
        if op=='equal':continue
        available=set(range(i,h))
        for n in range(j,k):
            block=b[n]
            if not bb[n].strip():continue
            candidates=[(SequenceMatcher(None,aa[q],bb[n],autojunk=False).ratio(),q) for q in available if a[q].tag==block.tag and block.tag==tag('p')]
            best=max(candidates,default=(0,None))
            previous=None
            if best[0]>=.45:
                q=best[1];available.remove(q);previous=''.join(a[q].xpath('.//w:t/text()',namespaces=NS))
            paragraphs=[block] if block.tag==tag('p') else block.findall('.//'+tag('p'))
            spans=sum(mark(p,previous if len(paragraphs)==1 else None) for p in paragraphs)
            changes.append(dict(block=n,type='paragraph' if block.tag==tag('p') else 'table',spans=spans,text=bb[n][:180]))
    assert text(root)==original_text
    assert math_before==[E.tostring(x) for x in root.xpath('//m:oMath',namespaces=NS)]
    entries['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in entries.items():z.writestr(n,data)
    stats=dict(baseline=str(baseline),changed_blocks=len(changes),highlighted_runs=len(root.xpath('//w:highlight[@w:val="yellow"]',namespaces=NS)),text_unchanged=True,math_unchanged=True,changes=changes)
    report.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in stats.items() if k!='changes'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--current',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();highlight(args.baseline,args.current,args.output,args.report)
