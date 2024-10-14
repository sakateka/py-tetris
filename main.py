import tty
import copy
import sys
import random
import threading
from time import sleep
from io import StringIO

ESCAPE = "\x1b"
CURSOR_UP = ESCAPE + "[1A"
CLEAR_LINE = ESCAPE + "[2K\r"
CURSOR_UP_AND_CLEAR_LINE = CURSOR_UP + CLEAR_LINE

Y_INIT_POS = 1
X_INIT_POS = 4
SCORE = 0
WIDTH = 10
HEIGHT: int = 20
EMPTY_ROW: list = ["  "] * WIDTH
SCREEN: list = EMPTY_ROW.copy() * HEIGHT
CONCRETE: list = EMPTY_ROW.copy() * HEIGHT
STRIKE: list = ["  "] + ["##"] * (WIDTH - 2) + ["  "]


O: list[list[str]] = [
     ["##", "##"],
     ["##", "##"],
]

I: list[list[str]] = [
     ["##"],
     ["##"],
     ["##"],
     ["##"],
]

L: list[list[str]] = [
     ["##", "  "],
     ["##", "  "],
     ["##", "##"],
]

J: list[list[str]] = [
     ["  ", "##"],
     ["  ", "##"],
     ["##", "##"],
]

S: list[list[str]] = [
     ["  ", "##", "##"],
     ["##", "##", "  "],
]

Z: list[list[str]] = [
     ["##", "##", "  "],
     ["  ", "##", "##"],
]

T: list[list[str]] = [
     ["##", "##", "##"],
     ["  ", "##", "  "],
]

TETRAMINOS = [O, I, L, J, S, Z, T]


def render() -> str:
    result = StringIO()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            result.write(SCREEN[x+WIDTH*y])
        result.write("\n")
    result.seek(0)
    return result.getvalue()

def can_place(tetramino: list[list[str]], xc, yc) -> bool:
    for y in range(len(tetramino)):
        for x in range(len(tetramino[0])):
            if tetramino[y][x] == "  ":
                continue
            idx = (xc+x)+WIDTH*(yc+y)
            if idx >= len(SCREEN) or SCREEN[idx] != "  ":
                return False
    return True

def place(container: list[str], tetramino: list[list[str]], xc, yc):
    for y in range(len(tetramino)):
        for x in range(len(tetramino[0])):
            if tetramino[y][x] == "  ":
                continue
            container[(xc+x)+WIDTH*(yc+y)] = "##"

def place_concrete():
    for y in range(1, HEIGHT-1):
        for x in range(1, WIDTH-1):
            idx = x+WIDTH*y
            SCREEN[idx] = CONCRETE[idx]

def is_empty(l: list[str]) -> bool:
    return all(c == "  " for c in l)


def reduce_concrete():
    global SCORE
    idx = WIDTH
    first_concret_idx = None
    while idx < len(CONCRETE)-WIDTH:
        row = CONCRETE[idx:idx+WIDTH]
        if first_concret_idx is None and "##" in row:
           first_concret_idx = idx

        if first_concret_idx is not None and is_empty(row):
            CONCRETE[WIDTH:idx+WIDTH] = CONCRETE[:idx]
            CONCRETE[:WIDTH] = EMPTY_ROW.copy()
            SCORE += 1
        idx += WIDTH


    idx = WIDTH
    while idx < len(CONCRETE) + WIDTH:
        if CONCRETE[idx:idx+WIDTH] == STRIKE:
            CONCRETE[idx:idx+WIDTH] =  EMPTY_ROW.copy()
        idx += WIDTH

def clear_concrete():
    for i in range(len(CONCRETE)):
        CONCRETE[i] = "  "

def clear_screen():
    for i in range(len(SCREEN)):
        SCREEN[i] = "  "

    # border
    for i in range(WIDTH):
        SCREEN[i] = "@@"

    for i in range(WIDTH):
        SCREEN[i+WIDTH*(HEIGHT-1)] = "@@"

    for j in range(HEIGHT):
        SCREEN[WIDTH*j] = "@@"
        SCREEN[(WIDTH-1)+WIDTH*j] = "@@"

def rotate_right(t: list[list[str]]):
    origin = copy.deepcopy(t)
    t.clear()

    for _ in range(len(origin[0])):
        t.append(["  "]*len(origin))
    # [        [
    #  [#, ]    [#, #, #]
    #  [#, ]    [#,  ,  ]
    #  [#,#]   ]
    # ]
    for ch_idx in range(len(origin)):
        for r_idx in range(len(origin[0])):

            new_ch_idx = len(origin)-1-ch_idx
            t[r_idx][new_ch_idx] = origin[ch_idx][r_idx]

def rotate_left(t: list[list[str]]):
    origin = copy.deepcopy(t)
    t.clear()

    for _ in range(len(origin[0])):
        t.append(["  "]*len(origin))
    # [        [
    #  [#, ]    [ ,  , #]
    #  [#, ]    [#, #, #]
    #  [#,#]   ]
    # ]

    for ch_idx in range(len(origin)):
        for r_idx in range(len(origin[0])):
            t[len(origin[0])-1-r_idx][ch_idx] = origin[ch_idx][r_idx]

def can_rotate(tetramino, rotator, x, y):
    clone = copy.deepcopy(tetramino)
    rotator(clone)
    return can_place(clone, x, y)

# copy paste from https://github.com/sakateka/big-jump
def getchr():
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
        return ""

CONTROL = ""
ROTATE = False
RESTART = False
EXIT = False

def control(main=False):
    global ROTATE, CONTROL, RESTART, EXIT

    if main:
        tty.setcbreak(sys.stdin.fileno())
        threading.Thread(target=control, daemon=True).start()
        return

    while True:
        if ch := getchr():
            CONTROL = ch
            if not ROTATE:
                ROTATE = CONTROL == "space"
            if not RESTART:
                RESTART = CONTROL == "enter"
            if not EXIT:
                EXIT = CONTROL == "exit"


def place_gameover():
    print()
    print()
    print()
    print()
    print()
    print("@@                ")
    print("@@  Game over!!!  ")
    print(f"@@  Score {SCORE:>6}  ")
    print("@@                ")


def main() -> None:
    global ROTATE, CONTROL, SCORE, RESTART

    control(True)

    clear_screen()
    place_concrete()

    y = Y_INIT_POS
    x = X_INIT_POS
    t = random.choice(TETRAMINOS)
    round = 0
    game_over = False

    while True:
        reduce_concrete()
        place_concrete()

        if round == 100:
            round = 0
            y += 1

        if ROTATE:
            if can_rotate(t, rotate_right, x, y):
                rotate_right(t)
            ROTATE = False

        if CONTROL:
            match CONTROL:
                case "left":
                    if can_place(t, x-1, y):
                        x -= 1
                case "right":
                    if can_place(t, x+1, y):
                        x += 1
                case "down":
                    if can_place(t, x, y+1):
                        y += 1
                case _:
                    pass
            CONTROL = ""


        if can_place(t, x, y):
            place(SCREEN, t, x, y)
        else:
            place(SCREEN, t, x, y-1)
            place(CONCRETE, t, x, y-1)

            y = Y_INIT_POS
            x = X_INIT_POS
            t = random.choice(TETRAMINOS)
            if not can_place(t, x, y):
                game_over = True
            place(SCREEN, t, x, y)

        print(render())
        sys.stdout.write(CURSOR_UP * (HEIGHT+1))
        sys.stdout.flush()
        if game_over:
            place_gameover()
            while True:
                sleep(0.5)
                if EXIT:
                    print(f"Bye!")
                    return

                if RESTART:
                    RESTART = False
                    game_over = False
                    SCORE = 0
                    clear_concrete()
                    break
        clear_screen()
        sleep(0.01)
        round += 1


if __name__ == "__main__":
    main()
