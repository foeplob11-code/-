"""
Realistic Four Seasons - props pack (Blender 5.x)
=================================================

Season-aware props in the same realistic style as `realistic_seasons.py`:

* Birch tree and flowering shrub in spring / summer / autumn / winter
* Log cabin, stone well and wooden footbridge (normal + snowy winter versions)
* Park bench (normal + snowy), cast-iron street lamp (with a real point light)
* Firewood stack (normal + snowy), hay bales, stepping stones, snowman

Every prop hangs under its own `Prop_*` empty so it can be moved or exported on
its own.  All textures are synthesised and packed, so they survive GLB export.

Run inside Blender after (or next to) `realistic_seasons.py`; it reuses that
file's texture/mesh toolkit and materials and builds them if they are missing.
"""
import math
import random

import numpy as np

if "make_image" not in globals():  # standalone run: pull in the shared toolkit
    try:
        from realistic_seasons import *  # noqa: F401,F403
    except ImportError:
        import bpy
        exec(bpy.data.texts["realistic_seasons.py"].as_string())

try:
    import bpy
    import bmesh
    from mathutils import Vector, Euler, noise
except ImportError:
    bpy = None


# =====================================================================
# 1. extra textures
# =====================================================================
BIRCH_PAL = {
    "Spring": ["#9BC65A", "#A9D163", "#8CB84E", "#B5D872"],
    "Summer": ["#4E7F2E", "#5C8F36", "#44722A", "#6A9A3E"],
    "Autumn": ["#E2B93A", "#D9A22A", "#EBC94E", "#C98E24", "#B9A23A"],
}
SHRUB_AUTUMN_PAL = ["#B8281E", "#D03A22", "#A01E1A", "#E0552A", "#C2402A"]


def tex_birch(n=512, seed=31):
    rng = np.random.default_rng(seed)
    base = ramp(norm01(fbm(n, n, 4, 8, 4, rng)), [(0, "#C9C3B6"), (0.6, "#E4DFD4"), (1, "#F4F1EA")])
    fib = vnoise(n, n, 192, 8, rng)
    base *= (0.93 + 0.1 * fib)[..., None]
    cv = Canvas(n, n, wrap=True)
    for _ in range(460):
        x, y, L = rng.uniform(0, n), rng.uniform(0, n), rng.uniform(6, 28)
        draw_line(cv, x - L / 2, y, x + L / 2, y, rng.uniform(1.2, 2.8), hexrgb("#4A443D") * rng.uniform(0.8, 1.15))
    for _ in range(28):
        L = rng.uniform(30, 95)
        cv.stamp(rng.uniform(0, n), rng.uniform(0, n), L * 0.6 + 6,
                 leaf_fn(L, L * rng.uniform(0.22, 0.42), math.pi / 2 + rng.normal(0, 0.12), hexrgb("#211D19"), rng))
    peel = sstep(0.7, 0.85, norm01(fbm(n, n, 6, 3, 3, rng)))
    rgb = mix(base, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a)
    rgb = mix(rgb, hexrgb("#D8B89A"), peel * 0.35)
    return np.clip(rgb, 0, 1), fib * 0.2 - cv.a * 0.35 + peel * 0.1


def tex_shingles(n=512, seed=32):
    """Weathered cedar shingles; rows run along x, the roof slope along y (towards the ridge)."""
    rng = np.random.default_rng(seed)
    rows, per = 8, 8
    ys, xs = np.mgrid[0:n, 0:n].astype(float)
    rh = n / rows
    row = (ys // rh).astype(int)
    fy = (ys % rh) / rh
    u = xs / (n / per) + (row % 2) * 0.5 + row * 0.125
    sid = np.floor(u).astype(int) % per
    fx = u % 1.0
    tone = rng.random((rows, per))[row, sid]
    grain = vnoise(n, n, 8, 160, rng)
    rgb = ramp(norm01(tone * 0.55 + grain * 0.45),
               [(0, "#3A322B"), (0.45, "#5A4E41"), (0.8, "#75685A"), (1, "#8B7E6E")])
    gap = sstep(0.0, 0.035, np.minimum(fx, 1 - fx))
    shadow = 1 - 0.55 * sstep(0.8, 1.0, fy)
    butt = 1 + 0.12 * sstep(0.08, 0.0, fy)
    rgb = rgb * (gap * shadow * butt)[..., None]
    lich = sstep(0.72, 0.85, norm01(fbm(n, n, 6, 6, 4, rng))) * sstep(0.4, 0.7, vnoise(n, n, 64, 64, rng))
    rgb = mix(rgb, hexrgb("#8E9A6A"), lich * 0.5)
    hgt = (1 - fy) * 0.5 + grain * 0.15 - (1 - gap) * 0.5
    return np.clip(rgb, 0, 1), hgt


def tex_logwood(n=512, seed=33):
    """Debarked, weathered log; grain runs along v (the log axis)."""
    rng = np.random.default_rng(seed)
    grain = norm01(vnoise(n, n, 128, 4, rng) * 0.5 + vnoise(n, n, 320, 8, rng) * 0.3 + vnoise(n, n, 24, 2, rng) * 0.2)
    rgb = ramp(grain, [(0, "#5A4026"), (0.4, "#80603C"), (0.75, "#9E7A4E"), (1, "#B89466")])
    cv = Canvas(n, n, wrap=True)
    for _ in range(40):
        y, x, L = rng.uniform(0, n), rng.uniform(0, n), rng.uniform(30, 160)
        draw_line(cv, x - L / 2, y, x + L / 2, y + rng.normal(0, 3), rng.uniform(1.0, 2.2), hexrgb("#2A1E14"))
    knots = disc_stamps(n, n, 8, 4, 10, rng)
    rgb = mix(rgb, hexrgb("#3A2A1C"), knots * 0.8)
    rgb = mix(rgb, hexrgb("#2A1E14"), cv.a * 0.85)
    hgt = grain * 0.4 - cv.a * 0.5 - knots * 0.2
    return np.transpose(np.clip(rgb, 0, 1), (1, 0, 2)).copy(), hgt.T.copy()


def tex_rings(n=256, seed=34, cols=("#7E5A38", "#B08656", "#D4AA74"), bark="#3E2E22", rings=14, checks=5):
    """Cut end of a log (or a hay bale with straw colours): growth rings, drying checks, bark rim."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:n, 0:n].astype(float)
    dx, dy = xs + 0.5 - n / 2, ys + 0.5 - n / 2
    r = np.hypot(dx, dy) / (n / 2)
    th = np.arctan2(dy, dx)
    wob = r * (1 + 0.04 * np.sin(3 * th + rng.uniform(0, 6)) + 0.02 * np.sin(7 * th + rng.uniform(0, 6)))
    ring = 0.5 + 0.5 * np.cos(wob * 2 * np.pi * rings)
    fine = vnoise(n, n, 64, 64, rng)
    rgb = ramp(np.clip(ring * 0.5 + r * 0.3 + fine * 0.2, 0, 1), [(0, cols[0]), (0.5, cols[1]), (1, cols[2])])
    cv = Canvas(n, n)
    for _ in range(checks):
        a = rng.uniform(0, 6.283)
        L = rng.uniform(0.3, 0.8) * n / 2
        x0, y0 = n / 2 + math.cos(a) * n * 0.45, n / 2 + math.sin(a) * n * 0.45
        draw_line(cv, x0, y0, x0 - math.cos(a) * L, y0 - math.sin(a) * L, rng.uniform(1.5, 3.0), hexrgb("#2A1C12"))
    rgb = mix(rgb, hexrgb("#2A1C12"), cv.a * 0.9)
    edge = sstep(0.86, 0.93, r)
    rgb = mix(rgb, hexrgb(bark) * (0.85 + 0.3 * fine)[..., None], edge)
    return np.clip(rgb, 0, 1), ring * 0.2 - cv.a * 0.4 + edge * 0.2


def tex_straw(n=512, seed=35):
    rng = np.random.default_rng(seed)
    base = ramp(norm01(fbm(n, n, 6, 6, 4, rng)), [(0, "#7A6430"), (0.5, "#A88C48"), (1, "#C9AE68")])
    cv = Canvas(n, n, wrap=True)
    cols = ["#E2CB86", "#C9A85C", "#A88A45", "#F0DCA0", "#8C7438", "#D8BC72"]
    for _ in range(4200):
        x, y = rng.uniform(0, n), rng.uniform(0, n)
        a = rng.normal(0, 0.35)
        L = rng.uniform(18, 70)
        draw_line(cv, x, y, x + math.cos(a) * L, y + math.sin(a) * L, rng.uniform(1.0, 2.2),
                  hexrgb(cols[rng.integers(len(cols))]) * rng.uniform(0.85, 1.1))
    rgb = mix(base, cv.c / np.maximum(cv.a[..., None], 1e-4), cv.a * 0.95)
    return np.clip(rgb, 0, 1), cv.a * 0.5 + base[..., 0] * 0.2


def tex_small_leaves(pal, n=1024, seed=40):
    """2 x 2 atlas of drooping twigs with small ovate leaves (birch-like)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(n, n)
    c = n // 2
    twig = hexrgb("#4A3A2C")
    for cell in range(4):
        ox, oy = (cell % 2) * c, (cell // 2) * c
        for _t in range(4):
            x, y = ox + c * rng.uniform(0.2, 0.8), oy + c * 0.97
            ang = rng.uniform(-0.5, 0.5)
            pts = []
            for _k in range(9):
                nx = min(max(x + math.sin(ang) * c * 0.095, ox + c * 0.08), ox + c * 0.92)
                ny = max(y - math.cos(ang) * c * 0.095, oy + c * 0.05)
                draw_line(cv, x, y, nx, ny, 2.0, twig)
                pts.append((nx, ny))
                x, y = nx, ny
                ang += rng.normal(0, 0.15)
            for (px, py) in pts:
                for side in (-1, 1):
                    if rng.random() < 0.95:
                        L = rng.uniform(58, 88)
                        a = math.pi + side * rng.uniform(0.5, 1.2)
                        lx = float(np.clip(px + math.sin(a) * L * 0.55, ox + L * 0.6, ox + c - L * 0.6))
                        ly = float(np.clip(py + math.cos(a) * L * 0.55, oy + L * 0.6, oy + c - L * 0.6))
                        col = hexrgb(pal[rng.integers(len(pal))]) * rng.uniform(0.88, 1.08)
                        cv.stamp(lx, ly, L * 0.6 + 6, leaf_fn(L, L * 0.62, a, col, rng))
    return cv.rgba()


def mat_metal(name, hexc, rough=0.45, metal=0.9):
    m = mat_solid(name, hexc, rough=rough, spec=0.5)
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Metallic'].default_value = metal
    return m


def mat_emit(name, hexc, strength):
    m = mat_solid(name, hexc, rough=0.2, spec=0.5)
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Emission Color'].default_value = (*to_lin(hexrgb(hexc)), 1.0)
    b.inputs['Emission Strength'].default_value = strength
    return m


def stage_prop_textures():
    if "M_Rock" not in bpy.data.materials:
        stage_textures()
    rgb, h = tex_birch()
    make_image("T_BirchBark", rgb)
    make_image("N_BirchBark", normal_map(h, 4.0), True)
    rgb, h = tex_shingles()
    make_image("T_Shingles", rgb)
    make_image("N_Shingles", normal_map(h, 5.0), True)
    rgb, h = tex_logwood()
    make_image("T_LogWood", rgb)
    make_image("N_LogWood", normal_map(h, 4.0), True)
    rgb, h = tex_rings()
    make_image("T_EndGrain", rgb)
    make_image("N_EndGrain", normal_map(h, 4.0), True)
    rgb, h = tex_rings(256, 36, ("#8A7034", "#B49650", "#D2B874"), "#9C8040", rings=22, checks=0)
    make_image("T_HayEnd", rgb)
    rgb, h = tex_straw()
    make_image("T_Straw", rgb)
    make_image("N_Straw", normal_map(h, 4.0), True)
    for i, S in enumerate(("Spring", "Summer", "Autumn")):
        make_image(f"T_BirchLeaves_{S}", tex_small_leaves(BIRCH_PAL[S], seed=40 + i))
    make_image("T_ShrubLeaves_Autumn", tex_small_leaves(SHRUB_AUTUMN_PAL, seed=45))

    mat_tex("M_BirchBark", "T_BirchBark", "N_BirchBark", 0.9, rough=0.7, spec=0.3)
    mat_tex("M_Shingles", "T_Shingles", "N_Shingles", 1.0, rough=0.85, spec=0.25)
    mat_tex("M_LogWood", "T_LogWood", "N_LogWood", 1.0, rough=0.75, spec=0.3)
    mat_tex("M_EndGrain", "T_EndGrain", "N_EndGrain", 0.8, rough=0.8, spec=0.25)
    mat_tex("M_HayEnd", "T_HayEnd", rough=0.9, spec=0.2)
    mat_tex("M_Straw", "T_Straw", "N_Straw", 1.0, rough=0.9, spec=0.2)
    for S in ("Spring", "Summer", "Autumn"):
        mat_tex(f"M_BirchLeaves_{S}", f"T_BirchLeaves_{S}", rough=0.7, spec=0.15, alpha=True)
    mat_tex("M_ShrubLeaves_Autumn", "T_ShrubLeaves_Autumn", rough=0.7, spec=0.15, alpha=True)
    mat_metal("M_Iron", "#2A2A2C", 0.5, 0.85)
    mat_solid("M_Glass", "#1B252B", rough=0.05, spec=0.9, coat=0.5)
    mat_emit("M_LampGlass", "#FFD49A", 8.0)
    mat_solid("M_Wool", "#8C2A2A", rough=0.95, spec=0.2)
    mat_solid("M_WoolGreen", "#2F5A45", rough=0.95, spec=0.2)
    mat_solid("M_Coal", "#151515", rough=0.6, spec=0.4)
    mat_solid("M_Carrot", "#D2641E", rough=0.55, spec=0.35)
    mat_solid("M_Rope", "#8A7550", rough=0.9, spec=0.2)
    mat_solid("M_Twine", "#5A4630", rough=0.9, spec=0.2)


# =====================================================================
# 2. mesh helpers
# =====================================================================
def ident():
    return Euler((0, 0, 0)).to_matrix()


def cap(mb, ring, mat, flip):
    s = len(ring) - 1
    ids = [v[0] for v in ring[:-1]]
    uvs = [(0.5 + 0.48 * math.cos(2 * math.pi * j / s), 0.5 + 0.48 * math.sin(2 * math.pi * j / s)) for j in range(s)]
    if flip:
        ids, uvs = ids[::-1], uvs[::-1]
    mb.face(ids, uvs, mat, False)


def log(mb, a, b, r, mat_side, mat_end, sides=12, top_mat=None, top_thresh=0.6):
    a, b = Vector(a), Vector(b)
    n = max(2, int((b - a).length / 0.3))
    pts = [a.lerp(b, i / n) for i in range(n + 1)]
    rings = add_tube(mb, pts, [r] * len(pts), sides, mat_side, v_scale=1.0, u_tile=0.6,
                     top_mat=top_mat, top_thresh=top_thresh)
    cap(mb, rings[0], mat_end, True)
    cap(mb, rings[-1], mat_end, False)
    return rings


def gable_roof(mb, half_x, half_span, zr, pitch, wood, shing, winter, snow, ice, rng, icicles=14):
    for side in (-1, 1):
        E = Vector((0, side * half_span, zr - half_span * math.tan(pitch)))
        Rg = Vector((0, 0, zr))
        L = (Rg - E).length
        rot = Euler((pitch, 0, 0 if side < 0 else math.pi)).to_matrix()
        nrm = rot @ Vector((0, 0, 1))
        c = (Rg + E) / 2 + nrm * 0.05
        mb.box(c, (half_x, L / 2 + 0.03, 0.05), rot, wood, shing, uvscale=1.0)
        if winter:
            mb.box(c + nrm * 0.11, (half_x - 0.03, L / 2 - 0.02, 0.06), rot, snow, snow)
            for k in range(icicles):
                x = -half_x + 2 * half_x * (k + 0.2 + rng.random() * 0.6) / icicles
                top = E + Vector((x, 0, -0.02))
                Lc = rng.uniform(0.08, 0.3)
                add_tube(mb, [top, top + Vector((0, 0, -Lc * 0.5)), top + Vector((0, 0, -Lc))],
                         [0.02, 0.011, 0.002], 6, ice)
    mb.box((0, 0, zr + 0.1), (half_x, 0.09, 0.04), ident(), wood, snow if winter else wood)


def rock_mesh(name, seed, d, mat_side, mat_top, thresh, flat_top=False):
    rng = random.Random(seed)
    planes = []
    for _ in range(8):
        nz = rng.uniform(-0.2, 0.9)
        a = rng.uniform(0, 6.283)
        r = math.sqrt(max(0.0, 1 - nz * nz))
        planes.append((Vector((r * math.cos(a), r * math.sin(a), nz)), rng.uniform(0.55, 0.8)))
    if flat_top:
        planes.append((Vector((0, 0, 1)), 0.45))
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((seed * 1.7, seed * 2.9, seed * 0.6))
    for v in bm.verts:
        p = v.co.copy()
        p = p * (1.0 + 0.12 * noise.fractal(p * 1.1 + off, 0.65, 2.1, 4))
        for nn, dd in planes:
            kk = p.dot(nn)
            if kk > dd:
                p = p - nn * ((kk - dd) * 0.92)
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
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    try:
        me.set_sharp_from_angle(angle=math.radians(38))
    except Exception:
        pass
    me.materials.append(M(mat_side))
    me.materials.append(M(mat_top))
    return me


def blob_mesh(name, seed, r, amp, mat, flat_z=None):
    """Lumpy sphere (packed snow, pom-pom)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    off = Vector((seed * 1.3, seed * 0.7, seed * 2.1))
    for v in bm.verts:
        p = v.co.copy()
        p = p * (1.0 + amp * noise.fractal(p * 1.6 + off, 0.6, 2.0, 4))
        p = p * r
        if flat_z is not None and p.z < flat_z:
            p.z = flat_z + (p.z - flat_z) * 0.15
        v.co = p
    bm.normal_update()
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        f.smooth = True
        n = f.normal
        ax = max(range(3), key=lambda q: abs(n[q]))
        for l in f.loops:
            co = l.vert.co
            l[uvl].uv = (co.y, co.z) if ax == 0 else ((co.x, co.z) if ax == 1 else (co.x, co.y))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M(mat))
    return me


def grow_skeleton(seed, cfg, starts):
    """Recursive branching like tree_skeleton, but with a per-species config and several root stems."""
    R = random.Random(seed)
    out = []

    def grow(p0, d, L, r, lvl):
        c = cfg[lvl]
        nseg = max(2, int(math.ceil(L / c['seg'])))
        pts, rad, dirs = [p0.copy()], [r], [d.copy()]
        for i in range(nseg):
            jit = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))) * c['bend']
            d = (d + jit + Vector((0, 0, c['up']))).normalized()
            pts.append(pts[-1] + d * (L / nseg))
            rad.append(max(r * (1 - c.get('taper', 0.8) * (i + 1) / nseg), 0.003))
            dirs.append(d.copy())
        if lvl == 0 and c.get('flare'):
            rad = [rr * (1 + 0.6 * math.exp(-max(p.z, 0) / 0.25)) for rr, p in zip(rad, pts)]
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

    for p0, d, L, r in starts:
        grow(Vector(p0), Vector(d).normalized(), L, r, 0)
    return out


def branch_mesh(name, skel, cfg, bark, winter, snow_thresh=0.5):
    mb = MB()
    for br in skel:
        add_tube(mb, br['pts'], br['rad'], cfg[br['lvl']]['sides'], 0, v_scale=0.5, u_tile=0.5,
                 top_mat=1 if winter else None, top_thresh=snow_thresh if br['lvl'] > 0 else 0.85)
    return mb.build(name, [M(bark), M("M_Snow")])


def cards_mesh(name, skel, mat, dens, smin, smax, min_lvl, seed, spread=0.07, tmin=0.15):
    rng = random.Random(seed)
    pos = []
    for br in skel:
        if br['lvl'] < min_lvl:
            continue
        pts = br['pts']
        L = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))
        for _ in range(int(dens * L + rng.random())):
            t = rng.uniform(tmin, 1.0) * (len(pts) - 1)
            i = min(int(t), len(pts) - 2)
            pos.append(pts[i].lerp(pts[i + 1], t - i)
                       + Vector((rng.gauss(0, spread), rng.gauss(0, spread), rng.gauss(0, spread))))
    if not pos:
        return None
    cen = sum(pos, Vector()) / len(pos)
    cen.z -= 0.4
    mb = MB()
    for p in pos:
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
    return mb.build(name, [M(mat)], custom_normals=True)


def prop_root(name, group, loc, rz=0.0):
    sc = bpy.context.scene
    coll = bpy.data.collections.get(group)
    if coll is None:
        coll = bpy.data.collections.new(group)
        sc.collection.children.link(coll)
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.5
    coll.objects.link(e)
    e.location = loc
    e.rotation_euler = (0, 0, rz)
    return coll, e


# =====================================================================
# 3. props
# =====================================================================
BIRCH_CFG = {
    0: dict(n=10, a=(35, 55), lr=0.42, rr=0.5, seg=0.35, bend=0.03, up=0.02, tmin=0.3, sides=10, taper=0.85, flare=True),
    1: dict(n=5, a=(30, 50), lr=0.6, rr=0.6, seg=0.25, bend=0.1, up=0.0, tmin=0.2, sides=6, taper=0.8),
    2: dict(n=4, a=(25, 45), lr=0.6, rr=0.6, seg=0.18, bend=0.12, up=-0.06, tmin=0.15, sides=4, taper=0.8),
    3: dict(n=0, seg=0.12, bend=0.12, up=-0.12, sides=3, taper=0.8),
}
SHRUB_CFG = {
    0: dict(n=4, a=(25, 45), lr=0.55, rr=0.6, seg=0.15, bend=0.12, up=0.03, tmin=0.3, sides=5, taper=0.8),
    1: dict(n=3, a=(25, 45), lr=0.55, rr=0.6, seg=0.1, bend=0.15, up=0.02, tmin=0.25, sides=4, taper=0.8),
    2: dict(n=0, seg=0.08, bend=0.15, up=0.0, sides=3, taper=0.8),
}


def build_birch(S, loc):
    coll, root = prop_root(f"Prop_Birch_{S}", "Props_Trees", loc)
    skel = grow_skeleton(5150, BIRCH_CFG, [((0, 0, -0.1), (0.03, 0.02, 1), 6.6, 0.15)])
    link_obj(f"Prop_Birch_{S}_Branches", branch_mesh(f"ME_Birch_{S}_Branches", skel, BIRCH_CFG, "M_BirchBark",
                                                       S == "Winter"), coll, root)
    if S != "Winter":
        dens = {"Spring": 8.0, "Summer": 11.0, "Autumn": 8.5}[S]
        me = cards_mesh(f"ME_Birch_{S}_Leaves", skel, f"M_BirchLeaves_{S}", dens, 0.45, 0.65, 2, 61, spread=0.1)
        link_obj(f"Prop_Birch_{S}_Leaves", me, coll, root)


def build_shrub(S, loc):
    coll, root = prop_root(f"Prop_Shrub_{S}", "Props_Trees", loc)
    rng = random.Random(77)
    starts = []
    for k in range(9):
        a = k * 2.39996 + rng.uniform(-0.3, 0.3)
        t = math.radians(rng.uniform(10, 35))
        starts.append(((0.05 * math.cos(a), 0.05 * math.sin(a), -0.05),
                       (math.cos(a) * math.sin(t), math.sin(a) * math.sin(t), math.cos(t)),
                       rng.uniform(1.2, 1.6), 0.032))
    skel = grow_skeleton(78, SHRUB_CFG, starts)
    link_obj(f"Prop_Shrub_{S}_Branches", branch_mesh(f"ME_Shrub_{S}_Branches", skel, SHRUB_CFG, "M_BarkSpruce",
                                                       S == "Winter", 0.45), coll, root)
    if S != "Winter":
        mat, dens = {"Spring": ("M_Leaves_Spring", 22.0), "Summer": ("M_Leaves_Summer", 28.0),
                     "Autumn": ("M_ShrubLeaves_Autumn", 22.0)}[S]
        me = cards_mesh(f"ME_Shrub_{S}_Leaves", skel, mat, dens, 0.24, 0.36, 1, 79, spread=0.06)
        link_obj(f"Prop_Shrub_{S}_Leaves", me, coll, root)


def build_cabin(winter, loc, seed=7):
    tag = "_Winter" if winter else ""
    coll, root = prop_root(f"Prop_Cabin{tag}", "Props_Buildings", loc)
    rng = random.Random(seed)
    W, D, base_h, lr, nl = 3.2, 2.6, 0.32, 0.11, 9
    mats = ["M_LogWood", "M_EndGrain", "M_Rock", "M_Shingles", "M_Wood", "M_Glass", "M_Iron", "M_Snow", "M_Icicle"]
    LOGW, END, ROCK, SHING, WOOD, GLASS, IRON, SNOW, ICE = range(9)
    mb = MB()
    for (cx, cy, hx, hy) in ((0, -D / 2, W / 2 + 0.12, 0.16), (0, D / 2, W / 2 + 0.12, 0.16),
                             (-W / 2, 0, 0.16, D / 2 + 0.12), (W / 2, 0, 0.16, D / 2 + 0.12)):
        mb.box((cx, cy, base_h / 2), (hx, hy, base_h / 2), ident(), ROCK, SNOW if winter else ROCK)
    pitch_z = 0.205
    for i in range(nl):
        z = base_h + lr + i * pitch_z
        for y in (-D / 2, D / 2):
            log(mb, (-W / 2 - 0.22, y, z), (W / 2 + 0.22, y, z), lr * rng.uniform(0.95, 1.05), LOGW, END, 12)
        if i < nl - 1:
            for x in (-W / 2, W / 2):
                log(mb, (x, -D / 2 - 0.22, z + pitch_z / 2), (x, D / 2 + 0.22, z + pitch_z / 2),
                    lr * rng.uniform(0.95, 1.05), LOGW, END, 12)
    zt = base_h + lr + (nl - 1) * pitch_z + lr

    fy = -D / 2 - lr - 0.02
    dz0, dz1, dw = base_h, base_h + 1.85, 0.46
    mb.box((0, fy, (dz0 + dz1) / 2), (dw, 0.035, (dz1 - dz0) / 2), ident(), WOOD, WOOD)
    for x in (-dw - 0.05, dw + 0.05):
        mb.box((x, fy - 0.01, (dz0 + dz1 + 0.1) / 2), (0.05, 0.05, (dz1 - dz0 + 0.1) / 2), ident(), WOOD, WOOD)
    mb.box((0, fy - 0.01, dz1 + 0.05), (dw + 0.1, 0.05, 0.05), ident(), WOOD, SNOW if winter else WOOD)
    for z in (dz0 + 0.35, dz1 - 0.35):
        mb.box((-dw * 0.45, fy - 0.04, z), (dw * 0.5, 0.008, 0.025), ident(), IRON, IRON)
    hx = dw * 0.7
    add_tube(mb, [Vector((hx, fy - 0.04, dz0 + 0.95)), Vector((hx, fy - 0.1, dz0 + 0.95)),
                  Vector((hx, fy - 0.1, dz0 + 1.05)), Vector((hx, fy - 0.04, dz0 + 1.05))], [0.012] * 4, 6, IRON)
    mb.box((0, -D / 2 - lr - 0.55, 0.08), (0.6, 0.18, 0.08), ident(), LOGW, SNOW if winter else LOGW)
    mb.box((0, -D / 2 - lr - 0.28, 0.2), (0.6, 0.12, 0.1), ident(), LOGW, SNOW if winter else LOGW)

    def window(C, ang):
        rot = Euler((0, 0, ang)).to_matrix()
        C = Vector(C)

        def part(off, half, side, top):
            mb.box(C + rot @ Vector(off), half, rot, side, top)
        part((0, 0, 0), (0.3, 0.012, 0.28), GLASS, GLASS)
        part((0, -0.03, 0.32), (0.38, 0.03, 0.045), WOOD, WOOD)
        part((0, -0.05, -0.33), (0.42, 0.06, 0.05), WOOD, SNOW if winter else WOOD)
        part((-0.34, -0.03, 0), (0.045, 0.03, 0.28), WOOD, WOOD)
        part((0.34, -0.03, 0), (0.045, 0.03, 0.28), WOOD, WOOD)
        part((0, -0.03, 0), (0.018, 0.025, 0.28), WOOD, WOOD)
        part((0, -0.03, 0), (0.3, 0.025, 0.018), WOOD, WOOD)
    wz = base_h + 1.2
    window((-1.0, -D / 2 - lr - 0.01, wz), 0)
    window((1.0, -D / 2 - lr - 0.01, wz), 0)
    window((-W / 2 - lr - 0.01, 0, wz), -math.pi / 2)
    window((W / 2 + lr + 0.01, 0, wz), math.pi / 2)
    window((0.6, D / 2 + lr + 0.01, wz), math.pi)

    p = math.radians(34)
    half_span = D / 2 + lr + 0.4
    zr = zt + (D / 2 + lr) * math.tan(p)
    for sx in (-1, 1):
        x = sx * (W / 2 + lr)
        hw = D / 2 + lr
        vs = [Vector((x, -hw, zt - 0.05)), Vector((x, hw, zt - 0.05)), Vector((x, 0, zr))]
        ids = [mb.vert(v) for v in vs]
        uvs = [(v.y, v.z) for v in vs]
        if sx < 0:
            ids, uvs = ids[::-1], uvs[::-1]
        mb.face(ids, uvs, WOOD, False)
    gable_roof(mb, W / 2 + 0.45, half_span, zr, p, WOOD, SHING, winter, SNOW, ICE, rng)
    chx, chy = W / 2 - 0.55, 0.45
    mb.box((chx, chy, (zt + zr + 0.9) / 2 - 0.1), (0.24, 0.24, (zr + 0.9 - zt) / 2 + 0.1), ident(), ROCK, ROCK)
    mb.box((chx, chy, zr + 0.95), (0.28, 0.28, 0.05), ident(), ROCK, SNOW if winter else ROCK)
    link_obj(f"Prop_Cabin{tag}_Mesh", mb.build(f"ME_Cabin{tag}", [M(m) for m in mats]), coll, root)


def build_well(winter, loc, seed=8):
    tag = "_Winter" if winter else ""
    coll, root = prop_root(f"Prop_Well{tag}", "Props_Buildings", loc)
    rng = random.Random(seed)
    mats = ["M_Rock", "M_Wood", "M_LogWood", "M_Shingles", "M_Ice" if winter else "M_Water", "M_Iron", "M_Rope",
            "M_Snow", "M_EndGrain", "M_Icicle"]
    ROCK, WOOD, LOGW, SHING, WAT, IRON, ROPE, SNOW, END, ICE = range(10)
    mb = MB()
    Rin, Rout, ch = 0.5, 0.78, 0.15
    rm = (Rin + Rout) / 2
    for c in range(5):
        z = c * ch + ch / 2
        ws = [rng.uniform(0.7, 1.3) for _ in range(rng.randint(11, 14))]
        a = rng.uniform(0, 2 * math.pi)
        for w in ws:
            span = 2 * math.pi * w / sum(ws)
            ac = a + span / 2
            a += span
            r_ = rm + rng.uniform(-0.015, 0.015)
            rot = Euler((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), ac + math.pi / 2)).to_matrix()
            mb.box((r_ * math.cos(ac), r_ * math.sin(ac), z + rng.uniform(-0.006, 0.006)),
                   (r_ * span / 2 * 0.93, (Rout - Rin) / 2 * rng.uniform(0.88, 1.0), ch / 2 * rng.uniform(0.84, 0.96)),
                   rot, ROCK, SNOW if (winter and c == 4) else ROCK)
            du, dv = rng.random(), rng.random()
            mb.uv[-24:] = [(u + du, v + dv) for (u, v) in mb.uv[-24:]]
    cen = mb.vert((0, 0, 0.35))
    ring = [mb.vert((Rin * math.cos(2 * math.pi * k / 32), Rin * math.sin(2 * math.pi * k / 32), 0.35)) for k in range(32)]
    for k in range(32):
        mb.face((cen, ring[k], ring[(k + 1) % 32]), [(0.5, 0.5), (0, 0), (1, 0)], WAT, True)
    for sx in (-1, 1):
        mb.box((sx * (Rout + 0.04), 0, 0.95), (0.06, 0.06, 0.95), ident(), WOOD, WOOD)
    log(mb, (-Rout - 0.15, 0, 1.55), (Rout + 0.15, 0, 1.55), 0.06, LOGW, END, 10)
    V = Vector
    add_tube(mb, [V((Rout + 0.15, 0, 1.55)), V((Rout + 0.25, 0, 1.55)), V((Rout + 0.25, 0, 1.38)),
                  V((Rout + 0.33, 0, 1.38))], [0.012] * 4, 6, IRON)
    add_tube(mb, [V((0, 0, 1.5)), V((0, 0, 1.25)), V((0, 0, 1.05))], [0.012] * 3, 6, ROPE)
    rings = add_tube(mb, [V((0, 0, 0.7)), V((0, 0, 0.95))], [0.11, 0.135], 14, WOOD, v_scale=0.5)
    cap(mb, rings[0], WOOD, True)
    for z, r in ((0.73, 0.118), (0.91, 0.133)):
        add_tube(mb, [V((0, 0, z)), V((0, 0, z + 0.02))], [r, r + 0.002], 14, IRON)
    add_tube(mb, [V((-0.135, 0, 0.95)), V((-0.1, 0, 1.02)), V((0, 0, 1.05)), V((0.1, 0, 1.02)), V((0.135, 0, 0.95))],
             [0.006] * 5, 6, IRON)
    gable_roof(mb, Rout + 0.3, 0.8, 2.2, math.radians(40), WOOD, SHING, winter, SNOW, ICE, rng, icicles=8)
    link_obj(f"Prop_Well{tag}_Mesh", mb.build(f"ME_Well{tag}", [M(m) for m in mats]), coll, root)


def build_bridge(winter, loc, seed=9):
    tag = "_Winter" if winter else ""
    coll, root = prop_root(f"Prop_Bridge{tag}", "Props_Buildings", loc)
    rng = random.Random(seed)
    mats = ["M_Wood", "M_LogWood", "M_Snow"]
    WOOD, LOGW, SNOW = range(3)
    mb = MB()
    L, Wd, H = 3.6, 1.1, 0.45

    def arch(x):
        return H * (1 - (2 * x / L) ** 2) + 0.15

    def slope(x):
        return -8 * H * x / (L * L)
    n = 14
    for sy in (-1, 1):
        for i in range(n):
            x0, x1 = -L / 2 + L * i / n, -L / 2 + L * (i + 1) / n
            xm = (x0 + x1) / 2
            seg = math.hypot(x1 - x0, arch(x1) - arch(x0))
            mb.box((xm, sy * (Wd / 2 - 0.08), arch(xm) - 0.08), (seg / 2 + 0.01, 0.06, 0.11),
                   Euler((0, -math.atan(slope(xm)), 0)).to_matrix(), LOGW, LOGW)
    x = -L / 2 - 0.1
    while x < L / 2 + 0.1:
        w = rng.uniform(0.15, 0.19)
        rot = Euler((rng.uniform(-0.01, 0.01), -math.atan(slope(x)), rng.uniform(-0.015, 0.015))).to_matrix()
        mb.box((x, rng.uniform(-0.02, 0.02), arch(x) + 0.055), (w / 2 - 0.006, Wd / 2 + 0.06, 0.025), rot,
               WOOD, SNOW if winter else WOOD)
        x += w
    posts = [-L / 2 + 0.15 + (L - 0.3) * i / 4 for i in range(5)]
    for sy in (-1, 1):
        for px in posts:
            mb.box((px, sy * (Wd / 2 + 0.02), arch(px) + 0.5), (0.045, 0.045, 0.45), ident(),
                   LOGW, SNOW if winter else LOGW)
        xs = [-L / 2 + 0.15 + (L - 0.3) * t / 12 for t in range(13)]
        for hz, r in ((0.93, 0.04), (0.5, 0.03)):
            pts = [Vector((px, sy * (Wd / 2 + 0.02), arch(px) + hz)) for px in xs]
            add_tube(mb, pts, [r] * len(pts), 8, LOGW, v_scale=1.0, u_tile=0.4,
                     top_mat=SNOW if winter else None, top_thresh=0.5)
    link_obj(f"Prop_Bridge{tag}_Mesh", mb.build(f"ME_Bridge{tag}", [M(m) for m in mats]), coll, root)


def build_bench(winter, loc, rz=0.0):
    tag = "_Winter" if winter else ""
    coll, root = prop_root(f"Prop_Bench{tag}", "Props_Small", loc, rz)
    WOOD, IRON, SNOW = range(3)
    mb = MB()
    V = Vector
    r = 0.022
    for sx in (-0.72, 0.72):
        add_tube(mb, [V((sx, -0.26, 0)), V((sx, -0.25, 0.22)), V((sx, -0.24, 0.43))], [r] * 3, 8, IRON)
        add_tube(mb, [V((sx, 0.24, 0)), V((sx, 0.24, 0.22)), V((sx, 0.25, 0.43)), V((sx, 0.29, 0.62)),
                      V((sx, 0.33, 0.86))], [r] * 5, 8, IRON)
        add_tube(mb, [V((sx, -0.28, 0.42)), V((sx, 0.0, 0.415)), V((sx, 0.26, 0.42))], [r] * 3, 8, IRON)
        add_tube(mb, [V((sx, -0.25, 0.43)), V((sx, -0.27, 0.55)), V((sx, -0.25, 0.64)), V((sx, -0.1, 0.67)),
                      V((sx, 0.2, 0.66))], [r] * 5, 8, IRON, top_mat=SNOW if winter else None, top_thresh=0.6)
        for y in (-0.26, 0.24):
            mb.box((sx, y, 0.012), (0.035, 0.045, 0.012), ident(), IRON, IRON)
    for i in range(5):
        mb.box((0, -0.24 + i * 0.105, 0.455), (0.8, 0.042, 0.017), ident(), WOOD, SNOW if winter else WOOD)
    for i in range(3):
        z = 0.56 + i * 0.11
        mb.box((0, 0.302 + (z - 0.56) * 0.2, z), (0.8, 0.017, 0.042), Euler((-0.2, 0, 0)).to_matrix(),
               WOOD, SNOW if winter else WOOD)
    if winter:
        mb.box((0, -0.03, 0.495), (0.74, 0.24, 0.025), ident(), SNOW, SNOW)
    link_obj(f"Prop_Bench{tag}_Mesh", mb.build(f"ME_Bench{tag}", [M("M_Wood"), M("M_Iron"), M("M_Snow")]), coll, root)


def build_lamp(loc):
    coll, root = prop_root("Prop_StreetLamp", "Props_Small", loc)
    mb = MB()
    V = Vector
    c = V((0, 0, 0))
    lathe(mb, c, [(0.17, 0.0), (0.17, 0.05), (0.12, 0.09), (0.085, 0.28), (0.055, 0.33), (0.045, 0.38)], [0] * 5, 20)
    add_tube(mb, [V((0, 0, 0.38)), V((0, 0, 1.6)), V((0, 0, 2.72))], [0.042, 0.037, 0.032], 12, 0)
    lathe(mb, c, [(0.03, 2.7), (0.09, 2.74), (0.12, 2.78), (0.125, 2.8)], [0] * 3, 16)
    z0, z1, h0, h1 = 2.8, 3.14, 0.1, 0.13
    corners = lambda h, z: [V((math.cos(a) * h * 1.414, math.sin(a) * h * 1.414, z))
                            for a in (math.pi / 4 + k * math.pi / 2 for k in range(4))]
    lo, hi = corners(h0, z0), corners(h1, z1)
    for k in range(4):
        k2 = (k + 1) % 4
        ids = [mb.vert(lo[k]), mb.vert(lo[k2]), mb.vert(hi[k2]), mb.vert(hi[k])]
        mb.face(ids, [(0, 0), (1, 0), (1, 1), (0, 1)], 1, False)
        add_tube(mb, [lo[k], hi[k]], [0.009, 0.009], 6, 0)
    lathe(mb, c, [(0.175, 3.14), (0.16, 3.17), (0.06, 3.32), (0.025, 3.36), (0.03, 3.4), (0.0001, 3.46)], [0] * 5, 20)
    link_obj("Prop_StreetLamp_Mesh", mb.build("ME_StreetLamp", [M("M_Iron"), M("M_LampGlass")]), coll, root)
    light = bpy.data.lights.new("Prop_StreetLamp_Light", 'POINT')
    light.energy = 35
    light.color = to_lin(hexrgb("#FFD49A"))
    light.shadow_soft_size = 0.05
    lo_ = bpy.data.objects.new("Prop_StreetLamp_Light", light)
    coll.objects.link(lo_)
    lo_.parent = root
    lo_.location = (0, 0, 2.97)


def build_firewood(winter, loc, seed=10):
    tag = "_Winter" if winter else ""
    coll, root = prop_root(f"Prop_Firewood{tag}", "Props_Small", loc)
    rng = random.Random(seed)
    BARK, END, WOOD, SNOW = range(4)
    mb = MB()
    for row, nrow in enumerate([7, 6, 6, 5, 4]):
        z = 0.075 + row * 0.125
        x0 = -(nrow - 1) * 0.15 / 2
        for i in range(nrow):
            x = x0 + i * 0.15 + rng.uniform(-0.01, 0.01)
            yo = rng.uniform(-0.04, 0.04)
            log(mb, (x, -0.24 + yo, z), (x + rng.uniform(-0.02, 0.02), 0.24 + yo, z + rng.uniform(-0.01, 0.01)),
                rng.uniform(0.06, 0.075), BARK, END, 10, top_mat=SNOW if winter else None, top_thresh=0.55)
    for sx in (-1, 1):
        mb.box((sx * 0.6, 0, 0.35), (0.025, 0.025, 0.4), ident(), WOOD, SNOW if winter else WOOD)
    link_obj(f"Prop_Firewood{tag}_Mesh",
             mb.build(f"ME_Firewood{tag}", [M("M_BarkSpruce"), M("M_EndGrain"), M("M_Wood"), M("M_Snow")]), coll, root)


def build_hay(loc):
    coll, root = prop_root("Prop_HayBales", "Props_Small", loc)
    STRAW, END, TW = range(3)
    mb = MB()
    log(mb, (-0.9, -0.6, 0.6), (-0.9, 0.6, 0.6), 0.6, STRAW, END, 32)
    log(mb, (0.6, 0.3, 0.0), (0.6, 0.3, 1.15), 0.55, STRAW, END, 32)
    rot = Euler((0, 0, 0.3)).to_matrix()
    cen = Vector((0.4, -1.05, 0.2))
    mb.box(cen, (0.45, 0.23, 0.2), rot, STRAW, STRAW)
    for dx in (-0.2, 0.2):
        mb.box(cen + rot @ Vector((dx, 0, 0)), (0.008, 0.235, 0.205), rot, TW, TW)
    link_obj("Prop_HayBales_Mesh", mb.build("ME_HayBales", [M("M_Straw"), M("M_HayEnd"), M("M_Twine")]), coll, root)


def build_stepping_stones(loc):
    coll, root = prop_root("Prop_SteppingStones", "Props_Small", loc)
    rng = random.Random(11)
    for k in range(8):
        t = k / 7
        d = (rng.uniform(0.25, 0.34), rng.uniform(0.2, 0.28), rng.uniform(0.07, 0.1))
        me = rock_mesh(f"ME_SteppingStone_{k + 1}", 100 + k, d, "M_Rock", "M_RockMoss", 0.93, flat_top=True)
        link_obj(f"Prop_SteppingStone_{k + 1}", me, coll, root,
                 loc=(-2.0 + 4.0 * t, 0.6 * math.sin(t * math.pi * 1.2), 0.0), rot=(0, 0, rng.uniform(0, 3.14)))


def build_snowman(loc):
    coll, root = prop_root("Prop_Snowman", "Props_Small", loc, rz=0.2)
    rng = random.Random(12)
    balls = [(0.42, 0.36), (0.31, 0.98), (0.22, 1.42)]
    for i, (r, z) in enumerate(balls):
        me = blob_mesh(f"ME_Snowman_Ball_{i + 1}", 20 + i, r, 0.05, "M_Snow", flat_z=-z + 0.01 if i == 0 else None)
        link_obj(f"Prop_Snowman_Ball_{i + 1}", me, coll, root, loc=(0, 0, z))
    coal = rock_mesh("ME_Snowman_Coal", 30, (0.025, 0.022, 0.02), "M_Coal", "M_Coal", 2.0)

    def on_ball(i, d, out=0.0):
        r, z = balls[i]
        d = Vector(d).normalized()
        return Vector((0, 0, z)) + d * (r + out)
    pieces = [on_ball(2, (sx * 0.35, -0.88, 0.3)) for sx in (-1, 1)]
    pieces += [on_ball(2, (a * 0.13, -0.95, -0.25 + 0.025 * a * a)) for a in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)]
    pieces += [on_ball(1, (0, -1, dz)) for dz in (0.45, 0.05)] + [on_ball(0, (0, -1, 0.3))]
    for k, p in enumerate(pieces):
        ob = link_obj(f"Prop_Snowman_Coal_{k + 1}", coal, coll, root, loc=p, rot=(rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3)))
        if k >= 8:
            ob.scale = (1.4, 1.4, 1.4)
    V = Vector
    mb = MB()
    hc = V((0, 0, 1.42))
    add_tube(mb, [hc + V((0, -0.19, 0)), hc + V((0.01, -0.3, -0.005)), hc + V((0.025, -0.4, -0.02)),
                  hc + V((0.035, -0.47, -0.035))], [0.032, 0.022, 0.012, 0.002], 10, 0)
    for sx in (-1, 1):
        a0 = V((sx * 0.26, 0, 1.05))
        a1 = V((sx * 0.55, 0.03, 1.2))
        a2 = V((sx * 0.8, 0.05, 1.36))
        add_tube(mb, [a0, a1, a2], [0.018, 0.013, 0.007], 6, 1)
        add_tube(mb, [a1.lerp(a2, 0.6), a1.lerp(a2, 0.6) + V((sx * 0.08, 0.02, 0.12))], [0.008, 0.003], 5, 1)
        add_tube(mb, [a2, a2 + V((sx * 0.1, 0.0, -0.03))], [0.006, 0.002], 5, 1)
    zn = 1.22
    loop = [V((0.2 * math.cos(2 * math.pi * k / 24), 0.2 * math.sin(2 * math.pi * k / 24), zn)) for k in range(25)]
    add_tube(mb, loop, [0.05] * 25, 10, 2)
    add_tube(mb, [V((0.1, -0.17, 1.2)), V((0.13, -0.24, 1.05)), V((0.14, -0.28, 0.9))], [0.045, 0.042, 0.04], 10, 2)
    lathe(mb, V((0, 0, 1.51)), [(0.215, 0.0), (0.2, 0.08), (0.17, 0.15), (0.11, 0.2), (0.0001, 0.225)], [3] * 4, 20)
    loop2 = [V((0.215 * math.cos(2 * math.pi * k / 24), 0.215 * math.sin(2 * math.pi * k / 24), 1.52)) for k in range(25)]
    add_tube(mb, loop2, [0.03] * 25, 8, 3)
    link_obj("Prop_Snowman_Accessories",
             mb.build("ME_Snowman_Accessories", [M("M_Carrot"), M("M_BarkSpruce"), M("M_Wool"), M("M_WoolGreen")]),
             coll, root)
    link_obj("Prop_Snowman_PomPom", blob_mesh("ME_Snowman_PomPom", 31, 0.06, 0.12, "M_Wool"), coll, root,
             loc=(0, 0, 1.75))


PROP_GROUPS = {
    "Props_Trees": ["Prop_Birch_*", "Prop_Shrub_*"],
    "Props_Buildings": ["Prop_Cabin*", "Prop_Well*", "Prop_Bridge*"],
    "Props_Small": ["Prop_Bench*", "Prop_StreetLamp", "Prop_Firewood*", "Prop_HayBales", "Prop_SteppingStones",
                    "Prop_Snowman"],
}


def stage_props():
    for i, S in enumerate(SEASONS):
        x = -7.5 + 5.0 * i
        build_birch(S, (x, 1.0, 0))
        build_shrub(S, (x, -2.0, 0))
    build_cabin(False, (-6.0, -13.0, 0))
    build_cabin(True, (-1.0, -13.0, 0))
    build_well(False, (3.4, -13.0, 0))
    build_well(True, (6.2, -13.0, 0))
    build_bridge(False, (-4.0, -19.0, 0))
    build_bridge(True, (1.0, -19.0, 0))
    build_bench(False, (-6.0, -26.0, 0))
    build_bench(True, (-4.0, -26.0, 0))
    build_lamp((-2.2, -25.4, 0))
    build_firewood(False, (-0.8, -26.0, 0))
    build_firewood(True, (0.8, -26.0, 0))
    build_hay((3.2, -25.6, 0))
    build_snowman((6.2, -26.0, 0))
    build_stepping_stones((0.0, -29.0, 0))


def frame_group(cam, group, elev=16, az=-28, lens=45, margin=1.08, aspect=16 / 9):
    pts = []
    for ob in bpy.data.collections[group].all_objects:
        if ob.type == 'MESH':
            pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    rad = (hi - lo).length / 2
    fov = 2 * math.atan(36 / 2 / lens)
    fov_v = 2 * math.atan(math.tan(fov / 2) / aspect)
    dist = rad / math.sin(min(fov, fov_v) / 2) * margin * 0.62
    cam.location = c + sun_dir(elev, az) * dist
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens


def build_props_all():
    if "Sun" not in bpy.data.objects:
        stage_setup()
    stage_prop_textures()
    stage_props()


if __name__ == "__main__" and bpy is not None:
    build_props_all()
