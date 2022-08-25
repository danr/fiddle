.mode qbox
create table test(
    k integer as (v -> 'id') unique,
    v text,
    check (typeof(k) = 'integer'),
    check (k >= 0),
    check (json_valid(v))
);
select ifnull(max(k) + 1, 0) from test;
create index test_k on test (k);
insert into test
    select json_object('id', value, 'x', value + 1, 'y', value + 3)
    from generate_series(0) limit 400000;
insert into test values ('{"id": -12, "x": 2, "y": 6, "z": "båt"}');
alter table test add x any as (v -> 'x');
alter table test add y any as (v -> 'y');
alter table test add z text as (v -> 'z');
-- select * from test limit 10;
select rowid, * from test order by k limit 3;
select max(k) from test;
select ifnull(max(k) + 1, 0) from test;
select max(rowid) from test;
select 'done';

-- well, which sql?

@dataclass
class Sentence
    id: int = -1

    def insert(self, con):
        id = con('select ifnull(max(k) + 1, 0) from sentence').fetchone()[0]
        return replace(self, id=id)

s = Sentence(...).insert(db) -- returns the replaced version with inserted id

db.Sentence[by_id]

con

db.insert(Sentence(...))
db.lookup(Sentence, 5)
