"""Builds the Stormcaller Oak (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Verdant tower:
chain lightning.

    blender -b --factory-startup --python tools/blender/build_tower.py -- storm <preview dir>

A great oak on the front cell (thick trunk, roots, a crown of leaf clumps) within a ring of rune stones; above its crown
a storm crystal floats between two small thunderclouds (the Head: lightning leaves the crystal). Back cells: standing
stones with glowing runes, a druid calling the storm (Crew). idle: the crystal turns, the clouds circle, the leaves
stir. fire: the crystal flares, the clouds whirl and the crown shakes.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "storm"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
STORM = (0.3, 0.55, 1.0)
CROWN_Z = 2.35


def build_base():
    col = collection("Storm")
    root = empty("Storm", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(31)
    F = FRONT
    # trunk, flaring roots, two big limbs
    bm = bmesh.new()
    bm_beam(bm, (F.x, F.y, T - 0.02), (F.x + 0.04, F.y, T + 1.25), 0.56, 0.56, w1=0.4, h1=0.4)
    bm_beam(bm, (F.x + 0.04, F.y, T + 1.2), (F.x - 0.05, F.y + 0.03, T + 1.9), 0.4, 0.4, w1=0.3, h1=0.3)
    bm_beam(bm, (F.x, F.y, T + 1.4), (F.x + 0.6, F.y - 0.1, T + 2.1), 0.22, 0.22, w1=0.12, h1=0.12)
    bm_beam(bm, (F.x, F.y, T + 1.5), (F.x - 0.55, F.y + 0.15, T + 2.15), 0.2, 0.2, w1=0.11, h1=0.11)
    for k in range(6):
        a = math.radians(60 * k + rnd.uniform(-12, 12))
        bm_beam(bm, (F.x + math.cos(a) * 0.15, F.y + math.sin(a) * 0.15, T + 0.32),
                (F.x + math.cos(a) * 0.75, F.y + math.sin(a) * 0.75, T - 0.02), 0.2, 0.14, w1=0.06, h1=0.05)
    o = paint(mesh_obj("Oak_Trunk", bm, col, root), "wood_dark", lo=0.2, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    # crown: overlapping leaf clumps in two greens
    lo_b, hi_b = bmesh.new(), bmesh.new()
    clumps = [(0, 0, CROWN_Z, 0.85), (0.55, -0.15, CROWN_Z - 0.2, 0.6), (-0.55, 0.15, CROWN_Z - 0.15, 0.62),
              (0.2, 0.5, CROWN_Z - 0.1, 0.55), (-0.2, -0.5, CROWN_Z - 0.05, 0.55), (0.05, 0.05, CROWN_Z + 0.45, 0.55)]
    for i, (dx, dy, z, r) in enumerate(clumps):
        bm_ellipsoid(lo_b if i % 2 == 0 else hi_b, (F.x + dx, F.y + dy, T + z), (r, r, r * 0.78), (0, 0, rnd.uniform(0, 90)), u=8, v=6)
    paint(mesh_obj("Oak_Leaves", lo_b, col, root), "grass", lo=0.1, hi=0.85)
    paint(mesh_obj("Oak_Leaves2", hi_b, col, root), "teal", lo=0.3, hi=0.8)
    # rune stones: a ring around the oak and standing stones on the back cells
    stone_b, rune_b = bmesh.new(), bmesh.new()
    spots = [(F + Vector((math.cos(math.radians(a)) * 0.85, math.sin(math.radians(a)) * 0.85, 0)), 0.55) for a in (200, 250, 290, 340)]
    spots += [(BR + Vector((0.1, 0.05, 0)), 1.0), (BL + Vector((-0.1, 0.05, 0)), 1.0), (BR + Vector((-0.45, -0.35, 0)), 0.6),
              (BL + Vector((0.45, -0.35, 0)), 0.6)]
    for (p, h) in spots:
        to = (Vector((F.x, F.y, 0)) - Vector((p.x, p.y, 0))).normalized()
        yaw = math.degrees(math.atan2(to.y, to.x)) + 90
        bm_box(stone_b, (0.32, 0.2, h), (p.x, p.y, T + h / 2 - 0.02), (rnd.uniform(-4, 4), rnd.uniform(-4, 4), yaw))
        for k in range(2 if h > 0.7 else 1):
            q = Vector((p.x, p.y, T + h * (0.45 + 0.3 * k))) + to * 0.105
            bm_box(rune_b, (0.12, 0.012, 0.12), tuple(q), (0, 45, yaw))
    o = paint(mesh_obj("Rune_Stones", stone_b, col, root), "stone2", lo=0.1, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    glow_obj("Rune_Glyphs", rune_b, col, root, STORM, 1.0)
    for i, (rel, loc, sc) in enumerate((("forest/Bush_1_C_Color1", (BR.x + 0.55, BR.y + 0.4, T - 0.02), 0.3),
                                        ("forest/Rock_1_D_Color1", (BL.x - 0.5, BL.y + 0.4, T - 0.02), 0.3),
                                        ("forest/Grass_1_A_Color1", (BL.x + 0.55, BL.y + 0.45, T - 0.02), 0.6))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, (BR.x - 0.35, BR.y + 0.25, T), 0.3, "SINGLE_ARROW")
    to = Vector((F.x, F.y, 0)) - Vector((crew.location.x, crew.location.y, 0))
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))
    empty("Head", col, root, (F.x, F.y, T + CROWN_Z + 1.25), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "crystal": ((0, 0, 0), (0, 0, 0.3), "root"),
    "clouds": ((0, 0, -0.1), (0, 0, 0.1), "root"),
}


def build_head():
    col = collection("Storm")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(17)
    bm = bmesh.new()
    top = bm.verts.new((0, 0, 0.42))
    bot = bm.verts.new((0, 0, -0.38))
    mid = [bm.verts.new((math.cos(math.radians(60 * i)) * 0.2, math.sin(math.radians(60 * i)) * 0.2, 0.04)) for i in range(6)]
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new((mid[i], mid[j], top))
        bm.faces.new((mid[j], mid[i], bot))
    rig_part("Head_Crystal", bm, None, rig, "crystal", col, bevel=0, mat=glow_mat("storm_glow", STORM, 0.75))
    cloud = bmesh.new()
    for s in (-1, 1):
        c = Vector((s * 0.75, 0.1 * s, -0.15))
        for k in range(5):
            bm_ellipsoid(cloud, c + Vector((rnd.uniform(-0.22, 0.22), rnd.uniform(-0.12, 0.12), rnd.uniform(-0.05, 0.1))),
                         (rnd.uniform(0.16, 0.24),) * 2 + (rnd.uniform(0.12, 0.16),), u=7, v=5)
    rig_part("Head_Clouds", cloud, "stone2", rig, "clouds", col, bevel=0, lo=0.3, hi=0.9)
    bolt = bmesh.new()
    for s in (-1, 1):
        c = Vector((s * 0.75, 0.1 * s, -0.3))
        pts = [c, c + Vector((0.05, 0, -0.18)), c + Vector((-0.06, 0, -0.32)), c + Vector((0.03, 0, -0.5))]
        for i in range(3):
            bm_beam(bolt, pts[i], pts[i + 1], 0.04, 0.04, w1=0.03, h1=0.03)
    rig_part("Head_Bolts", bolt, None, rig, "clouds", col, bevel=0, mat=glow_mat("storm_glow", STORM, 0.75))
    empty("Muzzle", col, head, (0, 0, 0), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 16


def pose(rig, spin=0.0, bob=0.0, swirl=0.0, flare=1.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["crystal"].rotation_quaternion = arm_space_quat(pb["crystal"], (0, 0, 1), spin)
    pb["crystal"].location = arm_space_loc(pb["crystal"], (0, 0, bob))
    pb["crystal"].scale = (flare,) * 3
    pb["clouds"].rotation_quaternion = arm_space_quat(pb["clouds"], (0, 0, 1), swirl)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, spin=360 * t, bob=0.08 * math.sin(2 * math.pi * t), swirl=-360 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = f / FIRE_LEN
        pose(rig, spin=360 * smooth(t), swirl=-360 * smooth(t), flare=1.0 + 0.6 * (smooth(f / 2.0) - smooth((f - 2) / 10.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.6), "dist": 10.0, "yaw": 150, "pitch": 20, "anim_target": (0, FRONT.y, 3.8), "anim_dist": 4.0,
           "frames": [("idle", 0), ("fire", 2), ("fire", 8)]}


def build_all():
    build_base()
    build_head()
    build_anims()
