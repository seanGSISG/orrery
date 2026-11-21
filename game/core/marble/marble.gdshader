// Placeholder marble look: two colours in alternate octants, so that the roll shows.
shader_type spatial;

uniform vec3 color_a : source_color = vec3(0.95, 0.62, 0.18);
uniform vec3 color_b : source_color = vec3(0.1, 0.14, 0.3);

varying vec3 local;

void vertex() {
	local = VERTEX;
}

void fragment() {
	float side = step(0.0, local.x) + step(0.0, local.y) + step(0.0, local.z);
	ALBEDO = mix(color_a, color_b, mod(side, 2.0));
	ROUGHNESS = 0.3;
}
