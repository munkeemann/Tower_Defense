"""Builds the Tidecaller Spire (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), the Tide's Tier IV
aura tower: every toll of its bell freezes everything around it, then leaves it slowed.

    blender -b --factory-startup --python tools/blender/build_tower.py -- tidecaller <preview dir>

Front cell: a twisting spire of coral and sea-ice on a rocky mound ringed by a tide pool; above it two coral horns hold a
great bronze bell, crowned by a glowing ice crystal. Back cells: tide pools with ice shards, coral and kelp, and a
frozen wave curling over the right-hand pool. It's an aura tower, so the rig lives on the root and nothing aims.
idle: the bell stirs, the crown crystal bobs. fire (every toll): the bell swings hard, a ring of frost bursts outward.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "tidecaller"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
R = hex_to_world(1, 0, MID)
L = hex_to_world(-1, 1, MID)
TOP = 0.34
T = TOP
WATER = T + 0.07
ICE = (0.62, 0.9, 1.0)
SPIRE_TOP = T + 1.55
BELL_PIVOT = Vector((F.x, F.y, T + 2.42))


def build_base():
    col = collection("Tidecaller")
    root = empty("Tidecaller", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(31)
    water, rocks = bmesh.new(), bmesh.new()
    bm_cyl(water, 0.98, 0.98, 0.04, (F.x, F.y, WATER - 0.02), seg=16)
    for c, r in ((R, 0.7), (L, 0.7)):
        bm_cyl(water, r, r, 0.04, (c.x, c.y, WATER - 0.02), seg=12)
        for k in range(9):
            a = math.radians(360 * k / 9 + rnd.uniform(-8, 8))
            s = rnd.uniform(0.11, 0.17)
            bm_ellipsoid(rocks, (c.x + math.cos(a) * r, c.y + math.sin(a) * r, T + s * 0.4), (s * 1.3, s, s * 0.8), rot=(0, 0, math.degrees(a)), u=6, v=4)
    for k in range(12):
        a = math.radians(360 * k / 12 + rnd.uniform(-6, 6))
        s = rnd.uniform(0.13, 0.2)
        bm_ellipsoid(rocks, (F.x + math.cos(a) * 0.98, F.y + math.sin(a) * 0.98, T + s * 0.4), (s * 1.3, s, s * 0.8), rot=(0, 0, math.degrees(a)), u=6, v=4)
    paint_water(mesh_obj("Pools", water, col, root))
    paint(mesh_obj("Pool_Rocks", rocks, col, root), "stone2", lo=0.1, hi=0.7)
    # the mound and the spire: twisted, tapering sections of coral and ice
    bm = bmesh.new()
    for k in range(7):
        a = 2 * math.pi * k / 7
        bm_rock(bm, rnd, Vector((F.x + 0.42 * math.cos(a), F.y + 0.42 * math.sin(a), 0)), rnd.uniform(0.32, 0.4), T, rnd.uniform(0.25, 0.4))
    paint(mesh_obj("Spire_Mound", bm, col, root), "stone_dark", lo=0.15, hi=0.7)
    coral, ice = bmesh.new(), bmesh.new()
    z = T + 0.3
    secs = [(0.4, 0.33, 0.36), (0.33, 0.27, 0.32), (0.27, 0.22, 0.3), (0.22, 0.18, 0.27)]
    for i, (r0, r1, h) in enumerate(secs):
        bm_cyl(coral if i % 2 == 0 else ice, r0, r1, h, (F.x, F.y, z + h / 2), rot=(0, 0, 22 * i), seg=6)
        z += h
    paint(mesh_obj("Spire_Coral", coral, col, root), "sky", lo=0.15, hi=0.75)
    o = mesh_obj("Spire_Ice", ice, col, root)
    o.data.materials.append(glow_mat("tide_ice", ICE, 0.35))
    o.data.uv_layers.new(name="UVMap")
    # two coral horns rise from the spire's top and bow together over the bell, a beam between them
    bm = bmesh.new()
    for sx in (-1, 1):
        pts = [Vector((F.x + sx * 0.16, F.y, SPIRE_TOP - 0.05)), Vector((F.x + sx * 0.48, F.y, SPIRE_TOP + 0.35)),
               Vector((F.x + sx * 0.5, F.y, SPIRE_TOP + 0.8)), Vector((F.x + sx * 0.24, F.y, SPIRE_TOP + 1.1))]
        for a, b_ in zip(pts, pts[1:]):
            bm_beam(bm, a, b_, 0.16, 0.16, w1=0.12, h1=0.12)
        for p in pts[1:3]:                                    # little coral branches
            bm_beam(bm, p, p + Vector((sx * 0.2, 0.05, 0.18)), 0.06, 0.06, w1=0.02, h1=0.02)
    bm_beam(bm, Vector((F.x - 0.34, F.y, BELL_PIVOT.z + 0.05)), Vector((F.x + 0.34, F.y, BELL_PIVOT.z + 0.05)), 0.09, 0.09)
    paint(mesh_obj("Spire_Horns", bm, col, root), "salmon", lo=0.2, hi=0.8)
    # the ice shards and coral on the back cells, and a frozen wave curling over the right pool
    shards, cor, kelp = bmesh.new(), bmesh.new(), bmesh.new()
    bm_spikes(shards, rnd, Vector((L.x - 0.1, L.y + 0.1, T)), 5, 0.25, 0.75, 0.09, 0.2, sides=5)
    bm_spikes(shards, rnd, Vector((R.x + 0.35, R.y - 0.35, T)), 4, 0.2, 0.5, 0.07, 0.16, sides=5)
    bm_spikes(shards, rnd, Vector((F.x + 0.75, F.y + 0.5, T)), 3, 0.15, 0.4, 0.06, 0.12, sides=5)
    o = mesh_obj("Ice_Shards", shards, col, root)
    o.data.materials.append(glow_mat("tide_ice", ICE, 0.35))
    o.data.uv_layers.new(name="UVMap")
    bm_coral(cor, rnd, Vector((L.x + 0.5, L.y - 0.45, T)), h=0.5, n=4, w=0.05)
    bm_coral(cor, rnd, Vector((R.x - 0.55, R.y + 0.45, T)), h=0.45, n=4, w=0.05)
    bm_kelp(kelp, rnd, Vector((L.x + 0.45, L.y + 0.5, T)), h=0.6, n=3)
    bm_kelp(kelp, rnd, Vector((R.x + 0.5, R.y + 0.4, T)), h=0.55, n=3)
    paint(mesh_obj("Back_Coral", cor, col, root), "salmon", lo=0.2, hi=0.8)
    paint(mesh_obj("Back_Kelp", kelp, col, root), "lime", lo=0.2, hi=0.8)
    bm = bmesh.new()                                          # the frozen wave: a curling fin of ice
    pts = []
    for k in range(9):
        t = k / 8
        ang = math.radians(-20 + 230 * t)
        rr = 0.5 - 0.3 * t
        pts.append(Vector((R.x - 0.1 + rr * math.cos(ang) * 0.6, R.y - 0.05 + 0.25 * t, T + 0.1 + 0.55 * math.sin(math.radians(170 * t)) + 0.2 * t)))
    for a, b_ in zip(pts, pts[1:]):
        bm_beam(bm, a, b_, 0.5 - 0.35 * pts.index(a) / 8, 0.1, w1=0.5 - 0.35 * (pts.index(a) + 1) / 8, h1=0.08, up=(0, 1, 0.3))
    o = mesh_obj("Frozen_Wave", bm, col, root)
    o.data.materials.append(glow_mat("tide_ice", ICE, 0.35))
    o.data.uv_layers.new(name="UVMap")
    head = empty("Head", col, root, (F.x, F.y, SPIRE_TOP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.6), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "bell": (tuple(BELL_PIVOT), tuple(BELL_PIVOT - Vector((0, 0, 0.3))), "root"),
         "clapper": (tuple(BELL_PIVOT - Vector((0, 0, 0.17))), tuple(BELL_PIVOT - Vector((0, 0, 0.7))), "bell"),
         "crown": ((F.x, F.y, BELL_PIVOT.z + 0.2), (F.x, F.y, BELL_PIVOT.z + 0.5), "root"),
         "frost": ((F.x, F.y, T + 0.12), (F.x, F.y, T + 0.4), "root")}


def build_rig():
    col = collection("Tidecaller")
    root = bpy.data.objects["Tidecaller"]
    rig = make_rig(col, root, BONES)
    bp = BELL_PIVOT
    K = 1.4                                                   # the bell's size

    def at(bm, z_off):
        bmesh.ops.scale(bm, vec=(K, K, K), verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=bp)
        return bm
    bm = bmesh.new()                                          # the bell: a crown, a waisted body, a flared lip
    bm_cyl(bm, 0.05, 0.05, 0.1, (0, 0, -0.03), seg=8)
    bm_ellipsoid(bm, (0, 0, -0.14), (0.2, 0.2, 0.12), u=12, v=6)
    bm_cyl(bm, 0.2, 0.25, 0.26, (0, 0, -0.27), seg=14)
    bm_cyl(bm, 0.25, 0.33, 0.1, (0, 0, -0.45), seg=14)
    rig_part("Bell", at(bm, 0), "gold", rig, "bell", col, bevel=0, lo=0.1, hi=0.6)
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.24, 0.2, -0.33, -0.29, seg=14)
    rig_part("Bell_Band", at(bm, 0), "team", rig, "bell", col, team=True, bevel=0, lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.025, 0.025, 0.34, (0, 0, -0.3), seg=6)
    bm_ellipsoid(bm, (0, 0, -0.48), (0.07, 0.07, 0.07), u=8, v=5)
    rig_part("Bell_Clapper", at(bm, 0), "iron", rig, "clapper", col, bevel=0, lo=0.1, hi=0.45)
    rnd = random.Random(5)
    bm = bmesh.new()                                          # the crown crystal over the arch
    bm_spikes(bm, rnd, Vector((F.x, F.y, bp.z + 0.12)), 4, 0.18, 0.5, 0.08, 0.1, sides=5)
    rig_part("Crown_Crystal", bm, None, rig, "crown", col, bevel=0, mat=glow_mat("tide_crown", ICE, 1.6))
    bm = bmesh.new()                                          # the frost ring, hidden until a toll
    ring(bm, (F.x, F.y, 0), 1.0, 0.82, T + 0.1, T + 0.16, seg=24)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p = Vector((F.x + 0.92 * math.cos(a), F.y + 0.92 * math.sin(a), T + 0.12))
        bm_cyl(bm, 0.06, 0.0, 0.22, tuple(p + Vector((0, 0, 0.1))), seg=4)
    rig_part("Frost_Ring", bm, None, rig, "frost", col, bevel=0, mat=glow_mat("tide_frost", (0.8, 0.95, 1.0), 1.4))
    return rig


IDLE_LEN = 96
FIRE_LEN = 36


def pose(rig, t=0.0, swing=0.0, frost=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["bell"].rotation_quaternion = arm_space_quat(pb["bell"], (1, 0, 0), swing + 3 * math.sin(2 * math.pi * t * 2))
    pb["clapper"].rotation_quaternion = arm_space_quat(pb["clapper"], (1, 0, 0), -0.6 * swing)
    pb["crown"].location = arm_space_loc(pb["crown"], (0, 0, 0.05 * math.sin(2 * math.pi * t * 2)))
    pb["crown"].rotation_quaternion = arm_space_quat(pb["crown"], (0, 0, 1), 360 * t)
    s = max(0.001, frost)
    pb["frost"].scale = (s, s, max(0.001, min(1.0, frost * 2.5) * (1.0 if frost < 1.2 else 0.6)))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        u = f / FIRE_LEN
        swing = 38 * math.sin(math.pi * 2.5 * u) * (1 - u) ** 1.3
        frost = 0.0 if f < 3 else (0.5 + 1.2 * smooth((f - 3) / 14.0)) * (1 - smooth((f - 14) / 8.0))
        pose(rig, t=0.0, swing=swing, frost=frost)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.1), "dist": 9.5, "yaw": 155, "pitch": 20, "anim_target": (F.x, F.y, T + 1.4), "anim_dist": 5.0,
           "frames": [("idle", 0), ("fire", 6), ("fire", 13)]}


def build_all():
    build_base()
    build_rig()
    build_anims()
