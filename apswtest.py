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

def go(path: str='test.db'):
    con = apsw.Connection(path)
    c1 = con.cursor()
    c2 = con.cursor()
    c1.execute('begin')
    c2.execute('begin')

if __name__ == '__main__':
    go()
