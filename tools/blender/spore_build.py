"""Builds the Spore Mound (footprint "pair": [0,0] front, [0,1] back), a Verdant tower that lobs spore pods.

    python tools/blender/build.py spore --out <preview dir>

One toadstool colony owns both hexes. The hero is a giant toadstool (the Head): a thick lofted stem with a bulbous
foot, a frilled skirt and a broad cap in the team's color, cream-spotted, gilled underneath, with glowing spore sacs
bedded in its crown. Smaller toadstools of the same kind cluster against its foot; a mossy rotten log lies across the
back hex, its roots and the giant's pale mycelium cords crawling over the ground between the two hexes; bracket fungi
grow on the log and the stem; a druid (Crew) stands by the log.
idle: the cap breathes, the stem sways, the sacs pulse, spores drift up round the cap. fire (0.53 s): the stem
squashes, the cap snaps up and the crown sac bursts in a puff of spores (the pod leaves from Muzzle, at the crown),
spores zip away, and the sac grows back.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "wildwood_common.py"), encoding="utf-8").read())

TID = "spore"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
FOOT = Vector((0.1, 0.35, 0))                 # where the giant's stem stands (world, on the plinth)
SPORE = "glow:0.62,1.0,0.3,0.85"
MOTE = "glow:0.72,1.0,0.48,0.8"
CAP_R, CAP_H, CAP_Z = 1.15, 0.84, 1.4         # the giant's cap: radius, height, underside height (head space)
CAP_C = Vector((0, 0.1, CAP_Z))               # the cap's middle (the stem leans a touch forward)
N_MOTES = 9

# a cap's profile from the rim up: (share of the radius, share of the height); the stem's: (share of the length, radius)
CAP_PROF = [(1.0, 0.0), (1.035, 0.09), (0.975, 0.25), (0.86, 0.43), (0.68, 0.61), (0.46, 0.78), (0.22, 0.92)]
STEM_PROF = [(0.0, 0.78), (0.07, 1.0), (0.2, 0.92), (0.45, 0.72), (0.75, 0.68), (1.0, 0.76)]


def cap_h_at(rf):
    """A cap's height share at share rf of its radius (0 the middle .. 1 the rim), and how fast it climbs inward."""
    prof = CAP_PROF[1:] + [(0.0, 1.0)]
    for (r0, h0), (r1, h1) in zip(prof, prof[1:]):
        if r1 <= rf <= r0:
            t = (r0 - rf) / (r0 - r1)
            return h0 + (h1 - h0) * t, (h1 - h0) / (r0 - r1)
    return 0.0, 0.0


def cap_point(rho, ang, r, h):
    """The point on a cap (radius r, height h) at polar (rho, ang) over its middle, and the surface normal there."""
    if rho < 1e-6:
        return Vector((0, 0, h)), Vector((0, 0, 1))
    hf, slope = cap_h_at(rho / r)
    nrm = Vector((math.cos(ang) * slope, math.sin(ang) * slope, 1.0)).normalized()
    return Vector((math.cos(ang) * rho, math.sin(ang) * rho, h * hf)), nrm


def keep_in(p, inset=0.2):
    """p (x, y) pulled toward the nearest cell's middle until it's on the footprint."""
    p = Vector((p[0], p[1], 0))
    for _ in range(60):
        if in_footprint(CELLS, p.x, p.y, inset):
            break
        c = FRONT if (p - FRONT).length < (p - BACK).length else BACK
        p = p + (c - p) * 0.06
    return p


def stem_geom(k, rnd, base, top, r, sw="cream:0.1:0.72"):
    """A toadstool's stem from base to top (one loft): a bulbous foot, a waist, a slight flare under the cap."""
    base, top = Vector(base), Vector(top)
    rings = []
    for t, rf in STEM_PROF:
        c = base.lerp(top, t)
        rings.append(oval(c, (1, 0, 0), (0, 1, 0), r * rf * rnd.uniform(0.97, 1.03), r * rf * 0.94, 10, power=2.3))
    bm_loft(k[sw], rings)


def skirt_geom(k, rnd, c, r, drop, sw="cream:0.25:0.65"):
    """A frilled skirt hanging from the stem at c (the stem is r wide there): a flared cone `drop` long with a wavy
    hem, both sides (one loft down the outside and back up the inside)."""
    c = Vector(c)
    n = 14
    outer_top, hem, inner_hem, inner_top = [], [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a) * 0.94
        rr = r * 1.8 + rnd.uniform(-0.08, 0.08) * r
        dz = -drop * rnd.uniform(0.85, 1.1)
        outer_top.append(c + Vector((ca * r * 1.02, sa * r * 1.02, 0.0)))
        hem.append(c + Vector((ca * rr, sa * rr, dz)))
        inner_hem.append(c + Vector((ca * rr * 0.93, sa * rr * 0.93, dz + 0.03)))
        inner_top.append(c + Vector((ca * r * 0.98, sa * r * 0.98, -0.01)))
    bm_loft(k[sw], [outer_top, hem, inner_hem, inner_top], cap0=False, cap1=False)


def cap_geom(k, rnd, c, r, h, sw, spots, gills, m=Matrix.Identity(4), avoid=(), stem_r=0.3):
    """A toadstool cap at c (its underside's middle), r wide, h tall: the dome (one loft, sw), cream spots lying on
    it and thin gills radiating underneath. m tilts the whole cap. avoid: (x, y, radius) spots kept clear (the sacs)."""
    c = Vector(c)
    m3 = m.to_3x3()
    n = 16 if r > 0.6 else 10
    rings = []
    for rf, hf in CAP_PROF:
        ring_ = []
        for i in range(n):
            a = 2 * math.pi * i / n
            rr = r * rf * rnd.uniform(0.975, 1.025)
            ring_.append(m @ Vector((math.cos(a) * rr, math.sin(a) * rr, h * hf + rnd.uniform(-0.006, 0.006) * r)) + c)
        rings.append(ring_)
    bm_loft(k[sw], rings, cap0=True, tip1=m @ Vector((0, 0, h)) + c)
    for i in range(gills):
        a = 2 * math.pi * (i + 0.5) / gills
        d = Vector((math.cos(a), math.sin(a), 0))
        p0, p1 = d * stem_r * 1.05 + Vector((0, 0, -0.045 * r)), d * r * 0.93 + Vector((0, 0, -0.03 * r))
        bm_beam(k["sand:0.35:0.85"], m @ p0 + c, m @ p1 + c, 0.03 * r + 0.006, 0.09 * r, w1=0.045 * r + 0.006, h1=0.07 * r,
                up=m3 @ Vector((0, 0, 1)))
    for i in range(spots):
        a, rf = 0.0, 0.5
        for _ in range(14):
            a, rf = rnd.uniform(0, 2 * math.pi), math.sqrt(rnd.uniform(0.06, 0.92))
            if all((math.cos(a) * rf * r - ax) ** 2 + (math.sin(a) * rf * r - ay) ** 2 > (ar + 0.1 * r) ** 2 for ax, ay, ar in avoid):
                break
        p, nrm = cap_point(rf * r, a, r, h)
        sr = r * rnd.uniform(0.09, 0.16)
        bm_ellipsoid(k["cream:0.02:0.4"], m @ (p - nrm * sr * 0.1) + c, (sr, sr * rnd.uniform(0.75, 1.0), sr * 0.3),
                     rot=rot_deg(m3 @ nrm), u=7, v=4)


def toadstool(k, rnd, base, h, r, lean=(0, 0), cap_sw="team!:0.08:0.7", skirt=True):
    """A whole small toadstool standing on base: stem, cap (tilted the way it leans), spots, gills, a skirt."""
    base = Vector(base)
    top = base + Vector((lean[0], lean[1], h))
    stem_r = max(0.07, r * 0.3)
    stem_geom(k, rnd, base - Vector((0, 0, 0.03)), top + Vector((0, 0, 0.08 * r)), stem_r)
    lv = Vector((lean[0], lean[1], 0))
    m = Matrix.Identity(4)
    if lv.length > 1e-3:
        m = Matrix.Rotation(math.atan2(lv.length, h) * 0.7, 4, Vector((0, 0, 1)).cross(lv).normalized())
    cap_geom(k, rnd, top, r, r * 0.9, cap_sw, spots=max(3, int(r * 20)), gills=max(10, int(r * 40)), m=m, stem_r=stem_r)
    if skirt:
        skirt_geom(k, rnd, top - Vector((0, 0, r * 0.4)), stem_r * 0.72, r * 0.3)


def bracket(k, rnd, c, out, r, tilt=-7.0):
    """A shelf fungus growing out of a surface at c, facing `out`: two stacked squashed ellipsoids (a ringed top)."""
    c, d = Vector(c), Vector(out).normalized()
    yaw = math.degrees(math.atan2(d.y, d.x))
    bm_ellipsoid(k["tan:0.25:0.8"], c + d * r * 0.55, (r, r * 0.8, r * 0.22), rot=(0, tilt, yaw), u=8, v=4)
    bm_ellipsoid(k["orange:0.1:0.55"], c + d * r * 0.5 + Vector((0, 0, r * 0.1)), (r * 0.72, r * 0.6, r * 0.16), rot=(0, tilt, yaw), u=8, v=4)


def build_base():
    col = collection("Spore")
    root = empty("Spore", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(9)
    k = Kit()
    # ---- the log across the back hex: rotten, mossy on top, hollow at the broken end that reaches the giant's foot
    A, B = Vector((-0.72, -1.42, 0)), Vector((0.62, -0.3, 0))
    d = (B - A).normalized()
    side = Vector((-d.y, d.x, 0))
    L = (B - A).length
    lz = T + 0.27
    pts = [A + Vector((0, 0, lz)), A + d * 0.45 + side * 0.03 + Vector((0, 0, lz + 0.03)), A + d * 0.95 + Vector((0, 0, lz + 0.04)),
           A + d * 1.4 - side * 0.03 + Vector((0, 0, lz + 0.03)), B + Vector((0, 0, lz))]
    bm_tube(k["wood_dark:0.3:0.9"], pts, [0.3, 0.32, 0.31, 0.3, 0.29], n=9)
    bm_cyl(k["black:0.55:0.9"], 0.2, 0.17, 0.08, B + Vector((0, 0, lz)) - d * 0.02, rot=rot_deg(d), seg=8)        # the hollow
    for i in range(5):                                                                                           # splinters
        a = math.radians(72 * i + 20)
        q = B + Vector((0, 0, lz)) + (side * math.cos(a) + Vector((0, 0, math.sin(a)))) * 0.27
        bm_crystal(k["wood_dark:0.4:0.9"], q - d * 0.1, q + d * rnd.uniform(0.1, 0.2), 0.035, n=4, shoulder=0.3)
    log = k.emit("Log", col, root)
    for o in log:
        if o.name.startswith("Log_wood"):
            paint_faces(o, "grass", lambda c, n: n.z > 0.55 and (c - Vector((B.x, B.y, 0))).length > 0.25, lo=0.25, hi=0.7)
    # roots: a splayed root ball at the far end, two long roots from the log's side into the front hex
    back_dir = -d
    for ang, ln in ((0, 0.9), (42, 0.72), (-46, 0.76), (84, 0.5), (-88, 0.55), (140, 0.4), (-140, 0.42)):
        a = math.atan2(back_dir.y, back_dir.x) + math.radians(ang)
        dd = Vector((math.cos(a), math.sin(a), 0))
        p0 = A + d * 0.12 + Vector((0, 0, lz - 0.05))
        p1 = A + dd * 0.26 + Vector((0, 0, T + 0.14))
        p2 = keep_in(A + dd * (0.26 + ln * 0.5)) + Vector((0, 0, T + 0.055))
        p3 = keep_in(A + dd * (0.26 + ln)) + Vector((0, 0, T + 0.02))
        bm_tube(k["wood_dark:0.3:0.9"], [p0, p1, p2, p3], [0.11, 0.09, 0.05, 0.0], n=5)
    for s0, sg, pts_ in ((1.05, 1, ((0.3, 0.1), (0.75, 0.3), (1.2, 0.2))), (1.5, 1, ((0.25, 0.1), (0.6, 0.35), (0.95, 0.55)))):
        base_ = A + d * s0 + Vector((0, 0, lz - 0.12))
        pts = [base_] + [keep_in(A + d * (s0 + fy) + side * sg * fx) + Vector((0, 0, T + 0.06 - 0.02 * i)) for i, (fx, fy) in enumerate(pts_)]
        bm_tube(k["wood_dark:0.3:0.9"], pts, [0.09, 0.075, 0.05, 0.0], n=5)
    k.emit("Roots", col, root)
    # ---- moss: a hummock the giant grows from, carpet along the log and under the clusters
    for (x, y, r, sq) in ((FOOT.x, FOOT.y, 0.98, 0.2), (-0.3, -1.2, 0.85, 0.15), (0.5, -0.55, 0.5, 0.14), (-0.5, 1.5, 0.5, 0.15),
                          (0.85, 1.2, 0.4, 0.14), (-0.85, 0.5, 0.42, 0.14), (0.3, 1.75, 0.5, 0.14), (-0.9, 1.35, 0.35, 0.14)):
        bm_blob(k["grass:0.25:0.8"], rnd, (x, y, T - 0.03), r, squash=(1, 0.92, sq), jitter=0.08, sub=1)
    for s in (0.35, 0.7, 1.1, 1.45):
        q = A + d * s + side * rnd.uniform(-0.06, 0.06) + Vector((0, 0, lz + 0.2))
        bm_blob(k["grass:0.2:0.7"], rnd, q, rnd.uniform(0.17, 0.24), squash=(1.3, 1, 0.45), jitter=0.12, sub=1)
    k.emit("Moss", col, root, vary=0.05)
    # ---- the giant's pale mycelium cords, crawling from its foot over both hexes to the clusters and the log
    for ang, ln, wig in ((20, 1.0, 0.1), (75, 0.9, -0.1), (150, 0.95, 0.12), (215, 1.4, -0.12), (250, 1.2, 0.1), (330, 0.9, -0.08), (110, 0.7, 0.06)):
        a = math.radians(ang)
        dd = Vector((math.cos(a), math.sin(a), 0))
        sd = Vector((-dd.y, dd.x, 0))
        pts = [FOOT + dd * 0.3 + Vector((0, 0, T + 0.15)), FOOT + dd * (0.3 + ln * 0.3) + sd * wig + Vector((0, 0, T + 0.07)),
               keep_in(FOOT + dd * (0.3 + ln * 0.65) - sd * wig * 0.6) + Vector((0, 0, T + 0.04)), keep_in(FOOT + dd * (0.3 + ln)) + Vector((0, 0, T + 0.02))]
        bm_tube(k["cream:0.3:0.85"], pts, [0.055, 0.045, 0.03, 0.0], n=5)
    k.emit("Cords", col, root)
    # ---- the smaller toadstools of the colony: against the giant's foot, by the hollow end, a trio on the log
    toadstool(k, rnd, (0.78, 0.5, T), 0.85, 0.34, lean=(0.12, 0.02))
    toadstool(k, rnd, (-0.52, 0.72, T), 0.65, 0.3, lean=(-0.12, 0.08))
    toadstool(k, rnd, (-0.42, 1.6, T), 0.95, 0.34, lean=(-0.14, 0.14), cap_sw="salmon:0.08:0.6")
    toadstool(k, rnd, (0.8, -0.72, T), 0.55, 0.26, lean=(0.1, -0.05), cap_sw="salmon:0.08:0.6")
    toadstool(k, rnd, (0.3, 0.98, T), 0.4, 0.19, lean=(0.04, 0.06), cap_sw="salmon:0.08:0.6", skirt=False)
    for s, sx, h, r in ((0.55, 0.08, 0.3, 0.13), (0.72, -0.1, 0.42, 0.17), (0.88, 0.05, 0.26, 0.11)):
        q = A + d * s + side * sx + Vector((0, 0, lz + 0.26))
        toadstool(k, rnd, q, h, r, lean=(side.x * sx * 0.8, side.y * sx * 0.8), cap_sw="salmon:0.08:0.6", skirt=False)
    k.emit("Shrooms", col, root, vary=0.06)
    # puffballs in threes, and bracket fungi on the log's flanks
    for cx, cy in ((-0.9, 0.95), (0.95, 1.1), (-0.85, -0.6), (0.2, 1.75)):
        for j in range(3):
            a = math.radians(120 * j + rnd.uniform(-30, 30))
            r = rnd.uniform(0.06, 0.1)
            q = keep_in((cx + math.cos(a) * 0.1, cy + math.sin(a) * 0.1), 0.18)
            bm_blob(k["cream:0.1:0.6"], rnd, (q.x, q.y, T + r * 0.7), r, jitter=0.1)
    k.emit("Puffballs", col, root, vary=0.08)
    for s, sg, r in ((0.3, 1, 0.2), (0.82, -1, 0.17), (1.2, 1, 0.22), (1.55, -1, 0.15)):
        q = A + d * s + side * sg * 0.27 + Vector((0, 0, lz + 0.08))
        bracket(k, rnd, q, side * sg, r)
    k.emit("Brackets", col, root, vary=0.06)
    # mossy stones half-buried along the edges, more carpet at the front
    for ang, cell, s in ((-72, FRONT, 0.3), (160, FRONT, 0.22), (30, BACK, 0.26), (-100, BACK, 0.3), (118, FRONT, 0.18)):
        ar = math.radians(ang)
        R = hex_r(ar, 0.22 + s * 0.7)
        p = cell + Vector((math.cos(ar) * R, math.sin(ar) * R, 0))
        bm_boulder(k["stone:0.15:0.9"], rnd, (p.x, p.y, T - 0.04), s, squash=(1, 1, rnd.uniform(0.7, 0.9)), n=12)
        bm_blob(k["grass:0.3:0.8"], rnd, (p.x * 0.97, p.y * 0.97, T + s * 0.95), s * 0.62, squash=(1, 1, 0.36), jitter=0.12)
    k.emit("Stones", col, root, vary=0.08, seed=3)
    for i, (rel, loc, sc) in enumerate((("forest/Grass_1_B_Color1", (-0.95, -1.0, T - 0.02), 0.42), ("forest/Grass_2_A_Color1", (0.95, 0.75, T - 0.02), 0.4),
                                        ("forest/Grass_1_A_Color1", (-0.2, -1.85, T - 0.02), 0.38))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Crew", col, root, (0.55, -1.45, T), 0.3, "SINGLE_ARROW")           # the druid by the log, facing the front
    empty("Head", col, root, (FOOT.x, FOOT.y, T), 0.5, "SINGLE_ARROW")
    return root


# ---- the giant, in the head's space (+Y forward)
def _sac(rho, ang, r):
    p, nrm = cap_point(rho, ang, CAP_R, CAP_H)
    return p, nrm, r


SACS = [_sac(0.0, 0.0, 0.18)] + [_sac(0.47, math.radians(90 + 72 * i), 0.13) for i in range(5)] + \
       [_sac(0.8, math.radians(126 + 72 * i), 0.095) for i in range(5)]
MOTE_C = CAP_C + Vector((0, 0, -0.04))
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "stem.1": ((0, 0, 0), (0, 0.04, 0.72), "root"),
    "stem.2": ((0, 0.04, 0.72), tuple(CAP_C), "stem.1"),
    "cap": (tuple(CAP_C), tuple(CAP_C + Vector((0, 0, CAP_H))), "stem.2"),
    "puff": (tuple(CAP_C + Vector((0, 0, CAP_H + 0.12))), tuple(CAP_C + Vector((0, 0, CAP_H + 0.4))), "cap"),
}
for _i, (_p, _n, _r) in enumerate(SACS):
    _c = CAP_C + _p - _n * _r * 0.3
    BONES["sac.%d" % _i] = (tuple(_c), tuple(_c + Vector((0, 0, 0.15))), "cap")
for _i in range(N_MOTES):
    _a = 2 * math.pi * _i / N_MOTES
    _s = MOTE_C + Vector((math.cos(_a) * 1.05, math.sin(_a) * 1.05, 0))
    BONES["mote.%d" % _i] = (tuple(_s), tuple(_s + Vector((0, 0, 0.1))), "root")


def build_head():
    col = collection("Spore")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(14)
    k = Kit()
    # ---- the stem: one loft over two bones, its foot earthy, bracket fungi on its flanks
    stem_geom(k, rnd, (0, 0, -0.06), CAP_C + Vector((0, 0, 0.1)), 0.52)
    for ang, z, r in ((205, 0.5, 0.2), (320, 0.8, 0.16), (60, 0.36, 0.17)):
        a = math.radians(ang)
        t = (z + 0.06) / (CAP_Z + 0.16)
        ax = Vector((0, 0, -0.06)).lerp(CAP_C + Vector((0, 0, 0.1)), t)
        rad = 0.52 * ramp(STEM_PROF, t)
        bracket(k, rnd, ax + Vector((math.cos(a), math.sin(a), 0)) * (rad - 0.03), (math.cos(a), math.sin(a), 0), r)
    for o in k.emit("Head_Stem", col, rig=rig, bones=["stem.1", "stem.2"]):
        if o.name.startswith("Head_Stem_cream"):
            paint_faces(o, "tan", lambda c, n: c.z < 0.17, lo=0.3, hi=0.85)
    skirt_geom(k, rnd, CAP_C + Vector((0, -0.01, -0.13)), 0.52 * 0.7, 0.3)
    k.emit("Head_Skirt", col, rig=rig, bone="stem.2")
    # ---- the cap in the team's color, spotted, gilled, with a lime collar round each spore sac
    cap_geom(k, rnd, CAP_C, CAP_R, CAP_H, "team!:0.08:0.72", spots=18, gills=34, avoid=[(p.x, p.y, r) for p, n_, r in SACS], stem_r=0.4)
    for p, nrm, r in SACS:
        bm_cyl(k["lime:0.15:0.6"], r * 1.3, r * 1.05, 0.06, CAP_C + p - nrm * 0.02, rot=rot_deg(nrm), seg=8)
    k.emit("Head_Cap", col, rig=rig, bone="cap", vary=0.06)
    # ---- the sacs (a bone each: they pulse, the crown one bursts), the burst's puff, the drifting spores
    bk = BoneKit()
    for i, (p, nrm, r) in enumerate(SACS):
        bk.bone("sac.%d" % i)
        bm_ellipsoid(bk[SPORE], Vector(BONES["sac.%d" % i][0]), (r, r, r * 0.9), rot=rot_deg(nrm), u=8, v=5)
    bk.emit_bones("Head_Sacs", col, rig)
    bk = BoneKit()
    bk.bone("puff")
    pc = Vector(BONES["puff"][0])
    for i in range(7):
        a = 2 * math.pi * i / 7
        rr = 0.2 if i else 0.0
        bm_blob(bk[MOTE], rnd, pc + Vector((math.cos(a) * rr, math.sin(a) * rr, 0.08 * (i % 2))), rnd.uniform(0.14, 0.2), jitter=0.15)
    bk.emit_bones("Head_Puff", col, rig)
    bk = BoneKit()
    for i in range(N_MOTES):
        bk.bone("mote.%d" % i)
        bm_blob(bk[MOTE], rnd, Vector(BONES["mote.%d" % i][0]), 0.075, jitter=0.1)
    bk.emit_bones("Head_Motes", col, rig)
    empty("Muzzle", col, head, tuple(CAP_C + Vector((0, 0, CAP_H + 0.2))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 90
FIRE_LEN = 16


def pose(rig, breathe=0.0, sway=0.0, tilt=0.0, squash=0.0, spring=0.0, sacs=None, top=1.0, puff=0.0, rise=0.0, t=0.0):
    """breathe: the cap swelling; sway / tilt: the stem's lean (degrees, about x / y); squash: the stem compressed and
    the cap flattened (the anticipation); spring: the opposite (the release); top: the crown sac's scale; puff: the
    burst cloud's scale, `rise` above the crown; t: the spores' moment in their climb (0..1)."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["stem.1"].rotation_quaternion = q(pb["stem.1"], (1, 0, 0), sway) @ q(pb["stem.1"], (0, 1, 0), tilt)
    pb["stem.2"].rotation_quaternion = q(pb["stem.2"], (1, 0, 0), sway * 0.8) @ q(pb["stem.2"], (0, 1, 0), tilt * 0.7)
    pb["stem.2"].location = arm_space_loc(pb["stem.2"], (0, 0, -0.2 * squash + 0.08 * spring))
    w, v = 0.08 * squash - 0.04 * spring, -0.1 * squash + 0.05 * spring
    pb["stem.2"].scale = (1 + w, 1 + v, 1 + w)                   # bone axes: (x, along the bone = up, y)
    w, v = breathe + 0.14 * squash - 0.09 * spring, breathe * 0.4 - 0.26 * squash + 0.22 * spring
    pb["cap"].scale = (1 + w, 1 + v, 1 + w)
    for i in range(len(SACS)):
        s = (sacs[i] if sacs else 1.0) * (top if i == 0 else 1.0)
        pb["sac.%d" % i].scale = (s, s, s)
    pb["puff"].scale = (max(puff, 0.001),) * 3
    pb["puff"].location = arm_space_loc(pb["puff"], (0, 0, rise))
    for i in range(N_MOTES):
        mote_pose(pb, "mote.%d" % i, t + i / N_MOTES, MOTE_C, 1.35, 1.05, 1.4, 0.3, 2 * math.pi * i / N_MOTES)


def _idle(f):
    ph = 2 * math.pi * f / IDLE_LEN
    return dict(breathe=0.035 * math.sin(2 * ph), sway=2.6 * math.sin(ph), tilt=1.8 * math.sin(ph + 1.3),
                sacs=[1.0 + 0.15 * math.sin(2 * ph + 1.1 * i) for i in range(len(SACS))], t=f / IDLE_LEN)


def _fire(f):
    # f0-4 the stem squashes and the crown sac swells; f4-6 it springs up and the sac bursts (the pod is away) in a
    # puff that rises and thins; a decaying wobble; the sac grows back by the end
    p = _idle(0)
    sq = smooth(f / 4.0) * (1 - smooth((f - 4) / 2.0))
    sp = smooth((f - 4) / 2.0) * (1 - smooth((f - 6) / 5.0))
    wob = math.sin((f - 6) / 9.0 * 2 * math.pi) * 0.3 * (1 - smooth((f - 11) / 5.0)) if f > 6 else 0.0
    swell = 1.0 + 1.1 * smooth((f - 1) / 4.0) if f < 6 else 0.05 + 0.95 * smooth((f - 7) / 9.0)
    puff = 1.3 * smooth((f - 5) / 3.0) * (1 - smooth((f - 11) / 5.0))
    p.update(squash=sq, spring=sp + wob, top=swell, puff=puff, rise=0.55 * smooth((f - 5) / 11.0) * (1 - smooth((f - 14) / 2.0)),
             t=smooth(f / FIRE_LEN))
    return p


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, **_idle(f))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        pose(rig, **_fire(f))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 8.2, "yaw": 150, "pitch": 22, "anim_target": (0.1, 0.45, 1.9), "anim_dist": 5.2,
           "frames": [("idle", 0), ("idle", 45), ("fire", 4), ("fire", 6), ("fire", 9)],
           "extra": [{"yaw": 180, "pitch": 60, "dist": 4.6, "target": (0.1, 0.45, 2.0)},
                     {"yaw": 210, "pitch": 26, "dist": 4.6, "target": (0.1, -1.0, 0.6)},
                     {"yaw": 120, "pitch": 4, "dist": 4.2, "target": (0.1, 0.45, 1.35)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
