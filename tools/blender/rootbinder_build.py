"""Builds the Rootbinder Shrine (footprint "fan5": [0,0] middle, [-1,0] front-left, [0,-1] front, [1,-1] front-right,
[1,0] back-right), a Verdant tower: slow orbs that root whatever they hit.

    python tools/blender/build.py rootbinder --out <preview dir>

One shrine. In the middle a huge hollow stump, its rim broken low at the back and high at the front, a well of green
spirit light inside it; above it the heart-seed, cradled in five arching roots that rise out of the hollow (the Head,
as before: the rig hangs under it, the Muzzle is the seed). From the stump's buttresses five thick roots run out over
the ground, one to each of five carved standing stones (one on every outer hex, the fifth a stump of a stone by the
steps), and wind up round them, binding them; thinner roots link stone to stone round the ring. Up the back of the
stump run the altar steps under a cloth in the team's color, with candles and offerings; every stone wears a band of
the same cloth. Clips: idle (the seed bobs, turns and pulses, wisps circle it, the cradle breathes), fire (the cradle
clenches on the seed and it flares).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open(os.path.join(REPO, "tools", "blender", "greatwood_common.py"), encoding="utf-8").read())

TID = "rootbinder"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
C0 = hex_to_world(0, 0, MID)
TOP = 0.34
T = TOP + 0.05                  # the turf's top (plinth(turf=True))
S = Vector((C0.x, C0.y + 0.1, 0.0))         # the stump's axis
STUMP_TOP = 1.05                # the Head's height above the turf (as the old script had it)
SEED_Z = 0.72                   # the seed's middle, above the Head
GLOW = "glow:%s,%s,%s,0.85" % SPIRIT
POOL = "glow:0.22,0.7,0.32,0.55"
# the standing stones: (bearing from the middle hex, how far out, height, rune, the root winds up it this way round)
STONES = [(150, 1.95, 1.55, "root", 1), (90, 2.0, 1.78, "tree", -1), (30, 1.95, 1.5, "coil", 1), (330, 1.88, 1.42, "eye", -1), (225, 0.72, 0.66, "home", 1)]
# the cradle's roots, in the Head's space: (how far out, height)
CRADLE = [(0.22, -0.5), (0.28, -0.1), (0.36, 0.3), (0.62, 0.68), (0.52, 1.06), (0.22, 1.34), (0.06, 1.4)]


def rp(a, r, off=0.0, z=0.0, c=None):
    """A point r out from the stump (or c) at bearing a (degrees), `off` to the left of that line, z above the turf."""
    c = S if c is None else c
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return Vector((c.x + ca * r - sa * off, c.y + sa * r + ca * off, T + z))


def stone_frame(i):
    """Where stone i stands: (base, height, yaw, lean), its carved face turned in to the stump."""
    a, r, h, rune, hand = STONES[i]
    base = rp(a, r, 0.0, 0.0, C0)
    base.z = T
    return base, h, a + 90.0, (-(9.0 + 3.0 * (i % 3)), 5.0 * hand * (1 if i % 2 else -1))


def seed(kit, c, up=0.44, down=0.33, r=0.3, n=6):
    """The heart-seed: an almond of green light, a second one turned half a facet inside it to show its facets."""
    c = Vector(c)
    x, y = Vector((1, 0, 0)), Vector((0, 1, 0))
    for sw, ph, kr in (("glow:0.2,0.75,0.3,0.7", 0.0, 1.0), ("glow:0.6,1.0,0.55,0.95", 0.5, 0.93)):
        rows = [oval(c + Vector((0, 0, z)), x, y, rr * kr, rr * kr, n, phase=ph) for z, rr in ((-down * 0.55, r * 0.7), (-down * 0.1, r), (up * 0.45, r * 0.8))]
        bm_loft(kit[sw], rows, tip0=c + Vector((0, 0, -down * kr)), tip1=c + Vector((0, 0, up * kr)))


def build_base():
    col = collection("Rootbinder")
    root = empty("Rootbinder", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(44)
    k = Kit()
    # ---- the stump: a hollow bole, its buttresses toward the stones, its rim broken low at the back and high at the front
    lobes = {150: 0.4, 90: 0.45, 30: 0.4, 330: 0.4, 210: 0.0, 270: -0.3, 0: -0.1, 60: -0.12, 120: -0.12, 180: -0.1, 240: -0.22, 300: -0.22}
    angles = list(range(0, 360, 30))
    stump = Trunk((S.x, S.y, T - 0.05), [(0.0, 0.8, 0.74, 1.0), (0.25, 0.68, 0.62, 0.6), (0.55, 0.62, 0.57, 0.25), (0.78, 0.6, 0.56, 0.05), (0.9, 0.62, 0.57, 0.0)],
                  angles, lobes, rnd, 0.02)
    for i, a in enumerate(angles):
        stump.rings[-1][i].z += 0.25 * (1.0 + math.sin(math.radians(a))) + rnd.uniform(-0.03, 0.08)
    stump.loft(k[BARK], cap1=False)
    bm_plates(k[BARK_PLATE], stump.rings, rnd, th=(0.03, 0.05), rows=(0.8, 1.4), gap=0.14, side=0.12, point=0.28, end=3.6)
    top = stump.rings[-1]
    mid = sum(top, Vector()) / len(top)
    bm = k["sand:0.15:0.6"]                                   # the broken rim
    outer = [bm.verts.new(p) for p in top]
    inner = [bm.verts.new(mid.lerp(p, 0.7) + Vector((0, 0, -0.02))) for p in top]
    for i in range(len(top)):
        j = (i + 1) % len(top)
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    bm = k["wood_dark:0.55:1.0"]                              # the hollow's wall, down to the floor
    inner2 = [bm.verts.new(mid.lerp(p, 0.7) + Vector((0, 0, -0.02))) for p in top]
    floor = [bm.verts.new(Vector((mid.x + (p.x - mid.x) * 0.6, mid.y + (p.y - mid.y) * 0.6, T + 0.5))) for p in top]
    for i in range(len(top)):
        j = (i + 1) % len(top)
        bm.faces.new((inner2[i], inner2[j], floor[j], floor[i]))
    bm = k[POOL]                                              # the well of light
    pool = [bm.verts.new(Vector((mid.x + (p.x - mid.x) * 0.61, mid.y + (p.y - mid.y) * 0.61, T + 0.5))) for p in top]
    bm.faces.new(pool)
    for i in range(7):
        a = rnd.uniform(0, 6.283)
        q = Vector((mid.x + math.cos(a) * rnd.uniform(0.05, 0.3), mid.y + math.sin(a) * rnd.uniform(0.05, 0.3), T + 0.49))
        bm_crystal(k[GLOW], q, q + Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), rnd.uniform(0.12, 0.26))), 0.035, n=4, shoulder=0.3)
    for a in (60, 100, 130):                                  # splinters standing up from the high side of the rim
        p = stump.at(a, 0.88, -0.03)
        p.z = T - 0.05 + 0.9 + 0.25 * (1.0 + math.sin(math.radians(a))) - 0.04
        bm_thorn(k["sand:0.1:0.5"], p, Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 1.0)), rnd.uniform(0.14, 0.26), 0.05, n=3)
    for a, z, r in ((20, 0.36, 0.14), (200, 0.5, 0.12), (300, 0.3, 0.1)):
        bm_shelf(k["sand:0.1:0.7"], stump.at(a, z, -0.01), stump.out(a), r=r, th=0.045)
    for a, z, r in ((120, 0.66, 0.16), (330, 0.55, 0.13)):
        bm_blob(k[MOSS], rnd, stump.at(a, z, 0.0), r, squash=(1.0, 1.0, 0.6), jitter=0.2)
    k.emit("Stump", col, root, vary=0.05, seed=4)
    # ---- the stones: each tilted, moss-capped, a glowing rune on the face it turns to the stump, a cloth band round it
    frames = []
    for i, (a, r, h, rune, hand) in enumerate(STONES):
        base, h, yaw, lean = stone_frame(i)
        frames.append((base, h, yaw, lean))
        w, d = (0.6, 0.36) if h > 1.0 else (0.44, 0.3)
        face = bm_menhir(k, rnd, base, h, w=w, d=d, yaw=yaw, lean=lean)
        bm_rune(k[GLOW], rune, face, h * 0.3, size=min(0.5, h * 0.36), w=0.05)
        if i == 3:                                            # (the back-right stone turns its back to the player: a rune there too)
            def back(u, v, face=face, h=h, w=w, d=d):
                p, o, up = face(-u, v)
                return p - o * (2.0 * menhir_half(v, h, w, d)[1]), -o, up
            bm_rune(k[GLOW], "eye", back, h * 0.3, size=0.5, w=0.05)
        bm_menhir_band(k["team!:0.1:0.6"], base, h, h * 0.62, h * 0.72, w=w, d=d, yaw=yaw, lean=lean, grow=0.03)
        bm_menhir_band(k["gold:0.15:0.6"], base, h, h * 0.615, h * 0.635, w=w, d=d, yaw=yaw, lean=lean, grow=0.038)
        for j in range(5):                                    # a kerb of small stones at its foot
            aa = math.radians(yaw + 90 + 72 * j + rnd.uniform(-15, 15))
            q = base + Vector((math.cos(aa) * (w * 0.5 + 0.2), math.sin(aa) * (w * 0.5 + 0.2), 0))
            if in_footprint(CELLS, q.x, q.y, 0.24):
                bm_stone(k["stone:0.2:0.9"], rnd, (q.x, q.y, T - 0.02), (0.2, 0.15, 0.12), yaw=rnd.uniform(0, 180), n=8, jit=0.2)
    k.emit("Stones", col, root, vary=0.07, seed=5)
    # ---- the binding roots: from each buttress out over the ground to its stone and winding up round it
    for i, (a, r, h, rune, hand) in enumerate(STONES):
        base, h, yaw, lean = frames[i]
        w, d = (0.6, 0.36) if h > 1.0 else (0.44, 0.3)
        to = Vector((base.x - S.x, base.y - S.y, 0))
        b, D = math.degrees(math.atan2(to.y, to.x)), to.length
        wrap = menhir_wrap(base, h, w=w, d=d, yaw=yaw, lean=lean, a0=60.0 * hand, a1=325.0 * hand, z0=0.12, z1=h * 0.72, gap=0.1)
        if D > 1.5:
            ctrl = [rp(b, 0.4, 0.0, 0.5), rp(b, 0.8, hand * 0.05, 0.32), rp(b, 1.2, hand * 0.14, 0.22), rp(b, D - 0.62, hand * 0.24, 0.18)]
            radii = [0.26, 0.23, 0.2, 0.17, 0.13, 0.1, 0.07, 0.0]
        else:
            ctrl = [rp(b, 0.36, 0.0, 0.42), rp(b, 0.52, hand * 0.14, 0.26)]
            radii = [0.18, 0.15, 0.11, 0.08, 0.0]
        cp, rad, rings = bm_root(k[ROOT], ctrl + wrap, radii, n=7, sub=3, squash=1.1)
        if D > 1.5:                                           # side rootlets off it, clawing across the hex
            for j, (s, side) in enumerate(((0.62, 1), (1.05, -1))):
                p0 = rp(b, s, hand * side * 0.08, 0.26)
                p1 = rp(b, s + 0.25, hand * side * 0.5, 0.14)
                p2 = rp(b, s + 0.42, hand * side * 0.85, 0.05)
                if in_footprint(CELLS, p2.x, p2.y, 0.25):
                    cq, rq, _ = bm_root(k[ROOT], [p0, p1, p2], [0.1, 0.08, 0.06], n=5, sub=3, squash=1.1)
                    bm_claw(k[ROOT], cq[-1], cq[-1] - cq[-2], rq[-1], rnd, toes=2, reach=0.16, T=T, n=4)
            for j in (4, 8):
                bm_blob(k[MOSS], rnd, cp[j] + Vector((0, 0, rad[j] * 0.75)), rad[j] * 1.05, squash=(1.25, 1.25, 0.4), jitter=0.2)
    # thinner roots linking stone to stone round the ring, moss along them
    for i in range(3):
        (b0, h0, _, _), (b1, h1, _, _) = frames[i], frames[i + 1]
        d = (b1 - b0).normalized()
        out = (((b0 + b1) * 0.5) - Vector((C0.x, C0.y, 0))).normalized()
        ctrl = [b0 + d * 0.3 + Vector((0, 0, 0.14)), (b0 + b1) * 0.5 + out * 0.22 + Vector((0, 0, 0.1)), b1 - d * 0.3 + Vector((0, 0, 0.14))]
        cp, rad, _ = bm_root(k[ROOT], ctrl, [0.1, 0.09, 0.08], n=5, sub=3, squash=1.1)
        bm_blob(k["teal:0.3:0.8"], rnd, cp[3] + Vector((0, 0, 0.02)), 0.3, squash=(1.3, 1.1, 0.16), jitter=0.2)
    k.emit("Roots", col, root, vary=0.06, seed=6)
    # ---- the altar steps up the back of the stump, the cloth laid down them, candles and offerings
    for r, wdt, dep, z in ((0.78, 0.9, 0.26, 0.13), (0.58, 0.74, 0.24, 0.27)):
        p = rp(270, r, 0.0, 0.0, C0)
        bm_stone(k["stone2:0.1:0.85"], rnd, (p.x, p.y, T - 0.02), (wdt, dep, z), yaw=rnd.uniform(-3, 3), n=0, jit=0.05)
    k.emit("Steps", col, root, vary=0.06, seed=7)
    path = [rp(270, r, 0.0, z, C0) for r, z in ((0.26, 0.88), (0.4, 0.9), (0.47, 0.72), (0.47, 0.5), (0.48, 0.29), (0.66, 0.29), (0.7, 0.16), (0.88, 0.15), (0.9, 0.04))]
    for sw, half, lift in (("team!:0.1:0.6", 0.17, 0.012), ("gold:0.15:0.6", 0.19, 0.0)):
        rows = []
        for i, p in enumerate(path):
            dd = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
            sd = Vector((1, 0, 0))
            nn = sd.cross(dd).normalized() if abs(dd.z) < 0.99 else Vector((0, 1, 0))
            if nn.z < 0:
                nn = -nn
            o = nn * lift
            rows.append([p - sd * half + o, p + sd * half + o, p + sd * half + nn * 0.016 + o, p - sd * half + nn * 0.016 + o])
        bm_loft(k[sw], rows)
    for (r, off, hh) in ((0.74, 0.38, 0.16), (0.76, -0.36, 0.12), (0.56, 0.34, 0.1), (0.58, -0.32, 0.14), (0.8, 0.46, 0.09)):
        bm_candle(k, rp(270, r, off, 0.13 if r > 0.68 else 0.27, C0), h=hh, r=0.034)
    for (r, off, z) in ((0.58, -0.26, 0.27), (0.76, 0.3, 0.13)):                 # bowls of berries
        p = rp(270, r, off, z, C0)
        bm_cyl(k["wood:0.3:0.8"], 0.07, 0.1, 0.07, (p.x, p.y, p.z + 0.035), seg=7)
        for j in range(5):
            aa = rnd.uniform(0, 6.283)
            bm_blob(k["red:0.2:0.7" if j % 2 else "orange:0.2:0.7"], rnd, p + Vector((math.cos(aa) * 0.045, math.sin(aa) * 0.045, 0.085)), 0.03, jitter=0.1)
    p = rp(270, 0.56, 0.18, 0.27, C0)                                            # a chalice
    bm_cyl(k["gold:0.1:0.5"], 0.055, 0.03, 0.03, (p.x, p.y, p.z + 0.015), seg=7)
    bm_cyl(k["gold:0.1:0.5"], 0.02, 0.02, 0.08, (p.x, p.y, p.z + 0.07), seg=5)
    bm_cyl(k["gold:0.1:0.5"], 0.03, 0.065, 0.08, (p.x, p.y, p.z + 0.15), seg=7)
    bm_cyl(k["glow:0.3,0.9,0.4,0.6"], 0.058, 0.058, 0.012, (p.x, p.y, p.z + 0.19), seg=7)
    k.emit("Altar", col, root)
    kk_import("props/Basket_Mushrooms", col, root, tuple(rp(270, 0.76, -0.2, 0.13, C0)), 200, 0.32, name="Prop_KK_0")
    kk_import("resources/Gold_Nuggets", col, root, tuple(rp(270, 0.78, 0.14, 0.13, C0)), 30, 0.3, name="Prop_KK_1")
    # ---- the forest floor over the outer hexes: moss, ferns, toadstools, fallen leaves
    for (a, r, off, s) in ((150, 1.4, 0.5, 0.36), (150, 2.3, -0.5, 0.3), (90, 1.5, -0.55, 0.34), (90, 2.4, 0.45, 0.3), (30, 1.45, -0.5, 0.36), (30, 2.3, 0.55, 0.3),
                           (330, 1.5, 0.5, 0.34), (330, 2.25, -0.5, 0.3), (120, 1.75, 0.0, 0.32), (60, 1.75, 0.0, 0.32), (0, 1.75, 0.0, 0.3), (210, 0.55, 0.3, 0.3),
                           (90, 2.6, 0.0, 0.3), (150, 2.65, 0.0, 0.28), (30, 2.65, 0.0, 0.28), (330, 2.6, 0.1, 0.28), (110, 1.3, 0.0, 0.26), (70, 1.3, 0.0, 0.26)):
        q = rp(a, r, off, -0.012, C0)
        if in_footprint(CELLS, q.x, q.y, 0.3):
            bm_blob(k[MOSS if (r + off) % 2 < 1 else "teal:0.3:0.8"], rnd, tuple(q), s, squash=(1.25, 1.0, 0.16), jitter=0.2)
    for (a, r, off, L) in ((150, 2.45, 0.4, 0.34), (90, 1.6, 0.6, 0.3), (90, 2.5, -0.4, 0.34), (30, 2.4, -0.42, 0.32), (330, 2.4, 0.4, 0.3), (330, 1.45, -0.6, 0.3),
                           (150, 1.5, -0.62, 0.3), (240, 0.8, 0.0, 0.26)):
        q = rp(a, r, off, 0.0, C0)
        if in_footprint(CELLS, q.x, q.y, 0.3):
            bm_fern(k["grass:0.1:0.75"], rnd, q, n=5, length=L, rise=L * 0.7, w=0.1)
    for i, (a, r, off, h, cr) in enumerate(((30, 1.6, 0.42, 0.3, 0.18), (30, 1.78, 0.56, 0.2, 0.12), (30, 1.5, 0.6, 0.14, 0.09), (150, 2.3, 0.1, 0.26, 0.16),
                                            (150, 2.45, -0.1, 0.16, 0.1), (330, 1.65, -0.42, 0.22, 0.14), (330, 1.8, -0.56, 0.13, 0.09))):
        q = rp(a, r, off, 0.0, C0)
        if in_footprint(CELLS, q.x, q.y, 0.28):
            bm_mushroom(k, rnd, q, h, cr, cap="orange:0.05:0.7", spots="cream:0.0:0.4" if cr > 0.13 else None, n=7 if cr > 0.13 else 6)
    for i in range(24):
        a, r = rnd.uniform(0, 360), rnd.uniform(1.1, 2.5)
        p = rp(a, r, 0, 0.012, C0)
        if in_footprint(CELLS, p.x, p.y, 0.25):
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
            bm_leaf(k["orange:0.1:0.7" if i % 3 else "gold:0.2:0.8"], p, p + d * 0.13 + Vector((0, 0, 0.01)), 0.08)
    k.emit("Floor", col, root, vary=0.08, seed=9)
    empty("Head", col, root, (S.x, S.y, T + STUMP_TOP), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Rootbinder")
    head = bpy.data.objects["Head"]
    rnd = random.Random(7)
    seedc = Vector((0, 0, SEED_Z))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "seed": (tuple(seedc), tuple(seedc + Vector((0, 0, 0.3))), "root"),
             "spin": (tuple(seedc), tuple(seedc + Vector((0, 0, 0.25))), "root")}
    shapes = []
    for i in range(5):
        a = math.radians(72 * i + 20)
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = spline_pts([d * r + Vector((0, 0, z)) for r, z in CRADLE], 3)
        shapes.append((d, pts))
        bones["cradle.%d.1" % i] = (tuple(pts[3]), tuple(pts[9]), "root")
        bones["cradle.%d.2" % i] = (tuple(pts[9]), tuple(pts[-1]), "cradle.%d.1" % i)
    wisps = [(0.0, 0.85, 0.5), (130.0, 1.0, 0.9), (250.0, 0.75, 1.15)]
    for i, (a, r, z) in enumerate(wisps):
        p = Vector((math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r, z))
        bones["wisp.%d" % i] = (tuple(p), tuple(p + Vector((0, 0, 0.12))), "spin")
    rig = make_rig(col, head, bones)
    k = Kit()
    seed(k, seedc)
    k.emit("Seed", col, rig=rig, bone="seed")
    for i, (d, pts) in enumerate(shapes):
        cp, rad, rings = bm_root(k[ROOT], pts, resample([0.17, 0.16, 0.14, 0.12, 0.09, 0.05, 0.0], len(pts)), n=6, sub=1, squash=1.0)
        for j in (6, 11):
            bm_sprig(k[LEAF_C], rnd, cp[j] + d * rad[j], d + Vector((0, 0, 0.5)), n=2, size=0.14)
        k.emit("Cradle%d" % i, col, rig=rig, bones=["cradle.%d.1" % i, "cradle.%d.2" % i])
    for i, (a, r, z) in enumerate(wisps):
        p = Vector((math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r, z))
        bm_blob(k["glow:0.65,1.0,0.6,0.9"], rnd, p, 0.055, jitter=0.1)
        t = Vector((-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))
        bm_tube(k["glow:0.45,0.9,0.45,0.7"], [p - t * 0.02, p - t * 0.14, p - t * 0.3 + Vector((0, 0, -0.03))], [0.04, 0.025, 0.0], n=4)
        k.emit("Wisp%d" % i, col, rig=rig, bone="wisp.%d" % i)
    empty("Muzzle", col, head, tuple(seedc), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def pose(rig, t=0.0, clench=0.0, flare=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    ph = 2 * math.pi * t
    s = pb["seed"]
    s.location = arm_space_loc(s, (0, 0, 0.05 * math.sin(2 * ph) + 0.08 * flare))
    s.rotation_quaternion = arm_space_quat(s, (0, 0, 1), 60.0 * t)             # (a sixth of a turn brings the six-sided seed back onto itself)
    s.scale = (1.0 + 0.05 * math.sin(4 * ph + 1.0) + 0.55 * flare,) * 3
    pb["spin"].rotation_quaternion = arm_space_quat(pb["spin"], (0, 0, 1), -360.0 * t)
    for i in range(3):
        w = pb["wisp.%d" % i]
        w.location = arm_space_loc(w, (0, 0, 0.06 * math.sin(3 * ph + i * 2.1)))
        w.scale = (1.0 + 0.5 * flare,) * 3
    for i in range(5):
        a = math.radians(72 * i + 20)
        axis = (-math.sin(a), math.cos(a), 0)      # a turn about this tips the root out (+) or in (-)
        breathe = 2.5 * math.sin(2 * ph + i * 1.3)
        b1, b2 = pb["cradle.%d.1" % i], pb["cradle.%d.2" % i]
        b1.rotation_quaternion = arm_space_quat(b1, axis, breathe - 9.0 * clench)
        b2.rotation_quaternion = arm_space_quat(b2, axis, breathe * 1.5 - 26.0 * clench)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the cradle opens a touch, snaps shut on the seed (frame 3) as it flares, then eases open again
        clench = smooth((f - 1) / 2.0) * (1.0 - smooth((f - 5) / 10.0)) - 0.35 * smooth(f / 1.0) * (1.0 - smooth((f - 1) / 1.5))
        flare = smooth((f - 1) / 2.0) * (1.0 - smooth((f - 4) / 9.0))
        pose(rig, clench=clench, flare=flare)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.0), "dist": 12.5, "yaw": 150, "pitch": 22, "anim_target": (S.x, S.y, 1.55), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 30), ("fire", 1), ("fire", 3), ("fire", 8)],
           "extra": [{"yaw": 0, "pitch": 30, "dist": 4.8, "target": (S.x, S.y - 0.2, 1.0)},
                     {"yaw": 250, "pitch": 26, "dist": 4.6, "target": (-1.9, 0.35, 0.8)},
                     {"yaw": 60, "pitch": 26, "dist": 4.6, "target": (1.3, -1.5, 0.8)},
                     {"yaw": 0, "pitch": 62, "dist": 10.0, "target": (0, 0, 0.5)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
    tri_report(collection("Rootbinder"))
