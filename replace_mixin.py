
'''
I figured out a way to make a mixin for a correctly typed replace method on
data classes. It reuses the type of the constructor of the class, accessed
using Type[Self]. One minor wrinkle is that you get a type error if not
supplying arguments for all fields without default values.
'''

from __future__ import annotations
from dataclasses import dataclass, replace, fields, MISSING
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

    def get(self, *args: P.args, **kws: P.kwargs) -> R:
        return self._where(self._opts, *args, **kws)[0]

    def limit(self, bound: int | None = None, offset: int | None = None) -> Select[P, R]:
        return self._replace(self._opts.replace(limit=bound, offset=offset))

    def order(self, by: str) -> Select[P, R]:
        return self._replace(self._opts.replace(order=by))

    def __iter__(self):
        yield from self.where() # type: ignore

def coll(cls: Any, *args: Any, **kws: Any):
    for field, arg in zip(fields(cls), args):
        kws[field.name] = arg
    return kws.items()

import json

def sqlquote(s: str) -> str:
    c = "'"
    return c + s.replace(c, c+c) + c

@dataclass
class DB:
    con: sqlite3.Connection
    to_json = json.dumps
    from_json = json.loads
    def get(self, t: Callable[P, R]) -> Select[P, R]:
        def where(opts: SelectOptions, *args: P.args, **kws: P.kwargs) -> list[R]:
            clauses: list[str] = []
            for f, a in coll(t, *args, **kws):
                clauses += [f"value -> {sqlquote(f)} = {sqlquote(json.dumps(a))} -> '$'"]
            if clauses:
                where_clause = 'where ' + ' and '.join(clauses)
            else:
                where_clause = ''
            stmt = f'select value from {t.__name__} {where_clause} order by value ->> {opts.order!r}'
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

from typing import Protocol
import textwrap

class DBMixin(ReplaceMixin):
    id: int

    def save(self, db: DB) -> Self:
        Table = self.__class__.__name__
        meta = getattr(self.__class__, '__meta__', None)
        db.con.executescript(textwrap.dedent(f'''
            create table if not exists {Table} (
                id integer as (value ->> 'id') unique,
                value text,
                check (typeof(id) = 'integer'),
                check (id >= 0),
                check (json_valid(value))
            );
            create index if not exists {Table}_id on {Table} (id);
        '''))
        if isinstance(meta, Meta) and meta.log:
            LogTable = meta.log_table or f'{Table}Log'
            exists = any(
                db.con.execute(f'''
                    select 1 from sqlite_master where type = "table" and name = ?
                ''', [LogTable])
            )
            if not exists:
                db.con.executescript(textwrap.dedent(f'''
                    create table {LogTable} (
                        t timestamp default (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
                        action text,
                        id integer,
                        new json
                    );
                    create trigger
                        {Table}_insert after insert on {Table}
                    begin
                        insert into {LogTable}(id, new, action) values (NEW.id, NEW.value, "insert");
                    end;
                    create trigger
                        {Table}_update after update on {Table}
                    begin
                        insert into {LogTable}(id, new, action) values (OLD.id, NEW.value, "update");
                    end;
                    create trigger
                        {Table}_delete after delete on {Table}
                    begin
                        insert into {LogTable}(id, new, action) values (OLD.id, NULL, "delete");
                    end;
                '''))
        if self.id == -1:
            exists = False
        else:
            exists = any(
                db.con.execute(f'''
                    select 1 from {Table} where id = ?
                ''', [self.id])
            )
        if exists:
            db.con.execute(f'''
                update {Table} set value = ? -> '$' where id = ?
            ''', [json.dumps(asdict(self)), self.id])
            db.con.commit()
            return self
        else:
            if self.id == -1:
                id, = db.con.execute(f'''
                    select ifnull(max(id) + 1, 0) from {Table};
                ''').fetchone()
                res = self.replace(id=id) # type: ignore
            else:
                id = self.id
                res = self
            db.con.execute(f'''
                insert into {Table} values (? -> '$')
            ''', [json.dumps(asdict(res))])
            db.con.commit()
            return res

    def delete(self, db: DB) -> int:
        Table = self.__class__.__name__
        c = db.con.execute(f'''
            delete from {Table} where id = ?
        ''', [self.id])
        return c.rowcount

    def reload(self, db: DB) -> Self:
        return db.get(self.__class__).where(id=self.id)[0]

@dataclass(frozen=True)
class Meta:
    log: bool = False
    log_table: None | str = None

@dataclass
class Todo(DBMixin):
    msg: str = ''
    done: bool = False
    # deleted: None | datetime = None
    # created: datetime = field(default_factory=lambda: datetime.now())
    id: int = -1

    __meta__: ClassVar[Meta] = Meta(log=True)

@dataclass
class Person(DBMixin):
    name: str = ''
    parent_ids: list[int] = field(default_factory=list)
    id: int = -1

    def parents(self, db: DB):
        return [
            p
            for pid in self.parent_ids
            for p in db.get(Person).where(id=pid)
        ]

    __meta__: ClassVar[Meta] = Meta(log=True)

from pprint import pp

def main():
    with sqlite3.connect(':memory:') as con:
        db: DB = DB(con)

        Todos = db.get(Todo)
        Persons = db.get(Person)

        Todo('banana').save(db)
        Todo('flapp', done=True).save(db)
        Todo('boop').save(db)
        Todo('floop').save(db)
        h = Todo('happ').save(db)
        pp(list(db.con.execute("select * from Todo")))
        pp(Todos.where(done=True))
        pp(Todos.where(done=False))
        pp(Todos.where(done=True, msg='flapp'))
        pp(Todos.where(msg='banana'))
        pp(Todos.where(id=2))
        pp(h)
        h = h.replace(msg='happ 2', done=True)
        pp(h.save(db))
        pp(list(db.con.execute("select * from Todo")))
        pp(Todos.where())
        pp(Todos.order('msg').where())

        print('---')

        dan = Person('Dan').save(db)

        dan.delete(db)
        dan.save(db)

        unni = Person('Unni').save(db)
        iris = Person('Iris', parent_ids=[dan.id, unni.id]).save(db)

        pp([dan, unni, iris])

        pp([p for p in Persons])
        pp(Persons.order('name').where())

        pp(Persons.where(parent_ids=[]))
        pp(Persons.where(parent_ids=[0, 1]))

        ps: list[Person] = iris.parents(db)
        pp(ps)

        pp(list(db.con.execute("""
            select
                a.value, b.value
            from
                Person a,
                json_each(a.value -> 'parent_ids') p,
                Person b
            where
                b.id = p.value
        """)))

        Persons.get(id=1).replace(name='Unni Björklund').save(db)
        u = Persons.get(id=0)
        u.delete(db)
        u.delete(db)
        u.save(db)
        print(Persons.get(id=1).name)

        if 0:
            def lens(value: str, update: Callable[[str], None], js_fragment: str='event.value'):
                return {
                    'value': value,
                    'onchange': call(update, js(js_fragment))
                }

            input(
                lens(dan.name, lambda s: dan.update(name=s))
            )

        if 1:
            from pathlib import Path
            db.con.commit()
            Path("lol.db").unlink(missing_ok=True)
            db.con.execute('vacuum into "lol.db"')
            # db.con.close()
            from subprocess import check_output
            print(
                check_output(
                    [
                        'sqlite3',
                        'lol.db',
                        '.mode box',
                        'select *, value ->> "name" as "name" from Person;'
                        'select *, value ->> "msg" as msg, value ->> "done" as done from Todo;'
                        'select *, new ->> "name" from PersonLog;'
                        'select *, new ->> "msg" as msg, new ->> "done" as done, new ->> "$.id" from TodoLog;'
                    ],
                    encoding='utf8'
                )
            )

if __name__ == '__main__':
    main()
