import random

class Figure:
    def __init__(self, data: bytearray, width: int):
        self.data = memoryview(data)
        self.width = width

    @property
    def height(self) -> int:
        return len(self.data) // self.width

    def get(self, x, y) -> int:
        return self.data[y * self.width + x]

    def rotate(self) -> "Figure":
        rotated: Figure = Figure(bytearray(self.data), self.height)

        for row_idx in range(self.height):
            for ch_idx in range(self.width):
                new_ch_idx = self.height - 1 - row_idx
                new_row_idx = ch_idx
                new_ch = self.data[row_idx * self.width + ch_idx]
                rotated.data[new_row_idx * rotated.width + new_ch_idx] = new_ch
        return rotated


DIGITS = [
    Figure(bytearray(
        b"\3\3\3"
        b"\3\0\3"
        b"\3\0\3"
        b"\3\0\3"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\0\0\3"
        b"\0\3\3"
        b"\0\0\3"
        b"\0\0\3"
        b"\0\0\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\0\0\3"
        b"\3\3\3"
        b"\3\0\0"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\0\0\3"
        b"\3\3\3"
        b"\0\0\3"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\3\0\3"
        b"\3\0\3"
        b"\3\3\3"
        b"\0\0\3"
        b"\0\0\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\3\0\0"
        b"\3\3\3"
        b"\0\0\3"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\3\0\0"
        b"\3\3\3"
        b"\3\0\3"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\0\0\3"
        b"\0\0\3"
        b"\0\0\3"
        b"\0\0\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\3\0\3"
        b"\3\3\3"
        b"\3\0\3"
        b"\3\3\3"
    ), width=3),
    Figure(bytearray(
        b"\3\3\3"
        b"\3\0\3"
        b"\3\3\3"
        b"\0\0\3"
        b"\3\3\3"
    ), width=3),
]

TETRAMINO = [
        Figure(bytearray(
            b"\1\1"
            b"\1\1"
        ), width=2),
        Figure(bytearray(
            b"\2"
            b"\2"
            b"\2"
            b"\2"
        ), width=1),
        Figure(bytearray(
            b"\3\0"
            b"\3\3"
            b"\3\0"
        ), width=2),
        Figure(bytearray(
            b"\4\4"
            b"\0\4"
            b"\0\4"
        ), width=2),
        Figure(bytearray(
            b"\5\5"
            b"\5\0"
            b"\5\0"
        ), width=2),
        Figure(bytearray(
            b"\6\0"
            b"\6\6"
            b"\0\6"
        ), width=2),
        Figure(bytearray(
            b"\0\7"
            b"\7\7"
            b"\7\0"
        ), width=2),
]

def random_tetramino() -> Figure:
    return random.choice(TETRAMINO)
