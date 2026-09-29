class_name Enemy
extends Node3D
## A creep walking a route of waypoints from its portal to the castle.

const HEALTHBAR_SHADER := preload("res://shaders/healthbar.gdshader")
static var _bar_mat: ShaderMaterial

var type_id := ""
var data: Dictionary
var game: Game
var max_hp := 1.0
var hp := 1.0
var speed := 1.0        # world units / sec
## Everything walks faster than the first versions: rounds should be quick, like Tower Dominion's.
const SPEED_MULT := 1.3
var vuln := 0.0          # Hex Tomb curse: extra damage taken
var vuln_time := 0.0
var armor := 0.0
var resist := 0.0
var flying := false
var is_boss := false
var dead := false

var route := PackedVector3Array()
var seg := 0            # index of the waypoint we're walking toward
var progress := 0.0     # distance walked
var route_len := 0.0

var slow_pct := 0.0
var slow_time := 0.0
var stun_time := 0.0
var dot_dps := 0.0
var dot_time := 0.0
var dot_dtype := "magic"
var _special_timer := 0.0
var _anim_t := 0.0

const FLY_HEIGHT := 1.6
## Height of the road surface (Kenney road tiles sit slightly below the grass).
static var GROUND_Y := 0.0

var _pp := Vector3.ZERO   # current point on the route (road surface)
var _body: Node3D
var _base_scale := 1.0
var _anim: AnimationPlayer
var _death_anim := ""
var _bar: MeshInstance3D
var _bar_height := 1.4


func setup(g: Game, id: String, r: PackedVector3Array, hp_mult: float, start_progress := 0.0) -> void:
	game = g
	type_id = id
	data = GameData.ENEMIES[id]
	route = r
	max_hp = float(data["hp"]) * hp_mult
	hp = max_hp
	speed = float(data["speed"]) * GameData.TILE * SPEED_MULT
	armor = data["armor"]
	resist = data["resist"]
	flying = data.get("flying", false)
	is_boss = data.get("boss", false)
	route_len = 0.0
	for i in range(1, route.size()):
		route_len += route[i - 1].distance_to(route[i])
	_anim_t = randf() * 10.0

	var m := Models.enemy(id, data)
	add_child(m["root"])
	Models.overlay(m["root"], Models.foe_mat())
	_body = m["body"]
	_base_scale = _body.scale.x
	_anim = m.get("anim")
	_death_anim = m.get("death", "")
	_bar_height = float(data.get("h", 1.5)) + 0.3 + (FLY_HEIGHT if flying else 0.0)
	_make_bar()
	_set_progress(start_progress)


func _make_bar() -> void:
	if _bar_mat == null:
		_bar_mat = ShaderMaterial.new()
		_bar_mat.shader = HEALTHBAR_SHADER
	var q := QuadMesh.new()
	q.size = Vector2(1.0, 0.14)
	_bar = MeshInstance3D.new()
	_bar.mesh = q
	_bar.material_override = _bar_mat
	_bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_bar.position = Vector3(0, _bar_height, 0)
	_bar.scale = Vector3(2.4 if is_boss else 0.9, 1.6 if is_boss else 1.0, 1.0)
	_bar.set_instance_shader_parameter("bar_color", Color(1.0, 0.35, 0.2) if is_boss else Color(0.35, 0.9, 0.3))
	add_child(_bar)
	_bar.visible = is_boss


func _set_progress(p: float) -> void:
	progress = 0.0
	seg = 1
	_pp = route[0]
	position = _pp
	_advance(p)


func remaining() -> float:
	return route_len - progress


## Point on the road under this enemy (includes road height).
func ground_pos() -> Vector3:
	return _pp


func aim_pos() -> Vector3:
	return position + Vector3(0, float(data.get("h", 1.2)) * 0.5, 0)


## Plays the death animation (if the model has one), then removes the node.
func play_death() -> void:
	dead = true
	if _bar:
		_bar.visible = false
	if _anim and _death_anim != "" and _anim.has_animation(_death_anim):
		_anim.speed_scale = 1.0
		_anim.play(_death_anim)
		var tw := create_tween()
		tw.tween_interval(1.1)
		tw.tween_property(self, "position:y", position.y - 1.2, 0.6)
		tw.tween_callback(queue_free)
	else:
		queue_free()


## Where this enemy will be (on the ground) after `t` seconds at its current pace.
func predict(t: float) -> Vector3:
	var dist := speed * (1.0 - slow_pct) * t
	if stun_time > 0.0:
		dist = max(0.0, dist - speed * stun_time)
	var p := ground_pos()
	var s := seg
	while dist > 0.0 and s < route.size():
		var to := route[s] - p
		var d := to.length()
		if d <= dist:
			p = route[s]
			dist -= d
			s += 1
		else:
			p += to / d * dist
			dist = 0.0
	return p


func _advance(dist: float) -> void:
	while dist > 0.0 and seg < route.size():
		var target := route[seg]
		var to := target - _pp
		var d := to.length()
		if d <= dist:
			_pp = target
			dist -= d
			progress += d
			seg += 1
		else:
			_pp += to / d * dist
			progress += dist
			dist = 0.0
		if d > 0.001:
			var look := Vector3(to.x, 0, to.z)
			if look.length() > 0.01:
				rotation.y = atan2(-look.x, -look.z)
	position.x = _pp.x
	position.z = _pp.z


func _process(delta: float) -> void:
	if dead:
		return
	_anim_t += delta
	_heal_cd -= delta
	vuln_time -= delta
	# status effects
	if dot_time > 0.0:
		dot_time -= delta
		take_damage(dot_dps * delta, dot_dtype, null, true)
		if dead:
			return
	if slow_time > 0.0:
		slow_time -= delta
		if slow_time <= 0.0:
			slow_pct = 0.0
	if data.has("regen"):
		hp = min(max_hp, hp + float(data["regen"]) * delta)
	_do_special(delta)

	var mult := 1.0 - slow_pct
	if stun_time > 0.0:
		stun_time -= delta
		mult = 0.0
	_advance(speed * mult * delta)

	# animation
	var y := _pp.y + GROUND_Y
	if flying:
		y = _pp.y + FLY_HEIGHT + sin(_anim_t * 3.0) * 0.15
	if _anim:
		# imported, rigged model: drive its walk cycle by how fast we're actually moving
		_anim.speed_scale = mult * (1.4 if speed > 3.0 else 1.0)
		if flying:
			_anim.speed_scale = max(_anim.speed_scale, 0.3)
	elif flying:
		var wl := _body.get_node_or_null("WingL") as Node3D
		var wr := _body.get_node_or_null("WingR") as Node3D
		var flap := sin(_anim_t * (6.0 if is_boss else 14.0)) * 0.6
		if wl: wl.rotation.z = flap
		if wr: wr.rotation.z = -flap
	elif mult > 0.0:
		y += abs(sin(_anim_t * 9.0)) * 0.08
		if type_id in ["slime", "slimelet"]:
			var sq := 1.0 + sin(_anim_t * 8.0) * 0.12
			_body.scale = Vector3(sq, 2.0 - sq, sq) * _base_scale
	position.y = y
	# fog of war: enemies are only visible on explored ground
	visible = game.board.is_revealed_at(position)
	if camo:
		_update_camo_look()
	if _punch > 0.0 and not type_id in ["slime", "slimelet"]:
		_punch = maxf(0.0, _punch - delta * 7.0)
		_body.scale = Vector3.ONE * _base_scale * (1.0 + 0.14 * _punch)

	if seg >= route.size():
		game.enemy_leaked(self)


func _do_special(delta: float) -> void:
	if data.has("heal"):
		_special_timer -= delta
		if _special_timer <= 0.0:
			_special_timer = 1.0
			var h: Dictionary = data["heal"]
			var r: float = float(h["radius"]) * GameData.TILE
			var healed := false
			for e in game.enemies:
				if e != self and not e.dead and e.hp < e.max_hp and e.position.distance_to(position) <= r:
					e.heal(float(h["hps"]) * game.hp_mult_for_wave())
					healed = true
			if healed:
				FX.ring(game.world, ground_pos(), Color(0.3, 1.0, 0.4), r, 0.4)
	elif data.has("summon"):
		_special_timer -= delta
		if _special_timer <= 0.0:
			var s: Dictionary = data["summon"]
			_special_timer = float(s["every"])
			for i in int(s["count"]):
				game.spawn_enemy(s["type"], route, max(0.0, progress - 1.0 - i * 1.2))
			FX.ring(game.world, ground_pos(), Color(0.4, 0.9, 1.0), 3.0, 0.5)


var _heal_cd := 0.0


## Shaman healing. It doesn't stack: an enemy takes at most one heal per second, however many shamans are near.
func heal(amount: float) -> void:
	if _heal_cd > 0.0:
		return
	_heal_cd = 0.95
	hp = min(max_hp, hp + amount)
	_update_bar()


## Returns damage actually dealt. Shields soak damage first; magic strips them 1.5x faster,
## shield-breaking towers (shred) 2.5x.
func take_damage(amount: float, dtype: String, source: Tower = null, silent := false, shred := false) -> float:
	if dead:
		return 0.0
	if vuln_time > 0.0:
		amount *= 1.0 + vuln
	if shield > 0.0:
		var mult := (2.5 if shred else (1.5 if dtype == "magic" else 1.0)) * (1.0 + float(game.mods.get("shield_break", 0.0)))
		var soak: float = minf(shield, amount * mult)
		shield -= soak
		amount -= soak / mult
		if shield <= 0.0:
			shield = 0.0
			if _bubble:
				_bubble.queue_free()
				_bubble = null
			FX.burst(game.world, aim_pos(), Color(0.4, 0.7, 1.0), 1.2, 0.25)
			game.sfx("shield", position)
		_update_bar()
		if amount <= 0.0:
			return soak
	if not silent:
		_punch = 1.0
	var red := armor if dtype == "phys" else resist
	var dmg := amount * (1.0 - red)
	hp -= dmg
	if source:
		source.damage_done += dmg
	if game.mods["execute"] > 0.0 and hp > 0.0 and hp < max_hp * game.mods["execute"] and not is_boss:
		dmg += hp
		hp = 0.0
	if hp <= 0.0:
		dead = true
		if source:
			source.kills += 1
		game.enemy_killed(self)
		return dmg
	_update_bar()
	return dmg


func _update_bar() -> void:
	if _bar:
		_bar.visible = is_boss or hp < max_hp or max_shield > 0.0
		_bar.set_instance_shader_parameter("fill", clamp(hp / max_hp, 0.0, 1.0))
	if _shield_bar:
		_shield_bar.visible = shield > 0.0
		_shield_bar.set_instance_shader_parameter("fill", clamp(shield / maxf(max_shield, 1.0), 0.0, 1.0))


# ------------------------------------------------------------------ run traits (Threat Intel)

var mod_trait := ""
var shield := 0.0
var max_shield := 0.0
var camo := false
var detected := false
var _bubble: MeshInstance3D
var _shield_bar: MeshInstance3D
var _punch := 0.0
var _camo_shown := -1


## Applies this run's modifier for the enemy (shield / camo / swift).
func set_trait(t: String) -> void:
	mod_trait = t
	match t:
		"shield":
			max_shield = max_hp * 0.6
			shield = max_shield
			var s := SphereMesh.new()
			var h: float = float(data.get("h", 1.5))
			s.radius = h * 0.62
			s.height = h * 1.24
			_bubble = MeshInstance3D.new()
			_bubble.mesh = s
			_bubble.material_override = Models.mat(Color(0.45, 0.75, 1.0), 0.0, 0.22)
			_bubble.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_bubble.position = Vector3(0, h * 0.5 + (FLY_HEIGHT if flying else 0.0) * 0.0, 0)
			add_child(_bubble)
			var q := QuadMesh.new()
			q.size = Vector2(1.0, 0.1)
			_shield_bar = MeshInstance3D.new()
			_shield_bar.mesh = q
			_shield_bar.material_override = _bar_mat
			_shield_bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_shield_bar.position = Vector3(0, _bar_height + 0.16, 0)
			_shield_bar.scale = _bar.scale
			_shield_bar.set_instance_shader_parameter("bar_color", Color(0.4, 0.75, 1.0))
			add_child(_shield_bar)
			_update_bar()
		"camo":
			camo = true
		"swift":
			speed *= 1.4


## Camouflaged enemies look ghostly until something detects them.
func _update_camo_look() -> void:
	var want := 1 if detected else 0
	if want == _camo_shown:
		return
	_camo_shown = want
	for c in find_children("*", "GeometryInstance3D", true, false):
		if c != _bar and c != _shield_bar:
			(c as GeometryInstance3D).transparency = 0.35 if detected else 0.75


func apply_slow(pct: float, dur: float) -> void:
	if is_boss:
		pct *= 0.5
	if pct >= slow_pct or slow_time <= 0.0:
		slow_pct = pct
	slow_time = max(slow_time, dur)


func apply_vuln(v: float, dur: float) -> void:
	vuln = maxf(vuln if vuln_time > 0.0 else 0.0, v)
	vuln_time = maxf(vuln_time, dur)


## Washed or dragged back along the road (Whirlpool Shrine, Tidal Surge).
func push_back(dist: float) -> void:
	if dead or is_boss:
		return
	_set_progress(maxf(0.0, progress - dist))


func apply_stun(dur: float) -> void:
	if is_boss:
		dur *= 0.25
	stun_time = max(stun_time, dur)


func apply_dot(dps: float, dur: float, dtype: String) -> void:
	if dps >= dot_dps or dot_time <= 0.0:
		dot_dps = dps
		dot_dtype = dtype
	dot_time = max(dot_time, dur)
