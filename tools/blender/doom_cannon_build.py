"""Builds the Doomsday Cannon (footprint "arrow5": [0,0] the tip in front, [1,0] / [-1,1] the flanks, [0,1] / [0,2] the
two cells trailing behind), the Deep Forge's Tier IV siege gun: one colossal shell every few seconds, lobbed across
the map.

    python tools/blender/build.py doom_cannon --out <preview dir>

One gun, laid out down the arrow like a fortress piece on its traversing platform. Over the front cell a great
toothed ring of stone and iron carries the pivot; from it a chassis of two long recoil rails runs back to iron trucks
on a curved racer rail laid across the flanks and the first trailing cell (the racer is the gun's 120 degree arc). On
the rails rides a massive wheeled carriage, and in its cheeks on huge trunnions lies the cannon: a banded iron barrel,
brass-ringed, the team's band round its chase, ending in a brass dragon's head whose open jaws are the muzzle. The
chassis carries the loading crane (by the breech, its hook over the shells) and the engineer's footboard (Crew). A
pyramid of man-sized shells waits on the left flank, the powder house with its glowing chimney on the right, and a
narrow track runs back over the trailing cells to buffer stops, a trolley with the next shell on it. All of the
platform, chassis, carriage, gun and crane is the Head (it turns within the arc; Muzzle is in the dragon's jaws).
idle: smoke curls from the dragon's mouth, the crane drifts, its hook sways, the pennant flies.
fire: the gun settles, then slams back up the rails: the dragon spits fire, a ring of smoke, the carriage rears and
      crashes down. It ends run back; reload: the carriage runs forward to its stops, the crane swings a shell over
      the breech, it drops in, and the crane swings back to the pile and takes the next.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forge_guns_common.py"), encoding="utf-8").read())

TID = "doom_cannon"
CELLS = [(0, 0), (1, 0), (-1, 1), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
R = hex_to_world(1, 0, MID)
L = hex_to_world(-1, 1, MID)
B1 = hex_to_world(0, 1, MID)
B2 = hex_to_world(0, 2, MID)
TOP = 0.34
T = TOP
PIV = Vector((0.0, 1.2, 0.0))           # the pivot (the Head): the great toothed ring's middle
RACER = 1.5                              # the racer rail's radius round the pivot
X = Vector((1, 0, 0))
ZV = Vector((0, 0, 1))
EL = 40.0                                # the barrel's elevation
E = Vector((0.0, math.cos(math.radians(EL)), math.sin(math.radians(EL))))
U = X.cross(E)                           # square to the barrel, upward
TC = Vector((0.0, 0.0, T + 1.7))         # the trunnions (head space)
WHEEL_R = 0.28
WHEELS = {"wheel.L1": (-0.69, 0.42), "wheel.R1": (0.69, 0.42), "wheel.L2": (-0.69, -0.48), "wheel.R2": (0.69, -0.48)}
MAST = Vector((-1.0, -0.55, T + 0.56))   # the crane's foot (head space)
TIP = Vector((-2.15, -0.55, T + 2.1))    # the jib's end, where the hook hangs
CREW = Vector((1.02, -0.82, T + 0.6))
EMB = "glow:1.0,0.4,0.06,0.9"            # embers: the dragon's eyes and throat, the chimney
PL = Vector((-2.25, 0.62, 0.0))          # the shell pile
PH = Vector((2.2, 0.62, 0.0))            # the powder house


def zc(y):
    """The chassis rails' middle height at y (head space): they climb a little toward the back."""
    return T + 0.41 + (0.85 - y) * 0.0653


def bpt(s, u=0.0, x=0.0):
    """A point in the barrel's frame: s along it from the trunnions, u up from its axis, x across."""
    return TC + E * s + U * u + X * x


def build_base():
    col = collection("Doom_cannon")
    root = empty("Doom_cannon", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(23)
    k = Kit()
    p0 = (PIV.x, PIV.y, 0)
    # ---- the yard: flagstones everywhere but the ring and the track's bed
    bm_flagstones(k["stone2:0.15:0.7"], rnd, lambda x, y: in_footprint(CELLS, x, y, 0.22) and (x - PIV.x) ** 2 + (y - PIV.y) ** 2 > 1.05 ** 2
                  and not (abs(x) < 0.42 and y < -0.3), (-3.0, -3.6, 3.0, 2.8), T, size=0.34, keep=1.0)
    k.emit("Yard", col, root, vary=0.09)
    prism(k["stone_dark:0.45:0.95"], [Vector(p) for p in ((-0.4, -0.45, 0), (0.4, -0.45, 0), (0.4, -1.3, 0), (0.36, -1.455, 0), (0.4, -1.61, 0),
                                                         (0.4, -2.85, 0), (-0.4, -2.85, 0), (-0.4, -1.61, 0), (-0.36, -1.455, 0), (-0.4, -1.3, 0))], T - 0.01, T + 0.02)
    k.emit("Ballast", col, root)
    # ---- the great toothed ring: a course of big blocks, a dark floor, the iron rack of teeth on top
    bm_block_course(k["stone:0.12:0.8"], rnd, p0, 1.1, T - 0.01, 0.17, 16, depth=0.3)
    k.emit("Ring", col, root, vary=0.08)
    bm_cyl(k["stone_dark:0.4:0.9"], 0.84, 0.84, 0.04, (PIV.x, PIV.y, T + 0.14), seg=16)
    k.emit("Ring_Floor", col, root)
    gear_ring(k["iron:0.3:0.8"], p0, 1.02, T + 0.15, T + 0.23, 30, depth=0.08, r_in=0.84)
    k.emit("Ring_Teeth", col, root)
    # ---- the racer: a curved iron rail on a stone curb, the gun's arc, stops at its ends
    bm_block_course(k["stone:0.12:0.8"], rnd, p0, 1.72, T - 0.01, 0.11, 26, depth=0.42, skip=lambda a: not (190 <= a <= 350))
    k.emit("Racer_Curb", col, root, vary=0.08)
    for i in range(16):
        a0, a1 = math.radians(192 + 156 * i / 16), math.radians(192 + 156 * (i + 1) / 16)
        bm_beam(k["iron:0.3:0.8"], (PIV.x + RACER * math.cos(a0), PIV.y + RACER * math.sin(a0), T + 0.13),
                (PIV.x + RACER * math.cos(a1), PIV.y + RACER * math.sin(a1), T + 0.13), 0.08, 0.06)
    for a in (191, 349):
        box_on(k["iron:0.3:0.8"], (0.14, 0.22, 0.14), (PIV.x + RACER * math.cos(math.radians(a)), PIV.y + RACER * math.sin(math.radians(a)), T + 0.17),
               (-math.sin(math.radians(a)), math.cos(math.radians(a))))
    k.emit("Racer_Rail", col, root)
    # ---- the track back over the trailing cells: sleepers, two rails, buffer stops, the trolley with the next shell
    y = -0.62
    while y > -2.75:
        if abs(y + 1.455) > 0.13:
            bm_box(k["wood_dark:0.3:0.8"], (0.72, 0.12, 0.05), (0, y + rnd.uniform(-0.02, 0.02), T + 0.03), (0, 0, rnd.uniform(-3, 3)))
        y -= 0.3
    k.emit("Track_Sleepers", col, root, vary=0.08)
    for x in (-0.25, 0.25):
        bm_beam(k["iron:0.3:0.8"], (x, -0.52, T + 0.08), (x, -2.72, T + 0.08), 0.06, 0.06)
    k.emit("Track_Rails", col, root)
    bm_block_wall(k["stone:0.12:0.8"], rnd, (-0.52, -3.0), (0.52, -3.0), T, T + 0.4, th=0.26, course=0.135, block=0.3)
    k.emit("Buffers", col, root, vary=0.08)
    for x in (-0.25, 0.25):
        bm_beam(k["wood_dark:0.2:0.7"], (x, -2.9, T + 0.25), (x, -2.7, T + 0.25), 0.15, 0.15)
        rod(k["iron:0.3:0.8"], (x, -2.72, T + 0.25), (x, -2.67, T + 0.25), 0.1, n=10)
    k.emit("Buffer_Beams", col, root)
    slab(k["team!:0.1:0.6"], [(-0.5, -3.165, T + 0.08), (0.5, -3.165, T + 0.08), (0.5, -3.165, T + 0.36), (-0.5, -3.165, T + 0.36)], 0.03, (0, -1, 0))
    slab(k["team!:0.1:0.6"], [(-0.5, -2.98, T + 0.4), (0.5, -2.98, T + 0.4), (0.5, -2.98, T + 0.56), (-0.5, -2.98, T + 0.56)], 0.12, (0, -1, 0))
    k.emit("Buffer_Board", col, root)
    ty = -1.92
    bm_planks(k["wood:0.4:0.9"], rnd, (-0.32, ty - 0.45, T + 0.27), (0, 0.9, 0), (0.64, 0, 0), 4, th=0.05)
    for x in (-0.3, 0.3):
        bm_beam(k["wood_dark:0.2:0.7"], (x, ty - 0.46, T + 0.2), (x, ty + 0.46, T + 0.2), 0.07, 0.1)
    for y2 in (ty - 0.22, ty + 0.22):
        bm_box(k["wood_dark:0.2:0.7"], (0.44, 0.1, 0.12), (0, y2, T + 0.31))
    k.emit("Trolley", col, root, vary=0.07)
    for x in (-0.25, 0.25):
        for y2 in (ty - 0.3, ty + 0.3):
            rod(k["iron:0.25:0.7"], (x - 0.035, y2, T + 0.19), (x + 0.035, y2, T + 0.19), 0.085, n=10)
    k.emit("Trolley_Wheels", col, root)
    bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], (0, ty - 0.52, T + 0.5), (0, 1, 0), 0.2, 1.0, band=k["orange:0.2:0.6"], n=10, rim=True)
    k.emit("Trolley_Shell", col, root)
    # ---- the left flank: a pyramid of man-sized shells on a timber cradle, two more stood by it
    for x in (PL.x - 0.22, PL.x + 0.22):
        bm_beam(k["wood_dark:0.2:0.7"], (x, PL.y - 0.52, T + 0.04), (x, PL.y + 0.52, T + 0.04), 0.1, 0.08)
    for y2 in (PL.y - 0.52, PL.y + 0.52):
        bm_box(k["wood_dark:0.2:0.7"], (0.56, 0.08, 0.14), (PL.x, y2, T + 0.12))
    k.emit("Pile_Cradle", col, root, vary=0.07)
    rows = [(-0.33, 0.24), (0.0, 0.24), (0.33, 0.24), (-0.165, 0.517), (0.165, 0.517), (0.0, 0.794)]
    for dy, z in rows:
        bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], (PL.x + 0.39, PL.y + dy, T + z), (-1, 0, 0), 0.16, 0.78, band=k["orange:0.2:0.6"], n=8)
    for dx, dy in ((0.3, -0.66), (-0.08, -0.7)):
        bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], (PL.x + dx, PL.y + dy, T), (0, 0, 1), 0.16, 0.78, band=k["orange:0.2:0.6"], n=8, rim=True)
    k.emit("Pile", col, root, vary=0.04)
    # ---- the right flank: the powder house, stone under a roof of the team's tiles, a chimney glowing at the top
    hx, hy = 0.34, 0.35
    bm_box(k["stone_dark:0.2:0.6"], (2 * hx + 0.14, 2 * hy + 0.14, 0.08), (PH.x, PH.y, T + 0.03))
    cs = [(PH.x - hx, PH.y - hy), (PH.x + hx, PH.y - hy), (PH.x + hx, PH.y + hy), (PH.x - hx, PH.y + hy)]
    for a, b in zip(cs, cs[1:] + cs[:1]):
        bm_block_wall(k["stone:0.12:0.8"], rnd, a, b, T + 0.07, T + 0.66, th=0.16, course=0.2, block=0.36)
    k.emit("House", col, root, vary=0.08)
    for sx in (-1, 1):          # the gable ends
        gx = PH.x + sx * (hx - 0.02)
        slab(k["stone_warm:0.2:0.7"], [(gx, PH.y - hy, T + 0.65), (gx, PH.y + hy, T + 0.65), (gx, PH.y, T + 1.08)], 0.12, (sx, 0, 0))
    bm_beam(k["wood_dark:0.2:0.7"], (PH.x - hx - 0.14, PH.y, T + 1.1), (PH.x + hx + 0.14, PH.y, T + 1.1), 0.08, 0.08)
    k.emit("House_Gables", col, root, vary=0.06)
    for sy in (-1, 1):
        e = PH.y + sy * (hy + 0.14)
        bm_tile_slope(k["team!:0.1:0.7"], rnd, (PH.x - hx - 0.14, e, T + 0.6), (PH.x + hx + 0.14, e, T + 0.6),
                      (PH.x - hx - 0.14, PH.y, T + 1.1), (PH.x + hx + 0.14, PH.y, T + 1.1), rows=4, cols=5)
    k.emit("House_Roof", col, root, vary=0.08)
    cx, cy = PH.x + 0.2, PH.y + 0.16
    for i in range(4):
        bm_box(k["stone_dark:0.15:0.65"], (0.25, 0.25, 0.235), (cx + rnd.uniform(-0.01, 0.01), cy + rnd.uniform(-0.01, 0.01), T + 0.62 + 0.24 * i + 0.12),
               (0, 0, rnd.uniform(-4, 4)))
    bm_box(k["stone:0.1:0.5"], (0.33, 0.33, 0.06), (cx, cy, T + 1.62))
    for ox, oy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bm_box(k["stone:0.1:0.5"], (0.06, 0.06, 0.1), (cx + ox * 0.12, cy + oy * 0.12, T + 1.7))
    bm_box(k["stone:0.1:0.5"], (0.3, 0.3, 0.04), (cx, cy, T + 1.77))
    k.emit("Chimney", col, root, vary=0.08)
    bm_box(k[EMB], (0.18, 0.18, 0.1), (cx, cy, T + 1.66))
    bm_box(k[EMB], (0.14, 0.03, 0.12), (PH.x - 0.2, PH.y - hy - 0.075, T + 0.42))
    k.emit("Embers", col, root)
    door_y = PH.y - hy - 0.08
    bm_planks(k["wood_dark:0.2:0.7"], rnd, (PH.x + 0.02, door_y + 0.03, T + 0.07), (0, 0, 0.44), (0.26, 0, 0), 3, th=0.05)
    k.emit("House_Door", col, root, vary=0.08)
    bm_box(k["stone_warm:0.2:0.7"], (0.42, 0.1, 0.08), (PH.x + 0.15, door_y + 0.02, T + 0.55))
    for z in (T + 0.17, T + 0.41):
        bm_box(k["iron:0.3:0.8"], (0.28, 0.02, 0.04), (PH.x + 0.15, door_y - 0.02, z))
    bm_box(k["iron:0.3:0.8"], (0.2, 0.03, 0.03), (PH.x - 0.2, PH.y - hy - 0.09, T + 0.42))
    k.emit("House_Trim", col, root)
    for (x, y2) in ((1.72, 0.2), (1.98, 0.06), (1.8, -0.1)):
        bm_keg(k["wood:0.35:0.85"], k["iron:0.3:0.8"], (x, y2, T), 0.14, 0.34)
    k.emit("Kegs", col, root, vary=0.06)
    empty("Head", col, root, tuple(PIV), 0.6, "SINGLE_ARROW")
    return root


# ---- the gun, in the head's space (+Y forward)
BONES = {"root": ((0, 0, T), (0, 0, T + 0.3), None),
         "carriage": ((0, -0.48, T + 0.867), (0, 0.42, T + 0.808), "root"),
         "barrel": (tuple(TC), tuple(TC + E * 0.4), "carriage"),
         "flash": (tuple(bpt(2.2)), tuple(bpt(2.5)), "barrel"),
         "smoke": (tuple(bpt(2.35)), tuple(bpt(2.6)), "root"),
         "crane": (tuple(MAST), tuple(MAST + ZV * 0.3), "root"),
         "hook": (tuple(TIP), tuple(TIP - ZV * 0.25), "crane"),
         "load": (tuple(TIP - ZV * 1.1), tuple(TIP - ZV * 1.3), "hook")}
for _n, (_x, _y) in WHEELS.items():
    _z = zc(_y) + 0.09 + WHEEL_R
    BONES[_n] = ((_x, _y, _z), (_x + 0.15 * (1 if _x > 0 else -1), _y, _z), "carriage")
for _i in range(2):
    BONES["wisp.%d" % _i] = (tuple(bpt(2.25, 0.0)), tuple(bpt(2.25, 0.0) + ZV * 0.2), "root")
flag_bones(BONES, "pen", (MAST.x, MAST.y, T + 2.52), (0, -1, 0), 0.62, segs=3, parent="crane")


def build_head():
    col = collection("Doom_cannon")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(9)
    k = Kit()
    # ---- the pivot plate and the chassis: two long recoil rails on transoms, trucks on the racer behind
    bm_cyl(k["wood:0.45:0.9"], 0.84, 0.84, 0.06, (0, 0, T + 0.265), seg=16)
    k.emit("Head_Plate", col, rig=rig, bone="root", vary=0.05)
    ring(k["iron:0.3:0.8"], (0, 0, 0), 0.87, 0.8, T + 0.225, T + 0.305, seg=16)
    k.emit("Head_PlateRim", col, rig=rig, bone="root")
    for sx in (-1, 1):
        bm_beam(k["wood_dark:0.2:0.7"], (sx * 0.69, 0.85, zc(0.85)), (sx * 0.69, -1.5, zc(-1.5)), 0.16, 0.18)
    for y in (0.7, 0.0, -0.75, -1.38):
        bm_box(k["wood_dark:0.2:0.7"], (1.62, 0.2, 0.14), (0, y, zc(y) - 0.06))
    k.emit("Head_Chassis", col, rig=rig, bone="root", vary=0.08)
    for sx in (-1, 1):
        bm_beam(k["iron:0.3:0.8"], (sx * 0.69, 0.85, zc(0.85) + 0.095), (sx * 0.69, -1.5, zc(-1.5) + 0.095), 0.1, 0.025)
        bm_box(k["iron:0.25:0.7"], (0.2, 0.1, 0.13), (sx * 0.69, 0.79, zc(0.79) + 0.15))
        bm_box(k["wood_dark:0.2:0.6"], (0.2, 0.12, 0.22), (sx * 0.69, -1.45, zc(-1.45) + 0.2))
        rod(k["iron:0.25:0.7"], (sx * 0.69, -1.395, zc(-1.45) + 0.2), (sx * 0.69, -1.38, zc(-1.45) + 0.2), 0.08, n=8)
        bm_box(k["iron:0.25:0.7"], (0.07, 0.26, 0.2), (sx * 0.42, -1.44, T + 0.37))
        rod(k["iron:0.3:0.8"], (sx * 0.42, -1.54, T + 0.29), (sx * 0.42, -1.34, T + 0.29), 0.035, n=6)
    rod(k["iron:0.25:0.7"], (0, 0, T + 0.28), (0, 0, zc(0) + 0.03), 0.17, n=8)
    k.emit("Head_ChassisIron", col, rig=rig, bone="root")
    for sx in (-1, 1):
        rod(k["iron:0.2:0.65"], (sx * 0.42, -1.48, T + 0.29), (sx * 0.42, -1.4, T + 0.29), 0.13, n=10)
    k.emit("Head_Trucks", col, rig=rig, bone="root")
    # the crane's outrigger (left) and the engineer's footboard with its rail (right)
    bm_planks(k["wood:0.4:0.9"], rnd, (-1.24, -0.95, T + 0.56), (0.47, 0, 0), (0, 0.8, 0), 4, th=0.05)
    bm_planks(k["wood:0.4:0.9"], rnd, (0.77, -1.28, T + 0.6), (0.44, 0, 0), (0, 0.94, 0), 5, th=0.05)
    k.emit("Head_Boards", col, rig=rig, bone="root", vary=0.08)
    for y in (-0.85, -0.25):
        bm_beam(k["wood_dark:0.2:0.7"], (-0.77, y, zc(y) - 0.08), (-1.16, y, T + 0.5), 0.07, 0.07)
    for y in (-1.2, -0.5):
        bm_beam(k["wood_dark:0.2:0.7"], (0.77, y, zc(y) - 0.08), (1.2, y, T + 0.54), 0.07, 0.07)
    for y in (-1.2, -0.42):
        bm_box(k["wood_dark:0.2:0.7"], (0.06, 0.06, 0.48), (1.17, y, T + 0.82))
    bm_beam(k["wood_dark:0.2:0.7"], (1.17, -1.24, T + 1.04), (1.17, -0.38, T + 1.04), 0.06, 0.06)
    k.emit("Head_Braces", col, rig=rig, bone="root", vary=0.06)
    # ---- the carriage: two stepped timber cheeks bound in iron, transoms, axles, four great wheels
    for sx in (-1, 1):
        xo = sx * 0.595
        for pts in ([(0.72, 0.66), (0.72, 1.0), (0.32, 1.62), (-0.22, 1.62), (-0.28, 0.68)],
                    [(-0.24, 0.68), (-0.24, 1.34), (-0.64, 1.3), (-0.72, 1.06), (-0.72, 0.7)]):
            slab(k["wood:0.35:0.85"], [Vector((xo, y, T + z)) for y, z in pts], 0.14, (sx, 0, 0))
    bm_box(k["wood:0.35:0.85"], (0.88, 0.16, 0.3), (0, 0.55, T + 0.86))
    bm_box(k["wood:0.35:0.85"], (0.88, 0.18, 0.13), (0, -0.6, T + 0.76))
    k.emit("Head_Carriage", col, rig=rig, bone="carriage", bevel=0.014, vary=0.08)
    for sx in (-1, 1):
        xo = sx * 0.61
        for y, z1 in ((0.45, 1.4), (0.0, 1.6), (-0.48, 1.3)):
            bm_box(k["iron:0.25:0.7"], (0.03, 0.07, z1 - 0.68), (xo, y, T + (0.68 + z1) / 2))
        bm_box(k["iron:0.2:0.65"], (0.18, 0.36, 0.07), (sx * 0.525, 0.0, T + 1.86))
        for y in (-0.16, 0.16):
            bm_box(k["iron:0.2:0.65"], (0.05, 0.05, 0.26), (sx * 0.525, y, T + 1.72))
    for y, z in ((0.42, zc(0.42) + 0.09 + WHEEL_R), (-0.48, zc(-0.48) + 0.09 + WHEEL_R)):
        rod(k["iron:0.3:0.8"], (-0.78, y, z), (0.78, y, z), 0.05, n=8)
    k.emit("Head_CarriageIron", col, rig=rig, bone="carriage")
    rivets(k["gold:0.1:0.5"], [Vector((sx * 0.625, y, T + z)) for sx in (-1, 1) for y, z in ((0.45, 0.78), (0.45, 1.3), (0.0, 0.78), (0.0, 1.5), (-0.48, 0.78), (-0.48, 1.2))],
           lambda p: (1 if p.x > 0 else -1, 0, 0), r=0.03)
    hw = Vector((0.6, -0.06, T + 1.38))                      # the elevating handwheel on the right cheek
    rod(k["gold:0.1:0.5"], hw, hw + X * 0.04, 0.14, n=10)
    rod(k["iron:0.3:0.8"], hw - X * 0.02, hw + X * 0.1, 0.03, n=6)
    k.emit("Head_CarriageBrass", col, rig=rig, bone="carriage")
    for n, (x, y) in WHEELS.items():
        z = zc(y) + 0.09 + WHEEL_R
        bm_wheel(k["iron:0.2:0.65"], k["wood:0.4:0.85"], k["gold:0.1:0.5"], (x, y, z), (1, 0, 0), WHEEL_R, 0.12, n_spokes=6, seg=10)
        k.emit("Head_" + n.replace(".", ""), col, rig=rig, bone=n)
    # ---- the barrel: banded iron, brass rings, the team's band on the chase, huge trunnions, a cascabel
    st = [(-0.98, 0.37), (-0.95, 0.45), (-0.17, 0.44), (-0.13, 0.41), (0.62, 0.39), (0.66, 0.35), (1.35, 0.33), (1.6, 0.36), (1.95, 0.37)]
    bm_loft(k["iron:0.12:0.6"], [oval(bpt(s), X, U, r, r, 12) for s, r in st])
    rod(k["iron:0.15:0.6"], bpt(-0.98), bpt(-1.06), 0.22, 0.1, n=10)
    rod(k["iron:0.15:0.6"], bpt(-1.04), bpt(-1.12), 0.07, n=8)
    bm_ellipsoid(k["iron:0.15:0.6"], tuple(bpt(-1.18)), (0.12, 0.12, 0.12), u=8, v=5)
    rod(k["iron:0.2:0.7"], TC - X * 0.6, TC + X * 0.6, 0.13, n=10)
    k.emit("Head_Barrel", col, rig=rig, bone="barrel")
    for s0, s1, r in ((-0.99, -0.89, 0.48), (-0.19, -0.09, 0.48), (0.58, 0.68, 0.44), (1.52, 1.6, 0.4)):
        rod(k["gold:0.1:0.5"], bpt(s0), bpt(s1), r, n=12)
    for sx in (-1, 1):
        rod(k["gold:0.1:0.5"], TC + X * (sx * 0.58), TC + X * (sx * 0.64), 0.16, n=10)
    k.emit("Head_BarrelBrass", col, rig=rig, bone="barrel")
    rod(k["team!:0.1:0.6"], bpt(0.76), bpt(1.3), 0.36, 0.345, n=12)
    k.emit("Head_BarrelBand", col, rig=rig, bone="barrel")
    # ---- the dragon's head: the muzzle, in brass; open jaws round the glowing bore
    skull = [(1.92, 0.0, 0.38, 0.38), (2.02, 0.06, 0.47, 0.42), (2.14, 0.11, 0.44, 0.33), (2.2, 0.2, 0.37, 0.19),
             (2.36, 0.22, 0.3, 0.145), (2.5, 0.22, 0.22, 0.1)]
    bm_loft(k["gold:0.08:0.55"], [oval(bpt(s, cu), X, U, rx, ru, 10) for s, cu, rx, ru in skull], tip1=bpt(2.63, 0.21))
    jaw = [(2.04, -0.25, 0.36, 0.13), (2.26, -0.28, 0.29, 0.085), (2.44, -0.26, 0.2, 0.065)]
    bm_loft(k["gold:0.08:0.55"], [oval(bpt(s, cu), X, U, rx, ru, 8) for s, cu, rx, ru in jaw], tip1=bpt(2.52, -0.23))
    for sx in (-1, 1):
        for u0, u1, ln in ((0.12, 0.2, 0.36), (-0.06, -0.1, 0.3)):
            bm_crystal(k["gold:0.3:0.75"], bpt(2.02, u0, sx * 0.41), bpt(2.02 - ln, u1, sx * 0.68), 0.075, n=4, shoulder=0.25)
    k.emit("Head_Dragon", col, rig=rig, bone="barrel")
    for sx in (-1, 1):
        bm_tube(k["iron:0.1:0.5"], [bpt(2.06, 0.33, sx * 0.22), bpt(1.84, 0.58, sx * 0.37), bpt(1.52, 0.7, sx * 0.45)], [0.1, 0.07, 0.0], n=6)
        bm_beam(k["iron:0.1:0.5"], bpt(1.98, 0.43, sx * 0.15), bpt(2.2, 0.36, sx * 0.37), 0.09, 0.06)
    for s, u in ((1.94, 0.46), (2.06, 0.44), (2.18, 0.4), (2.3, 0.34)):
        bm_crystal(k["iron:0.1:0.5"], bpt(s, u - 0.05), bpt(s - 0.12, u + 0.2), 0.055, n=4, shoulder=0.3)
    rod(k["black:0.4:0.8"], bpt(2.05, -0.04), bpt(2.09, -0.04), 0.25, n=10)
    k.emit("Head_DragonDark", col, rig=rig, bone="barrel")
    for s, x, u in ((2.25, 0.245, 0.082), (2.37, 0.21, 0.12), (2.48, 0.166, 0.144)):
        for sx in (-1, 1):
            bm_crystal(k["cream:0.05:0.4"], bpt(s, u + 0.02, sx * x), bpt(s + 0.02, u - 0.08, sx * x * 0.95), 0.028, n=4, shoulder=0.3)
    for s, x, u in ((2.2, 0.22, -0.2), (2.32, 0.185, -0.22), (2.42, 0.15, -0.218)):
        for sx in (-1, 1):
            bm_crystal(k["cream:0.05:0.4"], bpt(s, u - 0.02, sx * x), bpt(s + 0.02, u + 0.07, sx * x * 0.95), 0.026, n=4, shoulder=0.3)
    for sx in (-1, 1):
        bm_ellipsoid(k["black:0.3:0.6"], tuple(bpt(2.55, 0.28, sx * 0.08)), (0.04, 0.04, 0.04), u=6, v=4)
    k.emit("Head_Teeth", col, rig=rig, bone="barrel")
    rod(k[EMB], bpt(2.1, -0.04), bpt(2.13, -0.04), 0.14, n=10)
    for sx in (-1, 1):
        bm_ellipsoid(k[EMB], tuple(bpt(2.1, 0.3, sx * 0.35)), (0.08, 0.08, 0.08), u=6, v=4)
    k.emit("Head_DragonGlow", col, rig=rig, bone="barrel")
    # ---- the muzzle's fire (hidden at rest: scaled down on its bone) and the ring of smoke it leaves
    fb = bpt(2.2)
    bm_crystal(k["glow:1.0,0.55,0.12,1.1"], fb, fb + E * 1.25, 0.3, n=6, shoulder=0.3)
    for i in range(6):
        a = math.radians(60 * i)
        d = X * math.cos(a) + U * math.sin(a)
        bm_crystal(k["glow:1.0,0.55,0.12,1.1"], fb + E * 0.05, fb + E * 0.5 + d * 0.62, 0.13, n=4, shoulder=0.3)
        bm_crystal(k["glow:1.0,0.85,0.4,1.2"], fb + E * 0.1, fb + E * 0.85 + d * 0.3, 0.11, n=4, shoulder=0.3)
    k.emit("Head_Flash", col, rig=rig, bone="flash")
    sm = bpt(2.35)
    for i in range(8):
        a = math.radians(45 * i)
        bm_blob(k["white:0.0:0.25"], rnd, tuple(sm + (X * math.cos(a) + U * math.sin(a)) * 0.36), 0.16, jitter=0.15)
    bm_blob(k["white:0.0:0.25"], rnd, tuple(sm + E * 0.12), 0.22, jitter=0.12)
    k.emit("Head_Smoke", col, rig=rig, bone="smoke")
    for i in range(2):
        bm_blob(k["white:0.0:0.25"], random.Random(40 + i), tuple(bpt(2.25, 0.0) + ZV * 0.05), 0.08, squash=(1.2, 1.2, 0.9), jitter=0.12)
        k.emit("Head_Wisp%d" % i, col, rig=rig, bone="wisp.%d" % i)
    # ---- the crane: an iron-banded mast with a winch, a jib with a backstay, the hook with a shell in its sling
    m = MAST
    bm_box(k["wood_dark:0.2:0.7"], (0.17, 0.17, 2.0), tuple(m + ZV * 1.0))
    bm_beam(k["wood_dark:0.2:0.7"], (m.x, m.y, TIP.z), tuple(TIP + Vector((-0.06, 0, 0))), 0.12, 0.14)
    bm_beam(k["wood_dark:0.2:0.7"], (m.x - 0.05, m.y, T + 1.5), (m.x - 0.62, m.y, TIP.z - 0.05), 0.08, 0.08)
    k.emit("Head_Crane", col, rig=rig, bone="crane", bevel=0.01, vary=0.06)
    for z in (T + 0.9, T + 1.6, T + 2.3):
        bm_box(k["iron:0.25:0.7"], (0.2, 0.2, 0.05), (m.x, m.y, z))
    rod(k["iron:0.3:0.8"], (m.x, m.y, T + 2.56), tuple(TIP + ZV * 0.06), 0.018, n=4)
    rod(k["iron:0.25:0.7"], (m.x - 0.13, m.y - 0.17, T + 0.95), (m.x - 0.13, m.y + 0.17, T + 0.95), 0.1, n=8)
    k.emit("Head_CraneIron", col, rig=rig, bone="crane")
    rod(k["gold:0.1:0.5"], (m.x - 0.13, m.y - 0.13, T + 0.95), (m.x - 0.13, m.y + 0.13, T + 0.95), 0.075, n=10)
    rod(k["gold:0.1:0.5"], tuple(TIP + Vector((0, -0.04, -0.03))), tuple(TIP + Vector((0, 0.04, -0.03))), 0.07, n=8)
    bm_ellipsoid(k["gold:0.1:0.5"], (m.x, m.y, T + 2.62), (0.06, 0.06, 0.06), u=6, v=4)
    k.emit("Head_CraneBrass", col, rig=rig, bone="crane")
    rod(k["iron:0.3:0.8"], tuple(TIP - ZV * 0.08), tuple(TIP - ZV * 0.26), 0.02, n=4)
    bm_box(k["iron:0.25:0.7"], (0.12, 0.09, 0.12), tuple(TIP - ZV * 0.32))
    bm_tube(k["iron:0.25:0.7"], [TIP - ZV * 0.38, TIP - ZV * 0.46 + X * 0.03, TIP - ZV * 0.46 - X * 0.05, TIP - ZV * 0.4 - X * 0.06], 0.018, n=4)
    k.emit("Head_Hook", col, rig=rig, bone="hook")
    sb = TIP - ZV * 1.1
    bm_shell(k["gold:0.1:0.55"], k["stone:0.25:0.7"], sb, (0, 0, 1), 0.16, 0.72, band=k["orange:0.2:0.6"], n=8, rim=True)
    for sx in (-1, 1):
        rod(k["wood_dark:0.3:0.8"], TIP - ZV * 0.4, sb + ZV * 0.42 + X * (sx * 0.15), 0.012, n=4)
    rod(k["sand:0.3:0.7"], sb + ZV * 0.39, sb + ZV * 0.45, 0.172, n=8)
    k.emit("Head_Load", col, rig=rig, bone="load")
    flag_part("Head_Pennant", col, rig, "pen", (m.x, m.y, T + 2.52), (0, -1, 0), 0.62, 0.2, segs=3)
    empty("Muzzle", col, head, tuple(bpt(2.25, -0.05)), 0.3, "SPHERE")
    crew = empty("Crew", col, head, tuple(CREW), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(100))
    if os.environ.get("TR_CREW_PREVIEW"):          # a stand-in figure, for previews only
        bm = bmesh.new()
        bm_box(bm, (0.3, 0.2, 0.5), (0, 0, 0.3))
        bm_ellipsoid(bm, (0, 0, 0.68), (0.14, 0.14, 0.15))
        o = paint(mesh_obj("PreviewCrew", bm, col, head), "red")
        o.location = tuple(CREW)
        o.rotation_euler = (0, 0, math.radians(100))
    return rig


IDLE_LEN, FIRE_LEN, RELOAD_LEN = 120, 24, 60
RECOIL = 0.62
BACK = Vector((0, -2.45, 0.16)).normalized()


def pose(rig, flag=0.0, recoil=0.0, rock=0.0, kick=0.0, flash=0.0, smoke=0.0, drift=0.0, crane=0.0, sway=(0.0, 0.0),
         load=1.0, gust=0.0, wisp=1.0, wisp_t=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    c = pb["carriage"]
    c.location = arm_space_loc(c, BACK * (RECOIL * recoil))
    c.rotation_quaternion = q(c, (1, 0, 0), rock)
    pb["barrel"].rotation_quaternion = q(pb["barrel"], (1, 0, 0), kick)
    roll = math.degrees(RECOIL * recoil / WHEEL_R)
    for n in WHEELS:
        pb[n].rotation_quaternion = q(pb[n], (1, 0, 0), roll)
    v = max(flash, 0.02)
    pb["flash"].scale = (v, v, v)
    s = pb["smoke"]
    v = max(smoke, 0.02)
    s.scale = (v, v, v)
    s.location = arm_space_loc(s, E * (0.6 * drift) + ZV * (0.35 * drift))
    pb["crane"].rotation_quaternion = q(pb["crane"], (0, 0, 1), crane)
    h = pb["hook"]
    h.rotation_quaternion = q(h, (1, 0, 0), sway[0]) @ q(h, (0, 1, 0), sway[1])
    v = max(load, 0.02)
    pb["load"].scale = (v, v, v)
    wave_flag(rig, "pen", flag, amp=1.0 + gust)
    for i in range(2):
        u = (wisp_t + i * 0.5) % 1.0
        b = pb["wisp.%d" % i]
        b.location = arm_space_loc(b, E * (0.12 * u) + ZV * (0.55 * u) + X * (0.06 * math.sin(6.0 * u + i * 2.0)))
        sc = (0.5 + 1.1 * u) * min(1.0, u / 0.1) * min(1.0, (1.0 - u) / 0.3) * wisp
        b.scale = (max(sc, 0.02),) * 3


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        pose(rig, flag=2 * t, crane=6.0 * math.sin(ph), sway=(3.0 * math.sin(2 * ph), 2.0 * math.sin(ph)), wisp_t=2 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # settle (the carriage eases forward, the muzzle dips), then the shot at frame 3: fire and smoke, the carriage
        # slams back up the rails and rears, crashes down, rocks; it ends run back (reload brings it forward)
        pose(rig, flag=0.5 * f / FIRE_LEN,
             recoil=ease([(0, 0), (2, -0.03), (3, 0), (4, 0.55), (6, 0.88), (9, 1.0), (24, 1.0)], f),
             rock=ease([(0, 0), (3, 0), (5, 5.0), (8, -1.2), (10, 0.8), (13, 0), (24, 0)], f),
             kick=ease([(0, 0), (2, -1.0), (3, 0), (4, 4.0), (9, 1.0), (14, 0)], f),
             flash=ease([(0, 0), (3, 0), (3.5, 1.0), (5, 1.3), (7, 0.7), (9, 0)], f),
             smoke=ease([(0, 0), (3, 0), (5, 0.9), (12, 1.6), (24, 2.1)], f),
             drift=ease([(0, 0), (3, 0), (24, 1.0)], f),
             sway=(ease([(0, 0), (4, 0), (8, 7.0), (14, -4.0), (20, 2.0), (24, 0)], f), 0.0),
             gust=ease([(0, 0), (4, 0), (6, 1.5), (16, 0.4), (24, 0)], f),
             wisp=ease([(0, 1), (3, 1), (4, 0)], f))
        key_pose(rig, f)
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        # the carriage runs forward to its stops; the crane swings the shell over the breech, it drops in, the crane
        # swings back to the pile and takes the next one
        crane = ease([(0, 0), (8, 0), (28, 160), (36, 160), (56, 0)], f)
        pose(rig, flag=0.5 + 0.5 * f / RELOAD_LEN,
             recoil=ease([(0, 1.0), (4, 1.0), (24, 0.0)], f),
             rock=ease([(0, 0), (22, 0), (25, -1.2), (28, 0.5), (31, 0)], f),
             smoke=ease([(0, 2.1), (8, 2.4), (16, 0.0)], f),
             drift=ease([(0, 1.0), (16, 1.4), (16.5, 0.0)], f) if f <= 16 else 0.0,
             crane=crane,
             sway=(ease([(0, 0), (10, 0), (16, -7.0), (26, 5.0), (31, -3.0), (36, 0), (40, 6.0), (50, -4.0), (56, 3.0), (60, 0)], f), 0.0),
             load=ease([(0, 1), (30, 1), (35, 0), (50, 0), (58, 1)], f),
             wisp=ease([(0, 0), (50, 0), (60, 1)], f))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


_DRAGON = PIV + TC + E * 2.25
PREVIEW = {"target": (0, -0.2, 1.4), "dist": 13.0, "yaw": 150, "pitch": 22, "anim_target": (0, 0.9, 1.7), "anim_dist": 8.0,
           "frames": [("idle", 0), ("fire", 5), ("fire", 12), ("reload", 20), ("reload", 32)],
           "extra": [{"yaw": 150, "pitch": 12, "dist": 3.4, "target": tuple(_DRAGON)},
                     {"yaw": 20, "pitch": 32, "dist": 6.0, "target": (0.0, -0.4, 1.0)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
