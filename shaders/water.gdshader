shader_type spatial;
render_mode blend_mix, cull_disabled, specular_schlick_ggx;
// Stylized lake water: two-tone ripples with gentle waves and a soft glint.

uniform vec4 shallow : source_color = vec4(0.36, 0.78, 0.82, 1.0);
uniform vec4 deep : source_color = vec4(0.10, 0.36, 0.55, 1.0);
uniform float alpha = 0.86;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(w_pos.x * 0.6 + TIME * 1.1) * 0.03 + cos(w_pos.z * 0.7 + TIME * 0.8) * 0.03;
}

void fragment() {
	vec2 p = w_pos.xz;
	float r = sin(p.x * 1.3 + TIME * 1.4) * cos(p.y * 1.1 - TIME * 1.1);
	r += 0.5 * sin((p.x + p.y) * 2.1 - TIME * 2.0);
	float band = smoothstep(0.55, 0.95, r);
	ALBEDO = mix(deep.rgb, shallow.rgb, 0.45 + 0.25 * r) + vec3(band * 0.18);
	ALPHA = alpha;
	ROUGHNESS = 0.12;
	SPECULAR = 0.7;
	NORMAL = normalize(NORMAL + vec3(cos(p.x * 1.3 + TIME) * 0.08, 0.0, sin(p.y * 1.2 - TIME) * 0.08));
}
