shader_type spatial;
render_mode unshaded, cull_front;

uniform vec3 ink : source_color = vec3(0.17, 0.125, 0.14);
uniform float width = 0.035;

void vertex() {
	VERTEX += normalize(VERTEX) * width;
}

void fragment() {
	ALBEDO = ink;
}
