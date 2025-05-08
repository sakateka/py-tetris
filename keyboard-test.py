import sys
import tty
import time
import threading


class InputProcessor():
    def __init__(self):
        self.char = None
        tty.setcbreak(sys.stdin.fileno())

        x = threading.Thread(target=self.process_input, daemon=True)
        x.start()

    def current_char(self):
        ch = self.char
        self.char = None
        return ch

    def process_input(self):
        while True:
            ch = self.getchr()
            self.char = ch

    def getchr(self):
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Escape key
            ch = sys.stdin.read(2)
            if ch == '[A':  # ]
                return "up"
            elif ch == '[B':  # ]
                return "down"
            elif ch == '[C':  # ]
                return "right"
            elif ch == '[D':  # ]
                return "left"
            elif ch == '[5':  # ]
                ch = sys.stdin.read(1)
                return "page-up"
            elif ch == '[6':  # ]
                ch = sys.stdin.read(1)
                return "page-down"
        elif ch == '\r' or ch == '\n':  # Enter key
            return "enter"
        elif ch == 'e':
            return "exit"
        elif ch == ' ':  # Space key
            return "space"
        else:
            return ch

if __name__ == '__main__':
    ip = InputProcessor()
    key = ''
    while key != 'e':
        time.sleep(0.1)
        key = ip.current_char()
        print(f"input: {key}")
