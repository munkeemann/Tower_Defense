"""Builds the Moonwell (footprint "single"), a Verdant support tower (nearby towers attack faster).

    blender -b --factory-startup --python tools/blender/build_tower.py -- moonwell <preview dir>

An elven well of pale stone with a team-colored rune band, full of glowing moon-water, under a silver crescent on two
slender posts; motes of light drift round it, and a druid tends it (Crew). idle (its only clip): the water swells and
settles, the motes circle and bob, the crescent turns a little.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "moonwell"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34
MOON = (0.25, 0.55, 0.95)
W = Vector((0.08, 0.1, 0))       # the well's middle


def build_base():
    col = collection("Moonwell")
    root = empty("Moonwell", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True, stone="stone_warm")
    rnd = random.Random(3)
    bm = bmesh.new()
    ring(bm, (W.x, W.y, 0), 0.62, 0.46, T, T + 0.36, seg=16)
    o = paint(mesh_obj("Well_Wall", bm, col, root), "white", lo=0.2, hi=0.75)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (W.x, W.y, 0), 0.67, 0.43, T + 0.36, T + 0.43, seg=16)
    o = paint(mesh_obj("Well_Rim", bm, col, root), "white", lo=0.05, hi=0.3)
    bm = bmesh.new()
    ring(bm, (W.x, W.y, 0), 0.625, 0.6, T + 0.16, T + 0.24, seg=16)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        p = W + Vector((math.cos(a) * 0.625, math.sin(a) * 0.625, 0))
        bm_box(bm, (0.07, 0.04, 0.07), (p.x, p.y, T + 0.2), (0, 0, 45 * k + 22.5 + 90))
    paint(mesh_obj("Well_Runes", bm, col, root), "team", team=True, lo=0.1, hi=0.5)
    # crescent arch: two posts, a crossbar, and the silver crescent riding on it
    bm = bmesh.new()
    for sx in (-1, 1):
        p = W + Vector((sx * 0.66, -0.12, 0))
        bm_cyl(bm, 0.05, 0.04, 1.55, (p.x, p.y, T + 0.78), seg=6)
        bm_cyl(bm, 0.07, 0.0, 0.16, (p.x, p.y, T + 1.62), seg=6)
    bm_beam(bm, W + Vector((-0.66, -0.12, T + 1.38)), W + Vector((0.66, -0.12, T + 1.38)), 0.06, 0.06)
    paint(mesh_obj("Arch_Posts", bm, col, root), "stone", lo=0.05, hi=0.4)
    # bushes, a flowering shrub, stones
    for i, (rel, ang, r, sc) in enumerate((("forest/Bush_1_E_Color1", 230, 0.78, 0.3), ("forest/Bush_2_C_Color1", 320, 0.75, 0.28),
                                           ("forest/Rock_1_E_Color1", 140, 0.82, 0.3))):
        a = math.radians(ang)
        kk_import(rel, col, root, (math.cos(a) * r, math.sin(a) * r, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, (-0.55, 0.55, T), 0.3, "SINGLE_ARROW")
    to = Vector((W.x, W.y, 0)) - Vector((-0.55, 0.55, 0))
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))
    empty("Head", col, root, (W.x, W.y, T), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "water": ((0, 0, 0.3), (0, 0.2, 0.3), "root"),
    "moon": ((0, -0.12, 1.62), (0, -0.12, 1.82), "root"),
    "motes": ((0, 0, 0.7), (0, 0, 0.9), "root"),
}


def build_head():
    col = collection("Moonwell")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    bm_cyl(bm, 0.45, 0.45, 0.05, (0, 0, 0.3), seg=16)
    rig_part("Head_Water", bm, None, rig, "water", col, bevel=0, mat=glow_mat("moon_water", MOON, 0.7))
    # the crescent: an arc of a thick ring, standing upright
    bm = bmesh.new()
    c = Vector((0, -0.12, 1.75))
    n = 10
    for i in range(n):
        # a crescent opening to one side: thick in the middle of the arc, horns thinning to points
        a0 = math.radians(40 + 280 * i / n)
        a1 = math.radians(40 + 280 * (i + 1) / n)
        w0 = 0.015 + 0.1 * math.sin(math.pi * i / n)
        w1 = 0.015 + 0.1 * math.sin(math.pi * (i + 1) / n)
        p0 = c + Vector((math.cos(a0) * 0.28, 0, math.sin(a0) * 0.28))
        p1 = c + Vector((math.cos(a1) * 0.28, 0, math.sin(a1) * 0.28))
        bm_beam(bm, p0, p1, 0.06, w0, w1=0.06, h1=w1, up=tuple((p0 - c).normalized()))
    rig_part("Head_Moon", bm, None, rig, "moon", col, bevel=0, mat=glow_mat("moon_silver", (0.7, 0.8, 0.95), 0.45))
    bm = bmesh.new()
    rnd = random.Random(12)
    for k in range(6):
        a = math.radians(60 * k + rnd.uniform(-10, 10))
        r = rnd.uniform(0.5, 0.75)
        bm_ellipsoid(bm, (math.cos(a) * r, math.sin(a) * r, 0.7 + rnd.uniform(-0.15, 0.35)), (0.045, 0.045, 0.045), u=6, v=4)
    rig_part("Head_Motes", bm, None, rig, "motes", col, bevel=0, mat=glow_mat("moon_water", MOON, 0.7))
    empty("Muzzle", col, head, (0, 0, 0.6), 0.2, "SPHERE")
    return rig


IDLE_LEN = 90


def build_anims():
    rig = bpy.data.objects["Rig"]
    pb = rig.pose.bones
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        rest_pose(rig)
        sw = 1.0 + 0.05 * math.sin(ph * 2)
        pb["water"].scale = (sw, sw, 1.0)
        pb["water"].location = arm_space_loc(pb["water"], (0, 0, 0.02 * math.sin(ph * 2)))
        pb["moon"].rotation_quaternion = arm_space_quat(pb["moon"], (0, 0, 1), 12 * math.sin(ph))
        pb["motes"].rotation_quaternion = arm_space_quat(pb["motes"], (0, 0, 1), 360 * f / IDLE_LEN)
        pb["motes"].location = arm_space_loc(pb["motes"], (0, 0, 0.06 * math.sin(ph * 3)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 5.5, "yaw": 150, "pitch": 24, "anim_target": (0, 0, 1.0), "anim_dist": 4.2,
           "frames": [("idle", 0), ("idle", 30), ("idle", 60)]}


def build_all():
    build_base()
    build_head()
    build_anims()
