class_name Projectile
extends Node3D

enum K { HOMING, BOLT, LOB }

var game: Game
var packet: Dictionary
var kind := K.HOMING
var target: Enemy
var target_pos := Vector3.ZERO
var speed := 20.0
var dir := Vector3.FORWARD
var travel_left := 0.0
var hit_set := {}
var start := Vector3.ZERO
var t := 0.0
var dur := 1.0
var color := Color.WHITE


func _visual(style: String, c: Color) -> void:
	color = c
	match style:
		"arrow":
			var shaft := Models.box(Vector3(0.05, 0.05, 0.6), Color(0.55, 0.4, 0.25))
			add_child(shaft)
			add_child(Models.box(Vector3(0.1, 0.1, 0.12), Color(0.8, 0.8, 0.85), Vector3(0, 0, -0.3)))
		"dart":
			add_child(Models.box(Vector3(0.07, 0.07, 0.35), c.lightened(0.2), Vector3.ZERO, 0.6))
		"orb":
			add_child(Models.sphere(0.2, c, Vector3.ZERO, 3.0))
		"bolt":
			add_child(Models.box(Vector3(0.1, 0.1, 1.2), Color(0.5, 0.35, 0.2)))
			add_child(Models.box(Vector3(0.16, 0.16, 0.2), Color(0.85, 0.85, 0.9), Vector3(0, 0, -0.6)))
		"boulder":
			add_child(Models.sphere(0.3, Color(0.45, 0.45, 0.48)))
		"cannonball":
			add_child(Models.sphere(0.22, Color(0.12, 0.12, 0.14)))
		"spore":
			add_child(Models.sphere(0.25, c, Vector3.ZERO, 1.2))


func setup_homing(g: Game, pkt: Dictionary, from: Vector3, tgt: Enemy, spd: float, style: String, c: Color) -> void:
	game = g
	packet = pkt
	kind = K.HOMING
	position = from
	target = tgt
	target_pos = tgt.aim_pos()
	speed = spd
	_visual(style, c)


func setup_bolt(g: Game, pkt: Dictionary, from: Vector3, d: Vector3, dist: float, spd: float, c: Color) -> void:
	game = g
	packet = pkt
	kind = K.BOLT
	position = from
	dir = d
	travel_left = dist
	speed = spd
	_visual("bolt", c)
	look_at(position + dir, Vector3.UP)


func setup_lob(g: Game, pkt: Dictionary, from: Vector3, to: Vector3, flight: float, c: Color) -> void:
	game = g
	packet = pkt
	kind = K.LOB
	position = from
	start = from
	target_pos = to
	dur = flight
	var style := "boulder"
	if pkt["tower_id"] == "bombard":
		style = "cannonball"
	elif pkt["tower_id"] == "spore":
		style = "spore"
	_visual(style, c)


func _process(delta: float) -> void:
	match kind:
		K.HOMING:
			if is_instance_valid(target) and not target.dead:
				target_pos = target.aim_pos()
			var to := target_pos - position
			var step := speed * delta
			if to.length() <= step:
				position = target_pos
				var alive: Enemy = target if is_instance_valid(target) and not target.dead else null
				if alive:
					game.apply_hit(packet, alive)
				if packet["splash"] > 0.0:
					game.apply_splash(packet, position, alive)
					FX.burst(game.world, position, color, packet["splash"] * 0.6, 0.25)
				else:
					FX.burst(game.world, position, color, 0.35, 0.15)
				queue_free()
				return
			position += to / to.length() * step
			if Vector2(to.x, to.z).length() > 0.05:
				look_at(position + to, Vector3.UP)
		K.BOLT:
			var step := speed * delta
			position += dir * step
			travel_left -= step
			for e in game.enemies.duplicate():
				if e.dead or hit_set.has(e):
					continue
				if not game._can_hit(packet, e):
					continue
				if Vector2(e.position.x - position.x, e.position.z - position.z).length() < 0.9:
					hit_set[e] = true
					game.apply_hit(packet, e)
			if travel_left <= 0.0:
				queue_free()
		K.LOB:
			t += delta
			var s: float = min(1.0, t / dur)
			var arc := 1.5 + start.distance_to(target_pos) * 0.25
			position = start.lerp(target_pos, s) + Vector3(0, arc * 4.0 * s * (1.0 - s), 0)
			rotate_x(delta * 6.0)
			if s >= 1.0:
				game.apply_splash(packet, target_pos, null)
				var fx_col := Color(0.55, 0.45, 0.35) if packet["tower_id"] != "spore" else color
				FX.ring(game.world, target_pos + Vector3(0, 0.15, 0), fx_col, packet["splash"], 0.35)
				FX.burst(game.world, target_pos, fx_col, packet["splash"] * 0.5, 0.3)
				game.sfx("boom", target_pos)
				if packet["splash"] > 2.4:
					game.cam.shake(0.18)
				queue_free()
