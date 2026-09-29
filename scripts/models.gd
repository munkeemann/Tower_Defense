class_name Models
extends RefCounted
## Builds all tower / enemy / scenery visuals out of primitive meshes.
## Swap any of these for imported .glb models later without touching gameplay.

static var _mats := {}
static var _meshes := {}


static func mat(color: Color, glow := 0.0, alpha := 1.0) -> StandardMaterial3D:
	var key := "%s|%.2f|%.2f" % [color.to_html(), glow, alpha]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color.r, color.g, color.b, alpha)
	m.roughness = 0.85
	if glow > 0.0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = glow
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mats[key] = m
	return m


static func _mi(mesh: Mesh, color: Color, pos: Vector3, glow := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat(color, glow)
	mi.position = pos
	return mi


static var _stone_mats := {}


## Painted flagstone (world-space, tiles seamlessly across neighboring pieces), tinted. Plain color if missing.
static func stone_mat(tint: Color) -> Material:
	var key := tint.to_html()
	if _stone_mats.has(key):
		return _stone_mats[key]
	var path := "res://assets/custom/textures/tex_stone.png"
	var m: StandardMaterial3D = mat(tint).duplicate() if not ResourceLoader.exists(path) else StandardMaterial3D.new()
	if ResourceLoader.exists(path):
		m.albedo_texture = load(path)
		m.albedo_color = tint
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3(0.45, 0.45, 0.45)
		m.roughness = 0.95
	_stone_mats[key] = m
	return m


static func box(size: Vector3, color: Color, pos := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	var m := BoxMesh.new()
	m.size = size
	return _mi(m, color, pos, glow)


static func cyl(top_r: float, bot_r: float, h: float, color: Color, pos := Vector3.ZERO, glow := 0.0, sides := 12) -> MeshInstance3D:
	var m := CylinderMesh.new()
	m.top_radius = top_r
	m.bottom_radius = bot_r
	m.height = h
	m.radial_segments = sides
	m.rings = 1
	return _mi(m, color, pos, glow)


static func sphere(r: float, color: Color, pos := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	var m := SphereMesh.new()
	m.radius = r
	m.height = r * 2.0
	m.radial_segments = 14
	m.rings = 8
	return _mi(m, color, pos, glow)


static func cone(r: float, h: float, color: Color, pos := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	return cyl(0.0, r, h, color, pos, glow, 10)


static func torus(inner: float, outer: float, color: Color, pos := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	var m := TorusMesh.new()
	m.inner_radius = inner
	m.outer_radius = outer
	m.rings = 20
	m.ring_segments = 8
	return _mi(m, color, pos, glow)


static func _add(parent: Node3D, child: Node3D, rot_deg := Vector3.ZERO, scl := Vector3.ONE) -> Node3D:
	child.rotation_degrees = rot_deg
	child.scale = scl
	parent.add_child(child)
	return child


# ------------------------------------------------------------------ imported assets (CC0, see assets/CREDITS.md)

const TD := "res://assets/td/"
const CASTLE := "res://assets/castle/"
const NATURE := "res://assets/nature/"
const MON := "res://assets/monsters/"
const SKEL := "res://assets/skeletons/"
const CUSTOM := "res://assets/custom/"
## Kenney tower-kit units -> world units (a tile is 2 world units wide).
const K := 1.5
## Kenney weapons point down +Z; heads are aimed down -Z.
const WEAPON_ROT := 180.0

static var _scenes := {}
static var _has_assets := -1


static func has_assets() -> bool:
	if _has_assets < 0:
		_has_assets = 1 if ResourceLoader.exists(TD + "tile.glb") and not "--noassets" in OS.get_cmdline_user_args() else 0
	return _has_assets == 1


static func asset(path: String) -> Node3D:
	if not _scenes.has(path):
		_scenes[path] = load(path) if ResourceLoader.exists(path) else null
	var ps: PackedScene = _scenes[path]
	if ps == null:
		push_warning("Missing asset: " + path)
		return null
	return ps.instantiate() as Node3D


static var _fixed_mats := {}


## Kenney's Nature Kit stores sRGB colors as linear material colors, which renders them washed out.
static func _fix_nature_colors(n: Node) -> void:
	for c in n.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		for s in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(s) as StandardMaterial3D
			if m == null:
				continue
			if not _fixed_mats.has(m):
				var f := m.duplicate() as StandardMaterial3D
				var col := m.albedo_color.srgb_to_linear()
				# nudge the kit's teal foliage toward the same warm green as the ground tiles
				if col.s > 0.3 and col.h > 0.36 and col.h < 0.56:
					col = Color.from_hsv(col.h - 0.12, col.s * 0.95, col.v, col.a)
				f.albedo_color = col
				_fixed_mats[m] = f
			mi.set_surface_override_material(s, _fixed_mats[m])


static func place(parent: Node3D, path: String, pos := Vector3.ZERO, s := 1.0, rot_y := 0.0) -> Node3D:
	var n := asset(path)
	if n == null:
		return null
	if path.begins_with(NATURE):
		_fix_nature_colors(n)
	n.position = pos
	n.scale = Vector3.ONE * s
	n.rotation_degrees.y = rot_y
	parent.add_child(n)
	return n


## Transform of the first mesh inside an imported scene relative to the scene root.
static func asset_mesh_xform(path: String) -> Transform3D:
	var key := "xf|" + path
	if _scenes.has(key):
		return _scenes[key]
	var xf := Transform3D()
	var n := asset(path)
	if n:
		for c in n.find_children("*", "MeshInstance3D", true, false):
			var p: Node = c
			while p != null and p != n:
				if p is Node3D:
					xf = (p as Node3D).transform * xf
				p = p.get_parent()
			break
		n.free()
	_scenes[key] = xf
	return xf


## First mesh found inside an imported scene (for MultiMesh use).
static func asset_mesh(path: String) -> Mesh:
	var key := "mesh|" + path
	if _scenes.has(key):
		return _scenes[key]
	var n := asset(path)
	var m: Mesh = null
	if n:
		for c in n.find_children("*", "MeshInstance3D", true, false):
			m = (c as MeshInstance3D).mesh
			break
		n.free()
	_scenes[key] = m
	return m


# ------------------------------------------------------------------ AI-generated (Meshy) models

## Bounding box of everything visible under `root`, in root's local space (works before it's in the tree).
static func _local_aabb(root: Node3D) -> AABB:
	var out := AABB()
	var first := true
	for c in root.find_children("*", "VisualInstance3D", true, false):
		var vi := c as VisualInstance3D
		var xf := Transform3D()
		var n: Node = vi
		while n != null and n != root:
			if n is Node3D:
				xf = (n as Node3D).transform * xf
			n = n.get_parent()
		var bb := xf * vi.get_aabb()
		if first:
			out = bb
			first = false
		else:
			out = out.merge(bb)
	return out


## Places assets/custom/<file>.glb scaled to fit a w-wide, h-tall box, standing at height y, centered.
## Returns the holder node (meta "height" = final height), or null if the file is missing.
static func fit(parent: Node3D, file: String, w: float, h: float, y := 0.0, rot_y := 0.0) -> Node3D:
	var path := CUSTOM + file + ".glb"
	if not ResourceLoader.exists(path):
		return null
	var n := asset(path)
	if n == null:
		return null
	var holder := Node3D.new()
	holder.add_child(n)
	var bb := _local_aabb(n)
	var s: float = minf(w / maxf(maxf(bb.size.x, bb.size.z), 0.001), h / maxf(bb.size.y, 0.001))
	var c := bb.get_center()
	n.scale = Vector3.ONE * s
	n.position = Vector3(-c.x * s, -bb.position.y * s, -c.z * s)
	holder.position.y = y
	holder.rotation_degrees.y = rot_y
	parent.add_child(holder)
	holder.set_meta("height", bb.size.y * s)
	return holder


static func _has_custom(files: Array) -> bool:
	for f in files:
		if not ResourceLoader.exists(CUSTOM + f + ".glb"):
			return false
	return true


## Meshy models face +Z (toward the default camera). Aiming heads point down -Z, so they get turned around;
## decorative bodies keep facing the camera.
const AI_FACE := 180.0

## Builds a tower from Meshy models if they exist. Returns false to fall back to the kit models.
static func _ai_tower(id: String, color: Color, root: Node3D, head: Node3D) -> bool:
	match id:
		"archer":
			if not _has_custom(["archer_tower"]): return false
			fit(root, "archer_tower", 1.7, 3.5)
			head.position = Vector3(0, 3.0, 0)
		"ballista":
			if not _has_custom(["siege_base", "ballista_head"]): return false
			fit(root, "siege_base", 1.85, 0.8)
			head.position = Vector3(0, 0.72, 0)
			fit(head, "ballista_head", 1.7, 1.1, 0.0, AI_FACE)
		"bombard":
			if not _has_custom(["siege_base", "cannon_head"]): return false
			fit(root, "siege_base", 1.85, 0.8)
			head.position = Vector3(0, 0.72, 0)
			fit(head, "cannon_head", 1.6, 1.2, 0.0, AI_FACE)
		"trebuchet":
			if not _has_custom(["siege_base", "trebuchet"]): return false
			fit(root, "siege_base", 1.9, 0.6)
			head.position = Vector3(0, 0.52, 0)
			fit(head, "trebuchet", 1.85, 2.4, 0.0, AI_FACE)
		"arcane":
			if not _has_custom(["arcane_spire"]): return false
			fit(root, "arcane_spire", 1.4, 3.7)
			head.position = Vector3(0, 4.0, 0)
			_add(head, sphere(0.26, color, Vector3.ZERO, 2.5))
			_add(head, torus(0.36, 0.43, color, Vector3.ZERO, 1.5), Vector3(70, 0, 0))
		"chapel":
			if not _has_custom(["chapel"]): return false
			fit(root, "chapel", 1.85, 2.9)
			head.position = Vector3(0, 3.5, 0)
			_add(head, torus(0.26, 0.33, color, Vector3.ZERO, 3.0), Vector3(90, 0, 0))
			_add(head, sphere(0.12, color, Vector3.ZERO, 3.0))
		"banner":
			if not _has_custom(["war_banner"]): return false
			fit(root, "war_banner", 1.6, 3.4)
			head.position = Vector3(0, 2.6, 0)
		"gryphon":
			if not _has_custom(["gryphon_roost", "gryphon"]): return false
			var roost := fit(root, "gryphon_roost", 1.6, 3.2)
			head.position = Vector3(0, float(roost.get_meta("height")) * 0.72, 0)
			fit(head, "gryphon", 1.5, 1.1, 0.0, AI_FACE)
		"thorn":
			if not _has_custom(["thornspitter"]): return false
			head.position = Vector3(0, 1.3, 0)
			fit(head, "thornspitter", 1.6, 2.0, -1.3, AI_FACE)
		"spore":
			if not _has_custom(["spore_mound"]): return false
			fit(root, "spore_mound", 1.85, 1.9)
			head.position = Vector3(0, 1.4, 0)
		"briar":
			if not _has_custom(["briar_thicket"]): return false
			fit(root, "briar_thicket", 1.95, 1.4)
			head.position = Vector3(0, 0.6, 0)
		"treant":
			if not _has_custom(["treant"]): return false
			head.position = Vector3(0, 1.5, 0)
			fit(head, "treant", 1.8, 3.1, -1.5, AI_FACE)
		"storm":
			if not _has_custom(["storm_oak"]): return false
			fit(root, "storm_oak", 1.95, 3.5)
			head.position = Vector3(0, 3.9, 0)
			_add(head, sphere(0.22, color, Vector3.ZERO, 3.0))
			_add(head, torus(0.3, 0.36, color, Vector3.ZERO, 2.0), Vector3(90, 0, 0))
		"hive":
			if not _has_custom(["wasp_hive"]): return false
			fit(root, "wasp_hive", 1.7, 2.7)
			head.position = Vector3(0, 1.4, 0)
		"rootbinder":
			if not _has_custom(["rootbinder_shrine"]): return false
			fit(root, "rootbinder_shrine", 1.9, 2.2)
			head.position = Vector3(0, 2.6, 0)
			_add(head, sphere(0.16, color, Vector3.ZERO, 2.5))
			_add(head, torus(0.24, 0.29, color, Vector3.ZERO, 1.5), Vector3(90, 0, 0))
		_:
			return false
	return true


## Footprint-sized Meshy models for multi-hex towers: [file, yaw in degrees (multiple of 90) that turns the
## model's front toward -Z, height cap, how far it may be widened to fill the footprint]. Each is fitted to the
## whole footprint, not a single hex.
static var _rim_mats := {}
static var _foe_mat: ShaderMaterial


## A soft rim light in a color's accent (overlay for the player's towers).
static func rim_mat(c: Color) -> ShaderMaterial:
	var key := c.to_html()
	if not _rim_mats.has(key):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/rim.gdshader")
		m.set_shader_parameter("rim_col", Vector3(c.r, c.g, c.b))
		_rim_mats[key] = m
	return _rim_mats[key]


## Darker bodies with a hot rim (overlay for enemies).
static func foe_mat() -> ShaderMaterial:
	if _foe_mat == null:
		_foe_mat = ShaderMaterial.new()
		_foe_mat.shader = load("res://shaders/foe.gdshader")
	return _foe_mat


## Puts an overlay material on every mesh under n.
static func overlay(n: Node, m: Material) -> void:
	if n is MeshInstance3D:
		(n as MeshInstance3D).material_overlay = m
	for ch in n.get_children():
		overlay(ch, m)


## Footprint-shaped Meshy models, second set (fp2_*): each multi-hex tower is one model made to fill its footprint's
## silhouette (seen from above), so the tower itself covers every hex it stands on. [file, yaw in degrees (multiple of
## 90) that turns the model's front toward -Z, height cap, how far one axis may be stretched to fill the footprint].
## Set FOOTPRINT_ART_V2 to false to go back to the first set (FOOTPRINT_ART_V1); towers missing a v2 file use v1.
const FOOTPRINT_ART_V2 := true
const FOOTPRINT_ART := {
	"ballista": ["fp2_ballista", 270.0, 4.5, 1.3],
	"trebuchet": ["fp2_trebuchet", 270.0, 4.5, 1.3],
	"bombard": ["fp2_bombard", 0.0, 4.5, 1.3],
	"gryphon": ["fp2_gryphon", 0.0, 4.5, 1.3],
	"arcane": ["fp2_arcane", 90.0, 4.5, 1.3],
	"chapel": ["fp2_chapel", 0.0, 4.5, 1.3],
	"spore": ["fp2_spore", 90.0, 4.5, 1.3],
	"briar": ["fp2_briar", 90.0, 4.5, 1.3],
	"treant": ["fp2_treant", 180.0, 4.5, 1.3],
	"storm": ["fp2_storm", 0.0, 4.5, 1.3],
	"hive": ["fp2_hive", 90.0, 4.5, 1.3],
	"rootbinder": ["fp2_rootbinder", 0.0, 4.5, 1.3],
	"dwarf_flame": ["fp2_dwarf_flame", 270.0, 4.5, 1.3],
	"dwarf_hammer": ["fp2_dwarf_hammer", 0.0, 4.5, 1.3],
	"dwarf_mortar": ["fp2_dwarf_mortar", 270.0, 4.5, 1.3],
	"dwarf_gyro": ["fp2_dwarf_gyro", 180.0, 4.5, 1.3],
	"mer_harpoon": ["fp2_mer_harpoon", 270.0, 4.5, 1.3],
	"mer_whirl": ["fp2_mer_whirl", 180.0, 4.5, 1.3],
	"mer_siren": ["fp2_mer_siren", 0.0, 4.5, 1.3],
	"plague_cauldron": ["fp2_plague_cauldron", 180.0, 4.5, 1.3],
	"soul_obelisk": ["fp2_soul_obelisk", 0.0, 4.5, 1.3],
	"hex_tomb": ["fp2_hex_tomb", 180.0, 4.5, 1.3],
}
const FOOTPRINT_ART_V1 := {
	"ballista": ["fp_ballista", 270.0, 2.6, 1.15],
	"gryphon": ["fp_gryphon", 0.0, 3.4, 1.0],
	"trebuchet": ["fp_trebuchet", 90.0, 4.2, 1.25],
	"bombard": ["fp_bombard", 180.0, 3.0, 1.0],
	"briar": ["fp_briar", 90.0, 1.8, 1.9],
	"rootbinder": ["fp_rootbinder", 0.0, 4.2, 1.0],
	"dwarf_flame": ["fp_dwarf_flame", 270.0, 2.6, 1.0],
	"dwarf_hammer": ["fp_dwarf_hammer", 0.0, 3.4, 1.0],
	"dwarf_mortar": ["fp_dwarf_mortar", 0.0, 3.2, 1.0],
	"dwarf_gyro": ["fp_dwarf_gyro", 0.0, 3.0, 1.0],
	"mer_tide": ["fp_mer_tide", 0.0, 3.2, 1.0],
	"mer_harpoon": ["fp_mer_harpoon", 270.0, 2.8, 1.0],
	"mer_whirl": ["fp_mer_whirl", 0.0, 2.8, 1.0],
	"mer_siren": ["fp_mer_siren", 0.0, 3.4, 1.0],
	"bone_crypt": ["fp_bone_crypt", 0.0, 2.8, 1.0],
	"plague_cauldron": ["fp_plague_cauldron", 0.0, 2.8, 1.0],
	"soul_obelisk": ["fp_soul_obelisk", 0.0, 3.6, 1.0],
	"hex_tomb": ["fp_hex_tomb", 0.0, 3.0, 1.0],
}
## Props that fill footprint hexes the main model leaves bare: [cell (facing north), prop file, width, height].
const FOOTPRINT_EXTRAS := {
	"trebuchet": [[[1, 0], "prop_rock", 1.5, 0.8], [[-1, 1], "prop_rock", 1.5, 0.8]],
}


## A tower's footprint drawn facing north (-Z), as an XZ rectangle relative to the footprint's middle
## (the mean of its hex centers, which is where the Tower node sits).
static func footprint_box(id: String) -> Rect2:
	var cells: Array = GameData.shape_of(id)["cells"]
	var mid := Vector3.ZERO
	for c in cells:
		mid += Hex.to_world(Vector2i(c[0], c[1]))
	mid /= float(cells.size())
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for c in cells:
		var w := Hex.to_world(Vector2i(c[0], c[1])) - mid
		lo = Vector2(minf(lo.x, w.x - Hex.R), minf(lo.y, w.z - Hex.SQ3 * Hex.R * 0.5))
		hi = Vector2(maxf(hi.x, w.x + Hex.R), maxf(hi.y, w.z + Hex.SQ3 * Hex.R * 0.5))
	return Rect2(lo, hi - lo)


## The footprint art a tower uses (v2 when it exists), or [] for none.
static func footprint_art(id: String) -> Array:
	if FOOTPRINT_ART_V2 and FOOTPRINT_ART.has(id) and _has_custom([FOOTPRINT_ART[id][0]]):
		return FOOTPRINT_ART[id]
	if FOOTPRINT_ART_V1.has(id) and _has_custom([FOOTPRINT_ART_V1[id][0]]):
		return FOOTPRINT_ART_V1[id]
	return []


static func _fp_tower(id: String, root: Node3D, head: Node3D) -> bool:
	var art: Array = footprint_art(id)
	if art.is_empty():
		return false
	var v2 := String(art[0]).begins_with("fp2_")
	var n := asset(CUSTOM + art[0] + ".glb")
	if n == null:
		return false
	var spin := Node3D.new()
	spin.add_child(n)
	var yaw: float = art[1]
	spin.rotation_degrees.y = yaw
	var bb := _local_aabb(n)
	var turned := posmod(int(round(yaw / 90.0)), 2) == 1
	var wx := bb.size.z if turned else bb.size.x
	var wz := bb.size.x if turned else bb.size.z
	var box := footprint_box(id)
	var sc: float = minf(minf(box.size.x * 0.97 / maxf(wx, 0.001), box.size.y * 0.97 / maxf(wz, 0.001)), float(art[2]) / maxf(bb.size.y, 0.001))
	var c := bb.get_center()
	# stretch toward the footprint's full width (v1: across the facing only; v2: whichever axis has room too)
	var widen: float = clampf(box.size.x * 0.95 / maxf(wx * sc, 0.001), 1.0, float(art[3]))
	var deepen: float = clampf(box.size.y * 0.95 / maxf(wz * sc, 0.001), 1.0, float(art[3])) if v2 else 1.0
	n.scale = Vector3(sc * deepen, sc, sc * widen) if turned else Vector3(sc * widen, sc, sc * deepen)
	n.position = Vector3(-c.x * n.scale.x, -bb.position.y * sc + 0.1, -c.z * n.scale.z)
	var ctr := box.get_center()
	spin.position = Vector3(ctr.x, 0, ctr.y)
	root.add_child(spin)
	root.set_meta("fitted", true)
	var mid := Vector3.ZERO
	var cells: Array = GameData.shape_of(id)["cells"]
	for cc in cells:
		mid += Hex.to_world(Vector2i(cc[0], cc[1]))
	mid /= float(cells.size())
	for ex in ([] if v2 else FOOTPRINT_EXTRAS.get(id, [])):
		var holder := fit(root, ex[1], ex[2], ex[3])
		if holder:
			var at := Hex.to_world(Vector2i(ex[0][0], ex[0][1])) - mid
			holder.position = Vector3(at.x, 0.1, at.z)
	head.position = Vector3(0, bb.size.y * sc * 0.6, 0)   # the tower fires from above its centroid
	return true


## Returns {"root": Node3D, "head": Node3D}. The head is rotated toward targets (-Z forward).
## Multi-hex towers with footprint art come back with root meta "fitted" (already sized to the footprint).
static func tower(id: String, color: Color) -> Dictionary:
	if not has_assets():
		return _proc_tower(id, color)
	var root := Node3D.new()
	var head := Node3D.new()
	root.add_child(head)
	if _fp_tower(id, root, head):
		return {"root": root, "head": head}
	if _ai_tower(id, color, root, head):
		return {"root": root, "head": head}
	var ok := true
	match id:
		# ---------------- Crown: Kenney stone towers + weapons
		"archer":
			_stack(root, ["tower-round-bottom-a", "tower-round-middle-a", "tower-round-top-a"])
			head.position = Vector3(0, 1.7 * K + 0.1, 0)
			place(head, TD + "weapon-ballista.glb", Vector3.ZERO, 1.2, WEAPON_ROT)
		"ballista":
			place(root, TD + "tower-square-bottom-a.glb", Vector3.ZERO, K)
			place(root, TD + "tower-square-top-a.glb", Vector3(0, 0.5 * K, 0), K)
			head.position = Vector3(0, 1.0 * K + 0.1, 0)
			place(head, TD + "weapon-ballista.glb", Vector3.ZERO, 2.0, WEAPON_ROT)
		"arcane":
			_stack(root, ["tower-round-bottom-b", "tower-round-middle-c"])
			place(root, TD + "tower-round-crystals.glb", Vector3(0, 1.2 * K, 0), K)
			head.position = Vector3(0, 1.2 * K + 1.6, 0)
			_add(head, sphere(0.3, color, Vector3.ZERO, 2.5))
			_add(head, torus(0.42, 0.5, color, Vector3.ZERO, 1.5), Vector3(70, 0, 0))
		"trebuchet":
			place(root, TD + "tower-round-base.glb", Vector3.ZERO, K * 1.2)
			head.position = Vector3(0, 0.3, 0)
			place(head, CASTLE + "siege-trebuchet.glb", Vector3.ZERO, 1.05, -90.0)
		"chapel":
			place(root, CASTLE + "tower-square-base.glb", Vector3.ZERO, 1.25)
			place(root, CASTLE + "tower-square-mid-windows.glb", Vector3(0, 1.26, 0), 1.25)
			place(root, CASTLE + "tower-square-top-roof-high.glb", Vector3(0, 2.52, 0), 1.25)
			head.position = Vector3(0, 4.5, 0)
			_add(head, torus(0.3, 0.38, color, Vector3.ZERO, 3.0), Vector3(90, 0, 0))
			_add(head, sphere(0.14, color, Vector3.ZERO, 3.0))
		"banner":
			place(root, TD + "tower-round-base.glb", Vector3.ZERO, K)
			place(root, TD + "tower-round-bottom-c.glb", Vector3(0, 0.2 * K, 0), K * 0.8)
			head.position = Vector3(0, 0.95, 0)
			place(head, CASTLE + "flag-banner-long.glb", Vector3.ZERO, 1.35)
			_add(head, sphere(0.12, GOLD, Vector3(0, 3.0, 0), 1.0))
		"gryphon":
			_stack(root, ["tower-round-bottom-c", "tower-round-middle-c", "tower-round-middle-a", "tower-round-top-c"])
			head.position = Vector3(0, 2.3 * K + 0.1, 0)
			_add(head, sphere(0.3, color, Vector3(0, 0.25, 0)), Vector3.ZERO, Vector3(1, 0.9, 1.3))
			_add(head, sphere(0.18, Color(0.95, 0.95, 0.9), Vector3(0, 0.5, -0.35)))
			_add(head, cone(0.07, 0.2, GOLD, Vector3(0, 0.48, -0.55)), Vector3(-90, 0, 0))
			_add(head, box(Vector3(1.4, 0.05, 0.4), color.darkened(0.2), Vector3(0, 0.4, 0.05)), Vector3(0, 0, 12))
		"bombard":
			place(root, TD + "tower-round-bottom-c.glb", Vector3.ZERO, K * 1.1)
			place(root, TD + "tower-round-top-b.glb", Vector3(0, 0.6 * K * 1.1, 0), K * 1.1)
			head.position = Vector3(0, 0.66 * K * 1.1 + 0.15, 0)
			place(head, TD + "weapon-cannon.glb", Vector3.ZERO, 2.0, WEAPON_ROT)
		# ---------------- Verdant: Kenney nature pieces + glowing magic
		"thorn":
			place(root, NATURE + "plant_bushDetailed.glb", Vector3.ZERO, 2.6)
			_add(root, cyl(0.1, 0.16, 1.0, Color(0.3, 0.5, 0.2), Vector3(0, 0.6, 0)))
			head.position = Vector3(0, 1.3, 0)
			_add(head, sphere(0.36, color, Vector3.ZERO))
			for i in 6:
				var a := TAU * i / 6.0
				_add(head, cone(0.08, 0.35, Color(0.95, 0.9, 0.65), Vector3(cos(a) * 0.34, 0.05, sin(a) * 0.34)), Vector3(0, -rad_to_deg(a), -90))
			_add(head, cyl(0.12, 0.15, 0.3, Color(0.8, 0.3, 0.3), Vector3(0, 0.05, -0.38)), Vector3(-90, 0, 0))
		"spore":
			place(root, NATURE + "mushroom_tanGroup.glb", Vector3(0.1, 0, 0.1), 5.0)
			place(root, NATURE + "mushroom_redGroup.glb", Vector3(-0.2, 0, -0.1), 4.0, 120.0)
			head.position = Vector3(0, 0.05, 0)
			place(head, NATURE + "mushroom_redTall.glb", Vector3.ZERO, 7.0)
		"briar":
			for i in 5:
				var a := TAU * i / 5.0
				place(root, NATURE + "plant_bushLargeTriangle.glb", Vector3(cos(a) * 0.45, 0, sin(a) * 0.45), 2.4, rad_to_deg(a) * 2.0)
			place(root, NATURE + "plant_bushDetailed.glb", Vector3.ZERO, 2.0)
			for i in 6:
				var a := TAU * i / 6.0 + 0.3
				_add(root, cone(0.07, 0.6, Color(0.35, 0.22, 0.12), Vector3(cos(a) * 0.5, 0.45, sin(a) * 0.5)), Vector3(randf_range(-20, 20), 0, randf_range(-20, 20)))
			_add(root, sphere(0.09, Color(0.9, 0.15, 0.2), Vector3(0.25, 0.75, 0.1), 0.8))
			_add(root, sphere(0.09, Color(0.9, 0.15, 0.2), Vector3(-0.3, 0.65, -0.2), 0.8))
			head.position = Vector3(0, 0.5, 0)
		"treant":
			place(root, NATURE + "stump_roundDetailed.glb", Vector3.ZERO, 4.0)
			place(root, NATURE + "tree_oak.glb", Vector3(0, 0.3, 0), 2.3)
			head.position = Vector3(0, 1.3, 0)
			_add(head, box(Vector3(0.2, 1.0, 0.2), BARK, Vector3(-0.55, 0, -0.1)), Vector3(0, 0, 30))
			_add(head, box(Vector3(0.2, 1.0, 0.2), BARK, Vector3(0.55, 0, -0.1)), Vector3(0, 0, -30))
			_add(head, sphere(0.08, Color(1, 0.9, 0.3), Vector3(-0.13, 0.35, -0.3), 2.5))
			_add(head, sphere(0.08, Color(1, 0.9, 0.3), Vector3(0.13, 0.35, -0.3), 2.5))
		"storm":
			place(root, NATURE + "stump_roundDetailed.glb", Vector3.ZERO, 3.0)
			place(root, NATURE + "tree_detailed_dark.glb", Vector3(0, 0.2, 0), 2.4)
			head.position = Vector3(0, 3.9, 0)
			_add(head, sphere(0.22, color, Vector3.ZERO, 3.0))
			_add(head, torus(0.3, 0.36, color, Vector3.ZERO, 2.0), Vector3(90, 0, 0))
		"hive":
			place(root, NATURE + "stump_oldTall.glb", Vector3.ZERO, 2.6)
			head.position = Vector3(0, 1.75, 0)
			for i in 4:
				var c := color if i % 2 == 0 else Color(0.35, 0.22, 0.1)
				_add(head, sphere(0.42 - i * 0.06, c, Vector3(0, 0.45 - i * 0.26, 0)), Vector3.ZERO, Vector3(1, 0.6, 1))
			_add(head, sphere(0.09, Color(0.1, 0.05, 0.02), Vector3(0, 0.2, -0.36)))
		"moonwell" when ResourceLoader.exists(CUSTOM + "moonwell_meshy.glb"):
			# AI-generated with Meshy (assets/custom). Model is centered, so lift it onto the ground.
			place(root, CUSTOM + "moonwell_meshy.glb", Vector3(0, 0.77 * 0.95, 0), 0.95)
			head.position = Vector3(0, 2.0, 0)
			_add(head, sphere(0.1, color, Vector3(0.35, 0, 0), 2.5))
			_add(head, sphere(0.08, color, Vector3(-0.3, 0.15, 0.2), 2.5))
		"moonwell":
			for i in 5:
				var a := TAU * i / 5.0
				place(root, NATURE + "rock_tallA.glb", Vector3(cos(a) * 0.72, 0, sin(a) * 0.72), 0.55, rad_to_deg(a))
			_add(root, cyl(0.6, 0.6, 0.1, color.darkened(0.2), Vector3(0, 0.12, 0), 0.5))
			head.position = Vector3(0, 1.7, 0)
			_add(head, sphere(0.28, Color(0.9, 0.95, 1.0), Vector3.ZERO, 2.0))
			_add(head, torus(0.4, 0.45, color, Vector3.ZERO, 1.5), Vector3(80, 0, 0))
		"rootbinder":
			place(root, NATURE + "rock_tallC.glb", Vector3.ZERO, 1.2)
			place(root, NATURE + "stump_oldTall.glb", Vector3(0.45, 0, 0.3), 1.8, 40.0)
			place(root, NATURE + "stump_oldTall.glb", Vector3(-0.45, 0, -0.2), 1.6, 200.0)
			head.position = Vector3(0, 1.75, 0)
			_add(head, sphere(0.25, color, Vector3.ZERO, 2.5))
			_add(head, torus(0.34, 0.4, color, Vector3.ZERO, 1.5), Vector3(90, 0, 0))
		_:
			ok = false
	if not ok:
		root.free()
		return _proc_tower(id, color)
	return {"root": root, "head": head}


static func _stack(root: Node3D, parts: Array) -> void:
	var y := 0.0
	for p in parts:
		place(root, TD + p + ".glb", Vector3(0, y, 0), K)
		y += (0.5 if String(p).contains("-top-") else 0.6) * K


## Enemy art: model file, scale, and animation names. Quaternius/KayKit models face +Z.
const ENEMY_ART := {
	"goblin": {"path": MON + "blob_Orc.gltf", "scale": 0.5, "walk": "Walk", "death": "Death"},
	"wolf": {"path": MON + "blob_Dog.gltf", "scale": 0.55, "walk": "Walk", "death": "Death"},
	"orc": {"path": MON + "big_Orc.gltf", "scale": 0.55, "walk": "Walk", "death": "Death"},
	"harpy": {"path": MON + "fly_Hywirl.gltf", "scale": 0.45, "walk": "Fast_Flying", "death": "Death"},
	"slime": {"path": MON + "blob_GreenBlob.gltf", "scale": 0.6, "walk": "Walk", "death": "Death"},
	"slimelet": {"path": MON + "blob_GreenBlob.gltf", "scale": 0.33, "walk": "Walk", "death": "Death"},
	"shaman": {"path": MON + "blob_Wizard.gltf", "scale": 0.5, "walk": "Walk", "death": "Death"},
	"hexguard": {"path": MON + "big_Demon.gltf", "scale": 0.52, "walk": "Walk", "death": "Death"},
	"ironclad": {"path": MON + "big_Orc_Skull.gltf", "scale": 0.58, "walk": "Walk", "death": "Death"},
	"skeleton": {"path": SKEL + "Skeleton_Minion.glb", "scale": 0.62, "walk": "Walking_D_Skeletons", "death": "Death_A"},
	"wasp": {"path": MON + "fly_Armabee.gltf", "scale": 0.5, "walk": "Fast_Flying", "death": "Death", "y": -0.6},
	"gargoyle": {"path": MON + "fly_Goleling_Evolved.gltf", "scale": 0.6, "walk": "Flying_Idle", "death": "Death", "y": -0.75},
	"spikeback": {"path": MON + "blob_GreenSpikyBlob.gltf", "scale": 0.42, "walk": "Walk", "death": "Death"},
	"frostimp": {"path": MON + "big_BlueDemon.gltf", "scale": 0.48, "walk": "Run", "death": "Death"},
	"troll": {"path": MON + "big_Yeti.gltf", "scale": 1.1, "walk": "Walk", "death": "Death"},
	"dragon": {"path": MON + "fly_Dragon_Evolved.gltf", "scale": 1.05, "walk": "Flying_Idle", "death": "Death"},
	"lich": {"path": SKEL + "Skeleton_Mage.glb", "scale": 1.35, "walk": "Walking_A", "death": "Death_A"},
}


## Enemies with AI-generated, auto-rigged models (assets/custom/<name>_walk.glb + <name>_death.glb).
const ENEMY_AI := {
	"goblin": "goblin", "orc": "orc_brute", "shaman": "goblin_shaman", "hexguard": "hexguard",
	"ironclad": "ironclad", "frostimp": "frost_imp", "skeleton": "skeleton", "troll": "frost_troll",
	"lich": "lich_king",
}
## height_meters each was rigged at (see assets/custom/manifest.json)
const RIG_HEIGHT := {
	"goblin": 1.1, "orc_brute": 2.0, "goblin_shaman": 1.2, "hexguard": 1.9, "ironclad": 2.0,
	"frost_imp": 1.3, "skeleton": 1.6, "frost_troll": 3.0, "lich_king": 2.6,
}
static var _death_anims := {}


static func _first_anim(ap: AnimationPlayer) -> String:
	for a in ap.get_animation_list():
		if a != "RESET":
			return a
	return ""


## Copies the death clip from <name>_death.glb into this model's AnimationPlayer as "ai/death".
static func _add_death(ap: AnimationPlayer, name: String) -> String:
	if not _death_anims.has(name):
		var anim: Animation = null
		var path := CUSTOM + name + "_death.glb"
		if ResourceLoader.exists(path):
			var n := asset(path)
			var dap: AnimationPlayer = null
			if n:
				dap = n.find_child("AnimationPlayer", true, false) as AnimationPlayer
			if dap and _first_anim(dap) != "":
				anim = dap.get_animation(_first_anim(dap)).duplicate() as Animation
				anim.loop_mode = Animation.LOOP_NONE
			if n:
				n.free()
		_death_anims[name] = anim
	var a: Animation = _death_anims[name]
	if a == null:
		return ""
	if not ap.has_animation_library("ai"):
		ap.add_animation_library("ai", AnimationLibrary.new())
	var lib := ap.get_animation_library("ai")
	if not lib.has_animation("death"):
		lib.add_animation("death", a)
	return "ai/death"


static func _ai_enemy(id: String, d: Dictionary) -> Dictionary:
	var name: String = ENEMY_AI.get(id, "")
	if name == "" or not _has_custom([name + "_walk"]):
		return {}
	var root := Node3D.new()
	var body := Node3D.new()
	root.add_child(body)
	# Rigged models come back at the real-world height we asked Meshy for (skinned meshes don't
	# report reliable bounds before posing), so scale from that instead of measuring.
	var holder := asset(CUSTOM + name + "_walk.glb")
	holder.scale = Vector3.ONE * float(d.get("h", 1.5)) / float(RIG_HEIGHT.get(name, 1.7))
	holder.rotation_degrees.y = AI_FACE
	body.add_child(holder)
	var ap := holder.find_child("AnimationPlayer", true, false) as AnimationPlayer
	var walk := ""
	var death := ""
	if ap:
		walk = _first_anim(ap)
		if walk != "":
			ap.get_animation(walk).loop_mode = Animation.LOOP_LINEAR
			ap.play(walk)
			ap.seek(randf() * 0.8, true)
		death = _add_death(ap, name)
	return {"root": root, "body": body, "anim": ap, "walk": walk, "death": death}


## Returns {"root", "body", "anim": AnimationPlayer or null, "walk", "death"}.
static func enemy(id: String, d: Dictionary) -> Dictionary:
	if has_assets():
		var ai := _ai_enemy(id, d)
		if not ai.is_empty():
			return ai
	if has_assets() and ENEMY_ART.has(id):
		var art: Dictionary = ENEMY_ART[id]
		var model := asset(art["path"])
		if model:
			var root := Node3D.new()
			var body := Node3D.new()
			root.add_child(body)
			body.add_child(model)
			model.rotation_degrees.y = 180.0
			model.scale = Vector3.ONE * float(art["scale"])
			model.position.y = float(art.get("y", 0.0))
			var ap := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
			if ap:
				for a in [art["walk"], art["death"]]:
					if ap.has_animation(a):
						ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a == art["walk"] else Animation.LOOP_NONE
				if ap.has_animation(art["walk"]):
					ap.play(art["walk"])
					ap.seek(randf() * 0.8, true)
			return {"root": root, "body": body, "anim": ap, "walk": art["walk"], "death": art["death"]}
	var p := _proc_enemy(id, d)
	p["anim"] = null
	return p


static func castle() -> Node3D:
	if not has_assets():
		return _proc_castle()
	var n := Node3D.new()
	if fit(n, "castle", 3.8, 4.8):
		return n
	var s := 1.35
	place(n, CASTLE + "tower-square-base.glb", Vector3.ZERO, s * 1.2)
	place(n, CASTLE + "tower-square-mid-windows.glb", Vector3(0, 1.01 * s * 1.2, 0), s * 1.2)
	place(n, CASTLE + "tower-square-top-roof-high.glb", Vector3(0, 2.02 * s * 1.2, 0), s * 1.2)
	var o := 1.15
	for x in [-o, o]:
		for z in [-o, o]:
			place(n, CASTLE + "tower-hexagon-base.glb", Vector3(x, 0, z), s * 0.9)
			place(n, CASTLE + "tower-hexagon-roof.glb", Vector3(x, 1.31 * s * 0.9, z), s * 0.9)
	for side in 4:
		var a := side * 90.0
		var dir := Vector3(sin(deg_to_rad(a)), 0, cos(deg_to_rad(a)))
		place(n, CASTLE + "wall-half.glb", dir * o, s * 0.85, a)
	place(n, CASTLE + "flag.glb", Vector3(0, 4.4 * 1.0 + 0.9, 0), 1.6)
	return n


# ------------------------------------------------------------------ procedural towers

const STONE := Color(0.62, 0.62, 0.66)
const DARK_STONE := Color(0.42, 0.42, 0.46)
const WOOD := Color(0.5, 0.34, 0.2)
const GOLD := Color(0.95, 0.78, 0.3)
const BARK := Color(0.4, 0.27, 0.16)
const LEAF := Color(0.3, 0.6, 0.25)

## Returns {"root": Node3D, "head": Node3D}. The head is rotated toward targets.
static func _proc_tower(id: String, color: Color) -> Dictionary:
	var root := Node3D.new()
	var head := Node3D.new()
	match id:
		"archer":
			_add(root, cyl(0.55, 0.7, 1.6, STONE, Vector3(0, 0.8, 0)))
			_add(root, cyl(0.72, 0.72, 0.25, DARK_STONE, Vector3(0, 1.72, 0)))
			head.position = Vector3(0, 1.85, 0)
			_add(head, box(Vector3(0.25, 0.4, 0.25), color, Vector3(0, 0.2, 0)))
			_add(head, box(Vector3(0.9, 0.08, 0.08), WOOD, Vector3(0, 0.3, -0.25)))
			_add(root, cone(0.5, 0.6, color, Vector3(0, 2.75, 0)))
			_add(root, cyl(0.03, 0.03, 0.5, WOOD, Vector3(0, 2.45, 0)))
		"ballista":
			_add(root, box(Vector3(1.3, 0.5, 1.3), WOOD, Vector3(0, 0.25, 0)))
			_add(root, cyl(0.3, 0.4, 0.4, DARK_STONE, Vector3(0, 0.7, 0)))
			head.position = Vector3(0, 0.95, 0)
			_add(head, box(Vector3(0.18, 0.18, 1.7), WOOD, Vector3(0, 0, -0.1)))
			_add(head, box(Vector3(1.5, 0.1, 0.12), color.darkened(0.2), Vector3(0, 0.05, -0.65)))
			_add(head, box(Vector3(0.07, 0.07, 1.2), Color(0.8, 0.8, 0.8), Vector3(0, 0.12, -0.4)))
		"arcane":
			_add(root, cyl(0.35, 0.65, 2.2, Color(0.35, 0.3, 0.5), Vector3(0, 1.1, 0)))
			_add(root, torus(0.35, 0.5, GOLD, Vector3(0, 2.2, 0)))
			head.position = Vector3(0, 2.75, 0)
			_add(head, sphere(0.32, color, Vector3.ZERO, 2.5))
			_add(head, torus(0.45, 0.52, color, Vector3.ZERO, 1.5), Vector3(70, 0, 0))
		"trebuchet":
			_add(root, box(Vector3(1.4, 0.3, 1.4), WOOD, Vector3(0, 0.15, 0)))
			head.position = Vector3(0, 0.3, 0)
			_add(head, box(Vector3(0.15, 1.3, 0.15), WOOD, Vector3(-0.45, 0.65, 0)))
			_add(head, box(Vector3(0.15, 1.3, 0.15), WOOD, Vector3(0.45, 0.65, 0)))
			_add(head, box(Vector3(0.12, 0.12, 2.2), WOOD.lightened(0.15), Vector3(0, 1.3, 0.1)), Vector3(-30, 0, 0))
			_add(head, box(Vector3(0.45, 0.45, 0.45), DARK_STONE, Vector3(0, 0.75, 0.9)))
			_add(head, sphere(0.2, STONE, Vector3(0, 1.95, -0.9)))
		"chapel":
			_add(root, box(Vector3(1.2, 1.2, 1.2), Color(0.92, 0.9, 0.84), Vector3(0, 0.6, 0)))
			_add(root, cone(0.95, 0.9, GOLD, Vector3(0, 1.65, 0)))
			_add(root, box(Vector3(0.35, 0.6, 0.05), Color(0.3, 0.5, 0.9), Vector3(0, 0.55, -0.61), 0.8))
			head.position = Vector3(0, 2.5, 0)
			_add(head, torus(0.3, 0.38, color, Vector3.ZERO, 3.0), Vector3(90, 0, 0))
			_add(head, sphere(0.14, color, Vector3.ZERO, 3.0))
		"banner":
			_add(root, cyl(0.6, 0.7, 0.3, DARK_STONE, Vector3(0, 0.15, 0)))
			_add(root, cyl(0.05, 0.05, 2.8, WOOD, Vector3(0, 1.5, 0)))
			_add(root, sphere(0.1, GOLD, Vector3(0, 2.95, 0), 1.0))
			head.position = Vector3(0, 2.3, 0)
			_add(head, box(Vector3(0.9, 1.0, 0.04), color, Vector3(0.47, -0.2, 0)))
			_add(head, box(Vector3(0.3, 0.3, 0.05), GOLD, Vector3(0.47, -0.1, 0), 0.5))
		"gryphon":
			_add(root, cyl(0.45, 0.6, 2.0, STONE, Vector3(0, 1.0, 0)))
			_add(root, torus(0.35, 0.6, WOOD, Vector3(0, 2.05, 0)))
			head.position = Vector3(0, 2.3, 0)
			_add(head, sphere(0.3, color, Vector3(0, 0.1, 0)), Vector3.ZERO, Vector3(1, 0.9, 1.3))
			_add(head, sphere(0.18, Color(0.95, 0.95, 0.9), Vector3(0, 0.35, -0.35)))
			_add(head, cone(0.07, 0.2, GOLD, Vector3(0, 0.33, -0.55)), Vector3(-90, 0, 0))
			_add(head, box(Vector3(1.4, 0.05, 0.4), color.darkened(0.2), Vector3(0, 0.25, 0.05)), Vector3(0, 0, 12))
		"bombard":
			_add(root, cyl(0.75, 0.8, 0.7, DARK_STONE, Vector3(0, 0.35, 0), 0.0, 8))
			head.position = Vector3(0, 0.9, 0)
			_add(head, cyl(0.3, 0.35, 0.4, WOOD, Vector3(0, -0.05, 0)))
			_add(head, cyl(0.2, 0.26, 1.2, Color(0.18, 0.18, 0.2), Vector3(0, 0.25, -0.4)), Vector3(-70, 0, 0))
			_add(head, torus(0.18, 0.26, GOLD, Vector3(0, 0.45, -0.95)), Vector3(20, 0, 0))
		"thorn":
			_add(root, cyl(0.1, 0.18, 1.2, Color(0.3, 0.5, 0.2), Vector3(0, 0.6, 0)))
			_add(root, sphere(0.35, LEAF.darkened(0.2), Vector3(0, 0.15, 0)), Vector3.ZERO, Vector3(1.5, 0.5, 1.5))
			head.position = Vector3(0, 1.4, 0)
			_add(head, sphere(0.38, color, Vector3.ZERO))
			for i in 6:
				var a := TAU * i / 6.0
				_add(head, cone(0.08, 0.35, Color(0.9, 0.85, 0.6), Vector3(cos(a) * 0.35, 0.05, sin(a) * 0.35)), Vector3(0, -rad_to_deg(a), -90))
			_add(head, cyl(0.12, 0.15, 0.3, Color(0.8, 0.3, 0.3), Vector3(0, 0.05, -0.4)), Vector3(-90, 0, 0))
		"spore":
			_add(root, sphere(0.7, Color(0.4, 0.3, 0.22), Vector3(0, 0.0, 0)), Vector3.ZERO, Vector3(1.0, 0.6, 1.0))
			head.position = Vector3(0, 0.3, 0)
			_add(head, cyl(0.08, 0.1, 0.8, Color(0.9, 0.88, 0.8), Vector3(0, 0.4, 0)))
			_add(head, sphere(0.45, color, Vector3(0, 0.85, 0)), Vector3.ZERO, Vector3(1, 0.5, 1))
			_add(head, cyl(0.06, 0.08, 0.5, Color(0.9, 0.88, 0.8), Vector3(0.45, 0.25, 0.2)))
			_add(head, sphere(0.22, color.lightened(0.2), Vector3(0.45, 0.5, 0.2), 0.6), Vector3.ZERO, Vector3(1, 0.5, 1))
		"briar":
			for i in 7:
				var a := TAU * i / 7.0
				var r := 0.25 + 0.3 * float(i % 2)
				_add(root, cone(0.14, 0.9 + 0.2 * float(i % 3), color, Vector3(cos(a) * r, 0.45, sin(a) * r)), Vector3(randf_range(-15, 15), 0, randf_range(-15, 15)))
			_add(root, sphere(0.1, Color(0.85, 0.15, 0.2), Vector3(0.2, 0.8, 0.1), 0.6))
			_add(root, sphere(0.1, Color(0.85, 0.15, 0.2), Vector3(-0.25, 0.7, -0.2), 0.6))
			head.position = Vector3(0, 0.5, 0)
		"treant":
			_add(root, cyl(0.3, 0.45, 1.6, BARK, Vector3(0, 0.8, 0)))
			_add(root, sphere(0.6, LEAF, Vector3(0, 1.9, 0)))
			_add(root, sphere(0.4, LEAF.lightened(0.1), Vector3(0.35, 2.3, 0.1)))
			head.position = Vector3(0, 1.1, 0)
			_add(head, box(Vector3(0.18, 0.9, 0.18), BARK, Vector3(-0.5, 0, -0.1)), Vector3(0, 0, 30))
			_add(head, box(Vector3(0.18, 0.9, 0.18), BARK, Vector3(0.5, 0, -0.1)), Vector3(0, 0, -30))
			_add(head, sphere(0.07, Color(1, 0.9, 0.3), Vector3(-0.12, 0.3, -0.42), 2.0))
			_add(head, sphere(0.07, Color(1, 0.9, 0.3), Vector3(0.12, 0.3, -0.42), 2.0))
		"storm":
			_add(root, cyl(0.22, 0.4, 1.8, BARK.darkened(0.2), Vector3(0, 0.9, 0)))
			_add(root, sphere(0.65, Color(0.2, 0.3, 0.45), Vector3(0, 2.1, 0)))
			head.position = Vector3(0, 2.85, 0)
			_add(head, sphere(0.22, color, Vector3.ZERO, 3.0))
			_add(head, torus(0.3, 0.36, color, Vector3.ZERO, 2.0), Vector3(90, 0, 0))
		"hive":
			_add(root, cyl(0.08, 0.1, 1.2, BARK, Vector3(0, 0.6, 0)))
			head.position = Vector3(0, 1.4, 0)
			for i in 4:
				var c := color if i % 2 == 0 else Color(0.35, 0.22, 0.1)
				_add(head, sphere(0.45 - i * 0.06, c, Vector3(0, 0.5 - i * 0.28, 0)), Vector3.ZERO, Vector3(1, 0.6, 1))
			_add(head, sphere(0.1, Color(0.1, 0.05, 0.02), Vector3(0, 0.2, -0.38)))
		"moonwell":
			_add(root, torus(0.55, 0.8, STONE, Vector3(0, 0.2, 0)))
			_add(root, cyl(0.6, 0.6, 0.1, color, Vector3(0, 0.25, 0), 1.5))
			head.position = Vector3(0, 1.6, 0)
			_add(head, sphere(0.28, Color(0.9, 0.95, 1.0), Vector3.ZERO, 2.0))
			_add(head, torus(0.4, 0.45, color, Vector3.ZERO, 1.5), Vector3(80, 0, 0))
		"rootbinder":
			_add(root, box(Vector3(1.1, 0.5, 1.1), DARK_STONE, Vector3(0, 0.25, 0)))
			_add(root, box(Vector3(0.7, 0.9, 0.7), STONE, Vector3(0, 0.95, 0)))
			_add(root, torus(0.5, 0.62, BARK, Vector3(0, 0.6, 0)), Vector3(90, 0, 0))
			_add(root, torus(0.5, 0.62, BARK, Vector3(0, 0.6, 0)), Vector3(90, 90, 0))
			head.position = Vector3(0, 1.75, 0)
			_add(head, sphere(0.25, color, Vector3.ZERO, 2.5))
		_:
			_add(root, box(Vector3(1, 1, 1), color, Vector3(0, 0.5, 0)))
	root.add_child(head)
	return {"root": root, "head": head}


# ------------------------------------------------------------------ enemies

## Returns {"root": Node3D, "body": Node3D} where body is animated (bob/flap).
static func _proc_enemy(id: String, d: Dictionary) -> Dictionary:
	var root := Node3D.new()
	var body := Node3D.new()
	root.add_child(body)
	var c: Color = d["color"]
	match id:
		"goblin":
			_add(body, cyl(0.18, 0.25, 0.5, c.darkened(0.3), Vector3(0, 0.3, 0)))
			_add(body, sphere(0.22, c, Vector3(0, 0.7, 0)))
			_add(body, cone(0.07, 0.3, c, Vector3(-0.25, 0.75, 0)), Vector3(0, 0, 80))
			_add(body, cone(0.07, 0.3, c, Vector3(0.25, 0.75, 0)), Vector3(0, 0, -80))
			_add(body, sphere(0.05, Color(1, 0.2, 0.1), Vector3(-0.08, 0.74, -0.19), 2.0))
			_add(body, sphere(0.05, Color(1, 0.2, 0.1), Vector3(0.08, 0.74, -0.19), 2.0))
		"wolf":
			_add(body, box(Vector3(0.35, 0.35, 0.8), c, Vector3(0, 0.45, 0)))
			_add(body, box(Vector3(0.3, 0.3, 0.35), c.lightened(0.1), Vector3(0, 0.6, -0.5)))
			_add(body, box(Vector3(0.1, 0.1, 0.4), c.darkened(0.2), Vector3(0, 0.55, 0.55)), Vector3(-30, 0, 0))
			for x in [-0.12, 0.12]:
				for z in [-0.28, 0.28]:
					_add(body, box(Vector3(0.09, 0.3, 0.09), c.darkened(0.3), Vector3(x, 0.15, z)))
			_add(body, sphere(0.04, Color(1, 0.8, 0.1), Vector3(0.08, 0.66, -0.68), 3.0))
			_add(body, sphere(0.04, Color(1, 0.8, 0.1), Vector3(-0.08, 0.66, -0.68), 3.0))
		"orc", "ironclad", "hexguard":
			var armor := Color(0.5, 0.5, 0.55)
			if id == "hexguard":
				armor = Color(0.25, 0.15, 0.35)
			if id == "ironclad":
				armor = Color(0.7, 0.7, 0.75)
			_add(body, cyl(0.3, 0.38, 0.8, armor, Vector3(0, 0.5, 0)))
			_add(body, sphere(0.25, c if id == "orc" else armor.lightened(0.2), Vector3(0, 1.1, 0)))
			_add(body, box(Vector3(0.25, 0.6, 0.25), c, Vector3(-0.42, 0.6, 0)))
			_add(body, box(Vector3(0.25, 0.6, 0.25), c, Vector3(0.42, 0.6, 0)))
			if id == "hexguard":
				_add(body, box(Vector3(0.6, 0.7, 0.08), Color(0.6, 0.3, 1.0), Vector3(0, 0.6, -0.4), 1.5))
			elif id == "ironclad":
				_add(body, box(Vector3(0.7, 0.8, 0.1), armor.darkened(0.2), Vector3(0, 0.6, -0.42)))
				_add(body, cone(0.12, 0.3, armor, Vector3(0, 1.4, 0)))
			else:
				_add(body, box(Vector3(0.1, 0.9, 0.1), WOOD, Vector3(0.55, 0.8, -0.15)), Vector3(-30, 0, 0))
				_add(body, box(Vector3(0.3, 0.3, 0.12), STONE, Vector3(0.55, 1.2, -0.4)))
		"harpy":
			_add(body, sphere(0.28, c, Vector3.ZERO), Vector3.ZERO, Vector3(0.9, 0.9, 1.3))
			_add(body, sphere(0.16, c.lightened(0.3), Vector3(0, 0.2, -0.35)))
			var lw := Node3D.new(); lw.name = "WingL"; body.add_child(lw)
			var rw := Node3D.new(); rw.name = "WingR"; body.add_child(rw)
			_add(lw, box(Vector3(0.8, 0.04, 0.4), c.darkened(0.2), Vector3(-0.45, 0, 0)))
			_add(rw, box(Vector3(0.8, 0.04, 0.4), c.darkened(0.2), Vector3(0.45, 0, 0)))
		"slime", "slimelet":
			var m := sphere(0.5, c, Vector3(0, 0.4, 0), 0.3)
			m.material_override = mat(c, 0.4, 0.75)
			_add(body, m, Vector3.ZERO, Vector3(1, 0.75, 1))
			_add(body, sphere(0.08, Color(0.05, 0.1, 0.05), Vector3(-0.15, 0.55, -0.4)))
			_add(body, sphere(0.08, Color(0.05, 0.1, 0.05), Vector3(0.15, 0.55, -0.4)))
		"shaman":
			_add(body, cone(0.35, 0.9, c, Vector3(0, 0.45, 0)))
			_add(body, sphere(0.2, Color(0.45, 0.7, 0.25), Vector3(0, 0.95, 0)))
			_add(body, cyl(0.03, 0.03, 1.3, WOOD, Vector3(0.35, 0.65, 0)))
			_add(body, sphere(0.1, Color(0.3, 1.0, 0.4), Vector3(0.35, 1.35, 0), 3.0))
		"skeleton":
			_add(body, cyl(0.12, 0.15, 0.6, c, Vector3(0, 0.45, 0)))
			_add(body, sphere(0.2, c, Vector3(0, 0.95, 0)))
			_add(body, sphere(0.05, Color(0.3, 0.9, 1.0), Vector3(-0.07, 0.97, -0.17), 3.0))
			_add(body, sphere(0.05, Color(0.3, 0.9, 1.0), Vector3(0.07, 0.97, -0.17), 3.0))
		"troll":
			_add(body, cyl(0.45, 0.55, 1.1, c, Vector3(0, 0.75, 0)))
			_add(body, sphere(0.35, c.lightened(0.1), Vector3(0, 1.5, -0.1)))
			_add(body, box(Vector3(0.3, 1.0, 0.3), c, Vector3(-0.65, 0.8, 0)), Vector3(0, 0, 15))
			_add(body, box(Vector3(0.3, 1.0, 0.3), c, Vector3(0.65, 0.8, 0)), Vector3(0, 0, -15))
			_add(body, cyl(0.12, 0.2, 1.4, BARK, Vector3(0.85, 0.9, -0.3)), Vector3(-40, 0, 0))
			_add(body, cone(0.06, 0.25, Color(0.95, 0.95, 0.85), Vector3(-0.15, 1.45, -0.42)))
			_add(body, cone(0.06, 0.25, Color(0.95, 0.95, 0.85), Vector3(0.15, 1.45, -0.42)))
		"dragon":
			_add(body, sphere(0.5, c, Vector3.ZERO), Vector3.ZERO, Vector3(0.9, 0.8, 1.6))
			_add(body, cyl(0.12, 0.2, 0.8, c, Vector3(0, 0.35, -0.8)), Vector3(-50, 0, 0))
			_add(body, box(Vector3(0.3, 0.25, 0.5), Color(0.9, 0.88, 0.8), Vector3(0, 0.65, -1.2)))
			_add(body, sphere(0.06, Color(0.3, 1, 0.5), Vector3(0.1, 0.75, -1.35), 4.0))
			_add(body, sphere(0.06, Color(0.3, 1, 0.5), Vector3(-0.1, 0.75, -1.35), 4.0))
			_add(body, cone(0.2, 1.2, c.darkened(0.3), Vector3(0, 0, 1.2)), Vector3(90, 0, 0))
			var lw := Node3D.new(); lw.name = "WingL"; body.add_child(lw)
			var rw := Node3D.new(); rw.name = "WingR"; body.add_child(rw)
			_add(lw, box(Vector3(1.6, 0.05, 0.9), Color(0.85, 0.82, 0.75), Vector3(-0.9, 0.1, 0)))
			_add(rw, box(Vector3(1.6, 0.05, 0.9), Color(0.85, 0.82, 0.75), Vector3(0.9, 0.1, 0)))
		"lich":
			_add(body, cone(0.5, 1.6, c, Vector3(0, 0.8, 0)))
			_add(body, sphere(0.25, Color(0.85, 0.85, 0.8), Vector3(0, 1.7, 0)))
			_add(body, torus(0.2, 0.28, GOLD, Vector3(0, 1.9, 0), 1.0))
			_add(body, sphere(0.05, Color(0.3, 0.9, 1.0), Vector3(-0.08, 1.72, -0.22), 5.0))
			_add(body, sphere(0.05, Color(0.3, 0.9, 1.0), Vector3(0.08, 1.72, -0.22), 5.0))
			_add(body, cyl(0.03, 0.03, 2.0, Color(0.2, 0.2, 0.25), Vector3(0.55, 1.0, 0)))
			_add(body, sphere(0.15, Color(0.4, 0.9, 1.0), Vector3(0.55, 2.05, 0), 4.0))
		_:
			_add(body, sphere(0.4, c, Vector3(0, 0.4, 0)))
	body.scale = Vector3.ONE * (1.7 if d.get("boss", false) else 1.25)
	if id == "slimelet":
		body.scale *= 0.6
	return {"root": root, "body": body}


# ------------------------------------------------------------------ scenery

static func tree(rng: RandomNumberGenerator) -> Node3D:
	var n := Node3D.new()
	var h := rng.randf_range(0.9, 1.5)
	var green := LEAF.darkened(rng.randf_range(0.0, 0.35))
	_add(n, cyl(0.1, 0.14, 0.6, BARK, Vector3(0, 0.3, 0)))
	_add(n, cone(0.6, h, green, Vector3(0, 0.55 + h * 0.5, 0)))
	_add(n, cone(0.45, h * 0.8, green.lightened(0.08), Vector3(0, 0.9 + h * 0.5, 0)))
	n.rotation.y = rng.randf() * TAU
	var s := rng.randf_range(0.8, 1.25)
	n.scale = Vector3(s, s, s)
	return n


static func rock(rng: RandomNumberGenerator) -> Node3D:
	var n := Node3D.new()
	var g := rng.randf_range(0.45, 0.6)
	_add(n, sphere(0.55, Color(g, g, g + 0.03), Vector3(0, 0.2, 0)), Vector3(rng.randf() * 30, rng.randf() * 180, 0), Vector3(1.2, 0.7, 1.0))
	_add(n, sphere(0.3, Color(g - 0.05, g - 0.05, g), Vector3(0.4, 0.15, 0.3)))
	return n


static func crystal() -> Node3D:
	var n := Node3D.new()
	var c := Color(0.3, 0.85, 1.0)
	_add(n, cyl(0.0, 0.18, 0.9, c, Vector3(0, 0.5, 0), 1.8, 5))
	_add(n, cyl(0.0, 0.12, 0.6, c, Vector3(0.25, 0.3, 0.15), 1.8, 5), Vector3(0, 0, -20))
	_add(n, cyl(0.0, 0.1, 0.5, c, Vector3(-0.22, 0.25, -0.1), 1.8, 5), Vector3(15, 0, 20))
	return n


static func _proc_castle() -> Node3D:
	var n := Node3D.new()
	_add(n, box(Vector3(2.6, 1.4, 2.6), STONE, Vector3(0, 0.7, 0)))
	for x in [-1.2, 1.2]:
		for z in [-1.2, 1.2]:
			_add(n, cyl(0.45, 0.5, 2.4, STONE.darkened(0.05), Vector3(x, 1.2, z)))
			_add(n, cone(0.55, 0.9, Color(0.25, 0.35, 0.75), Vector3(x, 2.85, z)))
	_add(n, box(Vector3(1.4, 1.4, 1.4), STONE.lightened(0.05), Vector3(0, 2.0, 0)))
	_add(n, cone(0.95, 1.2, Color(0.25, 0.35, 0.75), Vector3(0, 3.3, 0)))
	_add(n, cyl(0.03, 0.03, 1.2, WOOD, Vector3(0, 4.3, 0)))
	_add(n, box(Vector3(0.6, 0.35, 0.03), GOLD, Vector3(0.3, 4.7, 0), 0.4))
	return n


static func portal() -> Node3D:
	var n := Node3D.new()
	var c := Color(0.75, 0.25, 1.0)
	if has_assets() and fit(n, "portal", 2.5, 1.5):
		# AI model + the animated bits (shards, beam, light) from the procedural version
		var sh := Node3D.new()
		sh.name = "Shards"
		sh.position = Vector3(0, 1.4, 0)
		n.add_child(sh)
		for i in 3:
			var a := TAU * i / 3.0
			_add(sh, cyl(0.0, 0.12, 0.45, c.lightened(0.3), Vector3(cos(a) * 0.55, 0, sin(a) * 0.55), 3.0, 4))
		var bm2 := CylinderMesh.new()
		bm2.top_radius = 0.5
		bm2.bottom_radius = 0.8
		bm2.height = 5.0
		var beam2 := MeshInstance3D.new()
		beam2.mesh = bm2
		beam2.material_override = mat(c, 0.0, 0.14)
		beam2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beam2.position = Vector3(0, 2.8, 0)
		n.add_child(beam2)
		var l2 := OmniLight3D.new()
		l2.light_color = c
		l2.light_energy = 2.0
		l2.omni_range = 5.0
		l2.position = Vector3(0, 1.2, 0)
		n.add_child(l2)
		return n
	# dark stone rim with standing stones, a swirling floor and a light beam
	_add(n, cyl(1.05, 1.15, 0.2, Color(0.22, 0.18, 0.26), Vector3(0, 0.1, 0), 0.0, 16))
	var core := cyl(0.85, 0.85, 0.06, Color(0.4, 0.08, 0.6), Vector3(0, 0.22, 0), 2.5, 20)
	core.name = "Core"
	n.add_child(core)
	var ring := torus(0.75, 0.95, c, Vector3(0, 0.26, 0), 3.0)
	ring.name = "Ring"
	n.add_child(ring)
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		_add(n, box(Vector3(0.25, 1.2, 0.25), Color(0.3, 0.26, 0.34), Vector3(cos(a) * 1.05, 0.6, sin(a) * 1.05)), Vector3(0, -rad_to_deg(a), 8))
		_add(n, sphere(0.1, c, Vector3(cos(a) * 1.05, 1.3, sin(a) * 1.05), 3.0))
	var shards := Node3D.new()
	shards.name = "Shards"
	shards.position = Vector3(0, 1.4, 0)
	n.add_child(shards)
	for i in 3:
		var a := TAU * i / 3.0
		_add(shards, cyl(0.0, 0.12, 0.45, c.lightened(0.3), Vector3(cos(a) * 0.55, 0, sin(a) * 0.55), 3.0, 4))
	var beam := MeshInstance3D.new()
	var bm := CylinderMesh.new()
	bm.top_radius = 0.5
	bm.bottom_radius = 0.8
	bm.height = 5.0
	bm.radial_segments = 16
	beam.mesh = bm
	beam.material_override = mat(c, 0.0, 0.18)
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	beam.position = Vector3(0, 2.7, 0)
	n.add_child(beam)
	var light := OmniLight3D.new()
	light.light_color = c
	light.light_energy = 2.0
	light.omni_range = 5.0
	light.position = Vector3(0, 1.2, 0)
	n.add_child(light)
	return n


## Flat translucent disc used for range indicators.
static func range_disc(color: Color) -> MeshInstance3D:
	var m := CylinderMesh.new()
	m.top_radius = 1.0
	m.bottom_radius = 1.0
	m.height = 0.02
	m.radial_segments = 48
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = mat(color, 0.0, 0.18)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var ring := TorusMesh.new()
	ring.inner_radius = 0.97
	ring.outer_radius = 1.0
	ring.rings = 48
	ring.ring_segments = 4
	var rmi := MeshInstance3D.new()
	rmi.mesh = ring
	rmi.material_override = mat(color, 0.0, 0.7)
	rmi.scale = Vector3(1, 0.05, 1)
	rmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.add_child(rmi)
	return mi
