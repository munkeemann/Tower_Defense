"""Builds the Elder Treant (footprint "star5": [0,0] middle, [1,-1], [-1,0], [1,0], [-1,1] around it), a Verdant tower:
it slams the ground at short range (GameData.STRIKES "erupt": the blow shows as build_strike()'s roots).

    python tools/blender/build.py treant --out <preview dir>

One tree-giant owns all five hexes. Its bole stands rooted on the middle hex, and its great buttress roots sprawl over
the four hexes round it, each gripping something: a mossy boulder (front right), a toppled rune stone (front left),
a ring of toadstools (back right), a sapling it shelters (back left). The giant itself is the Head: from the waist up
it turns in its bole to face its prey. A hunched bark body with plates of bark and mossy shoulders, a face (heavy brow,
glowing eyes, a twig nose, a jagged mouth and a beard of moss), two heavy arms ending in gnarled fists, antlers of bare
branch and a crown of leaves. The team's colors: the mantle down its back, the bracers on its forearms and a ribbon
tied to an antler.
Clips: idle (sways, breathes, the crown shivers, fingers flex, it blinks), fire (rears with both fists overhead and
brings them down in front, roaring; the fists land 0.3 s in, a shudder runs up the crown).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open(os.path.join(REPO, "tools", "blender", "greatwood_common.py"), encoding="utf-8").read())

TID = "treant"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)
TOP = 0.34
T = TOP + 0.05                  # the turf's top (plinth(turf=True))
EYES = (0.85, 1.0, 0.35)
TS = 0.95                       # the giant's scale (laid out at 1.0)
WAIST = T + 0.46                # the Head: where the body turns in its bole
SPINE = ["root", "hips", "chest", "head"]


def rp(a, r, off=0.0, z=0.0):
    """A point r out from the middle at angle a (degrees), `off` to the left of that line, z above the turf."""
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return Vector((C0.x + ca * r - sa * off, C0.y + sa * r + ca * off, T + z))


def build_base():
    col = collection("Treant")
    root = empty("Treant", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(52)
    k = Kit()
    # ---- the bole: the giant's foot, flaring into six buttresses (the four big ones toward the outer hexes)
    lobes = {30: 0.5, 150: 0.5, 210: 0.5, 330: 0.5, 90: 0.08, 270: 0.08, 0: -0.1, 60: -0.12, 120: -0.12, 180: -0.1, 240: -0.12, 300: -0.12}
    bole = Trunk((C0.x, C0.y, T), [(-0.08, 0.8, 0.8, 1.0), (0.14, 0.7, 0.7, 0.8), (0.36, 0.63, 0.61, 0.4), (0.56, 0.6, 0.57, 0.1)],
                 list(range(0, 360, 30)), lobes, rnd, 0.03)
    bole.loft(k[BARK])
    bm_plates(k[BARK_PLATE], bole.rings, rnd, th=(0.03, 0.055), rows=(1.1, 2.0), gap=0.16, side=0.12, point=0.28)

    def run(a, pts, radii, n=6, claw=3, reach=0.3, thick=0):
        ctrl = [rp(a, r, off, z) for r, off, z in pts]
        cp, rad, rings = bm_root(k[ROOT], ctrl, radii, n=n, sub=2, squash=1.12)
        if thick:                                                # (a great root: pads of moss along it)
            for i in (3, 6, 8):
                if rnd.random() < 0.8:
                    bm_blob(k[MOSS], rnd, cp[i] + Vector((0, 0, rad[i] * 0.72)), rad[i] * 1.05, squash=(1.25, 1.25, 0.4), jitter=0.2)
        if claw:
            bm_claw(k[ROOT], cp[-1], cp[-1] - cp[-2], rad[-1], rnd, toes=claw, reach=reach, T=T, n=4)
        return cp
    big = [0.3, 0.26, 0.22, 0.18, 0.14, 0.11]
    mid = [0.17, 0.155, 0.13, 0.11, 0.09]
    # front right: two roots clasp a mossy boulder, a third lies over it
    run(30, [(0.5, 0, 0.4), (0.95, 0.06, 0.3), (1.4, -0.15, 0.19), (1.85, -0.44, 0.17), (2.3, -0.52, 0.13), (2.6, -0.32, 0.08)], big, n=7, thick=10)
    run(30, [(1.05, 0.1, 0.24), (1.4, 0.42, 0.16), (1.8, 0.64, 0.14), (2.15, 0.66, 0.1), (2.42, 0.5, 0.06)], mid, claw=2, reach=0.24)
    run(30, [(1.62, -0.3, 0.2), (1.86, -0.14, 0.52), (2.1, 0.08, 0.66), (2.3, 0.24, 0.5)], [0.1, 0.09, 0.075, 0.0], claw=0)
    # front left: the roots pin a toppled rune stone
    run(150, [(0.5, 0, 0.4), (0.95, -0.08, 0.3), (1.4, -0.2, 0.24), (1.78, -0.32, 0.42), (2.06, -0.34, 0.54), (2.36, -0.2, 0.3), (2.62, -0.05, 0.08)],
        [0.3, 0.26, 0.22, 0.19, 0.17, 0.14, 0.11], n=7, thick=10)
    run(150, [(1.0, -0.12, 0.26), (1.32, -0.5, 0.17), (1.62, -0.74, 0.13), (1.9, -0.8, 0.08)], mid[:4], claw=2, reach=0.18)
    run(150, [(1.1, 0.15, 0.24), (1.42, 0.5, 0.2), (1.7, 0.74, 0.2), (1.9, 0.86, 0.1)], [0.15, 0.13, 0.11, 0.09], claw=2, reach=0.15)
    # back left: two roots part round a sapling and close again
    run(210, [(0.5, 0, 0.4), (0.95, 0.0, 0.3), (1.35, 0.2, 0.2), (1.8, 0.5, 0.16), (2.25, 0.44, 0.13), (2.58, 0.14, 0.08)], big, n=7, thick=10)
    run(210, [(1.0, -0.05, 0.26), (1.4, -0.32, 0.18), (1.85, -0.52, 0.14), (2.28, -0.42, 0.1), (2.52, -0.16, 0.06)], mid, claw=2, reach=0.22)
    # back right: a fork full of toadstools
    run(330, [(0.5, 0, 0.4), (0.95, 0.04, 0.3), (1.4, 0.22, 0.2), (1.9, 0.44, 0.16), (2.35, 0.34, 0.12), (2.62, 0.08, 0.07)], big, n=7, thick=10)
    run(330, [(1.05, -0.05, 0.24), (1.45, -0.4, 0.16), (1.85, -0.64, 0.12), (2.22, -0.58, 0.08)], mid[:4], claw=2, reach=0.22)
    # the middle hex's own short roots (front, back and to the sides)
    for a, far in ((90, 0.74), (270, 0.74), (0, 0.98), (180, 0.98)):
        run(a, [(0.45, 0, 0.3), (far * 0.75, 0.07, 0.17), (far, 0.0, 0.06)], [0.17, 0.13, 0.09], claw=2, reach=0.14)
    k.emit("Bole", col, root, vary=0.05, seed=4)
    # ---- what the roots hold
    B = rp(30, 2.1, 0.1)
    bm_boulder(k["stone:0.12:0.9"], rnd, (B.x, B.y, T - 0.02), 0.42, squash=(1.1, 0.95, 0.86), n=14)
    bm_boulder(k["stone:0.2:0.95"], rnd, tuple(rp(30, 2.5, 0.12, -0.02)), 0.17, n=9)
    bm_boulder(k["stone:0.2:0.95"], rnd, tuple(rp(30, 1.72, 0.3, -0.02)), 0.14, n=9)
    bm_blob(k[MOSS], rnd, (B.x - 0.08, B.y - 0.05, T + 0.55), 0.26, squash=(1.2, 1.0, 0.35), jitter=0.16)
    d240 = Vector((math.cos(math.radians(240)), math.sin(math.radians(240)), 0))
    S0 = rp(150, 2.05, 0.1, 0.1) - d240 * 0.62
    face = bm_menhir(k, rnd, S0, 1.35, w=0.56, d=0.34, yaw=330, lean=(-77, 0), stone="stone2:0.1:0.92")
    bm_rune(k["glow:%s,%s,%s,0.8" % SPIRIT], "tree", face, 0.56, size=0.52, w=0.05)
    k.emit("Held", col, root, vary=0.07, seed=2)
    for i, (r, off, h, cr, lean) in enumerate(((1.92, -0.1, 0.5, 0.34, (0.05, 0.03)), (1.6, 0.05, 0.3, 0.2, (-0.04, 0.02)), (2.24, -0.2, 0.34, 0.23, (0.05, -0.04)),
                                               (2.05, 0.2, 0.2, 0.13, (0.0, 0.03)), (1.7, -0.3, 0.17, 0.11, (-0.02, -0.02)), (2.4, 0.08, 0.15, 0.1, (0.02, 0.02)))):
        bm_mushroom(k, rnd, rp(330, r, off), h, cr, cap="orange:0.05:0.7", spots="cream:0.0:0.4" if i < 3 else None, lean=lean, n=7 if i < 3 else 6)
    for (a, r, off, h, cr) in ((90, 0.86, -0.3, 0.14, 0.09), (270, 0.9, 0.34, 0.16, 0.1), (270, 0.98, 0.2, 0.1, 0.07), (150, 2.5, 0.42, 0.14, 0.09)):
        bm_mushroom(k, rnd, rp(a, r, off), h, cr, cap="orange:0.05:0.7", n=6)
    k.emit("Shrooms", col, root, vary=0.05)
    # the sapling: a slip of a tree in a ring of stones
    P = rp(210, 2.0, -0.02)
    bm_root(k[BARK], [P - Vector((0, 0, 0.05)), P + Vector((0.03, 0.02, 0.3)), P + Vector((-0.03, 0.0, 0.62)), P + Vector((0.0, 0.02, 0.88))], [0.07, 0.06, 0.045, 0.03], n=5)
    bm_root(k[BARK], [P + Vector((0.0, 0.0, 0.42)), P + Vector((0.16, 0.06, 0.6)), P + Vector((0.2, 0.08, 0.74))], [0.035, 0.03, 0.02], n=4)
    bm_root(k[BARK], [P + Vector((-0.02, 0.0, 0.5)), P + Vector((-0.15, -0.08, 0.66)), P + Vector((-0.18, -0.1, 0.78))], [0.035, 0.03, 0.02], n=4)
    for (dx, dy, dz, r, sw) in ((0.0, 0.02, 0.98, 0.27, LEAF_C), (0.22, 0.09, 0.8, 0.19, LEAF_A), (-0.2, -0.11, 0.84, 0.21, LEAF_A)):
        bm_blob(k[sw], rnd, (P.x + dx, P.y + dy, P.z + dz), r, squash=(1, 1, 0.82), jitter=0.13, sub=2)
    for i in range(6):
        a = math.radians(60 * i + rnd.uniform(-12, 12))
        bm_boulder(k["stone:0.15:0.9"], rnd, (P.x + math.cos(a) * 0.3, P.y + math.sin(a) * 0.3, T - 0.02), rnd.uniform(0.07, 0.1), n=8)
    k.emit("Sapling", col, root, vary=0.06)
    # ---- the forest floor: moss among the roots, ferns, shelf fungus on the bole
    for (a, r, off, s) in ((30, 1.5, 0.14, 0.36), (30, 2.2, -0.2, 0.3), (150, 1.5, 0.12, 0.34), (150, 2.4, 0.3, 0.3), (210, 1.6, 0.06, 0.3),
                           (210, 2.36, 0.0, 0.26), (330, 1.5, -0.06, 0.34), (330, 2.36, -0.2, 0.3), (90, 0.7, 0.4, 0.26), (270, 0.72, -0.42, 0.26),
                           (0, 0.95, 0.3, 0.24), (180, 0.95, 0.3, 0.24), (150, 1.7, -0.56, 0.24), (330, 2.0, 0.72, 0.22),
                           (30, 2.5, 0.5, 0.3), (30, 2.55, -0.45, 0.26), (150, 2.5, -0.5, 0.3), (150, 2.6, 0.4, 0.26), (210, 2.5, 0.5, 0.3),
                           (210, 2.6, -0.42, 0.26), (330, 2.5, -0.5, 0.3), (330, 2.6, 0.42, 0.26), (210, 1.5, 0.6, 0.26), (330, 1.5, 0.62, 0.26)):
        q = rp(a, r, off, -0.01)
        if not in_footprint(CELLS, q.x, q.y, 0.3):
            continue
        bm_blob(k[MOSS if rnd.random() < 0.6 else "teal:0.3:0.8"], rnd, tuple(q), s, squash=(1.2, 1.0, 0.16), jitter=0.2)
    for (a, r, off, n_, L) in ((30, 2.16, 0.58, 5, 0.36), (30, 1.9, -0.7, 5, 0.3), (150, 2.5, 0.5, 5, 0.34), (210, 2.42, 0.62, 5, 0.32),
                               (210, 1.62, -0.66, 5, 0.34), (330, 2.5, -0.3, 5, 0.3), (330, 1.4, 0.62, 5, 0.3)):
        bm_fern(k["grass:0.1:0.75"], rnd, rp(a, r, off), n=n_, length=L, rise=L * 0.7, w=0.1)
    for a, z, r in ((62, 0.34, 0.15), (118, 0.26, 0.13), (242, 0.34, 0.16), (298, 0.24, 0.12)):
        bm_shelf(k["sand:0.1:0.7"], bole.at(a, z, -0.01), bole.out(a), r=r, th=0.05)
    for i in range(22):                                          # fallen leaves
        a, r = rnd.uniform(0, 360), rnd.uniform(0.95, 1.5)
        p = rp(a, r, 0, 0.012)
        if in_footprint(CELLS, p.x, p.y, 0.25):
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
            bm_leaf(k["orange:0.1:0.7" if i % 3 else "gold:0.2:0.8"], p, p + d * 0.13 + Vector((0, 0, 0.01)), 0.08)
    k.emit("Floor", col, root, vary=0.08)
    empty("Head", col, root, (C0.x, C0.y, WAIST), 0.5, "SINGLE_ARROW")
    return root


# ---- the giant from the waist up, in the head's space (+Y forward), laid out at 1.0
TORSO = [(-0.42, 0.40, 0.38, 0, 0, 0.0), (-0.05, 0.46, 0.42, 0, 0, 0.0), (0.3, 0.42, 0.39, 0, 0, 0.0), (0.62, 0.5, 0.44, 0, 0, 0.02),
         (0.95, 0.72, 0.52, 0, 0, 0.05), (1.18, 0.74, 0.5, 0, 0, 0.08), (1.36, 0.5, 0.46, 0, 0, 0.11), (1.61, 0.47, 0.45, 0, 0, 0.13),
         (1.82, 0.42, 0.41, 0, 0, 0.11), (1.96, 0.3, 0.3, 0, 0, 0.07)]
FZ = 0.16                       # (the face's heights below were laid out on a shorter trunk)
ARM = {"S": (0.76, 0.05, 1.16), "E": (1.14, -0.02, 0.66), "W": (1.04, 0.44, 0.33), "F": (1.0, 0.6, 0.2), "K": (1.0, 0.83, 0.24)}
ANTLERS = [([(-0.2, -0.02, 1.86), (-0.52, -0.1, 2.14), (-0.74, -0.15, 2.46), (-0.7, -0.13, 2.8)], [0.095, 0.08, 0.055, 0.0]),
           ([(-0.52, -0.1, 2.14), (-0.9, -0.06, 2.28), (-1.06, -0.05, 2.56)], [0.06, 0.05, 0.0]),
           ([(0.2, -0.02, 1.86), (0.54, -0.12, 2.12), (0.78, -0.16, 2.42), (0.82, -0.12, 2.72)], [0.095, 0.08, 0.055, 0.0]),
           ([(0.54, -0.12, 2.12), (0.94, -0.1, 2.22), (1.1, -0.06, 2.46)], [0.06, 0.05, 0.0]),
           ([(0.78, -0.16, 2.42), (0.64, -0.3, 2.58), (0.66, -0.36, 2.76)], [0.04, 0.03, 0.0])]
RIBBON = (-0.99, -0.07, 2.3)    # tied to the left antler's fork
BONES = {
    "root": ((0, 0, -0.45), (0, 0, -0.15), None),
    "hips": ((0, 0, -0.15), (0, 0, 0.55), "root"),
    "chest": ((0, 0, 0.55), (0, 0.05, 1.16), "hips"),
    "head": ((0, 0.08, 1.18), (0, 0.11, 1.86), "chest"),
    "jaw": ((0, 0.3, 1.32), (0, 0.62, 1.24), "head"),
    "brow": ((0, 0.5, 1.74), (0, 0.7, 1.74), "head"),
    "eyes": ((0, 0.5, 1.57), (0, 0.62, 1.57), "head"),
    "crown.1": ((0, -0.05, 1.91), (0, -0.08, 2.16), "head"),
    "crown.2": ((0, -0.08, 2.16), (0, -0.1, 2.41), "crown.1"),
    "crown.3": ((0, -0.1, 2.41), (0, -0.1, 2.66), "crown.2"),
}
for _s, _sx in (("R", 1), ("L", -1)):
    _S, _E, _W, _F, _K = (Vector((p[0] * _sx, p[1], p[2])) for p in (ARM["S"], ARM["E"], ARM["W"], ARM["F"], ARM["K"]))
    BONES["arm.%s.1" % _s] = (tuple(_S), tuple(_E), "chest")
    BONES["arm.%s.2" % _s] = (tuple(_E), tuple(_W), "arm.%s.1" % _s)
    BONES["hand.%s" % _s] = (tuple(_W), tuple(_F + (_F - _W) * 0.6), "arm.%s.2" % _s)
    BONES["fingers.%s" % _s] = (tuple(_K), tuple(_K + Vector((0, 0.02, -0.22))), "hand.%s" % _s)
flag_bones(BONES, "ribbon", RIBBON, (0, 0, -1), 0.62, segs=3, parent="crown.1")


def build_head():
    col = collection("Treant")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=TS)
    rnd = random.Random(7)
    S = TS
    k = Kit()
    torso = Trunk((0, 0, 0), TORSO, list(range(0, 360, 30)), power=2.4)
    fp = lambda x, z, out=0.0: torso.at(90 - x, z + FZ, out)  # a point on its face, x degrees round to its right
    glow = "glow:%s,%s,%s,1.0" % EYES

    # ---- the body: one loft from inside the bole to the top of the head, scaled with bark (bare where the face and
    # the mantle go), moss on the shoulders and round the waist
    torso.loft(k[BARK])

    def bare(c):
        a = math.degrees(math.atan2(c.y - 0.08, c.x)) % 360
        return c.z < 0.1 or (38 < a < 142 and c.z > 1.12) or (205 < a < 335 and 0.3 < c.z < 1.3)
    bm_plates(k[BARK_PLATE], torso.rings, rnd, th=(0.035, 0.065), rows=(1.0, 1.9), gap=0.14, side=0.1, skip=bare, start=1.0, point=0.26)
    for sx in (-1, 1):
        bm_blob(k[MOSS], rnd, (sx * 0.58, -0.02, 1.3), 0.32, squash=(1.1, 1.0, 0.5), jitter=0.15, sub=2)
        bm_blob(k["teal:0.2:0.8"], rnd, (sx * 0.32, -0.24, 1.38), 0.2, squash=(1.0, 1.0, 0.5), jitter=0.18)
    bm_blob(k[MOSS], rnd, (0.0, -0.3, 1.47), 0.22, squash=(1.3, 0.9, 0.5), jitter=0.16)
    for i in range(9):                                           # a skirt of moss where it turns in the bole
        a = 40 * i + rnd.uniform(-8, 8)
        bm_blob(k[MOSS if i % 3 else "teal:0.2:0.8"], rnd, tuple(torso.at(a, 0.12, 0.02)), rnd.uniform(0.15, 0.2), squash=(1, 1, 0.6), jitter=0.18)
    # a broken bough on its right shoulder, a knothole in its side
    bm_root(k[BARK], [(0.56, -0.12, 1.3), (0.8, -0.2, 1.52), (0.9, -0.22, 1.7)], [0.13, 0.11, 0.1], n=6, sub=2)
    bm_cyl(k[BARK_PALE], 0.085, 0.07, 0.03, (0.905, -0.221, 1.71), rot=(-6, 28, 0), seg=6)
    bm_sprig(k[LEAF_A], rnd, Vector((0.82, -0.2, 1.56)), (0.6, -0.5, 0.5), n=3, size=0.22)
    kn = torso.at(160, 0.72, 0.0)
    bm_ellipsoid(k["black:0.3:0.8"], tuple(kn), (0.05, 0.1, 0.13), (0, 0, -20), u=7, v=5)
    bm_shelf(k["sand:0.1:0.7"], torso.at(160, 0.56, -0.01), torso.out(160), r=0.13, th=0.045)
    # the face: a twig nose, the roof of the mouth with its fangs, the dark of the mouth and of the eye sockets, ears
    for sx in (-1, 1):
        bm_ellipsoid(k["black:0.3:0.8"], tuple(fp(sx * 21, 1.41, -0.015)), (0.125, 0.07, 0.092), (0, sx * -14, sx * -15), u=8, v=5)
        bm_box(k["black:0.3:0.8"], (0.25, 0.05, 0.2), tuple(fp(sx * 14, 1.1, 0.0)), (0, 0, sx * -15))
        bm_beam(k[BARK_PLATE], fp(0, 1.215, 0.06), fp(sx * 33, 1.19, 0.035), 0.15, 0.085, w1=0.1, h1=0.07)
        for x in (8, 21):
            bm_crystal(k["cream:0.05:0.45"], fp(sx * x, 1.19, 0.075), fp(sx * x, 1.08, 0.085), 0.036, n=4, shoulder=0.3)
        bm_shelf(k["sand:0.1:0.7"], torso.at(90 - sx * 84, 1.4 + FZ, -0.01), torso.out(90 - sx * 84), r=0.15, th=0.05, tilt=0.05)
    bm_root(k[BARK_PLATE], [fp(0, 1.38, -0.06), fp(0, 1.335, 0.13), fp(0, 1.25, 0.23), fp(0, 1.17, 0.265)], [0.09, 0.085, 0.07, 0.05], n=6, sub=2)
    k.emit("Head_Body", col, rig=rig, bones=SPINE, scale=S, vary=0.05, seed=3)
    # the mantle in the team's color down its back, hung from a rope over its shoulders; gold along its dagged hem
    cols_a = (218, 235, 252, 270, 288, 305, 322)
    hem = (0.5, 0.33, 0.5, 0.26, 0.5, 0.33, 0.5)
    flare = lambda z: 0.05 + 0.07 * max(0.0, 1.0 - (z - 0.25) / 0.95)

    def cape_row(zs, grow=0.0, inner=0.0):
        zs = [zs] * 7 if isinstance(zs, (int, float)) else list(zs)
        return ([torso.at(a, z, flare(z) + grow) for a, z in zip(cols_a, zs)] +
                [torso.at(a, z, inner) for a, z in reversed(list(zip(cols_a, zs)))])
    bm_loft(k["team!:0.12:0.72"], [cape_row(1.26), cape_row(0.96), cape_row(0.68), cape_row(hem)])
    bm_loft(k["gold:0.1:0.55"], [cape_row([z + 0.1 for z in hem], 0.014, 0.04), cape_row([z - 0.012 for z in hem], 0.014, 0.04)])
    bm_loft(k["gold:0.1:0.55"], [cape_row(1.27, 0.014, 0.04), cape_row(1.2, 0.014, 0.04)])

    def cape_face(u, v):
        a = 270 + math.degrees(u / 0.5)
        return torso.at(a, v, flare(v) + 0.008), torso.out(a), Vector((0, 0, 1))
    bm_rune(k["gold:0.1:0.55"], "tree", cape_face, 0.6, size=0.44, w=0.05, th=0.02)
    bm_tube(k["sand:0.3:0.75"], [torso.at(a, 1.25, 0.035) for a in range(170, 371, 25)], 0.04, n=4)
    k.emit("Head_Mantle", col, rig=rig, bones=SPINE, scale=S)
    # the jaw: an underbite of bark with fangs, and the beard of moss hanging from it
    for sx in (-1, 1):
        bm_beam(k[BARK_PLATE], fp(0, 1.035, 0.13), fp(sx * 34, 1.065, 0.035), 0.17, 0.115, w1=0.1, h1=0.085)
    for x in (-25, -13, 0, 13, 25):
        b = fp(x, 1.075, 0.125 - abs(x) * 0.0028)
        bm_crystal(k["cream:0.05:0.45"], b, b + Vector((0, 0.01, 0.105 if x else 0.085)), 0.034, n=4, shoulder=0.3)
    for i, (x, L, r) in enumerate(((-27, 0.3, 0.075), (-14, 0.46, 0.09), (0, 0.6, 0.1), (14, 0.48, 0.09), (27, 0.32, 0.075), (-7, 0.38, 0.07), (8, 0.36, 0.07))):
        b = fp(x, 1.0, 0.07 if i < 5 else 0.13)
        bm_crystal(k[MOSS if i % 2 == 0 else "teal:0.2:0.8"], b + Vector((0, 0, 0.04)), b + Vector((rnd.uniform(-0.03, 0.03), 0.05, -L)), r, n=4, shoulder=0.3, foot=0.8)
    k.emit("Head_Jaw", col, rig=rig, bone="jaw", scale=S, vary=0.05)
    # the brow: two heavy beams of bark frowning over the eyes, tufted with moss
    for sx in (-1, 1):
        bm_beam(k[BARK_PLATE], fp(0, 1.545, 0.05), fp(sx * 44, 1.67, 0.03), 0.16, 0.125, w1=0.11, h1=0.09)
        bm_blob(k[MOSS], rnd, tuple(fp(sx * 24, 1.69, 0.03)), 0.11, squash=(1.5, 1.0, 0.5), jitter=0.2)
    k.emit("Head_Brow", col, rig=rig, bone="brow", scale=S, bevel=0.012)
    for sx in (-1, 1):
        bm_ellipsoid(k[glow], tuple(fp(sx * 21, 1.405, 0.038)), (0.074, 0.03, 0.054), (0, sx * -14, sx * -15), u=7, v=5)
    k.emit("Head_Eyes", col, rig=rig, bone="eyes", scale=S)
    # ---- arms: one bark tube each from shoulder to wrist, scaled with bark, a bracer in the team's color, and a
    # gnarled knot of a fist whose fingers flex
    for s, sx in (("R", 1), ("L", -1)):
        S_, E_, W_, F_ = (Vector((p[0] * sx, p[1], p[2])) for p in (ARM["S"], ARM["E"], ARM["W"], ARM["F"]))
        path = [S_ + Vector((-0.26 * sx, 0, 0.02)), S_, S_.lerp(E_, 0.5) + Vector((0.04 * sx, -0.03, 0)), E_, E_.lerp(W_, 0.5) + Vector((0.03 * sx, 0, -0.03)), W_, F_]
        cp, rad, rings = bm_root(k[BARK], path, [0.21, 0.26, 0.21, 0.21, 0.265, 0.245, 0.22], n=8, sub=2)
        bm_plates(k[BARK_PLATE], rings, rnd, th=(0.03, 0.05), rows=(2.0, 3.2), gap=0.3, side=0.1, start=1.7, end=7.7, point=0.28, keep=0.72)
        bm_sleeve(k["team!:0.15:0.7"], rings, 8.25, 10.1, grow=0.032)
        bm_sleeve(k["gold:0.1:0.55"], rings, 8.0, 8.3, grow=0.048)
        bm_sleeve(k["gold:0.1:0.55"], rings, 10.0, 10.3, grow=0.048)
        bm_crystal(k[BARK_PALE], E_ + Vector((0.08 * sx, -0.08, 0.02)), E_ + Vector((0.22 * sx, -0.32, 0.1)), 0.075, n=5, shoulder=0.75, foot=1.0)   # an elbow spur
        k.emit("Head_Arm" + s, col, rig=rig, bones=["arm.%s.1" % s, "arm.%s.2" % s, "hand.%s" % s], scale=S, vary=0.05)
        bm_blob(k[BARK], rnd, F_, 0.29, squash=(0.95, 1.1, 0.9), jitter=0.1, sub=2)
        bm_root(k[BARK], [F_ + Vector((-0.23 * sx, 0.02, 0.0)), F_ + Vector((-0.35 * sx, 0.18, -0.08)), F_ + Vector((-0.28 * sx, 0.31, -0.23))], [0.095, 0.085, 0.055], n=5, sub=2)
        for i in range(3):                                           # knuckles
            bm_blob(k[BARK_PLATE], rnd, F_ + Vector(((i - 1) * 0.17, 0.15, 0.19)), 0.095, jitter=0.12)
        k.emit("Head_Fist" + s, col, rig=rig, bone="hand." + s, scale=S)
        for i in range(4):
            dx = (i - 1.5) * 0.135
            bm_root(k[BARK], [F_ + Vector((dx, 0.18, 0.07)), F_ + Vector((dx, 0.35, -0.06)), F_ + Vector((dx, 0.28, -0.25)), F_ + Vector((dx, 0.12, -0.31))],
                    [0.09, 0.088, 0.07, 0.05], n=5, sub=2)
        k.emit("Head_Fingers" + s, col, rig=rig, bone="fingers." + s, scale=S)
    # ---- the crown, set back from the brow: boughs and two antlers of bare branch, then three tiers of leaves
    top = Vector((0, 0.05, 1.88))
    for pts, rad in ANTLERS:
        bm_root(k[BARK], [Vector(p) for p in pts], rad, n=5, sub=2)
    t1 = [(90, 0.3, 0.28, 2.15), (160, 0.45, 0.37, 2.12), (232, 0.46, 0.38, 2.17), (306, 0.46, 0.38, 2.14), (20, 0.45, 0.36, 2.12)]
    for a, rr, r, z in t1:
        c = Vector((math.cos(math.radians(a)) * rr, -0.14 + math.sin(math.radians(a)) * rr, z))
        bm_tube(k[BARK], [top, top.lerp(c, 0.6) + Vector((0, 0, 0.05)), c], [0.1, 0.075, 0.05], n=5)
    bm_tube(k["sand:0.3:0.75"], [Vector(RIBBON) + Vector((0.09, 0, d)) for d in (0.03, -0.03)], 0.075, n=5)                 # the ribbon's knot
    k.emit("Head_Boughs", col, rig=rig, bone="crown.1", scale=S)
    for i, (a, rr, r, z) in enumerate(t1):
        c = Vector((math.cos(math.radians(a)) * rr, -0.14 + math.sin(math.radians(a)) * rr, z))
        bm_blob(k[LEAF_B if i % 2 else LEAF_A], rnd, c, r, squash=(1.05, 1.05, 0.74), jitter=0.14, sub=2)
    k.emit("Head_Crown1", col, rig=rig, bone="crown.1", scale=S)
    for i, a in enumerate((60, 180, 300)):
        c = Vector((math.cos(math.radians(a)) * 0.22, -0.16 + math.sin(math.radians(a)) * 0.22, 2.44))
        bm_blob(k[LEAF_A if i % 2 else LEAF_B], rnd, c, 0.33, squash=(1.05, 1.05, 0.76), jitter=0.14, sub=2)
    k.emit("Head_Crown2", col, rig=rig, bone="crown.2", scale=S)
    bm_blob(k[LEAF_TOP], rnd, (0.0, -0.17, 2.72), 0.3, squash=(1.05, 1.05, 0.8), jitter=0.14, sub=2)
    for pts, rad in ANTLERS:
        tip = Vector(pts[-1])
        bm_sprig(k[LEAF_A], rnd, tip - Vector((0, 0, 0.04)), (tip.x, 0, 0.6), n=3, size=0.2)
    k.emit("Head_Crown3", col, rig=rig, bone="crown.3", scale=S)
    flag_part("Head_Ribbon", col, rig, "ribbon", Vector(RIBBON) * S, (0, 0, -1), 0.62 * S, 0.17 * S, segs=3, swatch="team!", tail="swallow", hang=(1, 0, 0))
    empty("Muzzle", col, head, (0, 1.0 * S, 0.3 * S), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 24
GROUND = -(WAIST - T) / TS      # the turf, in the rig's layout


def pose(rig, sway=0.0, lean=0.0, bend=0.0, breathe=0.0, look=0.0, nod=0.0, shiver=(0, 0, 0), arm=(0, 0), fore=(0, 0), spread=(0, 0),
         curl=(0, 0), jaw=0.0, brow=0.0, blink=1.0, ribbon=(0.0, 1.0)):
    """lean: the whole body back (+) or forward (-) from the waist; bend: the same again from the chest up; arm: each
    arm swung forward / up from the shoulder (degrees; 0 hanging); fore: the forearm folded in (+) or straightened (-);
    spread: arms out sideways; curl: fingers clenched (+) or opened (-); shiver: the crown's three tiers; ribbon:
    (phase, strength) of the antler ribbon's flutter."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["hips"].rotation_quaternion = q(pb["hips"], (0, 1, 0), sway) @ q(pb["hips"], (1, 0, 0), lean)
    pb["chest"].rotation_quaternion = q(pb["chest"], (0, 1, 0), sway * 0.5) @ q(pb["chest"], (1, 0, 0), bend)
    pb["chest"].scale = (1 + breathe, 1 + breathe * 0.4, 1 + breathe)
    pb["head"].rotation_quaternion = q(pb["head"], (0, 0, 1), look) @ q(pb["head"], (1, 0, 0), nod)
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -jaw)
    pb["brow"].location = arm_space_loc(pb["brow"], (0, 0, -0.035 * TS * brow))
    pb["eyes"].scale = (1.0, 1.0, blink)
    for i in range(3):
        b = pb["crown.%d" % (i + 1)]
        b.rotation_quaternion = q(b, (1, 0, 0), shiver[i]) @ q(b, (0, 1, 0), shiver[(i + 1) % 3] * 0.7)
    for j, (s, sx) in enumerate((("R", 1), ("L", -1))):
        a1, a2 = pb["arm.%s.1" % s], pb["arm.%s.2" % s]
        a1.rotation_quaternion = q(a1, (1, 0, 0), arm[j]) @ q(a1, (0, 1, 0), -sx * spread[j])
        a2.rotation_quaternion = q(a2, (1, 0, 0), fore[j])
        pb["fingers." + s].rotation_quaternion = q(pb["fingers." + s], (1, 0, 0), -curl[j])
    wave_flag(rig, "ribbon", ribbon[0], amp=ribbon[1], segs=3, axis=(1, 0, 0))


def idle_pose(f):
    ph = 2 * math.pi * f / IDLE_LEN
    return dict(sway=2.2 * math.sin(ph), lean=1.0 * math.sin(2 * ph), bend=1.5 * math.sin(2 * ph - 0.5), breathe=0.022 * math.sin(2 * ph - 0.6),
                look=7.0 * math.sin(ph + 0.9), nod=2.0 * math.sin(2 * ph + 0.4),
                shiver=[2.6 * math.sin(3 * ph + i * 0.9) + 1.3 * math.sin(7 * ph + i * 1.7) for i in range(3)],
                arm=(3 * math.sin(ph + 0.5), 3 * math.sin(ph + 2.0)), fore=(2.5 * math.sin(2 * ph), 2.5 * math.sin(2 * ph + 1.5)),
                spread=(1.5 * math.sin(ph), -1.5 * math.sin(ph)), curl=(11 * math.sin(2 * ph), 11 * math.sin(2 * ph + 2.2)),
                jaw=3.0 * max(0.0, math.sin(ph - 1.0)) ** 2, brow=0.3 * math.sin(ph + 2.0), blink=0.12 if 60 <= f <= 63 else 1.0,
                ribbon=(2.0 * f / IDLE_LEN, 1.0))


def _mix(a, b, w):
    out = {}
    for key, va in a.items():
        vb = b.get(key, va)
        out[key] = [x + (y - x) * w for x, y in zip(va, vb)] if isinstance(va, (list, tuple)) else va + (vb - va) * w
    return out


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, **idle_pose(f))
        key_pose(rig, f)
    # fire: rears (frames 0-5), both fists come down in front (they land on frame 9 = 0.3 s, with the strike's roots),
    # a shudder runs up the crown, and it heaves itself upright again
    rest = idle_pose(0)
    up = dict(rest, lean=13, bend=11, nod=10, arm=(158, 158), fore=(18, 18), spread=(16, 16), curl=(16, 16), jaw=4, brow=1.0, look=0, sway=0, blink=1.0)
    down = dict(rest, lean=-23, bend=-17, nod=20, arm=(104, 104), fore=(-48, -48), spread=(-5, -5), curl=(18, 18), jaw=24, brow=1.0, look=0, sway=0, blink=1.0)
    best = None                 # (find the swing of the arms that puts the fists on the ground at this lean)
    for a in range(40, 150, 2):
        pose(rig, **dict(down, arm=(a, a)))
        bpy.context.view_layer.update()
        z = rig.pose.bones["fingers.R"].tail.z / TS
        if best is None or abs(z - (GROUND + 0.03)) < best[0]:
            best = (abs(z - (GROUND + 0.03)), a, rig.pose.bones["fingers.R"].tail.copy())
    down["arm"] = (best[1], best[1])
    print("TREANT slam arm", best[1], "fist at", tuple(round(v, 2) for v in best[2]))
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        w_up = smooth(f / 5.0)
        w_dn = min(max((f - 5) / 4.0, 0.0), 1.0) ** 2
        back = smooth((f - 13) / 10.0)
        p = _mix(_mix(rest, up, w_up), down, w_dn)
        p = _mix(p, rest, back)
        if f >= 9:
            d = f - 9
            p["shiver"] = [p["shiver"][i] + 13.0 * math.exp(-max(d - i * 1.2, 0) / 3.5) * math.sin(max(d - i * 1.2, 0) * 1.9) * (1 - back) for i in range(3)]
            p["lean"] += 3.0 * math.exp(-d / 2.5) * math.sin(d * 2.2) * (1 - back)
        p["blink"] = 1.0
        p["ribbon"] = (f / 12.0, 1.0 + 2.2 * math.sin(math.pi * f / FIRE_LEN))
        pose(rig, **p)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.5), "dist": 11.5, "yaw": 158, "pitch": 18, "anim_target": (C0.x, C0.y + 0.3, 1.8), "anim_dist": 7.4,
           "frames": [("idle", 0), ("idle", 40), ("fire", 5), ("fire", 9), ("fire", 12)],
           "extra": [{"yaw": 170, "pitch": 6, "dist": 3.8, "target": (0, 0.3, WAIST + 1.45)},
                     {"yaw": 0, "pitch": 40, "dist": 6.5, "target": (0, 0, 1.6)},
                     {"yaw": 200, "pitch": 30, "dist": 6.0, "target": (-0.6, 0.4, 0.8)},
                     {"yaw": 330, "pitch": 34, "dist": 6.0, "target": (0.6, -0.5, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
    tri_report(collection("Treant"))


# ================================================================================================ the strike
# What the game plays under the enemy the treant hits (Strike, GameData.STRIKES "erupt"): the ground heaves open, roots
# burst out round the enemy, splayed, and snap shut on it like a claw (the blow: 0.3 s in), hold, and sink back, while
# clods of earth fly. The model stands on the enemy's spot on the road; +Y points away from the tower.
STRIKE_LEN = 33
STRIKE_ROOTS = 6
STRIKE_CLODS = 7


def build_strike():
    col = collection("Treant_strike")
    root = empty("Treant_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(8)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "dirt": ((0, 0, 0), (0, 0, 0.3), "root")}
    shapes = []
    for i in range(STRIKE_ROOTS):
        a = 2 * math.pi * (i + rnd.uniform(-0.15, 0.15)) / STRIKE_ROOTS
        d = Vector((math.cos(a), math.sin(a), 0))
        h = rnd.uniform(1.3, 1.65)
        pts = [d * 0.56 + Vector((0, 0, -0.12)), d * 0.68 + Vector((0, 0, h * 0.36)), d * 0.52 + Vector((0, 0, h * 0.72)),
               d * 0.14 + Vector((0, 0, h))]
        shapes.append((d, pts))
        prev = "root"
        for j in range(3):
            bones["r%d.%d" % (i, j + 1)] = (tuple(pts[j]), tuple(pts[j + 1]), prev)
            prev = "r%d.%d" % (i, j + 1)
    fly = []
    for i in range(STRIKE_CLODS):
        a = 2 * math.pi * (i + 0.5 + rnd.uniform(-0.2, 0.2)) / STRIKE_CLODS
        d = Vector((math.cos(a), math.sin(a), 0))
        fly.append((d, rnd.uniform(0.85, 1.3), rnd.uniform(1.5, 2.3), rnd.uniform(0.1, 0.16)))
        bones["clod%d" % i] = (tuple(d * 0.5 + Vector((0, 0, 0.1))), tuple(d * 0.5 + Vector((0, 0, 0.3))), "root")
    rig = make_rig(col, root, bones)
    k = Kit()
    for i, (d, pts) in enumerate(shapes):
        mid = [pts[0], pts[0].lerp(pts[1], 0.5), pts[1], pts[1].lerp(pts[2], 0.5), pts[2], pts[2].lerp(pts[3], 0.55), pts[3]]
        bm_tube(k[BARK], mid, [0.17, 0.16, 0.14, 0.115, 0.09, 0.055, 0.0], n=6)
        for t, s in ((0.3, 0.075), (0.62, 0.06)):                    # thorns
            p = pts[0].lerp(pts[3], t) + d * 0.08
            bm_crystal(k[BARK_PALE], p, p + d * 0.22 + Vector((0, 0, 0.1)), s, n=4, shoulder=0.25)
        bm_sprig(k[LEAF_A], rnd, pts[2] + d * 0.08, d + Vector((0, 0, 0.5)), n=3, size=0.2)
        k.emit("Root%d" % i, col, rig=rig, bones=["r%d.%d" % (i, j) for j in (1, 2, 3)])
    # the ground heaved open: slabs of turf and earth tipped up round the hole
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.15, 0.15)
        r = rnd.uniform(0.74, 0.9)
        bm_stone(k["wood_red:0.55:0.98" if i % 2 else "taupe_dark:0.3:0.9"], rnd, (math.cos(a) * r, math.sin(a) * r, 0.0),
                 (0.36, 0.25, 0.24), yaw=math.degrees(a) + 90 + rnd.uniform(-20, 20), n=9, jit=0.2)
    k.emit("Heave", col, rig=rig, bone="dirt", vary=0.06)
    for i, (d, _, _, r) in enumerate(fly):
        bm_stone(k["wood_red:0.5:0.95"], rnd, tuple(d * 0.5 + Vector((0, 0, 0.1))), (r * 2, r * 1.6, r * 1.5), yaw=rnd.uniform(0, 180), n=8, jit=0.2)
        k.emit("Clod%d" % i, col, rig=rig, bone="clod%d" % i)
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    for f in range(STRIKE_LEN + 1):
        rest_pose(rig)
        grow = smooth(f / 6.0) * (1.0 - smooth((f - 25) / 8.0))
        # splayed open while they rise, snapping shut at frame 9 with a little overshoot, loosening as they sink
        shut = smooth((f - 6) / 3.0)
        over = 0.18 * math.sin(math.pi * min(max((f - 9) / 5.0, 0.0), 1.0))
        opened = (1.0 - shut) - over + 0.5 * smooth((f - 25) / 8.0)
        for i, (d, pts) in enumerate(shapes):
            axis = Vector((-d.y, d.x, 0))          # a turn about this tips the root outward (+) or inward (-)
            wob = 2.0 * math.sin(f * 1.3 + i) * (1.0 if 12 < f < 25 else 0.0)
            b1 = pb["r%d.1" % i]
            b1.scale = (max(grow, 0.02),) * 3
            b1.location = arm_space_loc(b1, (0, 0, -0.5 * (1.0 - grow)))
            b1.rotation_quaternion = arm_space_quat(b1, tuple(axis), 30 * opened + wob)
            pb["r%d.2" % i].rotation_quaternion = arm_space_quat(pb["r%d.2" % i], tuple(axis), 32 * opened)
            pb["r%d.3" % i].rotation_quaternion = arm_space_quat(pb["r%d.3" % i], tuple(axis), 26 * opened)
        up = math.sin(math.pi * min(f / 10.0, 1.0))
        pb["dirt"].scale = (0.7 + 0.5 * smooth(f / 5.0),) * 2 + (max(0.05, (1.0 - smooth((f - 23) / 9.0)) * smooth(f / 2.0)),)
        pb["dirt"].location = arm_space_loc(pb["dirt"], (0, 0, 0.16 * up - 0.02))
        for i, (d, reach, vz, r) in enumerate(fly):                  # clods thrown out and up, tumbling, gone as they land
            t = min(max((f - 1 - (i % 3)) / 15.0, 0.0), 1.0)
            b = pb["clod%d" % i]
            b.location = arm_space_loc(b, tuple(d * (reach * t) + Vector((0, 0, vz * t * (1.0 - t) * 1.6))))
            b.rotation_quaternion = arm_space_quat(b, (d.y, -d.x, 0), -420 * t)
            b.scale = (max(0.02, smooth(t / 0.12) * (1.0 - smooth((t - 0.8) / 0.2))),) * 3
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [3, 6, 9, 16, 29], "dist": 6.0, "target": (0, 0, 0.7)}
