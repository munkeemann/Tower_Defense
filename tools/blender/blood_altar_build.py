"""Builds the Blood Altar (footprint "pair": [0,0] front, [0,1] back), the Bone Legion's Tier IV support tower: the
towers around it deal more damage and attack faster, and after every wave it drinks castle health. Aura: it only
ever plays idle and nothing aims.

    python tools/blender/build.py blood_altar --out <preview dir>

One sacrificial altar. A stepped dais of black stone covers both cells; on the front cell a raised platform carries
a carved black altar (blind lancet arcades, corner colonnettes, a row of skulls under its heavy top slab) with a
basin of blood on it and the team's altar cloths hung down its back and front. Four tall black pillars stand at
the platform's corners, thorned with iron spikes and crowned with them, each carrying a cresset of red fire; heavy
chains run from their crowns to an iron ring over the altar, and from the ring hangs a great blood crystal that turns
over the basin and drips into it. Two channels carry the blood from the basin's spouts down the altar and the steps
across the waist into a blood sigil inlaid in the floor of the back cell, ringed with candles.
Idle (rich, it's all this tower does): the crystal turns and pulses, drops form on its point, fall and splash in the
basin, the fires flicker, the sigil breathes and a ripple runs out through it, the team banners stir.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

TID = "blood_altar"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # front: the altar
B = hex_to_world(0, 1, MID)          # back: the sigil
TOP = 0.34
T = TOP
Z1 = T + 0.15                        # the lower tier (both cells)
Z2 = Z1 + 0.17                       # the altar's platform
PLX, PLY = 0.64, 0.48                # the platform's half sizes
AX, AY = 0.38, 0.24                  # the altar body's half sizes
AH = 0.62                            # its height (to under the top slab)
ATOP = Z2 + AH + 0.1                 # the top slab's top
PILLARS = [Vector((sx * 0.6, F.y + sy * 0.46, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
PTOP = 2.9                           # the pillars' capitals
RING = Vector((F.x, F.y, 2.86))      # the iron ring the crystal hangs from
CZ = 2.3                             # the crystal's middle
CBOT = CZ - 0.36                     # its point
BASIN = ATOP + 0.08                  # the blood's surface in the basin
SG = Vector((0.0, -0.98, 0.0))       # the sigil's middle (back cell)
SGR = 0.7
CHX = 0.2                            # the channels run this far either side of the middle
FIRE_Z = 2.02
BLOOD2 = (0.8, 0.0, 0.03)            # deep red (BLOOD itself washes out to salmon)
HOT = (1.0, 0.12, 0.08)              # the crystal's brighter flanks, splashes
FLAME = (0.95, 0.04, 0.02)
DROPS = 3


def _yaw_to(dx, dy):
    return math.degrees(math.atan2(-dx, dy))


def _seg_d(p, a, b):
    p, a, b = Vector((p[0], p[1], 0)), Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    ab = b - a
    t = min(max((p - a).dot(ab) / max(ab.length_squared, 1e-9), 0.0), 1.0)
    return (a + ab * t - p).length


def _circle(bm, c, r, w, n, z, gap=0.02, skip=None):
    c = Vector(c)
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n + gap / r, 2 * math.pi * (i + 1) / n - gap / r
        if skip and skip(math.degrees((a0 + a1) / 2) % 360):
            continue
        bm_beam(bm, (c.x + math.cos(a0) * r, c.y + math.sin(a0) * r, z), (c.x + math.cos(a1) * r, c.y + math.sin(a1) * r, z), w, 0.02)


def _channel_path(x):
    """The (y, z) points one channel follows: off the basin's spout, down the altar's back, across the platform,
    down its riser and across the lower tier to the sigil's rim."""
    rim = SG.y + math.sqrt(SGR * SGR - x * x)
    return [(F.y - AY - 0.02, ATOP - 0.06), (F.y - AY - 0.02, Z2 + 0.08), (F.y - AY - 0.06, Z2 + 0.012), (F.y - PLY - 0.02, Z2 + 0.012),
            (F.y - PLY - 0.04, Z1 + 0.012), (rim, Z1 + 0.012)]


def build_base():
    col = collection("Blood_altar")
    root = empty("Blood_altar", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(13)
    k = Kit()
    # ---- the dais: a lower tier over both cells, the altar's platform on the front cell
    t1 = outline(CELLS, 0.17)
    plat = gs_rect(F.x, F.y, PLX, PLY)
    gs_step(k, rnd, t1, T, Z1, stone="black:0.1:0.5", core="black:0.4:0.8", block=0.42, th=0.2)
    gs_step(k, rnd, plat, Z1 - 0.02, Z2, stone="black:0.05:0.45", core="black:0.4:0.8", block=0.36, th=0.18)
    k.emit("Dais", col, root, bevel=0.012, vary=0.08)
    t1_in = outline(CELLS, 0.34)
    chans = [(sx * CHX, _channel_path(sx * CHX)) for sx in (-1, 1)]

    def flags1(x, y):
        if not inside(t1_in, x, y) or (abs(x - F.x) < PLX + 0.04 and abs(y - F.y) < PLY + 0.04):
            return False
        if abs(math.hypot(x - SG.x, y - SG.y) - SGR) < 0.08 or math.hypot(x - SG.x, y - SG.y) < SGR - 0.06:
            return False
        return all(abs(x - cx) > 0.08 or y > F.y - PLY for cx, _ in chans)
    bm_flagstones(k["stone_dark:0.3:0.85"], rnd, flags1, (-1.3, -2.2, 1.3, 2.2), Z1 - 0.012, size=0.27, gap=0.035, keep=0.95)
    bm_flagstones(k["stone_dark:0.25:0.8"], rnd, lambda x, y: abs(x - F.x) < PLX - 0.2 and abs(y - F.y) < PLY - 0.2 and
                  not (abs(x - F.x) < AX + 0.1 and abs(y - F.y) < AY + 0.1), (-1, 0, 1, 2), Z2 - 0.012, size=0.22, gap=0.03, keep=1.0)
    # the sigil's floor: one dark disc, the glowing lines lie on it
    bm_cyl(k["black:0.5:0.9"], SGR + 0.06, SGR + 0.06, 0.03, (SG.x, SG.y, Z1 - 0.005), seg=24)
    k.emit("Paving", col, root, vary=0.1)
    # ---- the altar: plinth, body, lancet arcades, colonnettes, skulls under a heavy top slab, the basin
    ak = k["black:0.0:0.45"]
    bm_box(ak, (2 * AX + 0.14, 2 * AY + 0.14, 0.08), (F.x, F.y, Z2 + 0.04))
    bm_box(ak, (2 * AX, 2 * AY, AH - 0.08), (F.x, F.y, Z2 + 0.08 + (AH - 0.08) / 2))
    bm_box(ak, (2 * AX + 0.16, 2 * AY + 0.16, 0.1), (F.x, F.y, ATOP - 0.05))
    bm_box(ak, (2 * AX + 0.06, 2 * AY + 0.06, 0.04), (F.x, F.y, ATOP - 0.12))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_cyl(ak, 0.045, 0.045, AH - 0.12, (F.x + sx * AX, F.y + sy * AY, Z2 + 0.08 + (AH - 0.12) / 2), seg=6)
    k.emit("Altar", col, root, bevel=0.01, vary=0.05)
    for sy in (-1, 1):                                          # blind lancets on the long faces
        for x in (-0.24, 0.0, 0.24):
            if sy < 0 and abs(x) < 0.1:
                continue                                        # (the cloth hangs there)
            gs_pointed_arch(k["stone_dark:0.0:0.5"], (F.x + x, F.y + sy * (AY + 0.012), Z2 + 0.14), (1, 0, 0), 0.12, 0.16, th=0.035, depth=0.03,
                            n=3, k=0.9, sill=0.03)
    for sx in (-1, 1):
        gs_pointed_arch(k["stone_dark:0.0:0.5"], (F.x + sx * (AX + 0.012), F.y, Z2 + 0.14), (0, 1, 0), 0.14, 0.16, th=0.035, depth=0.03, n=3, k=0.9, sill=0.03)
    k.emit("Altar_Arcades", col, root)
    for sy in (-1, 1):
        for x in (-0.24, 0.0, 0.24):
            if sy < 0 and abs(x) < 0.1:
                continue
            gs_skull(k, place((F.x + x, F.y + sy * (AY + 0.02), ATOP - 0.25), yaw=_yaw_to(0, sy), scale=0.13), n=6)
    k.emit("Altar_Skulls", col, root, vary=0.05)
    gs_lathe(k["black:0.05:0.5"], (F.x, F.y, ATOP), [(0.2, 0.0), (0.27, 0.06), (0.3, 0.12), (0.27, 0.13), (0.24, 0.07)], n=12, cap0=True, cap1=True)
    for sx in (-1, 1):                                          # the spouts at the basin's back
        bm_beam(k["black:0.05:0.5"], (F.x + sx * CHX * 0.8, F.y - 0.18, ATOP + 0.06), (F.x + sx * CHX, F.y - AY - 0.08, ATOP - 0.02), 0.07, 0.05)
    k.emit("Basin", col, root, vary=0.04)
    bl = k[glow(BLOOD2, 0.5)]
    bm_cyl(bl, 0.245, 0.245, 0.02, (F.x, F.y, BASIN - 0.01), seg=12)
    k.emit("Basin_Blood", col, root)
    gs_skull(k, place((F.x + 0.08, F.y + 0.06, BASIN - 0.1), yaw=150, pitch=60, scale=0.14), n=6)
    k.emit("Basin_Skull", col, root)
    # ---- the channels, the sigil, the candles round it
    ch = k[glow(BLOOD2, 0.65)]
    kb = k["black:0.0:0.4"]
    for x, path in chans:
        for (y0, z0), (y1, z1) in zip(path, path[1:]):
            d = Vector((0, y1 - y0, z1 - z0))
            n = Vector((0, -d.z, d.y)).normalized()
            bm_beam(ch, Vector((F.x + x, y0, z0)) + n * 0.006, Vector((F.x + x, y1, z1)) + n * 0.006, 0.05, 0.02, up=tuple(n))
            for s in (-1, 1):
                bm_beam(kb, Vector((F.x + x + s * 0.045, y0, z0)) + n * 0.012, Vector((F.x + x + s * 0.045, y1, z1)) + n * 0.012, 0.03, 0.035, up=tuple(n))
    k.emit("Channels", col, root)
    for i in range(7):                                          # candles round the sigil
        a = math.radians(-90 + 360 * (i + 0.5) / 7)
        if abs(math.degrees(a) % 360 - 90) < 30:
            continue
        p = SG + Vector((math.cos(a), math.sin(a), 0)) * (SGR + 0.13)
        if not in_footprint(CELLS, p.x, p.y, 0.3):
            continue
        for j in range(2):
            q = p + Vector((math.cos(a + 1.6 * j), math.sin(a + 1.6 * j), 0)) * 0.05 * j
            gs_candle(k, (q.x, q.y, Z1), h=0.13 - 0.04 * j, r=0.032, flame=glow((1.0, 0.3, 0.12), 0.8))
    k.emit("Candles", col, root)
    # ---- the pillars: black shafts on stepped bases, iron thorns up them, a crown of spikes, a cresset each
    for p in PILLARS:
        bm_box(k["black:0.0:0.45"], (0.3, 0.3, Z2 + 0.2 - Z1), (p.x, p.y, (Z1 + Z2 + 0.2) / 2))
        bm_box(k["black:0.0:0.4"], (0.34, 0.34, 0.06), (p.x, p.y, Z2 + 0.2))
        bm_box(k["black:0.0:0.4"], (0.32, 0.32, 0.1), (p.x, p.y, PTOP + 0.05))
    k.emit("Pillar_Bases", col, root, bevel=0.012, vary=0.05)
    for p in PILLARS:
        rr = [Vector((p.x + x, p.y + y, 0)) for x, y in ((0.11, -0.07), (0.11, 0.07), (0.07, 0.11), (-0.07, 0.11), (-0.11, 0.07), (-0.11, -0.07), (-0.07, -0.11), (0.07, -0.11))]
        bm_loft(k["black:0.05:0.5"], [[v + Vector((0, 0, Z2 + 0.23)) for v in rr], [v * 0.9 + p * 0.1 + Vector((0, 0, PTOP)) for v in rr]])
    k.emit("Pillars", col, root)
    ir = k[IRON]
    for i, p in enumerate(PILLARS):
        out = Vector((p.x - F.x, p.y - F.y, 0)).normalized()
        sd = Vector((-out.y, out.x, 0))
        for j, z in enumerate((1.25, 1.65, 2.45)):
            for s in (-1, 1):
                d = (out * 0.7 + sd * (s * 0.7)).normalized()
                base = Vector((p.x, p.y, z + 0.1 * s * (j % 2)))
                bm_crystal(ir, base + d * 0.06, base + d * 0.24 + Vector((0, 0, 0.05)), 0.035, n=4, shoulder=0.3, foot=0.7)
        top = Vector((p.x, p.y, PTOP + 0.1))
        bm_crystal(ir, top, top + Vector((0, 0, 0.42)), 0.06, n=4, shoulder=0.3, foot=0.8)
        for s in range(4):
            a = math.radians(45 + 90 * s)
            d = Vector((math.cos(a), math.sin(a), 0))
            bm_crystal(ir, top + d * 0.1, top + d * 0.26 + Vector((0, 0, 0.24)), 0.04, n=4, shoulder=0.3, foot=0.7)
        c = Vector((p.x, p.y, FIRE_Z)) + out * 0.2                          # the cresset on an iron bracket
        bm_beam(ir, Vector((p.x, p.y, FIRE_Z - 0.18)) + out * 0.1, c - Vector((0, 0, 0.06)), 0.04, 0.04)
        bm_beam(ir, Vector((p.x, p.y, FIRE_Z - 0.02)) + out * 0.1, c - Vector((0, 0, 0.02)), 0.035, 0.035)
        gs_lathe(ir, tuple(c - Vector((0, 0, 0.06))), [(0.03, 0.0), (0.12, 0.06), (0.15, 0.13), (0.13, 0.13), (0.1, 0.07)], n=8, cap0=True, cap1=True)
    k.emit("Pillar_Iron", col, root)
    em = k[glow((0.95, 0.08, 0.03), 0.6)]
    for p in PILLARS:
        out = Vector((p.x - F.x, p.y - F.y, 0)).normalized()
        c = Vector((p.x, p.y, FIRE_Z)) + out * 0.2
        bm_cyl(em, 0.11, 0.11, 0.02, tuple(c + Vector((0, 0, 0.05))), seg=8)
    k.emit("Cresset_Coals", col, root)
    # ---- the chains from the crowns to the ring, the ring's cross
    for p in PILLARS:
        d = Vector((p.x - F.x, p.y - F.y, 0)).normalized()
        a = Vector((p.x, p.y, PTOP + 0.02)) - d * 0.17
        b = RING + d * 0.2
        gs_chain(k[IRON], a, b, sag=0.1, link=0.12, w=0.07, th=0.028)
    for s in (0, 1):
        a = math.radians(45 + 90 * s)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_beam(k[IRON], RING - d * 0.2, RING + d * 0.2, 0.04, 0.04)
    k.emit("Chains", col, root)
    ring(k["iron:0.1:0.7"], tuple(RING), 0.24, 0.18, -0.03, 0.03, seg=12)
    k.emit("Ring", col, root)
    head = empty("Head", col, root, (F.x, F.y, CZ), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0), 0.2, "SPHERE")
    return root


DROP_FALL = CBOT - (BASIN + 0.01)
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "crystal": ((F.x, F.y, CZ), (F.x, F.y, CZ + 0.3), "root"),
         "sigil": ((SG.x, SG.y, Z1), (SG.x, SG.y, Z1 + 0.2), "root"),
         "sring": ((SG.x, SG.y, Z1), (SG.x, SG.y, Z1 + 0.2), "root")}
for _i in range(DROPS):
    BONES["drop.%d" % (_i + 1)] = ((F.x, F.y, CBOT), (F.x, F.y, CBOT + 0.1), "root")
    BONES["ripple.%d" % (_i + 1)] = ((F.x, F.y, BASIN), (F.x, F.y, BASIN + 0.1), "root")
for _i, _p in enumerate(PILLARS):
    _o = Vector((_p.x - F.x, _p.y - F.y, 0)).normalized()
    _c = Vector((_p.x, _p.y, FIRE_Z + 0.03)) + _o * 0.2
    BONES["fire.%d" % (_i + 1)] = (tuple(_c), tuple(_c + Vector((0, 0, 0.2))), "root")
BAN = []
for _i in range(4):                                             # each pillar carries a team banner on its outer face
    _p = PILLARS[_i]
    _top = Vector((_p.x, _p.y + (0.165 if _p.y > F.y else -0.165), 1.58))
    BAN.append(_top)
    flag_bones(BONES, "ban%d" % (_i + 1), tuple(_top), (0, 0, -1), 0.74, segs=3)


def build_head():
    col = collection("Blood_altar")
    root = bpy.data.objects["Blood_altar"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(8)
    k = Kit()
    # ---- the blood crystal: a long six-sided double point under an iron cap, a short chain up to the ring
    c = Vector((F.x, F.y, CZ))
    bm_crystal(k[glow(BLOOD2, 0.8)], c, c + Vector((0, 0, 0.34)), 0.2, n=6, shoulder=0.35, foot=1.0)
    bm_crystal(k[glow(BLOOD2, 0.8)], c, Vector((F.x, F.y, CBOT)), 0.2, n=6, shoulder=0.2, foot=1.0)
    for i in range(3):                                          # smaller crystals grown on its flanks
        a = 2 * math.pi * i / 3 + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_crystal(k[glow(HOT, 0.75)], c + d * 0.1 - Vector((0, 0, 0.05)), c + d * 0.34 + Vector((0, 0, 0.14)), 0.06, n=5, shoulder=0.5, foot=0.6)
    k.emit("Crystal", col, rig=rig, bone="crystal")
    cap = c + Vector((0, 0, 0.3))
    gs_lathe(k[IRON], tuple(cap), [(0.15, 0.0), (0.12, 0.08), (0.05, 0.12), (0.035, 0.18)], n=6, cap0=True, cap1=True)
    gs_chain(k[IRON], cap + Vector((0, 0, 0.18)), RING - Vector((0, 0, 0.0)), sag=0.0, link=0.1, w=0.06, th=0.024)
    k.emit("Crystal_Cap", col, rig=rig, bone="crystal")
    for i in range(DROPS):
        bm_crystal(k[glow(BLOOD2, 0.8)], Vector((F.x, F.y, CBOT + 0.01)), Vector((F.x, F.y, CBOT - 0.1)), 0.035, n=5, shoulder=0.1, foot=0.5)
        bm_ellipsoid(k[glow(BLOOD2, 0.8)], (F.x, F.y, CBOT - 0.075), (0.04, 0.04, 0.045), u=6, v=4)
        k.emit("Drop%d" % (i + 1), col, rig=rig, bone="drop.%d" % (i + 1))
        ring(k[glow(HOT, 0.75)], (F.x, F.y, BASIN + 0.012), 0.2, 0.17, -0.008, 0.008, seg=12)
        k.emit("Ripple%d" % (i + 1), col, rig=rig, bone="ripple.%d" % (i + 1))
    for i, p in enumerate(PILLARS):
        out = Vector((p.x - F.x, p.y - F.y, 0)).normalized()
        gs_flame(k[glow(FLAME, 0.6)], tuple(Vector((p.x, p.y, FIRE_Z + 0.04)) + out * 0.2), h=0.4, r=0.1, rnd=rnd, tongues=3)
        k.emit("Fire%d" % (i + 1), col, rig=rig, bone="fire.%d" % (i + 1))
    # ---- the sigil in the back cell's floor: two rings, ticks, a triangle pointing at the altar, the eye
    g = k[glow(BLOOD2, 0.7)]
    z = Z1 + 0.025
    _circle(g, SG, SGR, 0.05, 30, z, skip=lambda a: any(abs(a - math.degrees(math.atan2(math.sqrt(SGR * SGR - CHX * CHX), sx * CHX))) < 7 for sx in (-1, 1)))
    _circle(g, SG, SGR - 0.15, 0.04, 26, z)
    for i in range(9):
        a = math.radians(90 + 360 * (i + 0.5) / 9)
        bm_beam(g, (SG.x + math.cos(a) * (SGR - 0.13), SG.y + math.sin(a) * (SGR - 0.13), z), (SG.x + math.cos(a) * (SGR - 0.02), SG.y + math.sin(a) * (SGR - 0.02), z), 0.035, 0.02)
    tri = [SG + Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)) * (SGR - 0.17) for a in (90, 210, 330)]
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        bm_beam(g, (a.x, a.y, z), (b.x, b.y, z), 0.05, 0.02)
        bm_beam(g, (a.x, a.y, z), (SG.x + (a.x - SG.x) * 0.3, SG.y + (a.y - SG.y) * 0.3, z), 0.035, 0.02)
    _circle(g, SG, 0.16, 0.04, 12, z)
    bm_cyl(g, 0.07, 0.07, 0.02, (SG.x, SG.y, z), seg=8)
    k.emit("Sigil", col, rig=rig, bone="sigil")
    _circle(k[glow(HOT, 0.75)], SG, 1.0, 0.05, 24, Z1 + 0.035)
    k.emit("Sigil_Ripple", col, rig=rig, bone="sring")
    # ---- the team banners on the back pillars, the altar cloths
    for i, top in enumerate(BAN):
        gs_banner(k["team!:0.1:0.75"], tuple(top), (1, 0, 0), (0, 0, -1), 0.3, 0.74, rnd=random.Random(30 + i), cols=4, rows=4, tatter=0.3)
        k.emit("Banner%d" % (i + 1), col, rig=rig, bones=["ban%d.%d" % (i + 1, j + 1) for j in range(3)])
        sg_ = 1 if top.y > F.y else -1
        gs_skull(k, place(tuple(top + Vector((0, sg_ * 0.012, -0.3))), yaw=0 if sg_ > 0 else 180, scale=0.14) @ Matrix.Diagonal((1.0, 0.25, 1.0, 1.0)), n=6)
        k.emit("Banner%d_Badge" % (i + 1), col, rig=rig, bones=["ban%d.%d" % (i + 1, j + 1) for j in range(3)])
    rod = k[IRON]
    for top in BAN:
        bm_beam(rod, top + Vector((-0.17, 0, 0.02)), top + Vector((0.17, 0, 0.02)), 0.03, 0.03)
        bm_beam(rod, top + Vector((0, 0.0, 0.02)), top - Vector((0, 0.06 * (1 if top.y > F.y else -1), -0.02)), 0.03, 0.03)
    k.emit("Banner_Rods", col, rig=rig, bone="root")
    tk = k["team!:0.1:0.7"]
    for sy in (-1, 1):                                          # the altar cloths: over the top slab's edge and down
        y = F.y + sy * (AY + 0.085)
        gs_banner(tk, (F.x, y, ATOP - 0.01), (sy, 0, 0), (0, sy * 0.05, -1), 0.3 if sy < 0 else 0.42, 0.5, rnd=random.Random(50 + sy), cols=4, rows=3, tatter=0.12)
        bm_box(tk, (0.3 if sy < 0 else 0.42, 0.18, 0.016), (F.x, F.y + sy * (AY + 0.0), ATOP + 0.006))
    k.emit("Altar_Cloth", col, rig=rig, bone="root")
    gk = k["gold:0.1:0.5"]
    for sy in (-1, 1):
        w = 0.3 if sy < 0 else 0.42
        bm_beam(gk, (F.x - w / 2, F.y + sy * (AY + 0.095), ATOP - 0.05), (F.x + w / 2, F.y + sy * (AY + 0.095), ATOP - 0.05), 0.012, 0.03)
        gs_skull(k, place((F.x, F.y + sy * (AY + 0.1), ATOP - 0.32), yaw=_yaw_to(0, sy), scale=0.13, ) @ Matrix.Diagonal((1.0, 0.25, 1.0, 1.0)), bone="gold:0.05:0.4", n=6)
    k.emit("Altar_Cloth_Gold", col, rig=rig, bone="root")
    return rig


IDLE_LEN = 96


def pose(rig, t):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    ph = 2 * math.pi * t
    cr = pb["crystal"]
    cr.rotation_quaternion = q(cr, (0, 0, 1), 360.0 * t)
    cr.location = arm_space_loc(cr, (0, 0, 0.03 * math.sin(2 * ph)))
    s = 1.0 + 0.06 * math.sin(3 * ph) + 0.05 * max(0.0, math.sin(6 * ph)) ** 4
    cr.scale = (s, s, s)
    for i in range(DROPS):
        u = (t - i / DROPS) % 1.0                               # 0..0.18 the drop swells on the point, 0.18..0.28 falls
        d, rp = pb["drop.%d" % (i + 1)], pb["ripple.%d" % (i + 1)]
        if u < 0.18:
            d.scale = (max(smooth(u / 0.18), 0.01),) * 3
        elif u < 0.28:
            v = (u - 0.18) / 0.1
            d.location = arm_space_loc(d, (0, 0, -DROP_FALL * v * v))
            d.scale = (0.85, 1.3, 0.85)
        else:
            d.location = arm_space_loc(d, (0, 0, -DROP_FALL))
            d.scale = (0.01, 0.01, 0.01)
        w = (u - 0.28) / 0.16
        rp.scale = ((0.25 + 0.85 * smooth(w)) if 0.0 <= w < 1.0 else 0.01,) * 3
        if 0.0 <= w < 1.0:
            rp.scale = (rp.scale[0], 1.0, rp.scale[2])
    for i in range(len(PILLARS)):
        f = 1.0 + 0.2 * math.sin(2 * math.pi * (6 * t + 0.31 * i)) + 0.12 * math.sin(2 * math.pi * (11 * t + 0.7 * i))
        b = pb["fire.%d" % (i + 1)]
        b.scale = (0.92 + 0.08 * f, f, 0.92 + 0.08 * f)
        b.rotation_quaternion = q(b, (0, 0, 1), 16 * math.sin(2 * math.pi * (3 * t + 0.25 * i)))
    sg = pb["sigil"]
    sv = 1.0 + 0.035 * math.sin(2 * ph)
    sg.scale = (sv, 1.0, sv)
    sr = pb["sring"]
    u = (t * 2) % 1.0                                           # a ripple runs out through the sigil twice a loop
    rr = 0.2 + 0.72 * smooth(u / 0.7) if u < 0.72 else 0.01
    sr.scale = (rr, 1.0 if u < 0.72 else 0.01, rr)
    for i in range(4):
        sway(rig, "ban%d" % (i + 1), 3.0, segs=3, axis=(1, 0, 0), lag=0.12, phase=2 * t + 0.4 * i)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.4), "dist": 9.6, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y - 0.2, 1.8), "anim_dist": 5.2,
           "frames": [("idle", 0), ("idle", 16), ("idle", 32), ("idle", 48), ("idle", 64), ("idle", 80)],
           "extra": [{"yaw": 165, "pitch": 12, "dist": 3.2, "target": (F.x, F.y, 1.9)},
                     {"yaw": 20, "pitch": 40, "dist": 4.0, "target": (0, -0.5, 0.6)},
                     {"yaw": 270, "pitch": 12, "dist": 7.0, "target": (0, 0, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
