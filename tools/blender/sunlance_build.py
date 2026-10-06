"""Builds the Sunlance Lighthouse (footprint "pair": [0,0] front, [0,1] back), the Crown's Tier IV beam tower: a lance of
sunlight that burns through everything on a straight line.

    python tools/blender/build.py sunlance --out <preview dir>

One lighthouse and its keeper. On the front hex a tall tapering lighthouse of coursed pale stone rises from a rocky
foot: a coursed footing and coping, the shaft banded in the team color with small glowing windows and an arched door
at the back up a flight of steps, a corbelled gallery with an iron rail, a lantern room of gold mullions over team
panels, a gilded dome and a sun finial. In the lantern a big gold-rimmed lens on a yoke (the Head turns it; Muzzle at
its glass) blazes with a ring of gold sun rays. On the back hex the keeper's cottage of warm stone with a team-tiled
roof, a chimney and shuttered windows, joined to the lighthouse by coped walls round a paved yard and the steps.
Rig under the Head: idle (the lens sways and nods, the glass and lamp pulse, the rays breathe), fire (the lens winds
back, flares and kicks, a burst of light leaves the glass).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())

TID = "sunlance"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)            # (0, 1.04): the lighthouse
B = hex_to_world(0, 1, MID)            # (0, -1.04): the keeper's cottage
TOP = 0.34
T = TOP
Z_FOOT = T + 0.32                      # the footing's top, under its coping
Z_LAND = T + 0.4                       # the landing at the door
Z_SH = T + 2.3                         # the shaft's top
R0, R1 = 0.6, 0.42                     # the shaft's radius at the foot and the top
Z_GAL = Z_SH + 0.09                    # the gallery floor
Z_LAMP = Z_GAL + 0.5                   # the lens's middle: the Head
Z_CORN = Z_GAL + 0.8                   # the lantern's cornice
CB = Vector((0, -1.22, 0))             # the cottage
CW, CD = 1.3, 0.84
Z_CE, Z_CR = T + 0.62, T + 1.15        # its eaves and ridge
STONE_C = "stone_warm:0.1:0.7"
WARM = "glow:1.0,0.74,0.3,0.9"
LENS = "glow:1.0,0.8,0.36,1.0"
LAMP = "glow:1.0,0.72,0.25,1.0"
FLASH = "glow:1.0,0.84,0.45,0.9"
TEAM = "team!:0.1:0.6"


def tangent(deg):
    """The `right` for a curved wall facing out at deg degrees (so wall_out(right) points out)."""
    a = math.radians(deg)
    return Vector((-math.sin(a), math.cos(a), 0))


def shaft_r(z):
    return R0 + (R1 - R0) * (z - Z_LAND) / (Z_SH - Z_LAND)


def build_base():
    col = collection("Sunlance")
    root = empty("Sunlance", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(8)
    k = Kit()
    # ---- the rocky foot: boulders nestled round the footing, a gap at the back for the steps
    for i in range(12):
        a = 90 + 30 * i + rnd.uniform(-6, 6)
        if 240 < a % 360 < 300:
            continue
        corner = i % 2 == 1                     # toward a hex corner there's room for a bigger rock
        r = rnd.uniform(0.8, 0.86) if corner else rnd.uniform(0.72, 0.76)
        p = polar(F, r, a)
        bm_boulder(k["stone2:0.15:0.8"], rnd, (p.x, p.y, T - 0.02), rnd.uniform(0.25, 0.3) if corner else rnd.uniform(0.18, 0.22),
                   squash=(1, 1, rnd.uniform(0.8, 1.1)), n=12)
    for a in (200, 340, 15, 165):
        p = polar(F, 0.98, a)
        bm_boulder(k["stone2:0.2:0.85"], rnd, (p.x, p.y, T - 0.02), 0.15, squash=(1.1, 1, 0.75), n=10)
    k.emit("Rocks", col, root, vary=0.07)
    # ---- the lighthouse: a coursed footing and coping, the tapering shaft with team bands, windows, the door, steps
    course_tower(k, rnd, F, 0.84, 0.82, T, Z_FOOT, courses=2, n=14)
    cull_tower(k[STONE], F, 0.9)
    bm_block_course(k[STONE_LIGHT], rnd, F, 0.87, Z_FOOT, Z_LAND - Z_FOOT, 18, depth=0.3)
    course_tower(k, rnd, F, R0, R1, Z_LAND, Z_SH, courses=11, n=12, band=lambda c: TEAM if c in (2, 6, 10) else None)
    cull_tower(k[STONE], F, 0.7)
    cull_down(k[CORE])
    k.emit("Lighthouse", col, root, vary=0.07, tag="no_refine")
    for a, z in ((250, Z_LAND + 0.62), (35, Z_LAND + 0.98), (145, Z_LAND + 1.3), (290, Z_LAND + 1.55)):
        arch_window(k, polar(F, shaft_r(z + 0.1) + 0.005, a, z), tangent(a), 0.12, 0.25, glow=WARM, n=4, th=0.05, proud=0.04)
    arch_door(k, polar(F, shaft_r(Z_LAND) + 0.01, 270, Z_LAND), tangent(270), 0.26, 0.44, n=5)
    ye = F.y - 0.86
    for i, (d, h) in enumerate(((0.15, Z_LAND - T - 0.13), (0.3, Z_LAND - T - 0.26))):
        bm_box(k[STONE_LIGHT], (0.5 - 0.04 * i, d + 0.12, h), (0, ye - d * 0.5 + 0.06, T + h * 0.5))
    for sx in (-1, 1):
        bm_slopebox(k[STONE], (sx * 0.29, ye + 0.08), (1, 0, 0), (0, -1, 0), 0.08, 0.36, T, Z_LAND + 0.06, T + 0.12)
    k.emit("Lighthouse_Trim", col, root, vary=0.05)
    # ---- the gallery: a corbelled ring under a stone floor, an iron rail
    bm_block_course(k[STONE_LIGHT], rnd, F, 0.6, Z_SH - 0.12, 0.14, 14, depth=0.3)
    bm_cyl(k[STONE_LIGHT], 0.64, 0.64, 0.07, (F.x, F.y, Z_GAL - 0.035), seg=16)
    for i in range(12):
        bm_box(k[IRON], (0.03, 0.03, 0.22), tuple(polar(F, 0.6, 15 + 30 * i, Z_GAL + 0.11)), (0, 0, 15 + 30 * i))
    ring(k[IRON], (F.x, F.y, Z_GAL), 0.625, 0.575, 0.2, 0.24, seg=16)
    # ---- the lantern room: team panels under gold mullions, a glazing bar, a cornice; a gilded dome; a sun finial
    bm_cyl(k[TEAM], 0.39, 0.39, 0.2, (F.x, F.y, Z_GAL + 0.1), seg=8)
    ring(k[GOLD], (F.x, F.y, Z_GAL), 0.41, 0.33, 0.19, 0.24, seg=8)
    for i in range(6):
        a = 60 * i
        bm_box(k[GOLD], (0.034, 0.04, Z_CORN - Z_GAL - 0.24), tuple(polar(F, 0.385, a, (Z_GAL + 0.24 + Z_CORN) * 0.5)), (0, 0, a))
    bm_cyl(k[GOLD], 0.44, 0.44, 0.06, (F.x, F.y, Z_CORN + 0.03), seg=16)
    rings = []
    for a in (0, 24, 48, 70):
        rr = 0.4 * math.cos(math.radians(a))
        rings.append(oval((F.x, F.y, Z_CORN + 0.06 + 0.34 * math.sin(math.radians(a))), (1, 0, 0), (0, 1, 0), rr, rr, 16))
    bm_loft(k[GOLD], rings, tip1=(F.x, F.y, Z_CORN + 0.42))
    zs = Z_CORN + 0.42
    bm_cyl(k[GOLD], 0.06, 0.035, 0.1, (F.x, F.y, zs + 0.03), seg=8)
    bm_cyl(k[GOLD], 0.022, 0.018, 0.2, (F.x, F.y, zs + 0.15), seg=6)
    zsun = zs + 0.36
    bm_cyl(k[GOLD], 0.1, 0.1, 0.045, (F.x, F.y, zsun), rot=(90, 0, 0), seg=12)
    for i in range(12):
        a = math.radians(30 * i)
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((F.x, F.y, zsun))
        bm_crystal(k[GOLD], c + d * 0.08, c + d * (0.2 if i % 2 else 0.25), 0.032, n=4, shoulder=0.3)
    bm_cyl(k["glow:1.0,0.82,0.35,1.0"], 0.06, 0.06, 0.06, (F.x, F.y, zsun), rot=(90, 0, 0), seg=10)
    k.emit("Lantern", col, root, vary=0.04, tag="no_refine")
    # ---- the keeper's cottage: warm stone, quoins, a team-tiled gable roof, a chimney, shuttered windows, a door
    stone_box(k, rnd, CB, CW, CD, T, Z_CE, course=0.2, block=0.34, stone=STONE_C, quoins=STONE_LIGHT)
    for sx in (-1, 1):
        gable_wall(k, rnd, (sx * (CW * 0.5 - 0.08), CB.y - CD * 0.5), (sx * (CW * 0.5 - 0.08), CB.y + CD * 0.5), Z_CE, Z_CR - 0.03,
                   course=0.18, block=0.32, stone=STONE_C)
    stone_box(k, rnd, (CW * 0.5 + 0.1, CB.y), 0.24, 0.28, T, Z_CR + 0.32, th=0.1, course=0.2, block=0.26, stone=STONE_C)
    cull_box(k[STONE_C], CB, CW, CD)
    for key in (STONE_LIGHT, CORE):
        cull_down(k[key])
    k.emit("Cottage", col, root, vary=0.07, tag="no_refine")
    gable_roof(k, rnd, CB, CW, CD, Z_CE, Z_CR, eave=0.1, verge=0.08, rows=4, cols=6)
    k.emit("Cottage_Roof", col, root, vary=0.08, tag="no_refine")
    cx = CW * 0.5 + 0.1
    bm_box(k[STONE_LIGHT], (0.3, 0.34, 0.06), (cx, CB.y, Z_CR + 0.35))
    for dy in (-0.06, 0.06):
        bm_cyl(k["wood_red:0.3:0.7"], 0.045, 0.04, 0.12, (cx, CB.y + dy, Z_CR + 0.44), seg=6)
        bm_cyl(k["black:0.3:0.6"], 0.03, 0.03, 0.01, (cx, CB.y + dy, Z_CR + 0.5), seg=6)
    yb, yf = CB.y - CD * 0.5, CB.y + CD * 0.5
    arch_door(k, (-0.24, yf, T), (-1, 0, 0), 0.24, 0.42, n=5)
    arch_window(k, (0.26, yf, T + 0.2), (-1, 0, 0), 0.18, 0.3, glow=WARM, n=4)
    for x in (-0.3, 0.3):
        arch_window(k, (x, yb, T + 0.2), (1, 0, 0), 0.18, 0.3, glow=WARM, n=4)
        for s in (-1, 1):
            bm_box(k[TEAM], (0.08, 0.025, 0.3), (x + s * 0.15, yb - 0.02, T + 0.36))
    k.emit("Cottage_Trim", col, root, vary=0.05)
    # ---- the yard between them: coped walls from the cottage to the footing, paving, the woodpile by the cottage
    for sx in (-1, 1):
        crenel_wall(k, rnd, [(sx * 0.6, yf + 0.02), (sx * 0.53, F.y - 0.66)], T, 0.26, th=0.14, course=0.13, block=0.3, merlon=None, cap=STONE_LIGHT)
    cull_down(k[STONE])
    k.emit("YardWalls", col, root, vary=0.07)
    pave(k, rnd, CELLS, T, inset=0.2, size=0.26, where=lambda x, y: abs(x) < 0.5 and yf < y < ye - 0.3)
    pave(k, rnd, CELLS, T, inset=0.22, size=0.27, keep=0.85, where=lambda x, y: y < yb - 0.04 or (y < yf and abs(x) > CW * 0.5 + 0.02))
    k.emit("Paving", col, root, vary=0.09)
    kk_import("resources/Wood_Log_Stack", col, root, (-CW * 0.5 - 0.22, CB.y + 0.05, T), 90, 0.45, name="Prop_KK_Logs")
    head = empty("Head", col, root, (F.x, F.y, Z_LAMP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.3, 0), 0.2, "SPHERE")
    return root


# ---- the lens on its yoke, in the head's space (+Y forward; the lantern floor is 0.5 below)
BONES = {"root": ((0, 0, -0.3), (0, 0, -0.1), None),
         "turn": ((0, 0, -0.22), (0, 0, -0.02), "root"),
         "lens": ((0, -0.1, 0), (0, 0.2, 0), "turn"),
         "glass": ((0, 0.12, 0), (0, 0.3, 0), "lens"),
         "halo": ((0, 0.05, 0), (0, 0.25, 0), "lens"),
         "lamp": ((0, -0.17, 0), (0, -0.17, 0.15), "lens"),
         "flash": ((0, 0.3, 0), (0, 0.5, 0), "lens")}


def build_head():
    col = collection("Sunlance")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    k = Kit()
    bm_cyl(k[IRON], 0.1, 0.07, 0.28, (0, 0, -0.36), seg=8)                       # the pedestal
    k.emit("Head_Pedestal", col, rig=rig, bone="root")
    bm_cyl(k[GOLD], 0.16, 0.16, 0.04, (0, 0, -0.2), seg=12)                      # the turntable and the yoke
    bm_beam(k[GOLD], (-0.27, 0, -0.19), (0.27, 0, -0.19), 0.06, 0.05)
    for sx in (-1, 1):
        bm_beam(k[GOLD], (sx * 0.27, 0, -0.21), (sx * 0.27, 0, 0.02), 0.05, 0.06)
        bm_cyl(k[GOLD], 0.045, 0.045, 0.05, (sx * 0.25, 0, 0), rot=(0, 90, 0), seg=8)
    k.emit("Head_Yoke", col, rig=rig, bone="turn")
    bm_cyl(k[GOLD], 0.18, 0.25, 0.24, (0, 0, 0), rot=(-90, 0, 0), seg=14)         # the lens drum, flared to the front
    bm_ring_n(k[GOLD], (0, 0.125, 0), (0, 1, 0), 0.285, 0.21, 0.024, seg=16)
    bm_ring_n(k["gold:0.3:0.7"], (0, -0.06, 0), (0, 1, 0), 0.235, 0.17, 0.02, seg=14)
    k.emit("Head_Lens", col, rig=rig, bone="lens")
    bm_cyl(k[LENS], 0.215, 0.215, 0.03, (0, 0.125, 0), rot=(-90, 0, 0), seg=16)
    bm_ellipsoid(k[LENS], (0, 0.13, 0), (0.19, 0.055, 0.19), u=12, v=4)
    bm_ring_n(k[GOLD], (0, 0.17, 0), (0, 1, 0), 0.14, 0.12, 0.012, seg=14)
    k.emit("Head_Glass", col, rig=rig, bone="glass")
    for i in range(12):
        a = math.radians(30 * i + 15)
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((0, 0.06, 0))
        bm_crystal(k[GOLD], c + d * 0.27, c + d * (0.32 if i % 2 else 0.35), 0.032, n=4, shoulder=0.3)
    k.emit("Head_Rays", col, rig=rig, bone="halo")
    bm_gem(k[LAMP], (0, -0.17, 0), 0.075, 0.1, 0.09, n=6, axis=(0, 1, 0))
    k.emit("Head_Lamp", col, rig=rig, bone="lamp")
    bm_ellipsoid(k[FLASH], (0, 0.36, 0), (0.26, 0.07, 0.26), u=12, v=5)
    bm_cyl(k[FLASH], 0.17, 0.04, 0.55, (0, 0.64, 0), rot=(-90, 0, 0), seg=10)
    k.emit("Head_Flash", col, rig=rig, bone="flash")
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def pose(rig, t, sway=1.0, glow=1.0, lamp=1.0, kick=0.0, tilt=0.0, flash=0.0, rays=1.0, spin=0.0):
    """t: where in the idle loop (0..1); glow / lamp: the glass's and the lamp's size; kick: the lens driven back;
    tilt: its nose lifted; flash: the burst of light; rays: the sun rays' spread; spin: their extra turn."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    w = 2 * math.pi * t
    pb["turn"].rotation_quaternion = q(pb["turn"], (0, 0, 1), 9 * math.sin(w) * sway)
    pb["lens"].rotation_quaternion = q(pb["lens"], (1, 0, 0), 3 * math.sin(2 * w) * sway + tilt)
    pb["lens"].location = arm_space_loc(pb["lens"], (0, -0.1 * kick, 0))
    pb["glass"].scale = (glow, 1.0, glow)
    pb["lamp"].scale = (lamp, lamp, lamp)
    pb["halo"].rotation_quaternion = q(pb["halo"], (0, 1, 0), 15 * math.sin(w) + spin)
    pb["halo"].scale = (rays, 1.0, rays)
    f = max(flash, 0.001)
    pb["flash"].scale = (f, f, f)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        w = 2 * math.pi * t
        pose(rig, t, glow=1.0 + 0.06 * math.sin(2 * w), lamp=1.0 + 0.14 * math.sin(3 * w), rays=1.0 + 0.06 * math.sin(4 * w))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # wind-up (0-3: the lens draws back and dims), the flare (frame 5: the burst, the kick), the settle (to 18)
        wind = smooth(f / 3.0) * (1 - smooth((f - 3) / 2.0))
        k = smooth((f - 3) / 2.0) * (1 - smooth((f - 6) / 11.0))
        burst = smooth((f - 3) / 2.0) * (1 - smooth((f - 6) / 6.0))
        pose(rig, 0.0, glow=1.0 - 0.1 * wind + 0.55 * k, lamp=1.0 - 0.2 * wind + 0.9 * k, kick=-0.25 * wind + k, tilt=-4 * wind + 7 * k,
             flash=1.5 * burst, rays=1.0 + 0.3 * k, spin=25 * math.sin(math.pi * f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.9), "dist": 10.0, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y, Z_LAMP), "anim_dist": 2.8,
           "frames": [("idle", 0), ("idle", 48), ("fire", 2), ("fire", 5), ("fire", 10)],
           "extra": [{"yaw": 20, "pitch": 30, "dist": 4.4, "target": (0, -0.9, 0.8)},
                     {"yaw": 200, "pitch": 15, "dist": 3.0, "target": (F.x, F.y, Z_LAMP + 0.1)},
                     {"yaw": 0, "pitch": 57, "dist": 3.4, "target": (F.x, F.y, Z_LAMP)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
