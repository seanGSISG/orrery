// The sky of the Ascent climb: the panoramas of two sky presets (SkyPreset), blended.
// AscentSky sets `blend` from the marble's height. Each panorama has the energy of its preset.
shader_type sky;

uniform sampler2D from_panorama : filter_linear, source_color, hint_default_black;
uniform sampler2D to_panorama : filter_linear, source_color, hint_default_black;
uniform float from_energy = 1.0;
uniform float to_energy = 1.0;
// 0 shows from_panorama, 1 shows to_panorama.
uniform float blend : hint_range(0.0, 1.0) = 0.0;

void sky() {
	vec3 from = texture(from_panorama, SKY_COORDS).rgb * from_energy;
	vec3 to = texture(to_panorama, SKY_COORDS).rgb * to_energy;
	COLOR = mix(from, to, blend);
}
