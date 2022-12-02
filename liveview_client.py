from libpykak import q, KakConnection
from datetime import datetime
k = KakConnection.init('fiddle')
client, *_ = k.val.client_list
k.eval(q('echo', datetime.now().isoformat(sep=' '), client), client=client)
k.eval('''
    try %(
        decl line-specs livelines
    )
    try %(
        decl range-specs livevals
    )
    addhl -override buffer/ replace-ranges livevals
    addhl -override buffer/ flag-lines Default livelines
''', client=client)
import os

def underscore_encode(s: str) -> str:
    return s.replace('_', '__').replace('/', '_')

import time
from inotify_simple import INotify, masks, flags

my_file = '/tmp/' + underscore_encode(os.getcwd())

ino = INotify()
ino.add_watch(my_file, flags.MODIFY | flags.CLOSE_WRITE)
fp = None
st: dict[tuple[str, str, str], str] = {}
ts = '1'
while True:
    for e in ino.read():
        print(e, flags.from_mask(e.mask))
        if e.mask & flags.MODIFY:
            if not fp:
                fp = open(my_file, 'r', buffering=1)
                st = {}
                [[ts]] = k.eval_sync_up(f'{k.pk_send} %val[timestamp]', client=client)
            for line in fp:
                filename, lineno, line_len, value = line.strip().split('\t')
                st[filename, lineno, line_len] = value
                data = [q(f'{lineno}.{int(line_len)+1}+0|  ⇓ {str(value).replace("|", "||")}') for (_, lineno, line_len), value in st.items()]
                k.eval(h := f'set buffer={filename} livevals {ts} {" ".join(data)}', client=client)
                print(h)
                # print(filename, lineno, value, txt, sep='\t')
                # k.eval(q('echo', (filename, lineno, value, txt)
                print(line.strip())
        if e.mask & flags.CLOSE_WRITE:
            fp = None

