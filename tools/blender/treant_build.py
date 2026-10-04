"""Builds the Elder Treant (footprint "star5": [0,0] middle, [1,-1], [-1,0], [1,0], [-1,1] around it), a Verdant tower:
it slams the ground at short range.

    blender -b --factory-startup --python tools/blender/build_tower.py -- treant <preview dir>

A walking oak stands on the middle cell: a thick bark body with a carved face and glowing eyes, mossy shoulders, two
branch arms ending in twig claws, root feet, and a leafy crown (the Head: it turns toward its target). Its roots run out
over the four cells around it, among mossy rocks, mushrooms and saplings. idle: it sways, the crown rustles, it blinks.
fire: it lifts both arms over its head and slams them down in front of it.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "treant"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)
OTHERS = [hex_to_world(q, s, MID) for q, s in CELLS[1:]]
TOP = 0.34
EYES = (0.85, 1.0, 0.35)
TS = 1.25


def build_base():
    col = collection("Treant")
    root = empty("Treant", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True, stone="stone_warm")
    rnd = random.Random(52)
    bm = bmesh.new()
    for p in OTHERS:
        d = (p - C0).normalized()
        a = C0 + d * 0.55
        b = p + d * 0.35 + Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0))
        m = a.lerp(b, 0.5)
        bm_beam(bm, Vector((a.x, a.y, T + 0.12)), Vector((m.x, m.y, T + 0.18)), 0.22, 0.18, w1=0.16, h1=0.14)
        bm_beam(bm, Vector((m.x, m.y, T + 0.18)), Vector((b.x, b.y, T - 0.01)), 0.16, 0.14, w1=0.05, h1=0.05)
    paint(mesh_obj("Roots", bm, col, root), "wood_dark", lo=0.2, hi=0.75)
    props = [("forest/Rock_1_C_Color1", 0.5), ("forest/Bush_1_A_Color1", 0.3), ("forest/Tree_2_A_Color1", 0.22), ("forest/Rock_3_E_Color1", 0.45)]
    shroom_cap, shroom_stalk = bmesh.new(), bmesh.new()
    for i, p in enumerate(OTHERS):
        rel, sc = props[i % len(props)]
        side = (p - C0).normalized().cross(Vector((0, 0, 1)))
        q = p + side * 0.45
        kk_import(rel, col, root, (q.x, q.y, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
        m = p - side * 0.4
        for k in range(2):
            c = m + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0))
            h = rnd.uniform(0.12, 0.24)
            bm_beam(shroom_stalk, Vector((c.x, c.y, T)), Vector((c.x, c.y, T + h)), 0.05, 0.05)
            bm_ellipsoid(shroom_cap, (c.x, c.y, T + h), (0.1, 0.1, 0.06), u=8, v=4)
    paint(mesh_obj("Shroom_Stalks", shroom_stalk, col, root), "cream", lo=0.2, hi=0.6)
    paint(mesh_obj("Shroom_Caps", shroom_cap, col, root), "roof", lo=0.1, hi=0.5)
    empty("Head", col, root, (C0.x, C0.y, T), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, 0, 0.2), (0, 0, 1.1), "root"),
    "crown": ((0, 0, 1.45), (0, 0, 1.8), "body"),
    "arm.L.1": ((-0.42, 0.12, 1.05), (-0.66, 0.3, 0.72), "body"),
    "arm.L.2": ((-0.66, 0.3, 0.72), (-0.6, 0.6, 0.45), "arm.L.1"),
    "arm.R.1": ((0.42, 0.12, 1.05), (0.66, 0.3, 0.72), "body"),
    "arm.R.2": ((0.66, 0.3, 0.72), (0.6, 0.6, 0.45), "arm.R.1"),
    "eyes": ((0, 0.3, 0.98), (0, 0.4, 0.98), "body"),
}


def build_head():
    col = collection("Treant")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=TS)
    rnd = random.Random(7)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, scale=TS, **kw)

    # body: a tapering trunk, bark ridges, root feet
    bm = bmesh.new()
    bm_cyl(bm, 0.42, 0.34, 1.25, (0, 0, 0.72), seg=8)
    for k in range(6):
        a = math.radians(60 * k + 20)
        bm_beam(bm, (math.cos(a) * 0.36, math.sin(a) * 0.36, 0.25), (math.cos(a) * 0.32, math.sin(a) * 0.32, 1.25), 0.1, 0.08, w1=0.06, h1=0.05)
    for k in range(5):
        a = math.radians(72 * k + 50)
        bm_beam(bm, (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.3), (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.02), 0.18, 0.15, w1=0.08, h1=0.06)
    P("Head_Body", bm, "wood_dark", "body", lo=0.15, hi=0.8)
    # the face: a heavy brow, a hollow mouth; moss on the shoulders
    bm = bmesh.new()
    bm_beam(bm, (-0.2, 0.33, 1.07), (0.2, 0.33, 1.07), 0.08, 0.1, up=(0, 1, 0))
    bm_ellipsoid(bm, (0, 0.35, 0.8), (0.1, 0.035, 0.07), u=7, v=4)
    P("Head_Face", bm, "black", "body", lo=0.3, hi=0.6)
    bm = bmesh.new()
    for s in (-1, 1):
        bm_ellipsoid(bm, (s * 0.1, 0.35, 0.98), (0.055, 0.03, 0.04), u=6, v=4)
    rig_part("Head_Eyes", bm, None, rig, "eyes", col, bevel=0, scale=TS, mat=glow_mat("treant_eyes", EYES, 1.0))
    bm = bmesh.new()
    for k in range(6):
        a = math.radians(60 * k + rnd.uniform(-15, 15))
        bm_ellipsoid(bm, (math.cos(a) * 0.36, math.sin(a) * 0.32, 1.22 + rnd.uniform(-0.05, 0.05)), (0.16, 0.12, 0.08), (0, 0, math.degrees(a)), u=7, v=4)
    P("Head_Moss", bm, "grass", "body", lo=0.35, hi=0.75)
    # the crown: leaf clumps on a few short boughs
    bm = bmesh.new()
    for k in range(4):
        a = math.radians(90 * k + 30)
        bm_beam(bm, (0, 0, 1.3), (math.cos(a) * 0.35, math.sin(a) * 0.35, 1.6), 0.1, 0.1, w1=0.05, h1=0.05)
    P("Head_Boughs", bm, "wood_dark", "crown", lo=0.3, hi=0.7)
    la, lb = bmesh.new(), bmesh.new()
    for i, (x, y, z, r) in enumerate(((0, 0, 1.75, 0.55), (0.42, 0.1, 1.62, 0.38), (-0.4, -0.05, 1.65, 0.4), (0.05, 0.4, 1.6, 0.35),
                                      (-0.05, -0.4, 1.66, 0.36), (0.1, 0.05, 2.08, 0.34))):
        bm_ellipsoid(la if i % 2 == 0 else lb, (x, y, z), (r, r, r * 0.8), (0, 0, rnd.uniform(0, 90)), u=8, v=6)
    P("Head_Leaves", la, "grass", "crown", lo=0.1, hi=0.8)
    P("Head_Leaves2", lb, "teal", "crown", lo=0.3, hi=0.8)
    # branch arms with twig claws
    for s, sx in (("L", -1), ("R", 1)):
        for seg in (1, 2):
            h, t, _ = BONES["arm.%s.%d" % (s, seg)]
            bm = bmesh.new()
            w0, w1 = (0.24, 0.18) if seg == 1 else (0.18, 0.1)
            bm_beam(bm, h, t, w0, w0, w1=w1, h1=w1)
            if seg == 2:
                T_ = Vector(t)
                for k in range(3):
                    d = Vector(((k - 1) * 0.5 * sx * 0.4, 1.0, -0.6)).normalized()
                    bm_beam(bm, T_, T_ + d * 0.28, 0.07, 0.07, w1=0.0, h1=0.0)
            P("Head_Arm%s%d" % (s, seg), bm, "wood_dark", "arm.%s.%d" % (s, seg), lo=0.2, hi=0.7)
        bm = bmesh.new()
        bm_ellipsoid(bm, (sx * 0.5, 0.06, 0.92), (0.12, 0.1, 0.06), u=6, v=4)
        P("Head_ArmLeaves%s" % s, bm, "grass", "arm.%s.1" % s, lo=0.3, hi=0.7)
    empty("Muzzle", col, head, (0, 0.8 * TS, 0.4 * TS), 0.2, "SPHERE")
    return rig


IDLE_LEN = 80
FIRE_LEN = 24


def pose(rig, sway=0.0, rustle=0.0, blink=1.0, lift=0.0, slam=0.0, lean=0.0, arms=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["body"].rotation_quaternion = arm_space_quat(pb["body"], (0, 1, 0), sway) @ arm_space_quat(pb["body"], (1, 0, 0), lean)
    pb["crown"].rotation_quaternion = arm_space_quat(pb["crown"], (0, 1, 0), rustle) @ arm_space_quat(pb["crown"], (1, 0, 0), rustle * 0.5)
    pb["eyes"].scale = (1.0, 1.0, blink)
    for s, sx in (("L", -1), ("R", 1)):
        up = lift * 115 - slam * 35
        pb["arm.%s.1" % s].rotation_quaternion = (arm_space_quat(pb["arm.%s.1" % s], (1, 0, 0), up)
                                                 @ arm_space_quat(pb["arm.%s.1" % s], (0, 1, 0), sx * (arms - lift * 25)))
        pb["arm.%s.2" % s].rotation_quaternion = arm_space_quat(pb["arm.%s.2" % s], (1, 0, 0), lift * 30 - slam * 20)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        blink = 0.15 if 56 <= f <= 60 else 1.0
        pose(rig, sway=3 * math.sin(ph), rustle=4 * math.sin(ph * 2 + 1), blink=blink, arms=4 * math.sin(ph + 0.5))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        lift = smooth(f / 8.0) * (1 - smooth((f - 9) / 3.0))
        slam = smooth((f - 9) / 3.0) * (1 - smooth((f - 14) / 10.0))
        lean = -6 * lift + 14 * slam
        pose(rig, lift=lift, slam=slam, lean=lean, rustle=10 * slam)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.3), "dist": 10.5, "yaw": 160, "pitch": 18, "anim_target": (C0.x, C0.y, 1.6), "anim_dist": 6.0,
           "frames": [("idle", 0), ("fire", 8), ("fire", 12), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
