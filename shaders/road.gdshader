shader_type spatial;
render_mode cull_back, diffuse_burley;
// Roads: a calm flat color with only a hint of the painted texture's light and dark, so the lane reads
// as one clean shape (Tower Dominion style) instead of busy cobbles.

uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec3 base : source_color = vec3(0.6, 0.53, 0.46);
uniform float detail = 0.45;
uniform float scale = 0.32;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float lum = dot(texture(tex, w_pos.xz * scale).rgb, vec3(0.333));
	ALBEDO = base * (1.0 + (lum - 0.45) * detail * 2.0);
	ROUGHNESS = 1.0;
	SPECULAR = 0.15;
}
