"""Builds the Hex Tomb (footprint "fan4": [0,0] hub (back), [-1,0] left, [0,-1] front, [1,-1] right), a Bone Legion
aura tower: it curses nearby enemies so they take more damage from everything. It never turns.

    python tools/blender/build.py hex_tomb --out <preview dir>

One cursed tomb that is also a diagram drawn over all four cells. A dais of dark coursed stone covers the fan; in its
middle (where the four cells meet) a great stone sarcophagus lies sunk in a pit, its lid shoved ajar under a torn
team pall, violet light welling out of the gap and spilling down into the pit. Over it stand the ruins of a ribbed
vault: four piers, pointed arches (the right one broken, its stones fallen), one diagonal rib still whole with a skull
boss at its crown, the other snapped. High above hangs the hex: a seven-pointed star of violet light in a double
ring, turning slowly, an inner wheel turning against it. Four leaning cursed stelae, one out on each cell, each with
violet runes and a team rag tied round it, are joined to the pit by sigil lines inlaid in the cracked flagstones, and
to each other in a great lozenge, so the fan reads as one drawing.
Clips: idle (the star turns a seventh of a turn, the inner wheel the other way, the light in the tomb breathes, the
lid rattles once), fire (the star flashes and kicks round, a ring of light drops from it to the floor and rolls out
over the fan, the lid shudders).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

TID = "hex_tomb"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
HUB = hex_to_world(0, 0, MID)        # back
LEFT = hex_to_world(-1, 0, MID)
FRONT = hex_to_world(0, -1, MID)
RIGHT = hex_to_world(1, -1, MID)
TOP = 0.34
T = TOP
FZ = T + 0.28                        # the dais floor
PX, PY = 0.5, 0.72                   # the pit's half sizes
SX, SY, SH = 0.3, 0.58, 0.42         # the sarcophagus's half sizes and height
PIER = (0.74, 0.96)                  # the vault's piers (middles)
PW = 0.26
SPR_F, SPR_S = 0.78, 0.66            # where the front/back and the side arches spring (above the floor)
CROWN = FZ + 1.62                    # the ribs' crown
SZ = FZ + 2.12                       # the hex (star) in the air: the Head
SR = 1.05                            # its radius
VIO = (0.42, 0.12, 1.0)
PALE = (0.72, 0.5, 1.0)
STELAE = [Vector((0, -1.5, 0)), Vector((-2.05, 0, 0)), Vector((0, 1.5, 0)), Vector((2.05, 0, 0))]
LID_OFF, LID_ROT = Vector((0.06, 0.24, 0)), 11.0
GLYPHS = [[((0, 0), (0, 1)), ((0, 0.55), (-0.45, 1)), ((0, 0.55), (0.45, 1))],
          [((0, 0), (0, 1)), ((0, 1), (-0.45, 0.62)), ((0, 1), (0.45, 0.62))],
          [((-0.3, 0), (-0.3, 1)), ((0.3, 0), (0.3, 1)), ((-0.3, 0.68), (0.3, 0.32))],
          [((0, 0), (0.42, 0.5)), ((0.42, 0.5), (0, 1)), ((0, 1), (-0.42, 0.5)), ((-0.42, 0.5), (0, 0))],
          [((-0.25, 0), (-0.25, 1)), ((-0.25, 0.78), (0.32, 0.5)), ((0.32, 0.5), (-0.25, 0.22))],
          [((-0.35, 0), (-0.35, 1)), ((0.35, 0), (0.35, 1)), ((-0.35, 1), (0.35, 0.45)), ((0.35, 1), (-0.35, 0.45))]]


def _yaw_to(dx, dy):
    return math.degrees(math.atan2(-dx, dy))


def _seg_d(p, a, b):
    p, a, b = Vector((p[0], p[1], 0)), Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    ab = b - a
    t = min(max((p - a).dot(ab) / max(ab.length_squared, 1e-9), 0.0), 1.0)
    return (a + ab * t - p).length


def _cap_with_hole(bm, outer, hole, z):
    """A flat top over the outline `outer` with the rectangle `hole` left open (triangulated)."""
    from mathutils import geometry
    co = [Vector((p.x, p.y)) for p in outer] + [Vector((p.x, p.y)) for p in hole]
    n0, n1 = len(outer), len(hole)
    edges = [(i, (i + 1) % n0) for i in range(n0)] + [(n0 + i, n0 + (i + 1) % n1) for i in range(n1)]
    vs, _, fs, _, _, _ = geometry.delaunay_2d_cdt(co, edges, [], 1, 1e-5)
    verts = [bm.verts.new((p.x, p.y, z)) for p in vs]
    for f in fs:
        c = sum((vs[i] for i in f), Vector((0, 0))) / len(f)
        if inside(hole, c.x, c.y) or not inside(outer, c.x, c.y):
            continue
        face = bm.faces.new([verts[i] for i in f])
        face.normal_update()
        if face.normal.z < 0:
            face.normal_flip()


def _slab(bm, pts, th):
    """A slab from a counterclockwise outline in the XZ plane (x, z), th thick along Y."""
    fr = [bm.verts.new((x, th / 2, z)) for x, z in pts]
    bk = [bm.verts.new((x, -th / 2, z)) for x, z in pts]
    fs = [bm.faces.new(fr), bm.faces.new(list(reversed(bk)))]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((fr[i], bk[i], bk[j], fr[j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def _arch(bm, c, right, w, spring, th, depth, n, k, keep=lambda s, i: True, key=True):
    """gs_pointed_arch without jambs, leaving out the stones keep(side, index) refuses (a broken arch)."""
    c = Vector(c)
    rt = Vector(right).normalized()
    up = Vector((0, 0, 1))
    out = rt.cross(up)
    R = w * k
    xc = R - w * 0.5
    a_top = math.acos(min(max(xc / R, -1.0), 1.0))

    def stone(*ps):
        vs = [bm.verts.new(p + out * (depth * 0.5)) for p in ps] + [bm.verts.new(p - out * (depth * 0.5)) for p in ps]
        m = len(ps)
        fs = [bm.faces.new(vs[:m]), bm.faces.new(list(reversed(vs[m:])))]
        for i in range(m):
            j = (i + 1) % m
            fs.append(bm.faces.new((vs[j], vs[i], vs[m + i], vs[m + j])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    o = c + up * spring
    tops = {}
    for s in (-1, 1):
        cen = o - rt * (s * xc)
        pin = lambda a, rr, s=s, cen=cen: cen + rt * (s * math.cos(a) * rr) + up * (math.sin(a) * rr)
        for i in range(n):
            a0 = a_top * i / n + 0.014
            a1 = a_top * (i + 1) / n - (0.014 if i < n - 1 else 0.0)
            if keep(s, i):
                stone(pin(a0, R), pin(a0, R + th), pin(a1, R + th), pin(a1, R))
        tops[s] = pin(a_top, R + th)
    apex = math.sqrt(max(R * R - xc * xc, 0.0))
    if key:
        pk = o + up * apex
        stone(pk - up * 0.004, tops[1], pk + up * (th * 1.55), tops[-1])
    return spring + apex


def _rib_pts(a, b, n):
    """Points along a diagonal rib from pier top a up to the crown over the middle and down to pier top b."""
    a, b = Vector(a), Vector(b)
    h = Vector((a.x, a.y, 0)).length
    rise = CROWN - a.z
    R = (h * h + rise * rise) / (2 * rise)
    zc = CROWN - R
    out = []
    for i in range(n + 1):
        u = -1.0 + 2.0 * i / n                      # -1 at a, +1 at b
        s = u * h
        z = zc + math.sqrt(max(R * R - s * s, 0.0))
        d = Vector((b.x, b.y, 0)).normalized() if u >= 0 else Vector((a.x, a.y, 0)).normalized()
        out.append(Vector((0, 0, z)) + d * abs(s))
    return out


def build_base():
    col = collection("Hex_tomb")
    root = empty("Hex_tomb", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(17)
    k = Kit()
    # ---- the dais over the fan: an edge of coursed blocks, a dark floor with the pit left open
    edge = outline(CELLS, 0.2)
    pit = gs_rect(0, 0, PX, PY)
    gs_step(k, rnd, edge, T, FZ, stone="stone_dark:0.2:0.8", core=None, block=0.5, th=0.22)
    k.emit("Dais", col, root, vary=0.08)
    gs_step(k, rnd, list(reversed(pit)), T, FZ, stone="stone_dark:0.1:0.6", core=None, block=0.36, th=0.16)
    k.emit("Pit_Walls", col, root, bevel=0.01, vary=0.08)
    _cap_with_hole(k["stone_dark:0.6:0.95"], outline(CELLS, 0.3), gs_rect(0, 0, PX + 0.12, PY + 0.12), FZ - 0.012)
    bm_box(k["black:0.4:0.8"], (2 * PX + 0.02, 2 * PY + 0.02, 0.02), (0, 0, T + 0.01))
    k.emit("Dais_Core", col, root)
    # the lines of the diagram: the pit's rim, spokes out to the stelae, the lozenge joining them
    lines = []
    for p in STELAE:
        d = p.normalized()
        start = Vector((d.x * (PX + 0.2), d.y * (PY + 0.2), 0))
        lines.append((start, p - d * 0.3))
    for i in range(4):
        a, b = STELAE[i], STELAE[(i + 1) % 4]
        d = (b - a).normalized()
        lines.append((a + d * 0.3, b - d * 0.3))
    g = k[glow(VIO, 0.8)]
    for a, b in lines:
        bm_beam(g, (a.x, a.y, FZ + 0.012), (b.x, b.y, FZ + 0.012), 0.05, 0.02)
    rim = gs_rect(0, 0, PX + 0.21, PY + 0.21)
    for i in range(4):
        a, b = rim[i], rim[(i + 1) % 4]
        bm_beam(g, (a.x, a.y, FZ + 0.012), (b.x, b.y, FZ + 0.012), 0.045, 0.02)
    for p in STELAE:                                            # a ring round each stele's foot
        for j in range(10):
            a0, a1 = 2 * math.pi * j / 10 + 0.03, 2 * math.pi * (j + 1) / 10 - 0.03
            bm_beam(g, (p.x + math.cos(a0) * 0.38, p.y + math.sin(a0) * 0.38, FZ + 0.012),
                    (p.x + math.cos(a1) * 0.38, p.y + math.sin(a1) * 0.38, FZ + 0.012), 0.04, 0.02)
    k.emit("Sigil_Lines", col, root)
    floor_in = outline(CELLS, 0.36)

    def flags(x, y):
        if not inside(floor_in, x, y) or (abs(x) < PX + 0.3 and abs(y) < PY + 0.3):
            return False
        if any(_seg_d((x, y), a, b) < 0.09 for a, b in lines):
            return False
        return all(abs(math.hypot(x - p.x, y - p.y) - 0.38) > 0.07 for p in STELAE)
    bm_flagstones(k["stone:0.35:0.9"], rnd, flags, (-3.0, -2.2, 3.0, 2.2), FZ - 0.012, size=0.32, gap=0.04, keep=0.86)
    k.emit("Flagstones", col, root, vary=0.12)
    # ---- the sarcophagus, sunk in the pit: a plinth, panelled sides, the lid shoved ajar under a team pall
    sk = k["stone:0.15:0.7"]
    bm_box(sk, (2 * SX + 0.1, 2 * SY + 0.1, 0.08), (0, 0, T + 0.04))
    bm_box(sk, (2 * SX, 2 * SY, SH - 0.08), (0, 0, T + 0.08 + (SH - 0.08) / 2))
    bm_box(sk, (2 * SX + 0.05, 2 * SY + 0.05, 0.05), (0, 0, T + SH - 0.025))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(sk, (0.07, 0.07, SH - 0.1), (sx * (SX + 0.005), sy * (SY + 0.005), T + 0.08 + (SH - 0.1) / 2))
    k.emit("Sarcophagus", col, root, bevel=0.012, vary=0.05)
    pn = k["stone:0.4:0.9"]
    for sx in (-1, 1):                                          # sunk panels down the long sides, one on each end
        for y in (-0.28, 0.0, 0.28):
            bm_box(pn, (0.02, 0.22, 0.2), (sx * (SX + 0.002), y, T + 0.25))
    for sy in (-1, 1):
        bm_box(pn, (0.4, 0.02, 0.2), (0, sy * (SY + 0.002), T + 0.25))
    k.emit("Sarcophagus_Panels", col, root)
    gs_skull(k, place((0, -(SY + 0.012), T + 0.16), yaw=180, scale=0.2) @ Matrix.Diagonal((1.0, 0.35, 1.0, 1.0)), n=6)
    k.emit("Sarcophagus_Skull", col, root)
    # the light inside, welling out of the gap at the foot and spilling down into the pit
    gl = k[glow(VIO, 1.0)]
    bm_box(gl, (2 * SX - 0.08, 2 * SY - 0.08, 0.02), (0, 0, T + SH - 0.04))
    for x, y, L in ((-0.18, -SY, 0.3), (0.05, -SY, 0.36), (0.22, -SY, 0.26), (-SX, -0.38, 0.28)):
        side = Vector((0, -1, 0)) if y <= -SY + 1e-3 else Vector((-1, 0, 0))
        p0 = Vector((x, y, T + SH - 0.02))
        bm_tube(gl, [p0, p0 + side * 0.06 + Vector((0, 0, 0.02)), p0 + side * 0.09 - Vector((0, 0, L * 0.5)), p0 + side * 0.1 - Vector((0, 0, L))],
                [0.045, 0.04, 0.03, 0.0], n=5)
    pool = k[glow(VIO, 0.7)]
    for x, y, r in ((0.0, -0.66, 0.16), (-0.24, -0.62, 0.12), (0.22, -0.64, 0.13), (-0.4, -0.4, 0.12), (-0.42, -0.1, 0.09)):
        bm_cyl(pool, r, r, 0.012, (x, y, T + 0.025), seg=8)
    k.emit("Tomb_Light", col, root)
    # ---- the vault's ruin: four piers, three pointed arches (the right one broken), the ribs
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = Vector((sx * PIER[0], sy * PIER[1], 0))
            top = FZ + SPR_F
            for i, (z0, z1) in enumerate(((FZ, FZ + 0.2), (FZ + 0.2, FZ + 0.4), (FZ + 0.4, FZ + 0.6), (FZ + 0.6, top - 0.02))):
                sz = PW + (0.03 if i == 0 else 0.0)
                bm_box(k["stone_dark:0.1:0.65"], (sz, sz, z1 - z0 - 0.02), (c.x, c.y, (z0 + z1) / 2), (0, 0, 8 * (i % 2) - 4))
            bm_box(k["stone_dark:0.0:0.45"], (PW + 0.1, PW + 0.1, 0.09), (c.x, c.y, top + 0.035))
    k.emit("Piers", col, root, bevel=0.012, vary=0.08)
    ak = k["stone_dark:0.05:0.6"]
    wf = 2 * (PIER[0] - PW / 2)
    for sy in (-1, 1):
        _arch(ak, (0, sy * PIER[1], FZ), (1, 0, 0), wf, SPR_F + 0.08, 0.13, 0.2, 4, 0.75)
    ws = 2 * (PIER[1] - PW / 2)
    _arch(ak, (-PIER[0], 0, FZ), (0, 1, 0), ws, SPR_S + 0.08, 0.13, 0.2, 4, 0.62)
    _arch(ak, (PIER[0], 0, FZ), (0, 1, 0), ws, SPR_S + 0.08, 0.13, 0.2, 4, 0.62, keep=lambda s, i: (s == -1 and i < 2) or (s == 1 and i < 1), key=False)
    k.emit("Arches", col, root, bevel=0.01, vary=0.08)
    rb = k["stone_dark:0.05:0.6"]                              # the ribs: one whole across the crossing, one snapped
    tops = {(sx, sy): Vector((sx * (PIER[0] - 0.1), sy * (PIER[1] - 0.1), FZ + SPR_F + 0.08)) for sx in (-1, 1) for sy in (-1, 1)}
    pts = _rib_pts(tops[(-1, -1)], tops[(1, 1)], 10)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = (b - a).normalized()
        bm_beam(rb, a + d * 0.008, b - d * 0.008, 0.13, 0.15)
    pts2 = _rib_pts(tops[(1, -1)], tops[(-1, 1)], 10)
    for i, (a, b) in enumerate(zip(pts2, pts2[1:])):
        if i < 2 or 10 - i <= 3:
            d = (b - a).normalized()
            bm_beam(rb, a + d * 0.008, b - d * 0.008, 0.13, 0.15)
    k.emit("Ribs", col, root, bevel=0.008, vary=0.1)
    gs_skull(k, place((0, 0, CROWN - 0.2), yaw=180, pitch=-75, scale=0.26), n=6)          # the boss: a skull looking down
    k.emit("Boss", col, root)
    for (x, y, z, s, r) in ((1.0, 0.35, FZ, 0.16, 30), (1.15, -0.1, FZ, 0.14, 70), (0.92, -0.45, FZ, 0.12, 10), (0.46, 0.38, T, 0.12, 50),
                            (1.3, 0.15, FZ + 0.1, 0.1, 20)):
        bm_box(k["stone_dark:0.05:0.6"], (s * 1.6, s, s * 0.9), (x, y, z + s * 0.4), (rnd.uniform(-20, 20), rnd.uniform(-25, 25), r))
    k.emit("Rubble", col, root, bevel=0.01, vary=0.08)
    # team banners hung in the front and back arches from iron rods
    for sy in (-1, 1):
        bm_beam(k[IRON], (-0.47, sy * PIER[1], FZ + SPR_F + 0.6), (0.47, sy * PIER[1], FZ + SPR_F + 0.6), 0.035, 0.035)
    k.emit("Arch_Rods", col, root)
    for sy in (-1, 1):
        gs_banner(k["team!:0.1:0.75"], (0, sy * PIER[1], FZ + SPR_F + 0.58), (sy, 0, 0), (0, 0, -1), 0.4, 0.6,
                  rnd=random.Random(3 + sy), cols=5, rows=4, tatter=0.3)
    k.emit("Arch_Banners", col, root)
    for sy in (-1, 1):
        for side in (-1, 1):
            gs_skull(k, place((0, sy * PIER[1] + side * 0.012, FZ + SPR_F + 0.2), yaw=_yaw_to(0, side), scale=0.16) @ Matrix.Diagonal((1.0, 0.25, 1.0, 1.0)), n=6)
    k.emit("Arch_Banner_Badges", col, root)
    # ---- the four leaning stelae
    for i, p in enumerate(STELAE):
        d = p.normalized()
        bm_box(k["stone_dark:0.2:0.8"], (0.66, 0.36, 0.14), (p.x, p.y, FZ + 0.04), (0, 0, _yaw_to(-d.x, -d.y)))
    k.emit("Stele_Bases", col, root, bevel=0.012, vary=0.06)
    for i, p in enumerate(STELAE):
        d = p.normalized()
        broken = (i == 1)
        M = place((p.x, p.y, FZ + 0.1), yaw=_yaw_to(-d.x, -d.y), pitch=11 + 3 * (i % 2), roll=(-5, 6, -4, 5)[i])
        st, gk, tk = k["stone:0.25:0.75"], k[glow(VIO, 0.85)], k["team!:0.1:0.7"]
        with Stamp(M, st, gk, tk):
            if broken:
                _slab(st, [(-0.23, 0.0), (0.23, 0.0), (0.23, 0.88), (0.08, 1.0), (-0.05, 0.9), (-0.23, 1.04)], 0.15)
            else:
                _slab(st, [(-0.23, 0.0), (0.23, 0.0), (0.23, 1.04), (0.0, 1.28), (-0.23, 1.04)], 0.15)
            ring(gk, (0, 0.08, 0.84 if broken else 1.02), 0.1, 0.07, -0.01, 0.01, seg=10, axis="Y")
            for j, zc in enumerate((0.58, 0.36, 0.14) if broken else (0.74, 0.5, 0.26)):
                gg = GLYPHS[(i * 2 + j * 3) % len(GLYPHS)]
                for (u0, v0), (u1, v1) in gg:
                    for fy in (0.078, -0.078):                  # on both faces
                        a = Vector((u0 * 0.14 * (1 if fy > 0 else -1), fy, zc - 0.08 + v0 * 0.16))
                        b = Vector((u1 * 0.14 * (1 if fy > 0 else -1), fy, zc - 0.08 + v1 * 0.16))
                        dd = (b - a).normalized()
                        bm_beam(gk, a - dd * 0.01, b + dd * 0.01, 0.03, 0.02, up=(0, 1, 0))
            bm_box(tk, (0.5, 0.18, 0.07), (0, 0, 0.62 if not broken else 0.66))
            gs_banner(tk, (0.18, 0.0, 0.6 if not broken else 0.64), (0, 1, 0), (0.35, 0, -1), 0.14, 0.4, rnd=random.Random(70 + i), cols=3, rows=3, tatter=0.3)
        k.emit("Stele%d" % (i + 1), col, root, vary=0.05)
    p = STELAE[1]                                               # the broken stele's top, lying at its foot
    gs_hull(k["stone:0.25:0.75"], [Vector((p.x + 0.25 + x, p.y + 0.3 + y, FZ + z)) for x, y, z in
                                   ((-0.22, -0.08, 0.0), (0.18, -0.12, 0.0), (0.2, 0.08, 0.0), (-0.2, 0.1, 0.0), (-0.2, -0.06, 0.14),
                                    (0.16, -0.1, 0.15), (0.0, 0.08, 0.3))])
    k.emit("Stele_Shard", col, root, vary=0.05)
    for p in STELAE:                                            # candles at each stele's foot and the pit's corners
        d = p.normalized()
        rt = Vector((-d.y, d.x, 0))
        for j, s in enumerate((-1, 1)):
            q = p - d * 0.3 + rt * (s * 0.24)
            gs_candle(k, (q.x, q.y, FZ + 0.02), h=0.12 + 0.05 * j, r=0.032, flame=glow(PALE, 0.9))
    for sx in (-1, 1):
        for sy in (-1, 1):
            gs_candle(k, (sx * (PX + 0.14), sy * (PY + 0.16), FZ), h=0.1, r=0.03, flame=glow(PALE, 0.9))
    k.emit("Candles", col, root)
    head = empty("Head", col, root, (0, 0, SZ), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0), 0.2, "SPHERE")
    return root


LID_C = Vector((LID_OFF.x, LID_OFF.y, T + SH))
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "sigil": ((0, 0, SZ), (0, 0, SZ + 0.3), "root"),
         "wheel": ((0, 0, SZ), (0, 0, SZ + 0.25), "root"),
         "pulse": ((0, 0, SZ), (0, 0, SZ + 0.2), "root"),
         "lid": (tuple(LID_C), tuple(LID_C + Vector((0, 0, 0.2))), "root"),
         "well": ((-0.07, -0.42, T + SH - 0.04), (-0.07, -0.42, T + SH + 0.16), "root")}


def build_head():
    col = collection("Hex_tomb")
    root = bpy.data.objects["Hex_tomb"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(9)
    k = Kit()
    # ---- the hex: a seven-pointed star {7/3} in a double ring, small glyph ticks between its points
    g = k[glow(VIO, 0.95)]
    c = Vector((0, 0, SZ))
    for rr in (SR, SR - 0.11):
        n = 28
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            bm_beam(g, c + Vector((math.cos(a0) * rr, math.sin(a0) * rr, 0)), c + Vector((math.cos(a1) * rr, math.sin(a1) * rr, 0)), 0.045, 0.03)
    pts = [c + Vector((math.cos(math.radians(90 + 360 * i / 7)), math.sin(math.radians(90 + 360 * i / 7)), 0)) * (SR - 0.11) for i in range(7)]
    for i in range(7):
        a, b = pts[i], pts[(i + 3) % 7]
        d = (b - a).normalized()
        bm_beam(g, a - d * 0.02, b + d * 0.02, 0.05, 0.035)
    for i in range(7):                                          # little marks in the ring between the points
        a = math.radians(90 + 360 * (i + 0.5) / 7)
        r0, r1 = SR - 0.1, SR - 0.01
        bm_beam(g, c + Vector((math.cos(a - 0.05) * r0, math.sin(a - 0.05) * r0, 0)), c + Vector((math.cos(a + 0.05) * r1, math.sin(a + 0.05) * r1, 0)), 0.03, 0.025)
        bm_beam(g, c + Vector((math.cos(a + 0.05) * r0, math.sin(a + 0.05) * r0, 0)), c + Vector((math.cos(a - 0.05) * r1, math.sin(a - 0.05) * r1, 0)), 0.03, 0.025)
    k.emit("Hex_Star", col, rig=rig, bone="sigil")
    w = k[glow(PALE, 0.9)]                                      # the inner wheel, turning the other way
    for i in range(14):
        a0, a1 = 2 * math.pi * i / 14, 2 * math.pi * (i + 1) / 14
        bm_beam(w, c + Vector((math.cos(a0) * 0.3, math.sin(a0) * 0.3, 0)), c + Vector((math.cos(a1) * 0.3, math.sin(a1) * 0.3, 0)), 0.04, 0.03)
    for i in range(7):
        a = math.radians(90 + 360 * i / 7)
        bm_beam(w, c + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0)), c + Vector((math.cos(a) * 0.46, math.sin(a) * 0.46, 0)), 0.035, 0.03)
    bm_crystal(w, c - Vector((0, 0, 0.1)), c + Vector((0, 0, 0.14)), 0.07, n=7, shoulder=0.5, foot=0.6)
    bm_crystal(w, c - Vector((0, 0, 0.1)), c - Vector((0, 0, 0.3)), 0.07, n=7, shoulder=0.4, foot=1.0)
    k.emit("Hex_Wheel", col, rig=rig, bone="wheel")
    for i in range(32):                                         # the pulse it drops (hidden till it fires)
        a0, a1 = 2 * math.pi * i / 32, 2 * math.pi * (i + 1) / 32
        bm_beam(k[glow(VIO, 1.0)], c + Vector((math.cos(a0) * SR, math.sin(a0) * SR, 0)), c + Vector((math.cos(a1) * SR, math.sin(a1) * SR, 0)), 0.07, 0.05)
    k.emit("Hex_Pulse", col, rig=rig, bone="pulse")
    # ---- the lid, shoved ajar, and the pall over it
    M = Matrix.Translation(LID_C) @ Matrix.Rotation(math.radians(LID_ROT), 4, "Z")
    lk, pk, gk = k["stone:0.1:0.6"], k["team!:0.1:0.7"], k["gold:0.1:0.5"]
    with Stamp(M, lk, pk, gk):
        bm_box(lk, (2 * SX + 0.08, 2 * SY + 0.08, 0.09), (0, 0, 0.045))
        bm_box(lk, (2 * SX - 0.04, 2 * SY - 0.04, 0.05), (0, 0, 0.11))
        gs_cloth(pk, (-SX - 0.03, -SY + 0.12, 0.15), (SX + 0.03, -SY + 0.12, 0.15), (SX + 0.03, SY - 0.1, 0.15), (-SX - 0.03, SY - 0.1, 0.15),
                 nx=3, ny=5, sag=-0.015, rnd=rnd, th=0.016, ragged=0.02)
        for sx in (-1, 1):                                      # the pall's sides hanging over the lid's edges
            gs_banner(pk, (sx * (SX + 0.04), 0.0, 0.14), (0, 1, 0), (sx * 0.25, 0, -1), 0.98, 0.26, rnd=random.Random(12 + sx), cols=6, rows=2, tatter=0.35)
        for sx in (-1, 1):                                      # gold edging, and the hex's star worked on it in gold
            bm_beam(gk, (sx * (SX - 0.02), -SY + 0.16, 0.162), (sx * (SX - 0.02), SY - 0.14, 0.162), 0.035, 0.018)
        sp = [Vector((math.cos(math.radians(90 + 360 * i / 7)) * 0.17, 0.04 + math.sin(math.radians(90 + 360 * i / 7)) * 0.17, 0.168)) for i in range(7)]
        for i in range(7):
            a, b = sp[i], sp[(i + 3) % 7]
            bm_beam(gk, a, b, 0.03, 0.016)
    k.emit("Lid", col, rig=rig, bone="lid", vary=0.04)
    gs_skull(k, place(tuple(LID_C + Matrix.Rotation(math.radians(LID_ROT), 3, "Z") @ Vector((0, -0.36, 0.16))), yaw=LID_ROT, pitch=75, scale=0.13), n=6)
    k.emit("Lid_Skull", col, rig=rig, bone="lid")
    for x, y in ((-0.12, -0.42), (0.1, -0.5), (-0.2, -0.32)):   # the light welling up out of the gap
        bm_crystal(k[glow(PALE, 0.9)], (x, y, T + SH - 0.05), (x + rnd.uniform(-0.03, 0.03), y - 0.04, T + SH + 0.16 + rnd.uniform(0, 0.08)), 0.05, n=4, shoulder=0.3, foot=0.8)
    k.emit("Tomb_Wisps", col, rig=rig, bone="well")
    return rig


IDLE_LEN = 120
FIRE_LEN = 24
STEP = 360.0 / 7.0


def pose(rig, t=0.0, turn=0.0, flash=0.0, drop=None, lid=0.0, rattle=0.0, jf=0):
    """t: the idle's phase (0..1 loops); turn: extra turns of the star in sevenths; drop: (height, spread) of the
    pulse ring or None (hidden); lid: the shudder's strength; rattle: a light one."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    ph = 2 * math.pi * t
    sg = pb["sigil"]
    sg.rotation_quaternion = q(sg, (0, 0, 1), STEP * (t + turn))
    sg.location = arm_space_loc(sg, (0, 0, 0.05 * math.sin(ph) - 0.12 * flash))
    s = 1.0 + 0.02 * math.sin(2 * ph) + 0.16 * flash
    sg.scale = (s, s, s)
    wh = pb["wheel"]
    wh.rotation_quaternion = q(wh, (0, 0, 1), -2 * STEP * (t + turn))
    wh.location = arm_space_loc(wh, (0, 0, 0.05 * math.sin(ph) - 0.12 * flash))
    sw = 1.0 + 0.06 * math.sin(3 * ph) + 0.3 * flash
    wh.scale = (sw, sw, sw)
    pu = pb["pulse"]
    if drop is None:
        pu.scale = (0.01, 0.01, 0.01)
    else:
        h, spread = drop
        pu.location = arm_space_loc(pu, (0, 0, -h))
        pu.scale = (spread, max(spread, 0.01), spread)
    ld = pb["lid"]
    j = lid + rattle
    ld.rotation_quaternion = q(ld, (0, 1, 0), 2.4 * j * math.sin(2.1 * jf + 1.0)) @ q(ld, (1, 0, 0), 1.6 * j * math.sin(2.9 * jf))
    ld.location = arm_space_loc(ld, (0, 0, 0.035 * j * abs(math.sin(1.7 * jf + 0.4))))
    we = pb["well"]
    sv = 1.0 + 0.18 * math.sin(2 * ph) + 0.08 * math.sin(5 * ph) + 0.6 * lid
    we.scale = (1.0 + 0.3 * (sv - 1.0), sv, 1.0 + 0.3 * (sv - 1.0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(IDLE_LEN + 1):
        t = f / IDLE_LEN
        pose(rig, t=t, rattle=_rattle(t), jf=f)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the star flashes (0-4) and kicks round a seventh, the ring drops to the floor (2-9) and rolls out over the fan
        flash = smooth(f / 2.0) * (1 - smooth((f - 4) / 8.0))
        if f < 2:
            drop = (0.0, 0.01 + 0.99 * f / 2.0)
        elif f <= 9:
            u = (f - 2) / 7.0
            drop = ((SZ - FZ - 0.06) * u * u, 1.0 + 0.5 * u)
        elif f <= 15:
            u = (f - 9) / 6.0
            drop = (SZ - FZ - 0.06, 1.5 + 1.0 * smooth(u))
        else:
            drop = None
        lid = smooth((f - 3) / 2.0) * (1 - smooth((f - 8) / 10.0))
        pose(rig, t=0.0, turn=smooth(f / 14.0), flash=flash, drop=drop, lid=lid, jf=f)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


def _rattle(t):
    return 0.7 * (smooth((t - 0.62) / 0.03) * (1 - smooth((t - 0.68) / 0.05)))


PREVIEW = {"target": (0, 0, 1.2), "dist": 11.0, "yaw": 150, "pitch": 24, "anim_target": (0, 0, 1.6), "anim_dist": 7.2,
           "frames": [("idle", 0), ("idle", 60), ("fire", 3), ("fire", 7), ("fire", 11), ("fire", 15)],
           "extra": [{"yaw": 200, "pitch": 30, "dist": 3.4, "target": (0, 0, FZ + 0.3)},
                     {"yaw": 0, "pitch": 80, "dist": 9.0, "target": (0, 0, 0.6)},
                     {"yaw": 115, "pitch": 14, "dist": 3.6, "target": (STELAE[3].x, 0, 1.0)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
