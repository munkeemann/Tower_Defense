"""Builds the Kraken (footprint "fan5": [0,0] the hub, with [-1,0], [0,-1], [1,-1], [1,0] fanned round its front and
right), the Tide's tier-3 creature: tentacles seize and crush up to 3 enemies at once, holding walkers in place.

    blender -b --factory-startup --python tools/blender/build_tower.py -- kraken <preview dir>

A deep pool fills the hub cell, rimmed with barnacled rock; the kraken's great crimson head rises out of it, glaring
with slit-pupilled golden eyes (the Head: it turns to watch its prey). Six tentacles rise from the water: two beside the
head and one from a hole in each outer cell, hooked and lined with pale suckers. A snapped mast, kegs and coral lie in
the wreckage. idle: the tentacles writhe. fire: the three front tentacles rear back and lash down, squeezing, while the
rest thrash.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "kraken"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
H = hex_to_world(0, 0, MID)
OUTER = [hex_to_world(q, s, MID) for q, s in [(-1, 0), (0, -1), (1, -1), (1, 0)]]
TOP = 0.34
T = TOP
WATER = T + 0.1
BODY, SUCKER = "red", "salmon"
EYE = (1.0, 0.82, 0.25)
LASH = (0, 1, 2, 5)          # tentacles that strike (the outer front three, plus one by the head)


def tentacle_spots():
    """Base point and outward direction of each tentacle: one per outer cell, two in the pool beside the head."""
    spots = []
    for c in OUTER:
        d = Vector((c.x - H.x, c.y - H.y, 0)).normalized()
        spots.append((Vector((c.x, c.y, WATER - 0.04)) - d * 0.15, d))
    for sx in (-1, 1):
        d = Vector((sx, 0.35, 0)).normalized()
        spots.append((Vector((H.x, H.y, WATER - 0.04)) + d * 0.62, d))
    return spots


def tentacle_pts(base, d, scale=1.0):
    up = Vector((0, 0, 1))
    p0 = base
    p1 = p0 + up * 0.5 * scale + d * 0.08 * scale
    p2 = p1 + up * 0.42 * scale - d * 0.06 * scale
    p3 = p2 + up * 0.28 * scale + d * 0.18 * scale
    p4 = p3 + d * 0.26 * scale - up * 0.12 * scale
    return [p0, p1, p2, p3, p4]


def build_base():
    col = collection("Kraken")
    root = empty("Kraken", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(97)
    # the deep pool in the hub, and a water hole in each outer cell, all rimmed with rock
    water, rocks = bmesh.new(), bmesh.new()
    bm_cyl(water, 0.92, 0.92, 0.04, (H.x, H.y, WATER - 0.02), seg=14)
    for k in range(14):
        a = math.radians(360 * k / 14 + rnd.uniform(-6, 6))
        r = rnd.uniform(0.14, 0.22)
        bm_ellipsoid(rocks, (H.x + math.cos(a) * 0.92, H.y + math.sin(a) * 0.92, T + r * 0.45), (r * 1.25, r, r * 0.8),
                     rot=(0, 0, math.degrees(a)), u=6, v=4)
    for c in OUTER:
        bm_cyl(water, 0.42, 0.42, 0.04, (c.x, c.y, WATER - 0.02), seg=10)
        for k in range(7):
            a = math.radians(360 * k / 7 + rnd.uniform(-10, 10))
            r = rnd.uniform(0.1, 0.15)
            bm_ellipsoid(rocks, (c.x + math.cos(a) * 0.45, c.y + math.sin(a) * 0.45, T + r * 0.45), (r * 1.2, r, r * 0.8),
                         rot=(0, 0, math.degrees(a)), u=6, v=4)
    paint_water(mesh_obj("Pools", water, col, root))
    paint(mesh_obj("Rocks", rocks, col, root), "stone2", lo=0.1, hi=0.7)
    bm = bmesh.new()
    for k in range(10):
        c = [H] + OUTER
        p = c[k % 5] + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 0))
        a = math.atan2(p.y - c[k % 5].y, p.x - c[k % 5].x)
        rr = 0.92 if k % 5 == 0 else 0.46
        p = c[k % 5] + Vector((math.cos(a) * rr, math.sin(a) * rr, 0))
        bm_cyl(bm, 0.05, 0.025, 0.06, (p.x, p.y, T + 0.2), seg=6)
    paint(mesh_obj("Barnacles", bm, col, root), "cream", lo=0.3, hi=0.7)
    # wreckage: a snapped mast across the back cell, kegs, coral
    back = OUTER[3]
    bm = bmesh.new()
    m0 = Vector((back.x - 0.75, back.y + 0.55, T + 0.08))
    m1 = Vector((back.x + 0.55, back.y - 0.45, T + 0.12))
    bm_beam(bm, m0, m1, 0.13, 0.13, w1=0.1, h1=0.1)
    bm_beam(bm, m0.lerp(m1, 0.3) + Vector((0, 0, 0.0)), m0.lerp(m1, 0.3) + Vector((0.35, 0.45, 0.04)), 0.07, 0.07)
    paint(mesh_obj("Mast", bm, col, root), "wood_dark", lo=0.3, hi=0.8)
    kk_import("dungeon/barrel_small_stack", col, root, (OUTER[0].x - 0.15, OUTER[0].y - 0.6, T), 40, 0.33, name="Prop_KK_0")
    coral = bmesh.new()
    bm_coral(coral, rnd, (OUTER[2].x + 0.55, OUTER[2].y + 0.25, T), h=0.5, n=4)
    bm_coral(coral, rnd, (OUTER[1].x - 0.6, OUTER[1].y - 0.2, T), h=0.45, n=3)
    paint(mesh_obj("Coral", coral, col, root), "orange", lo=0.1, hi=0.7)
    # the head turns: a bare marker in the pool (its meshes go on it in build_head)
    empty("Head", col, root, (H.x, H.y, WATER), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Kraken")
    root = bpy.data.objects["Kraken"]
    head = bpy.data.objects["Head"]
    spots = tentacle_spots()
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None)}
    for i, (base, d) in enumerate(spots):
        pts = tentacle_pts(base, d, 1.0 if i < 4 else 0.85)
        for j in range(4):
            bones["t%d.%d" % (i, j + 1)] = (tuple(pts[j]), tuple(pts[j + 1]), "root" if j == 0 else "t%d.%d" % (i, j))
    rig = make_rig(col, root, bones)
    for i, (base, d) in enumerate(spots):
        pts = tentacle_pts(base, d, 1.0 if i < 4 else 0.85)
        r0, r1 = (0.17, 0.035) if i < 4 else (0.15, 0.03)
        side = d.cross(Vector((0, 0, 1)))
        for j in range(4):
            bm, sk = bmesh.new(), bmesh.new()
            seg = pts[j + 1] - pts[j]
            rot = tuple(math.degrees(x) for x in Vector((0, 0, 1)).rotation_difference(seg.normalized()).to_euler())
            for k in range(3):
                t = (j + (k + 0.5) / 3) / 4
                p = pts[j].lerp(pts[j + 1], (k + 0.5) / 3)
                r = r0 + (r1 - r0) * t
                bm_ellipsoid(bm, tuple(p), (r, r * 0.95, max(r * 1.2, seg.length / 3 * 0.8)), rot=rot, u=8, v=5)
                # suckers on the inner (hub) side
                inward = -d if j < 3 else Vector((0, 0, -1))
                bm_ellipsoid(sk, tuple(p + inward * r * 0.92), (r * 0.42, r * 0.42, r * 0.42), u=6, v=3)
            rig_part("Tent%d_%d" % (i, j + 1), bm, BODY, rig, "t%d.%d" % (i, j + 1), col, bevel=0, lo=0.5 + 0.08 * j, hi=0.9)
            rig_part("Tent%d_%dS" % (i, j + 1), sk, SUCKER, rig, "t%d.%d" % (i, j + 1), col, bevel=0, lo=0.1, hi=0.4)
    # the head on the turning marker: a great mantle, brow ridges, glaring eyes with slit pupils
    hp = head.matrix_world.translation
    mantle, spots_bm = bmesh.new(), bmesh.new()
    bm_ellipsoid(mantle, (0, -0.12, 0.62), (0.62, 0.62, 0.78), rot=(-14, 0, 0), u=14, v=9)
    bm_ellipsoid(mantle, (0, 0.18, 0.22), (0.58, 0.48, 0.32), u=12, v=6)
    for sx in (-1, 1):
        bm_ellipsoid(mantle, (sx * 0.3, 0.38, 0.5), (0.22, 0.12, 0.08), rot=(0, sx * 15, sx * -20), u=7, v=4)
    rnd = random.Random(3)
    for k in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(0.6, 1.2)
        rr = 0.6 * math.sqrt(max(0.05, 1 - ((z - 0.62) / 0.78) ** 2))
        bm_ellipsoid(spots_bm, (math.cos(a) * rr, -0.12 + math.sin(a) * rr - 0.05, z), (0.08, 0.08, 0.05), u=6, v=4)
    o = mesh_obj("Head_Mantle", mantle, col, head)
    paint(o, BODY, lo=0.55, hi=0.95)
    o = mesh_obj("Head_Spots", spots_bm, col, head)
    paint(o, SUCKER, lo=0.2, hi=0.5)
    eyes, pupils = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        c = Vector((sx * 0.3, 0.44, 0.38))
        bm_ellipsoid(eyes, tuple(c), (0.13, 0.08, 0.11), u=9, v=6)
        bm_box(pupils, (0.03, 0.03, 0.15), tuple(c + Vector((0, 0.065, 0))))
    o = mesh_obj("Head_Eyes", eyes, col, head)
    o.data.materials.append(glow_mat("kraken_eye", EYE, 0.8))
    o.data.uv_layers.new(name="UVMap")
    o = mesh_obj("Head_Pupils", pupils, col, head)
    paint(o, "black", lo=0.3, hi=0.6)
    empty("Muzzle", col, head, (0, 0.6, 0.45), 0.25, "SPHERE")
    return rig


IDLE_LEN = 90
FIRE_LEN = 30


def pose(rig, ph=0.0, amp=1.0, lash=0.0, squeeze=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    for i, (base, d) in enumerate(tentacle_spots()):
        a = d.cross(Vector((0, 0, 1))).normalized()      # positive about a tips a tentacle inward, toward the hub
        side = Vector((0, 0, 1))
        for j in range(4):
            b = pb["t%d.%d" % (i, j + 1)]
            w = amp * (6 + 5 * j) * math.sin(ph * 2 * math.pi + i * 1.3 - j * 0.7)
            sw = amp * (4 + 3 * j) * math.cos(ph * 2 * math.pi + i * 0.9 - j * 0.6)
            ang = w
            if i in LASH:
                ang += lash * (-10 - 10 * j) + squeeze * (8 + 14 * j)
            b.rotation_quaternion = arm_space_quat(b, tuple(a), ang) @ arm_space_quat(b, tuple(side), sw)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, ph=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 4.0)
        strike = smooth((f - 4) / 3.0)
        lash = -1.2 * rear * (1 - strike) + 2.2 * strike * (1 - smooth((f - 10) / 14.0))
        squeeze = smooth((f - 8) / 4.0) * (1 - smooth((f - 18) / 10.0))
        pose(rig, ph=f / FIRE_LEN * 2.0, amp=1.6, lash=lash, squeeze=squeeze)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 10.5, "yaw": 160, "pitch": 24, "anim_target": (0, 0, 0.9), "anim_dist": 8.0,
           "frames": [("idle", 0), ("idle", 45), ("fire", 3), ("fire", 8), ("fire", 14)]}


def build_all():
    build_base()
    build_head()
    build_anims()
