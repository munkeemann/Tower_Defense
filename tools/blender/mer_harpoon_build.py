"""Builds the Coral Harpooner (footprint "line3": [0,0] front, [0,1] middle, [0,2] back; a 60 degree arc), a Tide
tower: barbed harpoons pierce a whole line and slow what they hit.

    python tools/blender/build.py mer_harpoon --out <preview dir>

One pier, from the shore out over a tidal channel. Back hex: the shore, and the harpooners' store under a giant scallop
shell (its rim in the team's color), with a ramp up onto the jetty. Middle hex: the jetty of driftwood planks on posts,
running through the ribs of a whale; a rack of spare harpoons on one side, a net drying on a frame on the other. Front
hex: the round pier head, and on it the launcher (the Head: it turns to aim): a whale-vertebra turntable, a driftwood
stock slung between two ribs, bow limbs of whale rib grown over with red coral, a barbed harpoon with a glowing head in
the trough (the Muzzle is its tip), a quiver of spares, a pennant; and the merfolk warrior who works it, reared up on
his coiled tail behind the stock: shell breastplate, scale skirt, a sash in the team's color, a helm with a fan crest.
Clips: idle (he breathes and scans the water, his tail slithers, the pennant flies), fire (the string snaps forward and
the harpoon is gone; the stock kicks), reload (he takes a harpoon from the quiver, lays it in the trough and hauls the
string back: it ends on the idle's first frame; fire ends with the launcher spent, where reload begins).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

TID = "mer_harpoon"
CELLS = [(0, 0), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
MI = hex_to_world(0, 1, MID)
B = hex_to_world(0, 2, MID)
TOP = 0.34
ZS = TOP + 0.085                # the sand
W = TOP + 0.03                  # the water
DECK = TOP + 0.42               # the top of the pier's planks
PIVOT = Vector((0.0, F.y + 0.2, DECK))
PLAT_R = 0.86
ICE = "glow:0.35,0.9,1.0,0.8"
WOOD = "wood:0.2:0.85"
BONE = "cream:0.12:0.9"


def hwf(y):
    """Half the footprint's width at y."""
    return 1.2 - 0.5774 * min(abs(y - c.y) for c in (F, MI, B))


def build_base():
    col = collection("Mer_harpoon")
    root = empty("Mer_harpoon", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(41)
    k = Kit()
    # ---- the ground: a sand flat over the footprint, the channel cut into it from the shore on the back hex to the front
    flat = tb_shore(CELLS, 0.2, rnd, step=0.3, jitter=0.03, rounds=2)
    y0, y1 = B.y + 0.56, F.y + 0.62
    ys = [y0 + (y1 - y0) * i / 30.0 for i in range(31)]
    water = [Vector((hwf(y) - 0.42, y, 0)) for y in ys] + [Vector((-(hwf(y) - 0.42), y, 0)) for y in reversed(ys)]
    water = tb_wobble(tb_smooth(tb_resample(water, 0.25), 2), rnd, 0.015)
    bm = bmesh.new()
    tb_plate(bm, flat, [water], ZS, z_skirt=T - 0.02, flare=0.07, z_hole=T, hole_flare=0.05)
    tb_shore_obj("Flat_Sand", bm, col, root, top=0.3)
    deep = [tb_blob((c.x, c.y + dy), 0.5, 0.56, n=12, rnd=rnd, jitter=0.06) for c, dy in ((F, -0.05), (MI, 0.0))]
    bm = bmesh.new()
    tb_plate(bm, tb_offset(water, 0.04), deep, W)
    tb_sea_obj("Channel_0", bm, col, root, top=0.48)
    bm = bmesh.new()
    for loop in deep:
        tb_plate(bm, loop, [], W)
    tb_sea_obj("Channel_1", bm, col, root, top=0.76)
    bm = bmesh.new()
    keep = tb_offset(flat, -0.05)
    for c, a, n, ln in (((-0.72, B.y + 0.35), 12, 3, 0.6), ((0.7, B.y - 0.1), -10, 2, 0.5), ((0.0, B.y + 0.62), 4, 2, 0.6)):
        tb_ripples(bm, c, a, n, ln, ZS - 0.006, within=keep, avoid=[tb_offset(water, 0.06)])
    tb_shore_obj("Flat_Ripples", bm, col, root, top=0.1, side=(0.15, 0.45))
    # ---- the jetty: planks on stringers and posts from the shore to the round pier head
    ya, yb = B.y + 0.58, F.y - PLAT_R + 0.1
    bm_planks(k[WOOD], rnd, (-0.37, ya, DECK), (0.74, 0, 0), (0, yb - ya, 0), 19, th=0.05)
    bm_planks(k[WOOD], rnd, (-0.37, ya - 0.52, ZS + 0.03), (0.74, 0, 0), (0, 0.52, DECK - ZS - 0.03), 4, th=0.05)       # the ramp up from the sand
    for i in range(12):                                                                                                  # the pier head, round
        y = F.y - PLAT_R + (i + 0.5) * 2 * PLAT_R / 12.0
        half = math.sqrt(max(PLAT_R ** 2 - (y - F.y) ** 2, 0.0)) + rnd.uniform(-0.015, 0.015)
        bm_box(k[WOOD], (2 * half, 2 * PLAT_R / 12.0 - 0.012, 0.05), (rnd.uniform(-0.01, 0.01), y, DECK - 0.025 + rnd.uniform(-0.005, 0.005)))
    bm_planks(k[WOOD], rnd, (-0.88, MI.y - 0.3, DECK), (0.52, 0, 0), (0, 0.72, 0), 5, th=0.05)                             # a landing for the rack
    k.emit("Pier_Deck", col, root, vary=0.09, seed=3, bevel=0.008)
    for sx in (-1, 1):
        bm_beam(k["wood_dark:0.25:0.9"], (sx * 0.27, ya, DECK - 0.1), (sx * 0.27, yb, DECK - 0.1), 0.08, 0.09)
    for a in range(0, 360, 60):
        p = Vector((math.cos(math.radians(a + 30)) * (PLAT_R - 0.06), F.y + math.sin(math.radians(a + 30)) * (PLAT_R - 0.06), 0))
        tb_post(k["wood_dark:0.25:0.9"], rnd, (p.x, p.y, T), DECK - T + 0.14, r=0.075, lean=(rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02)))
    ring(k["wood_dark:0.25:0.9"], (0, F.y, 0), PLAT_R - 0.02, PLAT_R - 0.14, DECK - 0.13, DECK - 0.05, seg=12)
    for y in (ya + 0.12, MI.y - 0.52, MI.y + 0.5, yb - 0.1):
        for sx in (-1, 1):
            tb_post(k["wood_dark:0.25:0.9"], rnd, (sx * 0.41, y, T), DECK - T + 0.13, r=0.07, lean=(rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02)))
    for sx, y in ((-1, MI.y - 0.26), (-1, MI.y + 0.38)):
        tb_post(k["wood_dark:0.25:0.9"], rnd, (sx * 0.88, y, T), DECK - T + 0.02, r=0.06)
    k.emit("Pier_Frame", col, root, vary=0.06, seed=5)
    # ---- it runs through the ribs of a whale: three pairs standing in the shallows either side
    for y, h in ((MI.y - 0.86, 1.5), (MI.y - 0.12, 1.78), (MI.y + 0.66, 1.56)):
        for sx in (-1, 1):
            x = sx * min(0.58, hwf(y) - 0.3)
            tb_rib(k[BONE], (x, y, T + 0.02), (-sx, 0.0), abs(x) - 0.16, h, r0=0.085, r1=0.036, sink=0.04)
    k.emit("Whale_Ribs", col, root, vary=0.05)
    # ---- the rack of spare harpoons on the left
    rx = -0.82
    for y in (MI.y - 0.24, MI.y + 0.36):
        tb_post(k["wood_dark:0.25:0.9"], rnd, (rx, y, DECK - 0.02), 0.95, r=0.05, taper=0.85)
    for z in (0.32, 0.84):
        bm_beam(k["wood:0.3:0.85"], (rx, MI.y - 0.3, DECK + z), (rx, MI.y + 0.42, DECK + z), 0.05, 0.06)
    for i in range(4):
        y = MI.y - 0.15 + 0.14 * i
        tb_harpoon(k, (rx + 0.2, y, DECK + 0.02), (rx - 0.04, y + 0.01 * i, DECK + 1.22 + 0.05 * (i % 2)), r=0.026, ribbon="team!:0.1:0.6")
    k.emit("Rack", col, root)
    # ---- a net drying on a frame on the right, cork floats along its foot, two fish hung up by it
    p00, p10, p01, p11 = Vector((0.5, MI.y + 0.12, DECK + 1.02)), Vector((0.94, MI.y + 0.1, DECK + 1.0)), Vector((0.5, MI.y - 0.42, DECK + 0.14)), Vector((0.76, MI.y - 0.42, DECK + 0.12))
    for p in (p00, p10, p01, p11):
        tb_post(k["wood_dark:0.25:0.9"], rnd, (p.x, p.y, T), p.z - T + 0.1, r=0.05, taper=0.8)
    P = tb_net_quad(k["sand:0.2:0.7"], p00, p10, p01, p11, cols=4, rows=4, sag=0.1)
    for i in range(5):
        q = P(i / 4.0, 1.0)
        bm_ellipsoid(k["orange:0.1:0.6" if i % 2 else "cream:0.1:0.6"], (q.x, q.y, q.z - 0.02), (0.05, 0.05, 0.04), u=6, v=4)
    for u, key in ((0.3, "sky:0.2:0.8"), (0.72, "salmon:0.2:0.8")):
        q = p00.lerp(p10, u) + Vector((0, 0.03, -0.04))
        bm_tube(k[key], [q, q + Vector((0, 0, -0.1)), q + Vector((0, 0.01, -0.24)), q + Vector((0, 0, -0.32))], [0.012, 0.05, 0.04, 0.012], n=5, squash=0.5, up=(0, 1, 0))
        tb_slab(k[key], [q + Vector((0, 0, -0.3)), q + Vector((-0.05, 0, -0.4)), q + Vector((0.05, 0, -0.4))], Vector((0, 0.014, 0)))
    k.emit("Net", col, root)
    # ---- the store on the shore: plank walls between four posts, kegs inside, the great shell for a roof
    hc = Vector((0.0, B.y - 0.36, 0))
    for sx in (-1, 1):
        for dy, h in ((-0.42, 0.66), (0.42, 0.86)):
            tb_post(k["wood_dark:0.25:0.9"], rnd, (hc.x + sx * 0.56, hc.y + dy, ZS - 0.03), h, r=0.065)
    bm_planks(k[WOOD], rnd, (hc.x - 0.56, hc.y - 0.42, ZS), (0, 0, 0.58), (1.12, 0, 0), 7, th=0.05)
    for sx in (-1, 1):
        bm_planks(k[WOOD], rnd, (hc.x + sx * 0.56, hc.y - 0.42, ZS), (0, 0, 0.58), (0, 0.84, 0), 5, th=0.05)
    bm_box(k["wood_dark:0.4:0.95"], (1.04, 0.78, 0.04), (hc.x, hc.y, ZS + 0.02))
    k.emit("Store", col, root, vary=0.09, seed=8, bevel=0.008)
    tb_keg(k, (hc.x - 0.26, hc.y - 0.1, ZS + 0.22), (0, 0, 1), length=0.4, r=0.16)
    tb_keg(k, (hc.x + 0.12, hc.y - 0.16, ZS + 0.2), (0, 0, 1), length=0.36, r=0.15)
    tb_keg(k, (hc.x + 0.3, hc.y + 0.2, ZS + 0.15), (1, 0.3, 0), length=0.36, r=0.14)
    tb_keg(k, (-0.8, B.y + 0.12, ZS + 0.13), (0.4, 1, 0), length=0.34, r=0.13)
    for i in range(4):
        ring(k["sand:0.2:0.7"], (0.78, B.y + 0.2, 0), 0.2 - 0.02 * i, 0.1, ZS + 0.035 * i, ZS + 0.035 * i + 0.04, seg=10)
    k.emit("Store_Goods", col, root)
    sc = (hc.x, hc.y - 0.6, ZS + 0.6)
    tb_scallop(k["cream:0.02:0.65"], sc, 1.24, yaw=0, tilt=13, ribs=9, dome=0.28, th=0.05, rows=5, spread=62)
    tb_scallop(k["team!:0.1:0.6"], sc, 1.24, yaw=0, tilt=13, ribs=9, dome=0.28, th=0.05, rows=1, spread=62, t0=0.84, t1=1.02, lift=0.016)
    tb_slab(k["cream:0.25:0.9"], [(sc[0] - 0.34, sc[1] - 0.02, sc[2] - 0.01), (sc[0] + 0.34, sc[1] - 0.02, sc[2] - 0.01), (sc[0] + 0.2, sc[1] + 0.16, sc[2] + 0.05),
                                  (sc[0] - 0.2, sc[1] + 0.16, sc[2] + 0.05)], Vector((0, 0, 0.05)))
    k.emit("Store_Shell", col, root)
    # ---- the shore's own life: rocks, coral, weed, a starfish
    for x, y, r in ((-0.86, F.y - 0.42, 0.17), (0.9, F.y + 0.2, 0.14), (0.62, B.y + 0.74, 0.13), (-0.42, F.y + 0.92, 0.12)):
        bm_boulder(k["stone2:0.15:0.9"], rnd, (x, y, ZS - 0.04), r, squash=(1.1, 0.95, 0.75), n=10)
    k.emit("Rocks", col, root, vary=0.08)
    tb_coral(k["salmon:0.05:0.75"], rnd, (0.9, F.y - 0.25, ZS - 0.03), h=0.5, r=0.055, depth=2)
    tb_coral(k["orange:0.05:0.7"], rnd, (-0.92, F.y + 0.12, ZS - 0.03), h=0.42, r=0.05, depth=2)
    tb_tube_coral(k, rnd, (0.84, MI.y + 0.62, ZS - 0.02), n=3, key="salmon:0.1:0.7")
    for x, y in ((0.52, F.y - 0.6), (-0.62, MI.y - 0.05), (0.3, MI.y + 0.9), (-0.5, F.y + 0.55)):
        tb_weed(k["teal:0.25:0.9"], rnd, (x, y, W - 0.02), h=0.4, n=3)
    tb_starfish(k["orange:0.15:0.7"], (0.86, B.y - 0.42, ZS + 0.005), r=0.14, yaw=15, h=0.04)
    k.emit("Shore_Life", col, root)
    empty("Head", col, root, tuple(PIVOT), 0.5, "SINGLE_ARROW")
    return root


# ---- the launcher and its crew, in the head's space (+Y forward, the deck at z = 0)
NOCK = Vector((0, -0.2, 0.76))
TIP = {-1: Vector((-0.78, 0.14, 0.72)), 1: Vector((0.78, 0.14, 0.72))}
BOLT0, BOLT1 = Vector((0, -0.22, 0.795)), Vector((0, 0.95, 0.845))
QUIVER = Vector((0.6, -0.16, 0.0))
GRIP = {-1: Vector((-0.2, -0.5, 0.63)), 1: Vector((0.2, -0.5, 0.63))}
SPEC = dict(at=(0, -0.6, 0.5), scale=1.2, tail_bones=5, tail_r=(0.168, 0.05),
            tail=[(0, 0, 0.04), (0, -0.05, -0.18), (-0.03, -0.15, -0.31), (-0.16, -0.28, -0.33), (-0.34, -0.27, -0.345), (-0.43, -0.1, -0.355), (-0.36, 0.06, -0.37)],
            skin="tan:0.05:0.5", tail_key="teal:0.3:1.0", belly="cream", fin_key="orange:0.1:0.65", brow="wood_dark:0.3:0.8")
MER_M = tb_mer_matrix(SPEC)
MER_I = MER_M.inverted()


def _arm(sx, target, hint):
    """An arm's shape (shoulder, elbow, the end of the hand; the head's space) with its hand at `target`. Also (elbow,
    wrist) in the figure's own space."""
    sh = Vector((sx * MER_SHOULDER[0], MER_SHOULDER[1], MER_SHOULDER[2]))
    el, wr = tb_ik(sh, MER_I @ Vector(target), hint=hint)
    end = wr + (wr - el).normalized() * 0.09
    return [MER_M @ sh, MER_M @ el, MER_M @ end], (el, wr)


ARM_REST = {s: _arm(sx, GRIP[sx], (sx * 0.9, -0.5, -0.2)) for sx, s in ((-1, "L"), (1, "R"))}
SPEC["arms"] = {s: ARM_REST[s][1] for s in ("L", "R")}
ARM_REACH = _arm(1, QUIVER + Vector((-0.02, -0.02, 0.9)), (0.8, -0.6, 0.3))[0]
ARM_SET = _arm(1, Vector((0.1, -0.16, 0.9)), (0.9, -0.4, 0.2))[0]


def build_head():
    col = collection("Mer_harpoon")
    head = bpy.data.objects["Head"]
    rnd = random.Random(7)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "stock": ((0, 0.02, 0.66), (0, 0.6, 0.7), "root"),
             "slide": (tuple(NOCK), tuple(NOCK + Vector((0, 0.15, 0))), "stock"),
             "bolt": (tuple(BOLT0), tuple(BOLT0.lerp(BOLT1, 0.4)), "stock")}
    for sx, s in ((-1, "L"), (1, "R")):
        bones["bow." + s] = ((sx * 0.07, 0.44, 0.71), tuple(TIP[sx]), "stock")
    flag_top = Vector((-0.4, -0.02, 1.36))
    flag_bones(bones, "flag", flag_top, (0.25, -1, 0), 0.56, segs=3, parent="root")
    tb_mer_bones(bones, SPEC, parent="root")
    rig = make_rig(col, head, bones)
    k = Kit()
    rk = RigidKit().to("root")
    # ---- the turntable: a whale's vertebra, iron-bound; two ribs rising from it to carry the stock; the quiver; the pennant's pole
    bm_cyl(rk["wood_red:0.3:0.85"], 0.46, 0.43, 0.09, (0, 0, 0.045), seg=10)
    ring(rk["iron:0.2:0.75"], (0, 0, 0), 0.475, 0.4, 0.025, 0.07, seg=10)
    for a in range(18, 360, 36):
        tb_disc(rk["iron:0.1:0.6"], (math.cos(math.radians(a)) * 0.36, math.sin(math.radians(a)) * 0.36, 0.088), (0, 0, 1), 0.03, 0.02)
    for sx in (-1, 1):
        pts = tb_bezier((sx * 0.36, 0.02, 0.05), (sx * 0.42, 0.02, 0.42), (sx * 0.27, 0.02, 0.62), (sx * 0.1, 0.02, 0.645), 6)
        bm_tube(rk[BONE], pts, [0.08, 0.075, 0.07, 0.064, 0.058, 0.055], n=6, up=(0, 1, 0), squash=1.35)
    bm_tube(rk["iron:0.2:0.75"], [(-0.17, 0.02, 0.645), (0.17, 0.02, 0.645)], 0.04, n=6)
    bm_cyl(rk["wood:0.3:0.9"], 0.135, 0.155, 0.42, (QUIVER.x, QUIVER.y, 0.31), seg=8)
    for z in (0.16, 0.44):
        ring(rk["iron:0.2:0.75"], (QUIVER.x, QUIVER.y, 0), 0.165, 0.12, z, z + 0.04, seg=8)
    for dx, dy in ((0.05, 0.04), (-0.04, 0.05), (0.0, -0.05)):
        tb_harpoon(rk, (QUIVER.x + dx, QUIVER.y + dy, 0.14), (QUIVER.x + dx * 2.6, QUIVER.y + dy * 2.6, 1.14), r=0.024, head_len=0.2)
    bm_tube(rk["wood_dark:0.2:0.85"], [(-0.4, 0.02, 0.3), flag_top + Vector((0, 0, 0.06))], [0.032, 0.022], n=5)
    bm_tube(rk["sand:0.3:0.7"], [(-0.42, 0.02, 0.36), (-0.36, 0.02, 0.44)], 0.05, n=5)
    # ---- the stock: a driftwood beam with a trough, iron-strapped; the block that holds the bow; the crossbar he steers by
    rk.to("stock")
    bm_beam(rk["wood_dark:0.2:0.85"], (0, -0.52, 0.655), (0, 0.62, 0.7), 0.17, 0.15)
    bm_beam(rk["wood:0.3:0.8"], (0, -0.3, 0.735), (0, 0.64, 0.776), 0.075, 0.03)
    bm_box(rk[BONE], (0.3, 0.17, 0.18), (0, 0.45, 0.712))
    for y in (-0.3, 0.14):
        bm_box(rk["iron:0.2:0.75"], (0.19, 0.05, 0.165), (0, y, 0.668 + 0.04 * (y + 0.52)))
    bm_tube(rk["wood:0.2:0.75"], [tuple(GRIP[-1] + Vector((-0.06, 0, 0))), tuple(GRIP[1] + Vector((0.06, 0, 0)))], 0.034, n=6)
    bm_beam(rk["iron:0.2:0.75"], (0.06, -0.4, 0.6), (0.06, -0.46, 0.5), 0.03, 0.03)
    for sx in (-1, 1):
        tb_coral(rk["red:0.1:0.75"], rnd, (sx * 0.1, 0.46, 0.79), h=0.3, r=0.035, depth=1, direction=(sx * 0.35, 0.1, 1.0))
    # ---- the bow: two limbs of whale rib grown over with red coral; the string; the claw that holds it; the harpoon
    for sx, s in ((-1, "L"), (1, "R")):
        rk.to("bow." + s)
        pts = tb_bezier((sx * 0.08, 0.45, 0.715), (sx * 0.36, 0.53, 0.72), (sx * 0.63, 0.4, 0.72), tuple(TIP[sx]), 7)
        bm_tube(rk[BONE], pts, [0.09, 0.085, 0.078, 0.068, 0.058, 0.048, 0.038], n=6, squash=0.62)
        tb_coral(rk["red:0.1:0.75"], rnd, pts[3] + Vector((0, 0.02, 0.03)), h=0.3, r=0.034, depth=1, direction=(sx * 0.3, 0.5, 0.8))
        tb_coral(rk["red:0.1:0.75"], rnd, pts[5] + Vector((0, 0.0, 0.02)), h=0.2, r=0.028, depth=1, direction=(sx * 0.6, 0.2, 0.7))
        bm_tube(rk["red:0.2:0.8"], [pts[6] - (pts[6] - pts[5]).normalized() * 0.04, pts[6] + (pts[6] - pts[5]).normalized() * 0.05], 0.05, n=5)
    rk.to("slide")
    bm_box(rk["iron:0.2:0.75"], (0.1, 0.09, 0.06), tuple(NOCK + Vector((0, 0.01, 0.005))))
    rk.to("bolt")
    tb_harpoon(rk, BOLT0, BOLT1, r=0.036, head=ICE, head_len=0.34, ribbon="team!:0.1:0.6")
    rk.emit("Head_Launcher", col, rig, bevel=0.0)
    for sx, s in ((-1, "L"), (1, "R")):
        bm_tube(k["sand:0.2:0.65"], [tuple(TIP[sx]), tuple(NOCK)], 0.016, n=4)
        k.emit("Head_String" + s, col, rig=rig, bones=["bow." + s, "slide"])
    flag_part("Head_Flag", col, rig, "flag", flag_top, (0.25, -1, 0), 0.56, 0.3, segs=3)
    # ---- the warrior
    mer = tb_merfolk(col, rig, SPEC, name="Head_Mer")
    part = Kit()
    rk.to("head")                                   # the helm: a gold cap with a brim and a nose guard, a fan crest across it
    bm_loft(part["gold:0.1:0.7"], [oval((0, 0, z), (1, 0, 0), (0, 1, 0), hw, hd, 8, power=2.3, phase=0.5) for z, hw, hd in
                                   ((0.7, 0.2, 0.192), (0.77, 0.19, 0.182), (0.84, 0.155, 0.148), (0.878, 0.075, 0.07))])
    bm_loft(part["gold:0.3:0.9"], [oval((0, 0, z), (1, 0, 0), (0, 1, 0), 0.214, 0.206, 8, power=2.3, phase=0.5) for z in (0.69, 0.725)])
    bm_box(part["gold:0.3:0.9"], (0.04, 0.03, 0.13), (0, 0.19, 0.665))
    tb_fin(part["team!:0.1:0.6"], (-0.17, 0, 0.8), (0.17, 0, 0.8), [(-0.34, -0.02, 0.92), (-0.2, -0.03, 1.06), (0, -0.03, 1.12), (0.2, -0.03, 1.06), (0.34, -0.02, 0.92)],
           th=0.035, notch=0.6)
    tb_merge(rk, part, MER_M)
    rk.to("chest")                                  # a scallop for a breastplate, smaller shells on the shoulders
    tb_scallop(part["cream:0.05:0.7"], (0, 0.118, 0.125), 0.29, yaw=180, tilt=90, ribs=6, dome=0.26, th=0.03, rows=3, spread=50)
    tb_scallop(part["salmon:0.0:0.5"], (0, 0.118, 0.125), 0.29, yaw=180, tilt=90, ribs=6, dome=0.26, th=0.03, rows=1, spread=50, t0=0.82, t1=1.02, lift=0.012)
    for sx in (-1, 1):
        tb_scallop(part["salmon:0.0:0.55"], (sx * 0.15, 0.0, 0.43), 0.17, yaw=-sx * 90, tilt=-12, ribs=5, dome=0.45, th=0.025, rows=2, spread=60)
    tb_merge(rk, part, MER_M)
    rk.to("hips")                                   # a gold belt, a skirt of scales over the top of his tail
    tb_mer_band(part["gold:0.1:0.7"], lambda a: -0.015, 0.065, grow=0.022)
    bm_tile_cone(part["teal:0.45:1.0"], rnd, (0, 0, 0), 0.24, -0.2, 0.21, rows=2, n=9, th=0.03, lap=0.3, flare=0.02, top=0.168)
    tb_merge(rk, part, MER_M)
    rk.emit("Head_Mer_Gear", col, rig, vary=0.06)
    tb_mer_band(part["team!:0.1:0.6"], lambda a: 0.205 - 0.15 * math.cos(math.radians(a)), 0.08)
    tb_merge(k, part, MER_M)
    k.emit("Head_Mer_Sash", col, rig=rig, bones=["hips", "chest"])
    empty("Muzzle", col, head, tuple(BOLT1), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 12
RELOAD_LEN = 26
_T = {}


def pose(rig, ph=0.0, spent=0.0, gone=0.0, fly=0.0, kick=0.0, reach=0.0, set_=0.0, carry=None, haul=0.0, recoil=0.0):
    """spent: the string let go (0 drawn .. 1 forward); gone: the harpoon out of sight; fly: how far it has shot along
    the trough; kick: the stock's recoil; reach / set_: his right arm to the quiver / to the trough; carry: None, or
    0 .. 1 the new harpoon on its way from the quiver to the trough; haul: his heave on the string; recoil: his flinch."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    if not _T:
        rest = ARM_REST["R"][0]
        _T["reach"], _T["set"] = tb_turns(rest, ARM_REACH), tb_turns(rest, ARM_SET)
        d0 = (BOLT1 - BOLT0).normalized()
        d1 = Vector((0.12, 0.1, 1.0)).normalized()
        _T["stand"] = d0.rotation_difference(d1)
    breathe = math.sin(ph * 2)
    # the launcher
    pb["stock"].rotation_quaternion = q(pb["stock"], (1, 0, 0), 0.8 * math.sin(ph) + 5.0 * kick - 2.5 * haul)
    pb["stock"].location = arm_space_loc(pb["stock"], (0, -0.05 * kick, 0))
    pb["slide"].location = arm_space_loc(pb["slide"], (0, 0.44 * spent, 0))
    for sx, s in ((-1, "L"), (1, "R")):
        pb["bow." + s].rotation_quaternion = q(pb["bow." + s], (0, 0, 1), sx * 15.0 * spent)
    b = pb["bolt"]
    if carry is not None:
        t = smooth(carry)
        b.rotation_quaternion = (lambda r: r.inverted() @ _T["stand"].slerp(Quaternion(), t) @ r)(b.bone.matrix_local.to_quaternion())
        start = QUIVER + Vector((0, 0, 0.2)) - BOLT0
        b.location = arm_space_loc(b, tuple(start.lerp(Vector((0, 0, 0)), t) + Vector((0, 0, 0.3 * math.sin(math.pi * t)))))
    else:
        b.location = arm_space_loc(b, (0, 1.7 * fly, 0.06 * fly))
    g = max(0.01, 1.0 - gone)
    b.scale = (g, g, g)
    wave_flag(rig, "flag", ph / (2 * math.pi) * 3, amp=1.0 + 0.6 * kick, segs=3)
    # the warrior
    pb["hips"].rotation_quaternion = q(pb["hips"], (0, 1, 0), 1.6 * math.sin(ph)) @ q(pb["hips"], (1, 0, 0), -3.0 + 7.0 * recoil + 9.0 * haul - 4.0 * set_)
    pb["chest"].scale = (1 + 0.018 * breathe,) * 3
    pb["chest"].rotation_quaternion = q(pb["chest"], (0, 0, 1), -14.0 * reach - 5.0 * set_) @ q(pb["chest"], (1, 0, 0), 4.0 * recoil + 5.0 * haul)
    look = 20 * math.sin(ph) * (0.5 + 0.5 * math.sin(ph * 0.5 + 1.0)) * (1 - max(reach, set_, haul))
    pb["head"].rotation_quaternion = q(pb["head"], (0, 0, 1), look - 30.0 * reach - 8.0 * set_) @ q(pb["head"], (1, 0, 0), -4.0 - 6.0 * recoil - 10.0 * set_ + 3 * math.sin(ph * 2 + 1))
    turns = tb_mix(None, _T["reach"], reach)
    turns = tb_mix(turns, _T["set"], set_)
    tb_pose_chain(rig, "arm.R", turns)
    pb["arm.L.1"].rotation_quaternion = q(pb["arm.L.1"], (1, 0, 0), -6.0 * haul + 3.0 * recoil)
    nt = SPEC["tail_bones"]
    tb_pose_chain(rig, "tail", [Quaternion()] * nt, extra=tb_wave(nt, (0, 0, 1), 2.2, ph * 2, step=0.9, grow=3.2))
    c, x, t = TAIL_END
    pb["fin"].rotation_quaternion = q(pb["fin"], tuple(t.cross(x)), -16.0 * max(0.0, math.sin(ph * 2 + 0.6)) ** 3 - 10.0 * recoil)


TAIL_END = (Vector(), Vector((0, 0, 1)), Vector((0, 1, 0)))


def build_anims():
    global TAIL_END
    rig = bpy.data.objects["Rig"]
    tp = tb_even(tb_curve(SPEC["tail"], 40), SPEC["tail_bones"] * 2 + 1)
    c, x, t = tb_frames(tp, (0, -1, 0))[-1]
    R3 = MER_M.to_3x3()
    TAIL_END = (MER_M @ c, (R3 @ x).normalized(), (R3 @ t).normalized())
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, ph=2 * math.pi * f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the string is loosed on frame 1; by frame 3 the harpoon is gone and the stock has kicked
        spent = smooth(f / 1.5)
        fly = min(max(f / 3.0, 0.0), 1.0)
        gone = smooth((f - 1.5) / 1.5)
        kick = smooth(f / 2.0) * (1 - smooth((f - 2) / 6.0))
        pose(rig, spent=spent, fly=fly, gone=gone, kick=kick, recoil=kick)
        key_pose(rig, f)
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        # 0-6 he reaches for the quiver, 6-14 carries a harpoon across and lays it in the trough, 14-23 hauls the string back
        reach = smooth(f / 5.0) * (1 - smooth((f - 7) / 5.0))
        set_ = smooth((f - 7) / 5.0) * (1 - smooth((f - 14) / 5.0))
        carry = None if f < 6 else min((f - 6) / 8.0, 1.0)
        gone = 1.0 - smooth((f - 5) / 2.0)
        haul_t = min(max((f - 15) / 8.0, 0.0), 1.0)
        haul = math.sin(math.pi * haul_t) ** 0.8 if 0.0 < haul_t < 1.0 else 0.0
        spent = 1.0 - smooth((f - 15) / 7.0)
        pose(rig, spent=spent, gone=gone, reach=reach, set_=set_, carry=carry, haul=haul)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 0.9), "dist": 10.5, "yaw": 150, "pitch": 22, "anim_target": (0, F.y, 1.5), "anim_dist": 5.2,
           "frames": [("idle", 0), ("fire", 2), ("fire", 12), ("reload", 6), ("reload", 11), ("reload", 19)],
           "extra": [{"yaw": 140, "pitch": 12, "dist": 3.6, "target": (0, F.y - 0.2, 1.75)},
                     {"yaw": 0, "pitch": 50, "dist": 5.5, "target": (0, B.y + 0.6, 0.7)},
                     {"yaw": 250, "pitch": 18, "dist": 5.5, "target": (0, MI.y, 1.1)},
                     {"yaw": 20, "pitch": 24, "dist": 4.6, "target": (0, F.y - 0.2, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
