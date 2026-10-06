"""Shared pieces of the Tide Spire, the Whirlpool Shrine and the Tidecaller Spire (the Tidal Court's structures):
spiral shells, branching coral, barnacles, kelp that sways on bones, scallops, starfish, tidal pools inside a rim of
sea-worn stones, water rings and falls that move on bones, ice.

Exec'd by a tower script after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "tide_spires_common.py"), encoding="utf-8").read())
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

SEA = (0.45, 0.85, 1.0)             # the sea-blue glow
PEARL_C = (0.78, 0.95, 1.0)
ICE_C = (0.7, 0.92, 1.0)


def _perp(d):
    """Two unit vectors square to d (and to each other)."""
    d = Vector(d).normalized()
    x = d.cross(Vector((0, 0, 1)))
    if x.length < 1e-3:
        x = Vector((1, 0, 0))
    x.normalize()
    return x, d.cross(x).normalized()


def rot_about(v, axis, deg):
    return Quaternion(Vector(axis).normalized(), math.radians(deg)) @ Vector(v)


# ------------------------------------------------------------------------------------------- flat water
def bm_flat(bm, pts, z=None):
    """One flat face through pts (counterclockwise seen from above), facing up."""
    vs = [bm.verts.new((p[0], p[1], p[2] if z is None else z)) for p in pts]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return f


def circle_pts(c, r, n=16, phase=0.0, ry=None):
    c = Vector(c)
    ry = r if ry is None else ry
    return [Vector((c.x + r * math.cos(2 * math.pi * (i + phase) / n), c.y + ry * math.sin(2 * math.pi * (i + phase) / n), c.z))
            for i in range(n)]


def bm_ring_flat(bm, c, r_out, r_in, z, seg=20, th=0.012, crest=0.0):
    """A ring lying on the water at height z (a ripple): flat, `th` thick; crest: its middle line raised (a low wave)."""
    c = Vector(c)
    rm = (r_out + r_in) * 0.5
    prof = [(r_out, 0.0), (rm, th + crest), (r_in, 0.0)] if crest > 0 else [(r_out, 0.0), (r_out, th), (r_in, th), (r_in, 0.0)]
    rows = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        rows.append([bm.verts.new((c.x + r * math.cos(a), c.y + r * math.sin(a), z + dz)) for r, dz in prof])
    m = len(prof)
    for i in range(seg):
        j = (i + 1) % seg
        for q in range(m):
            w = (q + 1) % m
            bm.faces.new((rows[i][q], rows[j][q], rows[j][w], rows[i][w]))
    return bm


# ------------------------------------------------------------------------------------------- stones
def rim_stones(bm_by, rnd, pts, z, r=(0.14, 0.22), squash=(1.25, 1.0, 0.62), jitter=0.05, n=11):
    """Sea-worn stones along a closed line of points (one stone per point), long side along the line.
    bm_by: a function () -> the bmesh for the next stone (so stones can take turns between swatches)."""
    m = len(pts)
    for i, p in enumerate(pts):
        a, b = Vector(pts[i - 1]), Vector(pts[(i + 1) % m])
        d = (b - a)
        yaw = math.atan2(d.y, d.x)
        rr = rnd.uniform(*r)
        q = Vector((p[0] + rnd.uniform(-jitter, jitter), p[1] + rnd.uniform(-jitter, jitter), z))
        tmp = bmesh.new()
        bm_boulder(tmp, rnd, (0, 0, 0), rr, squash=(squash[0], squash[1], squash[2] * rnd.uniform(0.8, 1.25)), n=n, sink=0.22)
        bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(yaw + rnd.uniform(-0.3, 0.3), 3, "Z"))
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=q)
        _join(bm_by(), tmp)


def _join(bm, tmp):
    """Moves everything in tmp into bm (and frees tmp)."""
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def along_loop(pts, step):
    """Points every `step` along a closed loop of points."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    total = sum((pts[(i + 1) % n] - pts[i]).length for i in range(n))
    cnt = max(3, int(round(total / step)))
    out, want, acc = [], 0.0, 0.0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        seg = (b - a).length
        while want < acc + seg - 1e-6 and len(out) < cnt:
            out.append(a.lerp(b, (want - acc) / seg))
            want += total / cnt
        acc += seg
    return out


# ------------------------------------------------------------------------------------------- shells
WHORL = [(0.0, 0.0), (0.16, 0.10), (0.42, 0.165), (0.68, 0.185), (0.86, 0.11), (1.0, 0.0)]


class TurretShell:
    """A tall spiral sea shell (a turret shell): whorls winding up a cone, each one bulging between two seams.

        sh = TurretShell(base, height, r0, turns=6, k=0.78)     # k: each turn is this much smaller than the last
        sh.build(kit, "cream:0.05:0.9", {3: "team!:0.1:0.6"})    # rows of the whorl's profile that take another color
        sh.point(turn, u, out=0.0)                               # a point on the surface (turn 0..turns, u 0..1 up the whorl)

    The spiral starts `sunk` turns below `base` (so its foot is cut by the water) and leans by `lean` at its top."""

    def __init__(self, base, height, r0, turns=6.0, k=0.78, steps=12, profile=None, lean=(0.0, 0.0), th0=0.0, hand=1,
                 sunk=0.7, bulge=1.0):
        self.base, self.h, self.r0, self.turns, self.k = Vector(base), height, r0, turns, k
        self.steps, self.prof, self.lean, self.th0, self.hand, self.sunk, self.bulge = steps, profile or WHORL, lean, th0, hand, sunk, bulge
        self.s_end = k ** turns
        self.zs = height / (1.0 - k * self.s_end)

    def axis(self, z):
        t = min(max(z / self.h, 0.0), 1.2)
        return Vector((self.lean[0] * t ** 1.6, self.lean[1] * t ** 1.6, 0.0))

    def point(self, turn, u, out=0.0, b=None):
        """turn: how far up the spiral (in turns; below 0 is under the base); u: 0..1 up the whorl there."""
        s = self.k ** turn
        if b is None:                                   # the profile's bulge at u
            pr = self.prof
            b = 0.0
            for (u0, b0), (u1, b1) in zip(pr, pr[1:]):
                if u0 <= u <= u1:
                    b = b0 + (b1 - b0) * (u - u0) / max(u1 - u0, 1e-6)
        s2 = s * (1.0 - u * (1.0 - self.k))
        z = self.zs * (1.0 - s2)
        r = self.r0 * (s2 + b * s * self.bulge) + out
        a = self.th0 + self.hand * 2 * math.pi * turn
        return self.base + self.axis(z) + Vector((r * math.cos(a), r * math.sin(a), z))

    def normal(self, turn, u):
        a = self.th0 + self.hand * 2 * math.pi * turn
        return Vector((math.cos(a), math.sin(a), 0.25)).normalized()

    @property
    def apex(self):
        return self.base + self.axis(self.h) + Vector((0, 0, self.h))

    def build(self, kit, key, rows=None, tip=0.06):
        rows = rows or {}
        m = len(self.prof) - 1
        st = self.steps
        i0 = -int(round(self.sunk * st))
        n1 = int(round(self.turns * st))
        made = {}

        def vert(bm, i, j):
            if j == m and i + st <= n1:
                i, j = i + st, 0
            kk = (id(bm), i, j)
            if kk not in made:
                made[kk] = bm.verts.new(self.point(i / st, self.prof[j][0], b=self.prof[j][1]))
            return made[kk]
        for i in range(i0, n1):
            for j in range(m):
                bm = kit[rows.get(j, key)]
                q = (vert(bm, i, j), vert(bm, i + 1, j), vert(bm, i + 1, j + 1), vert(bm, i, j + 1))
                bm.faces.new(q if self.hand > 0 else tuple(reversed(q)))
        # the tip: the last turn's upper seam and the spiral's end, drawn up to a point
        bm = kit[key]
        loop = [self.point(i / st, 1.0, b=0.0) for i in range(n1 - st, n1 + 1)] + \
               [self.point(n1 / st, self.prof[j][0], b=self.prof[j][1]) for j in range(m - 1, 0, -1)]
        top = bm.verts.new(self.apex + Vector((0, 0, tip)))
        vs = [bm.verts.new(p) for p in loop]
        for a in range(len(vs)):
            b = (a + 1) % len(vs)
            f = (vs[a], vs[b], top)
            bm.faces.new(f if self.hand > 0 else tuple(reversed(f)))
        return self


def bm_scallop(bm, c, r=0.3, yaw=0.0, tilt=60.0, ribs=7, depth=0.22, th=0.035, spread=150.0):
    """A scallop shell standing on its hinge at c: a ribbed, domed fan whose outside faces along `yaw` (degrees,
    0 = +Y, clockwise seen from above); tilt 90 stands it upright, less leans it back. A closed, thick shell."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(-yaw), 4, "Z") @ Matrix.Rotation(math.radians(90.0 - tilt), 4, "X")
    n = ribs * 2
    tmp = bmesh.new()
    rows = []
    for side in (0, 1):                      # the ribbed outside, then the smooth inside
        row = []
        for i in range(n + 1):
            a = math.radians(-spread / 2 + spread * i / n)
            rr = r * (1.0 if i % 2 == 0 else 0.9) * (1.0 - 0.12 * abs(i - n / 2) / (n / 2))
            dome = depth * r * (1.0 - 0.7 * math.sin(a) ** 2)
            y = (dome if i % 2 == 0 else dome - th * 0.7) if side == 0 else dome - th * 1.7
            row.append(tmp.verts.new(c + (rz @ Vector((math.sin(a) * rr, y - depth * r, math.cos(a) * rr + 0.02)))))
        rows.append(row)
    hinge = [tmp.verts.new(c + (rz @ Vector((0, 0.03 - s * (th + 0.03), 0)))) for s in (0, 1)]
    for i in range(n):
        tmp.faces.new((hinge[0], rows[0][i], rows[0][i + 1]))
        tmp.faces.new((hinge[1], rows[1][i + 1], rows[1][i]))
        tmp.faces.new((rows[0][i + 1], rows[0][i], rows[1][i], rows[1][i + 1]))
    tmp.faces.new((hinge[0], hinge[1], rows[1][0], rows[0][0]))
    tmp.faces.new((hinge[1], hinge[0], rows[0][n], rows[1][n]))
    bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces[:])
    return _join(bm, tmp)


def bm_starfish(bm, c, r=0.2, yaw=0.0, normal=(0, 0, 1)):
    """A five-armed starfish lying on a surface at c."""
    c = Vector(c)
    q = Vector((0, 0, 1)).rotation_difference(Vector(normal).normalized())
    top = bm.verts.new(c + q @ Vector((0, 0, r * 0.22)))
    ring = []
    for k in range(10):
        a = math.radians(yaw + 36 * k)
        rr = r if k % 2 == 0 else r * 0.36
        ring.append(bm.verts.new(c + q @ Vector((math.cos(a) * rr, math.sin(a) * rr, r * (0.02 if k % 2 == 0 else 0.1)))))
    for k in range(10):
        bm.faces.new((ring[k], ring[(k + 1) % 10], top))
    return bm


# ------------------------------------------------------------------------------------------- coral, barnacles
def bm_coral(bm, rnd, base, h=0.6, r=0.06, up=(0, 0, 1), depth=3, n=5, spread=38.0, tips=None, knob=1.35, shrink=0.72):
    """A branching coral: a trunk that forks `depth` times into tapering, upturned branches with round knobs at
    their ends. tips: a list that collects the branch ends (for glows, or to hang things on)."""
    base = Vector(base)

    def branch(p, d, length, rad, level):
        d = d.normalized()
        x, y = _perp(d)
        bend = (x * rnd.uniform(-1, 1) + y * rnd.uniform(-1, 1)) * length * 0.1
        mid = p + d * length * 0.5 + bend
        end = p + d * length + Vector((0, 0, length * 0.08))
        bm_tube(bm, [p - d * rad * 0.5, mid, end], [rad, rad * 0.86, rad * 0.7], n=n, cap=True)
        if level >= depth:
            bm_ellipsoid(bm, tuple(end), (rad * knob * 0.7,) * 3, u=5, v=3)
            if tips is not None:
                tips.append(end)
            return
        forks = 2 if rnd.random() < 0.72 else 3
        a0 = rnd.uniform(0, 360)
        for f in range(forks):
            ax = rot_about(x, d, a0 + 360.0 * f / forks)
            nd = rot_about(d, ax, spread * rnd.uniform(0.75, 1.2))
            nd = (nd + Vector((0, 0, 0.35))).normalized()
            branch(end, nd, length * shrink * rnd.uniform(0.85, 1.1), rad * 0.72, level + 1)
    branch(base, Vector(up), h * 0.42, r, 1)
    return bm


def bm_tube_coral(bm, dark, rnd, base, n=5, h=(0.15, 0.4), r=(0.05, 0.085), spread=0.12):
    """A cluster of tube sponges: open pipes of different heights, flaring a little, dark inside."""
    base = Vector(base)
    for k in range(n):
        a = rnd.uniform(0, 6.283)
        d = 0.0 if k == 0 else rnd.uniform(0.6, 1.0) * spread
        p = base + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        hh = rnd.uniform(*h) * (1.0 if k else 1.15)
        rr = rnd.uniform(*r)
        lean = Vector((math.cos(a), math.sin(a), 0)) * (0.25 * hh if k else 0.0)
        top = p + lean + Vector((0, 0, hh))
        bm_tube(bm, [p - Vector((0, 0, 0.03)), p.lerp(top, 0.5), top], [rr * 0.8, rr * 0.9, rr * 1.15], n=6, cap=True)
        bm_cyl(dark, rr * 0.78, rr * 0.78, 0.012, tuple(top + Vector((0, 0, 0.004))), seg=6)
    return bm


def bm_barnacles(bm, dark, rnd, p, normal, n=4, r=0.045, spread=0.09):
    """A cluster of barnacles on a surface at p: little volcano cones with dark mouths."""
    p, nr = Vector(p), Vector(normal).normalized()
    x, y = _perp(nr)
    q = Vector((0, 0, 1)).rotation_difference(nr)
    rot = tuple(math.degrees(a) for a in q.to_euler())
    for k in range(n):
        a = rnd.uniform(0, 6.283)
        d = 0.0 if k == 0 else rnd.uniform(0.5, 1.0) * spread
        c = p + x * math.cos(a) * d + y * math.sin(a) * d
        rr = r * rnd.uniform(0.6, 1.0)
        bm_cyl(bm, rr, rr * 0.5, rr * 1.1, tuple(c + nr * rr * 0.35), rot=rot, seg=5)
        bm_cyl(dark, rr * 0.36, rr * 0.36, 0.01, tuple(c + nr * (rr * 0.9 + 0.003)), rot=rot, seg=5)
    return bm


# ------------------------------------------------------------------------------------------- kelp on bones
def kelp_bones(bones, name, base, h, segs=3, lean=(0.0, 0.0), parent="root"):
    """Adds a chain name.1 .. name.N going up from base (a frond `h` tall, leaning by `lean` at its top)."""
    base = Vector(base)
    prev = parent
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        p0 = base + Vector((lean[0] * t0 ** 1.5, lean[1] * t0 ** 1.5, h * t0))
        p1 = base + Vector((lean[0] * t1 ** 1.5, lean[1] * t1 ** 1.5, h * t1))
        bones["%s.%d" % (name, k + 1)] = (tuple(p0), tuple(p1), prev)
        prev = "%s.%d" % (name, k + 1)
    return bones


def kelp_part(name, col, rig, bone_name, rnd, base, h, segs=3, lean=(0.0, 0.0), fronds=3, w=0.16, swatch="teal:0.1:0.75",
              scale=1.0):
    """The kelp for kelp_bones(): a few wavy ribbon blades (`w` wide) from one foot, soft-skinned to the chain."""
    base = Vector(base)
    k = Kit()
    bm = k[swatch]
    for f in range(fronds):
        a = rnd.uniform(0, 6.283)
        hh = h * (1.0 if f == 0 else rnd.uniform(0.55, 0.9))
        off = Vector((math.cos(a), math.sin(a), 0)) * (0.0 if f == 0 else 0.07)
        pts, rad = [], []
        m = 6
        for i in range(m + 1):
            t = i / m
            wob = Vector((math.sin(t * 6.0 + a) * 0.05, math.cos(t * 5.0 + a * 1.7) * 0.05, 0)) * (0.3 + t)
            pts.append(base + off * (1 + t) + Vector((lean[0] * t ** 1.5, lean[1] * t ** 1.5, hh * t)) + wob)
            rad.append(w * 0.5 / (5.0 * 0.7071) * (0.45 + 0.55 * math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.7) if i < m else 0.0)
        bm_tube(bm, pts, rad, n=4, cap=True, up=(math.cos(a + 1.57), math.sin(a + 1.57), 0), squash=5.0, phase=0.5)
    return k.emit(name, col, rig=rig, bones=["%s.%d" % (bone_name, i + 1) for i in range(segs)], scale=scale)


def sway_kelp(rig, name, phase, amp=1.0, segs=3, push=(0.0, 0.0)):
    """Poses a kelp_bones() chain for one moment of its sway (phase 0..1 loops). push: an extra lean (degrees about
    X and Y), for a wave washing through."""
    pb = rig.pose.bones
    for k in range(segs):
        b = pb["%s.%d" % (name, k + 1)]
        ax = (4.0 + 3.5 * k) * amp * math.sin(2 * math.pi * (phase - 0.12 * k))
        ay = (3.0 + 2.5 * k) * amp * math.sin(2 * math.pi * (phase * 2 - 0.1 * k) + 1.3)
        b.rotation_quaternion = arm_space_quat(b, (1, 0, 0), ax + push[0] * (0.5 + 0.5 * k)) @ \
            arm_space_quat(b, (0, 1, 0), ay + push[1] * (0.5 + 0.5 * k))


# ------------------------------------------------------------------------------------------- ice
def bm_icicle(bm, top, length, r=0.05, n=5, lean=(0, 0)):
    """An icicle hanging from `top`."""
    top = Vector(top)
    bm_tube(bm, [top + Vector((0, 0, r * 0.4)), top + Vector((lean[0] * 0.4, lean[1] * 0.4, -length * 0.45)),
                 top + Vector((lean[0], lean[1], -length))], [r, r * 0.6, 0.0], n=n, cap=True)
    return bm


def bm_ice_cluster(bm, rnd, c, n=5, h=(0.25, 0.7), r=0.09, spread=0.16, up=(0, 0, 1), fan=28.0, sides=6):
    """A cluster of ice crystals growing from c: one tall in the middle, the rest leaning out round it."""
    c, upv = Vector(c), Vector(up).normalized()
    x, y = _perp(upv)
    for k in range(n):
        a = math.radians(360.0 * k / max(1, n - 1) + rnd.uniform(-15, 15))
        side = x * math.cos(a) + y * math.sin(a)
        if k == 0:
            d, hh, rr, base = upv, h[1], r, c
        else:
            d = rot_about(upv, side.cross(upv), fan * rnd.uniform(0.6, 1.3))
            hh, rr = rnd.uniform(h[0], h[1] * 0.75), r * rnd.uniform(0.55, 0.85)
            base = c + side * spread * rnd.uniform(0.6, 1.0)
        bm_crystal(bm, base - d * 0.05, base + d * hh, rr, n=sides, shoulder=rnd.uniform(0.6, 0.78), foot=0.7)
    return bm


def bm_floe(bm, rnd, c, r, z, th=0.05, n=None):
    """A flat slab of sea ice floating at z (its top): an irregular 5-7 sided plate, `th` thick."""
    c = Vector(c)
    n = n or rnd.choice((5, 6, 6, 7))
    a0 = rnd.uniform(0, 6.283)
    pts = [Vector((c.x + math.cos(a0 + 6.283 * i / n) * r * rnd.uniform(0.7, 1.1), c.y + math.sin(a0 + 6.283 * i / n) * r * rnd.uniform(0.7, 1.1), 0.0))
           for i in range(n)]
    return prism(bm, pts, z - th, z)


# ------------------------------------------------------------------------------------------- revolved shapes, waves
def bm_revolve(bm, prof, c=(0, 0, 0), seg=16, up=(0, 0, 1), cap0=True, cap1=True, phase=0.0):
    """A surface of revolution round the axis `up` through c: prof = [(radius, height along the axis), ...] in order
    along the surface (a bell: down the outside, round the lip, up the inside). A radius near 0 at an end makes a point."""
    c, upv = Vector(c), Vector(up).normalized()
    x, y = _perp(upv)
    rings, tip0, tip1 = [], None, None
    for i, (r, h) in enumerate(prof):
        p = c + upv * h
        if r < 1e-4 and i == 0:
            tip0 = p
        elif r < 1e-4 and i == len(prof) - 1:
            tip1 = p
        else:
            rings.append(oval(p, x, y, r, r, seg, phase=phase))
    return bm_loft(bm, rings, cap0=cap0, cap1=cap1, tip0=tip0, tip1=tip1)


# a breaking wave's profile (u: across, toward the curl; v: up), in heights: up the back, over the crest, the lip
# curling down and under, the hollow of the barrel, down the face to the foot
WAVE_PROF = [(-0.32, 0.0), (-0.32, 0.25), (-0.26, 0.55), (-0.13, 0.84), (0.1, 1.0), (0.36, 0.95), (0.54, 0.78), (0.58, 0.58),
             (0.46, 0.5), (0.44, 0.66), (0.33, 0.8), (0.13, 0.84), (-0.02, 0.7), (-0.05, 0.46), (0.07, 0.2), (0.3, 0.0)]


def bm_wave(bm, path, heights, outs, z, width=1.0):
    """A wave frozen mid-crash along `path` (x, y points on the water at height z): heights[i] tall at each, curling
    over toward outs[i] (a horizontal direction). The profile scales with the height, so the ends taper."""
    rings = []
    for p, h, o in zip(path, heights, outs):
        p = Vector((p[0], p[1], z))
        o = Vector((o[0], o[1], 0.0)).normalized()
        rings.append([p + o * (u * h * width) + Vector((0, 0, v * h)) for u, v in WAVE_PROF])
    return bm_loft(bm, rings, cap0=True, cap1=True)


def wave_arc(c, rx, ry, a0, a1, n=9, hmax=1.0, hmin=0.12, inward=False, bulge=0.75):
    """path, heights, outs for bm_wave along an elliptical arc round c (angles in degrees, a0 -> a1): tallest in the
    middle, tapering to hmin at the ends; curling outward from c (or inward)."""
    c = Vector(c)
    path, hs, outs = [], [], []
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(a0 + (a1 - a0) * t)
        path.append((c.x + rx * math.cos(a), c.y + ry * math.sin(a)))
        hs.append(max(hmin * hmax, hmax * math.sin(math.pi * t) ** bulge))
        o = Vector((math.cos(a) * ry, math.sin(a) * rx)).normalized()
        outs.append((-o.x, -o.y) if inward else (o.x, o.y))
    return path, hs, outs


def keyed(keys, f):
    """A value at frame f from [(frame, value), ...], eased (smoothstep) between neighbours."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            return v0 + (v1 - v0) * smooth((f - f0) / max(f1 - f0, 1e-6))
    return keys[-1][1]
