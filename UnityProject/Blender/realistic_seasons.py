"""
Realistic Four Seasons - Blender 5.x asset generator
====================================================

Builds four 7 m x 7 m diorama tiles of *the same place* through the seasons:
a cherry tree on a small mound, a pond, rocks, a fallen log, a wooden fence and
two spruces.  Spring = blossom + wildflowers, Summer = full foliage + reeds and
lily pads, Autumn = red/orange leaves, leaf litter, mushrooms and pumpkins,
Winter = bare snowy branches, ice, snow-covered everything and icicles.

All textures are synthesised with numpy and packed into the .blend as images,
so they survive a glTF/GLB export (no procedural shader nodes).

Run inside Blender (Scripting tab -> Run Script).  It first removes everything
in the current scene, then builds the four tiles.
"""
import math
import random

import numpy as np

try:
    import bpy
    import bmesh
    from mathutils import Vector, Euler, noise
except ImportError:  # allows the texture part to be tested outside Blender
    bpy = None

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
TILE = 7.0
HALF = TILE / 2
BASE_Z = -1.4
GAP = 8.8
GRID = {"Spring": (-GAP / 2, GAP / 2), "Summer": (GAP / 2, GAP / 2),
        "Autumn": (-GAP / 2, -GAP / 2), "Winter": (GAP / 2, -GAP / 2)}
POND_C = (1.3, -1.0)
POND_R = 1.55
WATER_Z = -0.06
TREE_P = (-1.25, 0.95)
ROCKS = [((0.15, -2.2), (0.55, 0.45, 0.38), 11), ((2.6, -2.35), (0.38, 0.32, 0.26), 12),
         ((-2.65, -2.45), (0.75, 0.6, 0.5), 13), ((-3.0, -1.55), (0.3, 0.28, 0.2), 14),
         ((2.8, -0.2), (0.28, 0.24, 0.18), 15), ((0.45, 0.4), (0.22, 0.2, 0.14), 16)]
LOG = ((-2.0, -0.45), 0.5, 1.9, 0.17)  # centre, z-rotation, length, radius
FENCE_X = [-3.15, -1.9, -0.65]
FENCE_Y = 3.1
SPRUCES = [((2.3, 2.35), 4.6, 1.6, 21), ((3.0, 0.95), 3.0, 1.1, 22), ((1.5, 2.95), 2.2, 0.8, 23)]


# =====================================================================
# 1. texture synthesis (numpy only, values are sRGB 0..1)
# =====================================================================
def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def vnoise(h, w, ch, cw, rng):
    """Tileable smooth value noise of size h x w with ch x cw lattice cells."""
    g = rng.random((ch, cw))
    y = np.arange(h) * ch / h
    x = np.arange(w) * cw / w
    y0 = np.floor(y).astype(int)
    x0 = np.floor(x).astype(int)
    fy = y - y0
    fx = x - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    y1 = (y0 + 1) % ch
    x1 = (x0 + 1) % cw
    y0 %= ch
    x0 %= cw
    a = g[np.ix_(y0, x0)]
    b = g[np.ix_(y0, x1)]
    c = g[np.ix_(y1, x0)]
    d = g[np.ix_(y1, x1)]
    fx = fx[None, :]
    fy = fy[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(h, w, ch, cw, octaves, rng, gain=0.5):
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for _ in range(octaves):
        if ch > h or cw > w:
            break
        out += amp * vnoise(h, w, ch, cw, rng)
        tot += amp
        amp *= gain
        ch *= 2
        cw *= 2
    return out / tot


def norm01(a):
    lo, hi = np.percentile(a, 1), np.percentile(a, 99)
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(t, stops):
    pos = np.array([p for p, _ in stops])
    cols = np.array([hexrgb(c) for _, c in stops])
    out = np.empty(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, pos, cols[:, c])
    return out


def mix(a, b, t):
    t = np.asarray(t)
    if t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def normal_map(hgt, strength):
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5 * strength
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5 * strength
    n = np.dstack([-dx, -dy, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def disc_stamps(h, w, n, rmin, rmax, rng):
    m = np.zeros((h, w))
    for _ in range(n):
        r = rng.uniform(rmin, rmax)
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        R = int(r) + 2
        ys = np.arange(int(cy) - R, int(cy) + R + 1)
        xs = np.arange(int(cx) - R, int(cx) + R + 1)
        d = np.sqrt((ys[:, None] + 0.5 - cy) ** 2 + (xs[None, :] + 0.5 - cx) ** 2)
        a = np.clip(r - d + 0.5, 0, 1)
        ix = np.ix_(ys % h, xs % w)
        m[ix] = np.maximum(m[ix], a)
    return m


class Canvas:
    """Premultiplied RGBA canvas for drawing leaves, flowers and needles."""

    def __init__(self, h, w, wrap=False):
        self.h, self.w, self.wrap = h, w, wrap
        self.c = np.zeros((h, w, 3))
        self.a = np.zeros((h, w))

    def over(self, y0, x0, alpha, rgb):
        hh, ww = alpha.shape
        ys = np.arange(y0, y0 + hh)
        xs = np.arange(x0, x0 + ww)
        rgb = np.broadcast_to(rgb, (hh, ww, 3)) if np.ndim(rgb) == 1 else rgb
        if self.wrap == 'x':
            xs = xs % self.w
            ky = (ys >= 0) & (ys < self.h)
            ys, alpha, rgb = ys[ky], alpha[ky], rgb[ky]
        elif self.wrap:
            ys, xs = ys % self.h, xs % self.w
        else:
            ky = (ys >= 0) & (ys < self.h)
            kx = (xs >= 0) & (xs < self.w)
            ys, xs = ys[ky], xs[kx]
            alpha = alpha[ky][:, kx]
            rgb = rgb[ky][:, kx]
        if ys.size == 0 or xs.size == 0:
            return
        ix = np.ix_(ys, xs)
        self.c[ix] = rgb * alpha[..., None] + self.c[ix] * (1 - alpha[..., None])
        self.a[ix] = alpha + self.a[ix] * (1 - alpha)

    def stamp(self, cx, cy, R, fn):
        x0, y0 = int(math.floor(cx - R)), int(math.floor(cy - R))
        n = int(2 * R) + 2
        ys, xs = np.mgrid[y0:y0 + n, x0:x0 + n].astype(float)
        a, rgb = fn(xs + 0.5 - cx, ys + 0.5 - cy)
        self.over(y0, x0, a, rgb)

    def rgba(self, fill=None):
        a = self.a[..., None]
        rgb = np.where(a > 1e-4, self.c / np.maximum(a, 1e-4), 0)
        if fill is None:
            fill = (self.c.sum((0, 1)) / max(self.a.sum(), 1e-4))
        rgb = np.where(a > 1e-4, rgb, fill)
        return np.dstack([np.clip(rgb, 0, 1), self.a])


def line_fn(dx, dy, w, rgb):
    """Segment from -d/2 to +d/2 (relative to stamp centre)."""
    L2 = dx * dx + dy * dy + 1e-9

    def f(xs, ys):
        t = np.clip(((xs + dx / 2) * dx + (ys + dy / 2) * dy) / L2, 0, 1)
        px, py = -dx / 2 + t * dx, -dy / 2 + t * dy
        d = np.hypot(xs - px, ys - py)
        return np.clip(w / 2 - d + 0.5, 0, 1), rgb
    return f


def draw_line(cv, x0, y0, x1, y1, w, rgb):
    cv.stamp((x0 + x1) / 2, (y0 + y1) / 2, math.hypot(x1 - x0, y1 - y0) / 2 + w + 1,
             line_fn(x1 - x0, y1 - y0, w, rgb))


def leaf_fn(L, W, ang, rgb, rng):
    """Broad leaf centred on the stamp, tip pointing to angle `ang` (0 = +y)."""
    ca, sa = math.cos(ang), math.sin(ang)
    lat = rng.uniform(0, 6.28)

    def f(xs, ys):
        along = xs * sa + ys * ca
        across = xs * ca - ys * sa
        u = along / L + 0.5
        uc = np.clip(u, 0, 1)
        halfw = 0.5 * W * np.sin(np.pi * uc) ** 0.8 * (1 - 0.25 * uc)
        dist = halfw - np.abs(across)
        a = np.clip(dist + 0.5, 0, 1) * ((u >= 0) & (u <= 1))
        pet = np.clip(1.2 - np.abs(across), 0, 1) * ((u < 0) & (u > -0.13))
        a = np.maximum(a, pet)
        mid = np.exp(-(across / 1.3) ** 2)
        lateral = 0.07 * np.cos((u * 9 - np.abs(across) / max(W, 1) * 5) * 6.283 + lat)
        shade = (0.82 + 0.28 * uc) * (1 - 0.2 * mid + lateral) * (0.88 + 0.12 * np.clip(dist / 3, 0, 1))
        return a, np.clip(rgb[None, None, :] * shade[..., None], 0, 1)
    return f


def maple_fn(R, ang, rgb, rng):
    ca, sa = math.cos(ang), math.sin(ang)
    blot = rng.uniform(0, 6.28)

    def f(xs, ys):
        xr = xs * ca - ys * sa
        yr = xs * sa + ys * ca
        th = np.arctan2(xr, yr)
        r = np.hypot(xr, yr) / R
        lob = ((np.cos(5 * th) + 1) / 2) ** 0.9
        shape = 0.52 + 0.48 * lob + 0.03 * np.cos(30 * th)
        shape = np.where(np.abs(th) > 2.7, shape * 0.55, shape)
        a = np.clip((shape - r) * R + 0.5, 0, 1)
        stem = np.clip(1.1 - np.abs(xr), 0, 1) * ((yr < 0) & (yr > -R * 1.15))
        a = np.maximum(a, stem)
        dth = np.abs(((th + np.pi / 5) % (2 * np.pi / 5)) - np.pi / 5)
        vein = np.clip(1.0 - dth * r * R / 1.1, 0, 1) * (r < shape * 0.92)
        tint = 0.9 + 0.12 * np.cos(r * 5 + th * 2 + blot)
        shade = tint * (1 - 0.25 * vein) * (0.86 + 0.14 * r)
        return a, np.clip(rgb[None, None, :] * shade[..., None], 0, 1)
    return f


def petals_fn(R, n, rot, petal_len, petal_w, col_out, col_in, center_col, center_r, notch=0.0):
    def f(xs, ys):
        r = np.hypot(xs, ys)
        a = np.zeros_like(xs)
        for k in range(n):
            t = rot + 2 * np.pi * k / n
            dx, dy = math.sin(t), math.cos(t)
            cxp, cyp = dx * R * (1 - petal_len / 2), dy * R * (1 - petal_len / 2)
            u = ((xs - cxp) * dx + (ys - cyp) * dy) / (R * petal_len / 2)
            v = ((xs - cxp) * dy - (ys - cyp) * dx) / (R * petal_w / 2)
            e = 1 - (u * u + v * v)
            pa = np.clip(e * R * petal_w / 3 + 0.5, 0, 1)
            if notch > 0:
                tipd = np.hypot(xs - dx * R, ys - dy * R)
                pa = pa * np.clip((tipd - notch * R) + 0.5, 0, 1)
            a = np.maximum(a, pa)
        t = np.clip(r / R, 0, 1)[..., None]
        rgb = col_in + (col_out - col_in) * t ** 0.6
        cen = np.clip(center_r * R - r + 0.5, 0, 1)
        a = np.maximum(a, cen)
        rgb = rgb * (1 - cen[..., None]) + center_col * cen[..., None]
        return a, rgb
    return f


def worley(h, w, ch, cw, rng, warp=None):
    """Tileable cellular noise: distance to nearest (F1) / second nearest (F2) feature point and cell id."""
    pts = rng.random((ch, cw, 2))
    Y, X = np.meshgrid((np.arange(h) + 0.5) * ch / h, (np.arange(w) + 0.5) * cw / w, indexing='ij')
    if warp is not None:
        Y, X = Y + warp[0], X + warp[1]
    iy, ix = np.floor(Y).astype(int), np.floor(X).astype(int)
    f1 = np.full((h, w), 9.0)
    f2 = np.full((h, w), 9.0)
    cid = np.zeros((h, w), dtype=np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cy, cx = iy + dy, ix + dx
            p = pts[cy % ch, cx % cw]
            d = np.hypot(cy + p[..., 0] - Y, cx + p[..., 1] - X)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, (cy % ch) * cw + (cx % cw), cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


def blur(a, r):
    """Cheap separable box blur (wraps around)."""
    out = a.copy()
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for k in range(-r, r + 1):
            acc += np.roll(out, k, axis)
        out = acc / (2 * r + 1)
    return out


def stone_fn(rx, ry, ang, rgb, rng, rough=0.12):
    """Rounded, irregular pebble lit from the upper left, centred on the stamp."""
    ca, sa = math.cos(ang), math.sin(ang)
    k = rng.uniform(0, 6.28)
    m = max(rx, ry)

    def f(xs, ys):
        u = (xs * ca + ys * sa) / rx
        v = (-xs * sa + ys * ca) / ry
        th = np.arctan2(v, u)
        rr = np.hypot(u, v) / (1 + rough * np.cos(3 * th + k) + rough * 0.5 * np.cos(5 * th + 2 * k))
        a = np.clip((1 - rr) * min(rx, ry) + 0.5, 0, 1)
        q = np.clip(rr, 0, 1)
        light = (-0.55 * xs + 0.65 * ys) / m
        shade = 0.82 + 0.38 * light - 0.3 * q ** 4
        grain = 0.92 + 0.16 * rng.random(xs.shape)
        return a, np.clip(rgb[None, None, :] * (shade * grain)[..., None], 0, 1)
    return f


def blob_fn(r, c, alpha=0.85, rim=0.25):
    def f(xs, ys):
        d = np.hypot(xs, ys)
        a = np.clip(r - d + 0.5, 0, 1) * alpha
        return a, np.clip(c[None, None, :] * (0.85 + rim * np.clip(d / r, 0, 1))[..., None], 0, 1)
    return f


def stones(h, w, n, rmin, rmax, cols, rng, ymin=0.0, ymax=1.0, flat=1.0, wrap=True):
    """Layer of n shaded stones (tileable by default); returns (rgb, alpha)."""
    cv = Canvas(h, w, wrap=wrap)
    for _ in range(n):
        r = rng.uniform(rmin, rmax)
        rx, ry = r * rng.uniform(0.8, 1.25), r * rng.uniform(0.6, 1.0) * flat
        c = hexrgb(cols[rng.integers(len(cols))]) * rng.uniform(0.85, 1.1)
        cv.stamp(rng.uniform(0, w), rng.uniform(ymin * h, ymax * h), max(rx, ry) * 1.3 + 2,
                 stone_fn(rx, ry, rng.uniform(-0.6, 0.6), c, rng))
    return cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a


def moss_over(rgb, hgt, coverage, rng):
    """Patchy moss layered over an existing square texture."""
    n = hgt.shape[0]
    mrgb, mh = tex_moss(n, rng=rng)
    mask = norm01(fbm(n, n, 6, 6, 5, rng) * 0.7 + vnoise(n, n, 64, 64, rng) * 0.3)
    m = sstep(1 - coverage - 0.06, 1 - coverage + 0.06, mask)
    m = np.clip(m * (0.75 + 0.5 * vnoise(n, n, 256, 256, rng)), 0, 1)
    return mix(rgb, mrgb, m), hgt * (1 - m) + (0.6 + mh * 0.6) * m


def tex_ground(season, n=1024, seed=1):
    rng = np.random.default_rng(seed)
    big = norm01(fbm(n, n, 4, 4, 5, rng))
    mid = norm01(fbm(n, n, 16, 16, 4, rng))
    fine = norm01(vnoise(n, n, 256, 256, rng) * 0.6 + vnoise(n, n, 512, 512, rng) * 0.4)
    blades = norm01(vnoise(n, n, 512, 128, rng) + vnoise(n, n, 128, 512, rng))
    if season == "Winter":
        hgt = big * 0.55 + mid * 0.35 + fine * 0.1
        rgb = ramp(hgt, [(0, "#B7C6DA"), (0.45, "#DCE5F0"), (0.75, "#EEF3F9"), (1, "#FAFCFE")])
        sp = disc_stamps(n, n, 2500, 0.4, 0.9, rng)
        rgb = mix(rgb, np.array([1.0, 1.0, 1.0]), sp * 0.8)
        dirt = disc_stamps(n, n, 140, 0.8, 2.2, rng) * (big < 0.35)
        rgb = mix(rgb, hexrgb("#6E6656"), dirt * 0.7)
        return rgb, hgt
    pal = {
        "Spring": (["#355A1E", "#5B8B2C", "#8DB955"], ["#4A3524", "#7A5A3E"], 0.14),
        "Summer": (["#24461A", "#3F7326", "#6E9E3E"], ["#46331F", "#6E5236"], 0.08),
        "Autumn": (["#5A5428", "#968642", "#C9B068"], ["#4E3826", "#7C5B3D"], 0.28),
    }[season]
    g, s, soil_amt = pal
    soil = sstep(soil_amt + 0.12, soil_amt - 0.05, big * 0.65 + mid * 0.35)
    gcol = ramp(norm01(mid * 0.35 + fine * 0.35 + blades * 0.3), [(0, g[0]), (0.55, g[1]), (1, g[2])])
    f1, f2, _ = worley(n, n, 160, 160, rng)
    clods = norm01(f1)
    scol = ramp(norm01(fine * 0.4 + mid * 0.3 + (1 - clods) * 0.5), [(0, "#2E2118"), (0.45, s[0]), (1, s[1])])
    scol *= (0.8 + 0.25 * sstep(0.0, 0.25, f2 - f1))[..., None]
    rgb = mix(gcol, scol, soil * 0.92)
    prgb, pa = stones(n, n, 700, 1.2, 4.5, ["#8C8478", "#9E968A", "#6F685E", "#B0A796", "#7D6A58"], rng)
    pa = pa * sstep(0.15, 0.6, soil)
    ring = np.clip(blur(pa, 2) - pa, 0, 1)
    rgb = rgb * (1 - 0.4 * ring[..., None])
    rgb = mix(rgb, prgb, pa)
    hgt = (fine * 0.3 + blades * 0.3 * (1 - soil) + mid * 0.25 - soil * 0.2 + (1 - clods) * 0.15 * soil
           + blur(pa, 1) * 0.5)
    if season == "Spring":
        for c, k in (("#F4F1E6", 260), ("#F2CB2E", 160)):
            fl = disc_stamps(n, n, k, 0.9, 1.6, rng) * (1 - soil)
            rgb = mix(rgb, hexrgb(c), fl)
    if season == "Autumn":
        cv = Canvas(n, n, wrap=True)
        for _ in range(1800):
            colr = hexrgb(["#C4501E", "#D9822B", "#E8B03A", "#8A4A22", "#A8361C"][rng.integers(5)])
            L = rng.uniform(5, 11)
            cv.stamp(rng.uniform(0, n), rng.uniform(0, n), L,
                     leaf_fn(L, L * 0.6, rng.uniform(0, 6.28), colr * rng.uniform(0.8, 1.05), rng))
        rgb = mix(rgb, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a * 0.9)
        hgt = hgt + cv.a * 0.2
    return np.clip(rgb, 0, 1), hgt


def tex_soil(w=1024, h=832, seed=2):
    """Soil profile for the tile sides, bottom -> top: weathered rock (C), clay (B), loam (A), organic (O)."""
    rng = np.random.default_rng(seed)
    tt = ((np.arange(h) / h)[:, None] + (vnoise(h, w, 3, 6, rng) - 0.5) * 0.06
          + (vnoise(h, w, 12, 24, rng) - 0.5) * 0.02)
    bC = sstep(0.26, 0.2, tt)
    bO = sstep(0.86, 0.9, tt)
    bA = sstep(0.6, 0.66, tt) * (1 - bO)
    bB = np.clip(1 - bC - bA - bO, 0, 1)
    crumb = norm01(vnoise(h, w, 160, 192, rng) * 0.5 + vnoise(h, w, 400, 480, rng) * 0.5)
    lam = vnoise(h, w, 90, 6, rng)
    mott = sstep(0.62, 0.75, norm01(fbm(h, w, 12, 14, 4, rng)))
    colB = ramp(norm01(crumb * 0.5 + lam * 0.5), [(0, "#62432F"), (0.5, "#775239"), (1, "#8B6445")])
    colB = mix(colB, hexrgb("#9C6A42"), mott * 0.45)
    gley = sstep(0.7, 0.82, norm01(fbm(h, w, 10, 12, 3, rng)))
    colB = mix(colB, hexrgb("#8A8072"), gley * 0.35)
    colA = ramp(crumb, [(0, "#2E2119"), (0.5, "#3F2E21"), (1, "#54402D")])
    colO = ramp(crumb, [(0, "#1C140F"), (0.6, "#2A1E15"), (1, "#3A2B1E")])
    warp = ((vnoise(h, w, 6, 8, rng) - 0.5) * 1.2, (vnoise(h, w, 6, 8, rng) - 0.5) * 1.2)
    f1, f2, cid = worley(h, w, 18, 22, rng, warp)
    blockv = rng.random(18 * 22)[cid]
    jw = 0.04 + 0.16 * vnoise(h, w, 10, 12, rng)
    joint = sstep(0.0, 1.0, (f2 - f1) / jw)
    rockc = ramp(norm01(blockv * 0.6 + crumb * 0.4), [(0, "#6E675C"), (0.5, "#8A8273"), (1, "#A39A88")])
    rockc = rockc * (1.08 - 0.3 * norm01(f1))[..., None]
    fill = ramp(crumb, [(0, "#4A3729"), (1, "#6B5039")])
    colC = mix(fill, rockc, joint)
    rgb = colC * bC[..., None] + colB * bB[..., None] + colA * bA[..., None] + colO * bO[..., None]
    rgb *= (0.88 + 0.22 * crumb)[..., None]
    rgb *= (1 - 0.35 * disc_stamps(h, w, 3500, 0.5, 1.3, rng))[..., None]
    hgt = crumb * 0.25 - (1 - joint) * 0.3 * bC + lam * 0.1 * bB
    for n_, r0, r1, y0, y1, cols in ((60, 14, 34, 0.0, 0.3, ["#8E877C", "#A39B8E", "#77706A", "#B0A595"]),
                                      (170, 4, 13, 0.18, 0.64, ["#8A8378", "#9C9384", "#6E675F", "#A68E72", "#B8AE9C"]),
                                      (260, 1.5, 5, 0.55, 0.9, ["#7A7368", "#8E8678", "#5E5850"])):
        srgb, sa = stones(h, w, n_, r0, r1, cols, rng, ymin=y0, ymax=y1, flat=0.8, wrap='x')
        ring = np.clip(blur(sa, 3) - sa, 0, 1)
        rgb = rgb * (1 - 0.45 * ring[..., None])
        rgb = mix(rgb, srgb, sa)
        hgt = hgt + blur(sa, 2) * 0.8
    cv = Canvas(h, w, wrap='x')
    for _ in range(26):
        x, y = rng.uniform(0, w), h - rng.uniform(0, 12)
        wdt = rng.uniform(2.0, 4.0)
        ang = rng.uniform(-0.5, 0.5)
        while y > h * 0.45 and wdt > 0.6:
            ang = float(np.clip(ang + rng.normal(0, 0.35), -1.1, 1.1))
            L = rng.uniform(8, 18)
            nx, ny = x + math.sin(ang) * L, y - math.cos(ang) * L
            draw_line(cv, x, y, nx, ny, wdt, hexrgb("#7A5C42") * rng.uniform(0.85, 1.1))
            if rng.random() < 0.25:
                a2 = ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.2)
                draw_line(cv, nx, ny, nx + math.sin(a2) * L * 1.2, ny - math.cos(a2) * L * 1.2,
                          max(wdt * 0.5, 0.8), hexrgb("#6E5240"))
            x, y = nx, ny
            wdt *= 0.93
    for _ in range(420):
        x, y = rng.uniform(0, w), rng.uniform(h * 0.7, h)
        a = rng.uniform(-2.6, 2.6)
        L = rng.uniform(4, 14)
        draw_line(cv, x, y, x + math.sin(a) * L, y - abs(math.cos(a)) * L, rng.uniform(0.7, 1.2), hexrgb("#8A6A4E"))
    rgb = mix(rgb, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a * 0.9)
    hgt = hgt + cv.a * 0.35
    rgb = mix(rgb, hexrgb("#2F3A1E"), sstep(0.95, 1.0, tt) * 0.5)
    return np.clip(rgb, 0, 1), hgt


def tex_bark_cherry(n=512, seed=3):
    rng = np.random.default_rng(seed)
    bands = norm01(vnoise(n, n, 6, 48, rng) * 0.6 + vnoise(n, n, 24, 128, rng) * 0.4)
    rgb = ramp(bands, [(0, "#3A2620"), (0.5, "#5E3E33"), (1, "#7A5547")])
    cv = Canvas(n, n, wrap=True)
    for _ in range(520):
        x, y, L = rng.uniform(0, n), rng.uniform(0, n), rng.uniform(6, 22)
        draw_line(cv, x - L / 2, y, x + L / 2, y, rng.uniform(1.5, 3.2), hexrgb("#9C7E6C") * rng.uniform(0.85, 1.1))
    rgb = mix(rgb, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a * 0.85)
    crack = norm01(vnoise(n, n, 64, 10, rng))
    rgb *= (0.8 + 0.2 * sstep(0.1, 0.35, crack))[..., None]
    hgt = bands * 0.4 + cv.a * 0.5 + sstep(0.1, 0.35, crack) * 0.3
    return np.clip(rgb, 0, 1), hgt


def tex_bark_spruce(n=512, seed=4):
    rng = np.random.default_rng(seed)
    flakes = vnoise(n, n, 40, 24, rng)
    ridge = 1 - np.abs(2 * vnoise(n, n, 12, 32, rng) - 1)
    t = norm01(flakes * 0.6 + ridge * 0.4)
    rgb = ramp(t, [(0, "#2E241C"), (0.4, "#4F4134"), (0.75, "#6E5E4E"), (1, "#8A7B6B")])
    rgb *= (0.85 + 0.25 * vnoise(n, n, 128, 128, rng))[..., None]
    return np.clip(rgb, 0, 1), t


def tex_rock(n=1024, seed=5):
    """Weathered granite: mineral grains, rain streaks, fine cracks and crustose lichen."""
    rng = np.random.default_rng(seed)
    tone = norm01(fbm(n, n, 3, 3, 6, rng))
    base = ramp(tone, [(0, "#5C5853"), (0.5, "#85807A"), (1, "#A8A39B")])
    f1, f2, cid = worley(n, n, 150, 150, rng)
    pal = [("#C2BDB5", 0.48), ("#928D85", 0.27), ("#B59C8E", 0.13), ("#3A3633", 0.12)]
    cum = np.cumsum([p for _, p in pal])
    idx = np.clip(np.searchsorted(cum, rng.random(150 * 150)), 0, len(pal) - 1)[cid]
    gcol = np.array([hexrgb(c) for c, _ in pal])[idx]
    grain_edge = sstep(0.0, 0.06, f2 - f1)
    gcol = gcol * (0.8 + 0.2 * grain_edge)[..., None]
    rgb = mix(base, gcol * (0.6 + 0.6 * tone)[..., None], 0.34)
    streak = norm01(vnoise(n, n, 5, 40, rng) * 0.6 + vnoise(n, n, 12, 90, rng) * 0.4)
    rgb *= (0.82 + 0.22 * streak)[..., None]
    warp = ((norm01(fbm(n, n, 4, 4, 4, rng)) - 0.5) * 0.9, (norm01(fbm(n, n, 4, 4, 4, rng)) - 0.5) * 0.9)
    rf1, rf2, _ = worley(n, n, 4, 4, rng, warp)
    keep = sstep(0.45, 0.6, norm01(fbm(n, n, 3, 3, 3, rng)))
    crack = (1 - sstep(0.0, 0.02, rf2 - rf1)) * keep
    halo = (1 - sstep(0.0, 0.08, rf2 - rf1)) * keep
    rgb *= (1 - 0.25 * halo)[..., None]
    rgb = mix(rgb, hexrgb("#1E1C1A"), crack * 0.85)
    cv = Canvas(n, n, wrap=True)
    lich = ["#A9B39A", "#B8BEA4", "#9EA88E", "#C9C27E", "#C7883C"]
    for _ in range(46):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        col = hexrgb(lich[min(int(rng.random() ** 2.5 * 5), 4)])
        for _k in range(int(rng.integers(12, 34))):
            r = rng.uniform(3, 11)
            cv.stamp(cx + rng.normal(0, 16), cy + rng.normal(0, 16), r + 2, blob_fn(r, col * rng.uniform(0.9, 1.05)))
    rgb = mix(rgb, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a)
    hgt = (tone * 0.4 + grain_edge * 0.08 - crack * 0.6 - halo * 0.15 + cv.a * 0.12
           + vnoise(n, n, 256, 256, rng) * 0.15)
    return np.clip(rgb, 0, 1), hgt


def tex_wood(n=512, seed=6):
    rng = np.random.default_rng(seed)
    grain = norm01(vnoise(n, n, 96, 3, rng) * 0.5 + vnoise(n, n, 256, 6, rng) * 0.3 + vnoise(n, n, 24, 2, rng) * 0.2)
    rgb = ramp(grain, [(0, "#3F362D"), (0.45, "#6B5D4E"), (0.8, "#8D7F6E"), (1, "#A89A88")])
    knots = disc_stamps(n, n, 6, 4, 9, rng)
    rgb = mix(rgb, hexrgb("#2E251D"), knots * 0.8)
    return np.clip(rgb, 0, 1), grain - knots * 0.3


def tex_moss(n=512, seed=7, rng=None):
    rng = rng if rng is not None else np.random.default_rng(seed)
    t = norm01(fbm(n, n, 8, 8, 5, rng) * 0.5 + vnoise(n, n, 256, 256, rng) * 0.5)
    tuft = norm01(vnoise(n, n, n // 4, n // 4, rng))
    rgb = ramp(t, [(0, "#22351A"), (0.5, "#3E5A28"), (1, "#6E8A3A")])
    rgb *= (0.8 + 0.35 * tuft)[..., None]
    return np.clip(rgb, 0, 1), t * 0.6 + tuft * 0.4


def tex_ice(n=512, seed=8):
    rng = np.random.default_rng(seed)
    t = norm01(fbm(n, n, 4, 4, 5, rng))
    rgb = ramp(t, [(0, "#7FA6BF"), (0.5, "#A9CBDD"), (1, "#D5E8F2")])
    ridge = 1 - np.abs(2 * fbm(n, n, 4, 4, 3, rng) - 1)
    crack = sstep(0.95, 0.99, ridge)
    rgb = mix(rgb, hexrgb("#F2FAFF"), crack * 0.8)
    frost = sstep(0.55, 0.85, norm01(fbm(n, n, 6, 6, 5, rng)))
    rgb = mix(rgb, hexrgb("#EEF4F8"), frost * 0.75)
    return np.clip(rgb, 0, 1), t * 0.3 + crack * 0.4 + frost * 0.3


def tex_water_normal(n=256, seed=9):
    rng = np.random.default_rng(seed)
    return normal_map(fbm(n, n, 8, 8, 4, rng), 6.0)


def tex_leaf_atlas(kind, n=1024, seed=10):
    """2 x 2 atlas of leaf / blossom clusters with alpha (cells of n/2)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(n, n)
    c = n // 2
    for cell in range(4):
        ox, oy = (cell % 2) * c, (cell // 2) * c
        # twig: from bottom centre up into the cell
        tx0, ty0 = ox + c * 0.5, oy + c * 0.04
        tx1, ty1 = ox + c * rng.uniform(0.4, 0.6), oy + c * 0.8
        twig_col = hexrgb("#4A3328")
        if kind == "Spring":
            leaves = 6
            for _ in range(int(rng.integers(30, 40))):
                r = rng.uniform(30, 44)
                x, y = ox + rng.uniform(r + 4, c - r - 4), oy + rng.uniform(c * 0.2, c - r - 4)
                cv.stamp(x, y, r + 2, petals_fn(r, 5, rng.uniform(0, 1.3), 0.92, 0.66,
                                                 hexrgb("#F9D3E0") * rng.uniform(0.95, 1.0), hexrgb("#E27FA6"),
                                                 hexrgb("#C9A04A"), 0.16, notch=0.08))
            draw_line(cv, tx0, ty0, tx1, ty1, 4, twig_col)
            for _ in range(leaves):
                L = rng.uniform(70, 100)
                ang = rng.uniform(-1.6, 1.6)
                x = ox + c * 0.5 + math.sin(ang) * L * 0.6
                y = oy + c * rng.uniform(0.25, 0.75) + math.cos(ang) * L * 0.4
                cv.stamp(x, y, L * 0.6 + 6, leaf_fn(L, L * 0.42, ang, hexrgb("#7E8F3A") * rng.uniform(0.85, 1.1), rng))
        elif kind == "Summer":
            draw_line(cv, tx0, ty0, tx1, ty1, 4, twig_col)
            for _ in range(int(rng.integers(26, 34))):
                L = rng.uniform(110, 160)
                ang = rng.uniform(-2.4, 2.4)
                bx, by = tx0 + (tx1 - tx0) * rng.uniform(0.1, 1), ty0 + (ty1 - ty0) * rng.uniform(0.1, 1)
                x, y = bx + math.sin(ang) * L * 0.5, by + math.cos(ang) * L * 0.5
                colr = hexrgb(["#2F5A22", "#3E6B2A", "#4F7F32", "#5C8A3A", "#36622A"][rng.integers(5)])
                cv.stamp(x, y, L * 0.6 + 6, leaf_fn(L, L * 0.45, ang, colr * rng.uniform(0.85, 1.12), rng))
        else:  # Autumn maple
            draw_line(cv, tx0, ty0, tx1, ty1, 4, twig_col)
            for _ in range(int(rng.integers(11, 16))):
                R = rng.uniform(55, 80)
                ang = rng.uniform(-2.2, 2.2)
                bx, by = tx0 + (tx1 - tx0) * rng.uniform(0.1, 1), ty0 + (ty1 - ty0) * rng.uniform(0.1, 1)
                x = np.clip(bx + math.sin(ang) * R, ox + R, ox + c - R)
                y = np.clip(by + math.cos(ang) * R, oy + R, oy + c - R)
                colr = hexrgb(["#C8361C", "#DD5A1E", "#E8862A", "#F0AE38", "#B82A1E", "#D4A22E"][rng.integers(6)])
                cv.stamp(x, y, R * 1.3, maple_fn(R, ang, colr * rng.uniform(0.85, 1.08), rng))
    return cv.rgba()


def tex_frond(snow=False, w=512, h=512, seed=11):
    """Spruce branch sprays; atlas of two 256 x 512 cells, branch axis along +y."""
    rng = np.random.default_rng(seed)
    cv = Canvas(h, w)
    cw = w // 2
    for cell in range(2):
        ox = cell * cw
        axis_x = ox + cw / 2

        def needles_along(x0, y0, x1, y1, step, nl, tipcol):
            L = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            k = 0
            for s in np.arange(0, L, step):
                px, py = x0 + ux * s, y0 + uy * s
                f = s / L
                for side in (-1, 1):
                    a = side * rng.uniform(0.8, 1.1)
                    dx = ux * math.cos(a) - uy * math.sin(a)
                    dy = ux * math.sin(a) + uy * math.cos(a)
                    ln = nl * rng.uniform(0.8, 1.15) * (1 - 0.35 * f)
                    col = hexrgb("#2C4A28") * rng.uniform(0.75, 1.2)
                    if f > 0.8:
                        col = col * 0.6 + tipcol * 0.4
                    draw_line(cv, px, py, px + dx * ln, py + dy * ln, rng.uniform(1.4, 2.0), col)
                k += 1
        draw_line(cv, axis_x, 6, axis_x, h - 8, 3.5, hexrgb("#4A3A2C"))
        needles_along(axis_x, 6, axis_x, h - 8, 3.2, 15, hexrgb("#6E9A45"))
        y = 40
        side = 1
        while y < h - 60:
            L = (h - y) * 0.3 * rng.uniform(0.8, 1.1) + 20
            ang = 0.85 * side
            x1 = axis_x + math.sin(ang) * L
            y1 = y + math.cos(ang) * L
            x1 = float(np.clip(x1, ox + 14, ox + cw - 14))
            draw_line(cv, axis_x, y, x1, y1, 2.2, hexrgb("#4A3A2C"))
            needles_along(axis_x, y, x1, y1, 3.0, 12, hexrgb("#6E9A45"))
            y += rng.uniform(26, 38)
            side = -side
    if snow:
        base_a = cv.a.copy()
        sc = Canvas(h, w)
        for _ in range(320):
            x, y = rng.uniform(10, w - 10), rng.uniform(10, h - 10)
            if base_a[int(y), int(x)] < 0.5:
                continue
            r = rng.uniform(9, 22)
            sc.stamp(x, y, r + 2, lambda xs, ys, r=r: (np.clip(r - np.hypot(xs, ys * 1.3) + 0.5, 0, 1),
                                                       np.array([0.94, 0.96, 1.0]) * (0.92 + 0.08 * np.clip(ys / r, -1, 1))[..., None]))
        a = sc.a * np.clip(base_a * 1.5, 0, 1)
        cv.c = cv.c * (1 - a[..., None]) + sc.c / np.maximum(sc.a[..., None], 1e-4) * a[..., None] * cv.a[..., None]
    return cv.rgba()


def tex_grass_atlas(season, n=128, seed=12):
    rng = np.random.default_rng(seed)
    pals = {
        "Spring": [["#2E4B1C", "#5E8F2E", "#A3C962"], ["#2A4419", "#527F28", "#8DB653"],
                   ["#34521F", "#6A9A34", "#B2D06E"], ["#2B4A1D", "#4F7A2A", "#86AE4E"]],
        "Summer": [["#1E3A16", "#3B6E24", "#73A146"], ["#22401A", "#447A2A", "#7FAA4A"],
                   ["#1C3614", "#356421", "#679440"], ["#25441B", "#4C7F2E", "#8CB352"]],
        "Autumn": [["#4A4822", "#958840", "#D2BB6C"], ["#3E4420", "#7E7E3A", "#BDB062"],
                   ["#524A24", "#A48C44", "#DCC27A"], ["#384A20", "#6A7C34", "#A8AC5A"]],
        "Winter": [["#4E4230", "#9A845A", "#D6C49A"], ["#5A4C36", "#A89068", "#E0D0A8"],
                   ["#463C2C", "#8C7A54", "#C8B68C"], ["#544632", "#9E8A60", "#D2C094"]],
    }[season]
    cols = []
    cw = n // 4
    v = np.linspace(0, 1, n)[:, None]
    for k in range(4):
        p = pals[k]
        g = ramp(np.repeat(v, cw, 1), [(0, p[0]), (0.45, p[1]), (1, p[2])])
        u = np.linspace(-1, 1, cw)[None, :]
        g *= (0.9 + 0.12 * (1 - np.abs(u)) + 0.05 * rng.standard_normal((1, cw)))[..., None]
        cols.append(g)
    return np.clip(np.concatenate(cols, axis=1), 0, 1)


def tex_flowers(n=512, seed=13):
    rng = np.random.default_rng(seed)
    cv = Canvas(n, n)
    c = n // 2
    R = c * 0.42
    specs = [
        (18, 0.76, 0.17, "#FBFAF4", "#EDEBDF", "#F0B323", 0.24, 0.0),   # daisy
        (34, 0.75, 0.10, "#F9D23C", "#E9A514", "#E39A10", 0.12, 0.0),   # dandelion
        (5, 0.95, 0.72, "#8A5CC4", "#4E2683", "#F2F0E6", 0.1, 0.0),     # violet
        (5, 0.95, 0.78, "#F7D51E", "#E0A90C", "#A8B33A", 0.14, 0.0),    # buttercup
    ]
    for cell, (k, pl, pw, co, ci, cc, cr, nt) in enumerate(specs):
        cx, cy = (cell % 2) * c + c / 2, (cell // 2) * c + c / 2
        cv.stamp(cx, cy, R + 3, petals_fn(R, k, rng.uniform(0, 1), pl, pw, hexrgb(co), hexrgb(ci), hexrgb(cc), cr, nt))
    return cv.rgba()


def tex_litter(n=512, seed=14):
    """4 x 4 atlas of single fallen leaves."""
    rng = np.random.default_rng(seed)
    cv = Canvas(n, n)
    c = n // 4
    for cell in range(16):
        cx, cy = (cell % 4) * c + c / 2, (cell // 4) * c + c / 2
        colr = hexrgb(["#C8361C", "#DD5A1E", "#E8862A", "#F0AE38", "#8A5A2A", "#6E4A2A", "#B82A1E", "#C9A030"][cell % 8])
        if cell % 3 == 2:
            cv.stamp(cx, cy, c * 0.5, leaf_fn(c * 0.8, c * 0.42, 0.0, colr * rng.uniform(0.85, 1.05), rng))
        else:
            cv.stamp(cx, cy, c * 0.5, maple_fn(c * 0.36, 0.0, colr * rng.uniform(0.85, 1.05), rng))
    return cv.rgba()


def tex_petal(n=64):
    cv = Canvas(n, n)
    cv.stamp(n / 2, n / 2, n / 2, petals_fn(n * 0.45, 1, 0.0, 1.9, 0.75, hexrgb("#F9D3E0"), hexrgb("#E890B2"),
                                              hexrgb("#F3B3C8"), 0.0, notch=0.06))
    return cv.rgba()


# =====================================================================
# 2. Blender helpers
# =====================================================================
def to_lin(rgb):
    rgb = np.asarray(rgb, dtype=float)
    return tuple(np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4))


def make_image(name, arr, non_color=False):
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.ones((h, w))])
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, w, h, alpha=True)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.pack()
    return img


def mat_tex(name, img, nrm=None, nrm_strength=1.0, rough=0.8, spec=0.5, alpha=False, coat=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    t = N.new('ShaderNodeTexImage')
    t.image = bpy.data.images[img]
    t.location = (-500, 200)
    Lk.new(t.outputs['Color'], b.inputs['Base Color'])
    if alpha:
        r = N.new('ShaderNodeMath')
        r.operation = 'ROUND'
        Lk.new(t.outputs['Alpha'], r.inputs[0])
        Lk.new(r.outputs[0], b.inputs['Alpha'])
        m.surface_render_method = 'DITHERED'
        m.use_transparent_shadow = True
    if nrm:
        t2 = N.new('ShaderNodeTexImage')
        t2.image = bpy.data.images[nrm]
        t2.location = (-700, -200)
        nm = N.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = nrm_strength
        Lk.new(t2.outputs['Color'], nm.inputs['Color'])
        Lk.new(nm.outputs['Normal'], b.inputs['Normal'])
    m.use_backface_culling = False
    m.use_fake_user = True
    px = bpy.data.images[img].pixels
    m.diffuse_color = (0.5, 0.5, 0.5, 1.0) if len(px) == 0 else (*to_lin(np.array(px[:3])), 1.0)
    return m


def mat_solid(name, hexc, rough=0.6, spec=0.5, coat=0.0, nrm=None, nrm_strength=0.3):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    col = (*to_lin(hexrgb(hexc)), 1.0)
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    if nrm:
        t2 = nt.nodes.new('ShaderNodeTexImage')
        t2.image = bpy.data.images[nrm]
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = nrm_strength
        nt.links.new(t2.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = col
    m.use_backface_culling = False
    m.use_fake_user = True
    return m


def M(name):
    return bpy.data.materials[name]


class MB:
    """Tiny mesh builder: vertices, faces with per-corner UVs, material index and smooth flag."""

    def __init__(self):
        self.v, self.f, self.uv, self.mi, self.sm, self.vn = [], [], [], [], [], []

    def vert(self, co, nrm=None):
        self.v.append((co[0], co[1], co[2]))
        self.vn.append(nrm)
        return len(self.v) - 1

    def face(self, idx, uvs, mat=0, smooth=True):
        self.f.append(tuple(idx))
        self.uv.extend(uvs)
        self.mi.append(mat)
        self.sm.append(smooth)

    def box(self, center, half, rot, side_mat, top_mat, uvscale=1.0):
        c = Vector(center)
        corners = []
        for z in (-1, 1):
            for y in (-1, 1):
                for x in (-1, 1):
                    corners.append(c + rot @ Vector((x * half[0], y * half[1], z * half[2])))
        ids = [self.vert(p) for p in corners]
        quads = [((0, 2, 3, 1), 'z-'), ((4, 5, 7, 6), 'z+'), ((0, 1, 5, 4), 'y-'),
                 ((2, 6, 7, 3), 'y+'), ((0, 4, 6, 2), 'x-'), ((1, 3, 7, 5), 'x+')]
        for q, ax in quads:
            loc = [Vector(((k & 1) * 2 - 1, ((k >> 1) & 1) * 2 - 1, ((k >> 2) & 1) * 2 - 1)) for k in q]
            if ax[0] == 'z':
                uvs = [(l.x * half[0] * uvscale, l.y * half[1] * uvscale) for l in loc]
            elif ax[0] == 'y':
                uvs = [(l.x * half[0] * uvscale, l.z * half[2] * uvscale) for l in loc]
            else:
                uvs = [(l.y * half[1] * uvscale, l.z * half[2] * uvscale) for l in loc]
            self.face([ids[k] for k in q], uvs, top_mat if ax == 'z+' else side_mat, False)

    def build(self, name, mats, custom_normals=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", [c for uv in self.uv for c in uv])
        me.polygons.foreach_set("material_index", self.mi)
        me.polygons.foreach_set("use_smooth", self.sm)
        for m in mats:
            me.materials.append(m)
        me.update()
        if custom_normals:
            me.normals_split_custom_set_from_vertices([n if n is not None else (0, 0, 1) for n in self.vn])
        return me


def link_obj(name, me, coll, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def add_tube(mb, pts, rad, sides, mat, v_scale=0.5, u_tile=0.5, top_mat=None, top_thresh=0.5, cap=False):
    t0 = (pts[1] - pts[0]).normalized()
    nrm = t0.orthogonal().normalized()
    prev_t = t0
    rings = []
    vacc = 0.0
    u_rep = max(1, round(2 * math.pi * rad[0] / u_tile))
    for i, p in enumerate(pts):
        if i == 0:
            t = t0
        elif i == len(pts) - 1:
            t = (pts[i] - pts[i - 1]).normalized()
        else:
            t = (pts[i + 1] - pts[i - 1]).normalized()
        nrm = prev_t.rotation_difference(t) @ nrm
        nrm = (nrm - t * nrm.dot(t)).normalized()
        prev_t = t
        bn = t.cross(nrm)
        if i > 0:
            vacc += (pts[i] - pts[i - 1]).length
        ring = []
        for j in range(sides + 1):
            a = 2 * math.pi * j / sides
            off = (nrm * math.cos(a) + bn * math.sin(a)) * rad[i]
            ring.append((mb.vert(p + off), (j / sides * u_rep, vacc / v_scale), off))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(sides):
            a, b, c, d = rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]
            mi = mat
            if top_mat is not None:
                s = a[2] + b[2] + c[2] + d[2]
                if s.length > 1e-9 and s.normalized().z > top_thresh:
                    mi = top_mat
            mb.face((a[0], b[0], c[0], d[0]), (a[1], b[1], c[1], d[1]), mi)
    return rings


def smooth01(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def height(x, y):
    n = noise.fractal(Vector((x * 0.32 + 11.0, y * 0.32 + 5.0, 0.7)), 0.55, 2.0, 5)
    h = 0.16 + 0.055 * n
    h += 0.32 * math.exp(-((x - TREE_P[0]) ** 2 + (y - TREE_P[1]) ** 2) / 2.4)
    dx, dy = x - POND_C[0], y - POND_C[1]
    ang = math.atan2(dy, dx)
    rr = math.hypot(dx, dy) / (1 + 0.13 * math.sin(3 * ang + 0.7) + 0.07 * math.sin(5 * ang + 2.1))
    h -= 0.7 * smooth01(POND_R, 0.45, rr)
    return h


def ground_z(x, y, season):
    return height(x, y) + (0.05 if season == "Winter" else 0.0)


def excluded(x, y, pad=0.0):
    if height(x, y) < WATER_Z + 0.03:
        return True
    for (rx, ry), d, _ in ROCKS:
        if ((x - rx) / (d[0] + pad)) ** 2 + ((y - ry) / (d[1] + pad)) ** 2 < 1:
            return True
    if (x - TREE_P[0]) ** 2 + (y - TREE_P[1]) ** 2 < 0.09:
        return True
    (lx, ly), lr, ll, lrad = LOG
    u = (x - lx) * math.cos(lr) + (y - ly) * math.sin(lr)
    v = -(x - lx) * math.sin(lr) + (y - ly) * math.cos(lr)
    if abs(u) < ll / 2 and abs(v) < lrad + pad:
        return True
    return False


def season_root(S):
    coll = bpy.data.collections.get(S)
    if coll is None:
        coll = bpy.data.collections.new(S)
        bpy.context.scene.collection.children.link(coll)
    root = bpy.data.objects.get(f"{S}_Tile")
    if root is None:
        root = bpy.data.objects.new(f"{S}_Tile", None)
        root.empty_display_type = 'PLAIN_AXES'
        root.empty_display_size = 1.0
        coll.objects.link(root)
        root.location = (*GRID[S], 0)
    return coll, root


# =====================================================================
# 3. stages
# =====================================================================
def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for dc in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.curves):
        for b in list(dc):
            dc.remove(b)
    for img in list(bpy.data.images):
        if img.type == 'IMAGE':
            bpy.data.images.remove(img)
    for ng in list(bpy.data.node_groups):
        if ng.users == 0:
            bpy.data.node_groups.remove(ng)


def stage_textures():
    for i, S in enumerate(SEASONS):
        rgb, hgt = tex_ground(S, 1024, seed=100 + i)
        make_image(f"T_Ground_{S}", rgb)
        make_image(f"N_Ground_{S}", normal_map(hgt[::2, ::2], 3.0 if S != "Winter" else 1.5), True)
    rgb, hgt = tex_soil()
    make_image("T_Soil", rgb)
    make_image("N_Soil", normal_map(hgt, 6.0), True)
    for nm, fn in (("BarkCherry", tex_bark_cherry), ("BarkSpruce", tex_bark_spruce), ("Wood", tex_wood),
                   ("Moss", tex_moss), ("Ice", tex_ice)):
        rgb, hgt = fn()
        make_image(f"T_{nm}", rgb)
        make_image(f"N_{nm}", normal_map(hgt, 5.0), True)
    rgb, hgt = tex_rock()
    make_image("T_Rock", rgb)
    make_image("N_Rock", normal_map(hgt[::2, ::2], 4.0), True)
    rgb, hgt = moss_over(rgb, hgt, 0.5, np.random.default_rng(55))
    make_image("T_RockMoss", rgb)
    make_image("N_RockMoss", normal_map(hgt[::2, ::2], 4.0), True)
    rgb, hgt = moss_over(*tex_bark_spruce(), 0.55, np.random.default_rng(56))
    make_image("T_LogMoss", rgb)
    make_image("N_LogMoss", normal_map(hgt, 5.0), True)
    make_image("N_Water", tex_water_normal(), True)
    for S in ("Spring", "Summer", "Autumn"):
        make_image(f"T_Leaves_{S}", tex_leaf_atlas(S, seed=200 + SEASONS.index(S)))
    make_image("T_Frond", tex_frond(False))
    make_image("T_FrondSnow", tex_frond(True))
    for S in SEASONS:
        make_image(f"T_Grass_{S}", tex_grass_atlas(S))
    make_image("T_Flowers", tex_flowers())
    make_image("T_Litter", tex_litter())
    make_image("T_Petal", tex_petal())

    for S in SEASONS:
        mat_tex(f"M_Ground_{S}", f"T_Ground_{S}", f"N_Ground_{S}", 1.0, rough=0.62 if S == "Winter" else 0.92,
                spec=0.5 if S == "Winter" else 0.15)
    mat_tex("M_Soil", "T_Soil", "N_Soil", 1.0, rough=0.95, spec=0.25)
    mat_tex("M_BarkCherry", "T_BarkCherry", "N_BarkCherry", 1.0, rough=0.75, spec=0.35)
    mat_tex("M_BarkSpruce", "T_BarkSpruce", "N_BarkSpruce", 1.2, rough=0.85, spec=0.3)
    mat_tex("M_Wood", "T_Wood", "N_Wood", 0.8, rough=0.85, spec=0.3)
    mat_tex("M_Moss", "T_Moss", "N_Moss", 1.0, rough=0.95, spec=0.2)
    mat_tex("M_Rock", "T_Rock", "N_Rock", 1.3, rough=0.8, spec=0.4)
    mat_tex("M_RockMoss", "T_RockMoss", "N_RockMoss", 1.2, rough=0.88, spec=0.3)
    mat_tex("M_LogMoss", "T_LogMoss", "N_LogMoss", 1.1, rough=0.88, spec=0.25)
    mat_tex("M_Snow", "T_Ground_Winter", "N_Ground_Winter", 0.8, rough=0.6, spec=0.5)
    mat_tex("M_Ice", "T_Ice", "N_Ice", 0.6, rough=0.12, spec=0.7, coat=0.6)
    mat_solid("M_Water", "#10201F", rough=0.04, spec=0.5, nrm="N_Water", nrm_strength=0.35)
    for S in ("Spring", "Summer", "Autumn"):
        mat_tex(f"M_Leaves_{S}", f"T_Leaves_{S}", rough=0.7, spec=0.15, alpha=True)
    mat_tex("M_Frond", "T_Frond", rough=0.75, spec=0.15, alpha=True)
    mat_tex("M_FrondSnow", "T_FrondSnow", rough=0.75, spec=0.2, alpha=True)
    for S in SEASONS:
        mat_tex(f"M_Grass_{S}", f"T_Grass_{S}", rough=0.8, spec=0.1)
    mat_tex("M_Flowers", "T_Flowers", rough=0.5, spec=0.3, alpha=True)
    mat_tex("M_Litter", "T_Litter", rough=0.7, spec=0.3, alpha=True)
    mat_tex("M_Petals", "T_Petal", rough=0.5, spec=0.3, alpha=True)
    mat_solid("M_Stem", "#4E7A2E", rough=0.6, spec=0.3)
    mat_solid("M_Cattail", "#5A3A22", rough=0.85, spec=0.2)
    mat_solid("M_Lily", "#3F6B2B", rough=0.3, spec=0.5, coat=0.4)
    mat_solid("M_LilyAutumn", "#8A7A2E", rough=0.35, spec=0.5, coat=0.3)
    mat_solid("M_MushCap", "#8A5530", rough=0.45, spec=0.4)
    mat_solid("M_MushGill", "#E2D2B0", rough=0.8, spec=0.3)
    mat_solid("M_MushStem", "#E8DCC4", rough=0.7, spec=0.3)
    mat_solid("M_Pumpkin", "#C8631C", rough=0.45, spec=0.45)
    mat_solid("M_PumpkinStem", "#6B5A2E", rough=0.8, spec=0.3)
    mat_solid("M_Icicle", "#D6EEFA", rough=0.05, spec=0.8, coat=1.0)


def build_terrain(S, coll, root):
    N = 120
    mb = MB()
    xs = [-HALF + TILE * i / N for i in range(N + 1)]
    H = [[ground_z(x, y, S) for x in xs] for y in xs]
    idx = [[mb.vert((xs[i], xs[j], H[j][i])) for i in range(N + 1)] for j in range(N + 1)]
    k = 1 / 2.5
    for j in range(N):
        for i in range(N):
            mb.face((idx[j][i], idx[j][i + 1], idx[j + 1][i + 1], idx[j + 1][i]),
                    [(xs[i] * k, xs[j] * k), (xs[i + 1] * k, xs[j] * k), (xs[i + 1] * k, xs[j + 1] * k),
                     (xs[i] * k, xs[j + 1] * k)], 0, True)
    per = [(i, 0) for i in range(N)] + [(N, j) for j in range(N)] + \
          [(i, N) for i in range(N, 0, -1)] + [(0, j) for j in range(N, 0, -1)] + [(0, 0)]
    cols = []
    s = 0.0
    px = py = None
    rows = 3
    for (i, j) in per:
        x, y, zt = xs[i], xs[j], H[j][i]
        if px is not None:
            s += math.hypot(x - px, y - py)
        px, py = x, y
        zs = [BASE_Z + (zt - BASE_Z) * r / rows for r in range(rows + 1)]
        cols.append(([mb.vert((x, y, z)) for z in zs], s, zs))
    for c in range(len(cols) - 1):
        (c0, s0, z0), (c1, s1, z1) = cols[c], cols[c + 1]
        for r in range(rows):
            mb.face((c0[r], c1[r], c1[r + 1], c0[r + 1]),
                    [(s0 / 2, 0.98 * r / rows), (s1 / 2, 0.98 * r / rows),
                     (s1 / 2, 0.98 * (r + 1) / rows), (s0 / 2, 0.98 * (r + 1) / rows)], 1, False)
    bottom = [cols[c][0][0] for c in range(len(cols) - 1)][::-1]
    mb.face(bottom, [(0, 0)] * len(bottom), 1, False)
    me = mb.build(f"ME_{S}_Terrain", [M(f"M_Ground_{S}"), M("M_Soil")])
    link_obj(f"{S}_Terrain", me, coll, root)


def build_water(S, coll, root):
    mb = MB()
    n, R = 64, POND_R + 0.1
    z = WATER_Z + (0.05 if S == "Winter" else 0.0)
    cx, cy = POND_C
    c = mb.vert((cx, cy, z))
    ring = [mb.vert((cx + R * math.cos(2 * math.pi * k / n), cy + R * math.sin(2 * math.pi * k / n), z)) for k in range(n)]
    for k in range(n):
        a, b = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        mb.face((c, ring[k], ring[(k + 1) % n]),
                [(cx / 1.5, cy / 1.5), ((cx + R * math.cos(a)) / 1.5, (cy + R * math.sin(a)) / 1.5),
                 ((cx + R * math.cos(b)) / 1.5, (cy + R * math.sin(b)) / 1.5)], 0, True)
    me = mb.build(f"ME_{S}_Pond", [M("M_Ice" if S == "Winter" else "M_Water")])
    link_obj(f"{S}_{'Ice' if S == 'Winter' else 'Water'}", me, coll, root)


def cover_mat(S, kind="rock"):
    if S == "Winter":
        return ("M_Snow", 0.3)
    return ("M_RockMoss", 0.55) if kind == "rock" else ("M_LogMoss", 0.6)


def build_rocks(S, coll, root):
    cm, thresh = cover_mat(S)
    for k, ((x, y), d, seed) in enumerate(ROCKS):
        rng = random.Random(seed)
        planes = []
        for _ in range(8):
            nz = rng.uniform(-0.2, 0.9)
            a = rng.uniform(0, 6.283)
            r = math.sqrt(max(0.0, 1 - nz * nz))
            planes.append((Vector((r * math.cos(a), r * math.sin(a), nz)), rng.uniform(0.55, 0.8)))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
        off = Vector((seed * 1.7, seed * 2.9, seed * 0.6))
        for v in bm.verts:
            p = v.co.copy()
            p = p * (1.0 + 0.12 * noise.fractal(p * 1.1 + off, 0.65, 2.1, 4))
            for n, dd in planes:
                kk = p.dot(n)
                if kk > dd:
                    p = p - n * ((kk - dd) * 0.92)
            p = p * (1.0 + 0.03 * noise.fractal(p * 4.0 + off * 2, 0.5, 2.0, 3))
            if p.z < -0.25:
                p.z = -0.25 + (p.z + 0.25) * 0.2
            v.co = Vector((p.x * d[0], p.y * d[1], p.z * d[2]))
        bm.normal_update()
        uvl = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            n = f.normal
            f.smooth = True
            f.material_index = 1 if n.z > thresh else 0
            ax = max(range(3), key=lambda q: abs(n[q]))
            for l in f.loops:
                co = l.vert.co
                l[uvl].uv = (co.y, co.z) if ax == 0 else ((co.x, co.z) if ax == 1 else (co.x, co.y))
        me = bpy.data.meshes.new(f"ME_{S}_Rock_{k + 1}")
        bm.to_mesh(me)
        bm.free()
        try:
            me.set_sharp_from_angle(angle=math.radians(38))
        except Exception:
            pass
        me.materials.append(M("M_Rock"))
        me.materials.append(M(cm))
        link_obj(f"{S}_Rock_{k + 1}", me, coll, root, loc=(x, y, ground_z(x, y, S) - 0.12 * d[2]),
                 rot=(0, 0, seed * 0.7))


def build_log(S, coll, root):
    (lx, ly), rz, L, r = LOG
    cm, thresh = cover_mat(S, "log")
    rng = random.Random(5)
    mb = MB()
    nseg = 14
    pts = [Vector((-L / 2 + L * i / nseg, 0, 0)) for i in range(nseg + 1)]
    rad = [r * (1 + 0.08 * math.sin(i * 1.7) + 0.05 * rng.uniform(-1, 1)) for i in range(nseg + 1)]
    rings = add_tube(mb, pts, rad, 16, 0, v_scale=0.6, u_tile=0.4, top_mat=2, top_thresh=thresh - 0.1)
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        ids = [v[0] for v in ring[:-1]]
        uvs = [((v[2].y) * 2 + 0.5, (v[2].z) * 2 + 0.5) for v in ring[:-1]]
        if rev:
            ids, uvs = ids[::-1], uvs[::-1]
        mb.face(ids, uvs, 1, False)
    me = mb.build(f"ME_{S}_Log", [M("M_BarkSpruce"), M("M_Wood"), M(cm)])
    z = ground_z(lx, ly, S) + r * 0.7
    link_obj(f"{S}_FallenLog", me, coll, root, loc=(lx, ly, z), rot=(0, 0.04, rz))


def build_fence(S, coll, root):
    rng = random.Random(9)
    mb = MB()
    top = 1 if S == "Winter" else 0
    posts = []
    for x in FENCE_X:
        g = ground_z(x, FENCE_Y, S)
        rot = Euler((rng.uniform(-0.04, 0.04), rng.uniform(-0.05, 0.05), rng.uniform(-0.1, 0.1))).to_matrix()
        mb.box((x, FENCE_Y, g + 0.42), (0.055, 0.055, 0.6), rot, 0, top, uvscale=1.0)
        posts.append((x, g))
        if S == "Winter":
            mb.box((x, FENCE_Y, g + 1.04), (0.07, 0.07, 0.03), rot, 1, 1)
    for (x0, g0), (x1, g1) in zip(posts, posts[1:]):
        for hgt in (0.36, 0.78):
            cx, cz = (x0 + x1) / 2, (g0 + g1) / 2 + hgt + rng.uniform(-0.03, 0.03)
            ang = math.atan2(g1 - g0, x1 - x0)
            rot = Euler((0, -ang, rng.uniform(-0.02, 0.02))).to_matrix()
            half = ((x1 - x0) / 2 + 0.09, 0.022, 0.06)
            mb.box((cx, FENCE_Y - 0.075, cz), half, rot, 0, top, uvscale=1.0)
            if S == "Winter":
                mb.box((cx, FENCE_Y - 0.075, cz + 0.075), (half[0] - 0.02, 0.035, 0.018), rot, 1, 1)
    me = mb.build(f"ME_{S}_Fence", [M("M_Wood"), M("M_Snow")])
    link_obj(f"{S}_Fence", me, coll, root)


def stage_ground():
    for S in SEASONS:
        coll, root = season_root(S)
        build_terrain(S, coll, root)
        build_water(S, coll, root)
        build_rocks(S, coll, root)
        build_log(S, coll, root)
        build_fence(S, coll, root)


# ---------------------------------------------------------------- trees
TREE_CFG = {
    0: dict(n=8, a=(42, 62), lr=0.52, rr=0.55, seg=0.3, bend=0.05, up=0.02, tmin=0.34, sides=10),
    1: dict(n=5, a=(30, 52), lr=0.56, rr=0.62, seg=0.24, bend=0.13, up=0.05, tmin=0.25, sides=7),
    2: dict(n=4, a=(28, 48), lr=0.5, rr=0.62, seg=0.16, bend=0.17, up=0.05, tmin=0.2, sides=5),
    3: dict(n=3, a=(25, 45), lr=0.48, rr=0.6, seg=0.11, bend=0.2, up=0.03, tmin=0.25, sides=4),
    4: dict(n=0, seg=0.08, bend=0.2, up=0.02, sides=3),
}


def tree_skeleton(seed=4242, H=5.3, r0=0.2):
    R = random.Random(seed)
    out = []

    def grow(p0, d, L, r, lvl):
        c = TREE_CFG[lvl]
        nseg = max(2, int(math.ceil(L / c['seg'])))
        pts, rad, dirs = [p0.copy()], [r], [d.copy()]
        for i in range(nseg):
            jit = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))) * c['bend']
            d = (d + jit + Vector((0, 0, c['up']))).normalized()
            pts.append(pts[-1] + d * (L / nseg))
            taper = 0.85 if lvl == 0 else 0.75
            rad.append(max(r * (1 - taper * (i + 1) / nseg), 0.004))
            dirs.append(d.copy())
        if lvl == 0:
            rad = [rr * (1 + 0.7 * math.exp(-max(p.z, 0) / 0.3)) for rr, p in zip(rad, pts)]
        out.append(dict(pts=pts, rad=rad, lvl=lvl))
        n = c.get('n', 0)
        for k in range(n):
            t = c['tmin'] + (1 - c['tmin']) * (k + R.random() * 0.8) / n
            fi = t * nseg
            i = min(int(fi), nseg - 1)
            f = fi - i
            p = pts[i].lerp(pts[i + 1], f)
            dd = dirs[i + 1]
            ax = dd.orthogonal().normalized()
            bx = dd.cross(ax).normalized()
            az = k * 2.39996 + R.uniform(-0.4, 0.4)
            perp = ax * math.cos(az) + bx * math.sin(az)
            ang = math.radians(R.uniform(*c['a']))
            cd = (dd * math.cos(ang) + perp * math.sin(ang)).normalized()
            Lc = L * c['lr'] * (1.15 - 0.6 * t) * R.uniform(0.8, 1.15)
            rc = min(rad[i] * 0.8, r * c['rr'])
            grow(p, cd, Lc, rc, lvl + 1)

    grow(Vector((0, 0, -0.15)), Vector((0, 0, 1)), H * 0.85, r0, 0)
    return out


def tree_branch_mesh(name, skel, winter):
    mb = MB()
    for br in skel:
        lvl = br['lvl']
        add_tube(mb, br['pts'], br['rad'], TREE_CFG[lvl]['sides'], 0, v_scale=0.5, u_tile=0.5,
                 top_mat=1 if winter else None, top_thresh=0.5 if lvl > 0 else 0.8)
    return mb.build(name, [M("M_BarkCherry"), M("M_Snow")])


def leaf_cards(name, skel, S, seed):
    rng = random.Random(seed)
    dens, smin, smax = {"Spring": (9.0, 0.34, 0.48), "Summer": (11.0, 0.38, 0.54), "Autumn": (6.5, 0.34, 0.48)}[S]
    mb = MB()
    cards = []
    for br in skel:
        if br['lvl'] < 3:
            continue
        pts = br['pts']
        L = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))
        n = int(dens * L + rng.random())
        for _ in range(n):
            t = rng.uniform(0.2, 1.0) * (len(pts) - 1)
            i = min(int(t), len(pts) - 2)
            p = pts[i].lerp(pts[i + 1], t - i) + Vector((rng.gauss(0, 0.07), rng.gauss(0, 0.07), rng.gauss(0, 0.07)))
            cards.append(p)
    if not cards:
        return None
    cen = sum(cards, Vector()) / len(cards)
    cen.z -= 0.6
    for p in cards:
        nrm = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + 0.6)).normalized()
        u = nrm.orthogonal().normalized()
        a = rng.uniform(0, 2 * math.pi)
        u = (u * math.cos(a) + nrm.cross(u) * math.sin(a)).normalized()
        v = nrm.cross(u)
        s = rng.uniform(smin, smax)
        cell = rng.randrange(4)
        cu, cv = (cell % 2) * 0.5, (cell // 2) * 0.5
        out = (p - cen).normalized()
        ids = []
        for (du, dv) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = p + u * du * s / 2 + v * dv * s / 2
            vn = ((q - cen).normalized() * 0.65 + nrm * 0.35 + out * 0.2).normalized()
            ids.append(mb.vert(q, tuple(vn)))
        mb.face(ids, [(cu, cv), (cu + 0.5, cv), (cu + 0.5, cv + 0.5), (cu, cv + 0.5)], 0, True)
    return mb.build(name, [M(f"M_Leaves_{S}")], custom_normals=True)


def spruce_parts(seed, H, Rmax):
    rng = random.Random(seed)
    branches = []
    cards = []
    tn = 10
    trunk = [Vector((0, 0, -0.1 + (H + 0.1) * i / tn)) for i in range(tn + 1)]
    branches.append((trunk, [0.035 * H * (1 - i / tn) + 0.012 for i in range(tn + 1)], 6))
    z = 0.45
    while z < H - 0.35:
        n = rng.randint(7, 9)
        off = rng.random() * 6.283
        for k in range(n):
            az = off + 6.283 * k / n + rng.uniform(-0.2, 0.2)
            L = 0.15 + Rmax * ((H - z) / H) ** 0.9 * rng.uniform(0.85, 1.1)
            droop = -0.35 + 0.35 * (z / H)
            d = Vector((math.cos(az), math.sin(az), droop)).normalized()
            p0 = Vector((0, 0, z))
            pts = [p0 + d * L * t + Vector((0, 0, -0.12 * L * math.sin(math.pi * t) + 0.1 * L * t * t))
                   for t in (0, 0.33, 0.66, 1.0)]
            r = 0.03 * min(1.0, L) + 0.006
            branches.append((pts, [r, r * 0.7, r * 0.4, 0.003], 4))
            dd = pts[-1] - pts[1]
            w = min(1.1, 0.8 * L + 0.25)
            for tilt in (-0.7, -0.35, 0.0, 0.35, 0.7):
                side = dd.cross(Vector((0, 0, 1))).normalized()
                axn = dd.normalized()
                side = (side * math.cos(tilt) + axn.cross(side) * math.sin(tilt)).normalized()
                start = pts[0].lerp(pts[1], 0.4)
                cards.append((start, start + dd * 1.12, side * w / 2, rng.randrange(2)))
        z += rng.uniform(0.16, 0.22)
    top = Vector((0, 0, H - 0.55))
    for k in range(2):
        side = Vector((math.cos(k * 1.57), math.sin(k * 1.57), 0)) * 0.2
        cards.append((top, top + Vector((0, 0, 0.8)), side, k))
    return branches, cards


def spruce_mesh(name, parts, winter):
    branches, cards = parts
    mb = MB()
    for pts, rad, sides in branches:
        add_tube(mb, pts, rad, sides, 0, v_scale=0.5, u_tile=0.4, top_mat=1 if winter else None, top_thresh=0.45)
    for a, b, side, cell in cards:
        cu = cell * 0.5
        ids = [mb.vert(a - side), mb.vert(a + side), mb.vert(b + side), mb.vert(b - side)]
        mb.face(ids, [(cu, 0), (cu + 0.5, 0), (cu + 0.5, 1), (cu, 1)], 2, True)
    return mb.build(name, [M("M_BarkSpruce"), M("M_Snow"), M("M_FrondSnow" if winter else "M_Frond")])


def stage_trees():
    skel = tree_skeleton()
    sp = [(p, spruce_parts(seed, H, R)) for p, H, R, seed in SPRUCES]
    for S in SEASONS:
        coll, root = season_root(S)
        x, y = TREE_P
        z = ground_z(x, y, S)
        me = tree_branch_mesh(f"ME_{S}_CherryTree_Branches", skel, S == "Winter")
        link_obj(f"{S}_CherryTree", me, coll, root, loc=(x, y, z))
        if S != "Winter":
            lm = leaf_cards(f"ME_{S}_CherryTree_Leaves", skel, S, 77)
            link_obj(f"{S}_CherryTree_Leaves", lm, coll, root, loc=(x, y, z))
        for k, ((px, py), parts) in enumerate(sp):
            me = spruce_mesh(f"ME_{S}_Spruce_{k + 1}", parts, S == "Winter")
            link_obj(f"{S}_Spruce_{k + 1}", me, coll, root, loc=(px, py, ground_z(px, py, S)), rot=(0, 0, k * 1.3))


# ---------------------------------------------------------------- ground cover
def add_blade(mb, base, H, W, az, lean, face_az, col, ncol=4, segs=3, up_n=0.75):
    d = Vector((math.cos(az), math.sin(az), 0))
    s = Vector((math.cos(face_az), math.sin(face_az), 0))
    rows = []
    for k in range(segs + 1):
        t = k / segs
        p = base + d * (H * math.sin(lean) * t * t) + Vector((0, 0, H * t * math.cos(lean * t)))
        w = W * (1 - t ** 1.6) * 0.5 + 0.0004
        bn = Vector((0, 0, 1)) * up_n + d.cross(s).normalized() * (1 - up_n) * 0.5
        bn = tuple(bn.normalized())
        rows.append((mb.vert(p - s * w, bn), mb.vert(p + s * w, bn), t))
    u0, u1 = (col + 0.15) / ncol, (col + 0.85) / ncol
    for k in range(segs):
        a, b = rows[k], rows[k + 1]
        mb.face((a[0], a[1], b[1], b[0]), [(u0, a[2]), (u1, a[2]), (u1, b[2]), (u0, b[2])], 0, True)


def build_grass(S, coll, root, rng):
    cfg = {"Spring": (3800, (4, 7), (0.08, 0.22), (0.007, 0.012), 0.6),
           "Summer": (4200, (5, 8), (0.16, 0.42), (0.007, 0.013), 0.7),
           "Autumn": (3000, (3, 6), (0.08, 0.28), (0.006, 0.011), 0.8),
           "Winter": (130, (2, 4), (0.15, 0.45), (0.003, 0.006), 0.9)}[S]
    n, nb, hr, wr, lean = cfg
    mb = MB()
    for _ in range(n):
        x, y = rng.uniform(-HALF + 0.05, HALF - 0.05), rng.uniform(-HALF + 0.05, HALF - 0.05)
        if excluded(x, y, 0.02):
            continue
        z = ground_z(x, y, S) - (0.04 if S == "Winter" else 0.01)
        col = rng.randrange(4)
        for _b in range(rng.randint(*nb)):
            base = Vector((x + rng.gauss(0, 0.025), y + rng.gauss(0, 0.025), z))
            add_blade(mb, base, rng.uniform(*hr), rng.uniform(*wr), rng.uniform(0, 6.283),
                      rng.uniform(0.05, lean), rng.uniform(0, 6.283), col)
    me = mb.build(f"ME_{S}_Grass", [M(f"M_Grass_{S}")], custom_normals=True)
    link_obj(f"{S}_Grass", me, coll, root)


def shore_points(rng, n, a0, a1):
    out = []
    for _ in range(n):
        a = rng.uniform(a0, a1)
        r = 0.3
        while r < 2.0 and height(POND_C[0] + r * math.cos(a), POND_C[1] + r * math.sin(a)) < WATER_Z - 0.02:
            r += 0.02
        r += rng.uniform(-0.15, 0.12)
        out.append((POND_C[0] + r * math.cos(a), POND_C[1] + r * math.sin(a)))
    return out


def build_reeds(S, coll, root, rng):
    hr = {"Spring": (0.35, 0.65), "Summer": (0.75, 1.3), "Autumn": (0.6, 1.15), "Winter": (0.4, 0.95)}[S]
    lean = 0.35 if S != "Winter" else 0.8
    mb = MB()
    heads = MB()
    for (x, y) in shore_points(rng, 46, 0.3, 3.4):
        z = max(ground_z(x, y, S), WATER_Z) - 0.03
        col = rng.randrange(4)
        for _b in range(rng.randint(3, 5)):
            base = Vector((x + rng.gauss(0, 0.04), y + rng.gauss(0, 0.04), z))
            add_blade(mb, base, rng.uniform(*hr), rng.uniform(0.012, 0.022), rng.uniform(0, 6.283),
                      rng.uniform(0.05, lean), rng.uniform(0, 6.283), col, segs=4, up_n=0.4)
        if S != "Spring" and rng.random() < 0.45:
            h = rng.uniform(*hr) * 1.05
            tip = Vector((x + rng.gauss(0, 0.03), y + rng.gauss(0, 0.03), z + h))
            base = Vector((x, y, z))
            add_tube(heads, [base, base.lerp(tip, 0.5), tip], [0.004, 0.0035, 0.003], 4, 1, v_scale=1.0)
            hb = base.lerp(tip, 0.78)
            add_tube(heads, [hb, base.lerp(tip, 0.93)], [0.017, 0.016], 8, 0, v_scale=1.0)
    me = mb.build(f"ME_{S}_Reeds", [M(f"M_Grass_{S}")], custom_normals=True)
    link_obj(f"{S}_Reeds", me, coll, root)
    if heads.f:
        me2 = heads.build(f"ME_{S}_Cattails", [M("M_Cattail"), M("M_Stem")])
        link_obj(f"{S}_Cattails", me2, coll, root)


def build_flowers(S, coll, root, rng):
    n, hr = {"Spring": (380, (0.06, 0.18)), "Summer": (120, (0.14, 0.3))}[S]
    kinds = [0, 1, 2, 3] if S == "Spring" else [0, 3]
    centers = []
    while len(centers) < 26:
        x, y = rng.uniform(-HALF + 0.3, HALF - 0.3), rng.uniform(-HALF + 0.3, HALF - 0.3)
        if not excluded(x, y, 0.1):
            centers.append((x, y, rng.choice(kinds)))
    stems, heads = MB(), MB()
    for _ in range(n):
        cx, cy, kind = rng.choice(centers)
        x, y = cx + rng.gauss(0, 0.35), cy + rng.gauss(0, 0.35)
        if abs(x) > HALF - 0.05 or abs(y) > HALF - 0.05 or excluded(x, y, 0.03):
            continue
        z = ground_z(x, y, S) - 0.01
        h = rng.uniform(*hr)
        top = Vector((x + rng.gauss(0, 0.015), y + rng.gauss(0, 0.015), z + h))
        add_tube(stems, [Vector((x, y, z)), Vector((x, y, z)).lerp(top, 0.5), top], [0.0022, 0.002, 0.0018], 3, 0)
        s = rng.uniform(0.035, 0.05) * (1.3 if kind == 1 else 1.0)
        nrm = Vector((rng.gauss(0, 0.35), rng.gauss(0, 0.35), 1)).normalized()
        u = nrm.orthogonal().normalized()
        a = rng.uniform(0, 6.283)
        u = (u * math.cos(a) + nrm.cross(u) * math.sin(a)).normalized()
        v = nrm.cross(u)
        cu, cv = (kind % 2) * 0.5, (kind // 2) * 0.5
        ids = [heads.vert(top + (u * du + v * dv) * s, tuple(nrm)) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        heads.face(ids, [(cu, cv), (cu + 0.5, cv), (cu + 0.5, cv + 0.5), (cu, cv + 0.5)], 0, True)
    link_obj(f"{S}_FlowerStems", stems.build(f"ME_{S}_FlowerStems", [M("M_Stem")]), coll, root)
    link_obj(f"{S}_Flowers", heads.build(f"ME_{S}_Flowers", [M("M_Flowers")], custom_normals=True), coll, root)


def build_lilypads(S, coll, root, rng):
    n = {"Spring": 6, "Summer": 11, "Autumn": 7}[S]
    mb = MB()
    for _ in range(n):
        a, r = rng.uniform(0, 6.283), rng.uniform(0.15, 0.85)
        x, y = POND_C[0] + r * math.cos(a), POND_C[1] + r * math.sin(a)
        R = rng.uniform(0.07, 0.15)
        rot = rng.uniform(0, 6.283)
        z = WATER_Z + 0.004
        c = mb.vert((x, y, z), (0, 0, 1))
        seg = 20
        ring = []
        for k in range(seg + 1):
            t = rot + 0.35 + (6.283 - 0.45) * k / seg
            ring.append(mb.vert((x + R * math.cos(t), y + R * math.sin(t), z), (0, 0, 1)))
        for k in range(seg):
            mb.face((c, ring[k], ring[k + 1]), [(0.5, 0.5), (0, 0), (1, 0)], 0, True)
    me = mb.build(f"ME_{S}_LilyPads", [M("M_LilyAutumn" if S == "Autumn" else "M_Lily")], custom_normals=True)
    link_obj(f"{S}_LilyPads", me, coll, root)


def build_litter(S, coll, root, rng):
    if S == "Autumn":
        n, smin, smax, mat, cells = 1600, 0.06, 0.11, "M_Litter", 4
    else:
        n, smin, smax, mat, cells = 650, 0.022, 0.034, "M_Petals", 1
    mb = MB()
    for i in range(n):
        if rng.random() < 0.6:
            x, y = TREE_P[0] + rng.gauss(0, 1.3), TREE_P[1] + rng.gauss(0, 1.3)
        else:
            x, y = rng.uniform(-HALF, HALF), rng.uniform(-HALF, HALF)
        if abs(x) > HALF - 0.03 or abs(y) > HALF - 0.03:
            continue
        on_water = height(x, y) < WATER_Z + 0.01
        if on_water and rng.random() < 0.85:
            continue
        if not on_water and excluded(x, y):
            continue
        z = (WATER_Z + 0.003) if on_water else ground_z(x, y, S) + 0.004 + rng.random() * 0.01
        s = rng.uniform(smin, smax)
        a = rng.uniform(0, 6.283)
        tilt = Vector((rng.gauss(0, 0.2), rng.gauss(0, 0.2), 1)).normalized()
        u = Vector((math.cos(a), math.sin(a), 0))
        u = (u - tilt * u.dot(tilt)).normalized()
        v = tilt.cross(u)
        cell = rng.randrange(cells * cells)
        cu, cv = (cell % cells) / cells, (cell // cells) / cells
        d = 1 / cells
        p = Vector((x, y, z))
        ids = [mb.vert(p + (u * du + v * dv) * s / 2, (0, 0, 1)) for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        mb.face(ids, [(cu, cv), (cu + d, cv), (cu + d, cv + d), (cu, cv + d)], 0, True)
    me = mb.build(f"ME_{S}_FallenLeaves" if S == "Autumn" else f"ME_{S}_Petals", [M(mat)], custom_normals=True)
    link_obj(f"{S}_FallenLeaves" if S == "Autumn" else f"{S}_FallenPetals", me, coll, root)


def lathe(mb, center, profile, mats, segs=20, tilt=None):
    """profile: list of (r, z); mats: material index per profile segment."""
    rings = []
    for (r, z) in profile:
        ring = []
        for k in range(segs + 1):
            a = 2 * math.pi * k / segs
            p = Vector((r * math.cos(a), r * math.sin(a), z))
            if tilt is not None:
                p = tilt @ p
            ring.append(mb.vert(center + p))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(segs):
            mb.face((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]),
                    [(k / segs, i / len(rings))] * 4, mats[i], True)


def build_mushrooms(S, coll, root, rng):
    mb = MB()
    for (cx, cy) in ((-1.7, -0.95), (-2.5, -0.1), (-0.8, 0.55), (0.9, 0.6)):
        for _ in range(rng.randint(3, 6)):
            x, y = cx + rng.gauss(0, 0.12), cy + rng.gauss(0, 0.12)
            z = ground_z(x, y, S) - 0.01
            R = rng.uniform(0.025, 0.07)
            hs = R * rng.uniform(1.2, 1.9)
            sr = R * 0.22
            tilt = Euler((rng.gauss(0, 0.12), rng.gauss(0, 0.12), 0)).to_matrix()
            c = Vector((x, y, z))
            lathe(mb, c, [(sr * 1.25, 0), (sr * 1.05, hs * 0.4), (sr * 0.92, hs)], [2, 2], 12, tilt)
            capz = hs * 0.95
            prof = [(0.0001, capz + R * 0.75), (R * 0.4, capz + R * 0.7), (R * 0.75, capz + R * 0.5),
                    (R * 0.97, capz + R * 0.22), (R, capz + R * 0.05), (R * 0.9, capz),
                    (R * 0.5, capz + R * 0.06), (sr, capz + R * 0.1)]
            lathe(mb, c, prof[::-1], [1, 1, 0, 0, 0, 0, 0], 18, tilt)
    me = mb.build(f"ME_{S}_Mushrooms", [M("M_MushCap"), M("M_MushGill"), M("M_MushStem")])
    link_obj(f"{S}_Mushrooms", me, coll, root)


def build_pumpkins(S, coll, root, rng):
    mb = MB()
    for (x, y, R) in ((-2.7, 2.5, 0.26), (-2.2, 2.75, 0.19), (-3.0, 2.0, 0.16)):
        z = ground_z(x, y, S) - 0.02
        rings = []
        nl, ns = 14, 30
        rot = rng.uniform(0, 6.283)
        for i in range(nl + 1):
            ph = math.pi * i / nl
            ring = []
            for k in range(ns + 1):
                th = 2 * math.pi * k / ns + rot
                rib = 1 - 0.07 * (1 - abs(math.cos(5 * (th - rot)))) ** 1.5
                r = R * math.sin(ph) * rib
                zz = R * 0.78 * (1 - math.cos(ph))
                if ph > math.pi * 0.85:
                    zz -= R * 0.12 * (ph - math.pi * 0.85) / (math.pi * 0.15)
                ring.append(mb.vert((x + r * math.cos(th), y + r * math.sin(th), z + zz)))
            rings.append(ring)
        for i in range(nl):
            for k in range(ns):
                mb.face((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]),
                        [(k / ns, i / nl), ((k + 1) / ns, i / nl), ((k + 1) / ns, (i + 1) / nl), (k / ns, (i + 1) / nl)], 0, True)
        top = Vector((x, y, z + R * 1.44))
        add_tube(mb, [top, top + Vector((0.01, 0.0, R * 0.25)), top + Vector((0.04, 0.01, R * 0.38))],
                 [R * 0.09, R * 0.07, R * 0.06], 6, 1, v_scale=0.3)
    me = mb.build(f"ME_{S}_Pumpkins", [M("M_Pumpkin"), M("M_PumpkinStem")])
    link_obj(f"{S}_Pumpkins", me, coll, root)


def build_icicles(S, coll, root, rng):
    mb = MB()
    for x0, x1 in zip(FENCE_X, FENCE_X[1:]):
        for hgt in (0.36, 0.78):
            g = (ground_z(x0, FENCE_Y, S) + ground_z(x1, FENCE_Y, S)) / 2
            for _ in range(rng.randint(3, 6)):
                x = rng.uniform(x0 + 0.1, x1 - 0.1)
                top = Vector((x, FENCE_Y - 0.075, g + hgt - 0.055))
                L = rng.uniform(0.04, 0.14)
                add_tube(mb, [top, top + Vector((0, 0, -L * 0.5)), top + Vector((0, 0, -L))],
                         [0.009, 0.005, 0.0008], 6, 0)
    me = mb.build(f"ME_{S}_Icicles", [M("M_Icicle")])
    link_obj(f"{S}_Icicles", me, coll, root)


def stage_cover():
    for i, S in enumerate(SEASONS):
        rng = random.Random(300 + i)
        coll, root = season_root(S)
        build_grass(S, coll, root, rng)
        build_reeds(S, coll, root, rng)
        if S in ("Spring", "Summer"):
            build_flowers(S, coll, root, rng)
        if S != "Winter":
            build_lilypads(S, coll, root, rng)
        if S in ("Spring", "Autumn"):
            build_litter(S, coll, root, rng)
        if S == "Autumn":
            build_mushrooms(S, coll, root, rng)
            build_pumpkins(S, coll, root, rng)
        if S == "Winter":
            build_icicles(S, coll, root, rng)


# ---------------------------------------------------------------- light, world, camera
LIGHT = {  # sun elevation, sun azimuth (0 = in front of the tile, +x = right), energy, colour, sky strength, aerosol
    "Spring": (40, 55, 5.5, "#FFF4E6", 0.18, 1.0),
    "Summer": (58, 40, 6.5, "#FFFAF0", 0.2, 0.8),
    "Autumn": (16, 70, 5.0, "#FFCB94", 0.16, 1.6),
    "Winter": (19, 60, 3.6, "#E8F0FF", 0.3, 3.0),
    "Overview": (40, 45, 5.5, "#FFF6EC", 0.2, 1.0),
}


def sun_dir(elev, az):
    e, a = math.radians(elev), math.radians(az)
    return Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))


def apply_light(key):
    sc = bpy.context.scene
    elev, az, energy, col, strength, aerosol = LIGHT[key]
    sun = bpy.data.objects["Sun"]
    sun.data.energy = energy
    sun.data.color = to_lin(hexrgb(col))
    sun.rotation_euler = Vector((0, 0, 1)).rotation_difference(sun_dir(elev, az)).to_euler()
    nt = sc.world.node_tree
    sky = next(n for n in nt.nodes if n.type == 'TEX_SKY')
    sky.sun_elevation = math.radians(elev)
    sky.sun_rotation = math.radians(az)
    for attr, val in (("aerosol_density", aerosol), ("dust_density", aerosol), ("air_density", 1.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    next(n for n in nt.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = strength


def setup_render(samples=32, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    e = sc.eevee
    e.taa_render_samples = samples
    for attr, val in (("use_raytracing", True), ("use_fast_gi", True), ("use_shadows", True),
                      ("shadow_ray_count", 2), ("shadow_step_count", 8)):
        if hasattr(e, attr):
            setattr(e, attr, val)
    sc.render.film_transparent = transparent
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass


def tile_camera(S, cam, dist=13.0, elev=24, az=-32, lens=38):
    p = Vector((*GRID[S], 0))
    target = p + Vector((0, 0.3, 1.05))
    cam.location = target + sun_dir(elev, az) * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens


def stage_setup():
    sc = bpy.context.scene
    coll = bpy.data.collections.get("Scene_Setup") or bpy.data.collections.new("Scene_Setup")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    sun = bpy.data.lights.new("Sun", 'SUN')
    sun.angle = math.radians(1.2)
    so = bpy.data.objects.new("Sun", sun)
    coll.objects.link(so)
    cam = bpy.data.cameras.new("Camera")
    cam.clip_end = 300
    co = bpy.data.objects.new("Camera", cam)
    coll.objects.link(co)
    sc.camera = co
    co.location = (0, -27, 15.5)
    co.rotation_euler = (Vector((0, 0.6, 0.6)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    cam.lens = 40
    world = sc.world or bpy.data.worlds.new("Sky")
    sc.world = world
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    world.color = to_lin(hexrgb("#9CC3E6"))
    apply_light("Overview")
    setup_render(32)
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080


def build_all():
    clear_scene()
    stage_textures()
    stage_ground()
    stage_setup()
    stage_trees()
    stage_cover()


if __name__ == "__main__" and bpy is not None:
    build_all()
