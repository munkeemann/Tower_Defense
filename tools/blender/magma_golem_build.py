"""Builds the Magma Golem (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Forge creature
tower: it hurls molten boulders that splash and leave enemies burning.

    python tools/blender/build.py magma_golem --out <preview dir>

One place: a small caldera. Its floor is black rock over all three cells, broken into basalt columns with magma
glowing in the joints: low crust round a lava pool on the front cell, rising over the two back cells into horns of
tall columns at the outer corners (low toward the camera behind, so it looks into the caldera). A stream of lava
steps down each horn into the pool (the right one through a pond of its own).
In the pool stands the golem (the Head: it turns to aim): courses of hewn basalt blocks over a molten core that
shows in every joint, a furnace behind an iron grate in its chest, boulders for shoulders under plates in the team's
color, a small head with fire behind its mask, one huge fist, and one open hand that holds the next molten rock.
The dwarves' harness: an iron collar and belt, a tabard and a banner down its back in the team's color.
Clips: idle (it breathes, the furnace and the rock pulse, it looks about, embers rise from the pool, lava bubbles,
the banner swings), fire (it swings the rock back, flings it underhand: it leaves the hand on frame 4, at the
Muzzle; then it bends, scoops the pool, and comes up with the next one).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "megabeast_common.py"), encoding="utf-8").read())

TID = "magma_golem"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # (0, 0.69): the pool
BR = hex_to_world(1, 0, MID)         # (1.8, -0.35)
BL = hex_to_world(-1, 1, MID)        # (-1.8, -0.35)
TOP = 0.34
LAVA = "glow:1.0,0.4,0.06,0.95"
HOT = "glow:1.0,0.74,0.2,1.0"
MOLTEN = "glow:1.0,0.27,0.03,0.78"     # the lava lying on the ground: deeper than what shows in the golem's joints
BASALT, BASALT2, CRUST, IRON = "stone_dark:0.3:0.98", "black:0.1:0.6", "black:0.2:0.7", "iron:0.2:0.8"
POOL_R = 0.8
POND = (1.5, -0.55, 0.36)             # the right stream's pond: x, y, radius
STREAM_L = [(-2.2, 0.2), (-1.85, -0.12), (-1.42, -0.2), (-1.02, 0.16), (-0.74, 0.4)]
STREAM_R = [(2.2, 0.2), (1.85, -0.2), (1.5, -0.55)]
LINK_R = [(1.5, -0.55), (1.15, -0.1), (0.76, 0.3)]

# ---- the golem, in the head's space (+Y forward): its trunk's courses (z, middle y, half width, half depth)
PROF = [(0.84, 0.0, 0.46, 0.36), (1.05, 0.0, 0.42, 0.33), (1.3, 0.04, 0.5, 0.4), (1.6, 0.1, 0.64, 0.5), (1.9, 0.14, 0.7, 0.54),
        (2.12, 0.15, 0.6, 0.47), (2.26, 0.16, 0.34, 0.3)]
SH_R, EL_R, WR_R = Vector((0.84, 0.08, 1.86)), Vector((0.94, 0.0, 1.2)), Vector((0.62, 0.55, 1.0))
SH_L, EL_L, WR_L = Vector((-0.84, 0.08, 1.86)), Vector((-0.95, 0.02, 1.2)), Vector((-0.74, 0.34, 0.84))
HF = Vector((-0.36, 0.93, -0.05)).normalized()         # the open hand: the way its fingers point,
HS = Vector((HF.y, -HF.x, 0)).normalized()             # ... and its thumb's side
ROCK_C = WR_R + HF * 0.27 + Vector((0, 0, 0.3))
FL_DIR = (WR_L - EL_L).normalized()
FIST_C = WR_L + FL_DIR * 0.26
EMBERS = [(0.5, 0.36), (-0.48, 0.46), (0.1, -0.6), (-0.58, -0.28), (0.6, -0.26)]
BUBBLES = [(0.16, 0.64), (-0.36, -0.56), (0.66, 0.08)]
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, 0, 0.84), (0, 0, 1.08), "root"),
    "chest": ((0, 0, 1.08), (0, 0.14, 1.95), "hips"),
    "head": ((0, 0.24, 2.2), (0, 0.3, 2.5), "chest"),
    "jaw": ((0, 0.3, 2.22), (0, 0.52, 2.16), "head"),
    "core": ((0, 0.45, 1.75), (0, 0.7, 1.75), "chest"),
    "arm.R.1": (tuple(SH_R), tuple(EL_R), "chest"),
    "arm.R.2": (tuple(EL_R), tuple(WR_R), "arm.R.1"),
    "hand.R": (tuple(WR_R), tuple(WR_R + HF * 0.3), "arm.R.2"),
    "rock": (tuple(ROCK_C), tuple(ROCK_C + Vector((0, 0, 0.25))), "hand.R"),
    "arm.L.1": (tuple(SH_L), tuple(EL_L), "chest"),
    "arm.L.2": (tuple(EL_L), tuple(WR_L), "arm.L.1"),
}
for _i, (_x, _y) in enumerate(EMBERS):
    BONES["ember.%d" % _i] = ((_x, _y, 0.1), (_x, _y, 0.3), "root")
for _i, (_x, _y) in enumerate(BUBBLES):
    BONES["bubble.%d" % _i] = ((_x, _y, 0.06), (_x, _y, 0.26), "root")
BAN_TOP = Vector((-0.3, -0.6, 2.03))
flag_bones(BONES, "banner", BAN_TOP, (0, -0.02, -1), 1.0, segs=3, parent="chest")


def _rise(x, y):
    """How high the caldera's columns stand at (x, y): low crust round the pool and along the back (the camera's
    side), rising to two horns at the back cells' outer front corners."""
    rf = math.hypot(x - F.x, y - F.y)
    side = min(max((abs(x) - 1.0) / 1.8, 0.0), 1.0)
    fwd = min(max((y + 1.45) / 2.1, 0.0), 1.0)
    return 0.1 + 2.3 * side ** 1.3 * (0.3 + 0.7 * fwd) * smooth((rf - 1.3) / 0.6)


def _poly_dist(pts, x, y):
    """How far (x, y) is from a polyline, and how far along it (0..1) the nearest point lies."""
    p = Vector((x, y))
    ls = [(Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:])]
    best, bt, run = 9e9, 0.0, 0.0
    for (a, b), l in zip(zip(pts, pts[1:]), ls):
        a, b = Vector(a), Vector(b)
        t = min(max((p - a).dot(b - a) / max(l * l, 1e-9), 0.0), 1.0)
        dd = (a + (b - a) * t - p).length
        if dd < best:
            best, bt = dd, (run + t * l) / sum(ls)
        run += l
    return best, bt


def _column(bm, c, r, z0, z1, rot=0.0, cham=0.035, cap=True):
    """A basalt column: a six-sided prism with a chamfered head."""
    def hexa(rr, z):
        return [Vector((c[0] + rr * math.cos(rot + math.pi / 3 * i + math.pi / 6), c[1] + rr * math.sin(rot + math.pi / 3 * i + math.pi / 6), z))
                for i in range(6)]
    rows = [hexa(r, z0), hexa(r, z1 - cham), hexa(r - cham, z1)] if cham > 1e-4 else [hexa(r, z0), hexa(r, z1)]
    return bm_loft(bm, rows, cap0=False, cap1=cap)


def build_base():
    col = collection("Magma_golem")
    root = empty("Magma_golem", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(31)
    k = Kit()
    # ---- the caldera's floor: a slab of black rock over all three cells, magma under the crust where it's thin
    prism(k[CRUST], outline(CELLS, 0.2), T - 0.02, T + 0.03)
    k.emit("Floor", col, root)
    edge = outline(CELLS, 0.36)
    seep = lambda x, y: inside(edge, x, y)
    for cx, cy, r in [(F.x, F.y, 1.3), (POND[0], POND[1], 0.75)] + [(x, y, 0.5) for x, y in STREAM_L[1:] + STREAM_R[1:] + LINK_R]:
        bm_patch(k[MOLTEN], rnd, (cx, cy), r, T + 0.03, T + 0.04, n=10, jitter=0.1, keep=seep)
    # the pool the golem stands in (hotter toward the middle), and the pond; slabs of cooled crust drift on both
    bm_patch(k[MOLTEN], rnd, (F.x, F.y), POOL_R, T + 0.04, T + 0.06, n=14, jitter=0.04)
    bm_patch(k[LAVA], rnd, (F.x, F.y), 0.66, T + 0.05, T + 0.066, n=12, jitter=0.1)
    bm_patch(k[HOT], rnd, (F.x, F.y), 0.46, T + 0.058, T + 0.072, n=10, jitter=0.12)
    bm_patch(k[MOLTEN], rnd, POND[:2], POND[2], T + 0.04, T + 0.06, n=9, jitter=0.1)
    bm_patch(k[LAVA], rnd, POND[:2], POND[2] * 0.55, T + 0.05, T + 0.068, n=7, jitter=0.15)
    k.emit("Lava", col, root)
    for a, rr, r in ((38, 0.66, 0.13), (112, 0.7, 0.1), (158, 0.62, 0.14), (203, 0.7, 0.11), (288, 0.68, 0.13), (327, 0.6, 0.1)):
        bm_patch(k[CRUST], rnd, (F.x + math.cos(math.radians(a)) * rr, F.y + math.sin(math.radians(a)) * rr), r, T + 0.05, T + 0.09, n=6, jitter=0.22,
                 rot=rnd.uniform(0, 1))
    bm_patch(k[CRUST], rnd, (POND[0] + 0.12, POND[1] - 0.14), 0.1, T + 0.05, T + 0.09, n=6, jitter=0.22)
    k.emit("Crust", col, root, vary=0.08)
    # ---- the pool's rim: slabs of crust (low: the golem's fist swings over them)
    rim = outline(CELLS, 0.24)
    for i in range(17):
        a = 2 * math.pi * i / 17 + rnd.uniform(-0.08, 0.08)
        rr = POOL_R + rnd.uniform(0.07, 0.13)
        x, y = F.x + math.cos(a) * rr, F.y + math.sin(a) * rr
        if inside(rim, x, y):
            bm_boulder(k[CRUST if i % 3 else BASALT], rnd, (x, y, T + 0.02), rnd.uniform(0.13, 0.18), squash=(1.0, 1.0, rnd.uniform(0.45, 0.7)), n=9)
    k.emit("Rim", col, root, vary=0.08)
    # ---- the columns: a honeycomb of them, magma in the joints; streams step down the horns into the pool
    d = 0.4
    R = d / math.sqrt(3.0)
    for j in range(-9, 9):
        for i in range(-9, 10):
            x, y = i * d + (d * 0.5 if j % 2 else 0.0), j * d * 0.866 + 0.1
            if not inside(edge, x, y):
                continue
            rf = math.hypot(x - F.x, y - F.y)
            if rf < POOL_R + 0.22 or math.hypot(x - POND[0], y - POND[1]) < POND[2] + 0.12:
                continue
            flow = None
            for path in (STREAM_L, STREAM_R, LINK_R):
                dist, t = _poly_dist(path, x, y)
                if dist < 0.2:
                    q, q2 = poly_at(path, t), poly_at(path, min(t + 0.22, 1.0))
                    flow = (max(0.07, _rise(q.x, q.y) - 0.12), max(0.05, _rise(q2.x, q2.y) - 0.12), q2 - q)
            if flow is not None:
                h, h2, dv = flow
                if h > 0.2:             # a step of the cascade: a basalt drum, the lava running over its top and down its face
                    _column(k[BASALT2], (x, y), R * 0.98, T + 0.03, T + h - 0.035, cham=0.0)
                    _column(k[LAVA], (x, y), R * 0.9, T + h - 0.045, T + h, cham=0.0)
                    if dv.length > 1e-3 and h - h2 > 0.05:
                        dv = dv.normalized()
                        bm_beam(k[LAVA], (x + dv.x * R * 0.8, y + dv.y * R * 0.8, T + h - 0.01), (x + dv.x * R * 0.8, y + dv.y * R * 0.8, T + h2 - 0.03),
                                R * 0.95, 0.07, up=(dv.x, dv.y, 0))
                else:
                    _column(k[MOLTEN], (x, y), R * 1.03, T + 0.03, T + h, cham=0.0)
                continue
            h = _rise(x, y)
            h += rnd.uniform(-0.04, 0.1) if h < 0.3 else rnd.uniform(-0.16, 0.24)
            if rf < 1.36:
                h = min(h, 0.2)
            h = max(0.06, round(h / 0.06) * 0.06)
            c = (x + rnd.uniform(-0.015, 0.015), y + rnd.uniform(-0.015, 0.015))
            rr = R * rnd.uniform(0.86, 0.93)
            sw = BASALT if rnd.random() < 0.72 else BASALT2
            rot = rnd.uniform(-0.06, 0.06)
            z = T
            while T + h - z > 0.95:                                             # tall ones in drums, a joint between
                seg = rnd.uniform(0.42, 0.62)
                _column(k[sw], c, rr, z, z + seg, rot=rot, cap=False)
                z += seg
                rr *= rnd.uniform(0.96, 1.0)
            _column(k[sw], c, rr, z, T + h, rot=rot)
    k.emit("Columns", col, root, vary=0.09)
    empty("Head", col, root, (F.x, F.y, T), 0.5, "SINGLE_ARROW")
    return root


def _course(k, rnd, a, b, phase=0.5, keep=None, gap=0.05, th=(0.05, 0.1)):
    """One course of hewn blocks round the trunk, between two rows of PROF."""
    rows = [oval((0, cy, z), (1, 0, 0), (0, 1, 0), rx, ry, 8, power=2.6, phase=phase) for z, cy, rx, ry in (a, b)]
    bm_plates(k[BASALT], rnd, rows, gap=gap, th=th, keep=keep)


def _limb(k, rnd, pts, radii, n=6, gap=0.05, th=(0.05, 0.1)):
    """A limb of basalt blocks round a molten core."""
    bm_tube(k[LAVA], pts, [r * 0.97 for r in radii], n=n)
    bm_plates(k[BASALT], rnd, tube_rings(pts, radii, n), gap=gap, th=th)


def build_head():
    col = collection("Magma_golem")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(8)
    k, kb = Kit(), Kit()                # plated and rough parts; hewn ones (bevelled)
    Z = Vector((0, 0, 1))
    core = lambda rows: [oval((0, cy, z), (1, 0, 0), (0, 1, 0), rx * 0.95, ry * 0.95, 8, power=2.6, phase=0.5) for z, cy, rx, ry in rows]
    # ---- legs, planted in the pool
    for sx in (-1, 1):
        _limb(k, rnd, [(sx * 0.3, 0.0, 1.0), (sx * 0.33, 0.05, 0.52), (sx * 0.34, 0.0, -0.08)], [0.25, 0.24, 0.3])
        bm_boulder(k[BASALT2], rnd, (sx * 0.34, 0.2, 0.38), 0.16, squash=(1.0, 0.8, 1.1), n=9, sink=0.0)         # kneecap
    k.emit("Head_Legs", col, rig=rig, bone="root", vary=0.08)
    # ---- hips: a course of blocks, the dwarves' iron belt, a tabard in the team's color
    bm_loft(k[LAVA], core(PROF[:3]))
    _course(k, rnd, PROF[0], PROF[1], phase=0.0)
    k.emit("Head_Hips", col, rig=rig, bone="hips", vary=0.08)
    bm_loft(kb[IRON], [oval((0, 0.0, z), (1, 0, 0), (0, 1, 0), 0.57, 0.47, 12, power=2.4) for z in (0.97, 1.1)])
    bm_cyl(kb["gold:0.1:0.5"], 0.11, 0.11, 0.05, (0, 0.47, 1.035), rot=(90, 0, 0), seg=6)
    bm_beam(kb["team!:0.1:0.7"], (0, 0.49, 1.0), (0, 0.53, 0.52), 0.36, 0.035, up=(0, 1, 0))
    bm_beam(kb["team!:0.3:0.8"], (0, 0.53, 0.52), (0, 0.54, 0.34), 0.36, 0.035, w1=0.03, up=(0, 1, 0))
    bm_beam(kb["gold:0.1:0.5"], (0, 0.532, 0.6), (0, 0.537, 0.53), 0.38, 0.045, up=(0, 1, 0))
    kb.emit("Head_Belt", col, rig=rig, bone="hips", bevel=0.012)
    # ---- the trunk: courses of blocks in running bond over the molten core; a furnace behind a grate in its chest
    bm_loft(k[LAVA], core(PROF[1:]))
    for i in range(1, len(PROF) - 1):
        _course(k, rnd, PROF[i], PROF[i + 1], phase=0.5 * (i % 2), keep=(lambda b, q: q != 1) if i == 3 else None)
    for sx in (-1, 1):                                                          # shoulders: a boulder each
        bm_boulder(k[BASALT if sx > 0 else BASALT2], rnd, (sx * 0.82, 0.12, 1.6), 0.43, squash=(1.0, 1.0, 0.92), n=16, sink=0.0)
    k.emit("Head_Trunk", col, rig=rig, bone="chest", vary=0.08)
    corners = {(-1, 0): Vector((-0.3, 0.645, 1.61)), (1, 0): Vector((0.3, 0.645, 1.61)), (-1, 1): Vector((-0.33, 0.725, 1.89)), (1, 1): Vector((0.33, 0.725, 1.89))}
    for a, b in (((-1, 0), (1, 0)), ((-1, 1), (1, 1)), ((-1, 0), (-1, 1)), ((1, 0), (1, 1))):
        bm_beam(kb[IRON], corners[a], corners[b], 0.07, 0.07, up=(0, 1, 0))
    for x in (-0.33, 0.0, 0.33):
        bm_beam(kb[IRON], corners[(-1, 0)].lerp(corners[(1, 0)], 0.5 + x * 0.5), corners[(-1, 1)].lerp(corners[(1, 1)], 0.5 + x * 0.5), 0.04, 0.04, up=(0, 1, 0))
    for sx in (-1, 1):                                                          # plates on the shoulders in the team's color
        bm_beam(kb["team!:0.1:0.6"], (sx * 0.46, 0.12, 2.4), (sx * 1.1, 0.12, 2.2), 0.64, 0.07, w1=0.5)
        bm_beam(kb["gold:0.1:0.5"], (sx * 1.06, 0.12, 2.215), (sx * 1.15, 0.12, 2.185), 0.54, 0.1, w1=0.5)
        bm_beam(kb["gold:0.1:0.5"], (sx * 0.43, 0.12, 2.41), (sx * 0.52, 0.12, 2.385), 0.68, 0.1, w1=0.66)
        bm_crystal(kb[IRON], (sx * 0.78, 0.12, 2.3), (sx * 0.88, 0.12, 2.58), 0.09, n=4, shoulder=0.3)
    bm_loft(kb[IRON], [oval((0, 0.2, z), (1, 0, 0), (0, 1, 0), 0.37, 0.33, 10) for z in (2.2, 2.32)])        # collar
    bm_tube(kb["gold:0.1:0.55"], [(-0.4, -0.6, 2.06), (0.4, -0.6, 2.06)], 0.035, n=6)                        # the banner's rod
    for sx in (-1, 1):
        bm_beam(kb[IRON], (sx * 0.34, -0.38, 2.0), (sx * 0.34, -0.62, 2.07), 0.05, 0.05)
        bm_ellipsoid(kb["gold:0.1:0.5"], (sx * 0.43, -0.6, 2.06), (0.06, 0.06, 0.06), u=6, v=4)
    kb.emit("Head_Harness", col, rig=rig, bone="chest", bevel=0.012)
    bm_ellipsoid(k[HOT], (0, 0.56, 1.75), (0.28, 0.11, 0.14), u=8, v=5)
    k.emit("Head_Furnace", col, rig=rig, bone="core")
    flag_part("Head_Banner", col, rig, "banner", BAN_TOP, (0, -0.02, -1), 1.0, 0.6, segs=3, hang=(1, 0, 0))
    bm_box(kb["gold:0.1:0.5"], (0.2, 0.02, 0.2), (0, -0.626, 1.62), (0, 45, 0))
    bm_box(kb["gold:0.1:0.5"], (0.6, 0.02, 0.05), (0, -0.626, 1.22))
    kb.emit("Head_BannerTrim", col, rig=rig, bones=["banner.1", "banner.2", "banner.3"])
    # ---- the head: small, a mask of basalt with the fire behind it; a jaw of stone teeth
    bm_box(kb[BASALT], (0.4, 0.36, 0.24), (0, 0.3, 2.46))
    bm_box(kb[BASALT2], (0.48, 0.16, 0.1), (0, 0.47, 2.43), (-12, 0, 0))                                     # brow
    bm_box(kb[BASALT], (0.08, 0.1, 0.17), (0, 0.5, 2.32))                                                    # nose
    for sx in (-1, 1):
        bm_box(kb[BASALT], (0.11, 0.22, 0.2), (sx * 0.2, 0.38, 2.3))                                         # cheeks
        bm_crystal(kb[BASALT2], (sx * 0.15, 0.2, 2.52), (sx * 0.3, 0.06, 2.8), 0.08, n=5, shoulder=0.35)       # crags like horns
    kb.emit("Head_Mask", col, rig=rig, bone="head", bevel=0.012)
    bm_box(k[HOT], (0.3, 0.06, 0.13), (0, 0.46, 2.33))                                                       # eyes
    bm_box(k[HOT], (0.26, 0.2, 0.05), (0, 0.4, 2.2))                                                         # throat
    k.emit("Head_Fire", col, rig=rig, bone="head")
    bm_box(kb[BASALT2], (0.36, 0.26, 0.1), (0, 0.4, 2.14))
    for x in (-0.12, -0.04, 0.04, 0.12):
        bm_crystal(kb["stone:0.1:0.5"], (x, 0.5, 2.17), (x, 0.51, 2.27), 0.035, n=4)
    kb.emit("Head_Jaw", col, rig=rig, bone="jaw", bevel=0.01)
    # ---- the right arm: the open hand, three fingers and a thumb round the next rock
    _limb(k, rnd, [SH_R, (0.9, 0.04, 1.52), EL_R], [0.24, 0.27, 0.23])
    bm_blob(k[LAVA], rnd, EL_R, 0.21, jitter=0.08)
    k.emit("Head_ArmR1", col, rig=rig, bone="arm.R.1", vary=0.08)
    _limb(k, rnd, [EL_R, (0.8, 0.26, 1.12), WR_R], [0.23, 0.3, 0.26])
    bm_blob(k[LAVA], rnd, WR_R, 0.2, jitter=0.08)
    k.emit("Head_ArmR2", col, rig=rig, bone="arm.R.2", vary=0.08)
    bm_beam(kb[BASALT], WR_R + HF * 0.06, WR_R + HF * 0.42, 0.46, 0.14)
    for o in (-0.16, 0.0, 0.16):
        a = WR_R + HF * 0.4 + HS * o
        b = a + HF * 0.2 + Z * 0.03
        c = b + HF * 0.1 + Z * 0.2
        bm_beam(kb[BASALT2], a, b, 0.13, 0.13)
        bm_beam(kb[BASALT], b - Z * 0.04, c, 0.12, 0.12, w1=0.085, h1=0.085)
    a = WR_R + HF * 0.16 + HS * 0.22
    b = a + HS * 0.15 + HF * 0.05 + Z * 0.04
    bm_beam(kb[BASALT2], a, b, 0.13, 0.13)
    bm_beam(kb[BASALT], b - Z * 0.04, b + HS * 0.03 + Z * 0.2, 0.12, 0.12, w1=0.085, h1=0.085)
    kb.emit("Head_HandR", col, rig=rig, bone="hand.R", bevel=0.012)
    bm_cyl(k[HOT], 0.15, 0.15, 0.02, WR_R + HF * 0.25 + Z * 0.075, seg=8)
    k.emit("Head_Palm", col, rig=rig, bone="hand.R")
    bm_blob(k[HOT], rnd, ROCK_C, 0.21, jitter=0.1, sub=2)                                                   # the molten rock
    for a, el in ((20, 10), (95, -25), (170, 15), (250, -15), (320, 30), (60, 70)):
        dv = Vector((math.cos(math.radians(a)) * math.cos(math.radians(el)), math.sin(math.radians(a)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        bm_boulder(k[BASALT2], rnd, ROCK_C + dv * 0.14 - Z * 0.08, 0.115, n=8, sink=0.0)
    k.emit("Head_Rock", col, rig=rig, bone="rock")
    # ---- the left arm: a forearm like a pillar, and the fist
    _limb(k, rnd, [SH_L, (-0.92, 0.04, 1.52), EL_L], [0.26, 0.3, 0.26])
    bm_blob(k[LAVA], rnd, EL_L, 0.23, jitter=0.08)
    k.emit("Head_ArmL1", col, rig=rig, bone="arm.L.1", vary=0.08)
    _limb(k, rnd, [EL_L, EL_L.lerp(WR_L, 0.5) + Vector((-0.04, 0.02, 0.0)), WR_L], [0.26, 0.36, 0.32], n=7)
    bm_blob(k[LAVA], rnd, WR_L, 0.25, jitter=0.08)
    bm_boulder(k[BASALT], rnd, FIST_C - Z * 0.32, 0.37, squash=(1.0, 1.0, 0.9), n=15, sink=0.0)
    side = FL_DIR.cross(Z).normalized()
    for o in (-0.24, -0.08, 0.08, 0.24):                                        # knuckles
        bm_boulder(k[BASALT2], rnd, FIST_C + FL_DIR * 0.27 + side * o - Z * 0.14, 0.13, n=8, sink=0.0)
    bm_boulder(k[BASALT2], rnd, FIST_C + side * 0.33 + FL_DIR * 0.05 - Z * 0.1, 0.14, n=8, sink=0.0)       # thumb
    k.emit("Head_ArmL2", col, rig=rig, bone="arm.L.2", vary=0.08)
    # ---- embers rising round it, bubbles in the pool
    for i, (x, y) in enumerate(EMBERS):
        bm_crystal(k[HOT], (x, y, 0.1), (x, y, 0.26), 0.05, n=4, shoulder=0.5, foot=0.3)
        k.emit("Head_Ember%d" % i, col, rig=rig, bone="ember.%d" % i)
    for i, (x, y) in enumerate(BUBBLES):
        bm_ellipsoid(k[HOT], (x, y, 0.07), (0.1, 0.1, 0.07), u=7, v=4)
        k.emit("Head_Bubble%d" % i, col, rig=rig, bone="bubble.%d" % i)
    empty("Muzzle", col, head, (0.45, 1.7, 1.9), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 26
RELEASE = 4


def pose(rig, t=0.0, breathe=0.0, look=0.0, nod=0.0, jaw=0.0, lean=0.0, twist=0.0, dip=0.0, ra=0.0, rf=0.0, rh=0.0, la=0.0, lf=0.0,
         rock=1.0, core=1.0, sway=1.0):
    """t: where the loop is (0..1): embers, bubbles, the banner. lean: degrees forward; twist: to its left; ra / rf / rh:
    the right arm swung forward at the shoulder, the elbow, the wrist; la / lf: the left."""
    pb = rig.pose.bones
    rest_pose(rig)
    turn(pb, "hips", x=-lean * 0.35)
    shift(pb, "hips", (0, 0, -dip))
    turn(pb, "chest", x=-lean * 0.65, z=twist)
    scale_arm(pb, "chest", (1 + breathe, 1 + breathe, 1))
    turn(pb, "head", x=-nod + lean * 0.5, z=look - twist * 0.6)                 # (it keeps its eyes on its mark)
    turn(pb, "jaw", x=-jaw * 24)
    turn(pb, "arm.R.1", x=ra)
    turn(pb, "arm.R.2", x=rf)
    turn(pb, "hand.R", x=rh)
    turn(pb, "arm.L.1", x=la)
    turn(pb, "arm.L.2", x=lf)
    s = max(rock, 0.02)
    pb["rock"].scale = (s, s, s)
    pb["core"].scale = (core, core, core)
    for i in range(3):                  # the banner hangs plumb when the golem bends, and swings out from its back
        b = pb["banner.%d" % (i + 1)]
        out = (lean * 0.9 if i == 0 else 0.0) + (2.5 + 2.0 * i) * sway * (1 + math.sin(2 * math.pi * (t * 2 - 0.15 * i)))
        b.rotation_quaternion = arm_space_quat(b, (1, 0, 0), -out)
    for i in range(len(EMBERS)):
        u = (t * 2 + i * 0.37) % 1.0
        s = max(0.02, math.sin(math.pi * u) ** 0.7 * (1.0 - 0.5 * u))
        pb["ember.%d" % i].scale = (s, s, s)
        shift(pb, "ember.%d" % i, (0.1 * math.sin(2 * math.pi * u * 2 + i), 0.08 * math.cos(2 * math.pi * u + i), 1.9 * u))
    for i in range(len(BUBBLES)):
        u = (t * 3 + i * 0.4) % 1.0
        s = max(0.02, smooth(u / 0.5) * (1.0 - smooth((u - 0.5) / 0.08)))
        pb["bubble.%d" % i].scale = (s, s * 1.3, s)


def _idle(f):
    t = f / IDLE_LEN
    ph = 2 * math.pi * t
    return dict(t=t, breathe=0.016 * math.sin(ph * 2), core=1.0 + 0.14 * math.sin(ph * 2), look=14 * math.sin(ph), nod=3 * math.sin(ph * 2 + 1.0),
                ra=2 * math.sin(ph * 2), rf=3 * math.sin(ph * 2 + 0.8), la=3 * math.sin(ph + 1.0), lf=4 * math.sin(ph + 2.0),
                rock=1.0 + 0.05 * math.sin(ph * 4), lean=1.5 * math.sin(ph * 2 + 0.5))


def _fire(f):
    """Frames 0-2 it swings the rock back, 2-4 flings it underhand (gone on frame 4), follows through; 8-14 it bends
    and plunges the hand into the pool; a new rock wells up in it; 18-26 it straightens up."""
    base = _idle(0)
    fade = 1 - smooth(f / 2.0) * (1 - smooth((f - 20) / 6.0))                  # the idle's own sway, out and back in
    p = {key: (v * fade if key not in ("t", "core", "rock") else v) for key, v in base.items()}
    p.update(t=f / FIRE_LEN,
             ra=p["ra"] + track(f, [(0, 0), (2, -34), (4, 108), (7, 126), (13, 30), (17, 24), (26, 0)]),
             rf=p["rf"] + track(f, [(0, 0), (2, -55), (4, -95), (7, -80), (13, -62), (17, -50), (26, 0)]),
             rh=track(f, [(0, 0), (4, 6), (8, 0), (13, -40), (17, -18), (26, 0)]),
             lean=p["lean"] + track(f, [(0, 0), (2, -7), (4, 13), (7, 17), (13, 34), (17, 31), (26, 0)]),
             twist=track(f, [(0, 0), (2, -16), (4, 13), (7, 17), (13, 8), (18, 4), (26, 0)]),
             dip=track(f, [(0, 0), (8, 0), (13, 0.14), (17, 0.13), (26, 0)]),
             la=p["la"] + track(f, [(0, 0), (2, 12), (4, -24), (8, -16), (13, 12), (26, 0)]),
             jaw=track(f, [(0, 0), (2, 0.3), (4, 1.0), (8, 0.8), (12, 0), (26, 0)]),
             rock=1.0 if f < RELEASE else smooth((f - 13) / 5.0),
             core=base["core"] + 0.5 * bump(f, 4, 4))
    return p


def build_anims():
    rig = bpy.data.objects["Rig"]
    pose(rig, **_fire(RELEASE))                                                 # where the rock leaves the hand: the muzzle
    bpy.context.view_layer.update()
    p = rig.matrix_world @ rig.pose.bones["rock"].head
    bpy.data.objects["Muzzle"].location = bpy.data.objects["Head"].matrix_world.inverted() @ p
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


PREVIEW = {"target": (0, 0.1, 1.2), "dist": 10.5, "yaw": 150, "pitch": 18, "anim_target": (F.x, F.y + 0.3, 1.6), "anim_dist": 6.4,
           "frames": [("idle", 0), ("fire", 2), ("fire", 3), ("fire", 4), ("fire", 14)],
           "extra": [{"yaw": 162, "pitch": 8, "dist": 3.4, "target": (F.x, F.y + 0.3, 2.3)},
                     {"yaw": 0, "pitch": 50, "dist": 9.5, "target": (0, 0.1, 0.9)},
                     {"yaw": 25, "pitch": 20, "dist": 5.2, "target": (F.x, F.y, 1.7)},
                     {"yaw": 215, "pitch": 28, "dist": 6.5, "target": (BL.x, BL.y, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
