"""Dwarven building blocks shared by the Deep Forge's machines (dwarf_flame, dwarf_hammer, dwarf_mortar, war_forge).

Exec'd by a tower script after kk_helpers.py (it uses its helpers and the Kit):
    exec(open(os.path.join(REPO, "tools", "blender", "forgeworks_common.py"), encoding="utf-8").read())

What's here: turned shapes (fw_lathe: kegs, barrels, stacks, bands), hand-wound faces and prisms, gears, chains,
rivets, rune glyphs, slab paving cut to the footprint's outline, a smith's bellows that really folds, smoke puffs on
bones, and a few rigging helpers (weights from a function, moving a whole Kit).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

FIRE = "glow:1.0,0.36,0.06,0.7"        # furnace fire, embers
HOT = "glow:1.0,0.6,0.15,0.95"         # molten metal, white-hot iron, sparks
RUNE = "glow:1.0,0.56,0.14,0.9"        # runes
CAST = "stone_dark:0.0:0.75"           # cast iron (the big dark masses: it keeps some shading)
IRON = "iron:0.0:0.55"                 # black iron: bands, straps, rails
BRASS = "gold:0.08:0.62"
STONE = "stone:0.2:0.85"
TIMBER = "wood_dark:0.15:0.8"

_FW_USED = set()


def fw_reset():
    _FW_USED.clear()


def fw_emit(k, name, col, parent=None, **kw):
    """Kit.emit, but it refuses a name used before (mesh_obj quietly replaces an older object of the same name)."""
    if name in _FW_USED:
        raise ValueError("fw_emit: the name %r is used twice" % name)
    _FW_USED.add(name)
    return k.emit(name, col, parent, **kw)


def fw_fx(objs):
    """Parts that come and go (sparks, flames, smoke): never shaded, and they throw no baked shade on the rest."""
    for o in objs:
        o["no_ao"] = True
        o["no_ao_cast"] = True
    return objs


# ------------------------------------------------------------------------------------------- shapes
def fw_frame(axis):
    """(a, x, y): the unit axis and two unit vectors square to it, right-handed (x cross y = a)."""
    a = Vector(axis).normalized()
    u = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
    x = a.cross(u).normalized()
    y = a.cross(x).normalized()
    return a, x, y


def fw_lathe(bm, c, axis, profile, n=10, phase=0.0, cap0=True, cap1=True):
    """Turns a profile [(radius, distance along the axis), ...] round `axis` through c. List it the way you'd draw the
    outside going up (bottom middle -> out -> up -> top middle) and every face points out; a radius of 0 makes a
    point. cap0 / cap1 close open ends with a flat face. Returns the rings of vertices."""
    a, x, y = fw_frame(axis)
    c = Vector(c)
    rings = []
    for r, d in profile:
        if r < 1e-5:
            rings.append([bm.verts.new(c + a * d)])
        else:
            rings.append([bm.verts.new(c + a * d + (x * math.cos(2 * math.pi * (i + phase) / n)
                                                    + y * math.sin(2 * math.pi * (i + phase) / n)) * r) for i in range(n)])
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        for i in range(n):
            j = (i + 1) % n
            if len(ra) == 1:
                bm.faces.new((ra[0], rb[j], rb[i]))
            elif len(rb) == 1:
                bm.faces.new((ra[i], ra[j], rb[0]))
            else:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    if cap0 and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap1 and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return rings


def fw_hoop(bm, c, axis, r, w=0.06, th=0.02, n=10, phase=0.0):
    """A band round a turned shape of radius r at c: `w` wide along the axis, standing `th` proud."""
    return fw_lathe(bm, c, axis, [(r - 0.012, -w / 2), (r + th, -w / 2), (r + th, w / 2), (r - 0.012, w / 2)], n=n, phase=phase,
                    cap0=False, cap1=False)


def fw_ring(bm, c, axis, r_in, r_out, h, n=12, phase=0.0):
    """A closed flat ring (a washer, a track, a wheel rim) standing on c: from r_in to r_out, `h` thick along axis."""
    return fw_lathe(bm, c, axis, [(r_in, 0), (r_out, 0), (r_out, h), (r_in, h), (r_in, 0)], n=n, phase=phase, cap0=False, cap1=False)


def fw_face(bm, pts, inside=None, toward=None):
    """One face through pts (points or vertices), flipped to look away from the point `inside` / along `toward`."""
    vs = [p if isinstance(p, bmesh.types.BMVert) else bm.verts.new(Vector(p)) for p in pts]
    f = bm.faces.new(vs)
    f.normal_update()
    if inside is not None and f.normal.dot(f.calc_center_median() - Vector(inside)) < 0:
        f.normal_flip()
    if toward is not None and f.normal.dot(Vector(toward)) < 0:
        f.normal_flip()
    return f


def fw_prism(bm, pts, vec):
    """A closed solid: the flat outline pts (in any plane, convex or not) pushed along vec."""
    vec = Vector(vec)
    a = [bm.verts.new(Vector(p)) for p in pts]
    b = [bm.verts.new(Vector(p) + vec) for p in pts]
    fs = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((a[j], a[i], b[i], b[j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return fs


def fw_wedge(bm, p0, p1, w, h0, h1, up=(0, 0, 1)):
    """A beam from p0 to p1 standing on that line: `w` wide, h0 tall at p0 and h1 at p1 (a ramp, a buttress, a fin)."""
    p0, p1, u = Vector(p0), Vector(p1), Vector(up).normalized()
    d = (p1 - p0).normalized()
    s = d.cross(u).normalized() * (w * 0.5)
    return fw_prism(bm, [p0 - s, p1 - s, p1 - s + u * max(h1, 1e-4), p0 - s + u * max(h0, 1e-4)], s * 2)


def fw_place(kit, loc=(0, 0, 0), rot_z=0.0, m=None):
    """Moves everything gathered in a Kit so far: turned rot_z degrees about Z, then moved to loc (or by matrix m)."""
    mat = m if m is not None else Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rot_z), 4, "Z")
    for bm in kit.parts.values():
        if bm.verts:
            bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return kit


def fw_merge(dst, src):
    """Pours a Kit's geometry into another (same swatch keys), emptying it."""
    for key, bm in src.parts.items():
        if bm.verts:
            me = bpy.data.meshes.new("_fw_tmp")
            bm.to_mesh(me)
            dst[key].from_mesh(me)
            bpy.data.meshes.remove(me)
        bm.free()
    src.parts = {}
    return dst


def fw_stud(bm, p, nrm, r=0.03, h=0.018):
    """A rivet head on p, facing along nrm."""
    fw_lathe(bm, p, nrm, [(r, -0.004), (r * 0.62, h)], n=4, phase=0.5, cap0=False, cap1=True)


def fw_studs(bm, p0, p1, count, nrm, r=0.03, h=0.018, ends=True):
    """`count` rivets in a row from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    for i in range(count):
        t = (i / (count - 1) if count > 1 else 0.5) if ends else (i + 0.5) / count
        fw_stud(bm, p0.lerp(p1, t), nrm, r, h)


def fw_studs_round(bm, c, axis, r, count, sr=0.03, h=0.018, phase=0.0, arc=(0.0, 360.0)):
    """Rivets round a turned shape of radius r (facing outward), over an arc in degrees."""
    a, x, y = fw_frame(axis)
    c = Vector(c)
    for i in range(count):
        ang = math.radians(arc[0] + (arc[1] - arc[0]) * (i + phase) / count)
        d = x * math.cos(ang) + y * math.sin(ang)
        fw_stud(bm, c + d * r, d, sr, h)


def fw_keg(k, c, axis, r, length, wood="wood:0.2:0.85", hoop=IRON, n=8, hoops=(-0.3, 0.3), lid="wood:0.05:0.5"):
    """A wooden keg centred on c, lying along `axis`: bulging staves, hoops, paler lids set in a little."""
    a = Vector(axis).normalized()
    c = Vector(c)
    L = length
    fw_lathe(k[wood], c, a, [(r * 0.78, -L / 2), (r * 0.94, -L * 0.27), (r, 0.0), (r * 0.94, L * 0.27), (r * 0.78, L / 2)], n=n,
             cap0=False, cap1=False)
    fw_lathe(k[lid], c, a, [(r * 0.78, -L / 2 + 0.025), (r * 0.78, L / 2 - 0.025)], n=n)
    fw_lathe(k[wood], c, a, [(r * 0.66, -L / 2 + 0.025), (r * 0.78, -L / 2)], n=n, cap0=False, cap1=False)
    fw_lathe(k[wood], c, a, [(r * 0.78, L / 2), (r * 0.66, L / 2 - 0.025)], n=n, cap0=False, cap1=False)
    for t in hoops:
        rr = r * (1.0 - 0.22 * (abs(t) / 0.5) ** 1.6)
        fw_hoop(k[hoop], c + a * (t * L), a, rr, w=L * 0.1, th=0.012, n=n)


def fw_gear(bm, c, axis, r, teeth=12, w=0.12, tooth=0.09, hub=0.3, spokes=4, phase=0.0, rim=0.16, hub_w=None):
    """A spur gear centred on c: a rim of outer radius r with `teeth` blunt teeth standing `tooth` proud, a hub
    (radius hub * r) and spokes. w: its thickness along the axis."""
    a, x, y = fw_frame(axis)
    c = Vector(c)
    fw_ring(bm, c - a * (w / 2), a, r * (1 - rim), r, w, n=teeth, phase=phase + 0.5)
    for i in range(teeth):
        ang = 2 * math.pi * (i + phase) / teeth
        d = x * math.cos(ang) + y * math.sin(ang)
        tw = 2 * math.pi * r / teeth
        bm_beam(bm, c + d * (r * math.cos(math.pi / teeth) - 0.02), c + d * (r + tooth), tw * 0.56, w, w1=tw * 0.34, h1=w * 0.9, up=a)
    if hub <= 0.0:
        return
    hw = hub_w if hub_w is not None else w * 1.35
    fw_lathe(bm, c - a * (hw / 2), a, [(r * hub, 0), (r * hub, hw)], n=8)
    for i in range(spokes):
        ang = 2 * math.pi * (i + phase) / spokes
        d = x * math.cos(ang) + y * math.sin(ang)
        bm_beam(bm, c + d * (r * hub * 0.8), c + d * (r * (1 - rim) + 0.01), r * 0.2, w * 0.7, w1=r * 0.15, up=a)


def fw_chain(bm, p0, p1, size=0.09, up=(0, 1, 0), slack=0.0):
    """Chain links from p0 to p1 (every other link turned a quarter). slack: how far its middle sags."""
    p0, p1 = Vector(p0), Vector(p1)
    length = (p1 - p0).length
    n = max(1, int(round(length / (size * 0.8))))
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(p0.lerp(p1, t) - Vector((0, 0, slack * 4 * t * (1 - t))))
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        d = (b - a)
        a2, b2 = a - d * 0.14, b + d * 0.14
        if i % 2:
            bm_beam(bm, a2, b2, size * 0.62, size * 0.24, up=up)
        else:
            bm_beam(bm, a2, b2, size * 0.24, size * 0.62, up=up)
    return n


# ---- runes: glyphs of straight strokes in a box 1 wide and 1.6 tall
FW_RUNES = {
    "fehu": [((-0.3, -0.8), (-0.3, 0.8)), ((-0.3, 0.1), (0.4, 0.62)), ((-0.3, -0.4), (0.4, 0.12))],
    "tiwaz": [((0, -0.8), (0, 0.8)), ((0, 0.8), (-0.45, 0.28)), ((0, 0.8), (0.45, 0.28))],
    "gebo": [((-0.45, -0.7), (0.45, 0.7)), ((-0.45, 0.7), (0.45, -0.7))],
    "algiz": [((0, -0.8), (0, 0.8)), ((0, 0.08), (-0.45, 0.75)), ((0, 0.08), (0.45, 0.75))],
    "othala": [((0, 0.8), (0.42, 0.25)), ((0.42, 0.25), (-0.42, -0.8)), ((0, 0.8), (-0.42, 0.25)), ((-0.42, 0.25), (0.42, -0.8))],
    "dagaz": [((-0.45, -0.6), (-0.45, 0.6)), ((0.45, -0.6), (0.45, 0.6)), ((-0.45, 0.6), (0.45, -0.6)), ((-0.45, -0.6), (0.45, 0.6))],
    "kaun": [((0.3, 0.7), (-0.3, 0.0)), ((-0.3, 0.0), (0.3, -0.7))],
    "thurs": [((-0.25, -0.8), (-0.25, 0.8)), ((-0.25, 0.45), (0.35, 0.05)), ((0.35, 0.05), (-0.25, -0.35))],
    "hagal": [((-0.35, -0.8), (-0.35, 0.8)), ((0.35, -0.8), (0.35, 0.8)), ((-0.35, 0.28), (0.35, -0.28))],
    "sowil": [((0.3, 0.8), (-0.3, 0.26)), ((-0.3, 0.26), (0.3, -0.26)), ((0.3, -0.26), (-0.3, -0.8))],
    "ing": [((0, 0.62), (0.42, 0)), ((0.42, 0), (0, -0.62)), ((0, -0.62), (-0.42, 0)), ((-0.42, 0), (0, 0.62))],
    "isa": [((0, -0.8), (0, 0.8))],
    "nauth": [((0, -0.8), (0, 0.8)), ((-0.38, 0.3), (0.38, -0.3))],
    "eihwaz": [((0, -0.8), (0, 0.8)), ((0, 0.8), (0.4, 0.4)), ((0, -0.8), (-0.4, -0.4))],
}
FW_RUNE_ROW = ["tiwaz", "othala", "fehu", "algiz", "dagaz", "thurs", "ing", "hagal", "gebo", "sowil", "eihwaz", "nauth", "kaun"]


def fw_rune(bm, c, right, up, size, glyph, stroke=0.16, th=0.012):
    """A rune of flat strokes on the plane through c spanned by right and up (it faces right x up), `size` wide
    and 1.6 * size tall. glyph: a name in FW_RUNES, or a number (taken round FW_RUNE_ROW)."""
    c, r, u = Vector(c), Vector(right).normalized(), Vector(up).normalized()
    nrm = r.cross(u).normalized()
    if not isinstance(glyph, str):
        glyph = FW_RUNE_ROW[int(glyph) % len(FW_RUNE_ROW)]
    for (x0, y0), (x1, y1) in FW_RUNES[glyph]:
        a = c + r * (x0 * size) + u * (y0 * size)
        b = c + r * (x1 * size) + u * (y1 * size)
        d = (b - a).normalized() * (stroke * size * 0.35)
        bm_beam(bm, a - d + nrm * (th * 0.4), b + d + nrm * (th * 0.4), stroke * size, th * 2, up=nrm)


# ------------------------------------------------------------------------------------------- paving
def _fw_clip(poly, a, b):
    """The part of a flat polygon (2D Vectors, anticlockwise) to the left of the line a -> b."""
    out = []
    d = b - a
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        sp = d.x * (p.y - a.y) - d.y * (p.x - a.x)
        sq = d.x * (q.y - a.y) - d.y * (q.x - a.x)
        if sp >= 0.0:
            out.append(p)
        if (sp > 0.0 and sq < 0.0) or (sp < 0.0 and sq > 0.0):
            out.append(p + (q - p) * (sp / (sp - sq)))
    return out


def fw_hex_polys(cells, inset):
    """One convex polygon per hex of a footprint: the hex, pulled in by `inset` along its edges on the footprint's
    outside (together they cover exactly outline(cells, inset))."""
    mid = footprint_mid(cells)
    full = outline(cells, 0.0)
    out = []
    for q, s in cells:
        c = hex_to_world(q, s, mid)
        cs = [Vector((p.x, p.y)) for p in hex_corners(c)]
        c2 = Vector((c.x, c.y))
        poly = list(cs)
        for i in range(6):
            a, b = cs[i], cs[(i + 1) % 6]
            m = (a + b) * 0.5
            nrm = (m - c2).normalized()
            probe = m + nrm * 0.06
            if not inside(full, probe.x, probe.y):
                poly = _fw_clip(poly, a - nrm * inset, b - nrm * inset)
        out.append(poly)
    return out


def _fw_area(poly):
    return 0.5 * abs(sum(poly[i].x * poly[(i + 1) % len(poly)].y - poly[(i + 1) % len(poly)].x * poly[i].y for i in range(len(poly))))


def fw_paving(bm, rnd, cells, z, h=0.045, sx=0.46, sy=0.3, inset=0.26, gap=0.024, skip=None, turn=0.0, jit=0.2):
    """A floor of cut stone slabs (running bond, sx by sy, the grid turned `turn` degrees) over a footprint, cut clean
    along its outline pulled in by `inset`. skip(x, y) -> True leaves a slab out (under a building). Lay a dark bed
    under it (fw_bed) so the joints read. Returns the number of slabs."""
    polys = fw_hex_polys(cells, inset)
    loop = outline(cells, inset + 0.002)
    R = max(p.length for p in outline(cells, 0.0)) + sx
    ca, sa = math.cos(math.radians(turn)), math.sin(math.radians(turn))

    def rot(x, y):
        return Vector((x * ca - y * sa, x * sa + y * ca))
    count, row, y = 0, 0, -R
    while y < R:
        x = -R - (sx * 0.5 if row % 2 else 0.0)
        while x < R:
            g = gap * 0.5
            corners = [rot(x + g, y + g), rot(x + sx - g, y + g), rot(x + sx - g, y + sy - g), rot(x + g, y + sy - g)]
            cen = rot(x + sx / 2, y + sy / 2)
            x += sx
            if cen.length > R or (skip and skip(cen.x, cen.y)):
                continue
            ins = [inside(loop, p.x, p.y) for p in corners]
            if all(ins):
                pieces = [corners]
            elif not any(ins) and not inside(loop, cen.x, cen.y):
                continue
            else:
                pieces = []
                for poly in polys:
                    pc = corners
                    for i in range(len(poly)):
                        pc = _fw_clip(pc, poly[i], poly[(i + 1) % len(poly)])
                        if len(pc) < 3:
                            break
                    if len(pc) >= 3 and _fw_area(pc) > 0.008:
                        pieces.append(pc)
            zt = z + h * (1.0 + rnd.uniform(-jit, jit))
            for pc in pieces:
                top = [bm.verts.new((p.x, p.y, zt)) for p in pc]
                bot = [bm.verts.new((p.x, p.y, z - 0.004)) for p in pc]
                bm.faces.new(top)
                for i in range(len(pc)):
                    j = (i + 1) % len(pc)
                    bm.faces.new((bot[i], bot[j], top[j], top[i]))
                count += 1
        y += sy
        row += 1
    return count


def fw_bed(bm, cells, z, h=0.016, inset=0.25):
    """The dark bed under fw_paving (what shows in the joints): the footprint's outline as one low slab."""
    return prism(bm, outline(cells, inset), z - 0.02, z + h)


# ------------------------------------------------------------------------------------------- the bellows
def fw_bellows(hinge, back, L, W, open_deg, board=TIMBER, top="team!:0.1:0.7", leather="tan:0.2:0.95", th=0.05, neck=0.1,
               nozzle=0.3, studs=True):
    """A smith's bellows: two pear-shaped boards hinged at the nozzle (at `hinge`), `L` long toward `back`, `W` wide,
    standing open by open_deg, with pleated leather between. Returns {"bottom", "top", "leather": Kits, "axis": the
    hinge's axis, "frac": a function (vertex position) -> 0 on the bottom board .. 1 on the top board}: emit the top
    Kit on the bellows bone, skin the leather with fw_skin and `frac`, and fold it with fw_bellows_pose."""
    hinge = Vector(hinge)
    back = Vector(back).normalized()
    axis = back.cross(Vector((0, 0, 1))).normalized()       # turning `back` about this by +angle lifts the tail
    nrm = axis.cross(back).normalized()
    theta = math.radians(open_deg)

    def frame(f):
        q = Quaternion(axis, theta * f)
        return q @ back, q @ nrm

    def pear(grow=1.0, strip=False):
        pts = [] if strip else [(0.0, -neck)]
        pts.append((0.16 * L, -neck * 1.3 * (grow if strip else 1.0)))
        sc, ra, rb = 0.6 * L, 0.4 * L, W * 0.5
        for i in range(7):
            ang = math.radians(-90 + 30 * i)
            pts.append((sc + ra * math.cos(ang) * grow, rb * math.sin(ang) * grow))
        pts.append((0.16 * L, neck * 1.3 * (grow if strip else 1.0)))
        if not strip:
            pts.append((0.0, neck))
        return pts
    kb, kt, kl = Kit(), Kit(), Kit()
    b0, n0 = frame(0.0)
    b1, n1 = frame(1.0)
    fw_prism(kb[board], [hinge + b0 * s + axis * w for s, w in pear()], -n0 * th)
    fw_prism(kt[top], [hinge + b1 * s + axis * w for s, w in pear()], n1 * th)
    # the leather: rings of the boards' outline at five openings, bulging and creased in turn
    grows = (0.96, 1.07, 0.9, 1.07, 0.9, 1.07, 0.96)
    rings = []
    for i, g in enumerate(grows):
        bf, nf = frame(i / (len(grows) - 1))
        rings.append([hinge + bf * s + axis * w for s, w in pear(g, strip=True)])
    core = hinge + frame(0.5)[0] * (0.6 * L)
    for ra_, rb_ in zip(rings, rings[1:]):
        for i in range(len(ra_) - 1):
            fw_face(kl[leather], (ra_[i], ra_[i + 1], rb_[i + 1], rb_[i]), inside=core)
    # the nozzle: an iron snout with a brass collar, forward of the hinge; an iron strap across the neck
    fw_lathe(kb[IRON], hinge - b0 * 0.02 + n0 * 0.0, -b0, [(neck * 1.05, 0.0), (neck * 0.62, nozzle)], n=8, cap0=True, cap1=True)
    fw_hoop(kb[BRASS], hinge - b0 * (nozzle * 0.3), -b0, neck * 0.94, w=0.06, th=0.02, n=8)
    bm_beam(kb[IRON], hinge + b0 * 0.05 - axis * (neck * 1.5), hinge + b0 * 0.05 + axis * (neck * 1.5), 0.12, 0.2, up=n0)
    # the top board's ironwork: a strap down the middle, studs round the rim, a handle bar at the tail
    bm_beam(kt[IRON], hinge + b1 * (0.08 * L) + n1 * (th + 0.008), hinge + b1 * (0.97 * L) + n1 * (th + 0.008), 0.09, 0.022, up=n1)
    if studs:
        for s, w in pear(0.86, strip=True)[1:-1]:
            fw_stud(kt[BRASS], hinge + b1 * s + axis * w + n1 * th, n1, r=0.035, h=0.022)
    for sg in (-1, 1):
        bm_beam(kt[IRON], hinge + b1 * (0.96 * L) + axis * (sg * W * 0.2) + n1 * (th * 0.5),
                hinge + b1 * (1.08 * L) + axis * (sg * W * 0.2) + n1 * (th * 0.5), 0.05, 0.05, up=n1)
    bm_beam(kt[board], hinge + b1 * (1.08 * L) - axis * (W * 0.3) + n1 * (th * 0.5),
            hinge + b1 * (1.08 * L) + axis * (W * 0.3) + n1 * (th * 0.5), 0.07, 0.07, up=n1)

    def frac(co):
        d = Vector(co) - hinge
        ang = math.atan2(d.dot(nrm), max(d.dot(back), 1e-6))
        return min(max(ang / theta, 0.0), 1.0)
    return {"bottom": kb, "top": kt, "leather": kl, "axis": axis, "frac": frac, "hinge": hinge, "back": back, "open": open_deg}


def fw_bellows_pose(rig, bone, axis, squeeze):
    """Folds a bellows' top board down by `squeeze` degrees from its open rest."""
    pb = rig.pose.bones[bone]
    pb.rotation_quaternion = arm_space_quat(pb, tuple(axis), -squeeze)


def fw_skin(obj, rig, fn):
    """Skins obj to rig with weights from fn(vertex position) -> {bone name: weight}."""
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    for m in [m for m in obj.modifiers if m.type == "ARMATURE"]:
        obj.modifiers.remove(m)
    obj.vertex_groups.clear()
    groups = {}
    for v in obj.data.vertices:
        ws = {b: w for b, w in fn(v.co).items() if w > 1e-4}
        total = sum(ws.values()) or 1.0
        for b, w in ws.items():
            if b not in groups:
                groups[b] = obj.vertex_groups.new(name=b)
            groups[b].add([v.index], w / total, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return obj


# ------------------------------------------------------------------------------------------- smoke
def fw_puff_bones(bones, name, at, n=3, parent="root"):
    """Adds bones name.0 .. name.N-1 at `at` (a chimney's mouth) to a BONES dict: one per smoke puff."""
    at = Vector(at)
    for i in range(n):
        bones["%s.%d" % (name, i)] = (tuple(at), tuple(at + Vector((0, 0, 0.2))), parent)
    return bones


def fw_puffs(name, col, rig, bone, at, n=3, r=0.17, swatch="stone:0.0:0.4", seed=3):
    """The smoke puffs for fw_puff_bones(bones, bone, at, n): one lumpy ball per bone, sitting in the chimney's mouth."""
    rnd = random.Random(seed)
    k = Kit()
    out = []
    for i in range(n):
        bm_blob(k[swatch], rnd, Vector(at), r, squash=(1.0, 1.0, 0.85), jitter=0.16, sub=2)
        out += fw_fx(fw_emit(k, "%s%d" % (name, i), col, rig=rig, bone="%s.%d" % (bone, i)))
    return out


def fw_puff_pose(rig, name, n, t, rise=0.9, drift=(0.2, 0.0), size=(0.45, 1.5), burst=0.0):
    """Poses the puffs at time t (one puff's whole life = t going 0..1; they follow each other evenly): each swells
    out of the mouth, climbs `rise`, leans along `drift` and thins away to nothing. burst: fatter (a shot)."""
    for i in range(n):
        u = (t + i / float(n)) % 1.0
        pb = rig.pose.bones["%s.%d" % (name, i)]
        s = max(0.001, (math.sin(math.pi * u) ** 0.6) * (size[0] + (size[1] - size[0]) * u) * (1.0 + burst))
        pb.scale = (s, s, s)
        pb.location = arm_space_loc(pb, (drift[0] * u * u, drift[1] * u * u, rise * u))
