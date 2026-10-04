shader_type spatial;
// The dark floor far under the board when it's drawn with KayKit tiles (the island look of the KayKit samples):
// big dark hexes with slightly darker gaps, each a touch lighter or darker than its neighbors, fading toward the edges.
render_mode unshaded, cull_disabled, fog_disabled, shadows_disabled;

uniform vec3 base_col : source_color = vec3(0.125, 0.125, 0.13);
uniform vec3 gap_col : source_color = vec3(0.085, 0.085, 0.09);
uniform float hex_size = 9.0;   // world units across a hex
uniform float gap = 0.035;      // gap width, as a fraction of a hex
uniform float vary = 0.012;     // how much each hex's shade varies

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// Hex tiling (pointy-top): returns the hex id in xy and the distance to its nearest edge in z (0 at the edge).
vec3 hex_tile(vec2 p) {
	const vec2 s = vec2(1.0, 1.7320508);
	vec4 c = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
	vec4 h = vec4(p - c.xy * s, p - (c.zw + 0.5) * s);
	vec4 g = dot(h.xy, h.xy) < dot(h.zw, h.zw) ? vec4(h.xy, c.xy) : vec4(h.zw, c.zw + 0.5);
	vec2 a = abs(g.xy);
	float d = 0.5 - max(dot(a, s * 0.5), a.x);
	return vec3(g.zw, d);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec3 h = hex_tile(wpos.xz / hex_size);
	vec3 col = base_col + (hash(h.xy) - 0.5) * 2.0 * vary;
	col = mix(gap_col, col, smoothstep(gap * 0.6, gap, h.z));
	ALBEDO = col;
}
