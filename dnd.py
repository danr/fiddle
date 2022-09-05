import viable as V
from viable import serve
from viable.provenance import store, js

import csv
import io

from pprint import pp

serve.suppress_flask_logging()

def parse(s_value: str):
    try:
        niff = csv.Sniffer()
        dialect = niff.sniff(s_value)
    except:
        dialect = None
    if dialect:
        reader = csv.DictReader(s_value.splitlines(), dialect=dialect)
        return list(reader)

def reparse(s_value: str):
    rows = parse(s_value)
    if rows:
        out = io.StringIO()
        w = csv.DictWriter(out, rows[0].keys(), dialect='excel', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
        return out.getvalue()

@serve.one()
def index():
    with store.db:
        s = store.str(name='s')
        p = store.str(name='p')
    print(repr({'s': s.value, 'p': p.value}))
    check = '(this.selectionStart == 0 || this.SelectionEnd == 0) && (event.preventDefault(), 1) &&'
    yield s.textarea().extend(
        placeholder='enter csv here...',
        rows='15',
        cols='120',
        onpaste=check + store.update(p, js('event.clipboardData.getData("text/plain")')).goto(),
        ondrop=check + store.update(p, js('event.dataTransfer.getData("text/plain")')).goto(),
    )
    yield V.script(V.raw('''
        window.ignore_focus = true
    '''), eval=True)
    if p.value:
        r = reparse(p.value)
        print('reparsed:', r)
        if r is not None:
            yield store.update(p, '').update(s, r).goto_script()
        else:
            yield store.update(p, '').goto_script()
    else:
        pp(parse(s.value))
