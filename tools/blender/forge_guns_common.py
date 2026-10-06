"""Shared pieces of the Deep Forge's guns (the Flak Battery and the Doomsday Cannon): dwarven ordnance of dark iron
with brass and gold bands, riveted plate, heavy stone blocks, thick timber and a furnace-orange glow.

Exec'd by a tower script after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "forge_guns_common.py"), encoding="utf-8").read())
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

FURNACE = "glow:1.0,0.45,0.1,0.9"           # the furnace-orange glow
FLARE = "glow:1.0,0.74,0.3,1.1"             # muzzle flashes


def frame3(d, up=(0, 0, 1)):
    """Three unit vectors (x, y, z): y along d, z as near `up` as it can be (as bm_beam picks them)."""
    y = Vector(d).normalized()
    u = Vector(up).normalized()
    if abs(y.dot(u)) > 0.99:
        u = Vector((1, 0, 0)) if abs(y.x) < 0.9 else Vector((0, 1, 0))
    x = y.cross(u).normalized()
    return x, y, x.cross(y).normalized()


def rod(bm, p0, p1, r0, r1=None, n=8):
    """A round bar from p0 to p1 (radius r0, r1 at p1): pins, axles, pipes, barrels."""
    return bm_tube(bm, [Vector(p0), Vector(p1)], [r0, r0 if r1 is None else r1], n=n)


def rivets(bm, pts, normal, r=0.022, n=4):
    """A domed rivet head at each point, standing out along `normal` (a vector, or a function of the point)."""
    for p in pts:
        p = Vector(p)
        nr = Vector(normal(p) if callable(normal) else normal).normalized()
        bm_tube(bm, [p - nr * 0.006, p + nr * r * 0.55], [r, r * 0.5], n=n)
    return bm


def row(p0, p1, n):
    """n points evenly spaced along p0 -> p1 (half a step in from each end)."""
    p0, p1 = Vector(p0), Vector(p1)
    return [p0.lerp(p1, (i + 0.5) / n) for i in range(n)]


def arc_pts(c, r, z, a0, a1, n):
    """n points on a level arc round c, from a0 to a1 degrees (both ends included)."""
    c = Vector(c)
    out = []
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / max(n - 1, 1))
        out.append(Vector((c.x + r * math.cos(a), c.y + r * math.sin(a), z)))
    return out


def slab(bm, pts, th, out):
    """A plate: the flat polygon pts (its outer face) thickened by th away from `out` (a direction to the outside)."""
    pts = [Vector(p) for p in pts]
    n = Vector()
    for i in range(len(pts)):
        n += pts[i].cross(pts[(i + 1) % len(pts)])
    n.normalize()
    if n.dot(Vector(out)) < 0:
        n = -n
    top = [bm.verts.new(p) for p in pts]
    bot = [bm.verts.new(p - n * th) for p in pts]
    m = len(pts)
    fs = [bm.faces.new(top), bm.faces.new(list(reversed(bot)))]
    for i in range(m):
        j = (i + 1) % m
        fs.append(bm.faces.new((top[j], top[i], bot[i], bot[j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def box_on(bm, size, c, x_dir, rot_extra=(0, 0, 0)):
    """bm_box turned so its local X runs along the level direction x_dir."""
    yaw = math.degrees(math.atan2(x_dir[1], x_dir[0]))
    return bm_box(bm, size, tuple(c), (rot_extra[0], rot_extra[1], yaw + rot_extra[2]))


def gear_ring(bm, c, r, z0, z1, teeth, depth=0.07, r_in=None, width=None):
    """A toothed ring lying flat round c: a band from r_in to r, with `teeth` square teeth standing out `depth`."""
    c = Vector(c)
    r_in = r - 0.12 if r_in is None else r_in
    tmp = bmesh.new()
    ring(tmp, (c.x, c.y, 0), r, r_in, z0, z1, seg=max(16, teeth))
    w = width or (2 * math.pi * r / teeth) * 0.5
    for i in range(teeth):
        a = 360.0 * (i + 0.5) / teeth
        rr = r + depth * 0.5 - 0.01
        bm_box(tmp, (depth, w, (z1 - z0) * 0.86), (c.x + rr * math.cos(math.radians(a)), c.y + rr * math.sin(math.radians(a)),
                                                  (z0 + z1) * 0.5), (0, 0, a))
    _merge(bm, tmp)
    return bm


def _merge(bm, tmp):
    """Moves everything in tmp into bm (and frees tmp)."""
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def bm_shell(case, nose, base, d, r, length, band=None, n=8, rim=False):
    """A shell from `base` along d: a rimmed brass case (into `case`), an ogive nose (into `nose`) and a copper
    driving band (into `band`, if given)."""
    base, d = Vector(base), Vector(d).normalized()
    L = length
    if rim:
        bm_tube(case, [base, base + d * (L * 0.06)], [r * 1.1, r * 1.1], n=n)
    bm_tube(case, [base + d * (L * (0.05 if rim else 0.0)), base + d * (L * 0.5)], [r, r], n=n)
    bm_tube(nose, [base + d * (L * 0.49), base + d * (L * 0.66), base + d * (L * 0.84), base + d * L],
            [r * 0.97, r * 0.9, r * 0.58, 0.0], n=n)
    if band is not None:
        bm_tube(band, [base + d * (L * 0.43), base + d * (L * 0.5)], r * 1.05, n=n)
    return case


def bm_keg(wood, hoop, c, r, h, axis=(0, 0, 1), n=8):
    """A keg from c along `axis` (standing, or lying): bulging staves and two iron hoops."""
    c, ax = Vector(c), Vector(axis).normalized()
    bm_tube(wood, [c, c + ax * (h * 0.5), c + ax * h], [r * 0.84, r, r * 0.84], n=n)
    for u in (0.17, 0.83):
        rr = r * (0.84 + 0.16 * math.sin(math.pi * u)) + 0.012
        bm_tube(hoop, [c + ax * (h * u - 0.025), c + ax * (h * u + 0.025)], [rr, rr], n=n)
    return wood


def bm_wheel(rim, spokes, hub, c, axis, r, w, n_spokes=8, seg=14, tyre=None):
    """A spoked wheel round c turning on `axis`: felloes (rim blocks, into `rim`), spokes, a hub; an iron tyre
    round it (into `tyre`, if given)."""
    c, ax = Vector(c), Vector(axis).normalized()
    x, _, z = frame3(ax)
    rd = r * 0.17

    def block(bm, r0, r1, a0, a1, wd):
        vs = []
        for s in (-0.5, 0.5):
            for rr, a in ((r0, a0), (r1, a0), (r1, a1), (r0, a1)):
                vs.append(bm.verts.new(c + ax * (wd * s) + x * (rr * math.cos(a)) + z * (rr * math.sin(a))))
        lo, hi = vs[:4], vs[4:]
        fs = [bm.faces.new(lo), bm.faces.new(list(reversed(hi)))]
        for k in range(4):
            j = (k + 1) % 4
            fs.append(bm.faces.new((lo[k], lo[j], hi[j], hi[k])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg + 0.01, 2 * math.pi * (i + 1) / seg - 0.01
        block(rim, r - rd, r - (0.025 if tyre is not None else 0.0), a0, a1, w)
        if tyre is not None:
            block(tyre, r - 0.03, r, a0 - 0.01, a1 + 0.01, w * 1.04)
    for i in range(n_spokes):
        a = 2 * math.pi * (i + 0.5) / n_spokes
        dv = x * math.cos(a) + z * math.sin(a)
        bm_beam(spokes, c + dv * (r * 0.16), c + dv * (r - rd * 0.6), w * 0.42, w * 0.3, up=tuple(ax))
    rod(hub, c - ax * (w * 0.75), c + ax * (w * 0.75), r * 0.2, r * 0.17, n=8)
    return rim


def ease(keys, f):
    """A value at frame f from [(frame, value), ...], eased (smoothstep) between neighbours."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            return v0 + (v1 - v0) * smooth((f - f0) / max(f1 - f0, 1e-6))
    return keys[-1][1]
