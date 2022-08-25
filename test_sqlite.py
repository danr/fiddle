
import sqlite3
from pathlib import Path
from typing import Any, Callable
import threading
from threading import Thread, RLock
import time
import signal, sys

# Path('test.sqlite').unlink(missing_ok=True)

con = sqlite3.connect('test.sqlite', check_same_thread=False)
print('restart')

lock = RLock()
closed = False

with lock:
    con.executescript('''
        pragma journal_mode=WAL;
        create table if not exists data (k, v);
    ''')

    print(con.execute('select count(*) from data').fetchone())

import atexit

def handle_signal(signum: int, _frame: Any):
    global closed
    with lock:
        if not closed:
            closed = True
            print('written in closing:', con.execute('select count(*) from data').fetchone())
            con.commit()
            con.close()
            if signum != 0:
                sys.exit(1)

signal.signal(signal.SIGTERM, handle_signal)
atexit.register(lambda: handle_signal(0, None))

def spawn(f: Callable[[], None]) -> None:
    threading.Thread(target=f, daemon=True).start()

@spawn
def serializer():
    global closed
    last = 0
    while True:
        time.sleep(0.1)
        with lock:
            if closed:
                return
            changes = con.total_changes - last
            if changes:
                print(f'committing {changes} changes')
                last = con.total_changes
                con.commit()

def sql(msg: str, *args: Any):
    global closed
    with lock:
        if not closed:
            return con.execute(msg, args)

def t(k: str):
    for i in range(10000):
        sql('insert into data values (?, ?)', f'{k}{i}', 'banana')
        if 0:
          if i % 1000 == 0:
            with lock:
                print(con.execute('select count(*) from data').fetchone())

    print(k, '...')

import string

ts = [
    Thread(target=t, args=(c), daemon=True)
    for c in string.ascii_lowercase
]

for m in ts:
    m.start()

for m in ts:
    m.join()

with lock:
    print(con.execute('select count(*) from data').fetchone())

with lock:
    closed = True
    con.commit()
    con.close()

with sqlite3.connect('test.sqlite') as con2:
    print(con2.execute('select count(*) from data').fetchone())

