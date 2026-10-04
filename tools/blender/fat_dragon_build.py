"""Builds the Fat Dragon (footprint "arrow5": [0,0] front, [1,0] / [-1,1] the flanks, [0,1] middle, [0,2] back), the
Forge's tier-3 creature: too heavy to move, it lies on its hoard and breathes fire in a straight line where it faces.

    blender -b --factory-startup --python tools/blender/build_tower.py -- fat_dragon <preview dir>

A round, low-poly red dragon sprawls on its belly across the middle cells, chin on its forepaws over the front cell,
stubby wings folded on its back (far too small for it), team-coloured spikes down its spine and a tail curled round a
mound of gold on the back cell. Coin heaps, a gold chest and treasure spill over the flanks. It never turns (the game
aims it with R), so the Head is a bare marker at the root and the rig spans the whole beast. idle: slow heavy breaths,
smoke curling from its nostrils, the tail tip flicking. fire: the head heaves up, the jaw drops and a cone of fire
roars out, the wings flare; then it settles back down.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "fat_dragon"
CELLS = [(0, 0), (1, 0), (-1, 1), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # front (0, 1.66)
FR = hex_to_world(1, 0, MID)         # right flank (1.8, 0.62)
FL = hex_to_world(-1, 1, MID)        # left flank (-1.8, 0.62)
M = hex_to_world(0, 1, MID)          # middle (0, -0.42)
B = hex_to_world(0, 2, MID)          # back (0, -2.49)
TOP = 0.34
T = TOP + 0.0                        # plinth top (no turf)
FIRE = (1.0, 0.36, 0.04)
EYE = (1.0, 0.85, 0.2)
BODY, BELLY, HORN = "red", "tan", "cream"

TAIL = [Vector((0, -1.12, T + 0.5)), Vector((0.3, -1.85, T + 0.32)), Vector((0.62, -2.55, T + 0.27)),
        Vector((0.45, -3.15, T + 0.3)), Vector((-0.12, -3.35, T + 0.36))]
MOUTH = Vector((0, 2.62, T + 0.74))
NOSE = Vector((0, 2.6, T + 0.98))
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, -0.8, T + 0.85), (0, 0.8, T + 0.95), "root"),
    "neck": ((0, 1.05, T + 1.05), (0, 1.55, T + 0.95), "body"),
    "head": ((0, 1.55, T + 0.95), (0, 2.25, T + 0.85), "neck"),
    "jaw": ((0, 1.78, T + 0.74), (0, 2.4, T + 0.62), "head"),
    "flame": (tuple(MOUTH), tuple(MOUTH + Vector((0, 0.6, 0))), "head"),
    "smoke": (tuple(NOSE), tuple(NOSE + Vector((0, 0, 0.3))), "head"),
    "wing.L": ((-0.42, 0.45, T + 1.55), (-0.85, 0.05, T + 1.85), "body"),
    "wing.R": ((0.42, 0.45, T + 1.55), (0.85, 0.05, T + 1.85), "body"),
}
for _i in range(4):
    BONES["tail.%d" % (_i + 1)] = (tuple(TAIL[_i]), tuple(TAIL[_i + 1]), "body" if _i == 0 else "tail.%d" % _i)


def build_base():
    col = collection("Fat_dragon")
    root = empty("Fat_dragon", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(23)
    # the hoard: gold mounds (the big one under the tail's curl), scattered coins, KayKit treasure
    bm = bmesh.new()
    for c, r in ((B + Vector((0.05, -0.15, 0)), (0.85, 0.75, 0.32)), (FR + Vector((0.1, 0.05, 0)), (0.62, 0.55, 0.2)),
                 (FL + Vector((-0.1, 0.05, 0)), (0.62, 0.55, 0.2)), (M + Vector((0.0, -0.6, 0)), (0.7, 0.5, 0.14))):
        bm_ellipsoid(bm, (c.x, c.y, T - 0.02), r, u=12, v=6)
    paint(mesh_obj("Hoard_Mounds", bm, col, root), "gold", lo=0.15, hi=0.7)
    bm = bmesh.new()
    for k in range(70):
        c = [B, FR, FL, F, M][k % 5]
        spread = 0.9 if c in (B, FR, FL) else 1.05
        a = rnd.uniform(0, 2 * math.pi)
        d = spread * math.sqrt(rnd.uniform(0.05, 1.0))
        p = Vector((c.x + math.cos(a) * d, c.y + math.sin(a) * d * 0.9, 0))
        if c is F and abs(p.x) < 0.75 and p.y < F.y + 0.5:
            continue                    # keep the space under the chin clear
        bm_cyl(bm, 0.075, 0.075, 0.02, (p.x, p.y, T + 0.012 + rnd.uniform(0, 0.01)), rot=(rnd.uniform(-12, 12), rnd.uniform(-12, 12), 0), seg=8)
    paint(mesh_obj("Hoard_Coins", bm, col, root), "gold", lo=0.3, hi=0.8)
    props = [("dungeon/chest_gold", B + Vector((-0.65, -0.55, 0)), 200, 0.38), ("dungeon/coin_stack_large", FR + Vector((0.35, -0.3, 0.05)), 30, 0.4),
             ("dungeon/coin_stack_medium", FL + Vector((-0.4, -0.3, 0.05)), 140, 0.45), ("dungeon/sword_shield_gold", FL + Vector((0.1, 0.45, 0.1)), 70, 0.36),
             ("resources/Gold_Nuggets", FR + Vector((-0.2, 0.45, 0.05)), 10, 0.5), ("resources/Gold_Bars_Stack_Medium", B + Vector((-0.75, 0.25, 0)), 25, 0.38),
             ("dungeon/coin_stack_small", F + Vector((0.85, 0.35, 0)), 80, 0.4), ("dungeon/coin_stack_small", F + Vector((-0.85, 0.3, 0)), 200, 0.38)]
    for i, (rel, loc, rot, sc) in enumerate(props):
        kk_import(rel, col, root, (loc.x, loc.y, T + loc.z), rot, sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (0, 0, 0), 0.5, "SINGLE_ARROW")
    return root


def _blob_along(bm, pts, r0, r1, n_per=3, squash=0.85):
    """Round segments (ellipsoids) along a polyline, the radius easing from r0 to r1: a chunky low-poly limb or tail."""
    total = len(pts) - 1
    out = []
    for i in range(total):
        for k in range(n_per):
            t = (i + (k + 0.5) / n_per) / total
            p = pts[i].lerp(pts[i + 1], (k + 0.5) / n_per)
            r = r0 + (r1 - r0) * t
            out.append((p, r))
            bm_ellipsoid(bm, tuple(p), (r, r, r * squash), u=8, v=5)
    return out


def build_head():
    col = collection("Fat_dragon")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(7)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, **kw)

    # ---- the body: a big round belly-down barrel with plump haunches
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.1, T + 0.8), (1.05, 1.35, 0.8), u=14, v=9)
    bm_ellipsoid(bm, (0, 0.85, T + 1.05), (0.7, 0.6, 0.55), u=10, v=7)                 # shoulders
    P("Head_Body", bm, BODY, "body", lo=0.2, hi=0.75)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.5, T + 0.62), (0.86, 1.02, 0.62), u=12, v=8)               # pale belly, bulging at the chest
    P("Head_Belly", bm, BELLY, "body", lo=0.35, hi=0.8)
    bm = bmesh.new()
    for y, z, h in ((1.0, 1.62, 0.32), (0.65, 1.66, 0.36), (0.3, 1.64, 0.38), (-0.05, 1.6, 0.36), (-0.4, 1.5, 0.32), (-0.75, 1.33, 0.28),
                    (-1.02, 1.12, 0.22)):
        bm_cyl(bm, 0.12, 0.0, h, (0, y, T + z + h / 2 - 0.08), rot=(12, 0, 0), seg=4)
    P("Head_Spikes", bm, "team", "body", team=True, lo=0.15, hi=0.6)
    # ---- legs (on the root: they stay planted while the body breathes)
    for sx in (-1, 1):
        bm = bmesh.new()
        bm_ellipsoid(bm, (sx * 0.86, -0.55, T + 0.42), (0.42, 0.55, 0.42), u=10, v=6)      # haunch
        bm_ellipsoid(bm, (sx * 1.0, -0.05, T + 0.1), (0.22, 0.34, 0.11), u=8, v=4)         # hind foot, toes forward
        bm_ellipsoid(bm, (sx * 0.72, 1.12, T + 0.42), (0.26, 0.3, 0.38), u=8, v=5)         # foreleg
        bm_ellipsoid(bm, (sx * 0.66, 1.58, T + 0.1), (0.22, 0.3, 0.12), u=8, v=4)          # forepaw
        P("Head_Legs" + ("L" if sx < 0 else "R"), bm, BODY, "root", lo=0.25, hi=0.7)
        bm = bmesh.new()
        for base, n in (((sx * 1.0, 0.27), 3), ((sx * 0.66, 1.86), 3)):
            for k in range(n):
                c = Vector((base[0] + (k - 1) * 0.11, base[1], T + 0.06))
                bm_cyl(bm, 0.045, 0.0, 0.14, tuple(c + Vector((0, 0.05, 0))), rot=(-80, 0, 0), seg=4)
        P("Head_Claws" + ("L" if sx < 0 else "R"), bm, HORN, "root", lo=0.1, hi=0.3)
    # ---- neck and head: a jowly round head resting low, horns swept back, glowing half-lidded eyes
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 1.22, T + 1.08), (0.48, 0.42, 0.46), u=10, v=7)
    bm_ellipsoid(bm, (0, 1.55, T + 0.98), (0.42, 0.36, 0.4), u=10, v=7)
    P("Head_Neck", bm, BODY, "neck", lo=0.25, hi=0.7)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 1.95, T + 0.98), (0.44, 0.45, 0.38), u=12, v=8)             # skull
    bm_ellipsoid(bm, (0, 2.36, T + 0.86), (0.3, 0.34, 0.2), u=10, v=6)               # snout
    for sx in (-1, 1):
        bm_ellipsoid(bm, (sx * 0.3, 2.0, T + 0.82), (0.2, 0.26, 0.2), u=8, v=5)        # jowls
        bm_box(bm, (0.2, 0.16, 0.07), (sx * 0.22, 2.25, T + 1.17), (12, 0, sx * -18))   # heavy brows, half over the eyes
    P("Head_Head", bm, BODY, "head", lo=0.2, hi=0.7)
    bm = bmesh.new()
    for sx in (-1, 1):
        p0 = Vector((sx * 0.22, 1.82, T + 1.22))
        p1 = Vector((sx * 0.36, 1.5, T + 1.45))
        p2 = Vector((sx * 0.4, 1.25, T + 1.68))
        bm_beam(bm, p0, p1, 0.13, 0.13, w1=0.09, h1=0.09)
        bm_beam(bm, p1, p2, 0.09, 0.09, w1=0.0, h1=0.0)
        for k in range(4):                                                          # upper fangs
            bm_cyl(bm, 0.03, 0.0, 0.08, (sx * (0.08 + k * 0.06), 2.5 - k * 0.08, T + 0.65), rot=(180, 0, 0), seg=4)
    P("Head_Horns", bm, HORN, "head", lo=0.1, hi=0.35)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_ellipsoid(bm, (sx * 0.27, 2.27, T + 1.08), (0.075, 0.05, 0.045), u=7, v=4)
    P("Head_Eyes", bm, None, "head", mat=glow_mat("dragon_eye", EYE, 1.0))
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_ellipsoid(bm, (sx * 0.1, 2.68, T + 0.93), (0.045, 0.03, 0.035), u=6, v=4)
    P("Head_Nostrils", bm, "black", "head", lo=0.3, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 2.3, T + 0.72), (0.2, 0.25, 0.08), u=8, v=5)                 # the glow down its throat
    P("Head_Throat", bm, None, "head", mat=glow_mat("dragon_fire", FIRE, 1.2))
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 2.2, T + 0.64), (0.29, 0.42, 0.11), u=10, v=5)               # lower jaw
    P("Head_Jaw", bm, BELLY, "jaw", lo=0.3, hi=0.7)
    bm = bmesh.new()
    for sx in (-1, 1):
        for k in range(3):
            bm_cyl(bm, 0.025, 0.0, 0.07, (sx * (0.1 + k * 0.07), 2.45 - k * 0.09, T + 0.72), seg=4)
    P("Head_JawFangs", bm, HORN, "jaw", lo=0.1, hi=0.3)
    # ---- the fire: a cone of tongues out of the mouth (scaled from nothing when it breathes)
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(MOUTH + Vector((0, 0.85, 0))), (0.3, 0.85, 0.26), u=10, v=6)
    for k in range(7):
        a = math.radians(360 * k / 7 + rnd.uniform(-10, 10))
        off = Vector((math.cos(a) * 0.16, 0, math.sin(a) * 0.14))
        d = (Vector((0, 1, 0)) + off * 1.4).normalized()
        ln = rnd.uniform(0.6, 0.95)
        base = MOUTH + Vector((0, 0.55, 0)) + off
        rot = tuple(math.degrees(x) for x in d.to_track_quat("Z", "Y").to_euler())
        bm_cyl(bm, 0.13, 0.0, ln, tuple(base + d * ln / 2), rot=rot, seg=5)
    P("Head_Flame", bm, None, "flame", mat=glow_mat("dragon_flame", FIRE, 0.9))
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(MOUTH + Vector((0, 0.6, 0))), (0.17, 0.62, 0.15), u=8, v=5)
    P("Head_FlameCore", bm, None, "flame", mat=glow_mat("dragon_flame_core", (1.0, 0.68, 0.15), 1.0))
    bm = bmesh.new()
    for k in range(3):
        bm_ellipsoid(bm, tuple(NOSE + Vector(((k - 1) * 0.07, 0.05 + k * 0.04, 0.1 + k * 0.13))), (0.07 + k * 0.03,) * 2 + (0.06 + k * 0.025,), u=6, v=4)
    P("Head_Smoke", bm, "stone2", "smoke", lo=0.2, hi=0.6)
    # ---- stubby bat wings, folded on the back
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector(BONES["wing." + s][0])
        wr = Vector(BONES["wing." + s][1])
        tips = [Vector((sx * 1.18, -0.3, T + 1.62)), Vector((sx * 1.02, -0.62, T + 1.38)), Vector((sx * 0.7, -0.7, T + 1.3))]
        bm = bmesh.new()
        bm_beam(bm, sh, wr, 0.09, 0.09, w1=0.07, h1=0.07)
        for tp in tips:
            bm_beam(bm, wr, tp, 0.05, 0.05, w1=0.02, h1=0.02)
        P("Head_WingBones" + s, bm, BODY, "wing." + s, lo=0.15, hi=0.5)
        bm = bmesh.new()
        ring_pts = [sh, wr] + tips + [Vector((sx * 0.45, -0.25, T + 1.52))]
        for off in (-0.012, 0.012):
            vs = [bm.verts.new(p + Vector((0, 0, off))) for p in ring_pts]
            c = bm.verts.new(sum(ring_pts, Vector()) / len(ring_pts) + Vector((0, 0, off)))
            for i in range(len(vs)):
                tri = (vs[i], vs[(i + 1) % len(vs)], c)
                bm.faces.new(tri if (off > 0) == (sx > 0) else tuple(reversed(tri)))
        P("Head_Wing" + s, bm, "salmon", "wing." + s, lo=0.3, hi=0.7)
    # ---- the tail, curling round the gold, with a team-coloured spade
    bm = bmesh.new()
    _blob_along(bm, TAIL[:2], 0.36, 0.28)
    P("Head_Tail1", bm, BODY, "tail.1", lo=0.25, hi=0.7)
    for i in range(1, 4):
        bm = bmesh.new()
        _blob_along(bm, TAIL[i:i + 2], 0.28 - 0.07 * (i - 1), 0.21 - 0.06 * (i - 1))
        P("Head_Tail%d" % (i + 1), bm, BODY, "tail.%d" % (i + 1), lo=0.25, hi=0.7)
    for i in range(3):                                                              # the spine's spikes run on
        bm = bmesh.new()
        p = TAIL[i].lerp(TAIL[i + 1], 0.5)
        bm_cyl(bm, 0.09 - 0.015 * i, 0.0, 0.22 - 0.03 * i, (p.x, p.y, p.z + 0.36 - 0.07 * i), rot=(12, 0, 0), seg=4)
        P("Head_TailSpike%d" % (i + 1), bm, "team", "tail.%d" % (i + 1), team=True, lo=0.15, hi=0.6)
    bm = bmesh.new()
    tip, prev = TAIL[4], TAIL[3]
    d = (tip - prev).normalized()
    yaw = math.degrees(math.atan2(d.y, d.x)) - 90
    bm_ellipsoid(bm, tuple(tip + d * 0.18), (0.2, 0.26, 0.05), rot=(0, 0, yaw), u=4, v=3)
    P("Head_TailSpade", bm, "team", "tail.4", team=True, lo=0.15, hi=0.6)
    empty("Muzzle", col, head, tuple(MOUTH), 0.25, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 32
NECK_LIFT, HEAD_LIFT = 18.0, 8.0     # how far the head heaves up to breathe (degrees)


def pose(rig, breathe=0.0, lift=0.0, jaw=0.0, flame=0.0, smoke=0.0, rise=0.0, wings=0.0, flick=0.0, curl=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    s = 1.0 + breathe
    pb["body"].scale = (s, 1.0 + breathe * 0.4, s)
    pitch = lift * (NECK_LIFT + HEAD_LIFT) + jaw * 8
    pb["neck"].rotation_quaternion = arm_space_quat(pb["neck"], (1, 0, 0), lift * NECK_LIFT)
    pb["head"].rotation_quaternion = arm_space_quat(pb["head"], (1, 0, 0), lift * HEAD_LIFT + jaw * 8)
    pb["jaw"].rotation_quaternion = arm_space_quat(pb["jaw"], (1, 0, 0), -jaw * 34)
    f = max(flame, 0.001)
    pb["flame"].scale = (f, f, f)
    pb["flame"].rotation_quaternion = arm_space_quat(pb["flame"], (1, 0, 0), -pitch - 4)   # the breath runs level
    sm = max(smoke, 0.001)
    pb["smoke"].scale = (sm, sm, sm)
    pb["smoke"].location = arm_space_loc(pb["smoke"], (0, 0.05 * rise, 0.2 * rise))
    for w, sx in (("wing.L", -1), ("wing.R", 1)):
        pb[w].rotation_quaternion = arm_space_quat(pb[w], (0, 1, 0), -sx * wings * 40)   # up and out
    pb["tail.2"].rotation_quaternion = arm_space_quat(pb["tail.2"], (0, 0, 1), curl * 4)
    pb["tail.3"].rotation_quaternion = arm_space_quat(pb["tail.3"], (0, 0, 1), curl * 6 + flick * 8)
    pb["tail.4"].rotation_quaternion = arm_space_quat(pb["tail.4"], (0, 0, 1), flick * 22) @ arm_space_quat(pb["tail.4"], (1, 0, 0), abs(flick) * 12)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        puff = t * 2 % 1.0                              # two smoke puffs per loop, one per breath out
        pose(rig, breathe=0.035 * math.sin(ph * 2), lift=0.04 * math.sin(ph * 2 - 0.6), smoke=0.9 * math.sin(math.pi * puff),
             rise=puff, wings=0.03 * math.sin(ph * 2), flick=math.sin(ph * 3) * (0.5 + 0.5 * math.sin(ph)), curl=math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        up = smooth(f / 3.0) * (1 - smooth((f - 20) / 11.0))
        jaw = smooth(f / 2.5) * (1 - smooth((f - 18) / 8.0))
        fl = smooth((f - 1) / 3.0) * (1 - smooth((f - 17) / 6.0))
        fl *= 1.0 + 0.06 * math.sin(f * 2.1)            # the fire roils
        pose(rig, breathe=-0.03 * up, lift=up, jaw=jaw, flame=fl, wings=0.9 * up, flick=0.6 * math.sin(f * 0.6) * up, curl=0.5 * up)
        key_pose(rig, f)
    # the shot leaves where the mouth is mid-breath
    rig.animation_data.action = bpy.data.actions["fire"]
    bpy.context.scene.frame_set(8)
    bpy.context.view_layer.update()
    mouth = rig.matrix_world @ rig.pose.bones["flame"].head
    mz = bpy.data.objects["Muzzle"]
    mz.location = bpy.data.objects["Head"].matrix_world.inverted() @ mouth
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, -0.3, 0.9), "dist": 12.5, "yaw": 150, "pitch": 22, "anim_target": (0, 1.4, 1.1), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 48), ("fire", 4), ("fire", 10), ("fire", 26)]}


def build_all():
    build_base()
    build_head()
    build_anims()
