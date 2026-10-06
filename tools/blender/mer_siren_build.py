"""Builds the Siren Rock (footprint "pair": [0,0] front, [0,1] back), a Tide tower: her song arcs between enemies
(chain lightning) and can leave them spellbound.

    python tools/blender/build.py mer_siren --out <preview dir>

Front hex: a tide pool, and rising from it a sea-worn stack of rock, eaten in at the waist; on its flat top the siren
(the Head: she turns toward her prey): a lofted figure with pale sea skin, long locks of flame-red hair down her back,
a teal tail draped over the edge with a pale forked fin, a wrap in the team's color at her hips, a shell lyre in her
arm, at her throat a pearl that glows (the Muzzle), and three sparks of her song circling her. Back hex: what her song brought in: the bow of a ship aground on
the sand, heeled over, its broken mast still carrying a torn sail in the team's color.
Clips: idle (she sways and strums, her tail curls and swings, her hair stirs, the pearl pulses), fire (she flings her
arms and head back and sings: the pearl flares into a star, her hair and tail fly up).
The sail is still: the one rig turns with her.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

TID = "mer_siren"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
ZS = TOP + 0.085                # the sand
W = TOP + 0.04                  # the pool
SEAT = Vector((F.x, F.y, TOP + 1.02))
PEARL = "glow:0.5,0.9,1.0,0.6"
HAIR = "ember:0.05:0.85"
ROCK = "stone2:0.12:0.9"
HULL = dict(length=2.6, beam=0.5, depth=0.46)
HULL_M = tb_place((0.02, B.y - 0.12, ZS - 0.1), yaw=-72, pitch=9, roll=18, origin=(0, 2.6 * 0.74, 0))
F0 = HULL_M @ Vector((0, 2.6 * 0.63, 0.06))
MD = Vector((-0.16, 0.1, 1.0)).normalized()
MAST_LEN = 1.85
YD = Vector((1.0, 0.04, -0.1)).normalized()


def build_base():
    col = collection("Mer_siren")
    root = empty("Mer_siren", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(52)
    k = Kit()
    # ---- a sand flat over both hexes; the tide pool on the front one, a tongue of it running back toward the wreck
    flat = tb_shore(CELLS, 0.2, rnd, step=0.3, jitter=0.03, rounds=2)
    raw = tb_star_pool(CELLS, F, 0.34, 7.5)
    raw = [F + (p - F).normalized() * min((p - F).length, 1.3) for p in raw]
    pool = tb_wobble(tb_smooth(tb_resample(raw, 0.22), 2), rnd, 0.015)
    bm = bmesh.new()
    tb_plate(bm, flat, [pool], ZS, z_skirt=T - 0.02, flare=0.07, z_hole=T, hole_flare=0.06)
    tb_shore_obj("Flat_Sand", bm, col, root, top=0.3)
    inner = [F + (p - F).normalized() * min(max((p - F).length - 0.24, 0.3), 0.62) for p in pool]
    tb_water("Pool", col, root, [tb_offset(pool, 0.04), inner], W, [0.48, 0.74])
    bm = bmesh.new()
    keep = tb_offset(flat, -0.05)
    for c, a, n, ln in (((-0.42, B.y + 0.52), 14, 2, 0.5), ((0.48, B.y + 0.58), -12, 2, 0.45), ((-0.3, B.y - 0.74), 6, 2, 0.5)):
        tb_ripples(bm, c, a, n, ln, ZS - 0.006, within=keep, avoid=[tb_offset(pool, 0.06)])
    if bm.verts:
        tb_shore_obj("Flat_Ripples", bm, col, root, top=0.1, side=(0.15, 0.45))
    # ---- the stack: a wave-cut foot, a waist the sea has eaten into, a broad flat cap; a lesser stump beside it
    c = (F.x, F.y, T)
    tb_chunk(k["stone2:0.4:1.0"], rnd, c, [(-0.02, 0.56, 0.52), (0.16, 0.52, 0.48), (0.34, 0.38)], n=9)
    tb_chunk(k[ROCK], rnd, c, [(0.26, 0.4), (0.5, 0.33), (0.76, 0.38)], n=8, jit=0.08)
    tb_chunk(k[ROCK], rnd, c, [(0.7, 0.4), (0.84, 0.55), (0.97, 0.52), (1.02, 0.44)], n=9, jit=0.06)
    tb_chunk(k[ROCK], rnd, (F.x - 0.3, F.y - 0.26, T), [(0.3, 0.3), (0.52, 0.26), (0.6, 0.16)], n=7)                # a shoulder on the stack
    tb_chunk(k[ROCK], rnd, (F.x - 0.56, F.y - 0.36, T), [(-0.02, 0.26), (0.26, 0.2), (0.46, 0.13)], n=7)
    tb_chunk(k["stone2:0.3:1.0"], rnd, (F.x + 0.5, F.y + 0.42, T), [(-0.02, 0.2), (0.16, 0.16), (0.26, 0.09)], n=7)
    tb_rim(k[ROCK], rnd, pool, ZS - 0.04, r=(0.1, 0.17), gap=0.62, out=0.1, n=9)
    k.emit("Rock", col, root, vary=0.08, seed=4)
    for a in (20, 95, 160, 215, 290, 335):
        p = Vector((F.x + math.cos(math.radians(a)) * 0.5, F.y + math.sin(math.radians(a)) * 0.46, 0))
        tb_barnacle(k, (p.x, p.y, T + 0.3), 0.045, nrm=(math.cos(math.radians(a)), math.sin(math.radians(a)), 0.9))
    for a, h in ((50, 0.36), (130, 0.3), (250, 0.42), (310, 0.3)):
        tb_weed(k["teal:0.25:0.9"], rnd, (F.x + math.cos(math.radians(a)) * 0.6, F.y + math.sin(math.radians(a)) * 0.56, W - 0.02), h=h, n=3)
    tb_coral(k["salmon:0.05:0.75"], rnd, (F.x + 0.84, F.y - 0.44, ZS - 0.03), h=0.5, r=0.055, depth=2)
    tb_coral(k["orange:0.05:0.7"], rnd, (F.x - 0.82, F.y + 0.5, ZS - 0.03), h=0.42, r=0.05, depth=2)
    tb_tube_coral(k, rnd, (F.x - 0.34, F.y - 0.2, T + 0.3), n=3, h=(0.12, 0.24), r=0.045, key="salmon:0.1:0.7")
    tb_starfish(k["orange:0.15:0.7"], (F.x + 0.36, F.y - 0.2, T + 0.345), r=0.12, yaw=30, h=0.035)
    tb_scallop(k["cream:0.05:0.7"], (F.x + 0.5, F.y + 0.86, ZS + 0.01), 0.2, yaw=-30, tilt=10, ribs=5, rows=2)
    tb_whelk(k["sand:0.05:0.75"], (F.x - 0.9, F.y - 0.2, ZS), 0.2, yaw=70)
    k.emit("Rock_Life", col, root)
    # ---- the wreck: a ship's bow aground on the back hex, heeled toward us; its broken mast, yard and torn sail
    part = Kit()
    tb_hull(part, rnd, t0=0.48, t1=1.0, ribs=(0.56, 0.68, 0.8), deck=(0.82, 0.96), **HULL)
    tb_merge(k, part, HULL_M)
    tb_spar(k, rnd, F0 - MD * 0.1, F0 + MD * MAST_LEN, r0=0.09, r1=0.065)
    ym = F0 + MD * 1.42
    bm_tube(k["wood_dark:0.3:0.9"], [ym - YD * 0.62, ym, ym + YD * 0.62], [0.042, 0.052, 0.042], n=6)
    bm_tube(k["sand:0.3:0.7"], [ym - MD * 0.07, ym + MD * 0.07], 0.1, n=7)
    tb_rope(k["sand:0.3:0.7"], ym + YD * 0.58, HULL_M @ Vector((0.0, 2.6, 1.0)), sag=0.16, r=0.014)
    k.emit("Wreck", col, root, vary=0.08, seed=7)
    tb_rag(k["team!:0.1:0.75"], ym - YD * 0.58 - Vector((0, 0.06, 0.03)), ym + YD * 0.58 - Vector((0, 0.06, 0.03)), (0.72, 0.9, 0.58, 0.82, 0.62, 0.34), rows=4, billow=(0.0, -0.14, 0))
    k.emit("Wreck_Sail", col, root)
    for x, y, r in ((-0.86, B.y - 0.3, 0.2), (0.86, B.y - 0.52, 0.16), (-0.5, B.y + 0.66, 0.13), (0.6, B.y + 0.74, 0.12)):
        bm_boulder(k[ROCK], rnd, (x, y, ZS - 0.04), r, squash=(1.1, 0.95, 0.78), n=10)
    k.emit("Wreck_Rocks", col, root, vary=0.08)
    tb_keg(k, (-0.72, B.y + 0.26, ZS + 0.12), (0.5, 1, 0.1), length=0.34, r=0.13)
    for i, (x, y, a) in enumerate(((0.5, B.y + 0.5, 30), (0.72, B.y + 0.36, 70), (-0.3, B.y + 0.72, 140))):
        bm_box(k["wood:0.3:0.85"], (0.5, 0.11, 0.035), (x, y, ZS + 0.02), (4, 3, a))
    tb_weed(k["teal:0.25:0.9"], rnd, (-0.92, B.y - 0.02, ZS - 0.02), h=0.4, n=3)
    tb_coral(k["orange:0.05:0.7"], rnd, (0.9, B.y - 0.2, ZS - 0.03), h=0.4, r=0.05, depth=2)
    k.emit("Wreck_Flotsam", col, root, vary=0.06)
    empty("Head", col, root, tuple(SEAT), 0.5, "SINGLE_ARROW")
    return root


# ---- the siren, in the head's space (+Y forward, the top of the rock at z = 0)
SPEC = dict(at=(0, -0.1, 0.2), scale=1.15, tail_bones=5, tail_r=(0.165, 0.045), tail_up=(0, 0, 1),
            tail=[(0, 0, 0.0), (0, 0.16, -0.03), (0.02, 0.32, -0.06), (0.04, 0.46, -0.14), (0.05, 0.54, -0.3), (0.04, 0.55, -0.48), (0.0, 0.5, -0.62)],
            skin="tan:0.0:0.36", tail_key="teal:0.12:0.95", belly="cream", fin_key="teal:0.0:0.35", mouth=True,
            crests=((2.2, 3.8, 0.09), (4.4, 6.0, 0.08)))
TAIL_CURL = [(0, 0, 0.0), (0, 0.16, -0.03), (0.02, 0.32, -0.06), (0.04, 0.47, -0.12), (0.07, 0.6, -0.24), (0.09, 0.71, -0.39), (0.07, 0.8, -0.5)]
TAIL_LIFT = [(0, 0, 0.0), (0, 0.16, -0.02), (0.02, 0.33, -0.02), (0.03, 0.5, -0.03), (0.04, 0.66, 0.0), (0.04, 0.82, 0.08), (0.03, 0.96, 0.2)]
MER_M = tb_mer_matrix(SPEC)


def _arm(sx, wrist, hint):
    """An arm with its wrist at `wrist` (the figure's space): ((elbow, wrist) there, its shape in the head's space)."""
    sh = Vector((sx * MER_SHOULDER[0], MER_SHOULDER[1], MER_SHOULDER[2]))
    el, wr = tb_ik(sh, wrist, hint=hint)
    return (el, wr), [MER_M @ sh, MER_M @ el, MER_M @ (wr + (wr - el).normalized() * 0.09)]


ARMS = {"L": _arm(-1, (-0.27, 0.2, 0.2), (-0.6, -0.6, -0.5)), "R": _arm(1, (-0.07, 0.3, 0.26), (0.7, -0.4, -0.6))}
FLING = {"L": _arm(-1, (-0.46, -0.1, 0.6), (-0.2, -0.6, -1.0))[1], "R": _arm(1, (0.46, -0.1, 0.62), (0.2, -0.6, -1.0))[1]}
SPEC["arms"] = {s: ARMS[s][0] for s in ("L", "R")}
HAIR_PTS = [Vector((0, -0.17, 0.7)), Vector((0, -0.21, 0.42)), Vector((0, -0.25, 0.14)), Vector((0, -0.33, -0.15))]
THROAT = Vector((0, 0.105, 0.455))


def build_head():
    col = collection("Mer_siren")
    head = bpy.data.objects["Head"]
    rnd = random.Random(9)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None)}
    tb_mer_bones(bones, SPEC, parent="root")
    tb_chain(bones, "hair", [MER_M @ p for p in HAIR_PTS], parent="head")
    th = MER_M @ THROAT
    bones["pearl"] = (tuple(th), tuple(th + Vector((0, 0.1, 0))), "chest")
    bones["flare"] = (tuple(th + Vector((0, 0.03, 0))), tuple(th + Vector((0, 0.13, 0))), "chest")
    bones["wisp"] = ((0, 0, 0.3), (0, 0, 0.6), "root")
    rig = make_rig(col, head, bones)
    mer = tb_merfolk(col, rig, SPEC, name="Head_Siren")
    k, part = Kit(), Kit()
    rk = RigidKit()
    # ---- her hair: a cap over her head, two locks forward over her shoulders, four long ones down her back (on a chain)
    rk.to("head")
    rows = []
    for z, hw, hd in ((0.6, 0.165, 0.11), (0.68, 0.19, 0.15), (0.76, 0.196, 0.18), (0.82, 0.172, 0.165), (0.87, 0.1, 0.095)):
        back = max(0.0, 0.78 - z)
        rows.append(oval((0, -0.03 - back * 0.42, z), (1, 0, 0), (0, 1, 0), hw, hd, 8, power=2.3, phase=0.5))
    bm_loft(part[HAIR], rows)
    tb_starfish(part["orange:0.1:0.6"], (-0.15, 0.1, 0.83), r=0.075, yaw=10, h=0.03)
    tb_merge(rk, part, MER_M)
    rk.emit("Head_Siren_HairCap", col, rig)
    for sx in (-1, 1):
        bm_tube(part[HAIR], [(sx * 0.16, 0.0, 0.72), (sx * 0.215, 0.06, 0.52), (sx * 0.19, 0.135, 0.34), (sx * 0.14, 0.16, 0.2)], [0.05, 0.055, 0.045, 0.0], n=5, squash=1.5,
                up=(0, 1, 0))
    tb_merge(k, part, MER_M)
    k.emit("Head_Siren_Locks", col, rig=rig, bones=["head", "chest"])
    for i, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
        w = 0.02 * math.sin(i * 2.3)
        bm_tube(part[HAIR], [(x, -0.14, 0.74), (x * 1.2 + w, -0.21, 0.5), (x * 1.45 - w, -0.24, 0.25), (x * 1.7 + w, -0.28, 0.02), (x * 1.9, -0.36, -0.17 + 0.03 * (i % 2))],
                [0.06, 0.072, 0.064, 0.048, 0.0], n=5, squash=1.5, up=(0, 1, 0))
    tb_merge(k, part, MER_M)
    k.emit("Head_Siren_Hair", col, rig=rig, bones=["head", "hair.1", "hair.2", "hair.3"])
    # ---- what she wears: shells, a string of pearls, a wrap in the team's color knotted at her hip
    rk.to("chest")
    for sx in (-1, 1):
        tb_scallop(part["salmon:0.0:0.5"], (sx * 0.095, 0.125, 0.25), 0.115, yaw=180, tilt=92, ribs=4, dome=0.5, th=0.02, rows=2, spread=62)
    for i in range(9):
        a = math.radians(200 + 140 * i / 8.0)
        bm_ellipsoid(part["white:0.0:0.3"], (math.cos(a) * 0.1, 0.0 - math.sin(a) * 0.085 + 0.01, 0.462 + 0.012 * math.cos(a * 2)), (0.02, 0.02, 0.02), u=5, v=3)
    tb_merge(rk, part, MER_M)
    rk.to("hips")
    tb_mer_band(part["team!:0.1:0.6"], lambda a: -0.035 - 0.03 * math.cos(math.radians(a - 200)), 0.1, grow=0.03)
    tb_slab(part["team!:0.15:0.7"], [(-0.19, 0.04, 0.04), (-0.3, 0.1, -0.02), (-0.33, 0.07, -0.2), (-0.24, 0.05, -0.12), (-0.22, 0.02, -0.03)], Vector((0.01, 0.02, 0)))
    bm_ellipsoid(part["team!:0.1:0.5"], (-0.2, 0.05, 0.03), (0.045, 0.045, 0.04), u=5, v=3)
    tb_merge(rk, part, MER_M)
    rk.to("pearl")
    bm_ellipsoid(part[PEARL], tuple(THROAT), (0.042, 0.042, 0.042), u=8, v=5)
    tb_merge(rk, part, MER_M)
    rk.to("flare")                                 # the star the pearl flares into: drawn in at rest
    for i in range(8):
        a = 2 * math.pi * i / 8
        d = Vector((math.cos(a), 0.12, math.sin(a)))
        ln = 0.3 if i % 2 == 0 else 0.17
        bm_crystal(part[PEARL], THROAT + Vector((0, 0.03, 0)), THROAT + Vector((0, 0.03, 0)) + d * ln, 0.035, n=4, shoulder=0.2, foot=0.6)
    tb_merge(rk, part, MER_M)
    # ---- her lyre: a shell for a sound box, two horns of gold, a bar of bone, strings; it rides on her left hand
    rk.to("arm.L.2")
    LM = Matrix.Translation(Vector((-0.2, 0.275, 0.25))) @ Matrix.Rotation(math.radians(24), 4, "Z")
    lyre = Kit()
    tb_scallop(lyre["cream:0.05:0.7"], (0, 0.02, -0.03), 0.13, yaw=180, tilt=90, ribs=5, dome=0.5, th=0.025, rows=2, spread=70)
    for sx in (-1, 1):
        pts = tb_bezier((sx * 0.06, 0, 0.03), (sx * 0.22, 0, 0.1), (sx * 0.2, 0, 0.3), (sx * 0.1, 0, 0.4), 6)
        bm_tube(lyre["gold:0.1:0.7"], pts, [0.026, 0.024, 0.022, 0.02, 0.018, 0.016], n=5)
        bm_ellipsoid(lyre["white:0.0:0.3"], tuple(pts[-1] + Vector((0, 0, 0.02))), (0.028, 0.028, 0.028), u=5, v=3)
    bm_tube(lyre["cream:0.2:0.8"], [(-0.14, 0, 0.345), (0.14, 0, 0.345)], 0.016, n=5)
    for x in (-0.06, -0.02, 0.02, 0.06):
        bm_beam(lyre["white:0.0:0.4"], (x, 0.0, 0.05), (x * 1.25, 0.0, 0.345), 0.009, 0.009)
    tb_merge(part, lyre, LM)
    tb_merge(rk, part, MER_M)
    rk.to("wisp")                                  # her song made visible: three sparks circling her
    for i in range(3):
        a = math.radians(120 * i + 40)
        p = Vector((math.cos(a) * 0.64, math.sin(a) * 0.64, 0.5 + 0.42 * i))
        bm_crystal(rk[PEARL], p, p + Vector((0, 0, 0.13)), 0.045, n=4, shoulder=0.4, foot=0.1)
        bm_crystal(rk[PEARL], p, p - Vector((0, 0, 0.09)), 0.045, n=4, shoulder=0.0, foot=1.0)
    rk.emit("Head_Siren_Gear", col, rig)
    empty("Muzzle", col, head, tuple(th + Vector((0, 0.06, 0))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 20
_T = {}


def pose(rig, ph=0.0, back=0.0, flare=0.0, tuck=0.0):
    """back: her arms and head flung back (the song); flare: the pearl's star; tuck: the breath before it."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    nt = SPEC["tail_bones"]
    if not _T:
        shape = lambda pts: [MER_M @ p for p in tb_even(tb_curve(pts, 40), nt + 1)]
        rest = shape(SPEC["tail"])
        _T["curl"], _T["lift"] = tb_turns(rest, shape(TAIL_CURL)), tb_turns(rest, shape(TAIL_LIFT))
        for s in ("L", "R"):
            _T["fling." + s] = tb_turns(ARMS[s][1], FLING[s])
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    still = 1.0 - back
    sway = math.sin(ph)
    # her body: a slow sway at the hips, breath in her chest, her head tilting as she hums; flung back when she sings out
    qh = Quaternion(Y, math.radians(3.0 * sway * still)) @ Quaternion(X, math.radians(-2.0 * tuck + 5.0 * back))
    qc = Quaternion(Z, math.radians(4.0 * math.sin(ph + 0.6) * still)) @ Quaternion(X, math.radians(-5.0 * tuck + 13.0 * back))
    qn = (Quaternion(Y, math.radians(-7.0 * sway * still)) @ Quaternion(Z, math.radians(9.0 * math.sin(ph + 1.2) * still))
          @ Quaternion(X, math.radians(3.0 * math.sin(ph * 2) * still - 8.0 * tuck + 30.0 * back)))
    for name, quat in (("hips", qh), ("chest", qc), ("head", qn)):
        r = pb[name].bone.matrix_local.to_quaternion()
        pb[name].rotation_quaternion = r.inverted() @ quat @ r
    pb["chest"].scale = (1 + 0.02 * math.sin(ph * 2) + 0.04 * back,) * 3
    head_turn = qh @ qc @ qn
    # her hair hangs by its own weight whatever her head does, stirring; it flies up behind her when she sings out
    lift = [Quaternion(X, math.radians(-(18 + 14 * i) * back)) for i in range(3)]
    stir = tb_wave(3, (0, 1, 0), 3.5, ph * 2, step=0.8, grow=2.4)
    tb_pose_chain(rig, "hair", lift, extra=stir, base=head_turn)
    # her arms: the left holds the lyre, the right strums it; both flung wide and back
    for s in ("L", "R"):
        turns = tb_mix(None, _T["fling." + s], back)
        strum = [Quaternion(), Quaternion(Z, math.radians(7.0 * math.sin(ph * 6) * still * (1.0 if s == "R" else 0.0)))]
        tb_pose_chain(rig, "arm." + s, turns, extra=strum)
    # her tail: the hanging end curls out from the rock and back, swinging; it kicks up when she sings out
    w_curl = (0.5 - 0.5 * math.cos(ph)) * still
    turns = tb_mix(None, _T["curl"], w_curl)
    turns = tb_mix(turns, _T["lift"], back)
    tb_pose_chain(rig, "tail", turns, extra=tb_wave(nt, (0, 1, 0), 2.2 * still, ph * 2 + 0.5, step=0.7, grow=3.0))
    pb["fin"].rotation_quaternion = q(pb["fin"], (1, 0, 0), 14.0 * math.sin(ph * 2 + 1.0) * still + 20.0 * back)
    s = 1.0 + 0.12 * math.sin(ph * 2) + 0.9 * flare
    pb["pearl"].scale = (s, s, s)
    g = max(0.001, flare * (1.0 + 0.15 * math.sin(flare * 9.0)))
    pb["flare"].scale = (g, g, g)
    pb["flare"].rotation_quaternion = q(pb["flare"], (0, 1, 0), 40.0 * flare)
    pb["wisp"].rotation_quaternion = q(pb["wisp"], (0, 0, 1), math.degrees(ph) + 100.0 * back)
    pb["wisp"].location = arm_space_loc(pb["wisp"], (0, 0, 0.05 * math.sin(ph * 2) + 0.12 * back))
    pb["wisp"].scale = (1.0 + 0.35 * flare, 1.0 + 0.35 * flare, 1.0 + 0.15 * math.sin(ph * 3) + 0.5 * flare)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, ph=2 * math.pi * f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # a breath in (0-2), then arms and head flung back by frame 5, the pearl flaring; held, and eased back
        tuck = smooth(f / 2.0) * (1 - smooth((f - 2) / 2.0))
        back = smooth((f - 2) / 3.0) * (1 - smooth((f - 10) / 9.0))
        flare = smooth((f - 2.5) / 2.5) * (1 - smooth((f - 8) / 7.0))
        pose(rig, back=back, flare=flare, tuck=tuck)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.0, 1.0), "dist": 8.0, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y, 1.75), "anim_dist": 4.2,
           "frames": [("idle", 0), ("idle", 24), ("idle", 48), ("fire", 2), ("fire", 6), ("fire", 12)],
           "extra": [{"yaw": 160, "pitch": 6, "dist": 2.6, "target": (F.x, F.y, 1.95)},
                     {"yaw": 20, "pitch": 24, "dist": 3.4, "target": (F.x, F.y, 1.7)},
                     {"yaw": 330, "pitch": 24, "dist": 5.0, "target": (0, B.y, 1.0)},
                     {"yaw": 90, "pitch": 14, "dist": 5.5, "target": (0, 0.3, 1.1)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
