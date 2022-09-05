from __future__ import annotations
from flask.wrappers import Response
from typing import Any
from flask import after_this_request, request

import os
import secrets
import sqlite3
from threading import Lock

from typing import *
import threading

def spawn(f: Callable[[], None]) -> None:
    threading.Thread(target=f, daemon=True).start()

def go(path: str='race.db'):
    con = sqlite3.connect(path, check_same_thread=False)
    con.executescript('''
        pragma locking_mode=EXCLUSIVE;
        pragma journal_mode=WAL;
        create table if not exists data (key integer primary key, value);
        create index if not exists data_key on data(key);
    ''')

    cl = Lock()

    K = 1_000

    def write():
        for k in range(K):
            with cl:
                con.execute('''
                    insert into data values (random(), hex(randomblob(8)));
                ''')
                if k % 10 == 1:
                    print(threading.current_thread(), 'begin', k)
                    con.commit()
                    print(threading.current_thread(), 'end', k)

    def read():
        for k in range(K):
            con.execute('select key, value from data order by key limit 10').fetchall()
            if k % 1000 == 999:
                print(threading.current_thread(), k)

    for w in range(10):
        threading.Thread(target=write).start()
    for r in range(10):
        threading.Thread(target=read).start()

if __name__ == '__main__':
    go()
