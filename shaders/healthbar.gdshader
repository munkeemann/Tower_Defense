shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

instance uniform float fill = 1.0;
instance uniform vec4 bar_color : source_color = vec4(0.3, 0.9, 0.3, 1.0);

void vertex() {
	// Screen-facing billboard that keeps the node's scale.
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(
		INV_VIEW_MATRIX[0] * length(MODEL_MATRIX[0].xyz),
		INV_VIEW_MATRIX[1] * length(MODEL_MATRIX[1].xyz),
		INV_VIEW_MATRIX[2],
		MODEL_MATRIX[3]);
}

void fragment() {
	float edge = step(UV.x, 0.015) + step(0.985, UV.x) + step(UV.y, 0.08) + step(0.92, UV.y);
	vec3 col = UV.x <= fill ? bar_color.rgb : vec3(0.15, 0.05, 0.05);
	col = mix(col, vec3(0.0), clamp(edge, 0.0, 1.0));
	ALBEDO = col;
}
