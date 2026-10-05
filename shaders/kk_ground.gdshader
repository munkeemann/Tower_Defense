shader_type spatial;
// The island's hex tiles (and towers' hexes): the KayKit atlas color (this biome's palette) with a pattern on top.
// Ground hexes (the atlas's grass swatch) get a biome surface on top (grass blades, snow drifts, leaf litter or
// marsh grass) and layered dirt and rock on their sides; road pieces get gravel, shore pieces sand ripples. Patterns
// live in world space so neighboring hexes join up, and fade out as they get too small on screen to read.

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;   // seamless value noise (red)
uniform bool use_instance_color = true;   // the tiles' per-hex shade rides on MultiMesh colors; a tower has none
uniform int style = 0;                    // 0 grass, 1 snow, 2 leaf litter, 3 marsh grass
uniform float strength = 1.0;
uniform float rough = 0.85;

varying vec3 wpos;
varying vec3 wnrm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float nz(vec2 p) {
	return texture(noise_tex, p).r;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// how readable a pattern of this world-space frequency is on screen (1 near the camera, 0 when it would shimmer)
float detail(vec2 g) {
	vec2 w = fwidth(g);
	return clamp(1.6 - max(w.x, w.y) * 2.2, 0.0, 1.0);
}

// short strokes scattered on a grid: grass blades (or leaves when round)
float strokes(vec2 xz, float freq, float density, float len, out float pick) {
	vec2 g = xz * freq;
	vec2 id = floor(g);
	vec2 f = fract(g) - 0.5;
	float h = hash(id);
	pick = hash(id + 17.3);
	vec2 jit = vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5;
	f -= jit * 0.5;
	float a = h * 6.2831;
	vec2 r = vec2(cos(a) * f.x - sin(a) * f.y, sin(a) * f.x + cos(a) * f.y);
	float d = length(vec2(r.x * len, r.y));
	float m = 1.0 - smoothstep(0.12, 0.2, d);
	return m * step(1.0 - density, hash(id + 11.0)) * detail(g);
}

vec3 grass_top(vec3 c, vec2 xz) {
	float patch = nz(xz * 0.045);
	c *= mix(0.9, 1.07, patch);
	float pick;
	float b = strokes(xz, 5.5, 0.55, 3.5, pick);
	c = mix(c, c * mix(0.72, 0.85, pick), b * 0.85 * strength);
	float b2 = strokes(xz + 0.37, 8.0, 0.35, 3.0, pick);
	c = mix(c, c * 1.16, b2 * 0.6 * strength);
	return c;
}

vec3 snow_top(vec3 c, vec2 xz) {
	float drift = nz(xz * 0.04 + 0.3);
	c = mix(c, c * vec3(0.84, 0.9, 1.0), smoothstep(0.45, 0.8, drift) * 0.55 * strength);
	float ripple = sin(dot(xz, vec2(0.6, 0.8)) * 3.5 + nz(xz * 0.12) * 7.0);
	c *= 1.0 + 0.035 * ripple * detail(xz * 3.5) * strength;
	vec2 g = xz * 16.0;
	float spark = step(0.988, hash(floor(g))) * detail(g);
	c += vec3(0.25) * spark * strength;
	return c;
}

vec3 leaf_top(vec3 c, vec2 xz) {
	c = grass_top(c, xz) * 0.97;
	float pick;
	float l = strokes(xz + 1.7, 4.0, 0.45, 1.5, pick);
	vec3 leaf = pick < 0.33 ? vec3(0.78, 0.26, 0.12) : (pick < 0.66 ? vec3(0.86, 0.55, 0.16) : vec3(0.5, 0.24, 0.12));
	c = mix(c, mix(c, leaf, 0.75), l * strength);
	return c;
}

vec3 marsh_top(vec3 c, vec2 xz) {
	c = grass_top(c, xz);
	float damp = nz(xz * 0.06 + 0.7);
	c = mix(c, c * vec3(0.8, 0.88, 0.86), smoothstep(0.55, 0.8, damp) * 0.6 * strength);
	return c;
}

vec3 sides(vec3 c, vec3 p, vec3 n) {
	// a horizontal coordinate along the face, so strata run round the hex
	float u = dot(p.xz, normalize(vec2(-n.z, n.x) + vec2(1e-4)));
	float warp = nz(vec2(u * 0.12, p.y * 0.3));
	float strata = sin(p.y * 10.0 + warp * 7.0);
	c *= 1.0 + 0.08 * strata * detail(vec2(p.y * 10.0)) * strength;
	// rock showing through the dirt in patches, greyer and lighter
	float rock = smoothstep(0.55, 0.75, nz(vec2(u * 0.18, p.y * 0.45) + 0.5));
	float lum = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(lum) * vec3(1.02, 1.0, 0.97) * 1.12, rock * 0.55 * strength);
	// cracks
	float h = nz(vec2(u * 0.25, p.y * 0.08) + 0.2);
	float crack = 1.0 - smoothstep(0.0, 0.018, abs(h - 0.5));
	c *= 1.0 - 0.35 * crack * detail(vec2(u, p.y) * 4.0) * strength;
	// pebbles
	vec2 g = vec2(u, p.y) * 9.0;
	float peb = step(0.9, hash(floor(g)));
	float pd = length(fract(g) - 0.5);
	c *= 1.0 + (hash(floor(g) + 2.0) - 0.5) * 0.4 * peb * (1.0 - smoothstep(0.2, 0.32, pd)) * detail(g) * strength;
	return c;
}

void fragment() {
	vec3 base = texture(atlas, UV).rgb;
	if (use_instance_color) {
		base *= COLOR.rgb;
	}
	int col = int(floor(UV.x * 8.0));
	int row = int(floor(UV.y * 4.0));
	float up = smoothstep(0.6, 0.85, wnrm.y);
	vec2 xz = wpos.xz;
	vec3 c = base;
	if (row == 2 && col == 0) {
		vec3 top = base;
		if (up > 0.0) {
			if (style == 1) {
				top = snow_top(base, xz);
			} else if (style == 2) {
				top = leaf_top(base, xz);
			} else if (style == 3) {
				top = marsh_top(base, xz);
			} else {
				top = grass_top(base, xz);
			}
		}
		vec3 side = up < 1.0 ? sides(base, wpos, wnrm) : base;
		c = mix(side, top, up);
	} else if (row == 2 && col == 3 && up > 0.0) {
		// road: packed earth with gravel
		vec2 g = xz * 9.0;
		float stone = step(0.72, hash(floor(g)));
		float sd = length(fract(g) - 0.5 - (vec2(hash(floor(g) + 1.0), hash(floor(g) + 2.0)) - 0.5) * 0.3);
		float s = stone * (1.0 - smoothstep(0.16, 0.26, sd)) * detail(g);
		c *= mix(0.94, 1.05, nz(xz * 0.2));
		c = mix(c, c * mix(0.8, 1.18, hash(floor(g) + 5.0)), s * up * strength);
	} else if (row == 2 && col == 4 && up > 0.0) {
		// shore sand: wind ripples and grain
		float ripple = sin(dot(xz, vec2(0.8, 0.6)) * 6.0 + nz(xz * 0.15) * 6.0);
		c *= 1.0 + 0.05 * ripple * detail(xz * 6.0) * strength;
		vec2 g = xz * 22.0;
		c *= 1.0 + (hash(floor(g)) - 0.5) * 0.12 * detail(g) * strength;
	}
	ALBEDO = c;
	ROUGHNESS = rough;
}
