"""Builds the Soul Obelisk (footprint "pair": [0,0] front, [0,1] back), a Grave tower: it rips out a share of a
target's current health with every hit.

    blender -b --factory-startup --python tools/blender/build_tower.py -- soul_obelisk <preview dir>

Front cell: a tall black obelisk on a stepped base, purple runes glowing down its faces; above its tip a violet soul
crystal floats, circled by three wisps (the Head: it turns to its target; soul-bolts leave from the crystal). Back cell:
a little graveyard: graves, headstones, a fence, a lantern and a dead tree. idle: the crystal turns and bobs, the wisps
circle. fire: the crystal flares and the wisps are pulled in to it.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "soul_obelisk"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
T = TOP
TIP = T + 2.15


def build_base():
    col = collection("Soul_obelisk")
    root = empty("Soul_obelisk", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    bm = bmesh.new()
    bm_box(bm, (1.15, 1.15, 0.16), (F.x, F.y, T + 0.08))
    bm_box(bm, (0.85, 0.85, 0.16), (F.x, F.y, T + 0.24))
    o = paint(mesh_obj("Obelisk_Steps", bm, col, root), "stone2", lo=0.2, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.36, 0.22, 1.45, (F.x, F.y, T + 0.32 + 0.725), rot=(0, 0, 45), seg=4)
    bm_cyl(bm, 0.22, 0.0, 0.32, (F.x, F.y, T + 1.77 + 0.16), rot=(0, 0, 45), seg=4)
    paint(mesh_obj("Obelisk", bm, col, root), "stone_dark", lo=0.05, hi=0.6)
    bm = bmesh.new()
    for k in range(4):                                          # rune glyphs down each face
        a = math.radians(90 * k)
        n = Vector((math.cos(a), math.sin(a), 0))
        for j in range(3):
            z = T + 0.55 + j * 0.38
            w = 0.29 - 0.05 * j
            p = Vector((F.x, F.y, z)) + n * (w * 0.5 + 0.035)
            bm_box(bm, (0.13, 0.02, 0.15) if k % 2 == 0 else (0.02, 0.13, 0.15), tuple(p))
    glow_obj("Obelisk_Runes", bm, col, root, SOUL, 0.9)
    for i, (rel, loc, rot, sc) in enumerate((("halloween/grave_A", (B.x - 0.4, B.y + 0.2, T), 0, 0.26),
                                              ("halloween/grave_B", (B.x + 0.45, B.y + 0.1, T), 10, 0.26),
                                              ("halloween/gravestone", (B.x + 0.05, B.y - 0.45, T), 185, 0.28),
                                              ("halloween/gravemarker_A", (B.x - 0.65, B.y - 0.4, T), 160, 0.3),
                                              ("halloween/fence", (B.x, B.y - 0.88, T), 0, 0.3),
                                              ("halloween/lantern_standing", (B.x + 0.72, B.y - 0.42, T), 0, 0.45),
                                              ("halloween/tree_dead_large", (F.x + 0.72, F.y + 0.05, T), 220, 0.3),
                                              ("halloween/candle_triple", (F.x - 0.68, F.y + 0.4, T), 30, 0.4))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (F.x, F.y, TIP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.05, 0.25), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "crystal": ((0, 0, 0.25), (0, 0, 0.55), "root"),
         "wisps": ((0, 0, 0.25), (0, 0, 0.45), "root")}
WISPS = [(0.42, 0.0, 0.3), (-0.21, 0.36, 0.15), (-0.21, -0.36, 0.42)]


def build_head():
    col = collection("Soul_obelisk")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0, 0.27), (0.16, 0.16, 0.27), u=4, v=2)
    rig_part("Head_Crystal", bm, None, rig, "crystal", col, bevel=0, mat=glow_mat("soul_crystal", SOUL, 1.1))
    bm = bmesh.new()
    for (x, y, z) in WISPS:
        bm_ellipsoid(bm, (x, y, z), (0.07, 0.07, 0.08), u=7, v=4)
        bm_cyl(bm, 0.05, 0.0, 0.16, (x, y, z + 0.1), seg=6)
    rig_part("Head_Wisps", bm, None, rig, "wisps", col, bevel=0, mat=glow_mat("soul_wisp", (0.85, 0.7, 1.0), 0.9))
    return rig


IDLE_LEN = 72
FIRE_LEN = 18


def pose(rig, t=0.0, flare=1.0, pull=0.0, spin=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["crystal"].rotation_quaternion = arm_space_quat(pb["crystal"], (0, 0, 1), 360 * t)
    pb["crystal"].location = arm_space_loc(pb["crystal"], (0, 0, 0.06 * math.sin(2 * math.pi * t * 2)))
    pb["crystal"].scale = (flare, flare, flare)
    pb["wisps"].rotation_quaternion = arm_space_quat(pb["wisps"], (0, 0, 1), -360 * t - spin)
    k = 1.0 - 0.75 * pull
    pb["wisps"].scale = (k, k, k)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, flare=1.0 + 0.08 * math.sin(2 * math.pi * t * 3))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        k = smooth(f / 2.5) * (1 - smooth((f - 5) / 11.0))
        pose(rig, t=0.1 * f / FIRE_LEN, flare=1.0 + 0.9 * k, pull=k, spin=240 * smooth(f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 7.5, "yaw": 160, "pitch": 18, "anim_target": (F.x, F.y, 2.2), "anim_dist": 3.5,
           "frames": [("idle", 0), ("idle", 30), ("fire", 4), ("fire", 12)]}


def build_all():
    build_base()
    build_head()
    build_anims()
