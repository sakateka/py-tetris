from microbit import *
import random
import neopixel

SCREEN_WIDTH = 8
SCREEN_HEIGHT = 32

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
PINK = (2, 0, 2)
BRICK = (12, 2, 0)
BLACK = (0, 0, 0)


def init_matrix() -> "list[list[tuple[int, int, int]]]":
    screen = [[]] * SCREEN_HEIGHT
    for idx in range(len(screen)):
        screen[idx] = [BLACK] * SCREEN_WIDTH
    return screen


def clear_screen(screen: "list[list[tuple[int,int,int]]]"):
    for row in screen:
        for i in range(len(row)):
            row[i] = BLACK


def render_screen(screen: "list[list[tuple[int, int, int]]]"):
    for y in range(len(screen)):
        for x in range(len(screen[y])):
            Dot(x, y, color=screen[y][x])


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


def is_full_row(row: "list[tuple[int, int, int]]"):
    for ch in row:
        if ch[0] == 0 and ch[1] == 0 and ch[2] == 0:
            return False
    return True


def reduce_concrete():
    global SCORE
    to_idx = 0
    for idx in range(len(CONCRETE) - 1, -1, -1):
        if is_full_row(CONCRETE[idx]):
            to_idx += 1
            SCORE += 1
        if idx > to_idx:
            CONCRETE[to_idx] = CONCRETE[idx]
    for row_idx in range(to_idx):
        for c_idx in range(len(CONCRETE[row_idx])):
            CONCRETE[row_idx][c_idx] = BLACK


def copy_matrix(_from: "list[list[tuple]]", to: "list[list[tuple]]"):
    for row_idx in range(len(_from)):
        for t_idx in range(len(_from[row_idx])):
            to[row_idx][t_idx] = _from[row_idx][t_idx]


def screen_dot(x: int, y: int, color: "tuple[int, int, int]"):
    SCREEN[y][x] = color


def concrete_dot(x: int, y: int, color: "tuple[int, int, int]"):
    CONCRETE[y][x] = color


def нарисуй_фигуру(
    M: "list[list[str]]",
    x: int,
    y: int,
    color: "tuple[int, int, int]" = GREEN,
    painter=screen_dot,
):
    for r_idx in range(len(M)):
        m_row = M[r_idx]
        for dot_idx in range(len(m_row)):
            if m_row[dot_idx] == "#":
                painter(x + dot_idx, y + r_idx, color)


def is_free_place(matrix: "list[list[tuple[int, int, int]]]", x: int, y: int) -> bool:
    if y < len(matrix) and x < len(matrix[y]):
        return matrix[y][x] == BLACK
    return False


def screen_checker(x: int, y: int):
    return is_free_place(SCREEN, x, y)


def concrete_checker(x: int, y: int):
    return is_free_place(CONCRETE, x, y)


def можно_рисовать(
    M: "list[list[str]]", x: int, y: int, can_draw=screen_checker
) -> bool:
    for r_idx in range(len(M)):
        m_row = M[r_idx]
        for dot_idx in range(len(m_row)):
            if m_row[dot_idx] == "#" and not can_draw(x + dot_idx, y + r_idx):
                return False
    return True


def draw_score(score: int):
    score = score % 100
    first, second = score // 10, score % 10
    нарисуй_фигуру(DIGITS[first], x=0, y=0)
    нарисуй_фигуру(DIGITS[second], x=4, y=0)


JUMP = 0


@run_every(ms=10)
def check_jump():
    global JUMP
    JUMP = JUMP or pin8.read_digital()


SCORE = 99
SCREEN = init_matrix()
CONCRETE = init_matrix()

X = 3
Y = 6
IPASS = 0
CURRENT_T = T


@run_every(ms=10)
def main():
    global JUMP, SCORE, X, Y, IPASS, CURRENT_T

    if JUMP:
        rotate(CURRENT_T)
        JUMP = 0
        SCORE += 1

    if SCORE > 99:
        # TODO: speed reset
        SCORE = 0

    if IPASS == 10:
        IPASS = 0
        Y += 1

    нарисуй_фигуру(I, x=3, y=28, color=BRICK, painter=concrete_dot)

    reduce_concrete()
    copy_matrix(CONCRETE, SCREEN)
    draw_score(SCORE)

    нарисуй_фигуру(HLINE, x=0, y=5, color=PINK)

    # Next tetromino
    if можно_рисовать(CURRENT_T, x=X, y=Y):
        нарисуй_фигуру(CURRENT_T, x=X, y=Y, color=BLUE)
    else:
        нарисуй_фигуру(CURRENT_T, x=X, y=Y - 1, color=BRICK, painter=concrete_dot)
        Y = 6
        CURRENT_T = random.choice(TETRAMINOS)

    render_screen(SCREEN)

    np.show()
    IPASS += 1


def real_main():
    while True:
        sleep(1000)


real_main()
