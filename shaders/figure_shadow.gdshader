// Soft contact patch under a figure's feet, hidden behind furniture like the figure.
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_disabled;

uniform sampler2D room_depth : filter_nearest, repeat_disable;
uniform vec3 room_origin;
uniform vec3 room_axis;
uniform float depth_span = 16.0;
uniform float strength = 0.38;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 baked = texture(room_depth, SCREEN_UV);
	float v = (round(baked.r * 255.0) * 256.0 + round(baked.g * 255.0)) / 65535.0;
	if (v > 0.0 && dot(wpos - room_origin, room_axis) < (v - 0.5) * depth_span - 0.03) {
		discard;
	}
	ALBEDO = vec3(0.16, 0.11, 0.08);
	ALPHA = strength * smoothstep(1.0, 0.25, length(UV * 2.0 - 1.0));
}
