"""The Verdant great trees' shared pieces (Elder Treant, Briar Thicket, Stormcaller Oak, Rootbinder Shrine, Heart of
the Forest): buttressed trunks with bark plates, roots that sprawl and grip, foliage pads, mushrooms and ferns, carved
standing stones with glowing runes, thorny canes and roses, rough stones, candles and lanterns.
Exec'd by a tower script after kk_helpers.py.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

SPIRIT = (0.35, 1.0, 0.45)          # the Verdant's soft green glow
BARK = "taupe_dark:0.5:1.0"        # a trunk's body (dark in the furrows)
BARK_PLATE = "wood:0.45:1.0"        # the raised plates on it
BARK_PALE = "sand:0.3:0.75"         # split, broken or carved wood
LEAF_A = "grass:0.05:0.8"
LEAF_B = "teal:0.1:0.8"
LEAF_C = "lime:0.0:0.55"
LEAF_TOP = "grass:0.0:0.5"
MOSS = "grass:0.35:0.85"
ROOT = "taupe_dark:0.2:0.8"          # roots on the ground (lighter than a trunk's furrows)


def spline_pts(pts, sub=3):
    """A smooth curve (Catmull-Rom) through pts: `sub` points per span, plus the last point."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    if n < 3 or sub < 2:
        return pts
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def resample(vals, m):
    """A list of numbers stretched (linearly) to m values; one number repeats."""
    if isinstance(vals, (int, float)):
        return [vals] * m
    n = len(vals)
    if n == m:
        return list(vals)
    out = []
    for i in range(m):
        t = i / max(m - 1, 1) * (n - 1)
        a = min(int(t), n - 2)
        out.append(vals[a] + (vals[a + 1] - vals[a]) * (t - a))
    return out


def ring_co(vr):
    """bm_loft / bm_tube's vertex rings as lists of points (for bm_plates, wraps and the like)."""
    return [[v.co.copy() for v in r] for r in vr]


# ---------------------------------------------------------------------------------------------- trunks and roots
class Trunk:
    """A trunk as a loft whose outline flares into buttress lobes toward its roots.
    sections: [(z, rx, ry, flare[, dx, dy])] from the foot up (flare: how much of the lobes shows at that height);
    angles: the outline's vertex angles (degrees, counterclockwise); lobes: {angle: amp}: there the radius is
    x (1 + amp * flare), so amp > 0 makes a buttress and amp < 0 a furrow."""

    def __init__(self, c, sections, angles, lobes=None, rnd=None, jit=0.0, power=2.0):
        self.c = Vector(c)
        self.angles = list(angles)
        self.sections = [tuple(s) if len(s) >= 6 else tuple(s) + (0.0, 0.0) for s in sections]
        lobes = lobes or {}
        e = 2.0 / power
        self.rings, self.mids = [], []
        for (z, rx, ry, fl, dx, dy) in self.sections:
            row = []
            for a in self.angles:
                k = 1.0 + lobes.get(a, 0.0) * fl + (rnd.uniform(-jit, jit) if rnd else 0.0)
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                row.append(self.c + Vector((dx + math.copysign(abs(ca) ** e, ca) * rx * k, dy + math.copysign(abs(sa) ** e, sa) * ry * k, z)))
            self.rings.append(row)
            self.mids.append(self.c + Vector((dx, dy, z)))

    def loft(self, bm, cap0=True, cap1=True):
        return bm_loft(bm, self.rings, cap0=cap0, cap1=cap1)

    def _row(self, z):
        zs = [s[0] for s in self.sections]
        z = min(max(z, zs[0]), zs[-1])
        for i in range(len(zs) - 1):
            if z <= zs[i + 1]:
                f = (z - zs[i]) / max(zs[i + 1] - zs[i], 1e-6)
                return [a.lerp(b, f) for a, b in zip(self.rings[i], self.rings[i + 1])], self.mids[i].lerp(self.mids[i + 1], f)
        return self.rings[-1], self.mids[-1]

    def at(self, a, z, out=0.0):
        """The point on the trunk's surface at angle a (degrees) and height z (above the trunk's c), pushed `out`."""
        row, mid = self._row(z)
        n = len(self.angles)
        a = (a - self.angles[0]) % 360.0 + self.angles[0]
        p = row[-1]
        for i in range(n):
            a0 = self.angles[i]
            a1 = self.angles[(i + 1) % n] + (360.0 if i == n - 1 else 0.0)
            if a0 <= a <= a1:
                p = row[i].lerp(row[(i + 1) % n], (a - a0) / max(a1 - a0, 1e-6))
                break
        d = Vector((p.x - mid.x, p.y - mid.y, 0))
        return p + d.normalized() * out if d.length > 1e-6 else p

    def out(self, a):
        return Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))


def bm_plates(bm, rings, rnd, th=(0.03, 0.06), rows=(0.7, 1.4), gap=0.1, side=0.1, keep=0.9, skip=None, start=0.0, end=None, cols=None,
              point=0.0, nar=0.3):
    """Bark plates (scales, armour) over a loft: slabs lying on the faces between its rings, column by column, each a
    random length (rows: in ring spacings) with furrows between. rings: lists of points as given to bm_loft.
    point: the share of a plate's length that narrows toward each end (0: square ends; 0.3: long six-sided scales of
    bark, their ends `nar` of their width and a little askew); skip(center) -> True leaves a plate out; cols: only
    these columns. Returns the number of plates."""
    m, n = len(rings), len(rings[0])
    end = (m - 1) if end is None else min(end, m - 1)
    cen = [sum(r, Vector()) / n for r in rings]
    made = 0

    def edge(j, s, u):
        i = min(int(s), m - 2)
        f = s - i
        a = rings[i][j].lerp(rings[i + 1][j], f)
        b = rings[i][(j + 1) % n].lerp(rings[i + 1][(j + 1) % n], f)
        return a.lerp(b, u), b - a, i

    for j in (cols if cols is not None else range(n)):
        s = start + rnd.uniform(0.0, 0.25)
        while s < end - 0.2:
            s1 = min(s + rnd.uniform(*rows), end)
            if s1 - s < 0.22:
                break
            if rnd.random() < keep:
                pt = point * (s1 - s)
                marks = [(s, 0.0)] + ([(s + pt, 1.0), (s1 - pt, 1.0)] if pt > 0.02 else []) + [(s1, 0.0)]
                lo, hi = (s + pt, s1 - pt) if pt > 0.02 else (s, s1)
                marks += [(float(i), 1.0) for i in range(int(math.floor(lo)) + 1, int(math.ceil(hi))) if lo + 0.1 < i < hi - 0.1]
                marks.sort()
                u0, u1 = side * rnd.uniform(0.6, 1.5), 1.0 - side * rnd.uniform(0.6, 1.5)
                t = rnd.uniform(*th)
                secs, mid = [], Vector()
                for q, (sc, full) in enumerate(marks):
                    ua, ub = u0, u1
                    if pt > 0.02 and full < 0.5:                # a narrowed, skewed end
                        c = (u0 + u1) * 0.5 + (u1 - u0) * rnd.uniform(-0.28, 0.28)
                        ua, ub = c - (u1 - u0) * nar * 0.5, c + (u1 - u0) * nar * 0.5
                    pl, across, i = edge(j, sc, ua)
                    pr = edge(j, sc, ub)[0]
                    along = (rings[i + 1][j] + rings[i + 1][(j + 1) % n]) * 0.5 - (rings[i][j] + rings[i][(j + 1) % n]) * 0.5
                    nrm = across.cross(along)
                    if nrm.length < 1e-9:
                        nrm = (pl + pr) * 0.5 - cen[i]
                    nrm.normalize()
                    if nrm.dot((pl + pr) * 0.5 - cen[i].lerp(cen[i + 1], sc - i)) < 0:
                        nrm = -nrm
                    tt = t * (0.45 if (pt > 0.02 and full < 0.5) else 1.0)
                    secs.append([pl + nrm * tt, pr + nrm * tt, pr - nrm * 0.03, pl - nrm * 0.03])
                    mid += (pl + pr) * 0.5
                if (pl - pr).length > 0.015 and (skip is None or not skip(mid / len(marks))):
                    bm_loft(bm, secs)
                    made += 1
            s = s1 + gap * rnd.uniform(0.6, 1.6)
    return made


def tri_report(col, top=14):
    """Prints the heaviest meshes of a tower (as built, before the shade bake's refinement): where the triangles go."""
    rows = []
    for o in col.all_objects:
        if o.type == "MESH":
            rows.append((sum(len(p.vertices) - 2 for p in o.data.polygons), o.name))
    rows.sort(reverse=True)
    print("TRIS total", sum(r[0] for r in rows), " ".join("%s=%d" % (nm, t) for t, nm in rows[:top]))


def bm_root(bm, ctrl, radii, n=6, sub=3, squash=1.0, phase=0.0, cap=True):
    """A root (branch, vine, cane) as a tube along the smooth curve through ctrl; radii: at the control points (0 at
    an end draws it to a point). Returns (curve points, their radii, the tube's rings as points)."""
    pts = spline_pts(ctrl, sub)
    rad = resample(radii, len(pts))
    vr = bm_tube(bm, pts, rad, n=n, cap=cap, squash=squash, phase=phase)
    return pts, rad, ring_co(vr)


def bm_claw(bm, p, d, r, rnd, toes=3, reach=0.3, T=0.0, spread=38.0, n=5):
    """Where a root ends: it forks into toes that spread, hump and dig into the ground (at height T) like talons."""
    p = Vector(p)
    d = Vector((d[0], d[1], 0)).normalized()
    for i in range(toes):
        a = math.radians(spread * ((i - (toes - 1) * 0.5) / max(toes - 1, 1) * 2.0) + rnd.uniform(-8, 8))
        dd = Vector((d.x * math.cos(a) - d.y * math.sin(a), d.x * math.sin(a) + d.y * math.cos(a), 0))
        L = reach * rnd.uniform(0.8, 1.2)
        knee = Vector((p.x, p.y, 0)) + dd * L * 0.55 + Vector((0, 0, T + r * 1.1))
        tip = Vector((p.x, p.y, 0)) + dd * L + Vector((0, 0, T - 0.05))
        bm_tube(bm, [p - dd * r * 0.5, p.lerp(knee, 0.5) + Vector((0, 0, r * 0.25)), knee, tip], [r * 0.8, r * 0.74, r * 0.55, 0.0], n=n)
    return bm


# ---------------------------------------------------------------------------------------------- growth
def bm_mushroom(kit, rnd, base, h=0.25, r=0.16, cap="orange:0.1:0.75", stalk="cream:0.25:0.8", lean=(0.0, 0.0), spots=None, n=7):
    """A toadstool on `base`: a bent stalk and a domed cap (spots: a swatch for flecks on the cap, or None)."""
    base = Vector(base)
    top = base + Vector((lean[0], lean[1], h))
    small = r < 0.15
    bm_tube(kit[stalk], [base - Vector((0, 0, 0.04))] + ([] if small else [base.lerp(top, 0.5) + Vector((lean[0] * 0.2, lean[1] * 0.2, 0))]) + [top],
            [r * 0.34, r * 0.22] if small else [r * 0.34, r * 0.24, r * 0.22], n=4 if small else 5)
    x, y = Vector((1, 0, 0)), Vector((0, 1, 0))
    prof = ((-r * 0.08, r), (r * 0.36, r * 0.62)) if small else ((-r * 0.1, r * 0.92), (r * 0.02, r), (r * 0.3, r * 0.8), (r * 0.52, r * 0.42))
    rows = [oval(top + Vector((0, 0, dz)), x, y, rr, rr, n) for dz, rr in prof]
    bm_loft(kit[cap], rows, cap0=True, cap1=False, tip1=top + Vector((0, 0, r * 0.62)))
    if spots:
        for i in range(3):
            a = rnd.uniform(0, 6.283)
            q = top + Vector((math.cos(a) * r * 0.55, math.sin(a) * r * 0.55, r * 0.44))
            bm_box(kit[spots], (r * 0.24, r * 0.24, r * 0.14), tuple(q), (rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 90)))
    return top


def bm_shelf(bm, p, out, r=0.16, th=0.05, n=7, tilt=0.0):
    """A bracket fungus: half a thick disc standing out of a trunk at p (out: the trunk's outward direction there)."""
    p, o = Vector(p), Vector(out).normalized()
    s = Vector((-o.y, o.x, 0))
    top, bot = [], []
    for i in range(n + 1):
        a = math.pi * i / n
        q = p + s * (math.cos(a) * r) + o * (math.sin(a) * r * 0.85 - r * 0.15)
        top.append(bm.verts.new(q + Vector((0, 0, th * 0.5 + tilt * math.sin(a)))))
        bot.append(bm.verts.new(q + Vector((0, 0, -th * 0.5 + tilt * math.sin(a))) - o * (math.sin(a) * r * 0.2)))
    fs = [bm.faces.new(top), bm.faces.new(list(reversed(bot)))]
    for i in range(n):
        fs.append(bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def bm_fern(bm, rnd, base, n=6, length=0.4, rise=0.28, w=0.1):
    """A fern: n fronds arching up and out from base (thin blades with both faces)."""
    base = Vector(base)
    for i in range(n):
        a = 2 * math.pi * (i + rnd.uniform(-0.25, 0.25)) / n
        d = Vector((math.cos(a), math.sin(a), 0))
        s = Vector((-d.y, d.x, 0))
        L = length * rnd.uniform(0.75, 1.15)
        p1 = base + d * L * 0.5 + Vector((0, 0, rise * rnd.uniform(0.8, 1.2)))
        p2 = base + d * L + Vector((0, 0, rise * 0.3))
        for side, dz in ((1, 0.004), (-1, -0.004)):
            o = Vector((0, 0, dz))
            q = [bm.verts.new(v + o) for v in (base + s * w * 0.25, base - s * w * 0.25, p1 - s * w * 0.5, p1 + s * w * 0.5)]
            t = [q[2], bm.verts.new(p2 + o), q[3]]
            bm.faces.new(q if side > 0 else list(reversed(q)))
            bm.faces.new(t if side > 0 else list(reversed(t)))
    return bm


def bm_leaf(bm, base, tip, w, up=(0, 0, 1)):
    """A flat pointed leaf from base to tip (a rhombus with both faces), `w` wide, lying across `up`."""
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    side = d.cross(Vector(up))
    if side.length < 1e-6:
        side = d.orthogonal()
    side = side.normalized() * (w * 0.5)
    nrm = side.cross(d).normalized() * 0.005
    mid = base + d * 0.45
    for s in (1, -1):
        vs = [bm.verts.new(p + nrm * s) for p in (base, mid + side, tip, mid - side)]
        bm.faces.new(vs if s > 0 else list(reversed(vs)))
    return bm


def bm_sprig(bm, rnd, p, d, n=3, size=0.14):
    """A few leaves fanning out from p round direction d (a twig's tuft)."""
    p, d = Vector(p), Vector(d).normalized()
    x = d.orthogonal().normalized()
    y = d.cross(x)
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.4, 0.4)
        dd = (d * 0.75 + (x * math.cos(a) + y * math.sin(a)) * 0.7).normalized()
        bm_leaf(bm, p, p + dd * size * rnd.uniform(0.8, 1.2), size * 0.5, up=d.cross(dd) if d.cross(dd).length > 1e-3 else x)
    return bm


def bm_thorn(bm, p, d, length, r, n=3):
    """A thorn: an open-bottomed spike from p along d (its foot sits inside whatever grows it)."""
    p, d = Vector(p), Vector(d).normalized()
    x = d.orthogonal().normalized()
    y = d.cross(x)
    base = [bm.verts.new(p + (x * math.cos(2 * math.pi * i / n) + y * math.sin(2 * math.pi * i / n)) * r) for i in range(n)]
    tip = bm.verts.new(p + d * length)
    for i in range(n):
        bm.faces.new((base[i], base[(i + 1) % n], tip))
    return bm


def bm_cane(cane_bm, thorn_bm, rnd, ctrl, radii, n=5, sub=3, every=0.24, tl=0.16, tr=0.045, squash=1.0, skip_ends=0.12, hook=0.25):
    """A thorny cane (briar, bramble) along the curve through ctrl, thorns standing off it all the way along.
    Returns (curve points, radii)."""
    pts = spline_pts(ctrl, sub)
    rad = resample(radii, len(pts))
    bm_tube(cane_bm, pts, rad, n=n, squash=squash)
    if thorn_bm is not None and every > 0:
        run, nxt, side = 0.0, every * rnd.uniform(0.3, 1.0), rnd.uniform(0, 6.283)
        total = sum((b - a).length for a, b in zip(pts, pts[1:]))
        for (a, b), ra, rb in zip(zip(pts, pts[1:]), rad, rad[1:]):
            seg = (b - a).length
            while nxt <= run + seg and seg > 1e-6:
                f = (nxt - run) / seg
                if skip_ends * total < nxt < (1.0 - skip_ends * 0.5) * total:
                    t = (b - a).normalized()
                    x = t.orthogonal().normalized()
                    y = t.cross(x)
                    side += rnd.uniform(1.6, 2.9)
                    o = x * math.cos(side) + y * math.sin(side)
                    if o.z < -0.35:              # (thorns under a cane are never seen)
                        o = -o
                    r = ra + (rb - ra) * f
                    k = rnd.uniform(0.75, 1.2)
                    bm_thorn(thorn_bm, a.lerp(b, f) + o * r * 0.5, o - t * hook, tl * k, max(tr * k, r * 0.5))
                nxt += every * rnd.uniform(0.7, 1.3)
            run += seg
    return pts, rad


def bm_rose(kit, rnd, c, r, up=(0, 0, 1), petal="red:0.5:0.95", heart="red:0.1:0.5", leaf=None):
    """A big briar rose at c, opening toward `up`: two rings of chunky petals round a tight bud (leaf: a swatch for
    a ruff of leaves under it)."""
    c, u = Vector(c), Vector(up).normalized()
    x = u.orthogonal().normalized()
    y = u.cross(x)
    ph = rnd.uniform(0, 6.283)
    for cnt, rr, lift, w, th, off in ((5, 1.0, 0.3, 0.86, 0.11, 0.0), (4, 0.62, 0.62, 0.6, 0.1, 0.5)):
        for i in range(cnt):
            a = ph + 2 * math.pi * (i + off) / cnt
            d = x * math.cos(a) + y * math.sin(a)
            p0 = c + d * r * 0.1 + u * r * (0.05 + lift * 0.2)
            p1 = c + d * r * rr + u * r * lift * rr * 1.2
            bm_beam(kit[petal], p0, p1, r * w * 0.5, r * th, w1=r * w, h1=r * th * 0.7, up=u)
    bm_blob(kit[heart], rnd, c + u * r * 0.42, r * 0.3, jitter=0.08)
    if leaf:
        for i in range(3):
            a = ph + 2 * math.pi * (i + 0.3) / 3
            d = x * math.cos(a) + y * math.sin(a)
            bm_leaf(kit[leaf], c - u * r * 0.05, c + d * r * 1.55 - u * r * 0.18, r * 0.75, up=u)
    return c


# ---------------------------------------------------------------------------------------------- stones
def bm_stone(bm, rnd, c, size, yaw=0.0, n=0, jit=0.16, sink=0.0):
    """A rough stone standing on c: the hull of a jittered box (n = 0: a block for a drystone wall, a slab, a step)
    or of n jittered points on an ellipsoid (a fieldstone), `size` (x, y, z) overall, turned by yaw degrees."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    hx, hy, hz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    pts = []
    if n <= 0:
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append(Vector((sx * hx * (1 + rnd.uniform(-jit, jit * 0.3)), sy * hy * (1 + rnd.uniform(-jit, jit * 0.3)),
                                       hz + sz * hz * (1 + rnd.uniform(-jit, jit * 0.3) * (1 if sz > 0 else 0)))))
    else:
        for i in range(n):
            u = (i + 0.5) / n
            z = 1.0 - 2.0 * u
            rad = math.sqrt(max(0.0, 1.0 - z * z))
            a = i * 2.39996 + rnd.uniform(-0.35, 0.35)
            k = rnd.uniform(1.0 - jit * 1.6, 1.0)
            pts.append(Vector((rad * math.cos(a) * hx * k, rad * math.sin(a) * hy * k, hz + z * hz * k)))
    vs = [bm.verts.new(c + rz @ Vector((p.x, p.y, max(p.z - sink, -0.03)))) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = [e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def bm_drystone(bm, rnd, path, z, h=0.42, th=0.32, stone=0.3, courses=3, skip=None):
    """A drystone wall along path (a list of points, any z ignored): courses of rough blocks with staggered joints,
    the top course of bigger flat capstones. skip(point) -> True leaves a gap (a gate). The wall stands on z."""
    path = [Vector((p[0], p[1], 0)) for p in path]
    lens = [(b - a).length for a, b in zip(path, path[1:])]
    total = sum(lens)

    def along(s):
        s = min(max(s, 0.0), total)
        for i, L in enumerate(lens):
            if s <= L or i == len(lens) - 1:
                d = (path[i + 1] - path[i]).normalized()
                return path[i] + d * min(s, L), d
            s -= L
    ch = h / courses
    for k in range(courses):
        top = k == courses - 1
        s = (0.5 if k % 2 else 0.0) * stone * rnd.uniform(0.8, 1.1)
        while s < total - stone * 0.3:
            L = stone * rnd.uniform(0.75, 1.3) * (1.25 if top else 1.0)
            L = min(L, total - s)
            p, d = along(s + L * 0.5)
            if L > stone * 0.3 and not (skip and skip(p)):
                yaw = math.degrees(math.atan2(d.y, d.x)) + rnd.uniform(-7, 7)
                side = Vector((-d.y, d.x, 0)) * rnd.uniform(-0.03, 0.03)
                w = th * rnd.uniform(0.85, 1.1) * (1.1 if top else 1.0)
                bm_stone(bm, rnd, (p.x + side.x, p.y + side.y, z + k * ch - 0.01), (L - 0.025, w, ch * rnd.uniform(0.95, 1.2)), yaw, jit=0.14)
            s += L
    return bm


RUNES = {   # strokes in a box: x -0.5..0.5 across, y 0..1 up
    "tree": [((0, 0), (0, 1)), ((0, 0.28), (-0.38, 0.6)), ((0, 0.28), (0.38, 0.6)), ((0, 0.6), (-0.26, 0.85)), ((0, 0.6), (0.26, 0.85))],
    "fork": [((0, 0), (0, 1)), ((0, 0.45), (-0.4, 0.95)), ((0, 0.45), (0.4, 0.95))],
    "arrow": [((0, 0), (0, 1)), ((0, 1), (-0.38, 0.62)), ((0, 1), (0.38, 0.62))],
    "eye": [((0, 0.12), (0.4, 0.5)), ((0.4, 0.5), (0, 0.88)), ((0, 0.88), (-0.4, 0.5)), ((-0.4, 0.5), (0, 0.12))],
    "bolt": [((0.3, 1), (-0.3, 0.62)), ((-0.3, 0.62), (0.3, 0.38)), ((0.3, 0.38), (-0.3, 0))],
    "home": [((-0.38, 0), (0.38, 0.62)), ((0.38, 0), (-0.38, 0.62)), ((-0.38, 0.62), (0, 1)), ((0.38, 0.62), (0, 1))],
    "coil": [((-0.4, 0.05), (0.4, 0.05)), ((0.4, 0.05), (0.4, 0.95)), ((0.4, 0.95), (-0.4, 0.95)), ((-0.4, 0.95), (-0.4, 0.35)),
             ((-0.4, 0.35), (0.12, 0.35)), ((0.12, 0.35), (0.12, 0.66))],
    "root": [((0, 1), (0, 0.4)), ((0, 0.4), (-0.36, 0)), ((0, 0.4), (0.36, 0)), ((0, 0.72), (-0.3, 0.42)), ((0, 0.72), (0.3, 0.42))],
    "sun": [((0, 0.25), (0.25, 0.5)), ((0.25, 0.5), (0, 0.75)), ((0, 0.75), (-0.25, 0.5)), ((-0.25, 0.5), (0, 0.25)),
            ((0, 0), (0, 0.14)), ((0, 0.86), (0, 1)), ((-0.5, 0.5), (-0.36, 0.5)), ((0.36, 0.5), (0.5, 0.5))],
}


def bm_menhir(kit, rnd, base, h, w=0.44, d=0.3, yaw=0.0, lean=(0.0, 0.0), stone="stone2:0.1:0.92", moss=MOSS, n=8, top=0.6, sink=0.14):
    """A weathered standing stone on `base`, h tall: a tapering slab, its carved face turned to yaw (degrees from +Y,
    counterclockwise), leaning (degrees: toward its face, to its right), moss on its head (moss: a swatch or None).
    Returns face(u, v) -> (point, out, up): a spot on the carved face (u -0.5..0.5 across, v 0..1 up) and the face's
    outward and upward directions there, for bm_rune and the like."""
    M = (Matrix.Translation(Vector(base)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(-lean[0]), 4, "X")
         @ Matrix.Rotation(math.radians(lean[1]), 4, "Y"))
    M3 = M.to_3x3()
    zs = [-sink, h * 0.3, h * 0.64, h * 0.9, h]
    ws = [1.0, 0.98, 0.88, top + 0.14, top * 0.72]
    slope = rnd.uniform(-0.35, 0.35)
    rows = []
    for i, (z, k) in enumerate(zip(zs, ws)):
        cx, cy = rnd.uniform(-0.02, 0.02) * (i > 0), rnd.uniform(-0.015, 0.015) * (i > 0)
        rx, ry = w * 0.5 * k * rnd.uniform(0.95, 1.05), d * 0.5 * (0.55 + 0.45 * k) * rnd.uniform(0.95, 1.05)
        row = oval((cx, cy, z), (1, 0, 0), (0, 1, 0), rx, ry, n, power=3.6, phase=0.5)
        if i == len(zs) - 1:
            row = [Vector((p.x, p.y, p.z + slope * p.x - 0.02)) for p in row]
        rows.append(row)
    bm_loft(kit[stone], [[M @ p for p in row] for row in rows])
    if moss:
        tp = M @ Vector((0, 0, h))
        bm_blob(kit[moss], rnd, tp + Vector((0, 0, 0.0)), w * 0.36 * top / 0.6, squash=(1.15, 0.95, 0.42), jitter=0.16)
        q = M @ Vector((w * 0.3 * rnd.choice((-1, 1)), -d * 0.3, h * 0.86))
        bm_blob(kit[moss], rnd, q, w * 0.2, squash=(1.0, 1.0, 0.7), jitter=0.2)

    def face(u, v):
        z = min(max(v, zs[0]), zs[-1] - 1e-4)
        for i in range(len(zs) - 1):
            if z <= zs[i + 1]:
                f = (z - zs[i]) / (zs[i + 1] - zs[i])
                a0, b0 = rows[i][1], rows[i][2]                 # (the +Y facet runs from vertex 1, at +x, to vertex 2)
                a1, b1 = rows[i + 1][1], rows[i + 1][2]
                lo = a0.lerp(b0, 0.5 + min(max(u / max((b0 - a0).length, 1e-6), -0.47), 0.47))
                hi = a1.lerp(b1, 0.5 + min(max(u / max((b1 - a1).length, 1e-6), -0.47), 0.47))
                p = lo.lerp(hi, f)
                upv = ((a1 + b1) - (a0 + b0)).normalized()
                out = (b0 - a0).cross(upv).normalized()
                if out.y < 0:
                    out = -out
                return M @ p, (M3 @ out).normalized(), (M3 @ upv).normalized()
        return M @ Vector((0, d * 0.5, h)), M3 @ Vector((0, 1, 0)), M3 @ Vector((0, 0, 1))
    return face


def bm_rune(bm, name, face, z0, size=0.3, w=0.035, th=0.016, u0=0.0, aspect=0.8):
    """A carved rune (RUNES[name], or a list of strokes) on a face from bm_menhir: its foot z0 up the stone, `size`
    tall and size * aspect wide (all in world units), strokes w wide standing th off the stone. Usually built into a
    glowing color."""
    strokes = RUNES[name] if isinstance(name, str) else name
    for (xa, ya), (xb, yb) in strokes:
        pa, oa, _ = face(u0 + xa * size * aspect, z0 + ya * size)
        pb, ob, _ = face(u0 + xb * size * aspect, z0 + yb * size)
        if (pb - pa).length < 1e-4:
            continue
        dd = (pb - pa).normalized()
        o = ((oa + ob) * 0.5).normalized()
        bm_beam(bm, pa - dd * w * 0.4 + o * th * 0.35, pb + dd * w * 0.4 + o * th * 0.35, w, th, up=o)
    return bm


# ---------------------------------------------------------------------------------------------- shrine dressing
FLAME = (1.0, 0.72, 0.28)


def bm_candle(kit, p, h=0.14, r=0.035, wax="cream:0.1:0.6", flame=FLAME):
    """A stubby candle standing on p, its flame glowing."""
    p = Vector(p)
    bm_cyl(kit[wax], r * 1.1, r, h, (p.x, p.y, p.z + h * 0.5), seg=6)
    bm_crystal(kit["glow:%s,%s,%s,1.0" % flame], p + Vector((0, 0, h + 0.005)), p + Vector((0, 0, h + r * 2.6)), r * 0.75, n=4, shoulder=0.35, foot=0.5)
    return p + Vector((0, 0, h + r * 1.3))


def bm_lantern(kit, p, s=0.16, glow=FLAME, cap="team!:0.1:0.6", frame="wood_dark:0.2:0.7", strength=1.0):
    """A hanging lantern whose top ring is at p: a little six-sided light under a pointed cap, s wide."""
    p = Vector(p)
    z = p.z - s * 0.25
    bm_cyl(kit[frame], s * 0.1, s * 0.1, s * 0.25, (p.x, p.y, p.z - s * 0.12), seg=4)
    bm_cyl(kit[cap], s * 0.62, s * 0.08, s * 0.4, (p.x, p.y, z - s * 0.2), seg=6)
    bm_cyl(kit["glow:%s,%s,%s,%s" % (glow[0], glow[1], glow[2], strength)], s * 0.36, s * 0.42, s * 0.62, (p.x, p.y, z - s * 0.7), seg=6)
    bm_cyl(kit[frame], s * 0.5, s * 0.4, s * 0.12, (p.x, p.y, z - s * 1.06), seg=6)
    return Vector((p.x, p.y, z - s * 0.7))


def bm_sleeve(bm, rings, s0, s1, grow=0.02):
    """A band wrapped round a tube or loft (cloth, rope, a bracer): the tube's skin from ring s0 to ring s1 (numbers,
    may fall between rings; rings as points, see ring_co) pushed out by `grow`."""
    def row(s):
        i = max(0, min(int(s), len(rings) - 2))
        r = [a.lerp(b, s - i) for a, b in zip(rings[i], rings[i + 1])]
        c = sum(r, Vector()) / len(r)
        return [p + (p - c).normalized() * grow for p in r]
    cuts = [s0] + [float(i) for i in range(int(math.floor(s0)) + 1, int(math.ceil(s1))) if s0 + 1e-3 < i < s1 - 1e-3] + [s1]
    out = [row(s) for s in cuts]
    bm_loft(bm, out)
    return out


def sway(rig, name, axis, deg):
    """Turns one pose bone about an armature-space axis (on top of whatever it has)."""
    pb = rig.pose.bones[name]
    pb.rotation_quaternion = arm_space_quat(pb, axis, deg) @ pb.rotation_quaternion


def bm_standin(kit, p, yaw=0.0, h=1.15, swatch="tan:0.1:0.8"):
    """A stand-in for a Crew character (previews only: build with TR_STANDIN=1): a robed figure h tall, feet on p,
    facing yaw (degrees from +Y, counterclockwise), a staff in its right hand."""
    p = Vector(p)
    R = Matrix.Rotation(math.radians(yaw), 3, "Z")
    x, y = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0))
    rows = [oval(p + Vector((0, 0, z * h)), x, y, rx * h, ry * h, 8) for z, rx, ry in
            ((0.0, 0.2, 0.17), (0.4, 0.15, 0.12), (0.72, 0.19, 0.12), (0.8, 0.07, 0.07))]
    bm_loft(kit[swatch], rows)
    bm_ellipsoid(kit[swatch], p + Vector((0, 0, 0.9 * h)) + y * 0.02, (0.12 * h, 0.12 * h, 0.13 * h), u=8, v=5)
    bm_box(kit["black:0.3:0.6"], (0.12 * h, 0.03, 0.03), tuple(p + Vector((0, 0, 0.92 * h)) + y * 0.115 * h), (0, 0, yaw))
    s = p + x * 0.27 * h + y * 0.1 * h
    bm_beam(kit["wood_dark:0.2:0.7"], s, s + Vector((0, 0, 1.25 * h)), 0.04, 0.04)
    return kit


# ---------------------------------------------------------------------------------------------- round a menhir
def menhir_frame(base, yaw=0.0, lean=(0.0, 0.0)):
    """bm_menhir's own frame as a matrix (its +Y is the carved face's outward side, +Z runs up the stone)."""
    return (Matrix.Translation(Vector(base)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(-lean[0]), 4, "X")
            @ Matrix.Rotation(math.radians(lean[1]), 4, "Y"))


def menhir_half(z, h, w=0.44, d=0.3, top=0.6, sink=0.14):
    """A bm_menhir's half width and half depth at height z up the stone (before its small random wobble)."""
    zs = [-sink, h * 0.3, h * 0.64, h * 0.9, h]
    ws = [1.0, 0.98, 0.88, top + 0.14, top * 0.72]
    z = min(max(z, zs[0]), zs[-1])
    k = ws[-1]
    for i in range(4):
        if z <= zs[i + 1]:
            k = ws[i] + (ws[i + 1] - ws[i]) * (z - zs[i]) / (zs[i + 1] - zs[i])
            break
    return w * 0.5 * k, d * 0.5 * (0.55 + 0.45 * k)


def bm_menhir_band(bm, base, h, z0, z1, w=0.44, d=0.3, yaw=0.0, lean=(0.0, 0.0), top=0.6, grow=0.035, n=8):
    """A band (cloth, rope) tied round a bm_menhir built with the same base, h, w, d, yaw, lean and top, from z0 to z1 up it."""
    M = menhir_frame(base, yaw, lean)
    rows = []
    for z in (z0, z1):
        rx, ry = menhir_half(z, h, w, d, top)
        rows.append([M @ p for p in oval((0, 0, z), (1, 0, 0), (0, 1, 0), rx + grow, ry + grow, n, power=3.6, phase=0.5)])
    bm_loft(bm, rows)
    return rows


def menhir_wrap(base, h, w=0.44, d=0.3, yaw=0.0, lean=(0.0, 0.0), top=0.6, a0=60.0, a1=320.0, z0=0.14, z1=None, gap=0.1, step=40.0):
    """The line of a root (rope, vine) winding up round a bm_menhir: points from angle a0 to a1 (degrees round the stone,
    0 = the middle of its carved face, 90 = its left side seen from in front of the face; a1 < a0 winds the other
    way), climbing from z0 to z1 (default 0.7 h), `gap` off the stone."""
    M = menhir_frame(base, yaw, lean)
    z1 = h * 0.7 if z1 is None else z1
    cnt = max(2, int(round(abs(a1 - a0) / step)) + 1)
    pts = []
    for i in range(cnt):
        f = i / (cnt - 1.0)
        a, z = math.radians(a0 + (a1 - a0) * f), z0 + (z1 - z0) * f
        rx, ry = menhir_half(z, h, w, d, top)
        sa, ca = math.sin(a), math.cos(a)
        pts.append(M @ Vector((math.copysign(abs(sa) ** 0.6, sa) * (rx + gap), math.copysign(abs(ca) ** 0.6, ca) * (ry + gap), z)))
    return pts
