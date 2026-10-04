"""Builds the Hall of Knights (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), the Crown's Tier IV
tower: it musters knights who march out onto the road and pin the foe.

    blender -b --factory-startup --python tools/blender/build_tower.py -- knight_hall <preview dir>

Front cell: a stone gatehouse with an arched gate of oak doors, flanked by two round towers with team cone roofs and
hung with team banners; on its battlements stands the knight-commander (the Head carries the Crew: he turns to face the
foe and raises his sword at every muster). Back cells: the knights' barracks and their stables (KayKit buildings), with
a training yard between them: a weapon rack and a straw target. idle: the banners stir. fire (every muster): the
gate doors swing open and shut again, the banners snap.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "knight_hall"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
R = hex_to_world(1, 0, MID)
L = hex_to_world(-1, 1, MID)
TOP = 0.34
T = TOP
GH = 1.05                     # gatehouse height above the plinth
GW, GD = 1.25, 0.95           # its width and depth
GY = F.y - 0.05               # its middle
ARCH_W, ARCH_H = 0.46, 0.62


def build_base():
    col = collection("Knight_hall")
    root = empty("Knight_hall", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    # paving: flagstones in front of the gate and across the yard
    rnd = random.Random(5)
    bm = bmesh.new()
    for k in range(16):
        p = Vector((rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, -0.2), 0)) if k < 9 else Vector((F.x + rnd.uniform(-0.55, 0.55), F.y + rnd.uniform(0.5, 0.85), 0))
        bm_box(bm, (rnd.uniform(0.22, 0.32), rnd.uniform(0.18, 0.28), 0.03), (p.x, p.y, T + 0.015), rot=(0, 0, rnd.uniform(0, 40)))
    paint(mesh_obj("Yard_Flags", bm, col, root), "stone2", lo=0.25, hi=0.75)
    # the gatehouse: a stone block, an arched gate (dark recess) facing +Y, a crenellated parapet
    bm = bmesh.new()
    bm_box(bm, (GW, GD, GH), (F.x, GY, T + GH / 2))
    o = paint(mesh_obj("Gate_House", bm, col, root), "stone", lo=0.1, hi=0.65)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for k in range(5):
        x = -GW / 2 + 0.1 + k * (GW - 0.2) / 4
        for y in (GY - GD / 2 + 0.06, GY + GD / 2 - 0.06):
            bm_box(bm, (0.14, 0.12, 0.16), (F.x + x, y, T + GH + 0.08))
    for y in (GY - 0.16, GY + 0.16):
        for x in (-GW / 2 + 0.06, GW / 2 - 0.06):
            bm_box(bm, (0.12, 0.14, 0.16), (F.x + x, y, T + GH + 0.08))
    bm_box(bm, (GW + 0.06, GD + 0.06, 0.06), (F.x, GY, T + GH - 0.03))
    o = paint(mesh_obj("Gate_Parapet", bm, col, root), "stone2", lo=0.15, hi=0.6)
    bm = bmesh.new()                                         # the arch: a dark recess with a round top
    yf = GY + GD / 2 + 0.005
    bm_box(bm, (ARCH_W, 0.03, ARCH_H - ARCH_W / 2), (F.x, yf, T + (ARCH_H - ARCH_W / 2) / 2))
    bm_cyl(bm, ARCH_W / 2, ARCH_W / 2, 0.03, (F.x, yf, T + ARCH_H - ARCH_W / 2), rot=(90, 0, 0), seg=12)
    paint(mesh_obj("Gate_Dark", bm, col, root), "black", lo=0.3, hi=0.6)
    bm = bmesh.new()                                         # voussoir stones round the arch
    for k in range(7):
        a = math.pi * k / 6
        p = Vector((F.x + math.cos(a) * (ARCH_W / 2 + 0.06), yf + 0.02, T + ARCH_H - ARCH_W / 2 + math.sin(a) * (ARCH_W / 2 + 0.06)))
        bm_box(bm, (0.1, 0.05, 0.12), tuple(p), rot=(0, -math.degrees(a) + 90, 0))
    paint(mesh_obj("Gate_Arch", bm, col, root), "stone_warm", lo=0.2, hi=0.7)
    # flanking towers with team cone roofs
    for i, sx in enumerate((-1, 1)):
        c = Vector((F.x + sx * (GW / 2 + 0.05), GY + 0.12, 0))
        bm = bmesh.new()
        bm_cyl(bm, 0.3, 0.33, GH + 0.45, (c.x, c.y, T + (GH + 0.45) / 2), seg=12)
        o = paint(mesh_obj("Gate_Tower_%d" % i, bm, col, root), "stone", lo=0.1, hi=0.65)
        bm = bmesh.new()
        bm_cyl(bm, 0.37, 0.0, 0.55, (c.x, c.y, T + GH + 0.45 + 0.275), seg=12)
        paint(mesh_obj("Gate_TowerRoof_%d" % i, bm, col, root), "team", team=True, lo=0.15, hi=0.65)
        bm = bmesh.new()
        bm_box(bm, (0.08, 0.04, 0.2), (c.x + sx * 0.0, c.y + 0.31, T + GH + 0.1))
        paint(mesh_obj("Gate_TowerSlit_%d" % i, bm, col, root), "black", lo=0.3, hi=0.6)
        bm = bmesh.new()
        bm_cyl(bm, 0.012, 0.012, 0.3, (c.x, c.y, T + GH + 1.1), seg=5)
        paint(mesh_obj("Gate_TowerSpike_%d" % i, bm, col, root), "gold", lo=0.2, hi=0.6)
    # the training yard and the back-cell buildings (KayKit, in the Crown's color)
    kk = [("hex/building_barracks_yellow", (L.x - 0.05, L.y - 0.05, T), 60, 0.82),
          ("hex/building_stables_yellow", (R.x + 0.05, R.y - 0.05, T), -60, 0.82),
          ("hex/weaponrack", (-0.55, -0.55, T), 200, 2.3),
          ("hex/target", (0.6, -0.62, T), 160, 2.4),
          ("hex/haybale", (R.x + 0.55, R.y + 0.62, T), 20, 1.3)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (F.x, GY - 0.02, T + GH), 0.5, "SINGLE_ARROW")
    empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.35, 1.0), 0.2, "SPHERE")      # (the commander's raised sword)
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "door.l": ((F.x - ARCH_W / 2, GY + GD / 2 + 0.03, T), (F.x - ARCH_W / 2, GY + GD / 2 + 0.03, T + 0.3), "root"),
         "door.r": ((F.x + ARCH_W / 2, GY + GD / 2 + 0.03, T), (F.x + ARCH_W / 2, GY + GD / 2 + 0.03, T + 0.3), "root"),
         "banner.l": ((F.x - 0.42, GY + GD / 2 + 0.05, T + GH - 0.05), (F.x - 0.42, GY + GD / 2 + 0.05, T + GH - 0.3), "root"),
         "banner.r": ((F.x + 0.42, GY + GD / 2 + 0.05, T + GH - 0.05), (F.x + 0.42, GY + GD / 2 + 0.05, T + GH - 0.3), "root")}


def build_rig():
    col = collection("Knight_hall")
    root = bpy.data.objects["Knight_hall"]
    rig = make_rig(col, root, BONES)
    # the gate: two oak doors with iron bands, hinged at the sides of the arch; they swing open at every muster
    yf = GY + GD / 2 + 0.03
    dh = ARCH_H - ARCH_W / 2 + 0.02
    for side, sx in (("l", -1), ("r", 1)):
        hx = F.x + sx * ARCH_W / 2
        bm = bmesh.new()
        bm_box(bm, (ARCH_W / 2 - 0.015, 0.04, dh), (hx - sx * (ARCH_W / 4), yf, T + dh / 2))
        rig_part("Gate_Door_%s" % side, bm, "wood_dark", rig, "door." + side, col, bevel=0, lo=0.2, hi=0.75)
        bm = bmesh.new()
        for z in (0.1, dh - 0.12):
            bm_box(bm, (ARCH_W / 2 - 0.03, 0.055, 0.04), (hx - sx * (ARCH_W / 4), yf, T + z))
        bm_cyl(bm, 0.025, 0.025, 0.02, (hx - sx * (ARCH_W / 2 - 0.06), yf + 0.03, T + dh * 0.5), rot=(90, 0, 0), seg=8)
        rig_part("Gate_Door_%s_Iron" % side, bm, "iron", rig, "door." + side, col, bevel=0, lo=0.1, hi=0.45)
    # two team banners hanging either side of the gate, each from a gold rod
    for side, sx in (("l", -1), ("r", 1)):
        x = F.x + sx * 0.42
        y = GY + GD / 2 + 0.05
        bm = bmesh.new()
        top, bot = T + GH - 0.05, T + 0.3
        vs = [bm.verts.new(p) for p in ((x - 0.13, y, top), (x + 0.13, y, top), (x + 0.13, y, bot + 0.08), (x, y, bot), (x - 0.13, y, bot + 0.08))]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
        rig_part("Banner_%s" % side, bm, "team", rig, "banner." + side, col, team=True, bevel=0, lo=0.15, hi=0.6)
        bm = bmesh.new()
        bm_ellipsoid(bm, (x, y + 0.02, (top + bot) / 2 + 0.05), (0.07, 0.015, 0.07), u=8, v=4)
        bm_cyl(bm, 0.015, 0.015, 0.32, (x, y, top + 0.01), rot=(0, 90, 0), seg=6)
        rig_part("Banner_%s_Crest" % side, bm, "gold", rig, "banner." + side, col, bevel=0, lo=0.15, hi=0.6)
    return rig


IDLE_LEN = 96
FIRE_LEN = 30


def pose(rig, t=0.0, lift=0.0, snap=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["door.l"].rotation_quaternion = arm_space_quat(pb["door.l"], (0, 0, 1), 105 * lift)  # (outward)
    pb["door.r"].rotation_quaternion = arm_space_quat(pb["door.r"], (0, 0, 1), -105 * lift)
    for i, side in enumerate(("l", "r")):
        sw = 4 * math.sin(2 * math.pi * (t * 2 + 0.3 * i)) + snap * (14 if i == 0 else -14)
        pb["banner." + side].rotation_quaternion = arm_space_quat(pb["banner." + side], (1, 0, 0), -abs(sw) * 0.6 - 2)
        pb["banner." + side].rotation_quaternion = arm_space_quat(pb["banner." + side], (0, 1, 0), sw * 0.6) @ \
            pb["banner." + side].rotation_quaternion


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        lift = smooth(f / 6.0) * (1 - smooth((f - 16) / 12.0))
        snap = math.sin(f * 0.6) * (1 - f / FIRE_LEN)
        pose(rig, t=0.0, lift=lift, snap=snap)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 9.5, "yaw": 160, "pitch": 22, "anim_target": (F.x, GY + 0.4, T + 0.6), "anim_dist": 3.6,
           "frames": [("idle", 0), ("fire", 8), ("fire", 16)]}


def build_all():
    build_base()
    build_rig()
    build_anims()
