from __future__ import annotations
from typing import *

from pathlib import Path
import importlib
import os
import pty
import runpy
import signal
import sys
import threading
import tty
import os
import argparse
import textwrap

from inotify_simple import INotify, masks, flags

def run(argv: list[str], is_module: bool):
    sys.stderr = sys.stdout
    sys.argv[1:] = argv[1:]
    if is_module:
        runpy.run_module(argv[0], run_name='__main__')
    else:
        runpy.run_path(argv[0], run_name='__main__')
    print('\nvire: child done.')

def main_inner(preload: str, argv: list[str], is_module: bool):
    for name in preload.split(','):
        importlib.import_module(name.strip())
    ino = INotify()
    for name in Path('.').glob('**/*py'):
        ino.add_watch(name, flags.CLOSE_WRITE)
    while True:
        pid = fork(lambda: run(argv, is_module=is_module))
        try:
            events = ino.read(read_delay=5)
        except KeyboardInterrupt:
            print('\nvire: parent recevied ^C, quitting.')
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            quit()
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        # print(events, flush=True)

def spawn(f: Callable[[], None]) -> None:
    threading.Thread(target=f, daemon=True).start()

STDIN_FILENO = 1

def fork(child: Callable[[], None]):
    pid, master_fd = pty.fork()

    if pid == 0:
        child()
        quit()

    try:
        mode = tty.tcgetattr(STDIN_FILENO)
        tty.setraw(STDIN_FILENO)
        restore = True
    except tty.error:    # This is the same as termios.error
        restore = False

    @spawn
    def bg():
        try:
            pty._copy(master_fd)
        finally:
            if restore:
                tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)
        os.close(master_fd)
        os.waitpid(pid, 0)[1]

    return pid

def main():
    parser = argparse.ArgumentParser(
        prog='vire',
        description=textwrap.dedent('''
            Runs a program and reruns it when any files matching **/*py is updated.
            Recommended: run with PYTHONDONTWRITEBYTECODE=x
        ''')
    )
    parser.add_argument('-p', '--preload', help='Modules to preload, comma-separated. Example: "flask,pandas"')
    parser.add_argument('-m', help='Argument is a module, will be run like python -m (using runpy)', action='store_true')
    parser.add_argument(dest='argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    mode = tty.tcgetattr(STDIN_FILENO)
    try:
        main_inner(args.preload, args.argv, is_module=args.m)
    finally:
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

if __name__ == '__main__':
    main()
