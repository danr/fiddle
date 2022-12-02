import threading
import time
from pathlib import Path

def poller():
    while True:
        seen = list(Path('.').glob('*.tmp'))
        print('I can see', len(seen), 'paths:', *seen)
        time.sleep(0.1)

def start_poller():
    threading.Thread(target=poller, daemon=True).start()

def main():
    start_poller()
    paths = [Path(f'test-{i}.tmp') for i in range(6)]
    for path in paths:
        path.write_text('test')
        time.sleep(0.25)
    for path in paths:
        path.unlink()
        time.sleep(0.25)

if __name__ == '__main__':
    main()
