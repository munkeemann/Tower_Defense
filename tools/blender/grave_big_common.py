"""The big Bone Legion towers' shared kit (bone_colossus, mass_grave, necromancer). Exec'd by those scripts after
kk_helpers.py:

    exec(open(os.path.join(REPO, "tools", "blender", "grave_big_common.py"), encoding="utf-8").read())

Placing (xf, frame, stamp: build a piece in its own space, then set it down anywhere), a plinth with pits cut into it
(plinth_cut, pit_lining), ruined coursed walls and piers, crypt paving, heaps (earth, bones), skulls, long bones,
gravestones, coffins, soul flames and braziers, skeletal hands and whole arms reaching out of the ground (reach_arm,
arm_bones, pose_arm), chains, hanging cloth, six-sided stepped platforms (hex_course), flat glowing rings and bands
(bm_annulus, bm_ribbon), and Fk: posing a rig by goals in armature space (limbs reach for points with two-bone IK while
the body moves). Preview aid: crew_standin() stands a plain figure at a Crew marker when GRAVE_CREW is set.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

# ---- the Bone Legion's palette
BONE = "cream:0.06:0.78"            # fresh bone
BONE_OLD = "beige:0.12:0.92"        # weathered bone (heaps, old graves)
BONE_DARK = "taupe:0.2:0.95"        # stained bone, horn
STONE = "stone_dark:0.08:0.8"       # dark crypt stone
STONE_LT = "stone2:0.2:0.9"         # paler, weathered blocks among it
SOCKET = "black:0.45:0.85"          # eye holes, pits
EARTH = "taupe_dark:0.35:0.95"      # dug earth
EARTH_LT = "wood_dark:0.3:0.9"      # drier spoil
RUST = "wood:0.45:0.98"             # rusted iron
IRON = "iron:0.15:0.8"
SOULFIRE = (0.36, 1.0, 0.3)         # sickly green soul-fire
SOULCORE = (0.78, 1.0, 0.55)        # its pale heart
VIOLET = (0.66, 0.4, 1.0)


def glow(c, s=0.9):
    """A Kit key for a glowing color."""
    return "glow:%.3f,%.3f,%.3f,%.2f" % (c[0], c[1], c[2], s)


# ---------------------------------------------------------------------------------------------- placing
def xf(loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    """A placement: scale, then turn (degrees about X, Y, Z), then move."""
    s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    return (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
            @ Matrix.Diagonal((s[0], s[1], s[2], 1.0)))


def frame(origin, fwd, up=(0, 0, 1), scale=1.0):
    """A placement whose +Y looks along fwd and whose +Z leans toward up."""
    y = Vector(fwd).normalized()
    x = y.cross(Vector(up))
    if x.length < 1e-4:
        x = y.orthogonal()
    x.normalize()
    z = x.cross(y)
    m = Matrix((x, y, z)).transposed().to_4x4()
    return Matrix.Translation(Vector(origin)) @ m @ Matrix.Diagonal((scale, scale, scale, 1.0))


def bm_merge(dst, src, M=None):
    """Adds bmesh src (moved by M) to dst and frees it."""
    if M is not None:
        bmesh.ops.transform(src, matrix=M, verts=src.verts)
        if M.to_3x3().determinant() < 0:
            bmesh.ops.reverse_faces(src, faces=src.faces)
    me = bpy.data.meshes.new("_merge")
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return dst


def stamp(dst, src, M=None):
    """Sets everything gathered in Kit src down in Kit dst, moved by M (src is emptied)."""
    for key, bm in src.parts.items():
        if bm.verts:
            bm_merge(dst[key], bm, M)
        else:
            bm.free()
    src.parts = {}
    return dst


def facet(bm):
    """Splits every face of bm off on its own, so Kit.emit(vary=...) shades each facet apart (earth, heaps)."""
    bmesh.ops.split_edges(bm, edges=bm.edges[:])
    return bm


def bm_disc(bm, c, nrm, r, n=6, ry=None, up=(0, 0, 1), phase=0.0):
    """A flat n-gon at c facing nrm (one face)."""
    c, nrm = Vector(c), Vector(nrm).normalized()
    x = Vector(up).cross(nrm)
    if x.length < 1e-4:
        x = nrm.orthogonal()
    x.normalize()
    y = nrm.cross(x)
    ry = r if ry is None else ry
    vs = [bm.verts.new(c + x * (math.cos(2 * math.pi * (i + phase) / n) * r) + y * (math.sin(2 * math.pi * (i + phase) / n) * ry))
          for i in range(n)]
    return bm.faces.new(vs)


def bm_annulus(bm, c, r0, r1, z, seg=24, a0=0.0, a1=360.0):
    """A flat ring (or an arc of one, from a0 to a1 degrees) at height z, facing up: one face per segment."""
    c = Vector(c)
    for i in range(seg):
        t0, t1 = math.radians(a0 + (a1 - a0) * i / seg), math.radians(a0 + (a1 - a0) * (i + 1) / seg)
        bm.faces.new([bm.verts.new((c.x + r * math.cos(t), c.y + r * math.sin(t), z)) for r, t in ((r0, t0), (r1, t0), (r1, t1), (r0, t1))])
    return bm


def bm_ribbon(bm, pts, across, w, both=True):
    """A flat band `w` wide laid along the points (up and down steps with them), across the direction `across`. Level
    stretches face up; steep ones get both faces if `both`."""
    a = Vector(across).normalized() * (w * 0.5)
    pts = [Vector(p) for p in pts]
    for p, q in zip(pts, pts[1:]):
        vs = [p - a, p + a, q + a, q - a]
        f = bm.faces.new([bm.verts.new(v) for v in vs])
        f.normal_update()
        if f.normal.z < -1e-4:
            f.normal_flip()
        if both and abs(f.normal.z) < 0.5:
            bm.faces.new([bm.verts.new(v) for v in reversed(vs)])
    return bm


def hex_pts(c, apothem, z=0.0):
    """The corners of a flat-top hexagon (as the map's) round c, counterclockwise from the one at +X."""
    r = apothem / math.cos(math.radians(30))
    return [Vector((c[0] + r * math.cos(math.radians(60 * i)), c[1] + r * math.sin(math.radians(60 * i)), z)) for i in range(6)]


def hex_course(k, rnd, c, apothem, depth, z, h, per_side=3, keys=(STONE,), gap=0.02, jit=0.01):
    """One course of a six-sided platform in the map's hexagon: blocks along each side between the outline at
    `apothem` and one `depth` further in, mitred at the corners, from z to z + h."""
    out, inn = hex_pts(c, apothem), hex_pts(c, apothem - depth)
    for j in range(6):
        a, b, ia, ib = out[j], out[(j + 1) % 6], inn[j], inn[(j + 1) % 6]
        for i in range(per_side):
            t0, t1 = i / per_side, (i + 1) / per_side
            g0, g1 = gap * 0.5 / (b - a).length, gap * 0.5 / (b - a).length
            pts = [a.lerp(b, t0 + g0), a.lerp(b, t1 - g1), ia.lerp(ib, t1 - g1), ia.lerp(ib, t0 + g0)]
            push = (a.lerp(b, 0.5) - Vector((c[0], c[1], 0))).normalized() * rnd.uniform(-jit, jit)
            prism(k[keys[(i + j) % len(keys)]], [q + push for q in pts], z + rnd.uniform(0, jit * 0.5), z + h - rnd.uniform(0, jit))
    return k


def crew_standin(col, parent, h=1.3):
    """(Previews only: when the environment has GRAVE_CREW set.) A plain robed figure with a staff where the game
    will stand the tower's crew, so a sheet shows what he hides and what frames him."""
    if not os.environ.get("GRAVE_CREW"):
        return None
    k = Kit()
    bm_cyl(k["taupe_dark:0.2:0.9"], 0.26, 0.13, h * 0.68, (0, 0, h * 0.34), seg=8)
    bm_ellipsoid(k[BONE], (0, 0.02, h * 0.82), (0.15, 0.16, 0.17), u=8, v=5)
    bm_cyl(k["taupe_dark:0.2:0.9"], 0.2, 0.05, 0.3, (0, -0.03, h * 0.9), seg=7)
    bm_beam(k["wood_dark:0.2:0.8"], (0.3, 0.3, 0.0), (0.3, 0.34, 1.3), 0.04, 0.04)
    return k.emit("Crew_Standin", col, parent)


def bm_lump(bm, rnd, c, r, squash=(1.0, 1.0, 1.0), rot=(0, 0, 0), n=11):
    """A faceted lump centred on c (a boulder that needn't sit on the ground): bone knobs, plates, knuckles, clods."""
    t = bmesh.new()
    bm_boulder(t, rnd, (0, 0, 0), r, squash=squash, n=n, sink=0.0)
    zs = [v.co.z for v in t.verts]
    mid = (min(zs) + max(zs)) * 0.5
    return bm_merge(bm, t, xf(c, rot) @ Matrix.Translation((0, 0, -mid)))


# ---------------------------------------------------------------------------------------------- ground
def _cdt_fill(bm, loops, z, holes=(), grid=0.24, lump=0.0, rnd=None, ring_verts=None):
    """Fills the outline loops[0] (counterclockwise) at height z with small triangles, leaving the holes open.
    ring_verts: BMVerts already standing on loops[0] (they're reused). lump: the inner points' random lift."""
    from mathutils import geometry
    outer = [Vector((p[0], p[1], 0)) for p in loops[0]]
    hs = [[Vector((p[0], p[1], 0)) for p in h] for h in holes]
    co, edges = [], []
    for loop in [outer] + hs:
        base = len(co)
        co.extend(Vector((p.x, p.y)) for p in loop)
        edges.extend((base + i, base + (i + 1) % len(loop)) for i in range(len(loop)))
    nfix = len(co)
    segs = [(co[a], co[b]) for a, b in edges]

    def edge_dist(p):
        best = 9.0
        for a, b in segs:
            t = min(max((p - a).dot(b - a) / max((b - a).length_squared, 1e-9), 0.0), 1.0)
            best = min(best, (a + (b - a) * t - p).length)
        return best
    xs, ys = [p.x for p in outer], [p.y for p in outer]
    row, y = 0, min(ys) + grid * 0.5
    while y < max(ys):
        x = min(xs) + (grid * 0.5 if row % 2 else grid)
        while x < max(xs):
            p = Vector((x, y))
            if inside(outer, x, y) and not any(inside(h, x, y) for h in hs) and edge_dist(p) > grid * 0.4:
                co.append(p)
            x += grid
        y += grid * 0.866
        row += 1
    vs, _, fs, _, _, _ = geometry.delaunay_2d_cdt(co, edges, [], 1, 1e-5)
    made = {}
    for i, p in enumerate(vs):
        best = None
        if ring_verts is not None:
            for j in range(len(outer)):
                if (co[j] - p).length < 1e-4:
                    best = ring_verts[j]
                    break
        if best is None:
            fixed = any((co[j] - p).length < 1e-4 for j in range(nfix))
            dz = 0.0 if fixed or not lump else rnd.uniform(-lump, lump)
            best = bm.verts.new((p.x, p.y, z + dz))
        made[i] = best
    for f in fs:
        c = (vs[f[0]] + vs[f[1]] + vs[f[2]]) / 3.0
        if any(inside(h, c.x, c.y) for h in hs):
            continue
        tri = [made[i] for i in f]
        if len(set(tri)) == 3:
            face = bm.faces.new(tri)
            if face.calc_area() > 1e-9 and Vector(face.normal).z < 0:
                face.normal_flip()
    return bm


def plinth_cut(cells, col, root, top=0.34, holes=(), name="Base", grid=0.24):
    """kk_helpers.plinth with pits: the same knoll under the footprint, its top left open over each outline in holes
    (lists of (x, y), counterclockwise). Line the pits with pit_lining. Returns the top's height."""
    bm = bmesh.new()
    rings = []
    for ins, z in ((0.05, -0.06), (0.1, top - 0.075), (0.16, top)):
        loop = outline(cells, ins)
        fine = []
        for i, p in enumerate(loop):
            q = loop[(i + 1) % len(loop)]
            fine.extend(p.lerp(q, k / 4.0) for k in range(4))
        rings.append([bm.verts.new((p.x, p.y, z)) for p in fine])
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):                      # (no bottom face: it's under the ground)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    _cdt_fill(bm, [[(v.co.x, v.co.y) for v in rings[2]]], top, holes=holes, ring_verts=rings[2], grid=grid)
    o = mesh_obj(name + "_Plinth", bm, col, root)
    o["ground"] = True
    paint_ground(o)
    return top


def smooth_loop(pts, rounds=1, k=0.25):
    """Cuts the corners of a closed outline (Chaikin)."""
    pts = [Vector((p[0], p[1], 0)) for p in pts]
    for _ in range(rounds):
        out = []
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            out.append(p.lerp(q, k))
            out.append(p.lerp(q, 1.0 - k))
        pts = out
    return pts


def inset_loop(pts, d):
    """A counterclockwise outline pulled in by d (out for d < 0)."""
    pts = [Vector((p[0], p[1], 0)) for p in pts]
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d0, d1 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n0, n1 = Vector((-d0.y, d0.x, 0)), Vector((-d1.y, d1.x, 0))
        bis = n0 + n1
        bis = bis / max(bis.length, 1e-6)
        out.append(p1 + bis * (d / max(bis.dot(n0), 0.35)))
    return out


def pit_lining(wall_bm, floor_bm, loop, z_top, z_floor, batter=0.05, rnd=None, lump=0.012, grid=0.22, lip=0.02):
    """The inside of a pit cut with plinth_cut: sides from the rim (a hair above z_top, so no gap shows) down to a
    floor of small triangles (a little uneven)."""
    rim = [Vector((p[0], p[1], 0)) for p in loop]
    foot = inset_loop(rim, batter)
    n = len(rim)
    top = [wall_bm.verts.new((p.x, p.y, z_top + lip)) for p in rim]
    bot = [wall_bm.verts.new((p.x, p.y, z_floor)) for p in foot]
    for i in range(n):
        j = (i + 1) % n
        wall_bm.faces.new((top[i], top[j], bot[j], bot[i]))        # facing into the pit
    _cdt_fill(floor_bm, [[(p.x, p.y) for p in foot]], z_floor, grid=grid, lump=lump, rnd=rnd or random.Random(3))
    return foot


def bm_heap(bm, rnd, height, bounds, z=0.0, grid=0.2, jit=0.3, skirt=0.04, noise=0.0):
    """A mound: a mesh of triangles over a jittered grid wherever height(x, y) > 0 (inside bounds x0, y0, x1, y1),
    lifted to z + height; its rim is tucked `skirt` under z. noise: random extra lift (lumps)."""
    from mathutils import geometry
    x0, y0, x1, y1 = bounds
    co, hs = [], []
    row, y = 0, y0
    while y <= y1 + 1e-6:
        x = x0 + (grid * 0.5 if row % 2 else 0.0)
        while x <= x1 + 1e-6:
            px, py = x + rnd.uniform(-jit, jit) * grid, y + rnd.uniform(-jit, jit) * grid
            h = height(px, py)
            co.append(Vector((px, py)))
            hs.append(h + (rnd.uniform(-noise, noise) if h > noise else 0.0) if h > 0 else h)
            x += grid
        y += grid * 0.866
        row += 1
    if len(co) < 3:
        return bm
    vs, _, fs, _, _, _ = geometry.delaunay_2d_cdt(co, [], [], 0, 1e-5)
    hv = []
    for p in vs:
        best = min(range(len(co)), key=lambda j: (co[j] - p).length_squared)
        hv.append(hs[best])
    made = {}
    for f in fs:
        if not any(hv[i] > 0 for i in f):
            continue
        if max((vs[f[a]] - vs[f[b]]).length for a, b in ((0, 1), (1, 2), (2, 0))) > grid * 2.6:
            continue                                        # (a sliver along the hull of the grid)
        tri = []
        for i in f:
            if i not in made:
                made[i] = bm.verts.new((vs[i].x, vs[i].y, z + (hv[i] if hv[i] > 0 else -skirt)))
            tri.append(made[i])
        face = bm.faces.new(tri)
        if face.calc_area() > 1e-9 and Vector(face.normal).z < 0:
            face.normal_flip()
    return bm


def bm_slabs(bm, rnd, where, bounds, z, size=0.44, gap=0.03, h=0.045, keep=1.0, yaw=0.0, heave=0.0, origin=(0, 0)):
    """Crypt paving: rectangular slabs in half-bonded rows (turned by yaw about origin), wherever where(x, y) is True
    at a slab's middle. heave: how far slabs are tipped and lifted (broken floors)."""
    x0, y0, x1, y1 = bounds
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    r = max(x1 - x0, y1 - y0)
    row, v = 0, -r
    while v <= r:
        u = -r + (size * 0.5 if row % 2 else 0.0)
        while u <= r:
            w = size * rnd.choice((1.0, 1.0, 0.5)) if rnd.random() < 0.25 else size
            cx, cy = origin[0] + (u + w * 0.5) * ca - (v + size * 0.3) * sa, origin[1] + (u + w * 0.5) * sa + (v + size * 0.3) * ca
            if x0 <= cx <= x1 and y0 <= cy <= y1 and where(cx, cy) and rnd.random() < keep:
                t = bmesh.new()
                hh = h * rnd.uniform(0.75, 1.2)
                bm_box(t, (w - gap, size * 0.6 - gap, hh), (0, 0, hh * 0.5))
                t.normal_update()
                bmesh.ops.delete(t, geom=[f for f in t.faces if f.normal.z < -0.9], context="FACES")
                tip = (rnd.uniform(-1, 1) * heave * 9, rnd.uniform(-1, 1) * heave * 9, yaw + rnd.uniform(-1.5, 1.5))
                bm_merge(bm, t, xf((cx, cy, z + abs(rnd.uniform(0, heave)) * 0.06), tip))
            u += w
        v += size * 0.6
        row += 1
    return bm


# ---------------------------------------------------------------------------------------------- masonry
def ruin_wall(k, rnd, p0, p1, z0, top, th=0.22, course=0.19, block=0.36, stone=STONE, pale=STONE_LT, core=SOCKET,
              holes=(), gap=0.016, jit=0.012, foot=None, back=None, side=1, core_step=0.45):
    """A ruined wall of coursed blocks from p0 to p1 (x, y), standing on z0 (core None: no dark core behind the
    joints, for low curbs). top: its height above z0 (a number, or
    a function of t = 0..1 along the wall): the blocks stop in steps where the wall has fallen. holes: (t0, t1, za, zb)
    openings left out of the blocks: niches, open toward the wall's left (side 1) or right (-1) and closed at the
    other face by a panel (Kit key `back`, default the core's). foot(t): how far below z0 the wall's foot goes (a wall
    over a slope or a pit). Every fifth block or so is paler stone."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    ax = d / L
    nr = Vector((-ax.y, ax.x, 0))
    tf = top if callable(top) else (lambda t: top)
    ff = foot if callable(foot) else (lambda t: foot or 0.0)
    hmax = max(tf(i / 24.0) for i in range(25))
    rows = int(math.ceil(hmax / course - 0.3))
    cols = max(1, round(L / block))
    bw = L / cols

    def box(bm, a, b, za, zb, t, lean=0.0):
        vs = []
        for z in (za, zb):
            for s, side in ((a, -1), (b, -1), (b, 1), (a, 1)):
                q = p0 + ax * s + nr * (side * t + (lean if z == zb else 0.0))
                vs.append(bm.verts.new((q.x, q.y, z)))
        lo, hi = vs[:4], vs[4:]
        bm.faces.new(hi)                                    # (no bottom face: it never shows)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    for r in range(rows):
        edges = [0.0] + [min(L, (i + (0.5 if r % 2 else 0.0)) * bw) for i in range(1, cols + (1 if r % 2 else 0))] + [L]
        edges = sorted(set(round(e, 5) for e in edges))
        za, zb = r * course, (r + 1) * course
        for a, b in zip(edges, edges[1:]):
            spans = [(a, b)]
            for t0, t1, ha, hb in holes:
                if ha - 0.02 < (za + zb) * 0.5 < hb + 0.02:
                    nxt = []
                    for u, v in spans:
                        if t1 * L <= u or t0 * L >= v:
                            nxt.append((u, v))
                        else:
                            if t0 * L - u > 0.07:
                                nxt.append((u, t0 * L))
                            if v - t1 * L > 0.07:
                                nxt.append((t1 * L, v))
                    spans = nxt
            for u, v in spans:
                if v - u < gap * 3:
                    continue
                tm = (u + v) * 0.5 / L
                h = tf(tm)
                if h < za + course * 0.55:
                    continue
                edge = h < zb + course * 0.6           # a block on the broken edge: sometimes gone, or knocked askew
                if edge and rnd.random() < 0.16:
                    continue
                bm = k[pale if rnd.random() < 0.2 else stone]
                zlo = z0 + za + rnd.uniform(0, jit * 0.5) if r else z0 - ff(tm)
                box(bm, u + gap * 0.5, v - gap * 0.5, zlo, z0 + zb - gap * 0.6 - (rnd.uniform(0, 0.04) if edge else 0.0),
                    th * 0.5 + rnd.uniform(-jit, jit), lean=rnd.uniform(-0.02, 0.02) if edge else 0.0)
    cuts = sorted(set([i / max(1, int(round(L / core_step))) for i in range(max(1, int(round(L / core_step))) + 1)]
                      + [t for hole in holes for t in hole[:2]]))
    for t0, t1 in zip(cuts, cuts[1:]):                  # the dark core that shows in the joints
        if t1 - t0 < 1e-4 or core is None:
            continue
        tm = (t0 + t1) * 0.5
        h = min(tf(t0), tf(tm), tf(t1))
        h = math.floor(h / course + 0.45) * course - 0.05
        if h <= 0.06:
            continue
        spans = [(-ff(tm) + 0.01, h)]
        for ht0, ht1, ha, hb in holes:
            if ht0 - 1e-4 <= tm <= ht1 + 1e-4:
                spans = [x for a, b in spans for x in ((a, min(b, ha)), (max(a, hb), b)) if x[1] - x[0] > 0.02]
        for a, b in spans:
            box(k[core], t0 * L, t1 * L, z0 + a, z0 + b, th * 0.3)
    for ht0, ht1, ha, hb in holes:                      # the niches' backs
        if back is None and core is None:
            continue
        vs = []
        off = -side * (th * 0.5 - 0.03)
        for z in (z0 + ha, z0 + hb):
            for s_, sd in ((ht0 * L, -1), (ht1 * L, -1), (ht1 * L, 1), (ht0 * L, 1)):
                q = p0 + ax * s_ + nr * (off + sd * 0.012)
                vs.append(k[back or core].verts.new((q.x, q.y, z)))
        bm = k[back or core]
        lo, hi = vs[:4], vs[4:]
        bm.faces.new(list(reversed(lo)))
        bm.faces.new(hi)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return k


def pier(k, rnd, c, w, z0, h, stone=STONE, pale=STONE_LT, course=0.2, cap="flat", gap=0.016, yaw=0.0, core=SOCKET):
    """A square pier of coursed blocks at c (w wide, h tall, standing on z0); every other course is split the other
    way. cap: "flat" (a capstone), "point" (a low pyramid on it), or None (a broken top)."""
    c = Vector((c[0], c[1], 0))
    t = Kit()
    rows = max(1, int(round(h / course)))
    ch = h / rows
    for r in range(rows):
        z = r * ch
        if cap is None and r == rows - 1:               # the broken top: one leaning half-block
            bm_box(t[stone], (w * 0.5, w - gap, ch * 0.8), (-w * 0.24, 0, z + ch * 0.4), (0, rnd.uniform(-8, 8), 0))
            continue
        for s in (-1, 1):
            size = (w * 0.5 - gap, w - gap, ch - gap) if r % 2 else (w - gap, w * 0.5 - gap, ch - gap)
            off = (s * w * 0.25, 0) if r % 2 else (0, s * w * 0.25)
            j = rnd.uniform(-0.008, 0.012)
            bm_box(t[pale if rnd.random() < 0.2 else stone], (size[0] + j, size[1] + j, size[2]), (off[0], off[1], z + ch * 0.5))
    for bm in t.parts.values():                         # (no bottom faces: they never show)
        bm.normal_update()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES")
    bm_box(t[core], (w * 0.8, w * 0.8, h - 0.05), (0, 0, h * 0.5 - 0.02))
    if cap:
        bm_box(t[pale], (w + 0.07, w + 0.07, 0.07), (0, 0, h + 0.035))
        if cap == "point":
            bm_cyl(t[stone], (w + 0.02) * 0.707, 0.03, 0.14, (0, 0, h + 0.14), rot=(0, 0, 45), seg=4)
    return stamp(k, t, xf((c.x, c.y, z0), (0, 0, yaw)))


def bm_rubble(bm, rnd, c, n=5, r=0.3, size=0.16, z=0.0):
    """Fallen blocks tumbled round c."""
    for i in range(n):
        a, d = rnd.uniform(0, 6.283), rnd.uniform(0, r)
        s = size * rnd.uniform(0.7, 1.2)
        bm_box(bm, (s * rnd.uniform(1.2, 1.9), s, s * rnd.uniform(0.75, 1.0)),
               (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d, z + s * 0.36), (rnd.uniform(-22, 22), rnd.uniform(-22, 22), rnd.uniform(0, 180)))
    return bm


# ---------------------------------------------------------------------------------------------- bones
def bm_bone(bm, p0, p1, r, n=4, knob=1.75, lite=False):
    """A long bone from p0 to p1: a shaft of radius r with a knob at each end. lite: fewer faces (heaps)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    kk = min(r * 2.0, L * 0.2) / L
    if lite:
        return bm_tube(bm, [p0, p0 + d * kk * 1.6, p1 - d * kk * 1.6, p1], [r * knob, r, r, r * knob], n=n, phase=0.5)
    pts = [p0, p0 + d * kk, p0 + d * kk * 2.1, p1 - d * kk * 2.1, p1 - d * kk, p1]
    return bm_tube(bm, pts, [r * knob * 0.7, r * knob, r, r, r * knob, r * knob * 0.7], n=n, phase=0.5)


def skull(k, M=None, s=0.2, bone=BONE, dark=SOCKET, detail=1, jaw=True, eyes=None, jaw_k=None):
    """A skull `s` tall, built facing +Y round its cranium's middle and set down with M. detail 0 (heaps), 1, 2.
    jaw: its lower jaw too (in Kit jaw_k if given, for a hinge). eyes: a glow key for lit sockets."""
    t, tj = Kit(), Kit()
    b, d = t[bone], t[dark]
    u, v = ((6, 4), (8, 5), (10, 6))[detail]
    bm_ellipsoid(b, (0, -0.05, 0.14), (0.36, 0.43, 0.34), u=u, v=v)
    bm_beam(b, (0, 0.2, 0.1), (0, 0.235, -0.3), 0.62, 0.3, w1=0.4, h1=0.2, up=(0, 1, 0))        # the face
    for sx in (-1, 1):
        bm_disc(d, (sx * 0.155, 0.378, 0.015), (sx * 0.12, 1, 0.08), 0.1, n=6, ry=0.115)
        if eyes:
            bm_ellipsoid(t[eyes], (sx * 0.155, 0.385, 0.01), (0.05, 0.03, 0.055), u=4, v=3)
        if detail >= 1:
            bm_beam(b, (sx * 0.35, 0.27, 0.2), (sx * 0.015, 0.385, 0.115), 0.11, 0.075)             # brow, scowling
            bm_beam(b, (sx * 0.34, 0.02, -0.02), (sx * 0.26, 0.33, -0.09), 0.06, 0.09)                # cheekbone
    bm_disc(d, (0, 0.392, -0.13), (0, 1, 0.1), 0.055, n=3, ry=0.07, phase=0.75)
    if detail >= 1:
        for i in range(4):
            bm_box(b, (0.075, 0.06, 0.09), ((i - 1.5) * 0.085, 0.3, -0.335), (0, 0, 0))               # upper teeth
    if jaw:
        j = (jaw_k or tj)[bone]
        bm_beam(j, (0, 0.03, -0.37), (0, 0.33, -0.45), 0.5, 0.11, w1=0.32, h1=0.1)
        if detail >= 1:
            for sx in (-1, 1):
                bm_beam(j, (sx * 0.24, 0.05, -0.4), (sx * 0.3, -0.04, -0.1), 0.07, 0.13, up=(0, 1, 0))
            for i in range(4):
                bm_box(j, (0.07, 0.055, 0.08), ((i - 1.5) * 0.075, 0.31, -0.375))
    M = (M or Matrix.Identity(4)) @ Matrix.Diagonal((s, s, s, 1.0))
    stamp(k, t, M)
    if jaw and jaw_k is None:
        stamp(k, tj, M)
    return k


def strew_bones(k, rnd, n, pick, zf, size=(0.26, 0.46), r=0.034, keys=(BONE_OLD, BONE), skulls=0, skull_s=0.19, ribs=0):
    """Loose bones lying where pick() -> (x, y) says, on the surface zf(x, y); then `skulls` skulls and `ribs` rib arcs."""
    for i in range(n):
        x, y = pick()
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(*size)
        dv = Vector((math.cos(a), math.sin(a), 0)) * (L * 0.5)
        z0, z1 = zf(x - dv.x, y - dv.y), zf(x + dv.x, y + dv.y)
        rr = r * rnd.uniform(0.85, 1.25)
        bm_bone(k[keys[i % len(keys)]], (x - dv.x, y - dv.y, z0 + rr * 1.3), (x + dv.x, y + dv.y, z1 + rr * 1.3), rr, lite=True)
    for i in range(skulls):
        x, y = pick()
        s = skull_s * rnd.uniform(0.85, 1.15)
        skull(k, xf((x, y, zf(x, y) + s * 0.3), (rnd.uniform(-25, 20), rnd.uniform(-20, 20), rnd.uniform(0, 360))), s=s,
              bone=keys[i % len(keys)], detail=0, jaw=rnd.random() < 0.4)
    for i in range(ribs):
        x, y = pick()
        z = zf(x, y)
        a = rnd.uniform(0, math.pi)
        for j in range(3):
            c = Vector((x, y, z)) + Vector((math.cos(a), math.sin(a), 0)) * (j * 0.085)
            w = Vector((-math.sin(a), math.cos(a), 0))
            pts = [c + w * (math.cos(t) * 0.17) + Vector((0, 0, math.sin(t) * 0.2 - 0.02)) for t in (0.1, 0.9, 1.57, 2.3, 3.04)]
            bm_tube(k[keys[0]], pts, [0.022, 0.026, 0.028, 0.026, 0.02], n=4)
    return k


# ---------------------------------------------------------------------------------------------- graves
def _upright(bm, pts, th, M):
    """A slab with the outline pts (x, height; counterclockwise from the front) and thickness th, stood up at M
    (its face looking down M's -Y)."""
    t = bmesh.new()
    prism(t, [Vector((x, z, 0)) for x, z in pts], -th * 0.5, th * 0.5)
    return bm_merge(bm, t, M @ Matrix.Rotation(math.radians(90), 4, "X"))


def gravestone(k, M, kind="round", w=0.34, h=0.5, th=0.09, stone=STONE_LT, mark=SOCKET, base=True):
    """A headstone standing at M (facing M's -Y). kind: "round", "point", "cross", "slab" (a ledger lying flat is a
    slab laid down), "broken" (snapped off at a slant)."""
    t = Kit()
    b = t[stone]
    hw = w * 0.5
    if kind == "round":
        pts = [(-hw, 0), (hw, 0), (hw, h - hw)] + [(math.cos(a) * hw, h - hw + math.sin(a) * hw) for a in (0.52, 1.05, 1.57, 2.09, 2.62)] + [(-hw, h - hw)]
    elif kind == "point":
        pts = [(-hw, 0), (hw, 0), (hw, h * 0.72), (hw * 0.55, h * 0.8), (0, h), (-hw * 0.55, h * 0.8), (-hw, h * 0.72)]
    elif kind == "broken":
        pts = [(-hw, 0), (hw, 0), (hw, h * 0.34), (hw * 0.3, h * 0.5), (-hw * 0.2, h * 0.42), (-hw, h * 0.66)]
    elif kind == "cross":
        a, c = hw * 0.32, h * 0.62
        pts = [(-a, 0), (a, 0), (a, c - a), (hw, c - a), (hw, c + a), (a, c + a), (a, h), (-a, h), (-a, c + a), (-hw, c + a), (-hw, c - a), (-a, c - a)]
    else:
        pts = [(-hw, 0), (hw, 0), (hw, h), (-hw, h)]
    _upright(b, pts, th, Matrix.Identity(4))
    if base:
        bm_box(b, (w + 0.1, th + 0.1, 0.07), (0, 0, 0.02))
    if kind in ("round", "point", "slab"):                  # a worn cross cut in the face
        bm_box(t[mark], (0.035, 0.012, h * 0.34), (0, -th * 0.5 - 0.002, h * 0.56))
        bm_box(t[mark], (w * 0.42, 0.012, 0.035), (0, -th * 0.5 - 0.002, h * 0.63))
    return stamp(k, t, M)


def wood_cross(k, M, h=0.6, w=0.36, th=0.06, wood="wood_dark:0.25:0.9", rope="sand:0.3:0.8", rag=None):
    """A grave's wooden cross planted at M (facing M's -Y): two rough boards lashed with rope. rag: a swatch key for a
    scrap of cloth tied to it."""
    t = Kit()
    bm_box(t[wood], (th, th * 0.8, h + 0.1), (0, 0, h * 0.5 - 0.05), (0, 0, 4))
    bm_box(t[wood], (w, th * 0.75, th * 1.1), (0, -th * 0.2, h * 0.7), (0, 6, 0))
    bm_box(t[rope], (th * 1.5, th * 1.25, th * 0.7), (0, -th * 0.1, h * 0.7), (0, 40, 0))
    bm_box(t[rope], (th * 1.5, th * 1.25, th * 0.7), (0, -th * 0.1, h * 0.7), (0, -40, 0))
    if rag:
        bm_beam(t[rag], (w * 0.3, -th * 0.5, h * 0.72), (w * 0.34, -th * 0.6, h * 0.36), 0.1, 0.012, w1=0.05, up=(0, 1, 0))
        bm_beam(t[rag], (w * 0.22, -th * 0.55, h * 0.72), (w * 0.2, -th * 0.65, h * 0.48), 0.07, 0.012, w1=0.04, up=(0, 1, 0))
    return stamp(k, t, M)


def coffin(k, M, l=0.84, w=0.36, h=0.2, wood="wood_dark:0.2:0.85", lid="wood:0.25:0.85", pall=None, trim="cream:0.2:0.7",
           open_=False, inside=SOCKET, lid_M=None, lid_k=None):
    """A six-sided coffin lying at M: its foot at the origin, its head toward +Y. pall: a swatch key for a cloth over
    the lid (the team's color) with a pale cross on it. open_: no lid (dark inside). lid_M: where the lid lies instead
    (in the coffin's own space). lid_k: a Kit the lid goes to instead of k (a lid that moves on a bone)."""
    t = Kit()
    out = [Vector((-0.27 * w, 0, 0)), Vector((0.27 * w, 0, 0)), Vector((0.5 * w, 0.7 * l, 0)), Vector((0.3 * w, l, 0)),
           Vector((-0.3 * w, l, 0)), Vector((-0.5 * w, 0.7 * l, 0))]
    c = Vector((0, 0.55 * l, 0))
    prism(t[wood], out, 0.0, h)
    if open_ or lid_k is not None:
        prism(t[inside], [c + (p - c) * 0.82 for p in out], h - 0.02, h + 0.004)
    lk = Kit()
    prism(lk[lid], [c + (p - c) * 1.06 for p in out], 0.0, 0.04)
    if pall:
        prism(lk[pall], [c + (p - c) * 0.84 for p in out], 0.04, 0.052)
        bm_box(lk[trim], (0.045, l * 0.56, 0.008), (0, 0.52 * l, 0.056))
        bm_box(lk[trim], (w * 0.5, 0.045, 0.008), (0, 0.66 * l, 0.056))
    else:
        for y in (0.2, 0.5, 0.8):
            bm_box(lk[wood], (w * (0.62 if y < 0.4 else 0.95), 0.05, 0.016), (0, y * l, 0.046))
    if lid_k is not None:
        stamp(lid_k, lk, M @ (lid_M if lid_M is not None else Matrix.Translation((0, 0, h))))
    elif lid_M is not None:
        stamp(t, lk, lid_M)
    elif not open_:
        stamp(t, lk, Matrix.Translation((0, 0, h)))
    else:
        for bm in lk.parts.values():
            bm.free()
    return stamp(k, t, M)


# ---------------------------------------------------------------------------------------------- fire
def bm_flame(bm, rnd, c, h=0.4, r=0.13, n=4, sides=5, lean=(0, 0, 0)):
    """A soul flame standing on c: a pointed main tongue and n lesser ones curling round it."""
    c, lean = Vector(c), Vector(lean)

    def tongue(base, hh, rr, bend):
        pts = [base, base + bend * 0.35 + Vector((0, 0, hh * 0.36)), base + bend * 0.15 + lean * 0.5 + Vector((0, 0, hh * 0.7)),
               base + bend * 0.75 + lean + Vector((0, 0, hh))]
        bm_tube(bm, pts, [rr * 0.7, rr, rr * 0.62, 0.0], n=sides)
    tongue(c, h, r, Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * r * 0.5)
    for i in range(n):
        a = 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / n
        d = Vector((math.cos(a), math.sin(a), 0))
        tongue(c + d * r * 0.72, h * rnd.uniform(0.42, 0.7), r * 0.56, d * r * rnd.uniform(0.5, 1.3))
    return bm


def brazier(k, c, h=0.55, r=0.2, iron=IRON, rust=RUST, coals=None, legs=3):
    """An iron fire bowl on splayed legs standing at c; its rim is h up. coals: a glow key for the bed of embers.
    Returns where a flame should stand."""
    c = Vector(c)
    t = Kit()
    for i in range(legs):
        a = 2 * math.pi * i / legs + 0.5
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_beam(t[iron], d * (r * 0.95), d * (r * 0.3) + Vector((0, 0, h - r * 0.5)), 0.045, 0.045)
    ring(t[rust], (0, 0, 0), r * 0.62, r * 0.5, h * 0.42, h * 0.42 + 0.035, seg=8)
    bm_cyl(t[iron], r * 0.5, r, r * 0.55, (0, 0, h - r * 0.28), seg=8)
    ring(t[rust], (0, 0, 0), r * 1.1, r * 0.82, h - 0.03, h + 0.025, seg=8)
    if coals:
        bm_cyl(t[coals], r * 0.84, r * 0.6, 0.05, (0, 0, h + 0.012), seg=8)
    stamp(k, t, Matrix.Translation(c))
    return c + Vector((0, 0, h + 0.02))


# ---------------------------------------------------------------------------------------------- hands, chains, cloth
FINGER_LEN = (0.92, 1.08, 1.0, 0.8)


def hand_parts(palm, fingers, s=0.3, curl=0.35, side=1, r=0.07, segs=3):
    """A skeletal hand in its own space, `s` long: the wrist at the origin, reaching along +Y, the palm facing -Z,
    the thumb toward side * X. palm gets the wrist bones, the four bones of the palm and the thumb; fingers gets the
    four clawed fingers, built round the knuckle line (0, 0.42 s, 0): turn them about X there to open and close.
    curl 0..1: how hooked the fingers are built. segs: 3 finger bones each, or 2 (cheaper, for small hands)."""
    rr = r * s
    bm_box(palm, (0.36 * s, 0.14 * s, 0.15 * s), (0, 0.03 * s, 0), (0, 0, 0))
    ky = 0.42 * s
    for i in range(4):
        x0, x1 = (i - 1.5) * 0.085 * s, (i - 1.5) * 0.19 * s
        bm_tube(palm, [(x0, 0.06 * s, 0), (x1, ky, 0)], [rr * 0.9, rr * 1.25], n=4, phase=0.5)
        ang = math.radians(8.0 * (i - 1.5))
        p = Vector((x1, ky, 0))
        a = 0.0
        phal = ((0.25, 8 + 26 * curl), (0.19, 22 + 34 * curl), (0.16, 24 + 30 * curl)) if segs >= 3 else \
            ((0.32, 10 + 30 * curl), (0.28, 34 + 46 * curl))
        for j, (ln, bend) in enumerate(phal):
            a += math.radians(bend)
            d = Vector((math.sin(ang) * math.cos(a), math.cos(ang) * math.cos(a), -math.sin(a)))
            q = p + d * (ln * s * FINGER_LEN[i])
            if j < len(phal) - 1:
                bm_tube(fingers, [p, q], [rr * (1.05 - 0.12 * j), rr * (0.92 - 0.12 * j)], n=4, phase=0.5)
            else:                                           # the claw
                bm_tube(fingers, [p, p.lerp(q, 0.5), q], [rr * (1.05 - 0.12 * j), rr * (0.7 - 0.08 * j), 0.0], n=4, phase=0.5)
            p = q
    t0 = Vector((side * 0.17 * s, 0.1 * s, -0.02 * s))
    t1 = t0 + Vector((side * 0.16, 0.14, -0.06)) * s
    t2 = t1 + Vector((side * 0.06, 0.15, -0.1)) * s
    bm_tube(palm, [t0, t1], [rr * 1.1, rr * 0.95], n=4, phase=0.5)
    bm_tube(palm, [t1, t1.lerp(t2, 0.5), t2], [rr * 0.95, rr * 0.62, 0.0], n=4, phase=0.5)
    return palm, fingers


def bm_forearm(bm, a, b, r=0.035, spread=0.05, side=(1, 0, 0), knob=True, rnd=None, lite=False):
    """The two bones of a forearm from a (the elbow) to b (the wrist), `spread` apart along side."""
    a, b, sd = Vector(a), Vector(b), Vector(side).normalized()
    bm_bone(bm, a + sd * spread, b + sd * spread * 0.8, r, n=4, lite=lite)
    bm_bone(bm, a - sd * spread, b - sd * spread * 0.8, r * 0.85, n=4, lite=lite)
    if knob:
        bm_lump(bm, rnd or random.Random(5), a, r * 2.6, squash=(1, 1, 0.9), n=9)
    return bm


def reach_arm(bm, base, wrist, out, s=0.3, side=1, curl=0.25, flex=0.35, segs=3, lite=False, rnd=None, elbow=0.0, thick=1.0):
    """A skeletal arm reaching out of the ground: the forearm's two bones from base (down in the earth) to wrist, and a
    clawed hand `s` long reaching on from it, bent at the wrist toward `out` (a direction: what it grasps at; the palm
    faces it). elbow: how far its elbow sticks out behind, as a part of its length (0: only the forearm shows): then
    an upper arm's one thick bone comes up to it first. thick: stouter arm bones. All of it goes into bm, to be
    soft-skinned to three bones.
    Returns the points for those bones and the
    axes to turn them about: {"base", "wrist", "knuck", "tip", "ax" (the knuckles' line: a negative turn about it closes
    the fingers, or flexes the wrist toward the palm), "dir", "out", "tilt" (a positive turn about it leans the arm
    toward out)}."""
    base, wrist, out = Vector(base), Vector(wrist), Vector(out).normalized()
    d = (wrist - base).normalized()
    fwd = (d + out * flex).normalized()
    up = -out if abs(fwd.dot(out)) < 0.97 else Vector((0, 0, 1))
    M = frame(wrist, fwd, up=up)
    t = bmesh.new()
    hand_parts(t, t, s=s, curl=curl, side=side, segs=segs)
    bm_merge(bm, t, M)
    ax = (M.to_3x3() @ Vector((1, 0, 0))).normalized()
    rnd = rnd or random.Random(5)
    start = base
    if elbow:
        back = out - d * out.dot(d)
        back = -back.normalized() if back.length > 1e-3 else d.orthogonal()
        start = base.lerp(wrist, 0.4) + back * (elbow * (wrist - base).length)
        bm_bone(bm, base, start, 0.165 * s * thick, n=5, knob=1.5, lite=lite)
        bm_lump(bm, rnd, start, 0.27 * s * thick, n=9)
    bm_forearm(bm, start, wrist - d * (0.03 * s), r=0.125 * s * thick, spread=0.16 * s * (0.5 + 0.5 * thick), side=ax, knob=False, lite=lite)
    bm_lump(bm, rnd, wrist, 0.22 * s * (0.5 + 0.5 * thick), squash=(1.25, 0.9, 0.8), rot=(0, 0, math.degrees(math.atan2(ax.y, ax.x))), n=8)
    c = math.radians(38)
    flat = Vector((out.x, out.y, 0))
    tilt = Vector((0, 0, 1)).cross(flat.normalized()) if flat.length > 1e-3 else Vector((1, 0, 0))
    return {"base": base, "wrist": wrist, "knuck": M @ Vector((0, 0.42 * s, 0)),
            "tip": M @ Vector((0, (0.42 + 0.5 * math.cos(c)) * s, -0.5 * math.sin(c) * s)), "ax": ax, "dir": d, "out": out, "tilt": tilt}


def arm_bones(bones, name, a, parent="root"):
    """Adds the three bones of a reach_arm() (its returned points) to a bones dict: name, name + ".h", name + ".g"."""
    bones[name] = (tuple(a["base"]), tuple(a["wrist"]), parent)
    bones[name + ".h"] = (tuple(a["wrist"]), tuple(a["knuck"]), name)
    bones[name + ".g"] = (tuple(a["knuck"]), tuple(a["tip"]), name + ".h")
    return [name, name + ".h", name + ".g"]


def pose_arm(fk, name, a, lean=0.0, side=0.0, rise=0.0, flex=0.0, grip=0.0, scale=1.0):
    """Poses a reach_arm(): lean (degrees toward what it reaches for), side (degrees across that), rise (how far it
    comes up out of the ground), flex (the wrist, degrees toward the palm), grip (the fingers closing, degrees)."""
    fk.put(name, Quaternion(a["tilt"], math.radians(lean)) @ Quaternion(a["out"], math.radians(side)), loc=a["dir"] * rise, scale=scale)
    fk.put(name + ".h", Quaternion(a["ax"], math.radians(-flex)))
    fk.put(name + ".g", Quaternion(a["ax"], math.radians(-grip)))


def loop_dist(loop, x, y):
    """How far (x, y) is from the outline `loop` (always positive)."""
    p = Vector((x, y, 0))
    best = 1e9
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        ab = b - a
        t = min(max((p - a).dot(ab) / max(ab.length_squared, 1e-9), 0.0), 1.0)
        best = min(best, (a + ab * t - p).length)
    return best


def bm_chain(bm, pts, link=0.15, w=0.085, th=0.03, seg=6):
    """A heavy chain along the points: flat links, every other one turned on edge. seg 4: square links (cheap)."""
    pts = [Vector(p) for p in pts]
    i, carry, flip = 0, 0.0, False
    for a, b in zip(pts, pts[1:]):
        d = b - a
        L = d.length
        s = carry
        while s < L:
            c = a + d * (s / L)
            t = bmesh.new()
            if seg == 4:
                bm_box(t, (w, w, th), (0, 0, 0))
            else:
                bm_cyl(t, w * 0.5, w * 0.5, th, (0, 0, 0), seg=seg)
            bmesh.ops.scale(t, vec=(1.0, link * 0.62 / (w * 0.5), 1.0), verts=t.verts)
            m = frame(c, d, up=(0, 0, 1) if abs(d.normalized().z) < 0.9 else (1, 0, 0))
            bm_merge(bm, t, m @ Matrix.Rotation(math.radians(90 if flip else 0), 4, "Y"))
            flip = not flip
            s += link * 0.8
        carry = s - L
    return bm


def bm_cloth(bm, a, b, drop, cols=4, rows=4, wave=0.03, tatter=0.14, rnd=None, th=0.012, taper=0.0):
    """Cloth hanging from the line a -> b, `drop` long: both faces, a slow fold across it, its hem cut in tatters.
    taper: how much narrower it is at the hem (0..1)."""
    rnd = rnd or random.Random(7)
    a, b = Vector(a), Vector(b)
    ax = (b - a)
    nrm = ax.normalized().cross(Vector((0, 0, -1))).normalized()
    hem = [drop * (1.0 - tatter * rnd.uniform(0.0, 1.0) * (1.6 if i % 2 else 0.5)) for i in range(cols + 1)]
    mid = (a + b) * 0.5
    for side in (1, -1):
        grid = []
        for i in range(cols + 1):
            u = i / cols
            row = []
            for j in range(rows + 1):
                v = j / rows
                p = a + ax * u
                p = p + (mid - p) * (taper * v)
                p = p + Vector((0, 0, -hem[i] * v)) + nrm * (math.sin(u * 5.0 + v * 2.2) * wave * v + side * th * 0.5)
                row.append(bm.verts.new(p))
            grid.append(row)
        for i in range(cols):
            for j in range(rows):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if side > 0 else tuple(reversed(f)))
    return bm


# ---------------------------------------------------------------------------------------------- posing by goals
class Fk:
    """Poses a rig by goals in armature space. It keeps every posed bone's frame, so a limb can be told where its end
    should be (ik: two bones reach for a point, bending toward a pole) while the body it hangs from moves.
    Pose parents before children.

        fk = Fk(rig)
        fk.clear()
        fk.put("hips", rot=fk.rx(12), loc=(0, 0.1, -0.2))          # armature axes, on top of the parent's pose
        fk.ik("leg.L.1", "leg.L.2", ankle_point)                   # the foot stays put
        key_pose(rig, frame)
    """

    def __init__(self, rig):
        self.rig = rig
        self.pb = rig.pose.bones
        self.rest = {}
        self.kids = {}
        for b in self.pb:
            par = b.parent.name if b.parent else None
            self.rest[b.name] = (b.bone.matrix_local.to_quaternion(), b.bone.head_local.copy(), b.bone.tail_local.copy(), par)
            self.kids.setdefault(par, []).append(b.name)
        self.delta = {}

    @staticmethod
    def rot(axis, deg):
        return Quaternion(Vector(axis), math.radians(deg))

    def clear(self):
        rest_pose(self.rig)
        self.delta = {}

    def D(self, name):
        """The posed bone's transform in armature space (what carries its rest-pose geometry)."""
        if name is None:
            return Matrix.Identity(4)
        if name not in self.delta:
            self.delta[name] = self.D(self.rest[name][3])
        return self.delta[name]

    def _drop(self, name):
        for c in self.kids.get(name, ()):
            if c in self.delta:
                del self.delta[c]
            self._drop(c)

    def put(self, name, rot=None, loc=None, scale=1.0):
        """rot: a Quaternion in armature axes, applied on top of the parent's pose, about the bone's head;
        loc: an offset in the same axes; scale: uniform."""
        r, h, t, par = self.rest[name]
        q = rot if rot is not None else Quaternion()
        l = Vector(loc) if loc is not None else Vector()
        b = self.pb[name]
        b.rotation_quaternion = r.inverted() @ q @ r
        b.location = r.inverted() @ l
        b.scale = (scale, scale, scale)
        self._drop(name)
        self.delta[name] = (self.D(par) @ Matrix.Translation(h + l) @ q.to_matrix().to_4x4()
                            @ Matrix.Diagonal((scale, scale, scale, 1.0)) @ Matrix.Translation(-h))

    def at(self, name, p):
        """Where a rest-pose point riding on bone `name` is now."""
        return self.D(name) @ Vector(p)

    def head(self, name):
        return self.D(name) @ self.rest[name][1]

    def tail(self, name):
        return self.D(name) @ self.rest[name][2]

    def _look(self, name, y1, x1=None, x0=None):
        r, h, t, par = self.rest[name]
        pq = self.D(par).to_quaternion()
        y1 = (pq.inverted() @ Vector(y1)).normalized()
        y0 = (t - h).normalized()
        if x1 is None or x0 is None:
            return y0.rotation_difference(y1)
        x1 = pq.inverted() @ Vector(x1)
        x1 = x1 - y1 * x1.dot(y1)
        x0 = Vector(x0) - y0 * Vector(x0).dot(y0)
        if x1.length < 1e-5 or x0.length < 1e-5:
            return y0.rotation_difference(y1)
        x1.normalize()
        x0.normalize()
        m0 = Matrix((x0, y0, x0.cross(y0))).transposed()
        m1 = Matrix((x1, y1, x1.cross(y1))).transposed()
        return (m1 @ m0.transposed()).to_quaternion()

    def aim(self, name, target, side=None, side0=None, loc=None, scale=1.0, twist=0.0):
        """Turns the bone to point from its head at the point `target`. side / side0: keep the direction that was
        side0 in the rest pose turned toward side (both armature space); without them, the shortest turn."""
        r, h, t, par = self.rest[name]
        l = Vector(loc) if loc is not None else Vector()
        head = self.D(par) @ (h + l)
        d = Vector(target) - head
        q = self._look(name, d, side, side0)
        if twist:
            pq = self.D(par).to_quaternion()
            q = Quaternion((pq.inverted() @ d).normalized(), math.radians(twist)) @ q
        self.put(name, q, loc, scale)

    def ik(self, upper, lower, target, pole=None, twist=0.0):
        """Two-bone IK: the lower bone's tail goes to `target` (as far as the limb reaches), the joint bending toward
        `pole` (a direction; default: the way it bends in the rest pose, carried by the parent). Returns the joint."""
        r1, h1, t1, par = self.rest[upper]
        r2, h2, t2, _ = self.rest[lower]
        P = self.D(par)
        a = P @ h1
        sc = P.to_scale().x
        l1, l2 = (t1 - h1).length * sc, (t2 - h2).length * sc
        d = Vector(target) - a
        dist = min(max(d.length, abs(l1 - l2) + 1e-4), l1 + l2 - 1e-4)
        dn = d.normalized()
        u0, w0 = (t1 - h1).normalized(), (t2 - h2).normalized()
        n0 = u0.cross(w0)
        if pole is None:
            e0 = (t1 - h1) - (t2 - h1).normalized() * (t1 - h1).dot((t2 - h1).normalized())
            pole = P.to_quaternion() @ e0
        pv = Vector(pole) - dn * Vector(pole).dot(dn)
        if pv.length < 1e-5:
            pv = dn.orthogonal()
        pv.normalize()
        ca = min(max((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1.0), 1.0)
        joint = a + dn * (l1 * ca) + pv * (l1 * math.sqrt(max(0.0, 1.0 - ca * ca)))
        n1 = pv.cross(dn)
        if n0.length > 1e-4:
            self.aim(upper, joint, side=n1, side0=n0.normalized())
            self.aim(lower, a + dn * dist, side=n1, side0=n0.normalized(), twist=twist)
        else:
            self.aim(upper, joint)
            self.aim(lower, a + dn * dist, twist=twist)
        return joint

    def rx(self, deg):
        return Quaternion((1, 0, 0), math.radians(deg))

    def ry(self, deg):
        return Quaternion((0, 1, 0), math.radians(deg))

    def rz(self, deg):
        return Quaternion((0, 0, 1), math.radians(deg))


def lerp(a, b, t):
    return a + (b - a) * t


def pulse(f, start, peak, end):
    """0 before start, easing to 1 at peak, easing back to 0 at end."""
    if f <= start or f >= end:
        return 0.0
    return smooth((f - start) / max(peak - start, 1e-6)) if f < peak else 1.0 - smooth((f - peak) / max(end - peak, 1e-6))
