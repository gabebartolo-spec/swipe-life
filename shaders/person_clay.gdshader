// Tinted clay for modular people (docs/PEOPLE.md §4). The sprite holds neutral clay:
// R = luminance (0.5 = the lit colour itself), G/B = masks picking c2/c3 over c1, A = alpha.
// Raw sprites (face decals) keep their own colours. The stop-motion boil from clay_cutout.gdshader
// is folded in so each piece needs one material.
shader_type canvas_item;

uniform vec3 c1 : source_color = vec3(0.8);
uniform vec3 c2 : source_color = vec3(1.0);
uniform vec3 c3 : source_color = vec3(0.2);
uniform bool raw = false;
uniform float boil_px = 0.9;
uniform float seed = 0.0;
// hair greying (director: gradual from the 40s): 0 none, 1 all grey; an even tint
uniform float grey = 0.0;
uniform vec3 grey_col : source_color = vec3(0.85);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	float step_t = floor(TIME * 12.0) + seed * 17.0;
	vec2 cell = floor(UV / TEXTURE_PIXEL_SIZE / 24.0);
	vec2 jitter = vec2(hash(cell + step_t), hash(cell + step_t + 7.3)) - 0.5;
	vec4 t = texture(TEXTURE, UV + jitter * boil_px * TEXTURE_PIXEL_SIZE * 2.0);
	if (raw) {
		COLOR = t;
	} else {
		vec3 base = mix(mix(c1, c2, t.g), c3, t.b);
		// even tint toward grey: no noise (director: flecks looked horrible)
		base = mix(base, grey_col, grey);
		// highlights fade on dark colours, so black stays black clay instead of turning grey
		float hl = 0.6 * smoothstep(0.05, 0.5, dot(base, vec3(0.299, 0.587, 0.114)));
		float l = t.r;
		vec3 col = l < 0.5 ? base * 2.0 * l : mix(base, vec3(1.0), (l - 0.5) * 2.0 * hl);
		COLOR = vec4(col, t.a);
	}
}
