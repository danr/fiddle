
'''
I figured out a way to make a mixin for a correctly typed replace method on
data classes. It reuses the type of the constructor of the class, accessed
using Type[Self]. One minor wrinkle is that you get a type error if not
supplying arguments for all fields without default values.
'''

from dataclasses import dataclass, replace, fields
from typing import Type, Any
from typing_extensions import Self

class ReplaceMixin:
    @property
    def replace(self) -> Type[Self]:
        def replacer(*args: Any, **kws: Any) -> Self:
            for field, arg in zip(fields(self), args):
                kws[field.name] = arg
            return replace(self, **kws)
        return replacer # type: ignore

@dataclass
class A(ReplaceMixin):
    x: int = 0
    y: int = 0

a = A(1, 2)
print(a)
print(a.replace(x=10))
print(a.replace(100))
print(a.replace(y=20))

'''output:
A(x=1, y=2)
A(x=10, y=2)
A(x=100, y=2)
A(x=1, y=20)
'''

@dataclass
class B(ReplaceMixin):
    '''
    No default values
    '''
    x: int
    y: int

b = B(1, 2)
print(b)
print(b.replace(y=20)) # Type error: Argument missing for parameter "x"
                       # (however it still does the correct thing at runtime:)

'''output:
B(x=1, y=2)
B(x=1, y=20)
'''
