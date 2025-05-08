import sys

class NeoPixel():
    def __init__(self, pin, size):
        self.pin = pin
        self.width = 8
        self.hieght = 32
        self.content = [()]*size

    def __setitem__(self, idx, val: int):
        self.content[idx] = val


    def write(self):
        sys.stdout.write(f'\x1b[{self.hieght*2}F\x1b[2K')

        for y in range(0, self.hieght):
            for _ in range(0, 2):
                for x in range(0, self.width):
                    if y % 2 == 0:
                        x = 7 - x
                    color = self.content[y*self.width + x]
                    red, green, blue = color
                    sys.stdout.write(f'\x1b[38;2;{red*20};{green*20};{blue*20}m#\x1b[0m')
                    sys.stdout.write(f'\x1b[38;2;{red*20};{green*20};{blue*20}m#\x1b[0m')
                    sys.stdout.write(f'\x1b[38;2;{red*20};{green*20};{blue*20}m#\x1b[0m')
                    sys.stdout.write(f'\x1b[38;2;{red*20};{green*20};{blue*20}m#\x1b[0m')
                sys.stdout.write('\n')
        sys.stdout.flush()
