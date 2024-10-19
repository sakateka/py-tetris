from microbit import *
import random
import neopixel

SCREEN_WIDTH = 8
SCREEN_HEIGHT = 32
HLINE = "#" * SCREEN_WIDTH


class Figures:
    def __init__(self):
        self.digits_text = """
###|  #|###|###|# #|###|###|###|###|###
# #| ##|  #|  #|# #|#  |#  |  #|# #|# #
# #|  #|###|###|###|###|###|  #|###|###
# #|  #|#  |  #|  #|  #|# #|  #|# #|  #
###|  #|###|###|  #|###|###|  #|###|###
"""
        self.digits: "list[str]" = self.parse_figures(self.digits_text.strip().split("\n"))

        self.tetramion_text = """
##| # |  #|#  | ##|## |
##|###|###|###|## | ##|####
"""
        self.tetramino: "list[str]" = self.parse_figures(self.tetramion_text.strip().split("\n"))

    def parse_figures(self, lines: "list[str]"):
        parts = []
        for line in lines:
            parts.append(line.strip().split("|"))

        figures = []
        for n in range(len(parts[0])):
            figure = []
            for pn in range(len(parts)):
                part = parts[pn][n]
                if part:
                    figure.append(part)
            figures.append("\n".join(figure))
        return figures

    def random_tetramino(self) -> str:
        return random.choice(self.tetramino)


FIGURES = Figures()

pin8.set_pull(pin8.PULL_UP)

np = neopixel.NeoPixel(pin0, 256)

BLACK = (0, 0, 0)
BRICK = (12, 2, 0)
RED = (6, 0, 0)
GREEN = (0, 6, 0)
BLUE = (0, 0, 6)
PINK = (3, 0, 3)
YELLOW = (6, 6, 0)

COLORS = (BLACK, BRICK, RED, GREEN, BLUE, PINK, YELLOW)
GREEN_IDX = COLORS.index(GREEN)

EMPTY_LINE = bytearray(SCREEN_WIDTH)


def init_matrix() -> "list[bytearray]":
    return [EMPTY_LINE[:] for _ in range(SCREEN_HEIGHT)]


def copy_matrix(_from: "list[bytearray]", to: "list[bytearray]"):
    for row_idx in range(len(_from)):
        to[row_idx] = _from[row_idx][:]


def render_screen(screen: "list[bytearray]"):
    for y in range(len(screen)):
        for x in range(len(screen[y])):
            Dot(x, y, color=screen[y][x])
    np.show()


def Dot(x: int, y: int, color: int):
    if y % 2 == 0:
        x = 7 - x
    np[SCREEN_WIDTH * y + x] = COLORS[color]


def has_color(matrix: "list[bytearray]", x: int, y: int, color: int) -> bool:
    if y < len(matrix) and x < len(matrix[y]):
        return matrix[y][x] == color
    return False


def concrete_checker(x: int, y: int, color) -> bool:
    return has_color(CONCRETE, x, y, color)


def screen_dot(x: int, y: int, color: int) -> bool:
    SCREEN[y][x] = color
    return True


def concrete_dot(x: int, y: int, color: int) -> bool:
    CONCRETE[y][x] = color
    return True


def нарисуй_фигуру(
    F: str,
    x: int,
    y: int,
    color: int = GREEN_IDX,
    painter=screen_dot,
):
    row = 0
    col = 0
    for ch in F:
        if ch == "#":
            if not painter(x + col, y + row, color):
                return False
        col += 1
        if ch == "\n":
            row += 1
            col = 0
    return True


def можно_рисовать(F: str, x: int, y: int, checker=concrete_checker) -> bool:
    return нарисуй_фигуру(F, x, y, 0, checker)


def draw_score(score: int):
    score %= 100
    speed = score // 10
    score %= 10
    нарисуй_фигуру(FIGURES.digits[speed], x=0, y=0)
    нарисуй_фигуру(FIGURES.digits[score], x=4, y=0)


def map_direction(analog_val: int, min: int, max: int, base: int = 0):
    v = base
    if analog_val < 350:
        v = min
    elif analog_val > 640:
        v = max
    return v


def rotate(origin: str) -> "tuple[str, int, int]":
    rotated: "list[list[str]]" = []
    lines = origin.split("\n")

    origin_height = len(lines)
    origin_width = len(lines[0])

    for _ in range(origin_width):
        rotated.append([" "] * origin_height)

    for row_idx in range(origin_height):
        for ch_idx in range(origin_width):
            new_ch_idx = origin_height - 1 - row_idx
            new_row_idx = ch_idx
            new_ch = lines[row_idx][ch_idx]
            rotated[new_row_idx][new_ch_idx] = new_ch

    return "\n".join("".join(line) for line in rotated), origin_height, origin_width


def is_full_row(row: bytearray):
    return all(ch != 0 for ch in row)


def is_empty_row(row: bytearray):
    return all(ch == 0 for ch in row)


def reduce_concrete() -> int:
    score = 0
    max_idx = len(CONCRETE) - 1
    for idx in range(max_idx, 5, -1):
        if is_full_row(CONCRETE[idx]):
            score += 1
            CONCRETE[idx] = EMPTY_LINE[:]
    return score


def shift_concrete():
    to_idx = SCREEN_HEIGHT - 1
    from_idx = SCREEN_HEIGHT - 1
    for _ in range(SCREEN_HEIGHT):
        if is_empty_row(CONCRETE[from_idx]):
            from_idx -= 1
            continue
        if from_idx != to_idx:
            CONCRETE[to_idx] = CONCRETE[from_idx][:]
        from_idx -= 1
        to_idx -= 1

    for idx in range(to_idx, -1, -1):
        CONCRETE[idx] = EMPTY_LINE[:]


def game_over(figure):
    while True:
        for idx in range(1, len(COLORS)):
            нарисуй_фигуру(figure, x=INIT_X, y=INIT_Y, color=idx)
            render_screen(SCREEN)
            sleep(500)
            нарисуй_фигуру(figure, x=INIT_X, y=INIT_Y, color=COLORS.index(BLACK))
            render_screen(SCREEN)
            sleep(500)


INIT_X = 3
INIT_Y = 6
NEXT_VISIBLE_Y = INIT_Y + 5

SCREEN = init_matrix()
CONCRETE = init_matrix()


def main():
    SCORE = 0
    ROTATE = 0

    X = INIT_X
    Y = INIT_Y
    X_DIFF = 0
    IPASS = 0

    curr_figure = FIGURES.random_tetramino()
    next_figure = FIGURES.random_tetramino()
    next_color = random.randrange(1, len(COLORS))
    curr_color = random.randrange(1, len(COLORS))

    reduced = 0

    pink_idx = COLORS.index(PINK)

    while True:
        ROTATE = ROTATE or pin8.read_digital()
        X_DIFF = X_DIFF or map_direction(pin1.read_analog(), 1, -1)
        SPEED_BONUS = map_direction(pin2.read_analog(), 0, 10, base=0)

        if IPASS >= 10:
            IPASS = 0
            Y += 1

        draw_score(SCORE)
        нарисуй_фигуру(HLINE, x=0, y=5, color=pink_idx)

        new_x = X + X_DIFF
        if new_x >= 0 and new_x < SCREEN_WIDTH and можно_рисовать(curr_figure, x=X + X_DIFF, y=Y):
            X += X_DIFF
        X_DIFF = 0

        if ROTATE:
            rotated, new_w, new_h = rotate(curr_figure)
            shift = new_h - new_w if X + new_w >= SCREEN_WIDTH else 0

            if можно_рисовать(curr_figure, x=X + shift, y=Y):
                curr_figure = rotated
                X += shift
            ROTATE = 0

        if Y > NEXT_VISIBLE_Y:
            нарисуй_фигуру(next_figure, x=INIT_X, y=INIT_Y, color=next_color)

        if можно_рисовать(curr_figure, x=X, y=Y):
            нарисуй_фигуру(curr_figure, x=X, y=Y, color=curr_color)
        else:
            нарисуй_фигуру(curr_figure, x=X, y=Y - 1, color=curr_color)
            нарисуй_фигуру(curr_figure, x=X, y=Y - 1, color=curr_color, painter=concrete_dot)
            X = INIT_X
            Y = INIT_Y + 1
            if not можно_рисовать(curr_figure, x=X, y=Y):
                game_over(curr_figure)

            curr_figure = next_figure
            next_figure = FIGURES.random_tetramino()
            print(next_figure, "\n")
            curr_color = next_color
            next_color = random.randrange(1, len(COLORS))

            reduced = reduce_concrete()
            SCORE += reduced

        render_screen(SCREEN)
        copy_matrix(CONCRETE, SCREEN)
        if reduced:
            shift_concrete()
            reduced = 0

        if SCORE > 99:
            SCORE = 0
        IPASS += max(1, SCORE // 10) + SPEED_BONUS
        sleep(10)


main()
