"""Builds the Royal Bombard (footprint: [0,0] the centre, [-1,0] / [0,-1] / [1,-1] across the front, [0,1] behind),
the Crown's tier III artillery: two great bombards lobbing shot in volleys.

    python tools/blender/build.py bombard --out <preview dir>

One small stone artillery fort on a clover plan. Its hub is a round gun tower standing where the four front hexes
meet: on top, bedded in a kerb of masonry, a turntable of heavy planks carries both bombards side by side on their
sledges (the Head: the game turns it, so the guns swing together and fire over the parapets). Three low round bastions
with crenellated parapets grow out of the hub, one on each front cell: shot and powder on the left one, the gunners'
fire basket on the right, the Crown's banner down the face of the middle one, a standing banner on each flank.
Behind, a timber stair climbs from the paved yard (shot pile, rammer rack) to the guns, and the powder magazine, a
squat stone house under a hipped roof of team-colored tiles, closes the yard on the back cell.
The guns: iron barrels with a narrow powder chamber, bronze hoops and muzzle ring, a band in the team's color, lifting
rings; each strapped to a sledge (runners, bearers, cheeks, bolster posts) that slides on greased skids.
Clips: idle (the standard flies, the matches glow, a wisp of smoke curls from each muzzle in turn), fire (left then right: flash, the sledges kick back and settle,
smoke rolls out, the turntable shudders), reload (the sledges are hauled back out to battery, the matches relit).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "siege_common.py"), encoding="utf-8").read())

TID = "bombard"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (0, 1)]
MID = footprint_mid(CELLS)
CC = hex_to_world(0, 0, MID)
FL = hex_to_world(-1, 0, MID)
FC = hex_to_world(0, -1, MID)
FR = hex_to_world(1, -1, MID)
BK = hex_to_world(0, 1, MID)
TOP = 0.34
PIV = Vector((0.0, (CC.y + FC.y) * 0.5, 0.0))       # the hub's middle: where the four front hexes meet
HUB_R = 1.2
LOBE_R = 0.87
LOBE_DECK = TOP + 0.3           # the bastions' floors
LOBE_SILL = LOBE_DECK + 0.26    # their parapets, between the merlons
MERLON = 0.22
BARB = TOP + 0.95               # the hub's top
HEAD_Z = BARB + 0.24            # the turntable's planks
DECK_R = 1.05
MAG = Vector((BK.x, BK.y, 0.0))
MAG_W, MAG_D = 1.5, 1.1

# ---- the guns, in the head's space (+Y forward, z = 0 the turntable's top)
GX = 0.5                        # each gun's offset to its side
ELEV = 17.0                     # the barrels' elevation
GQ = Vector((0.0, 0.2, 0.58))   # the middle of a barrel
RECOIL = 0.2


def gun_mat(sx):
    return Matrix.Translation((sx * GX, GQ.y, GQ.z)) @ Matrix.Rotation(math.radians(ELEV), 4, "X")


def on_axis(sx, s, up=0.0):
    """The point `s` along a barrel from its middle (`up` above its axis), in the head's space."""
    return gun_mat(sx) @ Vector((0.0, s, up))


def axis_z(y):
    """A barrel's axis height above the turntable at the head-space y."""
    return GQ.z + (y - GQ.y) * math.tan(math.radians(ELEV))


def in_hub(p, pad=0.0):
    return (p[0] - PIV.x) ** 2 + (p[1] - PIV.y) ** 2 < (HUB_R + pad) ** 2


def bastion(k, rnd, c, T, merlon_at):
    """One lobe of the clover: a low round bastion grown out of the hub: a flared foot, three courses, merlons."""
    c0 = Vector((c.x, c.y, 0))
    ST = "stone:0.15:0.92"
    skip = lambda a: in_hub(polar(c0, a, LOBE_R - 0.1), -0.06)
    bm_course(k[ST], rnd, c0, LOBE_R + 0.05, T - 0.02, 0.16, 12, depth=0.3, phase=0.5, skip=skip, inner=False)
    for i in range(3):
        bm_course(k[ST], rnd, c0, LOBE_R, T + 0.14 + 0.14 * i, 0.14, 12, depth=0.24, phase=0.5 * (i % 2), skip=skip, inner=i > 0)
    for i in range(9):
        a = 40.0 * i + merlon_at
        if in_hub(polar(c0, a, LOBE_R - 0.1), 0.17):
            continue
        half = math.degrees(0.15 / LOBE_R)
        bm_wedge(k[ST], c0, math.radians(a - half), math.radians(a + half), LOBE_R - 0.24, LOBE_R + 0.006, LOBE_SILL - 0.012, LOBE_SILL + MERLON)
    DK = "stone_dark:0.3:0.9"                                   # the core: the deck's bed, and a dark band in the parapet's joints
    bm_drum(k[DK], c0, LOBE_R - 0.1, LOBE_R - 0.1, T, LOBE_DECK - 0.03, seg=14)
    bm_drum(k[DK], c0, LOBE_R - 0.07, LOBE_R - 0.07, LOBE_DECK - 0.06, LOBE_SILL - 0.025, seg=14, cap=False)
    bm_drum(k[DK], c0, LOBE_R - 0.17, LOBE_R - 0.17, LOBE_DECK - 0.06, LOBE_SILL - 0.025, seg=14, cap=False, inward=True)

    def deck(x, y):
        return (x - c.x) ** 2 + (y - c.y) ** 2 < (LOBE_R - 0.27) ** 2 and not in_hub((x, y), 0.04)
    bm_flagstones(k["stone2:0.15:0.7"], rnd, deck, (c.x - 0.7, c.y - 0.7, c.x + 0.7, c.y + 0.7), LOBE_DECK - 0.035, size=0.31, gap=0.03)


def build_base():
    col = collection("Bombard")
    root = empty("Bombard", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(17)
    k = Kit()
    inner = outline(CELLS, 0.2)
    P = Vector((PIV.x, PIV.y, 0))
    lobes = (FL, FC, FR)
    # ---- the three bastions
    for c, m in ((FL, 20.0), (FC, 10.0), (FR, 0.0)):
        bastion(k, rnd, c, T, m)
    k.emit("Bastion", col, root, vary=0.08)
    # ---- the hub: a round gun tower, a kerb of masonry round the turntable's pit on top
    def hub_skip(i, a):
        p = polar(P, a, HUB_R)
        return i < 2 and any((p - Vector((c.x, c.y, 0))).length < LOBE_R - 0.12 for c in lobes)
    hh = (BARB - T) / 6
    for i in range(6):
        bm_course(k["stone:0.05:0.82"], rnd, P, HUB_R - 0.04 * (i + 0.5) / 6, T + i * hh, hh, 16, depth=0.2, phase=0.5 * (i % 2),
                  skip=lambda a, i=i: hub_skip(i, a), inner=False)
    bm_drum(k["stone_dark:0.3:0.9"], P, HUB_R - 0.09, HUB_R - 0.13, T, BARB + 0.07, seg=16)       # the core; its lid is the turntable's pit
    bm_course(k["stone:0.0:0.55"], rnd, P, HUB_R + 0.05, BARB - 0.02, 0.17, 18, depth=0.28, inner=False)
    k.emit("Hub", col, root, vary=0.08)
    for a in (238, 302):                                         # loops in the hub's back wall, a lantern between
        p = polar(P, a, HUB_R - 0.035, T + 0.5)
        bm_box(k["black:0.3:0.7"], (0.06, 0.07, 0.3), tuple(p), (0, 0, a - 90))
        bm_box(k["black:0.3:0.7"], (0.18, 0.07, 0.055), (p.x, p.y, p.z + 0.03), (0, 0, a - 90))
    la = 222
    bm_beam(k["iron:0.1:0.5"], polar(P, la, HUB_R - 0.05, T + 0.7), polar(P, la, HUB_R + 0.2, T + 0.73), 0.03, 0.03)
    lp = polar(P, la, HUB_R + 0.18, T + 0.62)
    bm_cyl(k["iron:0.1:0.5"], 0.05, 0.02, 0.04, (lp.x, lp.y, lp.z + 0.07), seg=6)
    bm_cyl(k["iron:0.1:0.5"], 0.045, 0.045, 0.02, (lp.x, lp.y, lp.z - 0.06), seg=6)
    bm_cyl(k["glow:1.0,0.72,0.3,1.0"], 0.036, 0.036, 0.1, tuple(lp), seg=6)
    k.emit("Hub_Kit", col, root)
    # ---- heraldry: the banner down the middle bastion's face, shields on the flanks, a standing banner on each
    bm_banner(k, (FC.x, FC.y + LOBE_R + 0.035, LOBE_SILL + MERLON - 0.03), (0, 1, 0), w=0.42, h=0.66, lean=0.04)
    for c, a in ((FL, 180.0), (FR, 0.0)):
        o = radial(a)
        bm_shield(k, Vector((c.x, c.y, 0)) + o * (LOBE_R + 0.03) + Vector((0, 0, LOBE_SILL - 0.02)), o, w=0.3, h=0.36)
    for c, sx in ((FL, -1), (FR, 1)):
        bm_gonfalon(k, (c.x + sx * 0.36, c.y + 0.3, LOBE_DECK), (0, -1, 0), pole=1.5, w=0.42, h=0.74)
    k.emit("Heraldry", col, root)
    # ---- the left bastion: ready shot in a garland of timbers, powder kegs
    sp = Vector((FL.x - 0.14, FL.y - 0.12, LOBE_DECK))
    bm_shot_pile(k["iron:0.3:0.95"], sp, r=0.11, layers=2, u=6, v=4, turn=15)
    for i in range(4):
        a0, a1 = polar(sp, 15 + 45 + 90 * i, 0.36, sp.z + 0.035), polar(sp, 15 + 135 + 90 * i, 0.36, sp.z + 0.035)
        bm_beam(k["wood_dark:0.2:0.8"], a0, a1, 0.06, 0.07)
    bm_keg(k, (FL.x - 0.02, FL.y + 0.42, LOBE_DECK + 0.19), r=0.15, h=0.38)
    bm_keg(k, (FL.x - 0.4, FL.y - 0.22 + 0.5, LOBE_DECK + 0.14), r=0.12, h=0.3, axis=(1, 0.5, 0))
    k.emit("Ready_Shot", col, root)
    # ---- the right bastion: the gunners' fire basket, a match tub, a coil of rope
    fb = bm_brazier(k, (FR.x + 0.16, FR.y - 0.12, LOBE_DECK), r=0.17, h=0.42, turn=20)
    bm_flame(k[FIRE], fb, h=0.26, r=0.085, lean=(0.03, 0.0, 0))
    bm_flame(k["glow:1.0,0.8,0.25,1.0"], fb + Vector((0.05, -0.04, 0)), h=0.16, r=0.055)
    bm_flame(k[FIRE], fb + Vector((-0.06, 0.03, 0)), h=0.13, r=0.05)
    bm_keg(k, (FR.x + 0.02, FR.y + 0.42, LOBE_DECK + 0.17), r=0.14, h=0.34)
    k.emit("Fire_Basket", col, root)
    # ---- the yard: paving from the hub's foot back round the magazine, a worn apron round the bastions
    mx0, mx1, my0, my1 = MAG.x - MAG_W / 2, MAG.x + MAG_W / 2, MAG.y - MAG_D / 2, MAG.y + MAG_D / 2

    def clear(x, y):
        if not inside(inner, x, y) or in_hub((x, y), 0.1):
            return False
        if any((x - c.x) ** 2 + (y - c.y) ** 2 < (LOBE_R + 0.13) ** 2 for c in lobes):
            return False
        return not (mx0 - 0.07 < x < mx1 + 0.07 and my0 - 0.07 < y < my1 + 0.07)
    bm_flagstones(k["stone2:0.15:0.7"], rnd, lambda x, y: clear(x, y) and my0 - 0.02 < y < CC.y + 0.12, (-1.5, -3.6, 1.5, 0.0), T, size=0.3, keep=0.95)
    bm_flagstones(k["stone2:0.2:0.8"], rnd, lambda x, y: clear(x, y) and y >= CC.y + 0.12 and
                  any((x - c.x) ** 2 + (y - c.y) ** 2 < (LOBE_R + 0.52) ** 2 for c in lobes), (-3.0, -0.5, 3.0, 2.8), T, size=0.27, keep=0.6)
    k.emit("Yard", col, root, vary=0.09)
    # ---- the stair up the back of the hub
    y_top, y_foot, z_top = P.y - HUB_R - 0.03, P.y - HUB_R - 0.8, BARB + 0.15
    for sx in (-1, 1):
        bm_beam(k["wood_dark:0.2:0.8"], (sx * 0.27, y_foot, T + 0.03), (sx * 0.27, y_top + 0.04, z_top - 0.03), 0.07, 0.15)
        bm_box(k["wood_dark:0.2:0.8"], (0.07, 0.07, 0.34), (sx * 0.27, y_top - 0.02, z_top + 0.14))
    steps = 7
    for i in range(steps):
        t = (i + 0.6) / steps
        bm_box(k["wood:0.25:0.8"], (0.52, 0.13, 0.045), (rnd.uniform(-0.01, 0.01), y_foot + (y_top - y_foot) * t, T + (z_top - T) * t + 0.02))
    k.emit("Stair", col, root, vary=0.08)
    # ---- left of the stair: the shot pile; right: the rack of rammer, sponge and ladle against the hub
    sp = Vector((-0.6, P.y - HUB_R - 0.26, T))
    bm_shot_pile(k["iron:0.3:0.95"], sp, r=0.1, layers=2, u=6, v=4, turn=8)
    for i in range(4):
        a0, a1 = polar(sp, 8 + 45 + 90 * i, 0.33, sp.z + 0.035), polar(sp, 8 + 135 + 90 * i, 0.33, sp.z + 0.035)
        bm_beam(k["wood_dark:0.2:0.8"], a0, a1, 0.06, 0.07)
    k.emit("Shot", col, root)
    rk = Vector((0.6, P.y - HUB_R - 0.22, T))
    for dx in (-0.2, 0.2):
        bm_box(k["wood_dark:0.2:0.8"], (0.06, 0.06, 0.74), (rk.x + dx, rk.y, T + 0.37))
        bm_beam(k["wood_dark:0.2:0.8"], (rk.x + dx, rk.y - 0.2, T + 0.02), (rk.x + dx, rk.y, T + 0.4), 0.05, 0.05)
    bm_beam(k["wood_dark:0.2:0.8"], (rk.x - 0.27, rk.y, T + 0.7), (rk.x + 0.27, rk.y, T + 0.7), 0.06, 0.07)
    for dx, kind in ((-0.12, "rammer"), (0.0, "sponge"), (0.12, "ladle")):
        foot = Vector((rk.x + dx, rk.y - 0.24, T + 0.02))
        tip = Vector((rk.x + dx * 1.3, rk.y + 0.1, T + 1.18))
        d = (tip - foot).normalized()
        bm_beam(k["wood:0.15:0.6"], foot, tip, 0.035, 0.035)
        if kind == "rammer":
            bm_tube(k["wood_dark:0.2:0.7"], [tip - d * 0.02, tip + d * 0.14], 0.065, n=7)
        elif kind == "sponge":
            bm_tube(k["cream:0.2:0.8"], [tip - d * 0.03, tip + d * 0.04, tip + d * 0.17, tip + d * 0.2], [0.05, 0.08, 0.08, 0.05], n=7)
        else:
            bm_tube(k["gold:0.3:0.85"], [tip - d * 0.02, tip + d * 0.18], [0.055, 0.065], n=7)
    k.emit("Rack", col, root)
    # ---- the powder magazine on the back cell: thick walls of warm stone, an arched door to the yard, a hipped roof
    ez, th, WS = T + 0.62, 0.17, "stone_warm:0.12:0.9"
    dw = 0.38
    bm_block_wall(k[WS], rnd, (mx0, my0 + th / 2), (mx1, my0 + th / 2), T, ez, th=th, course=0.155, block=0.36)
    for x in (mx0 + th / 2, mx1 - th / 2):
        bm_block_wall(k[WS], rnd, (x, my0 + th), (x, my1 - th), T, ez, th=th, course=0.155, block=0.36)
    bm_block_wall(k[WS], rnd, (mx0, my1 - th / 2), (MAG.x - dw / 2 - 0.1, my1 - th / 2), T, ez, th=th, course=0.155, block=0.36)
    bm_block_wall(k[WS], rnd, (MAG.x + dw / 2 + 0.1, my1 - th / 2), (mx1, my1 - th / 2), T, ez, th=th, course=0.155, block=0.36)
    bm_box(k["stone_dark:0.35:0.9"], (MAG_W - 0.1, MAG_D - 0.1, ez - T), (MAG.x, MAG.y, (T + ez) / 2))
    for sx in (-1, 1):                                           # corner buttresses, stepped
        for sy in (-1, 1):
            cx, cy = MAG.x + sx * (MAG_W / 2 - 0.04), MAG.y + sy * (MAG_D / 2 - 0.04)
            bm_box(k["stone:0.1:0.8"], (0.26, 0.26, 0.3), (cx, cy, T + 0.15))
            bm_box(k["stone:0.1:0.8"], (0.2, 0.2, ez - T - 0.3), (cx, cy, (T + 0.3 + ez) / 2))
    k.emit("Magazine", col, root, vary=0.08)
    bm_arch(k["stone:0.05:0.65"], (MAG.x, my1 - th / 2, T), (1, 0, 0), dw, 0.3, th=0.1, depth=th + 0.05, n=5)
    k.emit("Magazine_Arch", col, root, vary=0.07)
    bm_box(k["wood_dark:0.25:0.8"], (dw + 0.02, 0.05, 0.5), (MAG.x, my1 - 0.02, T + 0.25))
    for z in (0.12, 0.34):
        bm_box(k["iron:0.1:0.5"], (dw, 0.02, 0.045), (MAG.x, my1 + 0.012, T + z))
    ring(k["gold:0.1:0.5"], (MAG.x + 0.1, my1 + 0.02, T + 0.24), 0.04, 0.022, -0.008, 0.008, seg=8, axis="Y")
    for x in (-0.42, 0.42):                                      # barred vents in the back wall, the shield between them
        bm_box(k["black:0.3:0.7"], (0.2, 0.05, 0.13), (MAG.x + x, my0 - 0.002, T + 0.42))
        for dx in (-0.05, 0.05):
            bm_box(k["iron:0.1:0.5"], (0.022, 0.03, 0.14), (MAG.x + x + dx, my0 - 0.02, T + 0.42))
    k.emit("Magazine_Door", col, root)
    bm_shield(k, (MAG.x, my0 - 0.03, T + 0.36), (0, -1, 0), w=0.32, h=0.38)
    k.emit("Magazine_Shield", col, root)
    for a, b in (((mx0 - 0.04, my0), (mx1 + 0.04, my0)), ((mx0 - 0.04, my1), (mx1 + 0.04, my1)), ((mx0, my0), (mx0, my1)), ((mx1, my0), (mx1, my1))):
        bm_beam(k["wood_dark:0.2:0.8"], (a[0], a[1], ez + 0.01), (b[0], b[1], ez + 0.01), 0.1, 0.07)
    k.emit("Magazine_Plate", col, root)
    R = bm_hip_roof(k, rnd, (MAG.x, MAG.y), MAG_W, MAG_D, ez + 0.04, 0.5, ridge=0.62, rows=3, cols=5, over=0.14)
    k.emit("Magazine_Roof", col, root, vary=0.08)
    for r in R:
        bm_ellipsoid(k["gold:0.05:0.5"], (r.x, r.y, r.z + 0.14), (0.055, 0.055, 0.055), u=7, v=5)
        bm_cyl(k["gold:0.05:0.5"], 0.022, 0.0, 0.15, (r.x, r.y, r.z + 0.26), seg=5)
    k.emit("Magazine_Finials", col, root)
    bm_keg(k, (MAG.x - 0.5, my1 + 0.24, T + 0.2), r=0.16, h=0.4)
    bm_keg(k, (MAG.x + 0.5, my1 + 0.22, T + 0.15), r=0.15, h=0.36, axis=(1, 0.25, 0))
    k.emit("Kegs", col, root)
    # ---- rocks and green in the notches between the bastions
    for sx in (-1, 1):
        n = polar(P, 90 - sx * 60, 1.52)
        bm_boulder(k["stone:0.2:0.9"], rnd, (n.x, n.y, T - 0.02), 0.2, n=11)
        bm_boulder(k["stone:0.2:0.9"], rnd, (n.x + sx * 0.02, n.y + 0.27, T - 0.02), 0.12, n=9)
    k.emit("Rocks", col, root, vary=0.07)
    for i, (rel, loc, rot, sc) in enumerate((("hex/bucket_water", (-0.42, P.y - HUB_R - 0.72, T), 0, 1.9),
                                             ("forest/Bush_1_C_Color1", (1.02, MAG.y - 0.1, T - 0.02), 40, 0.22),
                                             ("forest/Grass_1_B_Color1", (-1.0, MAG.y + 0.05, T - 0.02), 0, 0.45),
                                             )):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    empty("Head", col, root, (PIV.x, PIV.y, HEAD_Z), 0.5, "SINGLE_ARROW")
    return root


POLE = Vector((0.0, 0.93, 0.0))
STD_Z = 1.92
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "table": ((0, 0, 0), (0, 0.3, 0), "root")}
for _s, _sx in (("L", -1), ("R", 1)):
    BONES["gun." + _s] = (tuple(on_axis(_sx, 0.0)), tuple(on_axis(_sx, 0.4)), "table")
    BONES["flash." + _s] = (tuple(on_axis(_sx, 0.9)), tuple(on_axis(_sx, 1.2)), "gun." + _s)
    BONES["fuse." + _s] = (tuple(on_axis(_sx, -0.6, 0.17)), tuple(on_axis(_sx, -0.6, 0.17) + Vector((0, 0, 0.1))), "gun." + _s)
    BONES["smoke." + _s] = (tuple(on_axis(_sx, 1.05)), tuple(on_axis(_sx, 1.05) + Vector((0, 0, 0.25))), "table")
flag_bones(BONES, "std", (POLE.x, POLE.y, STD_Z), (1, 0, 0), 0.76, segs=3, parent="table")


def bm_barrel(g):
    """One bombard lying along +Y, its middle on the origin: the narrow powder chamber behind, the stave barrel,
    bronze hoops and muzzle ring, a band in the team's color, lifting rings, the vent."""
    IR, BZ = "iron:0.15:0.85", "gold:0.4:0.95"
    prof = [(-0.80, 0.09), (-0.77, 0.15), (-0.40, 0.16), (-0.37, 0.215), (0.72, 0.225), (0.75, 0.225)]
    bm_tube(g[IR], [(0, y, 0) for y, r in prof], [r for y, r in prof], n=10)
    for y in (-0.385, -0.08, 0.2, 0.47):
        bm_tube(g[BZ], [(0, y - 0.032, 0), (0, y + 0.032, 0)], 0.243, n=10)
    bm_tube(g[BZ], [(0, -0.79, 0), (0, -0.72, 0)], 0.168, n=10)
    bm_ellipsoid(g[BZ], (0, -0.83, 0), (0.07, 0.07, 0.07), u=7, v=5)
    bm_box(g[BZ], (0.09, 0.09, 0.03), (0, -0.6, 0.165))
    bm_tube(g["team!:0.15:0.7"], [(0, 0.243, 0), (0, 0.427, 0)], 0.237, n=10)
    bm_cyl(g["black:0.5:0.95"], 0.16, 0.16, 0.02, (0, 0.765, 0), rot=(90, 0, 0), seg=10)
    ring(g["gold:0.2:0.85"], (0, 0, 0), 0.275, 0.15, 0.7, 0.9, seg=10, axis="Y")
    for y in (-0.23, 0.06):
        ring(g["iron:0.1:0.6"], (0, y, 0.27), 0.07, 0.042, -0.016, 0.016, seg=6, axis="X")
    return g


def bm_sledge(k, sx):
    """A gun's sledge, in the head's space: runners with upturned noses, bearers, the bolster and its cheek posts,
    cheeks along the barrel's flanks, a quoin under the chamber."""
    W, WD = "wood:0.2:0.8", "wood_dark:0.2:0.8"
    X = sx * GX
    for s in (-1, 1):
        x = X + s * 0.215
        bm_beam(k[WD], (x, -0.64, 0.06), (x, 0.66, 0.06), 0.11, 0.12)
        bm_beam(k[WD], (x, 0.64, 0.06), (x, 0.79, 0.125), 0.11, 0.12, h1=0.09)
        bm_beam(k[W], (x, -0.6, axis_z(-0.6) - 0.175), (x, 0.56, axis_z(0.56) - 0.175), 0.1, 0.12)
        for y in (0.1, 0.34):
            h = axis_z(y) - 0.235 - 0.12
            bm_box(k[WD], (0.07, 0.08, h), (x, y, 0.12 + h / 2))
        bm_box(k[WD], (0.085, 0.15, 0.6), (X + s * 0.285, 0.5, 0.4))
        bm_cyl(k["gold:0.1:0.55"], 0.06, 0.0, 0.08, (X + s * 0.285, 0.5, 0.74), rot=(0, 0, 45), seg=4)
    for y in (-0.56, -0.02, 0.5):
        bm_beam(k[W], (X - 0.31, y, 0.165), (X + 0.31, y, 0.165), 0.13, 0.09)
    bm_box(k[W], (0.34, 0.14, 0.09), (X, -0.02, 0.25))
    bm_box(k[W], (0.42, 0.15, 0.25), (X, 0.5, 0.33))
    bm_beam(k[W], (X, -0.76, 0.22), (X, -0.48, 0.24), 0.16, 0.05, h1=0.1)
    return k


def build_head():
    col = collection("Bombard")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(9)
    k = Kit()
    # ---- the turntable: planks along the guns, an iron tyre with studs, greased skids under the sledges' runners
    bm_deck(k["wood:0.3:0.85"], rnd, (0, 0, 0), circle_half(DECK_R), -DECK_R, DECK_R, 0.0, pw=0.165, th=0.07, turn=90)
    k.emit("Head_Deck", col, rig=rig, bone="table", vary=0.09)
    for a in (45, 135):
        o = radial(a)
        bm_beam(k["wood_dark:0.3:0.85"], o * -0.93 + Vector((0, 0, -0.105)), o * 0.93 + Vector((0, 0, -0.105)), 0.2, 0.09)
    ring(k["iron:0.1:0.55"], (0, 0, 0), DECK_R + 0.025, DECK_R - 0.06, -0.08, 0.012, seg=20)
    for i in range(8):
        p = polar((0, 0, 0), 45 * i + 22.5, DECK_R - 0.02, 0.014)
        bm_cyl(k["iron:0.0:0.4"], 0.03, 0.03, 0.014, tuple(p), seg=6)
    k.emit("Head_DeckIron", col, rig=rig, bone="table")
    for sx in (-1, 1):
        for s, y0, y1 in ((-1, -0.93, 0.84), (1, -0.74, 0.72)):
            x = sx * (GX + s * 0.215)
            bm_box(k["sand:0.4:0.85"], (0.16, y1 - y0, 0.016), (x, (y0 + y1) / 2, 0.008))
    k.emit("Head_Skids", col, rig=rig, bone="table")
    # ---- ready shot in a tray between the guns
    bm_box(k["wood_dark:0.2:0.8"], (0.4, 0.4, 0.05), (0, 0.4, 0.027))
    for s in (-1, 1):
        bm_box(k["wood_dark:0.2:0.8"], (0.05, 0.42, 0.07), (s * 0.2, 0.4, 0.06))
        bm_box(k["wood_dark:0.2:0.8"], (0.42, 0.05, 0.07), (0, 0.4 + s * 0.2, 0.06))
    k.emit("Head_Tray", col, rig=rig, bone="table")
    bm_shot_pile(k["iron:0.3:0.95"], (0, 0.4, 0.05), r=0.085, layers=2, u=6, v=4)
    k.emit("Head_TrayShot", col, rig=rig, bone="table")
    # ---- the standard at the turntable's front, between the muzzles
    bm_cyl(k["wood_dark:0.2:0.7"], 0.03, 0.02, STD_Z + 0.06, (POLE.x, POLE.y, (STD_Z + 0.06) / 2), seg=6)
    bm_cyl(k["iron:0.1:0.5"], 0.065, 0.045, 0.09, (POLE.x, POLE.y, 0.045), seg=6)
    bm_cyl(k["gold:0.05:0.5"], 0.045, 0.0, 0.13, (POLE.x, POLE.y, STD_Z + 0.125), seg=5)
    k.emit("Head_Pole", col, rig=rig, bone="table")
    flag_part("Head_Standard", col, rig, "std", (POLE.x, POLE.y, STD_Z), (1, 0, 0), 0.76, 0.44, segs=3, tail="swallow")
    # ---- the two guns: each sledge and barrel on a bone of its own, a flash at the muzzle, a match at the vent, smoke
    for name, sx in (("L", -1), ("R", 1)):
        bm_sledge(k, sx)
        k.emit("Head_Sledge" + name, col, rig=rig, bone="gun." + name)
        g = bm_barrel(Kit())
        for bm in g.parts.values():
            bmesh.ops.transform(bm, matrix=gun_mat(sx), verts=bm.verts[:])
        g.emit("Head_Gun" + name, col, rig=rig, bone="gun." + name)
        f = Kit()
        bm_crystal(f["glow:1.0,0.85,0.4,1.1"], (0, 0.9, 0), (0, 1.75, 0), 0.2, n=6, shoulder=0.3, foot=0.6)
        for i in range(6):
            a = math.radians(60 * i + 30)
            bm_crystal(f["glow:1.0,0.5,0.1,1.0"], (0, 0.92, 0), (math.cos(a) * 0.42, 1.3, math.sin(a) * 0.42), 0.09, n=4, shoulder=0.35, foot=0.5)
        for bm in f.parts.values():
            bmesh.ops.transform(bm, matrix=gun_mat(sx), verts=bm.verts[:])
        f.emit("Head_Flash" + name, col, rig=rig, bone="flash." + name)
        vent = on_axis(sx, -0.6, 0.17)
        bm_flame(k["glow:1.0,0.6,0.15,1.1"], vent, h=0.11, r=0.04)
        k.emit("Head_Fuse" + name, col, rig=rig, bone="fuse." + name)
        m = on_axis(sx, 1.05)
        bm_blob(k["white:0.0:0.6"], rnd, m + Vector((0, 0.08, 0.04)), 0.27, squash=(1.0, 1.15, 0.9), jitter=0.1, sub=2)
        bm_blob(k["white:0.0:0.6"], rnd, m + Vector((sx * 0.14, 0.26, 0.16)), 0.19, jitter=0.1)
        bm_blob(k["white:0.0:0.6"], rnd, m + Vector((-sx * 0.1, 0.3, -0.04)), 0.15, jitter=0.1)
        k.emit("Head_Smoke" + name, col, rig=rig, bone="smoke." + name)
    # ---- markers
    empty("Muzzle1", col, head, tuple(on_axis(-1, 0.95)), 0.25, "SPHERE")
    empty("Muzzle2", col, head, tuple(on_axis(1, 0.95)), 0.25, "SPHERE")
    crew = empty("Crew", col, head, (0.0, -0.5, 0.0), 0.3, "SINGLE_ARROW")
    mannequin(col, crew, 1.15, "engineer")
    return rig


IDLE_LEN = 80
FIRE_LEN = 18
RELOAD_LEN = 30
LAG = (0, 2)                    # the right gun fires two frames after the left


def keys(f, pts):
    """Piecewise-linear value at frame f through (frame, value) points."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * (f - f0) / float(f1 - f0)
    return pts[-1][1]


def pose(rig, wave=0.0, amp=1.0, rec=(0.0, 0.0), hop=(0.0, 0.0), flash=(0.0, 0.0), smoke=((0.0, 0.0), (0.0, 0.0)), fuse=(1.0, 1.0), rock=0.0):
    """rec: how far back each sledge has slid; hop: each gun's nose-up kick (degrees); flash: each muzzle flash's size;
    smoke: each puff's (size, drift); fuse: each match's size; rock: the turntable's pitch."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["table"].rotation_quaternion = q(pb["table"], (1, 0, 0), rock)
    for i, s in enumerate(("L", "R")):
        g = pb["gun." + s]
        g.location = arm_space_loc(g, (0, -rec[i], 0.012 * hop[i]))
        g.rotation_quaternion = q(g, (1, 0, 0), hop[i])
        pb["flash." + s].scale = (max(flash[i], 0.001),) * 3
        sm = pb["smoke." + s]
        sm.scale = (max(smoke[i][0], 0.001),) * 3
        sm.location = arm_space_loc(sm, (0, 0.6 * smoke[i][1], 0.45 * smoke[i][1]))
        pb["fuse." + s].scale = (max(fuse[i], 0.001),) * 3
    wave_flag(rig, "std", wave, amp=amp, segs=3)


FLASH = [(0, 0.0), (1, 1.0), (2, 1.35), (3, 0.9), (4, 0.35), (5, 0.0)]
REC = [(0, 0.0), (1, 0.1), (2, 0.2), (3, 0.26), (5, 0.235), (7, 0.2), (9, RECOIL)]
HOP = [(0, 0.0), (1, 4.0), (2, 6.0), (3, 3.0), (5, -1.0), (7, 0.3), (9, 0.0)]
SMOKE = [(1, 0.0), (2, 0.55), (5, 1.0), (9, 1.25), (12, 1.0), (15, 0.0)]
FUSE = [(0, 1.0), (1, 2.4), (2, 0.0)]
ROCK = [(0, 0.0), (2, -0.9), (4, 0.7), (6, -0.5), (8, 0.3), (11, -0.1), (14, 0.0)]


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        wisp = []                                               # a wisp of smoke curls from each warm muzzle in turn
        for start in (0, 40):
            t = (f - start) / 36.0
            wisp.append((0.36 * math.sin(math.pi * t), 0.6 * t) if 0.0 < t < 1.0 else (0.0, 0.0))
        pose(rig, wave=f / IDLE_LEN, fuse=(1.0 + 0.3 * math.sin(ph * 5), 1.0 + 0.3 * math.sin(ph * 7)), smoke=wisp)
        key_pose(rig, f)
    # ---- fire: the left gun, then the right: flash, the sledge kicks back along its skids and settles, smoke rolls out
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = [f - d for d in LAG]
        kick = smooth(f / 2.0) * (1 - smooth((f - 4) / 10.0))
        pose(rig, wave=f / FIRE_LEN, amp=1.0 + 1.5 * kick, rec=[keys(x, REC) for x in t], hop=[keys(x, HOP) for x in t],
             flash=[keys(x, FLASH) for x in t], smoke=[(keys(x, SMOKE), max(x - 1, 0) / 14.0) for x in t],
             fuse=[keys(x, FUSE) for x in t], rock=keys(f, ROCK))
        key_pose(rig, f)
    # ---- reload: the sledges are hauled back out to battery in heaves (left, then right), the matches are relit
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        rec, fuse = [], []
        for d in (0, 4):
            x = f - d
            p = 0.5 * smooth((x - 2) / 7.0) + 0.5 * smooth((x - 11) / 7.0)
            bump = 0.018 * math.sin(math.pi * min(max((x - 18) / 4.0, 0.0), 1.0))
            rec.append(RECOIL * (1 - p) - bump)
            fuse.append(keys(x, [(21, 0.0), (23, 1.7), (26, 1.0)]))
        pose(rig, wave=f / RELOAD_LEN, rec=rec, fuse=fuse, rock=0.25 * math.sin(2 * math.pi * f / 10.0) * (1 - smooth((f - 20) / 6.0)) * smooth(f / 3.0))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, -0.3, 1.0), "dist": 14.0, "yaw": 150, "pitch": 20, "anim_target": (PIV.x, PIV.y, HEAD_Z + 0.6), "anim_dist": 7.5,
           "frames": [("idle", 18), ("fire", 2), ("fire", 4), ("fire", 9), ("reload", 14)],
           "extra": [{"yaw": 150, "pitch": 16, "dist": 6.0, "target": (PIV.x, PIV.y, HEAD_Z + 0.3)},
                     {"yaw": 0, "pitch": 57, "dist": 8.5, "target": (0, -0.4, 0.8)},
                     {"yaw": 35, "pitch": 24, "dist": 6.5, "target": (0, -1.8, 0.7)},
                     {"yaw": 215, "pitch": 22, "dist": 6.5, "target": (-1.2, 0.9, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
    tri_report("Bombard")
