def getchar():
    '''
    Returns a single character from standard input

    https://gist.github.com/jasonrdsouza/1901709
    '''
    import sys
    import tty
    import termios
    import atexit

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def cleanup():
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    atexit.register(cleanup)
    try:
        tty.setcbreak(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        atexit.unregister(cleanup)
        cleanup()
    return ch
