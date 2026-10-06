"""Shared by the big creature towers (mammoth, fat_dragon, magma_golem, hive): egg-shaped body sections for lofts,
points on a lofted body's surface (so cloth, fringes, scutes and plates can hug it), plated shells with something
glowing in the joints, low ground patches, hipped roofs, and pose shorthands.

Exec after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "megabeast_common.py"), encoding="utf-8").read())

A body runs along +Y. A section is (y, zc, rx, up, dn, pinch): an oval round (0, y, zc), rx half wide, `up` tall
above the middle and `dn` below it, the upper half narrowed by `pinch` (a ridge back, a hump). Angles go from the
creature's right side (0 degrees, +X) over the top (90) to its left (180); the belly is 270 / -90.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion


def sec_point(sec, a, grow=0.0, power=2.3):
    """The point at angle a (radians) on a section, pushed `grow` out of its surface."""
    y, zc, rx, up, dn, pinch = sec
    e = 2.0 / power
    ca, sa = math.cos(a), math.sin(a)
    cx = math.copysign(abs(ca) ** e, ca)
    sz = math.copysign(abs(sa) ** e, sa)
    w = (rx + grow) * (1.0 - pinch * max(0.0, sz))
    return Vector((cx * w, y, zc + sz * ((up if sz > 0 else dn) + grow)))


def sec_ring(sec, n=10, grow=0.0, power=2.3, phase=0.5):
    """A section's outline: n points, counterclockwise seen from the front."""
    return [sec_point(sec, 2 * math.pi * (i + phase) / n, grow, power) for i in range(n)]


def sec_at(secs, y):
    """The section at spine position y, between the rows of `secs`."""
    if y <= secs[0][0]:
        return (y,) + tuple(secs[0][1:])
    for a, b in zip(secs, secs[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / max(b[0] - a[0], 1e-9)
            return (y,) + tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 6))
    return (y,) + tuple(secs[-1][1:])


def sec_arc(secs, y, a0, a1, grow=0.0, n=8, power=2.3):
    """n + 1 points over a body from angle a0 to a1 (degrees) at spine position y, `grow` off its surface."""
    s = sec_at(secs, y)
    return [sec_point(s, math.radians(a0 + (a1 - a0) * i / n), grow, power) for i in range(n + 1)]


def surf(secs, y, a, grow=0.0, power=2.3):
    """A point on a body's surface (a in degrees), and the direction straight out of it there."""
    s = sec_at(secs, y)
    p = sec_point(s, math.radians(a), grow, power)
    q = sec_point(s, math.radians(a), grow + 0.1, power)
    return p, (q - p).normalized()


def bm_drape(bm, secs, ys, a0, a1, th=0.03, n=8, power=2.3, sink=0.012):
    """Cloth (or a band of scutes, a strap) lying over a lofted body from angle a0 to a1, along the spine positions
    ys, `th` thick: a closed shell that starts a hair under the surface."""
    rings = []
    for y in ys:
        rings.append(sec_arc(secs, y, a0, a1, th, n, power) + list(reversed(sec_arc(secs, y, a0, a1, -sink, n, power))))
    return bm_loft(bm, rings)


def bm_lock(bm, base, tip, w, th, out):
    """A lock of hair, a leaf, a scale: a slab from `base` narrowing to a point at `tip`, w wide, th thick along
    `out` (the way its flat side faces)."""
    return bm_beam(bm, base, tip, w, th, w1=w * 0.2, h1=th * 0.35, up=out)


def bm_patch(bm, rnd, c, r, z0, z1, n=10, jitter=0.12, squash=1.0, rot=0.0, keep=None):
    """A low irregular slab (trampled earth, a puddle of honey, a crust of cooled lava): an n-gon about r across round
    c = (x, y), from z0 to z1. keep(x, y) -> False pulls a corner back toward c until it's True (stay on the hexes)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rot
        k = r * (1.0 + rnd.uniform(-jitter, jitter))
        for _ in range(12):
            x, y = c[0] + math.cos(a) * k, c[1] + math.sin(a) * k * squash
            if keep is None or keep(x, y):
                break
            k *= 0.9
        pts.append(Vector((x, y, 0)))
    return prism(bm, pts, z0, z1)


def bm_frustum(bm, c, hx, hy, z0, z1, top=0.0):
    """A hipped roof or a battered block: a rectangle 2 hx by 2 hy round c = (x, y) at z0, drawn in to `top` of its
    size at z1 (0: a point)."""
    cs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    lo = [bm.verts.new((c[0] + sx * hx, c[1] + sy * hy, z0)) for sx, sy in cs]
    bm.faces.new(list(reversed(lo)))
    if top <= 1e-4:
        ap = bm.verts.new((c[0], c[1], z1))
        for i in range(4):
            bm.faces.new((lo[i], lo[(i + 1) % 4], ap))
    else:
        hi = [bm.verts.new((c[0] + sx * hx * top, c[1] + sy * hy * top, z1)) for sx, sy in cs]
        bm.faces.new(hi)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def bm_plates(bm, rnd, rings, gap=0.03, th=(0.05, 0.1), skip=0.0, lift=0.004, chamfer=0.3, keep=None):
    """Armor plates / hewn blocks over a loft: every quad between the rings becomes a block standing proud of it
    (`th`: thickness range), `gap` apart, so what's lofted underneath (glowing magma, a pale hide) shows in the
    joints. skip: the share of blocks left out; keep(band, i) -> False leaves that one out (an opening)."""
    n = len(rings[0])
    mids = [sum((Vector(p) for p in r), Vector()) / n for r in rings]
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            quad = [Vector(rings[k][i]), Vector(rings[k][j]), Vector(rings[k + 1][j]), Vector(rings[k + 1][i])]
            c = sum(quad, Vector()) / 4
            nrm = (quad[1] - quad[0]).cross(quad[3] - quad[0]) + (quad[2] - quad[1]).cross(quad[0] - quad[1])
            if nrm.length < 1e-9 or rnd.random() < skip or (keep is not None and not keep(k, i)):
                continue
            nrm.normalize()
            if nrm.dot(c - (mids[k] + mids[k + 1]) * 0.5) < 0:
                nrm = -nrm
            t = rnd.uniform(*th)
            inner, outer = [], []
            for p in quad:
                d = c - p
                L = max(d.length, 1e-6)
                q = p + d * min(0.4, gap * 0.75 / L)
                inner.append(q + nrm * lift)
                outer.append(q + d / L * min(L * chamfer, t * 0.6) + nrm * t)
            vs = [bm.verts.new(p) for p in inner] + [bm.verts.new(p) for p in outer]
            fs = [bm.faces.new(list(reversed(vs[:4]))), bm.faces.new(vs[4:])]
            for a in range(4):
                b = (a + 1) % 4
                fs.append(bm.faces.new((vs[a], vs[b], vs[4 + b], vs[4 + a])))
            bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def tube_rings(pts, radii, n=6, up=(0, 0, 1), squash=1.0, phase=0.0):
    """The rings bm_tube() would make through pts, as points (to plate a limb with bm_plates)."""
    tmp = bmesh.new()
    vr = bm_tube(tmp, pts, radii, n=n, cap=False, up=up, squash=squash, phase=phase)
    out = [[v.co.copy() for v in r] for r in vr]
    tmp.free()
    return out


def track(f, keys):
    """A value at frame f from keys [(frame, value), ...], easing in and out between them."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * smooth((f - f0) / max(f1 - f0, 1e-9))
    return keys[-1][1]


def poly_at(pts, t):
    """The point `t` (0..1) of the way along a polyline, by length."""
    pts = [Vector(p) for p in pts]
    ls = [(b - a).length for a, b in zip(pts, pts[1:])]
    d = t * sum(ls)
    for a, b, l in zip(pts, pts[1:], ls):
        if d <= l or b is pts[-1]:
            return a.lerp(b, min(max(d / max(l, 1e-9), 0.0), 1.0))
        d -= l
    return pts[-1].copy()


def lerp_list(vals, t):
    """A value `t` (0..1) of the way along a list of numbers (the radii that go with poly_at)."""
    x = t * (len(vals) - 1)
    i = min(int(x), len(vals) - 2)
    return vals[i] + (vals[i + 1] - vals[i]) * (x - i)


# ---- posing
def turn(pb, name, x=0.0, y=0.0, z=0.0):
    """Sets a bone's pose rotation: degrees about the armature's Z, then X, then Y axes (as its parent carries them)."""
    b = pb[name]
    b.rotation_quaternion = arm_space_quat(b, (0, 0, 1), z) @ arm_space_quat(b, (1, 0, 0), x) @ arm_space_quat(b, (0, 1, 0), y)


def shift(pb, name, d):
    """Moves a bone by d = (x, y, z) in the armature's axes."""
    pb[name].location = arm_space_loc(pb[name], d)


def scale_arm(pb, name, s):
    """Scales a bone by s = (x, y, z) along the armature's axes (for a bone lying along one of them, near enough)."""
    m = pb[name].bone.matrix_local.to_3x3()
    out = []
    for i in range(3):
        ax = [abs(m[j][i]) for j in range(3)]           # the bone's own axis i, in the armature's space
        out.append(sum(ax[j] * s[j] for j in range(3)) / max(sum(ax), 1e-6))
    pb[name].scale = out


def bump(f, c, w):
    """A smooth bump: 1 at f = c, 0 at w away or more."""
    return max(0.0, 1.0 - ((f - c) / w) ** 2) ** 2
