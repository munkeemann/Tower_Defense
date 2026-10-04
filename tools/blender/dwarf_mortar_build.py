"""Builds the Siege Mortar (footprint "fan4": [0,0] back, [-1,0] front-left, [0,-1] front, [1,-1] front-right), a
Forge tower: colossal range, huge blasts.

    blender -b --factory-startup --python tools/blender/build_tower.py -- dwarf_mortar <preview dir>

A squat bronze mortar on an iron carriage turns on a round platform where the four hexes meet (the Head: shells leave
its mouth). Cannonball stacks, powder kegs and crates lie on the front cells; a small crane with a hanging shell and a
dwarf loader (Crew) stand at the back. idle: the carriage settles, the crane's shell sways. fire: the barrel slams back
and down, the carriage jolts, smoke billows from the mouth.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dwarf_mortar"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FLc = hex_to_world(-1, 0, MID)
Fc = hex_to_world(0, -1, MID)
FRc = hex_to_world(1, -1, MID)
TOP = 0.34
ELEV = 50.0          # barrel elevation


def build_base():
    col = collection("Dwarf_mortar")
    root = empty("Dwarf_mortar", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, stone="stone_dark", course="iron")
    rnd = random.Random(12)
    bm = bmesh.new()
    bm_cyl(bm, 1.0, 1.05, 0.16, (0, 0, T + 0.08), seg=16)
    o = paint(mesh_obj("Platform", bm, col, root), "stone", lo=0.1, hi=0.55)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.92, 0.84, T + 0.15, T + 0.19, seg=24)
    paint(mesh_obj("Platform_Rail", bm, col, root), "iron", lo=0.2, hi=0.5)
    # the crane at the back: a post, an arm, a chain and a shell
    bm = bmesh.new()
    cp = BK + Vector((0.6, -0.3, 0))
    bm_box(bm, (0.16, 0.16, 1.9), (cp.x, cp.y, T + 0.95))
    bm_beam(bm, (cp.x, cp.y, T + 1.85), (cp.x - 0.75, cp.y + 0.15, T + 1.9), 0.12, 0.12)
    bm_beam(bm, (cp.x, cp.y, T + 1.3), (cp.x - 0.45, cp.y + 0.1, T + 1.88), 0.07, 0.07)
    paint(mesh_obj("Crane", bm, col, root), "wood", lo=0.2, hi=0.8)
    kk = [("hex/cannonball_pallet", (FLc.x - 0.15, FLc.y + 0.1, T), 30, 2.6), ("dungeon/barrel_small_stack", (FRc.x + 0.1, FRc.y + 0.05, T), 200, 0.35),
          ("dungeon/crates_stacked", (Fc.x + 0.45, Fc.y + 0.45, T), 20, 0.3), ("hex/cannonball_pallet", (Fc.x - 0.5, Fc.y + 0.4, T), 70, 2.2),
          ("resources/Parts_Pile_Medium", (BK.x - 0.6, BK.y - 0.35, T), 140, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    crew = empty("Crew", col, root, (BK.x - 0.15, BK.y - 0.5, T), 0.3, "SINGLE_ARROW")   # faces the mortar (+Y)
    empty("Head", col, root, (0, 0, T + 0.19), 0.5, "SINGLE_ARROW")
    return root


PIVOT = Vector((0, -0.05, 0.62))
AXIS = Vector((0, math.cos(math.radians(ELEV)), math.sin(math.radians(ELEV))))
MUZ = PIVOT + AXIS * 0.78
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "carriage": ((0, 0, 0.0), (0, 0.3, 0.0), "root"),
         "barrel": (tuple(PIVOT), tuple(PIVOT + AXIS * 0.4), "carriage"),
         "smoke": (tuple(MUZ), tuple(MUZ + Vector((0, 0, 0.3))), "root"),
         "shell": None}


def build_head():
    col = collection("Dwarf_mortar")
    head = bpy.data.objects["Head"]
    cp = BK + Vector((0.6, -0.3, 0)) - Vector(head.location)
    hang = Vector((cp.x - 0.7, cp.y + 0.15, TOP + 1.85 - head.location.z))
    BONES["shell"] = (tuple(hang), tuple(hang - Vector((0, 0, 0.3))), "root")
    rig = make_rig(col, head, BONES)
    # carriage: a turning iron base and two cheek plates holding the trunnions
    bm = bmesh.new()
    bm_cyl(bm, 0.82, 0.82, 0.14, (0, 0, 0.07), seg=16)
    for sx in (-1, 1):
        vs = [Vector((sx * 0.42, -0.5, 0.14)), Vector((sx * 0.42, 0.45, 0.14)), Vector((sx * 0.42, 0.1, 0.85)), Vector((sx * 0.42, -0.35, 0.75))]
        for off in (-0.06, 0.06):
            bvs = [bm.verts.new(v + Vector((off, 0, 0))) for v in vs]
            bm.faces.new(bvs if off * sx > 0 else list(reversed(bvs)))
        bm_box(bm, (0.12, 0.95, 0.04), (sx * 0.42, -0.02, 0.15))
    o = rig_part("Head_Carriage", bm, "iron", rig, "carriage", col, bevel=0, lo=0.05, hi=0.6)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_cyl(bm, 0.1, 0.1, 0.18, (sx * 0.48, PIVOT.y, PIVOT.z), rot=(0, 90, 0), seg=8)
    rig_part("Head_Trunnions", bm, "gold", rig, "carriage", col, bevel=0, lo=0.1, hi=0.5)
    # the barrel: a stubby bronze tube, reinforcing rings, a flared mouth with a dark bore
    rot = tuple(math.degrees(x) for x in AXIS.to_track_quat("Z", "Y").to_euler())
    bm = bmesh.new()
    bm_cyl(bm, 0.36, 0.33, 1.05, tuple(PIVOT + AXIS * 0.25), rot=rot, seg=14)
    bm_ellipsoid(bm, tuple(PIVOT - AXIS * 0.25), (0.36, 0.36, 0.36), u=12, v=7)
    rig_part("Head_Barrel", bm, "gold", rig, "barrel", col, bevel=0, lo=0.15, hi=0.6)
    bm = bmesh.new()
    for t, r in ((-0.05, 0.4), (0.35, 0.38), (0.72, 0.42)):
        q = Vector((0, 0, 1)).rotation_difference(AXIS)
        tmp = bmesh.new()
        ring(tmp, (0, 0, 0), r, r - 0.08, -0.05, 0.05, seg=14)
        bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=q.to_matrix())
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=PIVOT + AXIS * t)
        me = bpy.data.meshes.new("_t"); tmp.to_mesh(me); tmp.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    rig_part("Head_BarrelRings", bm, "iron", rig, "barrel", col, bevel=0, lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_cyl(bm, 0.25, 0.25, 0.04, tuple(MUZ + AXIS * 0.01), rot=rot, seg=12)
    rig_part("Head_Bore", bm, "black", rig, "barrel", col, bevel=0, lo=0.3, hi=0.6)
    bm = bmesh.new()
    rnd = random.Random(6)
    for k in range(6):
        bm_ellipsoid(bm, MUZ + AXIS * (0.15 + k * 0.12) + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.05, 0.1))),
                     (0.24 + k * 0.03,) * 2 + (0.2 + k * 0.03,), u=7, v=5)
    rig_part("Head_Smoke", bm, "stone2", rig, "smoke", col, bevel=0, lo=0.05, hi=0.45)
    bm = bmesh.new()
    bm_beam(bm, hang, hang - Vector((0, 0, 0.35)), 0.025, 0.025)
    bm_ellipsoid(bm, tuple(hang - Vector((0, 0, 0.5))), (0.17, 0.17, 0.17), u=10, v=6)
    rig_part("Head_CraneShell", bm, "iron", rig, "shell", col, bevel=0, lo=0.2, hi=0.6)
    empty("Muzzle", col, head, tuple(MUZ + AXIS * 0.05), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 36


def pose(rig, recoil=0.0, jolt=0.0, smoke=0.0, drift=0.0, sway=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["barrel"].location = arm_space_loc(pb["barrel"], tuple(-AXIS * recoil * 0.28))
    pb["barrel"].rotation_quaternion = arm_space_quat(pb["barrel"], (1, 0, 0), -recoil * 5)
    pb["carriage"].location = arm_space_loc(pb["carriage"], (0, -jolt * 0.08, 0))
    pb["smoke"].scale = (max(smoke, 0.001),) * 3
    pb["smoke"].location = arm_space_loc(pb["smoke"], tuple(AXIS * drift))
    pb["shell"].rotation_quaternion = arm_space_quat(pb["shell"], (1, 0, 0), sway)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, sway=6 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rc = smooth(f / 1.5) * (1 - smooth((f - 3) / 18.0))
        jolt = smooth(f / 2.0) * (1 - smooth((f - 3) / 10.0))
        sm = 0.0 if f < 1 else 1.2 * smooth((f - 1) / 5.0) * (1 - smooth((f - 14) / 20.0))
        pose(rig, recoil=rc, jolt=jolt, smoke=sm, drift=0.9 * smooth(f / FIRE_LEN), sway=14 * math.sin(f * 0.5) * (1 - f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 10.0, "yaw": 150, "pitch": 22, "anim_target": (0, 0.3, 1.2), "anim_dist": 5.0,
           "frames": [("idle", 0), ("fire", 3), ("fire", 12)]}


def build_all():
    build_base()
    build_head()
    build_anims()
