"""Builds the Leviathan (footprint "line4": [0,0] front, then [0,1], [0,2], [0,3] going back), the Tide's Tier IV
creature: a sea serpent whose water jet pierces a whole line, slows what it hits and can wash walkers back.

    blender -b --factory-startup --python tools/blender/build_tower.py -- leviathan <preview dir>

A stone-lined sea canal runs the length of the footprint. The serpent's coils break the water in three arches over the
back cells, ending in a finned tail; on the front cell its neck rises out of the water (the Head: the neck turns within
its 90 degree arc to aim) to a long horned head with frilled fins, glowing eyes and a fanged jaw (the jet leaves its
mouth). Coral and kelp grow along the canal. idle: the neck sways and the jaw works.
fire: the head rears back and lunges, the jaw gapes, a gush of water bursts from the mouth.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "leviathan"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
C = [hex_to_world(0, s, MID) for s in range(4)]
TOP = 0.34
T = TOP
WATER = T + 0.08
HALF = 0.62                    # half the canal's width
Y0, Y1 = C[3].y - 0.95, C[0].y + 0.75
BODY, BELLY, FIN = "teal", "cream", "team"
EYE = (0.55, 1.0, 0.9)
JET = (0.42, 0.78, 1.0)
NECK = Vector((0, C[0].y - 0.45, WATER))


def _blob_along(bm, pts, r0, r1, n_per=3, squash=1.0):
    total = len(pts) - 1
    for i in range(total):
        for k in range(n_per):
            t = (i + (k + 0.5) / n_per) / total
            p = pts[i].lerp(pts[i + 1], (k + 0.5) / n_per)
            r = r0 + (r1 - r0) * t
            bm_ellipsoid(bm, tuple(p), (r, r, r * squash), u=9, v=6)


def build_base():
    col = collection("Leviathan")
    root = empty("Leviathan", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(21)
    # the canal: water between two low stone kerbs, closed at both ends
    bm = bmesh.new()
    bm_box(bm, (HALF * 2, Y1 - Y0, 0.04), (0, (Y0 + Y1) / 2, WATER - 0.02))
    paint_water(mesh_obj("Canal_Water", bm, col, root))
    bm = bmesh.new()
    n = 9
    for sx in (-1, 1):
        for k in range(n):
            y = Y0 + (k + 0.5) * (Y1 - Y0) / n
            bm_box(bm, (0.2, (Y1 - Y0) / n - 0.04, 0.16 + rnd.uniform(0, 0.04)), (sx * (HALF + 0.08), y, T + 0.08), rot=(0, 0, rnd.uniform(-2, 2)))
    for y in (Y0 - 0.08, Y1 + 0.08):
        bm_box(bm, (HALF * 2 + 0.36, 0.18, 0.17), (0, y, T + 0.085))
    o = paint(mesh_obj("Canal_Kerb", bm, col, root), "stone2", lo=0.15, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.015; b.segments = 1; b.limit_method = "ANGLE"
    # coral, kelp and shells along the kerbs
    cor, kelp, shells = bmesh.new(), bmesh.new(), bmesh.new()
    for i, (x, y) in enumerate(((-0.95, C[1].y + 0.3), (0.95, C[2].y - 0.2), (-0.95, C[3].y - 0.4), (0.92, C[0].y - 0.9))):
        bm_coral(cor, rnd, Vector((x, y, T)), h=rnd.uniform(0.35, 0.55), n=4, w=0.05)
    for (x, y) in ((0.95, C[1].y - 0.4), (-0.9, C[2].y + 0.5), (0.9, C[3].y + 0.3)):
        bm_kelp(kelp, rnd, Vector((x, y, T)), h=rnd.uniform(0.5, 0.75), n=3)
    bm_starfish(shells, Vector((-0.9, C[0].y - 0.2, T + 0.17)), r=0.14, yaw=20)
    bm_conch(shells, Vector((0.95, C[1].y + 0.6, T + 0.18)), length=0.26, yaw=70)
    paint(mesh_obj("Canal_Coral", cor, col, root), "salmon", lo=0.2, hi=0.8)
    paint(mesh_obj("Canal_Kelp", kelp, col, root), "lime", lo=0.2, hi=0.8)
    paint(mesh_obj("Canal_Shells", shells, col, root), "cream", lo=0.2, hi=0.7)
    head = empty("Head", col, root, tuple(NECK), 0.5, "SINGLE_ARROW")
    return root


# the coils: three arches breaking the water over the back cells, and the tail
ARCHES = [(C[1].y + 0.75, C[1].y - 0.55, 0.62, 0.27), (C[2].y + 0.45, C[2].y - 0.7, 0.55, 0.24), (C[3].y + 0.55, C[3].y - 0.45, 0.45, 0.2)]
# neck chain (in the Head's space: the base of the neck at the waterline)
NK = [Vector((0, 0, -0.1)), Vector((0, 0.12, 0.55)), Vector((0, -0.02, 1.08)), Vector((0, 0.2, 1.5))]
HEAD_C = Vector((0, 0.5, 1.62))
MOUTH = Vector((0, 1.02, 1.5))
HBONES = {"neck.root": ((0, 0, 0), (0, 0, 0.2), None),
          "neck.1": (tuple(NK[0]), tuple(NK[1]), "neck.root"),
          "neck.2": (tuple(NK[1]), tuple(NK[2]), "neck.1"),
          "neck.3": (tuple(NK[2]), tuple(NK[3]), "neck.2"),
          "skull": (tuple(NK[3]), tuple(HEAD_C), "neck.3"),
          "jaw": (tuple(HEAD_C + Vector((0, -0.15, -0.12))), tuple(MOUTH + Vector((0, -0.05, -0.12))), "skull"),
          "gush": (tuple(MOUTH), tuple(MOUTH + Vector((0, 0.3, 0))), "skull")}


def build_body():
    col = collection("Leviathan")
    root = bpy.data.objects["Leviathan"]

    def S(name, bm, sw, **kw):            # the coils lie still in the canal (one rig per tower: it's the neck's)
        return paint(mesh_obj(name, bm, col, root), sw, **kw)

    for i, (ya, yb, h, r) in enumerate(ARCHES):
        pts = []
        for k in range(9):
            t = k / 8
            y = ya + (yb - ya) * t
            z = WATER - 0.18 + (h + 0.18) * math.sin(math.pi * t)
            x = 0.12 * math.sin(math.pi * t * 2 + i) * (1 if i % 2 else -1)
            pts.append(Vector((x, y, z)))
        bm = bmesh.new()
        _blob_along(bm, pts, r, r * 0.92, n_per=2)
        S("Coil%d" % (i + 1), bm, BODY, lo=0.35, hi=0.85)
        bm = bmesh.new()                                     # a ridge of team fins along the top of each arch
        for k in range(2, 7):
            t = k / 8
            p = pts[k]
            bm_cyl(bm, r * 0.35, 0.0, r * 1.1, (p.x, p.y, p.z + r * 0.9), rot=(-25 if t < 0.5 else 25, 0, 0), seg=3)
        S("Coil%d_Fins" % (i + 1), bm, FIN, team=True, lo=0.15, hi=0.6)
    # the tail: a last thin rise ending in a fan fin
    bm = bmesh.new()
    tp = [Vector((0, C[3].y - 0.45, WATER - 0.15)), Vector((0.05, C[3].y - 0.62, WATER + 0.15)), Vector((0.08, C[3].y - 0.72, WATER + 0.42))]
    _blob_along(bm, tp, 0.14, 0.07, n_per=2)
    S("Tail", bm, BODY, lo=0.35, hi=0.85)
    bm = bmesh.new()
    tip = tp[-1]
    vs = [bm.verts.new(p) for p in (tip, tip + Vector((-0.38, -0.1, 0.42)), tip + Vector((0.0, -0.04, 0.24)), tip + Vector((0.38, -0.1, 0.42)))]
    bm.faces.new(vs)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
    S("Tail_Fin", bm, FIN, team=True, lo=0.15, hi=0.6)


def build_head():
    col = collection("Leviathan")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, HBONES)

    def P(name, bm, sw, bone, **kw):
        return rig_part(name, bm, sw, rig, bone, col, bevel=0, **kw)

    for j in range(3):
        bm = bmesh.new()
        r0, r1 = 0.3 - 0.04 * j, 0.26 - 0.04 * j
        _blob_along(bm, [NK[j], NK[j + 1]], r0, r1, n_per=3)
        P("Neck%d" % (j + 1), bm, BODY, "neck.%d" % (j + 1), lo=0.35, hi=0.85)
        bm = bmesh.new()                                      # pale throat plates down the front of the neck
        for k in range(3):
            p = NK[j].lerp(NK[j + 1], (k + 0.5) / 3)
            r = r0 + (r1 - r0) * (k + 0.5) / 3
            bm_ellipsoid(bm, tuple(p + Vector((0, r * 0.62, 0))), (r * 0.7, r * 0.45, r * 0.55), u=8, v=4)
        P("Neck%d_Belly" % (j + 1), bm, BELLY, "neck.%d" % (j + 1), lo=0.3, hi=0.75)
        bm = bmesh.new()
        p = NK[j].lerp(NK[j + 1], 0.5)
        bm_cyl(bm, 0.07, 0.0, 0.26, tuple(p + Vector((0, -r0 * 0.9, 0.05))), rot=(-60, 0, 0), seg=3)
        P("Neck%d_Fin" % (j + 1), bm, FIN, "neck.%d" % (j + 1), team=True, lo=0.15, hi=0.6)
    # the head: a long skull and snout, brow horns, frilled side fins, glowing eyes
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(HEAD_C), (0.3, 0.38, 0.26), u=12, v=8)
    bm_ellipsoid(bm, tuple(HEAD_C + Vector((0, 0.38, -0.06))), (0.21, 0.3, 0.16), u=10, v=6)
    for sx in (-1, 1):
        bm_box(bm, (0.14, 0.2, 0.06), tuple(HEAD_C + Vector((sx * 0.16, 0.16, 0.18))), rot=(10, 0, sx * -15))
    P("Skull", bm, BODY, "skull", lo=0.3, hi=0.85)
    bm = bmesh.new()
    for sx in (-1, 1):
        a = HEAD_C + Vector((sx * 0.14, 0.0, 0.2))
        b_ = HEAD_C + Vector((sx * 0.28, -0.35, 0.42))
        bm_beam(bm, a, b_, 0.08, 0.08, w1=0.02, h1=0.02)
        for k in range(4):                                     # upper fangs
            bm_cyl(bm, 0.025, 0.0, 0.08, tuple(HEAD_C + Vector((sx * (0.07 + 0.04 * k), 0.62 - 0.07 * k, -0.18))), rot=(180, 0, 0), seg=4)
    P("Skull_Horns", bm, "cream", "skull", lo=0.2, hi=0.5)
    bm = bmesh.new()                                           # frills: fanned fins behind the jaw
    for sx in (-1, 1):
        base = HEAD_C + Vector((sx * 0.22, -0.12, 0.0))
        vs = [bm.verts.new(base)]
        for k in range(4):
            a = math.radians(-30 + 25 * k)
            vs.append(bm.verts.new(base + Vector((sx * 0.38 * math.cos(a), -0.3 * math.cos(a) - 0.05, 0.38 * math.sin(a)))))
        for k in range(1, 4):
            bm.faces.new((vs[0], vs[k], vs[k + 1]) if sx > 0 else (vs[0], vs[k + 1], vs[k]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.025)
    P("Skull_Frills", bm, FIN, "skull", team=True, lo=0.15, hi=0.6)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_ellipsoid(bm, tuple(HEAD_C + Vector((sx * 0.21, 0.24, 0.1))), (0.07, 0.07, 0.05), u=7, v=4)
    P("Skull_Eyes", bm, None, "skull", mat=glow_mat("leviathan_eye", EYE, 1.4))
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(HEAD_C + Vector((0, 0.3, -0.2))), (0.2, 0.36, 0.08), u=10, v=5)
    for sx in (-1, 1):
        for k in range(3):
            bm_cyl(bm, 0.022, 0.0, 0.07, tuple(HEAD_C + Vector((sx * (0.08 + 0.04 * k), 0.56 - 0.08 * k, -0.15))), seg=4)
    P("Jaw", bm, BELLY, "jaw", lo=0.3, hi=0.7)
    # the gush: a burst of water out of the mouth, hidden at rest
    bm = bmesh.new()
    rnd = random.Random(4)
    bm_ellipsoid(bm, tuple(MOUTH + Vector((0, 0.35, 0))), (0.16, 0.42, 0.14), u=10, v=6)
    for k in range(6):
        a = 2 * math.pi * k / 6
        bm_ellipsoid(bm, tuple(MOUTH + Vector((math.cos(a) * 0.14, 0.25 + rnd.uniform(0, 0.25), math.sin(a) * 0.12))), (0.08, 0.14, 0.08), u=6, v=4)
    P("Gush", bm, None, "gush", mat=glow_mat("leviathan_jet", JET, 0.7))
    empty("Muzzle", col, head, tuple(MOUTH + Vector((0, 0.1, 0))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 26


def pose_neck(rig, t=0.0, rear=0.0, lunge=0.0, jaw=0.0, gush=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    sw = math.sin(2 * math.pi * t * 2)
    for j, k in ((1, 1.0), (2, -0.8), (3, 0.6)):
        q = arm_space_quat(pb["neck.%d" % j], (0, 0, 1), 5 * sw * k)
        q = arm_space_quat(pb["neck.%d" % j], (1, 0, 0), (12 * rear - 14 * lunge) * (0.6 if j == 1 else 1.0) + 2 * math.cos(2 * math.pi * t * 2)) @ q
        pb["neck.%d" % j].rotation_quaternion = q
    pb["skull"].rotation_quaternion = arm_space_quat(pb["skull"], (1, 0, 0), -10 * rear + 12 * lunge)
    pb["jaw"].rotation_quaternion = arm_space_quat(pb["jaw"], (1, 0, 0), -30 * jaw - 3 * (1 + math.sin(2 * math.pi * t * 4)))
    g = max(0.001, gush)
    pb["gush"].scale = (g, g, g)


def build_anims():
    neck = bpy.data.objects["Rig"]
    new_action(neck, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose_neck(neck, t=f / IDLE_LEN)
        key_pose(neck, f)
    new_action(neck, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 5.0) * (1 - smooth((f - 5) / 3.0))
        lunge = smooth((f - 5) / 3.0) * (1 - smooth((f - 12) / 12.0))
        jaw = smooth((f - 4) / 3.0) * (1 - smooth((f - 13) / 10.0))
        gush = 0.0 if f < 7 else 1.3 * smooth((f - 7) / 2.0) * (1 - smooth((f - 11) / 9.0))
        pose_neck(neck, t=0.0, rear=rear, lunge=lunge, jaw=jaw, gush=gush)
        key_pose(neck, f)
    neck.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.6, 0.8), "dist": 12.0, "yaw": 145, "pitch": 22, "anim_target": (0, C[0].y, 1.4), "anim_dist": 4.5,
           "frames": [("idle", 0), ("fire", 4), ("fire", 10)]}


def build_all():
    build_base()
    build_body()
    build_head()
    build_anims()
