"""Shared by the Aurelian Crown's buildings (Arcane Spire, Chapel of Dawn, War Banner, Hall of Knights, Sunlance
Lighthouse): stone-and-tile architecture on top of the kk_helpers kit. Coursed stone boxes with quoins, tiled gable /
pyramid / cone roofs over a solid underside, arched windows and doors, buttresses, battlements, shields, flames, cloth
with a painted device (for flag_bones chains), paving that keeps clear of the buildings, and a stand-in figure for
checking a Crew spot in the previews.

Exec after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

UP = Vector((0, 0, 1))
STONE = "stone:0.06:0.8"            # the Crown's pale grey masonry
STONE_LIGHT = "stone:0.0:0.45"      # dressed stone: arches, quoins, copings
STONE_FOOT = "stone2:0.25:0.9"      # footings and plinth courses
CORE = "stone_dark:0.35:0.95"       # what shows in the joints
TIMBER = "wood_dark:0.2:0.8"
TILES = "team!:0.08:0.7"
TILES_UNDER = "team!:0.72:0.95"
GOLD = "gold:0.08:0.55"
IRON = "iron:0.1:0.6"


def polar(c, r, deg, z=None):
    """The point r from c (x, y[, z]) at `deg` degrees (0 = +X, 90 = +Y: the tower's front)."""
    a = math.radians(deg)
    return Vector((c[0] + r * math.cos(a), c[1] + r * math.sin(a), (c[2] if len(c) > 2 else 0.0) if z is None else z))


def frame2(c, rot=0.0):
    """A turned frame on the ground: returns P(x, y, z) -> world point, and its x / y axes."""
    c = Vector((c[0], c[1], 0.0))
    a = math.radians(rot)
    ux, uy = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    return (lambda x, y, z=0.0: c + ux * x + uy * y + UP * z), ux, uy


# ------------------------------------------------------------------------------------------- solids
def bm_extrude(bm, pts, vec):
    """A flat outline (points in order, either way round) pushed along vec into a closed solid, facing outward."""
    vec = Vector(vec)
    a = [bm.verts.new(Vector(p)) for p in pts]
    b = [bm.verts.new(Vector(p) + vec) for p in pts]
    fs = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((a[j], a[i], b[i], b[j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return fs


def bm_hull(bm, pts):
    """The convex hull of some points as a closed solid."""
    vs = [bm.verts.new(Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = [e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def bm_obox(bm, c, along, w, d, h, z0=None):
    """A box at c turned so its length runs `along` (a horizontal direction): w along, d across, h tall. z0: its foot
    (otherwise c is its middle)."""
    c, ax = Vector(c), Vector((along[0], along[1], 0)).normalized()
    if z0 is not None:
        c = Vector((c.x, c.y, z0 + h * 0.5))
    return bm_beam(bm, c - ax * (w * 0.5), c + ax * (w * 0.5), d, h)


def bm_slopebox(bm, c, right, out, w, d, z0, z_in, z_out):
    """A block against a wall with a sloped top: w wide along `right`, reaching d along `out` from c, from z0 up to
    z_in at the wall and z_out at its outer face (buttress stages, weatherings, lean-to blocks)."""
    c, rt, o = Vector((c[0], c[1], 0)), Vector(right).normalized(), Vector(out).normalized()
    rings = []
    for dd, zt in ((0.0, z_in), (d, z_out)):
        p = c + o * dd
        rings.append([p - rt * (w * 0.5) + UP * z0, p + rt * (w * 0.5) + UP * z0, p + rt * (w * 0.5) + UP * zt, p - rt * (w * 0.5) + UP * zt])
    bm_loft(bm, rings)
    return bm


def bm_ring_n(bm, c, normal, r_out, r_in, half, seg=18):
    """A flat ring (band) round `normal` through c: outer / inner radius, `half` its half thickness."""
    c, n = Vector(c), Vector(normal).normalized()
    x = n.orthogonal().normalized()
    y = n.cross(x)
    vs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        d = x * math.cos(a) + y * math.sin(a)
        vs.append([bm.verts.new(c + d * r + n * z) for r, z in ((r_out, -half), (r_out, half), (r_in, half), (r_in, -half))])
    fs = []
    for i in range(seg):
        j = (i + 1) % seg
        for q in range(4):
            l = (q + 1) % 4
            fs.append(bm.faces.new((vs[i][q], vs[j][q], vs[j][l], vs[i][l])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def bm_gem(bm, c, r, up_len, down_len, n=6, girdle=0.12, axis=(0, 0, 1)):
    """A cut crystal: a point above and below a faceted girdle."""
    c, ax = Vector(c), Vector(axis).normalized()
    bm_tube(bm, [c - ax * down_len, c - ax * girdle, c + ax * girdle, c + ax * up_len], [0.0, r * 0.86, r, 0.0], n=n)
    return bm


def bm_flame(bm, base, r, h, n=5, lean=(0.0, 0.0)):
    """A teardrop flame standing on base."""
    b = Vector(base)
    pts = [b, b + Vector((lean[0] * 0.15, lean[1] * 0.15, h * 0.24)), b + Vector((lean[0] * 0.55, lean[1] * 0.55, h * 0.6)),
           b + Vector((lean[0], lean[1], h))]
    bm_tube(bm, pts, [r * 0.55, r, r * 0.6, 0.0], n=n)
    return bm


def transform_kit(kit, matrix):
    """Moves everything gathered in a Kit so far (build a part at the origin, then set it in place)."""
    for bm in kit.parts.values():
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return kit


# ------------------------------------------------------------------------------------------- economy
def cull(bm, hidden):
    """Deletes the faces of bm for which hidden(face) is True: faces no camera can see, so coursed masonry costs up
    to a third fewer triangles."""
    bm.normal_update()
    fs = [f for f in bm.faces if hidden(f)]
    if fs:
        bmesh.ops.delete(bm, geom=fs, context="FACES_ONLY")
    return bm


def cull_down(bm):
    """Every face of bm turned straight down (the bottoms of blocks sitting on the ground or the course below).
    Only for bms holding nothing that overhangs (no corbels, arches, eaves)."""
    return cull(bm, lambda f: f.normal.z < -0.9)


def cull_tower(bm, c, r):
    """A course_tower's hidden faces: every downward face, and the backs its blocks turn to the core (within r of c)."""
    c = Vector((c[0], c[1], 0))

    def hidden(f):
        n = f.normal
        if n.z < -0.9:
            return True
        m = f.calc_center_median()
        d = Vector((c.x - m.x, c.y - m.y, 0))
        return 1e-6 < d.length < r and n.dot(d.normalized()) > 0.85
    return cull(bm, hidden)


def cull_box(bm, c, w, d, th=0.16, rot=0.0):
    """A stone_box's (and its gable walls') hidden faces: every downward face, and the backs its walls turn inward."""
    P, ux, uy = frame2(c, rot)
    o = P(0, 0)
    hw, hd = w * 0.5, d * 0.5

    def hidden(f):
        n = f.normal
        if n.z < -0.9:
            return True
        m = f.calc_center_median() - o
        lx, ly, nx, ny = m.dot(ux), m.dot(uy), n.dot(ux), n.dot(uy)
        if abs(lx) > hw + 0.05 or abs(ly) > hd + 0.05:
            return False
        return ((ny < -0.9 and abs(ly - (hd - th)) < 0.035) or (ny > 0.9 and abs(ly + (hd - th)) < 0.035) or
                (nx < -0.9 and abs(lx - (hw - th)) < 0.035) or (nx > 0.9 and abs(lx + (hw - th)) < 0.035))
    return cull(bm, hidden)


# ------------------------------------------------------------------------------------------- masonry
def course_tower(kit, rnd, c, r0, r1, z0, z1, courses=6, n=10, depth=0.16, stone=STONE, core=CORE, skip=None, band=None):
    """round_tower() with a say in each course's color: band(course index) -> a Kit key (painted bands), or None."""
    c = Vector((c[0], c[1], 0))
    h = (z1 - z0) / courses
    for k in range(courses):
        r = r0 + (r1 - r0) * (k + 0.5) / courses
        key = (band(k) if band else None) or stone
        bm_block_course(kit[key], rnd, c, r, z0 + k * h, h, n, depth=depth, phase=0.5 * (k % 2),
                        skip=(lambda a, k=k: skip(k, a)) if skip else None)
    bm_cyl(kit[core], r0 - depth * 0.45, r1 - depth * 0.45, z1 - z0 - 0.01, (c.x, c.y, (z0 + z1) / 2), seg=max(n, 12))
    return kit


def stone_box(kit, rnd, c, w, d, z0, z1, rot=0.0, th=0.16, course=0.2, block=0.38, stone=STONE, core=CORE, quoins=None,
              sides="NSEW"):
    """A rectangular building's walls in coursed blocks over a dark core: w along its own X, d along its own Y, turned
    `rot` degrees round c. sides: which walls to lay (N = +Y, S = -Y, E = +X, W = -X in its own frame).
    quoins: a Kit key for dressed corner stones. Returns the frame's P(x, y, z)."""
    P, ux, uy = frame2(c, rot)
    hw, hd = w * 0.5, d * 0.5
    if "N" in sides:
        bm_block_wall(kit[stone], rnd, P(-hw, hd - th / 2), P(hw, hd - th / 2), z0, z1, th, course, block)
    if "S" in sides:
        bm_block_wall(kit[stone], rnd, P(hw, -hd + th / 2), P(-hw, -hd + th / 2), z0, z1, th, course, block)
    if "E" in sides:
        bm_block_wall(kit[stone], rnd, P(hw - th / 2, -hd + th), P(hw - th / 2, hd - th), z0, z1, th, course, block)
    if "W" in sides:
        bm_block_wall(kit[stone], rnd, P(-hw + th / 2, hd - th), P(-hw + th / 2, -hd + th), z0, z1, th, course, block)
    m = P(0, 0, (z0 + z1) / 2)
    bm_box(kit[core], (w - th * 0.9, d - th * 0.9, z1 - z0 - 0.012), tuple(m), (0, 0, rot))
    if quoins:
        rows = max(1, round((z1 - z0) / course))
        hh = (z1 - z0) / rows
        for k in range(rows):
            for sx in (-1, 1):
                for sy in (-1, 1):
                    lx, ly = (0.3, 0.19) if (k + (sx > 0) + (sy > 0)) % 2 else (0.19, 0.3)
                    p = P(sx * (hw - lx / 2 + 0.014), sy * (hd - ly / 2 + 0.014), z0 + (k + 0.5) * hh)
                    bm_box(kit[quoins], (lx, ly, hh - 0.022), tuple(p), (0, 0, rot))
    return P


def gable_wall(kit, rnd, p0, p1, z0, z1, th=0.16, course=0.2, block=0.38, stone=STONE, slab=CORE):
    """The triangle of wall under a gable, from p0 to p1 at z0 up to the ridge at z1: a flat slab with block courses
    stepping up it."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    ax = (p1 - p0).normalized()
    nr = Vector((-ax.y, ax.x, 0))
    mid = (p0 + p1) * 0.5
    bm_extrude(kit[slab], [p0 + UP * z0 - nr * (th * 0.38), p1 + UP * z0 - nr * (th * 0.38), mid + UP * z1 - nr * (th * 0.38)], nr * (th * 0.76))
    rows = max(1, round((z1 - z0) / course))
    hh = (z1 - z0) / rows
    for k in range(rows):
        t = (k + 1.0) / rows * 0.5
        a, b = p0.lerp(p1, t), p1.lerp(p0, t)
        if (b - a).length < 0.1:
            break
        bm_block_wall(kit[stone], rnd, a, b, z0 + k * hh, z0 + (k + 1) * hh, th, hh, block)
    return kit


def battlements(bm, p0, p1, z, w=0.2, h=0.16, th=0.16, gap=0.16, ends=True):
    """Merlons along a straight wall top from p0 to p1 (x, y), standing on z."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    length = (p1 - p0).length
    ax = (p1 - p0).normalized()
    n = max(1, int(round((length + gap) / (w + gap))))
    step = (length - w) / max(n - 1, 1) if n > 1 else 0.0
    for i in range(n):
        if not ends and i in (0, n - 1):
            continue
        s = w * 0.5 + step * i if n > 1 else length * 0.5
        c = p0 + ax * s
        bm_obox(bm, (c.x, c.y, 0), ax, w, th, h, z0=z)
    return bm


def crenel_wall(kit, rnd, pts, z0, h, th=0.16, course=0.17, block=0.34, stone=STONE, merlon=(0.2, 0.15, 0.15), cap=None,
                closed=False):
    """A low curtain wall along a polyline of (x, y) points: coursed blocks with merlons on top (merlon = width, height,
    gap; None for none), or a coping (cap: a Kit key)."""
    pts = [Vector((p[0], p[1], 0)) for p in pts]
    segs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if closed else [])
    for a, b in segs:
        bm_block_wall(kit[stone], rnd, a, b, z0, z0 + h, th, course, block)
        if cap:
            ax = (b - a).normalized()
            bm_beam(kit[cap], a - ax * 0.02 + UP * (z0 + h + 0.025), b + ax * 0.02 + UP * (z0 + h + 0.025), th + 0.05, 0.05)
        if merlon:
            battlements(kit[stone], a, b, z0 + h + (0.05 if cap else 0.0), w=merlon[0], h=merlon[1], th=th, gap=merlon[2])
    return kit


def buttress(kit, c, out, z0, z1, w=0.2, d0=0.28, d1=0.14, stone=STONE, split=0.5):
    """A two-stage buttress against the wall at c (x, y on the wall's face), reaching `out`: d0 deep below, d1 above,
    each stage ending in a sloped weathering."""
    o = Vector((out[0], out[1], 0)).normalized()
    rt = Vector((-o.y, o.x, 0))
    zm = z0 + (z1 - z0) * split
    bm_slopebox(kit[stone], c, rt, o, w, d0, z0, zm + 0.1, zm - 0.04)
    bm_slopebox(kit[stone], c, rt, o, w - 0.04, d1, zm - 0.06, z1, z1 - 0.16)
    return kit


# ------------------------------------------------------------------------------------------- openings
def arch_outline(c, right, w, h, n=6):
    """Points round an arched opening standing on c (the sill's middle): w wide, h to the crown (a half circle on top)."""
    c, rt = Vector(c), Vector(right).normalized()
    r = w * 0.5
    sp = max(h - r, 0.0)
    pts = [c - rt * r, c + rt * r] if sp > 1e-4 else []
    for i in range(n + 1):
        a = math.pi * i / n
        pts.append(c + UP * sp + rt * (math.cos(a) * r) + UP * (math.sin(a) * r))
    return pts


def wall_out(right):
    """The way a wall faces when `right` runs along it (as bm_arch has it)."""
    return Vector(right).normalized().cross(UP)


def arch_window(kit, c, right, w, h, glow="glow:1.0,0.74,0.3,0.9", frame=STONE_LIGHT, th=0.07, proud=0.05, n=5, sill=True,
                bars=None):
    """An arched window on a wall face: a glowing pane at c (the sill's middle; `right` runs along the wall, which
    faces wall_out(right)), in a surround of arch stones, on a sill. bars: a Kit key for a mullion and a transom."""
    c, rt = Vector(c), Vector(right).normalized()
    out = wall_out(rt)
    bm_extrude(kit[glow], arch_outline(c + out * 0.014, rt, w, h, n + 1), -out * 0.03)
    if frame:
        bm_arch(kit[frame], c + out * (proud * 0.5 - 0.015), rt, w, h - w * 0.5, th=th, depth=proud + 0.03, n=n)
        if sill:
            bm_beam(kit[frame], c - rt * (w * 0.5 + th + 0.015) - UP * 0.03 + out * (proud * 0.5), c + rt * (w * 0.5 + th + 0.015) - UP * 0.03 + out * (proud * 0.5),
                    proud + 0.05, 0.06)
    if bars:
        bm_beam(kit[bars], c + out * 0.022, c + out * 0.022 + UP * (h - 0.01), 0.025, 0.02, up=tuple(out))
        bm_beam(kit[bars], c + out * 0.022 - rt * (w * 0.5) + UP * (h - w * 0.5), c + out * 0.022 + rt * (w * 0.5) + UP * (h - w * 0.5), 0.02, 0.025)
    return kit


def arch_door(kit, c, right, w, h, wood="wood_dark:0.25:0.85", frame=STONE_LIGHT, th=0.09, proud=0.06, n=5, bands=IRON,
              knob=GOLD, split=True):
    """An arched door on a wall face (see arch_window): planks with iron bands and a ring, in a stone arch."""
    c, rt = Vector(c), Vector(right).normalized()
    out = wall_out(rt)
    bm_extrude(kit[wood], arch_outline(c + out * 0.016, rt, w, h, n + 1), -out * 0.04)
    if bands:
        for z in (h * 0.22, h * 0.58):
            bm_beam(kit[bands], c - rt * (w * 0.5 - 0.012) + UP * z + out * 0.022, c + rt * (w * 0.5 - 0.012) + UP * z + out * 0.022, 0.02, 0.04)
        if split:
            bm_beam(kit["black:0.3:0.7"], c + out * 0.018 + UP * 0.01, c + out * 0.018 + UP * (h - 0.02), 0.012, 0.012, up=tuple(out))
    if knob:
        bm_extrude(kit[knob], [c + rt * (w * 0.14) + UP * (h * 0.42) + out * 0.02 + (rt * math.cos(a) + UP * math.sin(a)) * 0.026
                               for a in (math.radians(60 * i) for i in range(6))], out * 0.02)
    if frame:
        bm_arch(kit[frame], c + out * (proud * 0.5 - 0.015), rt, w, h - w * 0.5, th=th, depth=proud + 0.03, n=n)
    return kit


# ------------------------------------------------------------------------------------------- roofs
def gable_roof(kit, rnd, c, length, span, z_e, z_r, rot=0.0, eave=0.1, verge=0.08, rows=4, cols=5, tiles=TILES,
               under=TILES_UNDER, ridge=GOLD, barge=TIMBER, ends=(True, True), ridge_w=0.09, th=0.04):
    """A tiled gable roof over a rectangle at c: the ridge runs along its own X (`length`), `span` across; z_e at the
    wall line, z_r at the ridge. Two tiled slopes over a solid underside, a ridge cap, barge boards at the gable ends
    (ends: at -X, at +X). Returns the frame's P(x, y, z)."""
    P, ux, uy = frame2(c, rot)
    hl, hs = length * 0.5 + verge, span * 0.5
    k = (z_r - z_e) / hs
    ze = z_e - eave * k
    for sy in (1, -1):
        bm_tile_slope(kit[tiles], rnd, P(-hl, sy * (hs + eave), ze), P(hl, sy * (hs + eave), ze), P(-hl, 0, z_r), P(hl, 0, z_r),
                      rows=rows, cols=cols, th=th)
    d = 0.03
    bm_loft(kit[under], [[P(x, -(hs + eave - 0.02), ze - d), P(x, 0, z_r - d), P(x, hs + eave - 0.02, ze - d)] for x in (-hl + 0.02, hl - 0.02)])
    if ridge:
        bm_beam(kit[ridge], P(-hl - 0.02, 0, z_r + 0.035), P(hl + 0.02, 0, z_r + 0.035), ridge_w, 0.075)
    if barge:
        for sx, on in ((-1, ends[0]), (1, ends[1])):
            if on:
                for sy in (1, -1):
                    bm_beam(kit[barge], P(sx * (hl + 0.012), sy * (hs + eave + 0.02), ze - 0.01), P(sx * (hl + 0.012), 0, z_r + 0.012), 0.05, 0.1)
    return P


def pyramid_roof(kit, rnd, c, w, d, z0, z1, rot=0.0, eave=0.1, rows=5, cols=4, tiles=TILES, under=TILES_UNDER, hips=GOLD,
                 th=0.04):
    """A tiled pyramid roof over a w x d rectangle at c, from z0 at the wall line up to its point at z1, with hip
    beams. The eave drops a little past the walls."""
    P, ux, uy = frame2(c, rot)
    hw, hd = w * 0.5 + eave, d * 0.5 + eave
    ze = z0 - eave * (z1 - z0) / max(w, d) * 2.0
    cs = [P(-hw, -hd, ze), P(hw, -hd, ze), P(hw, hd, ze), P(-hw, hd, ze)]
    apex = P(0, 0, z1)
    for i in range(4):
        e0, e1 = cs[i], cs[(i + 1) % 4]
        bm_tile_slope(kit[tiles], rnd, e0, e1, apex.lerp(e0, 0.06), apex.lerp(e1, 0.06), rows=rows, cols=cols, th=th)
    bm = kit[under]
    lo = [bm.verts.new(p - UP * 0.03 + (apex - p).normalized() * 0.02) for p in cs]
    top = bm.verts.new(apex - UP * 0.04)
    fs = [bm.faces.new(list(reversed(lo)))]
    for i in range(4):
        fs.append(bm.faces.new((lo[i], lo[(i + 1) % 4], top)))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    if hips:
        for p in cs:
            bm_beam(kit[hips], p + UP * 0.03, apex + UP * 0.03, 0.06, 0.06)
    return P


def cone_roof(kit, rnd, c, r, z, h, rows=5, n=12, tiles=TILES, under=TILES_UNDER, top=0.06, flare=0.05, finial=GOLD, spike=0.3):
    """A tiled cone roof (bm_tile_cone) over a solid underside, with a finial: a collar, a ball and a spike.
    top > 0.1 leaves it open (a truncated cone): no finial then."""
    c = Vector((c[0], c[1], 0))
    bm_tile_cone(kit[tiles], rnd, c, r, z, h, rows=rows, n=n, top=top, flare=flare)
    bm_cyl(kit[under], r - 0.025, max(top - 0.025, 0.0), h, (c.x, c.y, z + h / 2 - 0.03), seg=max(n, 10))
    if finial and top <= 0.1 and spike > 0:
        bm_cyl(kit[finial], top + 0.04, top + 0.015, 0.07, (c.x, c.y, z + h + 0.005), seg=8)
        bm_ellipsoid(kit[finial], (c.x, c.y, z + h + 0.09), (0.062, 0.062, 0.062), u=8, v=5)
        bm_cyl(kit[finial], 0.028, 0.0, spike, (c.x, c.y, z + h + 0.13 + spike / 2), seg=6)
    return kit


def bm_tile_cone_arc(bm, rnd, c, r, z, h, a0, a1, rows=4, n=7, th=0.04, lap=0.3, flare=0.05, top=0.06):
    """bm_tile_cone() over part of the circle only: from a0 to a1 degrees (an apse's half cone). n: tiles in the bottom
    row."""
    c = Vector((c[0], c[1], 0))
    a0, a1 = math.radians(a0), math.radians(a1)
    for k in range(rows):
        t0, t1 = max(0.0, (k - lap) / rows), (k + 1) / rows
        ra, rb = r + (top - r) * t0, r + (top - r) * t1
        za, zb = z + h * t0, z + h * t1
        if k == 0:
            ra += flare
            za -= flare * 0.6
        cnt = max(3, int(round(n * (0.35 + 0.65 * (1 - k / rows)))))
        cuts = [0.0] + [(i + (0.5 if k % 2 else 0.0)) / cnt for i in range(1, cnt + (1 if k % 2 else 0))] + [1.0]
        cuts = sorted(set(round(u, 5) for u in cuts if 0.0 <= u <= 1.0))
        sl = Vector((rb - ra, 0, zb - za))
        nz = Vector((-sl.z, 0, sl.x)).normalized()
        if nz.z < 0:
            nz = -nz
        for u0, u1 in zip(cuts, cuts[1:]):
            g = 0.012 / max(ra, 0.05) / max(a1 - a0, 1e-3)
            if u1 - u0 < g * 3:
                continue
            b0, b1 = a0 + (a1 - a0) * (u0 + g), a0 + (a1 - a0) * (u1 - g)
            lift = th + rnd.uniform(0, 0.012)

            def pt(rr, zz, a, lf):
                return Vector((c.x + rr * math.cos(a), c.y + rr * math.sin(a), zz)) + Vector((nz.x * math.cos(a), nz.x * math.sin(a), nz.z)) * lf
            vs = [bm.verts.new(pt(ra, za, b0, lift)), bm.verts.new(pt(ra, za, b1, lift)), bm.verts.new(pt(rb, zb, b1, 0.004)), bm.verts.new(pt(rb, zb, b0, 0.004)),
                  bm.verts.new(pt(ra, za, b0, 0.0)), bm.verts.new(pt(ra, za, b1, 0.0)), bm.verts.new(pt(rb, zb, b1, -th * 0.5)), bm.verts.new(pt(rb, zb, b0, -th * 0.5))]
            fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
            for q in range(4):
                j = (q + 1) % 4
                fs.append(bm.faces.new((vs[j], vs[q], vs[4 + q], vs[4 + j])))
            bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def dormer(kit, rnd, p, out, w=0.3, h=0.3, run=0.4, rise=0.16, wall=TIMBER, glow="glow:1.0,0.74,0.3,0.9", tiles=TILES,
           under=TILES_UNDER, rows=2, cols=2):
    """A small gabled dormer: its face stands on p (the middle of its sill line) looking `out`, w wide and h to its
    eaves, a little gable `rise` above; its roof runs back `run` into the main roof. A glowing window in the face."""
    p, o = Vector(p), Vector((out[0], out[1], 0)).normalized()
    rt = Vector((-o.y, o.x, 0))
    hw = w * 0.5
    face = [p - rt * hw, p + rt * hw, p + rt * hw + UP * h, p + UP * (h + rise), p - rt * hw + UP * h]
    bm_extrude(kit[wall], face, -o * run)
    bm_extrude(kit[glow], arch_outline(p + UP * 0.05 + o * 0.012, rt, w * 0.48, h * 0.92, 5), -o * 0.025)
    ov = 0.05
    k = rise / hw
    for s in (1, -1):
        e0, e1 = p + o * ov + rt * (s * (hw + ov)) + UP * (h - ov * k), p - o * run + rt * (s * (hw + ov)) + UP * (h - ov * k)
        r0, r1 = p + o * ov + UP * (h + rise), p - o * run + UP * (h + rise)
        bm_tile_slope(kit[tiles], rnd, e0, e1, r0, r1, rows=rows, cols=cols, th=0.03)
    bm_loft(kit[under], [[q + rt * (hw + ov - 0.01) + UP * (h - ov * k - 0.02), q + UP * (h + rise - 0.02), q - rt * (hw + ov - 0.01) + UP * (h - ov * k - 0.02)]
                         for q in (p + o * (ov - 0.01), p - o * run)])
    return kit


# ------------------------------------------------------------------------------------------- dressing
def shield(kit, c, out, w=0.3, h=0.36, face="team!:0.1:0.6", rim=GOLD, device=GOLD, th=0.035, kind="cross"):
    """A heater shield hung at c facing `out`: a team face in a gold rim, with a cross, a boss or a chevron."""
    c, o = Vector(c), Vector(out).normalized()
    rt = UP.cross(o).normalized()
    up = o.cross(rt).normalized()

    def shape(s):
        return [c + rt * (x * w * s) + up * (y * h * s) for x, y in ((-0.5, 0.5), (0.5, 0.5), (0.5, 0.05), (0.32, -0.28), (0, -0.5), (-0.32, -0.28), (-0.5, 0.05))]
    bm_extrude(kit[rim], shape(1.0), o * (th * 0.6))
    bm_extrude(kit[face], [q + o * (th * 0.3) for q in shape(0.82)], o * (th * 0.7))
    f = c + o * (th + 0.001)
    if kind == "cross":
        bm_extrude(kit[device], [f + rt * x + up * y for x, y in ((-0.035 * w / 0.3, 0.36 * h), (0.035 * w / 0.3, 0.36 * h), (0.035 * w / 0.3, -0.33 * h), (-0.035 * w / 0.3, -0.33 * h))], o * 0.008)
        bm_extrude(kit[device], [f + rt * x + up * y for x, y in ((-0.36 * w, 0.2 * h), (0.36 * w, 0.2 * h), (0.36 * w, 0.08 * h), (-0.36 * w, 0.08 * h))], o * 0.008)
    elif kind == "boss":
        bm_extrude(kit[device], [f + up * (0.08 * h) + (rt * math.cos(a) + up * math.sin(a)) * (w * 0.2) for a in (math.radians(45 * i) for i in range(8))], o * 0.02)
    elif kind == "chevron":
        bm_extrude(kit[device], [f + rt * (x * w) + up * (y * h) for x, y in ((-0.38, 0.0), (0, 0.3), (0.38, 0.0), (0.38, -0.14), (0, 0.16), (-0.38, -0.14))], o * 0.008)
    return kit


def hanging_banner(kit, top, right, w, h, cloth="team!:0.1:0.72", trim=GOLD, device=GOLD, rod=TIMBER, kind="sun"):
    """A still banner hung flat on a wall from a rod: top = the middle of its top edge on the wall face (`right` runs
    along the wall), w wide, h long, swallow-tailed, with a gold hem and a device."""
    top, rt = Vector(top), Vector(right).normalized()
    out = wall_out(rt)
    o = top + out * 0.03
    pts = [o - rt * (w / 2), o + rt * (w / 2), o + rt * (w / 2) - UP * h, o - UP * (h * 0.82), o - rt * (w / 2) - UP * h]
    bm_extrude(kit[cloth], pts, out * 0.016)
    bm_beam(kit[trim], o - rt * (w / 2) - UP * 0.05 + out * 0.01, o + rt * (w / 2) - UP * 0.05 + out * 0.01, 0.024, 0.035)
    bm_beam(kit[rod], top - rt * (w / 2 + 0.06) + out * 0.04, top + rt * (w / 2 + 0.06) + out * 0.04, 0.05, 0.05)
    m = o - UP * (h * 0.42) + out * 0.017
    if kind == "sun":
        bm_extrude(kit[device], [m + (rt * math.cos(a) + UP * math.sin(a)) * (w * (0.3 if i % 2 else 0.17)) for i, a in ((i, math.radians(22.5 * i)) for i in range(16))], out * 0.008)
    elif kind == "star":
        bm_extrude(kit[device], [m + (rt * math.sin(a) + UP * math.cos(a)) * (w * (0.13 if i % 2 else 0.33)) for i, a in ((i, math.radians(36 * i)) for i in range(10))], out * 0.008)
    elif kind == "disc":
        bm_extrude(kit[device], [m + (rt * math.cos(a) + UP * math.sin(a)) * (w * 0.24) for a in (math.radians(45 * i) for i in range(8))], out * 0.008)
    return kit


def torch(kit, p, out=None, h=0.34, iron=IRON, wood=TIMBER):
    """A torch: a wall torch on a bracket if `out` is given (p on the wall face), otherwise a standing one on p.
    Returns where its flame starts (build that on a bone with bm_flame)."""
    p = Vector(p)
    if out is not None:
        o = Vector((out[0], out[1], 0)).normalized()
        tip = p + o * 0.13 + UP * h * 0.5
        bm_beam(kit[iron], p - UP * (h * 0.2), p + o * 0.1 - UP * (h * 0.2), 0.035, 0.035)
        bm_beam(kit[wood], p + o * 0.1 - UP * (h * 0.4), tip, 0.05, 0.05, 0.065, 0.065)
        bm_cyl(kit[iron], 0.06, 0.045, 0.06, (tip.x, tip.y, tip.z + 0.0), seg=6)
        return tip + UP * 0.03
    bm_cyl(kit[wood], 0.035, 0.03, h, (p.x, p.y, p.z + h / 2), seg=6)
    bm_cyl(kit[iron], 0.075, 0.045, 0.08, (p.x, p.y, p.z + h + 0.03), seg=6)
    return p + UP * (h + 0.07)


def pave(kit, rnd, cells, z, keep_out=(), inset=0.3, size=0.29, key="stone2:0.12:0.7", keep=1.0, where=None, h=0.035):
    """Flagstones over the footprint's top, `inset` from its edge, clear of every circle (x, y, r) and box
    (x0, y0, x1, y1) in keep_out (the buildings), and only where where(x, y) holds if given."""
    loop = outline(cells, inset)
    xs, ys = [p.x for p in loop], [p.y for p in loop]

    def ok(x, y):
        if not inside(loop, x, y):
            return False
        for s in keep_out:
            if len(s) == 3:
                if (x - s[0]) ** 2 + (y - s[1]) ** 2 < s[2] ** 2:
                    return False
            elif s[0] <= x <= s[2] and s[1] <= y <= s[3]:
                return False
        return where(x, y) if where else True
    bm_flagstones(kit[key], rnd, ok, (min(xs), min(ys), max(xs), max(ys)), z, size=size, keep=keep, h=h)
    return kit


# ------------------------------------------------------------------------------------------- cloth with a device
def stamp(rows, u0, u1, v0, v1, key=GOLD, across=False):
    """A device for cloth_grid's color(): a little picture (strings, '#' = filled; the first string is its top row)
    over the cloth's u0..u1 by v0..v1. Rows run along v for a flag flying sideways (u = out from the pole, v = down);
    across=True for a hanging banner (u = down, v = across)."""
    nr, nc = len(rows), len(rows[0])

    def f(u, v):
        a, b = (u, v) if across else (v, u)       # a picks the row, b the column
        a0, a1, b0, b1 = (u0, u1, v0, v1) if across else (v0, v1, u0, u1)
        if not (a0 <= a < a1 and b0 <= b < b1):
            return None
        r = min(nr - 1, int((a - a0) / (a1 - a0) * nr))
        q = min(nc - 1, int((b - b0) / (b1 - b0) * nc))
        return key if rows[r][q] == "#" else None
    return f


def cloth_grid(kit, top, direction, hang, length, height, nu=8, nv=6, tail="swallow", notch=0.85, tail_from=0.72,
               color=None, base="team!:0.12:0.72", off=0.006, center=False):
    """A two-faced cloth for a flag_bones() chain, as a grid of nu x nv cells (so it bends smoothly and can carry a
    device): from `top` it runs `length` along `direction` and `height` along `hang`. color(u, v) -> a Kit key for
    the cell at (u along, v across; 0..1), None for the base: hems, stripes, a stamp(). tail: "swallow", "point" or
    "square". center: `top` is the middle of the cloth's width, not its corner. Emit the kit with rig=, bones=[chain]."""
    top, d, hv = Vector(top), Vector(direction).normalized(), Vector(hang).normalized()
    nrm = d.cross(hv).normalized()
    v_off = -0.5 if center else 0.0

    def P(u, v):
        uu = u
        if u > tail_from:
            if tail == "swallow":
                uu = tail_from + (u - tail_from) * (1.0 - notch * (1.0 - abs(2 * v - 1)))
            elif tail == "point":
                uu = tail_from + (u - tail_from) * (1.0 - 0.96 * abs(2 * v - 1))
        return top + d * (length * uu) + hv * (height * (v + v_off))
    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            key = (color((u0 + u1) * 0.5, (v0 + v1) * 0.5) if color else None) or base
            bm = kit[key]
            for side in (1, -1):
                q = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]
                if (q[1] - q[0]).length < 1e-4 and (q[2] - q[3]).length < 1e-4:
                    continue
                vs = [bm.verts.new(p + nrm * (side * off)) for p in q]
                bm.faces.new(vs if side > 0 else list(reversed(vs)))
    return kit


CROWN = ["#..#..#",
         "#.###.#",
         "#######",
         "#######",
         ".#####."]
SUN = ["..#.#..",
       ".#####.",
       "#######",
       ".#####.",
       "..#.#.."]
CROSS = ["..#..",
         "..#..",
         "#####",
         "..#..",
         "..#..",
         "..#.."]


# ------------------------------------------------------------------------------------------- previews
def crew_dummy(col, marker, h=1.12, gear="staff"):
    """A stand-in the size of a KayKit character at a Crew marker (its feet on the marker, facing its +Y), built only
    when the CREW_DUMMY environment variable is set: for checking a crew spot on the preview sheets. Never shipped."""
    if not os.environ.get("CREW_DUMMY"):
        return None
    k = Kit()
    s = h / 1.12
    bm_box(k["salmon:0.2:0.8"], (0.4 * s, 0.26 * s, 0.4 * s), (0, 0, 0.42 * s))
    bm_box(k["salmon:0.3:0.9"], (0.16 * s, 0.2 * s, 0.24 * s), (-0.1 * s, 0, 0.12 * s))
    bm_box(k["salmon:0.3:0.9"], (0.16 * s, 0.2 * s, 0.24 * s), (0.1 * s, 0, 0.12 * s))
    bm_box(k["cream:0.1:0.5"], (0.44 * s, 0.4 * s, 0.42 * s), (0, 0, 0.86 * s))
    bm_box(k["black:0.3:0.6"], (0.2 * s, 0.05 * s, 0.06 * s), (0, 0.21 * s, 0.88 * s))
    for sx in (-1, 1):
        bm_box(k["salmon:0.2:0.8"], (0.12 * s, 0.14 * s, 0.34 * s), (sx * 0.27 * s, 0.02, 0.44 * s))
    if gear in ("staff", "halberd"):
        bm_cyl(k["wood:0.2:0.8"], 0.022, 0.022, 1.3 * s, (0.33 * s, 0.1 * s, 0.65 * s), seg=5)
    elif gear == "sword":
        bm_box(k["white:0.1:0.6"], (0.04, 0.04, 0.55 * s), (0.33 * s, 0.14 * s, 0.7 * s))
        bm_box(k["sky:0.2:0.7"], (0.05, 0.3 * s, 0.36 * s), (-0.36 * s, 0.06 * s, 0.46 * s))
    return k.emit("CrewDummy", col, marker)
