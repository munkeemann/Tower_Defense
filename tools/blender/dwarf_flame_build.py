"""Builds the Flame Belcher (footprint "pair": [0,0] front, [0,1] back; a 90 degree cone), a Forge tower.

    blender -b --factory-startup --python tools/blender/build_tower.py -- dwarf_flame <preview dir>

Back cell: a riveted iron boiler on a brick firebox (glowing grate), a smoking chimney, a pressure gauge and a stack
of kegs, where a dwarf engineer works the valve (Crew). Front cell: pipes feed a squat nozzle housing whose spout is
a snarling iron face with a glowing throat. It's an aura (it doesn't turn): fire bursts in its cone. idle: the chimney smokes, the gauge
needle twitches, the boiler hums. fire (every burst): the spout jolts back, its throat flares, the chimney puffs.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dwarf_flame"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
EMBER = (1.0, 0.42, 0.08)


def build_base():
    col = collection("Dwarf_flame")
    root = empty("Dwarf_flame", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(2)
    B = BACK
    # firebox, boiler, rivets, chimney
    bm = bmesh.new()
    bm_box(bm, (0.95, 0.9, 0.42), (B.x, B.y - 0.05, T + 0.21))
    o = paint(mesh_obj("Firebox", bm, col, root), "wood_red", lo=0.2, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_box(bm, (0.42, 0.04, 0.16), (B.x, B.y + 0.41, T + 0.2))
    glow_obj("Firebox_Grate", bm, col, root, EMBER, 1.2)
    bm = bmesh.new()
    bm_cyl(bm, 0.4, 0.4, 0.95, (B.x, B.y - 0.05, T + 0.82), rot=(90, 0, 0), seg=12)
    bm_cyl(bm, 0.3, 0.0, 0.18, (B.x, B.y - 0.6, T + 0.82), rot=(90, 0, 0), seg=12)
    o = paint(mesh_obj("Boiler", bm, col, root), "iron", lo=0.05, hi=0.6)
    bm = bmesh.new()
    for y in (-0.42, -0.05, 0.32):
        ring(bm, (B.x, B.y + y, T + 0.82), 0.43, 0.39, -0.035, 0.035, seg=12, axis="Y")
    paint(mesh_obj("Boiler_Bands", bm, col, root), "gold", lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_cyl(bm, 0.11, 0.13, 0.9, (B.x - 0.2, B.y - 0.35, T + 1.55), seg=8)
    bm_cyl(bm, 0.17, 0.12, 0.12, (B.x - 0.2, B.y - 0.35, T + 2.02), seg=8)
    paint(mesh_obj("Chimney", bm, col, root), "stone_dark", lo=0.1, hi=0.6)
    # gauge on a little post, pipes forward to the nozzle housing
    bm = bmesh.new()
    bm_cyl(bm, 0.12, 0.12, 0.04, (B.x + 0.26, B.y + 0.12, T + 1.3), rot=(90, 0, 0), seg=10)
    bm_cyl(bm, 0.03, 0.03, 0.15, (B.x + 0.26, B.y + 0.12, T + 1.2), seg=6)
    for sx in (-1, 1):
        bm_beam(bm, Vector((B.x + sx * 0.18, B.y + 0.35, T + 0.75)), Vector((FRONT.x + sx * 0.18, FRONT.y - 0.55, T + 0.6)), 0.09, 0.09)
    paint(mesh_obj("Pipes", bm, col, root), "gold", lo=0.15, hi=0.55)
    for i, (rel, loc, sc) in enumerate((("dungeon/barrel_small_stack", (B.x + 0.6, B.y + 0.5, T), 0.4),
                                        ("resources/Parts_Pile_Small", (B.x - 0.6, B.y + 0.5, T), 0.55),
                                        ("resources/Iron_Bars_Stack_Small", (FRONT.x + 0.65, FRONT.y - 0.55, T), 0.5))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, (B.x + 0.6, B.y - 0.1, T), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(90))      # faces the boiler's side (-X)
    # the nozzle housing on the front cell
    F = FRONT
    bm = bmesh.new()
    bm_box(bm, (0.85, 0.75, 0.55), (F.x, F.y - 0.2, T + 0.27))
    bm_box(bm, (0.95, 0.85, 0.08), (F.x, F.y - 0.2, T + 0.58))
    o = paint(mesh_obj("Housing", bm, col, root), "iron", lo=0.05, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.025; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_ellipsoid(bm, (F.x + sx * 0.38, F.y - 0.2 + sy * 0.33, T + 0.45), (0.04, 0.04, 0.04), u=5, v=4)
    paint(mesh_obj("Housing_Rivets", bm, col, root), "gold", lo=0.1, hi=0.4)
    empty("Head", col, root, (F.x, F.y - 0.1, T + 0.62), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "spout": ((0, -0.1, 0.25), (0, 0.4, 0.25), "root"),
         "throat": ((0, 0.62, 0.25), (0, 0.75, 0.25), "spout"),
         "smoke": ((0, 0, 0), (0, 0, 0.3), "root"),
         "needle": ((0, 0, 0), (0, 0, 0.1), "root")}
SMOKE_AT = None
NEEDLE_AT = None


def build_head():
    global SMOKE_AT, NEEDLE_AT
    col = collection("Dwarf_flame")
    head = bpy.data.objects["Head"]
    hp = head.location
    SMOKE_AT = Vector((BACK.x - 0.2, BACK.y - 0.35, TOP + 2.15)) - hp
    NEEDLE_AT = Vector((BACK.x + 0.26, BACK.y + 0.1, TOP + 1.3)) - hp
    BONES["smoke"] = (tuple(SMOKE_AT), tuple(SMOKE_AT + Vector((0, 0, 0.3))), "root")
    BONES["needle"] = (tuple(NEEDLE_AT), tuple(NEEDLE_AT + Vector((0, 0, 0.1))), "root")
    rig = make_rig(col, head, BONES)
    # the spout: a snarling iron face (brow, cheeks, jaw) around a glowing throat
    bm = bmesh.new()
    bm_cyl(bm, 0.24, 0.3, 0.6, (0, 0.2, 0.25), rot=(-90, 0, 0), seg=8)
    bm_box(bm, (0.62, 0.12, 0.14), (0, 0.48, 0.5), (12, 0, 0))
    for sx in (-1, 1):
        bm_cyl(bm, 0.05, 0.0, 0.2, (sx * 0.26, 0.42, 0.62), rot=(-30, sx * 25, 0), seg=4)
    bm_box(bm, (0.5, 0.14, 0.1), (0, 0.5, 0.02), (-10, 0, 0))
    rig_part("Head_Spout", bm, "iron", rig, "spout", col, bevel=0, lo=0.05, hi=0.55)
    bm = bmesh.new()
    ring(bm, (0, 0.52, 0.25), 0.27, 0.2, -0.04, 0.04, seg=10, axis="Y")
    rig_part("Head_SpoutRim", bm, "gold", rig, "spout", col, bevel=0, lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_cyl(bm, 0.19, 0.19, 0.06, (0, 0.53, 0.25), rot=(-90, 0, 0), seg=10)
    rig_part("Head_Throat", bm, None, rig, "throat", col, bevel=0, mat=glow_mat("forge_ember", EMBER, 1.2))
    bm = bmesh.new()
    rnd = random.Random(5)
    for k in range(4):
        bm_ellipsoid(bm, SMOKE_AT + Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.12 + k * 0.18)), (0.16 + k * 0.04,) * 2 + (0.12 + k * 0.03,), u=7, v=5)
    rig_part("Head_Smoke", bm, "stone2", rig, "smoke", col, bevel=0, lo=0.05, hi=0.4)
    bm = bmesh.new()
    bm_beam(bm, NEEDLE_AT + Vector((0, 0.025, 0)), NEEDLE_AT + Vector((0.07, 0.025, 0.07)), 0.015, 0.01)
    rig_part("Head_Needle", bm, "red", rig, "needle", col, bevel=0, lo=0.3, hi=0.6)
    empty("Muzzle", col, head, (0, 0.62, 0.25), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 10


def pose(rig, recoil=0.0, flare=1.0, smoke=1.0, rise=0.0, needle=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["spout"].location = arm_space_loc(pb["spout"], (0, -recoil * 0.12, 0))
    pb["spout"].rotation_quaternion = arm_space_quat(pb["spout"], (1, 0, 0), recoil * 6)
    pb["throat"].scale = (flare, flare, flare)
    pb["smoke"].scale = (smoke, smoke, smoke)
    pb["smoke"].location = arm_space_loc(pb["smoke"], (0, 0, rise))
    pb["needle"].rotation_quaternion = arm_space_quat(pb["needle"], (0, 1, 0), needle)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, smoke=0.8 + 0.25 * math.sin(2 * math.pi * t), rise=0.12 * t, needle=20 + 8 * math.sin(2 * math.pi * t * 3),
             flare=1.0 + 0.08 * math.sin(2 * math.pi * t * 2))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        r = smooth(f / 1.5) * (1 - smooth((f - 2) / 7.0))
        pose(rig, recoil=r, flare=1.0 + 0.7 * r, smoke=1.0 + 0.6 * r, rise=0.05 * r, needle=60 * r + 20)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 7.0, "yaw": 150, "pitch": 22, "anim_target": (FRONT.x, FRONT.y, 0.9), "anim_dist": 4.0,
           "frames": [("idle", 0), ("fire", 2), ("fire", 6)]}


def build_all():
    build_base()
    build_head()
    build_anims()
