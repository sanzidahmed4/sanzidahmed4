#!/usr/bin/env python3
"""
Render a realistic-looking spiral galaxy (assets/galaxy.jpg) used behind the name.

  * tilted two-armed logarithmic spiral, warm bulge, blue-white arms
  * dark dust lanes hugging the inner edge of each arm
  * pink star-forming knots and blue star clusters along the arms
  * foreground stars, a few distant background galaxies, bloom + tone mapping

    pip install numpy pillow
    python3 generate_galaxy.py
"""
import numpy as np
from PIL import Image

W, H = 1882, 500
CX, CY = W * 0.5, H * 0.52
SCALE = 520.0               # galaxy disk scale (px)
COS_I = 0.42                # inclination (1 = face-on)
PA = np.radians(-16)        # position angle on screen
PITCH = np.radians(17)      # spiral pitch angle
OUTPUT = "assets/galaxy.jpg"
rng = np.random.default_rng(7)


def _box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, sigma):
    r = max(1, int(round((np.sqrt(4 * sigma * sigma + 1) - 1) / 2)))
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a


def value_noise(shape, cell, octaves=5, persistence=0.55):
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / 2 ** o))
        small = rng.random((shape[0] // c + 3, shape[1] // c + 3)).astype(np.float32)
        big = np.asarray(Image.fromarray(small).resize((shape[1] + 3 * c, shape[0] + 3 * c), Image.BICUBIC))
        out += amp * big[c:c + shape[0], c:c + shape[1]]
        tot += amp
        amp *= persistence
    return out / tot


Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = X - CX, Y - CY
# into the galaxy plane
gx = dx * np.cos(PA) + dy * np.sin(PA)
gy = (-dx * np.sin(PA) + dy * np.cos(PA)) / COS_I
r = np.sqrt(gx * gx + gy * gy) / SCALE + 1e-4
th = np.arctan2(gy, gx)

# spiral arm density (two arms, log spiral) with a little noise in the phase
warp = (value_noise((H, W), 110) - 0.5) * 1.4
phase = th - np.log(r) / np.tan(PITCH) + warp


def arm_profile(offset, width):
    d = np.angle(np.exp(1j * 2 * (phase + offset))) / 2       # distance to nearest of 2 arms, in radians
    return np.exp(-(d / width) ** 2)


arms = arm_profile(0.0, 0.6)
dust = arm_profile(0.42, 0.24)                                  # dust lane on the inner (trailing) edge
clump = value_noise((H, W), 26, octaves=4)
fluff = value_noise((H, W), 70)

bulge = np.exp(-(r / 0.12) ** 0.9) * 2.4 + np.exp(-r / 0.32) * 0.6
disk = np.exp(-r / 0.55) * np.clip(r / 0.12, 0, 1)
floc = 0.6 + 0.8 * value_noise((H, W), 16, octaves=3)
arm_light = disk * (0.32 + 1.0 * arms * (0.5 + 0.8 * clump) * floc) * (0.7 + 0.6 * fluff)
dust_mask = 1 - 0.55 * dust * np.clip(r / 0.15, 0, 1) * (0.5 + 0.8 * value_noise((H, W), 40))

warm = np.array([1.0, 0.86, 0.66]); cool = np.array([0.66, 0.8, 1.0]); white = np.array([0.95, 0.95, 1.0])
mix = np.clip(r / 0.5, 0, 1)[..., None]
img = bulge[..., None] * warm + arm_light[..., None] * (white * (1 - mix) + cool * mix)
img *= dust_mask[..., None]
img += (dust * disk)[..., None] * np.array([0.05, 0.025, 0.01])  # faint brown in the lanes

# star-forming knots (pink) and young blue clusters along the arms
knots = np.zeros((H, W, 3), np.float32)
prob = (arms * disk * (r > 0.2)).ravel()
prob /= prob.sum()
for n, col, amp in ((240, (1.0, 0.45, 0.65), 0.8), (380, (0.7, 0.85, 1.0), 0.6)):
    idx = rng.choice(prob.size, n, p=prob)
    iy, ix = np.unravel_index(idx, (H, W))
    np.add.at(knots, (iy, ix), (rng.uniform(0.3, 1.0, n)[:, None] * np.array(col) * amp).astype(np.float32))
img += blur(knots, 1.8) * 9.0

# foreground stars + distant galaxies
fg = np.zeros((H, W, 3), np.float32)
N = 2600
sx, sy = rng.integers(0, W, N), rng.integers(0, H, N)
b = rng.pareto(2.3, N) * 0.12 + 0.03
cols = rng.choice([(0.75, 0.85, 1.0), (1.0, 1.0, 1.0), (1.0, 0.92, 0.8)], N)
np.add.at(fg, (sy, sx), (b[:, None] * cols).astype(np.float32))
img += fg * 1.3 + blur(fg, 2.0) * 7.0
for _ in range(10):
    ex, ey = rng.uniform(0, W), rng.uniform(0, H)
    if abs(ex - CX) < 500:
        continue
    a = rng.uniform(0, np.pi); s = rng.uniform(2, 5); q = rng.uniform(0.3, 0.8)
    u = ((X - ex) * np.cos(a) + (Y - ey) * np.sin(a)) / s
    v = (-(X - ex) * np.sin(a) + (Y - ey) * np.cos(a)) / (s * q)
    img += (np.exp(-(u * u + v * v)) * 0.25)[..., None] * np.array([1.0, 0.9, 0.75])

# bloom + tone map
bright = np.clip(img - 0.6, 0, None).astype(np.float32)
img = img + 0.5 * blur(bright, 5) + 0.35 * blur(bright, 18) + 0.2 * blur(bright, 45)
img = 1 - np.exp(-img * 1.1)
img = np.clip(img, 0, 1) ** (1 / 1.05)

bg = np.array([13, 17, 23]) / 255.0
img = np.maximum(img, bg)
Image.fromarray((img * 255).astype(np.uint8)).save(OUTPUT, quality=86, optimize=True, progressive=True)
print("wrote", OUTPUT)
