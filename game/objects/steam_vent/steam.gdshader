// The steam column of a vent (objects/steam_vent): soft at its edges (the facing ratio), it
// fades toward its top and in at its foot, and slow noise drifts up through it, so it reads
// as steam, not as a tube. The mesh is an open cylinder with its centre at the mesh origin; set
// the instance parameter `height` to its height. The sun lights it from every side, as light
// scatters in a cloud, and only where no shadow falls.
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, specular_disabled;

instance uniform float height = 8.0;
uniform vec3 colour : source_color = vec3(0.93, 0.94, 0.95);
// The most opacity, at the foot of the column where it faces the camera.
uniform float strength = 0.5;
// How fast the noise rises, m/s.
uniform float rise_speed = 1.2;

varying vec3 local;

void vertex() {
	local = VERTEX;
}

// Returns a random number from 0 to 1 for a lattice point.
float lattice(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.x + p.y) * p.z);
}

// Value noise from 0 to 1, smooth across the lattice.
float noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(lattice(i), lattice(i + vec3(1.0, 0.0, 0.0)), f.x),
			mix(lattice(i + vec3(0.0, 1.0, 0.0)), lattice(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
		mix(mix(lattice(i + vec3(0.0, 0.0, 1.0)), lattice(i + vec3(1.0, 0.0, 1.0)), f.x),
			mix(lattice(i + vec3(0.0, 1.0, 1.0)), lattice(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),
		f.z);
}

void fragment() {
	float edge = abs(dot(NORMAL, VIEW));
	float rise = clamp(local.y / height + 0.5, 0.0, 1.0);
	vec3 p = local * vec3(1.4, 0.5, 1.4) - vec3(0.0, TIME * rise_speed * 0.5, 0.0);
	float wisps = noise(p) * 0.65 + noise(p * 2.3 + 7.1) * 0.35;
	float foot = smoothstep(0.0, 0.08, rise);
	ALBEDO = colour;
	ALPHA = strength * edge * edge * pow(1.0 - rise, 1.4) * foot * mix(0.35, 1.0, smoothstep(0.2, 0.8, wisps));
	// Light the steam as a cloud, not as a curved face.
	NORMAL = VIEW;
	ROUGHNESS = 1.0;
}

void light() {
	DIFFUSE_LIGHT += ATTENUATION * LIGHT_COLOR / PI;
}
