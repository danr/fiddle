
'''
I figured out a way to make a mixin for a correctly typed replace method on
data classes. It reuses the type of the constructor of the class, accessed
using Type[Self]. One minor wrinkle is that you get a type error if not
supplying arguments for all fields without default values.
'''

from __future__ import annotations
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

class PrivateReplaceMixin:
    @property
    def _replace(self) -> Type[Self]:
        def replacer(*args: Any, **kws: Any) -> Self:
            for field, arg in zip(fields(self), args):
                kws[field.name] = arg
            return replace(self, **kws)
        return replacer # type: ignore

@dataclass
class A(ReplaceMixin):
    x: int = 0
    y: int = 0

# a = A(1, 2)
# print(a)
# print(a.replace(x=10))
# print(a.replace(100))
# print(a.replace(y=20))

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

@dataclass
class C(A):
    cc: int = 9

C().replace(cc=4, y=4) # types correctly with inheritance

# b = B(1, 2, 3)
# print(b)
# print(b.replace(y=20)) # Type error: Argument missing for parameter "x"
#                        # (however it still does the correct thing at runtime:)

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

# ra = repl(A)
# rb = repl(B)
# print(ra(a, x=1000))
# print(rb(b, 99, y=98, z=97))

from datetime import datetime
from dataclasses import field
from typing import Any
import sqlite3

X = TypeVar('X')

@dataclass(frozen=True)
class SelectOptions(ReplaceMixin):
    order: str = 'id'
    limit: int | None = None
    offset: int | None = None

@dataclass(frozen=True)
class Select(Generic[P, R], PrivateReplaceMixin):
    _opts: SelectOptions = SelectOptions()
    _where: Callable[Concatenate[SelectOptions, P], list[R]] = cast(Any, ...)

    def where(self, *args: P.args, **kws: P.kwargs) -> list[R]:
        return self._where(self._opts, *args, **kws)

    def limit(self, bound: int | None = None, offset: int | None = None) -> Select[P, R]:
        return self._replace(self._opts.replace(limit=bound, offset=offset))

    def order(self, by: str) -> Select[P, R]:
        return self._replace(self._opts.replace(order=by))

    def __iter__(self):
        yield from self.where() # type: ignore

def coll(nonce: Any, *args: Any, **kws: Any):
    for field, arg in zip(fields(nonce), args):
        kws[field.name] = arg
    return kws.items()

import json

@dataclass
class DB:
    con: sqlite3.Connection
    def get(self, t: Callable[P, R]) -> Select[P, R]:
        def where(opts: SelectOptions, *args: P.args, **kws: P.kwargs) -> list[R]:
            clauses: list[str] = []
            for f, a in coll(t, *args, **kws):
                clauses += [f'v ->> {f!r} = {json.dumps(a)}']
            if clauses:
                where_clause = 'where ' + ' and '.join(clauses)
            else:
                where_clause = ''
            stmt = f'select v from {t.__name__} {where_clause} order by v ->> {opts.order!r}'
            limit, offset = opts.limit, opts.offset
            if limit is None:
                limit = -1
            if offset is None:
                offset = 0
            if limit != -1 or offset != 0:
                stmt += f' limit {limit} offset {offset}'
            print(stmt)
            return [
                t(**json.loads(v))
                for v, in self.con.execute(stmt).fetchall()
            ]
        return Select(_where=where)

from dataclasses import asdict

db: DB = ... # type: ignore

from typing import Protocol
import textwrap

class DBMixin(ReplaceMixin):
    id: int

    def save(self) -> Self:
        tbl = self.__class__.__name__
        db.con.executescript(textwrap.dedent(f'''
            create table if not exists {tbl} (
              id integer as (v ->> 'id') unique,
              v text,
              check (typeof(id) = 'integer'),
              check (id >= 0),
              check (json_valid(v))
            );
            create index if not exists {tbl}_id on {tbl} (id);
        '''))
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
            res = self.replace(id=id) # type: ignore
            db.con.execute(f'''
                insert into {tbl} values (?)
            ''', [json.dumps(asdict(res))])
            db.con.commit()
            return res

@dataclass
class Todo(DBMixin):
    msg: str = ''
    done: bool = False
    # deleted: None | datetime = None
    # created: datetime = field(default_factory=lambda: datetime.now())
    id: int = -1

@dataclass
class Person(DBMixin):
    name: str = ''
    parent_ids: list[int] = field(default_factory=list)
    id: int = -1

    @property
    def parents(self):
        return [
            p
            for pid in self.parent_ids
            for p in db.get(Person).where(id=pid)
        ]

from pprint import pp

with sqlite3.connect(':memory:') as con:
    db: DB = DB(con)

    Todos = db.get(Todo)
    Persons = db.get(Person)

    Todo('banana').save()
    Todo('flapp', done=True).save()
    Todo('boop').save()
    Todo('floop').save()
    h = Todo('happ').save()
    pp(list(db.con.execute("select * from Todo")))
    pp(Todos.where(done=True))
    pp(Todos.where(done=False))
    pp(Todos.where(done=True, msg='flapp'))
    pp(Todos.where(msg='banana'))
    pp(Todos.where(id=2))
    pp(h)
    h = h.replace(msg='happ 2', done=True)
    pp(h.save())
    pp(list(db.con.execute("select * from Todo")))
    pp(Todos.where())
    pp(Todos.order('msg').where())

    print('---')

    dan = Person('Dan').save()
    unni = Person('Unni').save()
    iris = Person('Iris', parent_ids=[dan.id, unni.id]).save()

    pp([dan, unni, iris])

    pp([p for p in Persons])
    pp(Persons.order('name').where())

    ps: list[Person] = iris.parents
    pp(ps)

    pp(list(db.con.execute("""
        select
            a.v, b.v
        from
            Person a,
            json_each(a.v -> 'parent_ids') p,
            Person b
        where
            b.id = p.value
    """)))

    if 0:
        from pathlib import Path
        Path("lol.db").unlink(missing_ok=True)
        db.con.execute('vacuum into "lol.db"')
