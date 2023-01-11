
from pathlib import Path
from typing import *
import re

from pbutils import p
A = TypeVar('A')
B = TypeVar('B')

finger = {
    f: i
    for i, fs in enumerate('a oq ejpukyix fdbghmctw rnv ls'.split())
    for f in fs
}

roll = {
    f: i
    for i, fs in enumerate('als oqrnv ejctw uhpgkmyfidxb'.split())
    for f in fs
}


hand = {
    f: i
    for i, fs in enumerate('aoeuipyqjkx fgcrldhtnsbwmvz'.split())
    for f in fs
}

def group_by(xs: Iterable[A], key: Callable[[A], B]) -> dict[B, list[A]]:
    d: dict[B, list[A]] = DefaultDict(list)
    for x in xs:
        d[key(x)] += [x]
    return dict(d)

def main():
    words = Path('./english-words/words_alpha.txt').read_text().splitlines()
    c = DefaultDict[str, list[str]](list)
    for w in words:
        for i, _ in enumerate(w):
            t = w[i:][:3]
            if len(t) < 3:
                continue
            ok = re.match('[oeukphtncrg]{3}', t)
            for u in range(3):
                for v in range(3):
                    if u >= v:
                        continue
                    ok = ok and finger[t[u]] != finger[t[v]]
                    if hand[t[u]] == hand[t[v]]:
                        ok = ok and roll[t[u]] < roll[t[v]]
            if ok and len(t) == 3:
                c[t.upper()] += [w]
    short = sorted([
        k
        for k, v in c.items()
        if len(v) < 15
    ])
    for i in range(3):
        for k, vs in group_by(short, lambda s: s[i]).items():
            print(k, *vs)
        print()

if __name__ == '__main__':
    main()
