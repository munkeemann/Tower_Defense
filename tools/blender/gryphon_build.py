"""Builds the Gryphon Roost (footprint "wing3": [0,0] the back cell, [1,-1] front-right, [-1,0] front-left; it fires from
both front cells).

    blender -b --factory-startup --python tools/blender/build_tower.py -- gryphon <preview dir>

A chunky low-poly gryphon (tan lion body, white feathered chest and head, hooked orange beak, gold talons, brown wings,
tufted tail) perches on a rocky aerie on the back cell; it's the Head, turning to aim, and its two shots leave from its
wings (Muzzle1 / Muzzle2). Front cells: a nest of golden eggs on a rock mound, and a perch post with a team pennant beside
a barrel and a sack. idle: it looks about, breathes, sways its tail, wings folded. fire: the wings snap open and beat,
the head thrusts forward with the beak open, then everything folds back.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "gryphon"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FR = hex_to_world(1, -1, MID)
FL = hex_to_world(-1, 0, MID)
TOP = 0.34
PERCH = 1.42
GS = 1.15                     # gryphon scale (laid out at 1.0)


def bm_ellipsoid(bm, center, radii, rot=(0, 0, 0), u=10, v=7):
    m = (Matrix.Translation(center) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
         @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=m)
    return bm


def _rock(bm, rnd, c, size, z0, h):
    rot = (rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 90))
    bm_box(bm, (size * rnd.uniform(0.85, 1.15), size * rnd.uniform(0.8, 1.1), h), (c.x, c.y, z0 + h / 2), rot)


def build_base():
    col = collection("Gryphon")
    root = empty("Gryphon", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(21)
    # the aerie: a crag of stacked rocks, a twig nest and straw on top
    C = BACK
    bm = bmesh.new()
    _rock(bm, rnd, C, 1.25, TOP, 0.36)
    _rock(bm, rnd, C + Vector((0.08, -0.05, 0)), 1.05, TOP + 0.34, 0.38)
    _rock(bm, rnd, C + Vector((-0.06, 0.04, 0)), 0.9, TOP + 0.7, 0.36)
    _rock(bm, rnd, C, 0.95, PERCH - 0.4, 0.3)
    for k in range(5):
        a = math.radians(72 * k + 20)
        p = C + Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, 0))
        _rock(bm, rnd, p, rnd.uniform(0.28, 0.4), TOP, rnd.uniform(0.2, 0.45))
    o = paint(mesh_obj("Aerie_Rocks", bm, col, root), "stone_warm", lo=0.1, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.04; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for k in range(16):
        a = math.radians(360 * k / 16 + rnd.uniform(-6, 6))
        a2 = a + math.radians(rnd.uniform(28, 40))
        r1, r2 = rnd.uniform(0.48, 0.58), rnd.uniform(0.48, 0.58)
        z = PERCH - 0.08 + rnd.uniform(-0.03, 0.05)
        bm_beam(bm, C + Vector((math.cos(a) * r1, math.sin(a) * r1, z)), C + Vector((math.cos(a2) * r2, math.sin(a2) * r2, z + 0.04)),
                0.05, 0.05)
    paint(mesh_obj("Aerie_Twigs", bm, col, root), "wood", lo=0.3, hi=0.8)
    bm = bmesh.new(); bm_cyl(bm, 0.5, 0.46, 0.08, (C.x, C.y, PERCH - 0.06), seg=12)
    paint(mesh_obj("Aerie_Straw", bm, col, root), "gold", lo=0.2, hi=0.5)
    # a team banner pole stuck in the crag
    bm = bmesh.new()
    pp = C + Vector((-0.55, -0.3, 0))
    bm_cyl(bm, 0.03, 0.03, 1.9, (pp.x, pp.y, TOP + 0.95), seg=6)
    paint(mesh_obj("Aerie_Pole", bm, col, root), "wood_dark", lo=0.2, hi=0.6)
    bm = bmesh.new()
    pts = [Vector((pp.x, pp.y, TOP + 1.85)), Vector((pp.x - 0.5, pp.y - 0.08, TOP + 1.76)), Vector((pp.x, pp.y, TOP + 1.55))]
    for off in (0.0, 0.01):
        vs = [bm.verts.new(p + Vector((0, off, 0))) for p in pts]
        bm.faces.new(vs if off > 0 else list(reversed(vs)))
    paint(mesh_obj("Aerie_Pennant", bm, col, root), "team", team=True, lo=0.2, hi=0.6)

    # front-left: a rock mound with a nest of golden eggs
    bm = bmesh.new()
    _rock(bm, rnd, FL, 0.8, TOP, 0.22)
    _rock(bm, rnd, FL + Vector((0.05, 0.02, 0)), 0.6, TOP + 0.2, 0.16)
    o = paint(mesh_obj("Nest_Rocks", bm, col, root), "stone_warm", lo=0.2, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    nz = TOP + 0.38
    for k in range(12):
        a = math.radians(30 * k + rnd.uniform(-8, 8))
        a2 = a + math.radians(rnd.uniform(30, 45))
        bm_beam(bm, FL + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, nz)), FL + Vector((math.cos(a2) * 0.32, math.sin(a2) * 0.32, nz + 0.04)),
                0.045, 0.045)
    paint(mesh_obj("Nest_Twigs", bm, col, root), "wood", lo=0.3, hi=0.8)
    bm = bmesh.new()
    for k, (dx, dy, rz) in enumerate(((0.0, 0.0, 0), (0.13, 0.06, 30), (-0.1, 0.1, -20))):
        bm_ellipsoid(bm, FL + Vector((dx, dy, nz + 0.1)), (0.085, 0.085, 0.12), (rz * 0.3, 0, rz))
    paint(mesh_obj("Nest_Eggs", bm, col, root), "gold", lo=0.05, hi=0.4)

    # front-right: a perch post with a pennant, a barrel and a sack of feed
    bm = bmesh.new()
    pp = FR + Vector((0.25, 0.15, 0))
    bm_box(bm, (0.12, 0.12, 1.3), (pp.x, pp.y, TOP + 0.65))
    bm_box(bm, (0.7, 0.1, 0.1), (pp.x, pp.y, TOP + 1.25))
    bm_beam(bm, (pp.x, pp.y, TOP + 0.95), (pp.x + 0.22, pp.y, TOP + 1.22), 0.06, 0.06)
    bm_beam(bm, (pp.x, pp.y, TOP + 0.95), (pp.x - 0.22, pp.y, TOP + 1.22), 0.06, 0.06)
    bm_box(bm, (0.3, 0.3, 0.1), (pp.x, pp.y, TOP + 0.05))
    paint(mesh_obj("Perch_Post", bm, col, root), "wood", lo=0.2, hi=0.8)
    bm = bmesh.new()
    pts = [Vector((pp.x + 0.3, pp.y, TOP + 1.2)), Vector((pp.x + 0.3, pp.y, TOP + 0.85)), Vector((pp.x + 0.18, pp.y, TOP + 0.95)),
           Vector((pp.x + 0.06, pp.y, TOP + 0.85)), Vector((pp.x + 0.06, pp.y, TOP + 1.2))]
    for off in (0.055, 0.065):
        vs = [bm.verts.new(p + Vector((0, off, 0))) for p in pts]
        bm.faces.new(vs if off > 0.06 else list(reversed(vs)))
    paint(mesh_obj("Perch_Pennant", bm, col, root), "team", team=True, lo=0.2, hi=0.6)
    kk = [("hex/barrel", (FR.x - 0.35, FR.y + 0.3, TOP), 20, 2.3), ("hex/sack", (FR.x - 0.3, FR.y - 0.25, TOP), 60, 2.4)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    empty("Head", col, root, (C.x, C.y, PERCH), 0.5, "SINGLE_ARROW")
    return root


# ---- the gryphon, laid out at 1.0 in the head's space (+Y forward), scaled by GS
WING = {"root": (0.28, 0.12, 0.88), "elbow": (0.78, -0.12, 1.22), "tip": (1.36, -0.32, 1.12)}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "body": ((0, 0, 0.45), (0, 0.2, 0.62), "root"),
    "neck": ((0, 0.4, 0.9), (0, 0.48, 1.14), "body"),
    "head": ((0, 0.48, 1.14), (0, 0.72, 1.24), "neck"),
    "jaw": ((0, 0.62, 1.2), (0, 0.78, 1.16), "head"),
    "wing.L.1": ((-WING["root"][0], WING["root"][1], WING["root"][2]), (-WING["elbow"][0], WING["elbow"][1], WING["elbow"][2]), "body"),
    "wing.L.2": ((-WING["elbow"][0], WING["elbow"][1], WING["elbow"][2]), (-WING["tip"][0], WING["tip"][1], WING["tip"][2]), "wing.L.1"),
    "wing.R.1": (WING["root"], WING["elbow"], "body"),
    "wing.R.2": (WING["elbow"], WING["tip"], "wing.R.1"),
    "tail.1": ((0, -0.48, 0.26), (0, -0.88, 0.32), "body"),
    "tail.2": ((0, -0.88, 0.32), (0, -1.12, 0.62), "tail.1"),
}


def _feathers(bm, a, b, side, n, length, spread, lean_out=0.5):
    """Flat feathers hanging down and back from the edge a->b (both sides of each feather)."""
    d = b - a
    for i in range(n):
        u = (i + 0.5) / n
        root = a + d * u
        ln = length * (0.8 + 0.4 * u)
        ang = math.radians(-15 - spread * u)
        dirv = (Vector((0, 0, -1)) * math.cos(ang) + Vector((side, 0, 0)) * -math.sin(ang) * lean_out + Vector((0, -1, 0)) * 0.3).normalized()
        w = 0.17
        sv = d.normalized() * w
        pts = [root - sv * 0.5, root + sv * 0.5, root + dirv * ln * 0.75 + sv * 0.3, root + dirv * ln]
        for off in (0.007, -0.007):
            vs = [bm.verts.new(p + Vector((0, off, 0))) for p in pts]
            bm.faces.new(vs if off < 0 else list(reversed(vs)))


def build_head():
    col = collection("Gryphon")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = make_rig(col, head, BONES, scale=GS)

    def P(name, bm, swatch, bone, **kw):
        return rig_part(name, bm, swatch, rig, bone, col, bevel=0, scale=GS, **kw)

    # body: a lion's barrel tilted up at the front, haunches, hind paws
    bm = bmesh.new()
    bm_ellipsoid(bm, Vector((0, 0.02, 0.56)), (0.34, 0.56, 0.38), (32, 0, 0))
    for sx in (-1, 1):
        bm_ellipsoid(bm, Vector((sx * 0.24, -0.28, 0.3)), (0.17, 0.26, 0.24), (10, 0, 0))
        bm_ellipsoid(bm, Vector((sx * 0.26, -0.08, 0.06)), (0.1, 0.17, 0.06))
    P("Head_Body", bm, "sand", "body", lo=0.15, hi=0.8)
    # chest ruff and the feathered neck
    bm = bmesh.new()
    bm_ellipsoid(bm, Vector((0, 0.34, 0.8)), (0.3, 0.26, 0.32), (20, 0, 0))
    P("Head_Ruff", bm, "white", "body", lo=0.05, hi=0.5)
    bm = bmesh.new()
    bm_ellipsoid(bm, Vector((0, 0.45, 1.02)), (0.17, 0.17, 0.2), (25, 0, 0))
    P("Head_Neck", bm, "white", "neck", lo=0.05, hi=0.4)
    # the eagle head: skull, ear tufts, eyes, hooked upper beak
    bm = bmesh.new()
    bm_ellipsoid(bm, Vector((0, 0.53, 1.24)), (0.19, 0.23, 0.18))
    for sx in (-1, 1):
        bm_cyl(bm, 0.05, 0.0, 0.2, (sx * 0.1, 0.42, 1.42), rot=(-35, sx * 15, 0), seg=4)
    P("Head_Head", bm, "white", "head", lo=0.05, hi=0.45)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_ellipsoid(bm, Vector((sx * 0.12, 0.66, 1.29)), (0.04, 0.03, 0.045), u=6, v=4)
    P("Head_Eyes", bm, "black", "head", lo=0.3, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.085, 0.02, 0.22, (0, 0.8, 1.23), rot=(-90, 0, 0), seg=6)
    bm_cyl(bm, 0.03, 0.0, 0.09, (0, 0.9, 1.18), rot=(180, 0, 0), seg=5)
    P("Head_Beak", bm, "orange", "head", lo=0.1, hi=0.5)
    bm = bmesh.new()
    bm_cyl(bm, 0.06, 0.015, 0.15, (0, 0.74, 1.15), rot=(-100, 0, 0), seg=6)
    P("Head_Jaw", bm, "orange", "jaw", lo=0.3, hi=0.6)
    # eagle forelegs with talons
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_beam(bm, Vector((sx * 0.15, 0.36, 0.55)), Vector((sx * 0.17, 0.44, 0.06)), 0.11, 0.11, w1=0.07, h1=0.07)
        for k in range(3):
            a = math.radians(-30 + 30 * k)
            base = Vector((sx * 0.17, 0.44, 0.04))
            tip = base + Vector((math.sin(a) * 0.12, math.cos(a) * 0.14, -0.02))
            bm_beam(bm, base, tip, 0.04, 0.04, w1=0.0, h1=0.0)
    P("Head_Talons", bm, "gold", "body", lo=0.1, hi=0.45)
    # wings: brown feathers under a sand-colored leading edge
    for s, sx in (("R", 1), ("L", -1)):
        r = Vector((sx * WING["root"][0], WING["root"][1], WING["root"][2]))
        e = Vector((sx * WING["elbow"][0], WING["elbow"][1], WING["elbow"][2]))
        t = Vector((sx * WING["tip"][0], WING["tip"][1], WING["tip"][2]))
        for seg, (a, b, n, ln, spr) in {1: (r, e, 5, 0.5, 20), 2: (e, t, 8, 0.78, 40)}.items():
            bm = bmesh.new()
            _feathers(bm, a, b, sx, n, ln, spr)
            P("Head_Wing.%s.%d" % (s, seg), bm, "wood", "wing.%s.%d" % (s, seg), lo=0.2, hi=0.75)
            bm = bmesh.new()
            bm_beam(bm, a, b, 0.11, 0.08, w1=0.08, h1=0.06, up=(0, -1, 0))
            P("Head_WingArm.%s.%d" % (s, seg), bm, "sand", "wing.%s.%d" % (s, seg), lo=0.2, hi=0.6)
    # tail: two segments and a dark tuft
    bm = bmesh.new()
    bm_beam(bm, Vector((0, -0.46, 0.27)), Vector((0, -0.9, 0.32)), 0.08, 0.08, w1=0.06, h1=0.06)
    P("Head_Tail1", bm, "sand", "tail.1", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_beam(bm, Vector((0, -0.88, 0.32)), Vector((0, -1.1, 0.58)), 0.06, 0.06, w1=0.05, h1=0.05)
    bm_ellipsoid(bm, Vector((0, -1.13, 0.66)), (0.08, 0.08, 0.13), (-30, 0, 0), u=6, v=5)
    P("Head_Tail2", bm, "wood_dark", "tail.2", lo=0.2, hi=0.6)
    # shots leave from the wings
    for i, sx in enumerate((-1, 1)):
        empty("Muzzle%d" % (i + 1), col, head, (sx * 0.9 * GS, 0.2 * GS, 1.15 * GS), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 22
FOLD = {"yaw": 62.0, "roll": 38.0, "bend": 70.0}     # how the wings fold against the body at rest


def pose(rig, look=0.0, nod=0.0, breathe=0.0, tail=0.0, open_=0.0, flap=0.0, beak=0.0, thrust=0.0):
    """open_: 0 folded .. 1 spread; flap: extra beat (degrees) on top of the spread."""
    pb = rig.pose.bones
    rest_pose(rig)
    pb["body"].scale = (1 + breathe, 1 + breathe, 1 + breathe)
    pb["neck"].rotation_quaternion = arm_space_quat(pb["neck"], (1, 0, 0), -thrust * 18) @ arm_space_quat(pb["neck"], (0, 0, 1), look * 0.4)
    pb["head"].rotation_quaternion = arm_space_quat(pb["head"], (0, 0, 1), look * 0.6) @ arm_space_quat(pb["head"], (1, 0, 0), nod - thrust * 10)
    pb["jaw"].rotation_quaternion = arm_space_quat(pb["jaw"], (1, 0, 0), -beak)
    f = 1.0 - open_
    for s, sg in (("R", 1), ("L", -1)):
        q1 = (arm_space_quat(pb["wing.%s.1" % s], (0, 0, 1), -sg * FOLD["yaw"] * f)
              @ arm_space_quat(pb["wing.%s.1" % s], (0, 1, 0), sg * (FOLD["roll"] * f + flap)))
        pb["wing.%s.1" % s].rotation_quaternion = q1
        pb["wing.%s.2" % s].rotation_quaternion = arm_space_quat(pb["wing.%s.2" % s], (0, 0, 1), -sg * FOLD["bend"] * f) @ \
            arm_space_quat(pb["wing.%s.2" % s], (0, 1, 0), sg * flap * 0.6)
    pb["tail.1"].rotation_quaternion = arm_space_quat(pb["tail.1"], (0, 0, 1), tail)
    pb["tail.2"].rotation_quaternion = arm_space_quat(pb["tail.2"], (0, 0, 1), tail * 1.4)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        look = 28 * math.sin(ph) * (0.5 + 0.5 * math.sin(ph * 0.5))
        ruffle = max(0.0, math.sin(ph * 2 - 1.0)) ** 6 * 0.25
        pose(rig, look=look, nod=4 * math.sin(ph * 2), breathe=0.025 * math.sin(ph * 3), tail=18 * math.sin(ph + 0.6),
             open_=ruffle, flap=ruffle * 20)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        op = smooth(f / 3.0) * (1.0 - smooth((f - 12) / 9.0))
        flap = 35 * math.sin(math.pi * min(f / 9.0, 1.0)) * (1 - smooth((f - 9) / 6.0)) - 10 * smooth(f / 2.0) * (1 - smooth((f - 4) / 3.0))
        thrust = smooth(f / 3.0) * (1.0 - smooth((f - 7) / 8.0))
        beak = 28 * smooth(f / 2.0) * (1.0 - smooth((f - 8) / 6.0))
        pose(rig, open_=op, flap=flap, thrust=thrust, beak=beak, tail=12 * math.sin(math.pi * f / FIRE_LEN))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.4), "dist": 9.0, "yaw": 150, "pitch": 20, "anim_target": (BACK.x, BACK.y, 2.3), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 24), ("fire", 3), ("fire", 8), ("fire", 18)]}


def build_all():
    build_base()
    build_head()
    build_anims()
