class_name Hex
extends RefCounted
## Hex math. Cells are flat-top hexagons in axial coordinates (q, s):
##   world x = 1.5 * R * q,   world z = sqrt(3) * R * (s + q / 2)
## Terrain tiles use the same orientation, scaled up: tile (Q, S) is centered on cell (K*Q, K*S).

const R := 1.2                       # cell circumradius (world units)
const SQ3 := 1.7320508075688772
const K := 4                         # cells between neighboring tile centers: 3 hexes along each tile edge
const HALF := K / 2                  # from a tile's middle to the half cell in the middle of each side (its entrance)
## Neighbor directions in edge order: edge i of a hexagon faces 60*i + 30 degrees (x right, z down).
const E := [Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 1), Vector2i(-1, 0), Vector2i(0, -1), Vector2i(1, -1)]

static var TEMPLATE: Array = []      # [cell offset, wedge mask] for the tile centered on the origin
static var BAND := {}                # cell offset -> Array of sides whose seam band the cell is in
static var WEDGE_OFF: Array = []     # wedge centroid offsets from a cell center
static var CORNER: Array = []        # the 6 corner offsets of a cell, corner i at 60*i degrees


## A flat hexagonal plate turned like the map's cells and tiles (corners on +-X), `h` tall and centred on y = 0.
## (Godot's six-sided CylinderMesh puts a corner on +Z instead: 30 degrees off.)
static func plate_mesh(radius: float, h: float) -> ArrayMesh:
	var cm := CylinderMesh.new()
	cm.top_radius = radius
	cm.bottom_radius = radius
	cm.height = h
	cm.radial_segments = 6
	cm.rings = 1
	var arr := cm.get_mesh_arrays()
	var b := Basis(Vector3.UP, deg_to_rad(30.0))
	var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var ns: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
	for i in vs.size():
		vs[i] = b * vs[i]
		ns[i] = b * ns[i]
	arr[Mesh.ARRAY_VERTEX] = vs
	arr[Mesh.ARRAY_NORMAL] = ns
	arr[Mesh.ARRAY_TANGENT] = null
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


static func setup() -> void:
	if not TEMPLATE.is_empty():
		return
	for i in 6:
		var a := deg_to_rad(60.0 * i)
		CORNER.append(Vector3(cos(a), 0, sin(a)) * R)
	for i in 6:
		WEDGE_OFF.append((CORNER[i] + CORNER[(i + 1) % 6]) / 3.0)
	var apothem := HALF * SQ3 * R
	for q in range(-K - 1, K + 2):
		for s in range(-K - 1, K + 2):
			var c := Vector2i(q, s)
			if length(c) > HALF + 1:
				continue
			var mask := 0
			for i in 6:
				if tile_of_point(to_world(c) + WEDGE_OFF[i]) == Vector2i.ZERO:
					mask |= 1 << i
			if mask == 0:
				continue
			TEMPLATE.append([c, mask])
			var sides: Array = []
			var p := to_world(c)
			for i in 6:
				if apothem - p.dot(dir_world(i)) <= SQ3 * R * 0.5 + 0.01:
					sides.append(i)
			if not sides.is_empty():
				BAND[c] = sides


static func to_world(c: Vector2i) -> Vector3:
	return Vector3(1.5 * R * c.x, 0.0, SQ3 * R * (c.y + c.x * 0.5))


static func _round(fq: float, fs: float) -> Vector2i:
	var x := fq
	var z := fs
	var y := -x - z
	var rx := roundf(x)
	var ry := roundf(y)
	var rz := roundf(z)
	var dx := absf(rx - x)
	var dy := absf(ry - y)
	var dz := absf(rz - z)
	if dx > dy and dx > dz:
		rx = -ry - rz
	elif dy <= dz:
		rz = -rx - ry
	return Vector2i(int(rx), int(rz))


static func from_world(p: Vector3) -> Vector2i:
	var fq := p.x / (1.5 * R)
	return _round(fq, p.z / (SQ3 * R) - fq * 0.5)


## Which tile slot contains a world point.
static func tile_of_point(p: Vector3) -> Vector2i:
	var fq := p.x / (1.5 * R)
	var fs := p.z / (SQ3 * R) - fq * 0.5
	return _round(fq / K, fs / K)


static func tile_center(t: Vector2i) -> Vector2i:
	return t * K


static func tile_world(t: Vector2i) -> Vector3:
	return to_world(t * K)


static func length(c: Vector2i) -> int:
	return maxi(maxi(absi(c.x), absi(c.y)), absi(c.x + c.y))


static func dist(a: Vector2i, b: Vector2i) -> int:
	return length(a - b)


## Unit world vector for side / direction i.
static func dir_world(i: int) -> Vector3:
	var a := deg_to_rad(60.0 * i + 30.0)
	return Vector3(cos(a), 0, sin(a))


## Yaw that turns a model's -Z forward toward direction i.
static func dir_yaw(i: int) -> float:
	var d := dir_world(i)
	return atan2(-d.x, -d.z)


## Rotate an axial offset by k steps of 60 degrees (E[i] -> E[i + k]).
static func rot(c: Vector2i, k: int) -> Vector2i:
	for i in posmod(k, 6):
		c = Vector2i(-c.y, c.x + c.y)
	return c


## Index of the side a direction vector points through (E[i] == d), or -1.
static func dir_index(d: Vector2i) -> int:
	return E.find(d)


## Tile slot that owns wedge i of cell c.
static func wedge_tile(c: Vector2i, i: int) -> Vector2i:
	return tile_of_point(to_world(c) + WEDGE_OFF[i])


static func neighbors(c: Vector2i) -> Array:
	var out: Array = []
	for d in E:
		out.append(c + d)
	return out


static func ring(c: Vector2i, r: int) -> Array:
	if r == 0:
		return [c]
	var out: Array = []
	var cur: Vector2i = c + E[4] * r
	for i in 6:
		for j in r:
			out.append(cur)
			cur += E[i]
	return out


static func disc(c: Vector2i, r: int) -> Array:
	var out: Array = []
	for k in r + 1:
		out.append_array(ring(c, k))
	return out
