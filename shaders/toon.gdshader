shader_type spatial;

uniform vec3 albedo : source_color = vec3(1.0);

void fragment() {
	ALBEDO = albedo;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float lit = step(0.0, ndl) * step(0.5, ATTENUATION);
	float band = mix(0.55, ndl > 0.55 ? 1.0 : 0.82, lit);
	DIFFUSE_LIGHT += LIGHT_COLOR * band / PI;
}
