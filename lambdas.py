from __future__ import annotations
from dataclasses import dataclass
from types import FunctionType, CellType, MethodType
from typing import Any, Callable
import marshal
import sys

@dataclass(frozen=True, slots=True)
class Box:
    value: Any

@dataclass(frozen=True, slots=True)
class Function:
    marshalled_code: bytes
    module: str
    name: str
    defaults: Any
    closure: tuple[Box | Function, ...]
    kwdefaults: dict[str, Any]
    qualname: str
    has_self: bool
    bound_self: Any

    @staticmethod
    def freeze(f: Callable[..., Any]):
        closure: list[Box | Function] = []
        for cell in f.__closure__ or ():
            c = cell.cell_contents
            if hasattr(c, '__code__') and hasattr(c, '__closure__'):
                closure += [Function.freeze(c)]
            else:
                closure += [Box(c)]
        return Function(
            marshal.dumps(f.__code__),
            f.__module__,
            f.__name__,
            f.__defaults__,
            tuple(closure),
            f.__kwdefaults__,
            f.__qualname__,
            hasattr(f, '__self__'),
            getattr(f, '__self__', None),
        )

    def thaw(self) -> Callable[..., Any]:
        code = marshal.loads(self.marshalled_code)
        g = sys.modules[self.module].__dict__
        closure: list[Any] = [
            Function._make_cell(c.thaw() if isinstance(c, Function) else c.value)
            for c in self.closure
        ]
        f = FunctionType(code, g, self.name, self.defaults, tuple(closure))
        f.__kwdefaults__ = self.kwdefaults
        f.__qualname__ = self.qualname
        if self.has_self:
            return MethodType(f, self.bound_self)
        return f

    @staticmethod
    def _make_cell(co: Any) -> CellType:
        c = CellType()
        c.cell_contents = co
        return c

import other

x = 1

@dataclass
class T:
    j : int = 8
    def f(self, i: int):
        return i + self.j

@dataclass
class NotF:
    def __call__(self, i: int):
        return i + 1

def main():
    global x

    def h(us: tuple[int, int], z: int):
        def g(j: int):
            return j + 1
        return lambda a, b=4, *, c=9: 1 + x + us[0] + z + g(a)

    def f1(i: int):
        def g(j: int):
            return j + i
        def h(j: int):
            return g(j) + i
        return g(i) + h(i)
    f2 = h((4, 3), 5)
    f3 = lambda y: x + y
    f4 = other.f

    t = T(7)

    def make_not_f():
        f=NotF()
        g = T().f
        def not_f(i: int) -> int:
            return f(i) + g(i)
        return not_f

    fs: list[Callable[[int], int]] = [f1, f2, f3, f4, t.f, T().f, make_not_f()]

    for f in fs:
        b = Function.freeze(f)
        print(b.closure)
        import pickle
        print(len(pickle.dumps(b)))
        F = b.thaw()
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

if __name__ == '__main__':
    main()
