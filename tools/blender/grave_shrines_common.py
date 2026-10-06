"""Shared pieces of five Bone Legion towers (bone_crypt, plague_cauldron, soul_obelisk, hex_tomb, blood_altar):
chunky low-poly skulls and bones, soul flames and wisps, heavy chains, pointed arches, coursed walls with openings,
stepped daises, iron fences, torn banners, lanterns, gargoyles, candles, dead ivy. Exec'd by a tower script after
kk_helpers.py:

    exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

Everything takes kk_helpers' Kit bmeshes (kit["swatch:lo:hi"]) and is laid out in the tower's own space.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

NECRO = (0.26, 1.0, 0.2)        # sickly green soul-fire
SOUL = (0.66, 0.36, 1.0)        # violet
BLOOD = (0.95, 0.05, 0.06)      # deep red
BONE = "cream:0.02:0.6"
IRON = "iron:0.25:0.95"
RUST = "wood_dark:0.35:0.95"


def glow(c, s=1.0):
    """A Kit key for a glowing colour."""
    return "glow:%.3f,%.3f,%.3f,%.2f" % (c[0], c[1], c[2], s)


def place(loc=(0, 0, 0), yaw=0.0, pitch=0.0, roll=0.0, scale=1.0):
    """A matrix: scale, roll about +Y (the piece's forward), pitch about +X, yaw about +Z (degrees), then move to loc."""
    return (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pitch), 4, "X")
            @ Matrix.Rotation(math.radians(roll), 4, "Y") @ Matrix.Diagonal((scale, scale, scale, 1.0)))


class Stamp:
    """with Stamp(M, bm1, bm2): build at the origin with the usual helpers; on leaving, what was added is moved by M."""

    def __init__(self, M, *bms):
        self.M, self.bms = M, bms

    def __enter__(self):
        self.n = [len(bm.verts) for bm in self.bms]
        return self

    def __exit__(self, *a):
        seen = set()
        for bm, n in zip(self.bms, self.n):
            if id(bm) in seen:
                continue
            seen.add(id(bm))
            bm.verts.ensure_lookup_table()
            vs = [bm.verts[i] for i in range(n, len(bm.verts))]
            if vs:
                bmesh.ops.transform(bm, matrix=self.M, verts=vs)
        return False


def gs_inset(pts, d):
    """A counterclockwise outline pulled in by d (out for d < 0)."""
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d0 = (p1 - p0).normalized()
        d1 = (p2 - p1).normalized()
        n0 = Vector((-d0.y, d0.x, 0))
        n1 = Vector((-d1.y, d1.x, 0))
        bis = n0 + n1
        bis = bis / max(bis.length, 1e-6)
        out.append(p1 + bis * (d / max(bis.dot(n0), 0.25)))
    return out


def gs_ngon(c, r, n, phase=0.0, sx=1.0, sy=1.0):
    """n points round c (counterclockwise from above), z = 0."""
    c = Vector((c[0], c[1], 0))
    return [c + Vector((math.cos(2 * math.pi * (i + phase) / n) * r * sx, math.sin(2 * math.pi * (i + phase) / n) * r * sy, 0)) for i in range(n)]


# ------------------------------------------------------------------------------------------- bones and skulls
def gs_skull(kit, M, bone=BONE, dark="black:0.3:0.8", n=8, jaw=True, eyes=None):
    """A chunky skull 1.0 tall standing on the origin (z 0..1), facing +Y, placed by M (place(loc, yaw, scale=size)).
    eyes: a glow key for the sockets instead of the dark one."""
    b, d = kit[bone], kit[eyes or dark]
    dk = kit[dark]
    with Stamp(M, b, d, dk):
        rings = [oval((0, cy, z), (1, 0, 0), (0, 1, 0), rx, ry, n, power=2.3, phase=0.5)
                 for z, rx, ry, cy in ((0.3, 0.33, 0.37, -0.03), (0.5, 0.43, 0.47, -0.02), (0.72, 0.42, 0.46, -0.03), (0.9, 0.29, 0.33, -0.05))]
        bm_loft(b, rings, tip1=(0, -0.05, 1.0))
        if jaw:
            bm_beam(b, (0, 0.27, 0.36), (0, 0.255, 0.0), 0.56, 0.38, w1=0.38, h1=0.3, up=(0, 1, 0))
            bm_box(dk, (0.36, 0.05, 0.04), (0, 0.42, 0.13))                                   # the teeth's line
        else:
            bm_beam(b, (0, 0.27, 0.36), (0, 0.26, 0.2), 0.54, 0.38, w1=0.44, h1=0.3, up=(0, 1, 0))
        for sx in (-1, 1):
            bm_box(d, (0.2, 0.09, 0.2), (sx * 0.19, 0.405, 0.58), (0, sx * -8, 0))             # eye sockets
        bm_box(dk, (0.09, 0.07, 0.13), (0, 0.44, 0.37))                                         # nose


def gs_bone(bm, p0, p1, r=0.035, n=5, knob=1.7):
    """A long bone from p0 to p1: a shaft with a knuckle at each end."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    u = d / max(L, 1e-6)
    k = min(r * knob * 1.2, L * 0.22)
    pts = [p0, p0 + u * k * 0.55, p0 + u * k * 1.35, p1 - u * k * 1.35, p1 - u * k * 0.55, p1]
    rad = [r * knob * 0.72, r * knob, r, r, r * knob, r * knob * 0.72]
    bm_tube(bm, pts, rad, n=n)
    return bm


def gs_rib(bm, base, up, over, length, r=0.03, curve=0.5, n=4, segs=4, tip=0.0):
    """A curved rib (a claw of bone) `length` long: it rises from base along `up` and curls toward `over` through
    curve * 180 degrees, tapering to `tip` of its thickness."""
    base, up, over = Vector(base), Vector(up).normalized(), Vector(over).normalized()
    rr = length / max(math.pi * curve, 1e-3)
    pts, rad = [], []
    for i in range(segs + 1):
        t = i / segs
        a = t * math.pi * curve
        pts.append(base + up * (math.sin(a) * rr) + over * ((1.0 - math.cos(a)) * rr))
        rad.append(r * (1.0 - (1.0 - tip) * t))
    bm_tube(bm, pts, rad, n=n)
    return pts


# ------------------------------------------------------------------------------------------- fire and souls
def gs_flame(bm, c, h=0.3, r=0.1, rnd=None, tongues=3, n=5):
    """A flame standing on c: a tall teardrop with a few smaller tongues round it."""
    rnd = rnd or random.Random(3)
    c = Vector(c)

    def tongue(base, hh, rr, lean):
        ph = rnd.random()
        rings = [oval(base + lean * t + Vector((0, 0, hh * t)), (1, 0, 0), (0, 1, 0), rr * s, rr * s, n, phase=ph)
                 for t, s in ((0.0, 0.6), (0.26, 1.0), (0.62, 0.58))]
        bm_loft(bm, rings, tip1=base + lean * 1.2 + Vector((0, 0, hh)))
    tongue(c, h, r, Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * r * 0.4)
    for i in range(tongues):
        a = 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / max(tongues, 1)
        d = Vector((math.cos(a), math.sin(a), 0))
        tongue(c + d * r * 0.8, h * rnd.uniform(0.42, 0.68), r * 0.55, d * r * 0.5)
    return bm


def gs_wisp(bm, c, r=0.085, tail=(-1, 0, 0), length=0.4, n=5, curl=(0, 0, 0.3), eyes=None):
    """A soul-wisp: a faceted glowing head at c with a thin tail streaming along `tail` (curling toward `curl`).
    eyes: a bmesh for two dark eye-holes on its face."""
    c, t, cu = Vector(c), Vector(tail).normalized(), Vector(curl)
    bm_ellipsoid(bm, tuple(c), (r, r, r * 1.08), u=6, v=4)
    s0 = r * 0.6
    pts = [c + t * s0, c + t * (s0 + length * 0.3) + cu * (length * 0.08), c + t * (s0 + length * 0.66) + cu * (length * 0.3),
           c + t * (s0 + length) + cu * (length * 0.66)]
    bm_tube(bm, pts, [r * 0.78, r * 0.5, r * 0.26, 0.0], n=n)
    if eyes is not None:
        side = t.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        for sx in (-1, 1):
            p = c - t * (r * 0.78) + side * (sx * r * 0.36) + Vector((0, 0, r * 0.18))
            bm_beam(eyes, p + t * (r * 0.2), p - t * (r * 0.14), r * 0.3, r * 0.42)
    return bm


def gs_candle(kit, c, h=0.2, r=0.035, flame=None, wax="cream:0.05:0.5", n=6):
    """A candle standing on c with a little flame (a glow key; None for a dead one)."""
    c = Vector(c)
    bm_cyl(kit[wax], r * 1.08, r * 0.92, h, (c.x, c.y, c.z + h / 2), seg=n)
    if flame:
        f = kit[flame]
        p = c + Vector((0, 0, h + 0.005))
        bm_loft(f, [oval(p + Vector((0, 0, z)), (1, 0, 0), (0, 1, 0), r * s, r * s, 4) for z, s in ((0.0, 0.45), (r * 1.3, 0.85))],
                tip1=p + Vector((0, 0, r * 4.2)))


# ------------------------------------------------------------------------------------------- iron
def gs_chain(bm, p0, p1, sag=0.12, link=0.12, w=0.08, th=0.032):
    """A heavy chain hanging from p0 to p1 (sagging by `sag` at its middle): slab links, every other one turned a
    quarter. Returns the points along it."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    n = max(2, int(round(L * (1.0 + 2.6 * (sag / max(L, 1e-6)) ** 2) / (link * 0.78))))
    pts = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= sag * 4.0 * t * (1.0 - t)
        pts.append(p)
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        m = (a + b) * 0.5
        d = (b - a).normalized()
        a2, b2 = m - d * (link * 0.6), m + d * (link * 0.6)
        if i % 2 == 0:
            bm_beam(bm, a2, b2, w, th)
        else:
            bm_beam(bm, a2, b2, th, w)
    return pts


def gs_fence(bm, p0, p1, z, h=0.5, n=6, bar=0.028, rnd=None, broken=0.0, rails=(0.18, 0.78)):
    """A run of iron fence from p0 to p1 standing on z: spear-topped bars on two rails. broken: the share of bars
    bent or snapped."""
    rnd = rnd or random.Random(5)
    p0, p1 = Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z))
    d = p1 - p0
    for t in rails:
        bm_beam(bm, p0 + Vector((0, 0, h * t)), p1 + Vector((0, 0, h * t)), bar * 0.9, bar * 1.2)
    for i in range(n):
        t = (i + 0.5) / n
        b = p0 + d * t
        hh = h * rnd.uniform(0.94, 1.06)
        lean = Vector((0, 0, 0))
        if rnd.random() < broken:
            if rnd.random() < 0.5:
                hh *= rnd.uniform(0.35, 0.6)                 # snapped off
            else:
                lean = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0))       # bent
        top = b + lean + Vector((0, 0, hh))
        bm_beam(bm, b, top, bar, bar)
        bm_crystal(bm, top - Vector((0, 0, 0.01)), top + lean * 0.3 + Vector((0, 0, bar * 3.4)), bar * 1.25, n=4, shoulder=0.25, foot=0.5)
    return bm


def gs_lantern(kit, M, fire=None, iron=IRON, rnd=None):
    """An iron lantern hanging from the origin (its ring at z = 0, the cage below it down to z = -0.52), placed by M.
    fire: the glow key of the soul-fire inside (None: an empty cage; its flame would stand on (0, 0, -0.48))."""
    b = kit[iron]
    f = kit[fire] if fire else b
    with Stamp(M, b, f):
        bm_box(b, (0.035, 0.035, 0.1), (0, 0, -0.04))
        bm_cyl(b, 0.2, 0.035, 0.11, (0, 0, -0.135), rot=(0, 0, 45), seg=4)
        bm_box(b, (0.3, 0.3, 0.03), (0, 0, -0.2))
        for sx in (-1, 1):
            for sy in (-1, 1):
                bm_box(b, (0.034, 0.034, 0.28), (sx * 0.118, sy * 0.118, -0.34))
        bm_box(b, (0.3, 0.3, 0.04), (0, 0, -0.5))
        if fire:
            gs_flame(f, (0, 0, -0.48), h=0.25, r=0.075, rnd=rnd or random.Random(4), tongues=2, n=4)


# ------------------------------------------------------------------------------------------- stonework
def gs_block_wall(bm, rnd, p0, p1, z0, z1, th=0.2, course=0.2, block=0.36, gap=0.02, jit=0.012, hole=None, batter=0.0):
    """A straight wall of coursed blocks (running bond) from p0 to p1 (x, y), z0 to z1, `th` thick, with openings:
    hole(z) -> [(s0, s1), ...], the spans (distances from p0 along the wall) left open at height z. Blocks beside an
    opening are cut to it (top and bottom edge each), so a pointed arch's curve is followed course by course.
    batter: how much thinner the wall is at the top (each face leans in by half of it)."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    d = p1 - p0
    length = d.length
    ax = d.normalized()
    nr = Vector((-ax.y, ax.x, 0))
    rows = max(1, round((z1 - z0) / course))
    hh = (z1 - z0) / rows
    cols = max(1, round(length / block))
    bw = length / cols

    def spans(z):
        return list(hole(z) or []) if hole else []

    def emit(a0, b0, a1, b1, za, zb, t0, t1):
        if b0 - a0 < 0.012 and b1 - a1 < 0.012:
            return
        vs = []
        for z, a, b, t in ((za, a0, b0, t0), (zb, a1, b1, t1)):
            for s, side in ((a, -1), (b, -1), (b, 1), (a, 1)):
                q = p0 + ax * s + nr * (side * t)
                vs.append(bm.verts.new((q.x, q.y, z)))
        lo, hi = vs[:4], vs[4:]
        fs = [bm.faces.new(list(reversed(lo))), bm.faces.new(hi)]
        for i in range(4):
            j = (i + 1) % 4
            fs.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))

    for k in range(rows):
        edges = [0.0] + [min(length, (i + (0.5 if k % 2 else 0.0)) * bw) for i in range(1, cols + (1 if k % 2 else 0))] + [length]
        edges = sorted(set(round(e, 5) for e in edges))
        zlo, zhi = z0 + k * hh, z0 + (k + 1) * hh
        s_lo, s_hi = spans(zlo + 0.02), spans(zhi - 0.03)
        for a, b in zip(edges, edges[1:]):
            if b - a < gap * 2:
                continue
            j = rnd.uniform(-jit, jit)
            fa, fb = (zlo - z0) / max(z1 - z0, 1e-6), (zhi - z0) / max(z1 - z0, 1e-6)
            t0, t1 = th * 0.5 - batter * 0.5 * fa + j, th * 0.5 - batter * 0.5 * fb + j
            za, zb = zlo + rnd.uniform(0, jit * 0.5), zhi - gap * 0.6
            a, b = a + gap * 0.5, b - gap * 0.5
            pieces = [(a, b, a, b)]                      # (bottom from, to, top from, to)
            holes = []
            for (h0, h1) in s_lo:                        # pair each opening at the bottom with itself at the top
                top = next(((u, v) for (u, v) in s_hi if u < h1 and v > h0), None)
                holes.append((h0, h1) + (top if top else ((h0 + h1) * 0.5,) * 2))
            for (u, v) in s_hi:
                if not any(u < h1 and v > h0 for (h0, h1) in s_lo):
                    holes.append(((u + v) * 0.5,) * 2 + (u, v))
            for (h0, h1, g0, g1) in holes:
                nxt = []
                for (pa, pb, qa, qb) in pieces:
                    if (h1 <= pa and g1 <= qa) or (h0 >= pb and g0 >= qb):
                        nxt.append((pa, pb, qa, qb))
                        continue
                    la, lb = min(pb, h0 - gap * 0.5), min(qb, g0 - gap * 0.5)          # what's left of the opening
                    if la - pa > 0.03 or lb - qa > 0.03:
                        nxt.append((pa, max(la, pa + 0.004), qa, max(lb, qa + 0.004)))
                    ra, rb = max(pa, h1 + gap * 0.5), max(qa, g1 + gap * 0.5)          # ... and right of it
                    if pb - ra > 0.03 or qb - rb > 0.03:
                        nxt.append((min(ra, pb - 0.004), pb, min(rb, qb - 0.004), qb))
                pieces = nxt
            for (pa, pb, qa, qb) in pieces:
                emit(pa, pb, qa, qb, za, zb, t0, t1)
    return bm


def arch_half_width(w, spring, k, h):
    """Half the width of a pointed arch's opening (w wide, straight to `spring`, arcs of radius k*w) at height h
    above its sill, or None above its point."""
    if h < spring:
        return w * 0.5
    R = w * k
    xc = R - w * 0.5
    y = h - spring
    if y >= math.sqrt(max(R * R - xc * xc, 0.0)):
        return None
    return math.sqrt(R * R - y * y) - xc


def arch_hole(sc, sill, w, spring, k=0.9):
    """A hole(z) for gs_block_wall: a pointed-arch opening centred sc along the wall, its sill at height `sill`."""
    def hole(z):
        if z < sill:
            return []
        hw = arch_half_width(w, spring, k, z - sill)
        return [] if hw is None else [(sc - hw, sc + hw)]
    return hole


def gs_pointed_arch(bm, c, right, w, spring, th=0.1, depth=0.2, n=4, k=0.9, jambs=True, sill=0.0, key=True):
    """A pointed (gothic) arch standing on c (the middle of its sill): an opening w wide, straight up to `spring`,
    then two arcs of radius k * w meeting in a point, n wedge stones a side and a keystone. right: along the wall;
    depth: through the wall; th: the stones' size; sill: a sill stone this thick under it. Returns the point's height
    above c."""
    c = Vector(c)
    rt = Vector(right).normalized()
    up = Vector((0, 0, 1))
    out = rt.cross(up)
    R = w * k
    xc = R - w * 0.5
    a_top = math.acos(min(max(xc / R, -1.0), 1.0))

    def stone(*ps):
        vs = [bm.verts.new(p + out * (depth * 0.5)) for p in ps] + [bm.verts.new(p - out * (depth * 0.5)) for p in ps]
        m = len(ps)
        fs = [bm.faces.new(vs[:m]), bm.faces.new(list(reversed(vs[m:])))]
        for i in range(m):
            j = (i + 1) % m
            fs.append(bm.faces.new((vs[j], vs[i], vs[m + i], vs[m + j])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    r = w * 0.5
    if jambs:
        for s in (-1, 1):
            stone(c + rt * (s * r), c + rt * (s * (r + th)), c + rt * (s * (r + th)) + up * spring, c + rt * (s * r) + up * spring)
    if sill > 0.0:
        stone(c - rt * (r + th * 1.3) - up * sill, c + rt * (r + th * 1.3) - up * sill, c + rt * (r + th * 1.3), c - rt * (r + th * 1.3))
    o = c + up * spring
    tops = {}
    for s in (-1, 1):
        cen = o - rt * (s * xc)
        pin = lambda a, rr, s=s, cen=cen: cen + rt * (s * math.cos(a) * rr) + up * (math.sin(a) * rr)
        for i in range(n):
            a0 = a_top * i / n + 0.014
            a1 = a_top * (i + 1) / n - (0.014 if i < n - 1 else 0.0)
            stone(pin(a0, R), pin(a0, R + th), pin(a1, R + th), pin(a1, R))
        tops[s] = pin(a_top, R + th)
    apex = math.sqrt(max(R * R - xc * xc, 0.0))
    if key:
        pk = o + up * apex
        stone(pk - up * 0.004, tops[1] + up * 0.0, pk + up * (th * 1.55), tops[-1])
    return spring + apex


def gs_step(kit, rnd, pts, z0, z1, stone="stone:0.3:0.9", core="stone_dark:0.35:0.95", block=0.42, th=0.16, course=None, batter=0.0):
    """One step of a dais (or a low wall round a shape): coursed blocks along the outline pts (counterclockwise), over
    a dark core that fills it."""
    n = len(pts)
    for i in range(n):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % n])
        p, q = Vector(pts[i - 1]), Vector(pts[(i + 2) % n])
        d = (b - a).normalized()
        nr = Vector((-d.y, d.x, 0))
        a2, b2 = a, b
        if (a - p).normalized().cross(d).z < -1e-4:       # a reflex corner: run on into it, so no notch is left
            a2 = a - d * (th * 0.6)
        if d.cross((q - b).normalized()).z < -1e-4:
            b2 = b + d * (th * 0.6)
        gs_block_wall(kit[stone], rnd, a2 + nr * (th * 0.5), b2 + nr * (th * 0.5), z0, z1, th=th, course=course or (z1 - z0), block=block, batter=batter)
    if core:
        prism(kit[core], gs_inset([Vector(p) for p in pts], th * 0.7), z0, z1 - 0.012)


def gs_hull(bm, pts):
    """The convex hull of pts as a closed, outward-facing chunk (wedges, caps, splinters of stone)."""
    vs = [bm.verts.new(Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = [e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def gs_buttress(kit, rnd, foot, out, z0, stages, width=0.17, stone="stone:0.3:0.95", cap="stone_dark:0.0:0.55", course=0.2, slope=0.1):
    """A stepped buttress against a wall: foot (x, y) on the wall's face, standing out along `out`. stages:
    [(height, depth), ...] from the ground up; each ends in a sloped weathering stone down to the next one's depth
    (the last dies into the wall)."""
    f = Vector((foot[0], foot[1], 0))
    o = Vector((out[0], out[1], 0)).normalized()
    s = Vector((-o.y, o.x, 0)) * (width * 0.5)
    z = z0
    for i, (h, dep) in enumerate(stages):
        nxt = stages[i + 1][1] if i + 1 < len(stages) else 0.0
        rows = max(1, round((h - slope) / course))
        hh = (h - slope) / rows
        for r in range(rows):
            j = rnd.uniform(-0.008, 0.008)
            za, zb = z + r * hh + 0.004, z + (r + 1) * hh - 0.012
            gs_hull(kit[stone], [f - o * 0.03 + s * sg + Vector((0, 0, zz)) for sg in (-1, 1) for zz in (za, zb)] +
                    [f + o * (dep + j) + s * sg + Vector((0, 0, zz)) for sg in (-1, 1) for zz in (za, zb)])
        zt = z + h - slope
        w2 = s * 1.08
        gs_hull(kit[cap], [f - o * 0.03 + w2 * sg + Vector((0, 0, zt)) for sg in (-1, 1)] + [f + o * (dep + 0.02) + w2 * sg + Vector((0, 0, zt)) for sg in (-1, 1)] +
                [f - o * 0.03 + w2 * sg + Vector((0, 0, zt + slope)) for sg in (-1, 1)] +
                [f + o * (nxt + 0.012) + w2 * sg + Vector((0, 0, zt + slope * (0.95 if nxt > 0 else 1.0))) for sg in (-1, 1)])
        z += h


def gs_rect(cx, cy, hx, hy, rot=0.0):
    """A rectangle's corners (counterclockwise), turned by rot degrees."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [Vector((cx + x * c - y * s, cy + x * s + y * c, 0)) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def gs_gargoyle(kit, M, stone="stone_dark:0.0:0.7", eye=None):
    """A horned beast-head spout 1.0 long, jutting along +Y from the origin (its root inside the wall), placed by M."""
    b = kit[stone]
    e = kit[eye] if eye else b
    with Stamp(M, b, e):
        bm_beam(b, (0, -0.15, 0.0), (0, 0.45, 0.06), 0.4, 0.4, w1=0.38, h1=0.36)                    # neck
        bm_beam(b, (0, 0.38, 0.09), (0, 1.0, -0.02), 0.42, 0.32, w1=0.22, h1=0.16)                  # skull and snout
        bm_beam(b, (0, 0.42, -0.14), (0, 0.93, -0.3), 0.3, 0.1, w1=0.17, h1=0.06)                   # the jaw, agape
        bm_box(b, (0.48, 0.14, 0.09), (0, 0.5, 0.27), (18, 0, 0))                                   # brow
        for sx in (-1, 1):
            bm_crystal(b, (sx * 0.16, 0.36, 0.2), (sx * 0.4, 0.02, 0.66), 0.1, n=4, shoulder=0.3)   # horns
            bm_beam(b, (sx * 0.2, 0.3, 0.05), (sx * 0.44, 0.22, 0.2), 0.05, 0.22, w1=0.03, h1=0.08)   # ears
            bm_box(e, (0.05, 0.1, 0.07), (sx * 0.185, 0.6, 0.13), (0, 0, sx * -9))                  # eyes
            bm_cyl(b, 0.035, 0.0, 0.13, (sx * 0.075, 0.9, -0.13), rot=(180, 0, 0), seg=4)             # fangs


def gs_wedge(bm, c, a0, a1, r_in, r_out, z0, z1):
    """A block between two angles (radians) and two radii round c: a piece of a ring."""
    c = Vector(c)
    vs = []
    for z in (z0, z1):
        for r, a in ((r_in, a0), (r_out, a0), (r_out, a1), (r_in, a1)):
            vs.append(bm.verts.new((c.x + r * math.cos(a), c.y + r * math.sin(a), z)))
    lo, hi = vs[:4], vs[4:]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def gs_lathe(bm, c, profile, n=12, phase=0.0, tip0=None, tip1=None, cap0=False, cap1=False):
    """Turns a profile [(radius, height), ...] round the vertical through c (pots, bowls, barrels, bottles). tip0 /
    tip1: a height at which the first / last ring closes to a point on the axis. The first band must not be flat."""
    c = Vector(c)
    rings = [[c + Vector((math.cos(2 * math.pi * (i + phase) / n) * r, math.sin(2 * math.pi * (i + phase) / n) * r, z)) for i in range(n)]
             for r, z in profile]
    return bm_loft(bm, rings, cap0=cap0, cap1=cap1, tip0=None if tip0 is None else c + Vector((0, 0, tip0)),
                   tip1=None if tip1 is None else c + Vector((0, 0, tip1)))


def gs_barrel(kit, c, r=0.2, h=0.4, n=10, wood="wood:0.3:0.9", hoop=IRON, fill=None, hoops=(0.22, 0.78)):
    """A stave barrel standing on c (r at its belly), iron-hooped. fill: a glow key for what brims in it (an open
    vat); None: a lid."""
    c = Vector(c)
    gs_lathe(kit[wood], c, [(r * 0.84, 0.0), (r, h * 0.33), (r, h * 0.67), (r * 0.86, h), (r * 0.72, h), (r * 0.7, h * 0.86)], n=n, cap0=True,
             cap1=fill is None)
    if fill:
        bm_cyl(kit[fill], r * 0.72, r * 0.72, 0.02, (c.x, c.y, c.z + h * 0.9), seg=n)
    for t in hoops:
        rr = r * (0.84 + 0.16 * min(1.0, min(t, 1.0 - t) * 3.0)) + 0.008
        gs_lathe(kit[hoop], c, [(rr, h * t - 0.022), (rr + 0.004, h * t), (rr, h * t + 0.022)], n=n)


def gs_bottle(kit, c, h=0.2, r=0.05, glass="teal:0.2:0.9", cork="sand:0.3:0.7", n=6, squat=False):
    """A bottle standing on c: a body, a neck, a cork. glass may be a glow key (a potion that shines)."""
    c = Vector(c)
    if squat:
        prof = [(r * 0.7, 0.0), (r, h * 0.2), (r, h * 0.42), (r * 0.32, h * 0.62), (r * 0.32, h * 0.86)]
    else:
        prof = [(r * 0.9, 0.0), (r, h * 0.08), (r, h * 0.52), (r * 0.36, h * 0.68), (r * 0.36, h * 0.86)]
    gs_lathe(kit[glass], c, prof, n=n, cap0=True, cap1=True)
    bm_cyl(kit[cork], r * 0.3, r * 0.4, h * 0.16, (c.x, c.y, c.z + h * 0.92), seg=5)


# ------------------------------------------------------------------------------------------- cloth
def gs_banner(bm, top, right, down, w, l, rnd=None, cols=6, rows=4, tatter=0.3, taper=1.0, th=0.012, notch=0.0):
    """A torn cloth (both faces): its attached edge is centred on `top` and runs w along `right`; it reaches l along
    `down`, where it ends in uneven points. taper: its width at the far end; notch: a swallow-tail cut this deep."""
    rnd = rnd or random.Random(9)
    top, rt, dn = Vector(top), Vector(right).normalized(), Vector(down).normalized()
    nrm = rt.cross(dn).normalized()
    ends = []
    for i in range(cols + 1):
        u = i / cols
        e = 1.0 - tatter * (rnd.uniform(0.55, 1.0) if i % 2 else rnd.uniform(0.0, 0.25))
        e -= notch * (1.0 - abs(u - 0.5) * 2.0)
        ends.append(l * e)
    for side in (1, -1):
        off = nrm * (th * 0.5 * side)
        grid = []
        for i in range(cols + 1):
            x = -w * 0.5 + w * i / cols
            col = []
            for j in range(rows + 1):
                t = j / rows
                col.append(bm.verts.new(top + rt * (x * (1.0 - (1.0 - taper) * t)) + dn * (ends[i] * t) + off))
            grid.append(col)
        for i in range(cols):
            for j in range(rows):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if side > 0 else tuple(reversed(f)))
    return bm


def gs_cloth(bm, p00, p10, p11, p01, nx=4, ny=4, sag=0.05, rnd=None, th=0.014, ragged=0.0):
    """A sheet of cloth (both faces) between four corners (going round), sagging in the middle; ragged: how far its
    edges wander."""
    rnd = rnd or random.Random(6)
    p00, p10, p11, p01 = Vector(p00), Vector(p10), Vector(p11), Vector(p01)
    nrm = (p10 - p00).cross(p01 - p00).normalized()
    if nrm.z < 0:
        nrm = -nrm
    pts = []
    for i in range(nx + 1):
        row = []
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            p = p00.lerp(p10, u).lerp(p01.lerp(p11, u), v)
            edge = (i in (0, nx)) or (j in (0, ny))
            p.z -= sag * math.sin(math.pi * u) * math.sin(math.pi * v) * rnd.uniform(0.7, 1.2)
            if edge and ragged > 0.0:
                p += Vector((rnd.uniform(-ragged, ragged), rnd.uniform(-ragged, ragged), 0))
            row.append(p)
        pts.append(row)
    for side in (1, -1):
        off = nrm * (th * 0.5 * side)
        grid = [[bm.verts.new(p + off) for p in row] for row in pts]
        for i in range(nx):
            for j in range(ny):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                face = bm.faces.new(f)
                face.normal_update()
                if (face.normal.dot(nrm) > 0) != (side > 0):
                    face.normal_flip()
    return bm


def sway(rig, name, deg, segs=3, axis=(0, 1, 0), lag=0.0, phase=0.0):
    """Poses a flag_bones() chain: every bone turned `deg` (more toward the free end) about an armature-space axis,
    the later bones `lag` of a cycle behind (phase 0..1)."""
    pb = rig.pose.bones
    for k in range(segs):
        b = pb["%s.%d" % (name, k + 1)]
        b.rotation_quaternion = arm_space_quat(b, axis, deg * (0.6 + 0.4 * k) * math.sin(2 * math.pi * (phase - lag * k)))


# ------------------------------------------------------------------------------------------- growth
def gs_vine(kit, rnd, pts, r=0.022, wood="wood_dark:0.3:0.9", leaf="taupe:0.2:0.9", leaves=5, out=(0, -1, 0), size=0.07):
    """Dead ivy: a wiry stem through pts with a few withered leaves standing off the wall along `out`."""
    pts = [Vector(p) for p in pts]
    bm_tube(kit[wood], pts, [r] * (len(pts) - 1) + [r * 0.4], n=4)
    o = Vector(out).normalized()
    lf = kit[leaf]
    for i in range(leaves):
        t = rnd.uniform(0.1, 0.98) * (len(pts) - 1)
        k = min(int(t), len(pts) - 2)
        p = pts[k].lerp(pts[k + 1], t - k)
        side = (pts[k + 1] - pts[k]).normalized().cross(o)
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side = side.normalized() * rnd.choice((-1, 1))
        s = size * rnd.uniform(0.7, 1.2)
        a = p + o * (r * 0.8)
        tip = a + side * s * 1.5 + o * s * 0.5 + Vector((0, 0, -s * 0.9))
        bm_beam(lf, a, tip, s * 0.9, 0.012, w1=0.012, h1=0.008, up=tuple(o))
    return pts


# ------------------------------------------------------------------------------------------- preview only
def gs_standin(loc, yaw=0.0, h=1.0, parent=None, name="Crew_Standin"):
    """A grey mannequin in the Guides collection where the game stands a KayKit character: it's in the preview renders
    only (the Guides collection isn't exported, counted or shaded), and only made when GS_STANDIN=1 is set (the final
    builds are plain)."""
    import os
    if not os.environ.get("GS_STANDIN"):
        return None
    guides = collection("Guides")
    bm = bmesh.new()
    s = h
    bm_box(bm, (0.13 * s, 0.13 * s, 0.34 * s), (-0.09 * s, 0, 0.17 * s))
    bm_box(bm, (0.13 * s, 0.13 * s, 0.34 * s), (0.09 * s, 0, 0.17 * s))
    bm_box(bm, (0.36 * s, 0.2 * s, 0.3 * s), (0, 0, 0.47 * s))
    bm_ellipsoid(bm, (0, 0.01 * s, 0.8 * s), (0.2 * s, 0.2 * s, 0.2 * s), u=8, v=5)
    bm_beam(bm, (-0.24 * s, 0, 0.56 * s), (-0.1 * s, 0.34 * s, 0.5 * s), 0.09 * s, 0.09 * s)
    bm_beam(bm, (0.24 * s, 0, 0.56 * s), (0.1 * s, 0.34 * s, 0.5 * s), 0.09 * s, 0.09 * s)
    o = mesh_obj(name, bm, guides, parent, loc)
    o.rotation_euler = (0, 0, math.radians(yaw))
    paint(o, "stone", lo=0.0, hi=0.5)
    o["no_ao"] = True
    return o
