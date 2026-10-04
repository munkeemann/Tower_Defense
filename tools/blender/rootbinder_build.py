"""Builds the Rootbinder Shrine (footprint "fan5": [0,0] middle, [-1,0] front-left, [0,-1] front, [1,-1] front-right,
[1,0] back-right), a Verdant tower: orbs that root ground enemies.

    blender -b --factory-startup --python tools/blender/build_tower.py -- rootbinder <preview dir>

An ancient hollow stump sits on the middle cell, its roots spreading over the others, cradling a glowing green orb in
four curling roots (the Head; orbs leave the orb). Mossy menhirs with green runes ring it, with mushrooms and ferns.
idle: the orb bobs and turns, the cradle roots breathe. fire: the cradle roots lash open, the orb flares.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "rootbinder"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)
OTHERS = [hex_to_world(q, s, MID) for q, s in CELLS[1:]]
TOP = 0.34
ROOT_GLOW = (0.2, 0.9, 0.35)
STUMP_TOP = 1.05


def build_base():
    col = collection("Rootbinder")
    root = empty("Rootbinder", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(44)
    C = C0
    bm = bmesh.new()
    ring(bm, (C.x, C.y, 0), 0.72, 0.5, T - 0.02, T + STUMP_TOP, seg=10)
    ring(bm, (C.x, C.y, 0), 0.82, 0.6, T - 0.02, T + 0.3, seg=10)
    for k in range(10):
        a = math.radians(36 * k + rnd.uniform(-10, 10))
        reach = rnd.uniform(1.4, 2.4)
        far = C + Vector((math.cos(a), math.sin(a), 0)) * 1.6
        if min((far - p).length for p in OTHERS) > 1.0:
            reach = 0.95          # no cell that way: the root stays on the middle hex
        tgt = C + Vector((math.cos(a), math.sin(a), 0)) * reach
        mid = C + Vector((math.cos(a), math.sin(a), 0)) * 0.9
        bm_beam(bm, Vector((mid.x, mid.y, T + 0.25)) - Vector((math.cos(a), math.sin(a), 0)) * 0.3, Vector((mid.x, mid.y, T + 0.12)),
                0.24, 0.22, w1=0.17, h1=0.15)
        bm_beam(bm, Vector((mid.x, mid.y, T + 0.12)), Vector((tgt.x, tgt.y, T + 0.0)), 0.17, 0.15, w1=0.05, h1=0.05)
    o = paint(mesh_obj("Stump", bm, col, root), "wood_dark", lo=0.15, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (C.x, C.y, 0), 0.71, 0.51, T + STUMP_TOP - 0.02, T + STUMP_TOP + 0.03, seg=10)
    paint(mesh_obj("Stump_Rim", bm, col, root), "sand", lo=0.2, hi=0.5)
    bm = bmesh.new()
    for k in range(5):
        a = math.radians(72 * k + 15)
        bm_ellipsoid(bm, (C.x + math.cos(a) * 0.7, C.y + math.sin(a) * 0.7, T + 0.6 + 0.3 * (k % 2)), (0.16, 0.12, 0.1), (0, 0, math.degrees(a)), u=7, v=4)
    paint(mesh_obj("Stump_Moss", bm, col, root), "grass", lo=0.3, hi=0.7)
    # menhirs with runes on the outer cells, plus mushrooms and ferns
    stone_b, rune_b = bmesh.new(), bmesh.new()
    for i, p in enumerate(OTHERS):
        q = p + (p - C).normalized() * 0.3
        h = 0.95 + 0.25 * (i % 2)
        yaw = math.degrees(math.atan2((C - q).y, (C - q).x)) + 90
        bm_beam(stone_b, Vector((q.x, q.y, T - 0.02)), Vector((q.x, q.y, T + h)), 0.4, 0.26, w1=0.26, h1=0.18, up=(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
        to = (C - q).normalized()
        for k in range(2):
            g = Vector((q.x, q.y, T + h * (0.4 + 0.28 * k))) + Vector((to.x, to.y, 0)) * 0.12
            bm_box(rune_b, (0.13, 0.012, 0.13), tuple(g), (0, 45, yaw))
    o = paint(mesh_obj("Menhirs", stone_b, col, root), "stone2", lo=0.1, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    glow_obj("Menhir_Runes", rune_b, col, root, ROOT_GLOW, 0.9)
    props = [("forest/Bush_1_B_Color1", 0.3), ("forest/Grass_1_D_Color1", 0.6), ("forest/Bush_2_D_Color1", 0.28), ("forest/Rock_1_G_Color1", 0.28)]
    for i, p in enumerate(OTHERS):
        rel, sc = props[i % len(props)]
        q = p + (p - C).normalized().cross(Vector((0, 0, 1))) * 0.5
        kk_import(rel, col, root, (q.x, q.y, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (C.x, C.y, T + STUMP_TOP), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None), "orb": ((0, 0, 0.55), (0, 0, 0.8), "root")}
for _k in range(4):
    _a = math.radians(90 * _k + 45)
    BONES["cradle.%d" % _k] = ((math.cos(_a) * 0.35, math.sin(_a) * 0.35, 0.0), (math.cos(_a) * 0.4, math.sin(_a) * 0.4, 0.55), "root")


def build_head():
    col = collection("Rootbinder")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.26, matrix=Matrix.Translation((0, 0, 0.55)))
    rig_part("Head_Orb", bm, None, rig, "orb", col, bevel=0, mat=glow_mat("root_glow", ROOT_GLOW, 0.7))
    for k in range(4):
        a = math.radians(90 * k + 45)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm = bmesh.new()
        p0 = d * 0.35
        p1 = d * 0.42 + Vector((0, 0, 0.35))
        p2 = d * 0.3 + Vector((0, 0, 0.7))
        p3 = d * 0.12 + Vector((0, 0, 0.85))
        bm_beam(bm, p0, p1, 0.14, 0.14, w1=0.11, h1=0.11)
        bm_beam(bm, p1, p2, 0.11, 0.11, w1=0.08, h1=0.08)
        bm_beam(bm, p2, p3, 0.08, 0.08, w1=0.03, h1=0.03)
        rig_part("Head_Cradle%d" % k, bm, "wood_dark", rig, "cradle.%d" % k, col, bevel=0, lo=0.2, hi=0.7)
    empty("Muzzle", col, head, (0, 0, 0.55), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 18


def pose(rig, bob=0.0, spin=0.0, flare=1.0, lash=0.0, breathe=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["orb"].location = arm_space_loc(pb["orb"], (0, 0, bob))
    pb["orb"].rotation_quaternion = arm_space_quat(pb["orb"], (0, 0, 1), spin)
    pb["orb"].scale = (flare,) * 3
    for k in range(4):
        a = math.radians(90 * k + 45)
        axis = (-math.sin(a), math.cos(a), 0)      # tangent: tilting about it opens the root outward
        b = pb["cradle.%d" % k]
        b.rotation_quaternion = arm_space_quat(b, axis, lash + breathe * math.sin(k))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, bob=0.06 * math.sin(ph), spin=360 * f / IDLE_LEN, breathe=5 * math.sin(ph * 2))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        lash = 32 * smooth(f / 3.0) * (1 - smooth((f - 4) / 12.0))
        pose(rig, lash=lash, flare=1.0 + 0.55 * (smooth(f / 2.0) - smooth((f - 3) / 12.0)), spin=180 * smooth(f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 11.0, "yaw": 150, "pitch": 26, "anim_target": (C0.x, C0.y, 1.6), "anim_dist": 4.0,
           "frames": [("idle", 0), ("fire", 3), ("fire", 9)]}


def build_all():
    build_base()
    build_head()
    build_anims()
