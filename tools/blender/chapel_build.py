"""Builds the Chapel of Dawn (footprint "fan4": [0,0] the back cell, [0,-1] front, [-1,0] front-left, [1,-1] front-right).

    blender -b --factory-startup --python tools/blender/build_tower.py -- chapel <preview dir>

Back cell: a stone nave with buttresses, stained-glass windows, a rose window and a team-colored gabled roof.
Front cell: the bell tower (open belfry, team pyramid roof) crowned by a golden sunburst. Front-left: a paladin statue on
a pedestal with candles. Front-right: a holy brazier, where the game stands a praying paladin (Crew). It's an aura tower,
so the head doesn't aim: the rig carries the bell, the sun and a flash ring. idle: the sun turns slowly, the bell barely
stirs. fire (every pulse): the bell swings, the sun flares, a ring of light bursts outward.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "chapel"
CELLS = [(0, 0), (0, -1), (-1, 0), (1, -1)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FRONT = hex_to_world(0, -1, MID)
FL = hex_to_world(-1, 0, MID)
FR = hex_to_world(1, -1, MID)
TOP = 0.34
GOLD = (1.0, 0.78, 0.3)
GLOW = 1.2

NAVE_Y0 = BACK.y - 0.78
NAVE_W = 1.36
WALL_TOP = 1.5
RIDGE = 2.25
TW = 0.96                     # bell tower width
TOWER_Y = FRONT.y + 0.12
NAVE_Y1 = TOWER_Y - TW / 2 + 0.02     # the nave runs into the tower
SHAFT_TOP = 2.6
BELFRY_TOP = 3.3
APEX = 4.05


def _gable_roof(bm, x_half, y0, y1, eave_z, ridge_z, overhang=0.16, n=6, th=0.07):
    """Plank roof: two slopes from the ridge (along Y) down to eaves at +-x_half, n planks per slope."""
    import random
    rnd = random.Random(11)
    span = (y1 - y0) + 2 * overhang
    w = span / n
    for sx in (-1, 1):
        for i in range(n):
            y = y0 - overhang + w * (i + 0.5)
            drop = rnd.uniform(-0.03, 0.05)
            top = Vector((sx * 0.02, y, ridge_z))
            low = Vector((sx * (x_half + overhang + drop), y, eave_z - (overhang + drop) * (ridge_z - eave_z) / x_half))
            bm_beam(bm, top, low, w - 0.02, th, up=(sx * 0.6, 0, 1))


def build_base():
    col = collection("Chapel")
    root = empty("Chapel", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    # paving between the buildings: a ring of flagstones in the courtyard cells
    import random
    rnd = random.Random(3)
    bm = bmesh.new()
    for c in (FL, FR):
        for i in range(9):
            a = math.radians(40 * i + rnd.uniform(-8, 8))
            r = rnd.uniform(0.35, 0.75)
            p = c + Vector((math.cos(a) * r, math.sin(a) * r, 0))
            bm_box(bm, (rnd.uniform(0.22, 0.32), rnd.uniform(0.18, 0.26), 0.03), (p.x, p.y, TOP + 0.015), (0, 0, rnd.uniform(0, 90)))
    paint(mesh_obj("Court_Flags", bm, col, root), "stone2", lo=0.15, hi=0.45)

    # ---- the nave
    bm = bmesh.new()
    bm_box(bm, (NAVE_W, NAVE_Y1 - NAVE_Y0, WALL_TOP - TOP), (0, (NAVE_Y0 + NAVE_Y1) / 2, (TOP + WALL_TOP) / 2))
    # back gable
    hw = NAVE_W / 2
    vs = [bm.verts.new(v) for v in ((-hw, NAVE_Y0, WALL_TOP), (hw, NAVE_Y0, WALL_TOP), (0, NAVE_Y0, RIDGE - 0.05))]
    bm.faces.new((vs[0], vs[1], vs[2]))
    vs2 = [bm.verts.new(v.co + Vector((0, 0.3, 0))) for v in vs]
    bm.faces.new((vs2[1], vs2[0], vs2[2]))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((vs2[i], vs2[j], vs[j], vs[i]))
    o = paint(mesh_obj("Nave_Walls", bm, col, root), "stone", lo=0.05, hi=0.65)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for sx in (-1, 1):
        for k in range(4):
            y = NAVE_Y0 + 0.12 + k * (NAVE_Y1 - NAVE_Y0 - 0.24) / 3
            bm_beam(bm, (sx * (hw + 0.1), y, TOP), (sx * (hw + 0.02), y, WALL_TOP - 0.15), 0.2, 0.16, w1=0.14, h1=0.12,
                    up=(0, 1, 0))
        bm_box(bm, (0.08, NAVE_Y1 - NAVE_Y0 + 0.04, 0.1), (sx * (hw + 0.02), (NAVE_Y0 + NAVE_Y1) / 2, WALL_TOP - 0.04))
    bm_box(bm, (NAVE_W + 0.16, NAVE_Y1 - NAVE_Y0 + 0.16, 0.14), (0, (NAVE_Y0 + NAVE_Y1) / 2, TOP + 0.07))
    paint(mesh_obj("Nave_Buttresses", bm, col, root), "stone_dark", lo=0.2, hi=0.6)
    # stained glass: tall arched windows between the buttresses, a rose window on the back gable
    glass = glow_mat("chapel_glass", (0.45, 0.75, 1.0), 0.6)
    bm = bmesh.new()
    for sx in (-1, 1):
        for k in range(3):
            y = NAVE_Y0 + 0.12 + (k + 0.5) * (NAVE_Y1 - NAVE_Y0 - 0.24) / 3
            bm_box(bm, (0.04, 0.2, 0.46), (sx * (hw + 0.005), y, 0.98))
            bm_cyl(bm, 0.1, 0.1, 0.04, (sx * (hw + 0.005), y, 1.21), rot=(0, 90, 0), seg=8)
    bm_cyl(bm, 0.22, 0.22, 0.04, (0, NAVE_Y0 - 0.005, 1.78), rot=(90, 0, 0), seg=12)
    o = mesh_obj("Nave_Glass", bm, col, root)
    o.data.materials.append(glass)
    bm = bmesh.new()
    ring(bm, (0, NAVE_Y0 - 0.01, 1.78), 0.26, 0.21, -0.03, 0.03, seg=16, axis="Y")
    for k in range(4):
        a = math.radians(45 * k)
        bm_box(bm, (0.42, 0.03, 0.03), (0, NAVE_Y0 - 0.03, 1.78), (0, math.degrees(a), 0))
    paint(mesh_obj("Nave_RoseFrame", bm, col, root), "stone_dark", lo=0.2, hi=0.5)
    bm = bmesh.new()
    _gable_roof(bm, hw + 0.04, NAVE_Y0 - 0.02, NAVE_Y1, WALL_TOP + 0.02, RIDGE, n=7)
    o = mesh_obj("Nave_Roof", bm, col, root)
    paint(o, "team", team=True, lo=0.08, hi=0.75)
    me = o.data
    uv = me.uv_layers.active.data
    for p in me.polygons:
        if (p.index // 6) % 2 == 1:
            for li in p.loop_indices:
                uv[li].uv = (uv[li].uv[0], uv[li].uv[1] - 0.03)
    bm = bmesh.new()
    bm_box(bm, (0.12, NAVE_Y1 - NAVE_Y0 + 0.36, 0.1), (0, (NAVE_Y0 + NAVE_Y1) / 2, RIDGE + 0.06))
    bm_cyl(bm, 0.035, 0.035, 0.42, (0, NAVE_Y0 - 0.06, RIDGE + 0.3), seg=6)
    bm_box(bm, (0.24, 0.05, 0.05), (0, NAVE_Y0 - 0.06, RIDGE + 0.4))
    paint(mesh_obj("Nave_Ridge", bm, col, root), "gold", lo=0.15, hi=0.5)

    # ---- the bell tower
    T = Vector((0, TOWER_Y, 0))
    bm = bmesh.new()
    bm_box(bm, (TW, TW, SHAFT_TOP - TOP), (T.x, T.y, (TOP + SHAFT_TOP) / 2))
    o = paint(mesh_obj("Tower_Shaft", bm, col, root), "stone", lo=0.05, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for z in (1.5, SHAFT_TOP - 0.05):
        bm_box(bm, (TW + 0.1, TW + 0.1, 0.1), (T.x, T.y, z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(4):
                z = TOP + 0.18 + k * 0.5
                bm_box(bm, (0.16, 0.16, 0.2), (T.x + sx * (TW / 2 - 0.05), T.y + sy * (TW / 2 - 0.05), z))
    bm_box(bm, (TW + 0.2, TW + 0.2, 0.16), (T.x, T.y, TOP + 0.08))
    paint(mesh_obj("Tower_Trim", bm, col, root), "stone_dark", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_box(bm, (0.42, 0.06, 0.62), (T.x, T.y + TW / 2 + 0.01, TOP + 0.31 + 0.02))
    bm_cyl(bm, 0.21, 0.21, 0.06, (T.x, T.y + TW / 2 + 0.01, TOP + 0.64), rot=(90, 0, 0), seg=10)
    paint(mesh_obj("Tower_Door", bm, col, root), "wood_red", lo=0.3, hi=0.7)
    bm = bmesh.new()
    for sx, sy in ((1, 0), (-1, 0)):
        bm_box(bm, (0.04, 0.18, 0.4), (T.x + sx * (TW / 2 + 0.005), T.y, 2.0))
        bm_cyl(bm, 0.09, 0.09, 0.04, (T.x + sx * (TW / 2 + 0.005), T.y, 2.2), rot=(0, 90, 0), seg=8)
    o = mesh_obj("Tower_Glass", bm, col, root)
    o.data.materials.append(glass)
    # belfry: corner pillars, a sill, a railing, and the pyramid roof
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(bm, (0.16, 0.16, BELFRY_TOP - SHAFT_TOP), (T.x + sx * (TW / 2 - 0.08), T.y + sy * (TW / 2 - 0.08),
                                                             (SHAFT_TOP + BELFRY_TOP) / 2))
    bm_box(bm, (TW + 0.06, TW + 0.06, 0.1), (T.x, T.y, BELFRY_TOP - 0.02))
    paint(mesh_obj("Belfry_Pillars", bm, col, root), "stone", lo=0.1, hi=0.5)
    bm = bmesh.new()
    rr = TW / 2 + 0.2
    base = [bm.verts.new((T.x + sx * rr, T.y + sy * rr, BELFRY_TOP + 0.02)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = bm.verts.new((T.x, T.y, APEX))
    corners = [v.co.copy() for v in base]
    for i in range(4):
        bm.faces.new((base[i], base[(i + 1) % 4], apex))
    bm.faces.new(list(reversed(base)))
    o = mesh_obj("Belfry_Roof", bm, col, root)
    paint(o, "team", team=True, lo=0.08, hi=0.7)
    bm = bmesh.new()
    for i in range(4):
        bm_beam(bm, corners[i] + Vector((0, 0, 0.04)), Vector((T.x, T.y, APEX + 0.02)), 0.07, 0.06)
    bm_cyl(bm, 0.07, 0.07, 0.2, (T.x, T.y, APEX + 0.08), seg=8)
    paint(mesh_obj("Belfry_Hips", bm, col, root), "gold", lo=0.15, hi=0.55)

    # ---- courtyard: the statue on the left, the brazier on the right
    bm = bmesh.new()
    bm_cyl(bm, 0.42, 0.46, 0.22, (FL.x - 0.15, FL.y + 0.05, TOP + 0.11), seg=8)
    bm_cyl(bm, 0.36, 0.36, 0.06, (FL.x - 0.15, FL.y + 0.05, TOP + 0.25), seg=8)
    bm_cyl(bm, 0.2, 0.26, 0.42, (FR.x + 0.25, FR.y + 0.1, TOP + 0.21), seg=8)
    bm_cyl(bm, 0.36, 0.22, 0.2, (FR.x + 0.25, FR.y + 0.1, TOP + 0.52), seg=10)
    paint(mesh_obj("Court_Stone", bm, col, root), "stone", lo=0.1, hi=0.6)
    bm = bmesh.new()
    rnd = random.Random(7)
    fc = Vector((FR.x + 0.25, FR.y + 0.1, TOP + 0.6))
    for k in range(7):
        a = math.radians(360 * k / 7 + rnd.uniform(-10, 10))
        d = 0.0 if k == 0 else 0.13
        c = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        h = 0.55 if k == 0 else rnd.uniform(0.25, 0.4)
        top = bm.verts.new(c + Vector((0, 0, h)))
        ms = [bm.verts.new(c + Vector((math.cos(math.radians(90 * j + 45)) * 0.08, math.sin(math.radians(90 * j + 45)) * 0.08, 0)))
              for j in range(4)]
        for j in range(4):
            bm.faces.new((ms[j], ms[(j + 1) % 4], top))
    o = mesh_obj("Court_Flame", bm, col, root)
    o.data.materials.append(glow_mat("holy_fire", (1.0, 0.62, 0.2), 1.6))
    kk = [
        ("props/paladin_statue", (FL.x - 0.15, FL.y + 0.05, TOP + 0.28), 180, 0.36),   # faces out the front, like the chapel
        ("dungeon/candle_triple", (FL.x + 0.45, FL.y + 0.4, TOP), 20, 0.4),
        ("dungeon/candle_triple", (FL.x + 0.35, FL.y - 0.45, TOP), 80, 0.34),
        ("dungeon/candle_triple", (FR.x - 0.5, FR.y - 0.42, TOP), 40, 0.38),
    ]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    crew = empty("Crew", col, root, (FR.x - 0.35, FR.y + 0.3, TOP), 0.3, "SINGLE_ARROW")
    to = Vector((fc.x, fc.y, 0)) - Vector((crew.location.x, crew.location.y, 0))
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))   # faces the brazier
    empty("Head", col, root, (0, 0, 0), 0.5, "SINGLE_ARROW")
    return root


BELL_Z = BELFRY_TOP - 0.1
SUN_Z = APEX + 0.42
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.3), None),
    "bell": ((0, TOWER_Y, BELL_Z), (0, TOWER_Y, BELL_Z - 0.3), "root"),
    "sun": ((0, TOWER_Y, SUN_Z), (0, TOWER_Y, SUN_Z + 0.3), "root"),
    "flash": ((0, TOWER_Y, SUN_Z), (0, TOWER_Y + 0.3, SUN_Z), "root"),
}


def build_head():
    col = collection("Chapel")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = make_rig(col, head, BONES)
    # the bell: a flared cup with a lip, its yoke and a clapper
    bm = bmesh.new()
    b0 = Vector((0, TOWER_Y, BELL_Z))
    bm_cyl(bm, 0.12, 0.08, 0.06, tuple(b0 + Vector((0, 0, -0.03))), seg=10)
    bm_cyl(bm, 0.22, 0.12, 0.3, tuple(b0 + Vector((0, 0, -0.2))), seg=12)
    bm_cyl(bm, 0.25, 0.25, 0.04, tuple(b0 + Vector((0, 0, -0.36))), seg=12)
    rig_part("Head_Bell", bm, "gold", rig, "bell", col, bevel=0, lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_box(bm, (TW - 0.1, 0.08, 0.08), tuple(b0 + Vector((0, 0, 0.04))))
    bm_cyl(bm, 0.04, 0.04, 0.22, tuple(b0 + Vector((0, 0, -0.3))), seg=6)
    bm_cyl(bm, 0.06, 0.06, 0.06, tuple(b0 + Vector((0, 0, -0.42))), seg=8)
    rig_part("Head_BellYoke", bm, "iron", rig, "bell", col, bevel=0)
    # the sunburst: a glowing core with twelve rays in every direction
    sun = glow_mat("dawn_sun", GOLD, GLOW)
    bm = bmesh.new()
    s0 = Vector((0, TOWER_Y, SUN_Z))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.17, matrix=Matrix.Translation(s0))
    dirs = []
    for i in range(6):
        a = math.radians(60 * i)
        dirs.append(Vector((math.cos(a), 0, math.sin(a))))
    for i in range(3):
        a = math.radians(120 * i + 30)
        dirs.append(Vector((math.cos(a) * 0.5, 0.86, math.sin(a) * 0.5)))
        dirs.append(Vector((math.cos(a + math.pi / 3) * 0.5, -0.86, math.sin(a + math.pi / 3) * 0.5)))
    for d in dirs:
        d.normalize()
        rot = d.to_track_quat("Z", "Y").to_euler()
        bm_cyl(bm, 0.07, 0.0, 0.34, tuple(s0 + d * 0.3), rot=tuple(math.degrees(x) for x in rot), seg=4)
    rig_part("Head_Sun", bm, None, rig, "sun", col, bevel=0, mat=sun)
    # the flash: a thin ring of light around the sun (hidden until a pulse)
    bm = bmesh.new()
    ring(bm, tuple(s0), 0.62, 0.5, -0.03, 0.03, seg=24)
    rig_part("Head_Flash", bm, None, rig, "flash", col, bevel=0, mat=sun)
    empty("Muzzle", col, head, tuple(s0), 0.25, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 24


def pose(rig, swing=0.0, spin=0.0, flare=1.0, flash=0.0, bob=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["bell"].rotation_quaternion = arm_space_quat(pb["bell"], (1, 0, 0), swing)
    pb["sun"].rotation_quaternion = arm_space_quat(pb["sun"], (0, 0, 1), spin)
    pb["sun"].scale = (flare,) * 3
    pb["sun"].location = arm_space_loc(pb["sun"], (0, 0, bob))
    pb["flash"].scale = (max(flash, 0.001),) * 3


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, swing=1.5 * math.sin(2 * math.pi * t), spin=90 * t, bob=0.05 * math.sin(2 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    swing = {0: 0, 2: 18, 4: 26, 7: 4, 10: -18, 13: -6, 16: 10, 19: 2, 22: -3, 24: 0}
    keys = sorted(swing)
    for f in range(FIRE_LEN + 1):
        k0 = max(k for k in keys if k <= f)
        k1 = min(k for k in keys if k >= f)
        sw = swing[k0] if k0 == k1 else swing[k0] + (swing[k1] - swing[k0]) * smooth((f - k0) / (k1 - k0))
        flare = 1.0 + 0.55 * (smooth(f / 3.0) - smooth((f - 3) / 12.0))
        flash = 0.0 if f == 0 else (2.6 * smooth(f / 10.0) if f <= 10 else 2.6 * (1.0 - smooth((f - 10) / 4.0)) + 0.4 * smooth((f - 10) / 4.0))
        if f >= 14:
            flash = 0.0
        pose(rig, swing=sw, spin=90 * smooth(f / FIRE_LEN), flare=flare, flash=flash)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.4), "dist": 11.5, "yaw": 150, "pitch": 24, "anim_target": (0, FRONT.y + 0.1, 3.6),
           "anim_dist": 5.0, "frames": [("idle", 0), ("fire", 4), ("fire", 9), ("fire", 13)]}


def build_all():
    build_base()
    build_head()
    build_anims()
