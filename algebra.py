
from typing import *
A = TypeVar('A')

class B(Protocol, Generic[A]):
    def lit(self, val: int) -> A: ...
    def add(self, lhs: A, rhs: A) -> A: ...

def q(m: B[A]) -> A:
    memmove()
    return m.add(m.lit(1), m.lit(2))

class Eval(B[int]):
    def lit(self, val: int):
        return val

    def add(self, lhs: int, rhs: int) -> int:
        return lhs + rhs

class Print(B[str]):
    def lit(self, val: int):
        return str(val)

    def add(self, lhs: str, rhs: str) -> str:
        return f'({lhs}+{rhs})'

class C(Generic[A], B[A], Protocol):
    def mul(self, lhs: A, rhs: A) -> A: ...

def qc(m: C[A]) -> A:
    return m.add(m.lit(1), m.mul(m.lit(2), m.lit(3)))

class PrintC(Print, C[str]):
    def mul(self, lhs: str, rhs: str):
        return f'({lhs}*{rhs})'

class EvalC(Eval, C[int]):
    def mul(self, lhs: int, rhs: int):
        return lhs * rhs

ev = EvalC()
pr = PrintC()

print(q(ev), '...', q(pr))
print(qc(ev), '...', qc(pr))


