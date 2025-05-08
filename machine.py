import sys
import tty
import threading

ch = None

class ADC():
    def __init__(self, id: int):
        self.id = id

    def read_u16(self) -> int:
        global ip, ch
        if not ch:
            ch = ip.current_char()  
        if self.id == 27: # left-right
            if ch == "left":
                ch = None
                return 65000
            elif ch == "right":
                ch = None
                return 1
            elif ch not in ["up", "down"]:
                ch = None
            return 32000
        elif self.id == 28: # up-down
            if ch == "up":
                ch = None
                return 1
            elif ch == "down":
                ch = None
                return 65000
            return 32000


class Pin():
    IN = 0
    OUT = 1
    PULL_UP = 0
    PULL_DOWN = 1
    IRQ_RISING = 10

    def __init__(self, id: int, dir: int = OUT, mode: int = PULL_DOWN):
        self.id = id
        self.dir = dir
        self.mode = mode
        self.trigger = None
        self.handler = lambda _: print("nop")

    def irq(self, trigger, handler):
        self.trigger = trigger
        ip.enter_callback = handler


class InputProcessor():
    def __init__(self):
        self.char = None
        self.enter_callback = None
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
            if ch == 'enter' and self.enter_callback:
                self.enter_callback(ch)
                continue
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

ip = InputProcessor()
