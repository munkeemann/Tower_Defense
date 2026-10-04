"""Builds the Coral Harpooner (footprint "line3": [0,0] front, [0,1] middle, [0,2] back; a 60 degree arc), a Tide
tower: barbed harpoons pierce a whole line and slow what they hit.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mer_harpoon <preview dir>

Front cell: a coral-rimmed stone basin of seawater where a bald, grey-bearded merman (the pack's Barbarian turned
sea-folk: a teal tail, team-coloured fins) rises with a barbed harpoon (the Head: he turns to aim; it leaves from his
throwing hand). Middle: a rack of spare harpoons, a coil of rope and a keg. Back: a giant open clam with a glowing pearl,
coral, kelp and an old anchor. idle: he breathes and his tail sways in the water. fire: he hurls the harpoon (the wind-up
trimmed, so it leaves as the clip starts) and a new one is in his hand by the end.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())
exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "mer_harpoon"
CELLS = [(0, 0), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
M = hex_to_world(0, 1, MID)
B = hex_to_world(0, 2, MID)
TOP = 0.34
WATER = TOP + 0.22
PEARL = (0.75, 0.95, 1.0)
CHAR = "Barbarian.glb"
HEIGHT = 1.6


def build_base():
    col = collection("Mer_harpoon")
    root = empty("Mer_harpoon", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(41)
    # the front basin: a stone ring holding seawater, coral on its rim
    bm = bmesh.new()
    ring(bm, (F.x, F.y, 0), 0.9, 0.72, T - 0.01, WATER + 0.06, seg=12)
    o = paint(mesh_obj("Basin", bm, col, root), "stone2", lo=0.15, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.74, 0.74, 0.04, (F.x, F.y, WATER - 0.02), seg=12)
    paint_water(mesh_obj("Basin_Water", bm, col, root))
    coral, coral2 = bmesh.new(), bmesh.new()
    for k, a in enumerate((35, 150, 260)):
        p = F + Vector((math.cos(math.radians(a)) * 0.82, math.sin(math.radians(a)) * 0.8, 0))
        bm_coral(coral if k % 2 == 0 else coral2, rnd, (p.x, p.y, WATER + 0.04), h=rnd.uniform(0.45, 0.6), n=4)
    paint(mesh_obj("Coral_A", coral, col, root), "salmon", lo=0.1, hi=0.7)
    paint(mesh_obj("Coral_B", coral2, col, root), "orange", lo=0.1, hi=0.7)
    # middle: a harpoon rack, a coil of rope, a keg
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.09, 0.09, 1.05), (M.x + sx * 0.5, M.y + 0.25, T + 0.52))
    bm_box(bm, (1.15, 0.1, 0.08), (M.x, M.y + 0.25, T + 0.98))
    bm_box(bm, (1.15, 0.08, 0.06), (M.x, M.y + 0.25, T + 0.3))
    paint(mesh_obj("Rack", bm, col, root), "wood", lo=0.3, hi=0.8)
    shafts, heads = bmesh.new(), bmesh.new()
    for k in range(4):
        x = M.x - 0.36 + k * 0.24
        b0 = Vector((x, M.y + 0.05, T + 0.02))
        tip = Vector((x + 0.03, M.y + 0.33, T + 1.25))
        d = (tip - b0).normalized()
        bm_beam(shafts, b0, tip, 0.035, 0.035)
        bm_beam(heads, tip, tip + d * 0.2, 0.065, 0.065, w1=0.0, h1=0.0)
        for sg in (-1, 1):
            bm_beam(heads, tip + d * 0.05, tip - d * 0.06 + Vector((sg * 0.06, 0, 0)), 0.025, 0.02, w1=0.0, h1=0.0)
    paint(mesh_obj("Rack_Harpoons", shafts, col, root), "wood", lo=0.2, hi=0.6)
    paint(mesh_obj("Rack_Heads", heads, col, root), "iron", lo=0.05, hi=0.5)
    bm = bmesh.new()
    for k in range(4):
        ring(bm, (M.x + 0.45, M.y - 0.45, 0), 0.24 - 0.02 * k, 0.12, T + 0.04 * k, T + 0.04 * k + 0.045, seg=12)
    paint(mesh_obj("Rope", bm, col, root), "sand", lo=0.2, hi=0.6)
    # back: the clam and its pearl, coral, kelp, an anchor
    shell, inner = bmesh.new(), bmesh.new()
    pearl_at = bm_clam(shell, inner, (B.x - 0.2, B.y + 0.05, T), size=0.55, yaw=15)
    paint(mesh_obj("Clam_Shell", shell, col, root), "cream", lo=0.15, hi=0.75)
    paint(mesh_obj("Clam_Inner", inner, col, root), "salmon", lo=0.5, hi=0.8)
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(pearl_at), (0.13, 0.13, 0.13), u=10, v=7)
    glow_obj("Clam_Pearl", bm, col, root, PEARL, 0.7)
    coral = bmesh.new()
    bm_coral(coral, rnd, (B.x + 0.6, B.y - 0.35, T), h=0.7, n=5)
    paint(mesh_obj("Coral_C", coral, col, root), "red", lo=0.15, hi=0.7)
    bm = bmesh.new()
    bm_kelp(bm, rnd, (B.x - 0.65, B.y - 0.45, T), h=0.9, n=3)
    bm_kelp(bm, rnd, (M.x - 0.6, M.y - 0.5, T), h=0.6, n=2)
    paint(mesh_obj("Kelp", bm, col, root), "teal", lo=0.1, hi=0.8)
    bm = bmesh.new()
    bm_conch(bm, (B.x + 0.45, B.y + 0.55, T), length=0.38, yaw=40)
    paint(mesh_obj("Conch", bm, col, root), "cream", lo=0.3, hi=0.8)
    for i, (rel, loc, rot, sc) in enumerate((("dungeon/barrel_large", (M.x - 0.5, M.y - 0.3, T), 20, 0.3),
                                              ("hex/anchor", (B.x + 0.3, B.y + 0.05, T), 70, 1.0))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (F.x, F.y - 0.05, WATER), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Mer_harpoon")
    head = bpy.data.objects["Head"]
    arm = make_merfolk(CHAR, col, head, HEIGHT, hover=0.0, drop=("BearHat",), skin=(0.42, 0.7, 0.62),
                       tail=[(0, 0.02, -0.04), (0, -0.08, -0.26), (0.06, -0.3, -0.3), (0.16, -0.5, -0.1)],
                       tail_sw="teal", fin_sw="team", weapon=(0.5, 1.05), pose_clip="Idle_B")
    rs = bone_world(arm, "upperarm.r")
    m = head.matrix_world.inverted() @ (rs + Vector((0.0, 0.3, 0.3)))
    empty("Muzzle", col, head, tuple(m), 0.25, "SPHERE")
    return arm


def build_anims():
    # the throw's wind-up is trimmed, so the harpoon leaves on the first frames (the game fires as the clip starts)
    merfolk_anims(bpy.data.objects["Rig"], "Idle_B", "Throw", idle_len=60, fire_len=24, fire_start=0.32, fire_speed=0.68,
                  hide=(3, 14, 22))


PREVIEW = {"target": (0, -0.2, 0.9), "dist": 9.0, "yaw": 160, "pitch": 18, "anim_target": (0, F.y, 1.0), "anim_dist": 4.2,
           "frames": [("idle", 0), ("idle", 30), ("fire", 2), ("fire", 8), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
