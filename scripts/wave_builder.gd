class_name WaveBuilder
extends RefCounted
## Turns a wave number into a list of spawns: [{"type", "trait", "t"}], where t is the spawn time in game seconds.
## What can spawn comes from the run's roster: the base enemies plus this run's threats
## (rolled once per run, see Game._roll_threats).

const TRAIT_NAMES := {"shield": "Shielded", "camo": "Camo", "swift": "Swift"}
## Spawn pacing. A wave's enemies arrive spread over a window whose length grows with the wave's size: linear from
## min_count enemies (min_s) to max_count (max_s), clamped to [min_s, max_s]. Spawns are evenly spaced, each nudged
## by up to +-jitter of the spacing, with enemy types interleaved. Game seconds, so 2x / 3x speed still applies.
const SPAWN_WINDOW := {
	"min_s": 2.0, "max_s": 10.0,
	"min_count": 10, "max_count": 150,
	"jitter": 0.15,
}


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
		for i in n:
			out.append({"type": t, "trait": r.get("trait", ""), "group": group})
		budget -= n * cost
		group += 1
	out = _interleave(out)
	if boss != "":
		out.append({"type": boss, "trait": "", "group": group})
	_schedule(out, rng)
	return out


## Mixes the enemy types through the wave: each type's members are spread evenly over the sequence, so fliers,
## brutes and fodder arrive mixed instead of in packs.
static func _interleave(list: Array) -> Array:
	var by_kind := {}
	var order: Array = []
	for e in list:
		var k: String = e["type"] + "|" + String(e["trait"])
		if not by_kind.has(k):
			by_kind[k] = []
			order.append(k)
		by_kind[k].append(e)
	var keyed: Array = []
	for ki in order.size():
		var members: Array = by_kind[order[ki]]
		for j in members.size():
			# tiny per-kind offset keeps ties stable and alternating
			keyed.append([(j + 0.5) / members.size() + ki * 0.0001, members[j]])
	keyed.sort_custom(func(a, b): return a[0] < b[0])
	return keyed.map(func(x): return x[1])


## How long the spawn window is for a wave of n enemies.
static func spawn_window(n: int) -> float:
	var sw := SPAWN_WINDOW
	var f := inverse_lerp(float(sw["min_count"]), float(sw["max_count"]), float(n))
	return clampf(lerpf(float(sw["min_s"]), float(sw["max_s"]), f), float(sw["min_s"]), float(sw["max_s"]))


## Spawn times: evenly spaced over the window, each jittered by up to +-jitter of the spacing (the first spawns at 0,
## the last at the end of the window, and the order never changes).
static func _schedule(list: Array, rng: RandomNumberGenerator) -> void:
	var n := list.size()
	if n == 0:
		return
	var window := spawn_window(n)
	var step := window / maxf(1.0, n - 1)
	var jit := float(SPAWN_WINDOW["jitter"])
	var prev := 0.0
	for i in n:
		var t := i * step
		if i > 0 and i < n - 1:
			t += rng.randf_range(-jit, jit) * step
		t = clampf(maxf(t, prev), 0.0, window)
		list[i]["t"] = t
		prev = t


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
