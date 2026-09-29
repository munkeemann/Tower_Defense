class_name CameraRig
extends Node3D
## Angled RTS-style camera. WASD/arrows pan, wheel zooms, Q/E rotate,
## right or middle mouse drag pans.

var camera: Camera3D
var yaw := 0.0
var pitch := deg_to_rad(-57.0)
## A long, narrow lens (Tower Dominion's near-flat look, where the grid reads cleanly). Distances everywhere
## keep their old meaning: the camera just stands farther back so the framing matches the old 50 degree lens.
const FOV := 32.0
var _fov_comp := tan(deg_to_rad(25.0)) / tan(deg_to_rad(FOV * 0.5))
var distance := 34.0
var min_dist := 12.0
var max_dist := 150.0
var bounds := 75.0
var auto_orbit := false

var _target_dist := 34.0
var _target_yaw := 0.0
var _dragging := false
var _glide: Variant = null
var _shake := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	camera = Camera3D.new()
	camera.fov = FOV
	camera.far = 700.0
	add_child(camera)
	_apply()


func _unscaled(delta: float) -> float:
	var ts := Engine.time_scale
	return delta / ts if ts > 0.0 else delta


func _process(delta: float) -> void:
	var dt := _unscaled(delta)
	if auto_orbit:
		_target_yaw += dt * 0.05
	else:
		var move := Vector2.ZERO
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): move.y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): move.y += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): move.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): move.x += 1
		if Input.is_key_pressed(KEY_Q): _target_yaw += dt * 1.8
		if Input.is_key_pressed(KEY_E): _target_yaw -= dt * 1.8
		if move != Vector2.ZERO:
			_glide = null
			var spd := distance * 0.9 * (2.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0)
			_pan(move.normalized() * spd * dt)
		elif _glide != null:
			position = position.lerp(_glide, min(1.0, dt * 3.0))
			if position.distance_to(_glide) < 0.1:
				_glide = null
	distance = lerp(distance, _target_dist, min(1.0, dt * 10.0))
	yaw = lerp_angle(yaw, _target_yaw, min(1.0, dt * 10.0))
	_apply()
	if _shake > 0.0:
		_shake = maxf(0.0, _shake - dt * 2.5)
		var a := _shake * _shake * distance * 0.012
		camera.h_offset = randf_range(-a, a)
		camera.v_offset = randf_range(-a, a)
	elif camera.h_offset != 0.0 or camera.v_offset != 0.0:
		camera.h_offset = 0.0
		camera.v_offset = 0.0


## Screen shake: 0.3 = a bump, 1.0 = a big hit. Stacks up to 1.
func shake(amount: float) -> void:
	_shake = minf(1.0, maxf(_shake, amount))


func _pan(v: Vector2) -> void:
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	var right := Vector3(cos(yaw), 0, -sin(yaw))
	position += right * v.x - fwd * v.y
	position.x = clamp(position.x, -bounds, bounds)
	position.z = clamp(position.z, -bounds, bounds)


func _apply() -> void:
	rotation = Vector3(0, yaw, 0)
	var d := distance * _fov_comp
	camera.position = Vector3(0, -sin(pitch) * d, cos(pitch) * d)
	camera.rotation = Vector3(pitch, 0, 0)


func handle_input(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_target_dist = clamp(_target_dist * 0.88, min_dist, max_dist)
			return true
		if mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_target_dist = clamp(_target_dist * 1.12, min_dist, max_dist)
			return true
		if mb.button_index == MOUSE_BUTTON_MIDDLE or mb.button_index == MOUSE_BUTTON_RIGHT:
			_dragging = mb.pressed
			return false
	elif event is InputEventMouseMotion and _dragging:
		var mm := event as InputEventMouseMotion
		if mm.relative.length() > 0.5:
			_glide = null
			_pan(Vector2(-mm.relative.x, -mm.relative.y) * distance * 0.0022)
		return true
	return false


func focus(p: Vector3) -> void:
	_glide = null
	position = Vector3(p.x, 0, p.z)


func glide_to(p: Vector3) -> void:
	_glide = Vector3(p.x, 0, p.z)


func mouse_ground_point(screen_pos: Vector2) -> Variant:
	var from := camera.project_ray_origin(screen_pos)
	var dir := camera.project_ray_normal(screen_pos)
	if abs(dir.y) < 0.0001:
		return null
	var t := -from.y / dir.y
	if t < 0.0:
		return null
	return from + dir * t
