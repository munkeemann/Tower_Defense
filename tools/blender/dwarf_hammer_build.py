"""Builds the Runic Hammer (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Forge tower: a
rune-powered steam hammer that crushes groups next to it.

    blender -b --factory-startup --python tools/blender/build_tower.py -- dwarf_hammer <preview dir>

Front cell: an iron gantry (two braced legs and a top beam with a piston cylinder) over an anvil plate; the hammer head
is a huge rune-carved block banded in gold, its runes glowing. Back-left: a vertical boiler with a steam pipe up to the
gantry. Back-right: big gears and a crate of ingots. The machine doesn't turn (the game's Head is a bare marker; the rig
hangs off the root). idle: the hammer hangs ready and breathes, the gears turn, steam wisps. fire: it slams down onto
the anvil, steam bursts, the gears spin, and it winches back up.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dwarf_hammer"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
EMBER = (1.0, 0.42, 0.08)
BEAM_Z = 2.55
UP_Z = 1.55          # hammer face height at rest (ready)


def build_base():
    col = collection("Dwarf_hammer")
    root = empty("Dwarf_hammer", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, stone="stone_dark", course="iron")
    rnd = random.Random(8)
    bm = bmesh.new()
    for sx in (-1, 1):
        x = F.x + sx * 0.72
        bm_beam(bm, (x, F.y - 0.35, T), (x, F.y, BEAM_Z), 0.16, 0.16, up=(0, 1, 0))
        bm_beam(bm, (x, F.y + 0.35, T), (x, F.y, BEAM_Z), 0.16, 0.16, up=(0, 1, 0))
        bm_beam(bm, (x, F.y - 0.22, T + 0.9), (x, F.y + 0.22, T + 0.9), 0.1, 0.1)
    bm_box(bm, (1.7, 0.3, 0.26), (F.x, F.y, BEAM_Z + 0.08))
    o = paint(mesh_obj("Gantry", bm, col, root), "iron", lo=0.05, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.2, 0.2, 0.55, (F.x, F.y, BEAM_Z - 0.3), seg=10)
    for sx in (-1, 1):
        bm_box(bm, (0.2, 0.34, 0.3), (F.x + sx * 0.82, F.y, BEAM_Z + 0.06))
    paint(mesh_obj("Gantry_Brass", bm, col, root), "gold", lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_box(bm, (0.95, 0.75, 0.22), (F.x, F.y, T + 0.11))
    bm_box(bm, (0.7, 0.55, 0.12), (F.x, F.y, T + 0.28))
    o = paint(mesh_obj("Anvil", bm, col, root), "stone_dark", lo=0.1, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    # back-left: boiler and steam pipe
    bm = bmesh.new()
    bc = BL + Vector((0.25, 0.1, 0))
    bm_cyl(bm, 0.38, 0.38, 1.3, (bc.x, bc.y, T + 0.65), seg=12)
    bm_ellipsoid(bm, (bc.x, bc.y, T + 1.3), (0.38, 0.38, 0.2), u=12, v=5)
    paint(mesh_obj("Boiler", bm, col, root), "iron", lo=0.05, hi=0.6)
    bm = bmesh.new()
    for z in (0.3, 0.75, 1.2):
        ring(bm, (bc.x, bc.y, 0), 0.41, 0.37, T + z - 0.035, T + z + 0.035, seg=12)
    bm_beam(bm, (bc.x, bc.y, T + 1.45), (bc.x + 0.3, bc.y + 0.2, T + 2.1), 0.1, 0.1)
    bm_beam(bm, (bc.x + 0.3, bc.y + 0.2, T + 2.1), (F.x - 0.75, F.y, BEAM_Z), 0.1, 0.1)
    paint(mesh_obj("Boiler_Brass", bm, col, root), "gold", lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_box(bm, (0.3, 0.04, 0.16), (bc.x, bc.y + 0.39, T + 0.25))
    glow_obj("Boiler_Fire", bm, col, root, EMBER, 1.2)
    for i, (rel, loc, sc) in enumerate((("resources/Gold_Bars_Stack_Small", (BR.x + 0.45, BR.y - 0.35, T), 0.5),
                                        ("resources/Iron_Bars_Stack_Medium", (BR.x - 0.5, BR.y - 0.4, T), 0.5),
                                        ("resources/Fuel_A_Barrel", (BL.x - 0.45, BL.y - 0.45, T), 0.55))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (F.x, F.y, T + UP_Z), 0.5, "SINGLE_ARROW")
    return root


GEAR_C = None


def build_head():
    col = collection("Dwarf_hammer")
    root = bpy.data.objects["Dwarf_hammer"]
    head = bpy.data.objects["Head"]
    T = TOP
    gear_c = BR + Vector((0.15, 0.3, 0))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "hammer": ((F.x, F.y, T + UP_Z), (F.x, F.y, T + UP_Z + 0.4), "root"),
             "gear.1": ((gear_c.x, gear_c.y - 0.05, T + 0.75), (gear_c.x, gear_c.y + 0.15, T + 0.75), "root"),
             "gear.2": ((gear_c.x + 0.45, gear_c.y - 0.05, T + 0.45), (gear_c.x + 0.45, gear_c.y + 0.15, T + 0.45), "root"),
             "steam": ((F.x, F.y, T + 0.4), (F.x, F.y, T + 0.7), "root")}
    rig = make_rig(col, root, bones)
    # the hammer head: rod, block, gold bands, glowing rune faces
    bm = bmesh.new()
    bm_cyl(bm, 0.08, 0.08, BEAM_Z - 0.55 - UP_Z, (F.x, F.y, T + UP_Z + (BEAM_Z - 0.55 - UP_Z) / 2 + 0.45), seg=8)
    bm_box(bm, (0.78, 0.58, 0.5), (F.x, F.y, T + UP_Z + 0.25))
    o = rig_part("Head_Hammer", bm, "stone_dark", rig, "hammer", col, bevel=0.015, lo=0.05, hi=0.55)
    bm = bmesh.new()
    for z in (0.06, 0.44):
        bm_box(bm, (0.84, 0.64, 0.07), (F.x, F.y, T + UP_Z + z))
    rig_part("Head_HammerBands", bm, "gold", rig, "hammer", col, bevel=0, lo=0.1, hi=0.5)
    bm = bmesh.new()
    for sy in (-1, 1):
        for k in range(2):
            bm_box(bm, (0.14, 0.012, 0.18), (F.x - 0.18 + k * 0.36, F.y + sy * 0.295, T + UP_Z + 0.25), (0, 0, 0))
    for sx in (-1, 1):
        bm_box(bm, (0.012, 0.2, 0.18), (F.x + sx * 0.395, F.y, T + UP_Z + 0.25))
    rig_part("Head_HammerRunes", bm, None, rig, "hammer", col, bevel=0, mat=glow_mat("forge_ember", EMBER, 1.2))
    for g, (r, teeth, w) in {"gear.1": (0.42, 10, 0.12), "gear.2": (0.26, 8, 0.1)}.items():
        h = Vector(bones[g][0])
        bm = bmesh.new()
        ring(bm, tuple(h), r, r * 0.35, -w / 2, w / 2, seg=16, axis="Y")
        for k in range(teeth):
            a = math.radians(360 * k / teeth)
            p = h + Vector((math.cos(a) * r, 0, math.sin(a) * r))
            bm_box(bm, (0.1, w, 0.1), tuple(p), (0, -math.degrees(a), 0))
        for k in range(3):
            a = math.radians(120 * k)
            bm_beam(bm, h, h + Vector((math.cos(a) * r * 0.9, 0, math.sin(a) * r * 0.9)), 0.06, w * 0.8, up=(0, 1, 0))
        rig_part("Head_" + g.replace(".", ""), bm, "gold" if g == "gear.1" else "iron", rig, g, col, bevel=0, lo=0.1, hi=0.55)
    bm = bmesh.new()
    rnd = random.Random(9)
    for k in range(7):
        a = math.radians(360 * k / 7)
        bm_ellipsoid(bm, (F.x + math.cos(a) * 0.5, F.y + math.sin(a) * 0.45, T + 0.45 + rnd.uniform(0, 0.2)), (0.22, 0.22, 0.17), u=7, v=5)
    rig_part("Head_Steam", bm, "white", rig, "steam", col, bevel=0, lo=0.05, hi=0.3)
    empty("Muzzle", col, head, (0, 0, -UP_Z + 0.4), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 30
DROP = UP_Z - 0.62      # how far it falls to meet the anvil


def pose(rig, down=0.0, gears=0.0, steam=0.0, breathe=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["hammer"].location = arm_space_loc(pb["hammer"], (0, 0, -down * DROP + breathe))
    pb["gear.1"].rotation_quaternion = arm_space_quat(pb["gear.1"], (0, 1, 0), gears)
    pb["gear.2"].rotation_quaternion = arm_space_quat(pb["gear.2"], (0, 1, 0), -gears * 1.6)
    pb["steam"].scale = (max(steam, 0.001),) * 3
    pb["steam"].location = arm_space_loc(pb["steam"], (0, 0, steam * 0.25))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, gears=90 * t, breathe=0.03 * math.sin(2 * math.pi * t), steam=0.0)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        down = smooth(f / 3.0) if f <= 3 else (1.0 if f <= 9 else 1.0 - smooth((f - 9) / 20.0))
        steam = 0.0 if f < 3 else 1.4 * smooth((f - 3) / 4.0) * (1 - smooth((f - 9) / 10.0))
        pose(rig, down=down, gears=360 * smooth(f / FIRE_LEN), steam=steam)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.3), "dist": 9.5, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y, 1.4), "anim_dist": 5.5,
           "frames": [("idle", 0), ("fire", 3), ("fire", 7), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
