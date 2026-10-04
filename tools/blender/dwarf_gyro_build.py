"""Builds the Flak Battery (footprint "wing3": [0,0] back, [1,-1] front-right, [-1,0] front-left; a 180 degree arc,
two guns), a Forge tower: twin rotary flak guns that shred flyers.

    blender -b --factory-startup --python tools/blender/build_tower.py -- dwarf_gyro <preview dir>

A turntable carries a yoke with two rotary guns side by side, each a ring of six barrels round an axle in a brass drum,
raised for the sky (the Head: it turns to aim; Muzzle1 / Muzzle2 are the two guns). Ammo boxes with belts and an iron
blast shield stand on the front cells; a gearbox engine with a smoking stack sits at the back. idle: the barrels idle
round, the guns nod. fire: the barrels whirl, the guns judder.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dwarf_gyro"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FRc = hex_to_world(1, -1, MID)
FLc = hex_to_world(-1, 0, MID)
TOP = 0.34
ELEV = 35.0
GUN_X = 0.42
GUN_Z = 0.95


def build_base():
    col = collection("Dwarf_gyro")
    root = empty("Dwarf_gyro", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, stone="stone_dark", course="iron")
    rnd = random.Random(15)
    bm = bmesh.new()
    bm_cyl(bm, 0.95, 1.0, 0.14, (0, 0, T + 0.07), seg=16)
    paint(mesh_obj("Platform", bm, col, root), "stone", lo=0.1, hi=0.55)
    # blast shields and ammo boxes on the front cells
    for c, side in ((FLc, -1), (FRc, 1)):
        bm = bmesh.new()
        d = Vector((c.x, c.y, 0)).normalized()
        n = Vector((-d.y, d.x, 0))
        p = Vector((c.x, c.y, 0)) + d * 0.35
        yaw = math.degrees(math.atan2(n.y, n.x))
        bm_box(bm, (1.0, 0.1, 0.6), (p.x, p.y, T + 0.3), (0, 0, yaw))
        o = paint(mesh_obj("Shield_%d" % side, bm, col, root), "iron", lo=0.05, hi=0.6)
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
        bm = bmesh.new()
        for k in range(2):
            q = Vector((c.x, c.y, 0)) - d * 0.15 + n * (k - 0.5) * 0.45
            bm_box(bm, (0.3, 0.42, 0.26), (q.x, q.y, T + 0.13), (0, 0, yaw))
        paint(mesh_obj("Ammo_%d" % side, bm, col, root), "wood_dark", lo=0.3, hi=0.8)
        bm = bmesh.new()
        for k in range(2):
            q = Vector((c.x, c.y, 0)) - d * 0.15 + n * (k - 0.5) * 0.45
            bm_box(bm, (0.33, 0.12, 0.04), (q.x, q.y, T + 0.27), (0, 0, yaw))
        paint(mesh_obj("Ammo_Band_%d" % side, bm, col, root), "team", team=True, lo=0.1, hi=0.5)
    # the engine at the back: a gearbox block and a smoke stack
    bm = bmesh.new()
    e = BK + Vector((0, -0.55, 0))
    bm_box(bm, (0.9, 0.42, 0.45), (e.x, e.y, T + 0.22))
    bm_cyl(bm, 0.09, 0.11, 0.9, (e.x + 0.3, e.y - 0.05, T + 0.8), seg=8)
    paint(mesh_obj("Engine", bm, col, root), "iron", lo=0.05, hi=0.55)
    for i, (rel, loc, sc) in enumerate((("resources/Parts_Cog", (e.x - 0.25, e.y, T + 0.45), 0.6),
                                        ("resources/Fuel_B_Barrel", (BK.x - 0.65, BK.y + 0.05, T), 0.55))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (0, 0, T + 0.14), 0.5, "SINGLE_ARROW")
    return root


AX = Vector((0, math.cos(math.radians(ELEV)), math.sin(math.radians(ELEV))))
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "yoke": ((0, 0, GUN_Z), (0, 0.3, GUN_Z), "root")}
for _s, _sx in (("L", -1), ("R", 1)):
    _c = Vector((_sx * GUN_X, 0, GUN_Z))
    BONES["spin." + _s] = (tuple(_c), tuple(_c + AX * 0.5), "yoke")


def _gun(bm_dark, bm_brass, c):
    rot = tuple(math.degrees(x) for x in AX.to_track_quat("Z", "Y").to_euler())
    bm_cyl(bm_brass, 0.2, 0.2, 0.42, tuple(c - AX * 0.05), rot=rot, seg=10)
    bm_cyl(bm_dark, 0.05, 0.05, 1.05, tuple(c + AX * 0.5), rot=rot, seg=6)
    side = AX.cross(Vector((1, 0, 0))).normalized()
    up = AX.cross(side).normalized()
    for k in range(6):
        a = math.radians(60 * k)
        off = side * math.cos(a) * 0.12 + up * math.sin(a) * 0.12
        bm_cyl(bm_dark, 0.04, 0.04, 0.95, tuple(c + AX * 0.55 + off), rot=rot, seg=6)
    for t in (0.4, 0.95):
        q = Vector((0, 0, 1)).rotation_difference(AX)
        tmp = bmesh.new()
        ring(tmp, (0, 0, 0), 0.19, 0.15, -0.03, 0.03, seg=10)
        bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=q.to_matrix())
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=c + AX * t)
        me = bpy.data.meshes.new("_t"); tmp.to_mesh(me); tmp.free(); bm_brass.from_mesh(me); bpy.data.meshes.remove(me)


def build_head():
    col = collection("Dwarf_gyro")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    bm_cyl(bm, 0.78, 0.78, 0.12, (0, 0, 0.06), seg=16)
    bm_box(bm, (0.5, 0.5, 0.55), (0, -0.1, 0.4))
    rig_part("Head_Base", bm, "iron", rig, "root", col, bevel=0, lo=0.05, hi=0.6)
    bm = bmesh.new()
    bm_box(bm, (1.05, 0.22, 0.18), (0, 0, GUN_Z))
    for sx in (-1, 1):
        bm_box(bm, (0.08, 0.3, 0.4), (sx * 0.62, 0, GUN_Z))
    rig_part("Head_Yoke", bm, "iron", rig, "yoke", col, bevel=0, lo=0.1, hi=0.55)
    bm = bmesh.new()
    bm_box(bm, (0.2, 0.06, 0.3), (0, -0.15, GUN_Z + 0.1))
    rig_part("Head_Sight", bm, "gold", rig, "yoke", col, bevel=0, lo=0.1, hi=0.5)
    for s, sx in (("L", -1), ("R", 1)):
        dark, brass = bmesh.new(), bmesh.new()
        _gun(dark, brass, Vector((sx * GUN_X, 0, GUN_Z)))
        rig_part("Head_Barrels" + s, dark, "black", rig, "spin." + s, col, bevel=0, lo=0.3, hi=0.7)
        rig_part("Head_Drum" + s, brass, "gold", rig, "spin." + s, col, bevel=0, lo=0.1, hi=0.5)
        empty("Muzzle%d" % (1 if s == "L" else 2), col, head, tuple(Vector((sx * GUN_X, 0, GUN_Z)) + AX * 1.05), 0.15, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 8


def pose(rig, spin=0.0, nod=0.0, judder=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["yoke"].rotation_quaternion = arm_space_quat(pb["yoke"], (1, 0, 0), nod)
    pb["yoke"].location = arm_space_loc(pb["yoke"], (0, -judder * 0.05, 0))
    for s in ("L", "R"):
        pb["spin." + s].rotation_quaternion = arm_space_quat(pb["spin." + s], tuple(AX), spin)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, spin=120 * t, nod=3 * math.sin(2 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        pose(rig, spin=480 * f / FIRE_LEN, judder=math.sin(f * 2.4) * (1 - f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 8.5, "yaw": 150, "pitch": 22, "anim_target": (0, 0.2, 1.3), "anim_dist": 4.5,
           "frames": [("idle", 0), ("fire", 3)]}


def build_all():
    build_base()
    build_head()
    build_anims()
