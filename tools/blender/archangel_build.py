"""Builds the Archangel (footprint "fan4": [0,0] the back cell, [0,-1] front, [-1,0] front-left, [1,-1] front-right).

    python tools/blender/build.py archangel --out <preview dir>

One temple: a great angel (KayKit's Paladin, bare-headed) with broad wings, a big halo and a greatsword of light rises
out of the open top of a marble rotunda where the four hexes meet: eight columns under a gilded ring entablature
with a team-colored frieze and team drapes, round a glowing mosaic sun in the floor. The rotunda stands on a coursed
podium that fills all four hexes, paved in rings of marble, with a stair cut into it front and back (a team runner up
each into the rotunda) and a gilded angel statue on a plinth at each side tip. Everything under the angel stays below
its wings' sweep, so nothing clips them and nothing hides it from the game camera.
The angel is the Head (it turns to face whoever it judges; the game drops the pillar of light on the target).
idle: the hover. fire: the summon clip with the wings flaring up, the sword kept in hand.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())

TID = "archangel"
CELLS = [(0, 0), (0, -1), (-1, 0), (1, -1)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FRONT = hex_to_world(0, -1, MID)
FL = hex_to_world(-1, 0, MID)
FR = hex_to_world(1, -1, MID)
TOP = 0.34
POD = 0.6                       # the podium's top (the Head)
CHAR = "Paladin.glb"
HEIGHT = 1.9
GOLD = (1.0, 0.82, 0.4)
RCOL = 1.62                     # the rotunda's columns
ENT = 1.6                       # the entablature's foot
HOVER = 1.9 - POD               # the angel's feet just over the entablature, below its wings' sweep
STAIR_W, STAIR_D = 0.36, 0.5


def podium_outline():
    """The footprint pulled in, with a stair notch in the middle of the back and front edges."""
    pts = outline(CELLS, 0.14)
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        out.append(a)
        if abs(a.y - b.y) < 1e-3 and abs(a.x + b.x) < 1e-3 and abs(a.y) > 1.5:
            sg = 1 if b.x > a.x else -1
            inward = 1 if a.y < 0 else -1
            for x, dy in ((-sg * STAIR_W, 0), (-sg * STAIR_W, STAIR_D), (sg * STAIR_W, STAIR_D), (sg * STAIR_W, 0)):
                out.append(Vector((x, a.y + inward * dy, 0)))
    return out


def build_base():
    col = collection("Archangel")
    root = empty("Archangel", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    k = Kit()
    O = (0.0, 0.0)
    cols = [math.radians(22.5 + 45 * i) for i in range(8)]
    cpos = [(RCOL * math.cos(a), RCOL * math.sin(a)) for a in cols]
    pod = podium_outline()
    inner = outline(CELLS, 0.3)

    # ---- the podium: coursed walls round the footprint, a core, rings of paving on top
    for i, a in enumerate(pod):
        b = pod[(i + 1) % len(pod)]
        d = (b - a)
        if d.length < 0.05:
            continue
        n = Vector((-d.y, d.x, 0)).normalized() * 0.1
        bm_block_wall(k["white:0.15:0.6"], rnd, (a + n).to_2d(), (b + n).to_2d(), T - 0.01, POD - 0.01, th=0.2, course=0.13, block=0.42)
    k.emit("Podium", col, root, vary=0.07)
    prism(k["white:0.55:0.95"], pod, T - 0.02, POD - 0.012)
    k.emit("Podium_Core", col, root, tag="no_refine")
    yb = BACK.y - 1.039 + 0.14             # the back edge (the front one mirrors it)

    def paved(x, y):
        if not inside(inner, x, y) or any((x - p[0]) ** 2 + (y - p[1]) ** 2 < 0.3 ** 2 for p in cpos):
            return False
        return not (abs(x) < STAIR_W + 0.08 and abs(y) > -yb - STAIR_D - 0.02)
    ring_paving(k, rnd, O, 1.42, 3.3, POD - 0.012, keep=paved, h=0.04, width=0.4, block=0.56,
                swatches=("white:0.12:0.55", "cream:0.15:0.6"))
    k.emit("Paving", col, root, vary=0.08)
    # ---- the stairs, front and back: two steps cut into the podium, gilded nosings
    for sy in (-1, 1):
        y0 = sy * -yb                       # the podium's edge on this side
        y_mid, y_in = y0 - sy * STAIR_D * 0.5, y0 - sy * STAIR_D
        bm_box(k["white:0.1:0.5"], (2 * STAIR_W, STAIR_D, 0.13), (0, (y0 + y_in) / 2, T + 0.065))
        bm_box(k["white:0.1:0.5"], (2 * STAIR_W, STAIR_D * 0.5, POD - T - 0.13), (0, (y_mid + y_in) / 2, T + 0.13 + (POD - T - 0.13) / 2))
        for yy, zz in ((y0, T + 0.13), (y_mid, POD)):
            bm_box(k["gold:0.1:0.5"], (2 * STAIR_W + 0.02, 0.04, 0.03), (0, yy + sy * 0.0, zz - 0.012))
    k.emit("Stairs", col, root, vary=0.05)
    # ---- inside the rotunda: the mosaic sun, rings of marble under rays of gold light and team color
    ring_paving(k, rnd, O, 0.3, 1.42, POD - 0.012, keep=lambda x, y: True, h=0.04, width=0.28, block=0.42,
                swatches=("white:0.1:0.45", "white:0.1:0.45", "cream:0.12:0.5"))
    k.emit("Mosaic_Floor", col, root, vary=0.07)
    zf = POD + 0.03
    ring(k["gold:0.05:0.4"], (0, 0, 0), 1.4, 1.3, zf - 0.01, zf + 0.012, seg=32)
    ring(k["gold:0.05:0.4"], (0, 0, 0), 0.36, 0.3, zf - 0.01, zf + 0.015, seg=16)
    bm_cyl(k["glow:1.0,0.85,0.45,0.95"], 0.3, 0.26, 0.03, (0, 0, zf + 0.005), seg=12)
    for i in range(16):
        a = math.radians(22.5 * i + 11.25)
        d = Vector((math.cos(a), math.sin(a), 0))
        if i % 2 == 0:
            bm_beam(k["glow:1.0,0.8,0.38,0.6"], d * 0.36 + Vector((0, 0, zf + 0.004)), d * 1.27 + Vector((0, 0, zf + 0.004)), 0.2, 0.02, w1=0.0, h1=0.02)
        else:
            bm_beam(k["team!:0.1:0.5"], d * 0.36 + Vector((0, 0, zf + 0.002)), d * 1.0 + Vector((0, 0, zf + 0.002)), 0.15, 0.02, w1=0.0, h1=0.02)
    k.emit("Mosaic_Sun", col, root)
    # ---- the runners: up each stair and across to the mosaic's ring
    for sy in (-1, 1):
        y0 = sy * -yb
        y_mid, y_in = y0 - sy * STAIR_D * 0.5, y0 - sy * STAIR_D
        pts = [Vector((0, y0, T + 0.142)), Vector((0, y_mid + sy * 0.02, T + 0.142)), Vector((0, y_mid + sy * 0.02, POD + 0.012)),
               Vector((0, sy * 1.34, POD + 0.04))]
        for p, q in zip(pts, pts[1:]):
            vert = abs(q.z - p.z) > 0.05
            bm_beam(k["team!:0.1:0.6"], p, q, 0.42, 0.024, up=(0, sy, 0) if vert else (0, 0, 1))
        for sx in (-1, 1):
            bm_beam(k["gold:0.05:0.4"], Vector((sx * 0.18, y_mid, POD + 0.05)), Vector((sx * 0.18, sy * 1.36, POD + 0.05)), 0.035, 0.012)
    k.emit("Runner", col, root)

    # ---- the rotunda: eight short columns on plinths, a ring entablature (team frieze, gilded lips), drapes
    for (x, y) in cpos:
        bm_box(k["white:0.1:0.5"], (0.44, 0.44, 0.08), (x, y, POD + 0.03))
        column(k, rnd, (x, y), POD + 0.07, ENT - POD - 0.07, 0.13, drums=2)
    ring_blocks(k["white:0.05:0.4"], rnd, O, RCOL + 0.2, 0.4, ENT, ENT + 0.1, 0, 360, block=0.55)                # architrave
    ring_blocks(k["team!:0.1:0.55"], rnd, O, RCOL + 0.17, 0.34, ENT + 0.1, ENT + 0.18, 11, 371, block=0.42)       # frieze
    ring_blocks(k["white:0.03:0.35"], rnd, O, RCOL + 0.25, 0.48, ENT + 0.18, ENT + 0.25, 5, 365, block=0.5)       # cornice
    ring(k["gold:0.05:0.4"], (0, 0, 0), RCOL + 0.26, RCOL + 0.2, ENT + 0.235, ENT + 0.27, seg=32)
    ring(k["gold:0.05:0.4"], (0, 0, 0), RCOL - 0.17, RCOL - 0.23, ENT + 0.235, ENT + 0.27, seg=32)
    for i in range(8):
        a0, a1 = 22.5 + 45 * i, 67.5 + 45 * i
        if (a0 + a1) / 2 % 180 == 90:       # the stair bays stay open
            continue
        drape(k, O, RCOL, a0 + 5, a1 - 5, ENT - 0.01, 0.08, 0.3, n=4)
    k.emit("Rotunda", col, root, vary=0.06)
    # ---- the guardians: a gilded angel on a plinth at each side tip, looking out and back
    for sx in (-1, 1):
        p = Vector((sx * 2.36, 0.0, 0))
        bm_box(k["white:0.1:0.5"], (0.42, 0.42, 0.3), (p.x, p.y, POD + 0.15))
        bm_box(k["white:0.05:0.4"], (0.48, 0.48, 0.06), (p.x, p.y, POD + 0.03))
        bm_box(k["gold:0.1:0.5"], (0.46, 0.46, 0.04), (p.x, p.y, POD + 0.3))
        statue(k, (p.x, p.y), (sx * 0.75, -0.66), POD + 0.32, h=0.85)
    k.emit("Guardians", col, root)
    empty("Head", col, root, (0, 0, POD), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Archangel")
    return make_angel(CHAR, col, bpy.data.objects["Head"], HEIGHT, HOVER, span=1.3, wing_scale=1.25, halo_r=0.26,
                      weapon=(0.1, 0.17), blade=(0.17, 1.2), muzzle_off=(0.0, 0.3, 0.9), gold=GOLD, kind="sword")


def build_anims():
    # wings that flare up, with hardly a downstroke: their sweep stays above the rotunda (see report_envelope)
    angel_anims(bpy.data.objects["Rig"], "Jump_Idle", "Ranged_Magic_Summon", fire_len=30, hide=None, beat=1.0, bob=0.08,
                down=6.0, flap=10.0)


PREVIEW = {"target": (0, 0.2, 1.8), "dist": 11.0, "yaw": 160, "pitch": 16, "anim_target": (0, 0, 2.7), "anim_dist": 6.5,
           "frames": [("idle", 0), ("idle", 30), ("fire", 6), ("fire", 14), ("fire", 24)],
           "extra": [{"yaw": 15, "pitch": 40, "dist": 5.5, "target": (0, 0, 2.2)},
                     {"yaw": 115, "pitch": 20, "dist": 4.2, "target": (FR.x + 0.2, 0, 1.1)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
