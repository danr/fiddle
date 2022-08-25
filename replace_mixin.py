
'''
I figured out a way to make a mixin for a correctly typed replace method on
data classes. It reuses the type of the constructor of the class, accessed
using Type[Self]. One minor wrinkle is that you get a type error if not
supplying arguments for all fields without default values.
'''

from dataclasses import dataclass, replace, fields
from typing import Type, Any
from typing_extensions import Self
from typing import *
from typing_extensions import *

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
    z: int

b = B(1, 2, 3)
print(b)
print(b.replace(y=20)) # Type error: Argument missing for parameter "x"
                       # (however it still does the correct thing at runtime:)

'''output:
B(x=1, y=2)
B(x=1, y=20)
'''

P = ParamSpec('P')
R = TypeVar('R')

def repl(con: Callable[P, R]) -> Callable[Concatenate[R, P], R]:
    def replacer(v: R, *args: P.args, **kws: P.kwargs) -> R:
        for field, arg in zip(fields(v), args):
            kws[field.name] = arg
        return replace(v, **kws)
    return replacer # type: ignore

ra = repl(A)
rb = repl(B)
print(ra(a, x=1000))
print(rb(b, 99, y=98, z=97))

from datetime import datetime
from dataclasses import field
from typing import Any
import sqlite3

X = TypeVar('X')

@dataclass
class Select(Generic[P, R]):
    where: Callable[P, list[R]]
    # __iter__: Callable[[], list[R]]

def coll(nonce: Any, *args: Any, **kws: Any):
    for field, arg in zip(fields(nonce), args):
        kws[field.name] = arg
    return kws.items()

import json

@dataclass
class DB:
    con: sqlite3.Connection
    def get(self, t: Callable[P, R]) -> Select[P, R]:
        def where(*args: P.args, **kws: P.kwargs) -> list[R]:
            clauses: list[str] = ['1']
            for f, a in coll(t, *args, **kws):
                clauses += [f'v ->> {f!r} = {json.dumps(a)}']
            clause = ' and '.join(clauses)
            stmt = f'select v from {t.__name__} where {clause}'
            print(stmt)
            return [
                t(**json.loads(v))
                for v, in self.con.execute(stmt).fetchall()
            ]
        return Select(where)

from dataclasses import asdict

@dataclass
class Todo(ReplaceMixin):
    msg: str = ''
    done: bool = False
    # deleted: None | datetime = None
    # created: datetime = field(default_factory=lambda: datetime.now())
    id: int = -1

    def save(self, db: DB) -> Self:
        tbl = self.__class__.__name__
        db.con.executescript(f'''
            create table if not exists {tbl} (
                id integer as (v -> 'id') unique,
                v text,
                check (typeof(id) = 'integer'),
                check (id >= 0),
                check (json_valid(v))
            );
            create index if not exists {tbl}_id on {tbl} (id);
        ''')
        exists = db.con.execute(f'''
            select 1 from {tbl} where id = ?
        ''', [self.id]).fetchall()
        if exists:
            db.con.execute(f'''
                update {tbl} set v = ? where id = ?
            ''', [json.dumps(asdict(self)), self.id])
            db.con.commit()
            return self
        else:
            id, = db.con.execute(f'''
                select ifnull(max(id) + 1, 0) from {tbl};
            ''').fetchone()
            res = self.replace(id=id)
            db.con.execute(f'''
                insert into {tbl} values (?)
            ''', [json.dumps(asdict(res))])
            db.con.commit()
            return res

from pprint import pp

with sqlite3.connect(':memory:') as con:
    db: DB = DB(con)
    Todo('banana').save(db)
    Todo('boop').save(db)
    Todo('floop').save(db)
    Todo('flapp', done=True).save(db)
    h = Todo('happ').save(db)
    pp(list(db.con.execute("select * from Todo")))
    pp(db.get(Todo).where(done=True))
    pp(db.get(Todo).where(msg='banana'))
    pp(db.get(Todo).where(id=2))
    pp(h)
    h = h.replace(msg = 'happ 2', done=True)
    pp(h.save(db))
    pp(db.get(Todo).where(id=h.id))
    pp(list(db.con.execute("select * from Todo")))
    pp(db.get(Todo).where(done=True))

