class_name Audio
extends Node
## Procedural sound effects plus a small generated music loop, so the game has sound with zero
## downloads. Drop a file named after a sound (e.g. res://assets/audio/boom.ogg or music.ogg)
## to replace any of them with a real recording. Each color can have its own battle track
## (music_<faction>.mp3, made by tools/music_batch.py); tracks loop with a crossfade.

const RATE := 22050
const MAX_VOICES := 18
const OVERRIDE_DIR := "res://assets/audio/"

## name -> [volume dB, min seconds between plays, pitch jitter]
const SOUNDS := {
	"arrow": [-17.0, 0.05, 0.12], "bolt": [-12.0, 0.06, 0.08], "orb": [-15.0, 0.07, 0.1],
	"lob": [-13.0, 0.08, 0.08], "boom": [-9.0, 0.07, 0.1], "chain": [-12.0, 0.08, 0.1],
	"slam": [-9.0, 0.08, 0.08], "pulse": [-19.0, 0.1, 0.06], "hit": [-24.0, 0.03, 0.2],
	"die": [-17.0, 0.04, 0.15], "gold": [-16.0, 0.05, 0.05], "build": [-8.0, 0.05, 0.05],
	"upgrade": [-9.0, 0.05, 0.0], "sell": [-10.0, 0.05, 0.0], "horn": [-7.0, 0.5, 0.0],
	"boss": [-5.0, 0.5, 0.0], "portal": [-10.0, 0.2, 0.05], "leak": [-8.0, 0.15, 0.0],
	"click": [-14.0, 0.03, 0.0], "victory": [-6.0, 1.0, 0.0], "defeat": [-6.0, 1.0, 0.0],
	"tile": [-7.0, 0.2, 0.03], "chest": [-7.0, 0.2, 0.0], "card": [-13.0, 0.05, 0.03],
	"shield": [-12.0, 0.08, 0.1],
	# recorded only (tools/sfx_batch.py); without a file they borrow a built-in sound (FALLBACK)
	"scaffold": [-8.0, 0.1, 0.05], "dig": [-8.0, 0.1, 0.05], "rune": [-12.0, 0.1, 0.0],
	"talent": [-9.0, 0.3, 0.0], "fire": [-17.0, 0.12, 0.08], "surge": [-9.0, 0.5, 0.0],
	# creature towers, zombies and the like
	"breath": [-11.0, 0.3, 0.05], "smite": [-9.0, 0.2, 0.05], "spear": [-16.0, 0.06, 0.1], "grasp": [-11.0, 0.15, 0.08],
	"stomp": [-9.0, 0.2, 0.06], "maul": [-11.0, 0.1, 0.08], "claw": [-12.0, 0.08, 0.1], "magma": [-13.0, 0.1, 0.08],
	"raise": [-12.0, 0.15, 0.08], "grab": [-12.0, 0.1, 0.1], "crumble": [-15.0, 0.08, 0.1], "graves": [-17.0, 0.25, 0.06],
	"wings": [-15.0, 0.5, 0.1], "splat": [-14.0, 0.08, 0.1], "wave_clear": [-8.0, 1.0, 0.0],
}
const FALLBACK := {"scaffold": "build", "dig": "build", "rune": "card", "talent": "upgrade", "fire": "pulse", "surge": "portal",
	"breath": "fire", "smite": "boom", "spear": "arrow", "grasp": "slam", "stomp": "slam", "maul": "slam", "claw": "hit",
	"magma": "lob", "raise": "portal", "grab": "hit", "crumble": "die", "graves": "pulse", "wings": "card", "splat": "lob",
	"wave_clear": "gold"}

var muted := false
var music_enabled := true
var listener: Node3D            # camera rig: sounds far from it are quieter
var _streams := {}
var _players: Array = []
var _last := {}
var _music: AudioStreamPlayer   # deck 0 (deck 1 is for crossfades)
var _decks: Array = []
var _cur := 0
var _music_key := "-"            # what's playing: "proc", "music" or "music_<faction>"
var _proc_stream: AudioStreamWAV
var _xfade: Tween
const MUSIC_DB := -15.0          # the procedural loop
const TRACK_DB := -24.5          # recorded tracks are mastered ~10 dB louder than the procedural loop (measured)
const MUSIC_XFADE := 4.0         # seconds; also how tracks loop without a seam
## Per-track trims (dB) so every recorded track sits at the same loudness (measured RMS; see README).
const TRACK_TRIM := {"music_forge": 2.7, "music_tide": 3.0, "music_grave": 0.5, "music_verdant": 0.5}
var _track_db := TRACK_DB
var _music_task := -1
var _music_pcm := PackedByteArray()


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in MAX_VOICES:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	for i in 2:
		var d := AudioStreamPlayer.new()
		d.volume_db = MUSIC_DB
		add_child(d)
		_decks.append(d)
	_music = _decks[0]
	if DisplayServer.get_name() == "headless":
		return   # nothing to hear; skip generating the sounds
	for n in SOUNDS:
		_streams[n] = _load_override(n)
		if _streams[n] == null:
			_streams[n] = _make(FALLBACK.get(n, n))


func _load_override(n: String) -> AudioStream:
	for ext in ["ogg", "wav", "mp3"]:
		var p: String = OVERRIDE_DIR + n + "." + String(ext)
		if ResourceLoader.exists(p):
			return load(p)
	return null


## Plays a sound. pos (optional) is a world position: far-off sounds are quieter.
func play(n: String, pos: Variant = null) -> void:
	if muted or not _streams.has(n):
		return
	var cfg: Array = SOUNDS[n]
	var now := Time.get_ticks_msec() / 1000.0
	if now - float(_last.get(n, -10.0)) < float(cfg[1]):
		return
	_last[n] = now
	var vol: float = cfg[0]
	if pos is Vector3 and listener:
		var cam := listener as CameraRig
		var reach: float = maxf(cam.distance * 1.1, 20.0) if cam else 30.0
		var d := Vector2(pos.x - listener.position.x, pos.z - listener.position.z).length()
		vol -= clampf((d - reach * 0.4) / reach, 0.0, 1.0) * 14.0
	for p in _players:
		var ap := p as AudioStreamPlayer
		if not ap.playing:
			ap.stream = _streams[n]
			ap.volume_db = vol
			ap.pitch_scale = 1.0 + randf_range(-float(cfg[2]), float(cfg[2]))
			ap.play()
			return


func set_muted(m: bool) -> void:
	muted = m
	for d in _decks:
		(d as AudioStreamPlayer).stream_paused = m
	if m:
		for p in _players:
			(p as AudioStreamPlayer).stop()


## Plays a color's battle track (music_<faction>), or with no faction the menu theme (music_menu). Falls back to
## music.ogg/.mp3/.wav, then to the procedural loop (generated on a worker thread the first time).
func start_music(faction := "") -> void:
	if not music_enabled:
		return
	var key := "music_" + (faction if faction != "" else "menu")
	var st: AudioStream = _load_override(key)
	if st == null:
		key = "music"
		st = _load_override(key)
	if st == null:
		key = "proc"
	if key == _music_key:
		return
	_music_key = key
	if key != "proc":
		_track_db = TRACK_DB + float(TRACK_TRIM.get(key, 0.0))
		_crossfade_to(st, _track_db)
	elif _proc_stream:
		_crossfade_to(_proc_stream, MUSIC_DB)
	elif _music_task < 0:
		_music_task = WorkerThreadPool.add_task(_gen_music)


## Fades the playing deck out while the other deck fades in with st.
func _crossfade_to(st: AudioStream, db: float) -> void:
	var old: AudioStreamPlayer = _decks[_cur]
	_cur = 1 - _cur
	var nw: AudioStreamPlayer = _decks[_cur]
	if _xfade and _xfade.is_valid():
		_xfade.kill()
	nw.stream = st
	nw.volume_db = -50.0 if old.playing else db
	nw.play()
	nw.stream_paused = muted
	_xfade = create_tween().set_parallel(true)
	_xfade.tween_property(nw, "volume_db", db, MUSIC_XFADE)
	if old.playing:
		_xfade.tween_property(old, "volume_db", -50.0, MUSIC_XFADE)
		_xfade.chain().tween_callback(func():
			if _decks[_cur] != old:
				old.stop())


func _process(_delta: float) -> void:
	if _music_task >= 0 and WorkerThreadPool.is_task_completed(_music_task):
		WorkerThreadPool.wait_for_task_completion(_music_task)
		_music_task = -1
		_proc_stream = AudioStreamWAV.new()
		_proc_stream.format = AudioStreamWAV.FORMAT_16_BITS
		_proc_stream.mix_rate = RATE
		_proc_stream.data = _music_pcm
		_proc_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		_proc_stream.loop_end = _music_pcm.size() / 2
		if _music_key == "proc":
			_crossfade_to(_proc_stream, MUSIC_DB)
	# recorded tracks don't loop by themselves: near the end, crossfade into a fresh start of the same track
	var d: AudioStreamPlayer = _decks[_cur]
	if d.playing and not d.stream_paused and d.stream and not (d.stream is AudioStreamWAV):
		if d.stream.get_length() - d.get_playback_position() <= MUSIC_XFADE:
			_crossfade_to(d.stream, _track_db)


# ------------------------------------------------------------------ synthesis helpers

static func _pcm(buf: PackedFloat32Array) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(buf.size() * 2)
	for i in buf.size():
		bytes.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 32000.0))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = RATE
	s.data = bytes
	return s


## One voice: frequency glides f0 -> f1 (exponential), shaped by an attack + power-curve decay.
## wave: sine / tri / square / saw. noise: 0..1 mix of low-passed noise.
static func _tone(dur: float, f0: float, f1: float, wave := "sine", vol := 0.5, noise := 0.0,
		attack := 0.004, decay_pow := 2.0, vib := 0.0, lp := 0.35) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var ph := 0.0
	var nz := 0.0
	for i in n:
		var t := float(i) / RATE
		var k := t / dur
		var f := f0 * pow(f1 / f0, k) * (1.0 + vib * sin(TAU * 6.0 * t))
		ph = fmod(ph + f / RATE, 1.0)
		var s := 0.0
		match wave:
			"sine": s = sin(TAU * ph)
			"tri": s = 1.0 - 4.0 * absf(ph - 0.5)
			"square": s = 1.0 if ph < 0.5 else -1.0
			"saw": s = 2.0 * ph - 1.0
		if noise > 0.0:
			nz += (randf_range(-1.0, 1.0) - nz) * lp
			s = s * (1.0 - noise) + nz * noise * 1.6
		var env := minf(1.0, t / attack) * pow(1.0 - k, decay_pow)
		out[i] = s * env * vol
	return out


static func _mix(a: PackedFloat32Array, b: PackedFloat32Array, offset := 0.0) -> PackedFloat32Array:
	var off := int(offset * RATE)
	var n := maxi(a.size(), b.size() + off)
	var out := a.duplicate()
	out.resize(n)
	for i in b.size():
		out[i + off] += b[i]
	return out


static func _notes(freqs: Array, step: float, dur: float, wave := "tri", vol := 0.35) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for i in freqs.size():
		out = _mix(out, _tone(dur, freqs[i], freqs[i], wave, vol, 0.0, 0.005, 1.6), step * i)
		out = _mix(out, _tone(dur, freqs[i] * 2.0, freqs[i] * 2.0, "sine", vol * 0.3, 0.0, 0.005, 2.5), step * i)
	return out


static func _make(n: String) -> AudioStreamWAV:
	var b := PackedFloat32Array()
	match n:
		"arrow":
			b = _tone(0.13, 1400.0, 500.0, "tri", 0.25, 0.75, 0.01, 1.5, 0.0, 0.6)
		"bolt":
			b = _mix(_tone(0.2, 190.0, 60.0, "square", 0.35, 0.35), _tone(0.05, 1800.0, 900.0, "tri", 0.3, 0.5))
		"orb":
			b = _mix(_tone(0.35, 520.0, 980.0, "sine", 0.3, 0.0, 0.02, 1.5, 0.04), _tone(0.35, 780.0, 1470.0, "sine", 0.18, 0.0, 0.03, 1.8, 0.05))
		"lob":
			b = _tone(0.28, 140.0, 70.0, "sine", 0.45, 0.45, 0.01, 1.5, 0.0, 0.15)
		"boom":
			b = _mix(_tone(0.6, 90.0, 32.0, "sine", 0.7, 0.0, 0.002, 2.2), _tone(0.5, 200.0, 60.0, "sine", 0.5, 0.95, 0.002, 2.5, 0.0, 0.08))
		"chain":
			b = _tone(0.3, 900.0, 300.0, "square", 0.22, 0.55, 0.002, 1.4, 0.35, 0.7)
		"slam":
			b = _mix(_tone(0.5, 70.0, 30.0, "sine", 0.8, 0.0, 0.002, 2.0), _tone(0.35, 150.0, 60.0, "sine", 0.5, 0.9, 0.002, 2.0, 0.0, 0.05))
		"pulse":
			b = _tone(0.45, 330.0, 220.0, "sine", 0.35, 0.1, 0.03, 1.5, 0.02)
		"hit":
			b = _tone(0.05, 1300.0, 500.0, "square", 0.2, 0.4, 0.001, 2.0)
		"die":
			b = _tone(0.22, 420.0, 110.0, "saw", 0.25, 0.3, 0.004, 1.8, 0.0, 0.3)
		"gold":
			b = _mix(_tone(0.25, 1319.0, 1319.0, "sine", 0.3, 0.0, 0.002, 3.0), _tone(0.3, 1760.0, 1760.0, "sine", 0.25, 0.0, 0.002, 3.0), 0.06)
		"build":
			b = _mix(_tone(0.25, 160.0, 80.0, "tri", 0.6, 0.55, 0.003, 2.0, 0.0, 0.2), _tone(0.12, 600.0, 400.0, "tri", 0.25, 0.3), 0.08)
		"upgrade":
			b = _notes([523.0, 659.0, 784.0, 1047.0], 0.07, 0.3, "tri", 0.3)
		"sell":
			b = _notes([1047.0, 784.0, 659.0], 0.06, 0.22, "sine", 0.3)
		"horn":
			b = _mix(_tone(1.2, 147.0, 147.0, "saw", 0.28, 0.1, 0.12, 1.2, 0.012, 0.3), _tone(1.2, 220.0, 220.0, "saw", 0.18, 0.1, 0.18, 1.2, 0.012, 0.3), 0.05)
			b = _lowpass(b, 0.12)
		"boss":
			b = _mix(_tone(1.8, 98.0, 92.0, "saw", 0.35, 0.1, 0.2, 1.1, 0.01), _tone(1.8, 73.0, 69.0, "saw", 0.3, 0.1, 0.25, 1.1, 0.01))
			b = _mix(_lowpass(b, 0.08), _tone(0.6, 60.0, 30.0, "sine", 0.8, 0.0, 0.002, 2.0))
		"portal":
			b = _mix(_tone(0.7, 180.0, 900.0, "sine", 0.3, 0.4, 0.2, 1.2, 0.03, 0.2), _tone(0.7, 270.0, 1350.0, "sine", 0.15, 0.0, 0.25, 1.5))
		"leak":
			b = _mix(_tone(0.4, 110.0, 90.0, "square", 0.3, 0.2, 0.005, 1.3), _tone(0.4, 116.0, 95.0, "square", 0.2, 0.0, 0.005, 1.3))
			b = _lowpass(b, 0.25)
		"click":
			b = _tone(0.035, 1800.0, 1200.0, "tri", 0.25, 0.2, 0.001, 2.0)
		"victory":
			b = _notes([523.0, 659.0, 784.0, 1047.0, 784.0, 1047.0], 0.16, 0.7, "tri", 0.3)
		"defeat":
			b = _notes([392.0, 370.0, 330.0, 262.0], 0.28, 0.9, "tri", 0.3)
		"tile":
			b = _mix(_tone(0.45, 90.0, 45.0, "sine", 0.6, 0.6, 0.004, 1.8, 0.0, 0.1), _tone(0.5, 880.0, 880.0, "sine", 0.15, 0.0, 0.01, 2.5), 0.1)
		"chest":
			b = _notes([784.0, 988.0, 1175.0, 1568.0], 0.08, 0.5, "sine", 0.3)
		"card":
			b = _tone(0.18, 700.0, 1100.0, "sine", 0.25, 0.2, 0.01, 2.0)
		"shield":
			b = _tone(0.3, 1600.0, 500.0, "sine", 0.3, 0.3, 0.002, 2.0, 0.08)
	return _pcm(b)


static func _lowpass(b: PackedFloat32Array, a: float) -> PackedFloat32Array:
	var y := 0.0
	for i in b.size():
		y += (b[i] - y) * a
		b[i] = y * 1.8
	return b


# ------------------------------------------------------------------ music

## A calm 8-bar loop in D minor: pad chords, a soft bass pulse and a plucked arpeggio.
func _gen_music() -> void:
	var bpm := 84.0
	var beat := 60.0 / bpm
	var chords := [[146.8, 174.6, 220.0], [116.5, 146.8, 174.6], [174.6, 220.0, 261.6], [130.8, 164.8, 196.0],
		[146.8, 174.6, 220.0], [116.5, 146.8, 174.6], [98.0, 116.5, 146.8], [110.0, 138.6, 164.8]]
	var bar := beat * 4.0
	var total := int(bar * chords.size() * RATE)
	var buf := PackedFloat32Array()
	buf.resize(total)
	var arp := [0, 1, 2, 1, 2, 0, 1, 2]
	for ci in chords.size():
		var ch: Array = chords[ci]
		var t0 := int(ci * bar * RATE)
		var len_ := int(bar * RATE)
		# pad: two slightly detuned soft triangles per note, swelling in and out
		for f in ch:
			var pa := 0.0
			var pb := 0.0
			var fa0: float = f * 0.997 / RATE
			var fb0: float = f * 1.003 / RATE
			for i in len_:
				var k := float(i) / len_
				var env := minf(1.0, k * 5.0) * minf(1.0, (1.0 - k) * 5.0) * 0.045
				pa = fmod(pa + fa0, 1.0)
				pb = fmod(pb + fb0, 1.0)
				buf[t0 + i] += (2.0 - 4.0 * absf(pa - 0.5) - 4.0 * absf(pb - 0.5)) * env
		# bass on each beat
		for bt in 4:
			var bs := t0 + int(bt * beat * RATE)
			var bl := int(beat * 0.9 * RATE)
			var fb: float = ch[0] * 0.5
			for i in bl:
				if bs + i >= total:
					break
				var k := float(i) / bl
				buf[bs + i] += sin(TAU * fb * i / RATE) * pow(1.0 - k, 1.5) * minf(1.0, i / 200.0) * (0.16 if bt % 2 == 0 else 0.09)
		# arpeggio, eighth notes, an octave up
		for st in 8:
			var s0 := t0 + int(st * beat * 0.5 * RATE)
			var sl := int(beat * 0.9 * RATE)
			var fa: float = ch[arp[st]] * 2.0
			var ph2 := 0.0
			for i in sl:
				if s0 + i >= total:
					break
				ph2 = fmod(ph2 + fa / RATE, 1.0)
				var k := float(i) / sl
				buf[s0 + i] += (1.0 - 4.0 * absf(ph2 - 0.5)) * pow(1.0 - k, 3.0) * minf(1.0, i / 60.0) * 0.07
	var bytes := PackedByteArray()
	bytes.resize(total * 2)
	for i in total:
		bytes.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 30000.0))
	_music_pcm = bytes
