
import pickle
import marshal
from types import FunctionType, CellType
from typing import Any
import builtins

def lamdumps(f: FunctionType):
    co = f.__code__
    buns = set(dir(builtins))
    g = {
        n: f.__globals__[n]
        for n in co.co_names
        if n not in buns
    }
    return pickle.dumps((
        marshal.dumps(f.__code__),
        g,
        f.__name__,
        f.__defaults__,
        tuple(
            c.cell_contents
            for c in f.__closure__ or ()
        ),
        f.__kwdefaults__,
        f.__qualname__,
    ))

def cell(co: Any) -> CellType:
    c = CellType()
    c.cell_contents = co
    return c

def lamloads(b: bytes):
    mco, g, n, d, clo, k, qn = pickle.loads(b)
    co = marshal.loads(mco)
    f = FunctionType(co, g, n, d, tuple(map(cell, clo)))
    f.__kwdefaults__ = k
    f.__qualname__ = qn
    return f

if 0:
    co = f.__code__
    for k in dir(co):
        if k.startswith('co_'):
            print(k, getattr(co, k))
    print(*co.co_lines())

x = 1
def h(us: tuple[int, int], z: int):
    return lambda a, b=4, *, c=9: 1 + x + us[0] + z

def f1(i: int):
    print(i+1)
    return i+2
f2 = h((4, 3), 5)
f3 = lambda y: x + y

for f in [f1, f2, f3]:
    b = lamdumps(f)
    F = lamloads(b)
    # x += 1
    print(F.__name__, f.__name__)
    print(F.__qualname__, f.__qualname__)
    print(F.__annotations__, f.__annotations__)
    print(F(1), f(1))
    print('---')

