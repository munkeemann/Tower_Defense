"""Builds the Mass Grave (footprint "line4": [0,0] .. [0,3] in a line), a Grave tower: a long trench of grasping dead
hands that claw and slow ground enemies passing it.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mass_grave <preview dir>

A trench runs the length of the four cells between heaped earth banks, dark at the bottom, and from it rise twelve
skeletal arms with clawing hands. Headstones, a coffin lid, a shovel stuck in the dirt, candles and fence posts line
the banks. It's an aura (it doesn't turn). idle: the arms sway and the hands clutch. fire (every claw): every arm thrusts
up and the hands snap shut.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "mass_grave"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
CS = [hex_to_world(0, s, MID) for s in range(4)]
TOP = 0.34
T = TOP
Y0, Y1 = CS[3].y - 0.75, CS[0].y + 0.75
ARMS = []
_r = random.Random(17)
for _c in CS:
    for _k, (_x, _dy) in enumerate(((-0.13, 0.5), (0.12, 0.0), (-0.08, -0.5))):
        ARMS.append((Vector((_x + _r.uniform(-0.04, 0.04), _c.y + _dy + _r.uniform(-0.08, 0.08), T)),
                     _r.uniform(-25, 25), _r.uniform(0.62, 0.8)))


def build_base():
    col = collection("Mass_grave")
    root = empty("Mass_grave", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(31)
    # the trench: two earth banks, a dark pit between
    earth, dark = bmesh.new(), bmesh.new()
    n = 14
    for sx in (-1, 1):
        for k in range(n):
            y = Y0 + (Y1 - Y0) * (k + 0.5) / n
            r = rnd.uniform(0.2, 0.27)
            bm_ellipsoid(earth, (sx * 0.5 + rnd.uniform(-0.04, 0.04), y, T + r * 0.3), (r * 1.1, (Y1 - Y0) / n * 0.75, r * 0.65),
                         rot=(0, 0, rnd.uniform(-10, 10)), u=7, v=4)
    bm_box(dark, (0.62, Y1 - Y0 - 0.2, 0.03), (0, (Y0 + Y1) / 2, T + 0.015))
    paint(mesh_obj("Banks", earth, col, root), EARTH_SW, lo=0.2, hi=0.75)
    paint(mesh_obj("Pit", dark, col, root), "black", lo=0.3, hi=0.6)
    props = []
    for i, c in enumerate(CS):
        sx = 1 if i % 2 == 0 else -1
        props.append(("halloween/" + ("gravestone" if i % 2 else "gravemarker_A"), (sx * 0.85, c.y + 0.2, T), 90 * sx + rnd.uniform(-15, 15), 0.28))
        props.append(("halloween/candle_triple", (-sx * 0.85, c.y - 0.35, T), rnd.uniform(0, 90), 0.36))
    props += [("halloween/fence_pillar", (0.85, CS[3].y - 0.55, T), 0, 0.3), ("halloween/fence_pillar", (-0.85, CS[0].y + 0.55, T), 0, 0.3),
              ("halloween/coffin_decorated", (-0.82, CS[2].y + 0.25, T), 95, 0.2), ("halloween/ribcage", (0.85, CS[1].y - 0.4, T + 0.08), 40, 0.32),
              ("halloween/skull", (-0.8, CS[1].y + 0.3, T), 100, 0.18)]
    for i, (rel, loc, rot, sc) in enumerate(props):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    bm = bmesh.new()                                         # a shovel stuck in the bank
    s0 = Vector((0.58, CS[2].y - 0.3, T + 0.05))
    s1 = s0 + Vector((0.1, 0.05, 0.75))
    bm_beam(bm, s0, s1, 0.045, 0.045)
    bm_beam(bm, s1, s1 + Vector((0.0, 0.0, 0.0)) + Vector((0.12, 0, 0.0)), 0.04, 0.04)
    paint(mesh_obj("Shovel_Haft", bm, col, root), "wood", lo=0.3, hi=0.7)
    bm = bmesh.new()
    bm_box(bm, (0.2, 0.04, 0.24), (s0.x - 0.01, s0.y, s0.z - 0.02))
    paint(mesh_obj("Shovel_Blade", bm, col, root), "iron", lo=0.1, hi=0.5)
    head = empty("Head", col, root, (0, 0, T), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.4), 0.2, "SPHERE")
    return root


def build_head():
    col = collection("Mass_grave")
    head = bpy.data.objects["Head"]
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None)}
    for i, (base, lean, h) in enumerate(ARMS):
        d = Vector((math.sin(math.radians(lean)) * 0.35, 0.15 * (1 if i % 2 == 0 else -1), 1)).normalized()
        b0 = base - Vector((0, 0, T))
        b1 = b0 + d * h
        bones["arm.%d" % i] = (tuple(b0), tuple(b1), "root")
        bones["hand.%d" % i] = (tuple(b1), tuple(b1 + d * 0.15), "arm.%d" % i)
    rig = make_rig(col, head, bones)
    for i in range(len(ARMS)):
        b0, b1, _ = bones["arm.%d" % i]
        b0, b1 = Vector(b0), Vector(b1)
        d = (b1 - b0).normalized()
        side = d.cross(Vector((0, 1, 0))).normalized()
        bm = bmesh.new()
        bm_beam(bm, b0, b1, 0.095, 0.095, w1=0.075, h1=0.075)
        bm_beam(bm, b0 + side * 0.05, b1 + side * 0.04, 0.05, 0.05)           # the second forearm bone
        bm_ellipsoid(bm, tuple(b1), (0.075, 0.075, 0.07), u=6, v=4)
        rig_part("Head_Arm%d" % i, bm, BONE_SW, rig, "arm.%d" % i, col, bevel=0, lo=0.1, hi=0.5)
        bm = bmesh.new()
        bm_hand(bm, b1, d, side, s=0.24, curl=0.35)
        rig_part("Head_Hand%d" % i, bm, BONE_SW, rig, "hand.%d" % i, col, bevel=0, lo=0.05, hi=0.4)
    return rig


IDLE_LEN = 72
FIRE_LEN = 20


def pose(rig, t=0.0, thrust=0.0, clutch=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    for i in range(len(ARMS)):
        a = pb["arm.%d" % i]
        h = pb["hand.%d" % i]
        ph = 2 * math.pi * t + i * 1.7
        a.rotation_quaternion = arm_space_quat(a, (1, 0, 0), 12 * math.sin(ph) * (1 - thrust)) @ arm_space_quat(a, (0, 1, 0), 10 * math.cos(ph * 0.5 + i))
        a.location = arm_space_loc(a, (0, 0, -0.18 + 0.18 * thrust + 0.04 * math.sin(ph * 1.3)))
        h.rotation_quaternion = arm_space_quat(h, (1, 0, 0), 25 * clutch + 15 * math.sin(ph * 2) * (1 - thrust))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, thrust=0.45 + 0.15 * math.sin(2 * math.pi * t), clutch=0.3 + 0.3 * math.sin(4 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        up = smooth(f / 3.0) * (1 - smooth((f - 8) / 12.0))
        pose(rig, t=f / FIRE_LEN * 0.3, thrust=0.45 + 0.55 * up, clutch=smooth((f - 3) / 2.0) * (1 - smooth((f - 9) / 9.0)) * 1.4)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.6), "dist": 12.0, "yaw": 150, "pitch": 26, "anim_target": (0, CS[1].y, 0.7), "anim_dist": 4.5,
           "frames": [("idle", 0), ("idle", 36), ("fire", 4), ("fire", 9)]}


def build_all():
    build_base()
    build_head()
    build_anims()
