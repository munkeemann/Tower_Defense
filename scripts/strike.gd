class_name Strike
extends Node3D
## A melee tower's blow, shown where it lands: a small Blender-made model of its own (assets/towers/<id>_strike.glb,
## built by the tower's script: roots bursting out of the ground, a tentacle, a spectral hammer, grasping hands) that
## plays its "strike" clip once under the enemy and is gone. The damage lands `hit` seconds in, when the model does.
## See GameData.STRIKES and Tower._slam / _grasp / _pulse.

var _land := Callable()
var _hit := 0.0
var _t := 0.0
var _len := 1.0
var _landed := false


## A strike of tower tw's at world point `at`; `land` is called when the blow lands (never, if the tower is gone by then).
static func spawn(tw: Tower, at: Vector3, hit: float, land: Callable) -> Strike:
	var s := Strike.new()
	tw.game.world.add_child(s)
	s._setup(tw, at, hit, land)
	return s


func _setup(tw: Tower, at: Vector3, hit: float, land: Callable) -> void:
	_land = land
	_hit = hit
	position = at
	# it faces the way the blow came: away from the tower
	var away := at - tw.global_position
	if Vector2(away.x, away.z).length() > 0.05:
		rotation.y = atan2(-away.x, -away.z)
	scale = Vector3.ONE * (1.0 + 0.1 * (tw.level - 1)) * float(tw._strike.get("scale", 1.0))
	var m := Models.strike_model(tw.id)
	if m.is_empty():
		_len = maxf(hit, 0.05)
		return
	add_child(m["root"])
	if tw.game.board:
		Models.set_ground(m["root"], tw.game.board.ground_material())
	var ap: AnimationPlayer = m["ap"]
	if ap and ap.has_animation("strike"):
		ap.play("strike")
		ap.seek(0.0, true)
		_len = ap.get_animation("strike").length
	visible = tw.game.board == null or tw.game.board.is_revealed_at(at)


## Stretches the model upward so its top (about 2 units up) reaches a flier `height` above the ground.
func reach_up(height: float) -> void:
	scale.y *= clampf(height / 2.0, 1.0, 3.5)


func _process(delta: float) -> void:
	_t += delta
	if not _landed and _t >= _hit:
		_landed = true
		if _land.is_valid():
			_land.call()
	if _t >= _len:
		queue_free()
