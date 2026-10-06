"""Builds the Ancient Mammoth (footprint "battery5": [0,0] middle, [-1,0] front-left, [0,-1] front, [1,-1] front-right,
[0,1] back), a Verdant creature tower: it stomps, hurting and stunning every ground enemy around it (an aura; the
game shows the blow under each enemy with the strike model built at the end of this file).

    python tools/blender/build.py mammoth --out <preview dir>

One place: the mammoth's stamping ground. A huge war mammoth stands over the middle cell, head and tusks out over the
front one: a lofted barrel body with a high shoulder hump and a sloping back, a domed head, a trunk on a chain of
bones, two great curved tusks with carved bands, a shaggy coat (layered skirts of locks along the belly, the shoulders
and the legs), and on its back the druids' howdah: a great blanket in the team's color with gold trim, a wicker box
under a two-tier canopy in the team's color, a rune stone glowing inside, charms swinging from the eaves.
Its ground ties the five cells together: trampled earth with its round footprints, the tree it pushed over
(front-left: a splintered stump, the trunk and crown lying where they fell), its feed (front-right: a heap of hay and
leafy boughs, gourds, a log trough) and its rubbing rocks (back: mossy boulders, one carved with a rune).
It never turns (an aura), so the Head is a marker under its middle and the Rig spans the whole beast.
Clips: idle (the trunk sways and curls, ears flap, it shifts its weight and paws the ground, breathes, the tail
swishes, the charms swing), fire (rears, slams both forefeet down on frame 7, trunk flung up trumpeting, a ripple
running back along its body to the tail).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "megabeast_common.py"), encoding="utf-8").read())

TID = "mammoth"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (0, 1)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)          # (0, -0.42)
FLc = hex_to_world(-1, 0, MID)        # (-1.8, 0.62)
FCc = hex_to_world(0, -1, MID)        # (0, 1.66)
FRc = hex_to_world(1, -1, MID)        # (1.8, 0.62)
BKc = hex_to_world(0, 1, MID)         # (0, -2.49)
TOP = 0.34
MS = 1.15                             # mammoth scale (laid out at 1.0)
HOME = Vector((C0.x, C0.y - 0.24, 0))
RUNE = (0.3, 1.0, 0.45)
GLOW = "glow:%s,%s,%s,0.8" % RUNE
FUR, SHAG, MANE, IVORY = "wood_red:0.08:0.85", "wood_red:0.55:0.98", "wood_red:0.68:0.99", "cream:0.03:0.5"
EARTH, PRINT = "wood_red:0.62:0.97", "wood_red:0.88:0.99"

# ---- the mammoth, in the head's space (+Y forward), laid out at 1.0: sections (y, zc, rx, up, dn, pinch)
BODY = [(-1.30, 1.14, 0.26, 0.24, 0.26, 0.10), (-1.14, 1.16, 0.50, 0.42, 0.40, 0.15), (-0.82, 1.19, 0.61, 0.50, 0.46, 0.20),
        (-0.38, 1.24, 0.65, 0.56, 0.50, 0.22), (0.06, 1.30, 0.64, 0.64, 0.50, 0.25), (0.42, 1.36, 0.61, 0.70, 0.52, 0.28),
        (0.74, 1.40, 0.54, 0.58, 0.50, 0.25), (1.00, 1.44, 0.42, 0.42, 0.44, 0.20)]
SKULL = [(0.76, 1.52, 0.40, 0.42, 0.42, 0.15), (0.98, 1.62, 0.52, 0.62, 0.52, 0.25), (1.22, 1.66, 0.54, 0.68, 0.52, 0.30),
         (1.44, 1.56, 0.48, 0.56, 0.46, 0.30), (1.60, 1.38, 0.38, 0.42, 0.36, 0.25), (1.70, 1.20, 0.28, 0.30, 0.26, 0.20)]
TRUNK = [(0, 1.58, 1.28), (0, 1.78, 1.00), (0, 1.86, 0.72), (0, 1.87, 0.46), (0, 1.93, 0.27), (0, 2.07, 0.16), (0, 2.21, 0.21)]
TRUNK_R = [0.26, 0.22, 0.18, 0.15, 0.125, 0.105, 0.09]
TUSK = [(0.25, 1.50, 1.26), (0.34, 1.76, 1.00), (0.50, 2.06, 0.84), (0.66, 2.38, 0.84), (0.74, 2.66, 1.02), (0.66, 2.84, 1.30),
        (0.48, 2.88, 1.60), (0.34, 2.84, 1.80)]
TUSK_R = [0.15, 0.15, 0.14, 0.125, 0.105, 0.08, 0.05, 0.0]
LEGS = {  # hip / shoulder, knee, the ground under the foot
    "FL": ((-0.40, 0.50, 1.05), (-0.42, 0.53, 0.55), (-0.42, 0.52, 0.0)),
    "FR": ((0.40, 0.50, 1.05), (0.42, 0.53, 0.55), (0.42, 0.52, 0.0)),
    "BL": ((-0.42, -0.86, 1.0), (-0.44, -0.80, 0.52), (-0.44, -0.86, 0.0)),
    "BR": ((0.42, -0.86, 1.0), (0.44, -0.80, 0.52), (0.44, -0.86, 0.0)),
}
HOW = Vector((0, -0.42, 1.97))        # the howdah's deck: its middle
HW, HL = 0.4, 0.38                    # ... half its width and length
ZC = HOW.z + 0.36                     # ... and its canopy's eaves
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, -1.0, 1.25), (0, -0.2, 1.32), "root"),
    "rump": ((0, -1.0, 1.22), (0, -0.2, 1.28), "hips"),             # (the body's own bones: they swell and ripple)
    "chest": ((0, -0.2, 1.32), (0, 0.7, 1.42), "hips"),
    "ribs": ((0, -0.2, 1.3), (0, 0.72, 1.4), "chest"),
    "head": ((0, 0.84, 1.55), (0, 1.5, 1.55), "chest"),
    "jaw": ((0, 1.2, 1.1), (0, 1.62, 1.0), "head"),
    "trunk.1": ((0, 1.6, 1.26), (0, 1.8, 0.94), "head"),
    "trunk.2": ((0, 1.8, 0.94), (0, 1.87, 0.6), "trunk.1"),
    "trunk.3": ((0, 1.87, 0.6), (0, 1.92, 0.3), "trunk.2"),
    "trunk.4": ((0, 1.92, 0.3), (0, 2.21, 0.21), "trunk.3"),
    "ear.L": ((-0.45, 1.16, 1.76), (-0.72, 0.98, 1.45), "head"),
    "ear.R": ((0.45, 1.16, 1.76), (0.72, 0.98, 1.45), "head"),
    "tail.1": ((0, -1.27, 1.32), (0, -1.42, 0.98), "hips"),
    "tail.2": ((0, -1.42, 0.98), (0, -1.47, 0.66), "tail.1"),
    "saddle": ((0, -0.42, 1.8), (0, -0.42, 2.3), "hips"),
    "charm.L": ((-HW - 0.12, HOW.y + HL + 0.12, ZC - 0.02), (-HW - 0.12, HOW.y + HL + 0.12, ZC - 0.26), "saddle"),
    "charm.R": ((HW + 0.12, HOW.y + HL + 0.12, ZC - 0.02), (HW + 0.12, HOW.y + HL + 0.12, ZC - 0.26), "saddle"),
}
for _n, (_a, _b, _c) in LEGS.items():
    BONES["leg.%s.1" % _n] = (_a, _b, "chest" if _n[0] == "F" else "hips")
    BONES["leg.%s.2" % _n] = (_b, (_c[0], _c[1], 0.03), "leg.%s.1" % _n)


def build_base():
    col = collection("Mammoth")
    root = empty("Mammoth", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(61)
    k = Kit()
    keep = lambda x, y: in_footprint(CELLS, x, y, 0.2)
    # ---- the stamping ground: trampled earth over the middle, lobes out to the tree, the feed and the rocks
    LOBES = ((HOME.x, HOME.y + 0.3, 1.5, 1.08, 0.03), (0.0, 1.6, 0.95, 0.85, 0.045), (-1.5, 0.5, 0.9, 0.8, 0.04),
             (1.5, 0.5, 0.9, 0.8, 0.04), (0.05, -2.2, 0.9, 1.05, 0.045))
    for cx, cy, r, sq, dz in LOBES:
        bm_patch(k[EARTH], rnd, (cx, cy), r, T - 0.01, T + dz, n=12, squash=sq, keep=keep)
    k.emit("Earth", col, root)
    on_earth = lambda x, y: any((x - cx) ** 2 + ((y - cy) / sq) ** 2 < (r * 0.9) ** 2 for cx, cy, r, sq, dz in LOBES)
    for x, y, rz in ((0.55, 1.5, 10), (-0.5, 1.95, -15), (-0.95, 0.95, 40), (1.05, 1.15, -30), (0.5, -1.95, 5), (-0.3, -2.35, -8),
                     (0.95, 0.0, -60), (-0.85, -0.75, 70)):             # its round footprints, pressed into the mud
        bm_cyl(k[PRINT], 0.2, 0.22, 0.014, (x, y, T + 0.052), seg=9)
        for i in range(3):
            a = math.radians(rz + 90 + (i - 1) * 38)
            bm_cyl(k[PRINT], 0.055, 0.06, 0.014, (x + math.cos(a) * 0.25, y + math.sin(a) * 0.25, T + 0.052), seg=6)
    k.emit("Prints", col, root)
    for p in scatter_points(rnd, CELLS, 40, inset=0.3, avoid=[(HOME.x, HOME.y + 0.2, 1.0)], min_gap=0.3):
        if not on_earth(p.x, p.y):
            continue
        bm_boulder(k["wood_red:0.45:0.9"], rnd, (p.x, p.y, T + 0.02), rnd.uniform(0.05, 0.1), n=7, sink=0.25)      # clods
    k.emit("Clods", col, root, vary=0.08)

    # ---- front-left: the tree it pushed over: a splintered stump, the trunk and its crown where they fell
    S0 = Vector((-1.2, 0.0, 0))
    bark = "wood_dark:0.2:0.85"
    bm_tube(k[bark], [(S0.x, S0.y, T - 0.03), (S0.x, S0.y, T + 0.2), (S0.x - 0.03, S0.y + 0.02, T + 0.4)], [0.36, 0.29, 0.26], n=8)
    for i in range(5):
        a = math.radians(72 * i + 25)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_tube(k[bark], [S0 + d * 0.2 + Vector((0, 0, T + 0.17)), S0 + d * 0.46 + Vector((0, 0, T + 0.07)),
                          S0 + d * 0.72 + Vector((0, 0, T - 0.02))], [0.11, 0.085, 0.04], n=5)
    fall = Vector((-0.78, 0.63, 0)).normalized()
    A, B = Vector((-1.42, 0.2, T + 0.42)), Vector((-2.12, 0.8, T + 0.19))
    bm_tube(k[bark], [A, A.lerp(B, 0.5) + Vector((0, 0, -0.03)), B], [0.22, 0.19, 0.15], n=8)
    for t, side, up in ((0.35, 1, 0.34), (0.6, -1, 0.2), (0.8, 1, 0.26)):       # broken boughs
        p = A.lerp(B, t)
        q = p + Vector((-fall.y, fall.x, 0)) * (side * 0.32) + fall * 0.12 + Vector((0, 0, up))
        bm_tube(k[bark], [p, p.lerp(q, 0.6) + Vector((0, 0, 0.05)), q], [0.075, 0.055, 0.03], n=5)
    k.emit("Tree", col, root)
    for i in range(7):                                                         # splinters on the stump, torn the way it fell
        a = math.radians(360 * i / 7 + rnd.uniform(-15, 15))
        p = Vector((S0.x - 0.03 + math.cos(a) * 0.15, S0.y + 0.02 + math.sin(a) * 0.15, T + 0.38))
        bm_crystal(k["sand:0.15:0.7"], p, p + fall * rnd.uniform(0.03, 0.16) + Vector((0, 0, rnd.uniform(0.14, 0.34))), 0.07, n=4, shoulder=0.25)
    for i in range(5):                                                         # ... and on the trunk's torn end
        a = math.radians(72 * i)
        side = Vector((-fall.y, fall.x, 0))
        p = A + side * (math.cos(a) * 0.12) + Vector((0, 0, math.sin(a) * 0.12))
        bm_crystal(k["sand:0.15:0.7"], p + fall * 0.04, p - fall * rnd.uniform(0.12, 0.26) + Vector((0, 0, rnd.uniform(-0.03, 0.06))), 0.07, n=4, shoulder=0.25)
    k.emit("Tree_Splinters", col, root)
    for i, (x, y, z, r, sw) in enumerate(((-2.25, 0.95, 0.36, 0.46, "grass:0.1:0.8"), (-2.02, 1.25, 0.26, 0.33, "teal:0.25:0.8"),
                                          (-2.5, 0.72, 0.24, 0.3, "teal:0.25:0.8"), (-2.3, 1.18, 0.56, 0.27, "grass:0.05:0.7"),
                                          (-1.95, 0.72, 0.5, 0.24, "grass:0.1:0.8"))):
        bm_blob(k[sw], rnd, (x, y, T + z), r, squash=(1.0, 1.0, 0.75), jitter=0.13, sub=2 if r > 0.4 else 1)
    k.emit("Tree_Crown", col, root)

    # ---- front-right: its feed: a heap of hay and leafy boughs, gourds, a trough hollowed out of a log
    P = Vector((1.78, 0.72, 0))
    bm_blob(k["gold:0.15:0.75"], rnd, (P.x, P.y, T + 0.2), 0.6, squash=(1.15, 0.95, 0.62), jitter=0.12, sub=2)
    bm_blob(k["gold:0.2:0.8"], rnd, (P.x - 0.52, P.y - 0.25, T + 0.08), 0.32, squash=(1.1, 1.0, 0.6), jitter=0.12)
    bm_blob(k["gold:0.2:0.8"], rnd, (P.x + 0.3, P.y + 0.42, T + 0.08), 0.28, squash=(1.1, 1.0, 0.6), jitter=0.12)
    for i in range(40):                                                        # thatch: straws lying down the heap
        a, el = rnd.uniform(0, 6.283), rnd.uniform(0.15, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        p = Vector((P.x + d.x * 0.66, P.y + d.y * 0.55, T + 0.2 + d.z * 0.36))
        bm_lock(k["gold:0.02:0.6"], p, p + Vector((d.x * 0.26, d.y * 0.26, -0.16)), 0.13, 0.035, d)
    k.emit("Hay", col, root, vary=0.1)
    for i in range(16):                                                        # wisps of hay dragged toward the mammoth
        a, r = rnd.uniform(2.2, 4.6), rnd.uniform(0.55, 1.05)
        p = P + Vector((math.cos(a) * r, math.sin(a) * r * 0.8, 0))
        if keep(p.x, p.y):
            bm_box(k["gold:0.1:0.6"], (rnd.uniform(0.2, 0.34), 0.035, 0.02), (p.x, p.y, T + 0.06), (0, rnd.uniform(-5, 5), rnd.uniform(0, 180)))
    k.emit("Hay_Wisps", col, root, vary=0.1)
    for (dx, dy, dz, ax, ay, ln) in ((0.1, 0.12, 0.5, 0.6, 0.5, 0.7), (-0.2, -0.05, 0.48, -0.7, 0.3, 0.6), (0.3, -0.2, 0.44, 0.5, -0.6, 0.62)):
        p = Vector((P.x + dx, P.y + dy, T + dz))
        q = p + Vector((ax, ay, 0.55)).normalized() * ln
        bm_tube(k["wood_dark:0.3:0.8"], [p - Vector((ax, ay, 0.55)).normalized() * 0.25, q], [0.04, 0.025], n=5)
        bm_blob(k["grass:0.1:0.75"], rnd, q, 0.2, squash=(1.0, 1.0, 0.8), jitter=0.16)
        bm_blob(k["teal:0.3:0.8"], rnd, p.lerp(q, 0.6) + Vector((0.08, -0.06, 0.02)), 0.14, jitter=0.16)
    k.emit("Boughs", col, root)
    for dx, dy, r in ((-0.72, 0.28, 0.17), (-0.5, 0.56, 0.13), (-0.9, -0.02, 0.12)):
        bm_ellipsoid(k["orange:0.15:0.8"], (P.x + dx, P.y + dy, T + r * 0.78), (r, r, r * 0.8), u=8, v=5)
        bm_box(k["grass:0.5:0.9"], (0.035, 0.035, 0.08), (P.x + dx, P.y + dy, T + r * 1.6 + 0.02), (10, 8, 0))
    k.emit("Gourds", col, root)
    L0, L1 = Vector((2.32, -0.02, T + 0.17)), Vector((1.5, -0.2, T + 0.17))    # the trough
    bm_tube(k["wood:0.3:0.85"], [L0, L1], 0.2, n=8)
    ax = (L1 - L0).normalized()
    bm_beam(k["wood_dark:0.5:0.9"], L0 + ax * 0.09 + Vector((0, 0, 0.115)), L1 - ax * 0.09 + Vector((0, 0, 0.115)), 0.25, 0.1)
    bm_beam(k["water"], L0 + ax * 0.12 + Vector((0, 0, 0.158)), L1 - ax * 0.12 + Vector((0, 0, 0.158)), 0.2, 0.03)
    k.emit("Trough", col, root, bevel=0.008)

    # ---- back: its rubbing rocks, mossy, one carved with the druids' rune
    R0 = Vector((-0.42, -2.78, 0))
    bm_boulder(k["stone:0.12:0.9"], rnd, (R0.x, R0.y, T - 0.03), 0.52, squash=(1.0, 0.92, 1.0), n=14)
    bm_boulder(k["stone:0.2:0.95"], rnd, (0.5, -2.92, T - 0.02), 0.36, squash=(1.1, 0.9, 0.85), n=12)
    bm_boulder(k["stone:0.2:0.95"], rnd, (0.02, -3.12, T - 0.02), 0.24, n=10)
    bm_boulder(k["stone:0.2:0.95"], rnd, (-0.9, -2.38, T - 0.02), 0.2, n=9)
    k.emit("Rocks", col, root, vary=0.07)
    bm_blob(k["grass:0.25:0.8"], rnd, (R0.x - 0.02, R0.y - 0.02, T + 0.7), 0.36, squash=(1.0, 0.95, 0.3), jitter=0.1, sub=2)
    bm_blob(k["grass:0.25:0.8"], rnd, (0.5, -2.94, T + 0.42), 0.24, squash=(1.0, 0.9, 0.3), jitter=0.1)
    k.emit("Moss", col, root)
    for dx, dz, w, h, ry in ((0.0, 0.4, 0.05, 0.32, 0), (-0.075, 0.5, 0.045, 0.2, -42), (0.075, 0.5, 0.045, 0.2, 42)):   # the rune, facing the camera
        bm_box(k[GLOW], (w, 0.04, h), (R0.x + dx, R0.y - 0.4 + (dz - 0.4) * 0.3, T + dz), (-18, ry, 0))
    k.emit("Rune", col, root)

    kk = [("forest/Grass_2_A_Color1", (-2.6, 0.2, 0), 0.5), ("forest/Grass_1_B_Color1", (2.62, 1.0, 0), 0.5),
          ("forest/Bush_1_C_Color1", (2.5, 0.1, 0), 0.3), ("forest/Grass_2_B_Color1", (0.95, -2.3, 0), 0.5),
          ("forest/Grass_1_A_Color1", (-0.85, 2.3, 0), 0.5), ("forest/Bush_2_B_Color1", (0.9, 2.25, 0), 0.24),
          ("forest/Grass_1_C_Color1", (-1.75, -0.1, 0), 0.5), ("props/Mushroom", (-0.95, -3.0, 0), 0.5)]
    for i, (rel, loc, sc) in enumerate(kk):
        kk_import(rel, col, root, (loc[0], loc[1], T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (HOME.x, HOME.y, T + 0.03), 0.5, "SINGLE_ARROW")
    return root


def _skirt(bm, rnd, secs, y0, y1, ang, length, step=0.15, w=0.21, th=0.06, sides=(1, -1)):
    """A row of hanging locks along a body's flanks at angle `ang` (degrees from the right side; under 0 = below the
    widest line), each about `length` long."""
    y = y0
    while y <= y1 + 1e-6:
        for side in sides:
            p, n = surf(secs, y, ang if side > 0 else 180.0 - ang)
            L = length * rnd.uniform(0.75, 1.15)
            bm_lock(bm, p + n * 0.02 + Vector((0, 0, 0.05)), p + n * 0.06 + Vector((0, rnd.uniform(-0.04, 0.04), -L)),
                    w * rnd.uniform(0.9, 1.2), th, n)
        y += step * rnd.uniform(0.9, 1.1)


def _mane(bm, rnd, secs, y0, y1, a0, a1, n, w=0.24, th=0.06, lift=0.05):
    """A row of locks lying back along a body from spine position y0 to y1, spread from angle a0 to a1."""
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n + rnd.uniform(-4, 4)
        p, nrm = surf(secs, y0, a, 0.015)
        q, _ = surf(secs, y1 + rnd.uniform(-0.05, 0.05), a, lift)
        bm_lock(bm, p, q, w * rnd.uniform(0.9, 1.15), th, nrm)


def build_head():
    col = collection("Mammoth")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=MS)
    rnd = random.Random(4)
    k = Kit()
    S = MS
    soft = ["rump", "ribs"]
    # ---- body: one loft from rump to neck, soft-skinned along the spine
    bm_loft(k[FUR], [sec_ring(s, 10) for s in BODY])
    body = k.emit("Head_Body", col, rig=rig, bones=soft, scale=S)[0]
    paint_faces(body, "wood_red", lambda c, n: n.z < -0.6, lo=0.6, hi=0.95)
    # ---- the shaggy coat: a skirt of locks along the belly, a second row on the shoulders and the rump, a mane
    _skirt(k[SHAG], rnd, BODY, -1.08, 0.9, -38, 0.5)
    _skirt(k[MANE], rnd, BODY, -1.12, 0.9, -15, 0.42, w=0.23)
    _skirt(k[SHAG], rnd, BODY, 0.32, 0.9, 8, 0.36, w=0.23)
    _skirt(k[SHAG], rnd, BODY, -1.2, -1.04, 8, 0.34, step=0.14)
    for a in (-55, -90, -125):                                                 # under the tail
        p, n = surf(BODY, -1.2, a)
        bm_lock(k[SHAG], p, p + Vector((0, -0.1, -0.34)), 0.24, 0.06, n)
    bm_drape(k[MANE], BODY, [0.34, 0.52, 0.74, 0.97], 12, 168, th=0.04, n=10)       # a cape of longer hair over the hump
    _skirt(k[MANE], rnd, BODY, 0.36, 0.94, 14, 0.3, step=0.13, w=0.2)
    _mane(k[MANE], rnd, BODY, 0.36, 0.16, 20, 160, 9, w=0.2, th=0.05, lift=0.055)
    k.emit("Head_Coat", col, rig=rig, bones=soft, scale=S, vary=0.07)
    # ---- the great blanket in the team's color: gold edges and hem, a rune boss on each flank, tassels
    ys = [-1.0, -0.72, -0.4, -0.08, 0.24]
    bm_drape(k["team!:0.1:0.7"], BODY, ys, -8, 188, th=0.035, n=10)
    for y in (-1.03, 0.22):
        bm_drape(k["gold:0.1:0.55"], BODY, [y, y + 0.06], -9, 189, th=0.05, n=10)
    for a0, a1 in ((-9, 1), (179, 189)):
        bm_drape(k["gold:0.1:0.55"], BODY, ys, a0, a1, th=0.05, n=2)
    for a0, a1 in ((11, 17), (163, 169)):                                      # a second, thinner stripe
        bm_drape(k["cream:0.1:0.5"], BODY, ys, a0, a1, th=0.045, n=1)
    for sx in (1, -1):
        p, n = surf(BODY, -0.38, 36 if sx > 0 else 144, 0.03)
        bm_tube(k["gold:0.1:0.5"], [p, p + n * 0.035], 0.14, n=6)
        bm_crystal(k[GLOW], p + n * 0.03, p + n * 0.1, 0.07, n=4, shoulder=0.4)
        for y in (-0.92, -0.66, -0.4, -0.14, 0.12):
            p, n = surf(BODY, y, -9 if sx > 0 else 189, 0.03)
            bm_crystal(k["gold:0.2:0.7"], p + Vector((0, 0, 0.02)), p + Vector((0, 0, -0.15)), 0.04, n=4, shoulder=0.3)
    k.emit("Head_Blanket", col, rig=rig, bones=soft, scale=S)

    # ---- the howdah (on its own bone, so it can rock): bolsters, a plank deck, wicker sides, a two-tier canopy
    dz = HOW.z
    for y, z in ((HOW.y + 0.36, 1.92), (HOW.y - 0.36, 1.8)):
        bm_tube(k["tan:0.2:0.8"], [(-0.46, y, z - 0.06), (-0.25, y, z + 0.02), (0.25, y, z + 0.02), (0.46, y, z - 0.06)], 0.075, n=6)
    for y, h in ((HOW.y + HL - 0.04, 0.08), (HOW.y - HL + 0.04, 0.2)):
        bm_box(k["wood_dark:0.2:0.7"], (2 * HW + 0.1, 0.1, h), (0, y, dz - 0.03 - h / 2))
    bm_planks(k["wood:0.2:0.75"], rnd, (-HW, HOW.y - HL, dz), (0, 2 * HL, 0), (2 * HW, 0, 0), 5, th=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k["wood_dark:0.15:0.7"], (0.075, 0.075, 0.38), (sx * HW, HOW.y + sy * HL, dz + 0.19))
        bm_box(k["sand:0.3:0.8"], (0.04, 2 * HL - 0.08, 0.17), (sx * HW, HOW.y, dz + 0.1))
        bm_box(k["wood_dark:0.15:0.7"], (0.055, 2 * HL, 0.04), (sx * HW, HOW.y, dz + 0.2))
        for i in range(4):                                                     # the weave
            bm_box(k["wood:0.3:0.8"], (0.05, 0.03, 0.17), (sx * HW, HOW.y - HL + 2 * HL / 5 * (i + 1), dz + 0.1))
    bm_box(k["sand:0.3:0.8"], (2 * HW - 0.08, 0.04, 0.17), (0, HOW.y - HL, dz + 0.1))
    bm_box(k["wood_dark:0.15:0.7"], (2 * HW, 0.055, 0.04), (0, HOW.y - HL, dz + 0.2))
    for i in range(4):
        bm_box(k["wood:0.3:0.8"], (0.03, 0.05, 0.17), (-HW + 2 * HW / 5 * (i + 1), HOW.y - HL, dz + 0.1))
    bm_box(k["stone:0.2:0.8"], (0.3, 0.3, 0.07), (0, HOW.y, dz + 0.035))         # the rune stone on its plinth
    k.emit("Head_Howdah", col, rig=rig, bone="saddle", scale=S, bevel=0.008, vary=0.05)
    bm_crystal(k[GLOW], (0, HOW.y, dz + 0.05), (0, HOW.y, dz + 0.34), 0.13, n=5, shoulder=0.62)
    zc = ZC
    bm_frustum(k["team!:0.1:0.65"], (0, HOW.y), HW + 0.12, HL + 0.12, zc, zc + 0.13, top=0.56)
    bm_frustum(k["team!:0.05:0.5"], (0, HOW.y), (HW + 0.12) * 0.62, (HL + 0.12) * 0.62, zc + 0.11, zc + 0.37)
    for sx, sy, lx, ly in ((0, 1, 2 * HW + 0.28, 0.05), (0, -1, 2 * HW + 0.28, 0.05), (1, 0, 0.05, 2 * HL + 0.28), (-1, 0, 0.05, 2 * HL + 0.28)):
        bm_box(k["gold:0.1:0.5"], (lx, ly, 0.05), (sx * (HW + 0.12), HOW.y + sy * (HL + 0.12), zc))
    bm_crystal(k["gold:0.05:0.5"], (0, HOW.y, zc + 0.33), (0, HOW.y, zc + 0.5), 0.05, n=4, shoulder=0.35)
    for sx in (-1, 1):                                                         # antlers on the front posts
        p = Vector((sx * (HW + 0.02), HOW.y + HL + 0.03, dz + 0.3))
        bm_tube(k["cream:0.1:0.6"], [p, p + Vector((sx * 0.16, 0.12, 0.08)), p + Vector((sx * 0.3, 0.16, 0.26)), p + Vector((sx * 0.3, 0.12, 0.46))],
                [0.04, 0.036, 0.028, 0.0], n=5)
        for t0, d in ((1, Vector((sx * 0.08, 0.14, 0.14))), (2, Vector((sx * 0.14, 0.02, 0.12)))):
            q = p + (Vector((sx * 0.16, 0.12, 0.08)), Vector((sx * 0.3, 0.16, 0.26)))[t0 - 1]
            bm_tube(k["cream:0.1:0.6"], [q, q + d * 0.5, q + d], [0.028, 0.02, 0.0], n=4)
        q = Vector((sx * (HW + 0.12), HOW.y - HL - 0.12, zc - 0.02))            # charms at the back eaves (the front ones swing)
        bm_box(k["sand:0.3:0.7"], (0.014, 0.014, 0.16), (q.x, q.y, q.z - 0.08))
        bm_crystal(k[GLOW], (q.x, q.y, q.z - 0.14), (q.x, q.y, q.z - 0.3), 0.045, n=4, shoulder=0.4, foot=0.4)
    k.emit("Head_Canopy", col, rig=rig, bone="saddle", scale=S)
    for s, sx in (("L", -1), ("R", 1)):
        q = Vector(BONES["charm." + s][0])
        bm_box(k["sand:0.3:0.7"], (0.014, 0.014, 0.2), (q.x, q.y, q.z - 0.1))
        bm_box(k["gold:0.1:0.5"], (0.05, 0.05, 0.03), (q.x, q.y, q.z - 0.2))
        bm_crystal(k[GLOW], (q.x, q.y, q.z - 0.2), (q.x, q.y, q.z - 0.42), 0.055, n=4, shoulder=0.4, foot=0.4)
        k.emit("Head_Charm" + s, col, rig=rig, bone="charm." + s, scale=S)

    # ---- the head: a domed skull running down into the trunk's root, tusk sockets, small eyes under heavy brows
    bm_loft(k[FUR], [sec_ring(s, 10) for s in SKULL])
    for sx in (-1, 1):
        bm_tube(k[FUR], [(sx * 0.2, 1.34, 1.42), (sx * 0.27, 1.58, 1.18), (sx * 0.32, 1.72, 1.02)], [0.15, 0.17, 0.15], n=7)
    skull = k.emit("Head_Skull", col, rig=rig, bone="head", scale=S)[0]
    paint_faces(skull, "wood_red", lambda c, n: c.y > 1.5 * S and c.z < 1.42 * S, lo=0.05, hi=0.5)
    for sx in (-1, 1):
        a = 14 if sx > 0 else 166
        p, n = surf(SKULL, 1.5, a, 0.0)
        bm_ellipsoid(k["black:0.2:0.5"], p + n * 0.005, (0.045, 0.05, 0.05), u=6, v=4)
        bm_ellipsoid(k["white:0.0:0.2"], p + n * 0.035 + Vector((0, 0.012, 0.014)), (0.016, 0.016, 0.016), u=4, v=3)   # a glint
        b0, n0 = surf(SKULL, 1.4, a + (21 if sx > 0 else -21), 0.02)
        b1, n1 = surf(SKULL, 1.59, a + (12 if sx > 0 else -12), 0.03)
        bm_beam(k[MANE], b0, b1, 0.07, 0.07, w1=0.05, h1=0.05, up=n0)           # brow
        for i, (yy, aa, L) in enumerate(((1.02, -8, 0.3), (1.2, -14, 0.34), (1.36, -22, 0.26))):     # cheek locks
            p, n = surf(SKULL, yy, aa if sx > 0 else 180 - aa)
            bm_lock(k[SHAG], p + n * 0.02, p + n * 0.05 + Vector((0, 0, -L)), 0.2, 0.06, n)
    bm_drape(k[MANE], SKULL, [0.84, 1.02, 1.22, 1.4], 30, 150, th=0.04, n=8)          # a mop of hair on the dome,
    _mane(k[MANE], rnd, SKULL, 1.38, 1.56, 42, 138, 5, w=0.19, th=0.05, lift=0.035)    # ... its fringe over the brow,
    for sx in (-1, 1):                                                         # ... and locks down past the ears
        for yy, L in ((0.94, 0.2), (1.1, 0.26), (1.26, 0.24), (1.38, 0.18)):
            p, n = surf(SKULL, yy, 31 if sx > 0 else 149)
            bm_lock(k[MANE], p + n * 0.02 + Vector((0, 0, 0.04)), p + n * 0.07 + Vector((0, 0, -L)), 0.19, 0.05, n)
    for x, y, dy, h in ((0, 1.2, -0.12, 0.17), (-0.15, 1.12, -0.16, 0.12), (0.15, 1.12, -0.16, 0.12), (0, 1.0, -0.2, 0.12)):
        p, n = surf(SKULL, y, 90 - x * 110, 0.0)                                # the top-knot
        bm_crystal(k[MANE], p, p + Vector((x * 0.4, dy, h)), 0.11, n=4, shoulder=0.3)
    k.emit("Head_Face", col, rig=rig, bone="head", scale=S, vary=0.06)
    for sx in (-1, 1):                                                         # tusks, banded in gold and the team's color
        pts = [Vector((sx * x, y, z)) for x, y, z in TUSK]
        bm_tube(k[IVORY], pts, TUSK_R, n=8)
        for t, sw, w in ((0.17, "gold:0.1:0.55", 0.05), (0.27, "team!:0.1:0.6", 0.09), (0.37, "gold:0.1:0.55", 0.05), (0.62, "gold:0.1:0.55", 0.04)):
            r = lerp_list(TUSK_R, t) + 0.02
            bm_tube(k[sw], [poly_at(pts, t - w / 2.2), poly_at(pts, t + w / 2.2)], r, n=8)
    k.emit("Head_Tusks", col, rig=rig, bone="head", scale=S)
    bm_loft(k["wood_red:0.4:0.9"], [sec_ring(s, 6) for s in ((1.2, 1.08, 0.2, 0.1, 0.12, 0.0), (1.46, 1.02, 0.19, 0.09, 0.1, 0.0),
                                                             (1.63, 0.98, 0.13, 0.07, 0.08, 0.0))])
    bm_box(k["salmon:0.4:0.8"], (0.26, 0.34, 0.02), (0, 1.42, 1.115), (-12, 0, 0))
    k.emit("Head_Jaw", col, rig=rig, bone="jaw", scale=S)
    # ---- trunk: one tube bending over four bones, darker at the tip
    bm_tube(k["wood_red:0.1:0.8"], TRUNK, TRUNK_R, n=8)
    bm_tube(k["wood_red:0.7:0.98"], [Vector(TRUNK[-1]) + Vector((0, 0.0, 0.0)), Vector(TRUNK[-1]) + Vector((0, 0.035, 0.012))], 0.07, n=8)
    k.emit("Head_Trunk", col, rig=rig, bones=["trunk.1", "trunk.2", "trunk.3", "trunk.4"], scale=S)
    # ---- ears: small flaps, shaggy at the hem
    for s, sx in (("L", -1), ("R", 1)):
        pts = [Vector((sx * 0.44, 1.17, 1.8)), Vector((sx * 0.62, 1.04, 1.6)), Vector((sx * 0.68, 0.98, 1.32)), Vector((sx * 0.62, 0.96, 1.16))]
        bm_tube(k["wood_red:0.25:0.9"], pts, [0.13, 0.27, 0.24, 0.0], n=6, squash=0.22, up=(0, 1, 0))
        for dy in (-0.14, 0.0, 0.14):
            bm_lock(k[SHAG], pts[2] + Vector((0, dy, 0.04)), pts[2] + Vector((sx * 0.02, dy * 1.2, -0.3)), 0.15, 0.05, Vector((sx, 0, 0)))
        k.emit("Head_Ear" + s, col, rig=rig, bone="ear." + s, scale=S)
    # ---- legs: pillars that bend at the knee, a skirt of locks at the top, toenails
    for name, (a, b, c) in LEGS.items():
        a, b, c = Vector(a), Vector(b), Vector(c)
        bm_tube(k["wood_red:0.3:0.95"], [a + Vector((0, 0, 0.22)), a, b, c + Vector((0, 0, 0.17)), c + Vector((0, 0, 0.02))],
                [0.26, 0.33, 0.27, 0.265, 0.31], n=8)
        k.emit("Head_Leg" + name, col, rig=rig, bones=["leg.%s.1" % name, "leg.%s.2" % name], scale=S)
        for i in range(7):
            ang = math.radians(360 * i / 7 + (0 if name[1] == "L" else 25))
            d = Vector((math.cos(ang), math.sin(ang), 0))
            bm_lock(k[SHAG], a + d * 0.3 + Vector((0, 0, -0.05)), a + d * 0.33 + Vector((0, 0, -0.52 - rnd.uniform(0, 0.12))), 0.29, 0.06, d)
        k.emit("Head_LegCoat" + name, col, rig=rig, bone="leg.%s.1" % name, scale=S, vary=0.07)
        for i in range(4):
            ang = math.radians(90 + (i - 1.5) * 34)
            p = c + Vector((math.cos(ang) * 0.29, math.sin(ang) * 0.29, 0.075))
            bm_ellipsoid(k["cream:0.05:0.45"], p, (0.062, 0.05, 0.075), (0, 0, math.degrees(ang) - 90), u=6, v=4)
        k.emit("Head_Nails" + name, col, rig=rig, bone="leg.%s.2" % name, scale=S)
    # ---- tail
    bm_tube(k["wood_red:0.3:0.9"], [(0, -1.25, 1.36), (0, -1.42, 0.98), (0, -1.47, 0.72)], [0.075, 0.05, 0.035], n=6)
    for dx in (-0.04, 0.04, 0.0):
        bm_lock(k[MANE], Vector((dx, -1.47, 0.76)), Vector((dx * 2.2, -1.5, 0.42)), 0.09, 0.07, Vector((0, -1, 0)))
    k.emit("Head_Tail", col, rig=rig, bones=["tail.1", "tail.2"], scale=S)
    empty("Muzzle", col, head, (0, 1.9 * S, 0.4 * S), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 30


def pose(rig, breathe=0.0, lean=0.0, nod=0.0, look=0.0, curl=0.0, swing=0.0, tip=0.0, ear_l=0.0, ear_r=0.0, tail=0.0, tail_up=0.0,
         paw=0.0, rear=0.0, tuck=0.0, jaw=0.0, sq_c=0.0, sq_h=0.0, bounce=0.0, charm=0.0, dip=0.0):
    """rear: 1 = up on its hind legs; tuck: the forelegs folded under it; sq_c / sq_h: the ribs / the rump squashed
    (the ripple of a stomp); dip: the whole body sinking on its knees."""
    pb = rig.pose.bones
    rest_pose(rig)
    turn(pb, "hips", x=rear * 27, y=lean * 1.5)
    shift(pb, "hips", (lean * 0.03, 0, -dip * 0.06))
    turn(pb, "chest", x=rear * 7)
    scale_arm(pb, "ribs", (1 + breathe + sq_c * 0.7, 1, 1 + breathe - sq_c))
    scale_arm(pb, "rump", (1 + breathe * 0.4 + sq_h * 0.7, 1, 1 + breathe * 0.4 - sq_h))
    turn(pb, "head", x=nod - rear * 16, z=look, y=lean * -1.0)
    turn(pb, "jaw", x=-jaw * 26)
    for i, (b, kx, ks) in enumerate((("trunk.1", 0.5, 0.5), ("trunk.2", 0.9, 0.9), ("trunk.3", 1.1, 1.2), ("trunk.4", 0.9, 1.0))):
        turn(pb, b, x=curl * kx + (tip if i == 3 else 0.0), y=swing * ks)
    turn(pb, "ear.L", z=-ear_l)
    turn(pb, "ear.R", z=ear_r)
    turn(pb, "tail.1", y=tail, x=-tail_up * 50)
    turn(pb, "tail.2", y=tail * 0.8, x=-tail_up * 30)
    turn(pb, "saddle", x=-bounce * 4, y=lean * -1.2)
    shift(pb, "saddle", (0, 0, -bounce * 0.05 - sq_h * 0.03))
    for s, sx in (("L", -1), ("R", 1)):
        turn(pb, "charm." + s, y=charm * sx * 0.3 + lean * 2, x=charm + rear * -24)
        fold = tuck + (paw if s == "L" else 0.0)
        turn(pb, "leg.F%s.1" % s, x=fold * 38 + dip * 10)
        turn(pb, "leg.F%s.2" % s, x=-fold * 80 - dip * 22)
        turn(pb, "leg.B%s.1" % s, x=-rear * 27 + dip * 9)
        turn(pb, "leg.B%s.2" % s, x=-dip * 20)


def _idle(f):
    ph = 2 * math.pi * f / IDLE_LEN
    return dict(breathe=0.022 * math.sin(ph * 2), lean=math.sin(ph), nod=2.5 * math.sin(ph * 2 + 0.5), look=5 * math.sin(ph + 1.0),
                curl=7 * math.sin(ph) + 6 * math.sin(ph * 2 + 1.0), swing=11 * math.sin(ph + 0.6), tip=16 * math.sin(ph * 2 + 2.0),
                ear_l=20 * max(0.0, math.sin(ph * 3)) ** 2, ear_r=20 * max(0.0, math.sin(ph * 3 - 0.7)) ** 2,
                tail=20 * math.sin(ph * 3 + 0.3), paw=0.3 * max(0.0, math.sin(ph - 2.4)) ** 4, charm=9 * math.sin(ph * 2 + 1.0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, **_idle(f))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    base = _idle(0)
    for f in range(FIRE_LEN + 1):
        # up on its hind legs in four frames, both forefeet down on frame 7 (the game's pulse lands as the clip starts),
        # the front sinks on its knees and bounces back, the blow ripples from the ribs to the rump to the tail
        rear = smooth(f / 4.0) * (1 - smooth((f - 4) / 3.0)) + 0.1 * bump(f, 14, 5)
        tuck = smooth(f / 3.0) * (1 - smooth((f - 4.5) / 2.5))
        up = smooth(f / 4.0) * (1 - smooth((f - 13) / 13.0))                    # the trunk flung up, the trumpet
        whip = math.sin((f - 7) * 0.8) * math.exp(-(f - 7) / 6.0) * (1 - smooth((f - 23) / 6.0)) if f > 7 else 0.0
        fade = 1 - smooth(f / 3.0) * (1 - smooth((f - 22) / 8.0))               # the idle's own sway, out and back in
        p = {key: v * fade for key, v in base.items()}
        p.update(rear=rear, tuck=tuck, jaw=up, curl=base["curl"] * fade + 46 * up + 12 * whip, tip=base["tip"] * fade + 20 * up,
                 ear_l=34 * up, ear_r=34 * up, nod=base["nod"] * fade + 9 * bump(f, 8.5, 3.5), dip=bump(f, 8.5, 3.5),
                 sq_c=0.07 * bump(f, 8, 3.5) - 0.025 * bump(f, 12.5, 3.5), sq_h=0.06 * bump(f, 10.5, 4) - 0.02 * bump(f, 15, 4),
                 bounce=bump(f, 10.5, 4) - 0.4 * bump(f, 15.5, 4), tail_up=bump(f, 13, 5),
                 charm=base["charm"] * fade + 22 * whip)
        pose(rig, **p)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.0, 1.35), "dist": 10.8, "yaw": 138, "pitch": 15, "anim_target": (0, 0.6, 1.8), "anim_dist": 7.2,
           "frames": [("idle", 0), ("idle", 42), ("fire", 4), ("fire", 7), ("fire", 11)],
           "extra": [{"yaw": 140, "pitch": 10, "dist": 4.6, "target": (0.1, 1.4, 1.9)},
                     {"yaw": 215, "pitch": 26, "dist": 7.0, "target": (0, -0.8, 1.6)},
                     {"yaw": 0, "pitch": 57, "dist": 8.0, "target": (0, -0.2, 1.2)},
                     {"yaw": 90, "pitch": 8, "dist": 8.5, "target": (0, 0.2, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()


# ================================================================================================ the strike
# What the game plays under every enemy the stomp reaches (GameData.STRIKES "erupt", hit 0: the damage lands as the
# clip starts): the ground bursts: a crown of jagged rock spikes leaning outward, slabs of broken crust tipped up
# round them, clods of earth thrown high. Out by frame 2-3, gone again (sunk and shrunk) by frame 24.
STRIKE_LEN = 24
N_SPIKES, N_CLODS, N_SLABS = 7, 7, 7


def build_strike():
    col = collection("Mammoth_strike")
    root = empty("Mammoth_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(12)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "crust": ((0, 0, 0), (0, 0, 0.3), "root")}
    spikes, clods = [], []
    for i in range(N_SPIKES):
        if i == 0:              # the tall one, leaning the way the blow went
            base, d, h, r = Vector((0.0, 0.08, 0)), Vector((0.05, 0.3, 1)).normalized(), 1.2, 0.2
        else:
            a = 2 * math.pi * (i - 1) / (N_SPIKES - 1) + rnd.uniform(-0.25, 0.25)
            rad, lean = rnd.uniform(0.3, 0.44), rnd.uniform(0.45, 0.85)
            base = Vector((math.cos(a) * rad, math.sin(a) * rad, 0))
            d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1)).normalized()
            h, r = rnd.uniform(0.6, 0.98), rnd.uniform(0.13, 0.18)
        bones["spike.%d" % i] = (tuple(base - d * 0.12), tuple(base + d * h), "root")
        spikes.append((base, d, h, r))
    for i in range(N_CLODS):
        a = 2 * math.pi * i / N_CLODS + rnd.uniform(-0.3, 0.3)
        clods.append((a, rnd.uniform(1.0, 2.0), rnd.uniform(3.4, 4.6), rnd.uniform(0, 360)))
        bones["clod.%d" % i] = ((0, 0, 0.1), (0, 0, 0.3), "root")
    rig = make_rig(col, root, bones)
    k = Kit()
    for i, (base, d, h, r) in enumerate(spikes):
        side = d.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        sw = "stone:0.05:0.9" if i % 2 else "stone2:0.1:0.95"
        bm_crystal(k[sw], base - d * 0.15, base + d * h, r, n=5, shoulder=0.3, foot=1.0)
        for sgn, hh in ((1, 0.5), (-1, 0.38)):             # shards splitting off its foot
            dd = (d + side * sgn * 0.55).normalized()
            bm_crystal(k["stone:0.25:0.95"], base + side * sgn * r * 0.6 - dd * 0.1, base + side * sgn * r * 0.6 + dd * h * hh, r * 0.6, n=4, shoulder=0.3, foot=1.0)
        k.emit("Spike%d" % i, col, rig=rig, bone="spike.%d" % i, vary=0.06, seed=i + 1)
    for i in range(N_SLABS):                               # the crust, broken and tipped up, on dark torn earth
        a = 2 * math.pi * (i + 0.5) / N_SLABS + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        p0, p1 = d * 0.5 + Vector((0, 0, 0.26)), d * 0.86 + Vector((0, 0, 0.03))
        bm_beam(k["wood_red:0.5:0.95"], p0, p1, rnd.uniform(0.3, 0.42), 0.09, w1=rnd.uniform(0.34, 0.5), h1=0.07)
    bm_patch(k["wood_red:0.9:0.99"], rnd, (0, 0), 0.72, 0.0, 0.03, n=9, jitter=0.2)
    k.emit("Crust", col, rig=rig, bone="crust", vary=0.08)
    for i in range(N_CLODS):
        bm_boulder(k["wood_red:0.5:0.95"], rnd, (0, 0, 0.1), rnd.uniform(0.09, 0.15), n=8, sink=0.0)
        if i % 2 == 0:
            bm_boulder(k["stone:0.3:0.9"], rnd, (0.12, 0.05, 0.16), rnd.uniform(0.05, 0.08), n=7, sink=0.0)
        k.emit("Clod%d" % i, col, rig=rig, bone="clod.%d" % i)
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    for f in range(STRIKE_LEN + 1):
        rest_pose(rig)
        for i in range(N_SPIKES):
            late = (i % 3) * 0.5
            g = smooth((f - late) / 2.0)
            over = 0.16 * math.sin(math.pi * min(max((f - late - 1.0) / 4.0, 0.0), 1.0))
            sink = smooth((f - 13 - (i % 2) * 1.5) / 8.0)
            s = max(0.02, (g + over) * (1.0 - sink))
            b = pb["spike.%d" % i]
            b.scale = (s, s, s)
            shift(pb, "spike.%d" % i, (0, 0, -0.3 * (1.0 - g) - 0.5 * sink))
        g = smooth(f / 2.0)
        sink = smooth((f - 15) / 8.0)
        wide = max(0.02, (0.55 + 0.45 * g) * (1 - sink * 0.6))
        scale_arm(pb, "crust", (wide, wide, max(0.02, (g + 0.25 * bump(f, 3, 3)) * (1 - sink))))
        shift(pb, "crust", (0, 0, -0.08 * sink))
        for i, (a, v_out, v_up, spin) in enumerate(clods):
            t = f / 30.0
            z = max(0.0, v_up * t - 6.5 * t * t)
            b = pb["clod.%d" % i]
            s = max(0.02, smooth(f / 1.5) * (1.0 - smooth((f - 17) / 6.0)))
            b.scale = (s, s, s)
            b.rotation_quaternion = arm_space_quat(b, (math.cos(a + 1.57), math.sin(a + 1.57), 0), spin + f * 24)
            shift(pb, "clod.%d" % i, (math.cos(a) * v_out * t, math.sin(a) * v_out * t, z - 0.12 * (1 - smooth(f / 1.5))))
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [1, 3, 7, 15, 21], "dist": 6.0, "target": (0, 0, 0.6)}
