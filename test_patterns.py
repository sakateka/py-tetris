#!/usr/bin/env python3
"""
Test the pattern cycling functionality
"""

# Simple test to verify pattern definitions
patterns = [
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

pattern_names = [
    "Random",
    "Glider", 
    "Blinker",
    "Block",
    "Toad",
    "Beacon"
]

print("Conway's Game of Life - Pattern Test")
print("=" * 40)

for i, (name, pattern) in enumerate(zip(pattern_names, patterns)):
    print(f"Pattern {i}: {name}")
    if pattern:
        print(f"  Coordinates: {pattern}")
        print(f"  Cell count: {len(pattern)}")
    else:
        print("  Random generation")
    print()

print("Pattern cycling test:")
for i in range(len(patterns) * 2):
    current_idx = i % len(patterns)
    print(f"Step {i}: Pattern {current_idx} ({pattern_names[current_idx]})")

print("\nAll pattern tests completed!")
