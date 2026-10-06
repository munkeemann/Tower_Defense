"""Builds the Bone Colossus (footprint "fan5": [0,0] the hub, with [-1,0], [0,-1], [1,-1], [1,0] fanned round its front
and right), the Bone Legion's tier IV giant: every 2.5 s it leaps across the map onto its prey, smashes both fists down
and bounds home (GameData.STRIKES "lunge").

    python tools/blender/build.py bone_colossus --out <preview dir>

Its home is one place across all five hexes: a broken ossuary, a pit sunk into the ground and ringed by a cracked
crypt wall that climbs from a low curb at the back to two wings at the far corners, each ending in a pier that burns
with soul-fire. The front of the ring is smashed open (where it climbs out). Inside: a paved floor heaved up round a
cracked, glowing seal (where it stands, and what you see when it's away), heaps of bones banked against the walls,
skull niches, toppled gravestones, broken chains and the Legion's banners in the team's color.
The colossus is the Head, so the game can send it across the map: a hunched giant of fused bones about 3 units tall, a
ridged spine and a cage of ribs round a burning soul, a horned skull with a hinged jaw and flaming sockets, bone-plate
shoulders, forearms of bundled bones and skulls, great knuckled fists, a ragged half-cape and loincloth in the team's
color. Its limbs reach for goals (grave_big_common.Fk): the feet stay planted while the body heaves.
Clips: idle (breathes, sways, looks about, flexes its fists), run (a bounding gallop, looped while it leaps), fire (both
fists heaved overhead and smashed down 1.4 in front: the blow lands 0.3 s in).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_big_common.py"), encoding="utf-8").read())

TID = "bone_colossus"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
H = hex_to_world(0, 0, MID)
FL, F, FR, BR = (hex_to_world(q, s, MID) for q, s in ((-1, 0), (0, -1), (1, -1), (1, 0)))
TOP = 0.34
FLOOR = 0.07                    # the pit's floor
RIM_IN = 0.52                   # the pit's rim, in from the footprint's outline
TH = 0.24                       # the ring wall's thickness
HOME = Vector((H.x, -0.3, 0.0))
SEAL_R = 0.66
STAND = FLOOR + 0.1             # the seal's top: where the colossus stands
TEAM = "team!:0.1:0.78"
AWAY = bool(os.environ.get("COLOSSUS_AWAY"))        # (a preview of the home without its giant)

# the ring wall's height above the ground along each edge of the pit (start, end), counterclockwise from the far-left
# tip: low at the back (the camera's side), climbing to the two far corners; the front is smashed open
HE = [(0.8, 0.34), (0.3, 0.2), (0.2, 0.16), (0.14, 0.14), (0.16, 0.24), (0.26, 0.3), (0.34, 0.45), (0.5, 0.55),
      (0.55, 0.8), (0.85, 1.25), (1.3, 0.62), (0.5, 0.12), (0.0, 0.0), (0.12, 0.5), (0.62, 1.3), (1.25, 0.8)]
FAR = (8, 9, 10, 11, 12, 13, 14, 15, 0)             # edges whose inner face shows: coursed down to the pit's floor
HEAPS = [(1.55, -1.75, 0.72, 0.5), (-2.2, 0.38, 0.62, 0.42), (1.62, 0.48, 0.5, 0.34)]      # bone heaps: x, y, radius, height


def heap_h(x, y):
    best = 0.0
    for cx, cy, r, h in HEAPS:
        d2 = ((x - cx) ** 2 + (y - cy) ** 2) / (r * r)
        if d2 < 1.0:
            best = max(best, h * (1.0 - d2) ** 0.85)
    return best


def build_base():
    col = collection("Bone_colossus")
    root = empty("Bone_colossus", col, None, (0, 0, 0), 0.6, "ARROWS")
    rnd = random.Random(13)
    U = outline(CELLS, RIM_IN)
    RIM = smooth_loop(U, 1, 0.15)
    WALL = inset_loop(RIM, -(TH * 0.5 - 0.03))
    pin = inset_loop(RIM, 0.08)
    in_pit = lambda x, y: inside(pin, x, y)
    plinth_cut(CELLS, col, root, TOP, holes=[RIM], grid=0.36)
    k = Kit()
    pit_lining(k[STONE], k[EARTH], RIM, TOP, FLOOR, batter=0.0, rnd=rnd, grid=0.36)
    k.emit("Pit", col, root)

    # ---- the ring wall, segment by segment round the pit
    def seg(j):
        i = j // 2
        if j % 2 == 0:
            hs, he = HE[i]
            return lerp(hs, he, 0.15), lerp(hs, he, 0.85), i in FAR, ("edge", i)
        return HE[i][1], HE[(i + 1) % 16][0], (i in FAR) and ((i + 1) % 16 in FAR), ("corner", (i + 1) % 16)
    n = len(RIM)
    banners, niches = [], []
    for j in range(n):
        hs, he, far, (kind, idx) = seg(j)
        if max(hs, he) < 0.1:
            continue
        a, b = WALL[j], WALL[(j + 1) % n]
        ax = (b - a).normalized()
        nin = Vector((-ax.y, ax.x, 0))                      # toward the pit
        z0 = FLOOR if far else TOP - 0.03
        up = TOP - z0
        notch = []
        if (hs + he) * 0.5 > 0.42 and kind == "edge":
            for _ in range(2):
                t0 = rnd.uniform(0.05, 0.75)
                notch.append((t0, t0 + rnd.uniform(0.12, 0.24)))
        holes = []
        if (kind, idx) in (("edge", 10), ("edge", 14)):     # a skull niche near the tall end of each front wall
            L = (b - a).length
            tc = 0.26 if idx == 10 else 0.74
            holes = [(tc - 0.18 / L, tc + 0.18 / L, up + 0.3, up + 0.3 + 0.42)]
            notch = [(0.62, 0.8)] if idx == 10 else [(0.2, 0.38)]
            niches.append((a.lerp(b, tc), ax, nin, z0 + up + 0.3))
        if (kind, idx) in (("edge", 9), ("edge", 15)):
            banners.append((a, b, ax, nin, lerp(hs, he, 0.5)))
            notch = notch[:1]
        top = lambda t, hs=hs, he=he, up=up, notch=notch: up + lerp(hs, he, t) - (0.19 if any(u < t < v for u, v in notch) else 0.0)
        ruin_wall(k, rnd, a - ax * 0.025, b + ax * 0.025, z0, top, th=TH, holes=holes, back=glow((0.1, 0.42, 0.1), 0.5), side=1,
                  core=SOCKET if max(hs, he) > 0.48 else None)
    k.emit("Wall", col, root, vary=0.09, seed=5)
    for c, ax, nin, z in niches:                            # the niche's arch, and three skulls piled in it
        bm_arch(k[STONE_LT], (c.x, c.y, z), ax, 0.36, 0.24, th=0.1, depth=TH + 0.07, n=5)
        for dx, dz, yaw in ((-0.088, 0.075, 12), (0.09, 0.07, -14), (0.0, 0.215, 3)):
            p = c + ax * dx + nin * 0.035 + Vector((0, 0, z + dz))
            p.z = z + dz
            skull(k, frame(p, nin) @ Matrix.Rotation(math.radians(yaw), 4, "Z"), s=0.16, bone=BONE_OLD, detail=0, jaw=dx != 0.0)
    k.emit("Niches", col, root, vary=0.06)
    # ---- the two brazier piers at the far corners, stub piers at the tips and either side of the breach
    fires = []
    for vi, w, h, cap in ((10, 0.42, 1.5, "flat"), (15, 0.42, 1.5, "flat"), (9, 0.32, 0.95, "point"), (0, 0.32, 0.9, None),
                          (11, 0.34, 0.66, None), (14, 0.34, 0.72, "flat"), (8, 0.3, 0.62, "point"), (6, 0.28, 0.5, None)):
        j = 2 * ((vi - 1) % 16) + 1
        c = (WALL[j] + WALL[(j + 1) % n]) * 0.5
        far = vi != 6
        z0 = FLOOR if far else TOP - 0.03
        yaw = math.degrees(math.atan2((WALL[(j + 1) % n] - WALL[j]).y, (WALL[(j + 1) % n] - WALL[j]).x))
        pier(k, rnd, c, w, z0, TOP - z0 + h, cap=cap, yaw=yaw)
        if h > 1.2:
            fires.append(brazier(k, (c.x, c.y, TOP + h + 0.07), h=0.2, r=0.21, coals=glow(SOULCORE, 0.8)))
    k.emit("Piers", col, root, vary=0.09, seed=8)
    for p in fires:
        bm_flame(k[glow(SOULFIRE, 0.7)], rnd, p, h=0.6, r=0.17, n=4)
    k.emit("Pier_Fire", col, root)
    # ---- the Legion's banners on the wing walls (both faces), on rods
    for a, b, ax, nin, hh in banners:
        m = a.lerp(b, 0.5)
        zr = TOP + hh - 0.17
        for sd in (1, -1):
            o = nin * (sd * (TH * 0.5 + 0.035))
            p0, p1 = m - ax * 0.19 + o, m + ax * 0.19 + o
            if sd < 0:
                p0, p1 = p1, p0
            bm_cloth(k[TEAM], (p0.x, p0.y, zr), (p1.x, p1.y, zr), 0.62 if sd > 0 else 0.5, cols=3, rows=3, wave=0.025, rnd=rnd)
            bm_beam(k["wood_dark:0.2:0.7"], (p0.x, p0.y, zr + 0.015) + tuple(), (p1.x, p1.y, zr + 0.015), 0.04, 0.04)
    k.emit("Banners", col, root)
    # ---- the floor: the cracked seal the colossus stands on, slabs heaved up round it, paving out to the walls
    sk = Kit()
    for i in range(9):
        a0, a1 = 2 * math.pi * (i + 0.04) / 9, 2 * math.pi * (i + 0.96) / 9
        t = bmesh.new()
        _wedge(t, Vector((0, 0, 0)), a0, a1, 0.25, SEAL_R, 0.0, 0.085)
        am = (a0 + a1) * 0.5
        tip = Matrix.Rotation(math.radians(rnd.uniform(-5, 5)), 4, Vector((math.cos(am), math.sin(am), 0))) @ \
            Matrix.Rotation(math.radians(rnd.uniform(-2, 7)), 4, Vector((-math.sin(am), math.cos(am), 0)))
        bm_merge(sk[STONE_LT if i % 3 == 0 else STONE], t, Matrix.Translation((HOME.x, HOME.y, FLOOR + 0.015 + rnd.uniform(0, 0.02))) @ tip)
        r = SEAL_R * 0.66
        g = bmesh.new()                                      # a rune cut in each stone
        bm_box(g, (0.2, 0.035, 0.012), (r, 0, 0.09))
        bm_box(g, (0.035, 0.12, 0.012), (r + 0.045, 0, 0.09))
        g.normal_update()
        bmesh.ops.delete(g, geom=[f for f in g.faces if f.normal.z < 0.9], context="FACES")
        bm_merge(sk[glow(SOULFIRE, 0.8)], g, Matrix.Translation((HOME.x, HOME.y, FLOOR + 0.02)) @ tip @ Matrix.Rotation(am, 4, "Z"))
    for sx in (-1, 1):
        bm_cyl(sk[STONE], 0.22, 0.2, 0.09, (HOME.x + sx * 0.03, HOME.y, FLOOR + 0.06), rot=(sx * 5, 0, 30), seg=6)
    bm_cyl(sk[glow(SOULFIRE, 0.8)], SEAL_R - 0.03, SEAL_R - 0.03, 0.03, (HOME.x, HOME.y, FLOOR + 0.02), seg=12)
    sk.emit("Seal", col, root, vary=0.06)
    dist = lambda x, y: math.hypot(x - HOME.x, y - HOME.y)
    bounds = (-3.2, -2.6, 2.6, 2.4)
    bm_slabs(k[STONE], rnd, lambda x, y: in_pit(x, y) and SEAL_R + 0.12 < dist(x, y) < 1.2 and heap_h(x, y) < 0.1,
             bounds, FLOOR, size=0.4, keep=0.9, heave=0.75, yaw=8)
    bm_slabs(k[STONE], rnd, lambda x, y: in_pit(x, y) and dist(x, y) >= 1.2 and heap_h(x, y) < 0.16,
             bounds, FLOOR, size=0.46, keep=0.8, heave=0.12, yaw=8)
    k.emit("Floor", col, root, vary=0.1, seed=3)
    for i in range(7):                                      # soul-light in the cracks radiating from the seal
        a = 2 * math.pi * (i + rnd.uniform(-0.25, 0.25)) / 7
        p0 = HOME + Vector((math.cos(a), math.sin(a), 0)) * (SEAL_R - 0.02)
        a2 = a + rnd.uniform(-0.35, 0.35)
        p1 = p0 + Vector((math.cos(a2), math.sin(a2), 0)) * rnd.uniform(0.28, 0.5)
        a3 = a2 + rnd.uniform(-0.6, 0.6)
        p2 = p1 + Vector((math.cos(a3), math.sin(a3), 0)) * rnd.uniform(0.2, 0.42)
        if not in_pit(p2.x, p2.y):
            continue
        bm_beam(k[glow(SOULFIRE, 0.8)], (p0.x, p0.y, FLOOR + 0.022), (p1.x, p1.y, FLOOR + 0.022), 0.07, 0.03, w1=0.045)
        bm_beam(k[glow(SOULFIRE, 0.8)], (p1.x, p1.y, FLOOR + 0.022), (p2.x, p2.y, FLOOR + 0.022), 0.045, 0.03, w1=0.012)
    k.emit("Cracks", col, root)
    # ---- heaps of bones banked against the walls, skulls and ribs on them
    hb = bmesh.new()
    bm_heap(hb, rnd, lambda x, y: heap_h(x, y) if in_pit(x, y) else 0.0, bounds, z=FLOOR, grid=0.2, noise=0.035)
    bm_merge(k["beige:0.45:0.98"], facet(hb))
    k.emit("Heaps", col, root, vary=0.12, seed=4)
    for hi, (cx, cy, r, h) in enumerate(HEAPS):
        def pick(cx=cx, cy=cy, r=r):
            for _ in range(40):
                a, d = rnd.uniform(0, 6.283), r * 0.85 * math.sqrt(rnd.random())
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
                if in_pit(x, y):
                    return x, y
            return cx, cy
        strew_bones(k, rnd, (7, 5, 4)[hi], pick, lambda x, y: FLOOR + heap_h(x, y), skulls=(3, 2, 2)[hi], ribs=(1, 1, 0)[hi],
                    skull_s=0.2)
    for x, y, yaw in ((-0.95, -0.72, 40), (0.72, -1.02, 110), (-0.3, 1.25, 20), (0.25, 1.05, 80), (-1.52, -0.1, 150)):   # strays
        strew_bones(k, rnd, 1, lambda x=x, y=y: (x, y), lambda x, y: FLOOR + 0.05, size=(0.3, 0.42), r=0.04)
    skull(k, xf((0.52, -0.82, FLOOR + 0.13), (-20, 10, 200)), s=0.22, bone=BONE_OLD, detail=1, jaw=False)
    k.emit("Bones", col, root, vary=0.08, seed=6)
    # ---- toppled gravestones, the breach's rubble, broken chains
    gravestone(k, xf((-0.25, -0.97, FLOOR + 0.02), (-20, 0, 176)), "round", w=0.36, h=0.56)
    gravestone(k, xf((0.82, -0.72, FLOOR + 0.11), (-86, 0, 24)), "point", w=0.34, h=0.58, base=False)
    gravestone(k, xf((-1.22, -0.42, FLOOR + 0.02), (6, -9, 118)), "broken", w=0.36, h=0.6)
    gravestone(k, xf((0.98, -1.5, FLOOR + 0.05), (14, 12, 215)), "cross", w=0.4, h=0.62, th=0.1)
    gravestone(k, xf((-0.55, -1.3, TOP), (8, 0, 172)), "point", w=0.3, h=0.42, base=False)
    gravestone(k, xf((1.5, 0.12, FLOOR + 0.2), (-70, 15, 300)), "round", w=0.32, h=0.5, base=False)
    k.emit("Graves", col, root, vary=0.08, seed=9)
    bc = (U[12] + U[13]) * 0.5
    rb = bmesh.new()
    edge = outline(CELLS, 0.36)                             # (the heap stops short of the plinth's flank)
    bm_heap(rb, rnd, lambda x, y: max(0.0, 0.3 * (1.0 - math.hypot((x - bc.x) / 0.62, (y - bc.y - 0.02) / 0.5) ** 2)) if inside(edge, x, y) else 0.0,
            bounds, z=FLOOR, grid=0.2, noise=0.03)
    bm_merge(k["stone_dark:0.3:0.95"], facet(rb))
    bm_rubble(k[STONE], rnd, (bc.x, bc.y - 0.15), n=7, r=0.55, size=0.17, z=FLOOR + 0.1)
    bm_rubble(k[STONE_LT], rnd, (bc.x + 0.05, bc.y + 0.14), n=4, r=0.2, size=0.16, z=TOP - 0.02)
    bm_rubble(k[STONE], rnd, (U[11].x - 0.25, U[11].y + 0.3), n=3, r=0.25, size=0.15, z=FLOOR)
    bm_rubble(k[STONE], rnd, (U[4].x - 0.1, U[4].y + 0.3), n=3, r=0.3, size=0.14, z=FLOOR)
    k.emit("Rubble", col, root, vary=0.1, seed=11)
    for pts in ([(1.52, 0.86, TOP + 0.7), (1.38, 0.72, TOP + 0.2), (1.2, 0.5, FLOOR + 0.3), (0.86, 0.1, FLOOR + 0.1), (0.62, -0.18, FLOOR + 0.1)],
                [(-1.74, 0.9, TOP + 0.62), (-1.66, 0.74, TOP + 0.12), (-1.5, 0.5, FLOOR + 0.1), (-1.12, -0.02, FLOOR + 0.1), (-1.0, -0.3, FLOOR + 0.1)]):
        bm_chain(k["iron:0.35:0.95"], pts, link=0.17, w=0.085, th=0.04, seg=4)
        e = Vector(pts[-1])
        ring(k[RUST], (e.x, e.y, 0), 0.13, 0.08, FLOOR + 0.07, FLOOR + 0.12, seg=7)
        s = Vector(pts[0])
        bm_box(k[RUST], (0.12, 0.12, 0.12), (s.x, s.y + 0.03, s.z))
    k.emit("Chains", col, root, vary=0.08)
    empty("Head", col, root, (HOME.x + (60.0 if AWAY else 0.0), HOME.y, STAND), 0.5, "SINGLE_ARROW")
    return root


# ================================================================================================ the colossus
# in the head's space (+Y forward, the ground under its middle at the origin); its rest pose is its stance
CS = 1.0
SIDES = (("L", -1), ("R", 1))
HIP = {s: Vector((s * 0.36, -0.05, 1.14)) for s in (-1, 1)}
KNEE = {s: Vector((s * 0.6, 0.3, 0.67)) for s in (-1, 1)}
ANK = {s: Vector((s * 0.54, -0.02, 0.23)) for s in (-1, 1)}
TOE = {s: Vector((s * 0.6, 0.42, 0.1)) for s in (-1, 1)}
SHO = {s: Vector((s * 0.9, -0.04, 2.36)) for s in (-1, 1)}
ELB = {s: Vector((s * 1.12, 0.06, 1.58)) for s in (-1, 1)}
WRI = {s: Vector((s * 0.9, 0.42, 1.0)) for s in (-1, 1)}
KNU = {s: Vector((s * 0.8, 0.76, 0.52)) for s in (-1, 1)}
SKULL_C = Vector((0, 0.46, 2.74))
SKULL_S = 0.8
SKULL_M = xf(SKULL_C, (-12, 0, 0), SKULL_S)
SPINE = [(0, -0.12, 1.3), (0, -0.24, 1.5), (0, -0.31, 1.72), (0, -0.34, 1.95), (0, -0.3, 2.17), (0, -0.17, 2.36),
         (0, 0.0, 2.48), (0, 0.16, 2.57)]
SPIKES = [0.16, 0.2, 0.27, 0.36, 0.42, 0.36, 0.25, 0.0]
# the cloak, torn in two down the spine: chain name -> (x from, x to, how far it hangs, rows, how tattered)
CAPE_Y, CAPE_Z, CAPE_DIR = -0.5, 2.5, (0, -0.2, -1)
CAPES = {"cape": (0.16, 0.98, 1.3, 4, 0.34), "capl": (-0.95, -0.16, 0.98, 3, 0.5)}
TABS = {"tabf": ((-0.24, 0.2, 1.12), (0, 0.1, -1), 0.72), "tabb": ((-0.24, -0.3, 1.14), (0, -0.12, -1), 0.78)}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.3), None),
    "hips": ((0, -0.08, 1.18), (0, -0.2, 1.5), "root"),
    "spine": ((0, -0.2, 1.5), (0, -0.28, 1.92), "hips"),
    "chest": ((0, -0.28, 1.92), (0, -0.1, 2.4), "spine"),
    "neck": ((0, -0.02, 2.42), (0, 0.2, 2.6), "chest"),
    "skull": ((0, 0.2, 2.6), (0, 0.62, 2.54), "neck"),
    "jaw": ((0, 0.34, 2.52), (0, 0.72, 2.3), "skull"),
    "core": ((0, 0.05, 1.8), (0, 0.05, 2.1), "chest"),
    "eyes": ((0, 0.72, 2.7), (0, 0.72, 2.9), "skull"),
}
for _n, _s in SIDES:
    BONES["pauld." + _n] = (tuple(SHO[_s]), tuple(SHO[_s] + Vector((_s * 0.3, 0, 0.25))), "chest")
    BONES["arm.%s.1" % _n] = (tuple(SHO[_s]), tuple(ELB[_s]), "chest")
    BONES["arm.%s.2" % _n] = (tuple(ELB[_s]), tuple(WRI[_s]), "arm.%s.1" % _n)
    BONES["hand." + _n] = (tuple(WRI[_s]), tuple(KNU[_s]), "arm.%s.2" % _n)
    BONES["leg.%s.1" % _n] = (tuple(HIP[_s]), tuple(KNEE[_s]), "hips")
    BONES["leg.%s.2" % _n] = (tuple(KNEE[_s]), tuple(ANK[_s]), "leg.%s.1" % _n)
    BONES["foot." + _n] = (tuple(ANK[_s]), tuple(TOE[_s]), "leg.%s.2" % _n)
for _n, (_x0, _x1, _l, _r, _t) in CAPES.items():
    flag_bones(BONES, _n, ((_x0 + _x1) * 0.5, CAPE_Y, CAPE_Z), CAPE_DIR, _l, segs=3, parent="chest")
for _n, (_t, _d, _l) in TABS.items():
    flag_bones(BONES, _n, _t, _d, _l, segs=2, parent="hips")


def _band(bm, a, b, t, r, h, seg=8):
    """A collar round the limb a -> b at t along it."""
    a, b = Vector(a), Vector(b)
    tmp = bmesh.new()
    bm_cyl(tmp, r, r, h, (0, 0, 0), seg=seg)
    return bm_merge(bm, tmp, frame(a.lerp(b, t), b - a) @ Matrix.Rotation(math.radians(-90), 4, "X"))


def _bundle(k, rnd, a, b, n, r_core, r_bone, off, key=BONE, core="taupe_dark:0.3:0.9", twist=24.0, sides=5, flare=1.15):
    """A limb of n long bones bound round a dark core."""
    a, b = Vector(a), Vector(b)
    m = frame(a, b - a)
    x, z = m.to_3x3() @ Vector((1, 0, 0)), m.to_3x3() @ Vector((0, 0, 1))
    bm_tube(k[core], [a, a.lerp(b, 0.5), b], [r_core, r_core * 1.12, r_core * flare], n=7)
    for i in range(n):
        a0 = 2 * math.pi * i / n + 0.3
        a1 = a0 + math.radians(twist)
        p0 = a + (x * math.cos(a0) + z * math.sin(a0)) * off + (b - a) * 0.03
        p1 = b + (x * math.cos(a1) + z * math.sin(a1)) * off * flare - (b - a) * 0.02
        bm_bone(k[key], p0, p1, r_bone * rnd.uniform(0.9, 1.1), n=sides, knob=1.5)


def _hero_skull(k, kj, ke):
    """The colossus's head, in its own space (as grave_big_common.skull: facing +Y round the cranium's middle)."""
    b, d = k[BONE], k[SOCKET]
    bm_ellipsoid(b, (0, -0.05, 0.14), (0.37, 0.44, 0.35), u=10, v=7)
    bm_beam(b, (0, 0.2, 0.1), (0, 0.24, -0.3), 0.64, 0.3, w1=0.42, h1=0.2, up=(0, 1, 0))
    for sx in (-1, 1):
        bm_beam(b, (sx * 0.38, 0.24, 0.23), (sx * 0.02, 0.41, 0.09), 0.14, 0.1)                      # brows, scowling
        bm_beam(b, (sx * 0.36, -0.02, -0.02), (sx * 0.28, 0.33, -0.1), 0.07, 0.1)                    # cheekbones
        bm_cyl(d, 0.118, 0.09, 0.09, (sx * 0.165, 0.345, 0.01), rot=(90, 0, 0), seg=6)
        bm_ellipsoid(ke[glow(SOULCORE, 0.9)], (sx * 0.165, 0.39, 0.005), (0.06, 0.035, 0.06), u=5, v=3)
        bm_tube(ke[glow(SOULFIRE, 0.7)], [(sx * 0.17, 0.4, 0.03), (sx * 0.22, 0.41, 0.13), (sx * 0.27, 0.36, 0.22), (sx * 0.29, 0.27, 0.3)],
                [0.035, 0.042, 0.028, 0.0], n=4)
    bm_disc(d, (0, 0.402, -0.135), (0, 1, 0.1), 0.06, n=3, ry=0.085, phase=0.75)
    for i in range(7):                                                                              # upper fangs
        x = (i - 3) * 0.062
        ln = 0.21 if i in (1, 5) else 0.11
        bm_crystal(b, (x, 0.315 - abs(i - 3) * 0.012, -0.28), (x * 1.06, 0.33, -0.28 - ln), 0.036, n=4, shoulder=0.3)
    j = kj[BONE]
    bm_beam(j, (0, 0.05, -0.4), (0, 0.37, -0.5), 0.54, 0.13, w1=0.36, h1=0.11)
    for sx in (-1, 1):
        bm_beam(j, (sx * 0.26, 0.07, -0.42), (sx * 0.31, -0.03, -0.1), 0.08, 0.15, up=(0, 1, 0))
        bm_crystal(j, (sx * 0.2, 0.3, -0.46), (sx * 0.235, 0.37, -0.2), 0.05, n=4, shoulder=0.3)       # tusks
    for i in range(6):
        x = (i - 2.5) * 0.07
        bm_crystal(j, (x, 0.345, -0.46), (x, 0.355, -0.34), 0.034, n=4, shoulder=0.3)
    h = k[BONE_DARK]                                                                                # horns: the left one snapped
    bm_tube(h, [(0.3, -0.02, 0.28), (0.56, -0.1, 0.4), (0.78, -0.06, 0.6), (0.86, 0.12, 0.84), (0.8, 0.34, 1.04)],
            [0.16, 0.14, 0.11, 0.07, 0.0], n=6)
    bm_tube(h, [(-0.3, -0.02, 0.28), (-0.56, -0.1, 0.4), (-0.76, -0.07, 0.57), (-0.82, 0.0, 0.7)], [0.16, 0.14, 0.11, 0.09], n=6)
    bm_crystal(h, (-0.8, -0.02, 0.66), (-0.9, 0.06, 0.86), 0.05, n=4, shoulder=0.3)
    for sx in (-1, 1):
        bm_lump(b, random.Random(3 + sx), (sx * 0.31, -0.03, 0.27), 0.2, squash=(0.9, 0.9, 0.55), rot=(0, sx * 40, 0), n=10)


def build_head():
    col = collection("Bone_colossus")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=CS)
    rnd = random.Random(7)
    k = Kit()
    E = lambda name, **kw: k.emit(name, col, rig=rig, scale=CS, **kw)
    # ---- pelvis: a broad yoke of bone, the hip sockets under it
    xs = [(-0.52, 1.31, 0.1, 0.13), (-0.42, 1.27, 0.2, 0.22), (-0.2, 1.2, 0.19, 0.17), (0.0, 1.17, 0.17, 0.14),
          (0.2, 1.2, 0.19, 0.17), (0.42, 1.27, 0.2, 0.22), (0.52, 1.31, 0.1, 0.13)]
    bm_loft(k[BONE], [oval((x, -0.07, z), (0, 1, 0), (0, 0, 1), ry, rz, 8, power=2.4, phase=0.5) for x, z, ry, rz in xs])
    for s in (-1, 1):
        bm_lump(k[BONE_OLD], rnd, HIP[s], 0.2, n=11)
    bm_crystal(k[BONE], (0, -0.2, 1.16), (0, -0.36, 0.95), 0.08, n=4, shoulder=0.3)
    E("Head_Pelvis", bone="hips", vary=0.04)
    # ---- the spine: a dark cord strung with knuckled vertebrae, a ridge of spines down the back
    bm_tube(k["taupe_dark:0.3:0.9"], SPINE, 0.085, n=6)
    for i, p in enumerate(SPINE):
        p = Vector(p)
        tan = (Vector(SPINE[min(i + 1, len(SPINE) - 1)]) - Vector(SPINE[max(i - 1, 0)])).normalized()
        back = Vector((0, -tan.z, tan.y))
        back = back if back.y < 0 else -back
        bm_lump(k[BONE], rnd, p, 0.145 if i < 6 else 0.125, squash=(1.25, 1.0, 0.8), rot=(math.degrees(math.atan2(tan.y, tan.z)), 0, 0), n=10)
        if SPIKES[i] > 0:
            d = (back * 0.9 + tan * 0.45).normalized()
            bm_crystal(k[BONE_DARK], p + back * 0.06, p + d * (SPIKES[i] + 0.1), 0.065, n=4, shoulder=0.25)
    E("Head_Spine", bones=["hips", "spine", "chest", "neck"], vary=0.05)
    # ---- the cage of ribs, the breastbone, collarbones and shoulder blades
    t = Kit()
    for jr, ((rx, ry), aend) in enumerate(zip(((0.5, 0.4), (0.6, 0.47), (0.63, 0.5), (0.58, 0.47), (0.5, 0.42)), (165, 165, 160, 136, 112))):
        zc = 2.3 - 0.165 * jr
        for sx in (-1, 1):
            pts = []
            for q in range(6):
                ph = math.radians(14 + (aend - 14) * q / 5.0)
                pts.append((sx * rx * math.sin(ph), 0.04 - ry * math.cos(ph), zc - 0.2 * (math.degrees(ph) / 165.0) ** 1.3))
            bm_tube(t[BONE], pts, [0.062, 0.064, 0.062, 0.058, 0.052, 0.042], n=5)
    bm_beam(t[BONE_OLD], (0, 0.5, 2.24), (0, 0.5, 1.7), 0.26, 0.085, w1=0.1, h1=0.06, up=(0, 1, 0))
    bm_lump(t[BONE_OLD], rnd, (0, 0.49, 2.24), 0.15, squash=(1.2, 0.6, 0.8), n=10)
    stamp(k, t, Matrix.Translation((0, -0.3, 1.95)) @ Matrix.Rotation(math.radians(-9), 4, "X") @ Matrix.Translation((0, 0.3, -1.95)))
    for s in (-1, 1):
        bm_bone(k[BONE], (s * 0.1, 0.5, 2.32), (s * 0.84, 0.03, 2.44), 0.06, n=5)
        bm_lump(k[BONE_OLD], rnd, (s * 0.48, -0.36, 2.16), 0.31, squash=(0.95, 0.4, 1.15), rot=(8, 0, s * 18), n=12)
    E("Head_Ribs", bone="chest", vary=0.045)
    # ---- the soul burning in the cage
    bm_blob(k[glow(SOULCORE, 0.8)], rnd, (0, 0.02, 1.84), 0.2, squash=(1.0, 0.9, 1.1), jitter=0.12)
    bm_flame(k[glow(SOULFIRE, 0.7)], rnd, (0, 0.02, 1.7), h=0.66, r=0.27, n=5)
    E("Head_Soul", bone="core")
    # ---- neck guard, the skull, its jaw, its burning eyes
    sk, sj, se = Kit(), Kit(), Kit()
    _hero_skull(sk, sj, se)
    stamp(k, sk, SKULL_M)
    skull_o = E("Head_Skull", bone="skull")
    inv = SKULL_M.inverted()
    for o in skull_o:
        if o.name.endswith("_cream"):                       # war paint: a broad stripe over the crown, bars under the eyes
            def paintable(c, n):
                p = inv @ (c / CS)
                return (p.z > 0.2 and abs(p.x) < 0.125 and p.y < 0.3 and n.length > 0) or \
                       (0.18 < abs(p.x) < 0.33 and 0.3 < p.y and -0.3 < p.z < -0.12)
            paint_faces(o, "team", paintable, team=True, lo=0.1, hi=0.7)
    stamp(k, sj, SKULL_M)
    E("Head_Jaw", bone="jaw")
    stamp(k, se, SKULL_M)
    E("Head_Eyes", bone="eyes")
    # ---- shoulders: plates of bone lapped over each other, horn spurs standing from them
    for nme, s in SIDES:
        bm_lump(k[BONE_OLD], rnd, SHO[s] + Vector((s * 0.04, -0.02, 0.2)), 0.46, squash=(1.0, 0.95, 0.42), rot=(0, s * 16, 0), n=14)
        bm_lump(k[BONE_OLD], rnd, SHO[s] + Vector((s * 0.3, 0.0, -0.02)), 0.36, squash=(1.0, 0.95, 0.45), rot=(0, s * 52, 0), n=12)
        for (dx, dy, dz), (tx, ty, tz), r in (((0.0, -0.1, 0.3), (0.12, -0.2, 0.74), 0.085), ((0.2, 0.12, 0.24), (0.42, 0.2, 0.58), 0.07),
                                              ((-0.16, 0.14, 0.3), (-0.2, 0.26, 0.6), 0.06)):
            bm_crystal(k[BONE_DARK], SHO[s] + Vector((s * dx, dy, dz)), SHO[s] + Vector((s * tx, ty, tz)), r, n=5, shoulder=0.25)
        E("Head_Pauld." + nme, bone="pauld." + nme, vary=0.05)
    # ---- arms: a thick upper bone and its mate, a forearm of bundled bones and skulls, a knuckled fist
    for nme, s in SIDES:
        a1, a2, hnd = "arm.%s.1" % nme, "arm.%s.2" % nme, "hand." + nme
        bm_bone(k[BONE], SHO[s] + Vector((0, 0.02, -0.04)), ELB[s], 0.14, n=6, knob=1.5)
        bm_bone(k[BONE_OLD], SHO[s] + Vector((s * 0.02, -0.17, -0.12)), ELB[s] + Vector((0, -0.14, 0.06)), 0.085, n=5, knob=1.5)
        bm_lump(k[BONE], rnd, SHO[s], 0.25, n=11)
        _band(k[RUST], SHO[s], ELB[s], 0.5, 0.24, 0.08)
        E("Head_Arm.%s.1" % nme, bone=a1, vary=0.04)
        bm_tube(k["taupe_dark:0.3:0.9"], [SHO[s].lerp(ELB[s], 0.7), ELB[s], ELB[s].lerp(WRI[s], 0.3)], [0.15, 0.2, 0.17], n=7)
        bm_lump(k[BONE], rnd, ELB[s] + Vector((s * 0.03, -0.05, 0.0)), 0.21, n=11)
        E("Head_Elbow." + nme, bones=[a1, a2])
        fa = (WRI[s] - ELB[s]).normalized()
        out = Vector((s, 0, 0)) - fa * fa.x * s
        out.normalize()
        _bundle(k, rnd, ELB[s], WRI[s], 6, 0.17, 0.078, 0.2)
        bm_crystal(k[BONE_DARK], ELB[s] + Vector((0, -0.1, 0.02)), ELB[s] + Vector((s * 0.06, -0.38, 0.2)), 0.085, n=5, shoulder=0.25)
        _band(k[RUST], ELB[s], WRI[s], 0.2, 0.3, 0.075)
        _band(k[TEAM], ELB[s], WRI[s], 0.74, 0.335, 0.22)
        _band(k[RUST], ELB[s], WRI[s], 0.93, 0.33, 0.06)
        skull(k, frame(ELB[s].lerp(WRI[s], 0.46) + out * 0.23, out, up=-fa), s=0.27, bone=BONE_OLD, detail=1, jaw=False)
        E("Head_Arm.%s.2" % nme, bone=a2, vary=0.05)
        # the fist, built along the hand: +Y to the knuckles, +Z its back
        t = Kit()
        bm_lump(t[BONE], rnd, (0, 0.33, 0.0), 0.36, squash=(1.08, 1.0, 0.86), n=15)
        bm_lump(t[BONE_OLD], rnd, (0, 0.0, 0.0), 0.24, n=10)
        for i in range(4):
            x = (i - 1.5) * 0.165
            bm_tube(t[BONE], [(x, 0.4, 0.2), (x, 0.66, -0.02), (x, 0.47, -0.3), (x, 0.24, -0.24)], [0.095, 0.105, 0.09, 0.075], n=5)
            bm_lump(t[BONE_OLD], rnd, (x, 0.47, 0.22), 0.115, n=9)
        bm_tube(t[BONE], [(-s * 0.3, 0.16, -0.02), (-s * 0.37, 0.46, -0.1), (-s * 0.2, 0.66, -0.2)], [0.1, 0.1, 0.075], n=5)
        for x in (-0.085, 0.085):
            bm_crystal(t[BONE_DARK], (x, 0.52, 0.24), (x * 1.3, 0.8, 0.36), 0.06, n=4, shoulder=0.25)
        stamp(k, t, frame(WRI[s], KNU[s] - WRI[s]))
        E("Head_Hand." + nme, bone=hnd, vary=0.05)
    # ---- legs: short and bowed, a three-clawed foot
    for nme, s in SIDES:
        l1, l2, ft = "leg.%s.1" % nme, "leg.%s.2" % nme, "foot." + nme
        bm_bone(k[BONE], HIP[s], KNEE[s], 0.15, n=6, knob=1.45)
        bm_bone(k[BONE_OLD], HIP[s] + Vector((-s * 0.14, 0.02, 0.0)), KNEE[s] + Vector((-s * 0.13, -0.04, 0.02)), 0.085, n=5, knob=1.5)
        _band(k[RUST], HIP[s], KNEE[s], 0.55, 0.235, 0.07)
        E("Head_Leg.%s.1" % nme, bone=l1, vary=0.04)
        bm_tube(k["taupe_dark:0.3:0.9"], [HIP[s].lerp(KNEE[s], 0.7), KNEE[s], KNEE[s].lerp(ANK[s], 0.3)], [0.15, 0.19, 0.16], n=7)
        bm_lump(k[BONE], rnd, KNEE[s] + Vector((0, 0.04, 0.0)), 0.21, n=11)
        bm_crystal(k[BONE_DARK], KNEE[s] + Vector((0, 0.1, 0.06)), KNEE[s] + Vector((s * 0.05, 0.34, 0.26)), 0.085, n=5, shoulder=0.25)
        E("Head_Knee." + nme, bones=[l1, l2])
        _bundle(k, rnd, KNEE[s], ANK[s], 3, 0.13, 0.075, 0.13, twist=30, flare=1.25)
        _band(k[RUST], KNEE[s], ANK[s], 0.62, 0.225, 0.06)
        E("Head_Leg.%s.2" % nme, bone=l2, vary=0.05)
        bm_lump(k[BONE], rnd, ANK[s], 0.2, n=11)
        bm_lump(k[BONE_OLD], rnd, ANK[s] + Vector((0, -0.17, -0.1)), 0.15, n=9)
        for ang in (-30, 0, 28):
            d = Vector((math.sin(math.radians(ang)) + s * 0.1, math.cos(math.radians(ang)), 0)).normalized()
            base = ANK[s] + Vector((0, 0.03, -0.06))
            end = base + d * 0.42 + Vector((0, 0, -0.085))
            bm_tube(k[BONE], [base, base + d * 0.24 + Vector((0, 0, -0.03)), end], [0.11, 0.105, 0.08], n=5)
            bm_crystal(k[BONE_DARK], end - d * 0.02, end + d * 0.2 + Vector((0, 0, -0.05)), 0.07, n=4, shoulder=0.3)
        E("Head_Foot." + nme, bone=ft, vary=0.05)
    # ---- the team's colors: a ragged half-cape off the right shoulder, a loincloth fore and aft
    lean = Matrix.Translation((0, CAPE_Y, CAPE_Z)) @ Matrix.Rotation(-math.atan2(-CAPE_DIR[1], -CAPE_DIR[2]), 4, "X") @         Matrix.Translation((0, -CAPE_Y, -CAPE_Z))
    for nme, (x0, x1, ln, rows, tat) in CAPES.items():
        t = bmesh.new()
        bm_cloth(t, (x0, CAPE_Y, CAPE_Z), (x1, CAPE_Y, CAPE_Z), ln, cols=4, rows=rows, wave=0.06, tatter=tat, rnd=rnd, th=0.016, taper=0.1)
        bm_merge(k[TEAM], t, lean)
        k.emit("Head_" + nme.capitalize(), col, rig=rig, bones=["%s.%d" % (nme, i + 1) for i in range(3)], scale=CS)
    for nme, (x0, x1, ln, rows, tat) in CAPES.items():      # their hangers
        bm_bone(k[BONE_DARK], (x0 - 0.03, CAPE_Y, CAPE_Z + 0.02), (x1 + 0.03, CAPE_Y, CAPE_Z + 0.02), 0.045, n=4)
    E("Head_Yoke", bone="chest")
    for nme, (tp, dr, ln) in TABS.items():
        flag_part("Head_" + nme.capitalize(), col, rig, nme, tp, dr, ln, 0.48, segs=2, swatch="team!", tail="point", scale=CS, hang=(1, 0, 0))
    bm_beam(k[RUST], (-0.3, 0.2, 1.13), (0.3, 0.2, 1.13), 0.07, 0.09)
    bm_beam(k[RUST], (-0.3, -0.3, 1.15), (0.3, -0.3, 1.15), 0.07, 0.09)
    skull(k, frame((0, 0.27, 1.15), (0, 1, -0.15)), s=0.24, bone=BONE_OLD, detail=1, jaw=False)
    E("Head_Belt", bone="hips")
    empty("Muzzle", col, head, (0, 1.4 * CS, 0.35 * CS), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
RUN_LEN = 16
FIRE_LEN = 24
HIT = 9                         # the frame the fists land (0.3 s)


def pose(fk, hips=(0, 0, 0), lean=0.0, yaw=0.0, roll=0.0, bend=0.0, chest=0.0, twist=0.0, breathe=1.0, look=0.0, nod=0.0, jaw=0.0,
         hands=None, poles=None, fist=0.0, feet=None, toes=None, core=1.0, eyes=1.0, cloth=0.0, sweep=0.0, flutter=1.0):
    """lean / bend / chest: degrees forward at the hips, the spine and the chest; hands / feet: {side: where the wrist
    / ankle goes (None: it hangs from the body as in the rest pose)}; poles: {side: which way the elbow points};
    toes: {side: degrees the foot points down}; cloth: its sway phase; sweep: degrees it streams back."""
    R = Fk.rot
    fk.clear()
    fk.put("hips", R((0, 0, 1), yaw) @ R((0, 1, 0), roll) @ R((1, 0, 0), -lean), hips)
    fk.put("spine", R((1, 0, 0), -bend))
    fk.put("chest", R((0, 0, 1), twist) @ R((1, 0, 0), -chest), scale=breathe)
    fk.put("neck", R((0, 0, 1), look * 0.4) @ R((1, 0, 0), -nod * 0.5))
    fk.put("skull", R((0, 0, 1), look * 0.6) @ R((1, 0, 0), -nod * 0.5))
    fk.put("jaw", R((1, 0, 0), jaw))
    fk.put("core", scale=core)
    fk.put("eyes", scale=eyes)
    cq = fk.D("chest").to_quaternion()
    for n, s in SIDES:
        a1, a2 = "arm.%s.1" % n, "arm.%s.2" % n
        tgt = hands.get(s) if hands else None
        if tgt is None:
            tgt = fk.at("chest", WRI[s])
        fk.ik(a1, a2, tgt, pole=(poles or {}).get(s))
        fk.put("hand." + n, R((1, 0, 0), fist))
        ref = cq @ (ELB[s] - SHO[s])                        # the shoulder plates follow the arm halfway
        now = fk.tail(a1) - fk.head(a1)
        part = Quaternion().slerp(ref.rotation_difference(now), 0.5)
        fk.put("pauld." + n, cq.inverted() @ part @ cq)
        l1, l2 = "leg.%s.1" % n, "leg.%s.2" % n
        ank = feet.get(s) if feet else None
        ank = ANK[s] if ank is None else Vector(ank)
        fk.ik(l1, l2, ank)
        drop = (toes or {}).get(s, 0.0)
        heel = fk.head("foot." + n)
        d = Quaternion((1, 0, 0), math.radians(-drop)) @ (TOE[s] - ANK[s])
        fk.aim("foot." + n, heel + d, side=(1, 0, 0), side0=(1, 0, 0))
    pb = fk.pb
    for name, segs, amp in (("cape", 3, 1.0), ("capl", 3, 1.2), ("tabf", 2, 0.7), ("tabb", 2, 0.8)):
        back = -1.0 if name == "tabf" else 1.0
        for i in range(segs):
            b = pb["%s.%d" % (name, i + 1)]
            a = (5.0 + 4.0 * i) * amp * flutter * math.sin(2 * math.pi * (cloth - 0.17 * i) + (1.3 if name == "capl" else 0.0)) +                 (sweep * (0.55 if i == 0 else 0.25)) * back
            if name == "tabf":
                a = max(a, -6.0) if sweep == 0 else a
            b.rotation_quaternion = arm_space_quat(b, (1, 0, 0), a)


def _idle(f):
    """The idle's pose at frame f: it breathes, shifts its weight, looks about, works its jaw, flexes its fists."""
    ph = 2 * math.pi * f / IDLE_LEN
    chatter = pulse(f, 58, 62, 76) * (0.5 + 0.5 * math.sin(f * 2.4))
    sway = math.sin(ph)
    return dict(hips=(0.06 * sway, 0, -0.035 * (0.5 - 0.5 * math.cos(2 * ph))), roll=2.6 * sway, lean=2.2 * math.sin(2 * ph),
                chest=3.2 * math.sin(2 * ph - 0.6), twist=4.5 * math.sin(ph + 0.4), breathe=1.0 + 0.028 * math.sin(2 * ph),
                look=22 * math.sin(ph + 0.6), nod=5 * math.sin(2 * ph + 1.0) + 3 - 10 * chatter, jaw=4 + 3 * math.sin(2 * ph) + 22 * chatter,
                fist=8 * math.sin(2 * ph + 1.0), core=1.0 + 0.1 * math.sin(4 * ph) + 0.06 * math.sin(7 * ph),
                eyes=1.0 + 0.2 * math.sin(6 * ph) + 0.1 * math.sin(11 * ph), cloth=2.0 * f / IDLE_LEN)


def build_anims():
    rig = bpy.data.objects["Rig"]
    fk = Fk(rig)
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(fk, **_idle(f))
        key_pose(rig, f)
    new_action(rig, "run", RUN_LEN)
    for f in range(RUN_LEN + 1):
        pose(fk, **_run(fk, f / RUN_LEN))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    base = _idle(0)
    for f in range(FIRE_LEN + 1):
        # 0-5: it rears back, both fists heaved over its head; 6-9: they come down (the blow: frame 9); then it hangs
        # over the crater, roaring, and straightens up into the idle's first pose
        up = pulse(f, 0, 5, HIT)
        dn = smooth((f - 6) / (HIT - 6.0)) * (1.0 - smooth((f - 14) / 9.5))
        calm = 1.0 - min(1.0, up + dn)
        jolt = math.sin(math.pi * min(max((f - HIT) / 5.0, 0.0), 1.0))
        hands, poles = {}, {}
        for s in (-1, 1):
            rest = WRI[s]
            p = rest.lerp(Vector((s * 0.42, 0.22, 3.34)), up).lerp(Vector((s * 0.3, 1.26, 0.64)), dn)
            if up + dn < 0.02:
                p = None
            hands[s] = p
            poles[s] = Vector((s, -0.45, 0.25)) if up + dn > 0.02 else None
        pose(fk, hips=Vector(base["hips"]) * calm + Vector((0, -0.13 * up + 0.4 * dn, 0.1 * up - 0.3 * dn - 0.05 * jolt)),
             roll=base["roll"] * calm, lean=base["lean"] * calm - 14 * up + 24 * dn, bend=-9 * up + 15 * dn,
             chest=base["chest"] * calm - 12 * up + 11 * dn, twist=base["twist"] * calm, breathe=base["breathe"],
             look=base["look"] * calm, nod=base["nod"] * calm - 22 * up + 16 * dn - 8 * jolt, jaw=base["jaw"] + 30 * up + 34 * dn,
             hands=hands, poles=poles, fist=base["fist"] * calm - 18 * up + 6 * dn, core=base["core"] + 0.3 * up + 0.5 * dn,
             eyes=base["eyes"] + 0.7 * up + 0.6 * dn, cloth=3.0 * f / FIRE_LEN, sweep=-10 * up + 16 * dn, flutter=1.0 + 1.5 * (up + dn))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


def fk_hang(s):
    return WRI[s].copy()


def _run(fk, t):
    """The bound at phase t (0..1): at 0 it's stretched out, fists reaching forward and legs driving back; at 0.5 it's
    gathered, fists swung back and knees drawn up under it."""
    ph = 2 * math.pi * t
    reach = 0.5 + 0.5 * math.cos(ph)                # 1 stretched .. 0 gathered
    lift = math.sin(ph)
    lean = 30 + 9 * math.cos(ph)
    hz = -0.2 + 0.1 * math.cos(ph + 0.6)
    hips = Vector((0, 0.1, hz))
    hands, feet, poles, toes = {}, {}, {}, {}
    for s in (-1, 1):
        o = 0.5 + 0.5 * math.cos(ph - 0.5 * s)      # the two sides a little out of step
        sh = Vector((s * 0.9, 0.95, 1.9 + hz))      # (about where the shoulders ride)
        hands[s] = sh + Vector((s * 0.08, 0.95, -0.85)).lerp(Vector((s * 0.3, -0.55, -1.1)), 1.0 - o) + Vector((0, 0, 0.3 * max(0.0, math.sin(ph - 0.5 * s))))
        poles[s] = Vector((s, -0.6, 0.3))
        hp = Vector((s * 0.36, 0.1, 1.14 + hz))
        feet[s] = hp + Vector((s * 0.14, -0.78, -0.62)).lerp(Vector((s * 0.2, 0.5, -0.5)), 1.0 - o)
        toes[s] = 38 * o
    return dict(hips=hips, lean=lean, bend=9 + 6 * math.cos(ph), chest=4, nod=-24 - 6 * math.cos(ph), jaw=14 + 6 * lift,
                hands=hands, poles=poles, feet=feet, toes=toes, fist=10 * lift, core=1.1, eyes=1.25,
                cloth=t, sweep=34, flutter=1.6)


PREVIEW = {"target": (0, 0.1, 1.3), "dist": 11.0, "yaw": 150, "pitch": 20, "anim_target": (HOME.x, HOME.y + 0.5, 1.75), "anim_dist": 7.8,
           "frames": [("idle", 0), ("run", 0), ("run", 8), ("fire", 5), ("fire", 9)],
           "extra": [{"yaw": 152, "pitch": 6, "dist": 4.6, "target": (HOME.x, HOME.y + 0.5, STAND + 2.45)},
                     {"yaw": 20, "pitch": 34, "dist": 8.0, "target": (HOME.x, HOME.y, 1.5)},
                     {"yaw": 0, "pitch": 57, "dist": 9.0, "target": (1.0, -0.6, 0.4)},
                     {"yaw": 200, "pitch": 30, "dist": 8.5, "target": (-0.6, 0.6, 0.7)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
