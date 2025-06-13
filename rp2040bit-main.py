import micropython
from machine import Pin, ADC
import time
import math
import random
import neopixel
import figures
from figures import Figure

if not getattr(time, "ticks_ms", None):
    setattr(time, "ticks_ms", lambda: time.time() * 1000)
if not getattr(time, "sleep_ms", None):
    setattr(time, "sleep_ms", lambda v: time.sleep(v/1000))

#  Coordinates
#        x
#     0 --->  7
#    0+-------+
#     |       |
#     |   S   |
#   | |   C   |
# y | |   R   |---+
#   | |   E   | +----+
#   v |   E   | |::::| <- microbit
#     |   N   | +----+
#     |       | @ |<---- joystick
#   31+-------+---+


SCREEN_WIDTH = 8
SCREEN_HEIGHT = 32
SCREEN_SIZE = SCREEN_WIDTH * SCREEN_HEIGHT

PIXEL_WIDTH = 3
PIXEL_MASK = 0b_111

np = neopixel.NeoPixel(Pin(13), 256)

BLACK = (0, 0, 0)
BRICK = (12, 2, 0)
RED = (6, 0, 0)
GREEN = (0, 6, 0)
BLUE = (0, 0, 6)
PINK = (3, 0, 3)
YELLOW = (6, 6, 0)
LIGHT_BLUE = (0, 6, 6)
LIGHT_GREEN = (0, 9, 0)
DARK_GREEN = (0, 3, 0)

COLORS = (
#     0      1     2     3     4        5        6      7
    BLACK, BRICK, RED, GREEN, BLUE, LIGHT_BLUE, PINK, YELLOW,
#       8           9
    DARK_GREEN, LIGHT_GREEN, 
)
BLACK_IDX = 0
BRICK_IDX = 1
RED_IDX = 2
GREEN_IDX = 3
BLUE_IDX = 4
LIGHT_BLUE_IDX = 5
PINK_IDX = 6
YELLOW_IDX = 7
DARK_GREEN_IDX = 8
LIGHT_GREEN_IDX = 9



micropython.alloc_emergency_exception_buf(100)

HLINE = Figure(bytearray(b"\6" * SCREEN_WIDTH), SCREEN_WIDTH)

class FrameBuffer():
    def __init__(self, content = None):
        self.content = content
        if not self.content:
            self.content = memoryview(bytearray(SCREEN_SIZE))
        if len(self.content) != SCREEN_SIZE:
            raise ValueError("invalid content size {} expected {}".format(len(self.content), SCREEN_SIZE))

    @staticmethod
    def from_rows(rows: list[int]) -> "FrameBuffer":
        buf = FrameBuffer()
        for y in range(SCREEN_HEIGHT):
            for x in range(len(rows)):
                color = (rows[x] >> (SCREEN_HEIGHT - y - 1) * PIXEL_WIDTH) & PIXEL_MASK
                buf.set(SCREEN_WIDTH - x - 1, y, color)

        return buf

    def render(self):
        for x in range(SCREEN_WIDTH):
            for y in range(SCREEN_HEIGHT):
                color = self.get(x, y)
                set_pixel(x, y, color)
        np.write()

    def clear(self, _from=0, to=SCREEN_SIZE):
        for idx in range(_from, to):
            self.content[idx] = 0

    def set(self, x, y, color):
        idx = y * SCREEN_WIDTH + x
        self.content[idx] = color

    def get(self, x, y) -> int:
        return self.content[y * SCREEN_WIDTH + x]

    def shift_right(self, count=1):
        self.content[count*SCREEN_WIDTH:] = self.content[:SCREEN_SIZE-count*SCREEN_WIDTH]
        self.clear(to=count)

    def copy_from(self: memoryview, _from: memoryview):
        self.content[:] = _from.content[:]

    def view(self, _from: int, to: int) -> memoryview:
        return self.content[_from:to]

    def available(self, x, y, color = BLACK_IDX):
        if -1 < x < SCREEN_WIDTH and -1 < y < SCREEN_HEIGHT:
            return self.content[y * SCREEN_WIDTH + x] == color
        return False

    def row(self, row) -> memoryview:
        return self.content[row*SCREEN_WIDTH:(row+1)*SCREEN_WIDTH]

    def collides(self, x: int, y: int, figure: Figure):
        for row in range(figure.height):
            for col in range(figure.width):
                ch = figure.get(col, row)
                if ch and not self.available(x + col, y + row):
                    return True
        return False

    def draw(self, x: int, y: int, figure: Figure, color=None):
        for row in range(figure.height):
            for col in range(figure.width):
                ch = figure.get(col, row)
                if ch:
                    self.set(x + col, y + row, ch if color is None else color)


def is_full(m: memoryview):
    return all(b != 0 for b in m)


def is_empty(m: memoryview):
    return all(b == 0 for b in m)


def set_pixel(x: int, y: int, color: int):
    if y % 2 == 0:
        x = 7 - x
    np[SCREEN_WIDTH * y + x] = COLORS[color]



class Joystick():
    def __init__(self, debounce_press=200):
        self.button = Pin(16, Pin.IN, Pin.PULL_UP)
        self.button.irq(trigger=Pin.IRQ_RISING, handler=lambda _: self.button_callback())
        self.debounce_press = debounce_press
        self.__pressed = 0
        self.__debounce_time = 0

        self.x_adc = ADC(27)
        self.x = 0
        self.__debounce_time_x = 0

        self.y_adc = ADC(28)
        self.y = 0
        self.__debounce_time_y = 0

    def was_pressed(self):
        pressed = self.__pressed
        self.__pressed = 0
        return pressed

    def button_callback(self):
        if (time.ticks_ms() - self.__debounce_time) > self.debounce_press:
            self.__pressed = 1
            self.__debounce_time = time.ticks_ms()

    def map_direction(self, analog_val: int, min: int, max: int) -> int:
        _max = -abs(max)
        _min = abs(min)

        val = analog_val - 32767
        if val < 0: 
            # The max mapping corresponds to the smaller half (it's a bit unusual, but correct)
            if _max != 0:
                val = round(val / ( 32768 / _max ))
                return int(math.copysign(1, max) * val)
        elif _min != 0:
                val = round(val / ( 32768 / _min ))
                return int(math.copysign(1, min) * val)
        return 0

    def read_x(self, left=-1, right=1, no_reset=False):
        if not self.x or not no_reset:
            self.x = self.map_direction(self.x_adc.read_u16(), left, right)
        return self.x

    def reset_x(self):
        self.x = 0

    def was_pressed_x(self, debounce=200):
        pressed = 0
        self.read_x(no_reset=True)
        if (time.ticks_ms() - self.__debounce_time_x) > debounce:
            pressed = self.x
            self.x = 0
            self.__debounce_time_x = time.ticks_ms()
        return pressed

    def read_y(self, up=-1, down=1, no_reset=False):
        if not self.y or not no_reset:
            self.y = self.map_direction(self.y_adc.read_u16(), down, up)
        return self.y

    def reset_y(self):
        self.y = 0

    def was_pressed_y(self, debounce=200):
        pressed = 0
        self.read_y(no_reset=True)
        if (time.ticks_ms() - self.__debounce_time_y) > debounce:
            pressed = self.y
            self.y = 0
            self.__debounce_time_y = time.ticks_ms()
        return pressed

joy = Joystick()

class Tetris():
    def __init__(self):
        self.init_x = 3
        self.init_y = 6
        self.next_visible_y = self.init_y + 5

        self.score = 0
        self.speed = 0
        self.ipass = 0

        joy.map_y_min = 0
        joy.map_y_max = 10

        self.screen = FrameBuffer()
        self.concrete = FrameBuffer()
        self.reduced = 0


    def run(self):
        x = self.init_x
        y = self.init_y

        curr = figures.random_tetramino()
        next = figures.random_tetramino()

        while True:
            if self.ipass >= 10:
                self.ipass = 0
                y += 1

            self.draw_score()

            x_diff = joy.read_x(no_reset=True)
            new_x = x + x_diff
            if (new_x >= 0 and new_x < SCREEN_WIDTH
                and not self.concrete.collides(new_x, y, figure=curr)):
                x = new_x
            joy.reset_x()

            if joy.was_pressed():
                rotated = curr.rotate()
                shift = rotated.height - rotated.width if x + rotated.width >= SCREEN_WIDTH else 0

                if not self.concrete.collides(x + shift, y, figure=rotated):
                    curr = rotated
                    x += shift

            if y > self.next_visible_y:
                self.screen.draw(self.init_x, self.init_y, next)
            if not self.concrete.collides(x, y, figure=curr):
                self.screen.draw(x, y, curr)
            else:
                self.screen.draw(x, y - 1, curr)
                self.concrete.draw(x, y - 1, curr)
                x = self.init_x
                y = self.init_y + 1
                if self.concrete.collides(x, y, figure=curr):
                    self.game_over(curr)
                    return

                curr = next
                next = figures.random_tetramino()

                self.reduced = self.reduce_concrete()
                self.score += self.reduced

            self.screen.render()
            self.screen.copy_from(self.concrete)
            self.shift_concrete()

            if self.score > 99:
                self.score = 0
            self.ipass += max(1, self.score // 10) + joy.read_y(up=0, down=10)
            time.sleep_ms(50)


    def draw_score(self):
        self.score %= 100
        self.speed = self.score // 10
        self.screen.draw(0, 0, figures.DIGITS[self.speed])
        self.screen.draw(4, 0, figures.DIGITS[self.score % 10])
        self.screen.draw(0, 5, HLINE)


    def reduce_concrete(self) -> int:
        score = 0
        for idx in range(SCREEN_HEIGHT, 5, -1):
            row_idx = (idx - 1)
            if is_full(self.concrete.row(row_idx)):
                score += 1
                self.concrete.clear(_from=row_idx*SCREEN_WIDTH, to=(row_idx+1)*SCREEN_WIDTH)
        return score


    def shift_concrete(self):
        if not self.reduced:
            return

        to_idx = SCREEN_HEIGHT - 1
        from_idx = SCREEN_HEIGHT - 1
        for _ in range(SCREEN_HEIGHT):
            if is_empty(self.concrete.row(from_idx)):
                from_idx -= 1
                continue
            if from_idx != to_idx:
                target = self.concrete.row(to_idx)
                target[:] = self.concrete.row(from_idx)
            from_idx -= 1
            to_idx -= 1

        # +1 to compensate last for loop iteration
        self.concrete.clear(to=(to_idx + 1) * SCREEN_WIDTH)


    def game_over(self, figure):
        while not joy.was_pressed():
            for idx in range(1, len(COLORS)):
                self.screen.draw(self.init_x, self.init_y, figure, color=idx)
                self.screen.render()
                time.sleep_ms(500)
                self.screen.draw(self.init_x, self.init_y, figure, color=BLACK_IDX)
                self.screen.render()
                time.sleep_ms(500)

class Dot():
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    def move(self, direction: "Dot") -> "Dot":
        return self + direction

    def move_wrap(self, direction: "Dot") -> "Dot":
        dot = self.move(direction)
        x = dot.x
        y = dot.y

        if x == -1:
            x = SCREEN_WIDTH - 1
        elif x == SCREEN_WIDTH:
            x = 0

        if y == -1:
            y = SCREEN_HEIGHT - 1
        elif y == SCREEN_HEIGHT:
            y = 0

        return Dot(x, y)

    def set(self, other) -> bool:
        self.x = other.x
        self.y = other.y

    def reset(self) -> bool:
        self.x = 0
        self.y = 0
    
    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0

    def is_opposite(self, other) -> bool:
        return (self + other).is_zero()

    def opposite(self) -> "Dot":
        return Dot(-self.x, -self.y)

    def __sub__(self, other) -> "Dot":
        return Dot(self.x - other.x, self.y - other.y)

    def __add__(self, other) -> "Dot":
        return Dot(self.x + other.x, self.y + other.y)

    def __eq__(self, other) -> bool:
        return self.x == other.x and self.y == other.y

    def outside(self) -> bool:
        return self.x < 0 or self.x >= SCREEN_WIDTH or self.y < 0 or self.y >= SCREEN_HEIGHT

    def __str__(self) -> str:
        return f"Dot(x={self.x}, y={self.y})"


class Missile():
    def __init__(self, pos: Dot, direction: Dot, group: int):
        self.pos = pos
        self.direction = direction
        self.group = group
    
    def move(self) -> bool:
        self.pos = self.pos.move(self.direction)
        return self.visible()

    def hide(self):
        self.pos.set(Dot(-1, -1))

    def visible(self):
        return not self.pos.outside()

class Tank():
    def __init__(self, pos: Dot, lives=3, origin=-1):
        self.missiles: list[Missile] = []
        self.pos = pos
        self.origin = origin
        self.is_player = origin == -1
        self.rotation = 0
        self.rotations = [
                Dot(-1, 0),
                Dot(0, -1),
                Dot(1, 0),
                Dot(0, 1),
            ]
        self.figure = Figure(bytearray(
            b"\0\3\3"
            b"\1\3\0"
            b"\0\3\3"
        ), width=3)
        self.lives = lives

    @property
    def direction(self) -> Dot:
        return self.rotations[self.rotation]

    def rotate(self, direction: Dot) -> bool:
        rotated = 0
        while self.direction != direction:
            self.figure = self.figure.rotate()
            self.rotation = (self.rotation + 1) % len(self.rotations)
            rotated += 1
            if rotated == len(self.rotations):
                return False
        return rotated > 0

    def fire(self):
        self.missiles.append(Missile(self.pos + Dot(1, 1), self.direction, group=self.origin))

    def move(self, direction: Dot, collides, allow_backword=False):
        if not direction.is_zero():
            if (allow_backword and self.direction.is_opposite(direction)) or not self.rotate(direction):
                pos = self.pos + direction
                if not collides(pos.x, pos.y, self.figure):
                    self.pos = pos
    
    def move_missiles(self):
        visible_idx = 0 
        for m in self.missiles:
            visible = m.move()
            if visible:
                self.missiles[visible_idx] = m
                visible_idx += 1
        self.missiles = self.missiles[:visible_idx]

    def collides(self, dot: Dot) -> bool:
        tank_center = self.pos + Dot(1, 1)
        distance = tank_center - dot
        return abs(distance.x) <= 1 and abs(distance.y) <= 1

    def hit(self, tank: "Tank"):
        if not self.is_player and not tank.is_player:
            return

        for m in self.missiles:
            if tank.collides(m.pos):
                tank.lives -= 1
                m.hide()

    def is_dead(self) -> bool:
        return self.lives <= -18

    def is_dying(self) -> bool:
        return self.lives <= 0


class Tanks():
    STAGE_SPAWN = 0
    STAGE_MOVE = 1
    STAGE_ROTATE = 2
    STAGE_FIRE = 3
    STAGE_NONE = 4
    STAGES = (
        STAGE_SPAWN,
        STAGE_MOVE, STAGE_MOVE,
        STAGE_ROTATE, STAGE_ROTATE,
        STAGE_FIRE, STAGE_FIRE, STAGE_FIRE,
    )

    def __init__(self):
        self.screen = FrameBuffer()
        self.tank = Tank(Dot(3, 16))
        self.score = 0
        self.spawns = [Dot(0, 6), Dot(5, 6), Dot(0, 29), Dot(5, 29)]
        self.enemies = []
        self.explosion = Figure(bytearray(
            b"\2\0\2"
            b"\0\2\0"
            b"\2\0\2"
        ), width=3)

    def run(self):
        step = 10
        round = 10
        while True:
            self.screen.clear()
            self.draw_score()
            self.draw_lives()

            x = joy.read_x()
            y = joy.read_y()
            if x and y:
                x = 0

            for e in self.enemies:
                self.draw_tank(e)
            self.tank.move(Dot(x, y), self.screen.collides)
            self.draw_tank(self.tank)

            if joy.was_pressed():
                self.tank.fire()
            self.tank.move_missiles()

            for e in self.enemies:
                e.move_missiles()
                self.tank.hit(e)
                e.hit(self.tank)
                self.draw_missiles(e.missiles)
            self.draw_missiles(self.tank.missiles)

            count = self.remove_dead_enemies()
            self.score += count

            self.screen.render()
            if self.tank.is_dead():
                self.game_over()
                return

            speedup = self.score // 10
            if step >= round - speedup:
                self.ai()
                step = 0
            step += 1

            time.sleep_ms(50)

    def ai(self):
        # Enhanced AI with better decision making
        stage = Tanks.STAGE_SPAWN
        if len(self.enemies) > 1:
            # Weight stages based on game state
            weighted_stages = []
            
            # More aggressive when player has fewer lives
            if self.tank.lives <= 1:
                weighted_stages.extend([Tanks.STAGE_FIRE] * 4)
                weighted_stages.extend([Tanks.STAGE_MOVE] * 2)
            else:
                weighted_stages.extend([Tanks.STAGE_FIRE] * 2)
                weighted_stages.extend([Tanks.STAGE_MOVE] * 3)
            
            weighted_stages.extend([Tanks.STAGE_ROTATE] * 2)
            weighted_stages.append(Tanks.STAGE_NONE)
            
            stage = random.choice(weighted_stages)

        if stage == Tanks.STAGE_SPAWN:
            if len(self.enemies) >= 4:
                return
            
            # Smart spawning - prefer spawns closer to player
            spawn_priorities = []
            player_pos = self.tank.pos
            
            for idx, spawn_pos in enumerate(self.spawns):
                is_used = any(idx == e.origin for e in self.enemies)
                if not is_used:
                    # Calculate distance to player (Manhattan distance)
                    distance = abs(spawn_pos.x - player_pos.x) + abs(spawn_pos.y - player_pos.y)
                    # Closer spawns get higher priority (lower distance = higher priority)
                    priority = 100 - distance
                    spawn_priorities.append((idx, priority))
            
            if spawn_priorities:
                # Weighted random selection favoring closer spawns
                total_weight = sum(priority for _, priority in spawn_priorities)
                if total_weight > 0:
                    rand_val = random.randrange(total_weight)
                    current_weight = 0
                    for idx, priority in spawn_priorities:
                        current_weight += priority
                        if rand_val < current_weight:
                            pos = self.spawns[idx]
                            self.enemies.append(Tank(pos, lives=1, origin=idx))
                            return
                            
        elif stage == Tanks.STAGE_NONE:
            return
        else:
            # Select tank based on strategic priority
            active_tanks = [t for t in self.enemies if not t.is_dying()]
            if not active_tanks:
                return
                
            # Prioritize tanks that can see the player or are closer
            tank_priorities = []
            player_pos = self.tank.pos
            
            for tank in active_tanks:
                priority = 1
                
                # Higher priority for tanks closer to player
                distance = abs(tank.pos.x - player_pos.x) + abs(tank.pos.y - player_pos.y)
                priority += max(0, 20 - distance)
                
                # Higher priority for tanks that can hit player in current direction
                if self.can_hit_player(tank):
                    priority += 15
                
                # Higher priority for tanks with clear line of sight
                if self.has_line_of_sight(tank, player_pos):
                    priority += 10
                
                tank_priorities.append((tank, priority))
            
            # Weighted selection
            total_weight = sum(priority for _, priority in tank_priorities)
            if total_weight <= 0:
                tank = random.choice(active_tanks)
            else:
                rand_val = random.randrange(total_weight)
                current_weight = 0
                tank = active_tanks[0]  # fallback
                for t, priority in tank_priorities:
                    current_weight += priority
                    if rand_val < current_weight:
                        tank = t
                        break

            if stage == Tanks.STAGE_MOVE:
                self.smart_move(tank)
            elif stage == Tanks.STAGE_FIRE:
                # Only fire if there's a good chance to hit
                if self.should_fire(tank):
                    tank.fire()
            elif stage == Tanks.STAGE_ROTATE:
                self.smart_rotate(tank)

    def can_hit_player(self, tank: Tank) -> bool:
        """Check if tank can potentially hit player in current direction"""
        direction = tank.direction
        pos = tank.pos + Dot(1, 1)  # Tank center
        player_center = self.tank.pos + Dot(1, 1)
        
        # Check if player is in the same line as tank's direction
        if direction.x != 0:  # Horizontal movement
            return (pos.y == player_center.y and
                   ((direction.x > 0 and pos.x < player_center.x) or
                    (direction.x < 0 and pos.x > player_center.x)))
        elif direction.y != 0:  # Vertical movement
            return (pos.x == player_center.x and
                   ((direction.y > 0 and pos.y < player_center.y) or
                    (direction.y < 0 and pos.y > player_center.y)))
        return False

    def has_line_of_sight(self, tank: Tank, target_pos: Dot) -> bool:
        """Check if tank has clear line of sight to target"""
        tank_center = tank.pos + Dot(1, 1)
        target_center = target_pos + Dot(1, 1)
        
        # Simple line of sight - check if target is in cardinal directions
        dx = target_center.x - tank_center.x
        dy = target_center.y - tank_center.y
        
        # Must be in cardinal direction (horizontal or vertical line)
        if dx != 0 and dy != 0:
            return False
            
        # Check for obstacles in the path (simplified)
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return True
            
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        # Check a few points along the path
        for i in range(1, min(steps, 5)):
            check_pos = Dot(tank_center.x + i * step_x, tank_center.y + i * step_y)
            if self.screen.collides(check_pos.x, check_pos.y, tank.figure):
                return False
                
        return True

    def should_fire(self, tank: Tank) -> bool:
        """Determine if tank should fire based on strategic considerations"""
        # Fire if can hit player
        if self.can_hit_player(tank):
            return True
            
        # Fire randomly but less frequently if no clear shot
        return random.randrange(10) == 0

    def smart_move(self, tank: Tank):
        """Enhanced movement AI with pathfinding towards player"""
        self.remove_tank(tank)
        
        player_pos = self.tank.pos
        tank_pos = tank.pos
        
        # Calculate direction towards player
        dx = player_pos.x - tank_pos.x
        dy = player_pos.y - tank_pos.y
        
        # Prefer moving towards player
        preferred_directions = []
        
        if abs(dx) > abs(dy):
            # Horizontal movement preferred
            if dx > 0:
                preferred_directions.append(Dot(1, 0))
            else:
                preferred_directions.append(Dot(-1, 0))
            # Add vertical as secondary
            if dy > 0:
                preferred_directions.append(Dot(0, 1))
            elif dy < 0:
                preferred_directions.append(Dot(0, -1))
        else:
            # Vertical movement preferred
            if dy > 0:
                preferred_directions.append(Dot(0, 1))
            else:
                preferred_directions.append(Dot(0, -1))
            # Add horizontal as secondary
            if dx > 0:
                preferred_directions.append(Dot(1, 0))
            elif dx < 0:
                preferred_directions.append(Dot(-1, 0))
        
        # Try preferred directions first
        for direction in preferred_directions:
            pos = tank.pos + direction
            if not self.screen.collides(pos.x, pos.y, tank.figure):
                tank.move(direction, self.screen.collides, allow_backword=True)
                return
        
        # If no preferred direction works, try current direction or reverse
        direction = tank.direction
        pos = tank.pos + direction
        if self.screen.collides(pos.x, pos.y, tank.figure):
            direction = direction.opposite()
        tank.move(direction, self.screen.collides, allow_backword=True)

    def smart_rotate(self, tank: Tank):
        """Enhanced rotation AI to face towards player"""
        player_pos = self.tank.pos
        tank_pos = tank.pos
        
        # Calculate direction towards player
        dx = player_pos.x - tank_pos.x
        dy = player_pos.y - tank_pos.y
        
        # Choose best direction to face player
        if abs(dx) > abs(dy):
            # Face horizontally
            target_direction = Dot(1 if dx > 0 else -1, 0)
        else:
            # Face vertically
            target_direction = Dot(0, 1 if dy > 0 else -1)
        
        # Rotate towards target direction
        if tank.direction != target_direction:
            tank.rotate(target_direction)
        else:
            # Already facing player, occasionally rotate randomly for unpredictability
            if random.randrange(4) == 0:
                direction = random.choice(tank.rotations)
                tank.rotate(direction)

    def remove_tank(self, tank: Tank):
        self.screen.draw(tank.pos.x, tank.pos.y, tank.figure, BLACK_IDX)

    def draw_missiles(self, missiles):
        for m in missiles:
            if m.visible():
                self.screen.set(m.pos.x, m.pos.y, RED_IDX)

    def draw_tank(self, tank: Tank):
        if tank.is_dead():
            return

        self.screen.draw(tank.pos.x, tank.pos.y, tank.figure)
        if tank.lives <= 0:
            tank.lives -= 1
            if tank.lives % 6 == 0:
                self.screen.draw(tank.pos.x, tank.pos.y, self.explosion)

    def remove_dead_enemies(self) -> int:
        left = 0
        right = len(self.enemies) - 1
        count = 0
        while left <= right:
            if self.enemies[left].is_dead():
                self.enemies[left] = self.enemies[right]
                self.enemies = self.enemies[:right]
                right -= 1
                count += 1
            else:
                left += 1

        return count

    def draw_score(self):
        self.score %= 100
        self.speed = self.score // 10
        self.screen.draw(0, 0, figures.DIGITS[self.speed])
        self.screen.draw(4, 0, figures.DIGITS[self.score % 10])
        self.screen.draw(0, 5, HLINE)

    def draw_lives(self):
        y = 5
        x = 0
        for _ in range(self.tank.lives):
            self.screen.set(x, y, LIGHT_BLUE_IDX)
            x += 2

    def game_over(self):
        while not joy.was_pressed():
            x = random.randrange(SCREEN_WIDTH)
            y = random.randrange(6, SCREEN_HEIGHT)
            color = random.choice(range(len(COLORS)))
            self.screen.set(x, y, color)
            self.screen.render()
            time.sleep_ms(50)
            


class Races():
    def __init__(self):
        self.screen = FrameBuffer()
        self.road = FrameBuffer.from_rows((
            0o_33000333000333000333000333000333,   #
            0o_00000000000000000000000000000000,   #  7^
            0o_00000000000000000000000000000000,   #   |
            0o_00000000000000000000000000000000,   # x |
            0o_00000000000000000000000000000000,   #   |
            0o_00000000000000000000000000000000,   #  0+---->
            0o_00000000000000000000000000000000,   #   0 y  31
            0o_33000333000333000333000333000333,   #
        ))
        self.car = Figure(bytearray(
            b"\0\3\0"
            b"\3\3\3"
            b"\0\3\0"
            b"\0\3\0"
            b"\3\3\3"
        ), width=3)
        
        # New features
        self.lives = 3
        self.score = 0
        self.obstacles = []  # List of obstacle positions
        self.bullets = []    # List of bullet positions
        self.obstacle_spawn_counter = 0
        self.invulnerable_time = 0  # Invulnerability frames after hit
        
        # Obstacle figure
        self.obstacle = Figure(bytearray(
            b"\2\2\2"
            b"\2\0\2"
            b"\2\2\2"
        ), width=3)

    def run(self):
        step = 5
        pos = Dot(3, 27)

        while True:
            # Handle input
            x = joy.read_x()
            y = joy.read_y()
            if x and y:
                y = 0

            # Move car
            new_pos = Dot(pos.x + x, pos.y + y)
            if not self.road.collides(new_pos.x, new_pos.y, self.car):
                pos = new_pos

            # Shooting
            if joy.was_pressed():
                self.bullets.append(Dot(pos.x + 1, pos.y - 1))  # Shoot from car center

            # Update game state
            self.update_bullets()
            self.update_obstacles()
            self.check_collisions(pos)
            
            # Draw everything
            self.screen.copy_from(self.road)
            self.draw_obstacles()
            self.draw_bullets()
            
            # Draw car (flash if invulnerable)
            if self.invulnerable_time <= 0 or self.invulnerable_time % 4 < 2:
                self.screen.draw(pos.x, pos.y, self.car)
            
            self.draw_ui()
            self.screen.render()

            # Check game over
            if self.lives <= 0:
                self.game_over()
                return

            # Scroll road and spawn obstacles
            if step >= 5:
                step = 0
                self.scroll_road()
                self.spawn_obstacles()

            # Update counters
            if self.invulnerable_time > 0:
                self.invulnerable_time -= 1
            step += 1
            time.sleep_ms(20)

    def scroll_road(self):
        """Scroll the road and move obstacles"""
        left_pixel = self.road.get(0, SCREEN_HEIGHT-1)
        right_pixel = self.road.get(SCREEN_WIDTH - 1, SCREEN_HEIGHT-1)
        self.road.shift_right(1)
        self.road.set(0, 0, left_pixel)
        self.road.set(SCREEN_WIDTH - 1, 0, right_pixel)
        
        # Move obstacles down
        for obstacle in self.obstacles:
            obstacle.y += 1
        
        # Remove obstacles that are off screen
        self.obstacles = [obs for obs in self.obstacles if obs.y < SCREEN_HEIGHT]

    def spawn_obstacles(self):
        """Randomly spawn obstacles at the top of the screen"""
        self.obstacle_spawn_counter += 1
        
        # Spawn obstacle every 15-30 steps randomly
        if self.obstacle_spawn_counter >= random.randrange(15, 31):
            self.obstacle_spawn_counter = 0
            
            # Choose random lane (avoid road edges)
            lanes = [1, 2, 3, 4, 5, 6]  # Valid lanes for 3-wide obstacles
            lane = random.choice(lanes)
            
            # Make sure obstacle doesn't overlap with existing ones
            can_spawn = True
            for existing in self.obstacles:
                if existing.y < 10 and abs(existing.x - lane) < 4:  # Too close
                    can_spawn = False
                    break
            
            if can_spawn:
                self.obstacles.append(Dot(lane, 0))

    def update_bullets(self):
        """Update bullet positions and remove off-screen bullets"""
        for bullet in self.bullets:
            bullet.y -= 2  # Bullets move up fast
        
        # Remove bullets that are off screen
        self.bullets = [bullet for bullet in self.bullets if bullet.y >= 0]

    def update_obstacles(self):
        """Handle bullet-obstacle collisions"""
        bullets_to_remove = []
        obstacles_to_remove = []
        
        for i, bullet in enumerate(self.bullets):
            for j, obstacle in enumerate(self.obstacles):
                # Check if bullet hits obstacle
                if (abs(bullet.x - (obstacle.x + 1)) <= 1 and
                    abs(bullet.y - (obstacle.y + 1)) <= 1):
                    bullets_to_remove.append(i)
                    obstacles_to_remove.append(j)
                    self.score += 10  # Points for destroying obstacle
        
        # Remove hit bullets and obstacles (in reverse order to maintain indices)
        for i in sorted(bullets_to_remove, reverse=True):
            if i < len(self.bullets):
                del self.bullets[i]
        for j in sorted(obstacles_to_remove, reverse=True):
            if j < len(self.obstacles):
                del self.obstacles[j]

    def check_collisions(self, car_pos):
        """Check if car collides with obstacles"""
        if self.invulnerable_time > 0:
            return  # Car is invulnerable
        
        car_center = Dot(car_pos.x + 1, car_pos.y + 2)  # Car center
        
        for obstacle in self.obstacles:
            obstacle_center = Dot(obstacle.x + 1, obstacle.y + 1)
            
            # Check collision (simple distance check)
            if (abs(car_center.x - obstacle_center.x) <= 2 and
                abs(car_center.y - obstacle_center.y) <= 3):
                self.lives -= 1
                self.invulnerable_time = 60  # 3 seconds of invulnerability at 50ms per frame
                break

    def draw_obstacles(self):
        """Draw all obstacles on screen"""
        for obstacle in self.obstacles:
            if 0 <= obstacle.y < SCREEN_HEIGHT - 2:  # Make sure obstacle fits on screen
                self.screen.draw(obstacle.x, obstacle.y, self.obstacle)

    def draw_bullets(self):
        """Draw all bullets on screen"""
        for bullet in self.bullets:
            if 0 <= bullet.y < SCREEN_HEIGHT:
                self.screen.set(bullet.x, bullet.y, YELLOW_IDX)

    def draw_ui(self):
        """Draw score and lives"""
        # Draw score (top left and right)
        score_display = min(99, self.score // 10)  # Show score/10, max 99
        self.screen.draw(0, 0, figures.DIGITS[score_display // 10])
        self.screen.draw(4, 0, figures.DIGITS[score_display % 10])
        
        # Draw lives (between score digits, as small dots)
        for i in range(min(3, self.lives)):  # Show max 3 lives
            self.screen.set(3, 1 + i, LIGHT_BLUE_IDX)  # Vertical stack between digits

    def game_over(self):
        """Game over animation"""
        while not joy.was_pressed():
            # Flash the screen
            for color_idx in range(1, len(COLORS)):
                for x in range(SCREEN_WIDTH):
                    for y in range(6, SCREEN_HEIGHT):
                        if random.randrange(3) == 0:  # Random flashing
                            self.screen.set(x, y, color_idx)
                
                self.screen.render()
                time.sleep_ms(100)
                
                # Clear and show final score
                self.screen.clear()
                final_score = min(99, self.score // 10)
                self.screen.draw(1, 14, figures.DIGITS[final_score // 10])
                self.screen.draw(5, 14, figures.DIGITS[final_score % 10])
                self.screen.render()
                time.sleep_ms(400)


class Snake():

    def __init__(self):
        self.body = [Dot(4, 15), Dot(4, 16), Dot(4, 17)]
        self.direction = Dot(0, 1)
        self.apple = Dot(5, 5)
        self.screen = FrameBuffer()


    def run(self):
        step = 30
        while True:
            new_x = joy.read_x()
            new_y = joy.read_y()
            if new_x and new_y:
                new_x = 0
            direction = Dot(new_x, new_y)
            speedup = 1

            if not (direction.is_zero() or self.direction.is_opposite(direction)):
                self.direction.set(direction)
                speedup = 5 if self.direction == direction else 1

            if step >= 30:
                step = 0

                self.screen.clear()
                self.draw_snake(DARK_GREEN_IDX)
                self.respawn_apple()
                if not self.move_forward():
                    self.game_over()
                    return
                self.draw_snake()

                self.screen.render()

            step += 1*speedup
            time.sleep_ms(20)

    def respawn_apple(self):
        if self.apple is None:
            x = random.randrange(SCREEN_WIDTH)
            y = random.randrange(SCREEN_HEIGHT)
            if self.screen.get(x, y) == BLACK_IDX:
                self.apple = Dot(x, y)

        if self.apple:
            self.screen.set(self.apple.x, self.apple.y, RED_IDX)

    def move_forward(self):
        head_idx = len(self.body)-1
        dot = self.body[head_idx].move_wrap(self.direction)

        color = self.screen.get(dot.x, dot.y)
        no_collision = color == 0 and dot not in self.body
        if not no_collision:
            if color == RED_IDX: 
                self.body.append(dot)
                self.apple = None
                return True # Eat the apple

        for idx in range(len(self.body) - 1):
            self.body[idx] = self.body[idx+1]
        self.body[head_idx] = dot

        return no_collision
    
    def draw_snake(self, color=GREEN_IDX):
        for dot in self.body:
            self.screen.set(dot.x, dot.y, color)
        head = self.body[-1]
        self.screen.set(head.x, head.y, LIGHT_GREEN_IDX)

    def game_over(self):
        self.draw_snake(color=BRICK_IDX)
        color = 0
        while not joy.was_pressed():
            self.screen.set(self.apple.x, self.apple.y, color)
            self.screen.render()
            color = (color + 1) % len(COLORS)
            time.sleep_ms(200)

class Live():

    def __init__(self):
        self.screen = FrameBuffer()
        self.next_screen = FrameBuffer()
        self.generation = 0
        self.paused = False
        self.pattern_index = 0
        
        # Define some classic Conway patterns
        self.patterns = [
            # Random pattern
            None,
            # Glider
            [(1, 8), (2, 9), (0, 10), (1, 10), (2, 10)],
            # Blinker
            [(3, 10), (3, 11), (3, 12)],
            # Block
            [(3, 10), (4, 10), (3, 11), (4, 11)],
            # Toad
            [(2, 10), (3, 10), (4, 10), (1, 11), (2, 11), (3, 11)],
            # Beacon
            [(1, 8), (2, 8), (1, 9), (4, 10), (3, 11), (4, 11)],
        ]
        
        # Initialize with first pattern
        self.set_pattern()

    def run(self):
        self.play_live()
    
    def set_pattern(self):
        """Set the current pattern on the grid"""
        self.screen.clear()
        self.generation = 0
        
        current_pattern = self.patterns[self.pattern_index]
        if current_pattern is None:
            # Random pattern
            for x in range(SCREEN_WIDTH):
                for y in range(6, SCREEN_HEIGHT):  # Skip top area for UI
                    if random.randrange(4) == 0:  # 25% chance of being alive
                        self.screen.set(x, y, GREEN_IDX)
        else:
            # Predefined pattern
            for x, y in current_pattern:
                if 0 <= x < SCREEN_WIDTH and 6 <= y < SCREEN_HEIGHT:
                    self.screen.set(x, y, GREEN_IDX)
    
    def next_pattern(self):
        """Cycle to the next pattern"""
        self.pattern_index = (self.pattern_index + 1) % len(self.patterns)
        self.set_pattern()
    
    def count_neighbors(self, x, y):
        """Count live neighbors around cell at (x, y)"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip the cell itself
                
                nx, ny = x + dx, y + dy
                
                # Handle wrapping at screen boundaries
                if nx < 0:
                    nx = SCREEN_WIDTH - 1
                elif nx >= SCREEN_WIDTH:
                    nx = 0
                    
                if ny < 6:  # Don't wrap vertically into UI area
                    continue
                elif ny >= SCREEN_HEIGHT:
                    ny = 6
                
                if self.screen.get(nx, ny) != BLACK_IDX:
                    count += 1
        
        return count
    
    def next_generation(self):
        """Calculate next generation based on Conway's rules"""
        self.next_screen.clear()
        
        # Copy UI area
        for x in range(SCREEN_WIDTH):
            for y in range(6):
                self.next_screen.set(x, y, self.screen.get(x, y))
        
        # Apply Conway's rules to game area
        for x in range(SCREEN_WIDTH):
            for y in range(6, SCREEN_HEIGHT):
                neighbors = self.count_neighbors(x, y)
                is_alive = self.screen.get(x, y) != BLACK_IDX
                
                # Conway's Game of Life rules:
                # 1. Live cell with 2-3 neighbors survives
                # 2. Dead cell with exactly 3 neighbors becomes alive
                # 3. All other cells die or stay dead
                if is_alive and (neighbors == 2 or neighbors == 3):
                    self.next_screen.set(x, y, GREEN_IDX)
                elif not is_alive and neighbors == 3:
                    self.next_screen.set(x, y, GREEN_IDX)
                # else: cell dies or stays dead (already cleared)
        
        # Swap buffers
        self.screen, self.next_screen = self.next_screen, self.screen
        self.generation += 1
    
    def draw_ui(self):
        """Draw pattern indicator and controls info"""
        # Display pattern number (0-5)
        self.screen.draw(0, 0, figures.DIGITS[self.pattern_index])
        
        # Show generation indicator (simplified)
        gen_indicator = min(9, self.generation // 10)  # Show progress as single digit
        self.screen.draw(4, 0, figures.DIGITS[gen_indicator])
        
        self.screen.draw(0, 5, HLINE)
        
        # Show pause indicator
        if self.paused:
            # Draw pause symbol (two vertical lines)
            self.screen.set(6, 1, YELLOW_IDX)
            self.screen.set(6, 2, YELLOW_IDX)
            self.screen.set(6, 3, YELLOW_IDX)
            self.screen.set(7, 1, YELLOW_IDX)
            self.screen.set(7, 2, YELLOW_IDX)
            self.screen.set(7, 3, YELLOW_IDX)
    
    def play_live(self):
        """Main Game of Life loop"""
        step = 0
        speed = 20  # Steps between generations (lower = faster)
        
        while True:
            # Handle input
            if joy.was_pressed():
                self.paused = not self.paused
            
            # Cycle through patterns
            if joy.was_pressed_x():
                self.next_pattern()
                self.paused = False
            
            # Speed control with joystick Y
            speed_change = joy.was_pressed_y()
            if speed_change > 0:
                speed = min(50, speed + 5)  # Slower
            elif speed_change < 0:
                speed = max(5, speed - 5)   # Faster
            
            # Update generation
            if not self.paused and step >= speed:
                self.next_generation()
                step = 0
            
            # Draw everything
            self.draw_ui()
            self.screen.render()
            
            step += 1
            time.sleep_ms(50)


GAMES = [
    (
        (
            0o_00000000000000000000000000000000,
            0o_00000000000000000000000000000000,
            0o_03330033300333003330030030033300,
            0o_00300030000030003030030030030000,
            0o_00300033300030003330030330030000,
            0o_00300030000030003000033030030000,
            0o_00300033300030003000030030033300,
            0o_00000000000000000000000000000000,
        ),
        Tetris,
    ),
    (
        (
            0o_00000000000000000000000000000000,
            0o_00000000000000000000000000000000,
            0o_00003330033300303003030030030000,
            0o_00003000030300303003300030030000,
            0o_00003000030300333003300030330000,
            0o_00003000030300303003030033030000,
            0o_00003000033300303003030030030000,
            0o_00000000000000000000000000000000,
        ),
        Races,
    ),
    (
        (
            0o_00000000000000000000000000000000,
            0o_00000000000000000000000000000000,
            0o_00003330003000303003030030030000,
            0o_00000300030300303003300030030000,
            0o_00000300033300333003300030330000,
            0o_00000300030300303003030033030000,
            0o_00000300030300303003030030030000,
            0o_00000000000000000000000000000000,
        ),
        Tanks,
    ),
    (
        (
            0o_00000000000000000000000000000000,
            0o_00000000000000000030000000000000,
            0o_03300330330333003000303003003300,
            0o_00030303030300003003303030030030,
            0o_03300300030333003030303300033330,
            0o_00030300030300003300303030030030,
            0o_03300300030333003000303003030030,
            0o_00000000000000000000000000000000,
        ),
        Snake,
    ),
    (
        (
            0o_00000000000000000000000000000000,
            0o_00000000000000000000000000000000,
            0o_00000303030300303300303030000000,
            0o_00000303030300300030303030000000,
            0o_00000333330303303300333033300000,
            0o_00000303030330300030303030300000,
            0o_00000303030300303300303033300000,
            0o_00000000000000000000000000000000,
        ),
        Live,
    )
]


def main():
    idx = 0
    while True:
        next = joy.was_pressed_x()
        idx = (idx + next) % len(GAMES)
        if joy.was_pressed():
            GAMES[idx][1]().run()
        FrameBuffer.from_rows(GAMES[idx][0]).render()
        time.sleep_ms(100)

main()
