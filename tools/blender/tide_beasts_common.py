"""The Tide beasts' shared pieces (snapjaw_crab, kraken, leviathan, mer_harpoon, mer_siren).

Exec'd by a tower script after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

Shores and pools (outlines, sand flats with holes cut for pools, water in depth zones, rock rims), sea dressing (corals,
weed, scallop and spiral shells, starfish, barnacles, whale ribs, wreck timbers, nets, harpoons), thin fins and sails,
tubes that remember their frames (so an underside can be painted paler), bone chains posed from one shape to another
(tentacles, necks, tails), and a merfolk figure built from lofts.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler


# ------------------------------------------------------------------------------------------- outlines
def tb_normals(pts):
    """Outward unit normals of a counterclockwise closed outline, one per point."""
    n = len(pts)
    out = []
    for i in range(n):
        d = pts[(i + 1) % n] - pts[i - 1]
        v = Vector((d.y, -d.x, 0.0))
        out.append(v.normalized() if v.length > 1e-9 else Vector((1, 0, 0)))
    return out


def tb_offset(pts, d):
    """The outline pushed out by d (in for d < 0)."""
    nr = tb_normals(pts)
    return [p + nr[i] * d for i, p in enumerate(pts)]


def tb_smooth(pts, rounds=1):
    for _ in range(rounds):
        n = len(pts)
        pts = [(pts[i - 1] + pts[i] * 2.0 + pts[(i + 1) % n]) * 0.25 for i in range(n)]
    return pts


def tb_resample(pts, step):
    """A closed outline with a point about every `step` along it."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        m = max(1, int(round((b - a).length / step)))
        for j in range(m):
            out.append(a.lerp(b, j / m))
    return out


def tb_wobble(pts, rnd, amount):
    nr = tb_normals(pts)
    return [p + nr[i] * rnd.uniform(-amount, amount) for i, p in enumerate(pts)]


def tb_shore(cells, inset, rnd=None, step=0.3, jitter=0.0, rounds=1):
    """The footprint's outline pulled in by `inset`: resampled, its corners rounded, its line made uneven."""
    pts = tb_smooth(tb_resample(outline(cells, inset), step), rounds)
    if rnd is not None and jitter > 0.0:
        pts = tb_wobble(pts, rnd, jitter)
    return pts


def tb_blob(c, rx, ry, n=14, rnd=None, jitter=0.0, rot=0.0):
    """An uneven oval outline (counterclockwise) round c."""
    c = Vector(c)
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1.0 + (rnd.uniform(-jitter, jitter) if rnd is not None else 0.0)
        x, y = math.cos(a) * rx * k, math.sin(a) * ry * k
        out.append(Vector((c.x + x * cr - y * sr, c.y + x * sr + y * cr, 0.0)))
    return out


def tb_inside(pts, p):
    return inside(pts, p.x, p.y)


# ------------------------------------------------------------------------------------------- plates, sand, water
def tb_plate(bm, outer, holes=(), z=0.0, z_skirt=None, flare=0.0, z_hole=None, hole_flare=0.0):
    """A flat plate facing up at height z: bounded by `outer` (counterclockwise), with holes (counterclockwise loops)
    cut out of it. z_skirt: a wall down to there round the outside (its foot pushed out by flare); z_hole: walls down
    inside each hole (their feet pulled in toward the hole's middle by hole_flare)."""
    from mathutils import geometry
    co = [Vector((p.x, p.y)) for p in outer]
    faces = [list(range(len(outer)))]
    for h in holes:
        base = len(co)
        co.extend(Vector((p.x, p.y)) for p in h)
        faces.append(list(range(base + len(h) - 1, base - 1, -1)))
    vs, _, fs, _, _, _ = geometry.delaunay_2d_cdt(co, [], faces, 3, 1e-5)
    made = [bm.verts.new((p.x, p.y, z)) for p in vs]
    for f in fs:
        tri = [made[i] for i in f]
        if len(set(tri)) >= 3:
            face = bm.faces.new(tri)
            face.normal_update()
            if face.normal.z < 0:
                face.normal_flip()

    def find(p):
        best, bd = None, 1e9
        for i, q in enumerate(vs):
            d = (q.x - p.x) ** 2 + (q.y - p.y) ** 2
            if d < bd:
                best, bd = made[i], d
        return best

    def wall(loop, zb, push, inward):
        nr = tb_normals(loop)
        top = [find(p) for p in loop]
        bot = [bm.verts.new((p.x + nr[i].x * push, p.y + nr[i].y * push, zb)) for i, p in enumerate(loop)]
        n = len(loop)
        for i in range(n):
            j = (i + 1) % n
            if top[i] is top[j]:
                continue
            bm.faces.new((top[i], top[j], bot[j], bot[i]) if inward else (top[j], top[i], bot[i], bot[j]))
    if z_skirt is not None:
        wall(list(outer), z_skirt, flare, False)
    if z_hole is not None:
        for h in holes:
            wall(list(h), z_hole, -hole_flare, True)
    return bm


def tb_shore_obj(name, bm, col, root, top=0.3, side=(0.55, 0.82)):
    """Colours a mesh like the map's shore sand (the pack's sand swatch on the ground material: in game it takes the
    biome's palette and the ground shader's sand ripples, like the coast tiles). top: 0 light dry sand .. 1 dark wet."""
    o = mesh_obj(name, bm, col, root)
    paint_ground(o, side=side, top=top, swatch=(4, 2))
    o["ground"] = True
    return o


def tb_sea_obj(name, bm, col, root, top=0.48, side=(0.66, 0.84)):
    """Colours a mesh like the map's water (paint_water), `top` picking how deep it looks (0.4 shallows .. 0.85 deep)."""
    o = mesh_obj(name, bm, col, root)
    paint_ground(o, side=side, top=top, swatch="blue")
    return o


def tb_water(name, col, root, loops, z, shades, holes=()):
    """Water at height z in depth zones: loops[0] is the shore, each next loop lies inside the one before and is a
    shade deeper (shades: one per loop). holes: loops cut out of the innermost zone. Returns the objects."""
    out = []
    for i, loop in enumerate(loops):
        bm = bmesh.new()
        inner = [loops[i + 1]] if i + 1 < len(loops) else list(holes)
        tb_plate(bm, loop, inner, z)
        out.append(tb_sea_obj("%s_%d" % (name, i), bm, col, root, top=shades[i]))
    return out


def tb_rim(bm, rnd, pts, z, r=(0.14, 0.24), gap=0.3, out=0.0, squash=(1.0, 1.0, 0.75), skip=None, n=10, sink=0.2):
    """Boulders along a closed outline (a pool's rim). skip(point) -> True leaves a gap."""
    acc = rnd.uniform(0, gap)
    m = len(pts)
    nr = tb_normals(pts)
    mean = (r[0] + r[1]) * 0.5
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % m]
        seg = (b - a).length
        while acc < seg:
            t = acc / max(seg, 1e-6)
            p = a.lerp(b, t)
            nn = nr[i].lerp(nr[(i + 1) % m], t)
            rr = rnd.uniform(*r)
            q = p + nn * (out + rnd.uniform(-0.04, 0.04))
            if not (skip and skip(q)):
                bm_boulder(bm, rnd, (q.x, q.y, z), rr, squash=(squash[0] * rnd.uniform(0.85, 1.2), squash[1] * rnd.uniform(0.85, 1.2),
                                                             squash[2] * rnd.uniform(0.8, 1.3)), n=n, sink=sink)
            acc += gap * rnd.uniform(0.8, 1.25) * (rr / mean)
        acc -= seg
    return bm


def tb_ripple(bm, c, direction, length, w=0.15, h=0.03, bend=0.0, z=0.0):
    """One sand ripple: a low, flat-topped ridge `length` long through c along `direction`, bowed sideways by bend."""
    c = Vector((c[0], c[1], 0.0))
    d = Vector((direction[0], direction[1], 0.0)).normalized()
    s = Vector((-d.y, d.x, 0.0))
    pts, rad = [], []
    for i in range(5):
        t = i / 4.0 - 0.5
        p = c + d * (length * t) + s * (bend * (1.0 - (2 * t) ** 2))
        pts.append(Vector((p.x, p.y, z)))
        rad.append(h * (0.4 + 0.6 * (1.0 - (2 * t) ** 2) ** 0.5))
    bm_tube(bm, pts, rad, n=6, squash=w / max(h, 1e-6) * 0.5)
    return bm


def tb_ripples(bm, c, ang, n, length, z, gap=0.17, w=0.15, h=0.03, bend=0.05, within=None, avoid=()):
    """A patch of n ripples side by side round c, running along `ang` (degrees). within: an outline every ripple must
    stay inside (it is shortened until it does, or left out); avoid: outlines it must stay out of (pools)."""
    a = math.radians(ang)
    d, s = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))

    def ok(p, ln):
        for t in (-0.5, -0.25, 0.0, 0.25, 0.5):
            for side in (-w * 0.5, w * 0.5):
                q = p + d * (ln * t) + s * side
                if within is not None and not inside(within, q.x, q.y):
                    return False
                if any(inside(loop, q.x, q.y) for loop in avoid):
                    return False
        return True
    for i in range(n):
        off = i - (n - 1) / 2.0
        p = Vector((c[0], c[1], 0)) + s * (gap * off) + d * (0.07 * ((i * 7) % 3 - 1))
        ln = length * (1.0 - 0.16 * abs(off))
        while ln > 0.24 and not ok(p, ln):
            ln *= 0.86
        if ln <= 0.24 and not ok(p, ln):
            continue
        tb_ripple(bm, (p.x, p.y), (d.x, d.y), ln, w=w, h=h, bend=bend if ln > 0.4 else bend * 0.5, z=z)
    return bm


# ------------------------------------------------------------------------------------------- thin solids
def tb_slab(bm, pts, th):
    """A thin solid from a flat outline (3D points in order) and a thickness vector (the far side is pts + th)."""
    th = Vector(th)
    a = [bm.verts.new(Vector(p)) for p in pts]
    b = [bm.verts.new(Vector(p) + th) for p in pts]
    fs = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        fs.append(bm.faces.new((a[i], b[i], b[j], a[j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return fs


def tb_sheet(bm, grid, th):
    """A thin solid from a grid of points (rows of equal length: sails, fins, shells). th: a thickness vector, or a
    number (then it is laid off against the sheet's own normal at each point)."""
    rows, cols = len(grid), len(grid[0])

    def nrm(i, j):
        a = Vector(grid[min(i + 1, rows - 1)][j]) - Vector(grid[max(i - 1, 0)][j])
        b = Vector(grid[i][min(j + 1, cols - 1)]) - Vector(grid[i][max(j - 1, 0)])
        n = a.cross(b)
        return n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
    top = [[bm.verts.new(Vector(grid[i][j])) for j in range(cols)] for i in range(rows)]
    if isinstance(th, (int, float)):
        bot = [[bm.verts.new(Vector(grid[i][j]) - nrm(i, j) * th) for j in range(cols)] for i in range(rows)]
    else:
        bot = [[bm.verts.new(Vector(grid[i][j]) + Vector(th)) for j in range(cols)] for i in range(rows)]
    fs = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            fs.append(bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j])))
            fs.append(bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1])))
    edge = ([(0, j) for j in range(cols)] + [(i, cols - 1) for i in range(1, rows)] +
            [(rows - 1, j) for j in range(cols - 2, -1, -1)] + [(i, 0) for i in range(rows - 2, 0, -1)])
    m = len(edge)
    for q in range(m):
        (i0, j0), (i1, j1) = edge[q], edge[(q + 1) % m]
        fs.append(bm.faces.new((top[i1][j1], top[i0][j0], bot[i0][j0], bot[i1][j1])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return top


def tb_fin(bm, base0, base1, tips, th=0.02, notch=0.55):
    """A webbed fin: its foot runs from base0 to base1, its rays end at `tips` (in order from base0's side to
    base1's); the web between two rays is cut back to `notch` of the way out. A thin solid with both faces."""
    base0, base1 = Vector(base0), Vector(base1)
    tips = [Vector(t) for t in tips]
    n = len(tips)
    pts = [base0]
    for i, t in enumerate(tips):
        pts.append(t)
        if i + 1 < n:
            foot = base0.lerp(base1, (i + 1.0) / n)
            mid = (t + tips[i + 1]) * 0.5
            pts.append(foot.lerp(mid, notch))
    pts.append(base1)
    nrm = (base1 - base0).cross(tips[n // 2] - base0)
    nrm = nrm.normalized() if nrm.length > 1e-9 else Vector((1, 0, 0))
    half = nrm * (th * 0.5)
    return tb_slab(bm, [p - half for p in pts], nrm * th)


# ------------------------------------------------------------------------------------------- sea dressing
def tb_scallop(bm, c, r, yaw=0.0, tilt=0.0, ribs=8, dome=0.3, th=0.035, t0=0.1, t1=1.0, rows=4, spread=78.0, wave=0.05,
               lift=0.0, roll=0.0):
    """A ribbed scallop shell: its hinge at c, fanning out toward local +Y (turned by yaw), domed upward. tilt lifts its
    lip (degrees about the hinge line); t0..t1: the part of the fan to build (a painted band: build the rim again,
    lifted a hair)."""
    cols = ribs * 2
    M = (Matrix.Translation(Vector(c)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "X")
         @ Matrix.Rotation(math.radians(roll), 4, "Y"))

    def surf(t, u, dz):
        a = math.radians(spread) * u
        rho = r * t
        h = dome * r * (max(0.0, 1.0 - (2.0 * min(t, 1.0) - 1.0) ** 2) ** 0.6) * (1.0 - 0.55 * u * u)
        return M @ Vector((rho * math.sin(a), rho * math.cos(a), h + dz))
    grid_top, grid_bot = [], []
    for i in range(rows + 1):
        t = t0 + (t1 - t0) * i / rows
        rt, rb = [], []
        for j in range(cols + 1):
            u = -1.0 + 2.0 * j / cols
            ridge = wave * r * t * (1.0 if j % 2 else 0.0) + lift
            rt.append(bm.verts.new(surf(t, u, ridge)))
            rb.append(bm.verts.new(surf(t, u, ridge - th)))
        grid_top.append(rt)
        grid_bot.append(rb)
    fs = []
    for i in range(rows):
        for j in range(cols):
            fs.append(bm.faces.new((grid_top[i][j], grid_top[i][j + 1], grid_top[i + 1][j + 1], grid_top[i + 1][j])))
            fs.append(bm.faces.new((grid_bot[i][j], grid_bot[i + 1][j], grid_bot[i + 1][j + 1], grid_bot[i][j + 1])))
    edge = ([(0, j) for j in range(cols + 1)] + [(i, cols) for i in range(1, rows + 1)] +
            [(rows, j) for j in range(cols - 1, -1, -1)] + [(i, 0) for i in range(rows - 1, 0, -1)])
    m = len(edge)
    for q in range(m):
        (i0, j0), (i1, j1) = edge[q], edge[(q + 1) % m]
        fs.append(bm.faces.new((grid_top[i1][j1], grid_top[i0][j0], grid_bot[i0][j0], grid_bot[i1][j1])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def tb_whelk(bm, c, size, yaw=0.0, pitch=0.0, turns=2.6, n=6):
    """A spiral sea-snail shell lying at c, its point toward local +X (turned by yaw, tipped up by pitch)."""
    M = (Matrix.Translation(Vector(c) + Vector((0, 0, size * 0.42))) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
         @ Matrix.Rotation(math.radians(-pitch), 4, "Y"))
    pts, rad = [], []
    steps = int(turns * 7)
    for i in range(steps + 1):
        u = i / steps
        a = u * turns * 2 * math.pi
        coil = size * 0.3 * (1 - u) ** 1.15
        pts.append(M @ Vector((size * (u ** 0.9) - size * 0.35, math.cos(a) * coil, math.sin(a) * coil)))
        rad.append(size * 0.36 * (1 - u) ** 1.1 + size * 0.015)
    rad[-1] = 0.0
    bm_tube(bm, pts, rad, n=n, up=(1, 0, 0))
    return bm


def tb_starfish(bm, c, r=0.2, yaw=0.0, h=0.05):
    c = Vector(c)
    top = bm.verts.new(c + Vector((0, 0, h)))
    ring_ = []
    for k in range(10):
        a = math.radians(yaw + 36 * k)
        rr = r if k % 2 == 0 else r * 0.36
        ring_.append(bm.verts.new(c + Vector((math.cos(a) * rr, math.sin(a) * rr, 0.0))))
    for k in range(10):
        bm.faces.new((ring_[k], ring_[(k + 1) % 10], top))
    bm.faces.new(list(reversed(ring_)))
    return bm


def tb_coral(bm, rnd, base, h=0.6, r=0.06, depth=2, spread=0.55, n=5, direction=None):
    """A branching coral: a trunk forking into upturned, tapering branches with knobbly ends."""
    base = Vector(base)
    d = (Vector(direction) if direction is not None else Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 1.0))).normalized()
    tip = base + d * (h * (0.5 if depth > 0 else 0.45))
    if depth <= 0:
        bm_tube(bm, [base, base.lerp(tip, 0.55), base.lerp(tip, 0.88), tip], [r, r * 0.85, r * 0.95, 0.0], n=n)
        return bm
    bm_tube(bm, [base, tip], [r, r * 0.8], n=n)
    kids = 2 if rnd.random() < 0.55 else 3
    a0 = rnd.uniform(0, 6.283)
    for i in range(kids):
        a = a0 + 2 * math.pi * i / kids + rnd.uniform(-0.4, 0.4)
        side = Vector((math.cos(a), math.sin(a), 0))
        nd = (d + side * spread + Vector((0, 0, 0.3))).normalized()
        tb_coral(bm, rnd, tip - d * (r * 0.4), h * 0.64, r * 0.74, depth - 1, spread, n, nd)
    return bm


def tb_fan_coral(bm, rnd, base, h=0.5, w=0.5, yaw=0.0, th=0.035, lobes=5):
    """A sea fan: a flat, scalloped plate on a short stalk, standing on `base`, facing local +Y."""
    base = Vector(base)
    rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    pts = [Vector((-0.04, 0, 0)), Vector((0.04, 0, 0)), Vector((0.05, 0, h * 0.2))]
    for i in range(lobes * 2 + 1):
        a = math.radians(-8 + 196 * i / (lobes * 2))
        k = (1.0 if i % 2 == 0 else 0.84) * rnd.uniform(0.92, 1.05)
        pts.append(Vector((math.cos(a) * w * 0.5 * k, 0, h * 0.42 + math.sin(a) * h * 0.58 * k)))
    pts.append(Vector((-0.05, 0, h * 0.2)))
    tb_slab(bm, [base + rz @ (p - Vector((0, th * 0.5, 0))) for p in pts], rz @ Vector((0, th, 0)))
    return bm


def tb_tube_coral(kit, rnd, base, n=4, h=(0.18, 0.4), r=0.06, key="salmon:0.1:0.7", dark="black:0.3:0.7"):
    """A cluster of organ-pipe coral: short open tubes, dark inside."""
    base = Vector(base)
    for i in range(n):
        a = rnd.uniform(0, 6.283)
        d = 0.0 if i == 0 else r * rnd.uniform(1.3, 1.9)
        p = base + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        hh = rnd.uniform(*h) * (1.0 if i == 0 else 0.75)
        rr = r * rnd.uniform(0.8, 1.1)
        bm_cyl(kit[key], rr * 0.85, rr, hh, (p.x, p.y, p.z + hh * 0.5), rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 60)), seg=6)
        bm_cyl(kit[dark], rr * 0.62, rr * 0.62, 0.012, (p.x, p.y, p.z + hh + 0.002), seg=6)
    return kit


def tb_weed(bm, rnd, base, h=0.6, n=3, w=0.08, lean=0.3):
    """A tuft of sea weed: flat, wavy fronds."""
    base = Vector(base)
    for k in range(n):
        a = rnd.uniform(0, 6.283)
        out = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-out.y, out.x, 0))
        hh = h * rnd.uniform(0.6, 1.0)
        pts = []
        for i in range(5):
            t = i / 4.0
            pts.append(base + out * (0.05 + lean * hh * t * t + 0.04 * math.sin(t * 7 + a)) + side * (0.05 * math.sin(t * 5 + a * 2))
                       + Vector((0, 0, hh * t)))
        bm_tube(bm, pts, [0.014, 0.014, 0.013, 0.011, 0.0], n=4, up=tuple(out), squash=w / 0.028)
    return bm


def tb_barnacle(kit, p, r=0.05, nrm=(0, 0, 1), key="stone:0.0:0.5", dark="black:0.3:0.7"):
    """One barnacle: a little volcano with a dark mouth, standing on p along nrm."""
    p, nz = Vector(p), Vector(nrm).normalized()
    rot = tuple(math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference(nz).to_euler())
    bm_cyl(kit[key], r, r * 0.55, r * 1.1, tuple(p + nz * (r * 0.5)), rot=rot, seg=6)
    bm_cyl(kit[dark], r * 0.38, r * 0.38, 0.012, tuple(p + nz * (r * 1.06)), rot=rot, seg=5)
    return kit


def tb_bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = Vector(p0), Vector(p1), Vector(p2), Vector(p3)
    out = []
    for i in range(n):
        t = i / (n - 1.0)
        s = 1.0 - t
        out.append(p0 * (s * s * s) + p1 * (3 * s * s * t) + p2 * (3 * s * t * t) + p3 * (t * t * t))
    return out


def tb_rib(bm, foot, toward, reach, height, r0=0.085, r1=0.035, sink=0.15, n=5, seg=8, flat=1.5):
    """A great curved rib standing in the ground at `foot`: it climbs to `height` and arches over toward `toward`
    (a flat direction) by `reach`, tapering; flattened across its bend."""
    foot = Vector(foot)
    d = Vector((toward[0], toward[1], 0.0)).normalized()
    up = Vector((0, 0, 1))
    pts = tb_bezier(foot - up * sink, foot + up * (height * 0.95) - d * (reach * 0.08), foot + d * (reach * 0.55) + up * (height * 1.18),
                    foot + d * reach + up * (height * 0.66), seg)
    rad = []
    for i in range(seg):
        t = i / (seg - 1.0)
        rad.append((r0 + (r1 - r0) * t ** 1.2) * (1.0 + 0.18 * math.sin(math.pi * min(1.0, t * 2.2))))
    bm_tube(bm, pts, rad, n=n, up=tuple(-d), squash=flat)
    return pts


def tb_harpoon(kit, tail, tip, r=0.03, shaft="cream:0.25:0.75", head="iron:0.05:0.55", barbs=2, head_len=0.24, ribbon=None):
    """A barbed harpoon from tail to tip: a bone shaft, an iron head with swept-back barbs, a collar (and a ribbon)."""
    tail, tip = Vector(tail), Vector(tip)
    d = (tip - tail).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    upv = side.cross(d).normalized()
    neck = tip - d * head_len
    bm_tube(kit[shaft], [tail, neck + d * 0.03], r, n=5)
    bm_crystal(kit[head], neck - d * 0.02, tip, r * 2.3, n=4, shoulder=0.3, foot=0.6)
    for i in range(barbs):
        for sv in (side, -side) if i == 0 else (upv, -upv):
            b0 = neck + d * (head_len * 0.42) + sv * (r * 0.8)
            tb_slab(kit[head], [b0 + d * 0.06, b0 - d * 0.12 + sv * (r * 3.6), b0 - d * 0.05], sv.cross(d) * (r * 0.9))
    bm_tube(kit[shaft], [neck - d * 0.05, neck + d * 0.02], r * 1.6, n=5)
    if ribbon:
        p = tail + d * 0.1
        tb_slab(kit[ribbon], [p, p - d * 0.16 + upv * 0.1, p - d * 0.2 + upv * 0.02, p - d * 0.08], side * 0.012)
    return kit


def tb_post(bm, rnd, base, h, r=0.07, lean=(0.0, 0.0), n=6, taper=0.8):
    """A driftwood post standing on base, a little crooked."""
    base = Vector(base)
    top = base + Vector((lean[0], lean[1], h))
    mid = base.lerp(top, 0.5) + Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0))
    bm_tube(bm, [base - Vector((0, 0, 0.05)), mid, top], [r, r * (1 + taper) * 0.5, r * taper], n=n)
    return top


def tb_rope(bm, a, b, sag=0.1, r=0.016, n=4, seg=5):
    """A rope from a to b, sagging in the middle."""
    a, b = Vector(a), Vector(b)
    pts = [a.lerp(b, i / (seg - 1.0)) - Vector((0, 0, sag * 4.0 * (i / (seg - 1.0)) * (1.0 - i / (seg - 1.0)))) for i in range(seg)]
    bm_tube(bm, pts, r, n=n)
    return pts


def tb_net(bm, a, b, drop, cols=6, rows=3, sag=0.12, r=0.011, belly=(0, 0, 0)):
    """A fishing net hung between a and b (its head rope), hanging down by `drop`, sagging; a diamond mesh of cords."""
    a, b = Vector(a), Vector(b)
    bel = Vector(belly)

    def P(u, v):
        p = a.lerp(b, u)
        s = 4.0 * u * (1.0 - u)
        return p - Vector((0, 0, sag * s + drop * v * (0.82 + 0.18 * s))) + bel * (math.sin(math.pi * v) * s)
    for i in range(cols):
        for j in range(rows):
            u0, u1 = i / cols, (i + 1) / cols
            v0, v1 = j / rows, (j + 1) / rows
            um = (u0 + u1) * 0.5
            vm = (v0 + v1) * 0.5
            for p, q in ((P(u0, vm), P(um, v0)), (P(um, v0), P(u1, vm)), (P(u1, vm), P(um, v1)), (P(um, v1), P(u0, vm))):
                bm_beam(bm, p, q, r * 2, r * 2)
    return P


# ------------------------------------------------------------------------------------------- tubes with frames
def tb_frames(pts, up=(0, 0, 1)):
    """The frames bm_tube gives a tube through pts: [(point, the `up` side there, tangent)]."""
    pts = [Vector(p) for p in pts]
    m = len(pts)
    tans = []
    for k in range(m):
        t = pts[min(k + 1, m - 1)] - pts[max(k - 1, 0)]
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    u = Vector(up).normalized()
    x = u - tans[0] * u.dot(tans[0])
    if x.length < 1e-3:
        x = Vector((1, 0, 0)) - tans[0] * tans[0].x
    x.normalize()
    out = []
    for k in range(m):
        t = tans[k]
        x = x - t * x.dot(t)
        if x.length < 1e-6:
            x = t.orthogonal()
        x.normalize()
        out.append((pts[k].copy(), x.copy(), t.copy()))
    return out


def tb_paint_side(obj, frames, swatch, side=-1.0, cos_min=0.3, scale=1.0, team=False, lo=0.12, hi=0.88, span=None):
    """Repaints one side of a tube (the belly / sucker side: against its frames' `up` for side -1) with another
    swatch. span: (first, last) frame to paint between."""
    fr = [(c * scale, x) for c, x, t in frames]

    def where(c, n):
        best, bd = 0, 1e9
        for i, (fc, fx) in enumerate(fr):
            d = (fc - c).length_squared
            if d < bd:
                best, bd = i, d
        if span and not (span[0] <= best <= span[1]):
            return False
        return n.dot(fr[best][1]) * side > cos_min
    return paint_faces(obj, swatch, where, team=team, lo=lo, hi=hi)


def tb_curve(pts, n):
    """n points along a smooth curve through pts (Catmull-Rom), evenly spread by parameter."""
    pts = [Vector(p) for p in pts]
    m = len(pts)
    out = []
    for i in range(n):
        u = i / (n - 1.0) * (m - 1)
        k = min(int(u), m - 2)
        t = u - k
        p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, m - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return out


def tb_even(pts, n):
    """n points evenly spaced by distance along the polyline pts."""
    pts = [Vector(p) for p in pts]
    lens = [0.0]
    for a, b in zip(pts, pts[1:]):
        lens.append(lens[-1] + (b - a).length)
    total = lens[-1]
    out = []
    k = 0
    for i in range(n):
        d = total * i / (n - 1.0)
        while k < len(pts) - 2 and lens[k + 1] < d:
            k += 1
        seg = max(lens[k + 1] - lens[k], 1e-9)
        out.append(pts[k].lerp(pts[k + 1], min(max((d - lens[k]) / seg, 0.0), 1.0)))
    return out


# ------------------------------------------------------------------------------------------- bone chains
def tb_chain(bones, name, pts, parent="root"):
    """Adds bones name.1 .. name.N along pts to a bones dict. Returns their names."""
    prev = parent
    names = []
    for i in range(len(pts) - 1):
        nm = "%s.%d" % (name, i + 1)
        bones[nm] = (tuple(pts[i]), tuple(pts[i + 1]), prev)
        prev = nm
        names.append(nm)
    return names


def tb_turns(rest_pts, pts):
    """For a chain laid along rest_pts: the armature-space turn that carries each bone onto the matching stretch of
    pts (another shape for the same chain; only its directions matter)."""
    out = []
    for i in range(len(rest_pts) - 1):
        d0 = (Vector(rest_pts[i + 1]) - Vector(rest_pts[i])).normalized()
        d1 = (Vector(pts[i + 1]) - Vector(pts[i])).normalized()
        out.append(d0.rotation_difference(d1))
    return out


def tb_mix(a, b, t):
    """Blends two lists of turns (tb_turns); either may be None (the rest shape)."""
    ident = Quaternion()
    n = len(a if a is not None else b)
    return [(a[i] if a is not None else ident).slerp(b[i] if b is not None else ident, t) for i in range(n)]


def tb_pose_chain(rig, name, turns, extra=None, base=None):
    """Poses chain name.1 .. name.N so that bone i is turned by turns[i] in armature space (then extra[i], a further
    armature-space turn, on top: a wave running along a tentacle). base: the turn the chain's parent already has."""
    pb = rig.pose.bones
    prev = base.copy() if base is not None else Quaternion()
    for i, q in enumerate(turns):
        b = pb["%s.%d" % (name, i + 1)]
        tot = (extra[i] @ q) if extra else q
        own = prev.inverted() @ tot
        r = b.bone.matrix_local.to_quaternion()
        b.rotation_quaternion = r.inverted() @ own @ r
        prev = tot


def tb_wave(n, axis, amp, phase, step=0.7, grow=1.0):
    """Turns for a wave running down a chain of n bones: bone i swings amp * (its share) * sin(phase - i * step)
    degrees about `axis` (armature space). grow: how much more the far end swings than the near end."""
    ax = Vector(axis).normalized()
    out = []
    for i in range(n):
        k = 1.0 + (grow - 1.0) * (i / max(1, n - 1))
        out.append(Quaternion(ax, math.radians(amp * k * math.sin(phase - i * step))))
    return out


# ------------------------------------------------------------------------------------------- rigid parts, few objects
class RigidKit(Kit):
    """A Kit for a machine or an armoured beast: every piece is rigid-skinned to the bone that was current when it was
    added, and emit() still makes just one object per color for the lot.

        rk = RigidKit()
        rk.to("arm.L"); bm_tube(rk["red"], ...)
        rk.to("claw.L"); bm_tube(rk["red"], ...); bm_crystal(rk["cream"], ...)
        rk.emit("Head_Limbs", col, rig, scale=S)
    """

    def __init__(self):
        Kit.__init__(self)
        self.ids = ["root"]
        self.cur = 1

    def _tag(self):
        for bm in self.parts.values():
            lay = bm.verts.layers.int["tb_bone"]
            for v in bm.verts:
                if v[lay] == 0:
                    v[lay] = self.cur

    def to(self, bone):
        self._tag()
        if bone not in self.ids:
            self.ids.append(bone)
        self.cur = self.ids.index(bone) + 1
        return self

    def __getitem__(self, key):
        if key not in self.parts:
            bm = bmesh.new()
            bm.verts.layers.int.new("tb_bone")
            self.parts[key] = bm
        return self.parts[key]

    def emit(self, name, col, rig, bevel=0.0, vary=0.0, seed=1, scale=1.0, segments=1, tag=None):
        self._tag()
        ids = list(self.ids)
        objs = Kit.emit(self, name, col, bevel=bevel, vary=vary, seed=seed, rig=rig, bone="root", scale=scale, segments=segments, tag=tag)
        for o in objs:
            me = o.data
            attr = me.attributes.get("tb_bone")
            vals = [0] * len(me.vertices)
            if attr is not None:
                attr.data.foreach_get("value", vals)
            o.vertex_groups.clear()
            groups = {}
            for i, b in enumerate(vals):
                groups.setdefault(ids[b - 1] if b > 0 else "root", []).append(i)
            for bone, idx in groups.items():
                o.vertex_groups.new(name=bone).add(idx, 1.0, "REPLACE")
            if attr is not None:
                me.attributes.remove(attr)
        self.ids = ["root"]
        self.cur = 1
        return objs


# ------------------------------------------------------------------------------------------- pieces set in place
def tb_merge(kit, part, M=None):
    """Adds another Kit's geometry to kit, moved by the matrix M: build a piece at the origin in a Kit of its own, then
    set it in place (tilted, turned, mirrored)."""
    for key, bm in part.parts.items():
        if not bm.verts:
            bm.free()
            continue
        if M is not None:
            bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
            if M.to_3x3().determinant() < 0:
                bmesh.ops.reverse_faces(bm, faces=bm.faces)
        me = bpy.data.meshes.new("tb_tmp")
        bm.to_mesh(me)
        bm.free()
        kit[key].from_mesh(me)
        bpy.data.meshes.remove(me)
    part.parts = {}
    return kit


def tb_place(pos, yaw=0.0, pitch=0.0, roll=0.0, origin=(0, 0, 0)):
    """A matrix for tb_merge: the piece's `origin` goes to pos; turned by yaw (about Z), its +Y end lifted by pitch,
    rolled about its +Y by roll (degrees)."""
    return (Matrix.Translation(Vector(pos)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pitch), 4, "X")
            @ Matrix.Rotation(math.radians(roll), 4, "Y") @ Matrix.Translation(-Vector(origin)))


def tb_dist_outline(pts, p):
    """The distance from p to a closed outline."""
    best = 1e9
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        e = b - a
        t = min(max((p - a).dot(e) / max(e.length_squared, 1e-12), 0.0), 1.0)
        best = min(best, (a + e * t - p).length)
    return best


def tb_star_pool(cells, origin, margin=0.5, step=5.0):
    """A pool outline (counterclockwise, one point every `step` degrees) spreading from `origin` as far as it can
    while keeping `margin` inside the footprint. margin: a number, or f(angle in degrees) -> a number."""
    edge = outline(cells)
    o = Vector((origin[0], origin[1], 0.0))
    pts = []
    a = 0.0
    while a < 360.0 - 1e-6:
        m = margin(a) if callable(margin) else margin
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0))
        r = 0.1
        while r < 30.0:
            p = o + d * (r + 0.03)
            if not inside(edge, p.x, p.y) or tb_dist_outline(edge, p) < m:
                break
            r += 0.03
        pts.append(o + d * r)
        a += step
    return pts


def tb_disc(bm, p, nrm, r, h, seg=5, top=0.7):
    """A low stud standing on p along nrm (a sucker, a rivet, a boss)."""
    p, nz = Vector(p), Vector(nrm).normalized()
    x = nz.orthogonal().normalized()
    y = nz.cross(x)
    lo = [bm.verts.new(p + (x * math.cos(2 * math.pi * i / seg) + y * math.sin(2 * math.pi * i / seg)) * r) for i in range(seg)]
    hi = [bm.verts.new(p + nz * h + (x * math.cos(2 * math.pi * i / seg) + y * math.sin(2 * math.pi * i / seg)) * (r * top)) for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(hi)
    return bm


def tb_foam(bm, c, r, a0, a1, w=0.07, z=0.0, seg=None):
    """A streak of foam lying on the water: part of a ring round c from angle a0 to a1 (degrees), pointed at both ends."""
    c = Vector(c)
    seg = seg or max(3, int(abs(a1 - a0) / 14.0))
    inner, outer = [], []
    for i in range(seg + 1):
        t = i / float(seg)
        a = math.radians(a0 + (a1 - a0) * t)
        hw = w * 0.5 * (math.sin(math.pi * t) ** 0.6 if 0 < i < seg else 0.0) + 0.004
        inner.append(bm.verts.new((c.x + math.cos(a) * (r - hw), c.y + math.sin(a) * (r - hw), z)))
        outer.append(bm.verts.new((c.x + math.cos(a) * (r + hw), c.y + math.sin(a) * (r + hw), z)))
    for i in range(seg):
        f = bm.faces.new((inner[i], outer[i], outer[i + 1], inner[i + 1]))
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    return bm


def tb_keg(kit, c, axis, length=0.36, r=0.14, wood="wood:0.2:0.8", hoop="iron:0.2:0.7"):
    """A keg lying (or standing) at c along `axis`."""
    c, ax = Vector(c), Vector(axis).normalized()
    up = (0, 0, 1) if abs(ax.z) < 0.9 else (1, 0, 0)
    bm_tube(kit[wood], [c + ax * (length * t) for t in (-0.5, -0.28, 0.0, 0.28, 0.5)], [r * 0.8, r * 0.96, r, r * 0.96, r * 0.8], n=8, up=up)
    for t in (-0.33, 0.33):
        bm_tube(kit[hoop], [c + ax * (length * (t - 0.04)), c + ax * (length * (t + 0.04))], r * 0.955, n=8, up=up)
    return kit


def tb_spar(kit, rnd, foot, head, r0=0.09, r1=0.07, key="wood_dark:0.2:0.85", splinter="wood:0.2:0.8", n=7):
    """A mast or spar from foot to head, snapped off at the head (splinters stand up from the break)."""
    foot, head = Vector(foot), Vector(head)
    d = (head - foot).normalized()
    bm_tube(kit[key], [foot, foot.lerp(head, 0.5), head], [r0, (r0 + r1) * 0.5, r1], n=n)
    if splinter:
        side = d.orthogonal().normalized()
        other = d.cross(side)
        for j in range(4):
            a = math.radians(90 * j + 20)
            off = side * math.cos(a) + other * math.sin(a)
            bm_crystal(kit[splinter], head - d * 0.04 + off * (r1 * 0.4), head + d * rnd.uniform(0.1, 0.24) + off * (r1 * 0.75), r1 * 0.5, n=4, shoulder=0.3)
    return d


def tb_rag(bm, a, b, drops, th=0.016, rows=4, billow=(0, -0.1, 0), ripple=0.05):
    """A torn sail hanging from the yard a -> b: one column of cloth per entry of drops (how far it hangs there),
    bellied out by the vector billow. A thin solid."""
    a, b = Vector(a), Vector(b)
    bl = Vector(billow)
    along = (b - a).normalized()
    cols = len(drops)
    grid = []
    for i, drop in enumerate(drops):
        u = i / (cols - 1.0)
        top = a.lerp(b, u)
        grid.append([top + Vector((0, 0, -drop * v)) + bl * (math.sin(v * 2.6) * (0.5 + 0.5 * math.sin(u * 3.1 + 0.4)))
                     + along * (ripple * math.sin(v * 3.0 + u * 4.0) * v) for v in [j / (rows - 1.0) for j in range(rows)]])
    tb_sheet(bm, grid, th)
    return grid


# ------------------------------------------------------------------------------------------- hulls
def tb_hull_shape(length, beam, depth):
    """A hull as two functions: P(t, u, side) -> the point of its skin at station t (0 the stern .. 1 the stem,
    along +Y) and height u (0 the keel .. 1 the gunwale; over 1 stands proud of it), on side +1 (+X) or -1; and
    N(t, u, side) -> the outward normal of the skin there (in the plane of the station)."""
    def dims(t):
        w = beam * (1.0 - max(0.0, (t - 0.4) / 0.6) ** 2.0) ** 0.75 * (0.8 + 0.2 * min(1.0, t / 0.25))
        kz = depth * 0.85 * max(0.0, (t - 0.62) / 0.38) ** 2.2
        g = depth * (1.0 + 0.5 * max(0.0, (t - 0.3) / 0.7) ** 2.0 + 0.25 * max(0.0, (0.3 - t) / 0.3) ** 2.0)
        return max(w, 0.035), kz, g

    def P(t, u, side=1.0):
        w, kz, g = dims(t)
        u = max(u, 0.0)
        return Vector((side * w * u ** 0.55, length * t, kz + (g - kz) * u ** 1.6))

    def N(t, u, side=1.0):
        a, b = P(t, max(u - 0.02, 0.0), 1.0), P(t, u + 0.02, 1.0)
        d = b - a
        n = Vector((d.z, 0.0, -d.x))
        n = n.normalized() if n.length > 1e-9 else Vector((1, 0, 0))
        return Vector((n.x * side, 0.0, n.z))
    return P, N


def tb_hull(kit, rnd, length=3.0, beam=0.55, depth=0.55, t0=0.4, t1=1.0, strakes=4, stations=6, th=0.04, ragged=0.12,
            plank="wood:0.2:0.85", frame="wood_dark:0.25:0.9", ribs=(0.5, 0.64, 0.78), deck=(0.76, 0.95), deck_key="sand:0.35:0.85"):
    """A piece of a wrecked wooden ship in its own space (the keel along +Y on z = 0, the stem at y = length), from
    station t0 to t1: lapped strakes snapped off at different lengths where it broke, the keel running up into a
    scrolled stem post (when t1 is 1), ribs standing inside, gunwale rails, a scrap of foredeck. Returns (P, N)."""
    P, N = tb_hull_shape(length, beam, depth)
    cut0, cut1 = t0 > 0.0, t1 < 1.0
    for side in (1.0, -1.0):
        ends = []
        for j in range(strakes):
            u0, u1 = j / float(strakes), (j + 1.0) / strakes
            ts = t0 + (rnd.uniform(0.0, ragged) if cut0 else 0.0)
            te = t1 - (rnd.uniform(0.0, ragged) if cut1 else 0.0)
            ends.append((ts, te))
            rings = []
            for i in range(stations):
                t = ts + (te - ts) * (i / (stations - 1.0)) ** 0.85
                n0, n1 = N(t, max(u0, 0.03), side), N(t, u1, side)
                a = P(t, u0, side) + n0 * (th * 0.45)
                b = P(t, u1, side)
                rings.append([a, b, b - n1 * th, a - n0 * (th * 1.2)])
            bm_loft(kit[plank], rings)
        ts, te = ends[-1]
        bm_tube(kit[frame], [P(ts + (te - ts) * i / 5.0, 1.0, side) + Vector((0, 0, 0.015)) for i in range(6)], 0.042, n=4, phase=0.5)
        for t in ribs:
            if t0 + 0.02 < t < t1 - 0.02:
                top = 1.0 + rnd.uniform(0.02, 0.2)
                bm_tube(kit[frame], [P(t, u, side) - N(t, max(u, 0.06), side) * (th + 0.03) for u in (0.03, 0.3, 0.62, 0.9, top)], 0.034, n=4, phase=0.5)
    ks = t0 + (ragged * 0.6 if cut0 else 0.0)
    ke = t1 - (ragged * 0.6 if cut1 else 0.0)
    kp = [Vector((0.0, length * t, P(t, 0.0)[2] - 0.03)) for t in [ks + (ke - ks) * i / 6.0 for i in range(7)]]
    if not cut1:
        g = P(1.0, 1.0)[2]
        kp += [Vector((0, length + 0.035, kp[-1].z + (g - kp[-1].z) * 0.6)), Vector((0, length + 0.06, g + 0.2)), Vector((0, length + 0.1, g + 0.4)),
               Vector((0, length + 0.03, g + 0.54)), Vector((0, length - 0.1, g + 0.5)), Vector((0, length - 0.13, g + 0.4)),
               Vector((0, length - 0.07, g + 0.36))]
    bm_tube(kit[frame], kp, [0.05] * (len(kp) - 1) + [0.035], n=6, up=(1, 0, 0), squash=1.5)
    if deck and deck[0] < t1:
        n = 5
        for i in range(n):
            t = deck[0] + (min(deck[1], t1) - deck[0]) * (i + 0.5) / n
            p = P(t, 0.8)
            bm_box(kit[deck_key], (2 * (p.x - th * 0.6), length * (min(deck[1], t1) - deck[0]) / n * 0.93, 0.035), (0, p.y, p.z + rnd.uniform(-0.006, 0.006)))
    return P, N


# ------------------------------------------------------------------------------------------- tentacles
def tb_tentacle(kit, ctrl, r0, r1, bones=8, rings=None, n=8, up=(0, 0, 1), body="red:0.3:0.95", sucker="cream:0.1:0.7", taper=1.0,
                discs=True):
    """A tentacle through the control points ctrl, tapering from r0 to r1 and ending in a point; its sucker side is the
    one against `up` (carried along it). discs: True, or (first, last) ring to give suckers. Returns (bone points for a
    chain of `bones` bones along it, the frames of its rings for tb_paint_side / tb_paint_span)."""
    path = tb_curve(ctrl, max(40, 10 * len(ctrl)))
    bpts = tb_even(path, bones + 1)
    m = rings or bones * 2 + 1
    rp = tb_even(path, m)
    rad = [r0 + (r1 - r0) * (i / (m - 1.0)) ** taper for i in range(m)]
    end = rp[-1] + (rp[-1] - rp[-2]).normalized() * (rad[-1] * 1.7)
    pts, rr = rp + [end], rad + [0.0]
    bm_tube(kit[body], pts, rr, n=n, up=up, phase=0.5)
    frames = tb_frames(pts, up)
    if discs:
        i0, i1 = (1, m - 2) if discs is True else discs
        for i in range(max(1, i0), min(m - 2, i1) + 1):
            c, x, t = frames[i]
            y = t.cross(x)
            r = rad[i]
            tb_disc(kit[sucker], c - x * (r * 0.9) + y * ((1 if i % 2 else -1) * r * 0.17), -x, r * 0.21, r * 0.12)
    return bpts, frames


def tb_paint_span(obj, frames, swatch, span, scale=1.0, team=False, lo=0.12, hi=0.88, side=None, cos_min=0.0):
    """Repaints a tube all the way round between two of its rings (a painted band): span = (first, last) stretch, stretch
    i lying between ring i and ring i + 1. side: only that side (+1 the `up` side, -1 the sucker side)."""
    mids = [((frames[i][0] + frames[i + 1][0]) * 0.5 * scale, frames[i][1]) for i in range(len(frames) - 1)]

    def where(c, n):
        best, bd = 0, 1e9
        for i, (mc, mx) in enumerate(mids):
            d = (mc - c).length_squared
            if d < bd:
                best, bd = i, d
        if not (span[0] <= best <= span[1]):
            return False
        return side is None or n.dot(mids[best][1]) * side > cos_min
    return paint_faces(obj, swatch, where, team=team, lo=lo, hi=hi)


def tb_crest(bm, frames, rad, i0, i1, h, rays=3, lean=0.35, th=0.03, sink=0.12, notch=0.55, side=None):
    """A webbed fin standing on a tube (tb_frames) between its rings i0 and i1: `rays` spines `h` long, leaning back
    against the way the tube runs. side: a turn (degrees) round the tube from its `up` side (0 = a dorsal fin)."""
    def at(u):
        i = min(int(u), len(frames) - 2)
        f = u - i
        c = frames[i][0].lerp(frames[i + 1][0], f)
        x = frames[i][1].lerp(frames[i + 1][1], f).normalized()
        t = frames[i][2].lerp(frames[i + 1][2], f).normalized()
        if side:
            x = Quaternion(t, math.radians(side)) @ x
        r = rad[i] + (rad[min(i + 1, len(rad) - 1)] - rad[i]) * f
        return c, x, t, r
    c, x, t, r = at(i0)
    b0 = c + x * (r * (1 - sink))
    c, x, t, r = at(i1)
    b1 = c + x * (r * (1 - sink))
    tips = []
    for j in range(rays):
        u = (j + 0.5) / rays
        c, x, t, r = at(i0 + (i1 - i0) * u)
        tips.append(c + x * (r + h * (0.7 + 0.3 * math.sin(math.pi * u))) - t * (lean * h))
    tb_fin(bm, b0, b1, tips, th=th, notch=notch)
    return bm


def tb_kerb(bm, rnd, loop, z0, z1, th=0.2, gap=0.025, jit=0.015, skip=None):
    """A kerb of dressed stones along a closed outline (counterclockwise): each stone runs from one point to the next,
    `th` wide to the inside of the outline, from z0 up to z1. skip(point) -> True leaves a stone out."""
    n = len(loop)
    nr = tb_normals(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        if skip and skip((a + b) * 0.5):
            continue
        d = b - a
        ln = d.length
        if ln < gap * 3:
            continue
        u = d / ln
        g = gap * 0.5
        t = th + rnd.uniform(-jit, jit)
        zt = z1 + rnd.uniform(-jit, jit)
        base = [a + u * g, b - u * g, b - nr[(i + 1) % n] * t - u * g, a - nr[i] * t + u * g]
        lo = [bm.verts.new((p.x, p.y, z0)) for p in base]
        hi = [bm.verts.new((p.x, p.y, zt)) for p in base]
        fs = [bm.faces.new(hi), bm.faces.new(list(reversed(lo)))]
        for q in range(4):
            j = (q + 1) % 4
            fs.append(bm.faces.new((lo[q], lo[j], hi[j], hi[q])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def tb_set_turn(pb, parent_turn, turn):
    """Poses one bone so that it is turned by `turn` in armature space, its parent already being turned by parent_turn
    (the last of a chain posed with tb_pose_chain, say). Returns turn."""
    r = pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion = r.inverted() @ (parent_turn.inverted() @ turn) @ r
    return turn


def tb_sections(rows, n=8, power=2.4, phase=0.5, grow=0.0):
    """Rings for bm_loft from rows of (y, z, half width, half height): a body or a skull lying along +Y."""
    return [oval((0, y, z), (1, 0, 0), (0, 0, 1), rx + grow, rz + grow, n, power=power, phase=phase) for y, z, rx, rz in rows]


def tb_chunk(bm, rnd, c, rings, n=8, jit=0.12):
    """A faceted block of rock with a flat top and bottom: the hull of rings of points round c, each ring (z, radius) or
    (z, rx, ry) above c, their points jittered. Stack a few for a sea stack worn in at the waist."""
    c = Vector(c)
    vs = []
    for ring_ in rings:
        z, rx = ring_[0], ring_[1]
        ry = ring_[2] if len(ring_) > 2 else rx
        a0 = rnd.uniform(0, 6.283)
        for i in range(n):
            a = a0 + 2 * math.pi * i / n + rnd.uniform(-0.2, 0.2)
            kk = 1.0 + rnd.uniform(-jit, jit)
            vs.append(bm.verts.new((c.x + math.cos(a) * rx * kk, c.y + math.sin(a) * ry * kk, c.z + z)))
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = list({e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def tb_net_quad(bm, p00, p10, p01, p11, cols=5, rows=3, sag=0.08, r=0.012, rope=0.02):
    """A net stretched over four corners (p00 -> p10 its head rope, p01 -> p11 its foot rope), sagging in the middle:
    a diamond mesh of cords between two ropes. Returns P(u, v) -> a point of it."""
    p00, p10, p01, p11 = Vector(p00), Vector(p10), Vector(p01), Vector(p11)

    def P(u, v):
        p = p00.lerp(p10, u).lerp(p01.lerp(p11, u), v)
        return p - Vector((0, 0, sag * 16.0 * u * (1 - u) * v * (1 - v)))
    for i in range(cols):
        for j in range(rows):
            u0, u1, v0, v1 = i / float(cols), (i + 1.0) / cols, j / float(rows), (j + 1.0) / rows
            um, vm = (u0 + u1) * 0.5, (v0 + v1) * 0.5
            for p, q in ((P(u0, vm), P(um, v0)), (P(um, v0), P(u1, vm)), (P(u1, vm), P(um, v1)), (P(um, v1), P(u0, vm))):
                bm_tube(bm, [p, q], r, n=3, cap=False)
    for v in (0.0, 1.0):
        bm_tube(bm, [P(i / float(cols), v) for i in range(cols + 1)], rope, n=4)
    return P


# ------------------------------------------------------------------------------------------- merfolk
# A figure built from lofts: a torso, a head with a face and ear fins, two arms, a fish tail with a forked fin. It is laid
# out at scale 1 with its hips at the origin, facing +Y, and set into the rig by its spec:
#   at (where the hips go, in the rig's space), yaw, lean (degrees forward), scale,
#   tail (points from the hips down along the tail, in the figure's space), tail_bones, tail_r (radius at hips, at fin),
#   arms {"L": (elbow, wrist), "R": (elbow, wrist)} (the figure's space; tb_ik finds elbows),
#   skin, tail_key, belly, fin_key (Kit colors), brow (a color, or None), mouth (True for an open mouth), fork (the fin's rays).
MER_TORSO = [(0.0, 0.165, 0.125, 0.0), (0.13, 0.145, 0.11, 0.0), (0.3, 0.2, 0.135, 0.01), (0.4, 0.215, 0.125, 0.0), (0.455, 0.12, 0.09, 0.0),
             (0.5, 0.075, 0.07, 0.0)]
MER_HEAD = [(0.5, 0.085, 0.08), (0.545, 0.15, 0.145), (0.62, 0.178, 0.17), (0.72, 0.18, 0.172), (0.8, 0.15, 0.145), (0.845, 0.08, 0.075)]
MER_SHOULDER = (0.235, 0.0, 0.405)
MER_ARM = (0.2, 0.2)


def tb_ik(sh, wr, l1=0.2, l2=0.2, hint=(0, -1, -1)):
    """Where the elbow goes for a shoulder at sh and a wrist at wr (upper arm l1 long, forearm l2), bent toward `hint`.
    Returns (elbow, wrist): the wrist is pulled in if it was out of reach."""
    sh, wr = Vector(sh), Vector(wr)
    d = wr - sh
    dist = max(d.length, 1e-6)
    reach = (l1 + l2) * 0.985
    if dist > reach:
        wr = sh + d * (reach / dist)
        d, dist = wr - sh, reach
    u = d / dist
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    hv = Vector(hint)
    hv = hv - u * hv.dot(u)
    hv = hv.normalized() if hv.length > 1e-6 else u.orthogonal().normalized()
    return sh + u * a + hv * h, wr


def tb_mer_matrix(spec):
    s = spec.get("scale", 1.0)
    return (Matrix.Translation(Vector(spec["at"])) @ Matrix.Rotation(math.radians(spec.get("yaw", 0.0)), 4, "Z")
            @ Matrix.Rotation(math.radians(-spec.get("lean", 0.0)), 4, "X") @ Matrix.Diagonal((s, s, s, 1.0)))


def tb_mer_torso(z, ang, grow=0.0):
    """A point on the figure's torso (its own space) at height z, `ang` degrees round it (0 its right side, 90 its front)."""
    rows = MER_TORSO
    z = min(max(z, rows[0][0]), rows[-1][0])
    for a, b in zip(rows, rows[1:]):
        if a[0] <= z <= b[0]:
            f = (z - a[0]) / (b[0] - a[0])
            hw, hd, y0 = a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f
            break
    e = 2.0 / 2.6
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return Vector((math.copysign(abs(ca) ** e, ca) * (hw + grow), y0 + math.copysign(abs(sa) ** e, sa) * (hd + grow), z))


def tb_mer_band(bm, z_of, width, grow=0.014, n=16):
    """A band of cloth or metal round the torso (the figure's space): its lower edge at height z_of(angle in degrees),
    `width` tall: a belt (a constant), a sash (slanting from one shoulder to the other hip)."""
    lo = [tb_mer_torso(z_of(360.0 * i / n), 360.0 * i / n, grow) for i in range(n)]
    hi = [tb_mer_torso(z_of(360.0 * i / n) + width, 360.0 * i / n, grow) for i in range(n)]
    bm_loft(bm, [lo, hi], cap0=False, cap1=False)
    return bm


def tb_mer_bones(bones, spec, parent="root", pre=""):
    """Adds the figure's bones to a bones dict: hips, chest, head, arm.L/R.1/.2, tail.1.., fin. The tail hangs from
    `parent` (it stays put where it lies), and so do the hips, which turn on the top of it. Returns the figure's matrix."""
    M = tb_mer_matrix(spec)
    F = lambda p: tuple(M @ Vector(p))
    bones[pre + "hips"] = (F((0, 0, -0.02)), F((0, 0, 0.2)), parent)
    bones[pre + "chest"] = (F((0, 0, 0.2)), F((0, 0, 0.46)), pre + "hips")
    bones[pre + "head"] = (F((0, 0, 0.47)), F((0, 0, 0.82)), pre + "chest")
    for sx, s in ((-1, "L"), (1, "R")):
        sh = Vector((sx * MER_SHOULDER[0], MER_SHOULDER[1], MER_SHOULDER[2]))
        el, wr = [Vector(p) for p in spec["arms"][s]]
        bones[pre + "arm.%s.1" % s] = (F(sh), F(el), pre + "chest")
        bones[pre + "arm.%s.2" % s] = (F(el), F(wr + (wr - el).normalized() * 0.09), pre + "arm.%s.1" % s)
    tail = [M @ p for p in tb_even(tb_curve(spec["tail"], 40), spec.get("tail_bones", 4) + 1)]
    names = tb_chain(bones, pre + "tail", tail, parent=parent)
    bones[pre + "fin"] = (tuple(tail[-1]), tuple(tail[-1] + (tail[-1] - tail[-2]).normalized() * (0.25 * spec.get("scale", 1.0))), names[-1])
    return M


def tb_merfolk(col, rig, spec, name="Mer", pre=""):
    """Builds the figure, skinned to the bones tb_mer_bones() made. Returns a dict: M (its matrix), hand {"L","R"}
    (the rig's space), tail (its frames in the rig's space), torso / head_obj / tail_obj (the meshes)."""
    M = tb_mer_matrix(spec)
    R3 = M.to_3x3()
    skin = spec.get("skin", "sky:0.15:0.5")
    tail_key = spec.get("tail_key", "teal:0.1:0.9")
    fin_key = spec.get("fin_key", "sky:0.0:0.5")
    k, part = Kit(), Kit()
    out = {"M": M, "hand": {}}
    # torso and neck
    bm_loft(part[skin], [oval((0, y0, z), (1, 0, 0), (0, 1, 0), hw, hd, 8, power=2.6, phase=0.5) for z, hw, hd, y0 in MER_TORSO])
    tb_merge(k, part, M)
    out["torso"] = k.emit(name + "_Torso", col, rig=rig, bones=[pre + "hips", pre + "chest"])[0]
    # head: a rounded block, dark eyes, brows, ear fins
    bm_loft(part[skin], [oval((0, 0, z), (1, 0, 0), (0, 1, 0), hw, hd, 8, power=2.3, phase=0.5) for z, hw, hd in MER_HEAD])
    for sx in (-1, 1):
        bm_ellipsoid(part["black:0.2:0.6"], (sx * 0.072, 0.166, 0.665), (0.03, 0.014, 0.046), u=6, v=4)
        bm_box(part["white:0.0:0.2"], (0.014, 0.01, 0.016), (sx * 0.064, 0.18, 0.682))
        if spec.get("brow"):
            bm_box(part[spec["brow"]], (0.08, 0.022, 0.024), (sx * 0.072, 0.172, 0.738), (0, sx * spec.get("brow_tilt", 14.0), 0))
        tb_fin(part[fin_key], (sx * 0.172, 0.012, 0.75), (sx * 0.172, -0.012, 0.6), [(sx * 0.31, -0.07, 0.82), (sx * 0.35, -0.11, 0.69), (sx * 0.28, -0.09, 0.57)],
               th=0.022, notch=0.6)
    if spec.get("mouth"):
        bm_ellipsoid(part["black:0.3:0.7"], (0, 0.168, 0.572), (0.03, 0.012, 0.024), u=6, v=3)
    tb_merge(k, part, M)
    out["head_obj"] = k.emit(name + "_Head", col, rig=rig, bone=pre + "head")
    # arms: a tube each over its two bones, a mitt for a hand
    for sx, s in ((-1, "L"), (1, "R")):
        sh = Vector((sx * MER_SHOULDER[0], MER_SHOULDER[1], MER_SHOULDER[2]))
        el, wr = [Vector(p) for p in spec["arms"][s]]
        d = (wr - el).normalized()
        bm_tube(part[skin], [sh - (el - sh).normalized() * 0.05 - Vector((sx * 0.03, 0, 0)), sh, el, wr], [0.06, 0.08, 0.063, 0.052], n=6)
        bm_ellipsoid(part[skin], tuple(wr + d * 0.045), (0.064, 0.064, 0.064), u=6, v=4)
        tb_merge(k, part, M)
        k.emit(name + "_Arm" + s, col, rig=rig, bones=[pre + "arm.%s.1" % s, pre + "arm.%s.2" % s])
        out["hand"][s] = M @ (wr + d * 0.05)
    # tail: a tube over its chain, paler along the belly, banded like rows of scales; a ridge of fins; the forked fin on a bone
    nt = spec.get("tail_bones", 4)
    tp = tb_even(tb_curve(spec["tail"], 40), nt * 2 + 1)
    r0, r1 = spec.get("tail_r", (0.168, 0.045))
    m = len(tp) - 1
    rad = [r0 + (r1 - r0) * (i / float(m)) ** 0.85 for i in range(m + 1)]
    up = spec.get("tail_up", (0, -1, 0))
    bm_tube(part[tail_key], tp, rad, n=8, up=up, phase=0.5)
    local = tb_frames(tp, up)
    for i0, i1, h in spec.get("crests", ((1.2, 2.8, 0.1), (3.2, 4.8, 0.085))):
        tb_crest(part[fin_key], local, rad, i0, i1, h, rays=2, lean=0.4, th=0.02)
    tb_merge(k, part, M)
    tail = k.emit(name + "_Tail", col, rig=rig, bones=[pre + "tail.%d" % (i + 1) for i in range(nt)])[0]
    frames = [(M @ c, (R3 @ x).normalized(), (R3 @ t).normalized()) for c, x, t in local]
    for i in range(1, m, 2):
        tb_paint_span(tail, frames, tail_key.split(":")[0], (i, i), lo=0.55, hi=1.0)
    tb_paint_side(tail, frames, spec.get("belly", "cream"), side=-1.0, cos_min=0.5, lo=0.15, hi=0.7)
    out["tail"], out["tail_obj"] = frames, tail
    c, x, t = local[-1]
    side = t.cross(x)
    fork = spec.get("fork", ((-62, 0.34), (-36, 0.3), (-10, 0.15), (10, 0.15), (36, 0.3), (62, 0.34)))
    tb_fin(part[fin_key], c - side * 0.05 - t * 0.03, c + side * 0.05 - t * 0.03,
           [c + t * (ln * math.cos(math.radians(a))) + side * (ln * math.sin(math.radians(a))) for a, ln in fork], th=0.026, notch=0.5)
    tb_merge(k, part, M)
    k.emit(name + "_Fin", col, rig=rig, bone=pre + "fin")
    return out
