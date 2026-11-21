// Floor look for test levels: a checker of 1 m tiles in world space, so motion shows.
shader_type spatial;

uniform vec3 tile_a : source_color = vec3(0.16, 0.18, 0.24);
uniform vec3 tile_b : source_color = vec3(0.24, 0.27, 0.34);

varying vec3 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float checker = mod(floor(world.x) + floor(world.z), 2.0);
	ALBEDO = mix(tile_a, tile_b, checker);
	ROUGHNESS = 0.9;
}
