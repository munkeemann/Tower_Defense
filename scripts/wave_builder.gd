class_name WaveBuilder
extends RefCounted
## Turns a wave number into a list of spawns: [{"type", "trait", "gap", "group"}].
## What can spawn comes from the run's roster: the base enemies plus this run's threats
## (rolled once per run, see Game._roll_threats).

const TRAIT_NAMES := {"shield": "Shielded", "camo": "Camo", "swift": "Swift"}
## Enemies arrive in tight packs so rounds play fast.
const GAP_MULT := 0.55


static func hp_mult(w: int) -> float:
	return 1.0 + 0.12 * w + 0.014 * w * w   # hex roads are long: enemies need more health than on the old square map


## roster: [{"enemy", "trait", "since"}]. boss: enemy id or "".
static func generate(w: int, rng: RandomNumberGenerator, count_mult: float, roster: Array, boss := "") -> Array:
	var out: Array = []
	var budget := (5.5 + w * 3.9 + w * w * 0.23) * count_mult
	if boss != "":
		budget *= 0.45
	var pool: Array = []
	var fresh: Array = []
	for r in roster:
		if int(r["since"]) <= w:
			pool.append(r)
			if int(r["since"]) == w:
				fresh.append(r)
	# threats that have arrived show up more often than the base rabble
	var weights: Array = []
	for r in pool:
		weights.append(1.6 if r.get("threat", false) else 1.0)
	var gap_scale: float = max(0.4, 1.0 - w * 0.02) * GAP_MULT
	var group := 0
	while budget > 0.0 and pool.size() > 0:
		var r: Dictionary
		var first := false
		if fresh.size() > 0:
			r = fresh.pop_front()
			first = true
		else:
			r = _weighted(pool, weights, rng)
		var t: String = r["enemy"]
		var cost := float(GameData.ENEMIES[t]["cost"])
		var n: int = clampi(rng.randi_range(3, 7) + w / 6, 1, int(ceil(budget / cost)))
		if first and r.get("threat", false):
			n = clampi(2 + w / 4, 2, n)   # a new threat's debut is a small group
		var gap := 0.6 * gap_scale
		if t == "wolf":
			gap *= 0.6
		for i in n:
			out.append({"type": t, "trait": r.get("trait", ""), "gap": gap, "group": group})
		out[out.size() - 1]["gap"] = 1.8 * gap_scale
		budget -= n * cost
		group += 1
	if boss != "":
		if out.size() > 0:
			out[out.size() - 1]["gap"] = 3.0
		out.append({"type": boss, "trait": "", "gap": 1.0, "group": group})
	return out


static func _weighted(pool: Array, weights: Array, rng: RandomNumberGenerator) -> Dictionary:
	var total := 0.0
	for x in weights:
		total += x
	var roll := rng.randf() * total
	for i in pool.size():
		roll -= weights[i]
		if roll <= 0.0:
			return pool[i]
	return pool[pool.size() - 1]


static func enemy_label(t: String, trait_: String) -> String:
	var d: Dictionary = GameData.ENEMIES[t]
	var s := String(d["name"])
	if trait_ != "":
		s = TRAIT_NAMES.get(trait_, trait_) + " " + s
	if d.get("flying", false):
		s += " (air)"
	return s


static func summary(list: Array) -> String:
	var counts := {}
	var order: Array = []
	for e in list:
		var key: String = e["type"] + "|" + String(e.get("trait", ""))
		if not counts.has(key):
			counts[key] = 0
			order.append(key)
		counts[key] += 1
	var parts: PackedStringArray = []
	for key in order:
		var bits: PackedStringArray = key.split("|")
		var d: Dictionary = GameData.ENEMIES[bits[0]]
		if d.get("boss", false):
			parts.append("BOSS: " + String(d["name"]))
		else:
			parts.append("%d %s" % [counts[key], enemy_label(bits[0], bits[1])])
	return ", ".join(parts)
