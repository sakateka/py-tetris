from microbit import *
import neopixel

SCREEN_WIDTH = 8

_0 = [
    ["#", "#", "#"],
    ["#", " ", "#"],
    ["#", " ", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
]
_1 = [
    [" ", " ", "#"],
    [" ", "#", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
]
_2 = [
    ["#", "#", "#"],
    [" ", " ", "#"],
    ["#", "#", "#"],
    ["#", " ", " "],
    ["#", "#", "#"],
]
_3 = [
    ["#", "#", "#"],
    [" ", " ", "#"],
    ["#", "#", "#"],
    [" ", " ", "#"],
    ["#", "#", "#"],
]
_4 = [
    ["#", " ", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
]
_5 = [
    ["#", "#", "#"],
    ["#", " ", " "],
    ["#", "#", "#"],
    [" ", " ", "#"],
    ["#", "#", "#"],
]
_6 = [
    ["#", "#", "#"],
    ["#", " ", " "],
    ["#", "#", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
]
_7 = [
    ["#", "#", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
    [" ", " ", "#"],
]
_8 = [
    ["#", "#", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
]
_9 = [
    ["#", "#", "#"],
    ["#", " ", "#"],
    ["#", "#", "#"],
    [" ", " ", "#"],
    ["#", "#", "#"],
]

DIGITS: "list[list[list[str]]]" = [_0, _1, _2, _3, _4, _5, _6, _7, _8, _9]

O = [
    ["#", "#"],
    ["#", "#"],
]

I = [
    ["#"],
    ["#"],
    ["#"],
    ["#"],
]

L = [
    ["#", " "],
    ["#", " "],
    ["#", "#"],
]

J = [
    [" ", "#"],
    [" ", "#"],
    ["#", "#"],
]

S = [
    [" ", "#", "#"],
    ["#", "#", " "],
]

Z = [
    ["#", "#", " "],
    [" ", "#", "#"],
]

T = [
    ["#", "#", "#"],
    [" ", "#", " "],
]

TETRAMINOS = [O, I, L, J, S, Z, T]

HLINE = [["#"] * SCREEN_WIDTH]


pin8.set_pull(pin8.PULL_UP)

np = neopixel.NeoPixel(pin0, 256)
RED = (1, 0, 0)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
BROWN = (2, 1, 0)
BLACK = (0, 0, 0)


def Dot(x: int, y: int, color: "tuple[int, int, int]"):
    if y % 2 == 0:
        x = 7 - x
    np[SCREEN_WIDTH * y + x] = color

def rotate(t: "list[list[str]]"):
    origin: "list[list[str]]" = []
    for idx in range(len(t)):
        origin.append([])
        for ch in t[idx]:
            origin[idx].append(ch)

    t.clear()

    for _ in range(len(origin[0])):
        t.append(["  "] * len(origin))

    for ch_idx in range(len(origin)):
        for r_idx in range(len(origin[0])):

            new_ch_idx = len(origin) - 1 - ch_idx
            t[r_idx][new_ch_idx] = origin[ch_idx][r_idx]

def НарисуйМатрицу(M: "list[list[str]]", x: int, y: int, color: "tuple[int, int, int]" = GREEN):
    for r_idx in range(len(M)):
        m_row = M[r_idx]
        for dot_idx in range(len(m_row)):
            if m_row[dot_idx] == "#":
                Dot(x + dot_idx, y + r_idx, color)
            else:
                Dot(x + dot_idx, y + r_idx, BLACK)


num = 0
num2 = 0
jump = 0


@run_every(ms=100)
def check_jump():
    global jump
    jump = jump or pin8.read_digital()


while True:
    if jump:
        num = (num + 1) % len(DIGITS)
        num2 = (num + 1) % len(DIGITS)
        rotate(T)
        jump = 0


    НарисуйМатрицу(DIGITS[num], x=0, y=0)
    НарисуйМатрицу(DIGITS[num2], x=4, y=0)
    НарисуйМатрицу(HLINE, x=0, y=10, color=BROWN)
    НарисуйМатрицу(T, x=0, y=6, color=BLUE)

    np.show()
    sleep(250)
