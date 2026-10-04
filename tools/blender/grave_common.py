"""The Grave towers' shared pieces: a low-poly skull, skeletal arms with clawing hands, a dirt mound with a dark grave
hole, and soul flames. Exec'd by a tower script after kk_helpers.py.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

BONE_SW = "cream"
EARTH_SW = "wood_dark"
NECRO = (0.55, 0.95, 0.35)
SOUL = (0.7, 0.42, 1.0)


def bm_skull(bone_bm, dark_bm, c, s=0.18, yaw=0.0):
    """A skull at c (s tall), facing yaw (degrees from +Y): cranium, cheekbones and jaw on bone_bm, eye holes and nose
    on dark_bm. Returns the two eye-socket centres (for glowing eyes)."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    bm_ellipsoid(bone_bm, tuple(c + Vector((0, 0, s * 0.1))), (s * 0.5, s * 0.55, s * 0.48), rot=(0, 0, yaw), u=9, v=6)
    bm_ellipsoid(bone_bm, tuple(c + rz @ Vector((0, s * 0.18, -s * 0.28))), (s * 0.34, s * 0.3, s * 0.18), rot=(0, 0, yaw), u=8, v=4)
    eyes = []
    for sx in (-1, 1):
        e = c + rz @ Vector((sx * s * 0.2, s * 0.45, s * 0.05))
        bm_ellipsoid(dark_bm, tuple(e), (s * 0.13, s * 0.06, s * 0.12), rot=(0, 0, yaw), u=6, v=4)
        eyes.append(e + rz @ Vector((0, s * 0.03, 0)))
    bm_ellipsoid(dark_bm, tuple(c + rz @ Vector((0, s * 0.5, -s * 0.12))), (s * 0.06, s * 0.04, s * 0.07), rot=(0, 0, yaw), u=5, v=3)
    return eyes


def bm_hand(bm, wrist, d, side, s=0.14, curl=0.0):
    """A skeletal hand at wrist, reaching along d: a palm and four bony fingers (and a thumb) curled by `curl` (0..1)."""
    wrist, d = Vector(wrist), Vector(d).normalized()
    side = Vector(side).normalized()
    nrm = d.cross(side).normalized()
    palm = wrist + d * s * 0.45
    bm_ellipsoid(bm, tuple(palm), (s * 0.3, s * 0.3, s * 0.3), u=6, v=4)
    for k in range(4):
        base = palm + d * s * 0.3 + side * s * (k - 1.5) * 0.17
        mid = base + (d * (1 - curl * 0.5) + nrm * curl * 0.6).normalized() * s * 0.38
        tip = mid + (d * (1 - curl) + nrm * curl).normalized() * s * 0.3
        bm_beam(bm, base, mid, s * 0.09, s * 0.09)
        bm_beam(bm, mid, tip, s * 0.08, s * 0.08, w1=s * 0.03, h1=s * 0.03)
    th = palm + side * s * 0.32
    bm_beam(bm, th, th + (side * 0.6 + d * 0.8).normalized() * s * 0.35, s * 0.09, s * 0.09, w1=s * 0.04, h1=s * 0.04)
    return bm


def bm_grave_hole(earth_bm, dark_bm, c, w=0.55, l=0.9, yaw=0.0, rnd=None):
    """A freshly dug grave: a heaped dirt rim round a dark hole, w x l, turned by yaw."""
    rnd = rnd or random.Random(1)
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    for k in range(10):
        a = math.radians(36 * k)
        p = c + rz @ Vector((math.cos(a) * w * 0.55, math.sin(a) * l * 0.55, 0))
        r = rnd.uniform(0.12, 0.18)
        bm_ellipsoid(earth_bm, tuple(p + Vector((0, 0, r * 0.3))), (r * 1.3, r * 1.1, r * 0.7), rot=(0, 0, yaw + 36 * k), u=6, v=4)
    bm_ellipsoid(dark_bm, tuple(c + Vector((0, 0, 0.02))), (w * 0.48, l * 0.48, 0.03), rot=(0, 0, yaw), u=10, v=4)
    return c


def bm_flame(bm, c, h=0.4, r=0.13, n=5, rnd=None):
    """A soul flame: a cluster of tongues licking up from c."""
    rnd = rnd or random.Random(2)
    c = Vector(c)
    bm_cyl(bm, r, 0.0, h, tuple(c + Vector((0, 0, h / 2))), seg=6)
    for k in range(n):
        a = math.radians(360 * k / n + rnd.uniform(-20, 20))
        p = c + Vector((math.cos(a) * r * 0.7, math.sin(a) * r * 0.7, 0))
        hh = h * rnd.uniform(0.45, 0.75)
        bm_cyl(bm, r * 0.55, 0.0, hh, tuple(p + Vector((0, 0, hh / 2))), rot=(math.cos(a) * 10, math.sin(a) * -10, 0), seg=5)
    return bm
