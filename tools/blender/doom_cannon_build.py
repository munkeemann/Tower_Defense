"""Builds the Doomsday Cannon (footprint "arrow5": [0,0] front, [1,0] / [-1,1] the back corners, [0,1] / [0,2] the
spine behind), the Forge's Tier IV siege gun: shells that level crowds at the far end of the map.

    blender -b --factory-startup --python tools/blender/build_tower.py -- doom_cannon <preview dir>

A colossal iron cannon with gold bands, a glowing rune band and a flared bronze mouth lies on a turning iron sled over a
round stone emplacement (the Head: it turns within its 120 degree arc; shells leave the mouth). Its breech ends in a big
cascabel ball and an elevation wheel. Shell pallets and crates fill the back corners; on the last hex a low ammo cart
carries one giant shell; a dwarf gunner (Crew) stands by the breech. idle: the rune band breathes, the wheel creeps.
fire: the barrel slams back along its sled, the sled jolts, a ring of smoke blooms at the mouth.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "doom_cannon"
CELLS = [(0, 0), (1, 0), (-1, 1), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
R = hex_to_world(1, 0, MID)
L = hex_to_world(-1, 1, MID)
B1 = hex_to_world(0, 1, MID)
B2 = hex_to_world(0, 2, MID)
TOP = 0.34
PIV_XY = Vector((0.0, (F.y + B1.y) * 0.5 - 0.1, 0.0))   # the turntable sits between the front hex and the spine
ELEV = 12.0
EMBER = (1.0, 0.45, 0.12)


def build_base():
    col = collection("Doom_cannon")
    root = empty("Doom_cannon", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    bm = bmesh.new()
    bm_cyl(bm, 1.25, 1.32, 0.18, (PIV_XY.x, PIV_XY.y, T + 0.09), seg=20)
    o = paint(mesh_obj("Emplacement", bm, col, root), "stone", lo=0.1, hi=0.55)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.025; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (PIV_XY.x, PIV_XY.y, 0), 1.12, 1.02, T + 0.17, T + 0.21, seg=28)
    paint(mesh_obj("Emplacement_Rail", bm, col, root), "iron", lo=0.2, hi=0.5)
    bm = bmesh.new()                                               # bolts round the rail
    for k in range(12):
        a = 2 * math.pi * k / 12
        bm_cyl(bm, 0.045, 0.045, 0.05, (PIV_XY.x + 1.19 * math.cos(a), PIV_XY.y + 1.19 * math.sin(a), T + 0.2), seg=6)
    paint(mesh_obj("Emplacement_Bolts", bm, col, root), "gold", lo=0.2, hi=0.6)
    # the ammo cart on the last hex: a low wagon with one giant shell lying in it
    C = B2
    bm = bmesh.new()
    bm_box(bm, (0.75, 1.15, 0.1), (C.x, C.y, T + 0.3))
    for sx in (-1, 1):
        bm_box(bm, (0.06, 1.15, 0.2), (C.x + sx * 0.36, C.y, T + 0.42))
    bm_beam(bm, (C.x, C.y + 0.55, T + 0.3), (C.x, C.y + 1.0, T + 0.18), 0.07, 0.07)
    paint(mesh_obj("Cart", bm, col, root), "wood_dark", lo=0.15, hi=0.8)
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-0.35, 0.35):
            P = (C.x + sx * 0.44, C.y + sy, T + 0.2)
            ring(bm, P, 0.2, 0.14, -0.035, 0.035, seg=12, axis="X")
            bm_cyl(bm, 0.05, 0.05, 0.1, P, rot=(0, 90, 0), seg=6)
            for k in range(3):
                bm_box(bm, (0.03, 0.3, 0.03), P, rot=(60 * k, 0, 0))
    paint(mesh_obj("Cart_Wheels", bm, col, root), "iron", lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_cyl(bm, 0.24, 0.24, 0.62, (C.x, C.y - 0.05, T + 0.6), rot=(90, 0, 0), seg=12)
    bm_cyl(bm, 0.24, 0.0, 0.42, (C.x, C.y + 0.47, T + 0.6), rot=(-90, 0, 0), seg=12)
    paint(mesh_obj("Cart_Shell", bm, col, root), "iron", lo=0.1, hi=0.45)
    bm = bmesh.new()
    ring(bm, (C.x, C.y + 0.05, T + 0.6), 0.26, 0.2, -0.05, 0.05, seg=12, axis="Y")
    glow_obj("Cart_ShellRune", bm, col, root, EMBER, 1.2)
    # shell pallets and crates on the back corners (no barrels: they don't fit the realm)
    kk = [("hex/cannonball_pallet", (R.x + 0.05, R.y - 0.1, T), 20, 2.7), ("hex/cannonball_pallet", (L.x - 0.1, L.y - 0.05, T), 75, 2.7),
          ("dungeon/crates_stacked", (R.x + 0.45, R.y + 0.45, T), 200, 0.32), ("dungeon/box_large", (L.x - 0.5, L.y + 0.45, T), 30, 0.36),
          ("resources/Parts_Pile_Medium", (B1.x + 0.75, B1.y - 0.35, T), 140, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    empty("Crew", col, root, (B1.x - 0.85, B1.y - 0.3, T), 0.3, "SINGLE_ARROW").rotation_euler = (0, 0, math.radians(-35))
    empty("Head", col, root, (PIV_XY.x, PIV_XY.y, T + 0.21), 0.5, "SINGLE_ARROW")
    return root


AXIS = Vector((0, math.cos(math.radians(ELEV)), math.sin(math.radians(ELEV))))
PIVOT = Vector((0, 0.05, 0.78))
BREECH = PIVOT - AXIS * 0.95
MOUTH = PIVOT + AXIS * 2.35
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "sled": ((0, 0, 0.0), (0, 0.3, 0.0), "root"),
         "barrel": (tuple(PIVOT), tuple(PIVOT + AXIS * 0.4), "sled"),
         "wheel": (tuple(Vector((0.62, -0.25, 0.62))), tuple(Vector((0.92, -0.25, 0.62))), "sled"),
         "smoke": (tuple(MOUTH), tuple(MOUTH + AXIS * 0.3), "root")}


def _ring_on_axis(bm, t, r, w, depth=0.06):
    tmp = bmesh.new()
    ring(tmp, (0, 0, 0), r, r - w, -depth, depth, seg=16)
    q = Vector((0, 0, 1)).rotation_difference(AXIS)
    bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(tmp, verts=tmp.verts, vec=PIVOT + AXIS * t)
    me = bpy.data.meshes.new("_t"); tmp.to_mesh(me); tmp.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)


def build_head():
    col = collection("Doom_cannon")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rot = tuple(math.degrees(x) for x in AXIS.to_track_quat("Z", "Y").to_euler())
    # the sled: a round turning plate and two long cheek plates that cradle the trunnions
    bm = bmesh.new()
    bm_cyl(bm, 1.0, 1.0, 0.12, (0, 0, 0.06), seg=20)
    for sx in (-1, 1):
        vs = [Vector((sx * 0.5, -1.05, 0.12)), Vector((sx * 0.5, 0.85, 0.12)), Vector((sx * 0.5, 0.45, 0.95)), Vector((sx * 0.5, -0.55, 0.85))]
        for off in (-0.07, 0.07):
            bvs = [bm.verts.new(v + Vector((off, 0, 0))) for v in vs]
            bm.faces.new(bvs if off * sx > 0 else list(reversed(bvs)))
        for a, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
            p = [vs[a] + Vector((-0.07, 0, 0)), vs[b_] + Vector((-0.07, 0, 0)), vs[b_] + Vector((0.07, 0, 0)), vs[a] + Vector((0.07, 0, 0))]
            bvs = [bm.verts.new(v) for v in p]
            bm.faces.new(bvs if sx > 0 else list(reversed(bvs)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm_box(bm, (1.1, 0.16, 0.12), (0, -0.95, 0.2))
    bm_box(bm, (1.1, 0.16, 0.12), (0, 0.72, 0.2))
    rig_part("Head_Sled", bm, "iron", rig, "sled", col, bevel=0, lo=0.05, hi=0.6)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_cyl(bm, 0.13, 0.13, 0.22, (sx * 0.56, PIVOT.y, PIVOT.z), rot=(0, 90, 0), seg=10)
        for y in (-0.8, -0.2, 0.45):
            bm_cyl(bm, 0.04, 0.04, 0.18, (sx * 0.5, y, 0.3), rot=(0, 90, 0), seg=6)
    rig_part("Head_Studs", bm, "gold", rig, "sled", col, bevel=0, lo=0.1, hi=0.5)
    # the elevation wheel on the right cheek
    bm = bmesh.new()
    W = Vector((0.66, -0.25, 0.62))
    ring(bm, tuple(W), 0.26, 0.2, -0.03, 0.03, seg=14, axis="X")
    for k in range(4):
        a = math.radians(45 * k)
        bm_box(bm, (0.04, 0.46, 0.04), tuple(W), rot=(math.degrees(a), 0, 0))
    bm_cyl(bm, 0.06, 0.06, 0.12, tuple(W), rot=(0, 90, 0), seg=8)
    rig_part("Head_Wheel", bm, "wood_dark", rig, "wheel", col, bevel=0, lo=0.2, hi=0.7)
    # the barrel: a long tapered iron tube, cascabel ball at the breech, flared bronze mouth
    bm = bmesh.new()
    mid = (BREECH + MOUTH) * 0.5
    bm_cyl(bm, 0.47, 0.32, (MOUTH - BREECH).length - 0.25, tuple(mid - AXIS * 0.12), rot=rot, seg=16)
    bm_ellipsoid(bm, tuple(BREECH), (0.46, 0.46, 0.4), rot=rot, u=14, v=8)
    bm_ellipsoid(bm, tuple(BREECH - AXIS * 0.5), (0.14, 0.14, 0.14), u=10, v=6)
    bm_beam(bm, BREECH - AXIS * 0.3, BREECH - AXIS * 0.46, 0.1, 0.1)
    rig_part("Head_Barrel", bm, "iron", rig, "barrel", col, bevel=0, lo=0.05, hi=0.45)
    bm = bmesh.new()
    bm_cyl(bm, 0.32, 0.5, 0.46, tuple(MOUTH - AXIS * 0.22), rot=rot, seg=16)
    _ring_on_axis(bm, (MOUTH - PIVOT).length - 0.52, 0.38, 0.07, 0.05)
    rig_part("Head_Mouth", bm, "gold", rig, "barrel", col, bevel=0, lo=0.15, hi=0.6)
    bm = bmesh.new()
    for t, r in ((-0.72, 0.5), (0.42, 0.44), (1.45, 0.4)):
        _ring_on_axis(bm, t, r, 0.08, 0.045)
    rig_part("Head_Bands", bm, "gold", rig, "barrel", col, bevel=0, lo=0.1, hi=0.55)
    bm = bmesh.new()
    _ring_on_axis(bm, -0.15, 0.47, 0.05, 0.03)
    _ring_on_axis(bm, 0.95, 0.42, 0.05, 0.03)
    rig_part("Head_Runes", bm, None, rig, "barrel", col, bevel=0, mat=glow_mat("doom_rune", EMBER, 1.6))
    bm = bmesh.new()
    bm_cyl(bm, 0.4, 0.4, 0.04, tuple(MOUTH + AXIS * 0.005), rot=rot, seg=14)
    rig_part("Head_Bore", bm, "black", rig, "barrel", col, bevel=0, lo=0.3, hi=0.6)
    # smoke: a ring of puffs round the mouth, hidden (scale 0) until it fires
    bm = bmesh.new()
    rnd = random.Random(9)
    q = Vector((0, 0, 1)).rotation_difference(AXIS)
    for k in range(9):
        a = 2 * math.pi * k / 9
        off = q @ Vector((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.0))
        bm_ellipsoid(bm, tuple(MOUTH + AXIS * (0.25 + rnd.uniform(0, 0.2)) + off), (0.2, 0.2, 0.17), u=7, v=5)
    for k in range(4):
        bm_ellipsoid(bm, tuple(MOUTH + AXIS * (0.5 + k * 0.28) + Vector((rnd.uniform(-0.12, 0.12), 0, rnd.uniform(0, 0.12)))),
                     (0.22 + k * 0.04,) * 2 + (0.19 + k * 0.03,), u=7, v=5)
    rig_part("Head_Smoke", bm, "stone2", rig, "smoke", col, bevel=0, lo=0.05, hi=0.4)
    empty("Muzzle", col, head, tuple(MOUTH + AXIS * 0.1), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 40


def pose(rig, recoil=0.0, jolt=0.0, smoke=0.0, drift=0.0, wheel=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["barrel"].location = arm_space_loc(pb["barrel"], tuple(-AXIS * recoil * 0.45))
    pb["barrel"].rotation_quaternion = arm_space_quat(pb["barrel"], (1, 0, 0), recoil * 4)
    pb["sled"].location = arm_space_loc(pb["sled"], (0, -jolt * 0.1, 0))
    pb["wheel"].rotation_quaternion = arm_space_quat(pb["wheel"], (1, 0, 0), wheel)
    pb["smoke"].scale = (max(smoke, 0.001),) * 3
    pb["smoke"].location = arm_space_loc(pb["smoke"], tuple(AXIS * drift))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, wheel=360 * f / IDLE_LEN * 0.25, recoil=0.015 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rc = smooth(f / 1.5) * (1 - smooth((f - 4) / 24.0))
        jolt = smooth(f / 2.0) * (1 - smooth((f - 3) / 12.0))
        sm = 0.0 if f < 1 else 1.1 * smooth((f - 1) / 5.0) * (1 - smooth((f - 16) / 22.0))
        pose(rig, recoil=rc, jolt=jolt, smoke=sm, drift=1.1 * smooth(f / FIRE_LEN), wheel=-40 * rc)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 11.0, "yaw": 150, "pitch": 22, "anim_target": (0, 0.8, 1.1), "anim_dist": 6.5,
           "frames": [("idle", 0), ("fire", 3), ("fire", 14)]}


def build_all():
    build_base()
    build_head()
    build_anims()
