// The sky of the Ascent climb: the panoramas of the two sky presets (SkyPreset) round the
// marble's height, blended. AscentSky sets them and `blend` from the height. Each panorama has
// the energy of its preset.
shader_type sky;

// Below the horizon the blend is blend^LAND_HOLD, so the land of the lower sky stays longer.
// The ground dawn has dim land below the horizon and noon a bright cloud layer: blended
// evenly, the clouds would hide the land as soon as the climb leaves the ground.
const float LAND_HOLD = 3.0;
// The two blends meet over this band round the horizon, in the sine of the elevation.
const float HORIZON_BAND = 0.05;

uniform sampler2D from_panorama : filter_linear, source_color, hint_default_black;
uniform sampler2D to_panorama : filter_linear, source_color, hint_default_black;
uniform float from_energy = 1.0;
uniform float to_energy = 1.0;
// 0 shows from_panorama, 1 shows to_panorama.
uniform float blend : hint_range(0.0, 1.0) = 0.0;

void sky() {
	vec3 from = texture(from_panorama, SKY_COORDS).rgb * from_energy;
	vec3 to = texture(to_panorama, SKY_COORDS).rgb * to_energy;
	float below = 1.0 - smoothstep(-HORIZON_BAND, 0.0, EYEDIR.y);
	COLOR = mix(from, to, mix(blend, pow(blend, LAND_HOLD), below));
}
