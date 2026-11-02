// Stop-motion "boil" for flat clay cut-outs: the silhouette and surface shimmer a hair every 1/12 s,
// like plasticine re-touched between frames. Sample offsets stay within ~1 px so edges never tear.
shader_type canvas_item;

uniform float boil_px = 0.9;
uniform float seed = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	float step_t = floor(TIME * 12.0) + seed * 17.0;
	vec2 cell = floor(UV / TEXTURE_PIXEL_SIZE / 24.0);
	vec2 jitter = vec2(hash(cell + step_t), hash(cell + step_t + 7.3)) - 0.5;
	COLOR = texture(TEXTURE, UV + jitter * boil_px * TEXTURE_PIXEL_SIZE * 2.0);
}
