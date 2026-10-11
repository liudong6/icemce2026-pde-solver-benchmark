"""Extract the complete pre-compression methods/results while preserving all XML evidence."""
from pathlib import Path
import re
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt
import build_iop_docx as h
ROOT=h.ROOT

def build():
    doc=Document(ROOT/'tools/supplementary_source.docx')
    body=doc._element.body
    active=False
    for node in list(body):
        text=''.join(node.itertext()) if False else ''.join(node.xpath('.//w:t/text()'))
        if text.startswith('3. Mathematical Model and Discretisation'):active=True
        if text.startswith('8. Conclusion'):active=False
        if text=='References':active=True
        if not active and node.tag!=qn('w:sectPr'):body.remove(node)
    for node in body.xpath('.//w:highlight'):
        node.getparent().remove(node)
    for node in body.xpath('.//w:t'):
        text=node.text or ''
        text=re.sub(r'\b(Table|Figure) (\d+)',r'\1 S\2',text)
        text=re.sub(r'\bEq\. \((\d+)\)',r'Eq. (S\1)',text)
        text=re.sub(r'\bEquation \((\d+)\)',r'Equation (S\1)',text)
        if re.fullmatch(r'\(\d+\)',text):text=text.replace('(','(S')
        for old,new in [('3. Mathematical','S1. Mathematical'),('4. Solver','S2. Solver'),('5. Experiments','S3. Experiments'),('6. Discussion','S4. Discussion'),('7. Reproducibility','S5. Reproducibility')]:
            if text.startswith(old):text=text.replace(old,new,1)
        text=re.sub(r'^5\.(\d+)\.',r'S3.\1.',text)
        node.text=text
    first=body[0]
    p=doc.add_paragraph('Supplementary methods and complete results','IOP-CS-Title')
    first.addprevious(p._p)
    p=doc.add_paragraph('A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation','IOP-CS-BodyNoIndent')
    first.addprevious(p._p)
    p=doc.add_paragraph('This companion retains the full experimental account underlying the compressed main paper: all nine result tables, six original figures, detailed protocols, failures and limitations. S-prefixed table, figure and equation numbers refer to this document. Experimental data and claims are unchanged; the main paper uses a smaller selection of displays. Full reference titles and identifiers are retained below.','IOP-CS-BodyNoIndent')
    p.paragraph_format.space_after=Pt(10);first.addprevious(p._p)
    doc.core_properties.title='Supplementary methods and complete results'
    target=ROOT/'paper/SUPPLEMENTARY_METHODS_AND_RESULTS.docx'
    doc.save(target);h.normalize_docx_revision(target);print(target)

if __name__=='__main__':build()
