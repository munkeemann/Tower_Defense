"""Builds the Wasp Hive (footprint "pair": [0,0] front, [0,1] back), a Verdant tower: a swarm of stingers.

    blender -b --factory-startup --python tools/blender/build_tower.py -- hive <preview dir>

Front cell: a gnarled dead tree arches over and a big striped papery hive hangs from it, wasps circling (the Head:
stingers leave from the hive's mouth). Back cell: honeycomb frames, honey pots and flowering bushes.
idle: the hive sways, wasps circle. fire: the hive throbs and the wasps dart out and back.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "hive"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
HIVE_Z = 1.25                  # hive centre above the Head (the head sits under the hanging point)


def build_base():
    col = collection("Hive")
    root = empty("Hive", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(9)
    F = FRONT
    # the dead tree: a trunk on the left that bends over the middle of the front cell
    bm = bmesh.new()
    pts = [Vector((-0.62, F.y - 0.25, T)), Vector((-0.66, F.y - 0.2, T + 0.9)), Vector((-0.5, F.y - 0.12, T + 1.75)),
           Vector((-0.15, F.y - 0.02, T + 2.25)), Vector((0.18, F.y + 0.05, T + 2.32))]
    ws = [0.3, 0.24, 0.19, 0.14, 0.1]
    for i in range(len(pts) - 1):
        bm_beam(bm, pts[i], pts[i + 1], ws[i], ws[i], w1=ws[i + 1], h1=ws[i + 1])
    bm_beam(bm, pts[2], pts[2] + Vector((-0.35, 0.1, 0.4)), 0.1, 0.1, w1=0.04, h1=0.04)
    bm_beam(bm, pts[3], pts[3] + Vector((-0.1, -0.35, 0.3)), 0.08, 0.08, w1=0.03, h1=0.03)
    bm_beam(bm, pts[4], pts[4] + Vector((0.35, 0.05, 0.12)), 0.07, 0.07, w1=0.03, h1=0.03)
    for k in range(4):
        a = math.radians(90 * k + 20)
        bm_beam(bm, pts[0] + Vector((0, 0, 0.12)), pts[0] + Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, -0.02)), 0.1, 0.08, w1=0.04, h1=0.04)
    paint(mesh_obj("Tree_Dead", bm, col, root), "wood_dark", lo=0.2, hi=0.75)
    # back cell: honeycomb frames on a stand, honey pots, flowers
    B = BACK
    bm = bmesh.new()
    for k in range(3):
        bm_box(bm, (0.5, 0.06, 0.4), (B.x + 0.25, B.y - 0.15 + k * 0.14, T + 0.42))
    bm_box(bm, (0.62, 0.5, 0.06), (B.x + 0.25, B.y - 0.01, T + 0.2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(bm, (0.06, 0.06, 0.2), (B.x + 0.25 + sx * 0.27, B.y - 0.01 + sy * 0.2, T + 0.1))
    paint(mesh_obj("Back_Frames", bm, col, root), "wood", lo=0.2, hi=0.7)
    bm = bmesh.new()
    for k in range(3):
        bm_box(bm, (0.42, 0.065, 0.32), (B.x + 0.25, B.y - 0.15 + k * 0.14, T + 0.42))
    paint(mesh_obj("Back_Comb", bm, col, root), "gold", lo=0.2, hi=0.5)
    bm = bmesh.new()
    for (dx, dy, r) in ((-0.45, -0.3, 0.16), (-0.6, 0.05, 0.13), (-0.3, 0.3, 0.11)):
        bm_ellipsoid(bm, (B.x + dx, B.y + dy, T + r), (r, r, r * 1.05), u=10, v=6)
        bm_cyl(bm, r * 0.6, r * 0.6, 0.06, (B.x + dx, B.y + dy, T + r * 2.0), seg=10)
    paint(mesh_obj("Back_Pots", bm, col, root), "roof", lo=0.2, hi=0.7)
    for i, (rel, loc, sc) in enumerate((("forest/Bush_1_E_Color1", (B.x + 0.6, B.y + 0.5, T - 0.02), 0.3),
                                        ("forest/Bush_2_A_Color1", (F.x + 0.7, F.y - 0.45, T - 0.02), 0.28),
                                        ("forest/Grass_1_C_Color1", (F.x + 0.5, F.y + 0.55, T - 0.02), 0.6))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (0.18, F.y + 0.05, T + 2.32 - HIVE_Z - 0.55), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hive": ((0, 0, HIVE_Z + 0.55), (0, 0, HIVE_Z), "root"),
}
WASPS = [(0.75, 0.0, 0.0), (0.9, 0.35, 120.0), (0.65, -0.3, 240.0), (1.05, 0.15, 60.0), (0.8, -0.1, 300.0)]


def build_head():
    global BONES
    for i, (r, dz, a) in enumerate(WASPS):
        BONES["wasp.%d" % i] = ((0, 0, HIVE_Z + dz), (0, 0, HIVE_Z + dz + 0.2), "root")
    col = collection("Hive")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    # the hive: stacked bands, alternately gold and tan, narrowing to the top and the bottom
    bands = [(0.0, 0.18), (0.14, 0.3), (0.28, 0.38), (0.42, 0.42), (0.56, 0.42), (0.7, 0.38), (0.84, 0.3), (0.96, 0.2)]
    gold_b, tan_b = bmesh.new(), bmesh.new()
    z0 = HIVE_Z - 0.5
    for i, (z, r) in enumerate(bands):
        bm_cyl(gold_b if i % 2 == 0 else tan_b, r, r * 0.95, 0.15, (0, 0, z0 + z + 0.07), seg=12)
    rig_part("Head_HiveA", gold_b, "gold", rig, "hive", col, bevel=0, lo=0.15, hi=0.45)
    rig_part("Head_HiveB", tan_b, "sand", rig, "hive", col, bevel=0, lo=0.3, hi=0.7)
    bm = bmesh.new()
    bm_cyl(bm, 0.1, 0.1, 0.2, (0, 0, z0 + 1.1), seg=8)
    bm_cyl(bm, 0.13, 0.13, 0.04, (0, 0.38, z0 + 0.3), rot=(90, 0, 0), seg=10)
    rig_part("Head_HiveTop", bm, "wood_dark", rig, "hive", col, bevel=0, lo=0.3, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.1, 0.1, 0.03, (0, 0.41, z0 + 0.3), rot=(90, 0, 0), seg=10)
    rig_part("Head_HiveMouth", bm, "black", rig, "hive", col, bevel=0, lo=0.3, hi=0.6)
    # wasps on their orbits
    for i, (r, dz, a) in enumerate(WASPS):
        c = Vector((math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r, HIVE_Z + dz))
        tang = Vector((-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))
        yb, kb, wb = bmesh.new(), bmesh.new(), bmesh.new()
        rot = tuple(math.degrees(x) for x in tang.to_track_quat("Y", "Z").to_euler())
        bm_ellipsoid(yb, c, (0.055, 0.1, 0.055), rot, u=6, v=4)
        bm_ellipsoid(kb, c - tang * 0.1, (0.045, 0.07, 0.045), rot, u=6, v=4)
        bm_cyl(kb, 0.012, 0.0, 0.06, tuple(c - tang * 0.18), rot=tuple(math.degrees(x) for x in (-tang).to_track_quat("Z", "Y").to_euler()), seg=4)
        side = tang.cross(Vector((0, 0, 1))).normalized()
        for s in (-1, 1):
            p = c + side * s * 0.03 + Vector((0, 0, 0.04))
            vs = [wb.verts.new(v) for v in (p, p + side * s * 0.12 + tang * 0.04 + Vector((0, 0, 0.06)),
                                              p + side * s * 0.13 - tang * 0.06 + Vector((0, 0, 0.04)))]
            wb.faces.new(vs)
            wb.faces.new(list(reversed([wb.verts.new(v.co + Vector((0, 0, -0.004))) for v in vs])))
        rig_part("Head_Wasp%dY" % i, yb, "gold", rig, "wasp.%d" % i, col, bevel=0, lo=0.05, hi=0.3)
        rig_part("Head_Wasp%dK" % i, kb, "black", rig, "wasp.%d" % i, col, bevel=0, lo=0.3, hi=0.6)
        rig_part("Head_Wasp%dW" % i, wb, "white", rig, "wasp.%d" % i, col, bevel=0, lo=0.05, hi=0.2)
    empty("Muzzle", col, head, (0, 0.45, z0 + 0.3), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 8


def pose(rig, sway=0.0, throb=0.0, orbit=0.0, dart=0.0, buzz=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["hive"].rotation_quaternion = arm_space_quat(pb["hive"], (1, 0, 0), sway) @ arm_space_quat(pb["hive"], (0, 1, 0), sway * 0.6)
    pb["hive"].scale = (1 + throb, 1 - throb * 0.5, 1 + throb)           # (a hanging bone: its own Y is the height)
    for i, (r, dz, a) in enumerate(WASPS):
        sp = (1.0 if i % 2 == 0 else -1.3)
        b = pb["wasp.%d" % i]
        b.rotation_quaternion = arm_space_quat(b, (0, 0, 1), orbit * sp + 37 * i)
        b.location = arm_space_loc(b, (0, 0, 0.05 * math.sin(buzz * 6 + i)))
        k = 1.0 + dart * (0.5 + 0.15 * i)
        b.scale = (k, k, 1.0)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, sway=4 * math.sin(ph), orbit=360 * f / IDLE_LEN, buzz=ph)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = f / FIRE_LEN
        pose(rig, throb=0.08 * math.sin(math.pi * t), orbit=60 * t, dart=math.sin(math.pi * t), buzz=t * 6.28)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 7.0, "yaw": 150, "pitch": 22, "anim_target": (0.18, FRONT.y, 1.9), "anim_dist": 4.0,
           "frames": [("idle", 0), ("idle", 20), ("fire", 4)]}


def build_all():
    build_base()
    build_head()
    build_anims()
