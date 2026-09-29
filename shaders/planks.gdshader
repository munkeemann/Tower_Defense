shader_type spatial;
render_mode cull_back, diffuse_burley;
// Wooden bridge deck: planks laid across the walking direction.
// UV.x = distance along the bridge (world units), UV.y = 0..1 across it.

uniform vec3 wood_a : source_color = vec3(0.50, 0.34, 0.20);
uniform vec3 wood_b : source_color = vec3(0.66, 0.47, 0.29);
uniform float plank_len = 0.34;

float hash(float n) {
	return fract(sin(n * 127.1 + 311.7) * 43758.5453);
}

void fragment() {
	float u = UV.x / plank_len;
	float id = floor(u);
	float f = fract(u);
	float h = hash(id);
	vec3 col = mix(wood_a, wood_b, h);
	// painterly grain running along each plank
	float grain = sin(UV.y * 34.0 + h * 21.0 + sin(UV.y * 7.0 + h * 9.0) * 2.2);
	col *= 0.93 + 0.07 * grain;
	// dark gaps between planks, and slightly worn middles
	float gap = smoothstep(0.0, 0.07, f) * smoothstep(1.0, 0.93, f);
	col *= mix(0.32, 1.0, gap);
	col *= 1.0 + 0.06 * (1.0 - abs(UV.y - 0.5) * 2.0);
	// darker stringer boards along both edges
	float edge = smoothstep(0.0, 0.06, UV.y) * smoothstep(1.0, 0.94, UV.y);
	col *= mix(0.62, 1.0, edge);
	// nail heads near the edges of every plank
	vec2 nail = vec2(fract(u) - 0.5, min(UV.y, 1.0 - UV.y) - 0.1);
	col *= mix(0.45, 1.0, smoothstep(0.012, 0.03, length(nail * vec2(plank_len, 1.0))));
	ALBEDO = col;
	ROUGHNESS = 0.92;
	SPECULAR = 0.15;
}
