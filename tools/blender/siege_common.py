"""The Crown's siege engines' shared pieces (archer, ballista, trebuchet, bombard): decks of planks cut to a circle or
an octagon, heraldry (shields, hanging banners, the crown device), palisade stakes, shot piles, braziers and flames,
rope coils, kegs, tiled gable roofs, and a stand-in for the KayKit crew member (previews only).
Exec'd by a tower script after kk_helpers.py.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

SQ2 = math.sqrt(2.0)
MANNEQUIN = bool(os.environ.get("TR_MANNEQUIN"))      # previews only: never set for a build that ships
FIRE = "glow:1.0,0.55,0.12,1.0"
EMBERS = "glow:1.0,0.32,0.06,0.8"


def polar(c, ang, r, z=None):
    """The point r from c at `ang` degrees (0 = +X, 90 = +Y: the front), at height z (c's own when None)."""
    c = Vector(c)
    a = math.radians(ang)
    return Vector((c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z if z is None else z))


def radial(ang):
    a = math.radians(ang)
    return Vector((math.cos(a), math.sin(a), 0.0))


def ang_off(a, b):
    """How far angle a is from angle b (degrees, 0..180)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def circle_half(r):
    return lambda v: math.sqrt(max(r * r - v * v, 0.0))


def octagon_half(apothem):
    return lambda v: max(0.0, min(apothem, apothem * SQ2 - abs(v)))


def bm_deck(bm, rnd, c, half, v0, v1, z, pw=0.17, th=0.07, gap=0.014, turn=0.0, jit=0.006):
    """A deck of planks cut to a convex outline: the planks run along the direction `turn` (degrees from +X) through c,
    laid side by side from offset v0 to v1 across it; half(v) is the outline's half width at offset v. Top at z."""
    c = Vector(c)
    a = math.radians(turn)
    ax, ay = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    n = max(1, int(round((v1 - v0) / pw)))
    w = (v1 - v0) / n
    for i in range(n):
        a0, a1 = v0 + i * w + gap * 0.5, v0 + (i + 1) * w - gap * 0.5
        h0, h1 = half(a0), half(a1)
        if max(h0, h1) < 0.05:
            continue
        h0, h1 = max(h0, 0.02), max(h1, 0.02)
        zt = z + rnd.uniform(-jit, jit)
        s0, s1 = rnd.uniform(-jit, jit), rnd.uniform(-jit, jit)
        top = [c + ax * (-h0 + s0) + ay * a0, c + ax * (h0 + s1) + ay * a0, c + ax * (h1 + s1) + ay * a1, c + ax * (-h1 + s0) + ay * a1]
        tv = [bm.verts.new((p.x, p.y, zt)) for p in top]
        bv = [bm.verts.new((p.x, p.y, zt - th)) for p in top]
        bm.faces.new(tv)
        bm.faces.new(list(reversed(bv)))
        for q in range(4):
            j = (q + 1) % 4
            bm.faces.new((bv[q], bv[j], tv[j], tv[q]))
    return bm


def bm_plate(bm, pts, origin, right, up, th=0.02):
    """A flat shape (2D points, counterclockwise seen from its front) standing at origin in the plane of right / up,
    `th` thick, both faces and the rim: shields, banners, signs, blades."""
    o, r, u = Vector(origin), Vector(right).normalized(), Vector(up).normalized()
    out = r.cross(u).normalized()
    f = [bm.verts.new(o + r * x + u * y + out * (th * 0.5)) for x, y in pts]
    b = [bm.verts.new(o + r * x + u * y - out * (th * 0.5)) for x, y in pts]
    bm.faces.new(f)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], f[j], f[i]))
    return bm


def shield_pts(w, h):
    return [(-w / 2, h / 2), (-w / 2, -h * 0.08), (-w * 0.3, -h * 0.34), (0, -h / 2), (w * 0.3, -h * 0.34), (w / 2, -h * 0.08), (w / 2, h / 2)]


def crown_pts(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (w / 4, -h * 0.05), (0, h / 2), (-w / 4, -h * 0.05), (-w / 2, h / 2)]


def banner_pts(w, h, notch=0.22):
    return [(-w / 2, 0), (-w / 2, -h), (0, -h * (1 - notch)), (w / 2, -h), (w / 2, 0)]


def bm_shield(kit, origin, out, w=0.3, h=0.36, device=True, rim=True):
    """A heater shield hung on a wall at origin, facing `out` (horizontal): the team's color, a gold rim, the crown."""
    o = Vector(out).normalized()
    right = Vector((0, 0, 1)).cross(o)
    up = Vector((0, 0, 1))
    c = Vector(origin)
    if rim:
        bm_plate(kit["gold:0.15:0.6"], shield_pts(w + 0.05, h + 0.05), c, right, up, 0.03)
    bm_plate(kit["team!:0.1:0.7"], shield_pts(w, h), c + o * 0.012, right, up, 0.035)
    if device:
        bm_plate(kit["gold:0.05:0.45"], crown_pts(w * 0.52, h * 0.3), c + o * 0.034 + up * (h * 0.08), right, up, 0.014)
    return kit


def bm_banner(kit, top, out, w=0.42, h=0.8, rod=True, device=True, lean=0.0):
    """A banner hanging from `top` (the middle of its upper edge), facing `out`: team cloth, swallow-tailed, a gold
    band and the crown device, on a wooden rod. lean: how far its lower end swings out from the wall."""
    o = Vector(out).normalized()
    right = Vector((0, 0, 1)).cross(o)
    up = (Vector((0, 0, 1)) - o * lean).normalized()
    c = Vector(top)
    bm_plate(kit["team!:0.08:0.75"], banner_pts(w, h), c, right, up, 0.022)
    bm_plate(kit["gold:0.1:0.55"], [(-w / 2, 0), (-w / 2, -0.05), (w / 2, -0.05), (w / 2, 0)], c + o * 0.006 - up * (h * 0.1), right, up, 0.022)
    if device:
        bm_plate(kit["gold:0.05:0.45"], crown_pts(w * 0.5, w * 0.3), c + o * 0.016 - up * (h * 0.42), right, up, 0.014)
    if rod:
        bm_beam(kit["wood_dark:0.2:0.7"], c - right * (w * 0.5 + 0.06) + up * 0.01, c + right * (w * 0.5 + 0.06) + up * 0.01, 0.045, 0.045)
        for s in (-1, 1):
            bm_cyl(kit["gold:0.1:0.5"], 0.035, 0.035, 0.03, tuple(c + right * (s * (w * 0.5 + 0.07)) + up * 0.01), rot=(0, 90, math.degrees(math.atan2(right.y, right.x))), seg=6)
    return kit


def bm_stake(bm, base, d, length, r=0.06, n=6, point=0.3):
    """A sharpened log from base along d."""
    b, d = Vector(base), Vector(d).normalized()
    return bm_tube(bm, [b, b + d * (length * (1 - point)), b + d * length], [r, r * 0.92, 0.0], n=n)


def bm_shot_pile(bm, c, r=0.1, layers=3, u=7, v=5, turn=0.0):
    """A square pyramid of round shot standing on c."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(turn), 3, "Z")
    for k in range(layers):
        n = layers - k
        for i in range(n):
            for j in range(n):
                p = rz @ Vector(((i - (n - 1) / 2) * 2 * r, (j - (n - 1) / 2) * 2 * r, 0))
                bm_ellipsoid(bm, (c.x + p.x, c.y + p.y, c.z + r + k * r * 1.42), (r, r, r), rot=(0, 0, 17 * (i + 2 * j + k)), u=u, v=v)
    return bm


def bm_rope_coil(bm, c, r=0.16, th=0.035, turns=3):
    c = Vector(c)
    for i in range(turns):
        rr = r - 0.012 * i
        ring(bm, (c.x, c.y, c.z + th * 2 * i), rr, rr - th * 2, 0.0, th * 2 - 0.006, seg=10)
    return bm


def bm_brazier(kit, c, r=0.15, h=0.36, legs=3, turn=0.0):
    """An iron fire basket on legs standing on c, full of glowing coals. Returns where its flames start."""
    c = Vector(c)
    for i in range(legs):
        a = turn + 360.0 * i / legs
        bm_beam(kit["iron:0.1:0.6"], polar(c, a, r * 1.05, c.z), polar(c, a, r * 0.55, c.z + h * 0.72), 0.03, 0.03)
    bm_cyl(kit["iron:0.05:0.5"], r * 0.6, r, h * 0.34, (c.x, c.y, c.z + h * 0.82), seg=8)
    ring(kit["iron:0.0:0.4"], (c.x, c.y, c.z + h), r * 1.08, r * 0.86, -0.025, 0.02, seg=8)
    bm_cyl(kit[EMBERS], r * 0.84, r * 0.6, 0.04, (c.x, c.y, c.z + h + 0.0), seg=8)
    return Vector((c.x, c.y, c.z + h + 0.01))


def bm_flame(bm, base, h=0.2, r=0.07, lean=(0, 0, 0), n=5):
    b = Vector(base)
    return bm_crystal(bm, b, b + Vector((0, 0, h)) + Vector(lean), r, n=n, shoulder=0.3, foot=0.55)


def bm_keg(kit, c, r=0.17, h=0.4, axis=(0, 0, 1), wood="wood:0.2:0.8", n=9):
    """A stout keg with iron hoops, its middle on c, lying along `axis`."""
    c, ax = Vector(c), Vector(axis).normalized()
    pts = [c + ax * (h * t) for t in (-0.5, -0.2, 0.2, 0.5)]
    bm_tube(kit[wood], pts, [r * 0.82, r, r, r * 0.82], n=n)
    for t in (-0.3, 0.3):
        p = c + ax * (h * t)
        bm_tube(kit["iron:0.1:0.5"], [p - ax * 0.022, p + ax * 0.022], r * 0.97 + 0.012, n=n)
    return kit


def bm_gable_roof(kit, rnd, c, w, d, eave_z, rise, swatch="team!:0.1:0.72", rows=4, cols=5, over=0.12, ridge="wood_dark:0.2:0.7",
                  along="x", th=0.04):
    """A tiled gable roof over a w (x) by d (y) box centred on c: ridge along `along`, eaves at eave_z, `rise` to the
    ridge, overhanging by `over`. Adds the ridge beam and a dark lining under the tiles."""
    c = Vector(c)
    if along == "x":
        ax, ay, hw, hd = Vector((1, 0, 0)), Vector((0, 1, 0)), w * 0.5 + over, d * 0.5 + over
    else:
        ax, ay, hw, hd = Vector((0, 1, 0)), Vector((1, 0, 0)), d * 0.5 + over, w * 0.5 + over
    up = Vector((0, 0, 1))
    slope = rise / max(hd - over, 1e-3)
    ez = eave_z - over * slope
    for s in (-1, 1):
        e0 = c + ax * (-hw) + ay * (s * hd) + up * ez
        e1 = c + ax * hw + ay * (s * hd) + up * ez
        r0 = c + ax * (-hw) + up * (eave_z + rise)
        r1 = c + ax * hw + up * (eave_z + rise)
        bm_tile_slope(kit[swatch], rnd, e0, e1, r0, r1, rows=rows, cols=cols, th=th)
        lin = [e0 + up * -0.02, e1 + up * -0.02, r1 + up * -0.02, r0 + up * -0.02]            # lining: the tiles' gaps stay dark
        vs = [kit["wood_dark:0.5:0.9"].verts.new(p) for p in lin] + [kit["wood_dark:0.5:0.9"].verts.new(p - up * 0.04) for p in lin]
        fs = [kit["wood_dark:0.5:0.9"].faces.new(vs[:4]), kit["wood_dark:0.5:0.9"].faces.new(list(reversed(vs[4:])))]
        for q in range(4):
            j = (q + 1) % 4
            fs.append(kit["wood_dark:0.5:0.9"].faces.new((vs[j], vs[q], vs[4 + q], vs[4 + j])))
        bmesh.ops.recalc_face_normals(kit["wood_dark:0.5:0.9"], faces=fs)
    bm_beam(kit[ridge], c + ax * (-hw - 0.03) + up * (eave_z + rise + 0.03), c + ax * (hw + 0.03) + up * (eave_z + rise + 0.03), 0.1, 0.09)
    return kit


def bm_wedge(bm, c, a0, a1, r_in, r_out, z0, z1, inner=True, bottom=False):
    """A block between two angles (radians) and two radii, like kk_helpers' _wedge, without the faces nobody sees:
    no bottom, and no inner face when inner=False (a block laid against a core)."""
    vs = []
    for z in (z0, z1):
        for r, a in ((r_in, a0), (r_out, a0), (r_out, a1), (r_in, a1)):
            vs.append(bm.verts.new((c.x + r * math.cos(a), c.y + r * math.sin(a), z)))
    lo, hi = vs[:4], vs[4:]
    if bottom:
        bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4 if inner else 3):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def bm_course(bm, rnd, c, r, z, h, n, depth=0.16, gap=0.02, phase=0.0, jit=0.012, skip=None, inner=True):
    """kk_helpers' bm_block_course on a budget (see bm_wedge): one course of n blocks round a circle."""
    c = Vector(c)
    ga = gap / max(r, 1e-3)
    for i in range(n):
        a0 = 2 * math.pi * (i + phase) / n + ga * 0.5
        a1 = 2 * math.pi * (i + 1 + phase) / n - ga * 0.5
        if skip and skip(math.degrees((a0 + a1) * 0.5) % 360.0):
            continue
        bm_wedge(bm, c, a0, a1, r - depth, r + rnd.uniform(-jit, jit), z + rnd.uniform(0, jit * 0.6), z + h - gap * 0.6 - rnd.uniform(0, jit * 0.6),
                 inner=inner)
    return bm


def bm_drum(bm, c, r0, r1, z0, z1, seg=16, cap=True, inward=False):
    """A round wall from z0 (radius r0) up to z1 (radius r1) with no bottom: the dark core behind a ring of blocks.
    cap: a lid on top; inward: its face is seen from inside."""
    c = Vector(c)
    lo = [bm.verts.new((c.x + r0 * math.cos(2 * math.pi * i / seg), c.y + r0 * math.sin(2 * math.pi * i / seg), z0)) for i in range(seg)]
    hi = [bm.verts.new((c.x + r1 * math.cos(2 * math.pi * i / seg), c.y + r1 * math.sin(2 * math.pi * i / seg), z1)) for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        f = (lo[i], lo[j], hi[j], hi[i])
        bm.faces.new(tuple(reversed(f)) if inward else f)
    if cap:
        bm.faces.new(hi)
    return bm


def bm_hip_roof(kit, rnd, c, w, d, eave_z, rise, ridge=0.5, swatch="team!:0.1:0.72", rows=4, cols=6, over=0.12, th=0.04,
                beam="wood_dark:0.2:0.7"):
    """A tiled hipped roof over a w (x) by d (y) box centred on c: a ridge `ridge` long along x, eaves at eave_z, `rise`
    to the ridge, overhanging by `over`; hip rolls, the ridge beam and a dark lining under the tiles. Returns the
    ridge's two ends."""
    c = Vector((c[0], c[1], 0.0))
    hw, hd, hr = w * 0.5 + over, d * 0.5 + over, ridge * 0.5
    ez = eave_z - over * rise / max(hd - over, 1e-3)
    top = eave_z + rise
    E = [c + Vector((sx * hw, sy * hd, ez)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    R = [c + Vector((-hr, 0, top)), c + Vector((hr, 0, top))]
    ends = max(2, int(round(cols * hd / hw)))
    for e0, e1, r0, r1, n in ((E[0], E[1], R[0], R[1], cols), (E[2], E[3], R[1], R[0], cols), (E[1], E[2], R[1], R[1], ends),
                              (E[3], E[0], R[0], R[0], ends)):
        bm_tile_slope(kit[swatch], rnd, e0, e1, r0, r1, rows=rows, cols=n, th=th)
    lin = kit["wood_dark:0.5:0.9"]
    dz = Vector((0, 0, -0.025))
    ev = [lin.verts.new(p + dz) for p in E]
    rv = [lin.verts.new(p + dz) for p in R]
    fs = [lin.faces.new(list(reversed(ev))), lin.faces.new((ev[0], ev[1], rv[1], rv[0])), lin.faces.new((ev[2], ev[3], rv[0], rv[1])),
          lin.faces.new((ev[1], ev[2], rv[1])), lin.faces.new((ev[3], ev[0], rv[0]))]
    bmesh.ops.recalc_face_normals(lin, faces=fs)
    for e, r in ((E[0], R[0]), (E[1], R[1]), (E[2], R[1]), (E[3], R[0])):
        bm_beam(kit[beam], e + Vector((0, 0, 0.04)), r + Vector((0, 0, 0.05)), 0.075, 0.06)
    bm_beam(kit[beam], R[0] + Vector((-0.05, 0, 0.055)), R[1] + Vector((0.05, 0, 0.055)), 0.1, 0.085)
    return R


def bm_gonfalon(kit, base, face, pole=1.45, w=0.4, h=0.72):
    """A standing banner: a pole on `base` with the team's banner hung from a crossbar near its top, facing `face`."""
    b = Vector(base)
    f = Vector(face).normalized()
    bm_cyl(kit["wood_dark:0.2:0.7"], 0.032, 0.024, pole, (b.x, b.y, b.z + pole / 2), seg=6)
    bm_cyl(kit["wood_dark:0.2:0.7"], 0.06, 0.045, 0.07, (b.x, b.y, b.z + 0.035), seg=6)
    bm_cyl(kit["gold:0.05:0.5"], 0.042, 0.0, 0.13, (b.x, b.y, b.z + pole + 0.065), seg=5)
    bm_banner(kit, b + Vector((0, 0, pole - 0.1)) + f * 0.05, f, w=w, h=h)
    return kit


def tri_report(col_name, top=30):
    """Debugging only (TR_TRIS=1 in the environment): prints the heaviest meshes of a tower, modifiers applied."""
    if not os.environ.get("TR_TRIS"):
        return
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for o in bpy.data.collections[col_name].all_objects:
        if o.type != "MESH":
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        rows.append((sum(len(p.vertices) - 2 for p in me.polygons), o.name))
        e.to_mesh_clear()
    rows.sort(reverse=True)
    print("TRIS total %d (before the finishing pass)" % sum(r[0] for r in rows))
    for n, name in rows[:top]:
        print("TRIS %6d %s" % (n, name))


def mannequin(col, crew, h=1.15, kind="archer"):
    """Previews only (TR_MANNEQUIN=1 in the environment): a stand-in for the KayKit character the game stands at the
    Crew marker, so the sheet shows how the crew reads. Never part of a build that ships."""
    if not MANNEQUIN or crew is None:
        return None
    k = Kit()
    cloth = "grass:0.3:0.8" if kind == "archer" else "wood_red:0.2:0.7"
    for sx in (-1, 1):
        bm_box(k["wood_dark:0.3:0.8"], (0.12, 0.14, 0.34), (sx * 0.085, 0, 0.17))
        bm_box(k[cloth], (0.1, 0.12, 0.3), (sx * 0.23, 0.02, 0.56), (0, sx * 12, 0))
    bm_box(k[cloth], (0.36, 0.22, 0.34), (0, 0, 0.5))
    bm_ellipsoid(k["tan:0.2:0.6"], (0, 0.02, 0.9), (0.2, 0.19, 0.22), u=8, v=6)
    bm_ellipsoid(k[cloth], (0, -0.03, 0.95), (0.22, 0.21, 0.21), u=8, v=6)
    if kind == "archer":
        bm_tube(k["wood:0.2:0.6"], [(-0.2, 0.34, 0.36), (-0.2, 0.42, 0.56), (-0.2, 0.44, 0.75), (-0.2, 0.42, 0.94), (-0.2, 0.34, 1.14)], 0.016, n=4)
        bm_beam(k[cloth], (-0.2, 0.05, 0.72), (-0.2, 0.42, 0.75), 0.08, 0.08)
    out = k.emit("ZZ_Mannequin", col, crew, scale=h / 1.15)
    return out
