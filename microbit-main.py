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
RED = (6, 0, 0)
GREEN = (0, 6, 0)
BLUE = (0, 0, 6)
PINK = (3, 0, 3)
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


def is_full_row(row: "list[tuple[int, int, int]]"):
    for ch in row:
        if ch[0] == 0 and ch[1] == 0 and ch[2] == 0:
            return False
    return True


def reduce_concrete():
    global SCORE
    to_idx = len(CONCRETE) - 1
    for idx in range(len(CONCRETE) - 1, -1, -1):
        if is_full_row(CONCRETE[idx]):
            SCORE += 1
        else:
            to_idx -= 1
        if idx > to_idx:
            print(idx, to_idx)
            for c_idx in range(len(CONCRETE[idx])):
                CONCRETE[to_idx][c_idx] = CONCRETE[idx][c_idx]

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


def можно_рисовать(M: "list[list[str]]", x: int, y: int, can_draw=screen_checker) -> bool:
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


def map_direction(analog_val: int, min: int, max: int, base: int = 0):
    v = base
    if analog_val < 350:
        v = min
    elif analog_val > 640:
        v = max
    return v


def rotate(origin: "list[list[str]]", x: int) -> "tuple[list[list[str]], int]":
    rotated: "list[list[str]]" = []
    shift = 0
    for _ in origin[0]:
        rotated.append([" "] * len(origin))

    if x + len(rotated[0]) >= SCREEN_WIDTH:
        shift = len(rotated) - len(origin)

    for ch_idx in range(len(origin)):
        for r_idx in range(len(origin[0])):
            new_ch_idx = len(origin) - 1 - ch_idx
            rotated[r_idx][new_ch_idx] = origin[ch_idx][r_idx]

    return rotated, shift


SCORE = 0
SCREEN = init_matrix()
CONCRETE = init_matrix()


def main():
    global SCORE

    JUMP = 0

    X = 3
    X_DIFF = 0
    Y = 6

    IPASS = 0
    IPASS_DIFF = 1
    CURRENT_T = T
    CONCRETE_UPDATED = False

    while True:
        JUMP = JUMP or pin8.read_digital()
        X_DIFF = X_DIFF or map_direction(pin1.read_analog(), 1, -1)
        IPASS_DIFF = map_direction(pin2.read_analog(), 1, 10, base=1)

        if SCORE > 99:
            # TODO: speed reset
            SCORE = 0

        if IPASS >= 10:
            IPASS = 0
            Y += 1

        if CONCRETE_UPDATED:
            reduce_concrete()
            CONCRETE_UPDATED = False
        copy_matrix(CONCRETE, SCREEN)
        draw_score(SCORE)

        нарисуй_фигуру(HLINE, x=0, y=5, color=PINK)

        new_x = X + X_DIFF
        if new_x >= 0 and new_x < SCREEN_WIDTH and можно_рисовать(CURRENT_T, x=X + X_DIFF, y=Y):
            X += X_DIFF
        X_DIFF = 0

        if JUMP:
            new_current_t, shift = rotate(CURRENT_T, X)
            if можно_рисовать(new_current_t, x=X + shift, y=Y):
                CURRENT_T = new_current_t
                X += shift
            JUMP = 0

        # Next tetromino
        if можно_рисовать(CURRENT_T, x=X, y=Y):
            нарисуй_фигуру(CURRENT_T, x=X, y=Y, color=BLUE)
        else:
            нарисуй_фигуру(CURRENT_T, x=X, y=Y - 1, color=BRICK, painter=concrete_dot)
            Y = 6
            CURRENT_T = random.choice(TETRAMINOS)
            CONCRETE_UPDATED = True

        render_screen(SCREEN)

        np.show()
        IPASS += IPASS_DIFF


main()
