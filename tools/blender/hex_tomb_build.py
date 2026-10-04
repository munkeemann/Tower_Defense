"""Builds the Hex Tomb (footprint "fan4": [0,0] hub, [-1,0] left, [0,-1] front, [1,-1] right), a Grave tower: it curses
nearby enemies so they take more damage from everything.

    blender -b --factory-startup --python tools/blender/build_tower.py -- hex_tomb <preview dir>

The hub holds a crypt whose dark doorway glows with two purple eyes. On the front cell a stone sarcophagus lies on a
dais, its lid knocked askew and purple light leaking out, and over it floats the hex: a slowly turning ring of runes
round a glowing hexagram. Headstones, candles, skull posts and a broken fence fill the side cells. It's an aura (it
doesn't turn). idle: the hex turns, the lid rattles now and then, the eyes pulse. fire (when the curse lands): the hex
flares wide and the lid jolts.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "hex_tomb"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
HUB = hex_to_world(0, 0, MID)
L = hex_to_world(-1, 0, MID)
FR = hex_to_world(0, -1, MID)
R = hex_to_world(1, -1, MID)
TOP = 0.34
T = TOP
DAIS = T + 0.24
CURSE = (0.72, 0.38, 1.0)


def build_base():
    col = collection("Hex_tomb")
    root = empty("Hex_tomb", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    face = math.degrees(math.atan2(FR.y - HUB.y, FR.x - HUB.x)) - 90       # the crypt's door faces the sarcophagus
    for i, (rel, loc, rot, sc) in enumerate((("halloween/crypt", (HUB.x, HUB.y - 0.15, T), face + 180, 0.19),
                                              ("halloween/gravestone", (L.x - 0.2, L.y + 0.35, T), 20, 0.3),
                                              ("halloween/grave_A", (L.x + 0.35, L.y - 0.3, T), -10, 0.24),
                                              ("halloween/candle_triple", (L.x - 0.6, L.y - 0.3, T), 0, 0.4),
                                              ("halloween/post_skull", (R.x + 0.55, R.y + 0.05, T), 160, 0.3),
                                              ("halloween/gravemarker_B", (R.x - 0.3, R.y + 0.45, T), -20, 0.32),
                                              ("halloween/fence_broken", (R.x + 0.1, R.y - 0.6, T), 30, 0.27),
                                              ("halloween/skull_candle", (FR.x + 0.7, FR.y + 0.35, T), 200, 0.26),
                                              ("halloween/candle_triple", (FR.x - 0.7, FR.y + 0.3, T), 60, 0.38))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    # the sarcophagus on its dais
    bm = bmesh.new()
    bm_box(bm, (1.2, 1.1, 0.12), (FR.x, FR.y, T + 0.06))
    bm_box(bm, (0.95, 0.9, 0.12), (FR.x, FR.y, T + 0.18))
    paint(mesh_obj("Dais", bm, col, root), "stone2", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_box(bm, (0.5, 0.88, 0.36), (FR.x, FR.y, DAIS + 0.18))
    bm_box(bm, (0.56, 0.94, 0.07), (FR.x, FR.y, DAIS + 0.035))
    paint(mesh_obj("Sarcophagus", bm, col, root), "stone2", lo=0.1, hi=0.55)
    bm = bmesh.new()
    bm_box(bm, (0.42, 0.8, 0.02), (FR.x, FR.y, DAIS + 0.355))
    glow_obj("Sarcophagus_Glow", bm, col, root, CURSE, 1.0)
    bm = bmesh.new()                                        # glowing eyes in the crypt's doorway
    door = Vector((HUB.x, HUB.y - 0.15, 0)) + (Vector((FR.x - HUB.x, FR.y - HUB.y, 0)).normalized() * 0.55)
    for sx in (-1, 1):
        side = Vector((FR.y - HUB.y, -(FR.x - HUB.x), 0)).normalized()
        bm_ellipsoid(bm, tuple(door + side * sx * 0.09 + Vector((0, 0, T + 0.48))), (0.045, 0.045, 0.03), u=6, v=4)
    glow_obj("Crypt_Eyes", bm, col, root, CURSE, 1.2)
    head = empty("Head", col, root, (FR.x, FR.y, DAIS + 0.36), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.95), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "lid": ((0, -0.42, 0.0), (0, 0.42, 0.0), "root"),
         "hex": ((0, 0, 0.95), (0, 0, 1.15), "root")}


def build_head():
    col = collection("Hex_tomb")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    bm_box(bm, (0.56, 0.96, 0.08), (0.03, 0.04, 0.04), (0, 0, 9))
    bm_box(bm, (0.24, 0.12, 0.05), (0.03, 0.12, 0.1), (0, 0, 9))
    rig_part("Head_Lid", bm, "stone_dark", rig, "lid", col, bevel=0, lo=0.1, hi=0.5)
    cm = glow_mat("hex_curse", CURSE, 1.0)
    bm = bmesh.new()
    ring(bm, (0, 0, 0.95), 0.62, 0.55, -0.015, 0.015, seg=24)
    for k in range(6):
        a = math.radians(60 * k)
        p = Vector((math.cos(a) * 0.68, math.sin(a) * 0.68, 0.95))
        bm_box(bm, (0.09, 0.09, 0.03), tuple(p), (0, 0, 60 * k + 45))
    for tri in range(2):                                    # the hexagram: two triangles of thin bars
        pts = [Vector((math.cos(math.radians(90 + 120 * k + 60 * tri)) * 0.5, math.sin(math.radians(90 + 120 * k + 60 * tri)) * 0.5, 0.95)) for k in range(3)]
        for k in range(3):
            bm_beam(bm, pts[k], pts[(k + 1) % 3], 0.035, 0.02)
    rig_part("Head_Hex", bm, None, rig, "hex", col, bevel=0, mat=cm)
    return rig


IDLE_LEN = 96
FIRE_LEN = 24


def pose(rig, t=0.0, flare=1.0, lid=0.0, lift=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["hex"].rotation_quaternion = arm_space_quat(pb["hex"], (0, 0, 1), 360 * t)
    pb["hex"].location = arm_space_loc(pb["hex"], (0, 0, 0.05 * math.sin(2 * math.pi * t * 2) + lift))
    pb["hex"].scale = (flare, 1.0, flare)          # (an upright bone: its own Y is the height)
    pb["lid"].rotation_quaternion = arm_space_quat(pb["lid"], (0, 1, 0), lid * 6)
    pb["lid"].location = arm_space_loc(pb["lid"], (0, 0, abs(lid) * 0.03))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        rattle = math.sin(f * 2.2) * max(0.0, math.sin(2 * math.pi * t * 2)) ** 8
        pose(rig, t=t, flare=1.0 + 0.04 * math.sin(2 * math.pi * t * 4), lid=rattle)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        k = smooth(f / 3.0) * (1 - smooth((f - 6) / 16.0))
        pose(rig, t=0.15 * f / FIRE_LEN, flare=1.0 + 0.9 * k, lid=math.sin(f * 2.5) * (1 - f / FIRE_LEN), lift=0.2 * k)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 9.0, "yaw": 160, "pitch": 22, "anim_target": (FR.x, FR.y, 1.0), "anim_dist": 4.5,
           "frames": [("idle", 0), ("fire", 5), ("fire", 14)]}


def build_all():
    build_base()
    build_head()
    build_anims()
