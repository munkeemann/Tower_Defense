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
var style := ""


## Towers whose shot has a look of its own (the rest take their attack kind's: arrow, bolt, orb...).
const LOOKS := {"hive": "wasp", "thorn": "thorn", "seraph": "lightspear", "dwarf_gyro": "shell", "bone_crypt": "bonebolt",
	"leviathan": "jet", "mer_harpoon": "harpoon"}


static func look(tower_id: String, kind: String) -> String:
	return LOOKS.get(tower_id, kind)


func _visual(style_: String, c: Color) -> void:
	color = c
	style = style_
	match style:
		"wasp":
			add_child(Models.box(Vector3(0.1, 0.1, 0.24), Color(0.98, 0.8, 0.15), Vector3.ZERO, 0.5))
			add_child(Models.box(Vector3(0.11, 0.11, 0.06), Color(0.1, 0.09, 0.08), Vector3(0, 0, 0.03)))
			add_child(Models.box(Vector3(0.11, 0.11, 0.05), Color(0.1, 0.09, 0.08), Vector3(0, 0, -0.08)))
			for sx in [-1.0, 1.0]:
				add_child(Models.box(Vector3(0.14, 0.012, 0.1), Color(0.92, 0.95, 1.0), Vector3(sx * 0.1, 0.06, 0.0), 0.4))
		"thorn":
			add_child(Models.box(Vector3(0.05, 0.05, 0.36), Color(0.36, 0.5, 0.22)))
			add_child(Models.box(Vector3(0.075, 0.075, 0.1), Color(0.55, 0.4, 0.22), Vector3(0, 0, -0.2)))
		"lightspear":
			add_child(Models.box(Vector3(0.06, 0.06, 1.0), Color(1.0, 0.95, 0.7), Vector3.ZERO, 3.0))
			add_child(Models.box(Vector3(0.13, 0.13, 0.26), Color(1.0, 0.98, 0.85), Vector3(0, 0, -0.5), 4.0))
		"shell":
			add_child(Models.box(Vector3(0.09, 0.09, 0.2), Color(0.25, 0.22, 0.2)))
			add_child(Models.box(Vector3(0.05, 0.05, 0.4), Color(1.0, 0.62, 0.2), Vector3(0, 0, 0.28), 3.0))
		"bonebolt":
			add_child(Models.box(Vector3(0.05, 0.05, 0.55), Color(0.9, 0.87, 0.76)))
			add_child(Models.box(Vector3(0.1, 0.1, 0.12), Color(0.5, 0.5, 0.55), Vector3(0, 0, -0.28)))
		"jet":
			add_child(Models.sphere(0.24, Color(0.7, 0.9, 1.0), Vector3(0, 0, -0.7), 1.6))
			add_child(Models.box(Vector3(0.26, 0.26, 1.4), Color(0.4, 0.75, 1.0), Vector3.ZERO, 1.2))
			add_child(Models.box(Vector3(0.16, 0.16, 0.9), Color(0.55, 0.85, 1.0), Vector3(0, 0, 1.1), 1.0))
		"harpoon":
			add_child(Models.box(Vector3(0.07, 0.07, 1.3), Color(0.9, 0.86, 0.76)))
			add_child(Models.box(Vector3(0.18, 0.05, 0.26), Color(0.6, 0.62, 0.68), Vector3(0, 0, -0.68)))
			add_child(Models.box(Vector3(0.05, 0.18, 0.2), Color(0.6, 0.62, 0.68), Vector3(0, 0, -0.62)))
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
		"magma":
			add_child(Models.sphere(0.3, Color(0.25, 0.12, 0.08)))
			add_child(Models.sphere(0.24, Color(1.0, 0.5, 0.1), Vector3.ZERO, 3.0))


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
	_visual(look(String(pkt["tower_id"]), "bolt"), c)
	look_at(position + dir, Vector3.UP)


func setup_lob(g: Game, pkt: Dictionary, from: Vector3, to: Vector3, flight: float, c: Color) -> void:
	game = g
	packet = pkt
	kind = K.LOB
	position = from
	start = from
	target_pos = to
	dur = flight
	var look := "boulder"
	if pkt["tower_id"] == "bombard":
		look = "cannonball"
	elif pkt["tower_id"] in ["spore", "plague_cauldron"]:
		look = "spore"
	elif pkt["tower_id"] == "magma_golem":
		look = "magma"
	_visual(look, c)


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
					VFX.magic_hit(game.world, position, color, true)
				elif style == "orb":
					VFX.magic_hit(game.world, position, color)
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
				var toxic: bool = packet["tower_id"] in ["spore", "plague_cauldron"]
				var fx_col := color if toxic else Color(0.55, 0.45, 0.35)
				FX.ring(game.world, target_pos + Vector3(0, 0.15, 0), fx_col, packet["splash"], 0.35)
				if toxic:
					VFX.poison(game.world, target_pos, color, packet["splash"])
				else:
					VFX.blast(game.world, target_pos, packet["splash"], packet["tower_id"] in ["magma_golem", "dwarf_mortar", "bombard"])
				game.sfx("splat" if toxic else "boom", target_pos)
				if packet["splash"] > 2.4:
					game.cam.shake(0.18)
				queue_free()
