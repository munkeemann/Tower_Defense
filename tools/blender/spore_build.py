"""Builds the Spore Mound (footprint "pair": [0,0] front, [0,1] back), a Verdant tower that lobs poison spores.

    blender -b --factory-startup --python tools/blender/build_tower.py -- spore <preview dir>

Front cell: a giant spotted puffball on a thick stalk, small toadstools and drifting spores round it (the Head; pods
leave from its crown). Back cell: a grove of tall mushrooms on a mossy mound, where a druid throws (Crew).
idle: the puffball breathes, spores drift and circle. fire: it squashes and bursts a purple spore cloud.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "spore"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
SPORE = (0.72, 0.4, 0.95)


def _toadstool(bms, c, h, r, rnd, tilt=0.0):
    """A mushroom: a cream stalk and a red cap with cream spots into bms = (stalk, cap, spots)."""
    c = Vector(c)
    lean = Vector((math.cos(tilt), math.sin(tilt), 0)) * h * 0.12
    bm_beam(bms[0], c, c + lean + Vector((0, 0, h)), r * 0.38, r * 0.38, w1=r * 0.3, h1=r * 0.3)
    cap = c + lean + Vector((0, 0, h))
    bm_ellipsoid(bms[1], cap, (r, r, r * 0.55), u=12, v=6)
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        e = rnd.uniform(0.25, 0.7)
        d = Vector((math.cos(a) * e, math.sin(a) * e, math.sqrt(max(0.0, 1 - e * e)) * 0.55)).normalized()
        p = cap + Vector((d.x * r, d.y * r, d.z * r * 0.55 / 0.55 * 0.55 / max(d.z, 0.3) * d.z))
        p = cap + Vector((math.cos(a) * e * r, math.sin(a) * e * r, math.sqrt(max(0.0, 1 - e * e)) * r * 0.55))
        bm_ellipsoid(bms[2], p, (r * 0.14, r * 0.14, r * 0.05), u=6, v=4)


def build_base():
    col = collection("Spore")
    root = empty("Spore", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(6)
    B = BACK
    bm = bmesh.new()
    bm_ellipsoid(bm, (B.x, B.y, T), (0.82, 0.8, 0.22))
    paint_ground(mesh_obj("Grove_Mound", bm, col, root))     # a rise in the ground: the map's colours
    bms = (bmesh.new(), bmesh.new(), bmesh.new())
    for (dx, dy, h, r) in ((0.42, -0.35, 1.35, 0.32), (-0.45, -0.28, 1.0, 0.27), (0.5, 0.35, 0.7, 0.22), (-0.15, -0.6, 0.55, 0.18)):
        _toadstool(bms, (B.x + dx, B.y + dy, T + 0.1), h, r, rnd, rnd.uniform(0, 6.28))
    for (dx, dy, h, r) in ((0.7, 0.35, 0.3, 0.14), (-0.75, 0.2, 0.26, 0.12), (0.6, -0.55, 0.22, 0.1)):
        _toadstool(bms, (FRONT.x + dx, FRONT.y + dy, T), h, r, rnd, rnd.uniform(0, 6.28))
    paint(mesh_obj("Shroom_Stalks", bms[0], col, root), "cream", lo=0.2, hi=0.7)
    paint(mesh_obj("Shroom_Caps", bms[1], col, root), "red", lo=0.05, hi=0.45)
    paint(mesh_obj("Shroom_Spots", bms[2], col, root), "white", lo=0.05, hi=0.25)
    for i, (rel, loc, sc) in enumerate((("forest/Bush_1_C_Color1", (BACK.x - 0.7, BACK.y + 0.45, T - 0.02), 0.3),
                                        ("forest/Rock_1_B_Color1", (FRONT.x - 0.65, FRONT.y - 0.5, T - 0.02), 0.28))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, (B.x - 0.05, B.y + 0.5, T + 0.12), 0.3, "SINGLE_ARROW")   # faces the front
    empty("Head", col, root, (FRONT.x, FRONT.y, T), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "cap": ((0, 0, 0.55), (0, 0, 0.95), "root"),
    "puff": ((0, 0, 1.25), (0, 0, 1.5), "root"),
    "drift": ((0, 0, 0.8), (0, 0, 1.0), "root"),
}


def build_head():
    col = collection("Spore")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(14)
    bm = bmesh.new()
    bm_beam(bm, (0, 0, 0), (0, 0, 0.62), 0.34, 0.34, w1=0.28, h1=0.28)
    bm_ellipsoid(bm, (0, 0, 0.08), (0.28, 0.28, 0.1))
    rig_part("Head_Stalk", bm, "cream", rig, "root", col, bevel=0, lo=0.2, hi=0.7)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0, 0.88), (0.62, 0.62, 0.48), u=14, v=8)
    rig_part("Head_Cap", bm, "red", rig, "cap", col, bevel=0, lo=0.05, hi=0.5)
    bm = bmesh.new()
    for k in range(11):
        a = rnd.uniform(0, 6.28)
        e = rnd.uniform(0.15, 0.85)
        p = Vector((math.cos(a) * e * 0.62, math.sin(a) * e * 0.62, 0.88 + math.sqrt(max(0.0, 1 - e * e)) * 0.48))
        bm_ellipsoid(bm, p, (0.08, 0.08, 0.035), u=6, v=4)
    rig_part("Head_Spots", bm, "white", rig, "cap", col, bevel=0, lo=0.05, hi=0.25)
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.58, 0.3, 0.6, 0.66, seg=14)
    rig_part("Head_Gills", bm, "cream", rig, "cap", col, bevel=0, lo=0.5, hi=0.8)
    spore = glow_mat("spore_glow", SPORE, 1.0)
    bm = bmesh.new()
    for k in range(9):
        a = math.radians(40 * k + rnd.uniform(-10, 10))
        r = rnd.uniform(0.1, 0.35)
        bm_ellipsoid(bm, (math.cos(a) * r, math.sin(a) * r, 1.25 + rnd.uniform(-0.05, 0.2)), (0.2, 0.2, 0.17), u=8, v=5)
    rig_part("Head_Puff", bm, None, rig, "puff", col, bevel=0, mat=spore)
    bm = bmesh.new()
    for k in range(8):
        a = math.radians(45 * k + rnd.uniform(-12, 12))
        r = rnd.uniform(0.7, 0.95)
        bm_ellipsoid(bm, (math.cos(a) * r, math.sin(a) * r, 0.55 + rnd.uniform(-0.2, 0.6)), (0.04, 0.04, 0.04), u=5, v=4)
    rig_part("Head_Drift", bm, None, rig, "drift", col, bevel=0, mat=spore)
    empty("Muzzle", col, head, (0, 0, 1.38), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 16


def pose(rig, breathe=0.0, squash=0.0, puff=0.0, drift=0.0, rise=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["cap"].scale = (1 + breathe + squash * 0.18, 1 + breathe - squash * 0.3, 1 + breathe + squash * 0.18)   # (Y up)
    pb["puff"].scale = (max(puff, 0.001),) * 3
    pb["puff"].location = arm_space_loc(pb["puff"], (0, 0, rise))
    pb["drift"].rotation_quaternion = arm_space_quat(pb["drift"], (0, 0, 1), drift)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, breathe=0.035 * math.sin(ph * 2), drift=360 * f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        sq = smooth(f / 3.0) * (1 - smooth((f - 3) / 3.0)) - 0.5 * smooth((f - 3) / 2.0) * (1 - smooth((f - 6) / 6.0))
        pf = 0.0 if f < 3 else (1.3 * smooth((f - 3) / 4.0) * (1 - smooth((f - 9) / 6.0)))
        pose(rig, squash=sq, puff=pf, rise=0.3 * smooth((f - 3) / 10.0), drift=120 * smooth(f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 7.0, "yaw": 150, "pitch": 24, "anim_target": (0, FRONT.y, 1.1), "anim_dist": 4.0,
           "frames": [("idle", 0), ("fire", 3), ("fire", 7), ("fire", 12)]}


def build_all():
    build_base()
    build_head()
    build_anims()
