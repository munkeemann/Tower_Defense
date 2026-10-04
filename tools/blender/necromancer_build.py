"""Builds the Necromancer (footprint "star5": [0,0] middle, with [1,-1], [-1,0], [1,0], [-1,1] at its four corners), the
Grave's tier-3 tower: dark bolts, and walkers that die in its reach rise as zombies.

    blender -b --factory-startup --python tools/blender/build_tower.py -- necromancer <preview dir>

On a round, stepped ritual dais in the middle, a skeleton mage (Crew, on the Head: he turns to his target; bolts leave
his staff) stands in a ring of glowing green runes, three green-eyed skulls circling above him. Each corner holds an open
grave with a headstone; two burn with braziers of green soul-fire, two with skull posts. idle: the runes turn, the
skulls circle and bob, the flames flicker. fire: the runes flare, the skulls whirl, the flames leap.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "necromancer"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C = hex_to_world(0, 0, MID)
CORNERS = [hex_to_world(q, s, MID) for q, s in [(1, -1), (-1, 0), (1, 0), (-1, 1)]]
TOP = 0.34
T = TOP
DAIS = T + 0.3
BRAZIERS = (0, 3)              # corner cells with braziers (the others get skull posts)


def build_base():
    col = collection("Necromancer")
    root = empty("Necromancer", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(41)
    bm = bmesh.new()
    bm_cyl(bm, 1.0, 1.05, 0.15, (C.x, C.y, T + 0.075), seg=16)
    bm_cyl(bm, 0.8, 0.84, 0.15, (C.x, C.y, T + 0.225), seg=16)
    o = paint(mesh_obj("Dais", bm, col, root), "stone_dark", lo=0.1, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    earth, dark = bmesh.new(), bmesh.new()
    props = []
    for i, c in enumerate(CORNERS):
        out = Vector((c.x - C.x, c.y - C.y, 0)).normalized()
        yaw = math.degrees(math.atan2(out.y, out.x)) - 90
        bm_grave_hole(earth, dark, (c.x + out.x * 0.15, c.y + out.y * 0.15, T), w=0.55, l=0.85, yaw=yaw, rnd=rnd)
        stone = c + out * 0.68
        props.append(("halloween/" + ("gravestone" if i % 2 else "grave_B"), (stone.x, stone.y, T), yaw + 180, 0.26))
        side = Vector((-out.y, out.x, 0))
        if i not in BRAZIERS:
            p = c - out * 0.25 + side * 0.5
            props.append(("halloween/post_skull", (p.x, p.y, T), yaw, 0.3))
    paint(mesh_obj("Graves_Earth", earth, col, root), EARTH_SW, lo=0.2, hi=0.75)
    paint(mesh_obj("Graves_Dark", dark, col, root), "black", lo=0.3, hi=0.6)
    for i, (rel, loc, rot, sc) in enumerate(props):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    bm = bmesh.new()                                            # brazier bowls on stems
    for i in BRAZIERS:
        c = CORNERS[i]
        out = Vector((c.x - C.x, c.y - C.y, 0)).normalized()
        side = Vector((-out.y, out.x, 0))
        p = c - out * 0.25 + side * 0.5
        bm_cyl(bm, 0.08, 0.12, 0.55, (p.x, p.y, T + 0.275), seg=8)
        bm_cyl(bm, 0.24, 0.16, 0.16, (p.x, p.y, T + 0.62), seg=10)
    paint(mesh_obj("Braziers", bm, col, root), "iron", lo=0.1, hi=0.6)
    head = empty("Head", col, root, (C.x, C.y, DAIS), 0.5, "SINGLE_ARROW")
    empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0.3, 0.35, 1.35), 0.2, "SPHERE")
    return root


def brazier_at(i):
    c = CORNERS[i]
    out = Vector((c.x - C.x, c.y - C.y, 0)).normalized()
    side = Vector((-out.y, out.x, 0))
    return c - out * 0.25 + side * 0.5 + Vector((0, 0, T + 0.68))


def build_head():
    col = collection("Necromancer")
    root = bpy.data.objects["Necromancer"]
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "runes": ((C.x, C.y, DAIS + 0.01), (C.x, C.y, DAIS + 0.21), "root"),
             "skulls": ((C.x, C.y, DAIS + 1.75), (C.x, C.y, DAIS + 1.95), "root")}
    for i in BRAZIERS:
        p = brazier_at(i)
        bones["flame.%d" % i] = (tuple(p), tuple(p + Vector((0, 0, 0.3))), "root")
    rig = make_rig(col, root, bones)
    gm = glow_mat("necro_green", NECRO, 0.9)
    bm = bmesh.new()
    ring(bm, (C.x, C.y, 0), 0.74, 0.67, DAIS + 0.005, DAIS + 0.025, seg=28)
    ring(bm, (C.x, C.y, 0), 0.5, 0.46, DAIS + 0.005, DAIS + 0.025, seg=24)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        p = Vector((C.x + math.cos(a) * 0.585, C.y + math.sin(a) * 0.585, DAIS + 0.015))
        bm_box(bm, (0.1, 0.05, 0.02), tuple(p), (0, 0, 45 * k + 22.5))
        bm_box(bm, (0.05, 0.1, 0.02), tuple(p), (0, 0, 45 * k + 22.5))
    rig_part("Runes", bm, None, rig, "runes", col, bevel=0, mat=gm)
    sk, skd, eyes = bmesh.new(), bmesh.new(), bmesh.new()
    for k in range(3):
        a = math.radians(120 * k)
        c = Vector((C.x + math.cos(a) * 0.7, C.y + math.sin(a) * 0.7, DAIS + 1.75 + 0.12 * (k - 1)))
        yaw = math.degrees(a) - 90 + 90                   # each faces along its circling path
        for e in bm_skull(sk, skd, c, s=0.24, yaw=yaw):
            bm_ellipsoid(eyes, tuple(e), (0.022, 0.022, 0.022), u=5, v=3)
    rig_part("Skulls", sk, BONE_SW, rig, "skulls", col, bevel=0, lo=0.05, hi=0.45)
    rig_part("Skulls_Dark", skd, "black", rig, "skulls", col, bevel=0, lo=0.3, hi=0.6)
    rig_part("Skulls_Eyes", eyes, None, rig, "skulls", col, bevel=0, mat=gm)
    for i in BRAZIERS:
        bm = bmesh.new()
        bm_flame(bm, brazier_at(i) - Vector((0, 0, 0.05)), h=0.45, r=0.14, rnd=random.Random(i))
        rig_part("Flame%d" % i, bm, None, rig, "flame.%d" % i, col, bevel=0, mat=glow_mat("necro_flame", NECRO, 1.1))
    return rig


IDLE_LEN = 96
FIRE_LEN = 20


def pose(rig, t=0.0, flare=1.0, whirl=0.0, leap=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["runes"].rotation_quaternion = arm_space_quat(pb["runes"], (0, 0, 1), -180 * t)
    pb["runes"].scale = (flare, 1.0, flare)                 # (upright bones: their own Y is the height)
    pb["skulls"].rotation_quaternion = arm_space_quat(pb["skulls"], (0, 0, 1), 360 * t + whirl)
    pb["skulls"].location = arm_space_loc(pb["skulls"], (0, 0, 0.08 * math.sin(2 * math.pi * t * 2)))
    for i in BRAZIERS:
        k = 1.0 + 0.12 * math.sin(2 * math.pi * t * 7 + i) + leap
        pb["flame.%d" % i].scale = (1.0 + 0.3 * leap, k, 1.0 + 0.3 * leap)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        k = smooth(f / 3.0) * (1 - smooth((f - 6) / 12.0))
        pose(rig, t=0.08 * f / FIRE_LEN, flare=1.0 + 0.25 * k, whirl=300 * smooth(f / FIRE_LEN), leap=0.8 * k)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 10.5, "yaw": 160, "pitch": 24, "anim_target": (0, 0, 1.4), "anim_dist": 6.0,
           "frames": [("idle", 0), ("fire", 5)]}


def build_all():
    build_base()
    build_head()
    build_anims()
