import copy
import sys
import random
from time import sleep
from io import StringIO

ESCAPE = "\x1b"
CURSOR_UP = ESCAPE + "[1A"
CLEAR_LINE = ESCAPE + "[2K\r"
CURSOR_UP_AND_CLEAR_LINE = CURSOR_UP + CLEAR_LINE

width = 10
height = 20
screen: list = ["  "] * width * height 
concrete: list = ["  "] * width * height 


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

def render() -> str:
    result = StringIO()

    for y in range(height):
        for x in range(width):
            result.write(screen[x+width*y])
        result.write("\n")
    result.seek(0)
    return result.getvalue()

def can_place(tetramino: list[list[str]], xc, yc) -> bool:
    for y in range(len(tetramino)):
        for x in range(len(tetramino[0])):
            if tetramino[y][x] == "  ":
                continue
            idx = (xc+x)+width*(yc+y)
            if idx >= len(concrete) or concrete[idx] != "  ":
                return False
    return True

def place(container: list[str], tetramino: list[list[str]], xc, yc):
    for y in range(len(tetramino)):
        for x in range(len(tetramino[0])):
            if tetramino[y][x] == "  ":
                continue
            container[(xc+x)+width*(yc+y)] = "##"

def place_concrete():
    for i in range(len(screen)):
        if concrete[i] != "  ":
            screen[i] = concrete[i]

def clear():
    for i in range(len(screen)):
        screen[i] = "  "

def place_border():
    for i in range(width):
        concrete[i] = "@@"

    for i in range(width):
        concrete[i+width*(height-1)] = "@@"

    for j in range(height):
        concrete[width*j] = "@@"
        concrete[(width-1)+width*j] = "@@"

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



TETRAMINOS = [O, I, L, J, S, Z, T]

def main() -> None:
    y = 1
    t: list[list[str]] = random.choice(TETRAMINOS)
    place_border()
    place_concrete()
    while True:
        place_border()

        if can_rotate(t, rotate_left, 3, y):
            rotate_left(t)
        if can_place(t, 3, y):
            place(screen, t, 3, y)
        else:
            place(concrete, t, 3, y-1)
            y = 1
            t = random.choice(TETRAMINOS)
            place(screen, t, 3, y)
        place_concrete()
        print(render())
        y += 1
        sys.stdout.write(CURSOR_UP * (height+1))
        sys.stdout.flush()
        clear()
        sleep(0.5)


if __name__ == "__main__":
    main()
