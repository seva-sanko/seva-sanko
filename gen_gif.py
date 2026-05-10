import numpy as np
from PIL import Image
import hashlib

RULE_N = 59350005
GRID_W = 150
GRID_H = 45
CELL_SIZE = 5
FRAME_DURATION = 100

BG   = (255, 255, 255)
CELL = (0,   0,   0)

FONT_5x7 = {
    'V': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'S': [
        [0,1,1,1,0],
        [1,0,0,0,1],
        [1,0,0,0,0],
        [0,1,1,1,0],
        [0,0,0,0,1],
        [1,0,0,0,1],
        [0,1,1,1,0],
    ],
}

SCALE = 5   # each font pixel -> SCALE cells

def draw_char(grid, char, ox, oy):
    bitmap = FONT_5x7[char]
    for row, line in enumerate(bitmap):
        for col, bit in enumerate(line):
            if bit:
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        y = oy + row * SCALE + dy
                        x = ox + col * SCALE + dx
                        if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                            grid[y, x] = 1

def make_rules(n):
    b = bin(n)[2:].zfill(32)
    return np.array([int(b[i]) for i in range(32)], dtype=np.uint8)

def step(grid, rules):
    top    = np.roll(grid,  1, axis=0)
    bottom = np.roll(grid, -1, axis=0)
    right  = np.roll(grid, -1, axis=1)
    left   = np.roll(grid,  1, axis=1)
    state  = grid*16 + top*8 + right*4 + bottom*2 + left
    return rules[state]

def grid_hash(g):
    return hashlib.md5(g.tobytes()).hexdigest()

def to_image(grid):
    h, w = grid.shape
    img = Image.new("RGB", (w * CELL_SIZE, h * CELL_SIZE), BG)
    pix = img.load()
    ys, xs = np.where(grid == 1)
    for y, x in zip(ys, xs):
        for dy in range(CELL_SIZE):
            for dx in range(CELL_SIZE):
                pix[x * CELL_SIZE + dx, y * CELL_SIZE + dy] = CELL
    return img

rules = make_rules(RULE_N)

# draw "SSV" centered on grid
char_w = 5 * SCALE   # 25 cells wide
char_h = 7 * SCALE   # 35 cells tall
gap    = 4
total_w = char_w * 3 + gap * 2
ox = (GRID_W - total_w) // 2
oy = (GRID_H - char_h) // 2

grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
draw_char(grid, 'V', ox, oy)
draw_char(grid, 'V', ox + char_w + gap, oy)
draw_char(grid, 'S', ox + (char_w + gap) * 2, oy)

# try to find cycle (run up to 600 steps)
g = grid.copy()
seen = {}
history = [g.copy()]
found_cycle = False
for i in range(1, 600):
    h = grid_hash(g)
    if h in seen:
        start = seen[h]
        period = i - start
        print(f"cycle: period={period}, start={start}")
        frames_data = history[start:start + period]
        found_cycle = True
        break
    seen[h] = i
    g = step(g, rules)
    history.append(g.copy())

if not found_cycle:
    # ping-pong: letters dissolve → reform, seamless loop
    half = 36
    fwd = history[:half]
    back = history[half-2:0:-1]
    frames_data = fwd + back
    print(f"ping-pong: {half} fwd + {len(back)} back")

print(f"frames: {len(frames_data)}")

frames = [to_image(f) for f in frames_data]

HOLD_MS = 1000  # pause on letters at start and end of each loop
durations = [HOLD_MS] + [FRAME_DURATION] * (len(frames) - 2) + [HOLD_MS]

out = "ca.gif"
frames[0].save(
    out, save_all=True, append_images=frames[1:],
    optimize=True, duration=durations, loop=0
)
size_kb = __import__("os").path.getsize(out) // 1024
print(f"saved {out}: {GRID_W*CELL_SIZE}x{GRID_H*CELL_SIZE}px, {len(frames)} frames, {size_kb}KB")
