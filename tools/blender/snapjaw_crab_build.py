"""Builds the Snapjaw Crab (footprint "wing3": [0,0] back, [1,-1] front-right, [-1,0] front-left; two front "guns"),
a Tide creature: two giant claws, each crushing ground enemies; cracked shells take more damage.

    blender -b --factory-startup --python tools/blender/build_tower.py -- snapjaw_crab <preview dir>

A huge orange-red crab squats on the back cell: a wide, bumpy shell with team-coloured markings and barnacles, eyes on
stalks, six jointed legs, and two massive claws on long arms reaching out over the front cells. Shells, a starfish and
seaweed lie about. It doesn't turn (a bare Head marker carries Muzzle1 / Muzzle2 at the claws). idle: it breathes, its
eyes twitch, the claws idly open and close. fire: both claws rear up and smash down, pincers snapping shut.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "snapjaw_crab"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FR = hex_to_world(1, -1, MID)
FL = hex_to_world(-1, 0, MID)
TOP = 0.34
T = TOP
SHELL, BELLY = "red", "cream"
BODY_C = Vector((0, -0.42, T + 0.52))


def arm_pts(s):
    """Shoulder, elbow, wrist, the claw's tip and the pincer's hinge and tip for side s (-1 left, 1 right)."""
    sh = Vector((s * 0.68, 0.12, T + 0.55))
    el = Vector((s * 1.22, 0.32, T + 0.92))
    wr = Vector((s * 1.62, 0.48, T + 0.62))
    tip = Vector((s * 1.8, 1.42, T + 0.3))
    hinge = Vector((s * 1.7, 0.9, T + 0.62))
    ptip = Vector((s * 1.7, 1.4, T + 0.66))
    return sh, el, wr, tip, hinge, ptip


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "body": ((0, -0.9, T + 0.5), (0, 0.2, T + 0.55), "root")}
for _s, _n in ((-1, "L"), (1, "R")):
    _sh, _el, _wr, _tip, _hg, _pt = arm_pts(_s)
    BONES["arm." + _n] = (tuple(_sh), tuple(_el), "body")
    BONES["fore." + _n] = (tuple(_el), tuple(_wr), "arm." + _n)
    BONES["claw." + _n] = (tuple(_wr), tuple(_wr.lerp(_tip, 0.7)), "fore." + _n)
    BONES["pinch." + _n] = (tuple(_hg), tuple(_pt), "claw." + _n)
    BONES["eye." + _n] = ((_s * 0.24, 0.18, T + 0.78), (_s * 0.3, 0.3, T + 1.12), "body")


def build_base():
    col = collection("Snapjaw_crab")
    root = empty("Snapjaw_crab", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(83)
    bm = bmesh.new()
    bm_starfish(bm, (FR.x + 0.55, FR.y - 0.45, T), r=0.24, yaw=20)
    bm_starfish(bm, (BK.x - 0.7, BK.y - 0.55, T), r=0.18, yaw=60)
    paint(mesh_obj("Starfish", bm, col, root), "orange", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_conch(bm, (FL.x - 0.55, FL.y - 0.4, T), length=0.34, yaw=-30)
    bm_conch(bm, (BK.x + 0.75, BK.y - 0.6, T), length=0.26, yaw=110)
    paint(mesh_obj("Conches", bm, col, root), "cream", lo=0.3, hi=0.8)
    bm = bmesh.new()
    bm_kelp(bm, rnd, (FL.x + 0.6, FL.y - 0.55, T), h=0.6, n=3)
    bm_kelp(bm, rnd, (BK.x + 0.4, BK.y - 0.85, T), h=0.5, n=2)
    paint(mesh_obj("Kelp", bm, col, root), "teal", lo=0.1, hi=0.8)
    bm = bmesh.new()
    for k in range(7):
        p = [FR, FL, BK][k % 3] + Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.6, -0.2), 0))
        r = rnd.uniform(0.06, 0.12)
        bm_ellipsoid(bm, (p.x, p.y, T + r * 0.4), (r * 1.2, r, r * 0.6), rot=(0, 0, rnd.uniform(0, 90)), u=5, v=3)
    paint(mesh_obj("Pebbles", bm, col, root), "stone2", lo=0.2, hi=0.7)
    empty("Head", col, root, (0, 0, T), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Snapjaw_crab")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, {k: (tuple(Vector(v[0]) - Vector((0, 0, T))), tuple(Vector(v[1]) - Vector((0, 0, T))), v[2])
                               for k, v in BONES.items()})
    rnd = random.Random(5)
    z0 = Vector((0, 0, T))

    def P(name, bm, sw, bone, **kw):
        bmesh.ops.translate(bm, vec=-z0, verts=bm.verts)     # (the rig sits on the Head, at the plinth's top)
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, **kw)

    # ---- the body: a wide bumpy shell over a pale belly, team markings, barnacles, eyes on stalks, mouthparts
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(BODY_C), (1.0, 0.74, 0.36), u=14, v=8)
    for k in range(9):                                  # the knobbly front rim
        a = math.radians(25 + 130 * k / 8)
        p = BODY_C + Vector((math.cos(a) * 0.95, math.sin(a) * 0.68, -0.02))
        bm_ellipsoid(bm, tuple(p), (0.1, 0.1, 0.08), u=6, v=4)
    for sx in (-1, 1):
        bm_ellipsoid(bm, tuple(BODY_C + Vector((sx * 0.42, -0.1, 0.22))), (0.3, 0.32, 0.16), u=8, v=5)
    P("Head_Shell", bm, SHELL, "body", lo=0.15, hi=0.75)
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(BODY_C + Vector((0, 0.05, -0.16))), (0.92, 0.66, 0.24), u=12, v=6)
    P("Head_Belly", bm, BELLY, "body", lo=0.3, hi=0.8)
    bm = bmesh.new()
    for p, r in (((0, -0.35, 0.36), 0.16), ((-0.32, -0.62, 0.28), 0.1), ((0.34, -0.6, 0.28), 0.1)):
        bm_ellipsoid(bm, tuple(BODY_C + Vector(p)), (r * 1.3, r, 0.04), u=8, v=4)
    P("Head_Markings", bm, "team", "body", team=True, lo=0.15, hi=0.55)
    bm = bmesh.new()
    for k in range(6):
        a = rnd.uniform(0, 2 * math.pi)
        p = BODY_C + Vector((math.cos(a) * rnd.uniform(0.3, 0.75), -0.25 + math.sin(a) * 0.4, 0.27))
        bm_cyl(bm, 0.06, 0.03, 0.06, tuple(p), seg=6)
    P("Head_Barnacles", bm, "cream", "body", lo=0.3, hi=0.7)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_ellipsoid(bm, (sx * 0.1, 0.33, T + 0.42), (0.07, 0.07, 0.1), rot=(20, 0, 0), u=6, v=4)
    P("Head_Mouth", bm, "salmon", "body", lo=0.3, hi=0.7)
    for s, n in ((-1, "L"), (1, "R")):
        h0, t0, _ = BONES["eye." + n]
        bm = bmesh.new()
        bm_beam(bm, h0, t0, 0.07, 0.07, w1=0.05, h1=0.05)
        P("Head_Stalk" + n, bm, SHELL, "eye." + n, lo=0.3, hi=0.7)
        bm = bmesh.new()
        bm_ellipsoid(bm, tuple(Vector(t0) + Vector((0, 0.02, 0.04))), (0.08, 0.08, 0.09), u=8, v=5)
        P("Head_Eye" + n, bm, "black", "eye." + n, lo=0.3, hi=0.6)
        bm = bmesh.new()
        bm_ellipsoid(bm, tuple(Vector(t0) + Vector((s * 0.02, 0.08, 0.08))), (0.025, 0.02, 0.025), u=5, v=3)
        P("Head_Glint" + n, bm, "white", "eye." + n, lo=0.05, hi=0.2)
    # ---- six jointed legs (on the body)
    legs = bmesh.new()
    for s in (-1, 1):
        for k, y in enumerate((-0.12, -0.48, -0.84)):
            hip = Vector((s * 0.82, y, T + 0.42))
            knee = Vector((s * 1.3, y - 0.12 - 0.05 * k, T + 0.78 - 0.05 * k))
            foot = Vector((s * 1.62, y - 0.3 - 0.1 * k, T + 0.02))
            bm_beam(legs, hip, knee, 0.12, 0.12, w1=0.1, h1=0.1)
            bm_beam(legs, knee, foot, 0.1, 0.1, w1=0.03, h1=0.03)
            bm_ellipsoid(legs, tuple(knee), (0.07, 0.07, 0.07), u=6, v=4)
    P("Head_Legs", legs, SHELL, "body", lo=0.25, hi=0.75)
    # ---- arms and claws
    for s, n in ((-1, "L"), (1, "R")):
        sh, el, wr, tip, hg, pt = arm_pts(s)
        bm = bmesh.new()
        bm_beam(bm, sh, el, 0.2, 0.2, w1=0.17, h1=0.17)
        bm_ellipsoid(bm, tuple(el), (0.12, 0.12, 0.12), u=7, v=4)
        P("Head_Arm" + n, bm, SHELL, "arm." + n, lo=0.2, hi=0.7)
        bm = bmesh.new()
        bm_beam(bm, el, wr, 0.17, 0.17, w1=0.2, h1=0.2)
        P("Head_Fore" + n, bm, SHELL, "fore." + n, lo=0.2, hi=0.7)
        bm = bmesh.new()
        palm = wr.lerp(tip, 0.22) + Vector((0, 0, 0.06))
        d = (tip - wr).normalized()
        q = Vector((0, 1, 0)).rotation_difference(d).to_euler()
        bm_ellipsoid(bm, tuple(palm), (0.27, 0.32, 0.25), rot=tuple(math.degrees(x) for x in q), u=10, v=7)
        root_f = palm + d * 0.18 - Vector((0, 0, 0.1))
        bm_beam(bm, root_f, root_f.lerp(tip, 0.6) + Vector((0, 0, 0.03)), 0.24, 0.18, w1=0.16, h1=0.13)
        bm_beam(bm, root_f.lerp(tip, 0.6) + Vector((0, 0, 0.03)), tip, 0.16, 0.13, w1=0.03, h1=0.03)
        for k in range(3):                                   # teeth along the fixed finger
            p = root_f.lerp(tip, 0.35 + 0.2 * k) + Vector((0, 0, 0.08 - 0.02 * k))
            bm_beam(bm, p, p + Vector((0, 0, 0.08)), 0.05, 0.05, w1=0.0, h1=0.0)
        P("Head_Claw" + n, bm, SHELL, "claw." + n, lo=0.1, hi=0.65)
        bm = bmesh.new()
        mid = hg.lerp(pt, 0.55) + Vector((0, 0, 0.07))
        bm_beam(bm, hg, mid, 0.2, 0.15, w1=0.15, h1=0.12)
        bm_beam(bm, mid, pt, 0.15, 0.12, w1=0.03, h1=0.03)
        bm_ellipsoid(bm, tuple(hg), (0.11, 0.11, 0.11), u=6, v=4)
        P("Head_Pinch" + n, bm, SHELL, "pinch." + n, lo=0.1, hi=0.6)
        bm = bmesh.new()
        bm_ellipsoid(bm, tuple(tip + Vector((0, -0.05, 0.0))), (0.05, 0.05, 0.05), u=5, v=3)
        bm_ellipsoid(bm, tuple(pt + Vector((0, -0.05, 0.0))), (0.045, 0.045, 0.045), u=5, v=3)
        P("Head_ClawTips" + n, bm, "black", "claw." + n, lo=0.4, hi=0.7)
    empty("Muzzle1", col, head, tuple(arm_pts(-1)[3] - z0), 0.2, "SPHERE")
    empty("Muzzle2", col, head, tuple(arm_pts(1)[3] - z0), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 24


def pose(rig, breathe=0.0, lift=0.0, pinch=0.0, sway=0.0, eyes=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["body"].location = arm_space_loc(pb["body"], (0, 0, breathe))
    up = Vector((0, 0, 1))
    for s, n in ((-1, "L"), (1, "R")):
        sh, el, wr, tip, hg, pt = arm_pts(s)
        a1 = (el - sh).normalized().cross(up)
        a2 = (wr - el).normalized().cross(up)
        pb["arm." + n].rotation_quaternion = arm_space_quat(pb["arm." + n], tuple(a1), lift * 28) @ arm_space_quat(pb["arm." + n], (0, 0, 1), -s * sway)
        pb["fore." + n].rotation_quaternion = arm_space_quat(pb["fore." + n], tuple(a2), lift * 22)
        ac = (tip - wr).normalized().cross(up)
        pb["claw." + n].rotation_quaternion = arm_space_quat(pb["claw." + n], tuple(ac), lift * 15)
        ap = (pt - hg).normalized().cross(up)
        pb["pinch." + n].rotation_quaternion = arm_space_quat(pb["pinch." + n], tuple(ap), pinch * 32)
        pb["eye." + n].rotation_quaternion = arm_space_quat(pb["eye." + n], (1, 0, 0), eyes * (1.0 if s < 0 else -0.7))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, breathe=0.025 * math.sin(ph * 2), pinch=0.5 + 0.5 * math.sin(ph * 2), sway=4 * math.sin(ph),
             eyes=10 * math.sin(ph * 3), lift=0.05 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 4.0)
        smash = smooth((f - 4) / 2.5)
        lift = rear * (1 - smash) * 1.3 - smash * 0.35 * (1 - smooth((f - 9) / 12.0))
        pinch = 1.0 * rear * (1 - smooth((f - 5) / 1.5)) + 0.3 * smooth((f - 12) / 10.0)
        pose(rig, breathe=-0.04 * smash * (1 - smooth((f - 8) / 10.0)), lift=lift, pinch=pinch, eyes=-15 * rear * (1 - smash))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.8), "dist": 8.5, "yaw": 160, "pitch": 22, "anim_target": (0, 0.2, 0.9), "anim_dist": 6.5,
           "frames": [("idle", 0), ("fire", 4), ("fire", 7), ("fire", 18)]}


def build_all():
    build_base()
    build_head()
    build_anims()
