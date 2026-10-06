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


def paint_ground(obj, side=GROUND_SIDE, top=GROUND_TOP, swatch="lime"):
    """Colours obj like a map hex tile: upward faces like a tile's top, the rest like its sides (on mat_ground)."""
    obj.data.materials.clear()
    obj.data.materials.append(mat_ground())
    polys = obj.data.polygons
    tops = {p.index for p in polys if p.normal.z > 0.7}
    swatch_uv(obj, swatch, faces=tops, lo=top, hi=top)
    swatch_uv(obj, swatch, faces={p.index for p in polys} - tops, lo=side[0], hi=side[1])
    return obj


def paint_water(obj):
    """Colours obj like the map's water tiles (their "blue" swatch, on mat_ground): in game a tower's pools take the
    biome's palette, like the sea."""
    return paint_ground(obj, side=(0.64, 0.76), top=0.48, swatch="blue")


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
            export_vertex_color="MATERIAL", export_all_vertex_colors=False,
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
    scn.render.fps = 30          # every tower's clips are keyed at 30 frames a second (the exporter times them by this;
    scn.render.fps_base = 1.0    # a factory-startup scene says 24, which made every clip play 25% slow)
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


def inside(pts, x, y):
    """Is (x, y) inside the outline pts (a closed loop of Vectors)?"""
    n, hit = len(pts), False
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < a.x + (b.x - a.x) * (y - a.y) / (b.y - a.y):
            hit = not hit
    return hit


def in_footprint(cells, x, y, inset=0.0):
    """Is (x, y) on the footprint's hexes, at least `inset` from their outer edge?"""
    return inside(outline(cells, inset), x, y)


def bm_cap(bm, ring, grid=0.24):
    """Fills a flat outline (BMVerts in order, counterclockwise from above, all at one height) with a mesh of small
    triangles, so the ground can hold baked shade under whatever stands on it."""
    from mathutils import geometry
    z = ring[0].co.z
    pts = [Vector((v.co.x, v.co.y, 0)) for v in ring]
    co = [Vector((p.x, p.y)) for p in pts]
    n = len(co)
    edges = [(i, (i + 1) % n) for i in range(n)]
    xs, ys = [p.x for p in co], [p.y for p in co]

    def edge_dist(p):
        best = 9.0
        for i in range(n):
            a, b = co[i], co[(i + 1) % n]
            t = min(max((p - a).dot(b - a) / max((b - a).length_squared, 1e-9), 0.0), 1.0)
            best = min(best, (a + (b - a) * t - p).length)
        return best
    row, y = 0, min(ys) + grid * 0.5
    while y < max(ys):
        x = min(xs) + (grid * 0.5 if row % 2 else grid)
        while x < max(xs):
            p = Vector((x, y))
            if inside(pts, x, y) and edge_dist(p) > grid * 0.4:
                co.append(p)
            x += grid
        y += grid * 0.866
        row += 1
    vs, _, fs, _, _, _ = geometry.delaunay_2d_cdt(co, edges, [], 1, 1e-5)
    made = {}
    for i, p in enumerate(vs):
        best = None
        for j in range(n):
            if (co[j] - p).length < 1e-4:
                best = ring[j]
                break
        made[i] = best or bm.verts.new((p.x, p.y, z))
    for f in fs:
        tri = [made[i] for i in f]
        if len(set(tri)) == 3:
            face = bm.faces.new(tri)
            if face.calc_area() > 1e-9 and Vector(face.normal).z < 0:   # (delaunay's winding isn't promised)
                face.normal_flip()
    return bm


def plinth(cells, col, root, top=0.34, name="Base", turf=False):
    """The shared Blender-tower foundation following the footprint's hex outline: a low knoll with battered sides and
    a chamfered shoulder, coloured like the map's hex tiles (paint_ground), so in game it takes the biome's palette
    (grass on top, earth down the sides). Its top is a mesh of small triangles that holds the baked contact shade.
    turf: a thicker layer of ground (the elves' towers). Returns the top's height."""
    if turf:
        top += 0.05
    bm = bmesh.new()
    rings = []
    for ins, z in ((0.05, -0.06), (0.1, top - 0.075), (0.16, top)):
        loop = outline(cells, ins)
        fine = []
        for i, p in enumerate(loop):          # four short edges per hex side, so the rim holds shade too
            q = loop[(i + 1) % len(loop)]
            fine.extend(p.lerp(q, k / 4.0) for k in range(4))
        rings.append([bm.verts.new((p.x, p.y, z)) for p in fine])
    n = len(rings[0])
    bm.faces.new(list(reversed(rings[0])))
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm_cap(bm, rings[2])
    o = mesh_obj(name + "_Plinth", bm, col, root)
    o["ground"] = True
    paint_ground(o)
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


# ------------------------------------------------------------------------------------------- finishing: baked shade
AO_NAME = "AO"


def apply_modifiers(objs):
    """Bakes every modifier but the armature into the mesh (bevels and the like), so the mesh that gets its shade
    baked is the mesh that's exported."""
    todo = []
    for o in objs:
        mods = [m for m in o.modifiers if m.type != "ARMATURE"]
        if not mods:
            continue
        arms = [m for m in o.modifiers if m.type == "ARMATURE"]
        for m in arms:
            m.show_viewport = False
        todo.append((o, mods, arms))
    if not todo:
        return
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for o, mods, arms in todo:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        old = o.data
        name = old.name
        for m in mods:
            o.modifiers.remove(m)
        o.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
        me.name = name
        for m in arms:
            m.show_viewport = True
    bpy.context.view_layer.update()


def refine_for_shade(o, max_edge=0.5):
    """Cuts a mesh's big faces into smaller ones (n-gons into triangles, then every edge longer than max_edge in
    half until none is), so shade baked at the corners has somewhere to live: a wide wall can go dark only near the
    ground, a round platform only under what stands on it. The surface itself doesn't change."""
    me = o.data
    sc = o.matrix_world.to_scale()
    s = max(abs(sc.x), abs(sc.y), abs(sc.z), 1e-6)
    bm = bmesh.new()
    bm.from_mesh(me)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, ngon_method="BEAUTY")
    for _ in range(4):
        long = [e for e in bm.edges if e.calc_length() * s > max_edge]
        if not long:
            break
        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, ngon_method="BEAUTY")
    bm.to_mesh(me)
    bm.free()
    me.update()


def _hemisphere(n):
    """n cosine-weighted directions over the +Z hemisphere (a sunflower spiral)."""
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        u = (i + 0.5) / n
        r = math.sqrt(u)
        out.append(Vector((r * math.cos(i * ga), r * math.sin(i * ga), math.sqrt(1.0 - u))))
    return out


def _is_glow(o):
    for m in o.data.materials:
        if m is None or not m.use_nodes:
            continue
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b and not b.inputs["Base Color"].is_linked and b.inputs["Emission Strength"].default_value > 0.0:
            return True
    return False


def bake_ao(col, samples=28, dist=0.85, strength=0.62, floor=0.36, ground_dist=1.25):
    """Bakes soft contact shade into every mesh of a tower: a float color attribute (AO_NAME) per face corner, which
    the materials multiply into their color (wire_ao) and the game reads as vertex colors. Everything is taken in its
    rest pose. Corners that share a vertex and a facing share one value, so flat ground shades smoothly while hard
    edges keep their crease. Glowing parts and objects with o["no_ao"] stay unshaded; objects with o["no_ao_cast"]
    throw no shade on the rest. Shade leans a little blue."""
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    objs = [o for o in col.all_objects if o.type == "MESH"]
    verts, tris = [], []
    for o in objs:
        if o.get("no_ao_cast"):
            continue
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        base = len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        tris.extend((base + t.vertices[0], base + t.vertices[1], base + t.vertices[2]) for t in me.loop_triangles)
    base = len(verts)       # the map around the tower: a big floor at ground level
    verts.extend(Vector(p) for p in ((-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)))
    tris.extend(((base, base + 1, base + 2), (base, base + 2, base + 3)))
    tree = BVHTree.FromPolygons(verts, tris, all_triangles=True)
    hemi = _hemisphere(samples)
    up = Vector((0, 0, 1))
    for o in objs:
        me = o.data
        attr = me.color_attributes.get(AO_NAME)
        if attr is None:
            attr = me.color_attributes.new(AO_NAME, "FLOAT_COLOR", "CORNER")
        cols = [1.0] * (len(me.loops) * 4)
        if not (o.get("no_ao") or _is_glow(o)):
            mw = o.matrix_world
            nm = mw.to_3x3().inverted_safe().transposed()
            reach = ground_dist if o.get("ground") else dist
            cache = {}
            for p in me.polygons:
                n = (nm @ p.normal).normalized()
                if n.length < 0.5:
                    continue
                c = mw @ p.center
                kn = (round(n.x, 1), round(n.y, 1), round(n.z, 1))
                t = n.cross(up)
                if t.length < 1e-3:
                    t = Vector((1, 0, 0))
                t.normalize()
                b = n.cross(t)
                for li, vi in zip(p.loop_indices, p.vertices):
                    key = (vi, kn)
                    m = cache.get(key)
                    if m is None:
                        pw = mw @ me.vertices[vi].co
                        start = pw + (c - pw) * 0.05 + n * 0.008
                        s = 0.0
                        for d in hemi:
                            hit = tree.ray_cast(start, t * d.x + b * d.y + n * d.z, reach)
                            if hit[0] is not None:
                                s += 1.0 - (hit[3] / reach) ** 1.6
                        m = max(floor, 1.0 - strength * min(1.0, s / samples * 1.15))
                        cache[key] = m
                    sh = 1.0 - m
                    cols[li * 4:li * 4 + 3] = (1.0 - sh * 1.07, 1.0 - sh, 1.0 - sh * 0.86)
        attr.data.foreach_set("color", cols)
        me.color_attributes.active_color = attr
        me.color_attributes.render_color_index = list(me.color_attributes).index(attr)
        me.update()


def wire_ao(mat):
    """Makes a textured material multiply its texture by the baked shade (the AO color attribute)."""
    if mat is None or not mat.use_nodes or mat.get("ao_wired"):
        return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    inp = bsdf.inputs["Base Color"]
    if not inp.is_linked or inp.links[0].from_node.type != "TEX_IMAGE":
        return
    src = inp.links[0].from_socket
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = AO_NAME
    attr.location = (-400, -120)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.location = (-180, 200)
    sock = {s.identifier: s for s in mix.inputs}
    sock["Factor_Float"].default_value = 1.0
    nt.links.new(src, sock["A_Color"])
    nt.links.new(attr.outputs["Color"], sock["B_Color"])
    nt.links.new(next(s for s in mix.outputs if s.identifier == "Result_Color"), inp)
    mat["ao_wired"] = True


def tri_count(col):
    n = 0
    for o in col.all_objects:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n += len(o.data.loop_triangles)
    return n


def finalize_tower(col, ao=True):
    """Call once a tower is built, before export_tower: applies the bevels, bakes the contact shade and wires it into
    the materials. Every mesh in the file gets the AO attribute (white where nothing is baked), because a wired
    material draws black on a mesh without it. Returns the triangle count."""
    if isinstance(col, str):
        col = bpy.data.collections[col]
    apply_modifiers([o for o in col.all_objects if o.type == "MESH"])
    if ao:
        for o in col.all_objects:
            if o.type == "MESH" and not (o.get("no_ao") or o.get("no_refine") or _is_glow(o)):
                refine_for_shade(o)
        bake_ao(col)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        me = o.data
        if me.color_attributes.get(AO_NAME) is None:
            a = me.color_attributes.new(AO_NAME, "FLOAT_COLOR", "CORNER")
            a.data.foreach_set("color", [1.0] * (len(me.loops) * 4))
        for m in me.materials:
            wire_ao(m)
    return tri_count(col)


# ------------------------------------------------------------------------------------------- the modelling kit
# Bigger building blocks, so a tower's script reads as a design rather than a pile of boxes: geometry gathered by
# color (Kit), coursed stonework, tiled roofs, plank decks, faceted rocks and foliage, lofted bodies and limbs for
# creatures (with soft skinning), flags that wave, paving and stones to dress the ground.
import random


def _islands(me):
    """Each polygon's connected piece (a number): boxes added one by one stay separate pieces."""
    parent = list(range(len(me.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for p in me.polygons:
        r = find(p.vertices[0])
        for v in p.vertices[1:]:
            parent[find(v)] = r
    return [find(p.vertices[0]) for p in me.polygons]


def vary_shade(obj, amount=0.06, seed=1):
    """Nudges each connected piece of obj (a stone, a plank, a tile) a random step lighter or darker along its
    swatch's gradient, so masonry and planking read as separate pieces. amount: the biggest step, in swatch heights."""
    me = obj.data
    if not me.uv_layers:
        return obj
    uv = me.uv_layers.active.data
    isl = _islands(me)
    rnd = random.Random(seed)
    shift = {}
    for p in me.polygons:
        d = shift.get(isl[p.index])
        if d is None:
            d = shift[isl[p.index]] = rnd.uniform(-amount, amount)
        for li in p.loop_indices:
            u, v = uv[li].uv
            v_top = math.ceil(v * 4.0 - 1e-6) / 4.0
            g = min(max((v_top - v) / 0.25 + d, 0.04), 0.96)
            uv[li].uv = (u, v_top - g * 0.25)
    return obj


def paint_faces(obj, swatch, where, team=False, lo=0.12, hi=0.88):
    """Repaints the faces of obj for which where(center, normal) is True (both in the object's own space, after any
    Kit scale) with another swatch, or the team color: war paint, a pale belly, a dark muzzle, a painted band, with
    no extra geometry. Returns how many faces it took."""
    me = obj.data
    mat = mat_team() if team else mat_kk()
    names = [m.name if m else "" for m in me.materials]
    if mat.name not in names:
        me.materials.append(mat)
        names.append(mat.name)
    idx = names.index(mat.name)
    faces = set()
    for p in me.polygons:
        if where(p.center, p.normal):
            p.material_index = idx
            faces.add(p.index)
    if faces:
        swatch_uv(obj, swatch, faces=faces, lo=lo, hi=hi)
    return len(faces)


class Kit:
    """Gathers geometry by color and makes one mesh object per color at the end:

        k = Kit()
        bm_box(k["stone"], ...)             # any swatch in SW
        bm_cyl(k["roof:0.1:0.6"], ...)      # with the part of the swatch's gradient to use (lo:hi, light to dark)
        bm_box(k["team!"], ...)             # "!" = the team material (the game slides it to your color)
        bm_box(k["ground"], ...)            # like the map's hexes (paint_ground); "water" likewise (paint_water)
        bm_box(k["glow:1,0.8,0.3"], ...)    # a glowing color (r,g,b[,strength]); never shaded
        k.emit("Keep", col, root, bevel=0.02, vary=0.05)        # -> Keep_stone, Keep_roof, Keep_team ... under root
        k.emit("Head_Arm", col, rig=rig, bone="arm.L")           # ... or rigid-skinned to one bone
        k.emit("Head_Tail", col, rig=rig, bones=["tail.1", "tail.2"])   # ... or soft-skinned to the nearest of some

    emit() empties the kit, so one Kit can be reused part after part. scale: lay parts out at 1.0, emit them bigger."""

    def __init__(self):
        self.parts = {}

    def __getitem__(self, key):
        if key not in self.parts:
            self.parts[key] = bmesh.new()
        return self.parts[key]

    def emit(self, name, col, parent=None, bevel=0.0, vary=0.0, seed=1, rig=None, bone=None, bones=None, scale=1.0,
             segments=1, tag=None):
        out = []
        used = set()
        for key, bm in self.parts.items():
            if not bm.verts:
                bm.free()
                continue
            if scale != 1.0:
                bmesh.ops.scale(bm, vec=(scale,) * 3, verts=bm.verts)
            bits = key.split(":")
            kind = bits[0]
            label = kind.rstrip("!")
            oname = "%s_%s" % (name, label)
            if oname in used:           # the same swatch twice (two gradient ranges): number the later ones
                oname = "%s%d" % (oname, len(out))
            used.add(oname)
            o = mesh_obj(oname, bm, col, rig if rig is not None else parent)
            if kind == "glow":
                c = [float(x) for x in bits[1].split(",")]
                o.data.materials.append(glow_mat("glow_%02x%02x%02x" % tuple(int(min(max(x, 0.0), 1.0) * 255) for x in c[:3]),
                                                 c[:3], c[3] if len(c) > 3 else 1.6))
                o.data.uv_layers.new(name="UVMap")
            elif kind == "ground":
                paint_ground(o)
                o["ground"] = True
            elif kind == "water":
                paint_water(o)
            else:
                lo = float(bits[1]) if len(bits) > 1 else 0.12
                hi = float(bits[2]) if len(bits) > 2 else 0.88
                paint(o, label, team=kind.endswith("!"), lo=lo, hi=hi)
                if vary > 0.0:
                    vary_shade(o, vary, seed + len(out))
            if bevel > 0.0 and kind != "glow":
                b = o.modifiers.new("Bevel", "BEVEL")
                b.width = bevel * scale
                b.segments = segments
                b.limit_method = "ANGLE"
                b.angle_limit = math.radians(40)
            if rig is not None:
                if bones:
                    skin_soft(o, rig, bones)
                else:
                    skin_to(o, rig, bone or "root")
            if tag:
                o[tag] = True
            out.append(o)
        self.parts = {}
        return out


# ---- rocks, foliage, crystals
def bm_boulder(bm, rnd, base, r, squash=(1.0, 1.0, 0.8), n=12, sink=0.18):
    """A faceted rock (the hull of n jittered points on an ellipsoid of radius r) sitting on `base`, sunk in a little."""
    base = Vector(base)
    pts = []
    for i in range(n):
        u = (i + 0.5) / n
        z = 1.0 - 2.0 * u
        rad = math.sqrt(max(0.0, 1.0 - z * z))
        a = i * 2.39996 + rnd.uniform(-0.35, 0.35)
        k = rnd.uniform(0.74, 1.0)
        pts.append(Vector((rad * math.cos(a) * r * squash[0] * k, rad * math.sin(a) * r * squash[1] * k, z * r * squash[2] * k)))
    low = min(p.z for p in pts)
    lift = -low - sink * r * squash[2]
    vs = [bm.verts.new(base + Vector((p.x, p.y, max(p.z + lift, -0.02)))) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    junk = [e for e in list(res.get("geom_interior", [])) + list(res.get("geom_unused", [])) if isinstance(e, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    faces = [f for f in res.get("geom", []) if isinstance(f, bmesh.types.BMFace) and f.is_valid]
    if faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)
    return bm


def bm_blob(bm, rnd, c, r, squash=(1.0, 1.0, 1.0), jitter=0.14, sub=1):
    """A lumpy low-poly ball (a jittered icosphere: 20 faces at sub 1, 80 at sub 2): tree crowns, bushes, clouds, smoke."""
    c = Vector(c)
    m = Matrix.Translation(c) @ Matrix.Diagonal((r * squash[0], r * squash[1], r * squash[2], 1.0))
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0, matrix=m)
    for v in res["verts"]:
        v.co = c + (v.co - c) * (1.0 + rnd.uniform(-jitter, jitter))
    return bm


def bm_crystal(bm, base, tip, r, n=6, shoulder=0.7, foot=0.75):
    """A pointed crystal from base to tip: a prism of n sides up to `shoulder` of its length, then a point."""
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    ax = d.normalized()
    x = ax.cross(Vector((0, 0, 1)))
    if x.length < 1e-3:
        x = Vector((1, 0, 0))
    x.normalize()
    y = ax.cross(x)
    lo = [bm.verts.new(base + (x * math.cos(2 * math.pi * i / n) + y * math.sin(2 * math.pi * i / n)) * r * foot) for i in range(n)]
    hi = [bm.verts.new(base + d * shoulder + (x * math.cos(2 * math.pi * i / n) + y * math.sin(2 * math.pi * i / n)) * r) for i in range(n)]
    top = bm.verts.new(tip)
    bm.faces.new(list(reversed(lo)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new((hi[i], hi[j], top))
    return bm


# ---- lofts and tubes: bodies, limbs, tails, tentacles, trunks, horns, ropes
def oval(c, x_axis, y_axis, rx, ry, n=8, power=2.0, phase=0.0):
    """n points round an ellipse (a rounded box for power > 2) at c, in the plane of x_axis and y_axis."""
    c, x, y = Vector(c), Vector(x_axis).normalized(), Vector(y_axis).normalized()
    out = []
    e = 2.0 / power
    for i in range(n):
        a = 2 * math.pi * (i + phase) / n
        ca, sa = math.cos(a), math.sin(a)
        out.append(c + x * (math.copysign(abs(ca) ** e, ca) * rx) + y * (math.copysign(abs(sa) ** e, sa) * ry))
    return out


def bm_loft(bm, rings, cap0=True, cap1=True, tip0=None, tip1=None):
    """Skins a row of rings (lists of points, the same count in each, going round the same way) into one surface.
    Ends are closed with a flat cap, or drawn to a point (tip0 / tip1). Returns the rings as lists of vertices."""
    vr = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(vr[0])
    faces = []
    for a, b in zip(vr, vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    for ring, cap, tip, flip in ((vr[0], cap0, tip0, True), (vr[-1], cap1, tip1, False)):
        if tip is not None:
            t = bm.verts.new(Vector(tip))
            for i in range(n):
                j = (i + 1) % n
                faces.append(bm.faces.new((ring[j], ring[i], t) if flip else (ring[i], ring[j], t)))
        elif cap:
            faces.append(bm.faces.new(list(reversed(ring)) if flip else ring))
    # rings may go round either way: make the first band face away from the loft's middle line, and flip all if not
    f = faces[0]
    f.normal_update()
    mid = sum((v.co for v in vr[0]), Vector()) / n
    if len(vr) > 1:
        mid2 = sum((v.co for v in vr[1]), Vector()) / n
    else:                       # one ring drawn to a point (a cone): its axis runs to the tip
        mid2 = Vector(tip1 if tip1 is not None else tip0) if (tip0 is not None or tip1 is not None) else mid
    if f.normal.dot(f.calc_center_median() - (mid + mid2) * 0.5) < 0:
        for q in faces:
            q.normal_flip()
    return vr


def bm_tube(bm, pts, radii, n=6, cap=True, up=(0, 0, 1), squash=1.0, phase=0.0):
    """A tube through pts with a radius at each (one number, or a list); a radius near 0 at an end makes a point.
    squash: how wide it is across compared with along `up` (a flattened tail, a blade). Returns its vertex rings."""
    pts = [Vector(p) for p in pts]
    m = len(pts)
    rad = [radii] * m if isinstance(radii, (int, float)) else list(radii)
    tans = []
    for k in range(m):
        t = pts[min(k + 1, m - 1)] - pts[max(k - 1, 0)]
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    u = Vector(up).normalized()
    x = u - tans[0] * u.dot(tans[0])
    if x.length < 1e-3:
        x = Vector((1, 0, 0)) - tans[0] * tans[0].x
    x.normalize()
    rings, tip0, tip1 = [], None, None
    for k in range(m):
        t = tans[k]
        x = x - t * x.dot(t)
        if x.length < 1e-6:
            x = t.orthogonal()
        x.normalize()
        y = t.cross(x)
        if rad[k] < 1e-4 and k == 0:
            tip0 = pts[k]
        elif rad[k] < 1e-4 and k == m - 1:
            tip1 = pts[k]
        else:
            rings.append(oval(pts[k], y, x, rad[k] * squash, rad[k], n, phase=phase))
    return bm_loft(bm, rings, cap0=cap, cap1=cap, tip0=tip0, tip1=tip1)


def skin_soft(obj, rig, bones=None, power=4.0, max_inf=3):
    """Skins obj to the nearest few of `bones` (default: all of the rig's), weights falling off with distance, so one
    mesh bends smoothly over a chain (a tail, a tentacle, a neck, a body over its spine). The mesh is in rig space."""
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    for m in [m for m in obj.modifiers if m.type == "ARMATURE"]:
        obj.modifiers.remove(m)
    obj.vertex_groups.clear()
    segs = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones if bones is None or b.name in bones]
    groups = {name: obj.vertex_groups.new(name=name) for name, _, _ in segs}
    for v in obj.data.vertices:
        ds = []
        for name, h, t in segs:
            ab = t - h
            k = min(max((v.co - h).dot(ab) / max(ab.length_squared, 1e-9), 0.0), 1.0)
            ds.append(((h + ab * k - v.co).length, name))
        ds.sort()
        top = ds[:max_inf]
        ws = [1.0 / max(d, 1e-3) ** power for d, _ in top]
        total = sum(ws)
        for (d, name), w in zip(top, ws):
            if w / total > 0.02:
                groups[name].add([v.index], w / total, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return obj


# ---- stonework
def _wedge(bm, c, a0, a1, r_in, r_out, z0, z1):
    """A block between two angles and two radii (a piece of a ring)."""
    vs = []
    for z in (z0, z1):
        for r, a in ((r_in, a0), (r_out, a0), (r_out, a1), (r_in, a1)):
            vs.append(bm.verts.new((c.x + r * math.cos(a), c.y + r * math.sin(a), z)))
    lo, hi = vs[:4], vs[4:]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))


def bm_block_course(bm, rnd, c, r, z, h, n, depth=0.16, gap=0.02, phase=0.0, jit=0.012, skip=None):
    """One course of n stone blocks round a circle: outer radius r, `depth` thick, from z to z + h. phase: turn the
    joints by this part of a block (0.5 for running bond). skip(angle in degrees) -> True leaves a block out (a door)."""
    c = Vector(c)
    ga = gap / max(r, 1e-3)
    for i in range(n):
        a0 = 2 * math.pi * (i + phase) / n + ga * 0.5
        a1 = 2 * math.pi * (i + 1 + phase) / n - ga * 0.5
        if skip and skip(math.degrees((a0 + a1) * 0.5) % 360.0):
            continue
        ro = r + rnd.uniform(-jit, jit)
        _wedge(bm, c, a0, a1, r - depth, ro, z + rnd.uniform(0, jit * 0.6), z + h - gap * 0.6 - rnd.uniform(0, jit * 0.6))
    return bm


def round_tower(kit, rnd, c, r0, r1, z0, z1, courses=6, n=10, depth=0.16, stone="stone", core="stone_dark:0.3:0.9", skip=None):
    """A round stone tower from z0 to z1 (radius r0 at the foot, r1 at the top) in coursed blocks, the joints
    staggered, over a dark core that shows in the joints. skip(course index, angle in degrees) leaves blocks out."""
    c = Vector(c)
    h = (z1 - z0) / courses
    for k in range(courses):
        r = r0 + (r1 - r0) * (k + 0.5) / courses
        bm_block_course(kit[stone], rnd, c, r, z0 + k * h, h, n, depth=depth, phase=0.5 * (k % 2),
                        skip=(lambda a, k=k: skip(k, a)) if skip else None)
    bm_cyl(kit[core], r0 - depth * 0.45, r1 - depth * 0.45, z1 - z0 - 0.01, (c.x, c.y, (z0 + z1) / 2), seg=max(n, 12))
    return kit


def bm_merlons(bm, c, r, z, n, w=0.24, h=0.2, depth=0.16, phase=0.0):
    """n battlement teeth round a circle of outer radius r, standing on z (each `w` wide along the wall)."""
    c = Vector(c)
    half = w / max(r, 1e-3) * 0.5
    for i in range(n):
        a = 2 * math.pi * (i + phase) / n
        _wedge(bm, c, a - half, a + half, r - depth, r, z, z + h)
    return bm


def bm_block_wall(bm, rnd, p0, p1, z0, z1, th=0.2, course=0.2, block=0.36, gap=0.02, jit=0.012):
    """A straight wall of coursed blocks (running bond) from p0 to p1 (x, y), z0 to z1, `th` thick."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    d = p1 - p0
    length = d.length
    ax = d.normalized()
    nr = Vector((-ax.y, ax.x, 0))
    rows = max(1, round((z1 - z0) / course))
    hh = (z1 - z0) / rows
    cols = max(1, round(length / block))
    bw = length / cols
    for k in range(rows):
        edges = [0.0] + [min(length, (i + (0.5 if k % 2 else 0.0)) * bw) for i in range(1, cols + (1 if k % 2 else 0))] + [length]
        edges = sorted(set(round(e, 5) for e in edges))
        for a, b in zip(edges, edges[1:]):
            if b - a < gap * 2:
                continue
            t = th * 0.5 + rnd.uniform(-jit, jit)
            za, zb = z0 + k * hh + rnd.uniform(0, jit * 0.5), z0 + (k + 1) * hh - gap * 0.6
            vs = []
            for z in (za, zb):
                for s, side in ((a + gap * 0.5, -1), (b - gap * 0.5, -1), (b - gap * 0.5, 1), (a + gap * 0.5, 1)):
                    q = p0 + ax * s + nr * (side * t)
                    vs.append(bm.verts.new((q.x, q.y, z)))
            lo, hi = vs[:4], vs[4:]
            bm.faces.new(list(reversed(lo)))
            bm.faces.new(hi)
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def bm_arch(bm, c, right, w, spring, th=0.14, depth=0.2, n=7, jambs=True):
    """A round stone arch standing on c (the middle of its sill): an opening `w` wide, straight up to `spring`, then
    a half circle of n wedge stones. right: the direction along the wall; depth: through the wall; th: stone size."""
    c = Vector(c)
    rt = Vector(right).normalized()
    up = Vector((0, 0, 1))
    out = rt.cross(up)
    r = w * 0.5

    def stone(p0, p1, p2, p3):          # four points of the stone's face, extruded through the wall
        vs = [bm.verts.new(p + out * (depth * 0.5)) for p in (p0, p1, p2, p3)] + \
             [bm.verts.new(p - out * (depth * 0.5)) for p in (p0, p1, p2, p3)]
        fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
        for i in range(4):
            j = (i + 1) % 4
            fs.append(bm.faces.new((vs[j], vs[i], vs[4 + i], vs[4 + j])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    if jambs:
        for s in (-1, 1):
            stone(c + rt * (s * r), c + rt * (s * (r + th)), c + rt * (s * (r + th)) + up * spring, c + rt * (s * r) + up * spring)
    o = c + up * spring
    for i in range(n):
        a0, a1 = math.pi * i / n + 0.012, math.pi * (i + 1) / n - 0.012
        pin = lambda a, rr: o + rt * (math.cos(a) * rr) + up * (math.sin(a) * rr)
        stone(pin(a0, r), pin(a0, r + th), pin(a1, r + th), pin(a1, r))
    return bm


# ---- timber and roofs
def bm_planks(bm, rnd, origin, along, across, n, th=0.05, gap=0.012, jit=0.012):
    """n planks side by side: each runs the length of `along`, they're laid across `across` (both vectors from
    origin, the deck's near corner), `th` thick below that plane. Ends and heights are a touch uneven."""
    o, a, w = Vector(origin), Vector(along), Vector(across)
    nrm = a.cross(w).normalized()
    if nrm.z < -0.3:
        nrm = -nrm          # a deck: always thick downward (for a wall, along x across points out of its face)
    step = w / n
    for i in range(n):
        e0, e1 = rnd.uniform(-jit, jit), rnd.uniform(-jit, jit)
        lift = rnd.uniform(-jit, jit) * 0.4
        p = o + step * i + step.normalized() * (gap * 0.5) + nrm * lift
        ww = step - step.normalized() * gap
        ad = a.normalized()
        q0, q1 = p + ad * e0, p + a + ad * e1
        vs = [bm.verts.new(v) for v in (q0, q1, q1 + ww, q0 + ww)] + [bm.verts.new(v - nrm * th) for v in (q0, q1, q1 + ww, q0 + ww)]
        fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
        for k in range(4):
            j = (k + 1) % 4
            fs.append(bm.faces.new((vs[j], vs[k], vs[4 + k], vs[4 + j])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def bm_tile_slope(bm, rnd, e0, e1, r0, r1, rows=5, cols=6, th=0.04, lap=0.3, jit=0.01):
    """A roof slope of overlapping tiles between an eave (e0 -> e1) and a ridge (r0 above e0, r1 above e1): rows from
    the eave up, each tile's lower end lifted over the row below; every other row is shifted half a tile."""
    e0, e1, r0, r1 = Vector(e0), Vector(e1), Vector(r0), Vector(r1)
    nrm = (e1 - e0).cross(r0 - e0).normalized()
    if nrm.z < 0:
        nrm = -nrm
    for k in range(rows):
        t0, t1 = k / rows, (k + 1) / rows
        t0 = max(0.0, t0 - lap / rows)
        a0, a1 = e0.lerp(r0, t0), e1.lerp(r1, t0)
        b0, b1 = e0.lerp(r0, t1), e1.lerp(r1, t1)
        cuts = [0.0] + [(i + (0.5 if k % 2 else 0.0)) / cols for i in range(1, cols + (1 if k % 2 else 0))] + [1.0]
        cuts = sorted(set(round(c, 5) for c in cuts if 0.0 <= c <= 1.0))
        for u0, u1 in zip(cuts, cuts[1:]):
            g = 0.012 / max((a1 - a0).length, 1e-6)
            if u1 - u0 < g * 3:
                continue
            lo0, lo1 = a0.lerp(a1, u0 + g), a0.lerp(a1, u1 - g)
            hi0, hi1 = b0.lerp(b1, u0 + g), b0.lerp(b1, u1 - g)
            up_ = nrm * (th + rnd.uniform(0, jit))
            vs = [bm.verts.new(v) for v in (lo0 + up_, lo1 + up_, hi1 + nrm * 0.004, hi0 + nrm * 0.004)] + \
                 [bm.verts.new(v) for v in (lo0 + nrm * 0.004, lo1 + nrm * 0.004, hi1 - nrm * th * 0.5, hi0 - nrm * th * 0.5)]
            fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
            for i in range(4):
                j = (i + 1) % 4
                fs.append(bm.faces.new((vs[j], vs[i], vs[4 + i], vs[4 + j])))
            bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


def bm_tile_cone(bm, rnd, c, r, z, h, rows=5, n=12, th=0.04, lap=0.3, flare=0.05, top=0.06):
    """A conical roof of overlapping tiles: base radius r at height z, `h` tall (it stops at radius `top`, where a
    finial goes). n tiles in the bottom row, fewer further up; the eave flares out a little."""
    c = Vector(c)
    for k in range(rows):
        t0, t1 = max(0.0, (k - lap) / rows), (k + 1) / rows
        ra, rb = r + (top - r) * t0, r + (top - r) * t1
        za, zb = z + h * t0, z + h * t1
        if k == 0:
            ra += flare
            za -= flare * 0.6
        cnt = max(5, int(round(n * (0.35 + 0.65 * (1 - k / rows)))))
        ph = 0.5 * (k % 2)
        for i in range(cnt):
            a0 = 2 * math.pi * (i + ph) / cnt + 0.012 / max(ra, 0.05)
            a1 = 2 * math.pi * (i + 1 + ph) / cnt - 0.012 / max(ra, 0.05)
            lift = th + rnd.uniform(0, 0.012)
            pts = []
            for rr, zz, lf in ((ra, za, lift), (rb, zb, 0.004)):
                for a in (a0, a1):
                    pts.append((Vector((c.x + rr * math.cos(a), c.y + rr * math.sin(a), zz)), lf, a))
            sl = Vector((rb - ra, 0, zb - za))
            nz = Vector((-sl.z, 0, sl.x)).normalized()          # the slope's normal in the (radial, z) plane
            if nz.z < 0:
                nz = -nz
            def off(p, lf, a):
                return p + Vector((nz.x * math.cos(a), nz.x * math.sin(a), nz.z)) * lf
            (p0, l0, aa0), (p1, l1, aa1), (p2, l2, aa2), (p3, l3, aa3) = pts
            vs = [bm.verts.new(off(p0, l0, aa0)), bm.verts.new(off(p1, l1, aa1)), bm.verts.new(off(p3, l3, aa3)), bm.verts.new(off(p2, l2, aa2)),
                  bm.verts.new(off(p0, 0.0, aa0)), bm.verts.new(off(p1, 0.0, aa1)), bm.verts.new(off(p3, -th * 0.5, aa3)), bm.verts.new(off(p2, -th * 0.5, aa2))]
            fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
            for q in range(4):
                j = (q + 1) % 4
                fs.append(bm.faces.new((vs[j], vs[q], vs[4 + q], vs[4 + j])))
            bmesh.ops.recalc_face_normals(bm, faces=fs)
    return bm


# ---- ground dressing
def bm_flagstones(bm, rnd, where, bounds, z, size=0.3, gap=0.035, h=0.035, keep=1.0):
    """Paving: irregular flat stones on a jittered honeycomb, wherever where(x, y) is True inside bounds
    (x0, y0, x1, y1). size: stone spacing; keep: the share of stones laid (under 1 for worn, broken paving)."""
    x0, y0, x1, y1 = bounds
    row, y = 0, y0
    while y <= y1:
        x = x0 + (size * 0.5 if row % 2 else 0.0)
        while x <= x1:
            cx, cy = x + rnd.uniform(-0.12, 0.12) * size, y + rnd.uniform(-0.12, 0.12) * size
            if where(cx, cy) and rnd.random() < keep:
                k = rnd.choice((5, 6, 6, 7))
                rr = size * 0.5 - gap * 0.5
                a0 = rnd.uniform(0, 6.283)
                top = [Vector((cx + math.cos(a0 + 6.283 * i / k) * rr * rnd.uniform(0.82, 1.08),
                               cy + math.sin(a0 + 6.283 * i / k) * rr * rnd.uniform(0.82, 1.08),
                               z + h * rnd.uniform(0.7, 1.15))) for i in range(k)]
                zt = sum(p.z for p in top) / k
                tv = [bm.verts.new((p.x, p.y, zt)) for p in top]
                bv = [bm.verts.new((p.x, p.y, z - 0.01)) for p in top]
                bm.faces.new(tv)
                for i in range(k):
                    j = (i + 1) % k
                    bm.faces.new((bv[i], bv[j], tv[j], tv[i]))
            x += size
        y += size * 0.866
        row += 1
    return bm


def scatter_points(rnd, cells, n, inset=0.3, avoid=(), min_gap=0.25, tries=60):
    """n random spots (Vectors, z = 0) on the footprint's hexes, `inset` from its edge, clear of every (x, y, radius)
    in avoid and of each other."""
    mid = footprint_mid(cells)
    loop = outline(cells, inset)
    xs, ys = [p.x for p in loop], [p.y for p in loop]
    out = []
    for _ in range(n):
        for _ in range(tries):
            x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
            if not inside(loop, x, y):
                continue
            if any((x - ax) ** 2 + (y - ay) ** 2 < ar * ar for ax, ay, ar in avoid):
                continue
            if any((x - p.x) ** 2 + (y - p.y) ** 2 < min_gap * min_gap for p in out):
                continue
            out.append(Vector((x, y, 0)))
            break
    return out


# ---- flags
def flag_bones(bones, name, top, direction, length, segs=3, parent="root"):
    """Adds a chain of bones name.1 .. name.N to a BONES dict: a flag `length` long flying from `top` along `direction`."""
    top, d = Vector(top), Vector(direction).normalized()
    step = d * (length / segs)
    prev = parent
    for k in range(segs):
        bones["%s.%d" % (name, k + 1)] = (tuple(top + step * k), tuple(top + step * (k + 1)), prev)
        prev = "%s.%d" % (name, k + 1)
    return bones


def flag_part(name, col, rig, bone_name, top, direction, length, height, segs=3, swatch="team!", tail="swallow", scale=1.0,
              hang=(0, 0, -1)):
    """The cloth for flag_bones(): one strip `height` wide below the bone chain (along `hang`), soft-skinned to it,
    with both faces. tail: "swallow" (a notched end), "point" or "square". A banner hanging down a wall: direction
    (0, 0, -1) and hang along the wall."""
    top, d = Vector(top), Vector(direction).normalized()
    hv = Vector(hang).normalized()
    cols = segs * 2
    k = Kit()
    bm = k[swatch + ":0.15:0.7"]
    for side, off in ((1, 0.006), (-1, -0.006)):
        nrm = d.cross(hv).normalized() * off
        rows = []
        for i in range(cols + 1):
            u = i / cols
            hh = height
            drop = 0.0
            if i == cols:
                if tail == "point":
                    hh, drop = 0.02, height * 0.5
            p = top + d * (length * u) + nrm
            rows.append((bm.verts.new(p + hv * drop), bm.verts.new(p + hv * (drop + hh))))
        for i in range(cols):
            a, b = rows[i], rows[i + 1]
            f = (a[0], b[0], b[1], a[1])
            bm.faces.new(f if side > 0 else tuple(reversed(f)))
        if tail == "swallow":
            a = rows[-1]
            midp = bm.verts.new((a[0].co + a[1].co) * 0.5 - d * (length / cols * 0.9))
            e = [bm.verts.new(a[0].co + d * (length / cols * 0.55)), bm.verts.new(a[1].co + d * (length / cols * 0.55))]
            f1, f2 = (a[0], e[0], midp), (midp, e[1], a[1])
            bm.faces.new(f1 if side > 0 else tuple(reversed(f1)))
            bm.faces.new(f2 if side > 0 else tuple(reversed(f2)))
    return k.emit(name, col, rig=rig, bones=["%s.%d" % (bone_name, i + 1) for i in range(segs)], scale=scale)


def wave_flag(rig, name, phase, amp=1.0, segs=3, axis=(0, 0, 1)):
    """Poses a flag_bones() chain for one moment of its flutter (phase 0..1 loops)."""
    pb = rig.pose.bones
    for k in range(segs):
        b = pb["%s.%d" % (name, k + 1)]
        b.rotation_quaternion = arm_space_quat(b, axis, (7.0 + 5.0 * k) * amp * math.sin(2 * math.pi * (phase - 0.13 * k)))
