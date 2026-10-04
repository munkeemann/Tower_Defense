extends SceneTree
## Dev tool (headless, no window): draws towers standing on KayKit hex tiles, as the game camera sees them, into
## one PNG with tools/snap.gd. Every tower is drawn at the same scale.
## Godot --headless --path . --script res://tools/tower_sheet.gd -- out.png [team] [all | id,id,...] [--front] [--fire]
##   team: blue / green / red / yellow (default blue); --front views from the tower's front instead;
##   --fire poses each crew partway through its attack clip (and Blender towers just after they let go); --zoom draws
##   twice as big; --no-blender draws the KayKit composites instead of the Blender-made towers; --biome=<id> draws the
##   tiles and the towers' ground in that biome's palette, as on its map (greenvale, highlands, deepwood...).

const S := preload("res://tools/snap.gd")
const TILE := 320
const PX := 34.0   # pixels per world unit (--zoom doubles it)


func _init() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := a[0] if a.size() > 0 else "user://tower_sheet.png"
	Models.team = a[1] if a.size() > 1 and not a[1].begins_with("--") else "blue"
	Models.blender_towers = not "--no-blender" in a
	var ids: Array = Models.KK_TOWER.keys()
	if a.size() > 2 and a[2] != "all" and not a[2].begins_with("--"):
		ids = Array(a[2].split(","))
	var view := Vector3(0.0, 0.84, 0.545)   # the game camera: 57 degrees down, looking north
	if "--front" in a:
		view = Vector3(0.35, 0.5, -1.0)
	var zoom := 2.0 if "--zoom" in a else 1.0
	var aim := 0.6   # turn the crews a little toward the camera's left, as if shooting there
	var grass: Array = KayKit.hex_mesh("hex_grass")
	var ground: Material = null
	for arg in a:
		if arg.begins_with("--biome="):
			var bd := Board.new()
			bd.biome_id = arg.substr(8)
			ground = bd.ground_material()
			bd.free()
	var imgs: Array = []
	for id in ids:
		var stage := Node3D.new()
		root.add_child(stage)
		var cells: Array = GameData.shape_of(id)["cells"]
		var mid := Vector3.ZERO
		for c in cells:
			mid += Hex.to_world(Vector2i(c[0], c[1]))
		mid /= float(cells.size())
		for c in cells:
			var mi := MeshInstance3D.new()
			mi.mesh = grass[0]
			var b := Basis(Vector3.UP, deg_to_rad(Board.KK_BASE_YAW)).scaled(Vector3(Board.KK_SCALE, Board.LEVEL_H, Board.KK_SCALE))
			mi.transform = Transform3D(b, Hex.to_world(Vector2i(c[0], c[1])) - mid) * (grass[1] as Transform3D)
			if ground:
				mi.material_override = ground
			stage.add_child(mi)
		var m := Models.tower(id, GameData.TOWERS[id]["color"])
		var tr: Node3D = m["root"]
		stage.add_child(tr)
		Models.set_ground(tr, ground)
		var still: bool = GameData.TOWERS[id].get("static", false) or String(GameData.TOWERS[id]["attack"]).begins_with("aura")
		if tr.has_meta("kaykit") and not (tr.has_meta("blender") and still):
			(m["head"] as Node3D).rotation.y = aim   # (Blender aura and static towers never turn their head)
			for tn in tr.get_meta("turrets", []):
				(tn as Node3D).rotation.y = aim
		if "--fire" in a and tr.has_meta("rig_ap"):
			# Blender towers: the machine just after it lets go (arms snapped forward, bolt gone)
			var rap: AnimationPlayer = tr.get_meta("rig_ap")
			rap.play("fire")
			rap.seek(0.12, true)
			rap.pause()
		if "--fire" in a and tr.has_meta("crew_ap") and String(tr.get_meta("crew_attack")) != "":
			var ap: AnimationPlayer = tr.get_meta("crew_ap")
			var clip := String(tr.get_meta("crew_attack"))
			ap.play(clip)
			ap.seek(ap.get_animation(clip).length * 0.3 * float(tr.get_meta("crew_cut", 1.0)), true)
			ap.pause()
		for i in 3:
			await process_frame
		imgs.append(S.draw(stage, int(TILE * zoom), view, PX * zoom, Vector3(0, 1.3, 0)))
		print("SHEET ", imgs.size() - 1, " ", id)
		stage.free()
	S.sheet(imgs, mini(5 if zoom == 1.0 else 3, imgs.size())).save_png(out)
	print("SHEET saved ", out)
	quit()
