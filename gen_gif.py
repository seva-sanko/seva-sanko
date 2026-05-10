import numpy as np
from PIL import Image
import hashlib

RULE_N = 59350005
GRID_W = 150
GRID_H = 45
CELL_SIZE = 5
FRAME_DURATION = 80

BG   = (255, 255, 255)
CELL = (0,   0,   0)
GAP  = 0

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
    img_w = w * CELL_SIZE
    img_h = h * CELL_SIZE
    img = Image.new("RGB", (img_w, img_h), BG)
    pix = img.load()
    ys, xs = np.where(grid == 1)
    for y, x in zip(ys, xs):
        x0 = x * CELL_SIZE + GAP
        y0 = y * CELL_SIZE + GAP
        x1 = x0 + CELL_SIZE - GAP
        y1 = y0 + CELL_SIZE - GAP
        for dy in range(y1 - y0):
            for dx in range(x1 - x0):
                pix[x0 + dx, y0 + dy] = CELL
    return img

rules = make_rules(RULE_N)

# dots_grid spacing=4 → period 45, seamless loop
grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
for y in range(0, GRID_H, 4):
    for x in range(0, GRID_W, 4):
        grid[y, x] = 1

g = grid.copy()

# detect cycle
seen = {}
history = []
for i in range(1000):
    h = grid_hash(g)
    if h in seen:
        start = seen[h]
        period = i - start
        print(f"cycle: period={period}, starts at frame {start}")
        frames_data = history[start:]
        break
    seen[h] = i
    history.append(g.copy())
    g = step(g, rules)
else:
    print("no cycle found, using first 60 frames")
    frames_data = history[:60]
    period = 60

print(f"GIF frames: {len(frames_data)}")

frames = [to_image(f) for f in frames_data]

out = "ca.gif"
frames[0].save(
    out, save_all=True, append_images=frames[1:],
    optimize=True, duration=FRAME_DURATION, loop=0
)
size_kb = __import__("os").path.getsize(out) // 1024
print(f"saved {out}: {GRID_W*CELL_SIZE}x{GRID_H*CELL_SIZE}px, {len(frames)} frames, {size_kb}KB")
