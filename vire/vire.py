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
import argparse

from inotify_simple import INotify, masks, flags

def run(argv: list[str], is_module: bool, clear_opt: int):
    sys.dont_write_bytecode = True
    sys.argv[1:] = argv[1:]
    clear(clear_opt)
    if is_module:
        runpy.run_module(argv[0], run_name='__main__')
    else:
        runpy.run_path(argv[0], run_name='__main__')
    print('\nvire: child done.')

def sigterm(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

def clear(clear_opt: int):
    # from entr: https://github.com/eradman/entr/blob/master/entr.c
    # 2J - erase the entire display
    # 3J - clear scrollback buffer
    # H  - set cursor position to the default
    if clear_opt == 1:
        print('\033[2J\033[H', end='', flush=True)
    if clear_opt >= 2:
        print('\033[2J\033[3J\033[H', end='', flush=True)

def main_inner(preload: str, argv: list[str], is_module: bool, glob_pattern: str, clear_opt: int=0):
    for name in preload.split(','):
        importlib.import_module(name.strip())
    ino = INotify()
    for name in Path('.').glob(glob_pattern):
        ino.add_watch(name, flags.MODIFY)
    while True:
        pid = fork(lambda: run(argv, is_module=is_module, clear_opt=clear_opt))
        try:
            events = ino.read(read_delay=5)
        except KeyboardInterrupt:
            print('\nvire: parent received ^C, quitting.')
            sigterm(pid)
            quit()
        sigterm(pid)
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
        description='''
            Runs a program and reruns it on updating files matching a glob (default **/*.py).
        ''',
        add_help=False,
    )
    parser.add_argument('--help', '-h', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--clear', '-c', action='count', default=0, help='Clear the screen before invoking the utility. Specify twice to erase the scrollback buffer.')
    parser.add_argument('--preload', '-p', metavar='M', help='Modules to preload, comma-separated. Example: flask,pandas')
    parser.add_argument('--glob', '-g', metavar='G', help='Watch for updates to files matching this glob, Default: **/*.py', default='**/*.py')
    parser.add_argument('-m', action='store_true', help='Argument is a module, will be run like python -m (using runpy)')
    parser.add_argument(dest='argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.argv or args.help:
        parser.print_help()
        quit()

    mode = tty.tcgetattr(STDIN_FILENO)
    try:
        main_inner(
            args.preload,
            args.argv,
            is_module=args.m,
            glob_pattern=args.glob,
            clear_opt=args.clear,
        )
    finally:
        tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

if __name__ == '__main__':
    main()
