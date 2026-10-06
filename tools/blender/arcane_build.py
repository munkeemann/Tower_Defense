"""Builds the Arcane Spire (footprint "pair": cells [0,0] front, [0,1] back).

    python tools/blender/build.py arcane --out <preview dir>

One wizard's tower in three interlocking rounds. Front cell: the spire, a slender coursed-stone shaft carrying a jettied,
timber-framed study with a ring of violet windows under a tiled cone roof that is cut open at the top: over its brass
rim a big crystal floats inside three turning orrery rings (the Head: it turns toward targets, orbs leave the crystal).
Back cell: the library, a low round annex under its own tiled cone, its door (toward the camera) on a rune circle set
in the paving. Between them, at the footprint's waist, the stair turret that joins the two: its battlemented top is the
study's landing, where the game stands the mage (Crew).
Clips: idle (the crystal bobs and turns, the rings tumble against each other, shards circle the roof), fire (the
crystal dips, flares and kicks; the rings snap level and whip round; a ring of light bursts out).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())

TID = "arcane"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
S = Vector((0.0, FRONT.y - 0.06, 0.0))      # the spire's axis
A = Vector((0.0, BACK.y + 0.22, 0.0))       # the library's axis
TR = Vector((0.0, -0.2, 0.0))               # the stair turret's axis (the footprint's waist)
R_FOOT = 0.74                               # the spire: its footing, the shaft's foot and top, the study, the eave
R0, R1 = 0.58, 0.44
R_ST = 0.64
R_EAVE = 0.84
R_TOP = 0.4                                 # the roof's open top
SHAFT_TOP = 1.8
FLOOR = 1.93                                # the study's floor and the turret's top (the mage's landing)
EAVE = 2.56
RIM = 3.2                                   # the roof's open rim: the Head sits here
CZ = 0.48                                   # the crystal's middle above the rim
VIOLET = "glow:0.5,0.2,1.0,0.95"
WINDOW = "glow:0.56,0.3,1.0,0.75"
RUNE = "glow:0.66,0.4,1.0,0.85"
WELL = "glow:0.42,0.16,0.9,0.7"


def tangent(deg):
    """Along a round wall at `deg`, so that the wall faces outward (see wall_out)."""
    a = math.radians(deg)
    return Vector((-math.sin(a), math.cos(a), 0))


def build_base():
    col = collection("Arcane")
    root = empty("Arcane", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(7)
    k = Kit()
    door = Vector((A.x, A.y - 0.72, 0))
    # ---- paving over both cells, running under the three rounds; the rune circle's step is laid into it
    pave(k, rnd, CELLS, T, keep_out=[(S.x, S.y, R_FOOT - 0.03), (A.x, A.y, 0.72), (TR.x, TR.y, 0.38), (door.x, door.y, 0.4)], inset=0.27, size=0.25)
    k.emit("Paving", col, root, vary=0.09)

    # ---- the spire: a flared footing, the tapering shaft, a corbel course under the jetty
    z0 = T + 0.28
    bm_block_course(k[STONE_FOOT], rnd, S, R_FOOT, T, 0.15, 12, depth=0.3)
    bm_block_course(k[STONE_FOOT], rnd, S, R_FOOT - 0.07, T + 0.15, 0.13, 11, depth=0.3, phase=0.5)
    course_tower(k, rnd, S, R0, R1, z0, SHAFT_TOP, courses=7, n=9)
    bm_block_course(k[STONE_LIGHT], rnd, S, R1 + 0.06, SHAFT_TOP, 0.07, 11, depth=0.2)
    bm_block_course(k[STONE_LIGHT], rnd, S, R1 + 0.13, SHAFT_TOP + 0.07, 0.06, 11, depth=0.24, phase=0.5)
    arch_door(k, polar(S, R0 + 0.005, 90, z0), tangent(90), 0.3, 0.5, th=0.08)
    bm_box(k[STONE_FOOT], (0.6, 0.26, 0.14), (S.x, S.y + R_FOOT + 0.05, T + 0.07))        # a step down to the paving
    for a, z in ((25, 1.15), (155, 1.4), (215, 1.0), (325, 1.45)):           # slit windows up the shaft
        r = R0 - (R0 - R1) * (z - z0) / (SHAFT_TOP - z0)
        arch_window(k, polar(S, r + 0.005, a, z), tangent(a), 0.09, 0.26, glow=WINDOW, th=0.04, proud=0.035, n=3, sill=False)
    k.emit("Spire", col, root, vary=0.07)

    # ---- the jetty: timber brackets off the shaft, a ring beam, and the study: a twelve-sided timber frame
    for i in range(12):
        a = 15 + 30 * i
        bm_beam(k[TIMBER], polar(S, R1, a, SHAFT_TOP - 0.36), polar(S, R_ST + 0.04, a, FLOOR - 0.06), 0.06, 0.075)
        bm_beam(k[TIMBER], polar(S, R_ST + 0.07, a, FLOOR), polar(S, R_ST + 0.07, a + 30, FLOOR), 0.1, 0.1)               # sill ring
        bm_beam(k[TIMBER], polar(S, R_ST + 0.03, a, EAVE - 0.05), polar(S, R_ST + 0.03, a + 30, EAVE - 0.05), 0.08, 0.1)  # head ring
        p = polar(S, R_ST + 0.012, a, (FLOOR + EAVE) / 2)
        bm_box(k[TIMBER], (0.08, 0.08, EAVE - FLOOR), tuple(p), (0, 0, a))                                                # post
    bm_cyl(k["wood_dark:0.5:0.95"], R_ST + 0.07, R_ST + 0.07, 0.06, (S.x, S.y, FLOOR - 0.03), rot=(0, 0, 15), seg=12)     # the floor, from below
    k.emit("Study_Frame", col, root, bevel=0.008)
    bm_cyl(k["cream:0.0:0.42"], R_ST, R_ST, EAVE - FLOOR, (S.x, S.y, (FLOOR + EAVE) / 2), rot=(0, 0, 15), seg=12)
    k.emit("Study_Plaster", col, root)
    wall_r = R_ST * math.cos(math.radians(15)) + 0.004
    for i in range(12):
        a = 30 * i
        if a == 270:
            arch_door(k, polar(S, wall_r, a, FLOOR + 0.05), tangent(a), 0.23, 0.52, frame=None)
        elif a == 90:
            continue                                                         # (the banner hangs here)
        elif i % 2 == 1:
            arch_window(k, polar(S, wall_r, a, FLOOR + 0.17), tangent(a), 0.15, 0.37, glow=WINDOW, frame=TIMBER, th=0.035, proud=0.035, n=4)
        else:                                                                # cross braces
            c = polar(S, wall_r + 0.012, a, 0)
            t = tangent(a)
            for s in (1, -1):
                bm_beam(k[TIMBER], c - t * 0.125 * s + UP * (FLOOR + 0.06), c + t * 0.125 * s + UP * (EAVE - 0.1), 0.03, 0.05, up=tuple(polar((0, 0), 1, a)))
    hanging_banner(k, polar(S, R_ST + 0.1, 90, EAVE - 0.14), tangent(90), 0.34, 0.95, kind="star")
    for s in (-1, 1):
        bm_beam(k[TIMBER], polar(S, R_ST, 90, EAVE - 0.14) + Vector((s * 0.19, 0, 0)), polar(S, R_ST + 0.16, 90, EAVE - 0.14) + Vector((s * 0.19, 0, 0)), 0.04, 0.04)
    k.emit("Study", col, root)

    # ---- the roof: a tiled cone cut open at the top, a brass rim round the well the crystal floats over
    bm_tile_cone(k[TILES], rnd, S, R_EAVE, EAVE, RIM - EAVE, rows=5, n=14, top=R_TOP, flare=0.06)
    k.emit("Roof", col, root, vary=0.09)
    ring_at = lambda r, z, n=14: [polar(S, r, 360.0 * i / n, z) for i in range(n)]
    bm_loft(k[TILES_UNDER], [ring_at(R_EAVE - 0.02, EAVE - 0.035), ring_at(R_TOP - 0.015, RIM - 0.03), ring_at(R_TOP - 0.06, RIM - 0.03), ring_at(R_TOP - 0.11, RIM - 0.3)])
    k.emit("Roof_Under", col, root)
    ring(k[GOLD], (S.x, S.y, 0), R_TOP + 0.07, R_TOP - 0.035, RIM - 0.05, RIM + 0.04, seg=14)
    for i in range(7):
        p = polar(S, R_TOP + 0.075, 360.0 * i / 7 + 12, RIM - 0.005)
        bm_ellipsoid(k[GOLD], tuple(p), (0.04, 0.04, 0.04), u=6, v=4)
    bm_cyl(k["black:0.3:0.7"], R_TOP - 0.1, R_TOP - 0.1, 0.02, (S.x, S.y, RIM - 0.29), seg=12)
    bm_cyl(k[WELL], 0.2, 0.2, 0.02, (S.x, S.y, RIM - 0.28), seg=10)
    k.emit("Roof_Fittings", col, root)

    # ---- the library: a low round annex under its own tiled cone, its door facing the rune circle
    bm_block_course(k[STONE_FOOT], rnd, A, 0.77, T, 0.13, 12, depth=0.24)
    course_tower(k, rnd, A, 0.72, 0.7, T + 0.13, 1.1, courses=4, n=11)
    for a in (205, 335, 150, 30):
        arch_window(k, polar(A, 0.715, a, 0.62), tangent(a), 0.15, 0.32, glow=WINDOW, th=0.05, proud=0.04, n=4)
    arch_door(k, polar(A, 0.72, 270, T + 0.03), tangent(270), 0.34, 0.58, th=0.08)
    ch = polar(A, 0.44, 148, 0)                                               # a chimney through the roof
    bm_box(k[STONE], (0.19, 0.19, 0.62), (ch.x, ch.y, 1.52), (0, 0, 148))
    bm_box(k[STONE_LIGHT], (0.25, 0.25, 0.06), (ch.x, ch.y, 1.85), (0, 0, 148))
    k.emit("Library", col, root, vary=0.07)
    for i in range(11):
        a = 360.0 * i / 11
        bm_beam(k[TIMBER], polar(A, 0.76, a, 1.13), polar(A, 0.76, a + 360.0 / 11, 1.13), 0.08, 0.08)
    k.emit("Library_Eave", col, root)
    cone_roof(k, rnd, A, 0.86, 1.15, 0.74, rows=4, n=13, spike=0.24)
    k.emit("Library_Roof", col, root, vary=0.09)
    ta = 22                                                                   # a brass telescope out of a roof hatch
    tp = polar(A, 0.5, ta, 1.5)
    td = (polar((0, 0), 1, ta) * 0.55 + UP * 0.83).normalized()
    bm_box(k[TIMBER], (0.2, 0.24, 0.16), tuple(tp - UP * 0.03), (0, 0, ta))
    bm_tube(k[GOLD], [tp, tp + td * 0.28, tp + td * 0.29, tp + td * 0.5], [0.045, 0.045, 0.06, 0.065], n=8)
    k.emit("Library_Scope", col, root)

    # ---- the stair turret between them: its corbelled, battlemented top is the landing at the study's door
    course_tower(k, rnd, TR, 0.42, 0.4, T, FLOOR - 0.2, courses=7, n=8, depth=0.14)
    bm_block_course(k[STONE_LIGHT], rnd, TR, 0.46, FLOOR - 0.2, 0.1, 10, depth=0.2)
    bm_block_course(k[STONE_LIGHT], rnd, TR, 0.51, FLOOR - 0.1, 0.1, 10, depth=0.26, phase=0.5)
    bm_block_course(k[STONE], rnd, TR, 0.52, FLOOR, 0.13, 9, depth=0.1, skip=lambda a: 50 < a < 130)
    for a in (150, 210, 270, 330, 30):
        half = 0.2 / 0.52 * 0.5
        _wedge(k[STONE], TR, math.radians(a) - half, math.radians(a) + half, 0.42, 0.52, FLOOR + 0.125, FLOOR + 0.26)
    for a in (0, 180):
        arch_window(k, polar(TR, 0.412, a, 1.0), tangent(a), 0.08, 0.24, glow=WINDOW, th=0.04, proud=0.03, n=3, sill=False)
    k.emit("Turret", col, root, vary=0.07)
    bm_cyl(k["stone2:0.1:0.5"], 0.44, 0.44, 0.05, (TR.x, TR.y, FLOOR - 0.022), seg=12)
    k.emit("Turret_Floor", col, root)

    # ---- the rune circle at the library door: a dark half-round step inlaid with glowing glyphs, two crystal lamps
    hs = [door + Vector((0.38, 0.02, 0))] + [polar(door, 0.38, 360 - 180.0 * i / 8) for i in range(9)] + [door + Vector((-0.38, 0.02, 0))]
    prism(k["stone_dark:0.15:0.6"], list(reversed(hs)), T - 0.01, T + 0.075)
    k.emit("Rune_Step", col, root, bevel=0.01)
    for i in range(6):
        a0 = math.radians(186 + 28.5 * i)
        _wedge(k[RUNE], door, a0, a0 + math.radians(22), 0.27, 0.32, T + 0.07, T + 0.085)
    for i in range(5):
        p = polar(door, 0.165, 198 + 36 * i, T + 0.079)
        bm_box(k[RUNE], (0.075, 0.035, 0.012), tuple(p), (0, 0, 198 + 36 * i + (50 if i % 2 else -40)))
        bm_box(k[RUNE], (0.03, 0.06, 0.012), tuple(p), (0, 0, 198 + 36 * i + (50 if i % 2 else -40)))
    for sx in (-1, 1):
        lp = Vector((sx * 0.5, door.y - 0.2, 0))
        bm_gem(k[VIOLET], (lp.x, lp.y, T + 0.56), 0.075, 0.16, 0.13, n=5)
        bm_cyl(k[STONE_LIGHT], 0.07, 0.1, 0.3, (lp.x, lp.y, T + 0.15), seg=6)
        bm_cyl(k[GOLD], 0.095, 0.07, 0.05, (lp.x, lp.y, T + 0.32), seg=6)
    k.emit("Rune", col, root)

    crew = empty("Crew", col, root, (TR.x, TR.y, FLOOR), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(180))      # looks out over the library, toward the camera
    crew_dummy(col, crew, 1.1, "staff")
    empty("Head", col, root, (S.x, S.y, RIM), 0.5, "SINGLE_ARROW")
    return root


# ---- the crystal and its orrery, in the head's space
N1 = Vector((math.sin(math.radians(22)), 0, math.cos(math.radians(22))))          # ring 1 leans; it wheels round Z
N2 = Vector((0, math.sin(math.radians(32)), math.cos(math.radians(32))))          # ring 2 tumbles about X
N3 = Vector((-math.sin(math.radians(40)), 0, math.cos(math.radians(40))))         # ring 3 tumbles about Y
RINGS = (("ring.1", N1, 0.62), ("ring.2", N2, 0.54), ("ring.3", N3, 0.47))
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "crystal": ((0, 0, CZ), (0, 0, CZ + 0.3), "root"),
    "ring.1": ((0, 0, CZ), (0.3, 0, CZ), "root"),
    "ring.2": ((0, 0, CZ), (0, 0.3, CZ), "root"),
    "ring.3": ((0, 0, CZ), (0, -0.3, CZ), "root"),
    "orbit": ((0, 0, CZ), (0, 0, CZ - 0.3), "root"),
    "flash": ((0, 0, CZ), (0.3, 0.3, CZ), "root"),
}


def build_head():
    col = collection("Arcane")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    c = Vector((0, 0, CZ))
    k = Kit()
    bm_gem(k[VIOLET], c, 0.24, 0.38, 0.33, n=6, girdle=0.1)
    k.emit("Head_Crystal", col, rig=rig, bone="crystal")
    for i, (bone, nrm, r) in enumerate(RINGS):
        bm_ring_n(k["gold:0.05:0.6"], c, nrm, r, r - 0.05, 0.024, seg=20)
        x = nrm.orthogonal().normalized()
        y = nrm.cross(x)
        for j in range(4):                                                    # rune studs, and a little planet
            d = x * math.cos(math.radians(90 * j + 20)) + y * math.sin(math.radians(90 * j + 20))
            bm_box(k["team!:0.1:0.5"], (0.065, 0.065, 0.065), tuple(c + d * (r - 0.025)), tuple(math.degrees(e) for e in Vector((0, 0, 1)).rotation_difference(nrm).to_euler()))
        bm_ellipsoid(k[("gold:0.0:0.4", "team!:0.0:0.4", "white:0.0:0.4")[i]], tuple(c + x * (r - 0.025)), (0.07 - 0.006 * i,) * 3, u=7, v=5)
        k.emit("Head_Ring%d" % (i + 1), col, rig=rig, bone=bone)
    for i in range(3):
        a = math.radians(120 * i + 30)
        bm_gem(k[VIOLET], c + Vector((math.cos(a) * 0.72, math.sin(a) * 0.72, -0.3 + 0.1 * i)), 0.055, 0.13, 0.1, n=4, girdle=0.02)
    k.emit("Head_Shards", col, rig=rig, bone="orbit")
    bm_ring_n(k["glow:0.8,0.6,1.0,1.1"], c, (0, 0, 1), 0.34, 0.27, 0.012, seg=16)
    k.emit("Head_Flash", col, rig=rig, bone="flash")
    empty("Muzzle", col, head, (0, 0, CZ), 0.25, "SPHERE")
    return rig


IDLE_LEN = 120
FIRE_LEN = 18


def _local(pb, q):
    """An armature-space rotation as this bone's own pose rotation."""
    r = pb.bone.matrix_local.to_quaternion()
    return r.inverted() @ q @ r


def pose(rig, spin=0.0, bob=0.0, flare=1.0, turn=0.0, level=0.0, whirl=0.0, orbit=0.0, flash=0.0):
    """turn: the rings' own tumbling (degrees: ring 1 wheels round Z, 2 and 3 roll about X and Y, twice as fast);
    level: 0..1 pulls all three flat (the snap); whirl: a spin about each ring's own axis; flash: the burst's size."""
    pb = rig.pose.bones
    rest_pose(rig)
    pb["crystal"].rotation_quaternion = arm_space_quat(pb["crystal"], (0, 0, 1), spin)
    pb["crystal"].location = arm_space_loc(pb["crystal"], (0, 0, bob))
    pb["crystal"].scale = (flare, flare, flare)
    z = Vector((0, 0, 1))
    for (bone, nrm, r), axis, rate in zip(RINGS, ((0, 0, 1), (1, 0, 0), (0, 1, 0)), (1.0, 2.0, -2.0)):
        q = Quaternion(Vector(axis), math.radians(turn * rate))
        flat = nrm.rotation_difference(z)                # lays the ring level
        q = q.slerp(flat, level) if level > 0.0 else q
        q = q @ Quaternion(nrm, math.radians(whirl * (1 if rate > 0 else -1)))
        pb[bone].rotation_quaternion = _local(pb[bone], q)
        pb[bone].location = arm_space_loc(pb[bone], (0, 0, bob * 0.5))
    pb["orbit"].rotation_quaternion = arm_space_quat(pb["orbit"], (0, 0, 1), orbit)
    pb["orbit"].location = arm_space_loc(pb["orbit"], (0, 0, -bob))
    s = max(flash, 0.001)
    pb["flash"].scale = (s, s, s)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, spin=360 * t, bob=0.045 * math.sin(2 * math.pi * t * 2), flare=1.0 + 0.04 * math.sin(2 * math.pi * t * 4),
             turn=360 * t, orbit=-360 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # gathers (the crystal dips and tightens, the rings snap level), bursts on frame 4, then the rings whip one
        # whole turn round as everything settles back into the idle's first pose
        dip = smooth(f / 3.0) * (1 - smooth((f - 3) / 2.0))
        burst = smooth((f - 3) / 1.5) * (1 - smooth((f - 5) / 9.0))
        level = smooth(f / 3.0) * (1 - smooth((f - 7) / 9.0))
        pose(rig, spin=360 * smooth(f / FIRE_LEN), bob=-0.12 * dip + 0.14 * burst, flare=1.0 - 0.14 * dip + 0.5 * burst,
             level=level, whirl=360 * smooth((f - 2) / 14.0), orbit=-360 * smooth(f / FIRE_LEN),
             flash=2.6 * smooth((f - 3) / 4.0) * (1 - smooth((f - 7) / 5.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.0, 1.85), "dist": 9.0, "yaw": 150, "pitch": 20, "anim_target": (S.x, S.y, RIM + 0.35), "anim_dist": 4.6,
           "frames": [("idle", 0), ("idle", 34), ("fire", 3), ("fire", 5), ("fire", 10)],
           "extra": [{"yaw": 20, "pitch": 22, "dist": 5.2, "target": (0, -0.3, 1.7)},
                     {"yaw": 0, "pitch": 40, "dist": 4.6, "target": (0, -1.3, 0.6)},
                     {"yaw": 165, "pitch": 12, "dist": 5.0, "target": (0, 1.2, 1.5)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
