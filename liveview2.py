
import executing
import asttokens
import reprlib
import inspect
import ast
from pprint import pprint
import typing as t
import sys

print(__file__)

def test(i: int):
    xs = list(range(i))
    ys = [
        i + j
        for i in xs
        for j in xs
    ]
    k = 0
    t = sum(ys)
    if t > 1:
        return 1
    else:
        return 2
    # reprlib.aRepr.repr(ys)
    # reprlib.aRepr.repr(repr(ys))
    for x in xs:
        k += x
    # for j in range(i):
    #     k += 1 + k * test(i - 1)
    return k
    # j = i + 1
    # i + j
    # j += 1
    # k: int = j + i

    # if i > 0:
    #     test(i - 3)
    #     test(i - 1) + test(i - 2)
    #     return test(i - 1) + j

    # for j in range(i):
    #     k += 1
    # return i + j

from types import FrameType
import executing

def f(frame: FrameType, what: str, arg: t.Any):
    try:
        if frame.f_code.co_filename != __file__:
            return None
    except:
        return None
    # frame.f_trace_opcodes = True
    if arg:
        print(executing.Source.executing(frame.f_back).text(), end=' ')
        print(frame.f_lasti, frame.f_lineno, what, arg)
    return f

sys.settrace(f)

test(1)
test(2)
test(3)

def ignore():
    from libpykak import q, KakConnection
    k = KakConnection.init('fiddle')
    client, *_ = k.val.client_list
    k.eval('''
        try %(
            decl line-specs livelines
        )
        try %(
            decl range-specs livevals
        )
        addhl -override buffer/ replace-ranges livevals
        addhl -override buffer/ flag-lines Default livelines
    ''', client=client)

    st: dict[int, str] = {}

    def pr(value: t.Any, txt: str, filename: str, lineno: int):
        st[lineno] = value
        data = [q(f'{lineno}|{str(value).replace("|", "||")}') for lineno, value in st.items()]
        k.eval(h := f'set buffer=liveview.py livelines %val[timestamp] {" ".join(data)}', client=client)
        print(h)
        # print(filename, lineno, value, txt, sep='\t')
        # k.eval(q('echo', (filename, lineno, value, txt)
        return value

    test(4)
