"""Builds the Plague Cauldron (footprint "pair": [0,0] front, [0,1] back), a Grave tower: it hurls bubbling plague that
poisons whole groups.

    blender -b --factory-startup --python tools/blender/build_tower.py -- plague_cauldron <preview dir>

Front cell: a great iron cauldron on three legs over a fire pit of logs and glowing embers, its green brew bubbling and
fuming (the Head: plague leaves from the brew). A skeleton mage (Crew) tends it from beside. Back cell: a potion station,
plague kegs, a coffin, bones and a dead tree. idle: bubbles swell and pop, fumes curl up, the embers flicker. fire: a
glob of brew heaves up out of the pot and the fumes billow.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "plague_cauldron"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
T = TOP
POT = Vector((F.x, F.y + 0.05, T))
BREW_Z = 0.86              # the brew's surface, above the plinth
PLAGUE = (0.5, 0.92, 0.28)
EMBER = (1.0, 0.45, 0.1)


def build_base():
    col = collection("Plague_cauldron")
    root = empty("Plague_cauldron", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(21)
    # the fire pit: a ring of stones, crossed logs, embers
    bm = bmesh.new()
    for k in range(11):
        a = math.radians(360 * k / 11 + rnd.uniform(-8, 8))
        r = rnd.uniform(0.1, 0.14)
        bm_ellipsoid(bm, (POT.x + math.cos(a) * 0.68, POT.y + math.sin(a) * 0.62, T + r * 0.5), (r * 1.2, r, r * 0.8), rot=(0, 0, math.degrees(a)), u=6, v=4)
    paint(mesh_obj("Pit_Stones", bm, col, root), "stone2", lo=0.15, hi=0.6)
    bm = bmesh.new()
    for k in range(4):
        a = math.radians(45 * k + 20)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_beam(bm, POT - d * 0.5 + Vector((0, 0, 0.07 + 0.03 * (k % 2))), POT + d * 0.5 + Vector((0, 0, 0.07 + 0.03 * (k % 2))), 0.1, 0.1)
    paint(mesh_obj("Pit_Logs", bm, col, root), "wood_dark", lo=0.3, hi=0.8)
    bm = bmesh.new()
    bm_cyl(bm, 0.45, 0.38, 0.05, (POT.x, POT.y, T + 0.03), seg=10)
    glow_obj("Pit_Embers", bm, col, root, EMBER, 1.0)
    # the cauldron: a bulging iron pot, a heavy rim, three legs, two ring handles
    bm = bmesh.new()
    bm_ellipsoid(bm, (POT.x, POT.y, T + 0.55), (0.56, 0.56, 0.42), u=14, v=8)
    bm_cyl(bm, 0.5, 0.5, 0.18, (POT.x, POT.y, T + 0.8), seg=14)
    for k in range(3):
        a = math.radians(120 * k + 30)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_beam(bm, POT + d * 0.32 + Vector((0, 0, 0.3)), POT + d * 0.48 + Vector((0, 0, 0.0)), 0.09, 0.09, w1=0.07, h1=0.07)
    paint(mesh_obj("Cauldron", bm, col, root), "iron", lo=0.1, hi=0.65)
    bm = bmesh.new()
    ring(bm, (POT.x, POT.y, 0), 0.6, 0.47, T + BREW_Z - 0.03, T + BREW_Z + 0.05, seg=14)
    for sx in (-1, 1):
        ring(bm, (POT.x + sx * 0.62, POT.y, T + 0.62), 0.1, 0.07, -0.025, 0.025, seg=8, axis="X")
    paint(mesh_obj("Cauldron_Rim", bm, col, root), "stone_dark", lo=0.1, hi=0.5)
    # the back cell: a potion station, plague kegs, a coffin, bones, a dead tree
    for i, (rel, loc, rot, sc) in enumerate((("props/Potionstation_decorated", (B.x - 0.35, B.y - 0.05, T), 180, 0.55),
                                              ("dungeon/barrel_small_stack", (B.x + 0.55, B.y + 0.3, T), 60, 0.33),
                                              ("halloween/coffin", (B.x + 0.45, B.y - 0.5, T), 75, 0.24),
                                              ("halloween/tree_dead_medium", (B.x - 0.65, B.y - 0.55, T), 30, 0.32),
                                              ("halloween/bone_B", (F.x + 0.75, F.y - 0.55, T + 0.02), 20, 0.35),
                                              ("halloween/skull_candle", (F.x - 0.78, F.y + 0.3, T), 120, 0.26))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, (POT.x - 0.82, POT.y - 0.42, T), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(-55))           # faces the pot
    head = empty("Head", col, root, (POT.x, POT.y, T + BREW_Z), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.3), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "brew": ((0, 0, 0), (0, 0, 0.2), "root"),
         "glob": ((0, 0, 0.0), (0, 0, 0.3), "root"),
         "fumes": ((0, 0, 0.15), (0, 0, 0.45), "root"),
         "embers": ((0, 0, -BREW_Z), (0, 0, -BREW_Z + 0.2), "root")}
BUB = [(0.2, 0.1), (-0.18, 0.15), (0.05, -0.22), (-0.25, -0.12), (0.26, -0.1)]
for _i, (_x, _y) in enumerate(BUB):
    BONES["bub.%d" % _i] = ((_x, _y, 0.0), (_x, _y, 0.15), "brew")


def build_head():
    col = collection("Plague_cauldron")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    pmat = glow_mat("plague_brew", PLAGUE, 0.7)
    bm = bmesh.new()
    bm_cyl(bm, 0.49, 0.49, 0.04, (0, 0, -0.01), seg=14)
    rig_part("Head_Brew", bm, None, rig, "brew", col, bevel=0, mat=pmat)
    for i, (x, y) in enumerate(BUB):
        bm = bmesh.new()
        bm_ellipsoid(bm, (x, y, 0.03), (0.09, 0.09, 0.07), u=7, v=4)
        rig_part("Head_Bubble%d" % i, bm, None, rig, "bub.%d" % i, col, bevel=0, mat=pmat)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0, 0.25), (0.3, 0.3, 0.32), u=9, v=6)
    for k in range(5):
        a = math.radians(72 * k)
        bm_ellipsoid(bm, (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.12), (0.12, 0.12, 0.12), u=6, v=4)
    rig_part("Head_Glob", bm, None, rig, "glob", col, bevel=0, mat=pmat)
    bm = bmesh.new()
    rnd = random.Random(4)
    for k in range(4):
        bm_ellipsoid(bm, (rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.25 + 0.2 * k), (0.16 + 0.04 * k,) * 2 + (0.12 + 0.03 * k,), u=7, v=5)
    rig_part("Head_Fumes", bm, None, rig, "fumes", col, bevel=0, mat=glow_mat("plague_fumes", (0.42, 0.7, 0.3), 0.3))
    return rig


IDLE_LEN = 64
FIRE_LEN = 24


def pose(rig, t=0.0, glob=0.0, rise=0.0, fumes=1.0, bob=0.0, embers=1.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["brew"].location = arm_space_loc(pb["brew"], (0, 0, bob))
    for i in range(len(BUB)):
        ph = (t * 2 + i * 0.37) % 1.0                    # each bubble swells, then pops
        s = 0.001 if ph > 0.85 else 0.3 + ph
        pb["bub.%d" % i].scale = (s, s, s)
    g = max(glob, 0.001)
    pb["glob"].scale = (g, g, g)
    pb["glob"].location = arm_space_loc(pb["glob"], (0, 0, rise))
    pb["fumes"].scale = (fumes, fumes, fumes)
    pb["fumes"].location = arm_space_loc(pb["fumes"], (0, 0, 0.15 * (fumes - 1.0) + 0.06 * math.sin(2 * math.pi * t)))
    pb["embers"].scale = (embers, embers, embers)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, bob=0.02 * math.sin(4 * math.pi * t), fumes=0.85 + 0.15 * math.sin(2 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        up = smooth(f / 3.0)
        gone = smooth((f - 5) / 3.0)
        pose(rig, t=f / FIRE_LEN, glob=up * (1 - gone), rise=0.5 * up, fumes=1.0 + 0.6 * smooth(f / 4.0) * (1 - smooth((f - 8) / 14.0)),
             bob=0.05 * up * (1 - gone))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 7.0, "yaw": 160, "pitch": 22, "anim_target": (F.x, F.y, 1.1), "anim_dist": 4.0,
           "frames": [("idle", 0), ("idle", 20), ("fire", 3), ("fire", 8)]}


def build_all():
    build_base()
    build_head()
    build_anims()
