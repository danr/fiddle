from __future__ import annotations
from flask.wrappers import Response
from typing import Any
from flask import after_this_request, request

import os
import secrets
# import sqlite3
import apsw
from threading import Lock

from typing import *
import threading
import time

def spawn(f: Callable[[], None]) -> None:
    threading.Thread(target=f, daemon=True).start()

def go(path: str='race.db'):
    con = apsw.Connection(path)
    for res in con.cursor().execute('''
        pragma journal_mode=WAL;
    '''):
        print(res)
    con.cursor().execute('''
        create table if not exists data (key integer primary key, value);
        create index if not exists data_key on data(key);
    ''')

    cl = Lock()

    K = 1_000

    def write():
        for k in range(K // 10):
            with cl:
                print(threading.current_thread(), 'begin', k)
                con.cursor().execute('begin transaction')
                for _ in range(10):
                    con.cursor().execute('''
                        insert into data values (random(), hex(randomblob(8)));
                    ''')
                print(threading.current_thread(), 'end', k)
                con.cursor().execute('commit')
            time.sleep(0)

    def read():
        for k in range(K // 10):
            for i in con.cursor().execute('select key, value from data order by key limit 10'):
                time.sleep(0.01)
            if k % 10 == 0:
                print(threading.current_thread(), k)

    for w in range(10):
        threading.Thread(target=write).start()
    for r in range(10):
        threading.Thread(target=read).start()

if __name__ == '__main__':
    go()
