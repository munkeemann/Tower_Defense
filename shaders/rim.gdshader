shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back;
// Overlay on your towers: a soft rim light in your color's accent, so everything you own reads as yours.

uniform vec3 rim_col : source_color = vec3(1.0);
uniform float strength = 0.4;
uniform float power = 2.4;

void fragment() {
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), power);
	ALBEDO = rim_col * f * strength;
}
