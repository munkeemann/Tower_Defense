extends SceneTree
## Dev tool (headless): grows a dozen maps with the real tile planner and counts ramps whose road bends or branches.
## A ramp is the pack's sloped straight road piece, so the road must run straight through it; prints bent=0 when it does.
## Godot --headless --path . --script res://tools/ramp_test.gd -- --scratch

func _init() -> void:
	await process_frame
	var total_ramps := 0
	var bad := 0
	var tiles := 0
	for seed_v in range(1, 13):
		var board := Board.new()
		root.add_child(board)
		board.generate(seed_v * 7919)
		var rng := RandomNumberGenerator.new()
		rng.seed = seed_v
		for step in 22:
			var slots: Array = board.expansion_slots()
			if slots.is_empty():
				break
			var done := false
			for attempt in 30:
				var slot: Vector2i = slots[rng.randi() % slots.size()]
				var card := board.make_tile(rng, 2)
				for k in 6:
					var p := board.plan_tile(slot, card, k)
					if not p.is_empty():
						board.commit_tile(p, 1)
						tiles += 1
						done = true
						break
				if done:
					break
		for g in board.ramps:
			total_ramps += 1
			var up: int = int(board.ramps[g])
			var sides: Array = []
			for n in board.links.get(g, []):
				sides.append(Hex.dir_index((n as Vector2i) - g))
			if board.open_ports.has(g):
				sides.append(int(board.open_ports[g]["side"]))
			for d in sides:
				if d != up and d != (up + 3) % 6:
					bad += 1
					print("RAMPTEST bent ramp at ", g, " up ", up, " road sides ", sides, " seed ", seed_v)
					break
		board.free()
	print("RAMPTEST tiles=%d ramps=%d bent=%d" % [tiles, total_ramps, bad])
	quit(1 if bad > 0 else 0)
