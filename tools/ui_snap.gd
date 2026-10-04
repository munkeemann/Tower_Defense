extends SceneTree
## Dev tool (headless, no window): draws the game's real HUD (its Control tree, laid out by Godot) into PNGs with a
## small software 2D renderer: style boxes (flat, and nine-slice textures with their tint), text (glyphs taken from
## the TextServer's own glyph cache, with outlines), textures and color rects. Custom-drawn controls (tile diagrams,
## item icons) and 3D portraits don't exist headless, so they show as faint boxes.
## Godot --headless --path . --script res://tools/ui_snap.gd -- out_dir [screens] [--no-kenney] --scratch
##   screens: comma list of menu, heroes, council, run, tile, rewards, info, castle, damage, end (default: all)
##   --hover: draws the first big card of each screen in its hover style; --deck: a 1280x800 screen

const ALL := ["menu", "heroes", "council", "run", "tile", "rewards", "info", "castle", "end"]

var game: Game
var img: Image
var ts: TextServer
var hover_one := false
var _hovered: Control
var _glyphs := {}
var _tex_imgs := {}


func _init() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := a[0] if a.size() > 0 else "user://ui"
	var screens: Array = ALL
	if a.size() > 1 and not a[1].begins_with("--") and a[1] != "all":
		screens = Array(a[1].split(","))
	hover_one = "--hover" in a
	ts = TextServerManager.get_primary_interface()
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(1600, 900) if not "--deck" in a else Vector2i(1280, 800)   # --deck: Steam Deck's screen
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	for i in 4:
		await process_frame
	for s in screens:
		await _open(s)
		for i in 3:
			await process_frame
		var path := "%s/ui_%s.png" % [out, s]
		_snap().save_png(path)
		print("UISNAP ", s, " -> ", path)
	quit()


## Puts the game on one screen.
func _open(s: String) -> void:
	var hud := game.hud
	match s:
		"menu":
			game.to_menu()
		"heroes":
			hud.show_hero_select("crown")
		"council":
			hud.show_council()
		"run", "tile":
			game.start_run("crown")
		"rewards":
			if game.state == Game.S.MENU:
				game.start_run("crown")
			hud.hide_choices()
			hud.hide_place_hint()
			game._enter_reward()
		"damage":
			# a few towers with made-up totals, for the damage chart
			if game.state == Game.S.MENU:
				game.start_run("crown")
			hud.hide_choices()
			hud.hide_place_hint()
			game._enter_build()
			for i in 4:
				_place_a_tower()
			var fake := [5230.0, 2875.0, 1190.0, 412.0]
			for i in game.towers.size():
				game.towers[i].damage_done = fake[i % fake.size()]
				game.towers[i].level = 1 + i % 3
			game.deselect()
			hud.refresh_damage(1.0)
		"info", "castle":
			if game.state == Game.S.MENU:
				game.start_run("crown")
			hud.hide_choices()
			hud.hide_place_hint()
			game._enter_build()
			if s == "info":
				_place_a_tower()
			else:
				hud.toggle_castle()
		"end":
			hud.show_end(true, "Waves held: 30 / 30\nTowers built: 24\nGold earned: 5120\nRenown earned: +140")
	await process_frame
	_hovered = null
	if hover_one:
		_hovered = _first_button(hud.root)


func _place_a_tower() -> void:
	game.gold = 999
	game.owned["archer"] = 2
	for pc in game.board.path_cells.keys():
		for c in Hex.disc(pc, 2):
			var cells := GameData.footprint("archer", c, 4)
			if game.board.can_build_all(cells):
				game.placing = "archer"
				game.place_facing = 4
				game.try_place(c)
				game.placing = ""
				if not game.towers.is_empty():
					game.select_tower(game.towers.back())
				return


func _first_button(n: Node) -> Control:
	for c in n.get_children():
		if c is CanvasItem and not (c as CanvasItem).visible:
			continue
		if c is Button and (c as Button).custom_minimum_size.y >= 150.0 and not (c as Button).disabled:
			return c
		var f := _first_button(c)
		if f:
			return f
	return null


# ------------------------------------------------------------------ drawing

func _snap() -> Image:
	var size := Vector2i(root.get_visible_rect().size)
	if size.x < 16:
		size = Vector2i(1600, 900)
	img = Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	# a stand-in for the 3D view underneath: KayKit grass and sea
	img.fill(Color(0.42, 0.55, 0.3))
	_fill(Rect2(0, size.y * 0.72, size.x, size.y * 0.28), Color(0.25, 0.45, 0.62))
	_draw_tree(game.hud.root, Color.WHITE)
	return img


func _draw_tree(n: Node, mod: Color) -> void:
	var m := mod
	if n is CanvasItem:
		var ci := n as CanvasItem
		if not ci.visible:
			return
		m = mod * ci.modulate
		if m.a <= 0.01:
			return
	if n is Control:
		_draw_control(n as Control, m * (n as Control).self_modulate)
	for c in n.get_children():
		_draw_tree(c, m)


func _draw_control(c: Control, m: Color) -> void:
	var r := c.get_global_rect()
	if c is Button:
		var b := c as Button
		var st := "normal"
		if b.disabled:
			st = "disabled"
		elif b.toggle_mode and b.button_pressed:
			st = "pressed"
		elif c == _hovered:
			st = "hover"
		var sb := b.get_theme_stylebox(st)
		_stylebox(sb, r, m)
		var col_name: String = {"disabled": "font_disabled_color", "pressed": "font_pressed_color", "hover": "font_hover_color"}.get(st, "font_color")
		var inner := r
		if sb:
			inner = Rect2(r.position + Vector2(sb.content_margin_left, sb.content_margin_top),
				r.size - Vector2(sb.content_margin_left + sb.content_margin_right, sb.content_margin_top + sb.content_margin_bottom))
		_text(b.text, inner, b.get_theme_font("font"), b.get_theme_font_size("font_size"), b.get_theme_color(col_name), m,
			b.get_theme_constant("outline_size"), b.get_theme_color("font_outline_color"), b.alignment, VERTICAL_ALIGNMENT_CENTER,
			b.autowrap_mode != TextServer.AUTOWRAP_OFF, b.get_theme_constant("line_spacing"))
	elif c is Label:
		var l := c as Label
		_stylebox(l.get_theme_stylebox("normal"), r, m)
		_text(l.text, r, l.get_theme_font("font"), l.get_theme_font_size("font_size"), l.get_theme_color("font_color"), m,
			l.get_theme_constant("outline_size"), l.get_theme_color("font_outline_color"), l.horizontal_alignment,
			l.vertical_alignment, l.autowrap_mode != TextServer.AUTOWRAP_OFF, l.get_theme_constant("line_spacing"))
	elif c is PanelContainer or c is Panel:
		_stylebox(c.get_theme_stylebox("panel"), r, m)
	elif c is ColorRect:
		_fill(r, (c as ColorRect).color * m)
	elif c is TextureRect:
		var t := (c as TextureRect).texture
		if t:
			_texture(t, r, m)
	elif c.get_script() != null and c.has_method("_draw"):
		_fill(r, Color(1, 1, 1, 0.08) * m)   # custom-drawn: a faint box where it goes


func _fill(r: Rect2, col: Color) -> void:
	var ri := Rect2i(r.position.round(), r.size.round()).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	if ri.size.x <= 0 or ri.size.y <= 0 or col.a <= 0.0:
		return
	var tmp := Image.create(ri.size.x, ri.size.y, false, Image.FORMAT_RGBA8)
	tmp.fill(Color(clampf(col.r, 0, 1), clampf(col.g, 0, 1), clampf(col.b, 0, 1), clampf(col.a, 0, 1)))
	img.blend_rect(tmp, Rect2i(Vector2i.ZERO, ri.size), ri.position)


func _stylebox(sb: StyleBox, r: Rect2, m: Color) -> void:
	if sb == null:
		return
	if sb is StyleBoxFlat:
		var f := sb as StyleBoxFlat
		var rr := r.grow_individual(f.expand_margin_left, f.expand_margin_top, f.expand_margin_right, f.expand_margin_bottom)
		if f.draw_center:
			_fill(rr, f.bg_color * m)
		var bc := f.border_color * m
		_fill(Rect2(rr.position, Vector2(rr.size.x, f.border_width_top)), bc)
		_fill(Rect2(rr.position + Vector2(0, rr.size.y - f.border_width_bottom), Vector2(rr.size.x, f.border_width_bottom)), bc)
		_fill(Rect2(rr.position, Vector2(f.border_width_left, rr.size.y)), bc)
		_fill(Rect2(rr.position + Vector2(rr.size.x - f.border_width_right, 0), Vector2(f.border_width_right, rr.size.y)), bc)
	elif sb is StyleBoxTexture:
		var t := sb as StyleBoxTexture
		if t.texture == null:
			return
		var src := _tinted(t.texture, t.modulate_color * m)
		var reg := Rect2i(t.region_rect) if t.region_rect.has_area() else Rect2i(Vector2i.ZERO, src.get_size())
		var d := r.grow_individual(t.expand_margin_left, t.expand_margin_top, t.expand_margin_right, t.expand_margin_bottom)
		var ml := int(t.texture_margin_left)
		var mt := int(t.texture_margin_top)
		var mr := int(t.texture_margin_right)
		var mb := int(t.texture_margin_bottom)
		var sx := [reg.position.x, reg.position.x + ml, reg.end.x - mr, reg.end.x]
		var sy := [reg.position.y, reg.position.y + mt, reg.end.y - mb, reg.end.y]
		var dx := [d.position.x, d.position.x + ml, d.end.x - mr, d.end.x]
		var dy := [d.position.y, d.position.y + mt, d.end.y - mb, d.end.y]
		for j in 3:
			for i in 3:
				if i == 1 and j == 1 and not t.draw_center:
					continue
				var s_rect := Rect2i(sx[i], sy[j], sx[i + 1] - sx[i], sy[j + 1] - sy[j])
				var dst := Rect2i(int(round(dx[i])), int(round(dy[j])), int(round(dx[i + 1])) - int(round(dx[i])),
					int(round(dy[j + 1])) - int(round(dy[j])))
				if s_rect.size.x <= 0 or s_rect.size.y <= 0 or dst.size.x <= 0 or dst.size.y <= 0:
					continue
				var piece := src.get_region(s_rect)
				if piece.get_size() != dst.size:
					piece.resize(dst.size.x, dst.size.y, Image.INTERPOLATE_BILINEAR)
				img.blend_rect(piece, Rect2i(Vector2i.ZERO, dst.size), dst.position)


## A texture's image multiplied by a color (cached).
func _tinted(t: Texture2D, tint: Color) -> Image:
	var key := "%d|%s" % [t.get_instance_id(), tint.to_html()]
	if _tex_imgs.has(key):
		return _tex_imgs[key]
	var im := t.get_image()
	if im == null:
		im = Image.create(4, 4, false, Image.FORMAT_RGBA8)
	if im.is_compressed():
		im.decompress()
	im = im.duplicate()
	im.convert(Image.FORMAT_RGBA8)
	if tint != Color.WHITE:
		for y in im.get_height():
			for x in im.get_width():
				var p := im.get_pixel(x, y)
				im.set_pixel(x, y, Color(clampf(p.r * tint.r, 0, 1), clampf(p.g * tint.g, 0, 1), clampf(p.b * tint.b, 0, 1),
					clampf(p.a * tint.a, 0, 1)))
	_tex_imgs[key] = im
	return im


func _texture(t: Texture2D, r: Rect2, m: Color) -> void:
	var src := _tinted(t, m)
	var ts_ := Vector2(src.get_size())
	var k := minf(r.size.x / ts_.x, r.size.y / ts_.y)
	var sz := Vector2i((ts_ * k).round())
	if sz.x <= 0 or sz.y <= 0:
		return
	var piece := src.duplicate()
	piece.resize(sz.x, sz.y, Image.INTERPOLATE_BILINEAR)
	var at := Vector2i((r.position + (r.size - Vector2(sz)) * 0.5).round())
	img.blend_rect(piece, Rect2i(Vector2i.ZERO, sz), at)


# ------------------------------------------------------------------ text

func _text(text: String, r: Rect2, font: Font, size: int, col: Color, m: Color, outline: int, ocol: Color, halign: int,
		valign: int, wrap: bool, line_sp: int) -> void:
	if text.strip_edges() == "" or font == null:
		return
	var p := TextParagraph.new()
	p.add_string(text, font, size)
	if wrap:
		p.width = r.size.x
		p.break_flags = TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE
	else:
		p.break_flags = TextServer.BREAK_MANDATORY
	var n := p.get_line_count()
	var total := 0.0
	for i in n:
		total += p.get_line_size(i).y + (line_sp if i < n - 1 else 0)
	var y := r.position.y
	if valign == VERTICAL_ALIGNMENT_CENTER:
		y += (r.size.y - total) * 0.5
	elif valign == VERTICAL_ALIGNMENT_BOTTOM:
		y += r.size.y - total
	var c := col * m
	var oc := ocol * m
	for i in n:
		var rid := p.get_line_rid(i)
		var w := p.get_line_width(i)
		var x := r.position.x
		if halign == HORIZONTAL_ALIGNMENT_CENTER:
			x += (r.size.x - w) * 0.5
		elif halign == HORIZONTAL_ALIGNMENT_RIGHT:
			x += r.size.x - w
		var base := y + p.get_line_ascent(i)
		var glyphs := ts.shaped_text_get_glyphs(rid)
		for pass_ in ([0, 1] if outline > 0 else [1]):
			var pen := x
			for g in glyphs:
				for k in int(g["repeat"]):
					if int(g["index"]) != 0 and g["font_rid"] != RID():
						_glyph(g["font_rid"], int(g["font_size"]), int(g["index"]), Vector2(pen, base) + g["offset"],
							oc if pass_ == 0 else c, outline if pass_ == 0 else 0)
					pen += float(g["advance"])
		y += p.get_line_size(i).y + line_sp


func _glyph(frid: RID, size: int, index: int, at: Vector2, col: Color, outline: int) -> void:
	var key := "%s|%d|%d|%d|%s" % [frid, size, index, outline, col.to_html()]
	var gi: Array = _glyphs.get(key, [])
	if gi.is_empty():
		var sz := Vector2i(size, outline)
		ts.font_render_glyph(frid, sz, index)
		var ti := ts.font_get_glyph_texture_idx(frid, sz, index)
		if ti < 0:
			_glyphs[key] = [null, Vector2.ZERO]
			return
		var uv := Rect2i(ts.font_get_glyph_uv_rect(frid, sz, index))
		var off := ts.font_get_glyph_offset(frid, sz, index)
		var atlas := ts.font_get_texture_image(frid, sz, ti)
		if atlas == null or uv.size.x <= 0 or uv.size.y <= 0:
			_glyphs[key] = [null, Vector2.ZERO]
			return
		var piece := atlas.get_region(uv)
		piece.convert(Image.FORMAT_RGBA8)
		for y in piece.get_height():
			for x in piece.get_width():
				var a := piece.get_pixel(x, y).a
				piece.set_pixel(x, y, Color(clampf(col.r, 0, 1), clampf(col.g, 0, 1), clampf(col.b, 0, 1), a * clampf(col.a, 0, 1)))
		gi = [piece, off]
		_glyphs[key] = gi
	if gi[0] == null:
		return
	var pc: Image = gi[0]
	var pos := Vector2i((at + (gi[1] as Vector2)).round())
	img.blend_rect(pc, Rect2i(Vector2i.ZERO, pc.get_size()), pos)
