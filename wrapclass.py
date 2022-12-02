
import typing as t
import functools

def trace_class(cls: t.Type[t.Any]):
    for k, v in list(cls.__dict__.items()):
        if not k.startswith('_'):
            def new_scope(v=v, k=k):
                @functools.wraps(v)
                def new_v(self, *args, **kws):
                    res = v(self, *args, **kws)
                    print(k, *args, *kws.items(), '=', res)
                    return res
                setattr(cls, k, new_v)
            new_scope()
    return cls

@trace_class
class Example:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def set_x(self, new_x: int):
        self.x = new_x

    def calc(self, theta: int):
        return self.x * self.y * theta


ex = Example(2, 3)
print(ex.calc(4))
ex.set_x(5)
print(ex.calc(4))


