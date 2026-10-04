class_name Game
extends Node3D
## Run controller: phases, economy, combat resolution, input and saving.
##
## A run, Tower Dominion-style: pick a faction and a hero, then between waves you grow the map
## with 5x5 terrain tiles (every open road end is an enemy entry point), draft tower blueprints
## (limited copies), pick doctrines, and prepare for this run's threats, which are rolled at the
## start and revealed a few waves before they arrive.

enum S { MENU, EXPAND, BUILD, WAVE, REWARD, OVER }

const SAVE_PATH := "user://tower_realms.cfg"
const RAISE := "__raise"   # placing mode: a Builder raising ground
const DIG := "__dig"       # placing mode: a Digger lowering ground
const SPEEDS := [1.0, 2.0, 3.0]
## Boss health by wave, whichever boss this run rolled for that slot.
const BOSS_HP := {10: 2600.0, 20: 6500.0, 30: 16000.0}
const BOSS_GOLD := {10: 120, 20: 250, 30: 500}
const BOSS_LEAK := {10: 10, 20: 15, 30: 20}
## A new road out of the castle (another battlefront) opens before these waves. Empty on the hex map:
## tiles with 3+ entrances already open plenty of battlefronts.
const NEW_FRONT_WAVES := []
const CASTLE_DETECT := 3.0     # tiles around the castle where camouflage fails
const SCOUT_DETECT := 4.0

var state := S.MENU
var _parked := {}           # a run set aside by the Menu button (state, speed, camera, open panels); empty if none
var faction := "crown"
var hero := ""
var hero_fx := {}
var difficulty := 0
var board: Board
var world: Node3D
var overlay: Node3D
var cam: CameraRig
var hud: Hud
var thumbs: Thumbs
var audio: Audio
var rng := RandomNumberGenerator.new()

var gold := 0
var hp := 0
var max_hp := 0
var wave := 0
var recon := 0
var owned := {}             # tower id -> blueprint copies left to build
var mods := {}
var masterwork := {}
var mine_income := 0
var builders := 0           # items: each raises a hex (or a whole tower) one level
var diggers := 0            # items: each lowers one
var talents := {}           # castle talent id -> rank
var _keep_cd := 0.0
var _range_mm: MultiMeshInstance3D
var _flight_mi: MeshInstance3D
var _range_key := ""
var enemies: Array = []
var towers: Array = []
var spawn_queue: Array = []
var wave_clock := 0.0       # game seconds since the wave started (spawn times count from here)
var _spawned := 0           # enemies spawned this wave (road ends take turns by this count)
var next_wave_list: Array = []
var wave_routes := {}       # port cell -> route (this wave)
var wave_port_cycle: Array = []
var speed := 1.0
var paused := false

## This run's threats: [{"id", "wave"}], and what can spawn (base enemies + threats).
var threats: Array = []
var roster: Array = []
var boss_plan := {}         # wave -> boss enemy id

## Between-wave steps still to go ("blueprint", "doctrine", "expand", "front").
var _steps: Array = []
var _cur_step := ""
var tile_cards: Array = []  # [{"family", "variant", "features"}]
var tile_pick := -1
var _slots: Array = []
var _hover_slot := Board.NONE
var _variant_offset := 0
var _plan := {}
var _rmb_at := Vector2.ZERO

var placing := ""
var place_facing := 4                 # side a tower being placed faces (R turns it)
var _ghost_cells: Array = []          # hex plates showing the footprint being placed
var _ghost_range: MeshInstance3D
var _sector_cache := {}
var selected: Tower = null
var hover_cell := Vector2i(-1, -1)
var _ghost: Node3D
var _sel_range: MeshInstance3D
var _hover_marker: MeshInstance3D
var _sel_outline: MeshInstance3D      # gold outline around the selected tower's footprint
var _hover_outline: MeshInstance3D    # white outline around the tower under the cursor
var _ghost_outline: MeshInstance3D    # green / red outline around a footprint being placed
var _outline_cache := {}

var ability_cd := 0.0
var ability_active := 0.0
var choice_options: Array = []
var run_stats := {}
var stats := {}
var _ui_timer := 0.0
var _detect_timer := 0.0
var _wave_leaks := {}

var force_biome := ""        # test flag: --biome=<id>
var autotest := false
var _auto_t := 0.0
var _auto_max_wave := 30
var shot_dir := ""
var _shots_taken := {}


# ------------------------------------------------------------------ setup

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	rng.randomize()
	if "--no-kaykit" in OS.get_cmdline_user_args():
		KayKit.enabled = false   # the models from before the KayKit swap (for before/after checks)
	if "--no-blender" in OS.get_cmdline_user_args():
		Models.blender_towers = false   # KK_TOWER composites instead of the Blender-made towers
	_setup_env()
	board = Board.new()
	board.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(board)
	world = Node3D.new()
	world.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(world)
	VFX.warmup(world)
	overlay = Node3D.new()
	add_child(overlay)
	cam = CameraRig.new()
	add_child(cam)
	thumbs = Thumbs.new()
	add_child(thumbs)
	audio = Audio.new()
	audio.listener = cam
	add_child(audio)
	hud = Hud.new()
	add_child(hud)
	hud.setup(self)
	_build_overlay()
	_load_stats()
	difficulty = clampi(int(stats.get("difficulty", 0)), 0, GameData.DIFFICULTIES.size() - 1)
	audio.set_muted(bool(stats.get("muted", false)))
	if bool(stats.get("fullscreen", false)) and OS.get_cmdline_user_args().is_empty():
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--autotest"):
			autotest = true
			var parts := a.split("=")
			if parts.size() > 1:
				faction = parts[1]
		if a.begins_with("--maxwave="):
			_auto_max_wave = int(a.split("=")[1])
		if a.begins_with("--shotdir="):
			shot_dir = a.substr(10)
		if a.begins_with("--faction="):
			faction = a.split("=")[1]
		if a.begins_with("--hero="):
			hero = a.split("=")[1]
		if a.begins_with("--biome="):
			force_biome = a.split("=")[1]
		if a.begins_with("--difficulty="):
			difficulty = clampi(int(a.split("=")[1]), 0, GameData.DIFFICULTIES.size() - 1)
		if a.begins_with("--seed="):
			rng.seed = int(a.split("=")[1])   # same map every time (before/after screenshots)
	if args.size() > 0:
		# test runs: don't let a sleeping monitor throttle vsync to a crawl, and stay quiet
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		audio.music_enabled = false
	if "--mapshot" in args:
		await _map_shot()
		get_tree().quit()
	elif "--fpsprobe" in args:
		await _fps_probe()
		get_tree().quit()
	elif "--fpshot" in args:
		await _footprint_shots()
		get_tree().quit()
	elif "--inputtest" in args:
		var ok: bool = await _input_test()
		get_tree().quit(0 if ok else 1)
	elif Array(args).any(func(x): return String(x).begins_with("--towertest")):
		var tid := "ballista"
		for x in args:
			if x.begins_with("--towertest="):
				tid = x.split("=")[1]
		var ok: bool = await _tower_test(tid)
		get_tree().quit(0 if ok else 1)
	elif "--menushot" in args:
		to_menu()
		await get_tree().create_timer(2.0).timeout
		await _shot("menu")
		hud.show_hero_select(faction)
		await get_tree().create_timer(1.0).timeout
		await _shot("heroes")
		hud.show_council()
		await get_tree().create_timer(0.6).timeout
		await _shot("council")
		get_tree().quit()
	elif autotest:
		start_run(faction, hero)
		cycle_speed(); cycle_speed()
		print("AUTOTEST threats=%s bosses=%s hero=%s biome=%s" % [str(threats.map(func(t): return "%s@%d" % [t["id"], t["wave"]])), str(boss_plan), hero, board.biome_id])
	else:
		to_menu()


## Grows a late-run map (several battlefronts, long roads, defenses, a wave in progress) and photographs it.
func _map_shot() -> void:
	start_run(faction if faction != "" else "crown", hero)
	hud.hide_choices()
	for w in range(1, 22):
		wave = w
		if w + 1 in NEW_FRONT_WAVES:
			_open_front()
		if w % 2 == 1:
			_auto_expand()
	for tid in run_towers():
		owned[tid] = 8
	hud.build_tower_bar()
	wave = 14
	gold = 8000
	for i in 40:
		_auto_build()
	gold = 400
	_steps.clear()
	_next_step()
	start_wave()
	cam._target_dist = 150.0
	cam.distance = 150.0
	cam.focus(Vector3.ZERO)
	await get_tree().create_timer(5.0).timeout
	await _shot("map_overview")
	cam.pitch = deg_to_rad(-89.0)
	await get_tree().create_timer(0.5).timeout
	await _shot("map_topdown")
	# close looks at the details: a bridge (if the roads crossed a lake), and the castle plaza
	cam.pitch = deg_to_rad(-40.0)
	for spot in [["bridge", board.bridges.keys()], ["castle", [board.center]], ["shore", _shore_cells()]]:
		if spot[1].is_empty():
			continue
		cam.focus(board.cell_to_world(spot[1][0]))
		cam._target_dist = 10.0 if spot[0] == "bridge" else 16.0
		cam.distance = cam._target_dist
		cam.pitch = deg_to_rad(-32.0 if spot[0] == "bridge" else -40.0)
		await get_tree().create_timer(1.0).timeout
		await _shot("detail_" + spot[0])
	# --closeup=<tower id>: frame one tower of that type up close
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--closeup="):
			var want := a.split("=")[1]
			if not board.towers.values().any(func(t): return t.id == want):
				var spot := Board.NONE
				for pc in board.path_cells:
					for d in Hex.E:
						for f in 6:
							var c2: Vector2i = pc + d * 2
							if spot == Board.NONE and board.can_build_all(GameData.footprint(want, c2, f)):
								spot = c2
								place_facing = f
				gold = 999
				owned[want] = 1
				placing = want
				try_place(spot)
			for t in towers:
				if t.id == want:
					cam.pitch = deg_to_rad(-40.0)
					cam._target_yaw = 0.5
					cam.focus(t.position)
					cam._target_dist = 13.0
					cam.distance = 13.0
					hud.help_panel.visible = false
					select_tower(t)
					break
			await get_tree().create_timer(2.5).timeout
			await _shot("closeup_" + want)


## Places every multi-hex tower of the faction facing the camera, with its range showing, and photographs each.
func _footprint_shots() -> void:
	start_run(faction if faction != "" else "crown", hero)
	hud.hide_choices()
	for i in 12:
		wave = i
		_auto_expand()
	wave = 1
	_steps.clear()
	_next_step()
	hud.help_panel.visible = false
	gold = 99999
	for tid in run_towers():
		if GameData.shape_of(tid)["cells"].size() < 2 and Models.footprint_art(tid).is_empty():
			continue
		owned[tid] = 1
		# an open spot away from the castle, with room in front for the camera
		var spot := Board.NONE
		var best := -1.0
		for c in board.whole:
			var cells := GameData.footprint(tid, c, 1)
			if Hex.length(c) < Hex.K or not board.can_build_all(cells):
				continue
			var clear := 0.0
			for n in Hex.disc(c, 3):
				clear += 1.0 if not board.towers.has(n) else -3.0
			if clear > best:
				best = clear
				spot = c
		if spot == Board.NONE:
			print("FPSHOT no room for ", tid)
			continue
		placing = tid
		place_facing = 1
		try_place(spot)
		placing = ""
		var t: Tower = board.towers.get(spot)
		if t == null:
			continue
		select_tower(t)
		cam.pitch = deg_to_rad(-38.0)
		cam._target_yaw = 0.0
		cam.focus(t.position)
		cam._target_dist = 15.0
		cam.distance = 15.0
		await get_tree().create_timer(1.5).timeout
		await _shot("fp_" + tid)
		deselect()


func _shore_cells() -> Array:
	var out: Array = []
	for c in board.whole:
		if board.level_at(c) == 0:
			for d in Hex.E:
				if board._is_water(c + d):
					out.append(c)
					break
		if out.size() > 0:
			break
	return out


## Measures FPS while switching expensive features off one by one (perf debugging).
func _fps_probe() -> void:
	start_run("crown")
	_auto_expand()
	var env: Environment = (find_children("*", "WorldEnvironment", false, false)[0] as WorldEnvironment).environment
	var sun := find_children("*", "DirectionalLight3D", false, false)[0] as DirectionalLight3D
	var steps := [
		["baseline", func(): pass],
		["vsync off", func(): DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)],
		["no ssao", func(): env.ssao_enabled = false],
		["no glow/fog", func(): env.glow_enabled = false; env.fog_enabled = false],
		["no shadows", func(): sun.shadow_enabled = false],
		["no portal lights", func():
			for l in board.find_children("*", "OmniLight3D", true, false): l.visible = false],
		["hide board deco", func():
			for c in board.get_children():
				if c != board._ground: c.visible = false],
		["hide ground", func():
			if is_instance_valid(board._ground):
				board._ground.visible = false],
	]
	for s in steps:
		s[1].call()
		await get_tree().create_timer(2.0).timeout
		print("FPSPROBE %-18s fps=%d draws=%d prims=%d" % [s[0], Engine.get_frames_per_second(),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)])


var _tt_shots: Array = []   # --towertest: where each of the tower's projectiles started


## Headless check for one tower (--towertest=id): build it beside the road where its arc covers the most of it, walk
## sturdy goblins (wasps along their flight line, for air-only towers) into range, check that it turns, fires, plays its Blender "fire" animation on every shot and that
## bolts leave from its Muzzle marker, then sell it and check the refund. Prints TOWERTEST lines; true if all passed.
func _tower_test(tid: String) -> bool:
	start_run("crown")
	await get_tree().process_frame
	hud.hide_choices()
	for i in 4:
		_auto_expand()
	owned[tid] = 3
	gold = 5000
	var ok := true
	# the spot whose reach covers the most route points (like the bot, but exhaustive)
	var routes: Array = board.open_ports.keys().map(func(pc): return board.route_from(pc))
	var air_only: bool = not GameData.TOWERS[tid].get("ground", false)
	if air_only:
		# fliers go straight from the road end to the castle: score spots against points along that line
		routes = routes.map(func(r):
			var line := flight_route(r)
			var pts := PackedVector3Array()
			var n := int(ceil(line[0].distance_to(line[1]) / 1.0))
			for i in n + 1:
				pts.append(line[0].lerp(line[1], float(i) / maxf(1.0, n)))
			return pts)
	var r := float(GameData.TOWERS[tid]["range"]) * GameData.TILE + GameData.reach_offset(tid)
	var arc := GameData.arc_of(tid)
	var best := Board.NONE
	var best_f := 4
	var best_route := PackedVector3Array()
	var best_score := 0
	var seen := {}
	for pc in board.path_cells.keys():
		for c in Hex.disc(pc, 3):
			if seen.has(c):
				continue
			seen[c] = true
			for f in 6:
				var cells := GameData.footprint(tid, c, f)
				if not board.can_build_all(cells):
					continue
				var wp := footprint_center(cells)
				var fd := Hex.dir_world(f)
				for route in routes:
					var score := 0
					for p in route:
						var v := Vector2(p.x - wp.x, p.z - wp.z)
						if v.length() <= r and (arc >= 359.0 or v.normalized().dot(Vector2(fd.x, fd.z)) >= cos(deg_to_rad(arc * 0.5))):
							score += 1
					if score > best_score:
						best_score = score
						best = c
						best_f = f
						best_route = route
	if best == Board.NONE:
		print("TOWERTEST FAIL no spot for %s" % tid)
		return false
	placing = tid
	place_facing = best_f
	try_place(best)
	placing = ""
	var t: Tower = towers.back() if not towers.is_empty() else null
	if t == null or t.id != tid:
		print("TOWERTEST FAIL could not place %s at %s facing %d" % [tid, best, best_f])
		return false
	var blender := t._model.has_meta("blender")
	print("TOWERTEST placed %s at %s facing %d covering %d route points: blender=%s rig=%s muzzles=%d crew=%s" % [tid, best,
		best_f, best_score, blender, t._rig != null, t._muzzle_nodes.size(), t._crew != null])
	if blender and (t._rig == null or t._muzzle_nodes.is_empty()):
		print("TOWERTEST FAIL Blender tower without its rig or muzzle")
		ok = false
	if t.is_support():
		# support towers never attack: check that a neighbor in reach gets the buff, then sell
		owned["archer"] = 2
		var near := Board.NONE
		for c in Hex.disc(t.cell, 2):
			if board.can_build_all(GameData.footprint("archer", c, 4)):
				near = c
				break
		var buffed := false
		if near != Board.NONE:
			placing = "archer"
			place_facing = 4
			try_place(near)
			placing = ""
			var a2: Tower = towers.back()
			buffed = a2 != t and a2.buff_dmg > 0.0
			print("TOWERTEST support: archer at %s gets +%d%% damage" % [near, int(a2.buff_dmg * 100)])
		if not buffed:
			print("TOWERTEST FAIL the aura didn't reach a neighbor")
			ok = false
		select_tower(t)
		sell_selected()
		await get_tree().process_frame
		print("TOWERTEST %s %s" % ["PASS" if ok and not towers.has(t) else "FAIL", tid])
		return ok and not towers.has(t)
	# goblins (made sturdy) start a little before the covered stretch of road
	var first := 0
	for i in best_route.size():
		if t.reaches(best_route[i], t.position, t.range_world()):
			first = i
			break
	var along := 0.0
	for i in range(1, first + 1):
		along += best_route[i - 1].distance_to(best_route[i])
	_tt_shots.clear()
	world.child_entered_tree.connect(_tt_note)
	for k in 4:
		var e := spawn_enemy("wasp" if air_only else "goblin", best_route, maxf(0.0, along - 2.0 - 1.5 * k))
		e.max_hp = 1.0e6
		e.hp = e.max_hp
	Engine.time_scale = 2.0
	var fires := 0
	var last_anim := ""
	var yaw0 := t.head.rotation.y
	var turned := false
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 25000 and (fires < 4 or t.attacks < 4):
		await get_tree().process_frame
		if absf(angle_difference(t.head.rotation.y, yaw0)) > 0.02:
			turned = true
		if t._rig:
			var cur := t._rig.current_animation
			if cur == "fire" and last_anim != "fire":
				fires += 1
			last_anim = cur
	Engine.time_scale = 1.0
	world.child_entered_tree.disconnect(_tt_note)
	var worst := 0.0
	var muzzle := (t._muzzle_nodes[0] as Node3D) if not t._muzzle_nodes.is_empty() else null
	var hp := t.head.global_position
	for s in _tt_shots:
		# the head turns between shots, so compare with the circle the muzzle sweeps around the head's pivot
		if muzzle:
			var m := muzzle.global_position
			var off := absf(Vector2(s.x - hp.x, s.z - hp.z).length() - Vector2(m.x - hp.x, m.z - hp.z).length())
			worst = maxf(worst, maxf(off, absf(s.y - m.y)))
	print("TOWERTEST attacks=%d projectiles=%d rig_fires=%d head_turned=%s muzzle_offset=%.3f" % [t.attacks, _tt_shots.size(),
		fires, turned, worst])
	if t.attacks == 0:
		print("TOWERTEST FAIL it never attacked")
		ok = false
	if blender and fires < t.attacks - 1:
		print("TOWERTEST FAIL the fire animation did not play on every shot")
		ok = false
	if blender and worst > 0.05:
		print("TOWERTEST FAIL shots did not leave from the Muzzle marker")
		ok = false
	if not turned and arc < 359.0:
		print("TOWERTEST note: the head never had to turn")
	# sell it
	select_tower(t)
	var g0 := gold
	var refund := t.sell_value()
	var copies := int(owned.get(tid, 0))
	var cells: Array = t.cells.duplicate()
	sell_selected()
	await get_tree().process_frame
	var gone := not is_instance_valid(t) or not towers.has(t)
	var freed := cells.all(func(c): return not board.towers.has(c))
	print("TOWERTEST sold: gone=%s cells_free=%s gold %d -> %d (refund %d) copies %d -> %d" % [gone, freed, g0, gold, refund,
		copies, int(owned.get(tid, 0))])
	if not gone or not freed or gold != g0 + refund or int(owned.get(tid, 0)) != copies + 1:
		print("TOWERTEST FAIL selling")
		ok = false
	print("TOWERTEST %s %s" % ["PASS" if ok else "FAIL", tid])
	return ok


func _tt_note(n: Node) -> void:
	if n is Projectile:
		_tt_origin.call_deferred(n)


## Where a projectile started: its position now (bolts: walked back along their flight by what they've travelled).
func _tt_origin(p: Projectile) -> void:
	if not is_instance_valid(p):
		return
	if p.kind != Projectile.K.BOLT:
		_tt_shots.append(p.position)
		return
	var t: Tower = p.packet.get("tower")
	var travelled: float = t.range_world() * 1.15 - p.travel_left
	_tt_shots.append(p.position - p.dir * travelled)


## Drives the real input path: tile placement by mouse, hotkey -> click to build, select, upgrade, raise, dig, castle.
## Prints an INPUTTEST line per step and an INPUTTEST FAIL line for each check that fails; true if all passed.
func _input_test() -> bool:
	start_run("crown")
	await get_tree().process_frame
	var ok := true
	# pick the first tile card, then hover and click its first glowing slot
	_on_tile_card(0)
	await get_tree().process_frame
	if _slots.is_empty():
		print("INPUTTEST FAIL the tile card has no glowing slot")
		return false
	var slot: Vector2i = _slots[0]
	var sp := _it_aim(Hex.tile_world(slot) + Vector3(0, board.surface_y(Hex.tile_center(slot)), 0))
	await _it_mouse(sp)
	print("INPUTTEST tile hover slot=%s plan=%s" % [_hover_slot, not _plan.is_empty()])
	if _hover_slot != slot or _plan.is_empty():
		print("INPUTTEST FAIL hovering slot %s gave slot %s (cell %s)" % [slot, _hover_slot, hover_cell])
		ok = false
	var tiles0 := board.placed.size()
	await _it_mouse(sp, true)
	print("INPUTTEST tiles placed=%d state=%s" % [board.placed.size(), S.keys()[state]])
	if board.placed.size() != tiles0 + 1 or state != S.BUILD:
		print("INPUTTEST FAIL clicking the slot did not place the tile (%d -> %d) and start building" % [tiles0, board.placed.size()])
		return false
	var bar := bar_towers()
	var tid: String = bar[0] if not bar.is_empty() else ""
	await _it_key(KEY_1)
	print("INPUTTEST placing after hotkey: '%s'" % placing)
	if tid == "" or placing != tid:
		print("INPUTTEST FAIL hotkey 1 did not start placing '%s'" % tid)
		return false
	# a clear hex beside the road that can be raised, and that the mouse ray really lands on (raised ground in front
	# of a hex can hide it)
	var target := Board.NONE
	var screen := Vector2.ZERO
	for pc in board.path_cells:
		for d in Hex.E:
			var c: Vector2i = pc + d
			var cells := GameData.footprint(tid, c, place_facing)
			if target != Board.NONE or not board.can_build_all(cells) or not cells.all(func(x): return board.can_raise(x)):
				continue
			var p := _it_aim(board.cell_to_world(c) + Vector3(0, board.surface_y(c), 0))
			if board.pick_cell(cam.camera.project_ray_origin(p), cam.camera.project_ray_normal(p)) == c:
				target = c
				screen = p
	if target == Board.NONE:
		print("INPUTTEST FAIL no clear, pickable hex beside the road for %s" % tid)
		return false
	await _it_mouse(screen)
	print("INPUTTEST hover=%s target=%s" % [hover_cell, target])
	if hover_cell != target:
		print("INPUTTEST FAIL the mouse over %s hovers %s" % [target, hover_cell])
		ok = false
	var copies := int(owned.get(tid, 0))
	var g0 := gold
	var e0 := int(run_stats["gold_earned"])
	await _it_mouse(screen, true)
	var t0: Tower = board.towers.get(target)
	# a new tower claims discoveries in its reach at once (a Treasure Chest pays gold), so count what came in meanwhile
	var earned := int(run_stats["gold_earned"]) - e0
	print("INPUTTEST towers=%d gold %d -> %d (earned %d) placing='%s' %s copies left=%d" % [towers.size(), g0, gold, earned, placing,
		tid, int(owned.get(tid, 0))])
	if t0 == null or t0.id != tid:
		print("INPUTTEST FAIL clicking %s did not build a %s" % [target, tid])
		return false
	if gold != g0 - t0.spent + earned or t0.spent != tower_cost(tid) or int(owned.get(tid, 0)) != copies - 1 or placing != "":
		print("INPUTTEST FAIL building did not charge %d gold, use a copy (%d -> %d) and stop placing" % [tower_cost(tid), copies,
			int(owned.get(tid, 0))])
		ok = false
	await _it_mouse(screen, true)
	print("INPUTTEST selected=%s info_visible=%s" % [selected != null, hud.info_panel.visible])
	if selected != t0 or not hud.info_panel.visible:
		print("INPUTTEST FAIL clicking the tower did not select it and show its panel")
		return false
	gold = 999
	await _it_key(KEY_U)
	await _it_key(KEY_U)
	var spec_tower := GameData.SPECS.has(tid)
	print("INPUTTEST level after U,U: %d (III needs a specialization)" % t0.level)
	if t0.level != (2 if spec_tower else 3):
		print("INPUTTEST FAIL U,U should reach level %d" % (2 if spec_tower else 3))
		ok = false
	if spec_tower:
		upgrade_selected(1)
		print("INPUTTEST after spec: level=%d spec=%d fx=%s" % [t0.level, t0.spec, t0.fx])
		if t0.level != 3 or t0.spec != 1:
			print("INPUTTEST FAIL choosing specialization 1 should reach level 3")
			ok = false
	# Builder (B) then Digger (N), each clicked on the tower
	var h0 := board.height_at(target)
	var r0 := t0.range_world()
	var b0 := builders
	var d0 := diggers
	await _it_key(KEY_B)
	await _it_mouse(screen, true)
	print("INPUTTEST after Builder: height=%d elevation=%d range %.1f -> %.1f builders %d -> %d scaffold=%s" % [
		board.height_at(target), t0.elevation, r0, t0.range_world(), b0, builders, board._scaffold.has(target)])
	if board.height_at(target) != h0 + 1 or t0.elevation != h0 + 1 or t0.range_world() <= r0 or builders != b0 - 1:
		print("INPUTTEST FAIL the Builder did not raise the tower one level")
		ok = false
	screen = _it_aim(board.cell_to_world(target) + Vector3(0, board.surface_y(target), 0))   # the tower stands higher now
	await _it_key(KEY_N)
	await _it_mouse(screen, true)
	print("INPUTTEST after Digger: height=%d elevation=%d diggers %d -> %d scaffold=%s" % [
		board.height_at(target), t0.elevation, d0, diggers, board._scaffold.has(target)])
	if board.height_at(target) != h0 or t0.elevation != h0 or diggers != d0 - 1:
		print("INPUTTEST FAIL the Digger did not lower the tower back")
		ok = false
	await _it_key(KEY_C)
	g0 = gold
	buy_talent("artificers", 0)
	print("INPUTTEST castle open=%s bought guild=%d gold %d -> %d cost mult=%.2f" % [hud.castle_open(), talent_rank("guild"), g0, gold, mods["cost"]])
	if not hud.castle_open() or talent_rank("guild") != 1 or gold >= g0:
		print("INPUTTEST FAIL C did not open the castle, or the first Artificers talent was not bought")
		ok = false
	print("INPUTTEST %s" % ("PASS" if ok else "FAIL"))
	return ok


## Points the camera at a world point (no glide, zoom settled) and returns where that point lands on the view.
func _it_aim(p: Vector3) -> Vector2:
	cam.focus(p)
	cam.distance = cam._target_dist
	cam.yaw = cam._target_yaw
	cam._apply()
	return cam.camera.unproject_position(p)


## Moves the mouse to a point on the view and optionally left-clicks there. Input.parse_input_event takes window
## coordinates, like a real mouse, and the view is stretched to fit the window (a headless window is 64 px wide, 1/25
## of the 1600 px view), so the point goes through the screen transform first.
func _it_mouse(at: Vector2, click := false) -> void:
	var wp := get_viewport().get_screen_transform() * at
	var mm := InputEventMouseMotion.new()
	mm.position = wp
	mm.global_position = wp
	Input.parse_input_event(mm)
	await get_tree().process_frame
	if not click:
		return
	for pressed in [true, false]:
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_BUTTON_LEFT
		mb.position = wp
		mb.global_position = wp
		mb.pressed = pressed
		Input.parse_input_event(mb)
		await get_tree().process_frame


## Presses and releases a key.
func _it_key(code: Key) -> void:
	for pressed in [true, false]:
		var k := InputEventKey.new()
		k.keycode = code
		k.pressed = pressed
		Input.parse_input_event(k)
		await get_tree().process_frame


## Saves a screenshot once per name (autotest / debugging only).
func _shot(shot_name: String) -> void:
	if shot_dir == "" or _shots_taken.has(shot_name):
		return
	_shots_taken[shot_name] = true
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(shot_dir.path_join(shot_name + ".png"))
	print("SHOT ", shot_name)


func _setup_env() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.3, 0.5, 0.82)
	sm.sky_horizon_color = Color(0.78, 0.8, 0.84)
	sm.ground_bottom_color = Color(0.18, 0.22, 0.16)
	sm.ground_horizon_color = Color(0.6, 0.64, 0.6)
	sky.sky_material = sm
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.68   # soft shadows: the ground never goes murky
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.2
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	env.ssao_enabled = true
	env.ssao_intensity = 1.8          # contact shadows in the corners of the blocks
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.0
	env.adjustment_contrast = 1.04
	env.fog_enabled = true
	env.fog_light_color = Color(0.6, 0.66, 0.7)
	env.fog_density = 0.0007          # a light haze toward the horizon
	env.fog_sky_affect = 0.0
	if Board.KAYKIT_TERRAIN and KayKit.available():
		_kaykit_look(env)
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-56, -34, 0)
	sun.light_energy = 1.2
	sun.light_color = Color(1.0, 0.94, 0.84)   # warm key light
	sun.shadow_enabled = true
	sun.shadow_blur = 1.6
	# shadows only near the camera: the hex map has thousands of trees, and every cascade redraws them
	sun.directional_shadow_max_distance = 85.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_fade_start = 0.75
	if Board.KAYKIT_TERRAIN and KayKit.available():
		sun.light_energy = 1.0
		sun.light_color = Color(1.0, 0.98, 0.94)
		sun.shadow_opacity = 0.75
	add_child(sun)


## The KayKit sample look: the board floats over a dark floor, lit plainly and brightly so the pack's colors read
## as they were painted (no film curve, no haze, light contact shadows).
func _kaykit_look(env: Environment) -> void:
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.11, 0.11, 0.115)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.86, 0.9, 1.0)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_white = 1.0
	env.ssao_intensity = 0.7
	env.adjustment_contrast = 1.0
	env.fog_enabled = false


func _build_overlay() -> void:
	_ghost_range = MeshInstance3D.new()
	_ghost_range.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_sel_range = MeshInstance3D.new()
	_sel_range.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for n in [_ghost_range, _sel_range]:
		n.visible = false
		overlay.add_child(n)
	_hover_marker = _hex_marker(Color(1, 1, 1), 0.18)
	overlay.add_child(_hover_marker)
	var hm := CylinderMesh.new()
	hm.top_radius = Hex.R * 0.93
	hm.bottom_radius = Hex.R * 0.93
	hm.height = 0.04
	hm.radial_segments = 6
	hm.rings = 1
	var rmat := StandardMaterial3D.new()
	rmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rmat.vertex_color_use_as_albedo = true
	rmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	hm.material = rmat
	var rmm := MultiMesh.new()
	rmm.transform_format = MultiMesh.TRANSFORM_3D
	rmm.use_colors = true
	rmm.mesh = hm
	rmm.instance_count = 900
	rmm.visible_instance_count = 0
	_range_mm = MultiMeshInstance3D.new()
	_range_mm.multimesh = rmm
	_range_mm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	overlay.add_child(_range_mm)
	for i in 7:
		var g := _hex_marker(Color(0.4, 1.0, 0.5), 0.35)
		overlay.add_child(g)
		_ghost_cells.append(g)
	_sel_outline = _outline_node(Color(1.0, 0.85, 0.3))
	_hover_outline = _outline_node(Color(1, 1, 1))
	_ghost_outline = _outline_node(Color(0.4, 1.0, 0.5))


func _outline_node(col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := Models.mat(col, 1.2, 0.95)
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	mi.visible = false
	overlay.add_child(mi)
	return mi


## A ribbon just outside the outer edge of a group of hexes (edges shared by two of them are skipped), in world
## space relative to the first cell. Cached by shape.
func _outline_mesh(cells: Array) -> ArrayMesh:
	var key := str(cells.map(func(c): return c - cells[0]))
	if _outline_cache.has(key):
		return _outline_cache[key]
	var inside := {}
	for c in cells:
		inside[c] = true
	var verts := PackedVector3Array()
	var o := Hex.to_world(cells[0])
	for c in cells:
		var p: Vector3 = Hex.to_world(c) - o
		for i in 6:
			if inside.has(c + Hex.E[i]):
				continue
			var a: Vector3 = Hex.CORNER[i]
			var b: Vector3 = Hex.CORNER[(i + 1) % 6]
			var a1: Vector3 = p + a * 0.98
			var b1: Vector3 = p + b * 0.98
			var a2: Vector3 = p + a * 1.12
			var b2: Vector3 = p + b * 1.12
			verts.append_array([a1, a2, b2, a1, b2, b1])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	_outline_cache[key] = m
	return m


func _show_outline(mi: MeshInstance3D, cells: Array, col := Color(-1, 0, 0)) -> void:
	if cells.is_empty():
		mi.visible = false
		return
	mi.mesh = _outline_mesh(cells)
	mi.position = board.cell_to_world(cells[0]) + Vector3(0, board.surface_y(cells[0]) + 0.08, 0)
	if col.r >= 0.0:
		(mi.material_override as StandardMaterial3D).albedo_color = Color(col.r, col.g, col.b, 0.95)
	mi.visible = true


func _hex_marker(col: Color, alpha: float) -> MeshInstance3D:
	var cm := CylinderMesh.new()
	cm.top_radius = Hex.R * 0.92
	cm.bottom_radius = Hex.R * 0.92
	cm.height = 0.05
	cm.radial_segments = 6
	cm.rings = 1
	var mi := MeshInstance3D.new()
	mi.mesh = cm
	mi.material_override = Models.mat(col, 0.0, alpha)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.visible = false
	return mi


## Unit-radius range shape: a full disc, or a pie slice for towers with a firing arc (facing -Z).
func _sector_mesh(arc: float) -> ArrayMesh:
	var key := int(arc)
	if _sector_cache.has(key):
		return _sector_cache[key]
	var verts := PackedVector3Array()
	var seg := maxi(8, int(arc / 6.0))
	var a0 := -deg_to_rad(arc) * 0.5
	var full := arc >= 359.0
	for i in seg:
		var t0 := a0 + deg_to_rad(arc) * i / seg
		var t1 := a0 + deg_to_rad(arc) * (i + 1) / seg
		verts.append(Vector3.ZERO)
		verts.append(Vector3(sin(t1), 0, -cos(t1)))
		verts.append(Vector3(sin(t0), 0, -cos(t0)))
		# rim
		var r0 := Vector3(sin(t0), 0, -cos(t0))
		var r1 := Vector3(sin(t1), 0, -cos(t1))
		verts.append_array([r0 * 0.97, r1, r0, r0 * 0.97, r1 * 0.97, r1])
	if not full:
		for side in [a0, -a0]:
			var d := Vector3(sin(side), 0, -cos(side))
			var n := Vector3(-d.z, 0, d.x) * 0.02
			verts.append_array([n, d + n, d - n, n, d - n, -n])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	_sector_cache[key] = m
	return m


func _show_range(mi: MeshInstance3D, pos: Vector3, r: float, arc: float, facing: int, col: Color) -> void:
	mi.mesh = _sector_mesh(arc)
	var m := Models.mat(col, 0.0, 0.22)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	mi.position = pos + Vector3(0, 0.08, 0)
	mi.rotation = Vector3(0, Hex.dir_yaw(facing), 0)
	mi.scale = Vector3(r, 1, r)
	mi.visible = true


## Range as the actual hexes a tower reaches on your tiles, measured from its footprint's centroid: road hexes
## (where enemies walk) bright, other ground faint. Towers with a firing arc only light the hexes in front.
func _show_range_cells(key: String, center: Vector3, r: float, arc: float, facing: int, col: Color, line_w := 0.0) -> void:
	if key == _range_key:
		return
	_range_key = key
	var mm := _range_mm.multimesh
	var n := 0
	var fd := Hex.dir_world(facing)
	var cos_half := cos(deg_to_rad(arc * 0.5))
	var reach := int(ceil(r / (Hex.SQ3 * Hex.R))) + 1
	var src := Hex.from_world(center)
	for c in Hex.disc(src, reach):
		if not (board.whole.has(c) or board.path_cells.has(c)) or n >= mm.instance_count:
			continue
		var cw := Hex.to_world(c)
		var v := Vector2(cw.x - center.x, cw.z - center.z)
		if v.length() > r:
			continue
		if line_w > 0.0:
			var along := v.x * fd.x + v.y * fd.z
			if along < -0.5 or absf(v.x * fd.z - v.y * fd.x) > line_w * 0.5:
				continue
		elif arc < 359.0 and v.length() > 0.1 and v.normalized().dot(Vector2(fd.x, fd.z)) < cos_half - 0.001:
			continue
		var road := board.path_cells.has(c)
		var y := board.road_y(c) + 0.05 if road else board.surface_y(c) + 0.06
		mm.set_instance_transform(n, Transform3D(Basis(), Vector3(cw.x, y, cw.z)))
		var cc := col
		cc.a = 0.5 if road else 0.17
		mm.set_instance_color(n, cc)
		n += 1
	mm.visible_instance_count = n


func _hide_range() -> void:
	if _range_key == "":
		return
	_range_key = ""
	_range_mm.multimesh.visible_instance_count = 0


func footprint_center(cells: Array) -> Vector3:
	var p := Vector3.ZERO
	for c in cells:
		p += Hex.to_world(c)
	p /= maxf(1.0, cells.size())
	p.y = board.surface_y(cells[0])
	return p


func _default_mods() -> Dictionary:
	return {"phys": 1.0, "magic": 1.0, "range": 1.0, "rate": 0.0, "cost": 1.0, "bounty": 0,
		"treasury": 0, "ley": 0.0, "crit": 0.0, "execute": 0.0, "ability_cd": 1.0,
		# castle talents
		"dmg_all": 0.0, "shield_break": 0.0, "vs_air": 0.0, "vs_armor": 0.0, "vs_camo": 0.0, "vs_boss": 0.0,
		"interest": 0.0, "recon_wave": 0, "kill_gold": 0.0, "extra_copies": 0, "castle_detect": 0.0,
		"turret": 0, "turret_rate": 1.0, "moat": 0.0, "repair": 0, "builder_every": 0}


func sfx(n: String, pos: Variant = null) -> void:
	if audio:
		audio.play(n, pos)


# ------------------------------------------------------------------ run lifecycle

func _clear_world() -> void:
	for c in world.get_children():
		c.queue_free()
	if _flight_mi:
		_flight_mi.visible = false
	enemies.clear()
	towers.clear()
	spawn_queue.clear()
	selected = null
	cancel_placing()
	if _range_mm:
		_hide_range()
	board.clear_preview()
	board.clear_slots()
	tile_pick = -1
	_steps.clear()


## The in-run Menu button: set the run aside, frozen exactly as it is, and show the main menu with Resume.
## Starting a new run discards it; so does losing or winning.
func open_menu() -> void:
	if state == S.MENU or state == S.OVER:
		to_menu()
		return
	_set_paused(false)
	cancel_placing()
	deselect()
	_parked = {"state": state, "speed": speed, "cam_pos": cam.position, "yaw": cam._target_yaw, "dist": cam._target_dist,
		"panels": hud.park_panels()}
	state = S.MENU
	world.process_mode = Node.PROCESS_MODE_DISABLED   # enemies, towers and shots stop where they are
	Engine.time_scale = 1.0
	cam.auto_orbit = true
	cam.focus(board.cell_to_world(board.center))
	cam._target_dist = 58.0
	hud.show_menu(stats)
	audio.start_music()


func can_resume() -> bool:
	return not _parked.is_empty()


## Back into the parked run, exactly where it was left.
func resume_run() -> void:
	if _parked.is_empty():
		return
	var p := _parked
	_parked = {}
	hud.hide_menu()
	hud.set_game_ui_visible(true)
	hud.unpark_panels(p["panels"])
	world.process_mode = Node.PROCESS_MODE_INHERIT
	state = p["state"]
	speed = p["speed"]
	Engine.time_scale = speed
	cam.auto_orbit = false
	cam.focus(p["cam_pos"])
	cam._target_yaw = p["yaw"]
	cam._target_dist = p["dist"]
	audio.start_music(faction)
	_refresh_ui()


func _drop_parked() -> void:
	_parked = {}
	if world:
		world.process_mode = Node.PROCESS_MODE_INHERIT


func to_menu() -> void:
	_drop_parked()
	_set_paused(false)
	Engine.time_scale = 1.0
	speed = 1.0
	_clear_world()
	state = S.MENU
	mods = _default_mods()
	hero_fx = {}
	wave = 0
	board.pond_bonus = 0.0
	board.fog_enabled = false
	board.generate(rng.randi())
	# grow a little road network for the backdrop
	for i in 9:
		_auto_expand()
	board.clear_slots()
	cam.auto_orbit = true
	cam.focus(Vector3.ZERO)
	cam._target_dist = 58.0
	hud.show_menu(stats)
	audio.start_music()


## Folds two fx dictionaries: "*_mult" keys multiply, numbers add, anything else is taken from b.
func _merge_fx(a: Dictionary, b: Dictionary) -> Dictionary:
	var out := a.duplicate(true)
	for k in b:
		if out.has(k) and String(k).ends_with("_mult"):
			out[k] = float(out[k]) * float(b[k])
		elif out.has(k) and (b[k] is float or b[k] is int) and (out[k] is float or out[k] is int):
			out[k] = float(out[k]) + float(b[k])
		else:
			out[k] = b[k]
	return out


## Towers this run can draft: the color's own plus the shared ones.
func run_towers() -> Array:
	return GameData.run_towers(faction)


## Build-bar order: every run tower you've drafted at least once.
func bar_towers() -> Array:
	return run_towers().filter(func(t): return owned.has(t))


func default_hero(fid: String) -> String:
	var last := String(stats.get("hero_" + fid, ""))
	if GameData.HEROES.has(last) and hero_unlocked(last) and GameData.HEROES[last]["faction"] == fid:
		return last
	for hid in GameData.HEROES:
		if GameData.HEROES[hid]["faction"] == fid and hero_unlocked(hid):
			return hid
	return ""


func start_run(fid: String, hero_id := "") -> void:
	_drop_parked()
	hud.hide_menu()
	hud.hide_end()
	_set_paused(false)
	_clear_world()
	faction = fid
	if not GameData.HEROES.has(hero_id) or GameData.HEROES[hero_id]["faction"] != fid:
		hero_id = default_hero(fid)
	hero = hero_id
	# the color's passive and the commander's powers, folded together
	hero_fx = _merge_fx(GameData.FACTIONS[fid].get("passive", {}), GameData.HEROES[hero]["fx"] if hero != "" else {})
	stats["hero_" + fid] = hero
	gold = GameData.START_GOLD + 40 * meta_level("gold")
	max_hp = GameData.START_HP + int(hero_fx.get("hp", 0)) + 3 * meta_level("keep")
	hp = max_hp
	wave = 0
	recon = GameData.START_RECON + meta_level("recon")
	mods = _default_mods()
	for k in ["phys", "magic", "range"]:
		mods[k] += float(hero_fx.get(k, 0.0))
	mods["rate"] += float(hero_fx.get("rate", 0.0))
	mods["ability_cd"] *= float(hero_fx.get("ability_cd", 1.0))
	owned = {}
	var fac: Dictionary = GameData.FACTIONS[fid]
	for tid in fac["start_copies"]:
		owned[tid] = int(fac["start_copies"][tid])
	var sc: Dictionary = hero_fx.get("start_copies", {})
	for tid in sc:
		owned[tid] = int(owned.get(tid, 0)) + int(sc[tid])
	owned[fac["start"][0]] = int(owned.get(fac["start"][0], 0)) + meta_level("armory")
	masterwork = {}
	mine_income = 0
	builders = GameData.START_BUILDERS
	diggers = GameData.START_DIGGERS
	talents = {}
	_keep_cd = 0.0
	ability_cd = 0.0
	ability_active = 0.0
	run_stats = {"kills": 0, "leaked": 0, "built": 0, "gold_earned": 0, "tiles": 0, "discoveries": 0}
	board.fog_enabled = false   # the map is just your tiles on a plain backdrop: nothing to hide
	board.team = KayKit.TEAM.get(fid, "blue")
	Models.team = board.team
	board.generate(rng.randi(), force_biome)
	_roll_threats()
	thumbs.queue_faction(fid)
	cam.auto_orbit = false
	cam.focus(Vector3(0, 0, -8))
	cam._target_dist = 44.0 / CameraRig.CELL_ZOOM
	cam._target_yaw = 0.0
	hud.set_game_ui_visible(true)
	hud.help_panel.visible = int(stats.get("runs", 0)) < 2 and OS.get_cmdline_user_args().is_empty()
	hud.build_tower_bar()
	board.pond_bonus = float(hero_fx.get("ponds", 0.0))
	audio.start_music(fid)
	if "--bridgetest" in OS.get_cmdline_user_args():
		board.seed_test_lake(Hex.E[4])
	# the first stretch of road out of the castle is laid for you; then you choose where it goes
	_auto_tile(board.open_ports.keys()[0])
	hud.refresh_intel()
	var hname: String = GameData.HEROES[hero]["name"] if hero != "" else "No hero"
	hud.toast("%s  -  %s" % [board.biome["name"], hname], Color(0.8, 0.95, 0.75))
	_steps = ["expand"]
	_next_step()


## Rolls this run's threats (which enemy types, and when they join) and the boss order.
func _roll_threats() -> void:
	threats.clear()
	roster.clear()
	for e in GameData.BASE_ENEMIES:
		roster.append({"enemy": e, "trait": "", "since": GameData.BASE_ENEMIES[e]})
	var ids: Array = GameData.THREATS.keys()
	_shuffle(ids)
	# stealth never opens the run: the first threat is always one you can shoot without a detector
	if GameData.THREATS[ids[0]].get("trait", "") == "camo":
		for k in range(1, ids.size()):
			if GameData.THREATS[ids[k]].get("trait", "") != "camo":
				var tmp = ids[0]
				ids[0] = ids[k]
				ids[k] = tmp
				break
	for i in GameData.THREAT_WAVES.size():
		var tid: String = ids[i]
		var th: Dictionary = GameData.THREATS[tid]
		threats.append({"id": tid, "wave": GameData.THREAT_WAVES[i]})
		roster.append({"enemy": th["enemy"], "trait": th.get("trait", ""), "since": GameData.THREAT_WAVES[i], "threat": true})
	var bosses: Array = GameData.BOSS_WAVES.values()
	_shuffle(bosses)
	boss_plan = {}
	var bw: Array = GameData.BOSS_WAVES.keys()
	bw.sort()
	for i in bw.size():
		boss_plan[bw[i]] = bosses[i]


func _shuffle(a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = a[i]
		a[i] = a[j]
		a[j] = tmp


func threat_known(t: Dictionary) -> bool:
	return wave + 1 >= int(t["wave"]) - GameData.THREAT_REVEAL


func _game_over(victory: bool) -> void:
	state = S.OVER
	cancel_placing()
	hud.set_start(false)
	hud.hide_choices()
	hud.hide_place_hint()
	board.clear_slots()
	var key := faction + "_best"
	var best_wave := wave if victory else wave - 1
	stats[key] = max(int(stats.get(key, 0)), best_wave)
	if victory:
		stats[faction + "_wins"] = int(stats.get(faction + "_wins", 0)) + 1
	stats["runs"] = int(stats.get("runs", 0)) + 1
	var earned := int(round(float(maxi(best_wave, 0)) * (1.0 + 0.5 * difficulty))) + (40 if victory else 0)
	stats["renown"] = int(stats.get("renown", 0)) + earned
	_save_stats()
	sfx("victory" if victory else "defeat")
	var lines := "%s  -  %s  -  %s\nHero: %s\nReached wave %d of %d\nEnemies slain: %d      Towers built: %d\nTiles placed: %d      Discoveries: %d\nGold earned: %d\n\nRenown earned: +%d   (total %d - spend it in the War Council)" % [
		GameData.FACTIONS[faction]["name"], String(board.biome.get("name", "")), _diff()["name"],
		GameData.HEROES[hero]["name"] if hero != "" else "-", wave, GameData.MAX_WAVES,
		run_stats["kills"], run_stats["built"], run_stats["tiles"], run_stats["discoveries"], run_stats["gold_earned"],
		earned, int(stats["renown"])]
	hud.show_end(victory, lines)
	if autotest:
		print("AUTOTEST END victory=%s wave=%d kills=%d towers=%d gold=%d tiles=%d fronts=%d renown=+%d" % [
			victory, wave, run_stats["kills"], towers.size(), gold, board.placed.size(), board.battlefronts(), earned])
		get_tree().quit()


# ------------------------------------------------------------------ meta progression

func meta_level(k: String) -> int:
	return int(stats.get("meta_" + k, 0))


func renown() -> int:
	return int(stats.get("renown", 0))


func buy_meta(k: String) -> void:
	var costs: Array = GameData.META_UPGRADES[k]["costs"]
	var lvl := meta_level(k)
	if lvl >= costs.size() or renown() < int(costs[lvl]):
		return
	stats["renown"] = renown() - int(costs[lvl])
	stats["meta_" + k] = lvl + 1
	_save_stats()
	sfx("upgrade")


func hero_unlocked(hid: String) -> bool:
	return int(GameData.HEROES[hid]["cost"]) <= 0 or hid in String(stats.get("heroes", "")).split(",", false)


func unlock_hero(hid: String) -> bool:
	var cost: int = GameData.HEROES[hid]["cost"]
	if hero_unlocked(hid) or renown() < cost:
		return false
	stats["renown"] = renown() - cost
	var have := String(stats.get("heroes", "")).split(",", false)
	have.append(hid)
	stats["heroes"] = ",".join(have)
	_save_stats()
	sfx("chest")
	return true


func hero_tower_bonus(tid: String) -> float:
	var td: Dictionary = hero_fx.get("tower_dmg", {})
	if td.is_empty() or tid not in td["tids"]:
		return 0.0
	return float(td["mult"])


# ------------------------------------------------------------------ phases

func phase_text() -> String:
	match state:
		S.EXPAND: return "Expand the realm - place a terrain tile"
		S.BUILD: return "Build phase - place towers, then start the wave"
		S.WAVE: return "Wave %d - %d enemies remaining" % [wave, enemies.size() + spawn_queue.size()]
		S.REWARD: return "Choose a reward"
		S.OVER: return "Run over"
	return ""


func _next_step() -> void:
	hud.hide_choices()
	hud.hide_place_hint()
	board.clear_slots()
	board.clear_preview()
	tile_pick = -1
	_plan = {}
	if state == S.OVER:
		return
	if _steps.is_empty():
		_enter_build()
		return
	_cur_step = _steps.pop_front()
	match _cur_step:
		"expand": _enter_expand()
		"reward": _enter_reward()
		"blueprint": _enter_blueprint()
		"doctrine": _enter_doctrine()
		"front":
			_open_front()
			_next_step()


func _enter_build() -> void:
	state = S.BUILD
	var boss: String = boss_plan.get(wave + 1, "")
	next_wave_list = WaveBuilder.generate(wave + 1, rng, float(_diff()["count"]), roster, boss)
	var fronts := board.battlefronts()
	var label := "Start Wave %d  [Space]" % (wave + 1)
	hud.set_start(true, label, WaveBuilder.summary(next_wave_list) + "\nFrom %d road end%s" % [fronts, "" if fronts == 1 else "s"])
	_show_flight_lines(_wave_has_fliers(next_wave_list))
	hud.refresh_intel()
	_refresh_ui()


func start_wave() -> void:
	if state != S.BUILD:
		return
	wave += 1
	_wave_leaks.clear()
	spawn_queue = next_wave_list.duplicate()
	wave_clock = -0.3
	_spawned = 0
	wave_routes.clear()
	wave_port_cycle.clear()
	# enemies split evenly across every open road end; a road end that opened just now gets a lighter share
	var ports: Array = board.open_ports.keys()
	for pc in ports:
		wave_routes[pc] = board.route_from(pc)
	for round_i in 3:
		for pc in ports:
			var fresh: bool = int(board.port_opened.get(pc, 0)) == wave and wave > 1
			if round_i == 0 or not fresh:
				wave_port_cycle.append(pc)
	state = S.WAVE
	hud.set_start(false)
	_show_flight_lines(false)
	var boss: String = boss_plan.get(wave, "")
	var arriving := ""
	for t in threats:
		if int(t["wave"]) == wave:
			arriving = GameData.THREATS[t["id"]]["name"]
	if boss != "":
		hud.toast("BOSS WAVE: %s" % GameData.ENEMIES[boss]["name"], Color(1, 0.4, 0.3))
		sfx("boss")
		cam.shake(0.5)
	elif arriving != "":
		hud.toast("New threat: %s!" % arriving, Color(1, 0.55, 0.35))
		sfx("horn")
	else:
		hud.toast("Wave %d" % wave, Color(1, 0.9, 0.7))
		sfx("horn")
	hud.refresh_intel()
	_refresh_ui()


func _wave_complete() -> void:
	for th in get_tree().get_nodes_in_group("thralls"):
		(th as Thrall).crumble()
	var supply := 0
	for c in board.neutrals:
		if board.neutrals[c]["kind"] == "supply":
			supply += 1
	var interest := mini(45, int(gold * float(mods["interest"])))
	var bonus: int = 25 + 4 * wave + int(mods["treasury"]) + mine_income + 15 * supply + interest
	_add_gold(bonus)
	var fronts := board.battlefronts()
	var rc := 1 + int(hero_fx.get("recon", 0)) + clampi(fronts - 1, 0, 3) + int(mods["recon_wave"])
	recon += rc
	if int(mods["builder_every"]) > 0 and wave % int(mods["builder_every"]) == 0:
		builders += 1
	if int(mods["repair"]) > 0:
		hp = mini(max_hp, hp + int(mods["repair"]))
	sfx("wave_clear")
	if wave >= GameData.MAX_WAVES:
		_game_over(true)
		return
	var key := faction + "_best"
	if wave > int(stats.get(key, 0)):
		stats[key] = wave
		_save_stats()
	hud.toast("Wave %d cleared   +%d gold   +%d Rune%s" % [wave, bonus, rc, "" if rc == 1 else "s"], Color(1, 0.9, 0.6))
	for t in threats:
		if int(t["wave"]) - GameData.THREAT_REVEAL == wave + 1:
			hud.toast("Threat Intel: %s arrive on wave %d" % [GameData.THREATS[t["id"]]["name"], t["wave"]], Color(1, 0.6, 0.4))
	_steps = ["reward", "expand"]
	if wave + 1 in NEW_FRONT_WAVES:
		_steps.append("front")
	_next_step()


func reroll() -> void:
	if recon < GameData.REROLL_COST:
		hud.toast("Not enough Runes", Color(1, 0.5, 0.4))
		return
	recon -= GameData.REROLL_COST
	sfx("rune")
	match _cur_step:
		"expand": _enter_expand()
		"reward": _enter_reward()
		"blueprint": _enter_blueprint()
		"doctrine": _enter_doctrine()
	_refresh_ui()


func _reroll_label() -> String:
	return "Reroll  (%d Rune%s, have %d)" % [GameData.REROLL_COST, "" if GameData.REROLL_COST == 1 else "s", recon]


# ------------------------------------------------------------------ expansion (terrain tiles)

func _enter_expand() -> void:
	state = S.EXPAND
	hud.set_start(false)
	tile_cards = _roll_tile_cards(1)
	if tile_cards.is_empty():
		hud.toast("No room left to expand", Color(0.8, 0.8, 0.8))
		_next_step()
		return
	_on_tile_card(0)


func _roll_tile_cards(n: int) -> Array:
	var out: Array = []
	var tries := 0
	while out.size() < n and tries < 40:
		tries += 1
		var card := board.make_tile(rng)
		var ne: int = card["entrances"].size()
		# keep the three cards different from each other
		if tries < 25 and out.any(func(c): return c["entrances"].size() == ne and ne > 2):
			continue
		var pl := _card_placements(card)
		if pl.is_empty():
			continue
		# with one tile on offer, don't keep forcing new battlefronts on a realm that already has several
		if n == 1 and tries < 30:
			var fronts := board.battlefronts()
			if _best_net_fronts(card, pl) > 0 and rng.randf() < clampf(0.22 * float(fronts - 1), 0.0, 0.8):
				continue
		out.append(card)
	return out


## The fewest extra battlefronts this card can add anywhere it fits (negative when it can merge roads).
func _best_net_fronts(card: Dictionary, pl: Array) -> int:
	var best := 99
	for p in pl:
		var plan := board.plan_tile(p[0], card, p[1])
		if not plan.is_empty():
			best = mini(best, int(plan["new_ports"]) - plan["merges"].size())
	return best


## Every (slot, variant) a card fits.
func _card_placements(card: Dictionary) -> Array:
	var out: Array = []
	for slot in board.expansion_slots():
		for k in 6:
			if not board.plan_tile(slot, card, k).is_empty():
				out.append([slot, k])
	return out


func _feature_lines(feats: Array) -> String:
	var parts: PackedStringArray = []
	var plateau := false
	for f in feats:
		match f["type"]:
			"plateau": plateau = true
			"ley": parts.append("Ley crystal (+%d%% damage)" % int(GameData.LEY_BONUS * 100))
			"pond":
				if "Pond" not in parts:
					parts.append("Pond")
			"neutral":
				var nd: Dictionary = GameData.NEUTRALS[f["kind"]]
				parts.append("%s: %s" % [nd["name"], nd["desc"]])
	if plateau:
		parts.insert(0, "High ground (+range)")
	return "\n".join(parts)


func tile_title(card: Dictionary) -> String:
	var ents: Array = card["entrances"]
	match ents.size():
		3: return "Fork"
		4: return "Crossroads"
		5: return "Five Ways"
		6: return "Great Crossroads"
	var d := absi(int(ents[0]) - int(ents[1]))
	d = mini(d, 6 - d)
	var inner := Hex.dist(Hex.E[ents[0]] * (Hex.HALF - 1), Hex.E[ents[1]] * (Hex.HALF - 1))
	var winding: bool = card["paths"][0].size() >= inner + 5
	if winding:
		return ["", "Looping Turn", "Winding Bend", "Winding Road"][d]
	return ["", "Sharp Turn", "Bend", "Straight Road"][d]


func _show_tile_cards() -> void:
	var cards: Array = []
	for c in tile_cards:
		var fits := _card_placements(c)
		var spots := {}
		for p in fits:
			spots[p[0]] = true
		var ne: int = c["entrances"].size()
		var fl := _feature_lines(c["features"])
		var desc := "%d entrances. Each one that doesn't join a road becomes a new enemy spawn." % ne
		var rise: int = c.get("rise", 0)
		if rise > 0:
			desc += "\nRaised tile: one level higher (+range)"
		elif rise < 0:
			desc += "\nLowland: one level lower"
		cards.append({"kind": "TERRAIN TILE", "title": tile_title(c), "tile": c,
			"desc": desc + ("\n" + fl if fl != "" else ""),
			"color": Color(0.55, 0.85, 0.45) if ne <= 2 else Color(0.85, 0.5, 1.0),
			"footer": "Fits %d spot%s" % [spots.size(), "" if spots.size() == 1 else "s"]})
	var fronts := board.battlefronts()
	hud.show_choices("Expand the Realm", "Wave %d approaches from %d road end%s.  Pick a tile, then place it on a glowing spot." % [
		wave + 1, fronts, "" if fronts == 1 else "s"], cards, _on_tile_card, func(_i: int): pass,
		"", Callable(), _reroll_label(), reroll)
	_refresh_ui()


func _on_tile_card(i: int) -> void:
	tile_pick = i
	_variant_offset = 0
	_hover_slot = Board.NONE
	_plan = {}
	hud.hide_choices()
	_slots.clear()
	for p in _card_placements(tile_cards[i]):
		if p[0] not in _slots:
			_slots.append(p[0])
	board.clear_preview()
	board.show_slots(_slots)
	var c: Dictionary = tile_cards[i]
	var fl := _feature_lines(c["features"])
	var rise: int = c.get("rise", 0)
	var lines: PackedStringArray = ["%d entrances" % c["entrances"].size()]
	if rise != 0:
		lines.append("Raised: one level up (+range)" if rise > 0 else "Lowland: one level down")
	if fl != "":
		lines.append(fl)
	hud.show_tile_panel(c, tile_title(c), "\n".join(lines), _reroll_label())
	var mid := Vector3.ZERO
	for sl in _slots:
		mid += Hex.tile_world(sl)
	cam.glide_to(mid / maxf(1.0, _slots.size()))
	sfx("card")


func tile_back() -> void:
	pass   # one tile is offered at a time: reroll it for Runes instead


func _plan_for(slot: Vector2i) -> Dictionary:
	if tile_pick < 0 or slot not in _slots:
		return {}
	var card: Dictionary = tile_cards[tile_pick]
	for k in 6:
		var p := board.plan_tile(slot, card, (_variant_offset + k) % 6)
		if not p.is_empty():
			return p
	return {}


func _update_tile_hover() -> void:
	var slot := board.tile_of(hover_cell) if board.in_bounds(hover_cell) else Board.NONE
	if slot == _hover_slot:
		return
	_hover_slot = slot
	_plan = _plan_for(slot)
	if _plan.is_empty():
		board.clear_preview()
	else:
		board.show_tile_preview(_plan)


func _rotate_tile() -> void:
	if tile_pick < 0:
		return
	# turn to the next rotation that fits this spot
	var cur: int = _plan.get("rot", _variant_offset)
	var card: Dictionary = tile_cards[tile_pick]
	for k in range(1, 7):
		var p := board.plan_tile(_hover_slot, card, (cur + k) % 6) if _hover_slot in _slots else {}
		if not p.is_empty():
			_variant_offset = (cur + k) % 6
			_plan = p
			break
	if _plan.is_empty():
		_variant_offset = (_variant_offset + 1) % 6
	board.show_tile_preview(_plan)
	sfx("click")


func _place_tile(plan: Dictionary) -> void:
	if plan.is_empty():
		return
	var merges: int = plan["merges"].size()
	var opened := board.commit_tile(plan, wave + 1)
	run_stats["tiles"] = int(run_stats.get("tiles", 0)) + 1
	sfx("tile", Hex.tile_world(plan["tile"]))
	cam.shake(0.12)
	if merges > 1:
		hud.toast("Roads merged: %d fewer battlefront%s" % [merges - 1, "" if merges == 2 else "s"], Color(0.6, 1.0, 0.6))
	elif opened.size() > 1:
		hud.toast("The road splits: %d new battlefronts!" % (opened.size() - 1), Color(0.85, 0.5, 1.0))
	recompute_buffs()
	_claim_with_towers()
	_next_step()


## Discoveries on a new tile are claimed at once if a tower already reaches them.
func _claim_with_towers() -> void:
	for t in towers:
		board.claim_in_range(t.position, t.range_world())


func _on_slot_click() -> void:
	if state != S.EXPAND or tile_pick < 0:
		return
	if _plan.is_empty():
		if tile_pick >= 0:
			hud.toast("The tile doesn't fit there - pick a glowing spot", Color(1, 0.5, 0.4))
		return
	var p := _plan
	_plan = {}
	_place_tile(p)


## Lays one tile at a road end with no player input (the first stretch of road, new battlefronts).
func _auto_tile(port: Vector2i) -> void:
	if not board.open_ports.has(port):
		return
	var slot: Vector2i = board.open_ports[port]["tile"] + Hex.E[board.open_ports[port]["side"]]
	for attempt in 40:
		var card := board.make_tile(rng, 2)
		for k in 6:
			var p := board.plan_tile(slot, card, k)
			if not p.is_empty() and p["merges"].size() == 1 and int(p["new_ports"]) == 1:
				board.commit_tile(p, wave + 1)
				recompute_buffs()
				return


## Picks and places a tile like a player would (autotest, menu backdrop, map screenshots).
func _auto_expand() -> void:
	var cards := _roll_tile_cards(1)
	for i in 3:
		if cards.is_empty() or recon < GameData.REROLL_COST or board.battlefronts() < 3:
			break
		if _best_net_fronts(cards[0], _card_placements(cards[0])) <= 0:
			break
		recon -= GameData.REROLL_COST
		cards = _roll_tile_cards(1)
	var best := {}
	var best_score := -INF
	var fronts := board.battlefronts()
	for c in cards:
		for p in _card_placements(c):
			var plan := board.plan_tile(p[0], c, p[1])
			var road_len := 0
			for r in plan["roads"]:
				road_len += r.size()
			var score: float = road_len + rng.randf() * 2.0
			score += 6.0 * (plan["merges"].size() - 1)
			score -= (3.0 + 2.0 * fronts) * maxf(0.0, float(plan["new_ports"]) - 1.0)
			if score > best_score:
				best_score = score
				best = plan
	if not best.is_empty():
		board.commit_tile(best, wave + 1)
		run_stats["tiles"] = int(run_stats.get("tiles", 0)) + 1
		recompute_buffs()
		_claim_with_towers()


## A new road out of the castle, with a free tile on it and gold to defend it.
func _open_front() -> void:
	var sides := board.free_hq_sides()
	if sides.is_empty():
		return
	var side: int = sides[rng.randi() % sides.size()]
	var pc := board.open_hq_exit(side, wave + 1)
	if pc == Board.NONE:
		return
	_auto_tile(pc)
	var reinforce := 120 + wave * 12
	_add_gold(reinforce)
	hud.toast("A new battlefront opens!  +%d gold to fortify it" % reinforce, Color(0.85, 0.5, 1.0))
	sfx("portal")
	cam.glide_to(board.cell_to_world(pc))


# ------------------------------------------------------------------ blueprints & doctrines

## Blueprints of a tier can be offered once the coming wave reaches GameData.TIER_WAVE (or if you own the tower).
func tier_open(tid: String) -> bool:
	return owned.has(tid) or wave + 1 >= int(GameData.TIER_WAVE[GameData.tier_of(tid)])


func _copies_for(tid: String) -> int:
	return GameData.copies_for(tid) + int(hero_fx.get("bonus_copies", {}).get(tid, 0)) + int(mods["extra_copies"])


func _enter_reward() -> void:
	state = S.REWARD
	choice_options = _roll_pairs(3)
	var skip_gold := 30 + wave * 2
	hud.show_pair_choices("Choose your spoils", choice_options, _on_pair_pick,
		"Skip  (+%d gold)" % skip_gold, _on_skip.bind(skip_gold), _reroll_label(), reroll)
	_refresh_ui()


func _roll_kind(exclude: Array) -> String:
	var total := 0.0
	var kinds: Array = []
	for k in GameData.REWARD_KINDS:
		if k in exclude or (k == "masterwork" and (wave < 3 or owned.is_empty())):
			continue
		kinds.append(k)
		total += float(GameData.REWARD_KINDS[k])
	var roll := rng.randf() * total
	for k in kinds:
		roll -= float(GameData.REWARD_KINDS[k])
		if roll <= 0.0:
			return k
	return kinds[kinds.size() - 1]


func _roll_item(kind: String, used: Dictionary) -> Dictionary:
	match kind:
		"blueprint":
			var pool: Array = run_towers().filter(func(t): return not used.has(t) and tier_open(t))
			if pool.is_empty():
				pool = run_towers().filter(func(t): return tier_open(t))
			var w: Array = []
			var total := 0.0
			for tid in pool:
				var x := 1.0 if owned.has(tid) else (3.0 if wave < 12 else 1.5)
				w.append(x)
				total += x
			var roll := rng.randf() * total
			var tid: String = pool[pool.size() - 1]
			for i in pool.size():
				roll -= w[i]
				if roll <= 0.0:
					tid = pool[i]
					break
			used[tid] = true
			var d: Dictionary = GameData.TOWERS[tid]
			var copies := _copies_for(tid)
			return {"kind": "blueprint", "tower": tid, "copies": copies, "badge": "x%d" % copies,
				"name": "%s blueprint x%d%s" % [d["name"], copies, "" if owned.has(tid) else "  (new)"],
				"desc": String(d["desc"]) + "  " + tower_stat_line(tid) + ".  %d gold each to build." % tower_cost(tid)}
		"doctrine":
			var boons: Array = GameData.BOONS.filter(func(b): return b["id"] != "war_chest" and not used.has(b["id"]))
			var total := 0.0
			for b in boons:
				total += float(b["weight"])
			var roll := rng.randf() * total
			var pick: Dictionary = boons[boons.size() - 1]
			for b in boons:
				roll -= float(b["weight"])
				if roll <= 0.0:
					pick = b
					break
			used[pick["id"]] = true
			return {"kind": "doctrine", "boon": pick, "icon": "res://assets/custom/icons/icon_%s.png" % pick["id"],
				"name": "Doctrine: " + String(pick["name"]), "desc": String(pick["desc"])}
		"masterwork":
			var mine: Array = owned.keys().filter(func(t): return not used.has("mw_" + t))
			var tid: String = mine[rng.randi() % mine.size()]
			used["mw_" + tid] = true
			var nm: String = GameData.TOWERS[tid]["name"]
			return {"kind": "masterwork", "tower": tid, "badge": "+30%", "icon": "res://assets/custom/icons/icon_masterwork.png",
				"name": "Masterwork " + nm, "desc": "All your %s towers deal +30%% damage." % nm}
		"builder":
			var n := 2 if rng.randf() < 0.35 else 1
			return {"kind": "builder", "amount": n, "badge": "x%d" % n, "name": "Builders x%d" % n,
				"desc": "Each Builder puts up scaffolding to raise a hex, or a whole tower, one level (+15% range per level)."}
		"digger":
			return {"kind": "digger", "amount": 1, "badge": "x1", "name": "Digger",
				"desc": "Lowers a hex, or a whole tower, one level. Handy for flattening ground for big towers."}
		"gold":
			var g := 50 + 10 * wave
			return {"kind": "gold", "amount": g, "badge": str(g), "name": "%d gold" % g, "desc": "Gold right now."}
		"recon":
			return {"kind": "recon", "amount": 2, "badge": "+2", "name": "2 Runes", "desc": "Cast Runes to reroll the tile or the rewards you're offered."}
	return {}


## Three options, each a pair of different kinds of item. Early on, most pairs lead with a blueprint.
func _roll_pairs(n: int) -> Array:
	var out: Array = []
	var used := {}
	for i in n:
		var k1 := "blueprint" if rng.randf() < 0.7 else _roll_kind([])
		var a := _roll_item(k1, used)
		var b := _roll_item(_roll_kind([k1]), used)
		out.append({"items": [a, b]})
	return out


func _grant(it: Dictionary) -> void:
	match String(it["kind"]):
		"blueprint":
			owned[it["tower"]] = int(owned.get(it["tower"], 0)) + int(it["copies"])
		"doctrine":
			apply_boon(it["boon"])
		"masterwork":
			masterwork[it["tower"]] = float(masterwork.get(it["tower"], 0.0)) + 0.3
		"builder":
			builders += int(it["amount"])
		"digger":
			diggers += int(it["amount"])
		"gold":
			_add_gold(int(it["amount"]))
		"recon":
			recon += int(it["amount"])


func _on_pair_pick(i: int) -> void:
	var names: PackedStringArray = []
	for it in choice_options[i]["items"]:
		_grant(it)
		names.append(String(it["name"]))
	hud.build_tower_bar()
	sfx("card")
	hud.toast("  +  ".join(names), Color(1, 0.9, 0.6))
	_next_step()


func _enter_blueprint() -> void:
	state = S.REWARD
	choice_options = _roll_blueprints(3)
	var skip_gold := 30 + wave * 2
	hud.show_choices("Wave %d Cleared" % wave, "Draft a blueprint.  Each copy lets you build one more of that tower.",
		choice_options, _on_blueprint_pick, func(_i: int): pass, "Skip  (+%d gold)" % skip_gold, _on_skip.bind(skip_gold),
		_reroll_label(), reroll)
	_refresh_ui()


func _roll_blueprints(n: int) -> Array:
	var pool: Array = run_towers().filter(func(t): return tier_open(t))
	var out: Array = []
	while out.size() < n and pool.size() > 0:
		var total := 0.0
		var w: Array = []
		for tid in pool:
			# towers you've never drafted are more likely early on
			var x := 1.0 if owned.has(tid) else (3.0 if wave < 12 else 1.5)
			w.append(x)
			total += x
		var roll := rng.randf() * total
		var pick := pool.size() - 1
		for i in pool.size():
			roll -= w[i]
			if roll <= 0.0:
				pick = i
				break
		var tid: String = pool[pick]
		pool.remove_at(pick)
		var d: Dictionary = GameData.TOWERS[tid]
		var copies := _copies_for(tid)
		var have := int(owned.get(tid, 0))
		out.append({"id": "blueprint", "tower": tid, "copies": copies, "kind": "BLUEPRINT" if owned.has(tid) else "NEW BLUEPRINT",
			"title": "%s  x%d" % [d["name"], copies],
			"desc": String(d["desc"]) + "\n" + tower_stat_line(tid) + ("\nYou have %d unbuilt." % have if owned.has(tid) else ""),
			"color": d["color"], "footer": "%d gold each to build" % tower_cost(tid)})
	return out


func _on_blueprint_pick(i: int) -> void:
	var o: Dictionary = choice_options[i]
	owned[o["tower"]] = int(owned.get(o["tower"], 0)) + int(o["copies"])
	hud.build_tower_bar()
	sfx("card")
	hud.toast("+%d %s blueprint%s" % [o["copies"], GameData.TOWERS[o["tower"]]["name"], "" if int(o["copies"]) == 1 else "s"])
	_next_step()


func _on_skip(amount: int) -> void:
	_add_gold(amount)
	sfx("gold")
	_next_step()


func _enter_doctrine() -> void:
	state = S.REWARD
	choice_options = _roll_boons(3)
	var skip_gold := 30 + wave * 2
	hud.show_choices("Doctrine", "Every %d waves your council adopts a doctrine for the rest of the run." % GameData.DOCTRINE_EVERY,
		choice_options, _on_boon_pick, func(_i: int): pass, "Skip  (+%d gold)" % skip_gold, _on_skip.bind(skip_gold),
		_reroll_label(), reroll)
	_refresh_ui()


func _on_boon_pick(i: int) -> void:
	apply_boon(choice_options[i])
	sfx("card")
	_next_step()


func _roll_boons(n: int) -> Array:
	var pool: Array = []  # [option, weight]
	if wave >= 3:
		for tid in owned:
			var d: Dictionary = GameData.TOWERS[tid]
			pool.append([{"id": "masterwork", "tower": tid, "kind": "MASTERWORK", "title": "Masterwork " + String(d["name"]),
				"desc": "All your %s towers deal +30%% damage." % d["name"], "color": GameData.RARITY_COLORS[1],
				"footer": "Rare"}, 2.5])
	for b in GameData.BOONS:
		var o: Dictionary = b.duplicate()
		var r: int = b["rarity"]
		o["kind"] = GameData.RARITY_NAMES[r].to_upper()
		o["title"] = b["name"]
		o["color"] = GameData.RARITY_COLORS[r]
		o["footer"] = ""
		o["icon"] = "res://assets/custom/icons/icon_%s.png" % b["id"]
		if b["id"] == "war_chest":
			o["amount"] = 80 + wave * 12
			o["desc"] = "Gain %d gold right now." % o["amount"]
		pool.append([o, float(b["weight"])])
	var out: Array = []
	while out.size() < n and pool.size() > 0:
		var total := 0.0
		for e in pool:
			total += e[1]
		var roll := rng.randf() * total
		for e in pool:
			roll -= e[1]
			if roll <= 0.0:
				out.append(e[0])
				pool.erase(e)
				break
	return out


func apply_boon(o: Dictionary) -> void:
	match o["id"]:
		"masterwork":
			masterwork[o["tower"]] = float(masterwork.get(o["tower"], 0.0)) + 0.3
		"war_chest":
			_add_gold(int(o.get("amount", 80 + wave * 12)))
		"whetstone":
			mods["phys"] += 0.12
		"attune":
			mods["magic"] += 0.12
		"range":
			mods["range"] += 0.08
			recompute_buffs()
			for t in towers:
				board.reveal_circle(t.position, t.range_world())
		"rate":
			mods["rate"] += 0.10
		"discount":
			mods["cost"] *= 0.9
		"bounty":
			mods["bounty"] += 1
		"masons":
			max_hp += 5
			hp = max_hp
		"treasury":
			mods["treasury"] += 20
		"ley":
			mods["ley"] += 0.25
		"crit":
			mods["crit"] += 0.12
		"execute":
			mods["execute"] = 0.12 if mods["execute"] <= 0.0 else mods["execute"] + 0.04
		"ability":
			mods["ability_cd"] *= 0.75
	_refresh_ui()


# ------------------------------------------------------------------ castle talents

func talent_rank(id: String) -> int:
	return int(talents.get(id, 0))


func talent_cost(path: String, idx: int) -> int:
	var tp: Dictionary = GameData.TALENTS[path]
	var node: Dictionary = tp["nodes"][idx]
	if tp.get("pick", false):
		return int(round(float(node["cost"]) * (1.0 + 0.8 * talent_rank(node["id"]))))
	if node.get("repeat", false):
		return GameData.TALENT_REPEAT_COST[0] + GameData.TALENT_REPEAT_COST[1] * talent_rank(node["id"])
	return int(GameData.TALENT_COSTS[idx])


## "owned", "open" (can buy now), "locked" (needs the node before it) or "maxed".
func talent_state(path: String, idx: int) -> String:
	var tp: Dictionary = GameData.TALENTS[path]
	var node: Dictionary = tp["nodes"][idx]
	if tp.get("pick", false):
		return "maxed" if talent_rank(node["id"]) >= GameData.TALENT_MAX_RANK else "open"
	if talent_rank(node["id"]) > 0 and not node.get("repeat", false):
		return "owned"
	if idx > 0 and talent_rank(tp["nodes"][idx - 1]["id"]) == 0:
		return "locked"
	return "open"


func buy_talent(path: String, idx: int) -> void:
	if state in [S.MENU, S.OVER] or talent_state(path, idx) != "open":
		return
	var cost := talent_cost(path, idx)
	if gold < cost:
		hud.toast("Not enough gold (%d)" % cost, Color(1, 0.5, 0.4))
		return
	gold -= cost
	var id: String = GameData.TALENTS[path]["nodes"][idx]["id"]
	talents[id] = talent_rank(id) + 1
	_apply_talent(id)
	sfx("talent")
	hud.toast(String(GameData.TALENTS[path]["nodes"][idx]["name"]), GameData.TALENTS[path]["color"])
	recompute_buffs()
	_refresh_ui()


func _apply_talent(id: String) -> void:
	match id:
		"tax": mods["treasury"] += 20
		"interest": mods["interest"] = 0.06
		"scouts":
			mods["recon_wave"] += 1
			mods["builder_every"] = 3
		"mint":
			mods["kill_gold"] += 0.3
			mods["treasury"] += 40
		"guild": mods["cost"] *= 0.9
		"drill": mods["rate"] += 0.12
		"optics": mods["range"] += 0.12
		"masters":
			mods["extra_copies"] += 1
			mods["dmg_all"] += 0.15
		"sky": mods["vs_air"] += 0.3
		"pierce": mods["vs_armor"] += 0.3
		"breaker": mods["shield_break"] += 0.6
		"seers":
			mods["castle_detect"] += 4.0
			mods["vs_camo"] += 0.2
		"giant": mods["vs_boss"] += 0.3
		"walls":
			max_hp += 8
			hp += 8
		"turret": mods["turret"] = 1
		"moat": mods["moat"] = 0.35
		"citadel":
			mods["turret_rate"] = 2.0
			mods["repair"] = 3
		"caravan":
			builders += 1
			recon += 2
		"refine": mods["dmg_all"] += 0.06
		"ramparts":
			max_hp += 4
			hp += 4
			mods["turret_dmg"] = float(mods.get("turret_dmg", 0.0)) + 0.25


## Bulwark: the keep ballista and the moat.
func _castle_defense(delta: float) -> void:
	var cpos := board.cell_to_world(board.center)
	if float(mods["moat"]) > 0.0:
		for e in enemies:
			if not e.flying and Vector2(e.position.x - cpos.x, e.position.z - cpos.z).length() <= 5.0 * GameData.TILE:
				e.apply_slow(float(mods["moat"]), 0.3)
	if int(mods["turret"]) <= 0:
		return
	_keep_cd -= delta
	if _keep_cd > 0.0:
		return
	var best: Enemy = null
	var bd := 4.0 * GameData.TILE
	for e in enemies:
		if e.dead or (e.camo and not e.detected):
			continue
		var d := Vector2(e.position.x - cpos.x, e.position.z - cpos.z).length()
		if d < bd:
			bd = d
			best = e
	if best == null:
		return
	_keep_cd = 1.0 / float(mods["turret_rate"])
	var pkt := {"dmg": 18.0 * (1.0 + 0.12 * wave) * (1.0 + float(mods.get("turret_dmg", 0.0))), "tower_id": "keep", "dtype": "phys", "splash": 0.0, "slow": [], "dot": [],
		"stun": [], "air_bonus": 1.0, "air": true, "ground": true, "shred": false, "push": [], "pct": 0.0, "tower": null}
	var pr := Projectile.new()
	world.add_child(pr)
	pr.setup_homing(self, pkt, cpos + Vector3(0, 4.5, 0), best, 34.0, "arrow", Color(0.9, 0.85, 0.7))
	sfx("arrow", cpos)


# ------------------------------------------------------------------ discoveries

func _process_claims() -> void:
	while not board.claimed_queue.is_empty():
		var cl: Dictionary = board.claimed_queue.pop_front()
		var kind: String = cl["kind"]
		var pos := board.cell_to_world(cl["cell"]) + Vector3(0, 2.5 + board.surface_y(cl["cell"]), 0)
		var msg := ""
		match kind:
			"chest":
				var g := 60 + 10 * wave
				_add_gold(g)
				recon += 1
				msg = "Treasure Chest: +%d gold, +1 Rune" % g
			"shrine":
				var opts := _roll_boons(1)
				if opts.size() > 0:
					apply_boon(opts[0])
					msg = "Ancient Shrine: %s" % opts[0]["title"]
			"mine":
				mine_income += 20
				msg = "Abandoned Mine: +20 gold after every wave"
			"ruins":
				var pool: Array = run_towers().filter(func(t): return not owned.has(t) and tier_open(t))
				if pool.is_empty():
					pool = run_towers().filter(func(t): return tier_open(t))
				var tid: String = pool[rng.randi() % pool.size()]
				owned[tid] = int(owned.get(tid, 0)) + 2
				hud.build_tower_bar()
				msg = "Forgotten Ruins: 2 %s blueprints" % GameData.TOWERS[tid]["name"]
			"cache":
				recon += 3
				msg = "Rune Cache: +3 Runes"
		run_stats["discoveries"] = int(run_stats.get("discoveries", 0)) + 1
		FX.burst(world, pos, Color(1, 0.85, 0.35), 1.6, 0.4)
		FX.float_text(world, pos + Vector3(0, 1, 0), GameData.DISCOVERIES[kind]["name"], Color(1, 0.85, 0.35), 56)
		sfx("chest", pos)
		if msg != "":
			hud.toast(msg, Color(1, 0.85, 0.4))
		_refresh_ui()


# ------------------------------------------------------------------ economy helpers

func _add_gold(n: int) -> void:
	gold += n
	if n > 0:
		run_stats["gold_earned"] = int(run_stats.get("gold_earned", 0)) + n


## Compact stats for a blueprint card, e.g. "42 phys dmg, 0.55/s, range 5.0, hits ground + air".
func tower_stat_line(tid: String) -> String:
	var d: Dictionary = GameData.TOWERS[tid]
	if d["attack"] == "aura_buff":
		var b: Dictionary = d["buff"]
		var what := "+%d%% damage" % int(b["dmg"] * 100) if b.has("dmg") else "+%d%% attack speed" % int(b["rate"] * 100)
		return "Aura: %s to towers within %.1f tiles" % [what, d["range"]]
	var hits: PackedStringArray = []
	if d.get("ground", false):
		hits.append("ground")
	if d.get("air", false):
		hits.append("air")
	var s := "Tier %s. %d %s dmg, %.2f/s, range %.1f, hits %s" % [GameData.TIER_NAMES[GameData.tier_of(tid)], d["dmg"],
		"magic" if d.get("dtype", "") == "magic" else "phys", d["rate"], d["range"], " + ".join(hits)]
	if d.get("detect", false):
		s += ", detects camo"
	if d.get("shred", false):
		s += ", breaks shields"
	return s


func dmg_mult(dtype: String) -> float:
	return mods["magic"] if dtype == "magic" else mods["phys"]


func cost_mult() -> float:
	return mods["cost"]


func tower_cost(tid: String) -> int:
	return int(round(float(GameData.TOWERS[tid]["cost"]) * mods["cost"]))


func haste_bonus() -> float:
	if ability_active > 0.0:
		var ab: Dictionary = GameData.FACTIONS[faction]["ability"]
		if ab["kind"] == "haste":
			return ab["power"]
	return 0.0


func hp_mult_for_wave() -> float:
	return WaveBuilder.hp_mult(wave) * float(_diff()["hp"])


func _diff() -> Dictionary:
	return GameData.DIFFICULTIES[difficulty]


func set_difficulty(i: int) -> void:
	difficulty = clampi(i, 0, GameData.DIFFICULTIES.size() - 1)
	stats["difficulty"] = difficulty
	_save_stats()


func toggle_mute() -> void:
	audio.set_muted(not audio.muted)
	stats["muted"] = audio.muted
	_save_stats()
	hud.refresh_top()


# ------------------------------------------------------------------ main loop

func _process(delta: float) -> void:
	_ui_timer -= delta / max(Engine.time_scale, 0.01)
	if state != S.MENU and _ui_timer <= 0.0:
		_ui_timer = 0.1
		_refresh_ui()
	if state == S.MENU:
		return
	_update_ghost()
	if not board.claimed_queue.is_empty():
		_process_claims()
	if paused:
		return
	if autotest:
		_autotest_step(delta)
	ability_cd = max(0.0, ability_cd - delta)
	ability_active = max(0.0, ability_active - delta)
	if state == S.WAVE:
		_castle_defense(delta)
		_detect_timer -= delta
		if _detect_timer <= 0.0:
			_detect_timer = 0.15
			_update_detection()
		wave_clock += delta
		while not spawn_queue.is_empty() and float(spawn_queue[0]["t"]) <= wave_clock:
			var e: Dictionary = spawn_queue.pop_front()
			var pc: Vector2i = wave_port_cycle[_spawned % wave_port_cycle.size()]
			_spawned += 1
			if GameData.ENEMIES[e["type"]].get("boss", false):
				pc = wave_port_cycle[rng.randi() % wave_port_cycle.size()]
			var en := spawn_enemy(e["type"], wave_routes[pc])
			if String(e.get("trait", "")) != "":
				en.set_trait(e["trait"])
		if spawn_queue.is_empty() and enemies.is_empty():
			_wave_complete()


## Camouflaged enemies can only be targeted inside a detector's reach.
func _update_detection() -> void:
	var any_camo := false
	for e in enemies:
		if e.camo:
			any_camo = true
			break
	if not any_camo:
		return
	var dets: Array = [[board.cell_to_world(board.center), (CASTLE_DETECT + float(mods["castle_detect"])) * GameData.TILE]]
	for t in towers:
		if t.detects():
			dets.append([t.position, t.range_world()])
	for c in board.scout_cells():
		dets.append([board.cell_to_world(c), SCOUT_DETECT * GameData.TILE])
	for e in enemies:
		if not e.camo:
			continue
		var seen := false
		for d in dets:
			var p: Vector3 = d[0]
			if Vector2(e.position.x - p.x, e.position.z - p.z).length() <= float(d[1]):
				seen = true
				break
		e.detected = seen


func _refresh_ui() -> void:
	hud.refresh_top()
	hud.refresh_tower_bar()
	if selected and is_instance_valid(selected):
		hud.show_tower_info(selected)
	var ab: Dictionary = GameData.FACTIONS[faction]["ability"]
	hud.update_ability(ab["name"], ability_cd, ability_active)


# ------------------------------------------------------------------ enemies & combat

func spawn_enemy(type_id: String, r: PackedVector3Array, progress := 0.0) -> Enemy:
	var e := Enemy.new()
	world.add_child(e)
	var d: Dictionary = GameData.ENEMIES[type_id]
	if d.get("flying", false) and r.size() > 2:
		r = flight_route(r)
	var mult := WaveBuilder.hp_mult(wave)
	if d.get("boss", false):
		mult = float(BOSS_HP.get(wave, float(d["hp"]) * (1.0 + 0.02 * wave))) / float(d["hp"])
	mult *= float(_diff()["hp"])
	e.setup(self, type_id, r, mult, progress)
	enemies.append(e)
	if progress <= 0.0:
		VFX.play(world, "magic", r[0] + Vector3(0, 1.0, 0), Color(0.75, 0.4, 1.0), 1.2)
		if e.flying:
			sfx("wings", r[0])
	return e


## Fliers skip the road: straight from where the road starts to the castle.
func flight_route(r: PackedVector3Array) -> PackedVector3Array:
	return PackedVector3Array([r[0], r[r.size() - 1]])


## Points every couple of units along every flight line (road end -> castle), for the bot and the preview.
func _flight_points() -> Array:
	var out: Array = []
	var cpos := board.cell_to_world(board.center)
	for pc in board.open_ports:
		var a: Vector3 = board.route_from(pc)[0]
		var n := int(ceil(Vector2(a.x - cpos.x, a.z - cpos.z).length() / 2.0))
		for i in n + 1:
			out.append(a.lerp(cpos, float(i) / maxf(1.0, n)))
	return out


func _wave_has_fliers(list: Array) -> bool:
	for e in list:
		if GameData.ENEMIES[e["type"]].get("flying", false):
			return true
	return false


## Build phase: dashed lines at flying height from every road end to the castle when the next wave has fliers.
func _show_flight_lines(on: bool) -> void:
	if _flight_mi == null:
		_flight_mi = MeshInstance3D.new()
		_flight_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var m := Models.mat(Color(1.0, 0.55, 0.35), 0.6, 0.55)
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		_flight_mi.material_override = m
		overlay.add_child(_flight_mi)
	_flight_mi.visible = on
	if not on:
		return
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var cpos := board.cell_to_world(board.center)
	for pc in board.open_ports:
		var a: Vector3 = board.route_from(pc)[0]
		var flat := Vector3(cpos.x - a.x, 0, cpos.z - a.z)
		var length := flat.length()
		if length < 1.0:
			continue
		var dir := flat / length
		var side := Vector3(-dir.z, 0, dir.x) * 0.14
		var t := Enemy.FLY_CLIMB
		while t < length - 2.0:
			var p0 := Vector3(a.x, Enemy.FLY_ALT, a.z) + dir * t
			var p1 := p0 + dir * 1.1
			for v in [p0 - side, p0 + side, p1 + side, p0 - side, p1 + side, p1 - side]:
				im.surface_add_vertex(v)
			t += 2.0
	im.surface_end()
	_flight_mi.mesh = im


func enemy_killed(e: Enemy) -> void:
	enemies.erase(e)
	var base_gold: float = float(BOSS_GOLD.get(wave, e.data["gold"])) / (1.0 + wave * 0.015) if e.is_boss else float(e.data["gold"])
	var g: int = int(round(base_gold * (1.0 + wave * 0.015) * (1.0 + float(hero_fx.get("kill_gold", 0.0)) + float(mods["kill_gold"])))) + int(mods["bounty"])
	_add_gold(g)
	run_stats["kills"] += 1
	VFX.death(world, e.aim_pos(), e.data["color"], e.is_boss)
	if e.is_boss:
		VFX.blast(world, e.ground_pos(), 6.0, true)
	if e.is_boss:
		FX.float_text(world, e.position + Vector3(0, 3, 0), "+%d" % g, Color(1, 0.85, 0.3), 96)
		hud.toast("%s defeated!" % e.data["name"], Color(1, 0.85, 0.3))
		sfx("boom", e.position)
		cam.shake(0.8)
	else:
		FX.float_text(world, e.position + Vector3(0, 1.2, 0), "+%d" % g, Color(1, 0.85, 0.3), 36)
		sfx("die", e.position)
	# Black's Plague Tide: poisoned enemies burst when they die
	var burst := float(hero_fx.get("death_burst", 0.0))
	if burst > 0.0 and e.dot_time > 0.0:
		var bd := e.max_hp * burst
		for o in enemies.duplicate():
			if not o.dead and o.position.distance_to(e.position) <= 1.6 * GameData.TILE:
				o.take_damage(bd, "magic", null, true)
		FX.burst(world, e.aim_pos(), Color(0.45, 0.9, 0.3), 1.6, 0.3)
	if e.data.has("split") and state != S.OVER:
		var sp: Dictionary = e.data["split"]
		for i in int(sp["count"]):
			var s := spawn_enemy(sp["into"], e.route, max(0.0, e.progress - 0.5 * i))
			if e.mod_trait != "":
				s.set_trait(e.mod_trait)
	if _try_raise(e):
		e.queue_free()   # it gets back up as a zombie instead of lying down
	else:
		e.play_death()


## Necromancers raise walkers (not bosses) that die in their reach as zombies (Thrall), up to their cap.
func _try_raise(e: Enemy) -> bool:
	if e.is_boss or e.flying or state == S.OVER:
		return false
	for t in towers:
		if not t.data.has("raise") or not t.reaches(e.position, t.position, t.range_world()):
			continue
		t.thralls = t.thralls.filter(func(x): return is_instance_valid(x) and not x.is_queued_for_deletion())
		if t.thralls.size() >= int(t.data["raise"]["max"]) + int(t.fxf("raise_max")):
			continue
		var th := Thrall.new()
		world.add_child(th)
		th.setup(self, e, t)
		t.thralls.append(th)
		return true
	return false


func enemy_leaked(e: Enemy) -> void:
	if e.dead:
		return
	e.dead = true
	enemies.erase(e)
	e.queue_free()
	if state == S.OVER:
		return
	var leak: int = int(BOSS_LEAK.get(wave, e.data["leak"])) if e.is_boss else int(e.data["leak"])
	hp -= leak
	run_stats["leaked"] += 1
	var lk := e.type_id + ("/" + e.mod_trait if e.mod_trait != "" else "")
	_wave_leaks[lk] = int(_wave_leaks.get(lk, 0)) + 1
	FX.burst(world, board.cell_to_world(board.center) + Vector3(0, 2, 0), Color(1, 0.2, 0.2), 2.5, 0.4)
	FX.float_text(world, board.cell_to_world(board.center) + Vector3(0, 4, 0), "-%d" % leak, Color(1, 0.3, 0.3), 72)
	sfx("leak")
	cam.shake(0.25 + 0.05 * leak)
	if hp <= 0:
		hp = 0
		_game_over(false)


func _can_hit(pkt: Dictionary, e: Enemy) -> bool:
	if e.camo and not e.detected:
		return false
	return (e.flying and pkt["air"]) or (not e.flying and pkt["ground"])


func apply_hit(pkt: Dictionary, e: Enemy) -> void:
	if e == null or not is_instance_valid(e) or e.dead:
		return
	var tw: Tower = null
	if is_instance_valid(pkt["tower"]):
		tw = pkt["tower"]
	var dmg: float = pkt["dmg"]
	if e.flying:
		dmg *= float(pkt["air_bonus"]) * (1.0 + float(mods["vs_air"]))
	if e.armor >= 0.3:
		dmg *= 1.0 + float(mods["vs_armor"])
	if e.camo:
		dmg *= 1.0 + float(mods["vs_camo"])
	if e.is_boss:
		dmg *= (1.0 + float(mods["vs_boss"])) * (1.0 + float(pkt.get("boss_bonus", 0.0)))
	var pct: float = float(pkt.get("pct", 0.0))
	if pct > 0.0:
		dmg += e.hp * pct * (0.3 if e.is_boss else 1.0)
	if mods["crit"] > 0.0 and rng.randf() < mods["crit"]:
		dmg *= 3.0
		FX.float_text(world, e.position + Vector3(0, 1.8, 0), "CRIT", Color(1, 0.5, 0.2), 32)
	e.take_damage(dmg, pkt["dtype"], tw, false, bool(pkt.get("shred", false)))
	if e.dead:
		return
	var slow: Array = pkt["slow"]
	if slow.size() == 2:
		e.apply_slow(slow[0], slow[1])
	var dot: Array = pkt["dot"]
	if dot.size() == 2:
		e.apply_dot(dot[0], dot[1], pkt["dtype"])
	var stun: Array = pkt["stun"]
	if stun.size() == 2 and not e.flying and rng.randf() < float(stun[0]):
		e.apply_stun(stun[1])
	var vuln: Array = pkt.get("vuln", [])
	if vuln.size() == 2:
		e.apply_vuln(float(vuln[0]), float(vuln[1]))
	var push: Array = pkt.get("push", [])
	if push.size() == 2 and not e.flying and rng.randf() < float(push[0]):
		e.push_back(float(push[1]) * GameData.TILE)


func apply_splash(pkt: Dictionary, center: Vector3, exclude: Enemy) -> void:
	var r: float = pkt["splash"]
	for e in enemies.duplicate():
		if e == exclude or e.dead or not _can_hit(pkt, e):
			continue
		if Vector2(e.position.x - center.x, e.position.z - center.z).length() <= r:
			apply_hit(pkt, e)


func chain_lightning(pkt: Dictionary, first: Enemy, jumps: int, from: Vector3, col: Color) -> void:
	var points: Array = [from]
	var hit := {}
	var cur: Enemy = first
	var factor := 1.0
	for i in jumps + 1:
		if cur == null:
			break
		var p := cur.aim_pos()
		points.append(p)
		hit[cur] = true
		var p2 := pkt.duplicate()
		p2["dmg"] = float(pkt["dmg"]) * factor
		apply_hit(p2, cur)
		factor *= 0.85
		var nxt: Enemy = null
		var best := GameData.TILE * 2.8
		for e in enemies:
			if e.dead or hit.has(e) or not _can_hit(pkt, e):
				continue
			var d: float = e.position.distance_to(p)
			if d < best:
				best = d
				nxt = e
		cur = nxt
	FX.lightning(world, points, col)
	for i in range(1, points.size()):
		VFX.play(world, "sparks", points[i], col.lightened(0.4))


# ------------------------------------------------------------------ ability

func use_ability() -> void:
	if state == S.MENU or state == S.OVER or ability_cd > 0.0 or ability_active > 0.0 or paused:
		return
	var ab: Dictionary = GameData.FACTIONS[faction]["ability"]
	ability_cd = float(ab["cooldown"]) * mods["ability_cd"]
	match ab["kind"]:
		"haste":
			ability_active = ab["duration"]
			for t in towers:
				FX.ring(world, t.position + Vector3(0, 0.2, 0), Color(1, 0.8, 0.3), 1.6, 0.5)
			hud.toast(ab["name"] + "!", Color(1, 0.8, 0.3))
		"root":
			ability_active = ab["duration"]
			var dmg: float = float(ab["damage"]) * (1.0 + wave * 0.15)
			for e in enemies.duplicate():
				if e.dead or e.flying:
					continue
				e.apply_stun(ab["duration"])
				FX.ring(world, e.ground_pos() + Vector3(0, 0.1, 0), Color(0.4, 0.9, 0.3), 1.0, 0.6)
				e.take_damage(dmg, "magic", null)
			hud.toast(ab["name"] + "!", Color(0.5, 1.0, 0.4))
		"blast":
			var dmg2: float = float(ab["damage"]) * (1.0 + wave * 0.25)
			for e in enemies.duplicate():
				if e.dead or e.flying:
					continue
				FX.burst(world, e.ground_pos() + Vector3(0, 0.4, 0), Color(1.0, 0.5, 0.15), 1.2, 0.35)
				e.take_damage(dmg2, "phys", null)
			cam.shake(0.5)
			hud.toast(ab["name"] + "!", Color(1.0, 0.55, 0.3))
		"surge":
			ability_active = ab["duration"]
			for e in enemies.duplicate():
				if e.dead:
					continue
				e.push_back(float(ab["push"]) * GameData.TILE)
				e.apply_slow(0.4, ab["duration"])
				FX.ring(world, e.ground_pos() + Vector3(0, 0.1, 0), Color(0.35, 0.65, 1.0), 1.2, 0.5)
			hud.toast(ab["name"] + "!", Color(0.45, 0.75, 1.0))
		"reap":
			for e in enemies.duplicate():
				if e.dead:
					continue
				e.take_damage(e.max_hp * (0.05 if e.is_boss else float(ab["pct"])), "magic", null)
				FX.burst(world, e.aim_pos(), Color(0.6, 0.35, 0.9), 0.9, 0.3)
			hud.toast(ab["name"] + "!", Color(0.7, 0.5, 1.0))
	sfx("surge" if ab["kind"] == "surge" else "portal")
	cam.shake(0.2)
	_refresh_ui()


# ------------------------------------------------------------------ building

func begin_placing(tid: String) -> void:
	if state not in [S.BUILD, S.WAVE]:
		return
	if int(owned.get(tid, 0)) <= 0:
		hud.toast("No %s blueprints - draft more after a wave" % GameData.TOWERS[tid]["name"], Color(0.85, 0.8, 0.75))
		return
	if gold < tower_cost(tid):
		hud.toast("Not enough gold", Color(1, 0.5, 0.4))
		return
	cancel_placing()
	deselect()
	placing = tid
	if GameData.arc_of(tid) < 359.0 or GameData.shape_of(tid)["cells"].size() > 1:
		hud.toast("R turns the tower", Color(0.8, 0.95, 0.7))
	var m := Models.tower(tid, GameData.TOWERS[tid]["color"])
	_ghost = m["root"]
	_set_transparency(_ghost, 0.45)
	overlay.add_child(_ghost)
	sfx("click")
	_refresh_ui()


func _set_transparency(n: Node, v: float) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).transparency = v
	for c in n.get_children():
		_set_transparency(c, v)


func cancel_placing() -> void:
	placing = ""
	if _ghost and is_instance_valid(_ghost):
		_ghost.queue_free()
	_ghost = null
	if _ghost_outline:
		_ghost_outline.visible = false
	if _range_mm and selected == null:
		_hide_range()
	for g in _ghost_cells:
		(g as Node3D).visible = false


func _update_ghost() -> void:
	var over_board := board.in_bounds(hover_cell)
	var ground_mode := placing == RAISE or placing == DIG
	_hover_marker.visible = over_board and (placing == "" or ground_mode) and state in [S.BUILD, S.WAVE] and board.is_placed(hover_cell)
	if over_board:
		_hover_marker.position = board.cell_to_world(hover_cell) + Vector3(0, 0.05 + board.surface_y(hover_cell), 0)
		var hm_col := Color(1, 1, 1)
		if placing == RAISE:
			hm_col = Color(0.4, 1.0, 0.5) if board.can_raise(hover_cell) and builders > 0 else Color(1, 0.3, 0.3)
		elif placing == DIG:
			hm_col = Color(0.95, 0.75, 0.4) if board.can_lower(hover_cell) and diggers > 0 else Color(1, 0.3, 0.3)
		_hover_marker.material_override = Models.mat(hm_col, 0.0, 0.35 if ground_mode else 0.18)
	# hovering a tower (not placing anything): outline its whole footprint
	var ht: Tower = board.towers.get(hover_cell) if over_board and placing == "" else null
	if ht and is_instance_valid(ht) and ht != selected:
		_show_outline(_hover_outline, ht.cells)
		_hover_marker.visible = false
	else:
		_hover_outline.visible = false
	for g in _ghost_cells:
		(g as Node3D).visible = false
	if placing == "" or ground_mode or _ghost == null:
		if selected == null:
			_hide_range()
		return
	var cells := GameData.footprint(placing, hover_cell, place_facing)
	var ok := board.can_build_all(cells) and gold >= tower_cost(placing)
	_ghost.visible = over_board
	if not over_board:
		_hide_range()
		_ghost_outline.visible = false
		return
	var col := Color(0.4, 1.0, 0.5) if ok else Color(1.0, 0.3, 0.3)
	var ctr := footprint_center(cells)
	_ghost.position = ctr
	_ghost.rotation.y = Hex.dir_yaw(place_facing)
	_ghost.scale = Vector3.ONE * (1.0 if _ghost.has_meta("fitted") else Tower.SIZE_SCALE[clampi(cells.size() - 1, 0, 6)])
	# each hex says for itself whether it can take the tower: clear, buildable and level with the first hex
	var lvl := board.level_at(cells[0])
	for i in cells.size():
		var g: MeshInstance3D = _ghost_cells[i]
		var good: bool = board.can_build(cells[i]) and board.level_at(cells[i]) == lvl and gold >= tower_cost(placing)
		g.visible = true
		g.position = board.cell_to_world(cells[i]) + Vector3(0, 0.08 + board.surface_y(cells[i]), 0)
		g.material_override = Models.mat(Color(0.4, 1.0, 0.5) if good else Color(1.0, 0.3, 0.3), 0.0, 0.45)
	_show_outline(_ghost_outline, cells, col)
	var d: Dictionary = GameData.TOWERS[placing]
	var nb := 0.2 if "relay" in board.neutrals_near(cells) else 0.0
	var r: float = float(d["range"]) * GameData.TILE * mods["range"] * (1.0 + GameData.ELEVATION_RANGE * board.level_at(hover_cell)) * (1.0 + nb) \
		+ GameData.reach_offset(placing)
	_show_range_cells("g|%s|%s|%d|%s" % [placing, hover_cell, place_facing, ok], ctr, r, GameData.arc_of(placing), place_facing, col,
		float(d.get("line", 0.0)) * GameData.TILE)


## Raise Ground: like Tower Dominion's platforms. Works on empty tiles and under towers.
func begin_raise() -> void:
	if state not in [S.BUILD, S.WAVE]:
		return
	if builders <= 0:
		hud.toast("No Builders - earn them from rewards", Color(0.85, 0.8, 0.75))
		return
	cancel_placing()
	deselect()
	placing = RAISE
	hud.toast("Click a hex or a tower to raise it on scaffolding", Color(0.8, 0.95, 0.7))
	_refresh_ui()


func begin_dig() -> void:
	if state not in [S.BUILD, S.WAVE]:
		return
	if diggers <= 0:
		hud.toast("No Diggers - earn them from rewards", Color(0.85, 0.8, 0.75))
		return
	cancel_placing()
	deselect()
	placing = DIG
	hud.toast("Click a raised hex or tower to lower it", Color(0.8, 0.9, 0.7))
	_refresh_ui()


func raise_cost(c: Vector2i) -> int:
	return int(round((GameData.RAISE_BASE + GameData.RAISE_STEP * board.height_at(c)) * mods["cost"]))


func try_raise(c: Vector2i) -> void:
	var cells: Array = [c]
	var t: Tower = board.towers.get(c)
	if t:
		cells = t.cells
	for cc in cells:
		if not board.can_raise(cc) or (t == null and board.towers.has(cc)):
			hud.toast("Can't raise that" if board.level_at(cc) < Board.MAX_LEVEL else "Already at max height", Color(1, 0.5, 0.4))
			return
	if builders <= 0:
		cancel_placing()
		return
	builders -= 1
	board.raise_cells(cells)
	_after_ground_change(t, c, "scaffold")
	if builders <= 0 or not Input.is_key_pressed(KEY_SHIFT):
		cancel_placing()
	_refresh_ui()


func try_dig(c: Vector2i) -> void:
	var cells: Array = [c]
	var t: Tower = board.towers.get(c)
	if t:
		cells = t.cells
	for cc in cells:
		if not board.can_lower(cc) or (t == null and board.towers.has(cc)):
			hud.toast("Can't dig there (roads and ground level can't go lower)", Color(1, 0.5, 0.4))
			return
	if diggers <= 0:
		cancel_placing()
		return
	diggers -= 1
	board.lower_cells(cells)
	_after_ground_change(t, c, "dig")
	if diggers <= 0 or not Input.is_key_pressed(KEY_SHIFT):
		cancel_placing()
	_refresh_ui()


func _after_ground_change(t: Tower, c: Vector2i, snd: String) -> void:
	if t:
		t.position.y = board.surface_y(t.cell)
		t.elevation = board.level_at(t.cell)
		board.claim_in_range(t.position, t.range_world())
		if t == selected:
			_update_sel_range()
	FX.burst(world, board.cell_to_world(c) + Vector3(0, board.surface_y(c), 0), Color(0.7, 0.55, 0.35), 1.3, 0.3)
	sfx(snd, board.cell_to_world(c))
	recompute_buffs()


func try_place(c: Vector2i) -> void:
	if placing == RAISE:
		try_raise(c)
		return
	if placing == DIG:
		try_dig(c)
		return
	if placing == "":
		return
	var cost := tower_cost(placing)
	var cells := GameData.footprint(placing, c, place_facing)
	if not board.can_build_all(cells):
		var n := cells.size()
		hud.toast(("Needs %d clear, level hexes on your tiles (R turns it)" % n) if n > 1 else "Build on clear ground on your own tiles", Color(1, 0.5, 0.4))
		return
	if gold < cost:
		hud.toast("Not enough gold", Color(1, 0.5, 0.4))
		return
	if int(owned.get(placing, 0)) <= 0:
		cancel_placing()
		return
	var t := Tower.new()
	world.add_child(t)
	t.position = footprint_center(cells)
	t.setup(self, placing, c, place_facing)
	t.spent = cost
	t.on_ley = cells.any(func(x): return board.is_ley(x))
	t.elevation = board.level_at(c)
	for cc in t.cells:
		board.towers[cc] = t
		board.clear_flora(cc)
	towers.append(t)
	owned[placing] = int(owned[placing]) - 1
	board.reveal_circle(t.position, t.range_world())
	board.claim_in_range(t.position, t.range_world())
	gold -= cost
	run_stats["built"] += 1
	VFX.build(world, t.position, cells.size())
	sfx("build", t.position)
	recompute_buffs()
	if not Input.is_key_pressed(KEY_SHIFT) or gold < cost or int(owned[placing]) <= 0:
		cancel_placing()
	_refresh_ui()


func select_tower(t: Tower) -> void:
	cancel_placing()
	selected = t
	_show_outline(_sel_outline, t.cells)
	_update_sel_range()
	hud.show_tower_info(t)


func deselect() -> void:
	selected = null
	if _sel_outline:
		_sel_outline.visible = false
	_hide_range()
	hud.show_tower_info(null)


func _update_sel_range() -> void:
	if selected == null:
		_hide_range()
		return
	var t := selected
	_show_range_cells("s|%d|%d|%d|%.2f" % [t.get_instance_id(), t.level, t.elevation, t.range_world()], t.position,
		t.range_world(), t.arc, t.facing, Color(1.0, 0.9, 0.45), t.line_w)
	_show_outline(_sel_outline, t.cells)


func needs_spec(t: Tower) -> bool:
	return t.level == 2 and GameData.SPECS.has(t.id)


## spec: which specialization to take when going from level II to III.
func upgrade_selected(spec := -1) -> void:
	if selected == null:
		return
	var c := selected.upgrade_cost()
	if c < 0 or gold < c:
		return
	if needs_spec(selected) and spec < 0:
		hud.toast("Choose a specialization in the tower panel", Color(1, 0.9, 0.6))
		return
	gold -= c
	selected.spent += c
	selected.upgrade(spec)
	board.reveal_circle(selected.position, selected.range_world())
	board.claim_in_range(selected.position, selected.range_world())
	sfx("upgrade", selected.position)
	recompute_buffs()
	_update_sel_range()
	_refresh_ui()


func sell_selected() -> void:
	if selected == null:
		return
	var t := selected
	_add_gold(t.sell_value())
	run_stats["gold_earned"] -= t.sell_value()
	owned[t.id] = int(owned.get(t.id, 0)) + 1   # the blueprint comes back
	for cc in t.cells:
		board.towers.erase(cc)
	towers.erase(t)
	FX.burst(world, t.position + Vector3(0, 0.5, 0), Color(1, 0.85, 0.3), 1.0, 0.3)
	sfx("sell", t.position)
	t.queue_free()
	deselect()
	recompute_buffs()
	_refresh_ui()


func cycle_target() -> void:
	if selected:
		selected.target_mode = (selected.target_mode + 1) % GameData.TARGET_MODES.size()
		_refresh_ui()


## Support auras plus neutral buildings (ammo depot: attack speed, relay station: range).
func recompute_buffs() -> void:
	for t in towers:
		t.buff_dmg = 0.0
		t.buff_rate = 0.0
		t.nb_range = 0.0
		t.water_bonus = float(hero_fx.get("water_dmg", 0.0)) if board.near_water(t.cells) else 0.0
		var near := board.neutrals_near(t.cells)
		if "ammo" in near:
			t.buff_rate += 0.25
		if "relay" in near:
			t.nb_range += 0.2
	for s in towers:
		if not s.is_support():
			continue
		var b: Dictionary = s.buff()
		var r: float = s.range_world()
		for t in towers:
			if t == s or t.is_support():
				continue
			if Vector2(t.position.x - s.position.x, t.position.z - s.position.z).length() <= r:
				t.buff_dmg += float(b.get("dmg", 0.0))
				t.buff_rate += float(b.get("rate", 0.0))


# ------------------------------------------------------------------ speed / pause

func cycle_speed() -> void:
	var i := SPEEDS.find(speed)
	speed = SPEEDS[(i + 1) % SPEEDS.size()]
	if autotest:
		speed = 4.0
	Engine.time_scale = speed
	_refresh_ui()


func toggle_pause() -> void:
	if state == S.MENU:
		return
	_set_paused(not paused)


func _set_paused(p: bool) -> void:
	paused = p
	get_tree().paused = p
	hud.set_paused(p)


# ------------------------------------------------------------------ input

## F11 or Alt+Enter: fullscreen on / off, anywhere (menus included). The choice is remembered.
func _input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k and k.pressed and not k.echo and (k.keycode == KEY_F11 or (k.keycode == KEY_ENTER and k.alt_pressed)):
		toggle_fullscreen()
		get_viewport().set_input_as_handled()


func is_fullscreen() -> bool:
	return DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_FULLSCREEN, DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN]


func toggle_fullscreen() -> void:
	set_fullscreen(not is_fullscreen())


func set_fullscreen(on: bool) -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if on else DisplayServer.WINDOW_MODE_WINDOWED)
	stats["fullscreen"] = on
	_save_stats()
	if state == S.MENU and hud.menu_root and is_instance_valid(hud.menu_root):
		hud.show_menu(stats)   # refresh the Fullscreen button's label


func _unhandled_input(event: InputEvent) -> void:
	if state == S.MENU:
		return
	if cam.handle_input(event):
		return
	if event is InputEventMouseMotion:
		_update_hover((event as InputEventMouseMotion).position)
		if state == S.EXPAND and tile_pick >= 0:
			_update_tile_hover()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		_update_hover(mb.position)
		if mb.button_index == MOUSE_BUTTON_RIGHT:
			# right-drag pans the camera; a right click (no drag) cancels
			if mb.pressed:
				_rmb_at = mb.position
			elif mb.position.distance_to(_rmb_at) < 6.0:
				if placing != "":
					cancel_placing()
					_refresh_ui()
			return
		if not mb.pressed or mb.button_index != MOUSE_BUTTON_LEFT:
			return
		if state == S.EXPAND:
			if tile_pick >= 0:
				_update_tile_hover()
				_on_slot_click()
			return
		if state == S.REWARD or state == S.OVER:
			return
		if placing != "":
			try_place(hover_cell)
		elif board.towers.has(hover_cell):
			select_tower(board.towers[hover_cell])
			sfx("click")
		else:
			deselect()
	elif event is InputEventKey:
		var k := event as InputEventKey
		if not k.pressed or k.echo:
			return
		_handle_key(k.keycode)


func _handle_key(code: Key) -> void:
	if state == S.EXPAND:
		match code:
			KEY_R: _rotate_tile()
			KEY_C: hud.toggle_castle()
			KEY_M: toggle_mute()
			KEY_P: toggle_pause()
			KEY_H: hud.help_panel.visible = not hud.help_panel.visible
		return
	match code:
		KEY_SPACE:
			start_wave()
		KEY_U:
			upgrade_selected()
		KEY_X, KEY_DELETE:
			sell_selected()
		KEY_T:
			cycle_target()
		KEY_F:
			use_ability()
		KEY_V:
			cycle_speed()
		KEY_P:
			toggle_pause()
		KEY_M:
			toggle_mute()
		KEY_H:
			hud.help_panel.visible = not hud.help_panel.visible
		KEY_R:
			if placing != "" and placing != RAISE and placing != DIG:
				place_facing = (place_facing + 1) % 6
				sfx("click")
		KEY_B, KEY_G:
			begin_raise()
		KEY_N:
			begin_dig()
		KEY_C:
			hud.toggle_castle()
		KEY_ESCAPE:
			if hud.castle_open():
				hud.toggle_castle()
			elif placing != "":
				cancel_placing()
			else:
				deselect()
			_refresh_ui()
		_:
			if code >= KEY_1 and code <= KEY_9:
				var i: int = code - KEY_1
				var list: Array = bar_towers()
				if i < list.size():
					begin_placing(list[i])


func _update_hover(screen_pos: Vector2) -> void:
	hover_cell = board.pick_cell(cam.camera.project_ray_origin(screen_pos), cam.camera.project_ray_normal(screen_pos))


# ------------------------------------------------------------------ save

func _load_stats() -> void:
	var cf := ConfigFile.new()
	if cf.load(SAVE_PATH) == OK:
		for k in cf.get_section_keys("stats"):
			stats[k] = cf.get_value("stats", k)


func _save_stats() -> void:
	# test / screenshot modes never touch the player's save
	if autotest or shot_dir != "" or OS.get_cmdline_user_args().size() > 0:
		return
	var cf := ConfigFile.new()
	for k in stats:
		cf.set_value("stats", k, stats[k])
	cf.save(SAVE_PATH)


# ------------------------------------------------------------------ autotest (headless play-through)

func _autotest_step(delta: float) -> void:
	_auto_t -= delta
	if _auto_t > 0.0:
		return
	_auto_t = 0.25
	match state:
		S.EXPAND:
			if shot_dir != "" and wave in [0, 5] and not _shots_taken.has("expand_%d" % wave):
				_auto_t = 99.0
				await get_tree().create_timer(0.6).timeout
				await _shot("expand_%d" % wave)
				await get_tree().create_timer(0.3).timeout
				_hover_slot = Board.NONE
				hover_cell = Hex.tile_center(_slots[0])
				_update_tile_hover()
				cam.focus(Hex.tile_world(_slots[0]))
				await get_tree().create_timer(0.8).timeout
				await _shot("place_%d" % wave)
				_on_slot_click()
				_auto_t = 0.25
				return
			hud.hide_choices()
			board.clear_slots()
			board.clear_preview()
			_auto_expand()
			_next_step()
		S.REWARD:
			if _cur_step == "reward":
				print("AUTOTEST wave=%d hp=%d gold=%d recon=%d towers=%d tiles=%d fronts=%d fps=%d builders=%d talents=%s owned=%s leaks=%s" % [wave, hp, gold, recon,
					towers.size(), board.placed.size(), board.battlefronts(), Engine.get_frames_per_second(), builders, str(talents.keys()), str(owned), str(_wave_leaks)])
			if shot_dir != "" and wave == 2 and not _shots_taken.has("reward"):
				_auto_t = 99.0
				hud._show_pair_detail(choice_options[1]["items"])
				await get_tree().create_timer(0.6).timeout
				await _shot("reward")
				_auto_t = 0.25
				return
			if wave >= _auto_max_wave:
				print("AUTOTEST END reached max wave %d hp=%d" % [wave, hp])
				get_tree().quit()
				return
			_on_pair_pick(_auto_pick_pair())
		S.BUILD, S.WAVE:
			if shot_dir != "" and state == S.BUILD and wave == 4 and not _shots_taken.has("castle"):
				_auto_t = 99.0
				_auto_talents()
				hud.toggle_castle()
				await get_tree().create_timer(0.6).timeout
				await _shot("castle")
				hud.toggle_castle()
				_auto_t = 0.25
				return
			if shot_dir != "" and state == S.WAVE and enemies.size() > 3 and not _shots_taken.has("ramp") and board.ramps.size() > 0:
				var rc: Vector2i = board.ramps.keys()[0]
				_auto_t = 3.0
				cam.focus(board.cell_to_world(rc))
				cam._target_dist = 16.0
				await get_tree().create_timer(1.2).timeout
				await _shot("ramp")
				cam._target_dist = 40.0
				return
			_auto_build()
			if state == S.BUILD:
				start_wave()
			var boss_here: Enemy = null
			for e in enemies:
				if e.is_boss:
					boss_here = e
			var ready_for_shot := (wave in [10, 20] and boss_here != null and boss_here.progress > 8.0) or (wave in [4, 9, 15] and enemies.size() > 6)
			if shot_dir != "" and state == S.WAVE and ready_for_shot:
				var key := "wave_%d" % wave
				if not _shots_taken.has(key) and towers.size() > 0:
					select_tower(towers[towers.size() / 2])
					var focus_on: Enemy = boss_here if boss_here else enemies[enemies.size() / 2]
					_auto_t = 3.0
					cam.focus(focus_on.position)
					cam._target_dist = 26.0
					await get_tree().create_timer(1.0).timeout
					await _shot(key)
					deselect()
			if ability_cd <= 0.0 and enemies.size() > 8:
				use_ability()


func _auto_build() -> void:
	# Spend gold like a player: upgrade sometimes, raise ground sometimes, otherwise build near the road.
	_auto_talents()
	for attempt in 6:
		if builders > 0 and towers.size() > 2 and rng.randf() < 0.3:
			var rt: Tower = towers[rng.randi() % towers.size()]
			if not rt.is_support() and rt.cells.all(func(x): return board.can_raise(x)):
				placing = RAISE
				try_raise(rt.cell)
				placing = ""
				continue
		var can_build_any := false
		for tid in owned:
			if int(owned[tid]) > 0 and gold >= tower_cost(tid):
				can_build_any = true
		if (towers.size() >= 4 and rng.randf() < 0.35) or (towers.size() > 0 and not can_build_any):
			var t: Tower = towers[rng.randi() % towers.size()]
			var c := t.upgrade_cost()
			if c > 0 and gold >= c:
				select_tower(t)
				upgrade_selected(rng.randi() % 2 if needs_spec(t) else -1)
				deselect()
				continue
		if not can_build_any:
			return
		var choices: Array = owned.keys().filter(func(k): return int(owned[k]) > 0 and gold >= tower_cost(k))
		var tid: String = choices[rng.randi() % choices.size()]
		# like a player would: cover as much road as possible, favoring the least-defended road end
		var route: Array = Array(_auto_weakest_route())
		var d: Dictionary = GameData.TOWERS[tid]
		if d.get("air", false):
			var fly_soon := _wave_has_fliers(next_wave_list) or threats.any(func(t): return threat_known(t) \
				and GameData.ENEMIES[GameData.THREATS[t["id"]]["enemy"]].get("flying", false))
			if not d.get("ground", false):
				route = _flight_points()
			elif fly_soon:
				route.append_array(_flight_points())
		var r: float = float(d["range"]) * GameData.TILE
		var arc := GameData.arc_of(tid)
		var roads: Array = board.path_cells.keys()
		var best := Board.NONE
		var best_f := 4
		var best_score := -1.0
		var turns: Array = [4] if (arc >= 359.0 and GameData.shape_of(tid)["cells"].size() == 1) else [0, 1, 2, 3, 4, 5]
		for k in 60:
			var pc: Vector2i = roads[rng.randi() % roads.size()]
			var near: Array = Hex.disc(pc, 3)
			var c2: Vector2i = near[rng.randi() % near.size()]
			var f: int = turns[rng.randi() % turns.size()]
			var cells := GameData.footprint(tid, c2, f)
			if not board.can_build_all(cells):
				continue
			var wp := footprint_center(cells)
			var rr := r * (1.0 + GameData.ELEVATION_RANGE * board.level_at(c2)) + GameData.reach_offset(tid)
			var fd := Hex.dir_world(f)
			var score := 0.0
			for p in route:
				var v := Vector2(p.x - wp.x, p.z - wp.z)
				if v.length() <= rr and (arc >= 359.0 or v.length() < 0.1 or v.normalized().dot(Vector2(fd.x, fd.z)) >= cos(deg_to_rad(arc * 0.5))):
					score += 1.0
			if score > best_score:
				best_score = score
				best = c2
				best_f = f
		if best == Board.NONE:
			return
		placing = tid
		place_facing = best_f
		try_place(best)
		placing = ""


func _auto_weakest_route() -> PackedVector3Array:
	var best := PackedVector3Array()
	var best_cover := INF
	for pc in board.open_ports:
		var route := board.route_from(pc)
		var cover := 0.0
		for t in towers:
			for p in route:
				if Vector2(p.x - t.position.x, p.z - t.position.z).length() <= t.range_world():
					cover += t.damage() * max(t.fire_rate(), 0.5)
		cover /= maxf(1.0, route.size())
		if cover < best_cover:
			best_cover = cover
			best = route
	return best


## Bot castle talents: economy early, then towers; slayers against revealed threats; the keep late.
func _auto_talents() -> void:
	if state != S.BUILD or gold < 180 or wave < 3:
		return
	var order: Array = [["treasury", 0], ["artificers", 0], ["treasury", 1], ["artificers", 1], ["bulwark", 0],
		["artificers", 2], ["treasury", 2], ["bulwark", 1], ["artificers", 3], ["treasury", 3]]
	for t in threats:
		if threat_known(t):
			var th: Dictionary = GameData.THREATS[t["id"]]
			if GameData.ENEMIES[th["enemy"]].get("flying", false):
				order.push_front(["slayers", 0])
			if th.get("trait", "") == "shield":
				order.push_front(["slayers", 2])
			if th.get("trait", "") == "camo":
				order.push_front(["slayers", 3])
	for o in order:
		if talent_state(o[0], o[1]) == "open" and gold - talent_cost(o[0], o[1]) >= 120:
			buy_talent(o[0], o[1])
	for k in 6:
		var o: Array = [["artificers", 4], ["bulwark", 4], ["treasury", 4]][k % 3]
		if talent_state(o[0], o[1]) == "open" and gold - talent_cost(o[0], o[1]) >= 250:
			buy_talent(o[0], o[1])


func _auto_pick_pair() -> int:
	var best := 0
	var best_score := -INF
	for i in choice_options.size():
		var score := rng.randf() * 0.5
		for it in choice_options[i]["items"]:
			match String(it["kind"]):
				"blueprint":
					score += 1.2 + _blueprint_need(it["tower"])
				"doctrine": score += 1.0
				"masterwork": score += 0.9
				"builder": score += 0.7
				"gold": score += 0.8
				"recon", "digger": score += 0.3
		if score > best_score:
			best_score = score
			best = i
	return best


func _blueprint_need(tid: String) -> float:
	var d: Dictionary = GameData.TOWERS[tid]
	var score := 0.0
	var have_detect := towers.any(func(t): return t.detects()) or owned.keys().any(func(k): return GameData.TOWERS[k].get("detect", false) and int(owned[k]) > 0)
	for t in threats:
		if not threat_known(t):
			continue
		var th: Dictionary = GameData.THREATS[t["id"]]
		if th.get("trait", "") == "camo" and d.get("detect", false) and not have_detect:
			score += 3.0
		if th.get("trait", "") == "shield" and (d.get("shred", false) or d.get("dtype", "") == "magic"):
			score += 1.0
		if GameData.ENEMIES[th["enemy"]].get("flying", false) and d.get("air", false):
			score += 2.0 if int(t["wave"]) <= wave + 3 else 1.0
	if String(d["attack"]).begins_with("aura_") and towers.size() < 6:
		score -= 1.5
	return score - 0.3 * int(owned.get(tid, 0))


## Bot drafting: counter the threats it knows about, then fill out the roster.
func _auto_pick_blueprint() -> int:
	var need := {}
	for t in threats:
		if threat_known(t):
			var th: Dictionary = GameData.THREATS[t["id"]]
			var ed: Dictionary = GameData.ENEMIES[th["enemy"]]
			if th.get("trait", "") == "camo":
				need["detect"] = true
			if th.get("trait", "") == "shield":
				need["shred"] = true
			if ed.get("flying", false):
				need["air"] = true
	for w in boss_plan:
		if int(w) - wave <= 4 and GameData.ENEMIES[boss_plan[w]].get("flying", false):
			need["air"] = true
	var best := 0
	var best_score := -INF
	for i in choice_options.size():
		var tid: String = choice_options[i]["tower"]
		var d: Dictionary = GameData.TOWERS[tid]
		var score := rng.randf()
		var have_detect := towers.any(func(t): return t.detects()) or owned.keys().any(func(k): return GameData.TOWERS[k].get("detect", false) and int(owned[k]) > 0)
		if need.has("detect") and d.get("detect", false) and not have_detect:
			score += 3.0
		if need.has("shred") and (d.get("shred", false) or d.get("dtype", "") == "magic"):
			score += 1.5
		if need.has("air") and d.get("air", false):
			score += 1.0
		if d["attack"] == "aura_buff" and towers.size() < 6:
			score -= 2.0
		score -= 0.4 * int(owned.get(tid, 0))
		if score > best_score:
			best_score = score
			best = i
	return best
