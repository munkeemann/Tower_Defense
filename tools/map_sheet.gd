extends SceneTree
## Dev tool (headless, no window): grows a run's map for some waves and draws the KayKit island (tiles, props,
## castle, neutral buildings) as the game camera sees it, into a PNG with tools/snap.gd. Flat shading only: it shows
## layout and colors, not the game's lighting.
## Godot --headless --path . --script res://tools/map_sheet.gd -- out.png [faction] [waves] [seed] [--bridge]
##   --bridge: every new tile tries to put a pond across its road (to check bridges)

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
	for tile in lists:
		var hm: Array = KayKit.hex_mesh(tile)
		for xf in lists[tile]:
			var mi := MeshInstance3D.new()
			mi.mesh = hm[0]
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
				mi.transform = b._prop_xform(set_["prop"], item)
				stage.add_child(mi)
	for n in [b._castle]:
		var c := (n as Node3D).duplicate() as Node3D
		c.transform = (n as Node3D).global_transform
		stage.add_child(c)
	for c in b.neutrals:
		var nn := (b.neutrals[c]["node"] as Node3D).duplicate() as Node3D
		nn.transform = (b.neutrals[c]["node"] as Node3D).global_transform
		stage.add_child(nn)
	await process_frame
	var img := S.draw(stage, 1400, Vector3(0.0, 0.84, 0.545), 0.0, Vector3.ZERO, Color(0.11, 0.11, 0.115))
	img.save_png(out)
	print("MAP tiles=%d cells=%d saved %s" % [b.placed.size(), seen.size(), out])
	quit()
