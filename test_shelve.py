
import shelve

with shelve.open('test.db', 'n') as d:
    pass

def t(k: str):
    for i in range(1000):
        with shelve.open('test.db') as d:
            d[f'{k}{i}'] = 'banana'
            print(k, i)

from threading import Thread

ts = [
    Thread(target=t, args=('a')),
    Thread(target=t, args=('b')),
    Thread(target=t, args=('c')),
    Thread(target=t, args=('d')),
]

for m in ts:
    m.start()

for m in ts:
    m.join()

with shelve.open('test.db', 'r') as d:
    print(len(d))
