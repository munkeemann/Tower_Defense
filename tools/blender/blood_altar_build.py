"""Builds the Blood Altar (footprint "pair": [0,0] front, [0,1] back), the Grave's Tier IV support tower: the towers
around it deal more damage and attack faster, and after every wave it drinks castle health.

    blender -b --factory-startup --python tools/blender/build_tower.py -- blood_altar <preview dir>

Front cell: a stepped altar of black stone with blood running down its steps from a brimming basin, four spiked
obsidian posts with candles at its corners and a blood crystal turning above it. Back cell: a ritual circle glowing in
the earth, a heap of candlelit skulls and a crooked iron fence. It's an aura tower: nothing aims. idle: the crystal
turns and bobs and pulses, drops of blood fall into the basin, the circle's runes breathe.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "blood_altar"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
T = TOP
BLOOD = (0.72, 0.02, 0.05)
STEPS = [(1.3, 0.16), (1.0, 0.16), (0.72, 0.18)]     # (width, height) of each step
ALTAR_TOP = T + sum(h for _, h in STEPS)
CRYSTAL = Vector((F.x, F.y, ALTAR_TOP + 0.95))


def build_base():
    col = collection("Blood_altar")
    root = empty("Blood_altar", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(66)
    # the stepped altar
    bm = bmesh.new()
    z = T
    for w, h in STEPS:
        bm_box(bm, (w, w, h), (F.x, F.y, z + h / 2))
        z += h
    o = paint(mesh_obj("Altar_Steps", bm, col, root), "stone_dark", lo=0.05, hi=0.55)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()                                          # the basin: a rim with a pool of blood in it
    ring(bm, (F.x, F.y, 0), 0.3, 0.22, ALTAR_TOP, ALTAR_TOP + 0.12, seg=14)
    paint(mesh_obj("Altar_Basin", bm, col, root), "stone2", lo=0.15, hi=0.6)
    blood = bmesh.new()
    bm_cyl(blood, 0.23, 0.23, 0.03, (F.x, F.y, ALTAR_TOP + 0.09), seg=14)
    # blood running over the basin's lip and down the steps on all four sides
    for k in range(4):
        a = math.radians(90 * k + 10)
        d = Vector((math.cos(a), math.sin(a), 0))
        n = Vector((-d.y, d.x, 0))
        x = 0.06 * (1 if k % 2 else -1)
        zz = ALTAR_TOP
        for (w, h) in reversed(STEPS):
            p = Vector((F.x, F.y, 0)) + d * (w / 2 + 0.008) + n * x
            bm_box(blood, (0.07, 0.07, h + 0.01), (p.x, p.y, zz - h / 2), rot=(0, 0, math.degrees(a)))
            q = Vector((F.x, F.y, 0)) + d * (w / 2 - 0.08) + n * x
            bm_box(blood, (0.18, 0.08, 0.012), (q.x, q.y, zz + 0.002), rot=(0, 0, math.degrees(a) + 90))
            zz -= h
    glow_obj("Altar_Blood", blood, col, root, BLOOD, 0.5)
    # four spiked obsidian posts at the corners, each with a candle
    posts = bmesh.new()
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p = Vector((F.x + 0.82 * math.cos(a), F.y + 0.82 * math.sin(a), 0))
        posts_h = 0.95
        bm_cyl(posts, 0.09, 0.06, posts_h, (p.x, p.y, T + posts_h / 2), seg=6)
        bm_cyl(posts, 0.06, 0.0, 0.28, (p.x, p.y, T + posts_h + 0.14), seg=6)
        for j in range(2):
            b_ = 2 * math.pi * j / 2 + a
            bm_beam(posts, Vector((p.x, p.y, T + 0.6 + 0.15 * j)), Vector((p.x + 0.16 * math.cos(b_), p.y + 0.16 * math.sin(b_), T + 0.75 + 0.15 * j)),
                    0.05, 0.05, w1=0.005, h1=0.005)
    paint(mesh_obj("Altar_Posts", posts, col, root), "black", lo=0.2, hi=0.7)
    for i, k in enumerate(range(4)):
        a = math.radians(45 + 90 * k)
        kk_import("halloween/candle", col, root, (F.x + 0.6 * math.cos(a), F.y + 0.6 * math.sin(a), T + STEPS[0][1]), 30 * k, 0.5,
                  name="Prop_Candle_%d" % i)
    # the back cell: a ritual circle, a heap of candlelit skulls, an iron fence
    circ = bmesh.new()
    ring(circ, (B.x, B.y, 0), 0.82, 0.76, T + 0.003, T + 0.012, seg=32)
    ring(circ, (B.x, B.y, 0), 0.58, 0.54, T + 0.003, T + 0.012, seg=28)
    for k in range(5):                                        # a pentagram's points on the inner ring
        a0 = math.radians(90 + 144 * k)
        a1 = math.radians(90 + 144 * (k + 1))
        bm_beam(circ, Vector((B.x + 0.56 * math.cos(a0), B.y + 0.56 * math.sin(a0), T + 0.008)),
                Vector((B.x + 0.56 * math.cos(a1), B.y + 0.56 * math.sin(a1), T + 0.008)), 0.035, 0.01)
    for k in range(8):                                        # runes round the outer ring
        a = 2 * math.pi * (k + 0.5) / 8
        bm_box(circ, (0.06, 0.12, 0.01), (B.x + 0.69 * math.cos(a), B.y + 0.69 * math.sin(a), T + 0.008), rot=(0, 0, math.degrees(a)))
    glow_obj("Ritual_Circle", circ, col, root, BLOOD, 0.45)
    kk = [("halloween/skull", (B.x - 0.12, B.y - 0.05, T), 170, 0.26), ("halloween/skull", (B.x + 0.14, B.y + 0.05, T), 200, 0.24),
          ("halloween/skull", (B.x + 0.0, B.y + 0.0, T + 0.12), 185, 0.24), ("halloween/skull_candle", (B.x + 0.18, B.y - 0.24, T), 150, 0.3),
          ("halloween/candle_triple", (B.x - 0.55, B.y - 0.45, T), 20, 0.45), ("halloween/candle_triple", (B.x + 0.6, B.y - 0.4, T), 70, 0.45),
          ("halloween/fence", (B.x - 0.05, B.y - 0.92, T), 180, 0.3), ("halloween/fence_pillar_broken", (B.x + 0.78, B.y - 0.7, T), 0, 0.3),
          ("halloween/bone_B", (B.x - 0.75, B.y + 0.2, T), 70, 0.55)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (F.x, F.y, ALTAR_TOP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.95), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "crystal": (tuple(CRYSTAL - Vector((0, 0, 0.2))), tuple(CRYSTAL + Vector((0, 0, 0.2))), "root"),
         "drop": (tuple(CRYSTAL - Vector((0, 0, 0.35))), tuple(CRYSTAL - Vector((0, 0, 0.55))), "root"),
         "drop2": (tuple(CRYSTAL - Vector((0.05, 0, 0.35))), tuple(CRYSTAL - Vector((0.05, 0, 0.55))), "root"),
         "circle": ((B.x, B.y, T), (B.x, B.y, T + 0.2), "root")}


def build_rig():
    col = collection("Blood_altar")
    root = bpy.data.objects["Blood_altar"]
    rig = make_rig(col, root, BONES)
    bm = bmesh.new()                                          # the crystal: a long double point with a ring of shards
    bm_cyl(bm, 0.0, 0.17, 0.32, tuple(CRYSTAL + Vector((0, 0, -0.16))), seg=6)
    bm_cyl(bm, 0.17, 0.0, 0.42, tuple(CRYSTAL + Vector((0, 0, 0.21))), seg=6)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        p = CRYSTAL + Vector((0.32 * math.cos(a), 0.32 * math.sin(a), 0.02))
        bm_cyl(bm, 0.0, 0.05, 0.1, tuple(p - Vector((0, 0, 0.05))), seg=4)
        bm_cyl(bm, 0.05, 0.0, 0.14, tuple(p + Vector((0, 0, 0.07))), seg=4)
    rig_part("Crystal", bm, None, rig, "crystal", col, bevel=0, mat=glow_mat("blood_crystal", BLOOD, 0.85))
    for name in ("drop", "drop2"):
        bm = bmesh.new()
        c = Vector(BONES[name][0])
        bm_ellipsoid(bm, tuple(c), (0.045, 0.045, 0.06), u=6, v=4)
        bm_cyl(bm, 0.035, 0.0, 0.06, tuple(c + Vector((0, 0, 0.06))), seg=6)
        rig_part("Blood_" + name, bm, None, rig, name, col, bevel=0, mat=glow_mat("blood_drop", BLOOD, 0.5))
    return rig


IDLE_LEN = 96


def pose(rig, t):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["crystal"].location = arm_space_loc(pb["crystal"], (0, 0, 0.08 * math.sin(2 * math.pi * t * 2)))
    pb["crystal"].rotation_quaternion = arm_space_quat(pb["crystal"], (0, 0, 1), 360 * t)
    k = 1.0 + 0.1 * math.sin(2 * math.pi * t * 4)
    pb["crystal"].scale = (k, k, k)
    fall = CRYSTAL.z - 0.35 - (ALTAR_TOP + 0.1)
    for name, off in (("drop", 0.0), ("drop2", 0.5)):
        u = (t * 3 + off) % 1.0
        pb[name].location = arm_space_loc(pb[name], (0, 0, -fall * u * u))
        s = 1.0 if u < 0.92 else 0.001
        pb[name].scale = (s, s, s)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 8.5, "yaw": 150, "pitch": 22, "anim_target": (F.x, F.y, ALTAR_TOP + 0.4), "anim_dist": 3.6,
           "frames": [("idle", 0), ("idle", 12), ("idle", 24)]}


def build_all():
    build_base()
    build_rig()
    build_anims()
