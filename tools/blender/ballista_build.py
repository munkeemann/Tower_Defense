"""Builds the Ballista tower (footprint "line3": cells [0,0], [0,1], [0,2], front = +Y here = Godot -Z).

Run in Blender after kk_helpers.py:
    exec(open(r"<repo>/tools/blender/kk_helpers.py").read())
    exec(open(r"<repo>/tools/blender/ballista_build.py").read())
    build_all()            # or build_base() / build_head() / build_anims() one at a time

Hierarchy (what the game reads):
    Ballista                 root, on the footprint's centroid at ground level
      Base_*                 static stone plinth, deck, dais, props
      Head                   turns to aim (the game sets its yaw); +Y is forward
        Rig                  armature: root, stock, arm.L/R, string.L/R, nock, slider, bolt, winch, rope, flag.*
        Head_* meshes        rigid-skinned to Rig's bones
        Muzzle               bolts leave from here
        Crew                 where the game stands its winch operator
Animations on Rig: idle (loops), fire (the arms snap, the string releases, the bolt leaves), reload (winch cranks,
the slider drags the string back, a new bolt drops in). The rest pose is cocked and loaded (= idle).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "ballista"
CELLS = [(0, 0), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)          # front cell center (0, 2.078)
HEAD_Z = 0.53                            # dais + track top

# ---- head layout (head-local, +Y forward)
PIVOT_Z = 0.64          # stock pin
BOLT_Z = 0.83           # bolt, string and arms all at this height
SPRING_X = 0.34
SPRING_Y = 0.86
ARM_LEN = 0.85
COCK = 40.0             # arm angle behind the lateral line when drawn
REST = 10.0             # ... when released
SNAP = 2.0              # ... at the end of the snap (overshoot)
FRAME_Y0, FRAME_Y1 = 0.78, 1.0
HEAD_SCALE = 1.3        # the head is laid out at 1.0, then scaled up by this (the turntable keeps its size)


def arm_tip(side, ang):
    a = math.radians(ang)
    return Vector((side * (SPRING_X + ARM_LEN * math.cos(a)), SPRING_Y - ARM_LEN * math.sin(a), BOLT_Z))


def released_nock_y():
    return arm_tip(1, REST).y


def _nock_cocked():
    # the string keeps its length: released it runs straight between the tips; drawn it makes a V to the nock
    half = arm_tip(1, REST).x
    t = arm_tip(1, COCK)
    return t.y - math.sqrt(half * half - t.x * t.x)


NOCK_COCKED = _nock_cocked()
WINCH_Y = NOCK_COCKED - 0.24
STOCK_Y0, STOCK_Y1 = WINCH_Y - 0.12, FRAME_Y1


# ================================================================================================ base
def build_base():
    col = collection("Ballista")
    root = empty("Ballista", col, None, (0, 0, 0), 0.6, "ARROWS")
    bm = bmesh.new(); prism(bm, outline(CELLS, 0.05), -0.06, 0.16)
    paint(mesh_obj("Base_Plinth", bm, col, root), "stone_dark")
    bm = bmesh.new(); prism(bm, outline(CELLS, 0.13), 0.16, 0.34)
    o = paint(mesh_obj("Base_Wall", bm, col, root), "stone", lo=0.05, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.035; b.segments = 1; b.limit_method = "ANGLE"

    import random
    random.seed(3)

    def half_w(y, ins):
        best = -1
        for q, s in CELLS:
            c = hex_to_world(q, s, MID)
            dy = abs(y - c.y)
            if dy <= HEX_R * SQ3 / 2:
                best = max(best, HEX_R - dy / SQ3)
        return best - ins
    bm = bmesh.new()
    y = FRONT.y - 1.0
    pw = 0.27
    while y - pw > -3.05:
        hw = min(half_w(y - 0.02, 0.2), half_w(y - pw + 0.02, 0.2))
        if hw > 0.15:
            j = random.uniform(-0.04, 0.04)
            bm_box(bm, (2 * hw + j, pw - 0.03, 0.07), (j * 0.5, y - pw / 2, 0.37), (0, 0, random.uniform(-1.2, 1.2)))
        y -= pw
    o = paint(mesh_obj("Base_Deck", bm, col, root), "wood", lo=0.35, hi=0.85)
    me = o.data
    uv = me.uv_layers.active.data
    for p in me.polygons:
        if int((p.center.y + 10) / pw) % 3 == 1:
            for li in p.loop_indices:
                uv[li].uv = (uv[li].uv[0], uv[li].uv[1] - 0.03)

    bm = bmesh.new(); bm_cyl(bm, 1.0, 1.0, 0.2, (FRONT.x, FRONT.y, 0.40), seg=16)
    o = paint(mesh_obj("Base_Dais", bm, col, root), "stone", lo=0.05, hi=0.5)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.03; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new(); ring(bm, (FRONT.x, FRONT.y, 0), 0.95, 0.83, 0.50, HEAD_Z, seg=24)
    paint(mesh_obj("Base_Track", bm, col, root), "iron")
    head = empty("Head", col, root, (FRONT.x, FRONT.y, HEAD_Z), 0.5, "SINGLE_ARROW")
    head.rotation_mode = "XYZ"
    head.rotation_euler = (0, 0, 0)
    return root


# ================================================================================================ head
BONES = {
    # name: (head, tail, parent)
    "root": ((0, 0, 0), (0, 0, 0.3), None),
    "stock": ((0, 0, PIVOT_Z), (0, 0.4, PIVOT_Z), "root"),
    "arm.L": ((-SPRING_X, SPRING_Y, BOLT_Z), tuple(arm_tip(-1, COCK)), "stock"),
    "arm.R": ((SPRING_X, SPRING_Y, BOLT_Z), tuple(arm_tip(1, COCK)), "stock"),
    "nock": ((0, NOCK_COCKED, BOLT_Z), (0, NOCK_COCKED - 0.15, BOLT_Z), "stock"),
    "string.L": (tuple(arm_tip(-1, COCK)), (0, NOCK_COCKED, BOLT_Z), "arm.L"),
    "string.R": (tuple(arm_tip(1, COCK)), (0, NOCK_COCKED, BOLT_Z), "arm.R"),
    "slider": ((0, NOCK_COCKED, 0.78), (0, NOCK_COCKED - 0.15, 0.78), "stock"),
    "bolt": ((0, NOCK_COCKED + 0.04, BOLT_Z), (0, 1.25, BOLT_Z), "stock"),
    "winch": ((0, WINCH_Y, 0.80), (0.3, WINCH_Y, 0.80), "stock"),
    "rope": ((0, WINCH_Y + 0.07, 0.80), (0, NOCK_COCKED - 0.08, 0.78), "stock"),
    "flag.0": ((0.52, 0.89, 1.2), (0.52, 0.89, 1.82), "stock"),
    "flag.1": ((0.52, 0.89, 1.74), (0.52, 0.73, 1.72), "flag.0"),
    "flag.2": ((0.52, 0.73, 1.72), (0.52, 0.57, 1.71), "flag.1"),
    "flag.3": ((0.52, 0.57, 1.71), (0.52, 0.41, 1.70), "flag.2"),
}


def build_rig():
    col = collection("Ballista")
    head = bpy.data.objects["Head"]
    old = bpy.data.objects.get("Rig")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    col.objects.link(rig)
    rig.parent = head
    arm.display_type = "STICK"
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    with view3d_override(rig):
        bpy.ops.object.mode_set(mode="EDIT")
        eb = {}
        for name, (h, t, par) in BONES.items():
            b = arm.edit_bones.new(name)
            b.head = Vector(h) * HEAD_SCALE
            b.tail = Vector(t) * HEAD_SCALE
            b.roll = 0.0
            if par:
                b.parent = eb[par]
            eb[name] = b
        bpy.ops.object.mode_set(mode="OBJECT")
    for side in ("L", "R"):
        pb = rig.pose.bones["string." + side]
        c = pb.constraints.new("STRETCH_TO")
        c.target = rig
        c.subtarget = "nock"
        c.volume = "NO_VOLUME"
        c.keep_axis = "SWING_Y"
    c = rig.pose.bones["rope"].constraints.new("STRETCH_TO")
    c.target = rig
    c.subtarget = "slider"
    c.volume = "NO_VOLUME"
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return rig


def part(name, bm, swatch, bone, team=False, bevel=0.012, **kw):
    """A head piece laid out at scale 1.0 (scaled up by HEAD_SCALE here), painted and rigid-skinned to `bone`."""
    col = collection("Ballista")
    rig = bpy.data.objects["Rig"]
    bmesh.ops.scale(bm, vec=(HEAD_SCALE,) * 3, verts=bm.verts)
    o = mesh_obj(name, bm, col, rig)
    paint(o, swatch, team=team, **kw)
    if bevel > 0:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel * HEAD_SCALE
        b.segments = 1
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
    skin_to(o, rig, bone)
    return o


def build_head():
    rig = build_rig()
    col = collection("Ballista")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    S = HEAD_SCALE

    # ---- turntable and trestles (root bone: they only turn with the head). The turntable keeps its real size.
    bm = bmesh.new(); bm_cyl(bm, 0.9 / S, 0.9 / S, 0.1 / S, (0, 0, 0.05 / S), seg=16)
    part("Head_Turntable", bm, "wood", "root", lo=0.45, hi=0.8)
    bm = bmesh.new(); ring(bm, (0, 0, 0), 0.92 / S, 0.84 / S, 0.015 / S, 0.085 / S, seg=20)
    part("Head_TurntableBand", bm, "iron", "root", bevel=0)
    tt = 0.1 / S          # turntable top
    bm = bmesh.new()
    for sx in (-1, 1):
        x = sx * 0.21
        bm_beam(bm, (x, -0.46, tt + 0.04), (x, 0.46, tt + 0.04), 0.12, 0.08)                      # sole
        bm_beam(bm, (x, -0.4, tt + 0.02), (x, -0.03, PIVOT_Z + 0.05), 0.1, 0.09, up=(0, 1, 0))      # legs
        bm_beam(bm, (x, 0.4, tt + 0.02), (x, 0.03, PIVOT_Z + 0.05), 0.1, 0.09, up=(0, 1, 0))
        bm_beam(bm, (x, -0.24, 0.33), (x, 0.24, 0.33), 0.08, 0.06)                                 # rung
    bm_beam(bm, (-0.26, 0.0, 0.17), (0.26, 0.0, 0.17), 0.08, 0.08)                                  # cross tie
    part("Head_Trestle", bm, "wood", "root", lo=0.25, hi=0.75)
    bm = bmesh.new()
    bm_cyl(bm, 0.045, 0.045, 0.62, (0, 0, PIVOT_Z), rot=(0, 90, 0), seg=8)
    for sx in (-1, 1):
        bm_cyl(bm, 0.07, 0.07, 0.03, (sx * 0.3, 0, PIVOT_Z), rot=(0, 90, 0), seg=8)
    part("Head_Pin", bm, "iron", "root", bevel=0)

    # ---- stock: beam, rails, iron bands, ratchet, winch cheeks
    sy, sl = (STOCK_Y0 + STOCK_Y1) / 2, STOCK_Y1 - STOCK_Y0
    bm = bmesh.new()
    bm_box(bm, (0.22, sl, 0.2), (0, sy, 0.66))
    part("Head_Stock", bm, "wood", "stock", lo=0.3, hi=0.85)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.05, sl - 0.06, 0.05), (sx * 0.075, sy, 0.785))
    part("Head_Rails", bm, "wood_red", "stock", lo=0.2, hi=0.6, bevel=0.006)
    bm = bmesh.new()
    for y in (STOCK_Y0 + 0.36, 0.42):
        bm_box(bm, (0.25, 0.05, 0.23), (0, y, 0.66))
    for sx in (-1, 1):
        for k in range(6):
            y = NOCK_COCKED - 0.05 + k * 0.12
            bm_beam(bm, (sx * 0.115, y, 0.62), (sx * 0.115, y + 0.09, 0.66), 0.03, 0.03, w1=0.03, h1=0.005)
    part("Head_StockIron", bm, "iron", "stock", bevel=0)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (0.05, 0.26, 0.3), (sx * 0.135, WINCH_Y, 0.74))
    part("Head_WinchCheeks", bm, "wood", "stock", lo=0.3, hi=0.8)

    # ---- front frame with torsion springs
    fy = (FRAME_Y0 + FRAME_Y1) / 2
    dy = FRAME_Y1 - FRAME_Y0
    bm = bmesh.new()
    bm_box(bm, (1.24, dy, 0.12), (0, fy, 1.16))                  # top beam
    bm_box(bm, (1.24, dy, 0.12), (0, fy, 0.46))                  # bottom beam
    for sx in (-1, 1):
        bm_box(bm, (0.1, 0.09, 0.6), (sx * 0.57, 0.955, 0.81))   # outer posts (front half: the arms swing behind them)
        bm_box(bm, (0.08, dy, 0.6), (sx * 0.15, fy, 0.81))       # inner posts beside the bolt channel
    part("Head_Frame", bm, "wood", "stock", lo=0.2, hi=0.75)
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_cyl(bm, 0.11, 0.11, 0.58, (sx * SPRING_X, SPRING_Y, 0.81), seg=10)
    part("Head_Springs", bm, "sand", "stock", lo=0.2, hi=0.8, bevel=0)
    bm = bmesh.new()
    for sx in (-1, 1):
        for z in (0.62, 1.0):
            ring(bm, (sx * SPRING_X, SPRING_Y, 0), 0.118, 0.1, z - 0.02, z + 0.02, seg=10)    # rope bands
    part("Head_SpringBands", bm, "wood_dark", "stock", lo=0.4, hi=0.6, bevel=0)
    bm = bmesh.new()
    for sx in (-1, 1):
        for z in (1.245, 0.375):
            bm_cyl(bm, 0.15, 0.15, 0.05, (sx * SPRING_X, SPRING_Y, z), seg=12)
        bm_box(bm, (0.38, 0.06, 0.05), (sx * SPRING_X, SPRING_Y, 1.29), (0, 0, sx * 25))    # tension levers
        for z in (1.16, 0.46):                                                            # corner plates
            bm_box(bm, (0.13, dy + 0.02, 0.14), (sx * 0.57, fy, z))
    part("Head_FrameIron", bm, "iron", "stock", bevel=0.006)

    # ---- arms (rest = drawn back)
    for side, sx in (("L", -1), ("R", 1)):
        bm = bmesh.new()
        p0 = Vector((sx * SPRING_X, SPRING_Y, BOLT_Z))
        p1 = arm_tip(sx, COCK)
        bm_beam(bm, p0, p1, 0.11, 0.15, w1=0.07, h1=0.09)
        part("Head_Arm." + side, bm, "wood_red", "arm." + side, lo=0.15, hi=0.6)
        bm = bmesh.new()
        d = (p1 - p0).normalized()
        bm_beam(bm, p1 - d * 0.13, p1 + d * 0.035, 0.09, 0.11)
        part("Head_ArmCap." + side, bm, "iron", "arm." + side, bevel=0.006)
        # string half: from the tip to the nock along the string bone
        bm = bmesh.new()
        bm_beam(bm, arm_tip(sx, COCK), (0, NOCK_COCKED, BOLT_Z), 0.035, 0.035)
        part("Head_String." + side, bm, "cream", "string." + side, lo=0.08, hi=0.25, bevel=0)

    # ---- nock (claw) and slider
    bm = bmesh.new()
    bm_box(bm, (0.11, 0.08, 0.08), (0, NOCK_COCKED - 0.03, BOLT_Z))
    part("Head_Nock", bm, "iron", "nock", bevel=0)
    bm = bmesh.new()
    bm_box(bm, (0.2, 0.22, 0.06), (0, NOCK_COCKED - 0.08, 0.78))
    bm_box(bm, (0.04, 0.1, 0.1), (0.07, NOCK_COCKED - 0.1, 0.84))       # trigger lever
    part("Head_Slider", bm, "wood_red", "slider", lo=0.2, hi=0.6, bevel=0.006)

    # ---- bolt: shaft, iron head, team fletching
    b0 = NOCK_COCKED + 0.04
    bl = FRAME_Y1 + 0.12 - b0
    bm = bmesh.new()
    bm_cyl(bm, 0.042, 0.042, bl, (0, b0 + bl / 2, BOLT_Z), rot=(-90, 0, 0), seg=6)
    part("Head_Bolt", bm, "wood", "bolt", lo=0.15, hi=0.35, bevel=0)
    bm = bmesh.new()
    bm_cyl(bm, 0.095, 0.0, 0.3, (0, b0 + bl + 0.15, BOLT_Z), rot=(-90, 0, 0), seg=4)
    bm_cyl(bm, 0.052, 0.052, 0.07, (0, b0 + bl - 0.02, BOLT_Z), rot=(-90, 0, 0), seg=6)
    part("Head_BoltTip", bm, "stone", "bolt", lo=0.1, hi=0.5, bevel=0)
    bm = bmesh.new()
    for k in range(3):
        a = math.radians(90 + 120 * k)
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((0, b0 + 0.2, BOLT_Z)) + d * 0.085
        bm_beam(bm, c + Vector((0, -0.17, 0)) + d * 0.02, c + Vector((0, 0.17, 0)) - d * 0.035, 0.014, 0.11, w1=0.014,
                h1=0.025, up=tuple(d))
    part("Head_Fletching", bm, "team", "bolt", team=True, lo=0.15, hi=0.6, bevel=0)

    # ---- winch drum, crank wheels, rope
    bm = bmesh.new()
    bm_cyl(bm, 0.075, 0.075, 0.22, (0, WINCH_Y, 0.80), rot=(0, 90, 0), seg=8)
    part("Head_WinchDrum", bm, "wood_red", "winch", lo=0.3, hi=0.7, bevel=0)
    bm = bmesh.new()
    for sx in (-1, 1):
        x = sx * 0.2
        bm_cyl(bm, 0.05, 0.05, 0.08, (x, WINCH_Y, 0.80), rot=(0, 90, 0), seg=8)
        for k in range(4):
            a = math.radians(45 + 90 * k)
            tip = Vector((x, WINCH_Y + math.cos(a) * 0.22, 0.80 + math.sin(a) * 0.22))
            bm_beam(bm, (x, WINCH_Y, 0.80), tip, 0.035, 0.035)
            bm_cyl(bm, 0.03, 0.03, 0.1, tip + Vector((sx * 0.05, 0, 0)), rot=(0, 90, 0), seg=6)
    part("Head_WinchSpokes", bm, "iron", "winch", bevel=0)
    bm = bmesh.new()
    bm_beam(bm, BONES["rope"][0], BONES["rope"][1], 0.03, 0.03)
    part("Head_Rope", bm, "sand", "rope", lo=0.3, hi=0.5, bevel=0)

    # ---- pennant on the frame
    bm = bmesh.new()
    bm_cyl(bm, 0.025, 0.025, 0.64, (0.52, 0.89, 1.5), seg=6)
    bm_cyl(bm, 0.045, 0.0, 0.09, (0.52, 0.89, 1.86), seg=6)
    part("Head_FlagPole", bm, "wood_dark", "flag.0", lo=0.2, hi=0.6, bevel=0)
    for k in (1, 2, 3):
        h0, t0, _ = BONES["flag.%d" % k]
        top0, top1 = Vector(h0), Vector(t0)
        hh0 = 0.28 - 0.075 * (k - 1)
        hh1 = 0.28 - 0.075 * k
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in (top0, top1, top1 - Vector((0, 0, hh1)), top0 - Vector((0, 0, hh0)))]
        bm.faces.new(vs)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0.004, 0, 0))) for v in vs])))
        part("Head_Flag.%d" % k, bm, "team", "flag.%d" % k, team=True, lo=0.2, hi=0.7, bevel=0)

    # ---- markers the game reads (in the head's space, already scaled)
    empty("Muzzle", col, head, (0, (b0 + bl + 0.3) * S, BOLT_Z * S), 0.25, "SPHERE")
    crank = Vector((0.2 * S + 0.08, WINCH_Y * S, 0))
    spot = Vector((0.62, -0.5, tt * S))
    crew = empty("Crew", col, head, tuple(spot), 0.3, "SINGLE_ARROW")
    to = crank - spot
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))   # its +Y (the character's front) faces the crank
    return rig


# ================================================================================================ props on the deck
DECK_Z = 0.405          # top of the plank deck


def _bolt(bms, start, direction, length, r=0.042):
    """A spare bolt (shaft, iron head, team fletching) into bms = (wood, iron, team) bmeshes."""
    d = Vector(direction).normalized()
    p0 = Vector(start)
    rot = d.to_track_quat("Z", "Y").to_euler()
    deg = tuple(math.degrees(a) for a in rot)
    bm_cyl(bms[0], r, r, length, tuple(p0 + d * (length / 2)), rot=deg, seg=6)
    bm_cyl(bms[1], r * 2.2, 0.0, 0.3, tuple(p0 + d * (length + 0.15)), rot=deg, seg=4)
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    for k in range(3):
        a = math.radians(90 + 120 * k)
        rd = up * math.sin(a) + side * math.cos(a)
        c = p0 + d * 0.2 + rd * (r * 2.0)
        bm_beam(bms[2], c - d * 0.17 + rd * 0.02, c + d * 0.17 - rd * 0.035, 0.014, 0.11, w1=0.014, h1=0.025, up=tuple(rd))


def build_props():
    col = collection("Ballista")
    root = bpy.data.objects["Ballista"]
    for o in [o for o in col.objects if o.name.startswith("Prop")]:
        bpy.data.objects.remove(o, do_unlink=True)
    back = hex_to_world(0, 2, MID)
    midc = hex_to_world(0, 1, MID)

    # ---- bolt store on the back cell: a hexagonal pavilion (six posts, team-colored pyramid roof) over spare bolts
    bm = bmesh.new()
    post_r, eave = 0.86, 1.3
    corners = [Vector((math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i)), 0)) for i in range(6)]
    for i, c in enumerate(corners):
        p = back + c * post_r
        bm_box(bm, (0.13, 0.13, eave - DECK_Z), (p.x, p.y, (DECK_Z + eave) / 2), (0, 0, 60 * i))
        q = back + corners[(i + 1) % 6] * post_r
        bm_beam(bm, (p.x, p.y, eave), (q.x, q.y, eave), 0.11, 0.12)                       # ring beam
        bm_beam(bm, p.lerp(q, 0.3) + Vector((0, 0, eave - 0.05)), p + Vector((0, 0, eave - 0.32)), 0.06, 0.06)   # braces
        bm_beam(bm, q.lerp(p, 0.3) + Vector((0, 0, eave - 0.05)), q + Vector((0, 0, eave - 0.32)), 0.06, 0.06)
    o = paint(mesh_obj("Prop_StoreFrame", bm, col, root), "wood", lo=0.25, hi=0.8)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.015; b.segments = 1; b.limit_method = "ANGLE"

    # roof: six thick triangular panels, each split into planks running down the slope
    apex = back + Vector((0, 0, 2.08))
    roof_r, roof_z, th = 1.13, eave - 0.07, 0.07
    bm = bmesh.new()
    planks = 3
    for i in range(6):
        a = back + corners[i] * roof_r + Vector((0, 0, roof_z))
        c = back + corners[(i + 1) % 6] * roof_r + Vector((0, 0, roof_z))
        for k in range(planks):
            e0, e1 = a.lerp(c, k / planks), a.lerp(c, (k + 1) / planks)
            gap = (e1 - e0) * 0.04
            e0, e1 = e0 + gap, e1 - gap
            t0, t1 = apex.lerp(e0, 0.06), apex.lerp(e1, 0.06)
            n = (e1 - e0).cross(apex - e0).normalized()
            if n.z < 0:
                n = -n
            top = [bm.verts.new(v + n * th) for v in (e0, e1, t1, t0)]
            bot = [bm.verts.new(v) for v in (e0, e1, t1, t0)]
            bm.faces.new(top)
            bm.faces.new(list(reversed(bot)))
            for j in range(4):
                jj = (j + 1) % 4
                bm.faces.new((bot[j], bot[jj], top[jj], top[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = mesh_obj("Prop_StoreRoof", bm, col, root)
    paint(o, "team", team=True, lo=0.08, hi=0.8)
    me = o.data
    uv = me.uv_layers.active.data
    for p in me.polygons:
        if (p.index // 6) % 2 == 1:            # every other plank a shade darker
            for li in p.loop_indices:
                uv[li].uv = (uv[li].uv[0], uv[li].uv[1] - 0.03)
    bm = bmesh.new()
    for i in range(6):
        a = back + corners[i] * (roof_r + 0.02) + Vector((0, 0, roof_z + th))
        bm_beam(bm, a, apex + Vector((0, 0, th)), 0.09, 0.08)                                 # hip ridges
    bm_cyl(bm, 0.09, 0.07, 0.22, tuple(apex + Vector((0, 0, 0.12))), seg=6)                    # finial
    o = paint(mesh_obj("Prop_StoreHips", bm, col, root), "wood_red", lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.06, 0.0, 0.32, tuple(apex + Vector((0, 0, 0.38))), seg=4)
    bm_cyl(bm, 0.1, 0.1, 0.05, tuple(apex + Vector((0, 0, 0.235))), seg=8)
    paint(mesh_obj("Prop_StoreSpike", bm, col, root), "iron")

    # spare bolts: stacked on bearers inside the store (along X), and on a rack on the middle cell (along Y)
    bms = (bmesh.new(), bmesh.new(), bmesh.new())
    bear = bmesh.new()
    for sy in (-0.3, 0.3):
        bm_box(bear, (1.3, 0.12, 0.1), (0, back.y + sy, DECK_Z + 0.05))
    rows = [(-0.27, 0.0, 0.17), (0.0, 0.0, 0.17), (0.27, 0.0, 0.17), (-0.135, 0.0, 0.25), (0.135, 0.0, 0.25)]
    for yy, _, zz in rows:
        _bolt(bms, (-0.72, back.y + yy, DECK_Z + zz), (1, 0, 0), 1.1, r=0.04)
    # rack on the middle cell: two trestles carrying three bolts that point forward
    rx = -0.5
    for sy in (-0.42, 0.38):
        for sx in (-1, 1):
            bm_beam(bear, (rx + sx * 0.3, midc.y + sy, DECK_Z), (rx + sx * 0.08, midc.y + sy, DECK_Z + 0.42), 0.07, 0.07,
                    up=(0, 1, 0))
        bm_box(bear, (0.62, 0.08, 0.08), (rx, midc.y + sy, DECK_Z + 0.36))
    for k, xx in enumerate((-0.2, 0.0, 0.2)):
        _bolt(bms, (rx + xx, midc.y - 0.75, DECK_Z + 0.44 + (0.04 if k == 1 else 0)), (0, 1, 0), 1.25, r=0.04)
    o = paint(mesh_obj("Prop_Bearers", bear, col, root), "wood_red", lo=0.3, hi=0.7)
    paint(mesh_obj("Prop_Bolts", bms[0], col, root), "wood", lo=0.15, hi=0.35)
    paint(mesh_obj("Prop_BoltTips", bms[1], col, root), "stone", lo=0.1, hi=0.5)
    paint(mesh_obj("Prop_BoltFletch", bms[2], col, root), "team", team=True, lo=0.15, hi=0.6)

    # ---- KayKit odds and ends on the middle cell
    kk = [
        ("hex/barrel", (0.58, midc.y + 0.42, DECK_Z), 20, 2.3),
        ("hex/barrel", (0.78, midc.y + 0.0, DECK_Z), 75, 2.1),
        ("hex/bucket_arrows", (0.45, midc.y - 0.42, DECK_Z), 10, 2.4),
        ("hex/crate_A_small", (-0.62, midc.y + 0.72, DECK_Z), 15, 2.6),
        ("hex/sack", (0.25, midc.y + 0.72, DECK_Z), 40, 2.4),
    ]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)


# ================================================================================================ animations
FPS = 30
FIRE_LEN = 15            # frames: snap, overshoot, settle
RELOAD_LEN = 45          # frames: slider forward, grab, winch back, bolt drops in
IDLE_LEN = 60            # frames: one loop of the pennant


def _arm_space_quat(pb, axis, deg):
    """A rotation of `deg` about an armature-space axis, as this bone's local pose rotation."""
    r = pb.bone.matrix_local.to_quaternion()
    return r.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ r


def _arm_space_loc(pb, delta):
    return pb.bone.matrix_local.to_3x3().inverted() @ Vector(delta)


def nock_y(phi):
    """Where the string's middle sits (head space, scaled) when the arms have swung `phi` degrees forward from drawn."""
    a = COCK - phi
    t = arm_tip(1, a)
    half = arm_tip(1, REST).x
    d = math.sqrt(max(half * half - t.x * t.x, 0.0))
    return (t.y - d) * HEAD_SCALE


def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def pose(rig, phi=0.0, slider=None, bolt=1.0, bolt_lift=0.0, pitch=0.0, kick=0.0, winch=0.0, wave=0.0, wave_amp=1.0):
    """Sets the whole rig. phi: arms swung forward (0 drawn .. COCK-REST released); slider: head-space Y of the slider
    (None: holding the nock); bolt: bolt scale (hidden near 0); pitch / kick: stock recoil (degrees nose-up, units back);
    winch: crank angle in degrees; wave: pennant phase (0..1)."""
    pb = rig.pose.bones
    for b in pb:
        b.location = (0, 0, 0)
        b.rotation_quaternion = (1, 0, 0, 0)
        b.scale = (1, 1, 1)
    pb["stock"].rotation_quaternion = _arm_space_quat(pb["stock"], (1, 0, 0), pitch)
    pb["stock"].location = _arm_space_loc(pb["stock"], (0, -kick, 0))
    pb["arm.R"].rotation_quaternion = _arm_space_quat(pb["arm.R"], (0, 0, 1), phi)
    pb["arm.L"].rotation_quaternion = _arm_space_quat(pb["arm.L"], (0, 0, 1), -phi)
    ny = nock_y(phi) - NOCK_COCKED * HEAD_SCALE
    pb["nock"].location = _arm_space_loc(pb["nock"], (0, ny, 0))
    sy = ny if slider is None else slider - NOCK_COCKED * HEAD_SCALE
    pb["slider"].location = _arm_space_loc(pb["slider"], (0, sy, 0))
    pb["bolt"].scale = (max(bolt, 0.001),) * 3
    pb["bolt"].location = _arm_space_loc(pb["bolt"], (0, 0, bolt_lift))
    pb["winch"].rotation_quaternion = _arm_space_quat(pb["winch"], (1, 0, 0), -winch)
    for k, (amp, lag) in enumerate(((7.0, 0.0), (11.0, 0.12), (15.0, 0.24)), start=1):
        pb["flag.%d" % k].rotation_quaternion = _arm_space_quat(pb["flag.%d" % k], (0, 0, 1),
                                                                amp * wave_amp * math.sin(2 * math.pi * (wave - lag)))


def _key(rig, f):
    for b in rig.pose.bones:
        b.keyframe_insert("location", frame=f)
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("scale", frame=f)


def _new_action(rig, name, length):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    act.frame_range = (0, length)
    act.use_frame_range = True
    return act


def build_anims():
    rig = bpy.data.objects["Rig"]
    released = COCK - REST
    over = COCK - SNAP
    # ---- idle: drawn and loaded, the pennant flutters
    _new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, wave=f / IDLE_LEN)
        _key(rig, f)
    # ---- fire: the trigger lets go, the arms snap forward past their stops and shiver to rest, the stock kicks
    _new_action(rig, "fire", FIRE_LEN)
    swing = {0: 0.0, 1: over * 0.6, 2: over, 3: over - 3, 4: released - 4, 5: released + 1.5, 6: released + 3,
             7: released + 1, 8: released - 1.5, 9: released - 1, 10: released + 0.8, 11: released + 0.6, 12: released - 0.3,
             13: released, 14: released, 15: released}
    for f in range(FIRE_LEN + 1):
        phi = swing[f]
        kick = (0.07 * (1 - _smooth((f - 2) / 9.0))) if f >= 2 else 0.035 * f
        pitch = (3.5 * (1 - _smooth((f - 2) / 10.0))) if f >= 2 else 1.75 * f
        slider = NOCK_COCKED * HEAD_SCALE          # the slider stays back; only the string flies forward
        pose(rig, phi=phi, slider=slider, bolt=1.0 if f == 0 else 0.0, pitch=pitch, kick=kick, wave=f / IDLE_LEN,
             wave_amp=1.0 + 0.6 * (1 - f / FIRE_LEN))
        _key(rig, f)
    # ---- reload: slider runs forward and grabs the string, the winch drags it back, a new bolt drops into the groove
    _new_action(rig, "reload", RELOAD_LEN)
    back_y = NOCK_COCKED * HEAD_SCALE
    front_y = nock_y(released)
    for f in range(RELOAD_LEN + 1):
        if f <= 9:                                   # run forward (winch pays out)
            p = _smooth(f / 9.0)
            phi, slider, winch = released, back_y + (front_y - back_y) * p, -120 * p
        elif f <= 11:                                # claw closes on the string
            phi, slider, winch = released, front_y, -120
        elif f <= 38:                                # winch it back, the arms bend
            p = _smooth((f - 11) / 27.0)
            phi, slider, winch = released * (1 - p), None, -120 + 840 * p
        else:
            phi, slider, winch = 0.0, None, 720
        if f < 28:
            bolt, lift = 0.0, 0.0
        else:
            p = _smooth((f - 28) / 12.0)
            bolt, lift = p, 0.55 * (1 - p)
        if slider is None:
            pose(rig, phi=phi, slider=None, bolt=bolt, bolt_lift=lift, winch=winch, wave=f / IDLE_LEN)
        else:
            pose(rig, phi=phi, slider=slider, bolt=bolt, bolt_lift=lift, winch=winch, wave=f / IDLE_LEN)
        _key(rig, f)
    # leave the rig on its idle, showing the rest pose
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


def build_all():
    build_base()
    build_head()
    build_props()
    build_anims()
