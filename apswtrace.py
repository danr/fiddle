
import apsw
import apsw.trace
class dotdict(dict):
    __getattr__ = dict.__getitem__
tr = apsw.trace.APSWTracer(dotdict(
    output = '-',
    sql = True,
    rows = True,
    length = 180,
    timestamps = True,
    report = True,
    reports =','.join(["summary", "popular", "aggregate", "individual"]),
    reportn = 15,
    thread = False,
))

# ...  open a db ...

tr.report()

