class_name Tower
extends Node3D

var id := ""
var data: Dictionary
var game: Game
var cell := Vector2i.ZERO
var level := 1
var cooldown := 0.0
var target_mode := 0
var spent := 0
var kills := 0
var damage_done := 0.0
var on_ley := false
var elevation := 0      # ground level the tower stands on (high ground = more range)
var buff_dmg := 0.0     # from nearby support towers (and ammo depots)
var buff_rate := 0.0
var nb_range := 0.0     # from a neighboring relay station
var spec := -1          # chosen specialization at level III (index into GameData.SPECS[id])
var fx := {}            # that specialization's effects
var cells: Array = []   # every hex the tower covers
var muzzles: Array = [] # its guns (one shot each per volley); everything fires from the centroid
var reach := 0.0        # GameData.reach_offset: added to range so the centroid reaches as far as the old gun hex did
var facing := 4         # side index it faces (Hex.E)
var arc := 360.0        # firing cone in degrees
var _base_scale := 1.0
var _fitted := false    # the model was built to fill the whole footprint
var water_bonus := 0.0  # Blue's Tidebound: extra damage next to water
var line_w := 0.0       # breath towers: width of the straight line they hit (world units); 0 = normal reach
var thralls: Array = [] # Necromancer: its zombies that are still up

## A tower's attack sound: its own ("sfx" in its data), or its attack kind's.
func attack_sfx() -> String:
	return String(data.get("sfx", attack()))

var head: Node3D
var _model: Node3D
var _level_marks: Array = []
var _anim := 0.0
var _recoil := 0.0
var _turrets: Array = []      # KayKit towers with several guns: each turret aims from where it stands
var _muzzle_y := 0.2          # shots leave this far above the head
var _crew: AnimationPlayer    # KayKit crew member's animations (null for other models)
var _crew_idle := ""
var _crew_attack := ""
var _crew_cut := 1.0
var _crew_back := 0.0         # seconds until the crew eases back into its idle
var _spinners: Array = []     # KayKit pieces that turn and bob (floating gems): [node, turn speed, bob height, base y]
var _rig: AnimationPlayer     # Blender towers: the machine's own animations (idle / fire / reload)
var _rig_back := 0.0          # seconds until the rig eases back into its idle
var _muzzle_nodes: Array = [] # Blender towers: markers where shots leave


const SIZE_SCALE := [1.0, 1.15, 1.3, 1.45, 1.55, 1.7, 1.85]


## The node sits at the middle of its footprint; set its position before calling this.
func setup(g: Game, tid: String, anchor: Vector2i, facing_ := 4) -> void:
	game = g
	id = tid
	data = GameData.TOWERS[tid]
	cell = anchor
	facing = facing_
	cells = GameData.footprint(tid, anchor, facing)
	muzzles = GameData.muzzle_cells(tid, anchor, facing)
	arc = GameData.arc_of(tid)
	reach = GameData.reach_offset(tid)
	line_w = float(data.get("line", 0.0)) * GameData.TILE
	target_mode = int(data.get("target", 0))
	var m := Models.tower(tid, data["color"])
	_model = m["root"]
	head = m["head"]
	add_child(_model)
	# everything you own carries your color's accent as a rim light
	Models.overlay(_model, Models.rim_mat(GameData.FACTIONS[game.faction]["color"]))
	_fitted = _model.has_meta("fitted")
	_turrets = _model.get_meta("turrets", [])
	_spinners = _model.get_meta("spinners", [])
	_muzzle_y = float(_model.get_meta("muzzle_y", 0.2))
	_muzzle_nodes = _model.get_meta("muzzles", [])
	if _model.has_meta("rig_ap"):
		_rig = _model.get_meta("rig_ap")
	if _model.has_meta("crew_ap"):
		_crew = _model.get_meta("crew_ap")
		_crew_idle = _model.get_meta("crew_idle")
		_crew_attack = _model.get_meta("crew_attack")
		_crew_cut = float(_model.get_meta("crew_cut", 1.0))
	_base_scale = 1.0 if _fitted else SIZE_SCALE[clampi(cells.size() - 1, 0, SIZE_SCALE.size() - 1)]
	_model.scale = Vector3.ONE * _base_scale
	_model.rotation.y = Hex.dir_yaw(facing)
	cooldown = randf() * 0.3
	_anim = randf() * 10.0


## Is point p inside this tower's reach from a gun at `from` (range and firing arc)?
func reaches(p: Vector3, from: Vector3, r: float) -> bool:
	var dx := p.x - from.x
	var dz := p.z - from.z
	if line_w > 0.0:
		# a straight line ahead, line_w wide and r long
		var fd0 := Hex.dir_world(facing)
		var along := dx * fd0.x + dz * fd0.z
		return along >= -0.5 and along <= r and absf(dx * fd0.z - dz * fd0.x) <= line_w * 0.5
	if dx * dx + dz * dz > r * r:
		return false
	if arc >= 359.0:
		return true
	var v := Vector2(dx, dz)
	if v.length() < 0.01:
		return true
	var fd := Hex.dir_world(facing)
	return v.normalized().dot(Vector2(fd.x, fd.z)) >= cos(deg_to_rad(arc * 0.5)) - 0.001


func attack() -> String:
	return data["attack"]


func is_support() -> bool:
	return attack() == "aura_buff"


func fxf(key: String, default := 0.0) -> float:
	return float(fx.get(key, default))


func damage() -> float:
	var d: float = float(data["dmg"]) * GameData.LEVEL_DMG[level - 1] * (1.0 + fxf("dmg"))
	d *= game.dmg_mult(data.get("dtype", "phys"))
	d *= 1.0 + buff_dmg
	if on_ley:
		d *= 1.0 + GameData.LEY_BONUS + game.mods["ley"]
	d *= 1.0 + float(game.masterwork.get(id, 0.0)) + game.hero_tower_bonus(id)
	d *= (1.0 + water_bonus) * (1.0 + float(game.mods.get("dmg_all", 0.0)))
	return d


func range_world() -> float:
	return float(data["range"]) * GameData.LEVEL_RANGE[level - 1] * GameData.TILE * game.mods["range"] \
		* (1.0 + GameData.ELEVATION_RANGE * elevation) * (1.0 + fxf("range") + nb_range) + reach


func fire_rate() -> float:
	return float(data["rate"]) * GameData.LEVEL_RATE[level - 1] * (1.0 + game.mods["rate"] + buff_rate + game.haste_bonus() + fxf("rate"))


func buff() -> Dictionary:
	var out := {}
	var b: Dictionary = data.get("buff", {})
	for k in b:
		out[k] = float(b[k]) * GameData.LEVEL_BUFF[level - 1]
	if fx.has("buff_dmg"):
		out["dmg"] = float(out.get("dmg", 0.0)) + fxf("buff_dmg")
	if fx.has("buff_rate"):
		out["rate"] = float(out.get("rate", 0.0)) + fxf("buff_rate")
	var am := float(game.hero_fx.get("aura_mult", 1.0))
	for k in out:
		out[k] = float(out[k]) * am
	return out


## Hex Tomb curse: enemies in range take this much extra damage from everything.
func curse() -> float:
	return (float(data.get("curse", 0.0)) * GameData.LEVEL_BUFF[level - 1] + fxf("curse")) * float(game.hero_fx.get("aura_mult", 1.0))


## Towers with detection (or a detecting specialization / hero) reveal camouflaged enemies in range.
func detects() -> bool:
	return data.get("detect", false) or fx.get("detect", false) or game.hero_fx.get("detect_all", false)


func upgrade_cost() -> int:
	if level >= 3:
		return -1
	var disc := 1.0 - float(game.hero_fx.get("upgrade_discount", 0.0))
	return int(round(float(data["cost"]) * GameData.UPGRADE_COST[level - 1] * game.cost_mult() * disc))


func sell_value() -> int:
	return int(spent * GameData.SELL_REFUND)


## Level II -> III needs a specialization: pass 0 or 1.
func upgrade(spec_index := -1) -> void:
	level += 1
	if level == 3 and spec_index >= 0 and GameData.SPECS.has(id):
		spec = spec_index
		fx = GameData.SPECS[id][spec_index]["fx"]
	var s := (1.0 + (level - 1) * (0.03 if _fitted else 0.08)) * _base_scale
	_model.scale = Vector3(s, s, s)
	var rr := sqrt(float(cells.size())) * 0.8 if _fitted else 0.72 * _base_scale
	var ring := Models.torus(rr, rr + 0.1 * (1.0 + float(_fitted)), GameData.FACTIONS[game.faction]["color"], Vector3(0, 0.3 + 0.12 * (level - 2), 0), 1.2)
	add_child(ring)
	_level_marks.append(ring)
	VFX.upgrade(game.world, global_position, GameData.FACTIONS[game.faction]["color"], cells.size())


func can_hit(e: Enemy) -> bool:
	if e.camo and not e.detected:
		return false
	return (e.flying and data.get("air", false)) or (not e.flying and data.get("ground", false))


func _flat_dist(a: Vector3, b: Vector3) -> float:
	return Vector2(a.x - b.x, a.z - b.z).length()


## Targets are picked from the footprint's centroid. First / Last compare remaining() (road distance left for
## walkers, straight-line distance left for fliers), so ground and air enemies share one pool.
func find_target() -> Enemy:
	var r := range_world()
	var best: Enemy = null
	var best_score := -INF
	for e in game.enemies:
		if e.dead or not can_hit(e) or not reaches(e.position, position, r):
			continue
		var score := 0.0
		match target_mode:
			0: score = -e.remaining()
			1: score = e.remaining()
			2: score = e.hp
			3: score = -_flat_dist(e.position, position)
		if score > best_score:
			best_score = score
			best = e
	return best


func make_packet() -> Dictionary:
	var dmg := damage()
	var dot: Array = fx.get("dot", data.get("dot", []))
	if dot.size() == 2:
		# poison scales with everything that scales the tower's hit damage
		var scale := dmg / float(data["dmg"]) if not fx.has("dot") else dmg / (float(data["dmg"]) * GameData.LEVEL_DMG[2])
		dot = [float(dot[0]) * scale * fxf("dot_mult", 1.0) * float(game.hero_fx.get("poison_mult", 1.0)), dot[1]]
	var slow: Array = fx.get("slow", data.get("slow", []))
	if slow.size() == 2:
		slow = [minf(0.8, float(slow[0]) * float(game.hero_fx.get("slow_mult", 1.0))), slow[1]]
	return {
		"dmg": dmg,
		"tower_id": id,
		"dtype": data.get("dtype", "phys"),
		"splash": (float(data.get("splash", 0.0)) + fxf("splash")) * GameData.TILE,
		"slow": slow,
		"dot": dot,
		"stun": fx.get("stun", data.get("stun", [])),
		"air_bonus": float(data.get("air_bonus", 1.0)),
		"air": data.get("air", false),
		"ground": data.get("ground", false),
		"shred": data.get("shred", false) or fx.get("shred", false),
		"push": fx.get("push", data.get("push", [])),
		"pct": fxf("pct", float(data.get("pct", 0.0))),
		"vuln": fx.get("vuln", data.get("vuln", [])),
		"boss_bonus": float(data.get("boss_bonus", 0.0)),
		"tower": self,
	}


func _process(delta: float) -> void:
	_anim += delta
	for s in _spinners:
		(s[0] as Node3D).rotate_y(float(s[1]) * delta)
		(s[0] as Node3D).position.y = float(s[3]) + sin(_anim * 1.7) * float(s[2])
	if _crew_back > 0.0:
		_crew_back -= delta
		if _crew_back <= 0.0 and _crew_idle != "":
			_crew.play(_crew_idle, 0.25)
	if _rig_back > 0.0:
		_rig_back -= delta
		if _rig_back <= 0.0 and _rig.has_animation("idle"):
			_rig.speed_scale = 1.0
			_rig.play("idle", 0.2)
	var a := attack()
	var kk := _model.has_meta("kaykit")
	if a == "aura_buff":
		if not kk:
			head.position.y += sin(_anim * 2.0) * 0.002
		if id == "banner":
			head.rotation.y = sin(_anim * 1.3) * 0.4
		else:
			head.rotate_y(delta * 0.8)
		return
	cooldown -= delta
	if _recoil > 0.0:
		_recoil = max(0.0, _recoil - delta * 4.0)
	if a == "aura_dmg":
		if id == "chapel":
			head.rotate_y(delta * 1.2)
		if cooldown <= 0.0 and _any_in_range():
			cooldown = 1.0 / fire_rate()
			_pulse()
			_crew_act()
			_rig_act()
		return
	if a == "aura_curse":
		# no attack: every half second, everything in reach is cursed to take more damage
		if cooldown <= 0.0:
			cooldown = 0.5
			var r := range_world()
			var v := curse()
			var sl: Array = fx.get("slow", [])
			for e in game.enemies:
				if not e.dead and _in_aura(e, r):
					e.apply_vuln(v, 0.7)
					if sl.size() == 2:
						e.apply_slow(sl[0], sl[1])
		return
	if id in ["arcane", "storm", "rootbinder", "moonwell"] and not kk:
		head.position.y += sin(_anim * 2.5) * 0.003
	var t := find_target()
	if t == null:
		return
	if not data.get("static", false):
		# each gun turns from where it stands (KayKit crews and turrets can sit off the footprint's middle)
		head.rotation.y = lerp_angle(head.rotation.y, _aim_yaw(head, t.position), min(1.0, delta * 12.0))
		for tn in _turrets:
			if tn != head:
				(tn as Node3D).rotation.y = lerp_angle((tn as Node3D).rotation.y, _aim_yaw(tn, t.position), min(1.0, delta * 12.0))
	if cooldown <= 0.0:
		cooldown = 1.0 / fire_rate()
		_fire(t)
		_crew_act()
		_rig_act()


## The yaw (inside the tower model) that turns gun node n's -Z toward point p.
func _aim_yaw(n: Node3D, p: Vector3) -> float:
	var to := p - n.global_position
	return atan2(-to.x, -to.z) - _model.rotation.y


## Auras reach around the centroid; cone-shaped ones (the Flame Belcher) only in front.
func _in_aura(e: Enemy, r: float) -> bool:
	return reaches(e.position, position, r)


func _any_in_range() -> bool:
	var r := range_world()
	for e in game.enemies:
		if not e.dead and can_hit(e) and _in_aura(e, r):
			return true
	return false


func _pulse() -> void:
	var r := range_world()
	var pkt := make_packet()
	for e in game.enemies.duplicate():
		if not e.dead and can_hit(e) and _in_aura(e, r):
			game.apply_hit(pkt, e)
	if arc < 359.0:
		# a cone of fire (Flame Belcher)
		var fwd := Hex.dir_world(facing)
		VFX.play(game.world, "cone", position + fwd * reach + Vector3(0, 0.6, 0), Color.WHITE, clampf(r / 8.0, 0.5, 1.6), fwd)
	else:
		FX.ring(game.world, position + Vector3(0, 0.15, 0), data["color"], r, 0.45)
		if data.has("stun"):
			VFX.stomp(game.world, position, r)
		elif id == "mass_grave":
			VFX.play(game.world, "dirt", position, Color.WHITE, 1.2)
	game.sfx(String(data.get("sfx", "pulse")), global_position)


## A KayKit crew member plays its attack clip (sped up to fit between shots), then eases back into its idle.
func _crew_act() -> void:
	if _crew == null or _crew_attack == "":
		return
	var gap := 1.0 / maxf(fire_rate(), 0.05)
	var length := _crew.get_animation(_crew_attack).length * _crew_cut
	var speed := clampf(length / (gap * 0.85), 1.0, 3.0)
	_crew.play(_crew_attack, 0.08, speed)
	_crew.seek(0.0, true)
	_crew_back = length / speed


## A Blender tower's machine plays "fire" then "reload", sped up to fit between shots, then eases back into its idle.
func _rig_act() -> void:
	if _rig == null or not _rig.has_animation("fire"):
		return
	var gap := 1.0 / maxf(fire_rate(), 0.05)
	var length := _rig.get_animation("fire").length
	var reload := _rig.get_animation("reload").length if _rig.has_animation("reload") else 0.0
	var speed := clampf((length + reload) / (gap * 0.9), 1.0, 4.0)
	_rig.clear_queue()
	_rig.speed_scale = speed
	_rig.play("fire", 0.04)
	_rig.seek(0.0, true)
	if reload > 0.0:
		_rig.queue("reload")
	_rig_back = (length + reload) / speed


func _muzzle() -> Vector3:
	return head.global_position + Vector3(0, _muzzle_y, 0)


## Where shot i of a volley leaves: the head above the centroid. Two-gun towers fire from barrels either side of it
## (or from their own turrets, on KayKit towers).
func _muzzle_world(i: int) -> Vector3:
	if not _muzzle_nodes.is_empty():
		return (_muzzle_nodes[i % _muzzle_nodes.size()] as Node3D).global_position
	if _turrets.size() > 1:
		return (_turrets[i % _turrets.size()] as Node3D).global_position + Vector3(0, _muzzle_y, 0)
	var p := _muzzle()
	var n := muzzles.size()
	if n > 1:
		var fd := Hex.dir_world(facing)
		p += Vector3(-fd.z, 0, fd.x) * (float(i) - (n - 1) * 0.5) * 0.9
	return p


func _fire(t: Enemy) -> void:
	var r := range_world()
	match attack():
		"breath":
			_breathe(r)
			return
		"grasp":
			_grasp(t, r)
			return
	for i in muzzles.size():
		_fire_at(t, _muzzle_world(i))
	# Volley / Barrage / Swarm specializations: extra shots at the next-best targets
	var extra := int(fxf("multishot"))
	if extra > 0:
		var others: Array = []
		for e in game.enemies:
			if e != t and not e.dead and can_hit(e) and reaches(e.position, position, r):
				others.append(e)
		others.sort_custom(func(a, b): return a.remaining() < b.remaining())
		for i in mini(extra, others.size()):
			_fire_at(others[i], _muzzle_world(0))
	game.sfx(attack_sfx(), global_position)


## Fat Dragon: fire along the whole line ahead, burning everything in it.
func _breathe(r: float) -> void:
	var pkt := make_packet()
	for e in game.enemies.duplicate():
		if not e.dead and can_hit(e) and reaches(e.position, position, r):
			game.apply_hit(pkt, e)
	var fd := Hex.dir_world(facing)
	VFX.breath(game.world, position + fd * reach + Vector3(0, 0.7, 0), fd, r - reach)
	_recoil = 1.0
	game.sfx(attack_sfx(), global_position)


## Kraken: seize the target and the next ones along (up to "grasp"), crushing and holding them.
func _grasp(t: Enemy, r: float) -> void:
	var victims: Array = [t]
	var others: Array = game.enemies.filter(func(e): return e != t and not e.dead and can_hit(e) and reaches(e.position, position, r))
	others.sort_custom(func(a, b): return a.remaining() < b.remaining())
	var n := int(data.get("grasp", 3)) + int(fxf("grasp"))
	for e in others:
		if victims.size() >= n:
			break
		victims.append(e)
	var pkt := make_packet()
	for e in victims:
		game.apply_hit(pkt, e)
		VFX.splash(game.world, e.ground_pos() + Vector3(0, 0.3, 0), data["color"])
		FX.ring(game.world, e.ground_pos() + Vector3(0, 0.1, 0), data["color"], 0.9, 0.35)
	_recoil = 1.0
	game.sfx(attack_sfx(), global_position)


func _fire_at(t: Enemy, from: Vector3) -> void:
	var pkt := make_packet()
	var col: Color = data["color"]
	match attack():
		"arrow":
			var p := Projectile.new()
			var spd := 34.0 if id != "hive" else 26.0
			game.world.add_child(p)
			p.setup_homing(game, pkt, from, t, spd, "arrow" if id != "hive" and id != "thorn" else "dart", col)
		"orb":
			var p := Projectile.new()
			game.world.add_child(p)
			p.setup_homing(game, pkt, from, t, 15.0, "orb", col)
		"bolt":
			var p := Projectile.new()
			game.world.add_child(p)
			var dir := t.aim_pos() - from
			p.setup_bolt(game, pkt, from, dir.normalized(), range_world() * 1.15, 32.0, col)
		"lob":
			var p := Projectile.new()
			game.world.add_child(p)
			var flight := 0.9 if id != "bombard" else 0.55
			p.setup_lob(game, pkt, from, t.predict(flight), flight, col)
		"chain":
			game.chain_lightning(pkt, t, int(data.get("chain", 3)) + int(fxf("chain")), from, col)
		"smite":
			# a pillar of light straight down on the target
			var sp := t.position
			for e in game.enemies.duplicate():
				if not e.dead and can_hit(e) and _flat_dist(e.position, sp) <= maxf(pkt["splash"], 0.6):
					game.apply_hit(pkt, e)
			VFX.smite(game.world, t.ground_pos(), col)
			FX.ring(game.world, t.ground_pos() + Vector3(0, 0.15, 0), col, maxf(pkt["splash"], 1.0), 0.4)
		"slam":
			var gp := t.ground_pos()
			for e in game.enemies.duplicate():
				if not e.dead and can_hit(e) and _flat_dist(e.position, gp) <= pkt["splash"]:
					game.apply_hit(pkt, e)
			FX.ring(game.world, gp + Vector3(0, 0.15, 0), Color(0.6, 0.45, 0.3), pkt["splash"], 0.3)
			VFX.stomp(game.world, gp, pkt["splash"])
	_recoil = 1.0
