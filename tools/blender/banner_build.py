"""Builds the War Banner (footprint "single": one hex), the Crown's support standard: nothing aims, it only ever idles.

    python tools/blender/build.py banner --out <preview dir>

One royal standard owning the hex: two octagonal steps of kerb stones carry a square dais of coursed stone (quoins, a
coping, corner posts with gilt balls, heater shields on its faces, an iron brazier built into its back with glowing
coals); the knight's step is at the front (Crew). From the dais a tall gold-banded mast with a crossbar carries one big
swallow-tailed gonfalon in the team color with a gold crown; two pennants fly from the mast above it; a gilded crown
finial on top; the war drums sit on the dais either side of the mast. Rig under the root: idle only (the gonfalon
rolls and sways, the pennants flutter out of phase, the brazier's flames flicker and its coals pulse).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())

TID = "banner"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34
Z1 = TOP + 0.14                 # the first step's top
Z2 = Z1 + 0.16                  # the second step's top: the knight's step
DAIS = 0.92                     # the dais's side
Z_DAIS = Z2 + 0.46              # the dais's top
Z_BAR = TOP + 2.4               # the crossbar
Z_TOP = TOP + 2.95              # the mast's top (the finial's foot)
BAN_W, BAN_L = 1.0, 1.15        # the gonfalon: wide, long
PEN = [((0.07, 0.0, Z_BAR + 0.22), (1.0, -0.3, 0.0), 0.72, 0.16), ((0.07, 0.0, Z_BAR + 0.46), (1.0, -0.2, 0.0), 0.58, 0.13)]
BRAZ = Vector((0.0, -0.52, Z_DAIS + 0.06))     # the brazier bowl's middle
FIRE = "glow:1.0,0.5,0.12,0.85"
EMBER = "glow:1.0,0.4,0.1,0.8"


def build_base():
    col = collection("Banner")
    root = empty("Banner", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(7)
    k = Kit()
    # ---- the podium: two octagonal steps of kerb stones, then the square dais in coursed blocks with quoins and a coping
    bm_block_course(k[STONE_FOOT], rnd, (0, 0, 0), 0.92, T, Z1 - T, 8, depth=0.26, phase=-0.5, jit=0.006)
    bm_cyl(k[CORE], 0.68, 0.68, Z1 - T - 0.01, (0, 0, (T + Z1) / 2), rot=(0, 0, 22.5), seg=8)
    bm_block_course(k[STONE], rnd, (0, 0, 0), 0.78, Z1, Z2 - Z1, 8, depth=0.24, phase=-0.5, jit=0.006)
    bm_cyl(k[CORE], 0.56, 0.56, Z2 - Z1 - 0.01, (0, 0, (Z1 + Z2) / 2), rot=(0, 0, 22.5), seg=8)
    stone_box(k, rnd, (0, 0), DAIS, DAIS, Z2, Z_DAIS - 0.06, quoins=STONE_LIGHT, course=0.2, block=0.3)
    bm_box(k[STONE_LIGHT], (DAIS + 0.1, DAIS + 0.1, 0.06), (0, 0, Z_DAIS - 0.03))                   # the coping slab
    for sx in (-1, 1):                                                                              # corner posts with gilt balls
        for sy in (-1, 1):
            bm_box(k[STONE_LIGHT], (0.16, 0.16, Z_DAIS + 0.22 - Z1), (sx * 0.5, sy * 0.5, (Z1 + Z_DAIS + 0.22) / 2))
            bm_box(k[STONE_LIGHT], (0.2, 0.2, 0.05), (sx * 0.5, sy * 0.5, Z_DAIS + 0.245))
            bm_ellipsoid(k[GOLD], (sx * 0.5, sy * 0.5, Z_DAIS + 0.33), (0.065, 0.065, 0.065), u=8, v=5)
    k.emit("Podium", col, root, vary=0.07)
    for c, out, kind in (((0.465, 0.0), (1, 0, 0), "cross"), ((-0.465, 0.0), (-1, 0, 0), "cross"), ((0.0, 0.465), (0, 1, 0), "boss"),
                         ((0.3, -0.465), (0, -1, 0), "chevron"), ((-0.3, -0.465), (0, -1, 0), "chevron")):
        shield(k, (c[0], c[1], Z2 + 0.22), out, w=0.24, h=0.3, kind=kind)
    k.emit("Shields", col, root)
    # ---- the brazier built into the dais's back: an iron bowl on a bracket (its coals and flames are on the rig)
    bm_cyl(k[IRON], 0.13, 0.25, 0.2, tuple(BRAZ), seg=10)
    ring(k[IRON], (BRAZ.x, BRAZ.y, 0), 0.27, 0.22, BRAZ.z + 0.08, BRAZ.z + 0.12, seg=10)
    for sx in (-1, 1):
        bm_beam(k[IRON], (sx * 0.18, -0.45, Z_DAIS - 0.3), (sx * 0.12, BRAZ.y, BRAZ.z - 0.08), 0.04, 0.04)
    bm_beam(k[IRON], (-0.2, -0.45, Z_DAIS - 0.32), (0.2, -0.45, Z_DAIS - 0.32), 0.04, 0.05)
    k.emit("Brazier", col, root)
    # ---- the war drums either side of the mast: red-painted shells, team hoops, gold lacing, cream skins, sticks on one
    for sx in (-1, 1):
        D = Vector((sx * 0.3, 0.04, Z_DAIS))
        bm_cyl(k["wood_red:0.25:0.7"], 0.155, 0.155, 0.28, (D.x, D.y, D.z + 0.14), seg=10)
        bm_cyl(k["cream:0.05:0.35"], 0.165, 0.165, 0.03, (D.x, D.y, D.z + 0.285), seg=10)
        for z in (0.04, 0.25):
            ring(k["team!:0.1:0.5"], (D.x, D.y, 0), 0.172, 0.15, D.z + z - 0.02, D.z + z + 0.02, seg=10)
        for i in range(8):
            a0, a1 = math.radians(45 * i), math.radians(45 * i + 45)
            bm_beam(k[GOLD], (D.x + math.cos(a0) * 0.165, D.y + math.sin(a0) * 0.165, D.z + 0.06),
                    (D.x + math.cos(a1) * 0.165, D.y + math.sin(a1) * 0.165, D.z + 0.23), 0.02, 0.02)
    D = Vector((0.3, 0.04, Z_DAIS + 0.31))
    bm_beam(k["wood:0.2:0.6"], (D.x - 0.12, D.y - 0.1, D.z), (D.x + 0.14, D.y + 0.12, D.z + 0.02), 0.025, 0.025)
    bm_beam(k["wood:0.2:0.6"], (D.x - 0.1, D.y + 0.12, D.z), (D.x + 0.15, D.y - 0.08, D.z + 0.04), 0.025, 0.025)
    k.emit("Drums", col, root)
    # ---- the mast: a dark pole in a gilt collar, gold bands and team sleeves up it, the crossbar, the crown finial
    bm_cyl(k[GOLD], 0.15, 0.1, 0.14, (0, 0, Z_DAIS + 0.07), seg=8)
    bm_cyl(k[TIMBER], 0.075, 0.055, Z_TOP - Z_DAIS, (0, 0, (Z_DAIS + Z_TOP) / 2), seg=8)
    for i in range(1, 5):
        z = Z_DAIS + 0.4 * i
        bm_cyl(k[GOLD], 0.088 - 0.004 * i, 0.088 - 0.004 * i, 0.06, (0, 0, z), seg=8)
    for z in (Z_DAIS + 0.6, Z_DAIS + 1.4):
        bm_cyl(k["team!:0.15:0.6"], 0.082, 0.078, 0.34, (0, 0, z), seg=8)
    bm_beam(k[TIMBER], (-0.62, 0, Z_BAR), (0.62, 0, Z_BAR), 0.07, 0.07)
    bm_cyl(k[GOLD], 0.1, 0.1, 0.12, (0, 0, Z_BAR), seg=8)
    for sx in (-1, 1):
        bm_ellipsoid(k[GOLD], (sx * 0.66, 0, Z_BAR), (0.055, 0.055, 0.055), u=8, v=5)
    bm_ellipsoid(k[GOLD], (0, 0, Z_TOP + 0.06), (0.085, 0.085, 0.085), u=8, v=5)
    ring(k[GOLD], (0, 0, 0), 0.12, 0.085, Z_TOP + 0.13, Z_TOP + 0.22, seg=8)
    for i in range(6):
        a = math.radians(60 * i)
        base = Vector((math.cos(a) * 0.105, math.sin(a) * 0.105, Z_TOP + 0.21))
        bm_crystal(k[GOLD], base, base + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.14)), 0.028, n=4, shoulder=0.35)
    bm_cyl(k[GOLD], 0.03, 0.0, 0.34, (0, 0, Z_TOP + 0.36), seg=6)
    k.emit("Mast", col, root)
    empty("Crew", col, root, (0, 0.6, Z2), 0.3, "SINGLE_ARROW")
    crew_dummy(col, bpy.data.objects["Crew"], 1.12, "halberd")
    head = empty("Head", col, root, (0, 0, Z_TOP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.1), 0.25, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "flame": (tuple(BRAZ + UP * 0.1), tuple(BRAZ + UP * 0.3), "root"),
         "ember": (tuple(BRAZ + UP * 0.09), tuple(BRAZ + UP * 0.15), "root")}
flag_bones(BONES, "ban", (0, 0, Z_BAR - 0.04), (0, 0, -1), BAN_L, segs=4)
for _n, (_top, _d, _l, _h) in zip(("pen1", "pen2"), PEN):
    flag_bones(BONES, _n, _top, _d, _l, segs=3)


def build_rig(root):
    col = collection("Banner")
    rig = make_rig(col, root, BONES)
    k = Kit()
    crown = stamp(CROWN, 0.25, 0.6, 0.25, 0.75, key=GOLD, across=True)

    def color(u, v):
        if u < 0.06 or v < 0.06 or v > 0.94:
            return GOLD
        return crown(u, v)
    cloth_grid(k, (0, 0, Z_BAR - 0.04), (0, 0, -1), (1, 0, 0), BAN_L, BAN_W, nu=14, nv=14, tail="swallow", notch=0.75,
               tail_from=0.76, color=color, center=True)
    k.emit("Gonfalon", col, rig=rig, bones=["ban.%d" % (i + 1) for i in range(4)])
    for n, (top, d, L, H) in zip(("pen1", "pen2"), PEN):
        cloth_grid(k, top, d, (0, 0, -1), L, H, nu=6, nv=2, tail="point", color=lambda u, v: GOLD if u > 0.72 else None)
        k.emit(n.capitalize(), col, rig=rig, bones=["%s.%d" % (n, i + 1) for i in range(3)])
    for i, (dx, dy, h) in enumerate(((0, 0, 0.3), (0.09, 0.05, 0.2), (-0.08, -0.05, 0.22), (0.03, -0.1, 0.17), (-0.05, 0.09, 0.16))):
        bm_flame(k[FIRE], (BRAZ.x + dx, BRAZ.y + dy, BRAZ.z + 0.08), 0.1 if i == 0 else 0.065, h, n=6)
    k.emit("Flames", col, rig=rig, bone="flame")
    bm_cyl(k[EMBER], 0.21, 0.21, 0.025, (BRAZ.x, BRAZ.y, BRAZ.z + 0.105), seg=10)
    k.emit("Embers", col, rig=rig, bone="ember")
    return rig


IDLE_LEN = 120


def pose(rig, t):
    """The standard at one moment of its loop (t 0..1): the gonfalon rolls front and back down its chain with a sideways
    sway over it, the pennants flutter and flap out of phase, the flames flicker, the coals pulse."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    w = 2 * math.pi * t
    for i in range(4):
        b = pb["ban.%d" % (i + 1)]
        b.rotation_quaternion = q(b, (1, 0, 0), (4.0 + 3.5 * i) * math.sin(2 * w - 0.9 * i) + 2.5 * math.sin(w - 0.4 * i)) \
            @ q(b, (0, 1, 0), (2.0 + 2.0 * i) * math.sin(w + 1.1 - 0.7 * i))
    for n, ph, amp in (("pen1", 0.0, 1.3), ("pen2", 2.3, 1.1)):
        for i in range(3):
            b = pb["%s.%d" % (n, i + 1)]
            b.rotation_quaternion = q(b, (0, 0, 1), (6.0 + 6.0 * i) * amp * math.sin(3 * w - 1.0 * i + ph)) \
                @ q(b, (0, 1, 0), (4.0 + 5.0 * i) * amp * math.sin(4 * w - 1.2 * i + ph + 0.8))
    f = pb["flame"]
    f.scale = (1.0 + 0.1 * math.sin(11 * w), 1.0 + 0.1 * math.sin(13 * w + 1), 1.0 + 0.28 * math.sin(9 * w) * math.sin(5 * w + 0.7) + 0.1 * math.sin(14 * w))
    f.rotation_quaternion = q(f, (1, 0, 0), 7 * math.sin(7 * w)) @ q(f, (0, 1, 0), 7 * math.sin(8 * w + 2))
    s = 1.0 + 0.06 * math.sin(3 * w)
    pb["ember"].scale = (s, s, 1.0)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.7), "dist": 8.0, "yaw": 150, "pitch": 22, "anim_target": (0, 0, Z_BAR - 0.45), "anim_dist": 4.6,
           "frames": [("idle", 0), ("idle", 30), ("idle", 60), ("idle", 90)],
           "extra": [{"yaw": 15, "pitch": 24, "dist": 3.4, "target": (0, -0.3, Z_DAIS + 0.1)},
                     {"yaw": 195, "pitch": 18, "dist": 3.6, "target": (0, 0.3, Z2 + 0.6)}]}


def build_all():
    root = build_base()
    build_rig(root)
    build_anims()
