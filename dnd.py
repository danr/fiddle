import viable as vi
from viable.provenance import store

vi.serve.suppress_flask_logging()

@vi.serve.one()
def index():
    s = store.str()
    print(repr(s.value))
    yield s.textarea().extend(
        rows='25',
        cols='120',
        onpaste='''
            console.log(event)
            console.log(JSON.stringify(event.clipboardData.types))
            console.log("text/plain", event.clipboardData.getData("text/plain"))
            console.log("text/html", event.clipboardData.getData("text/html"))
        ''',
        ondrop='''
            console.log(event)
            console.log(JSON.stringify(event.dataTransfer.types))
            console.log("text/plain", event.dataTransfer.getData("text/plain"))
            console.log("text/html", event.dataTransfer.getData("text/html"))
        ''',
        onchange='console.log(event)',
    )
