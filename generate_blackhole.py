#!/usr/bin/env python3
"""
Render a realistic-looking black hole still (assets/blackhole.jpg) for the banner intro.

  * starfield + faint Milky Way band with dust lanes + soft nebula clouds
  * gravitational lensing of that background (point-lens mapping, Einstein ring)
  * thin, tilted accretion disk with turbulent streaks and Doppler beaming
  * the far side of the disk lensed up over (and under) the shadow, photon ring
  * bloom + filmic tone mapping

    pip install numpy pillow
    python3 generate_blackhole.py
"""
import numpy as np
from PIL import Image, ImageFilter

W, H = 1882, 500            # 2x the banner size so the zoom stays sharp
CX, CY = W / 2, 266.0       # black hole centre (banner centre + 8px, at 2x)
RS = 60.0                   # shadow radius in px
COS_I = 0.13                # disk inclination: nearly edge-on
R_IN, R_OUT = 2.25 * RS, 7.0 * RS
OUTPUT = "assets/blackhole.jpg"
rng = np.random.default_rng(42)


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
    """Gaussian-ish blur: three box blurs per axis (works on float arrays, any channels)."""
    r = max(1, int(round(np.sqrt(12 * sigma * sigma / 3 + 1) - 1) / 2))
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a


# ───────────────────────── background sky (rendered larger, sampled through the lens) ─────────────────────────
PAD = 300
BH, BW = H + 2 * PAD, W + 2 * PAD
yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
sky = np.zeros((BH, BW, 3), np.float32)

# Milky Way: a soft diagonal band with dust lanes
d = ((yy - BH * 0.55) - (xx - BW / 2) * -0.16) / 150.0
band = np.exp(-d ** 2)
n1 = value_noise((BH, BW), 220)
n2 = value_noise((BH, BW), 60)
dust = np.clip((value_noise((BH, BW), 120) - 0.45) * 3.0, 0, 1)
mw = band * (0.55 * n1 + 0.45 * n2) * (1 - 0.8 * dust * band)
sky += mw[..., None] * np.array([0.11, 0.10, 0.12]) * 1.6

# faint nebula clouds (teal / violet, echoing the banner palette)
for (cx, cy, s, col) in [(0.18, 0.35, 260, (0.05, 0.12, 0.14)), (0.82, 0.62, 300, (0.12, 0.05, 0.16)),
                         (0.62, 0.2, 200, (0.04, 0.08, 0.13))]:
    g = np.exp(-(((xx - cx * BW) ** 2 + (yy - cy * BH) ** 2) / (2 * s * s)))
    sky += (g * value_noise((BH, BW), 140))[..., None] * np.array(col) * 1.8

# stars: power-law brightness, colour temperature from blue-white to orange
N = 5200
sx, sy = rng.uniform(0, BW, N), rng.uniform(0, BH, N)
bright = rng.pareto(2.2, N) * 0.12 + 0.03
temps = rng.choice([(0.75, 0.85, 1.0), (1.0, 1.0, 1.0), (1.0, 0.95, 0.85), (1.0, 0.8, 0.6)], N, p=[0.3, 0.35, 0.25, 0.1])
stars = np.zeros((BH, BW, 3), np.float32)
ix, iy = sx.astype(int), sy.astype(int)
np.add.at(stars, (iy, ix), (bright[:, None] * np.array(temps)).astype(np.float32))
core = blur(stars, 0.7) if False else stars
halo = blur(stars, 2.5)
sky += core * 1.4 + halo * 9.0

# ───────────────────────── lensing ─────────────────────────
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = X - CX, Y - CY
r = np.sqrt(dx * dx + dy * dy) + 1e-6
theta_e = 1.55 * RS
beta = r - theta_e ** 2 / r                    # point-lens mapping (negative -> other side)
sx_ = CX + dx / r * beta + PAD
sy_ = CY + dy / r * beta + PAD
sxi = np.clip(sx_, 0, BW - 2); syi = np.clip(sy_, 0, BH - 2)
x0, y0 = sxi.astype(int), syi.astype(int)
fx, fy = (sxi - x0)[..., None], (syi - y0)[..., None]
img = (sky[y0, x0] * (1 - fx) * (1 - fy) + sky[y0, x0 + 1] * fx * (1 - fy)
       + sky[y0 + 1, x0] * (1 - fx) * fy + sky[y0 + 1, x0 + 1] * fx * fy)
# magnification brightening near the Einstein ring
mag = np.clip(1.0 / np.abs(1 - (theta_e / r) ** 4 + 1e-3), 1, 4)
img *= (0.6 + 0.4 * mag)[..., None]

# ───────────────────────── accretion disk ─────────────────────────
# turbulent texture in (radius, angle) space: long streaks along the orbit
NR, NPHI = 256, 2048
tex_small = rng.random((NR // 4, 48)).astype(np.float32)
tex_small = np.concatenate([tex_small, tex_small[:, :3]], 1)
tex = np.asarray(Image.fromarray(tex_small).resize((NPHI + 128, NR), Image.BICUBIC))[:, :NPHI]
fine = np.asarray(Image.fromarray(rng.random((NR, 220)).astype(np.float32)).resize((NPHI, NR), Image.BICUBIC))
tex = 0.6 * tex + 0.4 * fine
tex = (tex - tex.min()) / (tex.max() - tex.min())


def disk_emission(rho, phi):
    """Brightness of the disk at disk-plane radius rho, azimuth phi."""
    inside = (rho >= R_IN) & (rho <= R_OUT)
    u = np.clip((rho - R_IN) / (R_OUT - R_IN), 0, 1)
    prof = (R_IN / np.maximum(rho, R_IN)) ** 2.4 * np.clip((rho - R_IN) / (0.12 * RS), 0, 1)
    prof *= np.clip((R_OUT - rho) / (1.6 * RS), 0, 1)
    ti = (u * (NR - 1)).astype(int)
    tj = (((phi / (2 * np.pi)) % 1.0) * (NPHI - 1)).astype(int)
    t = tex[ti, tj]
    return np.where(inside, prof * (0.45 + 0.85 * t ** 1.4), 0.0), u


def disk_color(u, doppler):
    hot = np.array([1.0, 0.96, 0.88]); mid = np.array([1.0, 0.68, 0.32]); cool = np.array([0.75, 0.28, 0.1])
    u = u[..., None]
    c = np.where(u < 0.35, hot + (mid - hot) * (u / 0.35), mid + (cool - mid) * ((u - 0.35) / 0.65))
    # approaching side is bluer/whiter
    return c + (np.array([1, 1, 1]) - c) * np.clip(doppler - 1, 0, 1)[..., None] * 0.5


# primary image of the disk (thin ellipse crossing the hole)
rho = np.sqrt(dx ** 2 + (dy / COS_I) ** 2)
phi = np.arctan2(dy / COS_I, dx)
e, u = disk_emission(rho, phi)
dop = 1 + 0.42 * (-dx / np.maximum(rho, 1))          # left side moves toward us
prim = e * dop ** 2.0
prim_col = disk_color(u, dop) * prim[..., None]
front = dy > 0                                       # near side passes in front of the shadow

# secondary (lensed) image: the far side of the disk bent over the top and under the bottom
psi = np.arctan2(dy, dx)
ring_t = (r - RS * 1.04) / (RS * 0.95)               # 0..1 across the lensed ring
rho2 = R_IN + np.clip(ring_t, 0, 1) ** 1.25 * (R_OUT - R_IN) * 0.85
top = np.clip(-np.sin(psi), 0, 1)
bottom = np.clip(np.sin(psi), 0, 1)
weight = (0.95 * top ** 0.45 + 0.35 * bottom ** 0.7) * ((ring_t >= 0) & (ring_t <= 1))
e2, u2 = disk_emission(rho2, psi * 1.0 + 0.4)
dop2 = 1 + 0.35 * (-np.cos(psi))
sec = e2 * weight * dop2 ** 2.0 * 2.1
sec_col = disk_color(u2, dop2) * sec[..., None]

# photon ring
pr = np.exp(-((r - RS * 1.035) / 1.6) ** 2) * (0.9 + 0.5 * (-np.cos(psi)))
pr_col = np.array([1.0, 0.92, 0.8]) * pr[..., None] * 1.3

shadow = r < RS
img = np.where(shadow[..., None], 0.0, img)
img = img + sec_col * 1.25 + pr_col
img = np.where((~front)[..., None] & ~shadow[..., None], img + prim_col * 1.2, img)   # back half
img = np.where(front[..., None], img + prim_col * 1.35, img)                         # front half (over shadow)

# ───────────────────────── bloom + tone mapping ─────────────────────────
bright_part = np.clip(img - 0.55, 0, None)
bloom = np.zeros_like(img)
for rad, w in ((4, 0.5), (12, 0.35), (30, 0.25)):
    bloom += w * blur(bright_part.astype(np.float32), rad)
img = img + bloom
img = 1 - np.exp(-img * 1.35)                         # filmic-ish tone map
img = np.clip(img, 0, 1) ** (1 / 1.1)

# vignette toward the banner background colour (#0d1117)
vig = np.clip(1 - ((X - CX) / (W * 0.62)) ** 2 - ((Y - CY) / (H * 0.9)) ** 2, 0, 1) ** 0.6
bg = np.array([13, 17, 23]) / 255.0
img = bg + (img - bg) * (0.25 + 0.75 * vig)[..., None]
img = np.maximum(img, bg * 0.9)

Image.fromarray((img * 255).astype(np.uint8)).save(OUTPUT, quality=86, optimize=True, progressive=True)
print("wrote", OUTPUT)
