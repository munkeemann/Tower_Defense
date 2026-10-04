"""Builds the Thornspitter (footprint "single"), a Verdant tower: a carnivorous thorn plant.

    blender -b --factory-startup --python tools/blender/build_tower.py -- thorn <preview dir>

A root bulb sits in mossy turf among bushes and stones; a thorny stalk carries a pod with a toothed mouth and a crown of
thorns (the Head: it turns to aim, thorns leave from its mouth). idle: the stalk sways, the pod breathes, the leaves
stir. fire: the pod jerks back and its jaw snaps open.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "thorn"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34


def build_base():
    col = collection("Thorn")
    root = empty("Thorn", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True, stone="stone_warm")
    rnd = random.Random(5)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0, T + 0.12), (0.42, 0.42, 0.24))
    for k in range(6):
        a = math.radians(60 * k + rnd.uniform(-15, 15))
        p0 = Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, T + 0.12))
        p1 = Vector((math.cos(a) * 0.82, math.sin(a) * 0.82, T + 0.02))
        bm_beam(bm, p0, p1, 0.14, 0.12, w1=0.05, h1=0.05)
    paint(mesh_obj("Roots", bm, col, root), "wood_dark", lo=0.2, hi=0.7)
    bm = bmesh.new()
    for k in range(3):
        a = math.radians(120 * k + 40)
        bm_rock(bm, rnd, Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 0)), rnd.uniform(0.18, 0.26), T - 0.02, rnd.uniform(0.1, 0.2))
    o = paint(mesh_obj("Stones", bm, col, root), "stone_warm", lo=0.2, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    for i, (rel, ang, r, sc) in enumerate((("forest/Bush_1_C_Color1", 200, 0.72, 0.35), ("forest/Bush_2_B_Color1", 300, 0.7, 0.3),
                                           ("forest/Grass_1_B_Color1", 100, 0.62, 0.6))):
        a = math.radians(ang)
        kk_import(rel, col, root, (math.cos(a) * r, math.sin(a) * r, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (0, 0, T + 0.22), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "stalk.1": ((0, 0, 0), (0, -0.05, 0.55), "root"),
    "stalk.2": ((0, -0.05, 0.55), (0, 0.06, 1.02), "stalk.1"),
    "pod": ((0, 0.06, 1.02), (0, 0.36, 1.12), "stalk.2"),
    "jaw": ((0, 0.3, 1.02), (0, 0.55, 1.0), "pod"),
    "leaf.L": ((-0.08, 0, 0.05), (-0.6, 0.1, 0.25), "root"),
    "leaf.R": ((0.08, 0, 0.05), (0.6, -0.1, 0.22), "root"),
    "leaf.B": ((0, -0.08, 0.05), (0.05, -0.6, 0.3), "root"),
}
POD = Vector((0, 0.2, 1.1))


def build_head():
    col = collection("Thorn")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(8)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, **kw)

    for seg, (a, b, w0, w1) in {"1": ((0, 0, 0), (0, -0.05, 0.57), 0.2, 0.15), "2": ((0, -0.05, 0.55), (0, 0.07, 1.04), 0.15, 0.12)}.items():
        bm = bmesh.new()
        bm_beam(bm, a, b, w0, w0, w1=w1, h1=w1)
        P("Head_Stalk" + seg, bm, "grass", "stalk." + seg, lo=0.2, hi=0.8)
        bm = bmesh.new()
        A, B = Vector(a), Vector(b)
        for k in range(5):
            t = (k + 0.5) / 5
            c = A.lerp(B, t)
            ang = math.radians(72 * k + 30 * int(seg))
            d = Vector((math.cos(ang), math.sin(ang), 0.35)).normalized()
            bm_cyl(bm, 0.03, 0.0, 0.14, tuple(c + d * 0.1), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=4)
        P("Head_StalkThorns" + seg, bm, "cream", "stalk." + seg, lo=0.1, hi=0.4)
    # the pod: a bulb with a red lip at its mouth, teeth, and a crown of thorns
    bm = bmesh.new()
    bm_ellipsoid(bm, POD, (0.3, 0.38, 0.3), (-10, 0, 0))
    P("Head_Pod", bm, "grass", "pod", lo=0.05, hi=0.65)
    bm = bmesh.new()
    ring(bm, tuple(POD + Vector((0, 0.34, 0.04))), 0.2, 0.13, -0.05, 0.05, seg=12, axis="Y")
    P("Head_Lip", bm, "red", "pod", lo=0.2, hi=0.6)
    bm = bmesh.new()
    for k in range(8):
        a = math.radians(45 * k)
        c = POD + Vector((math.cos(a) * 0.15, 0.36, 0.04 + math.sin(a) * 0.15))
        d = (POD + Vector((0, 0.4, 0.04)) - c).normalized()
        bm_cyl(bm, 0.025, 0.0, 0.09, tuple(c + d * 0.04), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=4)
    for k in range(9):
        a = math.radians(40 * k)
        d = Vector((math.cos(a), -0.35, math.sin(a))).normalized()
        c = POD + Vector((d.x * 0.28, d.y * 0.34, d.z * 0.28))
        bm_cyl(bm, 0.04, 0.0, 0.2, tuple(c + d * 0.08), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=4)
    P("Head_Thorns", bm, "cream", "pod", lo=0.05, hi=0.35)
    bm = bmesh.new()
    bm_ellipsoid(bm, POD + Vector((0, 0.28, -0.12)), (0.17, 0.14, 0.06))
    P("Head_Jaw", bm, "red", "jaw", lo=0.3, hi=0.7)
    # big leaves at the base
    for side, (a, b) in {"L": ((-0.08, 0, 0.05), (-0.6, 0.1, 0.25)), "R": ((0.08, 0, 0.05), (0.6, -0.1, 0.22)),
                         "B": ((0, -0.08, 0.05), (0.05, -0.6, 0.3))}.items():
        A, B = Vector(a), Vector(b)
        d = (B - A)
        side_v = d.cross(Vector((0, 0, 1))).normalized()
        bm = bmesh.new()
        pts = [A, A.lerp(B, 0.4) + side_v * 0.17 + Vector((0, 0, 0.06)), B + Vector((0, 0, -0.02)), A.lerp(B, 0.4) - side_v * 0.17 + Vector((0, 0, 0.06))]
        for off in (0.0, -0.01):
            vs = [bm.verts.new(p + Vector((0, 0, off))) for p in pts]
            bm.faces.new(vs if off < 0 else list(reversed(vs)))
        P("Head_Leaf" + side, bm, "grass", "leaf." + side, lo=0.1, hi=0.5)
    empty("Muzzle", col, head, tuple(POD + Vector((0, 0.42, 0.04))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 10


def pose(rig, sway=0.0, nod=0.0, breathe=0.0, jaw=0.0, recoil=0.0, leaves=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["stalk.1"].rotation_quaternion = arm_space_quat(pb["stalk.1"], (0, 1, 0), sway * 0.5) @ arm_space_quat(pb["stalk.1"], (1, 0, 0), -recoil * 6)
    pb["stalk.2"].rotation_quaternion = arm_space_quat(pb["stalk.2"], (0, 1, 0), sway) @ arm_space_quat(pb["stalk.2"], (1, 0, 0), nod - recoil * 10)
    pb["pod"].scale = (1 + breathe, 1 + breathe - recoil * 0.12, 1 + breathe)
    pb["pod"].rotation_quaternion = arm_space_quat(pb["pod"], (1, 0, 0), recoil * 8)
    pb["jaw"].rotation_quaternion = arm_space_quat(pb["jaw"], (1, 0, 0), -jaw)
    for k, s in (("L", 1), ("R", -1), ("B", 1)):
        pb["leaf." + k].rotation_quaternion = arm_space_quat(pb["leaf." + k], (0, 0, 1), s * leaves)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, sway=8 * math.sin(ph), nod=4 * math.sin(ph * 2), breathe=0.04 * math.sin(ph * 2), jaw=6 + 6 * math.sin(ph * 2),
             leaves=6 * math.sin(ph + 1))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        r = smooth(f / 2.0) * (1 - smooth((f - 2) / 7.0))
        j = 35 * smooth(f / 1.5) * (1 - smooth((f - 3) / 6.0)) + 6 * smooth((f - 6) / 4.0)
        pose(rig, recoil=r, jaw=j, breathe=-0.06 * r)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.0), "dist": 5.5, "yaw": 150, "pitch": 22, "anim_target": (0, 0.1, 1.3), "anim_dist": 3.6,
           "frames": [("idle", 0), ("idle", 30), ("fire", 2), ("fire", 5)]}


def build_all():
    build_base()
    build_head()
    build_anims()
