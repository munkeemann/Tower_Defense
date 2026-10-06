"""Builds the Tidecaller Spire (footprint "arrow3": [0,0] the front cell, [1,0] back-right, [-1,1] back-left), the Tide's
Tier IV aura: a great bell of ice and coral whose every toll freezes everything round it.

    python tools/blender/build.py tidecaller --out <preview dir>

One thing: a tall open belfry of four coral trunks on a rock rising from the sea. The sea fills all three cells inside
a rim of sea-worn stones, and three frozen waves are caught mid-crash round the rock, their crests white, with sea ice
floating beyond them. The trunks carry a coral ring and an ice yoke, and from the yoke hangs a huge bronze bell
collared in frost, banded in the team's color, icicles on its lip; the trunks close over it into a crown of glowing
ice. Team pennants fly from poles on the ring. It never turns: the Rig hangs on the root, the Head is at the bell.
idle: the bell stirs, the clapper swings a little, the crown pulses, pennants and kelp wave, drips fall, floes bob.
fire (every toll): the bell swings hard and the clapper strikes (frame 8), a ring of frost bursts out over the sea.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_spires_common.py"), encoding="utf-8").read())

TID = "tidecaller"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
R = hex_to_world(1, 0, MID)
L = hex_to_world(-1, 1, MID)
TOP = 0.34
T = TOP
WATER = T + 0.06
C = Vector((0.0, 0.3, 0.0))                 # the rock's (and belfry's) middle
ROCK_TOP = T + 0.9
RING_Z = T + 2.62                           # the coral ring and the ice yoke
P = T + 2.5                                 # the bell's pivot
APEX = T + 3.48                             # where the trunks meet
COL_A = (45, 135, 225, 315)
COL_STATIONS = [(0.88, T + 0.5, 0.21), (0.92, T + 1.25, 0.19), (0.86, T + 2.0, 0.17), (0.8, RING_Z, 0.15),
                (0.6, T + 3.05, 0.13), (0.32, T + 3.32, 0.105), (0.1, APEX, 0.085)]
RING_R = 0.8
GLOW_ICE = "glow:0.72,0.93,1.0,0.75"
DRIPS = [(0.36, -0.56), (-0.52, 0.45), (0.2, 0.62)]          # (angle round the ring (fraction), its icicle's offset) see below
FLOES = [((2.45, 0.55), 0.3), ((-2.4, 0.5), 0.34), ((2.6, -1.0), 0.26)]      # bobbing floes (centre, radius)


def col_point(a, z):
    """A point on trunk `a` (degrees) at height z, by interpolating its stations."""
    st = COL_STATIONS
    for (r0, z0, _), (r1, z1, _) in zip(st, st[1:]):
        if z0 <= z <= z1:
            r = r0 + (r1 - r0) * (z - z0) / (z1 - z0)
            return C + Vector((r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z))
    return C + Vector((st[-1][0] * math.cos(math.radians(a)), st[-1][0] * math.sin(math.radians(a)), z))


def build_base():
    col = collection("Tidecaller")
    root = empty("Tidecaller", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(7)
    k = Kit()
    # ---- the sea: a dark bed, the water over it, a rim of sea-worn stones round the footprint
    bed = [k["stone_dark:0.6:0.95"].verts.new((p.x, p.y, T + 0.012)) for p in outline(CELLS, 0.26)]
    bm_cap(k["stone_dark:0.6:0.95"], bed, grid=0.4)
    sea = [k["water"].verts.new((p.x, p.y, WATER)) for p in outline(CELLS, 0.35)]
    bm_cap(k["water"], sea, grid=0.3)
    k.emit("Sea", col, root)
    stones = [k["stone:0.15:0.85"], k["taupe:0.1:0.8"], k["stone2:0.1:0.8"]]
    cnt = [0]

    def next_stone():
        cnt[0] += 1
        return stones[cnt[0] % 3]
    rim_stones(next_stone, rnd, along_loop(outline(CELLS, 0.26), 0.33), T, r=(0.12, 0.19), squash=(1.3, 1.0, 0.6))
    k.emit("Rim", col, root, vary=0.08)
    # ---- the rock: a mound of boulders in the middle of the front cell, shouldering out onto the back cells
    rocks = [((0.0, 0.3), 1.05, 0.56, 16), ((0.6, -0.1), 0.72, 0.6, 14), ((-0.62, 0.0), 0.74, 0.56, 14), ((0.12, 0.98), 0.62, 0.58, 12),
             ((1.15, -0.3), 0.5, 0.5, 12), ((-1.2, -0.22), 0.52, 0.48, 12), ((0.75, 0.75), 0.4, 0.55, 10), ((-0.7, 0.8), 0.38, 0.5, 10),
             ((2.35, -0.95), 0.3, 0.5, 10), ((-2.45, -0.9), 0.28, 0.55, 10), ((0.45, 1.45), 0.24, 0.5, 9), ((-2.55, 0.1), 0.22, 0.5, 9)]
    for i, ((x, y), r, sz, n) in enumerate(rocks):
        bm_boulder(k["stone:0.12:0.9" if i % 2 else "taupe:0.1:0.85"], rnd, (x, y, T - 0.02), r, squash=(1.0, 0.92, sz), n=n, sink=0.18)
    k.emit("Rock", col, root, bevel=0.012, vary=0.08)
    # ---- frozen waves: two big ones crashing round the rock over the back cells, a smaller one at the front tip,
    #      and a low swell rolling in at the outer edge of each back cell
    waves = [wave_arc(C, 1.5, 1.35, 10, -52, n=9, hmax=1.08), wave_arc(C, 1.5, 1.35, 170, 232, n=9, hmax=0.98),
             wave_arc(C, 1.35, 1.25, 128, 52, n=8, hmax=0.72),
             (((2.3, 0.25), (2.5, -0.35), (2.2, -0.95)), (0.2, 0.42, 0.2), ((-1, 0.1), (-1, 0), (-0.8, 0.4))),
             (((-2.25, 0.3), (-2.5, -0.3), (-2.15, -0.95)), (0.18, 0.4, 0.22), ((1, 0.1), (1, 0), (0.8, 0.4)))]
    for path, hs, outs in waves:
        if len(path) == 3:                    # the swells: a smooth 5-station path through the three points
            p0, p1, p2 = (Vector(p) for p in path)
            path = [p0, (p0 + p1) * 0.5, p1, (p1 + p2) * 0.5, p2]
            hs = [hs[0], (hs[0] + hs[1]) * 0.6, hs[1], (hs[1] + hs[2]) * 0.6, hs[2]]
            o0, o1, o2 = (Vector(o) for o in outs)
            outs = [o0, (o0 + o1) * 0.5, o1, (o1 + o2) * 0.5, o2]
        bm_wave(k["sky:0.0:0.3"], path, hs, outs, WATER - 0.02, width=1.0)
    wv = k.emit("Waves", col, root)[0]
    paint_faces(wv, "blue", lambda c, n: n.z < -0.12 and c.z > T + 0.25, lo=0.3, hi=0.6)          # the hollow under the curl
    paint_faces(wv, "white", lambda c, n: n.z > 0.4 and c.z > T + 0.45, lo=0.0, hi=0.25)         # the crests
    for path, hs, outs in waves[:3]:         # spray frozen off the lips: a few white drops flung ahead of the curl
        m = len(path) // 2
        for i in (m - 1, m, m + 1):
            p, h, o = Vector((path[i][0], path[i][1], WATER)), hs[i], Vector((outs[i][0], outs[i][1], 0))
            bm_blob(k["white:0.0:0.3"], rnd, p + o * (0.68 * h) + Vector((0, 0, 0.5 * h)), 0.06 * h, jitter=0.2)
            if i == m:
                bm_blob(k["white:0.0:0.3"], rnd, p + o * (0.6 * h) + Vector((0, 0, 0.88 * h)), 0.05 * h, jitter=0.2)
    k.emit("Spray", col, root)
    # sea ice: still floes (the bobbing ones are built on the rig)
    for (x, y), r in (((2.1, 0.5), 0.24), ((-2.75, -0.45), 0.2), ((-0.95, 1.5), 0.2), ((1.05, 1.42), 0.17)):
        bm_floe(k["sky:0.0:0.3" if (x + y) > 0 else "white:0.0:0.3"], rnd, (x, y, 0), r, WATER + 0.035)
    k.emit("Floes", col, root, bevel=0.01, vary=0.06)
    # ---- life on the rock: coral tufts, tube sponges, barnacles, a scallop, starfish
    for (x, y, z, hh, sw) in ((0.78, 0.0, T + 0.62, 0.42, "orange:0.1:0.6"), (-0.8, 0.05, T + 0.6, 0.4, "salmon:0.1:0.7"),
                              (0.2, 1.1, T + 0.72, 0.36, "salmon:0.1:0.7"), (-0.3, -0.42, T + 0.55, 0.38, "orange:0.1:0.6"),
                              (1.3, -0.4, T + 0.45, 0.34, "salmon:0.1:0.7"), (-1.35, -0.3, T + 0.42, 0.32, "orange:0.1:0.6")):
        bm_coral(k[sw], rnd, (x, y, z), h=hh, r=0.045, depth=2, n=4, spread=42)
    k.emit("Coral", col, root)
    bm_tube_coral(k["tan:0.1:0.7"], k["black:0.3:0.6"], rnd, (0.55, 0.85, T + 0.6), n=4, h=(0.14, 0.3), r=(0.045, 0.07))
    bm_tube_coral(k["tan:0.1:0.7"], k["black:0.3:0.6"], rnd, (-0.95, -0.45, T + 0.4), n=4, h=(0.12, 0.28), r=(0.04, 0.065))
    for (x, y, nx, ny) in ((0.95, 0.35, 1, 0.3), (-0.98, 0.3, -1, 0.3), (0.3, -0.62, 0.3, -1), (-0.5, 1.2, -0.5, 1)):
        bm_barnacles(k["cream:0.1:0.6"], k["black:0.3:0.6"], rnd, (x, y, T + 0.3), (nx, ny, 0.35), n=4, r=0.04)
    bm_scallop(k["cream:0.05:0.7"], (0.35, 1.25, T + 0.55), r=0.2, yaw=20, tilt=55, ribs=7)
    bm_starfish(k["orange:0.1:0.5"], (-0.45, 0.95, T + 0.76), r=0.17, yaw=20, normal=(-0.3, 0.4, 1))
    bm_starfish(k["salmon:0.1:0.5"], (0.9, -0.55, T + 0.5), r=0.15, yaw=70, normal=(0.4, -0.3, 1))
    k.emit("Shells", col, root)
    # ---- the belfry: four lumpy coral trunks rooted in the rock, bending in to meet at the apex, knuckled and
    #      studded with polyps, with coral branches growing out of them; a band of the team's color under the ring
    for a in COL_A:
        rings, zs = [], []
        z = T + 0.5
        while z < APEX - 0.02:
            zs.append(z)
            z += 0.16 if z < RING_Z - 0.2 or z > RING_Z + 0.2 else 0.11
        zs.append(APEX)
        pts = [col_point(a, z) for z in zs]
        for i, (p, z) in enumerate(zip(pts, zs)):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            x, y = _perp(d)
            rt = 0.21 - 0.125 * (z - T - 0.5) / (APEX - T - 0.5)
            knuckle = sum(0.16 * math.exp(-((z - zk) / 0.07) ** 2) for zk in (T + 1.1, T + 1.75, T + 2.3, T + 3.0))
            ring = []
            for j in range(8):
                ang = 2 * math.pi * j / 8 + z * 0.9
                bump = 1.0 + 0.12 * math.sin(ang * 3 + z * 8 + a) + 0.07 * math.sin(ang * 2 - z * 5) + knuckle
                ring.append(p + (x * math.cos(ang) + y * math.sin(ang)) * (rt * bump))
            rings.append(ring)
        bm_loft(k["salmon:0.08:0.8"], rings, cap0=True, cap1=True)
        for z, side, hh in ((T + 1.45, 1, 0.42), (T + 2.95, -1, 0.3)):
            p = col_point(a, z)
            out = (p - Vector((C.x, C.y, z))).normalized()
            ax = Vector((-out.y, out.x, 0)) * side
            bm_coral(k["orange:0.1:0.55"], rnd, p + out * 0.1 + ax * 0.08, h=hh, r=0.04, up=(out * 0.7 + ax * 0.3 + Vector((0, 0, 0.6))), depth=2, n=4, spread=42)
        for _ in range(7):
            z = rnd.uniform(T + 0.9, T + 3.1)
            p = col_point(a, z)
            ang = rnd.uniform(0, 6.283)
            q = p + Vector((math.cos(ang), math.sin(ang), 0)) * (0.21 - 0.125 * (z - T - 0.5) / (APEX - T - 0.5)) * 0.92
            bm_ellipsoid(k["cream:0.05:0.5"], tuple(q), (0.045, 0.045, 0.035), u=6, v=4)
    bm_ellipsoid(k["salmon:0.05:0.5"], (C.x, C.y, APEX + 0.02), (0.24, 0.24, 0.18), u=8, v=5)
    cols = k.emit("Trunks", col, root)
    for o in cols:
        if o.name.endswith("salmon"):
            paint_faces(o, "team", lambda c, n: RING_Z - 0.34 < c.z < RING_Z - 0.1 and n.z < 0.7 and (Vector((c.x, c.y, 0)) - Vector((C.x, C.y, 0))).length > 0.55, team=True, lo=0.1, hi=0.6)
    # the coral ring through the trunks, the ice yoke across it, ice growing on the ring, icicles under it
    ringp = [C + Vector((RING_R * math.cos(2 * math.pi * i / 16), RING_R * math.sin(2 * math.pi * i / 16), RING_Z)) for i in range(17)]
    bm_tube(k["cream:0.1:0.6"], ringp, 0.085, n=7, cap=True)
    for a in COL_A:
        p = col_point(a, RING_Z)
        bm_ellipsoid(k["cream:0.1:0.6"], (p.x, p.y, RING_Z), (0.2, 0.2, 0.15), u=8, v=5)
    k.emit("Ring", col, root)
    bm_beam(k["sky:0.0:0.5"], (C.x, C.y - RING_R - 0.02, RING_Z + 0.03), (C.x, C.y + RING_R + 0.02, RING_Z + 0.03), 0.15, 0.13)
    for sy in (-1, 1):
        bm_ice_cluster(k["sky:0.0:0.5"], rnd, (C.x, C.y + sy * (RING_R - 0.02), RING_Z + 0.08), n=4, h=(0.14, 0.3), r=0.055, spread=0.1, fan=35)
    for a in COL_A:
        p = col_point(a, RING_Z + 0.1)
        out = (p - Vector((C.x, C.y, RING_Z + 0.1))).normalized()
        bm_ice_cluster(k["sky:0.0:0.5"], rnd, p + out * 0.1, n=4, h=(0.16, 0.34), r=0.05, spread=0.1, up=tuple(out * 0.55 + Vector((0, 0, 0.8))), fan=30)
    for i in range(12):
        a = math.radians(360 * i / 12 + 15)
        if min(abs((math.degrees(a) - ca + 180) % 360 - 180) for ca in COL_A) < 20:
            continue
        bm_icicle(k["sky:0.0:0.45"], (C.x + RING_R * math.cos(a), C.y + RING_R * math.sin(a), RING_Z - 0.06), rnd.uniform(0.14, 0.32), r=0.035)
    k.emit("Yoke", col, root)
    # pennant poles on the ring, left and right
    for sx in (-1, 1):
        bm_cyl(k["iron:0.2:0.7"], 0.03, 0.024, 0.7, (C.x + sx * RING_R, C.y, RING_Z + 0.32), seg=6)
        bm_cyl(k["gold:0.1:0.5"], 0.055, 0.0, 0.11, (C.x + sx * RING_R, C.y, RING_Z + 0.72), seg=6)
    k.emit("Poles", col, root)
    empty("Head", col, root, (C.x, C.y, P - 0.5), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((C.x, C.y, T), (C.x, C.y, T + 0.3), None),
         "bell": ((C.x, C.y, P), (C.x, C.y, P - 0.5), "root"),
         "clapper": ((C.x, C.y, P - 0.25), (C.x, C.y, P - 0.8), "bell"),
         "crown": ((C.x, C.y, APEX), (C.x, C.y, APEX + 0.3), "root"),
         "frost": ((C.x, C.y, WATER), (C.x, C.y, WATER + 0.2), "root")}
ICICLE_TIPS = [(C.x + RING_R * math.cos(math.radians(a)), C.y + RING_R * math.sin(math.radians(a)), RING_Z - 0.3) for a in (15, 195, 255)]
for _i, _p in enumerate(ICICLE_TIPS):
    BONES["drip.%d" % _i] = (_p, (_p[0], _p[1], _p[2] - 0.1), "root")
for _i, ((_x, _y), _r) in enumerate(FLOES):
    BONES["floe.%d" % _i] = ((_x, _y, WATER), (_x, _y, WATER + 0.1), "root")
PEN_TOP = RING_Z + 0.68
flag_bones(BONES, "pen.L", (C.x - RING_R, C.y, PEN_TOP), (-1, 0, 0), 0.78, segs=3)
flag_bones(BONES, "pen.R", (C.x + RING_R, C.y, PEN_TOP), (1, 0, 0), 0.78, segs=3)
KELP = [((1.75, 0.3), 0.55, (0.1, -0.08)), ((-2.0, -0.75), 0.6, (-0.08, 0.1)), ((-1.3, 0.75), 0.45, (0.0, 0.1))]
for _i, (_b, _h, _lean) in enumerate(KELP):
    kelp_bones(BONES, "kelp.%d" % _i, (_b[0], _b[1], WATER - 0.05), _h, segs=3, lean=_lean)

# the bell, round its pivot: down the outside (crown, shoulder, waist, sound bow, lip), then up the inside
BELL = [(0.11, -0.05), (0.21, -0.09), (0.33, -0.2), (0.39, -0.38), (0.41, -0.58), (0.46, -0.74), (0.57, -0.86), (0.61, -0.92),
        (0.52, -0.9), (0.46, -0.78), (0.37, -0.6), (0.32, -0.4), (0.24, -0.26), (0.1, -0.2)]


def build_rig():
    col = collection("Tidecaller")
    root = bpy.data.objects["Tidecaller"]
    head = bpy.data.objects["Head"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(11)
    k = Kit()
    # ---- the bell: bronze, a frost collar at the shoulder, the team's band round the waist, icicles on the lip
    bm_cyl(k["iron:0.2:0.7"], 0.05, 0.05, 0.2, (C.x, C.y, P + 0.03), seg=8)
    bm_revolve(k["gold:0.3:0.9"], BELL, (C.x, C.y, P), seg=18)
    bell = k.emit("Bell", col, rig=rig, bone="bell")[0]
    # the team's band on the shoulder (seen from above) and a thinner one above the sound bow
    paint_faces(bell, "team", lambda c, n: (P - 0.38 < c.z < P - 0.2 or P - 0.74 < c.z < P - 0.6) and n.z > -0.3
                and (Vector((c.x, c.y, 0)) - Vector((C.x, C.y, 0))).length > 0.3, team=True, lo=0.1, hi=0.55)
    bm_revolve(k["sky:0.0:0.45"], [(0.16, -0.06), (0.26, -0.11), (0.34, -0.19), (0.33, -0.22), (0.27, -0.17), (0.19, -0.12)], (C.x, C.y, P), seg=18)
    for i in range(9):
        a = math.radians(360 * i / 9 + 10)
        bm_icicle(k["sky:0.0:0.45"], (C.x + 0.55 * math.cos(a), C.y + 0.55 * math.sin(a), P - 0.9), rnd.uniform(0.12, 0.3), r=0.04)
    bm_ice_cluster(k["sky:0.0:0.45"], rnd, (C.x + 0.33, C.y + 0.12, P - 0.2), n=3, h=(0.1, 0.2), r=0.04, spread=0.06, up=(0.8, 0.3, 0.6))
    k.emit("Bell_Ice", col, rig=rig, bone="bell")
    # the clapper: an iron rod and ball, swinging from inside the crown
    bm_cyl(k["iron:0.2:0.7"], 0.035, 0.03, 0.55, (C.x, C.y, P - 0.52), seg=6)
    bm_ellipsoid(k["iron:0.15:0.65"], (C.x, C.y, P - 0.82), (0.12, 0.12, 0.11), u=8, v=5)
    k.emit("Clapper", col, rig=rig, bone="clapper", bevel=0.01)
    # ---- the crown: glowing ice at the apex, paler crystals round it
    bm_ice_cluster(k[GLOW_ICE], rnd, (C.x, C.y, APEX + 0.08), n=5, h=(0.32, 0.66), r=0.1, spread=0.13, fan=22)
    bm_ice_cluster(k["sky:0.0:0.5"], rnd, (C.x, C.y, APEX + 0.02), n=7, h=(0.18, 0.4), r=0.07, spread=0.3, fan=48)
    k.emit("Crown", col, rig=rig, bone="crown")
    # ---- the frost ring (hidden at rest: scaled down on its bone), drips, bobbing floes, kelp, pennants
    bm_ring_flat(k[GLOW_ICE], (C.x, C.y, 0), 2.7, 2.15, WATER + 0.03, seg=28, th=0.02, crest=0.14)
    k.emit("Frost", col, rig=rig, bone="frost")
    for i, p in enumerate(ICICLE_TIPS):
        bm_ellipsoid(k[GLOW_ICE], p, (0.03, 0.03, 0.045), u=6, v=4)
        k.emit("Drip_%d" % i, col, rig=rig, bone="drip.%d" % i)
    for i, ((x, y), r) in enumerate(FLOES):
        bm_floe(k["white:0.0:0.3"], rnd, (x, y, 0), r, WATER + 0.04)
        bm_ice_cluster(k["sky:0.0:0.5"], rnd, (x + r * 0.2, y - r * 0.1, WATER + 0.03), n=3, h=(0.12, 0.3), r=0.05, spread=0.1)
        k.emit("Floe_%d" % i, col, rig=rig, bone="floe.%d" % i, bevel=0.01)
    for i, (b, h, lean) in enumerate(KELP):
        kelp_part("Kelp_%d" % i, col, rig, "kelp.%d" % i, rnd, (b[0], b[1], WATER - 0.05), h, segs=3, lean=lean, fronds=3, w=0.14)
    for s, sx in (("L", -1), ("R", 1)):
        flag_part("Pennant_" + s, col, rig, "pen." + s, (C.x + sx * RING_R, C.y, PEN_TOP), (sx, 0, 0), 0.78, 0.2, segs=3)
    empty("Muzzle", col, head, (0, 0, -0.38), 0.2, "SPHERE")
    return rig


IDLE_LEN = 90
FIRE_LEN = 18


def pose(rig, t=0.0, bell=0.0, clap=0.0, crown=1.0, bob=0.0, frost=0.02, frost_z=0.0, gust=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["bell"].rotation_quaternion = q(pb["bell"], (0, 1, 0), bell)
    pb["clapper"].rotation_quaternion = q(pb["clapper"], (0, 1, 0), clap)
    pb["crown"].scale = (crown,) * 3
    pb["crown"].location = arm_space_loc(pb["crown"], (0, 0, bob))
    # the bone stands upright (its Y is the world's Z): scale its X and Z to grow the ring across the sea; at rest it
    # shrinks on every axis (scaling only X and Y left the ring a long needle along the world's Y)
    pb["frost"].scale = (frost, min(1.0, frost * 4.0), frost)
    pb["frost"].location = arm_space_loc(pb["frost"], (0, 0, frost_z))
    for s, off in (("L", 0.0), ("R", 0.37)):
        wave_flag(rig, "pen." + s, t + off, amp=1.0 + gust)
    for i in range(len(KELP)):
        sway_kelp(rig, "kelp.%d" % i, t + 0.31 * i, amp=1.0, push=(gust * 9.0, gust * 4.0))
    for i, p in enumerate(ICICLE_TIPS):
        u = (t + i / 3.0) % 1.0
        b = pb["drip.%d" % i]
        b.location = arm_space_loc(b, (0, 0, -(p[2] - WATER - 0.02) * u * u))
        s = min(1.0, math.sin(math.pi * u) * 2.5)
        b.scale = (s, s, s)
    for i in range(len(FLOES)):
        b = pb["floe.%d" % i]
        b.location = arm_space_loc(b, (0, 0, 0.018 * math.sin(2 * math.pi * (t + 0.3 * i))))
        b.rotation_quaternion = q(b, (1, 0, 0), 1.6 * math.sin(2 * math.pi * (t + 0.2 * i) + 0.7)) @ q(b, (0, 1, 0), 1.2 * math.sin(2 * math.pi * (t * 1.0 + 0.45 * i)))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        pose(rig, t=t, bell=3.5 * math.sin(ph), clap=-2.6 * math.sin(ph), crown=1.0 + 0.07 * math.sin(2 * ph), bob=0.04 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the bell pulls back, swings hard through (the clapper lags, then strikes the bow at frame 8), swings back, settles
        bell = keyed([(0, 0), (3, -10), (8, 42), (14, -26), (18, 0)], f)
        clap = keyed([(0, 0), (3, 7), (6, -6), (8, -32), (11, 10), (14, 24), (18, 0)], f)
        frost = keyed([(0, 0.02), (7, 0.02), (8, 0.3), (10, 1.0), (14, 1.3), (17, 1.45), (17.5, 0.02), (18, 0.02)], f)
        frost_z = keyed([(0, 0.0), (13, 0.0), (17, -0.32), (17.5, 0.0), (18, 0.0)], f)
        crown = 1.0 + 0.45 * smooth((f - 6) / 3.0) * (1 - smooth((f - 10) / 7.0))
        gust = 1.3 * smooth((f - 7) / 3.0) * (1 - smooth((f - 13) / 5.0))
        pose(rig, t=f / FIRE_LEN, bell=bell, clap=clap, crown=crown, frost=frost, frost_z=frost_z, gust=gust)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.7), "dist": 11.5, "yaw": 150, "pitch": 20, "anim_target": (C.x, C.y, T + 2.1), "anim_dist": 6.2,
           "frames": [("idle", 0), ("idle", 45), ("fire", 5), ("fire", 9), ("fire", 13)],
           "extra": [{"yaw": 200, "pitch": 10, "dist": 4.6, "target": (C.x, C.y, T + 2.2)},
                     {"yaw": 100, "pitch": 26, "dist": 5.6, "target": (1.6, -0.4, 0.9)}]}


def build_all():
    build_base()
    build_rig()
    build_anims()
