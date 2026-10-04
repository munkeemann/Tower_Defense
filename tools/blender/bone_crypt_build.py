"""Builds the Bone Crypt (footprint "single"), a Grave tower: cheap skeleton archers that hit air and ground.

    blender -b --factory-startup --python tools/blender/build_tower.py -- bone_crypt <preview dir>

A small stone crypt (Halloween Bits) stands at the front of the hex; behind it, on a raised step of old flagstones
(where the game's camera sees him clearly), a skeleton crossbowman (Crew, on the Head: he turns to aim) stands guard.
Candles, a skull post and a broken fence round it out, and two green soul-wisps drift round the crypt. idle: the wisps circle and bob. fire: they flare and dart.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "bone_crypt"
CELLS = [(0, 0)]
TOP = 0.34
T = TOP
SOUL = (0.55, 0.95, 0.4)
CRYPT = (-0.22, 0.38, TOP)
GUARD = Vector((0.3, -0.3, 0))


def build_base():
    col = collection("Bone_crypt")
    root = empty("Bone_crypt", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    for i, (rel, loc, rot, sc) in enumerate((("halloween/crypt", CRYPT, 180, 0.15),
                                              ("halloween/candle_triple", (0.68, 0.35, T), 20, 0.42),
                                              ("halloween/skull_candle", (-0.62, -0.5, T), -30, 0.28),
                                              ("halloween/post_skull", (0.62, 0.62, T), 200, 0.28),
                                              ("halloween/fence_broken", (-0.78, -0.05, T), 90, 0.26),
                                              ("halloween/bone_A", (0.05, -0.78, T + 0.02), 40, 0.4),
                                              ("halloween/skull", (0.72, -0.62, T), 160, 0.2))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    bm = bmesh.new()                                            # the guard's step: a raised ring of flagstones
    bm_cyl(bm, 0.38, 0.42, 0.24, (GUARD.x, GUARD.y, T + 0.12), seg=8)
    for k in range(7):
        a = math.radians(360 * k / 7 + rnd.uniform(-10, 10))
        p = GUARD + Vector((math.cos(a) * 0.22, math.sin(a) * 0.2, 0))
        bm_box(bm, (0.2, 0.17, 0.05), (p.x, p.y, T + 0.255), (0, 0, rnd.uniform(0, 60)))
    paint(mesh_obj("Step", bm, col, root), "stone2", lo=0.2, hi=0.6)
    head = empty("Head", col, root, (GUARD.x, GUARD.y, T + 0.27), 0.5, "SINGLE_ARROW")
    empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0.08, 0.35, 0.62), 0.2, "SPHERE")
    return root


def build_head():
    col = collection("Bone_crypt")
    root = bpy.data.objects["Bone_crypt"]
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "wisp.1": ((CRYPT[0], CRYPT[1], T + 1.1), (CRYPT[0], CRYPT[1], T + 1.3), "root"),
             "wisp.2": ((CRYPT[0], CRYPT[1], T + 0.8), (CRYPT[0], CRYPT[1], T + 1.0), "root")}
    rig = make_rig(col, root, bones)
    for i, (r, z) in enumerate(((0.62, 1.1), (0.55, 0.8))):
        bm = bmesh.new()
        c = Vector((CRYPT[0] + r, CRYPT[1], T + z))
        bm_ellipsoid(bm, tuple(c), (0.08, 0.08, 0.1), u=8, v=5)
        bm_cyl(bm, 0.06, 0.0, 0.2, tuple(c + Vector((0, 0, 0.13))), seg=6)          # a flame-tail
        rig_part("Wisp%d" % (i + 1), bm, None, rig, "wisp.%d" % (i + 1), col, bevel=0, mat=glow_mat("grave_soul", SOUL, 0.9))
    return rig


IDLE_LEN = 72
FIRE_LEN = 16


def pose(rig, t=0.0, flare=1.0, dart=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    for i, sp in ((1, 1.0), (2, -1.4)):
        b = pb["wisp.%d" % i]
        b.rotation_quaternion = arm_space_quat(b, (0, 0, 1), sp * 360 * t + 140 * i)
        b.location = arm_space_loc(b, (0, 0, 0.08 * math.sin(2 * math.pi * t * 2 + i) + dart * 0.15))
        s = flare
        b.scale = (s, s, s)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN, flare=1.0 + 0.1 * math.sin(2 * math.pi * f / IDLE_LEN * 3))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        k = smooth(f / 2.0) * (1 - smooth((f - 4) / 10.0))
        pose(rig, t=0.25 * f / FIRE_LEN, flare=1.0 + 0.7 * k, dart=k)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 6.0, "yaw": 160, "pitch": 20, "anim_target": (0, -0.2, 1.0), "anim_dist": 5.0,
           "frames": [("idle", 0), ("fire", 4)]}


def build_all():
    build_base()
    build_head()
    build_anims()
