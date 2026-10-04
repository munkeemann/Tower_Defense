class_name Thumbs
extends Node
## Renders small portrait images of towers (for reward cards and the build bar) in an off-screen viewport,
## one tower per frame, and caches them.

const SIZE := 256

var _cache := {}        # tower id + KayKit team color -> Texture2D
var _queue: Array = []
var _busy := false
var _vp: SubViewport
var _cam: Camera3D
var _stage: Node3D
var _enabled := true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_enabled = DisplayServer.get_name() != "headless"
	if not _enabled:
		return
	_vp = SubViewport.new()
	_vp.size = Vector2i(SIZE, SIZE)
	_vp.transparent_bg = true
	_vp.own_world_3d = true
	_vp.msaa_3d = Viewport.MSAA_4X
	_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(_vp)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 0.65
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	we.environment = env
	_vp.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, -35, 0)
	sun.light_energy = 1.3
	_vp.add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 28.0
	_vp.add_child(_cam)
	_stage = Node3D.new()
	_stage.rotation_degrees.y = 20.0
	_vp.add_child(_stage)


## Cached portrait, or null while it's still being rendered (it gets queued).
func get_thumb(tid: String) -> Texture2D:
	if _cache.has(_key(tid)):
		return _cache[_key(tid)]
	if _enabled and tid not in _queue:
		_queue.append(tid)
	return null


## KayKit buildings take your color's team color, so a portrait is kept per color.
func _key(tid: String) -> String:
	return tid + "|" + Models.team


func queue_faction(fid: String) -> void:
	for tid in GameData.run_towers(fid):
		get_thumb(tid)


func _process(_delta: float) -> void:
	if _busy or _queue.is_empty():
		return
	_busy = true
	_render(_queue.pop_front())


func _render(tid: String) -> void:
	for c in _stage.get_children():
		c.queue_free()
	var m := Models.tower(tid, GameData.TOWERS[tid]["color"])
	var root: Node3D = m["root"]
	if root.has_meta("kaykit"):
		# KayKit crews and guns look out of the portrait
		(m["head"] as Node3D).rotation.y = PI - 0.35
		for tn in root.get_meta("turrets", []):
			(tn as Node3D).rotation.y = PI - 0.35
	_stage.add_child(root)
	var bb := Models._local_aabb(root)
	var mid := _stage.transform * bb.get_center()
	var radius := maxf(bb.size.length() * 0.5, 0.5)
	var dist := radius / sin(deg_to_rad(_cam.fov * 0.5)) * 0.78
	_cam.position = mid + Vector3(0, 0.42, 1).normalized() * dist
	_cam.look_at(mid, Vector3.UP)
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := _vp.get_texture().get_image()
	if img and not img.is_empty():
		_cache[_key(tid)] = ImageTexture.create_from_image(img)
	else:
		_cache[_key(tid)] = null
	_busy = false
