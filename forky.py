
import pty
import tty
import os
from threading import Timer
from contextlib import contextmanager
import time

STDIN_FILENO = 1


def timeit(desc: str=''):
    # The inferred type for the decorated function is wrong hence this wrapper to get the correct type

    @contextmanager
    def worker():
        t0 = time.monotonic_ns()
        yield
        T = time.monotonic_ns() - t0
        print(f'{T/1e6:.1f}ms {desc}')

    return worker()

from flask import Flask

def child():
    Timer(0.25, lambda: os.kill(os.getpid(), 15)).start()
    app = Flask(__name__)
    @app.route('/')
    def root():
        return 'root'
    app.run(port=5001)

def main():
    for i in range(50):
        with timeit(f'iter {i}'):
            inner()

def inner():
    pid, master_fd = pty.fork()

    if pid == 0:
        child()
        quit()

    # print("I am the master")

    try:
        mode = tty.tcgetattr(STDIN_FILENO)
        tty.setraw(STDIN_FILENO)
        restore = True
    except tty.error:    # This is the same as termios.error
        restore = False

    try:
        pty._copy(master_fd)
    finally:
        if restore:
            tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    os.close(master_fd)
    os.waitpid(pid, 0)[1]

if __name__ == '__main__':
    print('MAIN')
    main()


