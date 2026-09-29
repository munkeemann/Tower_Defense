extends Node3D
## Dev tool: lays out a set of models in a labelled grid, prints their sizes and saves a screenshot.
## Run: Godot --path . res://tools/preview.tscn -- --files=a.glb,b.glb --shot=out.png [--cols=6] [--spacing=3]


func _ready() -> void:
	var files: PackedStringArray = []
	var shot := ""
	var cols := 6
	var spacing := 3.0
	var anim := true
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--files="):
			files = a.substr(8).split(",")
		elif a.begins_with("--shot="):
			shot = a.substr(7)
		elif a.begins_with("--cols="):
			cols = int(a.substr(7))
		elif a.begins_with("--spacing="):
			spacing = float(a.substr(10))
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.42, 0.55, 0.38)
	env.environment.ambient_light_color = Color(1, 1, 1)
	env.environment.ambient_light_energy = 0.6
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -35, 0)
	sun.shadow_enabled = true
	add_child(sun)
	# --files=towers:crown  /  --files=enemies  render the game's own builders
	var mode := ""
	if files.size() == 1 and (files[0].begins_with("towers") or files[0] == "enemies"):
		mode = files[0]
		files = []
		if mode.begins_with("towers"):
			for tid in GameData.FACTIONS[mode.split(":")[1]]["towers"]:
				files.append(tid)
		else:
			for eid in GameData.ENEMIES:
				files.append(eid)
	var rows := int(ceil(files.size() / float(cols)))
	for i in files.size():
		var path := files[i]
		var inst: Node3D
		if mode.begins_with("towers"):
			var m := Models.tower(path, GameData.TOWERS[path]["color"])
			inst = m["root"]
		elif mode == "enemies":
			var m2 := Models.enemy(path, GameData.ENEMIES[path])
			inst = m2["root"]
			if GameData.ENEMIES[path].get("flying", false):
				inst.position.y = 1.6
		else:
			if not path.begins_with("res://"):
				path = "res://assets/" + path
			var ps := load(path) as PackedScene
			if ps == null:
				print("PREVIEW missing ", path)
				continue
			inst = ps.instantiate() as Node3D
		var x := (i % cols - (cols - 1) / 2.0) * spacing
		var z := (i / cols - (rows - 1) / 2.0) * spacing
		inst.position = Vector3(x, inst.position.y, z)
		if mode != "":
			inst.rotation_degrees.y = 180.0  # game forward (-Z) faces the camera
		add_child(inst)
		var aabb := _aabb(inst)
		print("PREVIEW %s size=(%.2f, %.2f, %.2f) min_y=%.2f center=(%.2f, %.2f)" % [path.get_file(), aabb.size.x, aabb.size.y, aabb.size.z, aabb.position.y, aabb.get_center().x - x, aabb.get_center().z - z])
		var ap := inst.find_child("AnimationPlayer", true, false) as AnimationPlayer
		if ap and anim:
			var names := ap.get_animation_list()
			print("PREVIEW   anims: ", ", ".join(names))
			for want in ["Walk", "Walking_A", "Flying_Idle", "Fast_Flying"]:
				if ap.has_animation(want):
					ap.play(want)
					break
		var l := Label3D.new()
		l.text = path.get_file().get_basename()
		l.font_size = 40
		l.pixel_size = 0.01
		l.outline_size = 8
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.position = Vector3(x, -0.3, z + spacing * 0.42)
		add_child(l)
	var cam := Camera3D.new()
	var extent: float = max(cols, rows * 1.6) * spacing
	cam.position = Vector3(0, extent * 0.75, extent * 0.62)
	cam.rotation_degrees = Vector3(-50, 0, 0)
	cam.fov = 45
	add_child(cam)
	await get_tree().create_timer(0.6).timeout
	await RenderingServer.frame_post_draw
	if shot != "":
		get_viewport().get_texture().get_image().save_png(shot)
		print("PREVIEW saved ", shot)
	get_tree().quit()


func _aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	for c in n.find_children("*", "VisualInstance3D", true, false):
		var vi := c as VisualInstance3D
		var bb := vi.global_transform * vi.get_aabb()
		if first:
			out = bb
			first = false
		else:
			out = out.merge(bb)
	return out
