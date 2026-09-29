extends SceneTree
## Dev tool: footprint towers in a grid, each on its footprint (facing north, -Z) with a red arrow at the front, shot
## from straight above and from a three-quarter view. Use it to check facing (yaw) and how well models fill their hexes.
## Godot --path . --script res://tools/fp_preview.gd -- --out=<prefix> [--ids=a,b,c] [--glb=file1,file2] [--cols=6]
##   --ids: towers as the game builds them.  --glb: raw models from assets/custom (just to read their facing).

const CELL := 13.0


func _init() -> void:
	var out := "user://fp_preview"
	var ids: Array = []
	var glbs: Array = []
	var cols := 6
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
		elif a.begins_with("--ids="):
			ids = Array(a.substr(6).split(","))
		elif a.begins_with("--glb="):
			glbs = Array(a.substr(6).split(","))
		elif a.begins_with("--cols="):
			cols = int(a.substr(7))
	if ids.is_empty() and glbs.is_empty():
		for tid in GameData.TOWERS:
			if GameData.shape_of(tid)["cells"].size() > 1:
				ids.append(tid)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Hex.setup()
	var world := Node3D.new()
	root.add_child(world)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.36, 0.42, 0.34)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(1, 1, 1)
	env.environment.ambient_light_energy = 0.7
	world.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-60, -30, 0)
	world.add_child(sun)
	var items: Array = []
	for tid in ids:
		items.append({"label": tid, "node": Models.tower(tid, GameData.TOWERS[tid]["color"])["root"], "cells": GameData.shape_of(tid)["cells"]})
	for g in glbs:
		var n := Models.asset(Models.CUSTOM + g + ".glb")
		if n == null:
			continue
		var holder := Node3D.new()
		var bb := Models._local_aabb(n)
		var s := 8.0 / maxf(maxf(bb.size.x, bb.size.z), 0.01)
		n.scale = Vector3.ONE * s
		n.position = -bb.get_center() * s + Vector3(0, bb.size.y * 0.5 * s, 0)
		holder.add_child(n)
		items.append({"label": g, "node": holder, "cells": []})
	var rows := int(ceil(items.size() / float(cols)))
	for i in items.size():
		var it: Dictionary = items[i]
		var at := Vector3((i % cols) * CELL, 0, (i / cols) * CELL)
		var node: Node3D = it["node"]
		node.position += at
		world.add_child(node)
		var mid := Vector3.ZERO
		for c in it["cells"]:
			mid += Hex.to_world(Vector2i(c[0], c[1]))
		if it["cells"].size() > 0:
			mid /= float(it["cells"].size())
		for c in it["cells"]:
			var plate := Models.cyl(Hex.R * 0.97, Hex.R * 0.97, 0.04, Color(0.85, 0.85, 0.7), at + Hex.to_world(Vector2i(c[0], c[1])) - mid, 0.0, 6)
			world.add_child(plate)
		var arrow := Models.cone(0.5, 1.4, Color(1, 0.1, 0.1), at + Vector3(0, 0.1, -CELL * 0.45), 0.5)
		arrow.rotation_degrees = Vector3(-90, 0, 0)
		world.add_child(arrow)
		var lbl := Label3D.new()
		lbl.text = String(it["label"])
		lbl.font_size = 96
		lbl.pixel_size = 0.012
		lbl.rotation_degrees = Vector3(-90, 0, 0)
		lbl.position = at + Vector3(0, 0.2, CELL * 0.42)
		lbl.modulate = Color(1, 1, 1)
		lbl.outline_size = 16
		world.add_child(lbl)
	var cam := Camera3D.new()
	world.add_child(cam)
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	# fit the grid to the window's aspect (orthographic size is the visible height)
	await process_frame
	var vs := root.get_visible_rect().size
	var aspect := vs.x / maxf(1.0, vs.y)
	var span := maxf(rows * CELL, cols * CELL / aspect)
	cam.size = span
	cam.position = Vector3((cols - 1) * CELL * 0.5, 80, (rows - 1) * CELL * 0.5)
	cam.rotation_degrees = Vector3(-90, 0, 0)
	cam.far = 300
	cam.current = true
	for i in 8:
		await process_frame
	root.get_texture().get_image().save_png(out + "_top.png")
	cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	cam.fov = 30
	cam.rotation_degrees = Vector3(-42, 0, 0)
	cam.position = Vector3((cols - 1) * CELL * 0.5, span * 1.45, (rows - 1) * CELL * 0.5 + span * 1.6)
	for i in 8:
		await process_frame
	root.get_texture().get_image().save_png(out + "_side.png")
	print("FPPREVIEW saved ", out)
	quit()
