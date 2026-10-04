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
from mathutils import Vector, Matrix, Euler

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
    a, b = vs[:4], vs[4:]
    bm.faces.new((a[3], a[2], a[1], a[0]))
    bm.faces.new((b[0], b[1], b[2], b[3]))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
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
    """Context for bpy.ops calls made from the MCP connector (which runs outside any editor)."""
    win = bpy.context.window_manager.windows[0]
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
    with view3d_override():
        bpy.ops.object.select_all(action="DESELECT")
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
