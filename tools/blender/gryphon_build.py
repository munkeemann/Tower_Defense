"""Builds the Gryphon Roost (footprint "wing3": [0,0] the back cell, [1,-1] front-right, [-1,0] front-left).

    python tools/blender/build.py gryphon --out <preview dir>

One roost, not a scatter of props: a round stone eyrie on the back cell with a timber landing deck and a straw nest on
top, a ladder up its side and the team's banner down its front; a paved yard spreads over the two front cells, with
the clutch of golden eggs on a rock ledge on the left and the feed (trough, hay, a rack of lances) on the right.
The gryphon is the Head, so the game can fly it (GameData.STRIKES "fly"): eagle before, lion behind, soft-skinned over
its spine, with a team saddle cloth and a rider's place (Crew). Clips: idle (perched: looks about, ruffles its wings),
fly (the wingbeat, looped while it's in the air), fire (talons thrust forward, wings flared: the blow lands 0.12 s in).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "gryphon"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FR = hex_to_world(1, -1, MID)
FL = hex_to_world(-1, 0, MID)
TOP = 0.34
DECK = TOP + 1.42             # the landing deck's top
PERCH = DECK + 0.1            # the nest's top: where the gryphon stands
GS = 1.2                      # gryphon scale (laid out at 1.0)


def build_base():
    col = collection("Gryphon")
    root = empty("Gryphon", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(21)
    k = Kit()
    C = BACK
    # ---- the eyrie: a round stone tower, a corbelled ring under a hexagonal timber deck
    round_tower(k, rnd, (C.x, C.y, 0), 0.8, 0.68, T, T + 1.18, courses=6, n=11)
    bm_block_course(k["stone:0.1:0.7"], rnd, (C.x, C.y, 0), 0.8, T + 1.18, 0.14, 12, depth=0.3)
    bm_arch(k["stone_warm"], (C.x, C.y + 0.74, T), (1, 0, 0), 0.36, 0.34, th=0.1, depth=0.16, n=5)
    bm_box(k["wood_dark:0.3:0.8"], (0.36, 0.08, 0.6), (C.x, C.y + 0.7, T + 0.3))
    for a in (25, 155):
        p = C + Vector((math.cos(math.radians(a)) * 0.72, math.sin(math.radians(a)) * 0.72, 0))
        bm_box(k["black:0.3:0.7"], (0.07, 0.12, 0.3), (p.x, p.y, T + 0.75), (0, 0, a - 90))                 # arrow slits
    k.emit("Eyrie", col, root, bevel=0.012, vary=0.07)
    hexp = [C + Vector((math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i)), 0)) * 1.02 for i in range(6)]
    for i in range(6):                                          # joists out to the deck's corners, braces under them
        p = hexp[i]
        bm_beam(k["wood_dark:0.2:0.7"], (C.x, C.y, DECK - 0.12), (p.x, p.y, DECK - 0.12), 0.1, 0.1)
        q = C + (p - C) * 0.72
        bm_beam(k["wood_dark:0.2:0.7"], (q.x, q.y, T + 0.95), (p.x * 0.96 + C.x * 0.04, p.y * 0.96 + C.y * 0.04, DECK - 0.14), 0.07, 0.07)
    k.emit("Eyrie_Joists", col, root, bevel=0.008)
    # the deck's planks, clipped to the hexagon: one short plank bay per strip
    y, pw = C.y - 0.88, 0.2
    while y < C.y + 0.88:
        half = min(1.02 - abs(y - C.y) / SQ3, 1.02 - abs(y + pw - C.y) / SQ3)
        if half > 0.2:
            bm_planks(k["wood:0.2:0.75"], rnd, (C.x - half, y, DECK), (2 * half, 0, 0), (0, pw, 0), 1, th=0.07, gap=0.014)
        y += pw
    k.emit("Eyrie_Deck", col, root, vary=0.08)
    for i in range(6):                                          # corner posts and a rope rail (open at the front)
        p = hexp[i]
        bm_box(k["wood_dark:0.2:0.7"], (0.09, 0.09, 0.36), (p.x * 0.95 + C.x * 0.05, p.y * 0.95 + C.y * 0.05, DECK + 0.18))
        bm_cyl(k["gold:0.1:0.5"], 0.04, 0.0, 0.09, (p.x * 0.95 + C.x * 0.05, p.y * 0.95 + C.y * 0.05, DECK + 0.4), seg=5)
        if i not in (1,):
            a, b = hexp[i] * 0.95 + C * 0.05, hexp[(i + 1) % 6] * 0.95 + C * 0.05
            m = (a + b) * 0.5
            bm_tube(k["sand:0.3:0.6"], [(a.x, a.y, DECK + 0.3), (m.x, m.y, DECK + 0.22), (b.x, b.y, DECK + 0.3)], 0.018, n=4)
    k.emit("Eyrie_Rail", col, root)
    # the nest: a ring of woven twigs round a bed of straw
    for i in range(22):
        a = math.radians(360 * i / 22 + rnd.uniform(-6, 6))
        a2 = a + math.radians(rnd.uniform(30, 48))
        r1, r2 = rnd.uniform(0.5, 0.62), rnd.uniform(0.5, 0.62)
        z = DECK + rnd.uniform(0.02, 0.1)
        bm_beam(k["wood:0.3:0.8"], C + Vector((math.cos(a) * r1, math.sin(a) * r1, z)), C + Vector((math.cos(a2) * r2, math.sin(a2) * r2, z + 0.03)), 0.05, 0.05)
    bm_cyl(k["gold:0.25:0.6"], 0.5, 0.46, 0.08, (C.x, C.y, DECK + 0.05), seg=10)
    k.emit("Nest", col, root, vary=0.08)
    # the team's banner down the front of the tower, and a ladder up the side
    bm_box(k["wood_dark"], (0.56, 0.05, 0.05), (C.x, C.y + 0.86, T + 1.12))
    k.emit("Banner_Rod", col, root)
    bm = k["team!:0.1:0.75"]
    pts = [(-0.24, 1.1), (0.24, 1.1), (0.24, 0.52), (0.0, 0.4), (-0.24, 0.52)]
    for off, flip in ((0.9, False), (0.885, True)):
        vs = [bm.verts.new((C.x + px, C.y + off, T + pz)) for px, pz in pts]
        bm.faces.new(list(reversed(vs)) if flip else vs)
    k.emit("Banner", col, root)
    bm_cyl(k["gold:0.1:0.5"], 0.085, 0.085, 0.02, (C.x, C.y + 0.905, T + 0.82), rot=(90, 0, 0), seg=8)
    k.emit("Banner_Boss", col, root)
    for o in kk_import("hex/ladder", col, root, (C.x - 0.86, C.y - 0.3, T), 100, 1.9, name="Ladder"):
        o.rotation_euler = (math.radians(-10), 0, math.radians(100))
    # ---- the yard on the front cells: paving from the door, the egg ledge on the left, the feed on the right
    door = Vector((C.x, C.y + 0.8, 0))

    def yard(x, y):
        if not in_footprint(CELLS, x, y, 0.28) or (x - C.x) ** 2 + (y - C.y) ** 2 < 0.9 ** 2:
            return False
        p = Vector((x, y, 0))
        for end in (FL + Vector((0.35, -0.1, 0)), FR + Vector((-0.35, -0.1, 0))):
            ab = end - door
            t = min(max((p - door).dot(ab) / ab.length_squared, 0.0), 1.0)
            if (door + ab * t - p).length < 0.36 + 0.3 * t:
                return True
        return False
    bm_flagstones(k["stone2:0.15:0.7"], rnd, yard, (FL.x - 1.2, C.y, FR.x + 1.2, FR.y + 1.2), T, size=0.27, keep=0.95)
    k.emit("Yard", col, root, vary=0.09)
    L = FL + Vector((-0.25, 0.12, 0))
    for dx, dy, r, sq in ((0.0, 0.0, 0.5, 0.55), (0.42, -0.3, 0.3, 0.8), (-0.4, -0.28, 0.32, 0.9), (0.1, -0.52, 0.27, 0.8), (-0.45, 0.35, 0.2, 0.9)):
        bm_boulder(k["stone_warm:0.15:0.9"], rnd, (L.x + dx, L.y + dy, T - 0.02), r, squash=(1, 1, sq), n=12)
    k.emit("Ledge", col, root, vary=0.07)
    nz = T + 0.4
    for i in range(14):
        a = math.radians(360 * i / 14 + rnd.uniform(-8, 8))
        a2 = a + math.radians(rnd.uniform(32, 46))
        bm_beam(k["wood:0.3:0.8"], L + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, nz + rnd.uniform(0, 0.05))),
                L + Vector((math.cos(a2) * 0.3, math.sin(a2) * 0.3, nz + 0.05)), 0.045, 0.045)
    bm_cyl(k["gold:0.3:0.6"], 0.27, 0.25, 0.05, (L.x, L.y, nz + 0.01), seg=9)
    for dx, dy, rz in ((0.0, 0.03, 0), (0.14, -0.05, 30), (-0.11, -0.08, -20)):
        bm_ellipsoid(k["gold:0.02:0.35"], (L.x + dx, L.y + dy, nz + 0.13), (0.085, 0.085, 0.12), (rz * 0.3, 0, rz), u=8, v=5)
    k.emit("Eggs", col, root, vary=0.06)
    R = FR + Vector((0.3, 0.1, 0))
    sx0, sx1, sy0, sy1 = R.x - 0.5, R.x + 0.5, R.y - 0.42, R.y + 0.42       # the feed shed: a lean-to, open to the yard
    for x, y, h in ((sx0, sy0, 0.62), (sx1, sy0, 0.62), (sx0, sy1, 1.0), (sx1, sy1, 1.0)):
        bm_box(k["wood_dark:0.2:0.8"], (0.1, 0.1, h), (x, y, T + h / 2))
    for x in (sx0, sx1):
        bm_beam(k["wood_dark:0.2:0.8"], (x, sy0 - 0.12, T + 0.6), (x, sy1 + 0.12, T + 1.04), 0.08, 0.08)
    bm_block_wall(k["stone_warm:0.2:0.8"], rnd, (sx0, sy1), (sx1, sy1), T, T + 0.45, th=0.14, course=0.15, block=0.3)
    k.emit("Shed", col, root, bevel=0.01, vary=0.07)
    bm_tile_slope(k["team!:0.1:0.7"], rnd, (sx0 - 0.12, sy0 - 0.16, T + 0.62), (sx1 + 0.12, sy0 - 0.16, T + 0.62),
                  (sx0 - 0.12, sy1 + 0.16, T + 1.1), (sx1 + 0.12, sy1 + 0.16, T + 1.1), rows=4, cols=4)
    k.emit("Shed_Roof", col, root, vary=0.08)
    bm_blob(k["gold:0.2:0.7"], rnd, (R.x + 0.12, R.y + 0.1, T + 0.2), 0.34, squash=(1.15, 0.9, 0.8), jitter=0.1, sub=2)   # hay
    k.emit("Hay", col, root)
    kk = [("hex/trough", (R.x - 0.75, R.y - 0.55, T), 60, 2.2), ("hex/bucket_water", (R.x - 0.3, R.y - 0.2, T), 0, 2.0),
          ("hex/sack", (R.x + 0.3, R.y - 0.3, T), 60, 2.0), ("hex/spear", (R.x - 0.52, R.y + 0.3, T + 0.02), 0, 2.2),
          ("forest/Bush_1_C_Color1", (L.x + 0.62, L.y + 0.42, T - 0.02), 0, 0.26), ("forest/Grass_1_B_Color1", (L.x - 0.7, L.y - 0.1, T - 0.02), 0, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    empty("Head", col, root, (C.x, C.y, PERCH), 0.5, "SINGLE_ARROW")
    return root


# ---- the gryphon, in the head's space (+Y forward), laid out at 1.0 with its wings spread
BODY = [(-0.64, 0.50, 0.13, 0.14), (-0.5, 0.52, 0.26, 0.26), (-0.24, 0.53, 0.3, 0.29), (0.04, 0.56, 0.3, 0.3),
        (0.26, 0.65, 0.32, 0.34), (0.42, 0.76, 0.26, 0.3)]
NECK = [(0, 0.34, 0.8), (0, 0.44, 0.96), (0, 0.5, 1.1)]
SKULL = [(0.4, 1.12, 0.15, 0.15), (0.54, 1.16, 0.18, 0.17), (0.68, 1.14, 0.16, 0.15), (0.78, 1.1, 0.1, 0.1)]
WR, WE, WT = Vector((0.24, 0.16, 0.9)), Vector((0.92, 0.1, 0.97)), Vector((1.72, -0.08, 0.93))   # wing root, elbow, tip
LEGS = {"FL": ((-0.17, 0.3, 0.52), (-0.19, 0.4, 0.05)), "FR": ((0.17, 0.3, 0.52), (0.19, 0.4, 0.05)),
        "BL": ((-0.2, -0.36, 0.46), (-0.22, -0.4, 0.05)), "BR": ((0.2, -0.36, 0.46), (0.22, -0.4, 0.05))}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, -0.5, 0.53), (0, 0.3, 0.62), "root"),
    "neck": ((0, 0.32, 0.78), (0, 0.5, 1.08), "body"),
    "head": ((0, 0.5, 1.1), (0, 0.8, 1.12), "neck"),
    "jaw": ((0, 0.72, 1.06), (0, 0.92, 1.0), "head"),
    "wing.L.1": ((-WR.x, WR.y, WR.z), (-WE.x, WE.y, WE.z), "body"),
    "wing.L.2": ((-WE.x, WE.y, WE.z), (-WT.x, WT.y, WT.z), "wing.L.1"),
    "wing.R.1": (tuple(WR), tuple(WE), "body"),
    "wing.R.2": (tuple(WE), tuple(WT), "wing.R.1"),
    "tail.1": ((0, -0.6, 0.5), (0, -0.9, 0.4), "body"),
    "tail.2": ((0, -0.9, 0.4), (0, -1.16, 0.36), "tail.1"),
    "tail.3": ((0, -1.16, 0.36), (0, -1.38, 0.44), "tail.2"),
}
for _n, (_a, _b) in LEGS.items():
    BONES["leg." + _n] = (_a, _b, "body")


def _ovals(rows, n=8, power=2.3):
    return [oval((0, y, z), (1, 0, 0), (0, 0, 1), rx, rz, n, power=power, phase=0.5) for y, z, rx, rz in rows]


def _wing(k, sx):
    """One wing's feathers, spread: long flight feathers behind the arm (dark), a shorter row of coverts over them."""
    r, e, t = (Vector((sx * v.x, v.y, v.z)) for v in (WR, WE, WT))
    inner, outer = k_inner[sx], k_outer[sx]
    back = Vector((0, -1, 0))
    out = Vector((sx, 0, 0))
    for i in range(5):                       # secondaries, on the inner arm
        u = (i + 0.5) / 5
        p = r.lerp(e, u)
        d = (back + out * 0.12 * u).normalized()
        bm_beam(inner["wood_dark:0.15:0.7"], p - Vector((0, 0, 0.012)), p + d * (0.62 + 0.14 * u) - Vector((0, 0, 0.05)), 0.19, 0.014, w1=0.1, h1=0.01)
        bm_beam(inner["wood:0.1:0.6"], p + Vector((0, 0, 0.012)), p + d * (0.34 + 0.06 * u), 0.2, 0.016, w1=0.13, h1=0.01)
    for i in range(7):                       # primaries, fanning from straight back to straight out at the tip
        u = (i + 0.5) / 7
        p = e.lerp(t, u)
        d = (back * (1.0 - 0.85 * u * u) + out * (0.25 + 0.95 * u)).normalized()
        bm_beam(outer["wood_dark:0.15:0.7"], p - Vector((0, 0, 0.012)), p + d * (0.82 - 0.26 * u) - Vector((0, 0, 0.06)), 0.17, 0.014, w1=0.07, h1=0.008)
        bm_beam(outer["wood:0.1:0.6"], p + Vector((0, 0, 0.012)), p + d * (0.36 - 0.08 * u), 0.18, 0.016, w1=0.1, h1=0.01)
    bm_tube(inner["sand:0.15:0.6"], [r, e], [0.085, 0.065], n=6)
    bm_tube(outer["sand:0.15:0.6"], [e, t], [0.065, 0.03], n=6)
    bm_ellipsoid(inner["sand:0.1:0.5"], tuple(r), (0.12, 0.14, 0.1), u=7, v=5)      # shoulder


k_inner, k_outer = {}, {}


def build_head():
    col = collection("Gryphon")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = make_rig(col, head, BONES, scale=GS)
    S = GS
    k = Kit()
    # ---- the lion's body, one loft; its belly paler
    bm_loft(k["sand:0.1:0.85"], _ovals(BODY))
    body = k.emit("Head_Body", col, rig=rig, bones=["body"], scale=S)[0]
    paint_faces(body, "cream", lambda c, n: n.z < -0.5, lo=0.3, hi=0.8)
    # ---- the eagle's neck and ruff: white, with a collar of feather points over the lion's shoulders
    bm_tube(k["white:0.05:0.55"], NECK, [0.27, 0.2, 0.16], n=8)
    for i in range(11):
        a = math.radians(-20 + 22 * i)
        base = Vector((math.cos(a) * 0.25, 0.36, 0.8 + math.sin(a) * 0.26))
        bm_crystal(k["white:0.0:0.5"], base, base + Vector((math.cos(a) * 0.1, -0.26, math.sin(a) * 0.1 - 0.04)), 0.075, n=4, shoulder=0.35)
    k.emit("Head_Neck", col, rig=rig, bones=["body", "neck"], scale=S)
    # ---- the head: skull, hooked beak, fierce brows, feather tufts
    bm_loft(k["white:0.02:0.5"], _ovals(SKULL))
    for sx in (-1, 1):
        bm_crystal(k["white:0.0:0.45"], (sx * 0.1, 0.46, 1.25), (sx * 0.16, 0.26, 1.42), 0.05, n=4, shoulder=0.3)
    bm_tube(k["orange:0.1:0.6"], [(0, 0.76, 1.11), (0, 0.9, 1.09), (0, 0.98, 1.02), (0, 0.985, 0.93)], [0.095, 0.08, 0.05, 0.0], n=6)
    for sx in (-1, 1):
        bm_box(k["gold:0.2:0.6"], (0.13, 0.06, 0.04), (sx * 0.11, 0.66, 1.235), (22, sx * 26, sx * -8))          # brow
        bm_ellipsoid(k["black:0.2:0.5"], (sx * 0.125, 0.69, 1.185), (0.032, 0.03, 0.034), u=6, v=4)
    k.emit("Head_Head", col, rig=rig, bone="head", scale=S)
    bm_tube(k["orange:0.3:0.75"], [(0, 0.74, 1.04), (0, 0.86, 1.02), (0, 0.93, 0.99)], [0.07, 0.05, 0.0], n=5)
    k.emit("Head_Jaw", col, rig=rig, bone="jaw", scale=S)
    # ---- legs: feathered eagle forelegs with golden talons, a lion's hind legs
    for name, (a, b) in LEGS.items():
        a, b = Vector(a), Vector(b)
        if name[0] == "F":
            bm_tube(k["white:0.1:0.6"], [a + Vector((0, 0, 0.1)), a, a.lerp(b, 0.5)], [0.1, 0.13, 0.07], n=6)
            bm_tube(k["gold:0.1:0.6"], [a.lerp(b, 0.45), b + Vector((0, 0, 0.04))], [0.05, 0.045], n=5)
            for i in range(4):
                ang = math.radians((-40, 0, 40, 180)[i])
                d = Vector((math.sin(ang), math.cos(ang), 0))
                p = b + Vector((0, 0, 0.03))
                bm_tube(k["gold:0.15:0.6"], [p, p + d * 0.13 + Vector((0, 0, 0.01))], [0.04, 0.03], n=4)
                bm_crystal(k["black:0.1:0.5"], p + d * 0.12 + Vector((0, 0, 0.012)), p + d * 0.22 + Vector((0, 0, -0.03)), 0.028, n=4, shoulder=0.3)
        else:
            knee = a.lerp(b, 0.5) + Vector((0, 0.1, 0))
            bm_tube(k["sand:0.25:0.9"], [a + Vector((0, 0, 0.08)), a, knee, b + Vector((0, 0, 0.05))], [0.12, 0.17, 0.11, 0.085], n=6)
            bm_loft(k["sand:0.5:0.95"], [oval((b.x, y, z), (1, 0, 0), (0, 0, 1), rx, rz, 6, power=2.8, phase=0.5)
                                         for y, z, rx, rz in ((b.y - 0.1, 0.06, 0.09, 0.055), (b.y + 0.06, 0.065, 0.11, 0.065), (b.y + 0.2, 0.05, 0.09, 0.045))])
        k.emit("Head_Leg" + name, col, rig=rig, bone="leg." + name, scale=S)
    # ---- the tail: one tube bending over three bones, a dark tuft
    bm_tube(k["sand:0.3:0.8"], [(0, -0.58, 0.5), (0, -0.9, 0.4), (0, -1.16, 0.36), (0, -1.34, 0.42)], [0.075, 0.05, 0.04, 0.035], n=6)
    bm_blob(k["wood_dark:0.2:0.7"], random.Random(5), (0, -1.42, 0.47), 0.1, squash=(0.8, 1.25, 0.9), jitter=0.12)
    k.emit("Head_Tail", col, rig=rig, bones=["tail.1", "tail.2", "tail.3"], scale=S)
    # ---- wings (bind pose: spread)
    for s, sx in (("R", 1), ("L", -1)):
        k_inner[sx], k_outer[sx] = Kit(), Kit()
        _wing(k, sx)
        k_inner[sx].emit("Head_Wing.%s.1" % s, col, rig=rig, bone="wing.%s.1" % s, scale=S)
        k_outer[sx].emit("Head_Wing.%s.2" % s, col, rig=rig, bone="wing.%s.2" % s, scale=S)
    # ---- the saddle cloth in the team's color, gold-edged, with the girth under the belly
    def crescent(y, grow, a0, a1, n=6):
        for a, b in zip(BODY, BODY[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / (b[0] - a[0])
                z, rx, rz = (a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
        o, i_ = [], []
        for q in range(n + 1):
            ang = math.radians(a0 + (a1 - a0) * q / n)
            o.append(Vector((math.cos(ang) * (rx + grow), y, z + math.sin(ang) * (rz + grow))))
            i_.append(Vector((math.cos(ang) * (rx - 0.01), y, z + math.sin(ang) * (rz - 0.01))))
        return o + list(reversed(i_))
    bm_loft(k["team!:0.1:0.6"], [crescent(y, 0.022, 20, 160) for y in (-0.3, -0.08, 0.12)])
    for y in (-0.33, 0.12):
        bm_loft(k["gold:0.1:0.5"], [crescent(y + d, 0.032, 18, 162) for d in (0.0, 0.035)])
    bm_loft(k["wood_dark:0.3:0.7"], [crescent(y, 0.012, 160, 380, n=8) for y in (-0.13, -0.05)])
    bm_box(k["wood_red:0.2:0.7"], (0.22, 0.26, 0.05), (0, -0.1, 0.875))                                          # the saddle
    bm_box(k["wood_red:0.2:0.7"], (0.2, 0.05, 0.1), (0, -0.25, 0.92), (-12, 0, 0))
    k.emit("Head_Saddle", col, rig=rig, bone="body", scale=S, bevel=0.01)
    empty("Muzzle", col, head, (0, 0.95 * S, 0.9 * S), 0.2, "SPHERE")
    crew = empty("Crew", col, head, (0, -0.12 * S, 0.72 * S), 0.3, "SINGLE_ARROW")
    return rig


IDLE_LEN = 80
FLY_LEN = 16
FIRE_LEN = 14
FOLD = {"yaw": 76.0, "twist": 74.0, "bend": 16.0, "short": 0.72}   # how the wings fold down the flanks when it's perched


def pose(rig, fold=1.0, flap=0.0, flap2=0.0, look=0.0, nod=0.0, breathe=0.0, tail=0.0, lift=0.0, beak=0.0, reach=0.0,
         tuck=0.0, pitch=0.0, bob=0.0):
    """fold: 1 wings folded .. 0 spread; flap / flap2: the inner / outer wing's beat (degrees, up is +); tuck: legs
    drawn up for flight; reach: forelegs thrust forward for the strike; pitch: the body's nose-up tilt."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["body"].rotation_quaternion = q(pb["body"], (1, 0, 0), pitch)
    pb["body"].location = arm_space_loc(pb["body"], (0, 0, bob))
    pb["body"].scale = (1 + breathe,) * 3
    pb["neck"].rotation_quaternion = q(pb["neck"], (0, 0, 1), look * 0.4) @ q(pb["neck"], (1, 0, 0), -pitch * 0.6 + lift)
    pb["head"].rotation_quaternion = q(pb["head"], (0, 0, 1), look * 0.6) @ q(pb["head"], (1, 0, 0), nod)
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -beak)
    for s, sg in (("R", 1), ("L", -1)):
        b1, b2 = pb["wing.%s.1" % s], pb["wing.%s.2" % s]
        # folded: the arm swings back along the flank and rolls over, so the feathers hang down it like a cloak
        b1.rotation_quaternion = q(b1, (0, 0, 1), -sg * FOLD["yaw"] * fold) @ q(b1, (1, 0, 0), FOLD["twist"] * fold) @ q(b1, (0, 1, 0), -sg * flap)
        b2.rotation_quaternion = q(b2, (0, 0, 1), -sg * FOLD["bend"] * fold) @ q(b2, (0, 1, 0), -sg * flap2)
        b2.scale = (1.0 - (1.0 - FOLD["short"]) * fold,) * 3
    for i, b in enumerate(("tail.1", "tail.2", "tail.3")):
        pb[b].rotation_quaternion = q(pb[b], (0, 0, 1), tail * (1.0 + 0.4 * i)) @ q(pb[b], (1, 0, 0), -tuck * 8)
    for s in ("L", "R"):
        pb["leg.F" + s].rotation_quaternion = q(pb["leg.F" + s], (1, 0, 0), tuck * 62 - reach * 118)
        pb["leg.B" + s].rotation_quaternion = q(pb["leg.B" + s], (1, 0, 0), tuck * 70 - reach * 20)


def _fly(t):
    """The wingbeat at phase t (0..1): the inner wing leads, the outer lags; the body rides the beat."""
    ph = 2 * math.pi * t
    return dict(fold=0.0, flap=30 * math.sin(ph) + 6, flap2=34 * math.sin(ph - 0.9), tuck=1.0, pitch=-4 + 3 * math.sin(ph - 0.5),
                bob=-0.05 * math.sin(ph), tail=5 * math.sin(ph), lift=6.0)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        ruffle = max(0.0, math.sin(ph * 2 - 1.0)) ** 6
        pose(rig, fold=1.0 - 0.3 * ruffle, flap=14 * ruffle, flap2=10 * ruffle, look=30 * math.sin(ph) * (0.5 + 0.5 * math.sin(ph * 0.5)),
             nod=4 * math.sin(ph * 2), breathe=0.02 * math.sin(ph * 3), tail=14 * math.sin(ph + 0.6))
        key_pose(rig, f)
    new_action(rig, "fly", FLY_LEN)
    for f in range(FLY_LEN + 1):
        pose(rig, **_fly(f / FLY_LEN))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # out of the wingbeat: wings flare up and back to brake, talons thrust forward (the blow: frame 4), then back to the beat
        k = smooth(f / 3.0) * (1 - smooth((f - 6) / 7.0))
        p = _fly(0.0)
        p.update(flap=p["flap"] + 34 * k, flap2=p["flap2"] + 22 * k, reach=k, tuck=1.0 - 0.2 * k, pitch=p["pitch"] + 22 * k,
                 beak=30 * k, nod=-14 * k)
        pose(rig, **p)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.5), "dist": 10.0, "yaw": 150, "pitch": 20, "anim_target": (BACK.x, BACK.y, PERCH + 0.9), "anim_dist": 6.5,
           "frames": [("idle", 0), ("fly", 2), ("fly", 10), ("fire", 4), ("idle", 30)],
           "extra": [{"yaw": 135, "pitch": 14, "dist": 4.6, "target": (BACK.x, BACK.y + 0.2, PERCH + 0.9)},
                     {"yaw": 180, "pitch": 30, "dist": 6.0, "target": (0, FR.y - 0.2, 0.6)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
