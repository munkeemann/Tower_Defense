"""Shared by the small Verdant towers built together (Thornspitter, Moonwell, Spore Mound): curves, leaves and
flowers, skinning along a chain, parts on many bones in one mesh, and motes that rise and fade.

Exec after kk_helpers.py:
    exec(open(os.path.join(REPO, "tools", "blender", "wildwood_common.py"), encoding="utf-8").read())
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler


def spline(keys, s):
    """A smooth curve through [(s, value), ...] (Catmull-Rom); values are numbers or Vectors."""
    n = len(keys)
    if s <= keys[0][0]:
        return keys[0][1]
    if s >= keys[-1][0]:
        return keys[-1][1]
    for i in range(n - 1):
        s0, s1 = keys[i][0], keys[i + 1][0]
        if s <= s1:
            t = (s - s0) / (s1 - s0)
            p0, p1, p2, p3 = keys[max(i - 1, 0)][1], keys[i][1], keys[i + 1][1], keys[min(i + 2, n - 1)][1]
            return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)


def ramp(keys, s):
    """Straight lines through [(s, value), ...]."""
    if s <= keys[0][0]:
        return keys[0][1]
    for (s0, v0), (s1, v1) in zip(keys, keys[1:]):
        if s <= s1:
            return v0 + (v1 - v0) * ((s - s0) / (s1 - s0))
    return keys[-1][1]


def hex_r(a, inset=0.0):
    """How far a hex reaches from its middle in direction a (radians), `inset` in from its edge."""
    d = (math.degrees(a) % 60.0) - 30.0
    return (HEX_R * math.cos(math.radians(30)) - inset) / math.cos(math.radians(d))


def rot_deg(d, axis="Z"):
    """Euler degrees (for bm_cyl / bm_box / bm_ellipsoid's rot) that turn local `axis` to point along d."""
    return tuple(math.degrees(x) for x in Vector(d).to_track_quat(axis, "Y").to_euler())


def bm_hull(bm, pts):
    """A convex block through pts (its own island, faces outward)."""
    vs = [bm.verts.new(Vector(p)) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = [e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def leaf(bm, pts, width, th=0.022, n=6, up=(0, 0, 1)):
    """A broad leaf along pts (3 to 6 points): a flattened tube, widest a third of the way, drawn to a point."""
    m = len(pts)
    prof = {3: [0.5, 1.0, 0.0], 4: [0.5, 1.0, 0.7, 0.0], 5: [0.5, 0.95, 1.0, 0.6, 0.0], 6: [0.45, 0.85, 1.0, 0.8, 0.45, 0.0]}[m]
    return bm_tube(bm, pts, [th * p for p in prof], n=n, squash=width * 0.5 / th, up=up)


def bm_star(bm, c, axis, r, r_in=0.45, h=0.3, points=5, turn=0.0):
    """A little star-shaped blossom at c facing along `axis`: `points` petals of radius r, dished toward the middle."""
    c, ax = Vector(c), Vector(axis).normalized()
    x = ax.cross(Vector((0, 0, 1)))
    if x.length < 1e-3:
        x = Vector((1, 0, 0))
    x.normalize()
    y = ax.cross(x)
    rim = []
    for i in range(points * 2):
        a = turn + math.pi * i / points
        rr = r if i % 2 == 0 else r * r_in
        rim.append(bm.verts.new(c + (x * math.cos(a) + y * math.sin(a)) * rr + ax * (r * h if i % 2 == 0 else 0.0)))
    top, bot = bm.verts.new(c + ax * r * 0.08), bm.verts.new(c - ax * r * 0.3)
    m = len(rim)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((top, rim[i], rim[j]))
        bm.faces.new((bot, rim[j], rim[i]))
    return bm


def skin_chain(o, rig, bones, tops, blend=0.1, axis=2):
    """Skins o to a chain of bones by height (or along another axis): bone k up to tops[k], blending across each joint."""
    o.parent = rig
    o.parent_type = "OBJECT"
    o.matrix_parent_inverse = Matrix.Identity(4)
    for m in [m for m in o.modifiers if m.type == "ARMATURE"]:
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    groups = [o.vertex_groups.new(name=b) for b in bones]
    for v in o.data.vertices:
        z = v.co[axis]
        kk = 0
        while kk < len(tops) and z > tops[kk]:
            kk += 1
        w = [0.0] * len(bones)
        w[kk] = 1.0
        for j, zt in enumerate(tops):
            if abs(z - zt) < blend:
                m = 0.5 + (z - zt) / (2 * blend)
                w = [0.0] * len(bones)
                w[j], w[j + 1] = 1.0 - m, m
        for g, wt in zip(groups, w):
            if wt > 0.01:
                g.add([v.index], wt, "REPLACE")
    mod = o.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return o


class BoneKit(Kit):
    """A Kit whose geometry rides on several bones, in one mesh per color (a ruff of petals, a swarm of motes):

        k = BoneKit()
        k.bone("petal.0"); bm_tube(k["team!"], ...)       # everything added from here on follows petal.0
        k.bone("petal.1"); ...
        k.emit_bones("Head_Petals", col, rig)
    """

    def __init__(self):
        Kit.__init__(self)
        self.marks, self.cur, self.at = {}, None, {}

    def _close(self):
        if self.cur is None:
            return
        for key, bm in self.parts.items():
            v0 = self.at.get(key, 0)
            if len(bm.verts) > v0:
                self.marks.setdefault(key, []).append((self.cur, v0, len(bm.verts)))

    def bone(self, name):
        self._close()
        self.cur = name
        self.at = {key: len(bm.verts) for key, bm in self.parts.items()}

    def transform(self, m):
        for bm in self.parts.values():
            bmesh.ops.transform(bm, matrix=m, verts=bm.verts)

    def emit_bones(self, name, col, rig, **kw):
        self._close()
        keys = [key for key, bm in self.parts.items() if bm.verts]
        marks = self.marks
        objs = Kit.emit(self, name, col, rig=rig, bone="root", **kw)
        for o, key in zip(objs, keys):
            o.vertex_groups.clear()
            for bone, v0, v1 in marks.get(key, []):
                g = o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone)
                g.add(list(range(v0, v1)), 1.0, "REPLACE")
        self.marks, self.cur, self.at = {}, None, {}
        return objs


def kit_transform(kit, m):
    """Moves everything gathered in a Kit so far (parts laid out in a space of their own)."""
    for bm in kit.parts.values():
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)


def mote_pose(pb, name, t, start, rise, r0, r1, turns, a0, size=1.0):
    """Poses a mote's bone at moment t (0..1) of its climb: up a widening or narrowing spiral from `start`, swelling
    out of nothing and fading back to nothing at the top (so the jump back down can't be seen)."""
    b = pb[name]
    t = t % 1.0
    a = a0 + 2 * math.pi * turns * t
    r = r0 + (r1 - r0) * t
    home = Vector(b.bone.head_local)
    p = Vector(start) + Vector((math.cos(a) * r, math.sin(a) * r, rise * t))
    b.location = arm_space_loc(b, tuple(p - home))
    s = max(0.001, math.sin(math.pi * t) ** 0.7) * size
    b.scale = (s, s, s)
