// Clay / plasticine look (art test, GDD §10.4): lumpy boiling surface, fingerprint bump,
// wrapped diffuse as a cheap stand-in for subsurface scattering, soft sheen and rim.
shader_type spatial;

uniform vec3 albedo : source_color = vec3(0.8);
uniform float emission = 0.0;
// Blender-baked props: colour and AO come from the mesh's vertex colours.
uniform bool use_vertex_color = false;
// 1 = darken near the floor (fake contact AO; Mobile renderer has no SSAO).
uniform float contact_ao = 1.0;
uniform float lump = 0.012;
uniform float bump = 1.0;
// Stop-motion boil: surface noise jumps at this rate (12 fps = animated on twos).
uniform float boil_fps = 12.0;

varying vec3 wpos;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x),
			mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
			mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y),
		f.z);
}

void vertex() {
	float step_t = floor(TIME * boil_fps);
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX += NORMAL * (noise(w * 2.5 + vec3(step_t * 3.17)) - 0.5) * 2.0 * lump;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float step_t = floor(TIME * boil_fps);
	vec3 p = wpos * 7.0 + vec3(step_t * 1.31);
	float h = noise(p) * 0.6 + noise(p * 2.3) * 0.3;
	// Fingerprint patches: ridged rings where a low-frequency mask is high.
	float mask = smoothstep(0.55, 0.75, noise(wpos * 1.3 + vec3(7.0)));
	h += mask * sin(noise(wpos * 3.0) * 40.0) * 0.12;
	h *= bump * 0.02;
	// Bump from screen-space derivatives (no tangents needed).
	vec3 dpdx = dFdx(VERTEX);
	vec3 dpdy = dFdy(VERTEX);
	float dhx = dFdx(h);
	float dhy = dFdy(h);
	vec3 r1 = cross(dpdy, NORMAL);
	vec3 r2 = cross(NORMAL, dpdx);
	float det = dot(dpdx, r1);
	NORMAL = normalize(abs(det) * NORMAL - sign(det) * (dhx * r1 + dhy * r2));

	float ao = mix(1.0, mix(0.72, 1.0, smoothstep(0.0, 0.45, wpos.y)), contact_ao);
	vec3 base = use_vertex_color ? albedo * COLOR.rgb : albedo;
	ALBEDO = base * (0.94 + 0.12 * noise(wpos * 1.7)) * ao;
	EMISSION = base * emission;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float wrap = clamp((ndl + 0.45) / 1.45, 0.0, 1.0);
	float shade = LIGHT_IS_DIRECTIONAL ? mix(0.4, 1.0, ATTENUATION) : ATTENUATION;
	DIFFUSE_LIGHT += LIGHT_COLOR * wrap * shade / PI;
	float rim = pow(1.0 - max(dot(NORMAL, VIEW), 0.0), 3.0);
	DIFFUSE_LIGHT += LIGHT_COLOR * rim * 0.12 * wrap * shade / PI;
	vec3 hv = normalize(LIGHT + VIEW);
	SPECULAR_LIGHT += LIGHT_COLOR * pow(max(dot(NORMAL, hv), 0.0), 12.0) * 0.05 * shade / PI;
}
