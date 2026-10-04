"""Builds the Ancient Mammoth (footprint "battery5": [0,0] middle, [-1,0] front-left, [0,-1] front, [1,-1] front-right,
[0,1] back), a Verdant creature tower: it stomps, hurting and stunning every ground enemy around it.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mammoth <preview dir>

A woolly mammoth stands over the middle cell, its trunk reaching onto the front one: shaggy brown fur with darker
fringes, a domed head and shoulder hump, great curving tusks banded in gold, and a team-colored saddle blanket. Mossy
boulders, bushes and old bones lie on the cells around it. It's an aura tower, so it doesn't turn. idle: the trunk
swings, the ears flap, it breathes, the tail swishes. fire (every stomp): it rears up trumpeting and crashes down.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "mammoth"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (0, 1)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)
FLc = hex_to_world(-1, 0, MID)
FRc = hex_to_world(1, -1, MID)
BKc = hex_to_world(0, 1, MID)
TOP = 0.34
MS = 1.55


def build_base():
    col = collection("Mammoth")
    root = empty("Mammoth", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(61)
    props = [("forest/Rock_1_A_Color1", FLc, (-0.3, 0.15), 0.45), ("forest/Bush_1_E_Color1", FLc, (0.35, -0.3), 0.32),
             ("forest/Rock_1_H_Color1", FRc, (0.25, 0.15), 0.6), ("forest/Grass_1_A_Color1", FRc, (-0.3, -0.35), 0.6),
             ("forest/Bush_2_B_Color1", BKc, (0.5, -0.2), 0.3), ("halloween/bone_C", BKc, (-0.45, -0.3), 0.55),
             ("halloween/ribcage", FLc, (0.1, -0.55), 0.45)]
    for i, (rel, c, (dx, dy), sc) in enumerate(props):
        kk_import(rel, col, root, (c.x + dx, c.y + dy, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (C0.x, C0.y, T), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, -0.55, 0.95), (0, 0.2, 1.1), "root"),
    "head": ((0, 0.65, 1.4), (0, 0.95, 1.35), "body"),
    "trunk.1": ((0, 1.02, 1.15), (0, 1.12, 0.85), "head"),
    "trunk.2": ((0, 1.12, 0.85), (0, 1.16, 0.55), "trunk.1"),
    "trunk.3": ((0, 1.16, 0.55), (0, 1.26, 0.3), "trunk.2"),
    "ear.L": ((-0.3, 0.7, 1.45), (-0.5, 0.62, 1.3), "head"),
    "ear.R": ((0.3, 0.7, 1.45), (0.5, 0.62, 1.3), "head"),
    "leg.FL": ((-0.3, 0.38, 0.85), (-0.3, 0.4, 0.05), "body"),
    "leg.FR": ((0.3, 0.38, 0.85), (0.3, 0.4, 0.05), "body"),
    "leg.BL": ((-0.32, -0.5, 0.85), (-0.32, -0.5, 0.05), "root"),
    "leg.BR": ((0.32, -0.5, 0.85), (0.32, -0.5, 0.05), "root"),
    "tail": ((0, -0.9, 1.05), (0, -1.0, 0.75), "body"),
}


def build_head():
    col = collection("Mammoth")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=MS)
    rnd = random.Random(4)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, scale=MS, **kw)

    bm = bmesh.new()
    bm_ellipsoid(bm, (0, -0.08, 1.05), (0.52, 0.8, 0.55), u=12, v=8)
    bm_ellipsoid(bm, (0, 0.28, 1.42), (0.4, 0.42, 0.32))                       # shoulder hump
    P("Head_Body", bm, "wood_red", "body", lo=0.15, hi=0.8)
    fringe = bmesh.new()
    for k in range(22):
        a = math.radians(360 * k / 22)
        p = Vector((math.cos(a) * 0.5, -0.08 + math.sin(a) * 0.76, 0.72))
        d = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, -1)).normalized()
        bm_cyl(fringe, 0.1, 0.0, 0.3, tuple(p + d * 0.12), rot=tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler()), seg=5)
    P("Head_Fringe", fringe, "wood_dark", "body", lo=0.3, hi=0.8)
    # saddle blanket with gold trim
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.04, 0.7, 0.42), (sx * 0.52, -0.05, 1.18), (0, sx * -14, 0))
    bm_ellipsoid(bm, (0, -0.05, 1.5), (0.5, 0.4, 0.13), u=12, v=6)     # draped over the back
    P("Head_Blanket", bm, "team", "body", team=True, lo=0.1, hi=0.6)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.05, 0.74, 0.05), (sx * 0.555, -0.05, 0.98), (0, sx * -14, 0))
    P("Head_BlanketTrim", bm, "gold", "body", lo=0.1, hi=0.45)
    # the domed head, eyes, ears
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.82, 1.38), (0.32, 0.3, 0.38))
    bm_ellipsoid(bm, (0, 0.78, 1.66), (0.22, 0.22, 0.2))
    P("Head_Head", bm, "wood_red", "head", lo=0.15, hi=0.75)
    bm = bmesh.new()
    for s in (-1, 1):
        bm_ellipsoid(bm, (s * 0.22, 1.0, 1.42), (0.035, 0.03, 0.035), u=5, v=4)
    P("Head_Eyes", bm, "black", "head", lo=0.3, hi=0.6)
    for s, sx in (("L", -1), ("R", 1)):
        bm = bmesh.new()
        bm_ellipsoid(bm, (sx * 0.4, 0.68, 1.38), (0.04, 0.16, 0.18), (0, 0, sx * 20), u=7, v=5)
        P("Head_Ear" + s, bm, "wood_red", "ear." + s, lo=0.4, hi=0.8)
    # tusks: three tapering segments sweeping forward, out and up, banded in gold near the root
    tusk, band = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        pts = [Vector((sx * 0.17, 1.02, 1.08)), Vector((sx * 0.3, 1.25, 0.82)), Vector((sx * 0.36, 1.55, 0.9)), Vector((sx * 0.24, 1.72, 1.2))]
        ws = [0.11, 0.09, 0.065, 0.025]
        for i in range(3):
            bm_beam(tusk, pts[i], pts[i + 1], ws[i], ws[i], w1=ws[i + 1], h1=ws[i + 1])
        ring(band, tuple(pts[0].lerp(pts[1], 0.35)), 0.075, 0.05, -0.03, 0.03, seg=8, axis="Z")
    P("Head_Tusks", tusk, "cream", "head", lo=0.05, hi=0.3)
    P("Head_TuskBands", band, "gold", "head", lo=0.1, hi=0.4)
    # trunk
    for k, (w0, w1) in enumerate(((0.16, 0.13), (0.13, 0.1), (0.1, 0.07)), start=1):
        h, t, _ = BONES["trunk.%d" % k]
        bm = bmesh.new()
        bm_beam(bm, h, t, w0, w0, w1=w1, h1=w1)
        P("Head_Trunk%d" % k, bm, "wood_red", "trunk.%d" % k, lo=0.3, hi=0.75)
    # legs with toenails, tail with a tuft
    for leg, bone in (("FL", "leg.FL"), ("FR", "leg.FR"), ("BL", "leg.BL"), ("BR", "leg.BR")):
        h, t, _ = BONES[bone]
        bm = bmesh.new()
        bm_beam(bm, h, t, 0.3, 0.3, w1=0.26, h1=0.26)
        P("Head_Leg" + leg, bm, "wood_red", bone, lo=0.35, hi=0.9)
        bm = bmesh.new()
        for k in range(3):
            bm_ellipsoid(bm, (t[0] + (k - 1) * 0.08, t[1] + 0.13, 0.05), (0.04, 0.03, 0.035), u=5, v=4)
        P("Head_Nails" + leg, bm, "cream", bone, lo=0.1, hi=0.3)
    bm = bmesh.new()
    bm_beam(bm, (0, -0.85, 1.08), (0, -1.0, 0.75), 0.05, 0.05)
    bm_ellipsoid(bm, (0, -1.02, 0.7), (0.06, 0.06, 0.1), u=6, v=4)
    P("Head_Tail", bm, "wood_dark", "tail", lo=0.3, hi=0.7)
    empty("Muzzle", col, head, (0, 1.3 * MS, 0.4 * MS), 0.2, "SPHERE")
    return rig


IDLE_LEN = 90
FIRE_LEN = 30


def pose(rig, rear=0.0, curl=0.0, swing=0.0, ears=0.0, breathe=0.0, tail=0.0, nod=0.0, raise_=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["body"].rotation_quaternion = arm_space_quat(pb["body"], (1, 0, 0), rear * 24)
    pb["body"].scale = (1 + breathe, 1 + breathe, 1 + breathe)
    pb["head"].rotation_quaternion = arm_space_quat(pb["head"], (1, 0, 0), nod + raise_ * 12)
    for k, f in ((1, 0.6), (2, 1.0), (3, 1.4)):
        b = pb["trunk.%d" % k]
        b.rotation_quaternion = arm_space_quat(b, (1, 0, 0), (curl + raise_ * 55) * f * 0.6) @ arm_space_quat(b, (0, 1, 0), swing * f)
    for s, sx in (("L", -1), ("R", 1)):
        pb["ear." + s].rotation_quaternion = arm_space_quat(pb["ear." + s], (0, 0, 1), -sx * ears)
        pb["leg.F" + s].rotation_quaternion = arm_space_quat(pb["leg.F" + s], (1, 0, 0), rear * 35)
    pb["tail"].rotation_quaternion = arm_space_quat(pb["tail"], (0, 1, 0), tail)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, curl=10 * math.sin(ph), swing=8 * math.sin(ph * 2 + 0.5), ears=12 * max(0.0, math.sin(ph * 3)) ** 3,
             breathe=0.015 * math.sin(ph * 2), tail=20 * math.sin(ph * 3), nod=3 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 9.0) * (1 - smooth((f - 11) / 3.0)) - 0.15 * smooth((f - 13) / 2.0) * (1 - smooth((f - 16) / 8.0))
        up = smooth((f - 2) / 6.0) * (1 - smooth((f - 12) / 8.0))
        pose(rig, rear=rear, raise_=up, ears=25 * up, tail=25 * up, nod=-4 * rear)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 11.0, "yaw": 145, "pitch": 18, "anim_target": (C0.x, C0.y + 0.5, 1.5), "anim_dist": 7.0,
           "frames": [("idle", 0), ("fire", 9), ("fire", 14)]}


def build_all():
    build_base()
    build_head()
    build_anims()
