class_name Playtest
extends RefCounted
## Headless playtest bots: `--autotest=<faction> --skill=low|mid|high` (with --difficulty, --seed, --fresh).
## mid is the original autotest bot (Game._auto_*). low plays like a newcomer: slow to react, random drafts and
## facings, few upgrades, no Builders, talents bought late and at random. high plays like a veteran: it searches every
## spot near the road for the one that covers the most of every route, values towers by damage per gold, saves for
## better towers, upgrades its proven towers with the stronger specialization, guards the flight lines before fliers
## come, raises its best towers with Builders and drafts with the threats in mind.
## Tiles: low drops them anywhere; mid goes for long roads and merges with a little thought for open ground; high plans
## ahead for its big blueprints: it previews each placement's ground (Board.plan_ground), takes the one that opens a
## spot for a 4-5 hex tower it holds, rerolls with Runes when none does, and levels a nearly-flat patch with Builders
## and Diggers.
## Every run ends with one `PLAYTEST {json}` line: the result plus a per-wave log (health, leaks, unspent gold, wave
## length, crowds) and each tower's damage, for tools/playtest_report.py.

const SKILLS := ["low", "mid", "high"]

var g: Game
var skill := 1
var log := {"waves": [], "built": [], "upgrades": [], "talents": [], "picks": [], "raised": 0, "saved_phases": 0}
var sig_fired := 0
var _cur := {}            # the wave being fought: its start snapshot
var _was_wave := false
var _act_t := 0.0
var _pts: Array = []      # high: [Vector3, weight] road points of every route (shared stretches count more)
var _air: Array = []      # high: [Vector3, weight] flight-line points
var _cover := {}          # high: tower -> its coverage, this phase
var _cands: Array = []    # high: cells near the road worth trying
var _phase_key := -1


func _init(game: Game, s: int) -> void:
	g = game
	skill = s


# ------------------------------------------------------------------ the run log

## Every frame (game seconds): wave start and end snapshots, wave length and the biggest crowd.
func tick(delta: float) -> void:
	var in_wave := g.state == Game.S.WAVE
	if in_wave and not _was_wave:
		_cur = {"w": g.wave, "hp0": g.hp, "gold0": g.gold, "towers": g.towers.size(), "t": 0.0, "alive": 0,
			"boss": g.boss_plan.get(g.wave, ""), "n": g.spawn_queue.size()}
	if in_wave:
		_cur["t"] = float(_cur["t"]) + delta
		_cur["alive"] = maxi(int(_cur["alive"]), g.enemies.size())
	if _was_wave and not in_wave and not _cur.is_empty():
		_close_wave()
	_was_wave = in_wave


func _close_wave() -> void:
	_cur["hp1"] = g.hp
	_cur["leaks"] = g._wave_leaks.duplicate()
	_cur["gold1"] = g.gold
	log["waves"].append(_cur)
	_cur = {}


func report(victory: bool) -> void:
	if not _cur.is_empty():
		_close_wave()
	var dmg := {}
	var kills := {}
	var count := {}
	var levels := {}
	for t in g.towers:
		dmg[t.id] = float(dmg.get(t.id, 0.0)) + t.damage_done
		kills[t.id] = int(kills.get(t.id, 0)) + t.kills
		count[t.id] = int(count.get(t.id, 0)) + 1
		levels[t.id] = int(levels.get(t.id, 0)) + t.level
	var out := {"faction": g.faction, "hero": g.hero, "difficulty": g.difficulty, "skill": SKILLS[skill], "victory": victory,
		"wave": g.wave, "hp": g.hp, "max_hp": g.max_hp, "gold": g.gold, "kills": g.run_stats.get("kills", 0),
		"leaked": g.run_stats.get("leaked", 0), "biome": g.board.biome_id, "fronts": g.board.battlefronts(),
		"threats": g.threats.map(func(t): return "%s@%d" % [t["id"], t["wave"]]), "sig": sig_fired,
		"talents": g.talents.keys(), "owned": g.owned, "dmg": dmg, "tkills": kills, "count": count, "levels": levels,
		"masterwork": g.masterwork.keys(),
		"towers": g.towers.map(func(t): return [t.id, t.built_wave, t.level, t.spec, int(t.damage_done)]),
		"unplaced": _unplaced()}
	out.merge(log)
	print("PLAYTEST " + JSON.stringify(out))


## Owned blueprints that would fit nowhere right now (no clear, level patch near a road): [id, copies].
func _unplaced() -> Array:
	var out: Array = []
	for tid in g.owned:
		if int(g.owned[tid]) <= 0:
			continue
		var fits := false
		for pc in g.board.path_cells:
			for c in Hex.disc(pc, 3):
				for f in 6:
					if g.board.can_build_all(GameData.footprint(tid, c, f)):
						fits = true
						break
				if fits:
					break
			if fits:
				break
		if not fits:
			out.append([tid, int(g.owned[tid])])
	return out


# ------------------------------------------------------------------ shared

func _affordable() -> Array:
	return g.owned.keys().filter(func(k): return int(g.owned[k]) > 0 and g.gold >= g.tower_cost(k))


func _place(tid: String, c: Vector2i, f: int) -> bool:
	var before := g.towers.size()
	g.placing = tid
	g.place_facing = f
	g.try_place(c)
	g.placing = ""
	if g.towers.size() > before:
		log["built"].append([tid, g.wave])
		return true
	return false


func _upgrade(t: Tower, spec: int) -> bool:
	var lv := t.level
	g.select_tower(t)
	g.upgrade_selected(spec if g.needs_spec(t) else -1)
	g.deselect()
	if t.level > lv:
		log["upgrades"].append([t.id, t.level, t.spec, g.wave])
		return true
	return false


func _buy_talent(path: String, idx: int) -> void:
	var id: String = g.talent_tree()[path]["nodes"][idx]["id"]
	var rank := g.talent_rank(id)
	g.buy_talent(path, idx)
	if g.talent_rank(id) > rank:
		log["talents"].append([id, g.wave])


## A rough damage per second for a tower at a level (and specialization): hits per second times how many enemies
## each attack tends to reach. cap: the most one hit can usefully deal (overkill on small enemies is wasted).
static func est_dps(tid: String, level := 1, fx := {}, cap := INF) -> float:
	var d: Dictionary = GameData.TOWERS[tid]
	var a := String(d["attack"])
	if a == "aura_buff" or a == "aura_curse":
		return 0.0
	var dmg: float = minf(cap, float(d["dmg"]) * GameData.LEVEL_DMG[level - 1] * (1.0 + float(fx.get("dmg", 0.0))))
	var rate: float = float(d["rate"]) * GameData.LEVEL_RATE[level - 1] * (1.0 + float(fx.get("rate", 0.0)))
	var targets := 1.0 + 0.9 * (float(d.get("splash", 0.0)) + float(fx.get("splash", 0.0)))
	match a:
		"chain": targets *= 1.0 + 0.5 * (float(d.get("chain", 3)) + float(fx.get("chain", 0)))
		"bolt": targets *= 2.0 if d.get("pierce", false) else 1.0
		"beam", "breath", "aura_dmg": targets *= 2.5
		"grasp": targets *= 0.8 * (float(d.get("grasp", 3)) + float(fx.get("grasp", 0)))
		"muster": targets *= 1.3 * float(d["muster"]["hits"])
		"lob": targets *= 0.75   # shells land where the target was going: some miss
	targets *= 1.0 + 0.8 * float(fx.get("multishot", 0))
	var dps: float = dmg * rate * targets
	var dot: Array = fx.get("dot", d.get("dot", []))
	if dot.size() == 2:
		dps += float(dot[0]) * minf(1.0, rate * float(dot[1])) * targets
	for k in ["slow", "stun", "push"]:
		if d.has(k) or fx.has(k):
			dps *= 1.12
	return dps


## est_dps with this wave's overkill cap: a hit bigger than a couple of this wave's enemies is partly wasted.
func _dps(tid: String, level := 1, fx := {}) -> float:
	return est_dps(tid, level, fx, 120.0 * _hp_scale())


func _hp_scale() -> float:
	return WaveBuilder.hp_mult(g.wave + 1) * g.diff_mult("hp", g.wave + 1)


func _air_coming() -> bool:
	if g._wave_has_fliers(g.next_wave_list):
		return true
	for t in g.threats:
		if g.threat_known(t) and int(t["wave"]) <= g.wave + 3 \
				and GameData.ENEMIES[GameData.THREATS[t["id"]]["enemy"]].get("flying", false):
			return true
	for w in g.boss_plan:
		if int(w) - g.wave <= 3 and int(w) > g.wave and GameData.ENEMIES[g.boss_plan[w]].get("flying", false):
			return true
	return false


func _need_detect() -> bool:
	var have := g.towers.any(func(t): return t.detects())
	if have:
		return false
	for t in g.threats:
		if g.threat_known(t) and GameData.THREATS[t["id"]].get("trait", "") == "camo" and int(t["wave"]) <= g.wave + 3:
			return true
	return false


# ------------------------------------------------------------------ decisions, by skill

## The autotest's build / wave tick (every 0.25 game seconds).
func build_tick() -> void:
	match skill:
		0: _low_build()
		1: g._auto_build()
		2: _high_build()


func pick_pair() -> int:
	var i: int
	match skill:
		0: i = g.rng.randi() % g.choice_options.size()
		2: i = _high_pick_pair()
		_: i = g._auto_pick_pair()
	log["picks"].append(g.choice_options[i]["items"].map(func(it): return String(it.get("tower", it["kind"]))))
	return i


func expand() -> void:
	if skill == 0:
		_low_expand()
	else:
		_plan_expand(skill == 2)


## Representative big shapes for "open ground": 5-hex arrow (Trebuchet) and battery (Royal Bombard), shared by every color.
const BIG_PROBES := ["trebuchet", "bombard"]


## Owned blueprints of 4-5 hex towers that fit nowhere right now (what a planner wants room for).
func _homeless_big() -> Array:
	var out: Array = []
	for tid in g.owned:
		if int(g.owned[tid]) > 0 and (GameData.shape_of(tid)["cells"] as Array).size() >= 4 and not g._fits_somewhere(tid):
			out.append(tid)
	return out


## How a tile placement scores: long roads and merges (and few new battlefronts), plus open ground for big towers.
func _tile_score(plan: Dictionary, space_w: float, homeless: Array, fronts: int) -> float:
	var road_len := 0
	for r in plan["roads"]:
		road_len += r.size()
	var score: float = road_len + g.rng.randf() * 2.0
	score += 6.0 * (plan["merges"].size() - 1)
	score -= (3.0 + 2.0 * fronts) * maxf(0.0, float(plan["new_ports"]) - 1.0)
	if space_w <= 0.0 and homeless.is_empty():
		return score
	var ground: Dictionary = g.board.plan_ground(plan)
	var anchors: Array = ground.keys().filter(func(c): return ground[c][0])
	var patches := 0
	for tid in BIG_PROBES:
		for c in anchors:
			for f in [0, 2, 4]:
				if g.board.can_build_all_with(GameData.footprint(tid, c, f), ground):
					patches += 1
					break
	score += space_w * minf(float(patches), 6.0)
	for tid in homeless:
		var fits := false
		for c in anchors:
			for f in 6:
				if g.board.can_build_all_with(GameData.footprint(tid, c, f), ground):
					fits = true
					break
			if fits:
				break
		if fits:
			score += 14.0
	return score


func _plan_expand(veteran: bool) -> void:
	var homeless: Array = _homeless_big() if veteran else []
	var space_w := 1.0 if veteran else 0.3
	var fronts: int = g.board.battlefronts()
	var cards: Array = g._roll_tile_cards(1)
	for attempt in 3:
		var best := {}
		var best_s := -INF
		for c in cards:
			for p in g._card_placements(c):
				var plan: Dictionary = g.board.plan_tile(p[0], c, p[1])
				var s := _tile_score(plan, space_w, homeless, fronts)
				if s > best_s:
					best_s = s
					best = plan
		# reroll a tile that adds battlefronts on a busy realm, or (veteran) one with no room for a big blueprint held
		var bad_front := not best.is_empty() and int(best["new_ports"]) > 1 and fronts >= 3
		var no_room := veteran and not homeless.is_empty() and best_s < 14.0
		if attempt < 2 and g.recon >= GameData.REROLL_COST and (bad_front or no_room):
			g.recon -= GameData.REROLL_COST
			log["rerolls"] = int(log.get("rerolls", 0)) + 1
			cards = g._roll_tile_cards(1)
			continue
		if not best.is_empty():
			g.board.commit_tile(best, g.wave + 1)
			g.run_stats["tiles"] = int(g.run_stats.get("tiles", 0)) + 1
			g.recompute_buffs()
			g._claim_with_towers()
		return


## Veteran: a big blueprint has nowhere to go, but a patch near the road is clear and only uneven: level it with
## Builders (raise the low hexes) and Diggers (lower the high ones). True if it did.
func _level_for_big() -> bool:
	if g.builders + g.diggers <= 0:
		return false
	for tid in _homeless_big():
		if g.gold < g.tower_cost(tid) * 0.6:
			continue
		var best: Array = []
		var best_v := 0.0
		for c in _cands:
			for f in 6:
				var cells := GameData.footprint(tid, c, f)
				if not cells.all(func(x): return g.board.can_build(x)):
					continue
				var levels: Array = cells.map(func(x): return g.board.level_at(x))
				for L in [levels.min(), levels.max()]:
					var ups: Array = []
					var downs: Array = []
					for i in cells.size():
						for k in absi(int(L) - int(levels[i])):
							(ups if int(levels[i]) < int(L) else downs).append(cells[i])
					if ups.size() > g.builders or downs.size() > g.diggers or ups.size() + downs.size() == 0:
						continue
					if not ups.all(func(x): return g.board.can_raise(x)) or not downs.all(func(x): return g.board.can_lower(x)):
						continue
					var v := _cover_at(tid, g.footprint_center(cells), f, _reach(tid, c)) / float(1 + ups.size() + downs.size())
					if v > best_v:
						best_v = v
						best = [ups, downs]
		if best.is_empty():
			continue
		for x in best[0]:
			g.placing = Game.RAISE
			g.try_raise(x)
		for x in best[1]:
			g.placing = Game.DIG
			g.try_dig(x)
		g.placing = ""
		log["leveled"] = int(log.get("leveled", 0)) + 1
		_phase_key = -1
		return true
	return false


# ---- low: a newcomer

func _low_build() -> void:
	_act_t -= 0.25
	if g.state == Game.S.WAVE and _act_t > 0.0:
		return
	_act_t = 6.0   # reacts every few seconds during a wave
	if g.wave >= 6 and g.gold >= 300:
		var open: Array = []
		for path in g.talent_tree():
			for idx in (g.talent_tree()[path]["nodes"] as Array).size():
				if g.talent_state(path, idx) == "open":
					open.append([path, idx])
		if not open.is_empty():
			var o: Array = open[g.rng.randi() % open.size()]
			if g.gold >= g.talent_cost(o[0], o[1]):
				_buy_talent(o[0], o[1])
	for attempt in 3:
		if g.towers.size() > 2 and g.rng.randf() < 0.15:
			var t: Tower = g.towers[g.rng.randi() % g.towers.size()]
			if t.upgrade_cost() > 0 and g.gold >= t.upgrade_cost():
				_upgrade(t, g.rng.randi() % 2)
				continue
		var choices := _affordable()
		if choices.is_empty():
			return
		var tid: String = choices[g.rng.randi() % choices.size()]
		var roads: Array = g.board.path_cells.keys()
		var ports: Array = g.board.open_ports.keys()
		var route: PackedVector3Array = g.board.route_from(ports[g.rng.randi() % ports.size()]) if not ports.is_empty() else PackedVector3Array()
		var r := float(GameData.TOWERS[tid]["range"]) * GameData.TILE
		var best := Board.NONE
		var best_f := 4
		var best_s := -1.0
		for k in 10:
			var c: Vector2i = (Hex.disc(roads[g.rng.randi() % roads.size()], 2) as Array)[g.rng.randi() % 19]
			var f := g.rng.randi() % 6
			var cells := GameData.footprint(tid, c, f)
			if not g.board.can_build_all(cells):
				continue
			var wp := g.footprint_center(cells)
			var s := 0.0
			for p in route:
				if Vector2(p.x - wp.x, p.z - wp.z).length() <= r:
					s += 1.0
			if s > best_s:
				best_s = s
				best = c
				best_f = f
		if best != Board.NONE:
			_place(tid, best, best_f)


func _low_expand() -> void:
	var cards := g._roll_tile_cards(1)
	var opts: Array = []
	for c in cards:
		for p in g._card_placements(c):
			opts.append(g.board.plan_tile(p[0], c, p[1]))
	opts = opts.filter(func(p): return not p.is_empty())
	if opts.is_empty():
		return
	var plan: Dictionary = opts[g.rng.randi() % opts.size()]
	g.board.commit_tile(plan, g.wave + 1)
	g.run_stats["tiles"] = int(g.run_stats.get("tiles", 0)) + 1
	g.recompute_buffs()
	g._claim_with_towers()


# ---- high: a veteran

func _phase_setup() -> void:
	# road points, weighted by how likely an enemy walks them; flight lines when fliers are near
	var key := g.board.placed.size() * 1000 + g.towers.size() * 10 + g.wave
	if key == _phase_key:
		return
	_phase_key = key
	var acc := {}
	for pc in g.board.open_ports:
		var rs: Array = g.board.routes_from(pc)
		var best := float(rs[0][1])
		var ws: Array = []
		var total := 0.0
		for r in rs:
			var w := pow(best / maxf(1.0, float(r[1])), 2.0)
			ws.append(w)
			total += w
		for i in rs.size():
			for p in (rs[i][0] as PackedVector3Array):
				var k := Vector2i(roundi(p.x * 2.0), roundi(p.z * 2.0))
				if not acc.has(k):
					acc[k] = [p, 0.0]
				acc[k][1] = float(acc[k][1]) + float(ws[i]) / total
	_pts = acc.values()
	_air = []
	var aw := 1.6 if _air_coming() else 0.25
	for p in g._flight_points():
		_air.append([p, aw])
	var seen := {}
	_cands = []
	for pc in g.board.path_cells:
		for c in Hex.disc(pc, 3):
			if not seen.has(c):
				seen[c] = true
				_cands.append(c)
	# how much damage already reaches each point: well-defended stretches count for less (spread the defense)
	for pts in [_pts, _air]:
		for pw in pts:
			pw.append(0.0)
	for t in g.towers:
		if t.is_support():
			continue
		var r: float = t.range_world()
		var dps := _dps(t.id, t.level, t.fx)
		var sets: Array = []
		if t.data.get("ground", false):
			sets.append(_pts)
		if t.data.get("air", false):
			sets.append(_air)
		for pts in sets:
			for pw in pts:
				var p: Vector3 = pw[0]
				if Vector2(p.x - t.position.x, p.z - t.position.z).length() <= r:
					pw[2] = float(pw[2]) + dps
	_cover.clear()
	for t in g.towers:
		_cover[t] = _cover_at(t.id, t.position, t.facing, t.range_world())


func _reach(tid: String, level_c: Vector2i) -> float:
	return float(GameData.TOWERS[tid]["range"]) * GameData.TILE * float(g.mods["range"]) \
		* (1.0 + GameData.ELEVATION_RANGE * g.board.level_at(level_c)) + GameData.reach_offset(tid)


func _cover_at(tid: String, wp: Vector3, f: int, r: float) -> float:
	var d: Dictionary = GameData.TOWERS[tid]
	var arc := GameData.arc_of(tid)
	var fd := Hex.dir_world(f)
	var lw := float(d.get("line", 0.0)) * GameData.TILE
	var need := 30.0 * _hp_scale()   # the damage a stretch of road wants before more stops paying off
	var s := 0.0
	var sets: Array = []
	if d.get("ground", false):
		sets.append(_pts)
	if d.get("air", false):
		sets.append(_air)
	for pts in sets:
		for pw in pts:
			var p: Vector3 = pw[0]
			var dx := p.x - wp.x
			var dz := p.z - wp.z
			if lw > 0.0:
				var along := dx * fd.x + dz * fd.z
				if along < -0.5 or along > r or absf(dx * fd.z - dz * fd.x) > lw * 0.5:
					continue
			elif dx * dx + dz * dz > r * r:
				continue
			elif arc < 359.0:
				var v := Vector2(dx, dz)
				if v.length() > 0.1 and v.normalized().dot(Vector2(fd.x, fd.z)) < cos(deg_to_rad(arc * 0.5)):
					continue
			s += float(pw[1]) / (1.0 + float(pw[2]) / need)
	return s


## The best spot for a tower: [cell, facing, coverage] (cell NONE if it fits nowhere).
func _best_spot(tid: String) -> Array:
	var shape_n: int = (GameData.shape_of(tid)["cells"] as Array).size()
	var turns: Array = [4] if (GameData.arc_of(tid) >= 359.0 and shape_n == 1) else [0, 1, 2, 3, 4, 5]
	var best := Board.NONE
	var best_f := 4
	var best_s := 0.0
	for c in _cands:
		for f in turns:
			var cells := GameData.footprint(tid, c, f)
			if not g.board.can_build_all(cells):
				continue
			var s := _cover_at(tid, g.footprint_center(cells), f, _reach(tid, c))
			if s > best_s:
				best_s = s
				best = c
				best_f = f
	return [best, best_f, best_s]


## A support tower's spot: where its aura covers the most damage (est dps x coverage of the towers in reach).
func _best_support_spot(tid: String) -> Array:
	var r := float(GameData.TOWERS[tid]["range"]) * GameData.TILE
	var best := Board.NONE
	var best_f := 4
	var best_s := 0.0
	for c in _cands:
		for f in [0, 2, 4]:
			var cells := GameData.footprint(tid, c, f)
			if not g.board.can_build_all(cells):
				continue
			var wp := g.footprint_center(cells)
			var s := 0.0
			for t in g.towers:
				if t.is_support():
					continue
				if Vector2(t.position.x - wp.x, t.position.z - wp.z).length() <= r:
					s += _dps(t.id, t.level, t.fx) * float(_cover.get(t, 1.0))
			if s > best_s:
				best_s = s
				best = c
				best_f = f
	return [best, best_f, best_s]


func _buff_frac(tid: String, level := 1, fx := {}) -> float:
	var b: Dictionary = GameData.TOWERS[tid].get("buff", {})
	var lb: float = GameData.LEVEL_BUFF[level - 1]
	var v := (float(b.get("dmg", 0.0)) + float(b.get("rate", 0.0))) * lb + float(fx.get("buff_dmg", 0.0)) + float(fx.get("buff_rate", 0.0))
	if GameData.TOWERS[tid].has("burn"):
		v += 0.12
	if GameData.TOWERS[tid].has("grow"):
		v += minf(float(GameData.TOWERS[tid]["grow_max"]), float(GameData.TOWERS[tid]["grow"]) * 8.0)
	return v


func _value_mult(tid: String) -> float:
	var d: Dictionary = GameData.TOWERS[tid]
	var m := 1.0
	if _need_detect() and d.get("detect", false):
		m *= 3.0
	if _air_coming() and d.get("air", false):
		m *= 1.4
	if d.has("toll"):
		m *= 0.75 if g.hp > 12 else 0.2
	return m


## The best spec for a tower going to level III: the one with the most estimated damage (or the bigger aura).
func _best_spec(t: Tower) -> int:
	if not GameData.SPECS.has(t.id):
		return -1
	var specs: Array = GameData.SPECS[t.id]
	var best := 0
	var best_v := -INF
	for i in specs.size():
		var fx: Dictionary = specs[i]["fx"]
		var v := _buff_frac(t.id, 3, fx) * 100.0 if t.is_support() else _dps(t.id, 3, fx)
		v *= 1.0 + 0.5 * float(fx.has("detect")) * float(_need_detect()) + 0.1 * float(fx.get("range", 0.0)) * 10.0
		if v > best_v:
			best_v = v
			best = i
	return best


func _high_build() -> void:
	_act_t -= 0.25
	if g.state == Game.S.WAVE and _act_t > 0.0:
		return
	_act_t = 1.0
	_high_talents()
	_phase_setup()
	_level_for_big()
	for step in 10:
		_phase_setup()
		# Builders: raise the tower doing the most work (more range)
		if g.builders > 0 and g.towers.size() >= 3:
			var top: Tower = null
			var tv := 0.0
			for t in g.towers:
				if t.is_support() or not t.cells.all(func(x): return g.board.can_raise(x)):
					continue
				var v := _dps(t.id, t.level, t.fx) * float(_cover.get(t, 0.0))
				if v > tv:
					tv = v
					top = t
			if top:
				g.placing = Game.RAISE
				g.try_raise(top.cell)
				g.placing = ""
				log["raised"] = int(log["raised"]) + 1
				_phase_key = -1
				continue
		var opts: Array = []   # [value, kind, data...]
		var dream := 0.0
		for tid in g.owned:
			if int(g.owned[tid]) <= 0:
				continue
			var cost := float(g.tower_cost(tid))
			var sup: bool = GameData.TOWERS[tid]["attack"] == "aura_buff"
			if sup and g.towers.filter(func(t): return not t.is_support()).size() < 4:
				continue
			var spot: Array = _best_support_spot(tid) if sup else _best_spot(tid)
			if spot[0] == Board.NONE:
				continue
			var v: float = (float(spot[2]) * _buff_frac(tid) if sup else _dps(tid) * float(spot[2])) * _value_mult(tid) / cost
			if g.gold >= cost:
				opts.append([v, "build", tid, spot[0], spot[1]])
			elif cost <= g.gold + 140 + 12 * g.wave:
				dream = maxf(dream, v)
		for t in g.towers:
			var c: int = t.upgrade_cost()
			if c <= 0:
				continue
			var gain: float
			if t.is_support():
				var aura := 0.0
				for o in g.towers:
					if not o.is_support() and Vector2(o.position.x - t.position.x, o.position.z - t.position.z).length() <= t.range_world():
						aura += _dps(o.id, o.level, o.fx) * float(_cover.get(o, 1.0))
				var nfx: Dictionary = GameData.SPECS[t.id][_best_spec(t)]["fx"] if g.needs_spec(t) else t.fx
				gain = aura * (_buff_frac(t.id, t.level + 1, nfx) - _buff_frac(t.id, t.level, t.fx))
			else:
				var nfx2: Dictionary = GameData.SPECS[t.id][_best_spec(t)]["fx"] if g.needs_spec(t) else t.fx
				gain = (_dps(t.id, t.level + 1, nfx2) - _dps(t.id, t.level, t.fx)) * float(_cover.get(t, 0.0)) * 1.1
			var v2 := gain * _value_mult(t.id) / float(c)
			if g.gold >= c:
				opts.append([v2, "upgrade", t])
			elif c <= g.gold + 140 + 12 * g.wave:
				dream = maxf(dream, v2)
		if opts.is_empty():
			return
		opts.sort_custom(func(a, b): return a[0] > b[0])
		var o: Array = opts[0]
		# save up for something clearly better next phase, unless the last wave hurt
		var hurt: bool = not log["waves"].is_empty() and int(log["waves"][-1]["hp1"]) < int(log["waves"][-1]["hp0"])
		if dream > float(o[0]) * 1.35 and not hurt and g.state == Game.S.BUILD:
			log["saved_phases"] = int(log["saved_phases"]) + 1
			return
		var ok := false
		if o[1] == "build":
			ok = _place(o[2], o[3], o[4])
		else:
			ok = _upgrade(o[2], _best_spec(o[2]))
		_phase_key = -1
		if not ok:
			return


func _high_talents() -> void:
	if g.state != Game.S.BUILD or g.wave < 2:
		return
	var order: Array = [["economy", 0], ["arsenal", 0], ["economy", 1], ["arsenal", 1], ["arsenal", 2], ["economy", 2],
		["arsenal", 3], ["keep", 0], ["economy", 3], ["keep", 1], ["keep", 2]]
	if g.hp < g.max_hp * 0.5:
		order.push_front(["keep", 0])
		order.push_front(["keep", 2])
	for t in g.threats:
		if g.threat_known(t):
			var th: Dictionary = GameData.THREATS[t["id"]]
			if GameData.ENEMIES[th["enemy"]].get("flying", false):
				order.push_front(["slayers", 0])
			if th.get("trait", "") == "shield":
				order.push_front(["slayers", 2])
			if th.get("trait", "") == "camo" and _need_detect():
				order.push_front(["slayers", 3])
	var reserve := 40 + 4 * g.wave
	for o in order:
		if g.talent_state(o[0], o[1]) == "open" and g.gold - g.talent_cost(o[0], o[1]) >= reserve:
			_buy_talent(o[0], o[1])
	if g.wave >= 12:
		for k in 3:
			var o: Array = [["arsenal", 4], ["economy", 4], ["keep", 4]][k]
			if g.talent_state(o[0], o[1]) == "open" and g.gold - g.talent_cost(o[0], o[1]) >= 300:
				_buy_talent(o[0], o[1])


func _high_pick_pair() -> int:
	var top_ids: Array = []
	var by_dmg := {}
	for t in g.towers:
		by_dmg[t.id] = float(by_dmg.get(t.id, 0.0)) + t.damage_done
	var ids: Array = by_dmg.keys()
	ids.sort_custom(func(a, b): return by_dmg[a] > by_dmg[b])
	top_ids = ids.slice(0, 2)
	var best := 0
	var best_s := -INF
	for i in g.choice_options.size():
		var s := 0.0
		for it in g.choice_options[i]["items"]:
			match String(it["kind"]):
				"blueprint":
					var tid: String = it["tower"]
					var d: Dictionary = GameData.TOWERS[tid]
					var per_gold := _dps(tid) / float(g.tower_cost(tid)) if d["attack"] != "aura_buff" else 0.25 * _buff_frac(tid)
					s += 1.0 + 4.0 * per_gold + 0.35 * GameData.tier_of(tid) + 0.4 * (_value_mult(tid) - 1.0)
					s -= 0.35 * int(g.owned.get(tid, 0))
				"doctrine": s += 1.2
				"masterwork": s += 1.8 if it["tower"] in top_ids else 0.5
				"builder": s += 0.6 + 0.2 * int(it["amount"])
				"gold": s += float(it["amount"]) / 90.0
				"recon": s += 0.3
				"digger": s += 0.15
		if s > best_s:
			best_s = s
			best = i
	return best
