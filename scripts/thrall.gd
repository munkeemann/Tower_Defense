class_name Thrall
extends Node3D
## A zombie: an enemy that died in a Necromancer's reach, raised to fight for you. It shambles back down the road
## it came along, and the first walker it meets is grabbed (stunned and mauled), after which the zombie crumbles.
## It also crumbles when its time runs out, when it reaches the road's end, or when the wave is over.

const GRAB_STUN := 1.5
const GRAB_REACH := 1.0

var game: Game
var source: Tower
var route := PackedVector3Array()
var progress := 0.0
var speed := 1.0
var life := 8.0
var dmg := 0.0
var _rise := 0.0


func setup(g: Game, e: Enemy, src: Tower) -> void:
	game = g
	source = src
	route = e.route
	progress = e.progress
	var raise: Dictionary = src.data["raise"]
	speed = float(GameData.ENEMIES[e.type_id]["speed"]) * GameData.TILE * 0.7
	life = float(raise["life"])
	dmg = e.max_hp * float(raise["grab"]) * (1.0 + src.fxf("dmg"))
	var m := Models.enemy(e.type_id, e.data)
	add_child(m["root"])
	Models.overlay(m["root"], Models.rim_mat(Color(0.45, 1.0, 0.35)))
	add_to_group("thralls")
	position = e.ground_pos() + Vector3(0, -1.0, 0)
	VFX.raise(game.world, e.ground_pos())
	game.sfx("raise", e.ground_pos())


func _point_at(d: float) -> Vector3:
	var left := d
	for i in range(1, route.size()):
		var a := route[i - 1]
		var b := route[i]
		var l := a.distance_to(b)
		if left <= l:
			return a.lerp(b, left / maxf(l, 0.001))
		left -= l
	return route[route.size() - 1]


func _process(delta: float) -> void:
	life -= delta
	_rise = minf(1.0, _rise + delta * 2.0)
	if _rise >= 1.0:
		progress = maxf(0.0, progress - speed * delta)
	var p := _point_at(progress)
	var back := _point_at(maxf(0.0, progress - 0.6)) - p
	if Vector2(back.x, back.z).length() > 0.01:
		rotation.y = atan2(-back.x, -back.z)
	position = p + Vector3(0, Enemy.GROUND_Y - (1.0 - _rise), 0)
	if _rise >= 1.0:
		for e in game.enemies:
			if e.dead or e.flying:
				continue
			if Vector2(e.position.x - p.x, e.position.z - p.z).length() <= GRAB_REACH:
				e.apply_stun(GRAB_STUN)
				game.sfx("grab", p)
				VFX.play(game.world, "wisps", p + Vector3(0, 0.4, 0), Color(0.5, 1.0, 0.4), 0.8)
				e.take_damage(dmg, "magic", source if is_instance_valid(source) else null)
				crumble()
				return
	if life <= 0.0 or progress <= 0.0:
		crumble()


func crumble() -> void:
	if is_queued_for_deletion():
		return
	VFX.crumble(game.world, position)
	game.sfx("crumble", position)
	queue_free()
