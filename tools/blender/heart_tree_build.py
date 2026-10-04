"""Builds the Heart of the Forest (footprint "star5": [0,0] the middle, [1,-1] / [-1,0] front-right / front-left,
[1,0] / [-1,1] back-right / back-left), the Verdant's Tier IV support tower: the towers around it hit harder, more so for
every wave it has stood.

    blender -b --factory-startup --python tools/blender/build_tower.py -- heart_tree <preview dir>

On the middle hex stands an ancient tree on a raised bed of turf: a gnarled trunk split open at the front round a
glowing green heart-seed, great roots snaking out across all four outer hexes, and a wide crown of leaf clumps hung
with glowing blossoms. Mushrooms, flowers, ferns and mossy stones grow among the roots, and wisps circle the heart.
It's an aura tower: nothing aims. idle: the heart beats, the crown sways, the wisps circle and bob.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "heart_tree"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C = hex_to_world(0, 0, MID)
OUT = [hex_to_world(q, s, MID) for q, s in [(1, -1), (-1, 0), (1, 0), (-1, 1)]]
TOP = 0.34
HEART = (0.55, 1.0, 0.45)
BLOSSOM = (1.0, 0.55, 0.8)
CROWN_Z = 2.45


def build_base():
    col = collection("Heart_tree")
    root = empty("Heart_tree", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(17)
    # the trunk: two great halves split apart at the front round the heart, with a heavy base
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_beam(bm, (C.x + sx * 0.36, C.y - 0.02, T - 0.02), (C.x + sx * 0.3, C.y - 0.02, T + 1.05), 0.46, 0.7, w1=0.34, h1=0.56)
        bm_beam(bm, (C.x + sx * 0.3, C.y - 0.02, T + 1.0), (C.x + sx * 0.08, C.y - 0.08, T + 1.85), 0.34, 0.56, w1=0.28, h1=0.42)
    bm_beam(bm, (C.x, C.y - 0.32, T - 0.02), (C.x, C.y - 0.26, T + 1.65), 0.62, 0.4, w1=0.42, h1=0.32)        # the back of the trunk
    bm_beam(bm, (C.x, C.y - 0.1, T + 1.65), (C.x - 0.05, C.y, T + 2.4), 0.56, 0.56, w1=0.36, h1=0.36)
    for sx, ang in ((-1, 30), (1, -20), (0, 180)):                                                        # limbs into the crown
        a = math.radians(90 + ang)
        bm_beam(bm, (C.x, C.y, T + 1.7), (C.x + math.cos(a) * 0.95, C.y + math.sin(a) * 0.6, T + 2.35), 0.2, 0.2, w1=0.1, h1=0.1)
    o = paint(mesh_obj("Tree_Trunk", bm, col, root), "wood_dark", lo=0.15, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    # roots snaking out over every outer hex
    bm = bmesh.new()
    for c in OUT:
        d = Vector((c.x - C.x, c.y - C.y, 0))
        L = d.length
        d.normalize()
        n = Vector((-d.y, d.x, 0))
        pts = [Vector((C.x, C.y, T + 0.35)) + d * 0.25]
        for k in range(1, 5):
            t = k / 4
            pts.append(Vector((C.x, C.y, T)) + d * (0.25 + (L + 0.35) * t) + n * 0.2 * math.sin(t * 5 + c.x) + Vector((0, 0, 0.12 * (1 - t) + 0.03)))
        for i, (a, b_) in enumerate(zip(pts, pts[1:])):
            w0, w1 = 0.3 - 0.06 * i, 0.3 - 0.06 * (i + 1)
            bm_beam(bm, a, b_, w0, w0 * 0.7, w1=w1, h1=w1 * 0.7)
        side = pts[2] + n * 0.05
        bm_beam(bm, side, side + n * 0.5 + d * 0.2 + Vector((0, 0, -0.05)), 0.12, 0.09, w1=0.04, h1=0.03)
    for k in range(3):                                                                                     # short roots at the back
        a = math.radians(-90 + (k - 1) * 40)
        bm_beam(bm, (C.x + math.cos(a) * 0.2, C.y + math.sin(a) * 0.2, T + 0.3), (C.x + math.cos(a) * 0.9, C.y + math.sin(a) * 0.9, T + 0.02),
                0.22, 0.16, w1=0.06, h1=0.05)
    paint(mesh_obj("Tree_Roots", bm, col, root), "wood_dark", lo=0.2, hi=0.85)
    veins = bmesh.new()                                       # the heart's light running out along the roots and up the trunk
    for c in OUT:
        d = Vector((c.x - C.x, c.y - C.y, 0))
        L = d.length
        d.normalize()
        n = Vector((-d.y, d.x, 0))
        pts = [Vector((C.x, C.y, T)) + d * (0.25 + (L + 0.35) * t) + n * 0.2 * math.sin(t * 5 + c.x) + Vector((0, 0, 0.12 * (1 - t) + 0.03 + (0.3 - 0.06 * k * 0) * 0.0))
               for k, t in enumerate((0.15, 0.4, 0.65, 0.85))]
        for i, (a_, b_) in enumerate(zip(pts, pts[1:])):
            hgt = (0.3 - 0.06 * (i + 1.5)) * 0.7
            bm_beam(veins, a_ + Vector((0, 0, hgt * 0.5 + 0.005)), b_ + Vector((0, 0, hgt * 0.5 - 0.01)), 0.05, 0.02, w1=0.03, h1=0.02)
    for sx in (-1, 1):
        bm_beam(veins, Vector((C.x + sx * 0.2, C.y - 0.62, T + 0.15)), Vector((C.x + sx * 0.12, C.y - 0.55, T + 1.5)), 0.05, 0.03, w1=0.03, h1=0.02)
    glow_obj("Tree_Veins", veins, col, root, HEART, 0.8)
    # the hollow: a dark cleft between the trunk halves
    bm = bmesh.new()
    bm_ellipsoid(bm, (C.x, C.y - 0.04, T + 0.92), (0.3, 0.14, 0.6), u=8, v=6)
    paint(mesh_obj("Tree_Hollow", bm, col, root), "black", lo=0.3, hi=0.6)
    # the crown: overlapping leaf clumps in two greens, hung with glowing blossoms
    lo_b, hi_b, bl = bmesh.new(), bmesh.new(), bmesh.new()
    clumps = [(0, 0, CROWN_Z + 0.25, 1.1), (0.95, 0.2, CROWN_Z - 0.1, 0.8), (-0.95, 0.15, CROWN_Z - 0.05, 0.82),
              (0.4, -0.75, CROWN_Z - 0.05, 0.75), (-0.45, -0.7, CROWN_Z, 0.72), (0.1, 0.8, CROWN_Z - 0.15, 0.68),
              (0.0, 0.0, CROWN_Z + 0.9, 0.7)]
    for i, (dx, dy, z, r) in enumerate(clumps):
        bm_ellipsoid(lo_b if i % 2 == 0 else hi_b, (C.x + dx, C.y + dy, T + z), (r, r, r * 0.75), (0, 0, rnd.uniform(0, 90)), u=9, v=6)
    for k in range(16):
        dx, dy, z, r = clumps[k % len(clumps)]
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(-0.4, 0.5)
        p = Vector((C.x + dx + math.cos(a) * r * 0.95 * math.cos(e), C.y + dy + math.sin(a) * r * 0.95 * math.cos(e), T + z + r * 0.72 * math.sin(e)))
        bm_ellipsoid(bl, tuple(p), (0.07, 0.07, 0.07), u=6, v=4)
    paint(mesh_obj("Crown_Leaves", lo_b, col, root), "grass", lo=0.1, hi=0.85)
    paint(mesh_obj("Crown_Leaves2", hi_b, col, root), "lime", lo=0.2, hi=0.85)
    glow_obj("Crown_Blossoms", bl, col, root, BLOSSOM, 0.35)
    # life among the roots: mushrooms, flowers, ferns, mossy stones
    kk = [("props/Mushroom", (OUT[0].x + 0.4, OUT[0].y + 0.35, T - 0.02), 0, 0.7), ("props/Mushroom", (OUT[3].x - 0.45, OUT[3].y - 0.3, T - 0.02), 60, 0.6),
          ("props/Mushroom", (OUT[1].x - 0.45, OUT[1].y + 0.35, T - 0.02), 30, 0.55), ("forest/Rock_1_E_Color1", (OUT[2].x + 0.45, OUT[2].y - 0.35, T - 0.02), 80, 0.3),
          ("forest/Grass_2_B_Color1", (OUT[0].x - 0.4, OUT[0].y - 0.4, T - 0.02), 10, 0.6), ("forest/Grass_1_C_Color1", (OUT[2].x - 0.5, OUT[2].y + 0.3, T - 0.02), 40, 0.6),
          ("forest/Rock_1_A_Color1", (OUT[3].x + 0.4, OUT[3].y + 0.45, T - 0.02), 120, 0.25), ("props/Basket_Mushrooms", (OUT[1].x + 0.45, OUT[1].y - 0.45, T - 0.02), 200, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (C.x, C.y, T + 0.9), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.15, 0.05), 0.2, "SPHERE")
    return root


T0 = TOP + 0.05            # the turf's top (plinth(turf=True))
HEART_C = Vector((0, 0.12, T0 + 0.95))
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "heart": (tuple(HEART_C - Vector((0, 0, 0.15))), tuple(HEART_C + Vector((0, 0, 0.15))), "root"),
         "crown": ((0, 0, T0 + 1.9), (0, 0, T0 + 2.4), "root"),
         "wisps": (tuple(HEART_C), tuple(HEART_C + Vector((0, 0, 0.3))), "root")}


def build_rig():
    col = collection("Heart_tree")
    root = bpy.data.objects["Heart_tree"]
    rig = make_rig(col, root, BONES)
    # the crown sways as one: move the leaf clumps and blossoms onto the crown bone
    for name in ("Crown_Leaves", "Crown_Leaves2", "Crown_Blossoms"):
        o = bpy.data.objects[name]
        o.parent = rig
        skin_to(o, rig, "crown")
    bm = bmesh.new()                                          # the heart-seed: a faceted green gem
    bm_cyl(bm, 0.0, 0.24, 0.28, tuple(HEART_C - Vector((0, 0, 0.14))), seg=6)
    bm_cyl(bm, 0.24, 0.0, 0.38, tuple(HEART_C + Vector((0, 0, 0.19))), seg=6)
    rig_part("Heart_Seed", bm, None, rig, "heart", col, bevel=0, mat=glow_mat("heart_seed", HEART, 1.1))
    bm = bmesh.new()                                          # vines wrapping it
    for k in range(3):
        a0 = 2 * math.pi * k / 3
        pts = [HEART_C + Vector((0.2 * math.cos(a0 + t), 0.2 * math.sin(a0 + t) * 0.6, -0.25 + 0.2 * t)) for t in (0.0, 1.0, 2.0, 3.0)]
        for a, b_ in zip(pts, pts[1:]):
            bm_beam(bm, a, b_, 0.04, 0.04)
    rig_part("Heart_Vines", bm, "grass", rig, "heart", col, bevel=0, lo=0.2, hi=0.7)
    bm = bmesh.new()                                          # wisps circling the heart
    for k in range(5):
        a = 2 * math.pi * k / 5
        p = HEART_C + Vector((0.85 * math.cos(a), 0.85 * math.sin(a), 0.3 * math.sin(a * 2)))
        bm_ellipsoid(bm, tuple(p), (0.06, 0.06, 0.06), u=6, v=4)
        bm_cyl(bm, 0.045, 0.0, 0.12, tuple(p + Vector((0, 0, 0.08))), seg=5)
    rig_part("Heart_Wisps", bm, None, rig, "wisps", col, bevel=0, mat=glow_mat("heart_wisp", (0.6, 1.0, 0.45), 0.8))
    return rig


IDLE_LEN = 96


def pose(rig, t):
    pb = rig.pose.bones
    rest_pose(rig)
    beat = (t * 4) % 1.0                                      # a double heartbeat, four times a loop
    k = 1.0 + 0.22 * math.exp(-((beat - 0.1) / 0.05) ** 2) + 0.14 * math.exp(-((beat - 0.3) / 0.05) ** 2)
    pb["heart"].scale = (k, k, k)
    pb["crown"].rotation_quaternion = arm_space_quat(pb["crown"], (1, 0, 0), 2.0 * math.sin(2 * math.pi * t)) @ \
        arm_space_quat(pb["crown"], (0, 1, 0), 1.5 * math.sin(2 * math.pi * t * 2 + 0.6))
    pb["wisps"].rotation_quaternion = arm_space_quat(pb["wisps"], (0, 0, 1), 360 * t)
    pb["wisps"].location = arm_space_loc(pb["wisps"], (0, 0, 0.1 * math.sin(2 * math.pi * t * 3)))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.3), "dist": 11.0, "yaw": 160, "pitch": 18, "anim_target": (0, 0, TOP + 1.2), "anim_dist": 4.5,
           "frames": [("idle", 0), ("idle", 3), ("idle", 30)]}


def build_all():
    build_base()
    build_rig()
    build_anims()
