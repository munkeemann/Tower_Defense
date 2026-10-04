"""Builds the Dire Bear (footprint "pair": [0,0] front, [0,1] back), a Verdant creature tower: it mauls what's next to
it and leaves it bleeding.

    blender -b --factory-startup --python tools/blender/build_tower.py -- dire_bear <preview dir>

A chunky low-poly grizzly on all fours on the front cell, war-painted in team stripes with glowing green runes on its
shoulders (the Head: it turns toward its prey). Back cell: its den (a rock cave), a fallen log, old bones and a carved
totem. idle: it breathes, sniffs, looks about. fire: it rears up on its hind legs, roars, and mauls down.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dire_bear"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
RUNE = (0.3, 1.0, 0.45)
BS = 1.15               # bear scale (laid out at 1.0)


def build_base():
    col = collection("Dire_bear")
    root = empty("Dire_bear", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True, stone="stone_warm")
    rnd = random.Random(19)
    B = BACK
    # the den: the pack's boulders heaped round a dark cave mouth that faces the front
    for i, (rel, dx, dy, dz, sc, rot) in enumerate((("forest/Rock_3_A_Color1", -0.5, -0.2, 0, 0.75, 20),
                                                    ("forest/Rock_3_C_Color1", 0.5, -0.25, 0, 0.7, 140),
                                                    ("forest/Rock_1_A_Color1", 0.0, -0.55, 0, 0.8, 80),
                                                    ("forest/Rock_3_B_Color1", 0.05, -0.35, 0.45, 0.6, 200))):
        kk_import(rel, col, root, (B.x + dx, B.y + dy, T - 0.02 + dz), rot, sc, name="Den_%d" % i)
    bm = bmesh.new()
    bm_ellipsoid(bm, (B.x, B.y - 0.05, T + 0.02), (0.3, 0.06, 0.26), u=10, v=6)
    paint(mesh_obj("Den_Mouth", bm, col, root), "black", lo=0.3, hi=0.6)
    # a fallen log and a carved totem with a team band
    bm = bmesh.new()
    bm_cyl(bm, 0.13, 0.13, 1.0, (B.x + 0.62, B.y + 0.55, T + 0.12), rot=(90, 0, 60), seg=8)
    paint(mesh_obj("Log", bm, col, root), "wood_red", lo=0.3, hi=0.7)
    bm = bmesh.new()
    tp = B + Vector((-0.7, 0.55, 0))
    bm_cyl(bm, 0.12, 0.14, 1.3, (tp.x, tp.y, T + 0.65), seg=6)
    for z in (0.5, 0.95):
        bm_ellipsoid(bm, (tp.x, tp.y + 0.1, T + z), (0.13, 0.08, 0.12), u=6, v=4)
    paint(mesh_obj("Totem", bm, col, root), "wood", lo=0.2, hi=0.8)
    bm = bmesh.new()
    for z in (0.3, 0.75, 1.2):
        ring(bm, (tp.x, tp.y, 0), 0.15, 0.12, T + z - 0.04, T + z + 0.04, seg=6)
    paint(mesh_obj("Totem_Bands", bm, col, root), "team", team=True, lo=0.1, hi=0.5)
    for i, (rel, loc, sc) in enumerate((("halloween/bone_A", (B.x + 0.35, B.y + 0.15, T), 0.5), ("halloween/bone_B", (FRONT.x - 0.55, FRONT.y - 0.5, T), 0.5),
                                        ("forest/Bush_1_C_Color1", (FRONT.x + 0.7, FRONT.y + 0.45, T - 0.02), 0.28),
                                        ("forest/Grass_1_B_Color1", (FRONT.x - 0.6, FRONT.y + 0.4, T - 0.02), 0.55))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (FRONT.x, FRONT.y - 0.1, T), 0.5, "SINGLE_ARROW")
    return root


# ---- the bear, in the head's space (+Y forward), laid out at 1.0
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, -0.35, 0.55), (0, -0.05, 0.6), "root"),
    "chest": ((0, -0.05, 0.6), (0, 0.35, 0.68), "hips"),
    "neck": ((0, 0.35, 0.72), (0, 0.55, 0.78), "chest"),
    "head": ((0, 0.55, 0.78), (0, 0.85, 0.74), "neck"),
    "jaw": ((0, 0.68, 0.66), (0, 0.9, 0.62), "head"),
    "leg.FL": ((-0.2, 0.3, 0.5), (-0.22, 0.34, 0.02), "chest"),
    "leg.FR": ((0.2, 0.3, 0.5), (0.22, 0.34, 0.02), "chest"),
    "leg.BL": ((-0.22, -0.4, 0.45), (-0.22, -0.42, 0.02), "hips"),
    "leg.BR": ((0.22, -0.4, 0.45), (0.22, -0.42, 0.02), "hips"),
}


def build_head():
    col = collection("Dire_bear")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=BS)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, scale=BS, **kw)

    bm = bmesh.new()
    bm_ellipsoid(bm, (0, -0.3, 0.58), (0.36, 0.42, 0.33))
    bm_ellipsoid(bm, (0, -0.48, 0.66), (0.1, 0.08, 0.08), u=6, v=4)             # stubby tail
    P("Head_Hips", bm, "wood_red", "hips", lo=0.25, hi=0.85)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.12, 0.66), (0.4, 0.4, 0.4))
    bm_ellipsoid(bm, (0, 0.2, 0.92), (0.3, 0.3, 0.17))                           # the grizzly's shoulder hump
    P("Head_Chest", bm, "wood_red", "chest", lo=0.15, hi=0.8)
    bm = bmesh.new()
    for s in (-1, 1):
        for k in range(3):
            c = Vector((s * 0.37, 0.05 + k * 0.1, 0.78 - k * 0.07))
            bm_box(bm, (0.02, 0.22, 0.05), tuple(c), (25 * s, 0, 10))
    P("Head_Paint", bm, "team", "chest", team=True, lo=0.1, hi=0.4)
    bm = bmesh.new()
    for s in (-1, 1):
        c = Vector((s * 0.3, 0.25, 0.92))
        bm_box(bm, (0.02, 0.14, 0.14), tuple(c), (0, 45, 30 * s))
    o = rig_part("Head_Runes", bm, None, rig, "chest", col, bevel=0, scale=BS, mat=glow_mat("bear_rune", RUNE, 0.9))
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.45, 0.76), (0.22, 0.2, 0.22))
    P("Head_Neck", bm, "wood_red", "neck", lo=0.2, hi=0.75)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.7, 0.8), (0.24, 0.24, 0.21))
    for s in (-1, 1):
        bm_ellipsoid(bm, (s * 0.15, 0.6, 1.0), (0.07, 0.05, 0.07), u=6, v=4)
    P("Head_Skull", bm, "wood_red", "head", lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.9, 0.75), (0.13, 0.15, 0.1))
    P("Head_Snout", bm, "sand", "head", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 1.03, 0.78), (0.05, 0.04, 0.04), u=6, v=4)
    for s in (-1, 1):
        bm_ellipsoid(bm, (s * 0.11, 0.86, 0.88), (0.03, 0.025, 0.03), u=5, v=4)
    P("Head_Eyes", bm, "black", "head", lo=0.3, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.86, 0.64), (0.1, 0.12, 0.04), u=7, v=4)
    P("Head_Jaw", bm, "salmon", "jaw", lo=0.4, hi=0.7)
    # legs with paws and claws
    for leg, (x, y0, z0) in {"FL": (-0.2, 0.3, 0.5), "FR": (0.2, 0.3, 0.5), "BL": (-0.22, -0.4, 0.45), "BR": (0.22, -0.4, 0.45)}.items():
        bm = bmesh.new()
        front = leg[0] == "F"
        bm_beam(bm, (x, y0, z0 + 0.12), (x * 1.08, y0 + 0.04, 0.1), 0.24 if front else 0.27, 0.24 if front else 0.27, w1=0.17, h1=0.17)
        bm_ellipsoid(bm, (x * 1.08, y0 + 0.08, 0.06), (0.12, 0.15, 0.07), u=7, v=4)
        P("Head_Leg" + leg, bm, "wood_red", "leg." + leg, lo=0.3, hi=0.85)
        bm = bmesh.new()
        for k in range(3):
            c = Vector((x * 1.08 + (k - 1) * 0.06, y0 + 0.22, 0.05))
            bm_beam(bm, c - Vector((0, 0.04, 0)), c + Vector((0, 0.06, -0.03)), 0.035, 0.035, w1=0.0, h1=0.0)
        P("Head_Claws" + leg, bm, "cream", "leg." + leg, lo=0.1, hi=0.3)
    empty("Muzzle", col, head, (0, 1.05 * BS, 0.75 * BS), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 22


def pose(rig, breathe=0.0, look=0.0, sniff=0.0, rear=0.0, swipe=0.0, roar=0.0, lunge=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["hips"].rotation_quaternion = arm_space_quat(pb["hips"], (1, 0, 0), rear * 38)
    pb["hips"].location = arm_space_loc(pb["hips"], (0, lunge * 0.15 + rear * 0.05, 0))
    pb["chest"].scale = (1 + breathe, 1 + breathe, 1 + breathe)
    pb["chest"].rotation_quaternion = arm_space_quat(pb["chest"], (1, 0, 0), rear * 10 - lunge * 8)
    pb["neck"].rotation_quaternion = arm_space_quat(pb["neck"], (0, 0, 1), look * 0.5) @ arm_space_quat(pb["neck"], (1, 0, 0), -rear * 25 + sniff)
    pb["head"].rotation_quaternion = arm_space_quat(pb["head"], (0, 0, 1), look * 0.5) @ arm_space_quat(pb["head"], (1, 0, 0), roar * 18)
    pb["jaw"].rotation_quaternion = arm_space_quat(pb["jaw"], (1, 0, 0), -roar * 30)
    for s in ("L", "R"):
        pb["leg.F" + s].rotation_quaternion = arm_space_quat(pb["leg.F" + s], (1, 0, 0), rear * 50 + swipe * (40 if s == "R" else 25))
        pb["leg.B" + s].rotation_quaternion = arm_space_quat(pb["leg.B" + s], (1, 0, 0), -rear * 38)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, breathe=0.025 * math.sin(ph * 2), look=25 * math.sin(ph) * (0.5 + 0.5 * math.sin(ph * 0.5)),
             sniff=6 * max(0.0, math.sin(ph * 3)) ** 4)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 6.0) * (1 - smooth((f - 9) / 4.0))
        swipe = smooth((f - 8) / 3.0) * (1 - smooth((f - 13) / 8.0)) * 1.0 - smooth((f - 3) / 4.0) * (1 - smooth((f - 8) / 2.0)) * 0.6
        roar = smooth((f - 2) / 4.0) * (1 - smooth((f - 10) / 6.0))
        lunge = smooth((f - 9) / 3.0) * (1 - smooth((f - 13) / 8.0))
        pose(rig, rear=rear, swipe=swipe, roar=roar, lunge=lunge)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.4, 0.8), "dist": 7.0, "yaw": 145, "pitch": 18, "anim_target": (0, FRONT.y, 1.0), "anim_dist": 4.5,
           "frames": [("idle", 0), ("fire", 6), ("fire", 11), ("fire", 18)]}


def build_all():
    build_base()
    build_head()
    build_anims()
