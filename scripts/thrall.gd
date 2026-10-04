class_name Thrall
extends Node3D
## A zombie: an enemy that died in a Necromancer's reach, raised to fight for you. It shambles back down the road
## it came along, and the first walker it meets is grabbed (stunned and mauled), after which the zombie crumbles.
## It also crumbles when its time runs out, when it reaches the road's end, or when the wave is over.
## Knights (Hall of Knights) work the same way, but march out onto the road ahead of an enemy, strike "hits" times
## with their hall's attack (each strike pins the foe), then fall back to the hall.

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
var knight := false
var hits := 1           # strikes left before it's spent
var stun := GRAB_STUN
var pkt := {}           # knights strike with their hall's attack
var _swing := 0.0       # knights: seconds until they can strike (or march) again
var _ap: AnimationPlayer
var _walk := ""
var _strike := ""


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


## A knight mustered by Hall of Knights `src`, sent to meet enemy e: it appears on e's road a little ahead of it.
func setup_knight(g: Game, e: Enemy, src: Tower) -> void:
	game = g
	source = src
	knight = true
	route = e.route
	progress = minf(e.progress + 1.6 * GameData.TILE, maxf(e.route_len - 0.2, e.progress))
	var m: Dictionary = src.data["muster"]
	speed = 1.3 * GameData.TILE
	life = float(m["life"])
	stun = float(m["stun"])
	hits = int(m["hits"])
	pkt = src.make_packet()
	pkt["stun"] = []
	var c := KayKit.character("Knight.glb", "Medium", 1.3) if KayKit.available() else {}
	if c.is_empty():
		add_child(Models.cyl(0.25, 0.3, 1.1, Color(0.8, 0.8, 0.9), Vector3(0, 0.55, 0)))
	else:
		KayKit.hold(c, "sword_1handed", "r")
		KayKit.hold(c, "shield_badge_color", "l")
		add_child(c["root"])
		_ap = c["anim"]
		_walk = KayKit.clip(_ap, ["Walking_A"])
		_strike = KayKit.clip(_ap, ["Melee_1H_Attack_Chop", "Melee_1H_Attack_Slice_Diagonal"])
		if _walk != "":
			_ap.play(_walk)
	Models.overlay(self, Models.rim_mat(GameData.FACTIONS[game.faction]["color"]))
	add_to_group("thralls")
	var p := _point_at(progress)
	position = p + Vector3(0, -1.0, 0)
	VFX.smite(game.world, p, Color(1.0, 0.92, 0.6))
	FX.ring(game.world, p + Vector3(0, 0.15, 0), Color(1.0, 0.9, 0.55), 1.0, 0.35)


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
	if knight:
		_knight(delta)
		return
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


func _knight(delta: float) -> void:
	life -= delta
	_rise = minf(1.0, _rise + delta * 3.0)
	_swing -= delta
	if _rise >= 1.0 and _swing <= 0.0 and hits > 0:
		progress = maxf(0.0, progress - speed * delta)
		if _ap and _walk != "" and _ap.current_animation != _walk:
			_ap.play(_walk, 0.15)
	var p := _point_at(progress)
	var back := _point_at(maxf(0.0, progress - 0.6)) - p
	if Vector2(back.x, back.z).length() > 0.01:
		rotation.y = atan2(-back.x, -back.z)
	position = p + Vector3(0, Enemy.GROUND_Y - (1.0 - _rise), 0)
	if _rise >= 1.0 and _swing <= 0.0 and hits > 0:
		for e in game.enemies:
			if e.dead or e.flying:
				continue
			if Vector2(e.position.x - p.x, e.position.z - p.z).length() <= GRAB_REACH:
				e.apply_stun(stun)
				game.apply_hit(pkt, e)
				game.sfx("hit", p)
				VFX.magic_hit(game.world, e.aim_pos(), Color(1.0, 0.9, 0.55))
				hits -= 1
				_swing = 0.8
				if _ap and _strike != "":
					_ap.play(_strike, 0.08, 1.4)
				if hits <= 0:
					life = minf(life, 0.6)   # its last blow lands, then it's gone
				break
	if life <= 0.0 or progress <= 0.0:
		crumble()


func crumble() -> void:
	if is_queued_for_deletion():
		return
	if knight:
		FX.burst(game.world, position + Vector3(0, 0.6, 0), Color(1.0, 0.92, 0.6), 0.9, 0.35)
	else:
		VFX.crumble(game.world, position)
		game.sfx("crumble", position)
	queue_free()
