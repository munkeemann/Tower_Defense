"""Builds the Bone Colossus (footprint "fan5": [0,0] the hub, with [-1,0], [0,-1], [1,-1], [1,0] fanned round its front
and right), the Grave's Tier IV giant: its fists smash whole groups and can stun them.

    blender -b --factory-startup --python tools/blender/build_tower.py -- bone_colossus <preview dir>

On the hub stands a hunched giant of fused bones (the Head: it turns to face its prey): thick bowed legs, a ribcage
holding a burning green soul, skull pauldrons, a horned skull with glowing eyes, and long arms ending in great knuckled
fists of bone. Round it the ground is torn open: broken graves, scattered bones, skulls and glowing cracks.
idle: it breathes, sways and flexes its fists. fire: it heaves both fists overhead and smashes them down in front.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_common.py"), encoding="utf-8").read())

TID = "bone_colossus"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
H = hex_to_world(0, 0, MID)
OUT = {k: hex_to_world(q, s, MID) for k, (q, s) in {"fl": (-1, 0), "f": (0, -1), "fr": (1, -1), "br": (1, 0)}.items()}
TOP = 0.34
T = TOP
S = 1.0


def build_base():
    col = collection("Bone_colossus")
    root = empty("Bone_colossus", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(13)
    # torn earth round the giant's feet, split by glowing cracks
    earth, dark = bmesh.new(), bmesh.new()
    for k in range(10):
        a = 2 * math.pi * k / 10 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(0.85, 1.05)
        sz = rnd.uniform(0.14, 0.22)
        bm_ellipsoid(earth, (H.x + r * math.cos(a), H.y + r * math.sin(a), T + 0.02), (sz * 1.3, sz, sz * 0.55), rot=(rnd.uniform(-10, 10), 0, math.degrees(a)), u=7, v=4)
    paint(mesh_obj("Ground_Clods", earth, col, root), EARTH_SW, lo=0.2, hi=0.75)
    cracks = bmesh.new()
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.3, 0.3)
        p0 = Vector((H.x + 0.35 * math.cos(a), H.y + 0.35 * math.sin(a), T + 0.005))
        p1 = p0 + Vector((math.cos(a + rnd.uniform(-0.4, 0.4)), math.sin(a + rnd.uniform(-0.4, 0.4)), 0)) * rnd.uniform(0.6, 1.1)
        mid = p0.lerp(p1, 0.5) + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0))
        bm_beam(cracks, p0, mid, 0.07, 0.02, w1=0.05, h1=0.02)
        bm_beam(cracks, mid, p1, 0.05, 0.02, w1=0.01, h1=0.02)
    glow_obj("Ground_Cracks", cracks, col, root, NECRO, 0.8)
    # broken graves, bones and skulls on the outer cells
    kk = [("halloween/grave_A_destroyed", (OUT["fl"].x - 0.1, OUT["fl"].y + 0.1, T), 150, 0.3),
          ("halloween/gravestone", (OUT["f"].x + 0.45, OUT["f"].y + 0.35, T), 200, 0.3),
          ("halloween/gravemarker_B", (OUT["f"].x - 0.5, OUT["f"].y + 0.5, T), 170, 0.32),
          ("halloween/grave_B", (OUT["fr"].x + 0.15, OUT["fr"].y + 0.05, T), 220, 0.28),
          ("halloween/bone_A", (OUT["fl"].x + 0.5, OUT["fl"].y - 0.4, T), 30, 0.6),
          ("halloween/bone_B", (OUT["br"].x - 0.3, OUT["br"].y + 0.4, T), 100, 0.6),
          ("halloween/bone_C", (OUT["f"].x + 0.0, OUT["f"].y - 0.2, T), 60, 0.6),
          ("halloween/skull", (OUT["br"].x + 0.35, OUT["br"].y - 0.3, T), 200, 0.55),
          ("halloween/skull_candle", (OUT["fr"].x - 0.5, OUT["fr"].y - 0.45, T), 160, 0.5),
          ("halloween/coffin", (OUT["br"].x + 0.0, OUT["br"].y + 0.05, T), 110, 0.28)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (H.x, H.y, T), 0.5, "SINGLE_ARROW")
    return root


SH = {-1: Vector((-0.62, 0.0, 1.88)), 1: Vector((0.62, 0.0, 1.88))}
EL = {sx: Vector((sx * 0.86, 0.22, 1.32)) for sx in (-1, 1)}
WR = {sx: Vector((sx * 0.78, 0.6, 0.8)) for sx in (-1, 1)}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, -0.05, 0.95), (0, 0.05, 1.85), "root"),
    "skull": ((0, 0.12, 2.0), (0, 0.3, 2.3), "body"),
    "core": ((0, 0.14, 1.45), (0, 0.14, 1.6), "body"),
    "arm.L.1": (tuple(SH[-1]), tuple(EL[-1]), "body"),
    "arm.L.2": (tuple(EL[-1]), tuple(WR[-1]), "arm.L.1"),
    "arm.R.1": (tuple(SH[1]), tuple(EL[1]), "body"),
    "arm.R.2": (tuple(EL[1]), tuple(WR[1]), "arm.R.1"),
}


def build_head():
    col = collection("Bone_colossus")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=S)
    rnd = random.Random(7)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, scale=S, **kw)

    # ---- legs (on the root): thick bowed thigh and shin bones, knobbed joints, broad feet
    bm = bmesh.new()
    for sx in (-1, 1):
        hip, knee, ankle = Vector((sx * 0.32, -0.08, 0.98)), Vector((sx * 0.46, 0.2, 0.52)), Vector((sx * 0.4, 0.02, 0.14))
        bm_beam(bm, hip, knee, 0.2, 0.2, w1=0.15, h1=0.15)
        bm_beam(bm, knee, ankle, 0.17, 0.17, w1=0.13, h1=0.13)
        bm_ellipsoid(bm, tuple(knee), (0.17, 0.17, 0.16), u=8, v=5)
        bm_ellipsoid(bm, tuple(Vector((sx * 0.42, 0.12, 0.09))), (0.22, 0.32, 0.1), u=9, v=5)
        for k in range(3):
            bm_ellipsoid(bm, (sx * 0.42 + (k - 1) * 0.11, 0.42, 0.07), (0.06, 0.1, 0.06), u=6, v=4)
    bm_ellipsoid(bm, (0, -0.05, 1.0), (0.5, 0.3, 0.2), u=10, v=6)                      # pelvis
    P("Legs", bm, BONE_SW, "root", lo=0.3, hi=0.9)
    # ---- the torso: a spine, a great ribcage round a burning soul, skull pauldrons, a ridge of spikes
    bm = bmesh.new()
    for k in range(6):
        z = 1.08 + k * 0.16
        bm_ellipsoid(bm, (0, -0.18 + 0.02 * k, z), (0.13, 0.12, 0.08), u=7, v=4)
    for k in range(5):                                     # ribs: arcs from the spine round to the breastbone
        z = 1.25 + k * 0.13
        rr = 0.42 - 0.035 * abs(k - 2) - (0.06 if k == 0 else 0.0)
        for sx in (-1, 1):
            pts = [Vector((sx * rr * math.sin(math.radians(a)), 0.12 - rr * math.cos(math.radians(a)) * 0.85, z - 0.04 * math.sin(math.radians(a))))
                   for a in range(15, 181, 33)]
            for a, b_ in zip(pts, pts[1:]):
                bm_beam(bm, a, b_, 0.07, 0.06)
    bm_beam(bm, Vector((0, 0.45, 1.85)), Vector((0, 0.4, 1.22)), 0.12, 0.06, w1=0.08, h1=0.05, up=(0, 1, 0))   # breastbone
    for sx in (-1, 1):                                     # collarbones
        bm_beam(bm, Vector((0, 0.12, 1.9)), SH[sx] + Vector((0, 0.05, 0.02)), 0.1, 0.09)
    P("Torso", bm, BONE_SW, "body", lo=0.3, hi=0.9)
    bm, sockets = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        bm_skull(bm, sockets, SH[sx] + Vector((sx * 0.08, 0.02, 0.16)), s=0.42, yaw=sx * -35)
    for k in range(5):
        bm_cyl(bm, 0.07, 0.0, 0.35 - 0.04 * abs(k - 2), (0, -0.3 - 0.0 * k, 1.35 + k * 0.14), rot=(-55, 0, 0), seg=4)
    P("Pauldrons", bm, BONE_SW, "body", lo=0.15, hi=0.6)
    P("Pauldron_Sockets", sockets, "black", "body", lo=0.3, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0.14, 1.5), (0.2, 0.18, 0.24), u=4, v=2)
    for k in range(4):
        a = 2 * math.pi * k / 4
        bm_cyl(bm, 0.06, 0.0, 0.22, (0.12 * math.cos(a), 0.14 + 0.12 * math.sin(a), 1.62), rot=(math.sin(a) * 25, -math.cos(a) * 25, 0), seg=4)
    P("Soul", bm, None, "core", mat=glow_mat("colossus_soul", NECRO, 1.1))
    # ---- the skull: big, horned, glowing eyes
    bm, sockets, eyes = bmesh.new(), bmesh.new(), bmesh.new()
    ec = bm_skull(bm, sockets, (0, 0.2, 2.18), s=0.6)
    for sx in (-1, 1):
        a = Vector((sx * 0.2, 0.15, 2.32))
        b_ = Vector((sx * 0.48, 0.0, 2.55))
        c_ = Vector((sx * 0.52, 0.2, 2.82))
        bm_beam(bm, a, b_, 0.12, 0.12, w1=0.09, h1=0.09)
        bm_beam(bm, b_, c_, 0.09, 0.09, w1=0.01, h1=0.01)
    for e in ec:
        bm_ellipsoid(eyes, tuple(e), (0.06, 0.03, 0.05), u=6, v=4)
    P("Skull", bm, BONE_SW, "skull", lo=0.2, hi=0.8)
    P("Skull_Sockets", sockets, "black", "skull", lo=0.3, hi=0.6)
    P("Skull_Eyes", eyes, None, "skull", mat=glow_mat("colossus_eyes", NECRO, 1.2))
    # ---- arms: a thick upper bone, twin forearm bones, a great fist of knuckles
    for s, sx in (("L", -1), ("R", 1)):
        bm = bmesh.new()
        bm_beam(bm, SH[sx], EL[sx], 0.2, 0.2, w1=0.16, h1=0.16)
        bm_ellipsoid(bm, tuple(EL[sx]), (0.16, 0.16, 0.16), u=8, v=5)
        P("Arm%s1" % s, bm, BONE_SW, "arm.%s.1" % s, lo=0.3, hi=0.85)
        bm = bmesh.new()
        side = Vector((1, 0, 0))
        for off in (-0.07, 0.07):
            bm_beam(bm, EL[sx] + side * off, WR[sx] + side * off * 0.6, 0.11, 0.11, w1=0.09, h1=0.09)
        d = (WR[sx] - EL[sx]).normalized()
        fist = WR[sx] + d * 0.2
        bm_ellipsoid(bm, tuple(fist), (0.27, 0.27, 0.25), u=9, v=6)
        n = d.cross(Vector((1, 0, 0))).normalized()
        for k in range(4):                                  # knuckles across the front of the fist
            p = fist + d * 0.18 + Vector((1, 0, 0)) * (k - 1.5) * 0.12 + n * 0.08
            bm_ellipsoid(bm, tuple(p), (0.08, 0.08, 0.08), u=6, v=4)
        bm_ellipsoid(bm, tuple(fist + Vector((-sx * 0.22, 0.06, 0.05))), (0.08, 0.12, 0.08), u=6, v=4)   # thumb
        P("Arm%s2" % s, bm, BONE_SW, "arm.%s.2" % s, lo=0.3, hi=0.85)
        bm = bmesh.new()                                     # iron bands round the wrist
        ring(bm, (0, 0, 0), 0.19, 0.13, -0.05, 0.05, seg=10)
        q = Vector((0, 0, 1)).rotation_difference(d)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
        bmesh.ops.translate(bm, verts=bm.verts, vec=WR[sx] - d * 0.08)
        P("Arm%s2_Band" % s, bm, "iron", "arm.%s.2" % s, lo=0.1, hi=0.45)
    empty("Muzzle", col, head, (0, 0.9 * S, 0.4 * S), 0.2, "SPHERE")
    return rig


IDLE_LEN = 90
FIRE_LEN = 26


def pose(rig, breathe=0.0, sway=0.0, flex=0.0, lift=0.0, slam=0.0, lean=0.0, look=0.0, soul=1.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["body"].rotation_quaternion = arm_space_quat(pb["body"], (0, 1, 0), sway) @ arm_space_quat(pb["body"], (1, 0, 0), lean + 2 * breathe)
    pb["skull"].rotation_quaternion = arm_space_quat(pb["skull"], (0, 0, 1), look) @ arm_space_quat(pb["skull"], (1, 0, 0), -lean * 0.4)
    pb["core"].scale = (soul, soul, soul)
    for s, sx in (("L", -1), ("R", 1)):
        up = lift * 135 + slam * 58 + flex * 4
        pb["arm.%s.1" % s].rotation_quaternion = (arm_space_quat(pb["arm.%s.1" % s], (1, 0, 0), up)
                                                 @ arm_space_quat(pb["arm.%s.1" % s], (0, 1, 0), -sx * lift * 30))
        pb["arm.%s.2" % s].rotation_quaternion = arm_space_quat(pb["arm.%s.2" % s], (1, 0, 0), lift * 25 - slam * 20 + flex * 6)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, breathe=math.sin(ph * 2), sway=3 * math.sin(ph), flex=math.sin(ph * 2 + 1), look=8 * math.sin(ph + 0.7),
             soul=1.0 + 0.12 * math.sin(ph * 4))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        lift = smooth(f / 9.0) * (1 - smooth((f - 10) / 3.0))
        slam = smooth((f - 10) / 3.0) * (1 - smooth((f - 15) / 10.0))
        lean = -10 * lift + 22 * slam
        pose(rig, lift=lift, slam=slam, lean=lean, soul=1.0 + 0.6 * slam)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 10.5, "yaw": 160, "pitch": 18, "anim_target": (H.x, H.y + 0.3, T + 1.4), "anim_dist": 6.0,
           "frames": [("idle", 0), ("fire", 9), ("fire", 13), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
