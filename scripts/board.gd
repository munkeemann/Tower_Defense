class_name Board
extends Node3D
## The hex map.
##
## The world is a lattice of small flat-top hex cells (see Hex). Terrain tiles are big flat-top hexagons,
## one every 6 cells: 31 whole cells, plus half a cell at the middle of each side and a third of a cell at
## each corner. Halves and thirds are shared with the neighboring tile; once both tiles are down they merge
## into whole cells, and the new tile's seam copies the existing tile's heights so the join is flat.
## Every cell is drawn as 6 wedges and each wedge belongs to exactly one tile slot, which is what makes
## the half cells on an open edge look like half hexes.
##
## Roads run from the half cell at each entrance to the middle of the tile. Every open entrance on the
## frontier is an enemy spawn point; enemies take the shortest road to the castle.

enum T { GRASS, TREE, ROCK, LEY, WATER, BUILDING, POI, CASTLE }

const E := Hex.E
const LEVEL_H := 1.1
const MAX_LEVEL := 3
const BASE_Y := -1.0
const WATER_Y := -0.3
const MAP_RADIUS := 5          # tile slots from the castle tile to the map edge
## Outside your tiles the world is a flat, slightly lower backdrop meadow, so every placed tile stands
## out as a raised block with rounded edges.
const BACKDROP := -2
const BACKDROP_Y := -1.6        # the grass around the board sits well below it, so your tiles read as a raised board
const BACKDROP_TINT := Color(0.7, 0.76, 0.66)
const FRONTIER_WALLS := false
const NONE := Vector2i(99999, 99999)
const LEVEL_TINTS := [Color(0.84, 0.86, 0.84), Color(0.97, 0.98, 0.93), Color(1.08, 1.07, 0.95), Color(1.18, 1.14, 0.98)]

var center := Vector2i.ZERO
var biome: Dictionary = {}
var biome_id := ""
var seed_value := 0
var rng := RandomNumberGenerator.new()

# wild land (under the fog, until a tile replaces it)
var wild_h := {}               # cell -> level (-1 = lake bed)
var wild_t := {}               # cell -> T
# placed tiles
var placed := {}               # tile slot -> {"entrances": Array[int], "level": int}
var height := {}               # cell -> level, for cells of placed tiles (shared cells keep the first value)
var terrain := {}              # cell -> T, for cells of placed tiles
var whole := {}                # cells whose every wedge is on a placed tile (buildable area)
var path_cells := {}           # road cell -> true
var links := {}                # road cell -> Array of linked road cells (the castle center is the root)
var ramps := {}                # road cell -> side index its slope rises toward
var bridges := {}              # road cell over lake water -> true (drawn as water with a bridge on it)
var open_ports := {}           # open entrance half cell -> {"tile": Vector2i, "side": int}
var port_opened := {}          # port cell -> wave it opened
var portals := {}              # port cell -> Node3D
var towers := {}               # cell -> Tower (every cell of its footprint)
var neutrals := {}             # cell -> {"kind", "node"}
var pois := {}                 # cell -> {"kind", "node"}
var claimed_queue: Array = []

var _slots: Array = []         # every tile slot you can build on
var _draw_slots: Array = []    # those plus a ring of wild land around the map edge
var _info: Array = []          # template cells with precomputed neighbor-wedge tile offsets
var _dist := {}
var _net_dirty := true
var _meshes := {}              # tile slot -> MeshInstance3D
var _preview_nodes: Array = []
var _slot_marks: Array = []
var _castle: Node3D
var _ground: Node3D            # kept for the FPS probe


static func cell_to_world(c: Vector2i) -> Vector3:
	return Hex.to_world(c)


static func world_to_cell(p: Vector3) -> Vector2i:
	return Hex.from_world(p)


func in_map(t: Vector2i) -> bool:
	return Hex.length(t) <= MAP_RADIUS


func in_bounds(c: Vector2i) -> bool:
	return in_map(Hex.tile_of_point(Hex.to_world(c)))


func tile_of(c: Vector2i) -> Vector2i:
	return Hex.tile_of_point(Hex.to_world(c))


func level_at(c: Vector2i) -> int:
	if height.has(c):
		return height[c]
	return int(wild_h.get(c, 0))


func height_at(c: Vector2i) -> int:
	return level_at(c)


func surface_y(c: Vector2i) -> float:
	var l := level_at(c)
	if l == BACKDROP:
		return BACKDROP_Y
	return l * LEVEL_H if l >= 0 else BASE_Y + 0.15


func road_y(c: Vector2i) -> float:
	return surface_y(c) + (0.5 * LEVEL_H if ramps.has(c) else 0.0) + 0.02


func is_castle(c: Vector2i) -> bool:
	return terrain.get(c, -1) == T.CASTLE


func is_placed(c: Vector2i) -> bool:
	return whole.has(c)


func is_ley(c: Vector2i) -> bool:
	return terrain.get(c, -1) == T.LEY


func level_tint(lvl: int) -> Color:
	return LEVEL_TINTS[clampi(lvl, 0, LEVEL_TINTS.size() - 1)]


## Towers go on whole cells of your own tiles: open grass or ley crystals, not the road.
func can_build(c: Vector2i) -> bool:
	if not whole.has(c) or path_cells.has(c) or towers.has(c):
		return false
	var t: int = terrain.get(c, -1)
	return t == T.GRASS or t == T.LEY


## A multi-cell footprint needs every cell buildable and level.
func can_build_all(cells: Array) -> bool:
	if cells.is_empty():
		return false
	var lvl := level_at(cells[0])
	for c in cells:
		if not can_build(c) or level_at(c) != lvl:
			return false
	return true


func battlefronts() -> int:
	return open_ports.size()


func slot_world(t: Vector2i) -> Vector3:
	return Hex.tile_world(t)


# ------------------------------------------------------------------ generation

func generate(seed_v: int, want_biome := "") -> void:
	Hex.setup()
	_prep_info()
	for ch in get_children():
		ch.queue_free()
	for d in [wild_h, wild_t, placed, height, terrain, whole, path_cells, links, ramps, open_ports, port_opened,
			portals, towers, neutrals, pois, _meshes, _cell_props, _prop_sets, bridges, _scatter_mm, _scatter_cell,
			_frontier, _signed]:
		d.clear()
	_road_mi = null
	_bridge_root = null
	_water_mi = null
	_scaffold.clear()
	claimed_queue.clear()
	_preview_nodes.clear()
	_slot_marks.clear()
	_net_dirty = true
	seed_value = seed_v
	rng.seed = seed_v
	var ids: Array = GameData.BIOMES.keys()
	biome_id = want_biome if GameData.BIOMES.has(want_biome) else ids[rng.randi() % ids.size()]
	biome = GameData.BIOMES[biome_id]
	Enemy.GROUND_Y = 0.0
	_slots.clear()
	_draw_slots.clear()
	for q in range(-MAP_RADIUS - 1, MAP_RADIUS + 2):
		for s in range(-MAP_RADIUS - 1, MAP_RADIUS + 2):
			var t := Vector2i(q, s)
			if Hex.length(t) <= MAP_RADIUS + 1:
				_draw_slots.append(t)
				if in_map(t):
					_slots.append(t)
	_gen_wild()
	_init_fog()
	_stamp_hq([4])
	_build_props()
	for t in _draw_slots:
		_rebuild_mesh(t)
		_build_scatter(t)
	_update_frontier(Vector2i.ZERO)
	_rebuild_roads()
	_rebuild_water()
	_build_skirt()
	_castle = Models.castle()
	_castle.scale = Vector3.ONE * 1.4
	_castle.position = cell_to_world(center)
	add_child(_castle)



## The backdrop: flat meadow with a few cosmetic groves. Tiles bring their own terrain when placed.
func _gen_wild() -> void:
	var tn := FastNoiseLite.new()
	tn.seed = seed_value
	tn.frequency = 0.06
	for t in _draw_slots:
		for e in _info:
			var g: Vector2i = t * Hex.K + e["off"]
			if wild_h.has(g):
				continue
			wild_h[g] = BACKDROP
			# the backdrop is plain grass; the old grove rolls still run so a seed grows the same map
			var p := Hex.to_world(g)
			if not (tn.get_noise_2d(p.x, p.z) > 0.5 and rng.randf() < 0.22) and not rng.randf() < 0.002:
				rng.randf()
			wild_t[g] = T.GRASS


## Precompute, for every cell of the tile template, which tile slot owns each neighboring wedge
## (as an offset from the tile), so mesh building doesn't redo the geometry.
func _prep_info() -> void:
	if not _info.is_empty():
		return
	for entry in Hex.TEMPLATE:
		var off: Vector2i = entry[0]
		var nb: Array = []
		var same: Array = []
		for i in 6:
			nb.append(Hex.wedge_tile(off + E[i], (i + 3) % 6))
			same.append(Hex.wedge_tile(off, i))
		_info.append({"off": off, "mask": entry[1], "nb": nb, "same": same})


# ------------------------------------------------------------------ materials & meshes

static var _mat_cache := {}


func terrain_mat() -> Material:
	var key := "hex|" + biome_id
	if _mat_cache.has(key):
		return _mat_cache[key]
	var tex := "res://assets/custom/textures/"
	var m: Material
	if ResourceLoader.exists(tex + "tex_grass.png") and ResourceLoader.exists(tex + "tex_dirt.png") and ResourceLoader.exists(tex + "tex_cliff.png"):
		var sm := ShaderMaterial.new()
		sm.shader = load("res://shaders/terrain.gdshader")
		sm.set_shader_parameter("grass_tex", load(tex + "tex_grass.png"))
		sm.set_shader_parameter("dirt_tex", load(tex + "tex_dirt.png"))
		sm.set_shader_parameter("cliff_tex", load(tex + "tex_cliff.png"))
		sm.set_shader_parameter("use_palette", false)
		sm.set_shader_parameter("dirt_from_uv", true)
		sm.set_shader_parameter("stylized", true)
		if ResourceLoader.exists(tex + "tex_sand.png") and ResourceLoader.exists(tex + "tex_stone.png"):
			sm.set_shader_parameter("sand_tex", load(tex + "tex_sand.png"))
			sm.set_shader_parameter("stone_tex", load(tex + "tex_stone.png"))
			sm.set_shader_parameter("has_extra", true)
		var tint: Color = biome.get("tint", Color.WHITE)
		sm.set_shader_parameter("grass_tint", Vector3(tint.r, tint.g, tint.b))
		sm.set_shader_parameter("detail", 0.16)
		m = sm
	else:
		var st := StandardMaterial3D.new()
		st.vertex_color_use_as_albedo = true
		st.roughness = 0.95
		m = st
	_mat_cache[key] = m
	return m


## Level and whether it's tile ground, for a cell as seen from the tile slot that owns the wedge.
func _wedge_level(g: Vector2i, t: Vector2i) -> int:
	if placed.has(t):
		return int(height.get(g, placed[t]["level"]))
	return int(wild_h.get(g, 0))


## Surface height of a cell at a world point (ramps slope toward their high side).
func _surf(g: Vector2i, t: Vector2i, p: Vector3) -> float:
	if Hex.length(t) > MAP_RADIUS + 1:
		return BASE_Y
	var lvl := _wedge_level(g, t)
	if lvl == BACKDROP:
		return BACKDROP_Y
	if lvl < 0 or (placed.has(t) and bridges.has(g)):
		return BASE_Y + 0.15
	var y := lvl * LEVEL_H
	if placed.has(t) and ramps.has(g):
		var rel := p - Hex.to_world(g)
		y += LEVEL_H * clampf(0.5 + rel.dot(Hex.dir_world(ramps[g])) / (Hex.SQ3 * Hex.R), 0.0, 1.0)
	return y


var _mv := PackedVector3Array()
var _mn := PackedVector3Array()
var _mc := PackedColorArray()
var _mu := PackedVector2Array()
var _mu2 := PackedVector2Array()


func _tri(a: Vector3, b: Vector3, c: Vector3, n: Vector3, col: Color, dirt: float, sand := 0.0, stone := 0.0) -> void:
	# Godot's front faces wind clockwise seen from the normal side
	if (b - a).cross(c - a).dot(n) > 0.0:
		var tmp := b
		b = c
		c = tmp
	_mv.append(a)
	_mv.append(b)
	_mv.append(c)
	for k in 3:
		_mn.append(n)
		_mc.append(col)
		_mu.append(Vector2(dirt, 0))
		_mu2.append(Vector2(sand, stone))


func _wall(a: Vector3, b: Vector3, a2: float, b2: float, out: Vector3, col: Color) -> void:
	var a_lo := Vector3(a.x, a2, a.z)
	var b_lo := Vector3(b.x, b2, b.z)
	_tri(a, b, b_lo, out, col, 0.0)
	_tri(a, b_lo, a_lo, out, col, 0.0)


# ------------------------------------------------------------------ rounded terrain edges
## Wherever the ground drops (tile edges above the backdrop, cliffs, plateaus, pond shores) the top edge is
## rounded off with a quarter-circle lip. Every wedge's surface is a function of its distance to lower ground,
## so neighboring hexes meet without cracks, and any leftover height difference along an edge becomes a
## sampled wall.

const BEVEL_R := 0.42          # radius of the rounded lip
const BEVEL_N := 6             # subdivisions of a rounded wedge
var _ctx := {}                 # cell -> rounding data, rebuilt with each mesh
var _pos_buf := PackedVector3Array()
var _nrm_buf := PackedVector3Array()


## Level of one wedge for rounding: the backdrop, water and the void count as low, ramps as their high end
## (so the ground a ramp climbs to isn't rounded off).
func _eff_level(g: Vector2i, t: Vector2i) -> int:
	if Hex.length(t) > MAP_RADIUS + 1:
		return -9
	var l := _wedge_level(g, t)
	if l == BACKDROP:
		return -2
	if l < 0:
		return -1
	if placed.has(t):
		if bridges.has(g):
			return -1
		if ramps.has(g):
			return l + 1
	return l


## Per cell: the slot and level of each wedge, and for each wedge the boundary segments (toward lower
## ground) its surface rounds off toward. Roads, ramps, water and the backdrop keep hard edges.
func _cell_ctx(g: Vector2i) -> Dictionary:
	if _ctx.has(g):
		return _ctx[g]
	var p0 := Hex.to_world(g)
	var ts: Array = []
	var lw: Array = []
	var nb: Array = []
	for j in 6:
		var wt := Hex.wedge_tile(g, j)
		ts.append(wt)
		lw.append(_eff_level(g, wt))
		var n: Vector2i = g + E[j]
		nb.append(_eff_level(n, Hex.wedge_tile(n, (j + 3) % 6)))
	var segs: Array = []
	var elig: Array = []
	for j in 6:
		var wt: Vector2i = ts[j]
		var l: int = lw[j]
		var ok: bool = l >= 0 and not (placed.has(wt) and (ramps.has(g) or bridges.has(g) or path_cells.has(g)))
		var list: Array = []
		if ok:
			for k in 6:
				if int(nb[k]) < l:
					list.append([p0 + Hex.CORNER[k], p0 + Hex.CORNER[(k + 1) % 6]])
				if int(lw[k]) < l:
					list.append([p0, p0 + Hex.CORNER[k]])
					list.append([p0, p0 + Hex.CORNER[(k + 1) % 6]])
		elig.append(ok and not list.is_empty())
		segs.append(list)
	var c := {"t": ts, "l": lw, "segs": segs, "elig": elig}
	_ctx[g] = c
	return c


## Rounding at p: Vector3(drop below the flat top, height gradient x, gradient z).
func _bevel_at(p: Vector3, segs: Array) -> Vector3:
	var best := BEVEL_R
	var q_best := Vector2.ZERO
	var pp := Vector2(p.x, p.z)
	for sg in segs:
		var a := Vector2(sg[0].x, sg[0].z)
		var ab := Vector2(sg[1].x, sg[1].z) - a
		var f := clampf((pp - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		var q := a + ab * f
		var d := pp.distance_to(q)
		if d < best:
			best = d
			q_best = q
	if best >= BEVEL_R:
		return Vector3.ZERO
	var k := 1.0 - best / BEVEL_R
	var root := sqrt(maxf(0.0, 1.0 - k * k))
	var slope := minf(k / maxf(root, 0.02), 7.0)
	var dir := (pp - q_best).normalized() if best > 0.0001 else Vector2.ZERO
	return Vector3(BEVEL_R * (1.0 - root), slope * dir.x, slope * dir.y)


## Ground height of wedge j of cell g at p, including the rounded lips.
func _surf2(g: Vector2i, j: int, p: Vector3) -> float:
	var c := _cell_ctx(g)
	if c["elig"][j]:
		return int(c["l"][j]) * LEVEL_H - _bevel_at(p, c["segs"][j]).x
	return _surf(g, c["t"][j], p)


func _near_segs(p: Vector3, segs: Array) -> bool:
	var pp := Vector2(p.x, p.z)
	for sg in segs:
		var a := Vector2(sg[0].x, sg[0].z)
		var ab := Vector2(sg[1].x, sg[1].z) - a
		var f := clampf((pp - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		if pp.distance_to(a + ab * f) < BEVEL_R + 0.95:
			return true
	return false


func _tri_v(a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3, col: Color, u2: Vector2) -> void:
	if (b - a).cross(c - a).y > 0.0:
		_mv.append(a)
		_mv.append(c)
		_mv.append(b)
		_mn.append(na)
		_mn.append(nc)
		_mn.append(nb)
	else:
		_mv.append(a)
		_mv.append(b)
		_mv.append(c)
		_mn.append(na)
		_mn.append(nb)
		_mn.append(nc)
	for k in 3:
		_mc.append(col)
		_mu.append(Vector2.ZERO)
		_mu2.append(u2)


## Wall with a soft dark foot, so cliffs read as solid and grounded.
func _wall_v(a: Vector3, b: Vector3, a2: float, b2: float, out: Vector3) -> void:
	var a_lo := Vector3(a.x, a2, a.z)
	var b_lo := Vector3(b.x, b2, b.z)
	var hi := Color(1, 1, 1)
	var sa := lerpf(1.0, 0.62, clampf((a.y - a2) / 1.6, 0.0, 1.0))
	var sb := lerpf(1.0, 0.62, clampf((b.y - b2) / 1.6, 0.0, 1.0))
	var lo_a := Color(sa, sa, sa)
	var lo_b := Color(sb, sb, sb)
	for tri in [[a, b, b_lo, hi, hi, lo_b], [a, b_lo, a_lo, hi, lo_b, lo_a]]:
		var p1: Vector3 = tri[0]
		var p2: Vector3 = tri[1]
		var p3: Vector3 = tri[2]
		var c1: Color = tri[3]
		var c2: Color = tri[4]
		var c3: Color = tri[5]
		if (p2 - p1).cross(p3 - p1).dot(out) > 0.0:
			_mv.append(p1)
			_mv.append(p3)
			_mv.append(p2)
			_mc.append(c1)
			_mc.append(c3)
			_mc.append(c2)
		else:
			_mv.append(p1)
			_mv.append(p2)
			_mv.append(p3)
			_mc.append(c1)
			_mc.append(c2)
			_mc.append(c3)
		for k in 3:
			_mn.append(out)
			_mu.append(Vector2.ZERO)
			_mu2.append(Vector2.ZERO)


## Walls along one edge of a wedge, sampled so they follow rounded lips on either side.
func _edge_walls(g: Vector2i, i: int, og: Vector2i, oj: int, pa: Vector3, pb: Vector3, n: int, out: Vector3) -> void:
	var prev_p := pa
	var prev_s := _surf2(g, i, pa)
	var prev_o := _surf2(og, oj, pa)
	for k in range(1, n + 1):
		var p := pa.lerp(pb, float(k) / n)
		var sv := _surf2(g, i, p)
		var ov := _surf2(og, oj, p)
		if prev_s > prev_o + 0.01 or sv > ov + 0.01:
			_wall_v(Vector3(prev_p.x, prev_s, prev_p.z), Vector3(p.x, sv, p.z), minf(prev_o, prev_s), minf(ov, sv), out)
		prev_p = p
		prev_s = sv
		prev_o = ov


func _emit_round_wedge(p0: Vector3, a: Vector3, b: Vector3, n: int, segs: Array, top: float, col: Color, u2: Vector2) -> void:
	var w := n + 1
	_pos_buf.resize(w * w)
	_nrm_buf.resize(w * w)
	for u in w:
		for v in w - u:
			var p := p0 + (a - p0) * (float(u) / n) + (b - p0) * (float(v) / n)
			var bv := _bevel_at(p, segs)
			p.y = top - bv.x
			_pos_buf[u * w + v] = p
			_nrm_buf[u * w + v] = Vector3(-bv.y, 1.0, -bv.z).normalized()
	for u in n:
		for v in n - u:
			var i1 := u * w + v
			var i2 := (u + 1) * w + v
			var i3 := u * w + v + 1
			_tri_v(_pos_buf[i1], _pos_buf[i2], _pos_buf[i3], _nrm_buf[i1], _nrm_buf[i2], _nrm_buf[i3], col, u2)
			if u + v < n - 1:
				var i4 := (u + 1) * w + v + 1
				_tri_v(_pos_buf[i2], _pos_buf[i4], _pos_buf[i3], _nrm_buf[i2], _nrm_buf[i4], _nrm_buf[i3], col, u2)


func _rebuild_mesh(t: Vector2i) -> void:
	if _meshes.has(t):
		(_meshes[t] as Node).queue_free()
		_meshes.erase(t)
	_ctx.clear()
	_mv = PackedVector3Array()
	_mn = PackedVector3Array()
	_mc = PackedColorArray()
	_mu = PackedVector2Array()
	_mu2 = PackedVector2Array()
	var is_tile := placed.has(t)
	var base := t * Hex.K
	for e in _info:
		var off: Vector2i = e["off"]
		var mask: int = e["mask"]
		var g := base + off
		var p0 := Hex.to_world(g)
		var c := _cell_ctx(g)
		var lvl := _wedge_level(g, t)
		var water := lvl == -1 or (is_tile and bridges.has(g))
		var shore := 0.0
		if is_tile and not water and lvl == 0:
			for d in E:
				if _is_water(g + d):
					shore = 0.85
					break
		var stone := 1.0 if (is_tile and t == Vector2i.ZERO and Hex.dist(g, center) == 2 and not path_cells.has(g)) else 0.0
		# vertex alpha 0 marks the backdrop: the shader paints it a flat, muted meadow
		var top_col: Color = level_tint(lvl) if is_tile else Color(1, 1, 1, 0)
		if is_tile:
			top_col.a = 1.0
		var u2 := Vector2(1.0 if water else shore, stone)
		var p0f := Vector3(p0.x, 0, p0.z)
		for i in 6:
			if mask & (1 << i) == 0:
				continue
			var a: Vector3 = p0 + Hex.CORNER[i]
			var b: Vector3 = p0 + Hex.CORNER[(i + 1) % 6]
			var ng: Vector2i = g + E[i]
			var nj := (i + 3) % 6
			var rounded: bool = c["elig"][i] and _near_segs(p0 + Hex.WEDGE_OFF[i], c["segs"][i])
			if rounded:
				_emit_round_wedge(p0f, a, b, BEVEL_N, c["segs"][i], int(c["l"][i]) * LEVEL_H, top_col, u2)
			else:
				var yc := _surf(g, t, p0)
				var fa := Vector3(a.x, _surf(g, t, a), a.z)
				var fb := Vector3(b.x, _surf(g, t, b), b.z)
				var cc := Vector3(p0.x, yc, p0.z)
				var nrm := (fb - cc).cross(fa - cc).normalized()
				if nrm.y < 0.0:
					nrm = -nrm
				_tri(cc, fa, fb, nrm, top_col, 0.0, u2.x, u2.y)
			# walls toward the neighbor across the outer edge, sampled finely if either side is rounded
			var ns := BEVEL_N if (rounded or _cell_ctx(ng)["elig"][nj]) else 1
			_edge_walls(g, i, ng, nj, a, b, ns, Hex.dir_world(i))
			# radial edges shared with this cell's other wedges when they belong to another slot
			for side in [[(i + 1) % 6, b], [(i + 5) % 6, a]]:
				var j: int = side[0]
				if mask & (1 << j) != 0:
					continue
				var corner: Vector3 = side[1]
				var out := (Vector3(corner.x, 0, corner.z) - p0f).cross(Vector3.UP).normalized()
				if out.dot(Hex.WEDGE_OFF[i]) > 0.0:
					out = -out
				_edge_walls(g, i, g, j, p0f, Vector3(corner.x, 0, corner.z), BEVEL_N, out)
	if _mv.is_empty():
		return
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = _mv
	arr[Mesh.ARRAY_NORMAL] = _mn
	arr[Mesh.ARRAY_COLOR] = _mc
	arr[Mesh.ARRAY_TEX_UV] = _mu
	arr[Mesh.ARRAY_TEX_UV2] = _mu2
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.mesh = am
	mi.material_override = terrain_mat()
	add_child(mi)
	_meshes[t] = mi
	if _ground == null:
		_ground = mi


## Rebuild every slot whose drawing touches these cells.
func _refresh_cells(cells: Array) -> void:
	var slots := {}
	for c in cells:
		for n in Hex.disc(c, 1):
			for i in 6:
				var t := Hex.wedge_tile(n, i)
				if Hex.length(t) <= MAP_RADIUS + 1:
					slots[t] = true
	for t in slots:
		_rebuild_mesh(t)


## Lake water: one hexagonal sheet under the whole drawn map (land sits above it).
## Water sheets over the ponds on your tiles (and under bridges).
var _water_mi: MeshInstance3D


func _rebuild_water() -> void:
	if _water_mi and is_instance_valid(_water_mi):
		_water_mi.queue_free()
	_water_mi = null
	var verts := PackedVector3Array()
	for c in height:
		if int(height[c]) != -1 and not bridges.has(c):
			continue
		var p := Hex.to_world(c) + Vector3(0, WATER_Y, 0)
		for i in 6:
			var a: Vector3 = p + Hex.CORNER[i] * 1.04
			var b2: Vector3 = p + Hex.CORNER[(i + 1) % 6] * 1.04
			verts.append(p)
			verts.append(a)
			verts.append(b2)
	if verts.is_empty():
		return
	var norms := PackedVector3Array()
	norms.resize(verts.size())
	norms.fill(Vector3.UP)
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	_water_mi = MeshInstance3D.new()
	_water_mi.mesh = am
	var wm := ShaderMaterial.new()
	wm.shader = load("res://shaders/water.gdshader")
	_water_mi.material_override = wm
	_water_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_water_mi)


func _build_skirt() -> void:
	var pm := PlaneMesh.new()
	var ext := (MAP_RADIUS + 1) * Hex.K * Hex.SQ3 * Hex.R * 4.0
	pm.size = Vector2(ext, ext)
	var mi := MeshInstance3D.new()
	mi.mesh = pm
	var sm := terrain_mat()
	if sm is ShaderMaterial:
		sm = sm.duplicate()
		(sm as ShaderMaterial).set_shader_parameter("all_backdrop", true)
		_skirt_mat = sm
	mi.material_override = sm
	# level with the backdrop, so the meadow runs on to the horizon
	mi.position = Vector3(0, BACKDROP_Y - 0.01, 0)
	add_child(mi)


# ------------------------------------------------------------------ props (trees, rocks, crystals)

const PROP_SIZE := {
	"prop_oak": [3.0, 2.6], "prop_pine": [3.6, 2.2], "prop_birch": [3.1, 2.4], "prop_rock": [1.1, 1.8],
	"prop_ruin": [1.9, 1.5], "prop_crystal": [1.5, 1.4], "prop_bush": [0.9, 1.2],
}
## Newer props (optional: the map works without them).
const PROP_EXTRA := {
	"prop_log": [1.1, 2.3], "prop_outcrop": [2.3, 2.2], "prop_signpost": [2.1, 1.2], "prop_wall": [1.2, 2.0],
}
## Ground scatter, batched per tile slot and hidden when the camera is far away.
const SCATTER_SIZE := {
	"prop_grass": [0.8, 0.9], "prop_flowers": [0.45, 0.95], "prop_mushrooms": [0.6, 0.8], "prop_reeds": [1.4, 1.0],
}
const PROP_SPARE := 160
var _prop_sets := {}
var _cell_props := {}
var _props_ready := false


func _has_props() -> bool:
	for p in PROP_SIZE:
		if not ResourceLoader.exists(Models.CUSTOM + p + ".glb"):
			return false
	return true


var _prop_long_x := {}   # prop -> its long axis is X (else Z)
var _prop_h := {}        # prop -> fitted height


func _prop_exists(prop: String) -> bool:
	return ResourceLoader.exists(Models.CUSTOM + prop + ".glb")


func _prop_base(prop: String) -> Transform3D:
	var path := Models.CUSTOM + prop + ".glb"
	var mesh := Models.asset_mesh(path)
	if mesh == null:
		return Transform3D()
	var inner := Models.asset_mesh_xform(path)
	var bb := inner * mesh.get_aabb()
	var sz: Array = PROP_SIZE.get(prop, PROP_EXTRA.get(prop, SCATTER_SIZE.get(prop, [1.0, 1.0])))
	_prop_long_x[prop] = bb.size.x >= bb.size.z
	var s: float = minf(float(sz[0]) / maxf(bb.size.y, 0.001), float(sz[1]) / maxf(maxf(bb.size.x, bb.size.z), 0.001))
	var c := bb.get_center()
	_prop_h[prop] = bb.size.y * s
	return Transform3D(Basis().scaled(Vector3(s, s, s)), Vector3(-c.x * s, -bb.position.y * s, -c.z * s)) * inner


## Yaw that lays a prop's long axis along a world direction.
func _yaw_along(prop: String, d: Vector3) -> float:
	if _prop_long_x.get(prop, true):
		return atan2(-d.z, d.x)
	return atan2(d.x, d.z)


var _prop_bases := {}


func _prop_xform(prop: String, item: Dictionary) -> Transform3D:
	if not _prop_bases.has(prop):
		_prop_bases[prop] = _prop_base(prop)
	var base: Transform3D = _prop_bases[prop]
	var sc: float = item["scale"]
	return Transform3D(Basis(Vector3.UP, item["rot"]).scaled(Vector3(sc, sc, sc)), item["pos"]) * base


func _zero_xform() -> Transform3D:
	return Transform3D(Basis().scaled(Vector3(0.0001, 0.0001, 0.0001)), Vector3(0, -50, 0))


func _build_props() -> void:
	_props_ready = Models.has_assets() and _has_props()
	if not _props_ready:
		return
	var plan: Array = []
	var trees: Array = biome["trees"]
	for g in wild_t:
		if placed.has(tile_of(g)) or Hex.dist(g, center) <= 4:
			continue
		var p0 := Hex.to_world(g) + Vector3(0, surface_y_wild(g), 0)
		match int(wild_t[g]):
			T.TREE:
				var n := 1 if rng.randf() < 0.6 else 2
				for i in n:
					var off := Vector3(rng.randf_range(-0.45, 0.45), 0, rng.randf_range(-0.45, 0.45)) if n == 2 else Vector3.ZERO
					plan.append([trees[rng.randi() % trees.size()], g, {"pos": p0 + off, "rot": rng.randf() * TAU, "scale": rng.randf_range(0.8, 1.1) * (0.85 if n == 2 else 1.0)}])
			T.ROCK:
				var rock := "prop_ruin" if rng.randf() < 0.2 else "prop_rock"
				if _prop_exists("prop_outcrop") and rng.randf() < (0.6 if biome_id == "highlands" else 0.25):
					rock = "prop_outcrop"
				plan.append([rock, g, {"pos": p0, "rot": rng.randf() * TAU, "scale": rng.randf_range(0.85, 1.1)}])

	# a forest ring beyond the map edge
	var rim := (MAP_RADIUS + 1.6) * Hex.K * Hex.SQ3 * Hex.R
	for i in 220:
		var a := rng.randf() * TAU
		var d := rim + rng.randf_range(2.0, 16.0)
		var prop: String = trees[rng.randi() % trees.size()] if rng.randf() < 0.9 else "prop_rock"
		plan.append([prop, NONE, {"pos": Vector3(cos(a) * d, BACKDROP_Y, sin(a) * d), "rot": rng.randf() * TAU, "scale": rng.randf_range(1.1, 1.6)}])
	var counts := {}
	for e in plan:
		counts[e[0]] = int(counts.get(e[0], 0)) + 1
	var sets: Array = PROP_SIZE.keys()
	for prop in PROP_EXTRA:
		if _prop_exists(prop):
			sets.append(prop)
	# Two batches per prop: one for your tiles (casts shadows) and one for the wild land beyond them (the far tree
	# line), which never does: those trees are the bulk of the scene's triangles and would double the shadow work.
	for prop in sets:
		for wild in [false, true]:
			var n := int(counts.get(prop, 0)) if wild else PROP_SPARE
			if n == 0:
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = Models.asset_mesh(Models.CUSTOM + prop + ".glb")
			mm.instance_count = n
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			if wild:
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mmi)
			for i in mm.instance_count:
				mm.set_instance_transform(i, _zero_xform())
			var key: String = prop + ("|w" if wild else "")
			_prop_sets[key] = {"mm": mmi, "prop": prop, "items": [], "next": 0, "free": []}
			_prop_sets[key]["items"].resize(mm.instance_count)
	for prop in sets:
		_prop_bases[prop] = _prop_base(prop)   # also measures height and long axis (bridges, walls)
	for e in plan:
		_alloc_prop(e[0], e[1], e[2], true)


func surface_y_wild(g: Vector2i) -> float:
	var l: int = wild_h.get(g, 0)
	if l == BACKDROP:
		return BACKDROP_Y
	return l * LEVEL_H if l >= 0 else BASE_Y + 0.15


func _alloc_prop(prop: String, c: Vector2i, item: Dictionary, wild := false) -> int:
	var key: String = prop + ("|w" if wild else "")
	if not _props_ready or not _prop_sets.has(key):
		return -1
	var set_: Dictionary = _prop_sets[key]
	var mm := (set_["mm"] as MultiMeshInstance3D).multimesh
	var i: int
	if not set_["free"].is_empty():
		i = set_["free"].pop_back()
	else:
		i = set_["next"]
		if i >= mm.instance_count:
			return -1
		set_["next"] = i + 1
	set_["items"][i] = item
	mm.set_instance_transform(i, _prop_xform(prop, item))
	if c != NONE:
		if not _cell_props.has(c):
			_cell_props[c] = []
		_cell_props[c].append([key, i])
	return i


## Remove one prop instance (if it's still there).
func _free_prop(c: Vector2i, prop: String, i: int) -> void:
	if not _cell_props.has(c):
		return
	var list: Array = _cell_props[c]
	for k in list.size():
		if list[k][0] == prop and int(list[k][1]) == i:
			list.remove_at(k)
			var set_: Dictionary = _prop_sets[prop]
			(set_["mm"] as MultiMeshInstance3D).multimesh.set_instance_transform(i, _zero_xform())
			set_["free"].append(i)
			return


func _hide_props(c: Vector2i) -> void:
	_hide_scatter(c)
	if not _cell_props.has(c):
		return
	for pr in _cell_props[c]:
		var set_: Dictionary = _prop_sets[pr[0]]
		(set_["mm"] as MultiMeshInstance3D).multimesh.set_instance_transform(pr[1], _zero_xform())
		set_["free"].append(pr[1])
	_cell_props.erase(c)


func _move_props(c: Vector2i) -> void:
	if not _cell_props.has(c):
		return
	for pr in _cell_props[c]:
		var set_: Dictionary = _prop_sets[pr[0]]
		var item: Dictionary = set_["items"][pr[1]]
		item["pos"] = Vector3(item["pos"].x, surface_y(c), item["pos"].z)
		(set_["mm"] as MultiMeshInstance3D).multimesh.set_instance_transform(pr[1], _prop_xform(set_["prop"], item))


## Remove small decorations from a cell (when a tower is built there). Ley crystals stay.
func clear_flora(c: Vector2i) -> void:
	if terrain.get(c, -1) == T.GRASS:
		_hide_props(c)
	else:
		_hide_scatter(c)


# ------------------------------------------------------------------ the castle tile

func _stamp_hq(sides: Array) -> void:
	var t := Vector2i.ZERO
	placed[t] = {"entrances": [], "level": 0, "hq": true}
	for e in _info:
		var g: Vector2i = e["off"]
		height[g] = 0
		terrain[g] = T.GRASS
		if e["mask"] == 63:
			whole[g] = true
	for c in Hex.disc(center, 1):
		terrain[c] = T.CASTLE
	for s in sides:
		open_hq_exit(s, 0)
	reveal_tile(t)


## Opens a road from the castle out through one side of its tile (a new battlefront).
func open_hq_exit(side: int, wave := 0) -> Vector2i:
	var t := Vector2i.ZERO
	if side in placed[t]["entrances"] or placed.has(t + E[side]) or not in_map(t + E[side]):
		return NONE
	var half: Vector2i = E[side] * 3
	var inner: Vector2i = E[side] * 2
	path_cells[half] = true
	path_cells[inner] = true
	_link(half, inner)
	_link(inner, center)
	placed[t]["entrances"].append(side)
	_open_port(half, t, side, wave)
	_net_dirty = true
	_refresh_cells([half, inner])
	_hide_props(inner)
	_hide_props(half)
	if _prop_sets.size() > 0:
		_update_frontier(t)
	if _road_mi != null:
		_rebuild_roads()
	return half


func free_hq_sides() -> Array:
	var out: Array = []
	for s in 6:
		if s not in placed[Vector2i.ZERO]["entrances"] and not placed.has(E[s]) and in_map(E[s]):
			out.append(s)
	return out


func _link(a: Vector2i, b: Vector2i) -> void:
	if not links.has(a):
		links[a] = []
	if not links.has(b):
		links[b] = []
	if b not in links[a]:
		links[a].append(b)
	if a not in links[b]:
		links[b].append(a)


func _open_port(pc: Vector2i, t: Vector2i, side: int, wave: int) -> void:
	open_ports[pc] = {"tile": t, "side": side}
	port_opened[pc] = wave
	var p := Models.portal()
	add_child(p)
	p.position = cell_to_world(pc) + Vector3(0, road_y(pc), 0) + Hex.dir_world(side) * 0.3
	p.rotation.y = Hex.dir_yaw(side)
	p.scale = Vector3.ONE * 0.8
	portals[pc] = p


func _close_port(pc: Vector2i) -> void:
	open_ports.erase(pc)
	port_opened.erase(pc)
	if portals.has(pc):
		(portals[pc] as Node3D).queue_free()
		portals.erase(pc)


# ------------------------------------------------------------------ terrain tiles

## Rolls a tile card in its default orientation: entrances (sides), roads (cell sequences from each
## entrance's half cell inward) and features. Entrance counts skew toward 2 (see GameData.ENTRANCE_ODDS).
func make_tile(r: RandomNumberGenerator, n_ent := 0) -> Dictionary:
	if n_ent <= 0:
		var total := 0
		for k in GameData.ENTRANCE_ODDS:
			total += int(GameData.ENTRANCE_ODDS[k])
		var roll := r.randi() % total
		for k in GameData.ENTRANCE_ODDS:
			roll -= int(GameData.ENTRANCE_ODDS[k])
			if roll < 0:
				n_ent = int(k)
				break
	var sides: Array = [0, 1, 2, 3, 4, 5]
	for i in range(5, 0, -1):
		var j := r.randi_range(0, i)
		var tmp = sides[i]
		sides[i] = sides[j]
		sides[j] = tmp
	sides = sides.slice(0, n_ent)
	sides.sort()
	var paths := _gen_paths(sides, r)
	var roads := {}
	for p in paths:
		for c in p:
			roads[c] = true
	# a tile can sit a level above or below the road it joins
	var rise := 0
	var up: float = 0.3 if biome_id == "highlands" else 0.22
	var rr := r.randf()
	if rr < up:
		rise = 1
	elif rr < up + 0.18:
		rise = -1
	return {"entrances": sides, "paths": paths, "features": _gen_features(roads, r), "rise": rise}


func _gen_paths(sides: Array, r: RandomNumberGenerator) -> Array:
	var paths: Array = []
	if sides.size() == 2:
		var a: Vector2i = E[sides[0]] * 2
		var b: Vector2i = E[sides[1]] * 2
		var best: Array = []
		var want := Hex.dist(a, b) + r.randi_range(0, 4)
		for attempt in 30:
			var p := _walk(a, b, want, r)
			if p.size() > best.size() and p.size() <= want + 1:
				best = p
			if best.size() == want + 1:
				break
		if best.is_empty():
			best = _walk(a, b, 12, r)
		var full: Array = [E[sides[0]] * 3]
		full.append_array(best)
		full.append(E[sides[1]] * 3)
		paths.append(full)
		return paths
	var hub: Vector2i = Vector2i.ZERO if r.randf() < 0.5 else E[r.randi() % 6]
	var taken := {}
	for s in sides:
		var p: Array = [E[s] * 3, E[s] * 2]
		var cur: Vector2i = E[s] * 2
		var guard := 0
		while cur != hub and not taken.has(cur) and guard < 10:
			guard += 1
			var opts: Array = []
			for d in E:
				var n: Vector2i = cur + d
				if Hex.dist(n, hub) < Hex.dist(cur, hub) and Hex.length(n) <= 2:
					opts.append(n)
			if opts.is_empty():
				break
			cur = opts[r.randi() % opts.size()]
			p.append(cur)
		for c in p:
			taken[c] = true
		paths.append(p)
	return paths


## Random self-avoiding walk from a to b inside the tile (cells within 2 of the middle), at most max_len steps.
func _walk(a: Vector2i, b: Vector2i, max_len: int, r: RandomNumberGenerator) -> Array:
	var path: Array = [a]
	var seen := {a: true}
	var ok := _walk_rec(path, seen, b, max_len, r, [0])
	return path if ok else []


func _walk_rec(path: Array, seen: Dictionary, goal: Vector2i, max_len: int, r: RandomNumberGenerator, budget: Array) -> bool:
	budget[0] += 1
	if budget[0] > 400:
		return false
	var cur: Vector2i = path[path.size() - 1]
	if cur == goal:
		return true
	if path.size() - 1 + Hex.dist(cur, goal) > max_len:
		return false
	var opts: Array = []
	for d in E:
		var n: Vector2i = cur + d
		if Hex.length(n) > 2 or seen.has(n):
			continue
		# don't touch the path except where we came from (no shortcuts between road cells)
		var touch := false
		for d2 in E:
			var m: Vector2i = n + d2
			if m != cur and seen.has(m):
				touch = true
				break
		if touch and n != goal:
			continue
		opts.append(n)
	for i in range(opts.size() - 1, 0, -1):
		var j := r.randi_range(0, i)
		var tmp = opts[i]
		opts[i] = opts[j]
		opts[j] = tmp
	for n in opts:
		path.append(n)
		seen[n] = true
		if _walk_rec(path, seen, goal, max_len, r, budget):
			return true
		path.pop_back()
		seen.erase(n)
	return false


func _gen_features(roads: Dictionary, r: RandomNumberGenerator) -> Array:
	var free: Array = []
	for e in _info:
		var off: Vector2i = e["off"]
		if e["mask"] == 63 and not roads.has(off) and Hex.length(off) <= 3:
			free.append(off)
	for i in range(free.size() - 1, 0, -1):
		var j := r.randi_range(0, i)
		var tmp = free[i]
		free[i] = free[j]
		free[j] = tmp
	var feats: Array = []
	var taken := {}
	# a pond: a few water hexes away from the tile edge; sometimes the road crosses it on a bridge
	var pond_p: float = (0.5 if biome_id == "lakelands" else 0.22) + pond_bonus
	if force_bridge or r.randf() < pond_p:
		var bridge := force_bridge or r.randf() < 0.3
		force_bridge = false
		var seeds: Array = []
		for c in (roads.keys() if bridge else free):
			var cc: Vector2i = c
			if Hex.length(cc) <= 2 and not Hex.BAND.has(cc):
				seeds.append(cc)
		if not seeds.is_empty():
			var start: Vector2i = seeds[r.randi() % seeds.size()]
			var pond: Array = [start]
			var want := r.randi_range(3, 6)
			var guard := 0
			while pond.size() < want and guard < 40:
				guard += 1
				var from: Vector2i = pond[r.randi() % pond.size()]
				var n: Vector2i = from + E[r.randi() % 6]
				if n in pond or Hex.length(n) > 3 or Hex.BAND.has(n):
					continue
				if roads.has(n) and not bridge:
					continue
				pond.append(n)
			for c in pond:
				taken[c] = true
				feats.append({"cell": c, "type": "pond"})
	var interior := func(c: Vector2i) -> bool: return Hex.length(c) <= 2 and not roads.has(c) and not taken.has(c)
	if r.randf() < 0.55:
		for c in free:
			if interior.call(c):
				taken[c] = true
				feats.append({"cell": c, "type": "plateau"})
				for d in E:
					var n: Vector2i = c + d
					if interior.call(n) and r.randf() < 0.45:
						taken[n] = true
						feats.append({"cell": n, "type": "plateau"})
				break
	var put := func(ty: String, kind := "", inner := false) -> void:
		for c in free:
			if not taken.has(c) and (not inner or Hex.length(c) <= 2):
				taken[c] = true
				feats.append({"cell": c, "type": ty, "kind": kind})
				return
	for i in r.randi_range(1, 4):
		put.call("tree" if r.randf() < 0.7 else "rock")
	if r.randf() < 0.35:
		put.call("ley", "", true)
	if r.randf() < 0.35:
		var kinds: Array = GameData.NEUTRALS.keys()
		put.call("neutral", kinds[r.randi() % kinds.size()], true)
	return feats


## A card turned by k steps of 60 degrees.
func rotate_tile(card: Dictionary, k: int) -> Dictionary:
	var ents: Array = []
	for s in card["entrances"]:
		ents.append((s + k) % 6)
	var paths: Array = []
	for p in card["paths"]:
		var rp: Array = []
		for c in p:
			rp.append(Hex.rot(c, k))
		paths.append(rp)
	var feats: Array = []
	for f in card["features"]:
		var nf: Dictionary = f.duplicate()
		nf["cell"] = Hex.rot(f["cell"], k)
		feats.append(nf)
	return {"entrances": ents, "paths": paths, "features": feats, "rise": card.get("rise", 0)}


## Slots a new tile can go in: next to every open entrance.
func expansion_slots() -> Array:
	var out: Array = []
	for pc in open_ports:
		var t: Vector2i = open_ports[pc]["tile"] + E[open_ports[pc]["side"]]
		if in_map(t) and not placed.has(t) and t not in out:
			out.append(t)
	return out


## How a card (turned k steps) would sit in slot t, or {} if it can't go there. Sides that touch placed
## tiles must match exactly: entrance to entrance, wall to wall.
func plan_tile(t: Vector2i, card: Dictionary, k: int) -> Dictionary:
	if placed.has(t) or not in_map(t):
		return {}
	var ents: Array = []
	for s0 in card["entrances"]:
		ents.append((s0 + k) % 6)
	var merges: Array = []
	var lo := -99
	var hi := 99
	for side in 6:
		var nt: Vector2i = t + E[side]
		var has := side in ents
		if placed.has(nt):
			if has != (((side + 3) % 6) in placed[nt]["entrances"]):
				return {}
			if has:
				var half: Vector2i = t * Hex.K + E[side] * 3
				merges.append(half)
				var hh := level_at(half)
				lo = maxi(lo, hh - 1)
				hi = mini(hi, hh + 1)
		elif has and not in_map(nt):
			return {}
	if merges.is_empty():
		return {}
	if open_ports.size() - merges.size() + (ents.size() - merges.size()) < 1:
		return {}
	# the card's own height, relative to the road it joins, within one step of every road it touches
	var level := clampi(level_at(merges[0]) + int(card.get("rise", 0)), 0, 2)
	level = clampi(level, maxi(lo, 0), mini(hi, MAX_LEVEL - 1))
	if level < lo or level > hi:
		return {}
	var base := t * Hex.K
	var rc := rotate_tile(card, k)
	var roads: Array = []
	for p in rc["paths"]:
		var gp: Array = []
		for c in p:
			gp.append(base + c)
		roads.append(gp)
	var feats: Array = []
	for f in rc["features"]:
		var nf: Dictionary = f.duplicate()
		nf["cell"] = base + f["cell"]
		feats.append(nf)
	return {"tile": t, "rot": k, "entrances": ents, "roads": roads, "features": feats, "level": level,
		"merges": merges, "new_ports": ents.size() - merges.size()}


## Stamps a planned tile onto the map. Returns the entrance cells that became new spawn points.
func commit_tile(plan: Dictionary, wave := 0) -> Array:
	var t: Vector2i = plan["tile"]
	var level: int = plan["level"]
	var base := t * Hex.K
	var feats := {}
	for f in plan["features"]:
		feats[f["cell"]] = f
	var road := {}
	for p in plan["roads"]:
		for c in p:
			road[c] = true
	placed[t] = {"entrances": plan["entrances"], "level": level}
	var fresh: Array = []
	for e in _info:
		var off: Vector2i = e["off"]
		var g := base + off
		_claim_poi_at(g)
		_hide_props(g)
		if height.has(g):
			continue   # a shared cell already set by a neighboring tile: it merges as-is
		if feats.has(g) and feats[g]["type"] == "pond":
			# pond water can't be built on; a road crossing it gets a bridge
			if road.has(g):
				bridges[g] = true
			else:
				height[g] = -1
				terrain[g] = T.WATER
				fresh.append(g)
				continue
		var h := level
		if Hex.BAND.has(off):
			for side in Hex.BAND[off]:
				if placed.has(t + E[side]):
					var m: Vector2i = g + E[side]
					if height.has(m) and not road.has(g):
						h = height[m]
						break
		height[g] = h
		terrain[g] = T.GRASS
		fresh.append(g)
	# features on the tile's own fresh cells
	for g in fresh:
		if not feats.has(g) or road.has(g) or terrain.get(g, -1) == T.WATER:
			continue
		var f: Dictionary = feats[g]
		match String(f["type"]):
			"plateau":
				height[g] = mini(level + 1, MAX_LEVEL)
			"tree":
				terrain[g] = T.TREE
			"rock":
				terrain[g] = T.ROCK
			"ley":
				terrain[g] = T.LEY
			"neutral":
				terrain[g] = T.BUILDING
				_spawn_neutral(g, f["kind"])
	# roads, links and ramps
	for p in plan["roads"]:
		for i in p.size():
			path_cells[p[i]] = true
			if i > 0:
				_link(p[i - 1], p[i])
	for p in plan["roads"]:
		for i in range(1, p.size()):
			var a: Vector2i = p[i - 1]
			var b: Vector2i = p[i]
			var la := level_at(a)
			var lb := level_at(b)
			if absi(la - lb) == 1:
				var low := a if la < lb else b
				var high := b if la < lb else a
				ramps[low] = Hex.dir_index(high - low)
	# whole cells (merged halves and corners become buildable ground)
	for e in _info:
		var g: Vector2i = base + e["off"]
		var ok := true
		for i in 6:
			if not placed.has(Hex.wedge_tile(g, i)):
				ok = false
				break
		if ok:
			whole[g] = true
	# entrances: merged ones close, the rest open as new spawn points
	var opened: Array = []
	for side in plan["entrances"]:
		var half: Vector2i = base + E[side] * 3
		if placed.has(t + E[side]):
			_close_port(half)
		else:
			_open_port(half, t, side, wave)
			opened.append(half)
	_net_dirty = true
	_spawn_tile_scenery(fresh)
	_rebuild_mesh(t)
	_build_scatter(t)
	for d in E:
		if Hex.length(t + d) <= MAP_RADIUS + 1:
			_rebuild_mesh(t + d)
	_update_frontier(t)
	for d in E:
		if placed.has(t + d):
			_update_frontier(t + d)
	_place_signposts(plan["roads"])
	_rebuild_roads()
	_rebuild_water()
	reveal_tile(t)
	if Models.has_assets() and rng.randf() < DISCOVERY_CHANCE:
		_spawn_discovery(fresh, plan["roads"])
	return opened


func _spawn_tile_scenery(cells: Array) -> void:
	if not _props_ready:
		return
	var trees: Array = biome["trees"]
	for g in cells:
		var p0 := cell_to_world(g) + Vector3(0, surface_y(g), 0)
		match int(terrain.get(g, T.GRASS)):
			T.TREE:
				var tp: String = trees[rng.randi() % trees.size()]
				if rng.randf() < 0.18 and _prop_sets.has("prop_log"):
					tp = "prop_log"
				_alloc_prop(tp, g, {"pos": p0, "rot": rng.randf() * TAU, "scale": rng.randf_range(0.8, 1.05)})
			T.ROCK:
				var rk := "prop_outcrop" if (_prop_sets.has("prop_outcrop") and rng.randf() < (0.6 if biome_id == "highlands" else 0.3)) else "prop_rock"
				_alloc_prop(rk, g, {"pos": p0, "rot": rng.randf() * TAU, "scale": rng.randf_range(0.85, 1.1)})
			T.LEY:
				_alloc_prop("prop_crystal", g, {"pos": p0, "rot": rng.randf() * TAU, "scale": 0.5})


func _spawn_neutral(c: Vector2i, kind: String) -> void:
	var holder := Node3D.new()
	add_child(holder)
	holder.position = cell_to_world(c) + Vector3(0, surface_y(c), 0)
	var model: String = GameData.NEUTRALS[kind]["model"]
	if Models.fit(holder, model, 1.8, 2.2) == null:
		holder.add_child(Models.box(Vector3(1.2, 1.0, 1.2), Color(0.6, 0.45, 0.3), Vector3(0, 0.5, 0)))
	neutrals[c] = {"kind": kind, "node": holder}


## Kinds of neutral buildings touching any of these cells.
func neutrals_near(cells: Array) -> Array:
	var out: Array = []
	for c in cells:
		for n in Hex.disc(c, 1):
			if neutrals.has(n) and neutrals[n]["kind"] not in out:
				out.append(neutrals[n]["kind"])
	return out


func scout_cells() -> Array:
	var out: Array = []
	for c in neutrals:
		if neutrals[c]["kind"] == "scout":
			out.append(c)
	return out


# ------------------------------------------------------------------ raise ground

func can_raise(c: Vector2i) -> bool:
	if not whole.has(c) or path_cells.has(c) or level_at(c) >= MAX_LEVEL:
		return false
	var t: int = terrain.get(c, -1)
	return t == T.GRASS or t == T.LEY


func raise_cells(cells: Array) -> void:
	for c in cells:
		height[c] = level_at(c) + 1
		clear_flora(c)
		_move_props(c)
		_update_scaffold(c)
	_refresh_cells(cells)
	_rebuild_roads()


## Diggers: take a raised hex (or everything under a tower) down one level, never below ground level.
func can_lower(c: Vector2i) -> bool:
	if not whole.has(c) or path_cells.has(c) or level_at(c) <= 0:
		return false
	var t: int = terrain.get(c, -1)
	return t == T.GRASS or t == T.LEY


func lower_cells(cells: Array) -> void:
	for c in cells:
		height[c] = level_at(c) - 1
		_move_props(c)
		_update_scaffold(c)
	_refresh_cells(cells)
	_rebuild_roads()


## Builders raise ground on timber scaffolding: posts and cross beams around the raised column.
var _scaffold := {}


func _update_scaffold(c: Vector2i) -> void:
	if _scaffold.has(c):
		(_scaffold[c] as Node).queue_free()
		_scaffold.erase(c)
	var t := tile_of(c)
	if not placed.has(t):
		return
	var base_l: int = int(placed[t]["level"])
	var lvl := level_at(c)
	if lvl <= base_l:
		return
	var n := Node3D.new()
	add_child(n)
	var p0 := Hex.to_world(c)
	var y0 := base_l * LEVEL_H
	var y1 := lvl * LEVEL_H
	var h := y1 - y0
	var post := _wood(Color(0.47, 0.32, 0.19))
	var beam_m := _wood(Color(0.6, 0.43, 0.26))
	var corners: Array = []
	for i in 6:
		corners.append(p0 + Hex.CORNER[i] * 1.03)
	for i in 6:
		var cp: Vector3 = corners[i]
		var pm := Models.box(Vector3(0.12, h + 0.12, 0.12), Color.WHITE, Vector3(cp.x, y0 + h * 0.5, cp.z))
		pm.material_override = post
		n.add_child(pm)
		var cq: Vector3 = corners[(i + 1) % 6]
		for k in range(1, lvl - base_l + 1):
			for yy in [y0 + LEVEL_H * k - 0.12, y0 + LEVEL_H * (k - 0.5)]:
				var a := Vector3(cp.x, yy, cp.z)
				var b := Vector3(cq.x, yy, cq.z)
				var bm := Models.box(Vector3(0.08, 0.08, a.distance_to(b)), Color.WHITE, Vector3.ZERO)
				bm.material_override = beam_m
				n.add_child(bm)
				bm.look_at_from_position((a + b) * 0.5, b, Vector3.UP)
			# one diagonal brace per face per level
			var d1 := Vector3(cp.x, y0 + LEVEL_H * (k - 1) + 0.05, cp.z)
			var d2 := Vector3(cq.x, y0 + LEVEL_H * k - 0.15, cq.z)
			var br := Models.box(Vector3(0.07, 0.07, d1.distance_to(d2)), Color.WHITE, Vector3.ZERO)
			br.material_override = beam_m
			n.add_child(br)
			br.look_at_from_position((d1 + d2) * 0.5, d2, Vector3.UP)
	_scaffold[c] = n


## Is any of these cells next to open water (Blue's Tidebound)?
func near_water(cells: Array) -> bool:
	for c in cells:
		for d in E:
			if _is_water(c + d):
				return true
	return false


## Which cell the mouse ray hits, accounting for raised ground.
func pick_cell(origin: Vector3, dir: Vector3) -> Vector2i:
	if absf(dir.y) < 0.0001:
		return NONE
	for lvl in range(MAX_LEVEL, -1, -1):
		var t := (lvl * LEVEL_H - origin.y) / dir.y
		if t < 0.0:
			continue
		var c := world_to_cell(origin + dir * t)
		if in_bounds(c) and level_at(c) >= lvl:
			return c
	var tb := (BACKDROP_Y - origin.y) / dir.y
	if tb > 0.0:
		var cb := world_to_cell(origin + dir * tb)
		if in_bounds(cb):
			return cb
	return NONE


# ------------------------------------------------------------------ fog of war (world space)

const FOG_CELL := 1.5
const FOG_EXT := 120.0          # covers the forest ring too, so the spotlight darkens it
const SPOT_FALLOFF := 22.0       # world units from your tiles to full darkness
const SPOT_DARK := 0.6          # how dark the far backdrop gets
const SPOT_COL := Color(0.05, 0.06, 0.09)
var fog_enabled := true
var spotlight := false           # when fog of war is off, the decal can pool light on your tiles instead (off: plain grass)
var _skirt_mat: ShaderMaterial
var revealed := PackedByteArray()
var _fog: Decal
var _fog_noise := PackedByteArray()
var _fog_dirty := false
var _fog_n := 0


func _init_fog() -> void:
	_fog_n = int(FOG_EXT * 2.0 / FOG_CELL)
	revealed.resize(_fog_n * _fog_n)
	revealed.fill(0)
	_fog = Decal.new()
	_fog.size = Vector3(FOG_EXT * 2.0, 40.0, FOG_EXT * 2.0)
	_fog.position = Vector3(0, 8.0, 0)
	_fog.modulate = Color(0.13, 0.15, 0.22)
	_fog.albedo_mix = 1.0
	_fog.upper_fade = 0.0
	_fog.lower_fade = 0.0
	_fog.visible = fog_enabled or spotlight
	add_child(_fog)
	var fn := FastNoiseLite.new()
	fn.seed = seed_value + 5
	fn.frequency = 0.05
	fn.fractal_octaves = 3
	_fog_noise = fn.get_image(_fog_n * 2, _fog_n * 2).get_data()
	_fog_dirty = true


func set_fog(on: bool) -> void:
	fog_enabled = on
	if _fog:
		_fog.visible = on or spotlight
		_fog_dirty = true


func _fog_idx(p: Vector3) -> int:
	var x := int((p.x + FOG_EXT) / FOG_CELL)
	var y := int((p.z + FOG_EXT) / FOG_CELL)
	if x < 0 or y < 0 or x >= _fog_n or y >= _fog_n:
		return -1
	return y * _fog_n + x


func is_revealed_at(p: Vector3) -> bool:
	if not fog_enabled:
		return true
	var i := _fog_idx(p)
	return i >= 0 and revealed[i] == 1


func is_revealed(c: Vector2i) -> bool:
	return is_revealed_at(cell_to_world(c))


func reveal_circle(p: Vector3, r: float) -> void:
	var cr := int(ceil(r / FOG_CELL)) + 1
	var cx := int((p.x + FOG_EXT) / FOG_CELL)
	var cy := int((p.z + FOG_EXT) / FOG_CELL)
	for y in range(cy - cr, cy + cr + 1):
		for x in range(cx - cr, cx + cr + 1):
			if x < 0 or y < 0 or x >= _fog_n or y >= _fog_n:
				continue
			var i := y * _fog_n + x
			if revealed[i] == 1:
				continue
			var wx := x * FOG_CELL - FOG_EXT + FOG_CELL * 0.5
			var wz := y * FOG_CELL - FOG_EXT + FOG_CELL * 0.5
			if Vector2(wx - p.x, wz - p.z).length() <= r:
				revealed[i] = 1
				_fog_dirty = true


func reveal_tile(t: Vector2i) -> void:
	reveal_circle(Hex.tile_world(t), Hex.K * Hex.R + 2.0)


func _rebuild_fog() -> void:
	_fog_dirty = false
	var spot := spotlight and not fog_enabled
	var small := PackedByteArray()
	small.resize(_fog_n * _fog_n)
	if spot:
		small = _spot_mask()
	else:
		for i in small.size():
			small[i] = 0 if revealed[i] == 1 else 255
	var img := Image.create_from_data(_fog_n, _fog_n, false, Image.FORMAT_L8, small)
	var w := _fog_n * 2
	img.resize(w, w, Image.INTERPOLATE_CUBIC)
	var a := img.get_data()
	var out := PackedByteArray()
	out.resize(a.size() * 2)
	for i in a.size():
		out[i * 2] = 255
		if spot:
			out[i * 2 + 1] = int(a[i] * SPOT_DARK * (0.9 + float(_fog_noise[i]) / 255.0 * 0.1))
		else:
			out[i * 2 + 1] = int(a[i] * (0.74 + float(_fog_noise[i]) / 255.0 * 0.26))
	var tex := ImageTexture.create_from_image(Image.create_from_data(w, w, false, Image.FORMAT_LA8, out))
	_fog.texture_albedo = tex
	_fog.modulate = SPOT_COL if spot else Color(0.13, 0.15, 0.22)
	# the terrain shader draws the dark stripes (and keeps the dark going past the decal's edge)
	for m in [terrain_mat(), _skirt_mat]:
		if m is ShaderMaterial:
			m.set_shader_parameter("spot_on", spot)
			m.set_shader_parameter("spot_mask", tex)
			m.set_shader_parameter("spot_ext", FOG_EXT)
			m.set_shader_parameter("spot_dark", SPOT_DARK)
			m.set_shader_parameter("spot_col", Vector3(SPOT_COL.r, SPOT_COL.g, SPOT_COL.b))
	refresh_poi_visibility()


## Darkness per fog cell (0 lit .. 255 dark) by distance from anything your tiles cover:
## a two-pass chamfer distance transform, then a smooth falloff.
func _spot_mask() -> PackedByteArray:
	var n := _fog_n
	var d := PackedFloat32Array()
	d.resize(n * n)
	for i in n * n:
		d[i] = 0.0 if revealed[i] == 1 else 1.0e6
	for y in n:
		for x in n:
			var i := y * n + x
			var v := d[i]
			if x > 0:
				v = minf(v, d[i - 1] + 1.0)
			if y > 0:
				v = minf(v, d[i - n] + 1.0)
				if x > 0:
					v = minf(v, d[i - n - 1] + 1.414)
				if x < n - 1:
					v = minf(v, d[i - n + 1] + 1.414)
			d[i] = v
	for y in range(n - 1, -1, -1):
		for x in range(n - 1, -1, -1):
			var i := y * n + x
			var v := d[i]
			if x < n - 1:
				v = minf(v, d[i + 1] + 1.0)
			if y < n - 1:
				v = minf(v, d[i + n] + 1.0)
				if x < n - 1:
					v = minf(v, d[i + n + 1] + 1.414)
				if x > 0:
					v = minf(v, d[i + n - 1] + 1.414)
			d[i] = v
	var out := PackedByteArray()
	out.resize(n * n)
	for i in n * n:
		var t := clampf(d[i] * FOG_CELL / SPOT_FALLOFF, 0.0, 1.0)
		out[i] = int(255.0 * t * t * (3.0 - 2.0 * t))
	return out


# ------------------------------------------------------------------ discoveries

## Now and then a newly placed tile turns up something: claim it by reaching it with a tower's range.
const DISCOVERY_CHANCE := 0.3


func _spawn_discovery(cells: Array, roads: Array) -> void:
	var road := {}
	for p0 in roads:
		for c in p0:
			road[c] = true
	var spots: Array = []
	for c in cells:
		if whole.has(c) and terrain.get(c, -1) == T.GRASS and not road.has(c) and not towers.has(c):
			spots.append(c)
	if spots.is_empty():
		return
	var c: Vector2i = spots[rng.randi() % spots.size()]
	var kinds: Array = GameData.DISCOVERIES.keys()
	var kind: String = kinds[rng.randi() % kinds.size()]
	_hide_props(c)
	terrain[c] = T.POI
	var holder := Node3D.new()
	add_child(holder)
	holder.position = cell_to_world(c) + Vector3(0, surface_y(c), 0)
	Models.fit(holder, GameData.DISCOVERIES[kind]["model"], 1.6, 1.8)
	var beam := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.15
	cm.bottom_radius = 0.3
	cm.height = 6.0
	beam.mesh = cm
	beam.material_override = Models.mat(Color(1.0, 0.85, 0.35), 0.0, 0.22)
	beam.position = Vector3(0, 3.0, 0)
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	holder.add_child(beam)
	pois[c] = {"kind": kind, "node": holder}


func _place_discoveries() -> void:
	var kinds: Array = GameData.DISCOVERIES.keys()
	var tries := 0
	while pois.size() < 14 and tries < 600:
		tries += 1
		var t: Vector2i = _slots[rng.randi() % _slots.size()]
		if Hex.length(t) < 1 or placed.has(t):
			continue
		var c: Vector2i = Hex.tile_center(t) + Hex.rot(Vector2i(rng.randi_range(-2, 2), 0), rng.randi() % 6)
		if pois.has(c) or not wild_t.has(c) or int(wild_t[c]) == T.WATER:
			continue
		var kind: String = kinds[pois.size() % kinds.size()] if pois.size() < kinds.size() else kinds[rng.randi() % kinds.size()]
		_hide_props(c)
		wild_t[c] = T.POI
		var holder := Node3D.new()
		add_child(holder)
		holder.position = cell_to_world(c) + Vector3(0, surface_y_wild(c), 0)
		Models.fit(holder, GameData.DISCOVERIES[kind]["model"], 1.6, 1.8)
		var beam := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.15
		cm.bottom_radius = 0.3
		cm.height = 6.0
		beam.mesh = cm
		beam.material_override = Models.mat(Color(1.0, 0.85, 0.35), 0.0, 0.22)
		beam.position = Vector3(0, 3.0, 0)
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(beam)
		holder.visible = false
		pois[c] = {"kind": kind, "node": holder}


func refresh_poi_visibility() -> void:
	for c in pois:
		(pois[c]["node"] as Node3D).visible = is_revealed(c)


func _claim_poi_at(c: Vector2i) -> void:
	if not pois.has(c):
		return
	claimed_queue.append({"kind": pois[c]["kind"], "cell": c})
	(pois[c]["node"] as Node3D).queue_free()
	pois.erase(c)
	if terrain.get(c, -1) == T.POI:
		terrain[c] = T.GRASS


## Claims every explored discovery within r world units of p (a tower's reach).
func claim_in_range(p: Vector3, r: float) -> void:
	for c in pois.keys():
		if is_revealed(c) and cell_to_world(c).distance_to(Vector3(p.x, 0, p.z)) <= r:
			_claim_poi_at(c)


# ------------------------------------------------------------------ routing

func _rebuild_network() -> void:
	_net_dirty = false
	_dist = {center: 0}
	var q: Array = [center]
	var qi := 0
	while qi < q.size():
		var c: Vector2i = q[qi]
		qi += 1
		for n in links.get(c, []):
			if not _dist.has(n):
				_dist[n] = int(_dist[c]) + 1
				q.append(n)


## World-space waypoints from an entrance to the castle along the shortest road.
func route_from(port: Vector2i) -> PackedVector3Array:
	if _net_dirty:
		_rebuild_network()
	var pts := PackedVector3Array()
	var c := port
	var guard := 0
	while _dist.has(c) and c != center and guard < 2000:
		guard += 1
		pts.append(cell_to_world(c) + Vector3(0, road_y(c), 0))
		var best := c
		var bd: int = _dist[c]
		for n in links.get(c, []):
			if _dist.has(n) and int(_dist[n]) < bd:
				best = n
				bd = _dist[n]
		if best == c:
			break
		c = best
	pts.append(cell_to_world(center) + Vector3(0, 0.02, 0))
	return pts


func road_length_from(port: Vector2i) -> int:
	if _net_dirty:
		_rebuild_network()
	return int(_dist.get(port, 0))


# ------------------------------------------------------------------ placement previews

func _hex_plate(radius: float, col: Color, pos: Vector3, alpha: float, h := 0.08) -> MeshInstance3D:
	var cm := CylinderMesh.new()
	cm.top_radius = radius
	cm.bottom_radius = radius
	cm.height = h
	cm.radial_segments = 6
	cm.rings = 1
	var mi := MeshInstance3D.new()
	mi.mesh = cm
	mi.material_override = Models.mat(col, 0.6, alpha)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = pos
	return mi


func show_slots(slots: Array, col := Color(0.55, 1.0, 0.6)) -> void:
	clear_slots()
	for t in slots:
		var y := 0.0
		for e in _info:
			y = maxf(y, surface_y_wild(t * Hex.K + e["off"]))
		var m := _hex_plate(Hex.K * Hex.R - 0.3, col, Hex.tile_world(t) + Vector3(0, y + 0.25, 0), 0.16)
		add_child(m)
		_slot_marks.append(m)


func clear_slots() -> void:
	for n in _slot_marks:
		if is_instance_valid(n):
			n.queue_free()
	_slot_marks.clear()


func show_tile_preview(plan: Dictionary, valid := true) -> void:
	clear_preview()
	if plan.is_empty():
		return
	var lvl_y: float = int(plan["level"]) * LEVEL_H
	var t: Vector2i = plan["tile"]
	var outline := _hex_plate(Hex.K * Hex.R, Color(1.0, 0.9, 0.4) if valid else Color(1, 0.3, 0.3), Hex.tile_world(t) + Vector3(0, lvl_y + 0.35, 0), 0.12, 0.05)
	add_child(outline)
	_preview_nodes.append(outline)
	for p in plan["roads"]:
		for c in p:
			var m := _hex_plate(Hex.R * 0.85, Color(1.0, 0.85, 0.4), cell_to_world(c) + Vector3(0, lvl_y + 0.45, 0), 0.75, 0.12)
			add_child(m)
			_preview_nodes.append(m)
	for f in plan["features"]:
		var fc: Vector2i = f["cell"]
		var fcol: Color = {"plateau": Color(0.8, 0.65, 0.4), "tree": Color(0.3, 0.8, 0.35), "rock": Color(0.6, 0.6, 0.65),
			"ley": Color(0.4, 0.9, 1.0), "neutral": Color(1.0, 0.6, 0.2)}.get(f["type"], Color.WHITE)
		var hgt := 0.7 if f["type"] == "plateau" else 0.4
		var m2 := _hex_plate(Hex.R * 0.7, fcol, cell_to_world(fc) + Vector3(0, lvl_y + hgt * 0.5 + 0.3, 0), 0.6, hgt)
		add_child(m2)
		_preview_nodes.append(m2)
	for side in plan["entrances"]:
		var half: Vector2i = t * Hex.K + E[side] * 3
		var merge: bool = half in plan["merges"]
		var arrow := Models.cone(0.5, 1.0, Color(0.3, 1, 0.5) if merge else Color(0.85, 0.4, 1.0), cell_to_world(half) + Vector3(0, lvl_y + 2.0, 0), 1.5)
		arrow.rotation_degrees = Vector3(180, 0, 0)
		add_child(arrow)
		_preview_nodes.append(arrow)


func clear_preview() -> void:
	for n in _preview_nodes:
		if is_instance_valid(n):
			n.queue_free()
	_preview_nodes.clear()


func _process(_delta: float) -> void:
	if _fog_dirty and _fog:
		_rebuild_fog()
	var tm := Time.get_ticks_msec() / 1000.0
	for pc in portals:
		var p: Node3D = portals[pc]
		if is_instance_valid(p):
			var core := p.get_node_or_null("Core") as Node3D
			if core:
				var s := 0.85 + 0.12 * sin(tm * 3.0)
				core.scale = Vector3(s, 1.0, s)
			var shards := p.get_node_or_null("Shards") as Node3D
			if shards:
				shards.rotation.y = tm * 1.6
				shards.position.y = 1.4 + sin(tm * 2.0) * 0.15



# ------------------------------------------------------------------ map polish: scatter, roads, walls, signs, bridges

var _scatter_mm := {}     # tile slot -> Array of MultiMeshInstance3D
var _scatter_cell := {}   # cell -> Array of [MultiMesh, index]
var _scatter_base := {}   # prop -> fitted base transform
var _road_mi: MeshInstance3D
var _frontier := {}       # "slot|side" -> [cell, prop index]
var _signed := {}         # junction road cell -> true


func _is_water(c: Vector2i) -> bool:
	return height.has(c) and (int(height[c]) == -1 or bridges.has(c))


## Grass tufts, flowers, mushrooms and shore reeds for one tile slot, in one small batch per prop.
func _build_scatter(t: Vector2i) -> void:
	if _scatter_mm.has(t):
		for mi in _scatter_mm[t]:
			(mi as Node).queue_free()
		_scatter_mm.erase(t)
	if not _props_ready:
		return
	var is_tile := placed.has(t)
	var r := RandomNumberGenerator.new()
	r.seed = hash(t) * 31 + seed_value + (7 if is_tile else 0)
	var lists := {}
	var mush := 0.09 if biome_id == "deepwood" else 0.04
	for e in _info:
		if e["mask"] != 63:
			continue
		var g: Vector2i = t * Hex.K + e["off"]
		_scatter_cell.erase(g)
		var ty: int = terrain.get(g, -1) if is_tile else int(wild_t.get(g, T.GRASS))
		if ty != T.GRASS or path_cells.has(g) or towers.has(g) or Hex.dist(g, center) <= 2:
			continue
		var lvl := level_at(g) if is_tile else int(wild_h.get(g, 0))
		if lvl < 0:
			continue
		var p0 := Hex.to_world(g) + Vector3(0, lvl * LEVEL_H, 0)
		var put := func(prop: String, off: Vector3, sc: float) -> void:
			if not lists.has(prop):
				lists[prop] = []
			lists[prop].append([g, Transform3D(Basis(Vector3.UP, r.randf() * TAU).scaled(Vector3.ONE * sc), p0 + off)])
		var rnd := func() -> Vector3:
			var a := r.randf() * TAU
			var d := sqrt(r.randf()) * Hex.R * 0.72
			return Vector3(cos(a) * d, 0, sin(a) * d)
		# sparse on purpose: a few tufts read as grass, a carpet of them reads as noise
		var n := (1 if r.randf() < 0.28 else 0) if is_tile else (1 if r.randf() < 0.03 else 0)
		for i in n:
			put.call("prop_grass", rnd.call(), r.randf_range(0.7, 1.1))
		if r.randf() < (0.04 if is_tile else 0.0):
			put.call("prop_flowers", rnd.call(), r.randf_range(0.8, 1.15))
		if r.randf() < (mush * 0.35 if is_tile else 0.0):
			put.call("prop_mushrooms", rnd.call(), r.randf_range(0.8, 1.1))
		if lvl == 0:
			for d in E:
				if _is_water(g + d) and r.randf() < 0.5:
					put.call("prop_reeds", Hex.to_world(g + d) * 0.0 + (Hex.to_world(g + d) - Hex.to_world(g)) * 0.4, r.randf_range(0.8, 1.2))
					break
	var made: Array = []
	for prop in lists:
		if not _prop_exists(prop):
			continue
		if not _scatter_base.has(prop):
			_scatter_base[prop] = _prop_base(prop)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = Models.asset_mesh(Models.CUSTOM + prop + ".glb")
		mm.instance_count = lists[prop].size()
		var base: Transform3D = _scatter_base[prop]
		for i in lists[prop].size():
			var it: Array = lists[prop][i]
			mm.set_instance_transform(i, it[1] * base)
			var cell: Vector2i = it[0]
			if not _scatter_cell.has(cell):
				_scatter_cell[cell] = []
			_scatter_cell[cell].append([mm, i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if prop != "prop_reeds" else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		mmi.visibility_range_end = 75.0
		mmi.visibility_range_end_margin = 12.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		add_child(mmi)
		made.append(mmi)
	_scatter_mm[t] = made


func _hide_scatter(c: Vector2i) -> void:
	if not _scatter_cell.has(c):
		return
	for it in _scatter_cell[c]:
		var mm: MultiMesh = it[0]
		if is_instance_valid(mm):
			mm.set_instance_transform(it[1], _zero_xform())
	_scatter_cell.erase(c)


## Height of the road surface of cell c at point p (ramps slope along the road).
func _road_surface(c: Vector2i, p: Vector3) -> float:
	if c == center:
		return 0.0
	var y := level_at(c) * LEVEL_H
	if ramps.has(c):
		var rel := p - Hex.to_world(c)
		y += LEVEL_H * clampf(0.5 + rel.dot(Hex.dir_world(ramps[c])) / (Hex.SQ3 * Hex.R), 0.0, 1.0)
	return y


static var _road_mats := {}


func _road_mat(file: String, tint: Color) -> Material:
	var key := file + tint.to_html()
	if _road_mats.has(key):
		return _road_mats[key]
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/road.gdshader")
	var path := "res://assets/custom/textures/" + file + ".png"
	if ResourceLoader.exists(path):
		m.set_shader_parameter("tex", load(path))
	m.set_shader_parameter("base", Vector3(tint.r, tint.g, tint.b))
	_road_mats[key] = m
	return m


## Roads drawn as smooth ribbons along the road network (a dirt verge under a cobbled lane), joining
## at every road hex with a rounded patch, instead of stair-stepped dirt hexes.
func _rebuild_roads() -> void:
	if _road_mi and is_instance_valid(_road_mi):
		_road_mi.queue_free()
	# a darker packed-earth verge under a lighter lane: one clean shape, like Tower Dominion's paths
	var layers := [["tex_dirt", Color(0.4, 0.31, 0.23), 1.95, 0.035], ["tex_road", Color(0.52, 0.42, 0.33), 1.3, 0.06]]
	var am := ArrayMesh.new()
	for layer in layers:
		var w: float = layer[2] * 0.5
		var lift: float = layer[3]
		var verts: Array = []   # a plain Array: lambdas share it (packed arrays would be copied)
		var done := {}
		var seg := func(a: Vector3, b: Vector3) -> void:
			var d := Vector3(b.x - a.x, 0, b.z - a.z)
			if d.length() < 0.01:
				return
			var sd := Vector3(-d.z, 0, d.x).normalized() * w
			var a1 := a + sd + Vector3(0, lift, 0)
			var a2 := a - sd + Vector3(0, lift, 0)
			var b1 := b + sd + Vector3(0, lift, 0)
			var b2 := b - sd + Vector3(0, lift, 0)
			verts.append_array([a1, b1, b2, a1, b2, a2])
		for a in links:
			for b in links[a]:
				var key := str(a) + str(b) if str(a) < str(b) else str(b) + str(a)
				if done.has(key):
					continue
				done[key] = true
				var pa := Hex.to_world(a)
				var pb := Hex.to_world(b)
				var m := (pa + pb) * 0.5
				var edge_y := maxf(_road_surface(a, m), _road_surface(b, m)) if a != center and b != center else 0.0
				pa.y = _road_surface(a, pa)
				pb.y = _road_surface(b, pb)
				m.y = edge_y
				if not bridges.has(a):
					seg.call(pa, m)
				if not bridges.has(b):
					seg.call(m, pb)
		for c in path_cells:
			if bridges.has(c) or not whole.has(c):
				continue   # no round cap hanging over a tile's open edge
			var pc := Hex.to_world(c)
			pc.y = _road_surface(c, pc) + lift
			for i in 12:
				var a0 := TAU * i / 12.0
				var a1 := TAU * (i + 1) / 12.0
				verts.append_array([pc, pc + Vector3(cos(a1), 0, sin(a1)) * w, pc + Vector3(cos(a0), 0, sin(a0)) * w])
		if verts.is_empty():
			continue
		# wind every triangle clockwise seen from above (Godot's front face), like the terrain
		for i in range(0, verts.size(), 3):
			var va: Vector3 = verts[i]
			var vb: Vector3 = verts[i + 1]
			var vc: Vector3 = verts[i + 2]
			if (vb - va).cross(vc - va).dot(Vector3.UP) > 0.0:
				verts[i + 1] = vc
				verts[i + 2] = vb
		var norms := PackedVector3Array()
		norms.resize(verts.size())
		norms.fill(Vector3.UP)
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = PackedVector3Array(verts)
		arr[Mesh.ARRAY_NORMAL] = norms
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		var m2 := _road_mat(layer[0], layer[1])
		am.surface_set_material(am.get_surface_count() - 1, m2)
	_road_mi = MeshInstance3D.new()
	_road_mi.mesh = am
	_road_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_road_mi)
	_rebuild_bridges()


## Low crumbling walls along the open edges of your realm (sides of placed tiles that face the wild).
func _update_frontier(t: Vector2i) -> void:
	# off: tiles now stand as raised blocks over the backdrop, so their rims already mark the realm
	if not FRONTIER_WALLS or not placed.has(t) or not _prop_sets.has("prop_wall"):
		return
	for side in 6:
		var key := "%s|%d" % [t, side]
		var nt: Vector2i = t + E[side]
		var want: bool = in_map(nt) and not placed.has(nt) and side not in placed[t]["entrances"]
		if not want:
			if _frontier.has(key):
				_free_prop(_frontier[key][0], "prop_wall", _frontier[key][1])
				_frontier.erase(key)
			continue
		if _frontier.has(key):
			continue
		for e in _info:
			var off: Vector2i = e["off"]
			if e["mask"] != 63 or not Hex.BAND.has(off) or side not in Hex.BAND[off] or Hex.BAND[off].size() > 1:
				continue
			var g: Vector2i = t * Hex.K + off
			if terrain.get(g, -1) != T.GRASS or path_cells.has(g) or towers.has(g):
				continue
			var n := Hex.dir_world(side)
			var along := Vector3(-n.z, 0, n.x)
			var pos := Hex.to_world(g) + n * (Hex.SQ3 * Hex.R * 0.3) + Vector3(0, surface_y(g), 0)
			var idx := _alloc_prop("prop_wall", g, {"pos": pos, "rot": _yaw_along("prop_wall", along), "scale": 1.0})
			if idx >= 0:
				_frontier[key] = [g, idx]
			break


## A signpost with a lantern beside every road junction.
func _place_signposts(roads: Array) -> void:
	if not _prop_sets.has("prop_signpost"):
		return
	for p in roads:
		for c in p:
			if _signed.has(c) or links.get(c, []).size() < 3:
				continue
			for d in E:
				var g: Vector2i = c + d
				if whole.has(g) and terrain.get(g, -1) == T.GRASS and not path_cells.has(g) and not towers.has(g):
					var face := Hex.to_world(c) - Hex.to_world(g)
					var pos := Hex.to_world(g) + face * 0.35 + Vector3(0, surface_y(g), 0)
					_alloc_prop("prop_signpost", g, {"pos": pos, "rot": atan2(face.x, face.z), "scale": 1.0})
					_signed[c] = true
					break


## Test helper (--bridgetest): the next tile rolled gets a pond across its road.
var force_bridge := false
var pond_bonus := 0.0   # Blue's Tidebound: tiles bring more ponds


func seed_test_lake(_t: Vector2i) -> void:
	force_bridge = true


# ------------------------------------------------------------------ bridges

const DECK_W := 1.7
const RAIL_H := 0.55
var _bridge_root: Node3D
static var _wood_mats := {}


func _wood(col: Color) -> Material:
	var key := col.to_html()
	if not _wood_mats.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = col
		m.roughness = 0.9
		_wood_mats[key] = m
	return _wood_mats[key]


## Every road crossing over lake water becomes one continuous boardwalk: a single plank deck that follows
## the road's bends, railings on both sides, posts down into the water and stone footings on the shores.
func _rebuild_bridges() -> void:
	if _bridge_root and is_instance_valid(_bridge_root):
		_bridge_root.queue_free()
	_bridge_root = null
	if bridges.is_empty():
		return
	_bridge_root = Node3D.new()
	add_child(_bridge_root)
	# graph of bridge cells plus the land cells they touch
	var nodes := {}
	for c in bridges:
		nodes[c] = true
		for n in links.get(c, []):
			nodes[n] = true
	var deg := func(c: Vector2i) -> int:
		var k := 0
		for n in links.get(c, []):
			if nodes.has(n) and (bridges.has(c) or bridges.has(n)):
				k += 1
		return k
	var used := {}
	for start in nodes:
		if bridges.has(start) and deg.call(start) == 2:
			continue   # chains start at ends (land) or junctions
		for n0 in links.get(start, []):
			if not nodes.has(n0) or not (bridges.has(start) or bridges.has(n0)):
				continue
			var key0 := "%s>%s" % [start, n0]
			if used.has(key0):
				continue
			var chain: Array = [start, n0]
			var prev: Vector2i = start
			var cur: Vector2i = n0
			used[key0] = true
			used["%s>%s" % [n0, start]] = true
			while bridges.has(cur) and deg.call(cur) == 2:
				var nxt := NONE
				for n in links.get(cur, []):
					if n != prev and nodes.has(n):
						nxt = n
				if nxt == NONE:
					break
				used["%s>%s" % [cur, nxt]] = true
				used["%s>%s" % [nxt, cur]] = true
				chain.append(nxt)
				prev = cur
				cur = nxt
			_build_span(chain)
	# landings where three or more roads meet over water
	for c in bridges:
		if deg.call(c) >= 3:
			_build_landing(c)


func _deck_y(c: Vector2i) -> float:
	return _road_surface(c, Hex.to_world(c)) + 0.03


## Points along a chain of cells, with land ends pulled back to the shoreline and bends rounded off.
func _span_points(chain: Array) -> Array:
	var pts: Array = []
	for i in chain.size():
		var c: Vector2i = chain[i]
		var p := Hex.to_world(c)
		p.y = _deck_y(c)
		if not bridges.has(c):
			# a land end: start a little before the waterline, at the land's road height
			var other: Vector2i = chain[1] if i == 0 else chain[i - 1]
			var edge := (Hex.to_world(c) + Hex.to_world(other)) * 0.5
			var inward := (Hex.to_world(c) - edge).normalized()
			p = edge + inward * 0.45
			p.y = _deck_y(c)
		pts.append(p)
	# round every bend with a short curve so the deck doesn't kink
	var out: Array = [pts[0]]
	for i in range(1, pts.size() - 1):
		var a: Vector3 = pts[i - 1]
		var b: Vector3 = pts[i]
		var c2: Vector3 = pts[i + 1]
		var d1 := Vector3(b.x - a.x, 0, b.z - a.z)
		var d2 := Vector3(c2.x - b.x, 0, c2.z - b.z)
		var ang := d1.normalized().angle_to(d2.normalized())
		if ang < 0.05:
			out.append(b)
			continue
		var t := minf(minf(0.9 * tan(ang * 0.5), d1.length() * 0.45), d2.length() * 0.45)
		var p1 := b - d1.normalized() * t
		var p2 := b + d2.normalized() * t
		p1.y = lerpf(b.y, a.y, t / maxf(d1.length(), 0.01))
		p2.y = lerpf(b.y, c2.y, t / maxf(d2.length(), 0.01))
		for k in 7:
			var f := k / 6.0
			out.append(p1.lerp(b, f).lerp(b.lerp(p2, f), f))
	out.append(pts[pts.size() - 1])
	return out


func _build_span(chain: Array) -> void:
	if chain.size() < 2:
		return
	var pts := _span_points(chain)
	var n := pts.size()
	# side vectors at every point (averaged at bends)
	var sides: Array = []
	for i in n:
		var a: Vector3 = pts[maxi(i - 1, 0)]
		var b: Vector3 = pts[mini(i + 1, n - 1)]
		var d := Vector3(b.x - a.x, 0, b.z - a.z).normalized()
		sides.append(Vector3(-d.z, 0, d.x))
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var add_tri := func(va: Vector3, vb: Vector3, vc: Vector3, nn: Vector3, ua: Vector2, ub: Vector2, uc: Vector2) -> void:
		if (vb - va).cross(vc - va).dot(nn) > 0.0:
			verts.append_array([va, vc, vb])
			uvs.append_array([ua, uc, ub])
		else:
			verts.append_array([va, vb, vc])
			uvs.append_array([ua, ub, uc])
		norms.append_array([nn, nn, nn])
	var hw := DECK_W * 0.5
	var thick := 0.16
	var s_len := 0.0
	var posts: Array = []
	var next_post := 0.0
	for i in n:
		if i > 0:
			s_len += Vector3(pts[i]).distance_to(pts[i - 1])
		if s_len >= next_post or i == n - 1:
			posts.append([pts[i], sides[i]])
			next_post = s_len + 1.35
		if i == n - 1:
			break
		var p0: Vector3 = pts[i]
		var p1: Vector3 = pts[i + 1]
		var sd0: Vector3 = sides[i]
		var sd1: Vector3 = sides[i + 1]
		var u0 := s_len
		var u1 := s_len + p0.distance_to(p1)
		var l0 := p0 + sd0 * hw
		var r0 := p0 - sd0 * hw
		var l1 := p1 + sd1 * hw
		var r1 := p1 - sd1 * hw
		add_tri.call(l0, r0, r1, Vector3.UP, Vector2(u0, 0), Vector2(u0, 1), Vector2(u1, 1))
		add_tri.call(l0, r1, l1, Vector3.UP, Vector2(u0, 0), Vector2(u1, 1), Vector2(u1, 0))
		# the deck's edge boards
		var down := Vector3(0, -thick, 0)
		add_tri.call(l0, l1, l1 + down, sd0, Vector2(u0, 0), Vector2(u1, 0), Vector2(u1, 0))
		add_tri.call(l0, l1 + down, l0 + down, sd0, Vector2(u0, 0), Vector2(u1, 0), Vector2(u0, 0))
		add_tri.call(r0, r1, r1 + down, -sd0, Vector2(u0, 1), Vector2(u1, 1), Vector2(u1, 1))
		add_tri.call(r0, r1 + down, r0 + down, -sd0, Vector2(u0, 1), Vector2(u1, 1), Vector2(u0, 1))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var deck := MeshInstance3D.new()
	deck.mesh = am
	var dm := ShaderMaterial.new()
	dm.shader = load("res://shaders/planks.gdshader")
	deck.material_override = dm
	_bridge_root.add_child(deck)
	# posts and railings on both sides
	var post_col := Color(0.36, 0.24, 0.14)
	var rail_col := Color(0.52, 0.36, 0.22)
	for side in [1.0, -1.0]:
		var prev_top := Vector3.INF
		for k in posts.size():
			var pp: Vector3 = posts[k][0]
			var sd: Vector3 = posts[k][1]
			var at: Vector3 = pp + sd * (hw - 0.06) * side
			var over_water := _is_water(Hex.from_world(at))
			var bottom := BASE_Y + 0.1 if over_water else pp.y - 0.12
			var top := pp.y + RAIL_H + 0.05
			var post := Models.cyl(0.07, 0.08, top - bottom, post_col, Vector3(at.x, (top + bottom) * 0.5, at.z), 0.0, 6)
			post.material_override = _wood(post_col)
			_bridge_root.add_child(post)
			var rail_top := Vector3(at.x, pp.y + RAIL_H, at.z)
			if prev_top != Vector3.INF:
				for h in [0.0, -0.24]:
					var a2: Vector3 = prev_top + Vector3(0, h, 0)
					var b2: Vector3 = rail_top + Vector3(0, h, 0)
					var len := a2.distance_to(b2)
					if len < 0.05:
						continue
					var rail := Models.box(Vector3(0.07, 0.06, len), rail_col, (a2 + b2) * 0.5)
					rail.material_override = _wood(rail_col)
					_bridge_root.add_child(rail)
					rail.look_at_from_position((a2 + b2) * 0.5, b2, Vector3.UP)
			prev_top = rail_top
	# stone footings where the deck meets land
	for end_i in [0, chain.size() - 1]:
		var c: Vector2i = chain[end_i]
		if bridges.has(c):
			continue
		var other: Vector2i = chain[1] if end_i == 0 else chain[chain.size() - 2]
		var edge := (Hex.to_world(c) + Hex.to_world(other)) * 0.5
		var dir := (Hex.to_world(other) - Hex.to_world(c)).normalized()
		var top_y := _deck_y(c) - 0.03
		var h2 := top_y - (BASE_Y + 0.1)
		var foot := Models.box(Vector3(DECK_W + 0.35, h2, 0.7), Color(0.6, 0.6, 0.62), Vector3.ZERO)
		foot.material_override = Models.stone_mat(Color(0.95, 0.95, 0.95))
		_bridge_root.add_child(foot)
		foot.look_at_from_position(Vector3(edge.x, BASE_Y + 0.1 + h2 * 0.5, edge.z), Vector3(edge.x, BASE_Y + 0.1 + h2 * 0.5, edge.z) + dir, Vector3.UP)


## A small round platform where roads meet over the water.
func _build_landing(c: Vector2i) -> void:
	var p := Hex.to_world(c)
	var y := _deck_y(c)
	var cm := CylinderMesh.new()
	cm.top_radius = DECK_W * 0.62
	cm.bottom_radius = DECK_W * 0.62
	cm.height = 0.16
	cm.radial_segments = 12
	var mi := MeshInstance3D.new()
	mi.mesh = cm
	mi.material_override = _wood(Color(0.58, 0.41, 0.25))
	mi.position = Vector3(p.x, y - 0.08, p.z)
	_bridge_root.add_child(mi)
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		var at := p + Vector3(cos(a), 0, sin(a)) * DECK_W * 0.5
		var post := Models.cyl(0.08, 0.09, y - BASE_Y, Color(0.36, 0.24, 0.14), Vector3(at.x, (y + BASE_Y) * 0.5, at.z), 0.0, 6)
		post.material_override = _wood(Color(0.36, 0.24, 0.14))
		_bridge_root.add_child(post)
