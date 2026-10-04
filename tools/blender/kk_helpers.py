"""Helpers for building Tower Realms towers in Blender out of KayKit pieces plus our own geometry.

Run inside Blender (the MCP for Blender connector, or the Text Editor):
    exec(open(r"<repo>/tools/blender/kk_helpers.py").read())

Conventions (they match the game, see scripts/hex.gd and GameData.SHAPES):
- 1 Blender unit = 1 Godot unit. Blender +Y is the tower's front (Godot -Z), Z is up, the ground top is z = 0.
- The tower root sits on the footprint's centroid; cells come from GameData.SHAPES (axial q, s).
- Our own geometry is UV-mapped into the KayKit hex-pack atlas (hexagons_medieval.png, 8 x 4 gradient swatches),
  so it shares the pack's colors. Team-colored faces use the material "kk_team": the game slides its UVs across
  the team row (blue, red, yellow, green) for your color.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler, Quaternion

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) if "__file__" in globals() \
    else r"C:\Users\maxja\Vibe code\tower-realms"
KK = os.path.join(REPO, "assets", "kaykit")
ATLAS = os.path.join(KK, "hex", "hexagons_medieval.png")

HEX_R = 1.2
SQ3 = math.sqrt(3.0)

# Atlas swatches (column, row), row 0 at the top of the image. Each is a vertical gradient, light at the top.
SW = {
    "black": (0, 0), "white": (1, 0), "stone": (2, 0), "stone_dark": (3, 0), "iron": (4, 0), "roof": (5, 0),
    "wood": (6, 0), "ember": (7, 0),
    "sky": (0, 1), "blue": (1, 1), "wood_red": (2, 1), "gold": (3, 1), "grass": (4, 1), "sand": (5, 1),
    "stone_warm": (6, 1), "wood_dark": (7, 1),
    "lime": (0, 2), "teal": (1, 2), "stone2": (2, 2), "tan": (3, 2), "cream": (5, 2), "red": (6, 2), "salmon": (7, 2),
    "team": (0, 3), "orange": (4, 3), "beige": (5, 3), "taupe": (6, 3), "taupe_dark": (7, 3),
}


def hex_to_world(q, s, mid=(0.0, 0.0)):
    """Cell (q, s) -> Blender (x, y), relative to a footprint middle given in Godot (x, z)."""
    gx = 1.5 * HEX_R * q
    gz = SQ3 * HEX_R * (s + q * 0.5)
    return Vector((gx - mid[0], -(gz - mid[1]), 0.0))


def footprint_mid(cells):
    xs = [1.5 * HEX_R * q for q, s in cells]
    zs = [SQ3 * HEX_R * (s + q * 0.5) for q, s in cells]
    return (sum(xs) / len(xs), sum(zs) / len(zs))


def hex_corners(center, r=HEX_R):
    """Flat-top hexagon corners, corner i at 60*i degrees (counterclockwise seen from above)."""
    return [Vector((center.x + r * math.cos(math.radians(60 * i)), center.y + r * math.sin(math.radians(60 * i)), 0))
            for i in range(6)]


def outline(cells, inset=0.0):
    """The outline (counterclockwise, seen from above) of the union of a footprint's hexes, pulled in by `inset`."""
    mid = footprint_mid(cells)
    edges = {}
    key = lambda v: (round(v.x, 4), round(v.y, 4))
    for q, s in cells:
        cs = hex_corners(hex_to_world(q, s, mid))
        for i in range(6):
            a, b = key(cs[i]), key(cs[(i + 1) % 6])
            if (b, a) in edges:
                del edges[(b, a)]     # shared edge between two hexes: inside the union
            else:
                edges[(a, b)] = True
    nxt = {a: b for a, b in edges}
    start = min(nxt)
    loop = [start]
    while True:
        n = nxt[loop[-1]]
        if n == start:
            break
        loop.append(n)
    pts = [Vector((x, y, 0)) for x, y in loop]
    if inset == 0.0:
        return pts
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d0 = (p1 - p0).normalized()
        d1 = (p2 - p1).normalized()
        n0 = Vector((-d0.y, d0.x, 0))   # inward normal of a counterclockwise loop
        n1 = Vector((-d1.y, d1.x, 0))
        bis = (n0 + n1)
        bis = bis / max(bis.length, 1e-6)
        out.append(p1 + bis * (inset / max(bis.dot(n0), 0.2)))
    return out


# ------------------------------------------------------------------------------------------- materials
def atlas_image():
    for im in bpy.data.images:
        if os.path.normcase(bpy.path.abspath(im.filepath)) == os.path.normcase(ATLAS):
            return im
    return bpy.data.images.load(ATLAS, check_existing=True)


def _atlas_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = atlas_image()
    tex.location = (-400, 200)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Metallic"].default_value = 0.0
    return m


def mat_kk():
    """The hex-pack atlas material, shared with every imported hex-pack piece."""
    return _atlas_mat("hexagons_medieval")


def mat_team():
    """Atlas material for team-colored faces (UVs in the blue team swatch; the game shifts them to your color)."""
    return _atlas_mat("kk_team")


def mat_ground():
    """Atlas material for the hexes under a tower. The game gives these faces the map tiles' own material (the biome's
    palette), so a tower's ground always matches the map around it."""
    return _atlas_mat("kk_ground")


# Where the pack's hex tiles sample their ground swatch ("lime", the one the biome palettes recolour): the light band
# on top, a darker band down the sides, darker still at the foot.
GROUND_TOP = 0.32
GROUND_SIDE = (0.64, 0.72)
GROUND_FOOT = (0.72, 0.86)


def paint_ground(obj, side=GROUND_SIDE, top=GROUND_TOP):
    """Colours obj like a map hex tile: upward faces like a tile's top, the rest like its sides (on mat_ground)."""
    obj.data.materials.clear()
    obj.data.materials.append(mat_ground())
    polys = obj.data.polygons
    tops = {p.index for p in polys if p.normal.z > 0.7}
    swatch_uv(obj, "lime", faces=tops, lo=top, hi=top)
    swatch_uv(obj, "lime", faces={p.index for p in polys} - tops, lo=side[0], hi=side[1])
    return obj


def merge_duplicate_materials():
    """Imports make hexagons_medieval.001 etc.; point everything back at one material per name."""
    for o in bpy.data.objects:
        for slot in o.material_slots:
            m = slot.material
            if m and "." in m.name and m.name.rsplit(".", 1)[1].isdigit():
                base = bpy.data.materials.get(m.name.rsplit(".", 1)[0])
                if base:
                    slot.material = base
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)


def swatch_uv(obj, swatch, faces=None, lo=0.12, hi=0.88, axis=2, flip=False):
    """Map faces of obj into one atlas swatch: u at the swatch's middle, v following height (light at the top).
    swatch: a name from SW or (col, row). lo / hi: the part of the swatch's gradient to use."""
    col, row = SW[swatch] if isinstance(swatch, str) else swatch
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    zs = [v.co[axis] for v in me.vertices]
    z0, z1 = min(zs), max(zs)
    span = max(z1 - z0, 1e-6)
    u = (col + 0.5) / 8.0
    v_top = 1.0 - row / 4.0
    for p in me.polygons:
        if faces is not None and p.index not in faces:
            continue
        for li in p.loop_indices:
            t = (me.vertices[me.loops[li].vertex_index].co[axis] - z0) / span
            if flip:
                t = 1.0 - t
            g = lo + (hi - lo) * (1.0 - t)          # 0 = top of the swatch (light)
            g = min(max(g, 0.04), 0.96)             # stay off the swatch's edge (the atlas wraps / bleeds there)
            uv[li].uv = (u, v_top - g * 0.25)


def paint(obj, swatch, team=False, **kw):
    """One swatch for the whole object, on the atlas (or team) material."""
    obj.data.materials.clear()
    obj.data.materials.append(mat_team() if team else mat_kk())
    swatch_uv(obj, swatch, **kw)
    return obj


# ------------------------------------------------------------------------------------------- objects
def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c


def mesh_obj(name, bm, coll, parent=None, loc=(0, 0, 0)):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if parent:
        o.parent = parent
    o.location = loc
    for p in me.polygons:
        p.use_smooth = False
    return o


def empty(name, coll, parent=None, loc=(0, 0, 0), size=0.3, kind="PLAIN_AXES"):
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, None)
        coll.objects.link(o)
    o.empty_display_type = kind
    o.empty_display_size = size
    o.parent = parent
    o.location = loc
    return o


def bm_box(bm, size, loc=(0, 0, 0), rot=(0, 0, 0)):
    m = Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    return bm


def bm_cyl(bm, r1, r2, h, loc=(0, 0, 0), rot=(0, 0, 0), seg=10):
    """A cylinder / cone along its local Z, base at loc - h/2."""
    m = Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=m)
    return bm


def bm_beam(bm, p0, p1, w, h, w1=None, h1=None, up=(0, 0, 1)):
    """A box from point p0 to p1 (w wide, h tall at p0; w1 / h1 at p1 for a taper). `up` picks the 'tall' side."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    y = d.normalized()
    u = Vector(up)
    if abs(y.dot(u.normalized())) > 0.99:
        u = Vector((1, 0, 0)) if abs(y.x) < 0.9 else Vector((0, 1, 0))
    x = y.cross(u).normalized()
    z = x.cross(y).normalized()
    w1 = w if w1 is None else w1
    h1 = h if h1 is None else h1
    vs = []
    for (p, ww, hh) in ((p0, w, h), (p1, w1, h1)):
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vs.append(bm.verts.new(p + x * (sx * ww / 2) + z * (sz * hh / 2)))
    a, b = vs[:4], vs[4:]       # wound so every face points out (single-sided materials cull the backs)
    bm.faces.new((a[0], a[1], a[2], a[3]))
    bm.faces.new((b[3], b[2], b[1], b[0]))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((b[i], b[j], a[j], a[i]))
    return bm


def ring(bm, center, r_out, r_in, z0, z1, seg=16, axis="Z"):
    """A flat ring (washer / band) around `axis` through center."""
    c = Vector(center)
    vs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        row = []
        for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
            if axis == "Z":
                row.append(bm.verts.new(c + Vector((r * ca, r * sa, z))))
            elif axis == "X":
                row.append(bm.verts.new(c + Vector((z, r * ca, r * sa))))
            else:
                row.append(bm.verts.new(c + Vector((r * ca, z, r * sa))))
        vs.append(row)
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(4):
            l = (k + 1) % 4
            bm.faces.new((vs[i][k], vs[j][k], vs[j][l], vs[i][l]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def teamify(obj):
    """Faces of an imported KayKit piece whose UVs sit in the blue team swatch move to the kk_team material."""
    me = obj.data
    if not me.uv_layers:
        return 0
    if mat_kk().name not in [m.name for m in me.materials if m]:
        return 0
    if mat_team().name not in [m.name for m in me.materials if m]:
        me.materials.append(mat_team())
    ti = [m.name for m in me.materials].index(mat_team().name)
    uv = me.uv_layers.active.data
    n = 0
    for p in me.polygons:
        us = [uv[li].uv for li in p.loop_indices]
        cu = sum(u.x for u in us) / len(us)
        cv = sum(u.y for u in us) / len(us)
        if 0.0 <= cu < 0.125 and 0.0 <= cv < 0.25:
            p.material_index = ti
            n += 1
    return n


def view3d_override(obj=None):
    """Context for bpy.ops calls made from the MCP connector (which runs outside any editor). In a background run
    (blender -b, no windows) there's nothing to override: the active object is enough."""
    if obj is not None:
        bpy.context.view_layer.objects.active = obj
    wm = bpy.context.window_manager
    if not wm.windows or not any(a.type == "VIEW_3D" for a in wm.windows[0].screen.areas):
        import contextlib
        return contextlib.nullcontext()
    win = wm.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    kw = dict(window=win, area=area, region=region)
    if obj is not None:
        kw.update(active_object=obj, object=obj, selected_objects=[obj], selected_editable_objects=[obj])
    return bpy.context.temp_override(**kw)


def skin_to(obj, rig, bone):
    """Rigid-skin a part to one bone of `rig` (an Armature modifier plus one vertex group at full weight).
    The part's vertices are in the rig's own space."""
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    for m in [m for m in obj.modifiers if m.type == "ARMATURE"]:
        obj.modifiers.remove(m)
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return obj


def prism(bm, pts, z0, z1):
    """Extrude a counterclockwise outline from z0 to z1 (closed, with caps)."""
    bot = [bm.verts.new((p.x, p.y, z0)) for p in pts]
    top = [bm.verts.new((p.x, p.y, z1)) for p in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    return bm


def render_preview(path, yaw=0.0, pitch=33.0, dist=11.0, target=(0, 0, 0.6), size=(900, 650), engine="EEVEE",
                   lens=50.0, frame=None):
    """Render the scene from a camera orbiting `target` to a PNG (works while Blender sits behind other windows).
    yaw 0 looks from the back (-Y) toward the front, like the game camera looks at a tower facing north;
    pitch is degrees above the horizon (the game camera is 57 degrees down: pitch 57)."""
    scn = bpy.context.scene
    guides = collection("Guides")
    cam = bpy.data.objects.get("PreviewCam")
    if cam is None:
        cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
        guides.objects.link(cam)
    cam.data.lens = lens
    t = Vector(target)
    y, p = math.radians(yaw), math.radians(pitch)
    off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.location = t + off
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sun = bpy.data.objects.get("PreviewSun")
    if sun is None:
        sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
        guides.objects.link(sun)
        sun.data.energy = 3.5
        sun.data.angle = math.radians(8)
        sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-35))
    if scn.world is None:
        scn.world = bpy.data.worlds.new("World")
    scn.world.use_nodes = True
    bg = next(n for n in scn.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.42, 0.5, 0.6, 1)
    bg.inputs["Strength"].default_value = 0.9
    scn.camera = cam
    if engine == "WORKBENCH":
        scn.render.engine = "BLENDER_WORKBENCH"
        scn.display.shading.light = "STUDIO"
        scn.display.shading.color_type = "TEXTURE"
    else:
        for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                scn.render.engine = e
                break
            except TypeError:
                pass
    scn.view_settings.view_transform = "Standard"
    scn.render.resolution_x, scn.render.resolution_y = size
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.render.image_settings.file_format = "PNG"
    if frame is not None:
        scn.frame_set(frame)
    hidden = []
    for c in ("Palette",):
        cc = bpy.data.collections.get(c)
        if cc and not cc.hide_render:
            cc.hide_render = True
            hidden.append(cc)
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def export_tower(coll_name, path):
    """Exports one tower collection (its root empty, Head, Rig, meshes, markers) to a GLB the game loads from
    assets/towers/. Bevels are applied, parts stay skinned to the Rig, and every action on the Rig becomes an
    animation (sampled per frame, so the stretch-to string bones are baked)."""
    coll = bpy.data.collections[coll_name]
    rig = next((o for o in coll.objects if o.type == "ARMATURE"), None)
    keep = rig.animation_data.action if rig and rig.animation_data else None
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in coll.objects:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig or coll.objects[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with view3d_override(rig):
        bpy.ops.export_scene.gltf(
            filepath=path, export_format="GLB", use_selection=True, export_apply=True,
            export_yup=True, export_texcoords=True, export_normals=True, export_materials="EXPORT",
            export_cameras=False, export_lights=False, export_extras=False,
            export_skins=True, export_def_bones=False, export_rest_position_armature=True,
            export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
            export_frame_step=1, export_anim_slide_to_zero=True, export_reset_pose_bones=True,
            export_optimize_animation_size=False)
    if rig and keep:
        rig.animation_data.action = keep
    return path


def kk_import(rel, coll, parent=None, loc=(0, 0, 0), rot_z=0.0, scale=1.0, name=None):
    """Import a KayKit model (path under assets/kaykit without extension) as children of `parent`."""
    path = os.path.join(KK, rel + ".gltf")
    if not os.path.exists(path):
        path = os.path.join(KK, rel + ".glb")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    roots = [o for o in new if o.parent is None]
    for o in roots:
        if name:
            o.name = name
        o.parent = parent
        o.location = loc
        o.rotation_mode = "XYZ"     # the glTF importer leaves QUATERNION, which ignores rotation_euler
        o.rotation_euler = (0, 0, math.radians(rot_z))
        o.scale = (scale, scale, scale)
        o["kaykit"] = rel
    merge_duplicate_materials()
    return roots


# ------------------------------------------------------------------------------------------- tower scaffolding
TOWERS_DIR = os.path.join(REPO, "assets", "towers")


def start_tower(tid, cells, keep=("Guides", "Palette", "Palette2")):
    """Turns the open file into tower `tid`'s source: drops every other tower collection, lays KayKit grass guide hexes
    under the footprint (game scale and turn), and saves as assets/towers/src/<tid>.blend. Returns the collection."""
    scn = bpy.context.scene
    for c in list(scn.collection.children):
        if c.name not in keep:
            for o in list(c.all_objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    guides = collection("Guides")
    for o in [o for o in guides.objects if o.name.startswith("guide_hex")]:
        bpy.data.objects.remove(o, do_unlink=True)
    mid = footprint_mid(cells)
    for i, (q, s) in enumerate(cells):
        for o in kk_import("hex/hex_grass", guides, None, tuple(hex_to_world(q, s, mid)), 30.0, 1.0, "guide_hex_%d" % i):
            o.scale = (1.2 / 1.1547005, 1.2 / 1.1547005, 1.1)
            o.hide_select = True
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)
    col = collection(tid.capitalize())
    os.makedirs(os.path.join(TOWERS_DIR, "src"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TOWERS_DIR, "src", tid + ".blend"), relative_remap=True)
    return col


def plinth(cells, col, root, top=0.34, name="Base", turf=False):
    """The shared Blender-tower foundation following the footprint's hex outline: a foot course and a bevelled step,
    coloured like the map's hex tiles (paint_ground), so in game they take the biome's palette. turf: a raised layer
    of ground on top (the elves' towers); returns its top."""
    bm = bmesh.new(); prism(bm, outline(cells, 0.05), -0.06, 0.16)
    paint_ground(mesh_obj(name + "_Plinth", bm, col, root), side=GROUND_FOOT)
    bm = bmesh.new(); prism(bm, outline(cells, 0.13), 0.16, top)
    o = paint_ground(mesh_obj(name + "_Wall", bm, col, root))
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.035; b.segments = 1; b.limit_method = "ANGLE"
    if turf:
        bm = bmesh.new(); prism(bm, outline(cells, 0.17), top - 0.01, top + 0.05)
        o = paint_ground(mesh_obj(name + "_Turf", bm, col, root))
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.025; b.segments = 1; b.limit_method = "ANGLE"
        return top + 0.05
    return top


def bm_ellipsoid(bm, center, radii, rot=(0, 0, 0), u=10, v=7):
    """An ellipsoid (a squashed UV sphere) with radii (x, y, z), turned by rot (degrees)."""
    m = (Matrix.Translation(Vector(center)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
         @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=m)
    return bm


def bm_rock(bm, rnd, c, size, z0, h):
    """A rough rock block (a turned, uneven box) standing on z0."""
    rot = (rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 90))
    bm_box(bm, (size * rnd.uniform(0.85, 1.15), size * rnd.uniform(0.8, 1.1), h), (c.x, c.y, z0 + h / 2), rot)


def bm_spikes(bm, rnd, c, n, h0, h1, r, spread, sides=4):
    """A cluster of pointed shards (crystals, flames, thorns) around c: one tall in the middle, n-1 around it."""
    c = Vector(c)
    for k in range(n):
        a = math.radians(360.0 * k / max(1, n - 1) + rnd.uniform(-12, 12))
        d = 0.0 if k == 0 else spread
        cc = c + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        h = h1 if k == 0 else rnd.uniform(h0, h1 * 0.75)
        lean = Vector((math.cos(a), math.sin(a), 0)) * (0.0 if k == 0 else h * 0.18)
        top = bm.verts.new(cc + lean + Vector((0, 0, h)))
        ms = [bm.verts.new(cc + Vector((math.cos(math.radians(360.0 * j / sides + 45)) * r,
                                        math.sin(math.radians(360.0 * j / sides + 45)) * r, 0))) for j in range(sides)]
        base = bm.verts.new(cc)
        for j in range(sides):
            bm.faces.new((ms[j], ms[(j + 1) % sides], top))
            bm.faces.new((ms[(j + 1) % sides], ms[j], base))
    return bm


def glow_obj(name, bm, coll, parent, color, strength=1.4):
    """A mesh object with a glowing material (no atlas UVs needed)."""
    o = mesh_obj(name, bm, coll, parent)
    o.data.materials.append(glow_mat(name.split("_")[0].lower() + "_glow_%02x%02x%02x" % tuple(int(c * 255) for c in color[:3]),
                                     color, strength))
    o.data.uv_layers.new(name="UVMap")
    return o


def make_rig(coll, parent, bones, name="Rig", scale=1.0):
    """An armature under `parent` from {bone: (head, tail, parent bone)}, laid out at 1.0 and scaled by `scale`.
    Pose bones use quaternions."""
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    arm = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm)
    coll.objects.link(rig)
    rig.parent = parent
    arm.display_type = "STICK"
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    with view3d_override(rig):
        bpy.ops.object.mode_set(mode="EDIT")
        eb = {}
        for bname, (h, t, par) in bones.items():
            b = arm.edit_bones.new(bname)
            b.head = Vector(h) * scale
            b.tail = Vector(t) * scale
            b.roll = 0.0
            if par:
                b.parent = eb[par]
            eb[bname] = b
        bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return rig


def rig_part(name, bm, swatch, rig, bone, coll, team=False, bevel=0.012, scale=1.0, mat=None, **kw):
    """A piece laid out at 1.0 (scaled by `scale`), painted from the atlas (or given `mat`), bevelled, and rigid-skinned
    to one bone of `rig`."""
    if scale != 1.0:
        bmesh.ops.scale(bm, vec=(scale,) * 3, verts=bm.verts)
    o = mesh_obj(name, bm, coll, rig)
    if mat is not None:
        o.data.materials.clear()
        o.data.materials.append(mat)
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    else:
        paint(o, swatch, team=team, **kw)
    if bevel > 0:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel * scale
        b.segments = 1
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
    skin_to(o, rig, bone)
    return o


def glow_mat(name, color, strength=2.5):
    """A flat glowing material (crystals, halos, light) exported as a glTF emissive color."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color[:3], 1)
    bsdf.inputs["Emission Color"].default_value = (*color[:3], 1)
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Roughness"].default_value = 0.35
    return m


def arm_space_quat(pb, axis, deg):
    """A rotation of `deg` about an armature-space axis, as this bone's local pose rotation."""
    r = pb.bone.matrix_local.to_quaternion()
    return r.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ r


def arm_space_loc(pb, delta):
    return pb.bone.matrix_local.to_3x3().inverted() @ Vector(delta)


def rest_pose(rig):
    for b in rig.pose.bones:
        b.location = (0, 0, 0)
        b.rotation_quaternion = (1, 0, 0, 0)
        b.scale = (1, 1, 1)


def key_pose(rig, frame):
    for b in rig.pose.bones:
        b.keyframe_insert("location", frame=frame)
        b.keyframe_insert("rotation_quaternion", frame=frame)
        b.keyframe_insert("scale", frame=frame)


def new_action(rig, name, length):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    act.frame_range = (0, length)
    act.use_frame_range = True
    return act


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)
