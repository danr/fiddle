
import pickle
import marshal
from types import FunctionType, CellType, MethodType
from typing import Any, Callable
import sys

def lamdumps(f: Callable[..., Any]):
    co = f.__code__
    return pickle.dumps((
        marshal.dumps(f.__code__),
        f.__module__,
        f.__name__,
        f.__defaults__,
        tuple(
            c.cell_contents
            for c in f.__closure__ or ()
        ),
        f.__kwdefaults__,
        f.__qualname__,
        (hasattr(f, '__self__'), getattr(f, '__self__', None)),
    ))

def cell(co: Any) -> CellType:
    c = CellType()
    c.cell_contents = co
    return c

def lamloads(b: bytes):
    mco, m, n, d, clo, k, qn, (has_self, slf) = pickle.loads(b)
    co = marshal.loads(mco)
    g = sys.modules[m].__dict__
    f = FunctionType(co, g, n, d, tuple(map(cell, clo)))
    f.__kwdefaults__ = k
    f.__qualname__ = qn
    if has_self:
        return MethodType(f, slf)
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

import other

def f1(i: int):
    return i+2
f2 = h((4, 3), 5)
f3 = lambda y: x + y
f4 = other.f

from dataclasses import dataclass

@dataclass
class T:
    j : int = 8
    def f(self, i: int):
        return i + self.j

t = T(7)

fs: list[Callable[[int], int]] = [f1, f2, f3, f4, t.f, T().f]

for f in fs:
    b = lamdumps(f)
    F = lamloads(b)
    other.incr()
    x += 1
    print(F.__module__, f.__module__)
    print(F.__name__, f.__name__)
    print(F.__qualname__, f.__qualname__)
    print(F(1), f(1))
    print('---')

'''
@expose
def call_impl(f: bytes, args: ...)
    return f(lamloads(f), args)

def call(f: Callable, args: ...)
    return call_impl(lamdumps(f), args)
'''
