
import executing
import asttokens
import reprlib
import inspect
import ast
from pprint import pprint
import typing as t
from pathlib import Path
import time

def test(i: int):
    # xs = list(range(i))
    # ys = [
    #     i + j
    #     for i in xs
    #     for j in xs
    # ]
    # k = 0
    # reprlib.aRepr.repr(ys)
    # reprlib.aRepr.repr(repr(ys))
    k = 0
    for x in range(i):
        time.sleep(0.1)
        k += x
        k
    # for j in range(i):
    #     k += 1 + k * test(i - 1)
    'zzz'
    time.sleep(0.5)
    'done'
    return k
    # if i > 0:
    #     test(i - 3)
    #     test(i - 1) + test(i - 2)
    #     return test(i - 1) + j

    # for j in range(i):
    #     k += 1
    # return i + j

# test(1)
# test(2)
# test(3)

def relative_to_cwd(p: str | Path):
    p = Path(p)
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p.absolute())

def rewrite(fn: t.Callable[..., t.Any]):
    filename = relative_to_cwd(inspect.getsourcefile(fn) or '?')
    _, start_line = inspect.findsource(fn)
    toks = asttokens.ASTTokens(inspect.getsource(fn), parse=True)
    # print(ast.dump(toks.tree, indent=2))
    line_lens: dict[int, int] = {}
    text: str = toks.get_text(toks.tree)
    assert isinstance(text, str)
    for i, s in enumerate(text.splitlines(), start=1):
        line_lens[i + start_line] = len(s)

    todo: list[tuple[int, int, int]] = []

    for n in ast.walk(toks.tree):
        if isinstance(n, (ast.Expr, ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Return)):
            start = n.value.first_token.startpos
            end = n.value.last_token.endpos
            print(
                n.lineno,
                n.end_lineno,
                n.__class__.__name__,
                toks.get_text(n).splitlines(),
                toks.get_text(n.value).splitlines(),
                # ast.dump(n, indent=None),
                sep='\t'
            )
            todo.append((start, end, n.end_lineno))
            # start, end = attr_node.last_token.startpos, attr_node.last_token.endpos
            # todo.append((start, end))

    todo = sorted(todo, key=lambda xs: -xs[0])
    for start, end, end_lineno in todo:
        lineno = start_line + end_lineno
        text = text[:start] + f'pr({filename!r},{lineno},{line_lens[lineno]},' + text[start:end] + ')' + text[end:]

    print(text)

    # rewrites in parents globals, could use decorator instead (?)
    exec(text, fn.__globals__, )
    import functools
    functools.update_wrapper(fn.__globals__[fn.__name__], fn)
    return fn.__globals__[fn.__name__]

rewrite(test)

import os

def underscore_encode(s: str) -> str:
    return s.replace('_', '__').replace('/', '_')

fp = open('/tmp/' + underscore_encode(os.getcwd()), 'w', buffering=1)

def pr(filename: str, line_no: int, line_len: int, value: t.Any):
    fp.write('\t'.join((
        filename,
        str(line_no),
        str(line_len),
        repr(value),
    )) + '\n')
    fp.flush()
    return value

test(40)
