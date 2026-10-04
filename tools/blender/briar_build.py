"""Builds the Briar Thicket (footprint "line4": [0,0]..[0,3]), a Verdant tower: an aura that slows and scratches.

    blender -b --factory-startup --python tools/blender/build_tower.py -- briar <preview dir>

A long hedge of brambles over four hexes: dark thorny vines arching between bushes and bare twisted saplings, red briar
roses here and there, and a great rose at the heart (the second cell). Its vines are rigged. idle: the vines sway, the
heart rose breathes. fire (every pulse): the vines lash up and the heart rose opens wide.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "briar"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
CS = [hex_to_world(0, i, MID) for i in range(4)]
TOP = 0.34
HEART = CS[1] + Vector((0.0, -0.3, 0))


def _arc(bm, a, b, h, w, n=6):
    """A drooping vine arching from a to b, h high, with thorns."""
    pts = [a.lerp(b, i / n) + Vector((0, 0, h * math.sin(math.pi * i / n))) for i in range(n + 1)]
    for i in range(n):
        bm_beam(bm, pts[i], pts[i + 1], w, w)
    return pts


def build_base():
    col = collection("Briar")
    root = empty("Briar", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(27)
    # a dark hedge running the length of the line, brambles arching over it, bushes and bare saplings
    hedge_a, hedge_b = bmesh.new(), bmesh.new()
    y = CS[3].y - 0.75
    i = 0
    while y < CS[0].y + 0.75:
        r = rnd.uniform(0.3, 0.42)
        bm_ellipsoid(hedge_a if i % 2 == 0 else hedge_b, (rnd.uniform(-0.25, 0.25), y, T + r * 0.55), (r * 1.25, r, r * 0.85),
                     (0, 0, rnd.uniform(0, 90)), u=8, v=5)
        y += r * 1.1
        i += 1
    paint(mesh_obj("Hedge", hedge_a, col, root), "teal", lo=0.35, hi=0.85)
    paint(mesh_obj("Hedge2", hedge_b, col, root), "grass", lo=0.45, hi=0.9)
    vine_b, thorn_b = bmesh.new(), bmesh.new()
    for k in range(9):
        y0 = CS[3].y + rnd.uniform(-0.6, 0.2) + k * 0.7
        a = Vector((rnd.uniform(-0.75, 0.75), y0, T))
        b = Vector((rnd.uniform(-0.75, 0.75), y0 + rnd.uniform(0.6, 1.2), T))
        pts = _arc(vine_b, a, b, rnd.uniform(0.6, 0.95), 0.07)
        for p in pts[1:-1]:
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1))).normalized()
            bm_cyl(thorn_b, 0.025, 0.0, 0.1, tuple(p + d * 0.05), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=4)
    paint(mesh_obj("Brambles", vine_b, col, root), "wood_dark", lo=0.2, hi=0.6)
    paint(mesh_obj("Bramble_Thorns", thorn_b, col, root), "cream", lo=0.2, hi=0.5)
    rose_b, leaf_b = bmesh.new(), bmesh.new()
    for k in range(7):
        c = Vector((rnd.uniform(-0.45, 0.45), rnd.uniform(CS[3].y - 0.6, CS[0].y + 0.6), T + rnd.uniform(0.55, 0.8)))
        bm_ellipsoid(rose_b, c, (0.08, 0.08, 0.06), u=6, v=4)
        bm_ellipsoid(leaf_b, c - Vector((0, 0, 0.06)), (0.12, 0.07, 0.03), (0, 0, rnd.uniform(0, 180)), u=6, v=3)
    paint(mesh_obj("Roses", rose_b, col, root), "red", lo=0.1, hi=0.5)
    paint(mesh_obj("Rose_Leaves", leaf_b, col, root), "grass", lo=0.4, hi=0.8)
    for i, (rel, cell, dx, dy, sc) in enumerate((("forest/Bush_1_E_Color1", 0, 0.45, 0.2, 0.32), ("forest/Tree_Bare_1_A_Color1", 0, -0.45, 0.35, 0.32),
                                                 ("forest/Bush_2_E_Color1", 1, 0.55, 0.45, 0.3), ("forest/Bush_1_C_Color1", 2, -0.5, 0.2, 0.34),
                                                 ("forest/Tree_Bare_2_A_Color1", 2, 0.45, -0.2, 0.3), ("forest/Bush_1_G_Color1", 3, 0.3, 0.1, 0.33),
                                                 ("forest/Rock_1_K_Color1", 3, -0.55, -0.35, 0.28))):
        c = CS[cell]
        kk_import(rel, col, root, (c.x + dx, c.y + dy, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (HEART.x, HEART.y, T), 0.5, "SINGLE_ARROW")
    return root


# rigged vines (in the head's space): each a chain of two bones rising from the ground
VINES = [(-0.55, 0.55, 30), (0.6, 0.3, -40), (-0.4, -0.75, 160), (0.5, -1.0, 210), (-0.2, 1.4, 80), (0.35, -2.4, 250),
         (-0.5, 2.6, 100), (0.1, -3.6, 270)]


def _bones():
    b = {"root": ((0, 0, 0), (0, 0, 0.2), None), "rose": ((0, 0, 1.0), (0, 0, 1.25), "root")}
    for i, (x, y, yaw) in enumerate(VINES):
        d = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
        p0 = Vector((x, y, 0))
        p1 = p0 + d * 0.25 + Vector((0, 0, 0.5))
        p2 = p1 + d * 0.35 + Vector((0, 0, 0.25))
        b["vine.%d.1" % i] = (tuple(p0), tuple(p1), "root")
        b["vine.%d.2" % i] = (tuple(p1), tuple(p2), "vine.%d.1" % i)
    return b


def build_head():
    col = collection("Briar")
    head = bpy.data.objects["Head"]
    bones = _bones()
    rig = make_rig(col, head, bones)
    rnd = random.Random(3)
    for i, (x, y, yaw) in enumerate(VINES):
        for seg in (1, 2):
            h, t, _ = bones["vine.%d.%d" % (i, seg)]
            bm = bmesh.new()
            bm_beam(bm, h, t, 0.08 if seg == 1 else 0.06, 0.08 if seg == 1 else 0.06, w1=0.06 if seg == 1 else 0.02, h1=0.06 if seg == 1 else 0.02)
            A, B = Vector(h), Vector(t)
            for k in range(3):
                p = A.lerp(B, (k + 0.5) / 3)
                d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.6))).normalized()
                bm_cyl(bm, 0.022, 0.0, 0.09, tuple(p + d * 0.04), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=4)
            rig_part("Head_Vine%d_%d" % (i, seg), bm, "wood_dark", rig, "vine.%d.%d" % (i, seg), col, bevel=0, lo=0.2, hi=0.6)
    # the heart rose: a stem, leaves and five petals around a dark core
    bm = bmesh.new()
    bm_beam(bm, (0, 0, 0), (0, 0, 0.98), 0.1, 0.1, w1=0.07, h1=0.07)
    for s in (-1, 1):
        bm_ellipsoid(bm, (s * 0.2, 0, 0.62), (0.22, 0.09, 0.03), (0, s * 20, 0), u=6, v=3)
    rig_part("Head_RoseStem", bm, "grass", rig, "root", col, bevel=0, lo=0.3, hi=0.7)
    bm = bmesh.new()
    for k in range(6):
        a = math.radians(60 * k)
        bm_ellipsoid(bm, (math.cos(a) * 0.22, math.sin(a) * 0.22, 1.06), (0.26, 0.16, 0.07), (0, -35, math.degrees(a)), u=7, v=4)
    bm_ellipsoid(bm, (0, 0, 1.12), (0.16, 0.16, 0.14), u=8, v=5)
    rig_part("Head_Rose", bm, "red", rig, "rose", col, bevel=0, lo=0.1, hi=0.55)
    empty("Muzzle", col, head, (0, 0, 1.1), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 18


def pose(rig, sway=0.0, lash=0.0, bloom=1.0, ph=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    for i, (x, y, yaw) in enumerate(VINES):
        d = (-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0)
        s = math.sin(ph + i * 0.9)
        pb["vine.%d.1" % i].rotation_quaternion = arm_space_quat(pb["vine.%d.1" % i], d, sway * s - lash * 0.6)
        pb["vine.%d.2" % i].rotation_quaternion = arm_space_quat(pb["vine.%d.2" % i], d, sway * 1.5 * s - lash)
    pb["rose"].scale = (bloom, 1.0 + (bloom - 1.0) * 0.4, bloom)          # (an upright bone: its own Y is the height)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, sway=7.0, ph=ph, bloom=1.0 + 0.05 * math.sin(ph * 2))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        l = 40 * smooth(f / 3.0) * (1 - smooth((f - 4) / 12.0))
        pose(rig, sway=3.0, ph=f * 0.4, lash=l, bloom=1.0 + 0.4 * smooth(f / 3.0) * (1 - smooth((f - 6) / 10.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.6), "dist": 11.0, "yaw": 130, "pitch": 26, "anim_target": (HEART.x, HEART.y, 0.8), "anim_dist": 5.0,
           "frames": [("idle", 0), ("fire", 4), ("fire", 10)]}


def build_all():
    build_base()
    build_head()
    build_anims()
