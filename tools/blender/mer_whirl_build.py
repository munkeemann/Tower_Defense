"""Builds the Whirlpool Shrine (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Tide tower: a
swirling vortex that drags ground enemies back along the road.

    python tools/blender/build.py mer_whirl --out <preview dir>

One shrine, in two tiers of water. The lower tier is a broad stone basin that follows the whole footprint. From it, on
the front cell, rises the whirlpool's bowl of coursed stone: its water turns in a stepped spiral funnel, darker toward a
glowing eye. Three twisted shell columns stand on the bowl's rim and lean together under a carved ring in the team's
color, hung with pennants; coral arches from the ring hold a great pearl over the eye (the Muzzle). Under the two back
columns the bowl spills through gates down stepped cascades into the lower basin. Back-left: the altar, a giant clam
with its pearl on a stepped dais, reached by stepping stones. Back-right: the reef garden, coral, sponges and kelp.
It's an aura: nothing turns, so the Rig hangs on the root. idle: the whirlpool turns, the pearl bobs, foam tumbles down
the cascades, pennants and kelp sway. fire (every pulse): the vortex spins up and its funnel plunges, the eye and the
pearl flare, the colonnade shivers, and a ring of tidewater runs out over the lower basin.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_spires_common.py"), encoding="utf-8").read())

TID = "mer_whirl"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
LAGOON = TOP + 0.085                  # the lower basin's water
C = Vector((0.0, 0.7, 0.0))           # the bowl's middle
R_FOOT, R_WALL, R_IN = 0.86, 0.8, 0.64
SILL = TOP + 0.6                      # the top of the wall under the coping (the spill gates' sills)
RIM = TOP + 0.76                      # the top of the coping
WATER = TOP + 0.65                    # the whirlpool's level
R_VORTEX, R_EYE, DEPTH = 0.66, 0.08, 0.3
PILLARS = (90.0, 210.0, 330.0)        # where the columns stand on the rim (degrees round the bowl)
GATES = (210.0, 330.0)                # the two that stand over a spill gate
COL_R, COL_LEAN = 0.74, 0.13          # the columns' place on the rim, and how far they lean in at the top
COL_Z0, COL_H = RIM + 0.2, 0.74
RING_Z = COL_Z0 + COL_H - 0.03        # the carved ring's underside
RING_R = COL_R - COL_LEAN
PEARL = Vector((C.x, C.y, RING_Z + 0.42))
APEX = Vector((C.x, C.y, RING_Z + 0.92))          # where the coral ribs meet over the pearl
STEPS = 3
STEP_D, STEP_H = 0.22, 0.165
KELP = [("kelp.A", Vector((BR.x + 0.72, BR.y - 0.5, LAGOON - 0.03)), 0.95, (0.1, -0.08)),
        ("kelp.B", Vector((BR.x - 0.25, BR.y - 0.72, LAGOON - 0.03)), 0.7, (-0.05, -0.1)),
        ("kelp.C", Vector((BL.x - 0.78, BL.y + 0.42, LAGOON - 0.03)), 0.85, (-0.1, 0.06))]


# a whorl with a sharp shoulder and a ledge stepping in to the seam (the ledge takes the team's color)
LEDGE = [(0.0, 0.0), (0.12, 0.085), (0.46, 0.16), (0.7, 0.235), (0.83, 0.1), (1.0, 0.0)]


def polar(a, r, z=0.0):
    return Vector((C.x + r * math.cos(math.radians(a)), C.y + r * math.sin(math.radians(a)), z))


def curb(bm, rnd, cells, ins_out, ins_in, z0, z1, block=0.42, gap=0.02):
    """A low wall of mitred blocks along the footprint's outline, between two insets."""
    outer, inner = outline(cells, ins_out), outline(cells, ins_in)
    n = len(outer)
    for i in range(n):
        o0, o1, i0, i1 = outer[i], outer[(i + 1) % n], inner[i], inner[(i + 1) % n]
        cnt = max(1, int(round((o1 - o0).length / block)))
        for j in range(cnt):
            g = gap / max((o1 - o0).length, 1e-6)
            a, b = j / cnt + g * 0.5, (j + 1) / cnt - g * 0.5
            lift = rnd.uniform(-0.012, 0.012)
            prism(bm, [o0.lerp(o1, a), o0.lerp(o1, b), i0.lerp(i1, b), i0.lerp(i1, a)], z0, z1 + lift)
    return bm


def bm_vortex(water, foam, arms=3, wind=1.3, lam=0.3, step_deg=20.0, foam_t=0.76):
    """The whirlpool, about the origin at height 0: `arms` terraces winding inward and down to the eye, each one
    dropping to the next over a step (steep faces come out darker), with a line of foam along its lip."""
    R, re = R_VORTEX, R_EYE
    b = math.log(R / re) / (2 * math.pi * wind)
    da = 2 * math.pi / arms
    st = math.radians(step_deg)
    n0, n1 = -int(round(da / st)), int(round(2 * math.pi * wind / st))

    def H(psi):
        r = min(R, R * math.exp(-b * psi))
        return -DEPTH * ((R - r) / (R - re)) ** 1.9

    def P(a, i, t, drop=False):
        psi = i * st
        r = min(R + 0.03, R * math.exp(-b * (psi + t * da)))
        phi = -a * da + psi
        z = H(psi + da) if drop else H(psi + lam * t * da)
        return Vector((r * math.cos(phi), r * math.sin(phi), z))
    for a in range(arms):
        for i in range(n0, n1):
            for bm, t0, t1 in ((water, 0.0, foam_t), (foam, foam_t, 1.0)):
                bm.faces.new([bm.verts.new(p) for p in (P(a, i, t0), P(a, i + 1, t0), P(a, i + 1, t1), P(a, i, t1))])
            water.faces.new([water.verts.new(p) for p in (P(a, i, 1.0), P(a, i + 1, 1.0), P(a, i + 1, 1.0, True), P(a, i, 1.0, True))])
    for bm in (water, foam):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
        bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges[:])
        for f in bm.faces:
            f.normal_update()
            c = f.calc_center_median()
            inward = Vector((-c.x, -c.y, 0))
            if (f.normal.z < -0.05) or (abs(f.normal.z) <= 0.05 and f.normal.dot(inward) < 0):
                f.normal_flip()


def build_base():
    col = collection("Mer_whirl")
    root = empty("Mer_whirl", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(73)
    k = Kit()
    # ---- the lower tier: one broad basin over the whole footprint, a curb of mitred blocks, a dark bed
    bm_flat(k["stone_dark:0.55:0.95"], outline(CELLS, 0.2), T + 0.012)
    k.emit("Basin_Bed", col, root)
    bm_flat(k["water"], outline(CELLS, 0.3), LAGOON)
    k.emit("Basin_Water", col, root)
    curb(k["stone2:0.1:0.8"], rnd, CELLS, 0.16, 0.36, T - 0.01, T + 0.2)
    k.emit("Basin_Curb", col, root, vary=0.09, seed=2)
    # ---- the bowl: a foot course, two courses of wall, a coping with two spill gates; a dark lining
    bm_block_course(k["stone:0.2:0.9"], rnd, C, R_FOOT, T - 0.01, 0.15, 14, depth=0.2)
    bm_block_course(k["stone2:0.1:0.8"], rnd, C, R_WALL + 0.02, T + 0.14, 0.23, 12, depth=0.17)
    bm_block_course(k["stone2:0.1:0.8"], rnd, C, R_WALL, T + 0.37, 0.23, 12, depth=0.17, phase=0.5)
    gate = lambda a: any(abs((a - g + 180) % 360 - 180) < 12 for g in GATES)
    bm_block_course(k["stone_warm:0.05:0.6"], rnd, C, R_WALL + 0.045, SILL, RIM - SILL, 12, depth=0.24, phase=0.5, skip=gate)
    k.emit("Bowl", col, root, bevel=0.012, vary=0.08, seed=5)
    ring(k["stone_dark:0.4:0.95"], (C.x, C.y, 0), R_WALL - 0.08, R_IN - 0.02, T, RIM - 0.03, seg=20)
    k.emit("Bowl_Lining", col, root)
    # the shrine's face, toward the back: a great scallop in the team's color on the bowl's wall, a pearl at its hinge
    bm_scallop(k["team!:0.08:0.7"], polar(270, R_WALL + 0.05, T + 0.17), r=0.36, yaw=180, tilt=80, ribs=6, depth=0.2)
    k.emit("Emblem", col, root)
    bm_ellipsoid(k["glow:0.6,0.92,1.0,0.8"], tuple(polar(270, R_WALL + 0.1, T + 0.2)), (0.07, 0.07, 0.07), u=7, v=5)
    k.emit("Emblem_Pearl", col, root)
    # the columns' pedestals: blocks on the rim (lintels over the two gates)
    for a in PILLARS:
        p = polar(a, COL_R, RIM + 0.1)
        bm_box(k["stone2:0.05:0.6"], (0.3, 0.52 if a in GATES else 0.36, 0.2), tuple(p), (0, 0, a))
        bm_box(k["stone_warm:0.05:0.5"], (0.36, 0.4 if a in GATES else 0.42, 0.05), (p.x, p.y, RIM + 0.215), (0, 0, a))
    k.emit("Pedestals", col, root, bevel=0.015)
    # ---- the cascades: three steps down from each gate, water sheets and falls, cheek walls
    for a in GATES:
        e = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        tn = Vector((-e.y, e.x, 0))
        o = C + e * R_WALL
        for s in range(STEPS):
            r0, z = s * STEP_D, SILL - 0.06 - s * STEP_H
            mid = o + e * (r0 + STEP_D * 0.5 + 0.01)
            bm_box(k["stone:0.15:0.85"], (STEP_D + 0.06, 0.56, z - T + 0.02), (mid.x, mid.y, (z + T - 0.02) / 2), (0, 0, a))
            bm_box(k["water"], (STEP_D + 0.04, 0.4, 0.035), (mid.x, mid.y, z + 0.012), (0, 0, a))                   # the sheet on the tread
            lip = o + e * (r0 + STEP_D + 0.035)
            zn = (z - STEP_H) if s < STEPS - 1 else LAGOON - 0.03
            bm_box(k["water"], (0.035, 0.4, z - zn + 0.02), (lip.x, lip.y, (z + zn) / 2 + 0.02), (0, 0, a))        # the fall
            bm_box(k["white:0.0:0.3"], (0.07, 0.36, 0.022), (lip.x - e.x * 0.02, lip.y - e.y * 0.02, z + 0.034), (0, 0, a))
        sheet = o - e * 0.1                                         # the water in the gate, over the sill
        bm_box(k["water"], (0.3, 0.4, 0.05), (sheet.x, sheet.y, WATER - 0.02), (0, 0, a))
        for sg in (-1, 1):                                           # cheek walls, stepping down beside the stair
            for s in range(STEPS):
                mid = o + e * (s * STEP_D + STEP_D * 0.5) + tn * sg * 0.3
                z = SILL + 0.06 - s * STEP_H
                bm_box(k["stone2:0.1:0.7"], (STEP_D + 0.03, 0.1, z - T + 0.02), (mid.x, mid.y, (z + T - 0.02) / 2), (0, 0, a))
        foot = o + e * (STEPS * STEP_D + 0.16)
        bm_ring_flat(k["white:0.0:0.3"], (foot.x - e.x * 0.06, foot.y - e.y * 0.06, 0), 0.25, 0.2, LAGOON + 0.004, seg=12, th=0.008)
    k.emit("Cascade", col, root, vary=0.06, seed=9)
    # ---- back-left: the altar. A stepped dais in the basin, a giant clam with its pearl, conch horns, a stepping stone
    A = BL + Vector((-0.1, -0.06, 0))
    bm_cyl(k["stone:0.15:0.8"], 0.57, 0.54, 0.16, (A.x, A.y, T + 0.07), seg=12)
    bm_cyl(k["stone2:0.05:0.6"], 0.43, 0.41, 0.14, (A.x, A.y, T + 0.22), seg=12)
    k.emit("Altar_Dais", col, root, bevel=0.02)
    yaw = 205.0                                                      # the clam opens toward the back, where you stand
    fw = Vector((math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0))
    side = Vector((fw.y, -fw.x, 0))
    az = T + 0.47
    B = A - fw * 0.05
    bm_cyl(k["stone_warm:0.05:0.6"], 0.29, 0.27, 0.18, (B.x, B.y, T + 0.38), seg=8)
    k.emit("Altar_Block", col, root, bevel=0.02)
    cloth = k["team!:0.1:0.7"]                                       # the altar cloth: over the block and down its front
    bm_box(cloth, (0.34, 0.6, 0.025), (B.x, B.y, az + 0.012), (0, 0, -yaw))
    drape = B + fw * 0.3
    bm_box(cloth, (0.34, 0.03, 0.2), (drape.x, drape.y, az - 0.09), (0, 0, -yaw))
    bm_box(k["gold:0.1:0.5"], (0.36, 0.036, 0.035), (drape.x, drape.y, az - 0.2), (0, 0, -yaw))
    k.emit("Altar_Cloth", col, root)
    hinge = B - fw * 0.27 + Vector((0, 0, az + 0.02))
    bm_scallop(k["cream:0.02:0.6"], hinge, r=0.5, yaw=yaw, tilt=168, ribs=7)
    bm_scallop(k["cream:0.02:0.55"], hinge + Vector((0, 0, 0.02)), r=0.5, yaw=yaw + 180, tilt=48, ribs=7)
    k.emit("Altar_Clam", col, root)
    mid = hinge + fw * 0.25
    bm_ellipsoid(k["salmon:0.2:0.7"], (mid.x, mid.y, az + 0.07), (0.3, 0.22, 0.05), rot=(0, 0, -yaw), u=8, v=4)
    k.emit("Altar_Flesh", col, root)
    bm_ellipsoid(k["glow:0.6,0.92,1.0,0.8"], (mid.x, mid.y, az + 0.19), (0.13, 0.13, 0.13), u=8, v=6)
    k.emit("Altar_Pearl", col, root)
    for sx, h in ((-1, 0.44), (1, 0.36)):                            # a conch standing each side
        p = A + side * sx * 0.44 + fw * 0.16
        TurretShell((p.x, p.y, T + 0.15), h, 0.12, turns=3.4, k=0.74, steps=7, th0=sx * 1.0, hand=sx, sunk=0.25).build(
            k, "beige:0.05:0.8", {3: "salmon:0.2:0.7"})
    k.emit("Altar_Conches", col, root)
    g = C + Vector((math.cos(math.radians(210)), math.sin(math.radians(210)), 0)) * (R_WALL + STEPS * STEP_D + 0.12)
    p = g.lerp(A, 0.42) + Vector((0.03, -0.1, 0))                    # a stepping stone from the cascade's foot to the dais
    bm_boulder(k["stone2:0.1:0.7"], rnd, (p.x, p.y, T + 0.02), 0.16, squash=(1.2, 1.0, 0.42), n=10, sink=0.1)
    bm_starfish(k["orange:0.15:0.6"], (A.x + side.x * 0.1 - fw.x * 0.48, A.y + side.y * 0.1 - fw.y * 0.48, T + 0.155), 0.11, yaw=10)
    k.emit("Altar_Stones", col, root, vary=0.07)
    # ---- back-right: the reef garden on a mound of rocks
    G = BR + Vector((0.22, -0.12, 0))
    for dx, dy, r, sq in ((0.0, 0.0, 0.42, 0.6), (0.4, -0.22, 0.28, 0.6), (-0.36, -0.3, 0.26, 0.55), (0.1, 0.4, 0.24, 0.5)):
        bm_boulder(k["stone2:0.15:0.9"], rnd, (G.x + dx, G.y + dy, T), r, squash=(1.1, 1.0, sq), n=12)
    k.emit("Reef_Rocks", col, root, vary=0.08)
    bm_coral(k["salmon:0.12:0.85"], rnd, (G.x, G.y, T + 0.2), h=1.05, r=0.095, depth=3, knob=1.45)
    bm_coral(k["orange:0.1:0.7"], rnd, (G.x + 0.44, G.y - 0.26, T + 0.14), h=0.6, r=0.075, depth=2, up=(0.25, -0.1, 1), knob=1.5)
    bm_coral(k["red:0.05:0.5"], rnd, (G.x - 0.4, G.y - 0.34, T + 0.12), h=0.5, r=0.07, depth=2, up=(-0.2, -0.15, 1), knob=1.5)
    bm_tube_coral(k["sky:0.2:0.8"], k["black:0.3:0.7"], rnd, (G.x + 0.12, G.y + 0.44, T + 0.1), n=5, h=(0.18, 0.4), r=(0.055, 0.08))
    bm_blob(k["beige:0.1:0.7"], rnd, (G.x + 0.5, G.y + 0.2, T + 0.12), 0.17, squash=(1.1, 1.0, 0.75), jitter=0.08, sub=2)
    bm_starfish(k["orange:0.15:0.6"], (G.x + 0.36, G.y - 0.2, T + 0.34), 0.12, yaw=30, normal=(0.2, -0.1, 1))
    k.emit("Reef", col, root)
    # ---- sea life on the curb
    cz = T + 0.2
    for (x, y), kind in (((BL.x - 0.78, BL.y - 0.42), "star"), ((BR.x + 0.3, BR.y + 0.82), "star"), ((BL.x + 0.25, BL.y - 0.83), "barn"),
                         ((BR.x + 0.84, BR.y - 0.1), "barn"), ((F.x - 0.62, F.y + 0.72), "barn"), ((BR.x - 0.4, BR.y - 0.83), "shell")):
        if kind == "star":
            bm_starfish(k["orange:0.15:0.6"], (x, y, cz), 0.12, yaw=rnd.uniform(0, 72))
        elif kind == "barn":
            bm_barnacles(k["stone2:0.05:0.5"], k["black:0.3:0.6"], rnd, (x, y, cz - 0.005), (0, 0, 1), n=5, r=0.05, spread=0.1)
        else:
            bm_scallop(k["cream:0.05:0.6"], (x, y, cz), r=0.13, yaw=200, tilt=35)
    k.emit("Curb_Life", col, root)
    empty("Head", col, root, (C.x, C.y, TOP), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "vortex": ((C.x, C.y, WATER), (C.x, C.y, WATER + 0.25), "root"),
         "eye": ((C.x, C.y, WATER - DEPTH * 0.52), (C.x, C.y, WATER - DEPTH * 0.52 + 0.15), "vortex"),
         "frame": ((C.x, C.y, RIM), (C.x, C.y, RIM + 0.4), "root"),
         "pearl": (tuple(PEARL), tuple(PEARL + Vector((0, 0, 0.2))), "root"),
         "surge": ((C.x, C.y, LAGOON), (C.x, C.y, LAGOON + 0.2), "root")}
PENNANTS = []
for _i, _a in enumerate((150.0, 270.0, 30.0)):
    _p = polar(_a, RING_R + 0.075, RING_Z + 0.02)
    _t = Vector((-math.sin(math.radians(_a)), math.cos(math.radians(_a)), 0))
    PENNANTS.append(("pen.%d" % _i, _p - _t * 0.12, _t))
    flag_bones(BONES, "pen.%d" % _i, _p - _t * 0.12, (0, 0, -1), 0.46, segs=2, parent="frame")
for _n, _b, _h, _l in KELP:
    kelp_bones(BONES, _n, _b, _h, lean=_l)
for _g in range(len(GATES)):
    for _s in range(STEPS):
        _e = Vector((math.cos(math.radians(GATES[_g])), math.sin(math.radians(GATES[_g])), 0))
        _p = C + _e * (R_WALL + (_s + 1) * STEP_D + 0.05) + Vector((0, 0, SILL - 0.03 - _s * STEP_H))
        BONES["fall.%d.%d" % (_g, _s)] = (tuple(_p), tuple(_p + Vector((0, 0, 0.12))), "root")


def build_rig():
    col = collection("Mer_whirl")
    root = bpy.data.objects["Mer_whirl"]
    head = bpy.data.objects["Head"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(12)
    k = Kit()
    # ---- the whirlpool and its eye
    wat, foam = bmesh.new(), bmesh.new()
    bm_vortex(wat, foam)
    for bm in (wat, foam):
        bmesh.ops.translate(bm, verts=bm.verts, vec=(C.x, C.y, WATER))
    _join(k["water"], wat)
    _join(k["white:0.0:0.3"], foam)
    k.emit("Vortex", col, rig=rig, bone="vortex")
    bm_cyl(k["glow:%s,%s,%s,0.9" % SEA], 0.165, 0.13, 0.03, (C.x, C.y, WATER - DEPTH * 0.52), seg=10)
    k.emit("Vortex_Eye", col, rig=rig, bone="eye")
    # ---- the colonnade: three twisted shell columns leaning in, a carved ring in the team's color, a crown of coral
    for i, a in enumerate(PILLARS):
        e = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        tn = Vector((-e.y, e.x, 0))
        base = polar(a, COL_R, COL_Z0)
        sh = TurretShell(tuple(base), COL_H, 0.18, turns=3.3, k=0.84, steps=8, lean=(-e.x * COL_LEAN, -e.y * COL_LEAN),
                         th0=math.radians(a + 40 * i), hand=1 if i % 2 == 0 else -1, sunk=0.3, profile=LEDGE)
        sh.build(k, "cream:0.05:0.85", {3: "team!:0.1:0.7", 4: "team!:0.1:0.7"})
        top = polar(a, RING_R, RING_Z + 0.12)
        rib = [top, top + e * 0.03 + Vector((0, 0, 0.26)), top - e * 0.13 + Vector((0, 0, 0.52)), top - e * 0.36 + Vector((0, 0, 0.72)),
               APEX + e * 0.03]
        bm_tube(k["salmon:0.1:0.8"], rib, [0.085, 0.08, 0.068, 0.055, 0.05], n=6)
        bm_coral(k["salmon:0.1:0.75"], rnd, rib[1] + e * 0.03, h=0.34, r=0.05, up=e * 0.9 + tn * 0.3 * (1 if i % 2 else -1) + Vector((0, 0, 0.7)),
                 depth=2, knob=1.5, n=5)
        bm_ellipsoid(k["salmon:0.1:0.7"], tuple(rib[2] + e * 0.05), (0.07, 0.07, 0.07), u=5, v=3)
    TurretShell((APEX.x, APEX.y, APEX.z + 0.02), 0.3, 0.1, turns=3.0, k=0.72, steps=7, sunk=0.4).build(k, "cream:0.05:0.8", {3: "team!:0.1:0.7"})
    bm_block_course(k["team!:0.1:0.65"], rnd, C, RING_R + 0.075, RING_Z, 0.13, 12, depth=0.15, gap=0.015, jit=0.004)
    ring(k["cream:0.1:0.6"], (C.x, C.y, 0), RING_R + 0.095, RING_R - 0.095, RING_Z - 0.03, RING_Z + 0.005, seg=18)
    ring(k["cream:0.1:0.6"], (C.x, C.y, 0), RING_R + 0.09, RING_R - 0.09, RING_Z + 0.125, RING_Z + 0.155, seg=18)
    for j in range(6):
        p = polar(60 * j + 30, RING_R + 0.085, RING_Z + 0.065)
        bm_ellipsoid(k["white:0.0:0.3"], tuple(p), (0.04, 0.04, 0.04), u=5, v=3)
    k.emit("Colonnade", col, rig=rig, bone="frame")
    for name, top, tn in PENNANTS:
        flag_part("Pennant_" + name[-1], col, rig, name, top, (0, 0, -1), 0.46, 0.24, segs=2, tail="point", hang=tuple(tn))
    # ---- the pearl
    bm_ellipsoid(k["glow:0.5,0.88,1.0,0.75"], tuple(PEARL), (0.19, 0.19, 0.19), u=10, v=7)
    k.emit("Pearl", col, rig=rig, bone="pearl")
    # ---- foam tumbling down each cascade step; the surge ring
    for g, a in enumerate(GATES):
        for s in range(STEPS):
            h, _, _ = BONES["fall.%d.%d" % (g, s)]
            h = Vector(h)
            e = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            tn = Vector((-e.y, e.x, 0))
            for j, off in enumerate((-0.12, 0.02, 0.13)):
                p = h + tn * off + e * (0.01 * j)
                bm_ellipsoid(k["white:0.0:0.25"], tuple(p), (0.045, 0.06, 0.04), rot=(0, 0, a), u=5, v=3)
            k.emit("Fall_%d_%d" % (g, s), col, rig=rig, bone="fall.%d.%d" % (g, s), tag="no_ao")
    bm_ring_flat(k["glow:0.35,0.78,1.0,0.7"], (C.x, C.y, 0), 0.8, 0.7, LAGOON, seg=28, crest=0.07)
    bm_ring_flat(k["white:0.0:0.2"], (C.x, C.y, 0), 0.84, 0.8, LAGOON, seg=28, crest=0.03)
    k.emit("Surge", col, rig=rig, bone="surge", tag="no_ao")
    for (n, b, h, l), sw in zip(KELP, ("teal:0.1:0.75", "grass:0.3:0.9", "teal:0.2:0.8")):
        kelp_part("Kelp_" + n[-1], col, rig, n, rnd, b, h, lean=l, fronds=4, w=0.12, swatch=sw)
    empty("Muzzle", col, head, (PEARL.x - C.x, PEARL.y - C.y, PEARL.z - TOP), 0.25, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 22
HIDE = (0.02, 0.02, 0.02)


def pose(rig, t=0.0, spin=0.0, dip=0.0, eye=1.0, bob=0.0, flare=1.0, shiver=(0.0, 0.0), surge=0.0, push=0.0, flow=None):
    """t: the idle's phase (0..1); spin: the vortex's turn (degrees); dip: how far its funnel plunges (0..1);
    flow: the cascades' phase (0..1, None = t * 4)."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["vortex"].rotation_quaternion = q(pb["vortex"], (0, 0, 1), -spin)
    pb["vortex"].scale = (1.0, 1.0 + 0.95 * dip, 1.0)            # (the bone points up: its own Y is the height)
    pb["eye"].scale = (eye, 1.0, eye)
    pb["frame"].rotation_quaternion = q(pb["frame"], (0, 0, 1), shiver[0]) @ q(pb["frame"], (1, 0, 0), shiver[1])
    pb["pearl"].location = arm_space_loc(pb["pearl"], (0, 0, bob))
    pb["pearl"].scale = (flare,) * 3
    for i, (name, top, tn) in enumerate(PENNANTS):
        wave_flag(rig, name, t * 2 + 0.3 * i, amp=0.9 + push * 0.05, segs=2, axis=tuple(tn))
    for i, (n, b, h, l) in enumerate(KELP):
        out = Vector((b.x - C.x, b.y - C.y, 0)).normalized()
        sway_kelp(rig, n, t + 0.3 * i, push=(-out.y * push, out.x * push))
    fl = (t * 4.0) if flow is None else flow
    for g, a in enumerate(GATES):
        e = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        for s in range(STEPS):
            b = pb["fall.%d.%d" % (g, s)]
            u = (fl + 0.37 * s + 0.5 * g) % 1.0                  # over the lip, down the fall, and gone into the tread below
            drop = STEP_H if s < STEPS - 1 else (SILL - 0.06 - s * STEP_H) - LAGOON
            fall = smooth((u - 0.1) / 0.6)
            sc = min(1.0, u * 9.0) * (1.0 - smooth((u - 0.72) / 0.28))
            b.location = arm_space_loc(b, tuple(e * (0.07 * fall + 0.04 * u) + Vector((0, 0, -drop * fall))))
            b.scale = (max(sc, 0.02),) * 3
    b = pb["surge"]
    if surge <= 0.0 or surge >= 1.0:
        b.scale = HIDE
        b.location = arm_space_loc(b, (0, 0, -0.2))
    else:
        s = 0.9 + 2.1 * (1 - (1 - surge) ** 1.6)
        up = min(1.0, surge * 6.0) * (1.0 - smooth((surge - 0.7) / 0.3))
        b.scale = (s, max(0.05, up), s)
        b.location = arm_space_loc(b, (0, 0, -0.7 * (1 - up) + 0.12 * min(1.0, surge * 2)))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, spin=360.0 * t, eye=1.0 + 0.12 * math.sin(4 * math.pi * t), bob=0.05 * math.sin(2 * math.pi * t),
             flare=1.0 + 0.04 * math.sin(4 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        u = f / FIRE_LEN
        wind = smooth(f / 3.0) * (1 - smooth((f - 3) / 3.0))                 # a breath in: the funnel flattens, the pearl lifts
        plunge = smooth((f - 3) / 3.0) * (1 - smooth((f - 9) / 11.0))
        sh = math.sin(f * 2.6) * plunge
        pose(rig, t=0.0, spin=720.0 * smooth(u) ** 0.9, dip=plunge - 0.35 * wind, eye=1.0 + 0.9 * plunge,
             bob=0.07 * wind - 0.12 * plunge, flare=1.0 + 0.45 * plunge, shiver=(2.2 * sh, 0.9 * math.cos(f * 2.1) * plunge),
             surge=(f - 4) / 15.0, push=24 * smooth((f - 6) / 4.0) * (1 - smooth((f - 11) / 10.0)), flow=0.0 + u)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.1), "dist": 9.6, "yaw": 150, "pitch": 22, "anim_target": (C.x, C.y - 0.2, 1.3), "anim_dist": 6.4,
           "frames": [("idle", 0), ("idle", 24), ("fire", 3), ("fire", 8), ("fire", 14)],
           "extra": [{"yaw": 0, "pitch": 57, "dist": 6.0, "target": (0, 0.2, 0.8)},
                     {"yaw": 25, "pitch": 20, "dist": 4.2, "target": (BL.x + 0.3, BL.y + 0.2, 0.7)},
                     {"yaw": -30, "pitch": 24, "dist": 4.4, "target": (BR.x - 0.3, BR.y + 0.2, 0.7)},
                     {"yaw": 150, "pitch": 40, "dist": 4.0, "target": (C.x, C.y, 1.4)}]}


def build_all():
    build_base()
    build_rig()
    build_anims()
