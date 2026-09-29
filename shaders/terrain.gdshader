shader_type spatial;
render_mode cull_back, diffuse_burley;
// Painted terrain: world-space grass/dirt on flat faces and rock on steep faces.
// On Kenney tiles the original palette color decides dirt (road) vs grass (verge).

uniform sampler2D palette : source_color, filter_nearest;
uniform bool use_palette = true;
uniform bool dirt_top = false;
uniform bool dirt_from_uv = false;   // hex terrain: UV.x = 1 on road / lake-bed tops
uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D dirt_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cliff_tex : source_color, filter_linear_mipmap, repeat_enable;
// hex terrain extras: UV2.x = sand (shores, lake beds), UV2.y = flagstone (the castle plaza)
uniform bool has_extra = false;
uniform sampler2D sand_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D stone_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float tex_scale = 0.16;
uniform vec3 grass_tint : source_color = vec3(1.0);
// stylized hex terrain: calm base colors, the painted textures only as light detail, banded rock faces
uniform bool stylized = false;
uniform vec3 grass_base : source_color = vec3(0.43, 0.63, 0.27);
uniform vec3 rock_base : source_color = vec3(0.58, 0.53, 0.47);
uniform float detail = 0.35;
uniform vec3 backdrop_col : source_color = vec3(0.41, 0.52, 0.33);   // plain grass, about half the map's saturation
// the board's outer walls (below tile level, down to the grass): a pale stone lip over banded earth
uniform vec3 edge_lip : source_color = vec3(0.6, 0.56, 0.48);
uniform vec3 edge_soil : source_color = vec3(0.4, 0.3, 0.21);
uniform float edge_depth = 1.6;
uniform bool all_backdrop = false;   // the ground beyond the map edge
// spotlight: light pools on your tiles; the backdrop beyond fades into dark diagonal stripes
uniform bool spot_on = false;
uniform sampler2D spot_mask : filter_linear, repeat_disable;
uniform float spot_ext = 90.0;
uniform float spot_dark = 0.66;
uniform vec3 spot_col = vec3(0.05, 0.06, 0.09);

varying vec3 w_pos;
varying vec3 w_nrm;
varying vec4 v_col;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize(MODEL_NORMAL_MATRIX * NORMAL);
	v_col = COLOR;
}

float hash2(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash2(i);
	float b = hash2(i + vec2(1.0, 0.0));
	float c = hash2(i + vec2(0.0, 1.0));
	float d = hash2(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

vec3 tiled(sampler2D t, vec2 p) {
	// two scales blended to hide repetition
	return mix(texture(t, p).rgb, texture(t, p * 0.37 + vec2(0.31, 0.17)).rgb, 0.35);
}

void fragment() {
	float dirt = dirt_top ? 1.0 : 0.0;
	if (dirt_from_uv) {
		dirt = UV.x;
	}
	if (use_palette) {
		vec3 base = texture(palette, UV).rgb;
		dirt = smoothstep(-0.02, 0.1, base.r - base.g);
	}
	vec2 p = w_pos.xz * tex_scale;
	vec3 grass = tiled(grass_tex, p) * grass_tint;
	if (stylized) {
		float patch = vnoise(w_pos.xz * 0.06) * 0.65 + vnoise(w_pos.xz * 0.21) * 0.35;
		vec3 calm = grass_base * grass_tint * mix(0.86, 1.12, patch);
		grass = mix(calm, grass, detail);
	}
	vec3 top = mix(grass, tiled(dirt_tex, p), dirt);
	if (has_extra) {
		top = mix(top, tiled(sand_tex, p * 0.8), UV2.x);
		top = mix(top, tiled(stone_tex, p * 1.2), UV2.y);
	}
	vec3 cx = texture(cliff_tex, w_pos.zy * tex_scale * 1.3).rgb;
	vec3 cz = texture(cliff_tex, w_pos.xy * tex_scale * 1.3).rgb;
	vec3 side = mix(cz, cx, abs(w_nrm.x));
	if (stylized) {
		float band = sin(w_pos.y * 6.5 + vnoise(w_pos.xz * 0.35) * 4.0);
		side = mix(rock_base, side, 0.35) * (0.92 + 0.08 * band);
		if (w_pos.y < 0.02) {
			// the raised board's edge: stone lip, then earth strata darkening toward the grass
			float d = clamp(-w_pos.y / edge_depth, 0.0, 1.0);
			float strata = 0.9 + 0.1 * sin(w_pos.y * 13.0 + vnoise(w_pos.xz * 0.5) * 3.0);
			vec3 earth = edge_soil * strata * mix(1.05, 0.7, d);
			side = mix(edge_lip, earth, smoothstep(0.1, 0.2, -w_pos.y));
		}
	}
	float steep = 1.0 - smoothstep(0.55, 0.8, abs(w_nrm.y));
	vec3 col = mix(top, side, steep);
	if (stylized && (v_col.a < 0.5 || all_backdrop)) {
		// the grass outside your tiles: plain, muted and a little darker, shaded by three octaves of value noise
		// (no texture, so nothing repeats)
		float broad = vnoise(w_pos.xz * 0.012);
		float n = broad * 0.5 + vnoise(w_pos.xz * 0.045) * 0.3 + vnoise(w_pos.xz * 0.19) * 0.2;
		col = backdrop_col * grass_tint * mix(0.88, 1.07, n);
		col = mix(col, col * vec3(1.06, 1.03, 0.88), smoothstep(0.45, 0.8, broad) * 0.6);   // sun-dried patches
		if (spot_on) {
			vec2 suv = (w_pos.xz + vec2(spot_ext)) / (2.0 * spot_ext);
			float m = 1.0;
			if (suv.x >= 0.0 && suv.y >= 0.0 && suv.x <= 1.0 && suv.y <= 1.0) {
				m = texture(spot_mask, suv).a / max(spot_dark, 0.01);
			} else {
				col = mix(col, spot_col, spot_dark);   // past the decal: keep the dark going
			}
		}
	}
	ALBEDO = col * v_col.rgb;
	ROUGHNESS = 0.95;
	SPECULAR = 0.2;
}
