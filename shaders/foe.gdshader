shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back;
// Overlay on enemies: darker bodies with a hot rim, so foes stand out from the ground and your towers.

uniform vec3 rim_col : source_color = vec3(1.0, 0.3, 0.2);
uniform float darken = 0.38;

void fragment() {
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	ALBEDO = mix(vec3(0.03, 0.02, 0.04), rim_col, f);
	ALPHA = clamp(darken + f * 0.8, 0.0, 1.0);
}
