// Writes distance toward the camera from the room's centre plane, for tools/godot/render_house.gd depth.
// figure_clay.gdshader compares against it so furniture hides figures.
shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec3 origin;
uniform vec3 axis;
uniform float span = 16.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float v = dot(wpos - origin, axis) / span + 0.5;
	ALBEDO = vec3(v);
}
