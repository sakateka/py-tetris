import micropython
from machine import Pin, ADC
import time
import random
import neopixel


SCREEN_WIDTH = 8
SCREEN_HEIGHT = 32

micropython.alloc_emergency_exception_buf(100)


class Figure:
    def __init__(self, data: memoryview, width: int):
        self.data = data
        self.width = width

    @property
    def height(self) -> int:
        return len(self.data) // self.width

    @staticmethod
    def from_str(figure: str) -> "Figure":
        lines = figure.split("\n")
        width = len(lines[0])
        data = bytearray("".join(lines).encode())
        return Figure(
            memoryview(
                data,
            ),
            width,
        )

    def rotate(self) -> "Figure":
        rotated: Figure = Figure(memoryview(bytearray(self.data)), self.height)

        for row_idx in range(self.height):
            for ch_idx in range(self.width):
                new_ch_idx = self.height - 1 - row_idx
                new_row_idx = ch_idx
                new_ch = self.data[row_idx * self.width + ch_idx]
                rotated.data[new_row_idx * rotated.width + new_ch_idx] = new_ch
        return rotated

    def __str__(self) -> str:
        lines = []
        for row in range(self.height):
            lines.append(bytes(self.data[self.width * row : self.width * (row + 1)]).decode())
        return "\n".join(lines)


class Figures:
    def __init__(self):
        self.digits_text = """
###|  #|###|###|# #|###|###|###|###|###
# #| ##|  #|  #|# #|#  |#  |  #|# #|# #
# #|  #|###|###|###|###|###|  #|###|###
# #|  #|#  |  #|  #|  #|# #|  #|# #|  #
###|  #|###|###|  #|###|###|  #|###|###
"""
        self.digits: "list[Figure]" = self.parse_figures(self.digits_text.strip().split("\n"))

        self.tetramion_text = """
##| # |  #|#  | ##|## |
##|###|###|###|## | ##|####
"""
        self.tetramino: "list[Figure]" = self.parse_figures(self.tetramion_text.strip().split("\n"))

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
            figures.append(Figure.from_str("\n".join(figure)))
        return figures

    def random_tetramino(self) -> Figure:
        return random.choice(self.tetramino)


HLINE = Figure.from_str("#" * SCREEN_WIDTH)
FIGURES = Figures()

np = neopixel.NeoPixel(Pin(13), 256)

BLACK = (0, 0, 0)
BRICK = (12, 2, 0)
RED = (6, 0, 0)
GREEN = (0, 6, 0)
BLUE = (0, 0, 6)
PINK = (3, 0, 3)
YELLOW = (6, 6, 0)

COLORS = (BLACK, BRICK, RED, GREEN, BLUE, PINK, YELLOW)
GREEN_IDX = COLORS.index(GREEN)


def init_matrix() -> memoryview:
    return memoryview(bytearray(SCREEN_WIDTH * SCREEN_HEIGHT))


def copy_matrix(_from: memoryview, to: memoryview):
    for idx in range(len(_from)):
        to[idx] = _from[idx]


def render_screen(screen: memoryview):
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT):
            Dot(x, y, color=screen[y * SCREEN_WIDTH + x])
    np.write()


def Dot(x: int, y: int, color: int):
    if y % 2 == 0:
        x = 7 - x
    np[SCREEN_WIDTH * y + x] = COLORS[color]


def concrete_checker(x: int, y: int, color) -> bool:
    if x < SCREEN_WIDTH and y < SCREEN_HEIGHT:
        return CONCRETE[y * SCREEN_WIDTH + x] == color
    return False


def screen_dot(x: int, y: int, color: int) -> bool:
    SCREEN[y * SCREEN_WIDTH + x] = color
    return True


def concrete_dot(x: int, y: int, color: int) -> bool:
    CONCRETE[y * SCREEN_WIDTH + x] = color
    return True


def нарисуй_фигуру(
    F: Figure,
    x: int,
    y: int,
    color: int = GREEN_IDX,
    painter=screen_dot,
):
    row = 0
    col = 0
    for ch in F.data:
        if ch == ord('#'):
            if not painter(x + col, y + row, color):
                return False
        col += 1
        if col == F.width:
            row += 1
            col = 0
    return True


def можно_рисовать(F: Figure, x: int, y: int, checker=concrete_checker) -> bool:
    return нарисуй_фигуру(F, x, y, 0, checker)


def draw_score(score: int):
    score %= 100
    speed = score // 10
    score %= 10
    нарисуй_фигуру(FIGURES.digits[speed], x=0, y=0)
    нарисуй_фигуру(FIGURES.digits[score], x=4, y=0)


def map_direction(analog_val: int, min: int, max: int, base: int = 0):
    v = base
    if analog_val < 16000:
        v = min
    elif analog_val > 48000:
        v = max
    return v


def is_full(m: memoryview):
    return all(b != 0 for b in m)


def is_empty(m: memoryview):
    return all(b == 0 for b in m)


def clear(m: memoryview):
    for idx in range(len(m)):
        m[idx] = 0


def reduce_concrete() -> int:
    score = 0
    for idx in range(SCREEN_HEIGHT, 5, -1):
        row_start = (idx - 1) * SCREEN_WIDTH
        if is_full(CONCRETE[row_start : row_start + SCREEN_WIDTH]):
            score += 1
            clear(CONCRETE[row_start : row_start + SCREEN_WIDTH])
    return score


def shift_concrete():
    to_idx = SCREEN_HEIGHT - 1
    from_idx = SCREEN_HEIGHT - 1
    for _ in range(SCREEN_HEIGHT):
        row_from_start = from_idx * SCREEN_WIDTH
        row_from_end = row_from_start + SCREEN_WIDTH
        if is_empty(CONCRETE[row_from_start : row_from_start + SCREEN_WIDTH]):
            from_idx -= 1
            continue
        if from_idx != to_idx:
            row_to_start = to_idx * SCREEN_WIDTH
            row_to_end = row_to_start + SCREEN_WIDTH
            copy_matrix(CONCRETE[row_from_start:row_from_end], CONCRETE[row_to_start:row_to_end])
        from_idx -= 1
        to_idx -= 1

    # +1 to compensate last for loop iteration
    clear(CONCRETE[0 : (to_idx + 1) * SCREEN_WIDTH])


def game_over(figure):
    while True:
        for idx in range(1, len(COLORS)):
            нарисуй_фигуру(figure, x=INIT_X, y=INIT_Y, color=idx)
            render_screen(SCREEN)
            time.sleep_ms(500)
            нарисуй_фигуру(figure, x=INIT_X, y=INIT_Y, color=COLORS.index(BLACK))
            render_screen(SCREEN)
            time.sleep_ms(500)


INIT_X = 3
INIT_Y = 6
NEXT_VISIBLE_Y = INIT_Y + 5

SCREEN = init_matrix()
CONCRETE = init_matrix()

DEBOUNCE = 200
BUTTON_PRESS_COUNT = 0
DEBOUNCE_TIME = 0
BUTTON = Pin(16, Pin.IN, Pin.PULL_UP)
def button_callback(_):
    global BUTTON_PRESS_COUNT, DEBOUNCE_TIME
    if (time.ticks_ms() - DEBOUNCE_TIME) > DEBOUNCE:
        BUTTON_PRESS_COUNT = 1
        DEBOUNCE_TIME = time.ticks_ms()
BUTTON.irq(trigger=Pin.IRQ_RISING, handler=button_callback)

X_AXIS = ADC(27)
Y_AXIS = ADC(28)

def main():
    global BUTTON_PRESS_COUNT

    SCORE = 0

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
        X_DIFF = X_DIFF or map_direction(X_AXIS.read_u16(), 1, -1)
        SPEED_BONUS = map_direction(Y_AXIS.read_u16(), 0, 10, base=0)

        if IPASS >= 10:
            IPASS = 0
            Y += 1

        draw_score(SCORE)
        нарисуй_фигуру(HLINE, x=0, y=5, color=pink_idx)

        new_x = X + X_DIFF
        if new_x >= 0 and new_x < SCREEN_WIDTH and можно_рисовать(curr_figure, x=X + X_DIFF, y=Y):
            X += X_DIFF
        X_DIFF = 0

        if BUTTON_PRESS_COUNT:
            BUTTON_PRESS_COUNT = 0
            rotated = curr_figure.rotate()
            shift = rotated.height - rotated.width if X + rotated.width >= SCREEN_WIDTH else 0

            if можно_рисовать(rotated, x=X + shift, y=Y):
                curr_figure = rotated
                X += shift

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
            print(next_figure)
            print("-" * 4)
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
        time.sleep_ms(50)


main()
