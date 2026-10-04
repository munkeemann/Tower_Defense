"""Builds the Forge of Ages (footprint "fan4": [0,0] back, [-1,0] front-left, [0,-1] front, [1,-1] front-right), the
Forge's Tier IV support tower: the towers around it hit harder and set what they hit burning.

    blender -b --factory-startup --python tools/blender/build_tower.py -- war_forge <preview dir>

Back cell: a great domed stone furnace with a glowing mouth and a tall chimney spitting embers; a molten channel runs from
its mouth to the front cell, where a giant trip hammer on a timber frame beats a black anvil. Front-left: a quench
trough and stacks of iron and gold bars. Front-right: a huge pair of bellows feeding the furnace. It's an aura tower,
so nothing aims (the Head just sits on the anvil); idle: the hammer rises and slams down (sparks burst), the bellows
pump, the chimney's embers breathe.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "war_forge"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FL = hex_to_world(-1, 0, MID)
FC = hex_to_world(0, -1, MID)
FR = hex_to_world(1, -1, MID)
TOP = 0.34
T = TOP
EMBER = (1.0, 0.45, 0.12)
MOLTEN = (1.0, 0.62, 0.2)
ANVIL = Vector((FC.x, FC.y - 0.05, 0))
AXLE = Vector((0.0, FC.y - 0.85, T + 1.0))      # the trip hammer's pivot, on the frame behind the anvil
STRIKE = Vector((ANVIL.x, ANVIL.y, T + 0.82))   # where the hammer head rests on the anvil
FURN = Vector((BK.x, BK.y - 0.1, 0))


def build_base():
    col = collection("War_forge")
    root = empty("War_forge", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(8)
    # the furnace: a squat stone dome on a round footing, a glowing mouth facing the front
    bm = bmesh.new()
    bm_cyl(bm, 0.82, 0.86, 0.3, (FURN.x, FURN.y, T + 0.15), seg=16)
    bm_ellipsoid(bm, (FURN.x, FURN.y, T + 0.3), (0.78, 0.78, 0.85), u=16, v=8)
    o = paint(mesh_obj("Furnace", bm, col, root), "stone_warm", lo=0.1, hi=0.65)
    bm = bmesh.new()                                     # iron hoops round the dome
    for z, r in ((T + 0.55, 0.76), (T + 0.85, 0.66)):
        ring(bm, (FURN.x, FURN.y, 0), r + 0.03, r - 0.05, z, z + 0.07, seg=16)
    paint(mesh_obj("Furnace_Hoops", bm, col, root), "iron", lo=0.1, hi=0.45)
    bm = bmesh.new()                                     # the mouth: an arch of fire on the front face
    my = FURN.y + 0.74
    bm_box(bm, (0.5, 0.06, 0.32), (FURN.x, my, T + 0.32))
    bm_cyl(bm, 0.25, 0.25, 0.06, (FURN.x, my, T + 0.48), rot=(90, 0, 0), seg=12)
    glow_obj("Furnace_Mouth", bm, col, root, EMBER, 2.2)
    bm = bmesh.new()
    for k in range(7):
        a = math.pi * k / 6
        bm_box(bm, (0.12, 0.1, 0.12), (FURN.x + math.cos(a) * 0.33, my + 0.02, T + 0.48 + math.sin(a) * 0.33),
               rot=(0, -math.degrees(a) + 90, 0))
    bm_box(bm, (0.16, 0.1, 0.48), (FURN.x - 0.33, my + 0.02, T + 0.24))
    bm_box(bm, (0.16, 0.1, 0.48), (FURN.x + 0.33, my + 0.02, T + 0.24))
    paint(mesh_obj("Furnace_Arch", bm, col, root), "stone_dark", lo=0.1, hi=0.6)
    # the chimney, set to the back corner so it doesn't hide the anvil, with a glowing ember crown
    C = Vector((FURN.x + 0.5, FURN.y - 0.35, 0))
    bm = bmesh.new()
    bm_box(bm, (0.42, 0.42, 2.05), (C.x, C.y, T + 1.02))
    bm_box(bm, (0.52, 0.52, 0.12), (C.x, C.y, T + 2.06))
    o = paint(mesh_obj("Chimney", bm, col, root), "stone2", lo=0.1, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_box(bm, (0.3, 0.3, 0.04), (C.x, C.y, T + 2.13))
    glow_obj("Chimney_Glow", bm, col, root, EMBER, 2.0)
    # the molten channel from the furnace mouth to the anvil
    bm = bmesh.new()
    y0, y1 = my + 0.08, ANVIL.y - 0.35
    for sx in (-1, 1):
        bm_box(bm, (0.1, y1 - y0, 0.1), (sx * 0.15, (y0 + y1) / 2, T + 0.05))
    paint(mesh_obj("Channel_Stones", bm, col, root), "stone_dark", lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_box(bm, (0.2, y1 - y0, 0.04), (0, (y0 + y1) / 2, T + 0.04))
    glow_obj("Channel_Molten", bm, col, root, MOLTEN, 1.8)
    # the anvil on its stone block
    bm = bmesh.new()
    bm_box(bm, (0.78, 0.66, 0.36), (ANVIL.x, ANVIL.y, T + 0.18))
    o = paint(mesh_obj("Anvil_Block", bm, col, root), "stone", lo=0.15, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_box(bm, (0.34, 0.24, 0.12), (ANVIL.x, ANVIL.y, T + 0.42))
    bm_box(bm, (0.2, 0.18, 0.14), (ANVIL.x, ANVIL.y, T + 0.54))
    bm_box(bm, (0.6, 0.3, 0.12), (ANVIL.x - 0.03, ANVIL.y, T + 0.66))
    bm_cyl(bm, 0.12, 0.0, 0.36, (ANVIL.x + 0.43, ANVIL.y, T + 0.66), rot=(0, 90, 0), seg=8)
    paint(mesh_obj("Anvil", bm, col, root), "black", lo=0.2, hi=0.75)
    bm = bmesh.new()
    bm_box(bm, (0.3, 0.16, 0.03), (ANVIL.x - 0.05, ANVIL.y, T + 0.735))
    glow_obj("Anvil_Hot", bm, col, root, MOLTEN, 1.5)      # a glowing blade being beaten
    # the trip hammer's frame: two timber posts and a cross beam carrying the axle
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.14, 0.14, 1.08), (sx * 0.48, AXLE.y, T + 0.54))
        bm_beam(bm, (sx * 0.48, AXLE.y - 0.45, T), (sx * 0.48, AXLE.y, T + 0.75), 0.09, 0.09)
    bm_box(bm, (1.1, 0.12, 0.12), (0, AXLE.y, AXLE.z + 0.12))
    paint(mesh_obj("Hammer_Frame", bm, col, root), "wood_dark", lo=0.15, hi=0.8)
    # front-left: a quench trough and bars; front-right: the bellows' footing
    kk = [("hex/trough", (FL.x + 0.25, FL.y + 0.15, T), 60, 2.3),
          ("resources/Iron_Bars_Stack_Medium", (FL.x - 0.35, FL.y - 0.35, T), 20, 0.5),
          ("resources/Gold_Bars_Stack_Small", (FL.x - 0.45, FL.y + 0.45, T), 70, 0.5),
          ("resources/Copper_Bars_Stack_Small", (FR.x + 0.45, FR.y + 0.5, T), 200, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    bm = bmesh.new()
    bm_box(bm, (0.5, 0.9, 0.16), (FR.x - 0.1, FR.y - 0.25, T + 0.08), rot=(0, 0, 35))
    paint(mesh_obj("Bellows_Stand", bm, col, root), "stone2", lo=0.2, hi=0.7)
    bm = bmesh.new()                                     # its pipe into the furnace
    bm_beam(bm, (FR.x - 0.45, FR.y - 0.7, T + 0.3), (FURN.x + 0.62, FURN.y + 0.25, T + 0.45), 0.1, 0.1)
    paint(mesh_obj("Bellows_Pipe", bm, col, root), "iron", lo=0.15, hi=0.5)
    head = empty("Head", col, root, (ANVIL.x, ANVIL.y, T + 0.75), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.3), 0.2, "SPHERE")
    return root


BELLOW = Vector((FR.x - 0.1, FR.y - 0.25, T + 0.22))
BELLOW_DIR = Vector((-math.sin(math.radians(35)), math.cos(math.radians(35)), 0)) * -1.0   # toward the furnace
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "hammer": (tuple(AXLE), tuple(AXLE + Vector((0, 0.3, 0))), "root"),
         "sparks": (tuple(STRIKE), tuple(STRIKE + Vector((0, 0, 0.2))), "root"),
         "bellows": (tuple(BELLOW + BELLOW_DIR * 0.4), tuple(BELLOW + BELLOW_DIR * 0.4 + Vector((0, 0, 0.2))), "root"),
         "embers": ((FURN.x + 0.5, FURN.y - 0.35, T + 2.15), (FURN.x + 0.5, FURN.y - 0.35, T + 2.35), "root")}


def build_rig():
    col = collection("War_forge")
    root = bpy.data.objects["War_forge"]
    rig = make_rig(col, root, BONES)
    # the trip hammer: an iron-shod beam from the axle to a great hammer head resting on the anvil
    head_c = STRIKE + Vector((0, 0, 0.2))
    bm = bmesh.new()
    bm_beam(bm, AXLE - Vector((0, 0.25, 0)), head_c + Vector((0, 0.05, 0.12)), 0.13, 0.13)
    bm_cyl(bm, 0.09, 0.09, 1.05, tuple(AXLE), rot=(0, 90, 0), seg=8)
    rig_part("Hammer_Beam", bm, "wood", rig, "hammer", col, bevel=0, lo=0.2, hi=0.8)
    bm = bmesh.new()
    bm_box(bm, (0.3, 0.3, 0.42), tuple(head_c + Vector((0, 0, 0.02))))
    bm_box(bm, (0.36, 0.36, 0.08), tuple(head_c - Vector((0, 0, 0.2))))
    rig_part("Hammer_Head", bm, "iron", rig, "hammer", col, bevel=0.015, lo=0.05, hi=0.5)
    bm = bmesh.new()
    for dz in (-0.06, 0.14):
        bm_box(bm, (0.33, 0.33, 0.05), tuple(head_c + Vector((0, 0, dz))))
    rig_part("Hammer_Bands", bm, "gold", rig, "hammer", col, bevel=0, lo=0.15, hi=0.6)
    # sparks: a burst of glowing shards round the strike, hidden at rest
    bm = bmesh.new()
    rnd = random.Random(3)
    for k in range(10):
        a = 2 * math.pi * k / 10 + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.2, 0.9))).normalized()
        p = STRIKE + d * rnd.uniform(0.25, 0.45)
        bm_beam(bm, p, p + d * 0.14, 0.035, 0.035, 0.008, 0.008)
    rig_part("Hammer_Sparks", bm, None, rig, "sparks", col, bevel=0, mat=glow_mat("forge_sparks", (1.0, 0.8, 0.35), 3.0))
    # the bellows: a bottom board on the stand, a leather pleat, a top board hinged at the nozzle end
    q = Euler((0, 0, math.radians(35))).to_matrix()
    def drop(z0, z1, k=1.0):
        pts = [Vector((0.24 * k * math.cos(a), 0.12 + 0.3 * k * math.sin(a), 0)) for a in [math.radians(d) for d in range(0, 181, 30)]]
        pts += [Vector((-0.05 * k, -0.38, 0)), Vector((0.05 * k, -0.38, 0))]
        b = bmesh.new()
        prism(b, pts, z0, z1)
        return b
    def merge(dst, src):
        me = bpy.data.meshes.new("_t"); src.to_mesh(me); src.free(); dst.from_mesh(me); bpy.data.meshes.remove(me)
    bm = bmesh.new()
    merge(bm, drop(-0.03, 0.03))
    bm_cyl(bm, 0.05, 0.03, 0.3, (0, -0.5, 0.05), rot=(90, 0, 0), seg=8)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q)
    bmesh.ops.translate(bm, verts=bm.verts, vec=BELLOW)
    rig_part("Bellows_Bottom", bm, "wood_dark", rig, "root", col, bevel=0, lo=0.2, hi=0.8)
    bm = bmesh.new()
    merge(bm, drop(0.18, 0.23))
    bm_box(bm, (0.06, 0.26, 0.06), (0, 0.48, 0.24))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q)
    bmesh.ops.translate(bm, verts=bm.verts, vec=BELLOW)
    rig_part("Bellows_Top", bm, "wood_dark", rig, "bellows", col, bevel=0, lo=0.2, hi=0.8)
    bm = bmesh.new()
    merge(bm, drop(0.03, 0.08, 0.86))
    merge(bm, drop(0.08, 0.13, 0.95))
    merge(bm, drop(0.13, 0.18, 0.86))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q)
    bmesh.ops.translate(bm, verts=bm.verts, vec=BELLOW)
    rig_part("Bellows_Leather", bm, "wood_red", rig, "bellows", col, bevel=0, lo=0.2, hi=0.7)
    # the chimney's embers
    bm = bmesh.new()
    for k in range(6):
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.3, 0.3)
        p = Vector((FURN.x + 0.5 + math.cos(a) * 0.1, FURN.y - 0.35 + math.sin(a) * 0.1, T + 2.2 + rnd.uniform(0.05, 0.4)))
        bm_ellipsoid(bm, tuple(p), (0.04, 0.04, 0.05), u=5, v=3)
    rig_part("Chimney_Embers", bm, None, rig, "embers", col, bevel=0, mat=glow_mat("forge_embers", EMBER, 2.5))
    return rig


IDLE_LEN = 48


def pose(rig, lift=0.0, spark=0.0, pump=0.0, ember=1.0, rise=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["hammer"].rotation_quaternion = arm_space_quat(pb["hammer"], (1, 0, 0), 32 * lift)
    s = max(0.001, spark)
    pb["sparks"].scale = (s, s, s)
    pb["bellows"].rotation_quaternion = arm_space_quat(pb["bellows"], (math.cos(math.radians(35)), math.sin(math.radians(35)), 0), -8 * pump)
    pb["embers"].scale = (ember, ember, ember)
    pb["embers"].location = arm_space_loc(pb["embers"], (0, 0, rise))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1):
        t = f / IDLE_LEN
        # two blows a loop: a slow lift (frames 0-16), a fast fall (16-20), a beat on the anvil
        u = (f % 24) / 24.0
        lift = smooth(u / 0.66) if u < 0.66 else 1.0 - smooth((u - 0.66) / 0.17)
        spark = 0.0 if u < 0.83 else 1.4 * (1 - (u - 0.83) / 0.17)
        pose(rig, lift=lift, spark=spark, pump=0.5 + 0.5 * math.sin(2 * math.pi * t * 2),
             ember=1.0 + 0.25 * math.sin(2 * math.pi * t * 3), rise=0.12 * ((t * 2) % 1.0))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 0.8), "dist": 10.0, "yaw": 150, "pitch": 22, "anim_target": (0, FC.y - 0.4, T + 0.7), "anim_dist": 4.0,
           "frames": [("idle", 2), ("idle", 14), ("idle", 21)]}


def build_all():
    build_base()
    build_rig()
    build_anims()
