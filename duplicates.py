
from pathlib import Path
import re
import textwrap
from pbutils import p
from typing import *

def paragraphs(s: str):
    out: list[str] = []
    for par in re.split('\n{2,}', s):
        out += re.split(r'\n+(?=\S)', par)
    out = [x.strip() for x in out]
    out = [x for x in out if x]
    out = [x for x in out if '\n' in x]
    return out


def test():
    example = '''
    import bla
    import bli

    def bi bo():
        ba ba ba
    '''

    print(paragraphs(example))

def dups_from(root: Path):
    c = DefaultDict[str, list[str]](list)

    pys = root.rglob('**/*.py')

    for py in pys:
        txt = py.read_text()
        for p in set(paragraphs(txt)):
            c[p] += [str(py.relative_to(root))]

    for p, pys in c.items():
        if len(pys) > 1:
            print(''*80, *pys, *p.splitlines()[:3], sep='\n')

def example():
    root = Path('/home/dan/code/monorepo/cellpainter')
    dups_from(root)

example()
