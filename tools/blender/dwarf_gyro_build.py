"""Builds the Flak Battery (footprint "wing3": [0,0] the back cell, [1,-1] front-right, [-1,0] front-left), the Deep
Forge's anti-air gun: twin rotary flak guns that shred flyers.

    python tools/blender/build.py dwarf_gyro --out <preview dir>

One armored flak turret. A round barbette of coursed stone and riveted iron plate fills the back cell and carries a
turning cupola (the Head): eight riveted plates under a roof of team-colored plates, a rotary gun on each cheek (six
barrels round an axle in brass clamps, a brass drum magazine, raised for the sky: Muzzle1 the left gun, Muzzle2 the
right). On each front cell an iron-bound shell locker sends a riveted chute up to a brass hoist on the barbette's flank,
a rack of shells stands by it, and a blast wall of stone blocks under a timber cap wraps the cell's front. A spotting
scope and a wind vane ride the roof; the engine's firebox glows at the cupola's back and its stack puffs smoke.
idle: the guns scan slowly up and down, the scope sweeps, the vane swings in the wind, smoke puffs.
fire (a short alternating kick): both barrel clusters whirl, the left gun kicks and flashes, then the right.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forge_guns_common.py"), encoding="utf-8").read())

TID = "dwarf_gyro"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FR = hex_to_world(1, -1, MID)
FL = hex_to_world(-1, 0, MID)
TOP = 0.34
T = TOP
BZ = T + 0.9                    # the barbette's top: the turret ring, where the Head sits
EZ = 0.5                        # the trunnions' height over the ring (head space)
GX = 0.86                       # each gun's axis, out from the middle
EL = 58.0                       # the guns' elevation
D = Vector((0.0, math.cos(math.radians(EL)), math.sin(math.radians(EL))))
GZ = Vector((1, 0, 0)).cross(D)                 # square to the gun's axis, in its plane of elevation
ZV = Vector((0, 0, 1))
STACK = Vector((0.22, -0.4, 1.17))
EMBERS = "glow:1.0,0.34,0.04,0.75"          # the firebox's coals              # the exhaust stack's mouth (head space)
VANE = Vector((-0.22, -0.36, 1.3))


def build_base():
    col = collection("Dwarf_gyro")
    root = empty("Dwarf_gyro", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(15)
    k = Kit()
    C = BK
    c0 = (C.x, C.y, 0)
    # ---- the yard: flagstones over all three cells round the barbette
    bm_flagstones(k["stone2:0.15:0.7"], rnd, lambda x, y: in_footprint(CELLS, x, y, 0.22) and (x - C.x) ** 2 + (y - C.y) ** 2 > 0.93 ** 2,
                  (FL.x - 1.2, BK.y - 1.2, FR.x + 1.2, FR.y + 1.2), T, size=0.3, keep=1.0)
    k.emit("Yard", col, root, vary=0.09)
    # ---- the barbette: a footing of big dark blocks, coursed stone, a band of riveted iron plates, a brass rim
    bm_block_course(k["stone_dark:0.2:0.7"], rnd, c0, 0.9, T - 0.01, 0.15, 13, depth=0.22)
    k.emit("Footing", col, root, vary=0.08)
    round_tower(k, rnd, c0, 0.84, 0.81, T + 0.14, T + 0.6, courses=3, n=11, depth=0.18)
    k.emit("Barbette", col, root, bevel=0.012, vary=0.08)
    bm_block_course(k["iron:0.25:0.75"], rnd, c0, 0.835, T + 0.6, BZ - 0.08 - (T + 0.6), 12, depth=0.08, gap=0.018, phase=0.25)
    k.emit("Barbette_Plates", col, root, vary=0.07)
    pts = []
    for i in range(12):
        for f in (0.5,):
            a = math.radians(30.0 * (i + 0.25 + f))
            pts.append(Vector((C.x + 0.84 * math.cos(a), C.y + 0.84 * math.sin(a), BZ - 0.14)))
    rivets(k["gold:0.1:0.5"], pts, lambda p: Vector((p.x - C.x, p.y - C.y, 0)), r=0.024)
    k.emit("Barbette_Rivets", col, root)
    ring(k["gold:0.15:0.55"], c0, 0.89, 0.77, BZ - 0.08, BZ - 0.02, seg=28)
    k.emit("Barbette_Rim", col, root, bevel=0.008)
    bm_cyl(k["stone_dark:0.4:0.9"], 0.79, 0.79, 0.05, (C.x, C.y, BZ - 0.045), seg=24)
    k.emit("Barbette_Deck", col, root)
    gear_ring(k["iron:0.3:0.8"], c0, 0.71, BZ - 0.03, BZ + 0.035, 24, depth=0.06, r_in=0.6)
    k.emit("Race", col, root)
    # the door at the back, toward the game camera: an arch over thick planks with iron straps
    dz, dy = T + 0.14, C.y - 0.845
    bm_arch(k["stone_warm:0.15:0.7"], (C.x, dy, dz), (1, 0, 0), 0.34, 0.24, th=0.09, depth=0.12, n=5)
    k.emit("Door_Arch", col, root, bevel=0.01, vary=0.06)
    bm_planks(k["wood_dark:0.2:0.7"], rnd, (C.x - 0.17, dy + 0.035, dz), (0, 0, 0.4), (0.34, 0, 0), 4, th=0.05)
    k.emit("Door", col, root, vary=0.08)
    for z in (dz + 0.09, dz + 0.29):
        bm_box(k["iron:0.3:0.8"], (0.36, 0.02, 0.045), (C.x, dy - 0.02, z))
    bm_cyl(k["gold:0.1:0.5"], 0.035, 0.035, 0.02, (C.x + 0.09, dy - 0.03, dz + 0.19), rot=(90, 0, 0), seg=6)
    k.emit("Door_Iron", col, root)
    # a lantern on a bracket over the door
    lp = Vector((C.x, dy - 0.15, T + 0.6))
    bm_beam(k["iron:0.3:0.8"], (C.x, dy + 0.04, T + 0.75), (C.x, dy - 0.17, T + 0.75), 0.03, 0.03)
    bm_beam(k["iron:0.3:0.8"], (C.x, dy - 0.15, T + 0.75), tuple(lp + ZV * 0.08), 0.015, 0.015)
    bm_box(k["iron:0.3:0.8"], (0.11, 0.11, 0.02), tuple(lp - ZV * 0.07))
    bm_cyl(k["iron:0.3:0.8"], 0.08, 0.02, 0.05, tuple(lp + ZV * 0.08), seg=4, rot=(0, 0, 45))
    for ax, ay in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bm_box(k["iron:0.3:0.8"], (0.014, 0.014, 0.14), (lp.x + ax * 0.045, lp.y + ay * 0.045, lp.z))
    k.emit("Lantern", col, root)
    bm_box(k["glow:1.0,0.62,0.25,0.9"], (0.07, 0.07, 0.11), tuple(lp))
    k.emit("Lantern_Glow", col, root)
    # the team's banners on the barbette's back, either side of the door
    for a in (236, 304):
        n = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        tv = Vector((-n.y, n.x, 0))
        p = C + n * 0.875
        top, bot, hw = BZ - 0.1, T + 0.24, 0.14
        shape = [(-hw, top), (hw, top), (hw, bot + 0.12), (0, bot), (-hw, bot + 0.12)]
        slab(k["team!:0.1:0.6"], [p + tv * x + ZV * z for x, z in shape], 0.02, n)
        bm_beam(k["wood_dark:0.2:0.7"], p + n * 0.02 - tv * 0.19 + ZV * (top + 0.01), p + n * 0.02 + tv * 0.19 + ZV * (top + 0.01), 0.04, 0.04)
        rod(k["gold:0.1:0.45"], p + n * 0.005 + ZV * (top - 0.2), p + n * 0.03 + ZV * (top - 0.2), 0.07, n=8)
    k.emit("Banners", col, root)
    # ---- the two magazine bays on the front cells
    for sx, Cc in ((1, FR), (-1, FL)):
        bay(k, rnd, col, root, sx, Cc)
    empty("Head", col, root, (C.x, C.y, BZ), 0.5, "SINGLE_ARROW")
    return root


def bay(k, rnd, col, root, sx, Cc):
    """One front cell: the blast wall round its front, the shell locker, the chute up to the barbette's hoist, a
    rack of shells."""
    C = BK
    tag = "R" if sx > 0 else "L"
    dv = Vector((Cc.x - C.x, Cc.y - C.y, 0)).normalized()       # out from the barbette toward this cell
    wv = Vector((-dv.y, dv.x, 0))
    cam = Vector((sx * 0.5, -0.866, 0))                          # the locker's side that faces the game camera
    yaw = math.degrees(math.atan2(dv.y, dv.x))
    # the blast wall: coursed blocks under a timber cap, round the cell's three front sides, posts at the bends
    angs = (0, 60, 120, 180) if sx > 0 else (180, 120, 60, 0)
    wp = [Cc + Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)) * 0.76 for a in angs]
    for p0, p1 in zip(wp, wp[1:]):
        bm_block_wall(k["stone:0.12:0.75"], rnd, p0, p1, T, T + 0.4, th=0.22, course=0.135, block=0.3)
    k.emit("Wall_" + tag, col, root, vary=0.08)
    for p0, p1 in zip(wp, wp[1:]):
        bm_beam(k["wood:0.55:0.95"], (p0.x, p0.y, T + 0.445), (p1.x, p1.y, T + 0.445), 0.27, 0.09)
    for p, a in zip(wp, angs):
        bm_box(k["wood_dark:0.2:0.75"], (0.15, 0.15, 0.62), (p.x, p.y, T + 0.3), (0, 0, a))
        bm_box(k["iron:0.3:0.8"], (0.17, 0.17, 0.04), (p.x, p.y, T + 0.5), (0, 0, a))
        bm_box(k["iron:0.3:0.8"], (0.17, 0.17, 0.04), (p.x, p.y, T + 0.14), (0, 0, a))
    k.emit("Wall_Timber_" + tag, col, root, vary=0.08)
    # the shell locker: thick planks bound in iron on a stone sill, a vaulted lid in the team's color
    Lc = Cc - dv * 0.05
    bm_box(k["stone_dark:0.2:0.6"], (0.94, 0.66, 0.08), (Lc.x, Lc.y, T + 0.03), (0, 0, yaw))
    for i in range(3):
        bm_box(k["wood_dark:0.15:0.7"], (0.8, 0.52, 0.106), (Lc.x, Lc.y, T + 0.07 + 0.11 * i + 0.053), (0, 0, yaw))
    k.emit("Locker_" + tag, col, root, bevel=0.01, vary=0.09)
    for z in (T + 0.13, T + 0.35):
        bm_box(k["iron:0.25:0.75"], (0.82, 0.54, 0.045), (Lc.x, Lc.y, z), (0, 0, yaw))
    for a, b in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        p = Lc + dv * (a * 0.39) + wv * (b * 0.25)
        bm_box(k["iron:0.25:0.75"], (0.07, 0.07, 0.36), (p.x, p.y, T + 0.25), (0, 0, yaw))
    pad = Lc + cam * 0.275
    bm_box(k["iron:0.3:0.8"], (0.06, 0.03, 0.14), (pad.x, pad.y, T + 0.36), (0, 0, yaw))
    bm_box(k["gold:0.1:0.5"], (0.1, 0.05, 0.09), (pad.x + cam.x * 0.02, pad.y + cam.y * 0.02, T + 0.27), (0, 0, yaw))
    hatch = Lc - dv * 0.405
    bm_box(k["iron:0.3:0.8"], (0.05, 0.3, 0.2), (hatch.x, hatch.y, T + 0.28), (0, 0, yaw))
    k.emit("Locker_Iron_" + tag, col, root)

    def lid(grow, s0, s1):
        rings = []
        for s in (s0, s1):
            rings.append([Lc + dv * s + wv * (math.cos(math.pi * i / 8) * (0.29 + grow)) +
                          ZV * (T + 0.4 + math.sin(math.pi * i / 8) * (0.17 + grow)) for i in range(9)])
        return rings
    bm_loft(k["team!:0.1:0.6"], lid(0.0, -0.43, 0.43))
    k.emit("Locker_Lid_" + tag, col, root, vary=0.05)
    for s in (-0.27, 0.27):
        bm_loft(k["gold:0.1:0.5"], lid(0.018, s - 0.03, s + 0.03))
    k.emit("Locker_Bands_" + tag, col, root)
    # the chute: a riveted iron trough from the locker's hatch up to the hoist, on a timber trestle, shells in it
    P0 = hatch - dv * 0.02 + ZV * (T + 0.3)
    P1 = Vector((C.x, C.y, 0)) + dv * 1.06 + ZV * (T + 0.66)
    x, y, z = frame3(P1 - P0)
    bm_beam(k["iron:0.3:0.8"], P0, P1, 0.26, 0.035)
    for s in (-1, 1):
        bm_beam(k["iron:0.3:0.8"], P0 + x * (s * 0.12) + z * 0.05, P1 + x * (s * 0.12) + z * 0.05, 0.03, 0.11)
    M = (P0 + P1) * 0.5
    for s in (-1, 1):
        bm_beam(k["wood_dark:0.2:0.7"], Vector((M.x, M.y, T)) + x * (s * 0.19), M - z * 0.02 + x * (s * 0.11), 0.06, 0.06)
    bm_beam(k["wood_dark:0.2:0.7"], Vector((M.x, M.y, T + 0.22)) + x * 0.17, Vector((M.x, M.y, T + 0.22)) - x * 0.17, 0.05, 0.05)
    k.emit("Chute_" + tag, col, root, vary=0.05)
    for s in (-1, 1):
        rivets(k["gold:0.1:0.5"], row(P0 + x * (s * 0.135) + z * 0.08, P1 + x * (s * 0.135) + z * 0.08, 5), x * s, r=0.02)
    for i in range(2):
        bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], P0 + y * (0.1 + 0.25 * i) + z * 0.075, y, 0.05, 0.22, band=k["orange:0.2:0.6"], n=6)
    rod(k["wood_dark:0.3:0.8"], P0 + z * 0.13, P1 + z * 0.13 + y * 0.05, 0.012, n=4)
    k.emit("Chute_Brass_" + tag, col, root)
    # the hoist: an iron shaft on the barbette's flank, banded in brass, a pulley wheel and a crank
    H = Vector((C.x, C.y, 0)) + dv * 0.9
    bm_box(k["iron:0.2:0.7"], (0.3, 0.26, 0.78), (H.x, H.y, T + 0.39), (0, 0, yaw + 90))
    k.emit("Hoist_" + tag, col, root, bevel=0.012)
    for zz in (T + 0.12, T + 0.45, T + 0.74):
        bm_box(k["gold:0.1:0.5"], (0.33, 0.29, 0.05), (H.x, H.y, zz), (0, 0, yaw + 90))
    W = H + dv * 0.25 + ZV * (T + 0.78)
    rod(k["gold:0.1:0.5"], W - wv * 0.03, W + wv * 0.03, 0.12, n=12)
    rod(k["iron:0.3:0.8"], W - wv * 0.08, W + wv * 0.08, 0.035, n=6)
    for s in (-1, 1):
        bm_beam(k["iron:0.3:0.8"], H + dv * 0.12 + wv * (s * 0.075) + ZV * (T + 0.78), W + wv * (s * 0.075), 0.03, 0.06)
    cr = H + wv * (sx * 0.17) + ZV * (T + 0.55)
    rod(k["gold:0.1:0.5"], cr, cr + wv * (sx * 0.04), 0.09, n=8)
    bm_beam(k["iron:0.3:0.8"], cr + wv * (sx * 0.05), cr + wv * (sx * 0.05) + ZV * 0.12 + dv * 0.04, 0.025, 0.025)
    k.emit("Hoist_Brass_" + tag, col, root)
    # a rack of shells by the locker, on the camera's side
    Rc = Lc + cam * 0.5 + dv * 0.04
    bm_box(k["wood:0.2:0.7"], (0.7, 0.3, 0.05), (Rc.x, Rc.y, T + 0.025), (0, 0, yaw))
    for s in (-1, 1):
        q = Rc + cam * (s * 0.12)
        bm_beam(k["wood:0.2:0.7"], q - dv * 0.35 + ZV * (T + 0.17), q + dv * 0.35 + ZV * (T + 0.17), 0.04, 0.04)
    for a, b in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        p = Rc + dv * (a * 0.33) + cam * (b * 0.12)
        bm_box(k["wood_dark:0.2:0.7"], (0.05, 0.05, 0.22), (p.x, p.y, T + 0.11), (0, 0, yaw))
    k.emit("Rack_" + tag, col, root, vary=0.07)
    for i in range(4):
        for s in (-1, 1):
            p = Rc + dv * (-0.24 + 0.16 * i) + cam * (s * 0.065)
            bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], (p.x, p.y, T + 0.05), (0, 0, 1), 0.05, 0.34, band=k["orange:0.2:0.6"], n=6)
    k.emit("Rack_Shells_" + tag, col, root)


# ---- the turret, in the head's space (+Y forward)
TPL, TPR = Vector((-GX, 0, EZ)), Vector((GX, 0, EZ))
BONES = {"root": ((0, 0, 0), (0, 0, 0.3), None),
         "elev": ((-0.3, 0, EZ), (0.3, 0, EZ), "root"),
         "scope": ((0, 0.2, 0.76), (0, 0.2, 0.96), "root"),
         "vane": (tuple(VANE), tuple(VANE + Vector((0, 0, 0.16))), "root")}
for _s, _tp in (("L", TPL), ("R", TPR)):
    BONES["gun." + _s] = (tuple(_tp), tuple(_tp + D * 0.3), "elev")
    BONES["spin." + _s] = (tuple(_tp + D * 0.36), tuple(_tp + D * 1.5), "gun." + _s)
    BONES["flash." + _s] = (tuple(_tp + D * 1.5), tuple(_tp + D * 1.7), "gun." + _s)
for _i in range(3):
    BONES["puff.%d" % _i] = (tuple(STACK), tuple(STACK + Vector((0, 0, 0.1))), "root")


def _oct(r, a):
    return Vector((r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 0))


def build_head():
    col = collection("Dwarf_gyro")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(5)
    k = Kit()
    # ---- the cupola: eight riveted plates over a brass skirt, a brass band, a roof of team-colored plates
    bm_cyl(k["gold:0.15:0.55"], 0.65, 0.63, 0.08, (0, 0, 0.04), seg=16)
    bm_cyl(k["gold:0.15:0.55"], 0.6, 0.6, 0.06, (0, 0, 0.5), seg=8, rot=(0, 0, 22.5))
    k.emit("Head_Skirt", col, rig=rig, bone="root")
    r0, r1, z0, z1 = 0.61, 0.56, 0.07, 0.48
    for i in range(8):
        a0, a1 = 22.5 + 45 * i, 22.5 + 45 * (i + 1)
        m = _oct(1.0, (a0 + a1) / 2)
        slab(k["iron:0.15:0.65"], [_oct(r0, a0) + ZV * z0, _oct(r0, a1) + ZV * z0, _oct(r1, a1) + ZV * z1, _oct(r1, a0) + ZV * z1], 0.07, m)
    bm_cyl(k["stone_dark:0.5:0.95"], 0.52, 0.48, 0.46, (0, 0, 0.27), seg=8, rot=(0, 0, 22.5))
    k.emit("Head_Cupola", col, rig=rig, bone="root", bevel=0.012, vary=0.07)
    for i in range(8):
        a, m = 22.5 + 45 * i, _oct(1.0, 22.5 + 45 * i)
        rivets(k["gold:0.1:0.5"], [_oct(0.6 - 0.04 * z / 0.48, a) + ZV * z for z in (0.17, 0.38)], m, r=0.024)
    k.emit("Head_Rivets", col, rig=rig, bone="root")
    for i in range(8):
        a0, a1 = 22.5 + 45 * i, 22.5 + 45 * (i + 1)
        m = _oct(1.0, (a0 + a1) / 2) + ZV * 0.9
        slab(k["team!:0.08:0.6"], [_oct(0.66, a0) + ZV * 0.52, _oct(0.66, a1) + ZV * 0.52, _oct(0.36, a1) + ZV * 0.72, _oct(0.36, a0) + ZV * 0.72], 0.05, m)
    k.emit("Head_Roof", col, rig=rig, bone="root", bevel=0.008, vary=0.06)
    for i in range(8):
        a = 22.5 + 45 * i
        bm_beam(k["gold:0.1:0.5"], _oct(0.67, a) + ZV * 0.535, _oct(0.36, a) + ZV * 0.735, 0.05, 0.035)
    bm_cyl(k["iron:0.2:0.7"], 0.38, 0.37, 0.05, (0, 0, 0.735), seg=8, rot=(0, 0, 22.5))
    bm_cyl(k["iron:0.3:0.8"], 0.2, 0.19, 0.05, (0, -0.04, 0.78), seg=10)
    bm_box(k["gold:0.1:0.5"], (0.07, 0.12, 0.04), (0, -0.25, 0.775))
    bm_beam(k["gold:0.1:0.5"], (-0.07, 0.06, 0.82), (0.07, 0.06, 0.82), 0.025, 0.025)
    k.emit("Head_Top", col, rig=rig, bone="root")
    # the vision slit at the front, the firebox at the back (toward the game camera), the exhaust stack
    bm_box(k["black:0.3:0.7"], (0.34, 0.06, 0.06), (0, 0.535, 0.34))
    bm_box(k["gold:0.1:0.5"], (0.44, 0.12, 0.035), (0, 0.56, 0.4), (-25, 0, 0))
    bm_box(k[EMBERS], (0.3, 0.04, 0.17), (0, -0.535, 0.22))
    k.emit("Head_Face", col, rig=rig, bone="root")
    for x in (-0.1, 0.0, 0.1):
        bm_box(k["iron:0.3:0.8"], (0.03, 0.03, 0.2), (x, -0.565, 0.22))
    bm_box(k["gold:0.1:0.5"], (0.38, 0.03, 0.03), (0, -0.56, 0.32))
    bm_box(k["gold:0.1:0.5"], (0.38, 0.03, 0.03), (0, -0.56, 0.12))
    sb = Vector((STACK.x, STACK.y + 0.05, 0.56))
    rod(k["iron:0.25:0.75"], sb, STACK - ZV * 0.06, 0.06, 0.055, n=8)
    rod(k["gold:0.1:0.5"], sb + ZV * 0.12, sb + ZV * 0.18, 0.085, n=8)
    rod(k["iron:0.3:0.8"], STACK - ZV * 0.08, STACK + ZV * 0.02, 0.07, 0.1, n=8)
    k.emit("Head_Stack", col, rig=rig, bone="root")
    bm_cyl(k[EMBERS], 0.06, 0.06, 0.02, tuple(STACK + ZV * 0.005), seg=8)
    k.emit("Head_Stack_Glow", col, rig=rig, bone="root")
    # the vane's mast, the scope's post
    rod(k["iron:0.3:0.8"], Vector((VANE.x, VANE.y, 0.6)), VANE + ZV * 0.04, 0.025, 0.02, n=6)
    rod(k["gold:0.1:0.5"], Vector((VANE.x, VANE.y, 0.68)), Vector((VANE.x, VANE.y, 0.74)), 0.05, n=6)
    k.emit("Head_Mast", col, rig=rig, bone="root")
    # ---- the gun cheeks: riveted iron brackets with brass bosses, the trunnion pins through them
    for sx in (-1, 1):
        bm_box(k["iron:0.2:0.65"], (0.14, 0.44, 0.42), (sx * 0.6, 0, 0.36))
        rod(k["gold:0.1:0.5"], Vector((sx * 0.66, 0, EZ)), Vector((sx * 0.7, 0, EZ)), 0.14, n=10)
        rod(k["iron:0.3:0.8"], Vector((sx * 0.6, 0, EZ)), Vector((sx * (GX - 0.1), 0, EZ)), 0.06, n=8)
    k.emit("Head_Cheeks", col, rig=rig, bone="elev")
    for sx in (-1, 1):
        rivets(k["gold:0.1:0.5"], [Vector((sx * 0.675, y, z)) for y in (-0.17, 0.17) for z in (0.22, 0.5)], (sx, 0, 0), r=0.022)
    k.emit("Head_Cheek_Rivets", col, rig=rig, bone="elev")
    # ---- the guns: a receiver drum with a brass magazine, then six barrels round an axle in brass clamps
    for s, sx, tp in (("L", -1, TPL), ("R", 1, TPR)):
        X = Vector((sx, 0, 0))
        rod(k["iron:0.15:0.6"], tp - D * 0.3, tp + D * 0.36, 0.16, n=8)
        rod(k["iron:0.25:0.7"], tp - D * 0.3, tp - D * 0.38, 0.14, 0.07, n=8)
        k.emit("Head_Gun%s" % s, col, rig=rig, bone="gun." + s)
        for u in (-0.26, 0.3):
            rod(k["gold:0.1:0.5"], tp + D * (u - 0.035), tp + D * (u + 0.035), 0.175, n=8)
        rod(k["gold:0.12:0.55"], tp + X * 0.15 + D * 0.03, tp + X * 0.3 + D * 0.03, 0.2, n=12)
        rod(k["iron:0.3:0.8"], tp + X * 0.29 + D * 0.03, tp + X * 0.33 + D * 0.03, 0.09, n=8)
        rivets(k["iron:0.3:0.8"], [tp + X * 0.3 + D * 0.03 + (D * math.cos(a) + GZ * math.sin(a)) * 0.15 for a in
                                    (math.radians(30 + 60 * j) for j in range(6))], X, r=0.02)
        k.emit("Head_Gun%s_Brass" % s, col, rig=rig, bone="gun." + s)
        rod(k["iron:0.2:0.6"], tp + D * 0.34, tp + D * 0.5, 0.14, 0.13, n=8)
        rod(k["iron:0.1:0.5"], tp + D * 0.4, tp + D * 1.46, 0.04, n=6)
        for j in range(6):
            a = math.radians(60 * j)
            o = (X * math.cos(a) + GZ * math.sin(a)) * 0.095
            rod(k["iron:0.25:0.75"], tp + D * 0.45 + o, tp + D * 1.52 + o, 0.036, n=6)
            rod(k["black:0.3:0.7"], tp + D * 1.515 + o, tp + D * 1.525 + o, 0.024, n=5)
        for u, w, sw in ((0.62, 0.05, "gold:0.1:0.5"), (1.02, 0.05, "gold:0.1:0.5"), (1.42, 0.06, "iron:0.3:0.8")):
            rod(k[sw], tp + D * (u - w), tp + D * (u + w), 0.15, n=12)
        k.emit("Head_Barrels%s" % s, col, rig=rig, bone="spin." + s)
        # the muzzle flash (hidden at rest: scaled down on its bone)
        f0 = tp + D * 1.5
        bm_crystal(k[FLARE], f0, f0 + D * 0.5, 0.1, n=5, shoulder=0.35)
        for j in range(4):
            a = math.radians(45 + 90 * j)
            sd = X * math.cos(a) + GZ * math.sin(a)
            bm_crystal(k[FLARE], f0 + D * 0.02, f0 + D * 0.2 + sd * 0.26, 0.05, n=4, shoulder=0.35)
        k.emit("Head_Flash%s" % s, col, rig=rig, bone="flash." + s)
    # ---- the spotting scope on its fork, the wind vane, the smoke puffs
    rod(k["iron:0.3:0.8"], (0, 0.2, 0.74), (0, 0.2, 0.86), 0.03, n=6)
    bm_box(k["iron:0.3:0.8"], (0.14, 0.04, 0.05), (0, 0.2, 0.87))
    for sx in (-1, 1):
        bm_box(k["iron:0.3:0.8"], (0.02, 0.04, 0.09), (sx * 0.06, 0.2, 0.92))
    k.emit("Head_ScopePost", col, rig=rig, bone="scope")
    rod(k["gold:0.1:0.5"], (0, -0.02, 0.92), (0, 0.42, 0.97), 0.04, 0.05, n=8)
    rod(k["gold:0.15:0.6"], (0, 0.4, 0.968), (0, 0.46, 0.975), 0.06, n=8)
    rod(k["iron:0.3:0.8"], (0, -0.08, 0.912), (0, -0.02, 0.92), 0.026, n=6)
    rod(k["sky:0.0:0.3"], (0, 0.46, 0.975), (0, 0.465, 0.976), 0.045, n=8)
    k.emit("Head_Scope", col, rig=rig, bone="scope")
    v = VANE + ZV * 0.06
    bm_beam(k["iron:0.3:0.8"], v - Vector((0, 0.24, 0)), v + Vector((0, 0.2, 0)), 0.025, 0.025)
    bm_crystal(k["gold:0.1:0.5"], v + Vector((0, 0.18, 0)), v + Vector((0, 0.32, 0)), 0.05, n=4, shoulder=0.2)
    rod(k["gold:0.1:0.5"], v - ZV * 0.08, v + ZV * 0.05, 0.022, n=6)
    bm_ellipsoid(k["gold:0.1:0.5"], tuple(v + ZV * 0.08), (0.04, 0.04, 0.04), u=6, v=4)
    k.emit("Head_Vane", col, rig=rig, bone="vane")
    slab(k["team!:0.1:0.6"], [v + Vector((0, -0.12, -0.02)), v + Vector((0, -0.34, 0.1)), v + Vector((0, -0.34, -0.14)), v + Vector((0, -0.12, -0.06))], 0.016, (1, 0, 0))
    k.emit("Head_VaneFin", col, rig=rig, bone="vane")
    for i in range(3):
        rp = random.Random(30 + i)
        bm_blob(k["white:0.0:0.25"], rp, tuple(STACK + Vector((0.02, 0, 0.09))), 0.12 - 0.012 * i, squash=(1.2, 1.1, 0.85), jitter=0.12)
        bm_blob(k["white:0.0:0.25"], rp, tuple(STACK + Vector((-0.06, -0.03, 0.06))), 0.08, squash=(1.1, 1.1, 0.85), jitter=0.12)
        k.emit("Head_Puff%d" % i, col, rig=rig, bone="puff.%d" % i)
    empty("Muzzle1", col, head, tuple(TPL + D * 1.6), 0.2, "SPHERE")
    empty("Muzzle2", col, head, tuple(TPR + D * 1.6), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 12


def pose(rig, elev=0.0, scan=0.0, vane=0.0, kick=(0.0, 0.0), spin=(0.0, 0.0), flash=(0.0, 0.0), puff=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["elev"].rotation_quaternion = q(pb["elev"], (1, 0, 0), elev)
    for i, s in enumerate(("L", "R")):
        g = pb["gun." + s]
        g.location = arm_space_loc(g, -D * (0.12 * kick[i]))
        sp = pb["spin." + s]
        sp.rotation_quaternion = q(sp, D, spin[i])
        fl = pb["flash." + s]
        v = max(flash[i], 0.02)
        fl.scale = (v, v, v)
    pb["scope"].rotation_quaternion = q(pb["scope"], (0, 0, 1), scan)
    pb["vane"].rotation_quaternion = q(pb["vane"], (0, 0, 1), vane)
    for i in range(3):
        u = (puff + i / 3.0) % 1.0
        b = pb["puff.%d" % i]
        b.location = arm_space_loc(b, (-0.05 * u, -0.18 * u, 0.6 * u))
        s = (0.35 + 0.95 * u) * min(1.0, u / 0.08) * min(1.0, (1.0 - u) / 0.3)
        b.scale = (max(s, 0.02),) * 3


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(IDLE_LEN + 1):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        pose(rig, elev=5.0 * math.sin(ph), scan=30.0 * math.sin(ph) + 8.0 * math.sin(3 * ph),
             vane=24.0 * math.sin(2 * ph) + 9.0 * math.sin(5 * ph), puff=2.0 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        spin = 360.0 * f / FIRE_LEN
        kl = ease([(0, 0), (1, 1), (4, 0.15), (7, 0)], f)
        kr = ease([(0, 0), (5, 0), (6, 1), (9, 0.15), (12, 0)], f)
        fl = ease([(0, 0), (1, 1.15), (2, 0.7), (3, 0)], f)
        fr = ease([(0, 0), (5, 0), (6, 1.15), (7, 0.7), (8, 0)], f)
        pose(rig, elev=-2.5 * (kl + kr), kick=(kl, kr), spin=(spin, -spin), flash=(fl, fr), puff=0.0)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, -0.1, 1.3), "dist": 9.0, "yaw": 150, "pitch": 20, "anim_target": (BK.x, BK.y + 0.4, BZ + 0.7), "anim_dist": 5.4,
           "frames": [("idle", 0), ("idle", 30), ("fire", 1), ("fire", 6), ("fire", 9)],
           "extra": [{"yaw": 20, "pitch": 42, "dist": 4.2, "target": (BK.x, BK.y, BZ + 0.6)},
                     {"yaw": 145, "pitch": 30, "dist": 4.4, "target": (FR.x - 0.3, FR.y - 0.1, 0.6)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
