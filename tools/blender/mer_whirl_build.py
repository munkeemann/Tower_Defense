"""Builds the Whirlpool Shrine (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Tide tower: a
swirling vortex that drags ground enemies back along the road.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mer_whirl <preview dir>

Front cell: a stone basin whose water turns in a whirlpool: three spiral arms of foam round a dark eye ringed with
light. Back-left: a shrine of two coral pillars under a great scallop canopy, a glowing pearl on its altar. Back-right:
standing stones with glowing tide-runes, kelp and a clam. It's an aura (it doesn't turn). idle: the whirlpool turns,
its eye pulsing. fire (every pulse): it spins hard and a spout of water bursts up from the eye and falls back.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "mer_whirl"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
WATER = TOP + 0.14
TIDE = (0.55, 0.85, 1.0)
PEARL = (0.7, 0.95, 1.0)


def build_base():
    col = collection("Mer_whirl")
    root = empty("Mer_whirl", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(73)
    # the basin and its water
    bm = bmesh.new()
    ring(bm, (F.x, F.y, 0), 1.02, 0.86, T - 0.01, WATER + 0.08, seg=14)
    o = paint(mesh_obj("Basin", bm, col, root), "stone2", lo=0.15, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.88, 0.88, 0.04, (F.x, F.y, WATER - 0.02), seg=14)
    paint_water(mesh_obj("Basin_Water", bm, col, root))
    coral = bmesh.new()
    for a in (200, 320):
        p = F + Vector((math.cos(math.radians(a)) * 0.95, math.sin(math.radians(a)) * 0.95, 0))
        bm_coral(coral, rnd, (p.x, p.y, WATER + 0.06), h=0.5, n=4)
    paint(mesh_obj("Coral_A", coral, col, root), "salmon", lo=0.1, hi=0.7)
    # back-left: the scallop shrine
    c = BL + Vector((0.12, 0.05, 0))
    pil, canopy, altar = bmesh.new(), bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        for k in range(6):
            r = 0.15 - 0.012 * k
            p = c + Vector((sx * 0.48, 0.15, 0))
            bm_ellipsoid(pil, (p.x + 0.02 * math.sin(k * 1.7), p.y, T + 0.1 + k * 0.19), (r, r, 0.13), rot=(0, 0, 30 * k), u=7, v=4)
    hinge = c + Vector((0, -0.25, 1.22))
    fan_pts = []
    for k in range(9):
        a = math.radians(-70 + 17.5 * k)
        tip = hinge + Vector((math.sin(a) * 0.82, 0.45 + math.cos(a) * 0.25, math.cos(a) * 0.35))
        fan_pts.append(tip)
        bm_beam(canopy, hinge, tip, 0.04, 0.05, w1=0.09, h1=0.05)
    for off in (-0.012, 0.012):
        h_v = canopy.verts.new(hinge + Vector((0, 0, off)))
        vs = [canopy.verts.new(p + Vector((0, 0, off))) for p in fan_pts]
        for i in range(len(vs) - 1):
            tri = (h_v, vs[i], vs[i + 1])
            canopy.faces.new(tri if off > 0 else tuple(reversed(tri)))
    bm_box(altar, (0.55, 0.36, 0.32), (c.x, c.y + 0.1, T + 0.16))
    bm_box(altar, (0.62, 0.42, 0.06), (c.x, c.y + 0.1, T + 0.35))
    paint(mesh_obj("Shrine_Pillars", pil, col, root), "salmon", lo=0.15, hi=0.75)
    paint(mesh_obj("Shrine_Canopy", canopy, col, root), "cream", lo=0.15, hi=0.7)
    paint(mesh_obj("Shrine_Altar", altar, col, root), "stone2", lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (c.x, c.y + 0.1, T + 0.48), (0.1, 0.1, 0.1), u=9, v=6)
    glow_obj("Shrine_Pearl", bm, col, root, PEARL, 0.8)
    # back-right: standing stones with glowing runes
    stones, runes = bmesh.new(), bmesh.new()
    for k, (dx, dy, h, tilt) in enumerate(((-0.45, 0.2, 1.05, -5), (0.15, 0.4, 1.3, 3), (0.55, -0.25, 0.9, 6))):
        p = BR + Vector((dx, dy, 0))
        bm_box(stones, (0.3, 0.22, h), (p.x, p.y, T + h / 2 - 0.02), (tilt, -tilt * 0.5, 15 * k))
        for j in range(2):
            bm_box(runes, (0.12, 0.02, 0.07), (p.x, p.y + 0.115, T + h * (0.45 + 0.25 * j)), (tilt, 0, 15 * k))
    paint(mesh_obj("Stones", stones, col, root), "stone2", lo=0.1, hi=0.7)
    glow_obj("Stones_Runes", runes, col, root, TIDE, 0.8)
    bm = bmesh.new()
    bm_kelp(bm, rnd, (BR.x - 0.6, BR.y - 0.45, T), h=0.8, n=3)
    bm_kelp(bm, rnd, (BL.x - 0.55, BL.y - 0.5, T), h=0.6, n=2)
    paint(mesh_obj("Kelp", bm, col, root), "teal", lo=0.1, hi=0.8)
    shell, inner = bmesh.new(), bmesh.new()
    bm_clam(shell, inner, (BR.x + 0.5, BR.y + 0.45, T), size=0.3, yaw=-30)
    paint(mesh_obj("Clam_Shell", shell, col, root), "cream", lo=0.15, hi=0.75)
    paint(mesh_obj("Clam_Inner", inner, col, root), "salmon", lo=0.5, hi=0.8)
    empty("Head", col, root, (F.x, F.y, WATER), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "vortex": ((0, 0, 0), (0, 0, 0.2), "root"),
         "eye": ((0, 0, 0.01), (0, 0, 0.2), "root"),
         "spout": ((0, 0, 0), (0, 0, 0.3), "root")}


def build_head():
    col = collection("Mer_whirl")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    foam = bmesh.new()
    for j in range(3):                                   # three spiral arms of foam, winding in to the eye
        th0 = math.radians(120 * j)
        pts = []
        for i in range(14):
            t = i / 13
            r = 0.82 * (1 - t) + 0.2 * t
            th = th0 + t * math.radians(320)
            pts.append(Vector((math.cos(th) * r, math.sin(th) * r, 0.025 + 0.02 * t)))
        for i in range(13):
            w = 0.15 * (1 - i / 13) + 0.05
            bm_beam(foam, pts[i], pts[i + 1], w, 0.035, w1=w * 0.9, h1=0.03)
    rig_part("Head_Foam", foam, "white", rig, "vortex", col, bevel=0, lo=0.05, hi=0.4)
    bm = bmesh.new()
    bm_cyl(bm, 0.24, 0.24, 0.02, (0, 0, 0.01), seg=12)
    rig_part("Head_EyeDark", bm, "blue", rig, "vortex", col, bevel=0, lo=0.85, hi=0.95)
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.3, 0.23, 0.015, 0.04, seg=16)
    rig_part("Head_EyeRing", bm, None, rig, "eye", col, bevel=0, mat=glow_mat("whirl_eye", TIDE, 0.8))
    bm = bmesh.new()
    bm_cyl(bm, 0.24, 0.13, 1.5, (0, 0, 0.75), seg=10)
    for k in range(3):
        ring(bm, (0, 0, 0), 0.3 - 0.04 * k, 0.18 - 0.03 * k, 0.35 + 0.4 * k, 0.43 + 0.4 * k, seg=10)
    for k in range(6):
        a = math.radians(60 * k)
        bm_ellipsoid(bm, (math.cos(a) * 0.14, math.sin(a) * 0.14, 1.5), (0.12, 0.12, 0.09), u=6, v=4)
    rig_part("Head_Spout", bm, None, rig, "spout", col, bevel=0, mat=glow_mat("whirl_spout", TIDE, 0.5))
    empty("Muzzle", col, head, (0, 0, 0.3), 0.25, "SPHERE")
    return rig


IDLE_LEN = 48
FIRE_LEN = 26


def pose(rig, spin=0.0, eye=1.0, spout=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["vortex"].rotation_quaternion = arm_space_quat(pb["vortex"], (0, 0, 1), -spin)
    pb["eye"].scale = (eye, 1.0, eye)                  # (these bones point up: their own Y is the height)
    w = max(0.001, (0.6 + 0.4 * spout) if spout > 0.001 else 0.001)
    pb["spout"].scale = (w, max(0.001, spout), w)
    pb["spout"].rotation_quaternion = arm_space_quat(pb["spout"], (0, 0, 1), -spin * 1.5)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, spin=360 * t, eye=1.0 + 0.12 * math.sin(2 * math.pi * t * 2))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = f / FIRE_LEN
        sp = smooth(f / 4.0) * (1 - smooth((f - 12) / 12.0))
        pose(rig, spin=720 * smooth(t), eye=1.0 + 0.6 * smooth(f / 3.0) * (1 - smooth((f - 8) / 12.0)), spout=sp)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 9.0, "yaw": 160, "pitch": 24, "anim_target": (F.x, F.y, 0.9), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 12), ("fire", 5), ("fire", 12), ("fire", 22)]}


def build_all():
    build_base()
    build_head()
    build_anims()
