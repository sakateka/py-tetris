#!/usr/bin/env python3
"""
Test script for Conway's Game of Life implementation
"""

import sys
import time

# Mock the hardware-specific modules for testing
class MockPin:
    def __init__(self, pin, mode=None, pull=None):
        pass
    def irq(self, trigger=None, handler=None):
        pass

class MockADC:
    def __init__(self, pin):
        pass
    def read_u16(self):
        return 32767  # Neutral position

class MockNeoPixel:
    def __init__(self, pin, count):
        self.pixels = [(0,0,0)] * count
    def __setitem__(self, index, value):
        self.pixels[index] = value
    def write(self):
        pass

# Mock modules
class MockMachine:
    Pin = MockPin
    ADC = MockADC

class MockNeopixel:
    NeoPixel = MockNeoPixel

class MockMicropython:
    @staticmethod
    def alloc_emergency_exception_buf(size):
        pass

# Replace imports
sys.modules['machine'] = MockMachine()
sys.modules['neopixel'] = MockNeopixel()
sys.modules['micropython'] = MockMicropython()

# Now we can import our game logic
SCREEN_WIDTH = 8
SCREEN_HEIGHT = 32
SCREEN_SIZE = SCREEN_WIDTH * SCREEN_HEIGHT

BLACK_IDX = 0
GREEN_IDX = 3

class TestFrameBuffer:
    def __init__(self):
        self.content = [0] * SCREEN_SIZE
    
    def clear(self):
        self.content = [0] * SCREEN_SIZE
    
    def set(self, x, y, color):
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            self.content[y * SCREEN_WIDTH + x] = color
    
    def get(self, x, y):
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            return self.content[y * SCREEN_WIDTH + x]
        return 0
    
    def print_grid(self, start_y=6):
        """Print the grid for visualization"""
        print("Generation:")
        for y in range(start_y, min(start_y + 10, SCREEN_HEIGHT)):
            row = ""
            for x in range(SCREEN_WIDTH):
                if self.get(x, y) != BLACK_IDX:
                    row += "█"
                else:
                    row += "·"
            print(row)
        print()

class TestConway:
    def __init__(self):
        self.screen = TestFrameBuffer()
        self.next_screen = TestFrameBuffer()
        self.generation = 0
    
    def set_pattern(self, pattern, start_x=2, start_y=10):
        """Set a specific pattern on the grid"""
        self.screen.clear()
        for y, row in enumerate(pattern):
            for x, cell in enumerate(row):
                if cell == 1:
                    self.screen.set(start_x + x, start_y + y, GREEN_IDX)
    
    def count_neighbors(self, x, y):
        """Count live neighbors around cell at (x, y)"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                
                # Handle wrapping at screen boundaries
                if nx < 0:
                    nx = SCREEN_WIDTH - 1
                elif nx >= SCREEN_WIDTH:
                    nx = 0
                    
                if ny < 6:
                    continue
                elif ny >= SCREEN_HEIGHT:
                    ny = 6
                
                if self.screen.get(nx, ny) != BLACK_IDX:
                    count += 1
        
        return count
    
    def next_generation(self):
        """Calculate next generation based on Conway's rules"""
        self.next_screen.clear()
        
        # Apply Conway's rules to game area
        for x in range(SCREEN_WIDTH):
            for y in range(6, SCREEN_HEIGHT):
                neighbors = self.count_neighbors(x, y)
                is_alive = self.screen.get(x, y) != BLACK_IDX
                
                if is_alive and (neighbors == 2 or neighbors == 3):
                    self.next_screen.set(x, y, GREEN_IDX)
                elif not is_alive and neighbors == 3:
                    self.next_screen.set(x, y, GREEN_IDX)
        
        # Swap buffers
        self.screen, self.next_screen = self.next_screen, self.screen
        self.generation += 1

def test_blinker():
    """Test the classic blinker pattern"""
    print("Testing Blinker pattern:")
    conway = TestConway()
    
    # Blinker pattern (oscillates between horizontal and vertical line)
    blinker = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0]
    ]
    
    conway.set_pattern(blinker)
    
    for i in range(4):
        print(f"Generation {conway.generation}:")
        conway.screen.print_grid()
        conway.next_generation()
        time.sleep(0.5)

def test_block():
    """Test the stable block pattern"""
    print("Testing Block pattern (should remain stable):")
    conway = TestConway()
    
    # Block pattern (stable)
    block = [
        [1, 1],
        [1, 1]
    ]
    
    conway.set_pattern(block)
    
    for i in range(3):
        print(f"Generation {conway.generation}:")
        conway.screen.print_grid()
        conway.next_generation()
        time.sleep(0.5)

def test_glider():
    """Test the glider pattern"""
    print("Testing Glider pattern:")
    conway = TestConway()
    
    # Glider pattern (moves diagonally)
    glider = [
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ]
    
    conway.set_pattern(glider, start_x=1, start_y=8)
    
    for i in range(6):
        print(f"Generation {conway.generation}:")
        conway.screen.print_grid()
        conway.next_generation()
        time.sleep(0.5)

if __name__ == "__main__":
    print("Conway's Game of Life - Test Suite")
    print("=" * 40)
    
    test_blinker()
    print("\n" + "=" * 40)
    test_block()
    print("\n" + "=" * 40)
    test_glider()
    
    print("All tests completed!")
