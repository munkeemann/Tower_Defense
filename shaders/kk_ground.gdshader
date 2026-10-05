shader_type spatial;
// The island's hex tiles (and towers' hexes): the KayKit atlas in this biome's palette, with a surface drawn on it.
// Ground hexes (the atlas's grass swatch) get a biome top (lush grass, snow, leaf litter or marsh) and brown earth
// sides like the pack's own knolls: the atlas's dirt swatch, a wavy grass lip over it, strata, stones and cracks. Road
// pieces get gravel, shore pieces sand ripples. Patterns live in world space so neighboring hexes join up, and fade
// out where they would get too small on screen to read.

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;   // seamless value noise (red)
uniform bool use_instance_color = true;   // the tiles' per-hex shade rides on MultiMesh colors; a tower has none
uniform int style = 0;                    // 0 grass, 1 snow, 2 leaf litter, 3 marsh grass
uniform float strength = 1.0;
uniform float rough = 0.85;
// the atlas spots the pack's knolls use: their sides run down the dirt swatch from DIRT_V.x (top) to DIRT_V.y
const float DIRT_U = 0.30;
const vec2 DIRT_V = vec2(0.37, 0.42);
// a ground hex's side runs down its swatch from SIDE_V.x (the top edge) to SIDE_V.y (the foot)
const vec2 SIDE_V = vec2(0.64, 0.71);

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
	return clamp(1.7 - max(w.x, w.y) * 2.0, 0.0, 1.0);
}

// short strokes scattered on a grid (grass blades, or leaves when `len` is near 1). Returns the mask; `along` runs
// 0 at the stroke's root to 1 at its tip, `pick` is a random number for the stroke.
float strokes(vec2 xz, float freq, float density, float len, float width, out float pick, out float along) {
	vec2 g = xz * freq;
	vec2 id = floor(g);
	vec2 f = fract(g) - 0.5;
	pick = hash(id + 17.3);
	vec2 jit = vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5;
	f -= jit * 0.55;
	float a = (hash(id) - 0.5) * 1.4 + 1.5708;   // mostly "upright" on the ground: a shared lean reads as grass
	vec2 r = vec2(cos(a) * f.x - sin(a) * f.y, sin(a) * f.x + cos(a) * f.y);
	along = clamp(r.y * len * 1.6 + 0.5, 0.0, 1.0);
	float d = length(vec2(r.x / max(width * (1.0 - along * 0.7), 0.01), r.y * len));
	float m = 1.0 - smoothstep(0.75, 1.0, d);
	return m * step(1.0 - density, hash(id + 11.0)) * detail(g);
}

// grass tufts: three blades fanning up from one root (along -z, away from the game's camera, so they read as standing), dark at
// the root and light at the tip. Returns the mask; `shade` is the tone to darken / lighten by.
float tufts(vec2 xz, float freq, float density, float blade_len, out float shade) {
	vec2 g = xz * freq;
	vec2 id = floor(g);
	vec2 root = vec2(hash(id + 2.3), hash(id + 5.9)) * 0.6 + 0.2;
	vec2 f = fract(g) - root;
	float m = 0.0;
	shade = 0.0;
	float lean = (hash(id + 8.1) - 0.5) * 0.6;
	for (int k = 0; k < 3; k++) {
		float a = (float(k) - 1.0) * 0.5 + lean + (hash(id + float(k) * 3.7) - 0.5) * 0.25;
		vec2 dir = vec2(sin(a), -cos(a));
		float len = blade_len * (0.75 + 0.5 * hash(id + float(k) * 1.9));
		float t = clamp(dot(f, dir) / len, 0.0, 1.0);
		float d = length(f - dir * t * len);
		float w = 0.055 * (1.0 - t * 0.85);
		float bm = 1.0 - smoothstep(w * 0.6, w, d);
		if (bm > m) {
			m = bm;
			shade = t;
		}
	}
	return m * step(1.0 - density, hash(id + 11.0)) * detail(g);
}

// tiny round things (flowers, stones, clover, puddles): mask and pick
float dots(vec2 xz, float freq, float density, float radius, out float pick) {
	vec2 g = xz * freq;
	vec2 id = floor(g);
	vec2 f = fract(g) - 0.5 - (vec2(hash(id + 2.0), hash(id + 9.0)) - 0.5) * 0.5;
	pick = hash(id + 31.0);
	float m = 1.0 - smoothstep(radius * 0.7, radius, length(f));
	return m * step(1.0 - density, hash(id + 5.0)) * detail(g);
}

vec3 grass_top(vec3 c, vec2 xz) {
	// lush and dry patches
	float lush = nz(xz * 0.05);
	float dry = nz(xz * 0.03 + 0.4);
	c *= mix(0.88, 1.08, lush);
	c = mix(c, c * vec3(1.12, 1.06, 0.72), smoothstep(0.55, 0.8, dry) * 0.6 * strength);
	// clover clumps
	float pick;
	float clover = dots(xz, 1.6, 0.35, 0.35, pick);
	c = mix(c, c * vec3(0.78, 0.92, 0.8), clover * 0.5 * strength);
	// a fine grain of blades everywhere (noise stretched along the blades), then three layers of tufts, big to small:
	// dark at the root, light at the tip
	float grain = nz(vec2(xz.x * 7.0, xz.y * 1.6)) - 0.5;
	c *= 1.0 + grain * 0.35 * detail(xz * 7.0) * strength;
	float sh;
	float t1 = tufts(xz, 3.2, 0.85, 0.45, sh);
	c = mix(c, c * mix(0.6, 1.2, sh), t1 * 0.9 * strength);
	float t2 = tufts(xz + 0.37, 5.0, 0.8, 0.42, sh);
	c = mix(c, c * mix(0.66, 1.18, sh), t2 * 0.8 * strength);
	float t3 = tufts(xz + 1.13, 8.0, 0.75, 0.38, sh);
	c = mix(c, c * mix(0.72, 1.12, sh), t3 * 0.65 * strength);
	// a few small flowers
	float fl = dots(xz + 3.3, 2.6, 0.12, 0.13, pick);
	vec3 petal = pick < 0.4 ? vec3(1.0, 0.97, 0.88) : (pick < 0.75 ? vec3(1.0, 0.86, 0.3) : vec3(0.78, 0.6, 1.0));
	c = mix(c, petal, fl * 0.9 * strength);
	return c;
}

vec3 snow_top(vec3 c, vec2 xz) {
	// drifts with blue shadow on their lee side
	float drift = nz(xz * 0.04 + 0.3);
	float lee = nz(xz * 0.04 + 0.3 + vec2(0.012, 0.0)) - drift;
	c = mix(c, c * vec3(0.8, 0.88, 1.0), smoothstep(0.42, 0.8, drift) * 0.6 * strength);
	c *= 1.0 + clamp(lee * 30.0, -0.08, 0.08) * strength;
	// wind ripples
	float ripple = sin(dot(xz, vec2(0.6, 0.8)) * 4.5 + nz(xz * 0.12) * 8.0);
	c *= 1.0 + 0.05 * ripple * detail(xz * 4.5) * strength;
	// grass poking through, and a few stones
	float pick;
	float sh;
	float tuft = tufts(xz + 0.8, 3.0, 0.14, 0.38, sh);
	c = mix(c, vec3(0.32, 0.42, 0.3) * mix(0.75, 1.25, sh), tuft * 0.8 * strength);
	float st = dots(xz + 5.0, 1.8, 0.12, 0.18, pick);
	c = mix(c, vec3(0.45, 0.47, 0.52) * mix(0.8, 1.1, pick), st * 0.7 * strength);
	// sparkle
	vec2 g = xz * 26.0;
	c += vec3(0.35) * step(0.988, hash(floor(g))) * detail(g) * strength;
	return c;
}

vec3 leaf_top(vec3 c, vec2 xz) {
	c = grass_top(c, xz) * 0.96;
	float pick;
	float along;
	float l = strokes(xz + 1.7, 5.0, 0.6, 1.2, 0.5, pick, along);
	vec3 leaf = pick < 0.25 ? vec3(0.8, 0.24, 0.1) : (pick < 0.5 ? vec3(0.92, 0.58, 0.14) : (pick < 0.75 ? vec3(0.62, 0.3, 0.12) : vec3(0.9, 0.78, 0.3)));
	c = mix(c, leaf * mix(0.85, 1.1, along), l * 0.9 * strength);
	float l2 = strokes(xz + 4.2, 8.0, 0.45, 1.2, 0.5, pick, along);
	c = mix(c, c * vec3(1.15, 0.85, 0.6), l2 * 0.6 * strength);
	return c;
}

vec3 marsh_top(vec3 c, vec2 xz) {
	c = grass_top(c, xz);
	float damp = nz(xz * 0.06 + 0.7);
	c = mix(c, c * vec3(0.78, 0.88, 0.86), smoothstep(0.55, 0.8, damp) * 0.6 * strength);
	// small puddles
	float pick;
	float pud = dots(xz + 2.2, 0.9, 0.25, 0.32, pick);
	c = mix(c, vec3(0.32, 0.45, 0.5), pud * smoothstep(0.5, 0.7, damp) * 0.85 * strength);
	// reeds
	float sh;
	float reed = tufts(xz + 6.1, 2.5, 0.3, 0.6, sh);
	c = mix(c, vec3(0.42, 0.48, 0.28) * mix(0.65, 1.25, sh), reed * 0.75 * strength);
	return c;
}

// earth sides: strata, rock showing through, stones and cracks
vec3 earth(vec3 c, vec3 p, vec3 n) {
	float u = dot(p.xz, normalize(vec2(-n.z, n.x) + vec2(1e-4)));   // runs round the hex
	float warp = nz(vec2(u * 0.12, p.y * 0.3));
	float strata = sin(p.y * 12.0 + warp * 7.0);
	c *= 1.0 + 0.1 * strata * detail(vec2(p.y * 12.0)) * strength;
	float rock = smoothstep(0.55, 0.75, nz(vec2(u * 0.18, p.y * 0.45) + 0.5));
	float lum = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(lum) * vec3(1.0, 0.98, 0.95) * 1.15, rock * 0.5 * strength);
	float h = nz(vec2(u * 0.25, p.y * 0.08) + 0.2);
	float crack = 1.0 - smoothstep(0.0, 0.01, abs(h - 0.5));
	c *= 1.0 - 0.25 * crack * detail(vec2(u, p.y) * 4.0) * strength;
	// embedded stones: grey, lit from above
	vec2 g = vec2(u, p.y) * 6.0;
	vec2 id = floor(g);
	vec2 f = fract(g) - 0.5 - (vec2(hash(id + 1.0), hash(id + 4.0)) - 0.5) * 0.4;
	float st = step(0.82, hash(id)) * (1.0 - smoothstep(0.18, 0.28, length(f * vec2(1.0, 1.4)))) * detail(g);
	vec3 stone = vec3(0.56, 0.54, 0.52) * (1.0 + f.y * 0.8);
	c = mix(c, stone, st * 0.85 * strength);
	return c;
}

void fragment() {
	vec3 inst = use_instance_color ? COLOR.rgb : vec3(1.0);
	vec3 base = texture(atlas, UV).rgb * inst;
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
		vec3 side = base;
		if (up < 1.0) {
			// how far down the side this is (0 at the top edge), and the pack's dirt there
			float sv = clamp((UV.y - SIDE_V.x) / (SIDE_V.y - SIDE_V.x), 0.0, 1.0);
			vec3 dirt = texture(atlas, vec2(DIRT_U, mix(DIRT_V.x, DIRT_V.y, sv))).rgb * inst;
			side = earth(dirt, wpos, wnrm);
			// the top's surface lips over the edge, wavy
			float u = dot(wpos.xz, normalize(vec2(-wnrm.z, wnrm.x) + vec2(1e-4)));
			float edge = 0.12 + (nz(vec2(u * 0.35, 0.5)) - 0.5) * 0.14 + (hash(vec2(floor(u * 14.0), 3.0)) - 0.5) * 0.05;
			float lip = 1.0 - smoothstep(edge - 0.02, edge + 0.02, sv);
			vec3 lip_col = base * (style == 1 ? 1.0 : 0.92);
			side = mix(side, lip_col, lip);
			// a soft shadow just under the lip
			side *= 1.0 - 0.18 * (1.0 - smoothstep(edge, edge + 0.12, sv)) * (1.0 - lip);
		}
		c = mix(side, top, up);
	} else if (row == 2 && col == 3 && up > 0.0) {
		// road: packed earth with gravel
		float pick;
		float s = dots(xz, 9.0, 0.35, 0.22, pick);
		c *= mix(0.92, 1.06, nz(xz * 0.2));
		c = mix(c, c * mix(0.78, 1.2, pick), s * up * strength);
	} else if (row == 2 && col == 4 && up > 0.0) {
		// shore sand: wind ripples and grain
		float ripple = sin(dot(xz, vec2(0.8, 0.6)) * 6.0 + nz(xz * 0.15) * 6.0);
		c *= 1.0 + 0.06 * ripple * detail(xz * 6.0) * strength;
		vec2 g = xz * 22.0;
		c *= 1.0 + (hash(floor(g)) - 0.5) * 0.14 * detail(g) * strength;
	}
	ALBEDO = c;
	ROUGHNESS = rough;
}
