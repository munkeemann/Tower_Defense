"""Builds the Heart of the Forest (footprint "star5": [0,0] the middle, [1,-1] / [-1,0] front-right / front-left,
[1,0] / [-1,1] back-right / back-left), the Verdant's Tier IV support tower: the towers round it hit harder.

    python tools/blender/build.py heart_tree --out <preview dir>

The grandest tree: one colossal trunk whose four great buttresses run out as roots over all four outer hexes and claw
into the far ground, a hollow in its back holding the forest's heart (a big green glowing heart with veins running into
the bark: it beats; the Head / Muzzle), a broad canopy in three tiers of several greens, blossoming in the team's color,
lanterns hanging under it, spirit-lights circling the trunk, ribbons in the team's color tied to the boughs, a shrine
door at its foot with a lit step, and ferns, toadstools and mossy stones in the hollows between its roots.
A support tower: nothing turns, the rig is under the root and it only ever plays idle (the heart beats, the canopy
sways tier over tier, the lights circle and bob, the lanterns swing, the ribbons stir).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open(os.path.join(REPO, "tools", "blender", "greatwood_common.py"), encoding="utf-8").read())

TID = "heart_tree"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C = hex_to_world(0, 0, MID)
TOP = 0.34
T = TOP + 0.05                  # the turf's top (plinth(turf=True))
ZC = T + 0.1                    # the trunk's own zero
HEART = Vector((0.0, -0.36, T + 1.28))      # the heart's middle, in the hollow at the back
HOLLOW_A = 270.0                # where the hollow opens (the back: toward the player)
DOOR_A = 232.0
CANOPY_Z = T + 2.3              # where the limbs leave the trunk
HG = "glow:0.3,0.95,0.42,0.75"  # the heart's light
HGB = "glow:0.7,1.0,0.65,0.95"
PETAL = "team!:0.1:0.6"
# the canopy: (tier, bearing, how far out (x, y), height above the turf, size, swatch)
PADS = [(0, 30, 1.5, 1.2, 2.45, 0.8, LEAF_B), (0, 150, 1.5, 1.2, 2.5, 0.8, LEAF_A), (0, 210, 1.5, 1.2, 2.42, 0.78, LEAF_A), (0, 330, 1.5, 1.2, 2.48, 0.8, LEAF_B),
        (0, 90, 0.85, 0.85, 2.62, 0.62, LEAF_C), (0, 270, 0.8, 0.8, 2.58, 0.6, LEAF_A),
        (1, 0, 0.9, 0.9, 3.0, 0.7, LEAF_A), (1, 90, 0.8, 0.8, 3.06, 0.66, LEAF_B), (1, 180, 0.9, 0.9, 2.98, 0.7, LEAF_C), (1, 270, 0.78, 0.78, 3.04, 0.66, LEAF_B),
        (2, 60, 0.45, 0.45, 3.42, 0.6, LEAF_C), (2, 180, 0.45, 0.45, 3.4, 0.6, LEAF_A), (2, 300, 0.45, 0.45, 3.44, 0.6, LEAF_B), (2, 0, 0.0, 0.0, 3.7, 0.56, LEAF_TOP)]
LAMPS = [(30, 1.25, 2.2), (120, 1.0, 2.3), (200, 1.2, 2.18), (260, 1.0, 2.26), (320, 1.2, 2.2)]      # (bearing, out, the rope's top)
WISPS = [(0.0, 1.05, 1.5), (80.0, 1.3, 1.9), (160.0, 1.1, 2.1), (240.0, 1.35, 1.7), (300.0, 1.15, 1.3)]  # (bearing, out, height)


def rp(a, r, off=0.0, z=0.0):
    """A point r out from the trunk at bearing a (degrees), `off` to the left of that line, z above the turf."""
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return Vector((C.x + ca * r - sa * off, C.y + sa * r + ca * off, T + z))


def pad_c(i):
    tier, a, rx, ry, z, r, sw = PADS[i]
    return Vector((C.x + math.cos(math.radians(a)) * rx, C.y + math.sin(math.radians(a)) * ry, T + z))


def bm_blossom(bm, c, up, r, rnd):
    """A five-petalled blossom lying on a leaf pad, opening toward up."""
    c, u = Vector(c), Vector(up).normalized()
    x = u.orthogonal().normalized()
    y = u.cross(x)
    ph = rnd.uniform(0, 6.283)
    for i in range(5):
        a = ph + 2 * math.pi * i / 5
        d = x * math.cos(a) + y * math.sin(a)
        s = u.cross(d)
        tip = c + d * r + u * r * 0.25
        for side in (1, -1):
            vs = [bm.verts.new(p + u * (0.004 * side)) for p in (c + u * 0.01, tip + s * r * 0.42, tip - s * r * 0.42)]
            bm.faces.new(vs if side > 0 else list(reversed(vs)))
    return bm


def build_base():
    col = collection("Heart_tree")
    root = empty("Heart_tree", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(17)
    k = Kit()
    # ---- the trunk: a colossal bole flaring into four great buttresses toward the outer hexes, a hollow dented into its back
    lobes = {30: 0.55, 150: 0.55, 210: 0.55, 330: 0.55, 90: 0.22, 270: 0.18, 0: -0.1, 60: -0.12, 120: -0.12, 180: -0.1, 240: -0.08, 300: -0.08}
    angles = list(range(0, 360, 15))
    secs = [(-0.1, 1.05, 1.0, 1.0), (0.3, 0.86, 0.8, 0.7), (0.62, 0.74, 0.7, 0.4), (0.78, 0.7, 0.66, 0.3), (1.15, 0.64, 0.62, 0.12), (1.5, 0.63, 0.6, 0.0),
            (1.68, 0.64, 0.6, 0.0), (1.95, 0.68, 0.64, 0.0), (2.2, 0.78, 0.72, 0.0)]
    trunk = Trunk((C.x, C.y, ZC), secs, angles, lobes, rnd, 0.015)
    for row in (3, 4, 5):                                     # the hollow: the rings pressed in round the back
        for j, a in enumerate(angles):
            da = abs((a - HOLLOW_A + 180.0) % 360.0 - 180.0)
            if da <= 37.5:
                dent = (0.52, 0.56, 0.5)[row - 3] * math.cos(math.radians(da) * 2.4) ** 0.8
                p, m = trunk.rings[row][j], trunk.mids[row]
                trunk.rings[row][j] = m + (p - m) * (1.0 - dent)
    trunk.loft(k[BARK])
    tp = trunk.at
    hollow_c = Vector((C.x, C.y - 0.5, T + 1.28))
    bm_plates(k[BARK_PLATE], trunk.rings, rnd, th=(0.035, 0.06), rows=(1.5, 2.8), gap=0.2, side=0.2, point=0.3, nar=0.4,
              skip=lambda c: (c - hollow_c).length < 0.62 or (c - rp(DOOR_A, 1.0, 0.0, 0.4)).length < 0.5)
    # the hollow's lip: a swollen rim of bark round the opening
    lip = []
    for i in range(13):
        a = 2 * math.pi * i / 12
        lip.append(tp(HOLLOW_A + math.cos(a) * 34.0, 1.15 + math.sin(a) * 0.46, 0.04))
    bm_tube(k[BARK_PLATE], lip, 0.07, n=5)
    # the heart's veins, from the hollow into the bark
    for a, z, L in ((250, 1.5, 0.5), (292, 1.45, 0.45), (246, 1.0, 0.4), (296, 0.98, 0.42), (270, 0.78, 0.45)):
        q = tp(a, z, 0.03)
        bm_tube(k[HG], [HEART + (q - HEART) * 0.35, q, tp(a + (a - 270) * 0.3, z + (0.35 if z > 1.2 else -0.3), 0.03)], [0.045, 0.035, 0.0], n=4)
    # the trunk's top: the limbs carrying the canopy, each to its pad
    limbs = {}
    for i, (tier, a, rx, ry, z, r, sw) in enumerate(PADS):
        c = pad_c(i)
        base = Vector((C.x, C.y, CANOPY_Z - 0.2)) + Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)) * (0.3 if tier == 0 else 0.15)
        mid = base.lerp(c, 0.5) + Vector((0, 0, 0.25 if tier == 0 else 0.1))
        limbs[i] = bm_root(k[BARK], [base, mid, c - Vector((0, 0, r * 0.3))], [0.3 if tier == 0 else 0.2, 0.2 if tier == 0 else 0.13, 0.08], n=6, sub=3)
    k.emit("Trunk", col, root, vary=0.05, seed=4)
    bark = bpy.data.objects.get("Trunk_taupe_dark")
    if bark:                                                  # the hollow's inside is dark
        paint_faces(bark, "black", lambda c, n: (c - hollow_c).length < 0.5, lo=0.35, hi=0.8)
    # ---- the roots: four great buttress roots out over the outer hexes, rootlets off them, short roots to the other sides
    def run(a, pts, radii, n=6, claw=3, reach=0.3, moss=()):
        ctrl = [rp(a, r, off, z) for r, off, z in pts]
        cp, rad, rings = bm_root(k[ROOT], ctrl, radii, n=n, sub=3, squash=1.15)
        for i in moss:
            bm_blob(k[MOSS], rnd, cp[i] + Vector((0, 0, rad[i] * 0.72)), rad[i] * 1.1, squash=(1.3, 1.3, 0.4), jitter=0.2)
        if claw:
            bm_claw(k[ROOT], cp[-1], cp[-1] - cp[-2], rad[-1], rnd, toes=claw, reach=reach, T=T, n=4)
        return cp
    big = [0.36, 0.32, 0.27, 0.23, 0.19, 0.15, 0.11]
    for a, sg in ((30, 1), (150, -1), (210, 1), (330, -1)):
        run(a, [(0.7, 0, 0.5), (1.2, sg * 0.06, 0.34), (1.65, sg * -0.1, 0.24), (2.05, sg * -0.3, 0.2), (2.4, sg * -0.3, 0.15), (2.7, sg * -0.1, 0.08)], big, n=7,
            claw=3, reach=0.3, moss=(4, 8, 12))
        run(a, [(1.3, sg * 0.1, 0.3), (1.6, sg * 0.5, 0.2), (1.95, sg * 0.82, 0.14), (2.25, sg * 0.95, 0.06)], [0.17, 0.15, 0.12, 0.09], claw=2, reach=0.2)
        run(a, [(1.5, sg * -0.14, 0.28), (1.8, sg * -0.62, 0.17), (2.1, sg * -0.92, 0.08)], [0.14, 0.11, 0.08], claw=2, reach=0.18)
    for a, far in ((90, 0.98), (270, 0.95), (0, 1.1), (180, 1.1), (60, 1.05), (120, 1.05), (300, 1.05)):
        run(a, [(0.62, 0, 0.34), (far * 0.78, 0.05, 0.18), (far, 0.0, 0.06)], [0.2, 0.15, 0.1], claw=2, reach=0.14)
    k.emit("Roots", col, root, vary=0.06, seed=6)
    # ---- the shrine door at the foot, between two buttresses: a planked door under an arch of branch, a lit step, a path
    dp = tp(DOOR_A, 0.05, 0.0)
    out = trunk.out(DOOR_A)
    side = Vector((-out.y, out.x, 0))
    dw, dh = 0.44, 0.58
    bm_box(k["black:0.3:0.7"], (dw + 0.1, 0.12, dh + 0.3), tuple(dp + out * 0.0 + Vector((0, 0, dh * 0.5))), (0, 0, DOOR_A + 90))
    bm_planks(k["wood_dark:0.2:0.7"], rnd, dp + out * 0.08 - side * (dw * 0.5), Vector((0, 0, dh)), side * dw, 4, th=0.04)
    bm_cyl(k["wood_dark:0.2:0.7"], dw * 0.5, dw * 0.5, 0.04, tuple(dp + out * 0.06 + Vector((0, 0, dh))), rot=(90, 0, DOOR_A + 90), seg=12)
    bm_cyl(k["wood_dark:0.2:0.7"], dw * 0.5 - 0.02, dw * 0.5 - 0.02, 0.04, tuple(dp + out * 0.08 + Vector((0, 0, dh))), rot=(90, 0, DOOR_A + 90), seg=12)
    for z in (0.14, 0.42):
        bm_box(k["iron:0.2:0.6"], (dw * 0.86, 0.03, 0.05), tuple(dp + out * 0.11 + Vector((0, 0, z))), (0, 0, DOOR_A + 90))
    bm_blob(k["gold:0.1:0.5"], rnd, dp + out * 0.12 + side * 0.13 + Vector((0, 0, 0.3)), 0.03, jitter=0.1)
    arch = [dp + out * 0.1 + side * (math.cos(math.pi * i / 10) * (dw * 0.5 + 0.06)) + Vector((0, 0, dh + math.sin(math.pi * i / 10) * (dw * 0.5 + 0.06))) for i in range(11)]
    bm_tube(k[BARK_PLATE], [dp + out * 0.1 - side * (dw * 0.5 + 0.06) + Vector((0, 0, -0.05))] + list(reversed(arch)) + [dp + out * 0.1 + side * (dw * 0.5 + 0.06) + Vector((0, 0, -0.05))],
            0.05, n=5)
    bm_stone(k["stone:0.15:0.85"], rnd, (dp.x + out.x * 0.26, dp.y + out.y * 0.26, T - 0.02), (0.66, 0.34, 0.1), yaw=DOOR_A + 90, n=0, jit=0.08)
    for s in (-1, 1):
        bm_candle(k, dp + out * 0.28 + side * (s * 0.3) + Vector((0, 0, 0.1)), h=0.12, r=0.032)
    bm_flagstones(k["stone:0.15:0.85"], rnd, lambda x, y: 0.0 < (Vector((x, y, 0)) - Vector((dp.x, dp.y, 0))).dot(out) < 0.9 and
                  abs((Vector((x, y, 0)) - Vector((dp.x, dp.y, 0))).dot(side)) < 0.26 and in_footprint(CELLS, x, y, 0.22),
                  (dp.x - 1.1, dp.y - 1.1, dp.x + 1.1, dp.y + 1.1), T - 0.005, size=0.26, gap=0.03, h=0.035)
    k.emit("Door", col, root, vary=0.07, seed=8)
    # ---- the forest floor: ferns and toadstools in the root hollows, mossy stones and moss out on the hexes, fallen petals
    for a in (0, 60, 120, 180, 300):
        bm_fern(k["grass:0.1:0.75"], rnd, rp(a, 1.02, rnd.uniform(-0.1, 0.1)), n=5, length=0.32, rise=0.24, w=0.1)
    for (a, r, off, h, cr) in ((60, 0.95, 0.22, 0.26, 0.16), (60, 1.1, 0.0, 0.16, 0.1), (180, 0.95, -0.2, 0.22, 0.14), (300, 1.0, 0.2, 0.2, 0.13), (0, 0.9, -0.22, 0.14, 0.09),
                               (30, 2.2, 0.55, 0.3, 0.18), (30, 2.4, 0.42, 0.18, 0.11), (210, 2.3, -0.55, 0.26, 0.16), (210, 2.45, -0.4, 0.15, 0.1), (150, 1.6, 0.6, 0.2, 0.13)):
        q = rp(a, r, off)
        if in_footprint(CELLS, q.x, q.y, 0.28):
            bm_mushroom(k, rnd, q, h, cr, cap="orange:0.05:0.7", spots="cream:0.0:0.4" if cr > 0.13 else None, n=7 if cr > 0.13 else 6)
    for (a, r, off, s) in ((30, 2.1, 0.62, 0.3), (150, 2.3, -0.5, 0.28), (210, 1.9, 0.62, 0.3), (330, 2.35, 0.5, 0.26), (330, 1.6, -0.62, 0.2), (150, 1.5, 0.6, 0.22)):
        q = rp(a, r, off)
        if in_footprint(CELLS, q.x, q.y, 0.32):
            bm_boulder(k["stone:0.15:0.9"], rnd, (q.x, q.y, T - 0.02), s, squash=(1.1, 1.0, 0.8), n=11)
            bm_blob(k[MOSS], rnd, (q.x - 0.03, q.y + 0.02, T + s * 1.15), s * 0.7, squash=(1.2, 1.0, 0.35), jitter=0.16)
    for (a, r, off, s) in ((30, 1.55, -0.5, 0.36), (30, 2.55, 0.2, 0.3), (150, 1.9, 0.0, 0.34), (150, 2.6, -0.3, 0.3), (210, 1.5, -0.5, 0.34), (210, 2.6, 0.2, 0.3),
                           (330, 1.95, 0.1, 0.34), (330, 2.6, -0.3, 0.28), (90, 0.95, 0.4, 0.26), (270, 0.95, -0.42, 0.26), (0, 1.1, 0.3, 0.24), (180, 1.1, -0.3, 0.24),
                           (30, 1.9, 0.9, 0.26), (210, 2.0, -0.95, 0.26), (150, 2.2, 0.85, 0.24), (330, 2.15, -0.9, 0.24)):
        q = rp(a, r, off, -0.012)
        if in_footprint(CELLS, q.x, q.y, 0.3):
            bm_blob(k[MOSS if (r * 10) % 2 < 1 else "teal:0.3:0.8"], rnd, tuple(q), s, squash=(1.25, 1.0, 0.16), jitter=0.2)
    for (a, r, off, L) in ((30, 2.6, 0.5, 0.34), (150, 2.5, 0.5, 0.32), (210, 2.5, -0.55, 0.34), (330, 2.6, -0.5, 0.32), (30, 1.7, 0.75, 0.3), (330, 1.5, 0.7, 0.3),
                           (150, 1.75, -0.7, 0.3), (210, 1.7, 0.7, 0.3)):
        q = rp(a, r, off)
        if in_footprint(CELLS, q.x, q.y, 0.3):
            bm_fern(k["grass:0.1:0.75"], rnd, q, n=5, length=L, rise=L * 0.7, w=0.1)
    for i in range(36):
        a, r = rnd.uniform(0, 360), rnd.uniform(0.9, 2.7)
        p = rp(a, r, 0, 0.012)
        if in_footprint(CELLS, p.x, p.y, 0.25):
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
            bm_leaf(k[PETAL if i % 2 else "cream:0.1:0.5"], p, p + d * 0.1 + Vector((0, 0, 0.01)), 0.07)
    k.emit("Floor", col, root, vary=0.08, seed=9)
    head = empty("Head", col, root, (C.x, C.y, HEART.z), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, HEART.y - 0.2, 0), 0.2, "SPHERE")
    return root, limbs


def build_rig(limbs):
    col = collection("Heart_tree")
    root = bpy.data.objects["Heart_tree"]
    rnd = random.Random(23)
    top = Vector((C.x, C.y, CANOPY_Z))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "heart": (tuple(HEART), tuple(HEART + Vector((0, 0, 0.3))), "root"),
             "spin": (tuple(HEART + Vector((0, 0.36, 0.4))), tuple(HEART + Vector((0, 0.36, 0.7))), "root"),
             "sway.0": (tuple(top), tuple(top + Vector((0, 0, 0.5))), "root"),
             "sway.1": (tuple(top + Vector((0, 0, 0.5))), tuple(top + Vector((0, 0, 1.0))), "sway.0"),
             "sway.2": (tuple(top + Vector((0, 0, 1.0))), tuple(top + Vector((0, 0, 1.5))), "sway.1")}
    for i, (a, r, z) in enumerate(WISPS):
        p = rp(a, r, 0.0, z)
        bones["wisp.%d" % i] = (tuple(p), tuple(p + Vector((0, 0, 0.12))), "spin")
    for i, (a, r, z) in enumerate(LAMPS):
        p = rp(a, r, 0.0, z)
        bones["lamp.%d" % i] = (tuple(p), tuple(p + Vector((0, 0, -0.3))), "sway.0")
    ribs = {"A": rp(250, 1.15, 0.0, 2.3), "B": rp(295, 1.2, 0.0, 2.26)}
    for nm, p in ribs.items():
        flag_bones(bones, "rib." + nm, tuple(p), (0, 0, -1), 1.1, segs=3, parent="sway.0")
    rig = make_rig(col, root, bones)
    k = Kit()
    # ---- the heart: a lofted heart of green light, two lobes above, a brighter one turned half a facet inside it
    x, y = Vector((1, 0, 0)), Vector((0, 1, 0))
    for sw, ph, kr in ((HG, 0.0, 1.0), (HGB, 0.5, 0.9)):
        rows = [oval(HEART + Vector((0, 0, z)), x, y, rx * kr, ry * kr, 6, phase=ph) for z, rx, ry in ((-0.2, 0.13, 0.11), (-0.02, 0.25, 0.2), (0.14, 0.26, 0.2))]
        bm_loft(k[sw], rows, tip0=HEART + Vector((0, 0, -0.36 * kr)), cap1=True)
        for sx in (-1, 1):
            bm_ellipsoid(k[sw], HEART + Vector((sx * 0.13 * kr, 0, 0.22 * kr)), (0.15 * kr, 0.13 * kr, 0.13 * kr), (0, 0, 30 * ph * sx), u=7, v=4)
    k.emit("Heart", col, rig=rig, bone="heart")
    # ---- the canopy, tier by tier: pads of leaves, blossoms in the team's color on top, sprigs at the rims
    for i, (tier, a, rx, ry, z, r, sw) in enumerate(PADS):
        c = pad_c(i)
        bm_blob(k[sw], rnd, c, r, squash=(1.15, 1.15, 0.62), jitter=0.17, sub=2)
        for j in range(6):
            aa = rnd.uniform(0, 6.283)
            d = Vector((math.cos(aa), math.sin(aa), 0.2))
            bm_sprig(k[LEAF_C if sw != LEAF_C else LEAF_A], rnd, c + Vector((d.x * r * 1.05, d.y * r * 1.05, r * 0.15)), d, n=3, size=0.24)
        for j in range(5 if tier > 0 else 3):
            aa, rr = rnd.uniform(0, 6.283), rnd.uniform(0.2, 0.75) * r
            q = c + Vector((math.cos(aa) * rr, math.sin(aa) * rr, r * 0.62 * math.sqrt(max(0.0, 1.0 - (rr / (r * 1.1)) ** 2)) + 0.01))
            up = ((q - c).normalized() + Vector((0, 0, 0.6))).normalized()
            bm_blossom(k[PETAL], q, up, 0.125, rnd)
            bm_crystal(k["gold:0.1:0.5"], q + up * 0.005, q + up * 0.055, 0.028, n=3, shoulder=0.4)
    k.emit("Canopy", col, rig=rig, bones=["sway.0", "sway.1", "sway.2"], vary=0.06, seed=10)
    for i, (a, r, z) in enumerate(LAMPS):                     # lanterns on ropes under the lower boughs
        p = rp(a, r, 0.0, z)
        bm_tube(k["sand:0.3:0.7"], [p + Vector((0, 0, 0.08)), p + Vector((0, 0, -0.26))], 0.012, n=4)
        bm_lantern(k, p + Vector((0, 0, -0.26)), s=0.2, glow=FLAME, cap="team!:0.1:0.6", strength=0.9)
        k.emit("Lamp%d" % i, col, rig=rig, bone="lamp.%d" % i)
    for i, (a, r, z) in enumerate(WISPS):                     # spirit-lights circling the trunk
        p = rp(a, r, 0.0, z)
        bm_blob(k[HGB], rnd, p, 0.06, jitter=0.1)
        t = Vector((-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))
        bm_tube(k["glow:0.45,0.9,0.45,0.65"], [p - t * 0.03, p - t * 0.18, p - t * 0.36 + Vector((0, 0, -0.04))], [0.045, 0.028, 0.0], n=4)
        k.emit("Wisp%d" % i, col, rig=rig, bone="wisp.%d" % i)
    for nm, p in ribs.items():
        flag_part("Ribbon" + nm, col, rig, "rib." + nm, tuple(p), (0, 0, -1), 1.1, 0.14, segs=3, tail="point", hang=(1, 0, 0))
    return rig


IDLE_LEN = 96


def pose(rig, t):
    pb = rig.pose.bones
    rest_pose(rig)
    ph = 2 * math.pi * t
    # the heartbeat: two quick pulses, twice a loop
    u = (t * 2.0) % 1.0
    beat = 0.14 * math.exp(-((u - 0.08) / 0.05) ** 2) + 0.09 * math.exp(-((u - 0.24) / 0.05) ** 2)
    h = pb["heart"]
    h.scale = (1.0 + beat, 1.0 + beat * 0.8, 1.0 + beat)
    h.location = arm_space_loc(h, (0, 0, 0.01 * math.sin(ph)))
    pb["spin"].rotation_quaternion = arm_space_quat(pb["spin"], (0, 0, 1), -360.0 * t)
    for i in range(len(WISPS)):
        w = pb["wisp.%d" % i]
        w.location = arm_space_loc(w, (0, 0, 0.08 * math.sin(3 * ph + i * 1.9)))
        w.scale = (1.0 + 0.2 * math.sin(6 * ph + i),) * 3
    for i in range(3):                                        # the canopy sways, each tier a little more than the one below
        b = pb["sway.%d" % i]
        b.rotation_quaternion = arm_space_quat(b, (1, 0, 0), (1.6 + 0.6 * i) * math.sin(ph + 0.5 * i)) @ arm_space_quat(b, (0, 1, 0), (1.2 + 0.5 * i) * math.sin(2 * ph + 0.7 * i + 1.0))
    for i, (a, r, z) in enumerate(LAMPS):
        b = pb["lamp.%d" % i]
        b.rotation_quaternion = arm_space_quat(b, (math.cos(math.radians(a)), math.sin(math.radians(a)), 0), 7.0 * math.sin(2 * ph + i * 1.3)) \
            @ arm_space_quat(b, (-math.sin(math.radians(a)), math.cos(math.radians(a)), 0), 4.0 * math.sin(3 * ph + i * 0.8))
    for i, nm in enumerate(("A", "B")):
        wave_flag(rig, "rib." + nm, 2.0 * t + 0.4 * i, amp=0.7, segs=3, axis=(1, 0, 0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(IDLE_LEN + 1):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.6), "dist": 13.0, "yaw": 150, "pitch": 20, "anim_target": (0, -0.3, 1.5), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 4), ("idle", 30), ("idle", 60)],
           "extra": [{"yaw": 0, "pitch": 14, "dist": 4.6, "target": (0, -0.4, 1.3)},
                     {"yaw": 330, "pitch": 24, "dist": 5.0, "target": (-0.9, -0.9, 0.6)},
                     {"yaw": 0, "pitch": 60, "dist": 11.0, "target": (0, 0, 1.0)},
                     {"yaw": 180, "pitch": 16, "dist": 7.0, "target": (0, 0, 1.8)}]}


def build_all():
    root, limbs = build_base()
    build_rig(limbs)
    build_anims()
    tri_report(collection("Heart_tree"))
