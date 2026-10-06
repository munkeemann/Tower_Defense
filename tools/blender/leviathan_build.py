"""Builds the Leviathan (footprint "line4": [0,0] front, then [0,1], [0,2], [0,3] going back), the Tide's Tier IV
creature: a sea serpent whose water jet pierces a whole line (a 90 degree arc).

    python tools/blender/build.py leviathan --out <preview dir>

One stone-kerbed canal runs the whole footprint, a basin in each hex joined by narrows, fed by a shell-crowned spout at
the back. The serpent lies along it: its body arches out of one basin, over the narrows and down into the next, three
times (banded teal over a pale plated belly, a row of webbed fins in the team's color down its spine), its finned tail
curls up beside the spout, and from the front basin its neck rears to a horned dragon's head with frills in the team's
color, glowing eyes and a fanged jaw (the Head: the neck base turns to aim; the jet leaves its mouth).
Clips: idle (the neck sways, the head looks about, the jaw works, the frills flutter), fire (it rears back, lunges with
its jaw wide and its frills flared, and a gush of water bursts from its mouth).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

TID = "leviathan"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
C = [hex_to_world(0, s, MID) for s in range(4)]
STEP = C[0].y - C[1].y
TOP = 0.34
W = TOP + 0.11                  # the canal's surface
KERB = TOP + 0.21               # the top of its kerb
BODY = "teal:0.1:0.9"
DARK = "teal"
BELLY = "cream"
FIN = "team!:0.1:0.7"
EYE = "glow:0.5,1.0,0.9,1.0"
JET = "glow:0.42,0.78,1.0,0.7"
PEARL = "glow:0.7,0.95,1.0,0.7"
NECK0 = Vector((0.0, C[0].y + 0.14, W))


def body_pt(y):
    """The middle line of the serpent's body where the canal is at y: over the narrows between two basins, under the
    water in the basins."""
    ph = 2 * math.pi * y / STEP
    amp = 0.75 + 0.07 * y
    return Vector((0.1 * math.sin(ph * 0.5 + 0.6), y, W - 0.12 + amp * (math.cos(ph) + 0.25) / 1.25))


def body_r(y):
    return 0.3 + 0.012 * y


def _skin(obj, frames, m):
    """A serpent's colors on a tube: a pale belly in plates, saddles in the team's color over its back."""
    tb_paint_side(obj, frames, BELLY, side=-1.0, cos_min=0.5, lo=0.15, hi=0.65)
    for i in range(1, m, 2):
        tb_paint_span(obj, frames, BELLY, (i, i), side=-1.0, cos_min=0.5, lo=0.45, hi=0.9)
    for i in range(1, m, 3):
        tb_paint_span(obj, frames, "team", (i, i), team=True, side=1.0, cos_min=0.5, lo=0.1, hi=0.6)


def build_base():
    col = collection("Leviathan")
    root = empty("Leviathan", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(21)
    k = Kit()
    # ---- the canal: a kerb of dressed stone following the footprint, water inside it, darker in the basins
    edge = tb_shore(CELLS, 0.2, None, step=0.3, rounds=2)
    tb_kerb(k["stone:0.05:0.85"], rnd, edge, T - 0.01, KERB, th=0.2)
    k.emit("Kerb", col, root, vary=0.09, seed=2, bevel=0.012)
    deep = [tb_blob((c.x, c.y), 0.5, 0.6, n=12, rnd=rnd, jitter=0.06) for c in C]
    bm = bmesh.new()
    tb_plate(bm, tb_offset(edge, -0.1), deep, W)
    tb_sea_obj("Canal_0", bm, col, root, top=0.5)
    bm = bmesh.new()
    for loop in deep:
        tb_plate(bm, loop, [], W)
    tb_sea_obj("Canal_1", bm, col, root, top=0.8)
    # ---- the spout that feeds it: a pier of coursed stone on the back kerb, a great shell on top, water falling from its pipe
    yb = C[3].y - 0.74
    xs = -0.26
    bm_block_wall(k["stone:0.05:0.85"], rnd, (xs - 0.36, yb), (xs + 0.36, yb), T, T + 0.9, th=0.3, course=0.225, block=0.36)
    bm_box(k["stone:0.0:0.55"], (0.84, 0.4, 0.07), (xs, yb, T + 0.935))
    k.emit("Spout", col, root, vary=0.09, seed=5, bevel=0.012)
    tb_scallop(k["cream:0.02:0.65"], (xs, yb - 0.02, T + 0.96), 0.5, yaw=0, tilt=80, ribs=8)
    tb_scallop(k["salmon:0.0:0.5"], (xs, yb - 0.02, T + 0.96), 0.5, yaw=0, tilt=80, ribs=8, t0=0.82, t1=1.02, rows=1, lift=0.014)
    bm_tube(k["stone_dark:0.2:0.85"], [(xs, yb + 0.1, T + 0.66), (xs, yb + 0.4, T + 0.64)], [0.12, 0.1], n=6)
    bm_cyl(k["black:0.3:0.7"], 0.07, 0.07, 0.012, (xs, yb + 0.402, T + 0.64), rot=(90, 0, 0), seg=6)
    bm_tube(k["sky:0.0:0.5"], [(xs, yb + 0.38, T + 0.63), (xs, yb + 0.56, T + 0.57), (xs, yb + 0.68, T + 0.4), (xs, yb + 0.73, W - 0.03)], 0.04,
            n=6, squash=2.2, up=(0, 1, 0))
    for a0 in (20, 140, 260):
        tb_foam(k["white:0.0:0.25"], (xs, yb + 0.74, 0), 0.17, a0, a0 + 90, w=0.06, z=W + 0.012)
    k.emit("Spout_Top", col, root)
    # ---- what grows on the kerb: corals, weed trailing in the water, shells; two pearls glowing in open shells
    for x, y, key, h in ((-0.86, C[1].y + 0.12, "salmon:0.05:0.75", 0.62), (0.87, C[2].y - 0.1, "orange:0.05:0.7", 0.56), (0.84, C[0].y - 0.32, "salmon:0.05:0.75", 0.42)):
        tb_coral(k[key], rnd, (x, y, KERB - 0.04), h=h, r=0.06, depth=2)
    tb_tube_coral(k, rnd, (-0.84, C[3].y + 0.2, KERB - 0.02), n=4, key="orange:0.1:0.7")
    tb_tube_coral(k, rnd, (0.85, C[1].y + 0.3, KERB - 0.02), n=3, key="salmon:0.1:0.7")
    for x, y in ((0.6, C[1].y - 0.4), (-0.62, C[2].y - 0.3), (0.52, C[3].y + 0.55), (-0.58, C[0].y - 0.5), (-0.6, C[1].y - 0.5)):
        tb_weed(k["teal:0.3:0.95"], rnd, (x, y, W - 0.02), h=0.5, n=3)
    tb_starfish(k["orange:0.15:0.7"], (0.8, C[2].y + 0.48, KERB + 0.005), r=0.14, yaw=20, h=0.04)
    tb_whelk(k["sand:0.05:0.75"], (-0.84, C[2].y + 0.2, KERB), 0.26, yaw=100)
    for x, y, yaw in ((-0.86, C[0].y + 0.02, -70), (0.86, C[3].y + 0.05, 110)):
        tb_scallop(k["cream:0.05:0.7"], (x, y, KERB + 0.01), 0.26, yaw=yaw, tilt=8, ribs=6, rows=3)
        tb_scallop(k["salmon:0.0:0.5"], (x, y, KERB + 0.02), 0.25, yaw=yaw, tilt=62, ribs=6, rows=3)
        d = Vector((math.sin(math.radians(-yaw)), math.cos(math.radians(yaw)), 0))
        bm_ellipsoid(k[PEARL], (x + d.x * 0.13, y + d.y * 0.13, KERB + 0.12), (0.09, 0.09, 0.09), u=8, v=5)
    for x, y in ((0.97, C[1].y - 0.2), (-0.96, C[3].y - 0.3), (0.45, C[0].y - 1.0), (-0.95, C[2].y + 0.4)):
        tb_barnacle(k, (x, y, KERB - 0.01), 0.045)
    k.emit("Kerb_Life", col, root)
    # ---- the serpent's body: three arches over the narrows, each from basin to basin, and its tail in the back basin
    for j, yj in enumerate((C[0].y - STEP * 0.5, C[1].y - STEP * 0.5, C[2].y - STEP * 0.5)):
        m = 16
        ys = [yj - 0.98 + 1.96 * i / m for i in range(m + 1)]
        pts = [body_pt(y) for y in ys]
        rad = [body_r(y) for y in ys]
        bm_tube(k[BODY], pts, rad, n=10, phase=0.5)
        frames = tb_frames(pts)
        for i0, i1, h in ((3.4, 5.6, 0.34), (5.9, 8.1, 0.42), (8.4, 10.6, 0.4), (10.9, 12.8, 0.3)):
            tb_crest(k[FIN], frames, rad, i0, i1, h, rays=3, lean=0.45)
        for sgn in (-90, 90):                                                          # a pair of side fins at the top of the arch
            tb_crest(k[FIN], frames, rad, 6.8, 9.2, 0.46 - 0.04 * j, rays=4, lean=0.55, side=sgn, th=0.035)
        body = k.emit("Coil%d" % (j + 1), col, root)[0]
        _skin(body, frames, m)
        for i, sgn in ((4.5, 1), (11.5, -1)):                                          # foam where it breaks the water
            p = body_pt(yj - 0.98 + 1.96 * i / m - sgn * 0.26)
            for a0 in (30, 150, 270):
                tb_foam(k["white:0.0:0.25"], (p.x, p.y, 0), body_r(p.y) + 0.1, a0, a0 + 85, w=0.06, z=W + 0.012)
    k.emit("Coil_Foam", col, root)
    tp = tb_curve([(0.14, C[3].y + 0.5, W - 0.5), (0.3, C[3].y + 0.26, W - 0.08), (0.45, C[3].y + 0.02, W + 0.3), (0.5, C[3].y - 0.2, W + 0.68),
                   (0.44, C[3].y - 0.32, W + 0.98), (0.3, C[3].y - 0.26, W + 1.13)], 11)
    rad = [0.2 - 0.13 * i / 10.0 for i in range(11)]
    bm_tube(k[BODY], tp, rad, n=8, phase=0.5, up=(0, -1, 0))
    frames = tb_frames(tp, (0, -1, 0))
    c, x, t = frames[-1]
    tb_fin(k[FIN], c - x * 0.07 - t * 0.04, c + x * 0.07 - t * 0.04, [c + (t * math.cos(math.radians(a)) + x * math.sin(math.radians(a))) * ln
                                                                      for a, ln in ((-72, 0.42), (-36, 0.52), (0, 0.36), (36, 0.52), (72, 0.42))], th=0.03, notch=0.5)
    tb_crest(k[FIN], frames, rad, 4.0, 7.0, 0.22, rays=3, lean=0.4)
    tail = k.emit("Tail", col, root)[0]
    _skin(tail, frames, 10)
    for a0 in (30, 150, 270):
        tb_foam(k["white:0.0:0.25"], (0.33, C[3].y + 0.2, 0), 0.3, a0, a0 + 85, w=0.06, z=W + 0.012)
    for a0 in (10, 130, 250):
        tb_foam(k["white:0.0:0.25"], (NECK0.x, NECK0.y, 0), 0.44, a0, a0 + 80, w=0.07, z=W + 0.012)
    k.emit("Tail_Foam", col, root)
    empty("Head", col, root, tuple(NECK0), 0.5, "SINGLE_ARROW")
    return root


# ---- the neck and head, in the head's space (+Y forward; the neck's foot at the water's surface, at the origin)
NKC = [(0, 0.0, -0.45), (0, -0.02, 0.0), (0, -0.1, 0.5), (0, -0.28, 1.0), (0, -0.36, 1.5), (0, -0.25, 2.0), (0, -0.02, 2.36), (0, 0.22, 2.52)]
REAR = [(0, 0.0, -0.45), (0, -0.04, 0.0), (0, -0.2, 0.5), (0, -0.5, 0.98), (0, -0.74, 1.5), (0, -0.76, 2.05), (0, -0.56, 2.52), (0, -0.3, 2.78)]
LUNGE = [(0, 0.0, -0.45), (0, 0.0, 0.0), (0, 0.04, 0.5), (0, 0.1, 1.02), (0, 0.26, 1.52), (0, 0.56, 1.92), (0, 0.9, 2.14), (0, 1.18, 2.2)]
NB = 6
SK = [(0.12, 2.5, 0.19, 0.19), (0.3, 2.56, 0.27, 0.24), (0.5, 2.56, 0.28, 0.21), (0.68, 2.5, 0.22, 0.15), (0.9, 2.46, 0.17, 0.115),
      (1.08, 2.44, 0.14, 0.09), (1.17, 2.43, 0.1, 0.06)]
JW = [(0.3, 2.3, 0.19, 0.06), (0.55, 2.28, 0.2, 0.065), (0.8, 2.28, 0.16, 0.06), (1.0, 2.29, 0.12, 0.05), (1.11, 2.3, 0.085, 0.035)]


def _neck_pts(ctrl, n):
    return tb_even(tb_curve(ctrl, 60), n)


def build_head():
    col = collection("Leviathan")
    head = bpy.data.objects["Head"]
    bpts = _neck_pts(NKC, NB + 1)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None)}
    names = tb_chain(bones, "neck", bpts)
    bones["skull"] = ((0, 0.22, 2.52), (0, 0.95, 2.45), names[-1])
    bones["jaw"] = ((0, 0.34, 2.34), (0, 1.05, 2.26), "skull")
    for sx, s in ((-1, "L"), (1, "R")):
        bones["frill." + s] = ((sx * 0.24, 0.3, 2.5), (sx * 0.62, 0.02, 2.56), "skull")
    bones["gush"] = ((0, 1.0, 2.34), (0, 1.3, 2.34), "skull")
    rig = make_rig(col, head, bones)
    k = Kit()
    # ---- the neck: one tube soft-skinned along its chain; fins down its back, a pair of side fins near the water
    m = NB * 2
    rp = _neck_pts(NKC, m + 1)
    rad = [0.32 - 0.12 * i / float(m) for i in range(m + 1)]
    bm_tube(k[BODY], rp, rad, n=10, up=(0, -1, 0), phase=0.5)
    frames = tb_frames(rp, (0, -1, 0))
    neck = k.emit("Head_Neck", col, rig=rig, bones=names + ["skull"])[0]
    _skin(neck, frames, m)
    rk = RigidKit()
    for j in range(1, NB):
        rk.to(names[j])
        tb_crest(rk[FIN], frames, rad, 2 * j + 0.15, 2 * j + 1.85, 0.36 - 0.02 * j, rays=3, lean=0.4)
    rk.to(names[1])
    for sgn in (-90, 90):
        tb_crest(rk[FIN], frames, rad, 2.3, 4.2, 0.5, rays=4, lean=0.5, side=sgn, th=0.035)
    # ---- the head: skull and snout in one loft, the roof of its mouth red; brows running back into horns, eyes, fangs, a crest
    bm_loft(k[BODY], tb_sections(SK, n=8))
    skull = k.emit("Head_Skull", col, rig=rig, bone="skull")[0]
    paint_faces(skull, "salmon", lambda c, n: n.z < -0.6 and c.y > 0.42, lo=0.3, hi=0.85)
    paint_faces(skull, DARK, lambda c, n: n.z > 0.5 and c.y < 0.62, lo=0.75, hi=1.0)
    bm_loft(k["cream:0.15:0.85"], tb_sections(JW, n=8))
    jaw = k.emit("Head_Jaw", col, rig=rig, bone="jaw")[0]
    paint_faces(jaw, "salmon", lambda c, n: n.z > 0.6, lo=0.3, hi=0.8)
    rk.to("skull")
    for sx in (-1, 1):
        bm_tube(rk["teal:0.7:1.0"], [(sx * 0.15, 0.7, 2.64), (sx * 0.27, 0.54, 2.72), (sx * 0.3, 0.32, 2.75), (sx * 0.26, 0.16, 2.72)], [0.045, 0.07, 0.075, 0.06], n=5)
        bm_tube(rk["cream:0.1:0.8"], [(sx * 0.22, 0.24, 2.72), (sx * 0.3, 0.02, 2.9), (sx * 0.35, -0.24, 3.04), (sx * 0.32, -0.46, 3.08)], [0.085, 0.07, 0.045, 0.0], n=5)
        bm_crystal(rk["cream:0.1:0.8"], (sx * 0.25, 0.36, 2.44), (sx * 0.46, 0.14, 2.42), 0.055, n=4, shoulder=0.25)
        bm_ellipsoid(rk["black:0.3:0.7"], (sx * 0.262, 0.53, 2.62), (0.03, 0.105, 0.075), u=6, v=4)
        bm_ellipsoid(rk[EYE], (sx * 0.275, 0.54, 2.62), (0.03, 0.08, 0.055), u=6, v=4)
        bm_box(rk["black:0.2:0.5"], (0.02, 0.024, 0.085), (sx * 0.303, 0.55, 2.62))
        bm_ellipsoid(rk["black:0.3:0.7"], (sx * 0.075, 1.12, 2.475), (0.024, 0.035, 0.018), u=5, v=3)
        for y, ln in ((0.62, 0.08), (0.74, 0.09), (0.86, 0.1), (0.98, 0.17), (1.09, 0.1)):
            w = 0.22 - 0.24 * (y - 0.68) if y > 0.68 else 0.22
            bm_crystal(rk["cream:0.0:0.6"], (sx * w * 0.86, y, 2.375), (sx * w * 0.86, y + 0.01, 2.375 - ln), 0.034, n=4, shoulder=0.2)
    bm_crystal(rk["cream:0.1:0.8"], (0, 1.02, 2.5), (0, 0.98, 2.68), 0.05, n=4, shoulder=0.25)
    tb_fin(rk[FIN], (0, 0.56, 2.74), (0, 0.16, 2.68), [(0, 0.5, 3.0), (0, 0.28, 3.1), (0, 0.04, 3.02)], th=0.03, notch=0.55)
    rk.to("jaw")
    for sx in (-1, 1):
        for y, ln in ((0.68, 0.07), (0.8, 0.075), (0.92, 0.08), (1.04, 0.12)):
            w = 0.2 - 0.25 * (y - 0.6)
            bm_crystal(rk["cream:0.0:0.6"], (sx * w * 0.8, y, 2.33), (sx * w * 0.8, y + 0.01, 2.33 + ln), 0.03, n=4, shoulder=0.2)
        bm_crystal(rk["cream:0.1:0.8"], (sx * 0.1, 0.9, 2.25), (sx * 0.14, 0.78, 2.1), 0.035, n=4, shoulder=0.25)
    bm_tube(rk["red:0.3:0.8"], [(0, 0.42, 2.335), (0, 0.7, 2.35), (0, 0.94, 2.34)], [0.09, 0.075, 0.03], n=6, squash=2.0)
    # the frills: webbed fans behind the jaw on either side, each on a bone of its own
    for sx, s in ((-1, "L"), (1, "R")):
        rk.to("frill." + s)
        tb_fin(rk[FIN], (sx * 0.25, 0.36, 2.68), (sx * 0.23, 0.3, 2.36), [(sx * 0.58, 0.14, 2.96), (sx * 0.8, 0.02, 2.74), (sx * 0.8, -0.03, 2.46), (sx * 0.6, 0.05, 2.2)],
               th=0.03, notch=0.6)
        for tip in ((sx * 0.58, 0.14, 2.96), (sx * 0.8, 0.02, 2.74), (sx * 0.8, -0.03, 2.46), (sx * 0.6, 0.05, 2.2)):
            bm_tube(rk["teal:0.6:1.0"], [(sx * 0.24, 0.33, 2.52), tip], [0.03, 0.012], n=4)
    # the gush: a burst of water out of its mouth, drawn in at rest
    rk.to("gush")
    bm_tube(rk[JET], [(0, 1.0, 2.34), (0, 1.3, 2.34), (0, 1.75, 2.33), (0, 2.2, 2.32)], [0.07, 0.16, 0.14, 0.0], n=7)
    for i in range(6):
        a = 2 * math.pi * i / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        bm_crystal(rk[JET], Vector((0, 1.12, 2.34)) + d * 0.08, Vector((0, 1.5, 2.34)) + d * 0.34, 0.06, n=4, shoulder=0.4)
    rk.emit("Head_Parts", col, rig)
    empty("Muzzle", col, head, (0, 1.12, 2.34), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 24
_T = {}


def pose(rig, ph=0.0, rear=0.0, lunge=0.0, jaw=0.0, flare=0.0, gush=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    if not _T:
        rest = _neck_pts(NKC, NB + 1)
        _T["rear"] = tb_turns(rest, _neck_pts(REAR, NB + 1))
        _T["lunge"] = tb_turns(rest, _neck_pts(LUNGE, NB + 1))
    still = 1.0 - max(rear, lunge)
    sway = tb_wave(NB, (0, 1, 0), 2.4 * still, ph, step=0.55, grow=1.6)
    nod = tb_wave(NB, (1, 0, 0), 1.3 * still, ph * 2 + 1.0, step=0.4, grow=1.5)
    extra = [a @ b for a, b in zip(sway, nod)]
    turns = tb_mix(None, _T["rear"], rear)
    turns = tb_mix(turns, _T["lunge"], lunge)
    tb_pose_chain(rig, "neck", turns, extra=extra)
    last = extra[-1] @ turns[-1]
    # the skull keeps its own level: it looks about, lifts as the neck rears, drops as it lunges
    look = (Quaternion((0, 0, 1), math.radians(8 * math.sin(ph + 0.8) * still)) @ Quaternion((0, 1, 0), math.radians(3 * math.sin(ph) * still))
            @ Quaternion((1, 0, 0), math.radians(3 * math.sin(ph * 2) * still + 16 * rear - 9 * lunge)))
    tb_set_turn(pb["skull"], last, look)
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -(5 + 5 * max(0.0, math.sin(ph * 2 + 2.0)) ** 2 * still + 40 * jaw))
    for sx, s in ((-1, "L"), (1, "R")):
        pb["frill." + s].rotation_quaternion = q(pb["frill." + s], (0, 0, 1), sx * (7 * math.sin(ph * 3 + (0.0 if sx < 0 else 0.8)) * still + 3 * math.sin(ph) + 30 * flare))
    g = max(0.001, gush)
    pb["gush"].scale = (g, g, g)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, ph=2 * math.pi * f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        rear = smooth(f / 5.0) * (1 - smooth((f - 5) / 3.0))
        lunge = smooth((f - 5) / 3.0) * (1 - smooth((f - 13) / 10.0))
        jaw = smooth((f - 2) / 4.0) * (1 - smooth((f - 14) / 9.0))
        flare = smooth(f / 4.0) * (1 - smooth((f - 15) / 9.0))
        gush = 0.0 if f < 7 else 1.25 * smooth((f - 7) / 2.0) * (1 - smooth((f - 12) / 6.0))
        pose(rig, rear=rear, lunge=lunge, jaw=jaw, flare=flare, gush=gush)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.3, 1.1), "dist": 14.0, "yaw": 150, "pitch": 20, "anim_target": (0, C[0].y + 0.3, 2.0), "anim_dist": 6.5,
           "frames": [("idle", 0), ("idle", 24), ("fire", 4), ("fire", 8), ("fire", 12)],
           "extra": [{"yaw": 148, "pitch": 4, "dist": 3.4, "target": (0, C[0].y + 0.7, 2.95)},
                     {"yaw": 0, "pitch": 50, "dist": 7.5, "target": (0, -1.6, 0.7)},
                     {"yaw": 90, "pitch": 14, "dist": 9.5, "target": (0, 0.2, 1.0)},
                     {"yaw": 35, "pitch": 24, "dist": 5.0, "target": (0, C[3].y + 0.3, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
