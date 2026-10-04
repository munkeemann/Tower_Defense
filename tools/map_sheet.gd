extends SceneTree
## Dev tool (headless, no window): grows a run's map for some waves and draws the KayKit island (tiles, props,
## castle, neutral buildings) as the game camera sees it, into a PNG with tools/snap.gd. Flat shading only: it shows
## layout and colors, not the game's lighting.
## Godot --headless --path . --script res://tools/map_sheet.gd -- out.png [faction] [waves] [seed] [--bridge] [--biome=<id>]
##   --bridge: every new tile tries to put a pond across its road (to check bridges)
##   --holo: also draws the next tile on offer as its placement hologram, on the first spot it fits

const S := preload("res://tools/snap.gd")


func _init() -> void:
	var a := OS.get_cmdline_user_args()
	var out := a[0] if a.size() > 0 else "user://map_sheet.png"
	var fid := a[1] if a.size() > 1 else "verdant"
	var waves := int(a[2]) if a.size() > 2 else 12
	var main: Node = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	await process_frame
	await process_frame
	var g := main as Game
	g.rng.seed = int(a[3]) if a.size() > 3 else 33
	for x in a:
		if x.begins_with("--biome="):
			g.force_biome = x.substr(8)
	g.start_run(fid)
	g.hud.hide_choices()
	for i in waves:
		g.wave = i
		if "--bridge" in a:
			g.board.force_bridge = true
		g._auto_expand()
	var b := g.board
	# the KayKit tiles, as plain mesh instances (headless MultiMeshes don't keep their transforms)
	var stage := Node3D.new()
	root.add_child(stage)
	var lists := {}
	var seen := {}
	for t in b.placed:
		for e in b._info:
			var gc: Vector2i = t * Hex.K + e["off"]
			if not seen.has(gc):
				seen[gc] = true
				b._kk_cell(gc, lists)
	b._kk_sea(seen, lists)
	var palette := b._kk_material()
	for tile in lists:
		var hm: Array = KayKit.hex_mesh(tile)
		var vary: bool = String(tile).begins_with("hex_grass") or String(tile).begins_with("hex_coast")
		for xf in lists[tile]:
			var mi := MeshInstance3D.new()
			mi.mesh = hm[0]
			var mat := palette
			if vary:
				# the per-hex shade the game sets as MultiMesh instance colors
				var v := 0.94 + 0.1 * b._kk_hash(Hex.from_world((xf as Transform3D).origin), 60 + int((xf as Transform3D).origin.y * 3.0))
				mat = (palette as BaseMaterial3D).duplicate()
				(mat as BaseMaterial3D).albedo_color = Color(v, v, v)
			mi.material_override = mat
			mi.transform = (xf as Transform3D) * (hm[1] as Transform3D)
			stage.add_child(mi)
	# props on your tiles
	for key in b._prop_sets:
		var set_: Dictionary = b._prop_sets[key]
		var mm := (set_["mm"] as MultiMeshInstance3D).multimesh
		for item in set_["items"]:
			if item is Dictionary and not (item as Dictionary).is_empty():
				var mi := MeshInstance3D.new()
				mi.mesh = mm.mesh
				mi.material_override = (set_["mm"] as MultiMeshInstance3D).material_override
				mi.transform = b._prop_xform(set_["prop"], item)
				stage.add_child(mi)
	if "--holo" in a:
		var cards := g._roll_tile_cards(1)
		if not cards.is_empty():
			var pl := g._card_placements(cards[0])
			if not pl.is_empty():
				var plan := b.plan_tile(pl[0][0], cards[0], pl[0][1])
				print("MAPSHEET hologram on slot %s: %s" % [pl[0][0], g.tile_title(cards[0])])
				for part in b.hologram_parts(plan):
					for xf in part[1]:
						var mi := MeshInstance3D.new()
						mi.mesh = part[0]
						mi.material_override = b._holo_mat(true, part[2])
						mi.transform = xf
						stage.add_child(mi)
	for n in [b._castle]:
		var c := (n as Node3D).duplicate() as Node3D
		c.transform = (n as Node3D).global_transform
		stage.add_child(c)
	for c in b.neutrals:
		var nn := (b.neutrals[c]["node"] as Node3D).duplicate() as Node3D
		nn.transform = (b.neutrals[c]["node"] as Node3D).global_transform
		stage.add_child(nn)
	# the open sea around it, as the game draws it (a patch of it a little bigger than the island)
	if b.ocean_mi:
		var bb := Models._local_aabb(stage)
		var sea_mi := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(bb.size.x, bb.size.z) + Vector2(16, 16)
		sea_mi.mesh = pm
		sea_mi.material_override = b.ocean_mi.material_override
		stage.add_child(sea_mi)
		sea_mi.position = Vector3(bb.get_center().x, b.ocean_mi.position.y, bb.get_center().z)
	await process_frame
	# seen from the run's opening camera (turned CameraRig.START_YAW around the castle), over the open sea
	var yaw := CameraRig.START_YAW
	var sea := b.ocean_color * 0.9   # (snap shades a flat top face about this much)
	var img := S.draw(stage, 1400, Vector3(0.0, 0.84, 0.545).rotated(Vector3.UP, yaw), 0.0, Vector3.ZERO, sea)
	img.save_png(out)
	# a close-up of the castle's corner of the map, about as near as the game's opening view
	var close := S.draw(stage, 1000, Vector3(0.25, 0.84, 0.545).rotated(Vector3.UP, yaw), 52.0,
		b._castle.global_position + Vector3(0, 0, -4).rotated(Vector3.UP, yaw), sea)
	close.save_png(out.get_basename() + "_close.png")
	print("MAP tiles=%d cells=%d saved %s" % [b.placed.size(), seen.size(), out])
	quit()
