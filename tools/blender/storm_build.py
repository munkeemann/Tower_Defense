"""Builds the Stormcaller Oak (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Verdant tower:
chain lightning.

    python tools/blender/build.py storm --out <preview dir>

One lightning-scarred great oak on a rocky mound on the front hex. Its trunk is split from the fork down, glowing
blue-white from within, and bound with a sash in the team's color; a storm crystal hangs in the fork between its two
great limbs (the Head / Muzzle) and a ring of storm cloud turns round its crown. The back of the crown is blasted bare:
a broken stub, two bare boughs flying the team's banners. Its two greatest roots run down the mound onto the flanking
hexes, where each grips a rune-carved menhir; glowing channels run from the runes along the roots and up the trunk to
the split. Back right: the druid's stone (Crew, facing the oak). Back left: the bough the lightning tore off.
The rig is under the root (nothing turns with the aim; the Head only carries the Muzzle).
Clips: idle (the cloud turns and flickers, the crystal bobs, turns and pulses, sparks run up the channels, banners
stir), fire (the crystal flares, the cloud jolts and discharges into it, the runes flash, the banners snap).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open(os.path.join(REPO, "tools", "blender", "greatwood_common.py"), encoding="utf-8").read())

TID = "storm"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
T = TOP + 0.05                  # the turf's top (plinth(turf=True))
OAK = Vector((FRONT.x, FRONT.y, 0.0))       # the trunk's axis
ZC = T + 0.25                   # the trunk's own zero
SG = "glow:0.36,0.66,1.0,0.8"   # storm light
SGB = "glow:0.82,0.94,1.0,1.1"  # ... at its brightest
CHAR = "black:0.3:0.8"
CRYS = Vector((OAK.x, OAK.y, T + 2.2))      # the crystal's waist
CLOUD = Vector((OAK.x, OAK.y, T + 2.86))    # the cloud ring's middle
CLOUD_R = 1.02
CREW = Vector((1.05, -0.72, T + 0.33))
WINGS = ((335.0, 1.0, "R"), (205.0, -1.0, "L"))     # (the root's bearing from the oak, its side, name)
CHAN = {}                       # the glowing channels' lines, rune to trunk (build_base fills them in)
RUNE_AT = {}                    # the runes' middles


def rp(a, r, off=0.0, z=0.0):
    """A point r out from the oak at bearing a (degrees), `off` to the left of that line, z above the turf."""
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return Vector((OAK.x + ca * r - sa * off, OAK.y + sa * r + ca * off, T + z))


def op(dx, dy, z):
    return Vector((OAK.x + dx, OAK.y + dy, T + z))


def gem(kit, c, r, up, down, a="glow:0.22,0.5,1.0,0.75", b="glow:0.7,0.9,1.0,0.95", n=6):
    """A two-pointed crystal round c: two six-sided gems, one turned half a facet inside the other, in two lights (flat
    glow has no shading: the second gem's edges breaking through the first's faces is what shows its facets)."""
    c = Vector(c)
    x, y = Vector((1, 0, 0)), Vector((0, 1, 0))
    for sw, ph, kr in ((a, 0.0, 1.0), (b, 0.5, 0.94)):
        rows = [oval(c + Vector((0, 0, z)), x, y, rr * kr, rr * kr, n, phase=ph) for z, rr in ((-down * 0.3, r * 0.82), (up * 0.3, r))]
        bm_loft(kit[sw], rows, tip0=c + Vector((0, 0, -down * kr)), tip1=c + Vector((0, 0, up * kr)))


def zigzag(bm, p0, p1, rnd, n=4, jit=0.1, w=0.05, w1=0.02):
    """A fork of lightning from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    side = (p1 - p0).cross(Vector((0.3, 0.2, 1))).normalized()
    pts = [p0.lerp(p1, i / n) + side * (jit * (1 if i % 2 else -1) * (0 if i in (0, n) else 1)) + Vector((0, 0, rnd.uniform(-0.3, 0.3) * jit)) * (0 if i in (0, n) else 1)
           for i in range(n + 1)]
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        bm_beam(bm, pts[i], pts[i + 1], w + (w1 - w) * f0, w + (w1 - w) * f0, w1=w + (w1 - w) * f1, h1=w + (w1 - w) * f1)
    return pts


def build_base():
    col = collection("Storm")
    root = empty("Storm", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(31)
    k = Kit()
    # ---- the rocky mound: a rise of turf ringed with boulders between the oak's buttresses, scree running on to the wings
    bm_blob(k["ground"], rnd, (OAK.x, OAK.y, T - 0.02), 0.98, squash=(1.0, 0.9, 0.36), jitter=0.05, sub=2)
    for a, r, s in ((0, 0.72, 0.3), (60, 0.68, 0.3), (120, 0.68, 0.32), (180, 0.72, 0.3), (250, 0.62, 0.26), (294, 0.62, 0.27), (22, 0.88, 0.19),
                    (158, 0.88, 0.2), (76, 0.86, 0.17), (104, 0.85, 0.18), (272, 0.8, 0.16)):
        p = rp(a, r)
        bm_boulder(k["stone:0.12:0.92"], rnd, (p.x, p.y, T + 0.02), s, squash=(1.0, 1.0, 1.0), n=12)
    for (x, y, s) in ((1.3, 0.34, 0.22), (1.52, -0.6, 0.17), (2.42, -0.86, 0.24), (2.56, 0.12, 0.2), (1.85, -1.02, 0.16), (2.2, 0.38, 0.18), (0.8, -0.1, 0.22),
                      (2.7, -0.42, 0.15), (-1.28, 0.36, 0.22), (-2.4, -0.84, 0.22), (-2.56, 0.1, 0.2), (-1.9, -1.04, 0.17), (-2.22, 0.4, 0.17), (-0.8, -0.1, 0.2),
                      (-2.72, -0.4, 0.15), (-1.0, -0.42, 0.15)):
        if in_footprint(CELLS, x, y, 0.2 + s * 0.6):
            bm_boulder(k["stone:0.15:0.95"], rnd, (x, y, T - 0.02), s, squash=(1.15, 1.0, 0.8), n=10)
    k.emit("Mound", col, root, vary=0.08, seed=3)
    # ---- the oak's trunk: buttressed, its two greatest lobes toward the wings
    lobes = {330: 0.45, 210: 0.45, 90: 0.3, 270: 0.12, 30: 0.18, 150: 0.18, 0: -0.12, 60: -0.12, 120: -0.12, 180: -0.12, 240: -0.1, 300: -0.1}
    trunk = Trunk((OAK.x, OAK.y, ZC), [(-0.1, 0.62, 0.62, 1.0), (0.18, 0.5, 0.5, 0.7), (0.5, 0.42, 0.42, 0.3), (0.85, 0.4, 0.38, 0.08), (1.2, 0.45, 0.38, 0.0)],
                  list(range(0, 360, 30)), lobes, rnd, 0.02)
    tp = trunk.at
    trunk.loft(k[BARK])
    # the split: a crack of light down the back from the fork (and a shorter one down the front), between charred lips
    clear = []
    for crack in ([(0.3, 283, 0.0), (0.45, 288, 2.5), (0.6, 281, 4.0), (0.75, 289, 5.5), (0.9, 283, 7.0), (1.05, 288, 9.0), (1.2, 285, 12.0)],
                  [(0.62, 104, 0.0), (0.78, 109, 3.0), (0.92, 102, 5.0), (1.06, 107, 7.5), (1.2, 104, 10.0)]):
        bm = k[SGB]
        rows = [(bm.verts.new(tp(a - w, z, 0.016)), bm.verts.new(tp(a + w, z, 0.016))) for z, a, w in crack]
        for (l0, r0), (l1, r1) in zip(rows, rows[1:]):
            bm.faces.new((l0, r0, r1, l1))
        for sg in (-1, 1):
            bm_tube(k[CHAR], [tp(a + sg * (w + 2.5), z, 0.0) for z, a, w in crack], [0.02] + [0.034] * (len(crack) - 1), n=4)
        clear += [tp(a, z) for z, a, w in crack]
    # the channels' way up the trunk, from each great lobe round to the crack
    spiral = {"R": [(293, 0.97), (303, 0.8), (315, 0.6), (326, 0.42), (330, 0.26)], "L": [(277, 0.97), (265, 0.8), (248, 0.62), (228, 0.44), (212, 0.27)]}
    for nm in ("R", "L"):
        CHAN[nm] = [tp(a, z, 0.022) for a, z in spiral[nm]]
        clear += CHAN[nm]
    bm_plates(k[BARK_PLATE], trunk.rings, rnd, th=(0.03, 0.055), rows=(0.7, 1.25), gap=0.14, side=0.12, point=0.28,
              skip=lambda c: min((c - q).length for q in clear) < 0.17)
    # a sash in the team's color bound round the trunk across the split, its tails hanging at the back
    bm_sleeve(k["team!:0.1:0.6"], trunk.rings, 2.5, 2.98, grow=0.07)
    for rs, gr in ((2.44, 0.08), (3.0, 0.08)):
        bm_sleeve(k["gold:0.15:0.6"], trunk.rings, rs, rs + 0.07, grow=gr)
    for a in range(15, 360, 30):
        if not 240 < a < 300:
            p = tp(a, 0.64, 0.085)
            bm_beam(k["team!:0.25:0.75"], p, p + Vector((0, 0, -0.2)) + trunk.out(a) * 0.03, 0.12, 0.02, w1=0.02, up=trunk.out(a))
    for a, L in ((252, 0.44), (262, 0.34)):
        p = tp(a, 0.68, 0.1)
        bm_beam(k["team!:0.2:0.7"], p, p + Vector((0, 0, -L)) + trunk.out(a) * 0.06, 0.13, 0.025, up=trunk.out(a))
    # the fork: two great limbs, boughs off them; the back of the crown is bare (a broken stub, two bare boughs)
    def limb(ctrl, radii, n=7, plates=False):
        cp, rad, rings = bm_root(k[BARK], [op(*c) for c in ctrl], radii, n=n, sub=3)
        if plates:
            bm_plates(k[BARK_PLATE], rings, rnd, th=(0.02, 0.04), rows=(1.2, 2.4), gap=0.25, side=0.14, keep=0.7, point=0.28, start=2.0)
        return cp
    limb([(-0.16, 0.0, 1.28), (-0.36, 0.02, 1.68), (-0.66, 0.05, 1.98), (-0.98, 0.04, 2.12), (-1.25, 0.0, 2.16)], [0.3, 0.26, 0.2, 0.15, 0.1], plates=True)
    limb([(0.16, 0.0, 1.28), (0.38, -0.02, 1.7), (0.7, 0.02, 2.0), (1.02, 0.06, 2.14), (1.3, 0.08, 2.18)], [0.3, 0.26, 0.2, 0.15, 0.1], plates=True)
    limb([(-0.5, 0.04, 1.85), (-0.62, 0.4, 2.02), (-0.7, 0.75, 2.08)], [0.15, 0.12, 0.08], n=6)
    limb([(0.55, 0.0, 1.9), (0.6, 0.42, 2.04), (0.55, 0.8, 2.1)], [0.15, 0.12, 0.08], n=6)
    limb([(0.0, 0.25, 1.15), (0.02, 0.6, 1.55), (0.0, 0.95, 1.84)], [0.2, 0.15, 0.1], n=6)
    BOUGH = {"L": limb([(-0.6, 0.05, 1.9), (-0.85, -0.3, 2.0), (-1.1, -0.56, 1.98), (-1.3, -0.72, 2.06)], [0.13, 0.11, 0.08, 0.0], n=5),
             "R": limb([(0.62, 0.0, 1.95), (0.9, -0.32, 2.04), (1.12, -0.56, 2.0), (1.32, -0.7, 2.1)], [0.13, 0.11, 0.08, 0.0], n=5)}
    limb([(-0.9, -0.36, 2.0), (-0.86, -0.62, 2.2), (-0.8, -0.78, 2.42)], [0.06, 0.05, 0.0], n=4)
    limb([(0.95, -0.38, 2.04), (0.9, -0.64, 2.26), (0.98, -0.78, 2.44)], [0.06, 0.05, 0.0], n=4)
    stub = limb([(-0.26, -0.08, 1.22), (-0.42, -0.26, 1.42), (-0.55, -0.4, 1.58)], [0.19, 0.17, 0.15], n=6)
    sd = (stub[-1] - stub[-2]).normalized()
    bm_cyl(k[CHAR], 0.165, 0.15, 0.12, tuple(stub[-1] - sd * 0.03), rot=tuple(math.degrees(v) for v in sd.to_track_quat("Z", "Y").to_euler()), seg=6)
    for i in range(6):
        q = stub[-1] + sd * 0.02 + Vector((rnd.uniform(-0.09, 0.09), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.08, 0.09)))
        bm_thorn(k["cream:0.15:0.6"], q, sd + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0.0, 0.5))), rnd.uniform(0.16, 0.3), 0.05, n=3)
    bm_ellipsoid(k[CHAR], op(0, 0, 1.44), (0.32, 0.27, 0.11), u=8, v=4)          # the fork's scorched bowl
    for dx, dy, h, r in ((0.0, 0.0, 0.42, 0.13), (-0.12, 0.05, 0.28, 0.09), (0.12, -0.05, 0.3, 0.09), (0.02, -0.14, 0.2, 0.07)):
        bm_crystal(k[SG], op(dx, dy, 1.4), op(dx * 1.6, dy * 1.6, 1.44 + h), r, n=5, shoulder=0.55)
    # twigs curling up out of the fork to cradle the crystal
    for a in (35, 155, 270):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        bm_root(k[BARK], [op(0, 0, 1.42) + d * 0.2, op(0, 0, 1.62) + d * 0.36, op(0, 0, 1.86) + d * 0.38, op(0, 0, 2.06) + d * 0.3], [0.05, 0.045, 0.035, 0.0], n=4)
    for nm, sx in (("L", -1), ("R", 1)):                                           # the banners' yards, slung under the bare boughs
        c = BOUGH[nm][6] + Vector((0, 0, -0.2))
        bm_cyl(k["wood_dark:0.2:0.7"], 0.028, 0.028, 0.62, tuple(c), rot=(0, 90, 0), seg=5)
        for dx in (-0.22, 0.22):
            bm_beam(k["sand:0.3:0.7"], c + Vector((dx, 0, 0)), BOUGH[nm][6] + Vector((dx * 0.5, 0, 0.02)), 0.022, 0.022)
    k.emit("Oak", col, root, vary=0.05, seed=4)
    # ---- the crown: pads of leaves on the limbs' ends, to the sides and the front (the middle stays open for the storm)
    for (dx, dy, z, r, sw) in ((-1.32, 0.05, 2.2, 0.52, LEAF_B), (-1.0, 0.3, 2.32, 0.4, LEAF_C), (-0.74, 0.86, 2.16, 0.5, LEAF_A), (-1.25, 0.55, 2.06, 0.36, LEAF_A),
                               (1.38, 0.1, 2.24, 0.54, LEAF_A), (1.05, 0.34, 2.36, 0.4, LEAF_C), (0.56, 0.92, 2.2, 0.5, LEAF_B), (1.2, 0.62, 2.1, 0.36, LEAF_B),
                               (0.0, 1.05, 1.98, 0.52, LEAF_A), (-0.1, 0.92, 2.24, 0.36, LEAF_C), (-1.62, 0.3, 1.96, 0.38, LEAF_A), (1.66, 0.36, 2.0, 0.38, LEAF_B),
                               (-0.42, 1.2, 1.9, 0.36, LEAF_B), (0.4, 1.24, 1.92, 0.36, LEAF_A), (-0.98, 0.72, 2.3, 0.34, LEAF_C), (0.9, 0.78, 2.34, 0.34, LEAF_C)):
        c = op(dx, dy, z)
        bm_blob(k[sw], rnd, c, r, squash=(1.15, 1.15, 0.62), jitter=0.17, sub=2)
        for i in range(4):
            a = rnd.uniform(0, 6.283)
            d = Vector((math.cos(a), math.sin(a), 0.25))
            bm_sprig(k[LEAF_C if sw != LEAF_C else LEAF_A], rnd, c + Vector((d.x * r * 1.0, d.y * r * 1.0, r * 0.2)), d, n=3, size=0.22)
    k.emit("Crown", col, root, vary=0.07, seed=6)
    # ---- the wings: the oak's two great roots, each gripping a rune-carved menhir; channels of light from rune to trunk
    for a, sg, nm in WINGS:
        def run(pts, radii, n=6, claw=2, reach=0.2):
            cp, rad, rings = bm_root(k[ROOT], [rp(a, r, sg * off, z) for r, off, z in pts], radii, n=n, sub=3, squash=1.12)
            if claw:
                bm_claw(k[ROOT], cp[-1], cp[-1] - cp[-2], rad[-1], rnd, toes=claw, reach=reach, T=T, n=4)
            return cp, rad
        cp, rad = run([(0.42, 0.0, 0.5), (0.8, 0.0, 0.37), (1.2, -0.06, 0.25), (1.6, -0.22, 0.18), (1.95, -0.39, 0.16), (2.3, -0.4, 0.1), (2.52, -0.18, 0.05)],
                      [0.27, 0.24, 0.2, 0.17, 0.14, 0.11, 0.08], n=7, claw=3, reach=0.22)
        cb, rb = run([(0.9, 0.1, 0.3), (1.3, 0.34, 0.2), (1.75, 0.46, 0.18), (2.15, 0.4, 0.14), (2.42, 0.2, 0.08)], [0.17, 0.155, 0.13, 0.11, 0.09])
        for i in (4, 8):
            bm_blob(k[MOSS], rnd, cb[i] + Vector((0, 0, rb[i] * 0.7)), rb[i] * 1.1, squash=(1.25, 1.25, 0.4), jitter=0.2)
        run([(1.5, 0.1, 0.22), (1.78, 0.14, 0.3), (1.94, 0.16, 0.62), (2.0, 0.14, 0.98)], [0.11, 0.1, 0.08, 0.0], claw=0)
        base = rp(a, 2.12, 0.0)
        face = bm_menhir(k, rnd, (base.x, base.y, T), 1.5 if sg > 0 else 1.38, w=0.62, d=0.36, yaw=180 + sg * 17, lean=(-5, 4) if sg > 0 else (-3, -6))
        bm_flagstones(k["stone:0.15:0.9"], rnd, lambda x, y: (x - base.x) ** 2 + (y - base.y) ** 2 < 0.8 and (x - OAK.x) ** 2 + (y - OAK.y) ** 2 > 1.0
                      and in_footprint(CELLS, x, y, 0.22), (base.x - 0.95, base.y - 0.95, base.x + 0.95, base.y + 0.95), T - 0.008, size=0.3, gap=0.035, h=0.04, keep=0.86)
        rune = "bolt" if sg > 0 else "arrow"
        bm_rune(k[SG], rune, face, 0.5, size=0.56, w=0.06)
        RUNE_AT[nm] = (face, rune)
        top, tipb = face(0.0, 1.3 if sg > 0 else 1.2)[0] + Vector((0, 0.1, 0.12)), op(sg * 1.31, -0.71, 2.07)
        line = [tipb.lerp(top, i / 8.0) + Vector((0, 0, -0.2 * math.sin(math.pi * i / 8.0))) for i in range(9)]
        bm_tube(k["sand:0.3:0.7"], line, 0.013, n=4)
        for i in (1, 3, 5, 7):
            d = (line[i + 1] - line[i - 1]).normalized()
            for side in (1, -1):
                o = Vector((0, 0.005 * side, 0))
                vs = [k["team!:0.1:0.65"].verts.new(q + o) for q in (line[i] - d * 0.085, line[i] + d * 0.085, line[i] + Vector((0, 0, -0.27)))]
                k["team!:0.1:0.65"].faces.new(vs if (side > 0) == (d.x > 0) else list(reversed(vs)))
        # the channel: up the menhir's foot from the root lying before it, along the root's back, up the lobe to the crack
        im = min(range(len(cp)), key=lambda i: (cp[i] - Vector((base.x, base.y, cp[i].z))).length)
        back = [cp[i] + Vector((0, 0, rad[i] - 0.004)) for i in range(len(cp)) if i <= im and (Vector((cp[i].x - OAK.x, cp[i].y - OAK.y, 0))).length > 0.74]
        foot = [face(0.0, v)[0] + face(0.0, v)[1] * 0.022 for v in (0.48, 0.22)]
        CHAN[nm] = CHAN[nm] + back + [foot[1], foot[0]]
        bm_tube(k[SG], CHAN[nm], [0.014] + [0.03] * (len(CHAN[nm]) - 1), n=4)
        CHAN[nm].reverse()                                                         # (sparks run from the rune to the trunk)
        for i, (r, off, s) in enumerate(((1.7, 0.72, 0.24), (2.5, -0.62, 0.22), (1.25, -0.5, 0.26), (2.62, 0.46, 0.2))):
            q = rp(a, r, sg * off, -0.012)
            if in_footprint(CELLS, q.x, q.y, 0.3):
                bm_blob(k[MOSS if i % 2 else "teal:0.3:0.8"], rnd, tuple(q), s, squash=(1.2, 1.0, 0.16), jitter=0.2)
        for (r, off, L) in ((2.3, 0.72, 0.32), (1.6, -0.78, 0.3), (2.74, -0.1, 0.28)):
            q = rp(a, r, sg * off)
            if in_footprint(CELLS, q.x, q.y, 0.3):
                bm_fern(k["grass:0.1:0.75"], rnd, q, n=5, length=L, rise=L * 0.7, w=0.1)
    for a, r, off in ((90, 0.98, 0.0), (45, 0.95, 0.0), (135, 0.95, 0.0)):       # the mound's own short roots, to the front
        cp, rad, rings = bm_root(k[ROOT], [rp(a, 0.4, off, 0.42), rp(a, 0.72, off + 0.06, 0.26), rp(a, r, off, 0.05)], [0.16, 0.12, 0.08], n=6, sub=3, squash=1.12)
        bm_claw(k[ROOT], cp[-1], cp[-1] - cp[-2], rad[-1], rnd, toes=2, reach=0.13, T=T, n=4)
    k.emit("Roots", col, root, vary=0.06, seed=8)
    # ---- back right: the druid's stone, a cloth in the team's color laid on it. Back left: the bough the lightning tore off
    yaw = math.degrees(math.atan2(-(OAK.x - CREW.x), OAK.y - CREW.y))
    bm_stone(k["stone:0.1:0.85"], rnd, (CREW.x, CREW.y, T - 0.02), (0.84, 0.7, 0.33), yaw=yaw + 8, n=0, jit=0.1)
    bm_stone(k["stone:0.15:0.9"], rnd, (CREW.x + 0.05, CREW.y - 0.42, T - 0.02), (0.44, 0.3, 0.16), yaw=yaw - 10, n=0, jit=0.12)
    k.emit("Stone", col, root, vary=0.08, seed=10)
    bm_box(k["team!:0.15:0.6"], (0.5, 0.56, 0.024), (CREW.x, CREW.y, T + 0.32), (0, 0, yaw))
    for sy in (-1, 1):
        bm_box(k["gold:0.15:0.6"], (0.52, 0.05, 0.028), (CREW.x - math.sin(math.radians(yaw)) * sy * 0.25, CREW.y + math.cos(math.radians(yaw)) * sy * 0.25, T + 0.321),
               (0, 0, yaw))
    k.emit("Rug", col, root)
    cp, rad, rings = bm_root(k[BARK], [(-0.6, -0.06, T + 0.4), (-0.86, -0.38, T + 0.24), (-1.15, -0.72, T + 0.17), (-1.44, -1.0, T + 0.13)], [0.2, 0.18, 0.15, 0.1],
                             n=7, sub=3)
    bm_plates(k[BARK_PLATE], rings, rnd, th=(0.02, 0.04), rows=(1.2, 2.2), gap=0.25, side=0.14, keep=0.7, point=0.28, start=1.5)
    d = (cp[0] - cp[1]).normalized()
    bm_cyl(k[CHAR], 0.21, 0.2, 0.16, tuple(cp[0] - d * 0.02), rot=tuple(math.degrees(v) for v in d.to_track_quat("Z", "Y").to_euler()), seg=7)
    for i in range(6):
        q = cp[0] + Vector((rnd.uniform(-0.11, 0.11), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.1, 0.12)))
        bm_thorn(k["cream:0.15:0.6"], q, d + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0.0, 0.4))), rnd.uniform(0.14, 0.3), 0.05, n=3)
    bm_root(k[BARK], [cp[5], cp[5] + Vector((-0.3, 0.1, 0.25)), cp[5] + Vector((-0.5, 0.26, 0.34))], [0.07, 0.05, 0.0], n=4)
    bm_root(k[BARK], [cp[7], cp[7] + Vector((0.2, -0.12, 0.26)), cp[7] + Vector((0.3, -0.3, 0.42))], [0.06, 0.045, 0.0], n=4)
    for (i, h, r) in ((3, 0.16, 0.1), (6, 0.2, 0.13), (8, 0.13, 0.08)):
        bm_mushroom(k, rnd, cp[i] + Vector((0.03, 0.02, rad[i] * 0.8)), h, r, cap="orange:0.05:0.7", spots="cream:0.0:0.4" if r > 0.12 else None, n=6)
    k.emit("Fallen", col, root, vary=0.06, seed=12)
    if os.environ.get("TR_STANDIN"):
        bm_standin(k, CREW, yaw)
        k.emit("Standin", col, root)
    crew = empty("Crew", col, root, tuple(CREW), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(yaw))
    empty("Head", col, root, tuple(CRYS), 0.5, "SINGLE_ARROW")
    return root, BOUGH


# one quarter of the cloud ring (bearing, how far out, height, size); the ring is four of these, so a quarter turn
# brings it back onto itself (the idle clip turns it just that far)
PUFFS = [(10, 1.0, 0.0, 0.42), (55, 1.05, -0.02, 0.4), (33, 0.96, 0.17, 0.3), (78, 1.02, 0.16, 0.26), (20, 1.3, 0.0, 0.2), (68, 1.3, 0.03, 0.22), (44, 0.72, 0.02, 0.17)]


def build_head(BOUGH):
    col = collection("Storm")
    root = bpy.data.objects["Storm"]
    head = bpy.data.objects["Head"]
    rnd = random.Random(17)
    tip = CRYS + Vector((0, 0, 0.5))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "crystal": (tuple(CRYS), tuple(CRYS + Vector((0, 0, 0.3))), "root"),
             "cloud": (tuple(CLOUD), tuple(CLOUD + Vector((0, 0, 0.3))), "root"),
             "arc": (tuple(tip), tuple(tip + Vector((0, 0, 0.2))), "cloud")}
    sparks = []
    for i in range(4):
        a = math.radians(30 + 90 * i)
        p = CLOUD + Vector((math.cos(a) * 0.9, math.sin(a) * 0.9, -0.1))
        sparks.append((p, a))
        bones["bolt.%d" % i] = (tuple(p), tuple(p + Vector((0, 0, -0.2))), "cloud")
    for nm in ("L", "R"):
        face, rune = RUNE_AT[nm]
        c = face(0.0, 0.78)[0]
        bones["rune." + nm] = (tuple(c), tuple(c + Vector((0, 0, 0.2))), "root")
        bones["bead." + nm] = (tuple(CHAN[nm][0]), tuple(CHAN[nm][0] + Vector((0, 0, 0.15))), "root")
        flag_bones(bones, "ban." + nm, tuple(BOUGH[nm][6] + Vector((-0.26, 0, -0.2))), (0, 0, -1), 0.98, segs=3)
    rig = make_rig(col, root, bones)
    k = Kit()
    gem(k, CRYS, 0.21, 0.5, 0.38)
    k.emit("Crystal", col, rig=rig, bone="crystal")
    for q in range(4):
        for a, r, z, s in PUFFS:
            an = math.radians(a + 90 * q)
            c = CLOUD + Vector((math.cos(an) * r * CLOUD_R, math.sin(an) * r * CLOUD_R, z))
            bm_blob(k["stone2:0.35:1.0" if z < 0.1 else "stone:0.0:0.6"], random.Random(40 + PUFFS.index((a, r, z, s))), c, s, squash=(1.0, 1.0, 0.66), jitter=0.07, sub=2)
    k.emit("Cloud", col, rig=rig, bone="cloud")
    for i, (p, a) in enumerate(sparks):                 # forks flickering under the ring
        inw = Vector((-math.cos(a), -math.sin(a), 0))
        zigzag(k[SGB], p, p + inw * 0.16 + Vector((0, 0, -0.5)), random.Random(5), n=3, jit=0.09, w=0.05, w1=0.015)
        k.emit("Bolt%d" % i, col, rig=rig, bone="bolt.%d" % i)
    for i in range(4):                                  # the discharge: four forks from the ring into the crystal's point
        a = math.radians(75 + 90 * i)
        zigzag(k[SGB], tip + Vector((0, 0, 0.02)), CLOUD + Vector((math.cos(a) * 0.74, math.sin(a) * 0.74, -0.06)), random.Random(9), n=4, jit=0.13, w=0.03, w1=0.07)
    k.emit("Arc", col, rig=rig, bone="arc")
    for nm in ("L", "R"):
        face, rune = RUNE_AT[nm]
        bm_rune(k[SGB], rune, face, 0.47, size=0.62, w=0.095, th=0.035)
        k.emit("Rune" + nm, col, rig=rig, bone="rune." + nm)
        bm_blob(k[SGB], rnd, CHAN[nm][0], 0.075, jitter=0.1)
        k.emit("Bead" + nm, col, rig=rig, bone="bead." + nm)
        flag_part("Banner" + nm, col, rig, "ban." + nm, tuple(BOUGH[nm][6] + Vector((-0.26, 0, -0.2))), (0, 0, -1), 0.98, 0.52, segs=3, tail="swallow", hang=(1, 0, 0))
    empty("Muzzle", col, head, (0, 0, 0.5), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def along(path, u):
    """The point u (0..1) of the way along a line of points."""
    lens = [(b - a).length for a, b in zip(path, path[1:])]
    s = min(max(u, 0.0), 1.0) * sum(lens)
    for (a, b), L in zip(zip(path, path[1:]), lens):
        if s <= L:
            return a.lerp(b, s / max(L, 1e-9))
        s -= L
    return path[-1].copy()


def pose(rig, t=0.0, turn=0.0, jolt=0.0, flare=0.0, arc=0.0, bolts=(0, 0, 0, 0), rune=0.0, gust=0.0, bead=1.0):
    """t: the idle's time (0..1); turn: the cloud's extra turn (degrees); jolt, flare, arc, rune, gust: the shot's."""
    pb = rig.pose.bones
    rest_pose(rig)
    ph = 2 * math.pi * t
    c = pb["crystal"]
    c.rotation_quaternion = arm_space_quat(c, (0, 0, 1), 60.0 * t)             # (a sixth of a turn brings a six-sided gem back onto itself)
    c.location = arm_space_loc(c, (0, 0, 0.045 * math.sin(2 * ph) + 0.1 * flare))
    c.scale = (1.0 + 0.05 * math.sin(4 * ph) + 0.6 * flare,) * 3
    cl = pb["cloud"]
    cl.rotation_quaternion = arm_space_quat(cl, (0, 0, 1), 90.0 * t + turn)
    cl.scale = (1.0 + 0.1 * jolt, 1.0 + 0.16 * jolt, 1.0 + 0.1 * jolt)        # (the bone's own Y is up)
    cl.location = arm_space_loc(cl, (0, 0, 0.02 * math.sin(ph) - 0.08 * jolt))
    pb["arc"].scale = (max(arc, 0.02),) * 3
    for i in range(4):
        pb["bolt.%d" % i].scale = (max(bolts[i], 0.02),) * 3
    for i, nm in enumerate(("L", "R")):
        pb["rune." + nm].scale = (max(rune, 0.02),) * 3
        u = (t + 0.5 * i) % 1.0                                                  # a spark runs from the rune to the split
        b = pb["bead." + nm]
        b.location = arm_space_loc(b, tuple(along(CHAN[nm], u) - CHAN[nm][0]))
        b.scale = (max(0.02, bead * min(1.0, 6.0 * u, 6.0 * (1.0 - u)) * (1.0 + 0.25 * math.sin(8 * ph + i))),) * 3
        wave_flag(rig, "ban." + nm, 2.0 * t + 0.3 * i, amp=0.45 + 1.3 * gust, segs=3, axis=(1, 0, 0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(IDLE_LEN + 1):
        bolts = [1.0 if (f - 9 - 23 * i) in (0, 1, 3, 4) else 0.0 for i in range(4)]         # each fork flickers twice, in turn
        pose(rig, t=f / IDLE_LEN, bolts=bolts)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the cloud discharges into the crystal on frames 1-5 and the crystal flares; the cloud jolts and swings a few
        # degrees on; the runes flash; then everything settles
        flare = smooth(f / 2.0) * (1.0 - smooth((f - 3) / 7.0)) - 0.12 * math.sin(math.pi * min(max((f - 9) / 6.0, 0.0), 1.0))
        jolt = smooth(f / 2.0) * (1.0 - smooth((f - 2) / 6.0)) - 0.25 * math.sin(math.pi * min(max((f - 8) / 6.0, 0.0), 1.0))
        turn = 16.0 * smooth(f / 4.0) * (1.0 - smooth((f - 5) / 11.0))
        arc = (0.0, 0.7, 1.0, 0.55, 1.0, 0.8, 0.3)[f] if f < 7 else 0.0
        on = 1.0 if f in (1, 2, 4, 5, 8) else 0.0
        pose(rig, turn=turn, jolt=jolt, flare=flare, arc=arc, bolts=(on, on, on, on), rune=1.12 * smooth(f / 1.5) * (1.0 - smooth((f - 6) / 6.0)),
             gust=smooth(f / 3.0) * (1.0 - smooth((f - 5) / 12.0)), bead=1.0 + 1.2 * flare)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.5), "dist": 11.5, "yaw": 150, "pitch": 20, "anim_target": (0, 0.2, 1.7), "anim_dist": 8.5,
           "frames": [("idle", 0), ("idle", 34), ("fire", 2), ("fire", 4), ("fire", 10)],
           "extra": [{"yaw": 0, "pitch": 22, "dist": 5.0, "target": (0, 0.3, 1.5)},
                     {"yaw": 15, "pitch": 26, "dist": 4.6, "target": (1.6, -0.45, 0.7)},
                     {"yaw": 345, "pitch": 26, "dist": 4.6, "target": (-1.6, -0.45, 0.7)},
                     {"yaw": 180, "pitch": 12, "dist": 6.0, "target": (0, 0.6, 1.7)}]}


def build_all():
    root, bough = build_base()
    build_head(bough)
    build_anims()
    tri_report(collection("Storm"))
