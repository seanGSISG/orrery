// Glass of marble A (docs/style/README.md): clear glass with a pale cool tint and a strong
// rim, around the brass core. Put it on a sphere around the core. It draws after the opaque
// objects and reads the frame behind it (docs/design/visual-quality.md §5):
// - Where the core is behind the glass, it shows the core as it is, so the core stays crisp.
// - Elsewhere it shows the world the way a solid glass ball does, upside down and small: it
//   follows the view ray through the ball and reads the frame where that ray points, on the
//   far side of the marble's outline.
// The engine adds the reflections of the sky, the probes and the sun. The rim is darker and
// cooler than the middle, so the marble shows on pale stone and on a bright sky.
shader_type spatial;

uniform sampler2D frame : hint_screen_texture, repeat_disable, filter_linear_mipmap;
uniform sampler2D frame_depth : hint_depth_texture, repeat_disable, filter_nearest;
/// Colour of the light that passes through the glass.
uniform vec3 tint : source_color = vec3(0.88, 0.96, 1.0);
/// Index of refraction.
uniform float ior : hint_range(1.0, 2.5) = 1.65;
/// How far behind the marble the bent view reads the frame, in marble radii.
uniform float reach : hint_range(1.0, 20.0) = 5.0;
/// Extra mipmap levels of the frame in the bent view; they soften the small picture.
uniform float blur : hint_range(0.0, 4.0) = 0.5;
/// Colour of the light that passes through the rim.
uniform vec3 rim_tint : source_color = vec3(0.25, 0.42, 0.62);
/// How close to the outline the rim stays: a higher value gives a thinner rim.
uniform float rim_power : hint_range(1.0, 16.0) = 6.0;
/// Width of the dark line at the outline: 1 is the radius of the marble on the frame.
uniform float outline_width : hint_range(0.0, 0.5) = 0.08;
uniform float roughness : hint_range(0.0, 1.0) = 0.05;

// Returns the frame position (0..1) of a point in view space.
vec2 on_frame(mat4 projection, vec3 point) {
	vec4 clip = projection * vec4(point, 1.0);
	return clip.xy / clip.w * 0.5 + 0.5;
}

void fragment() {
	vec3 centre = NODE_POSITION_VIEW;
	vec3 normal = normalize(NORMAL);
	vec3 ray = normalize(VERTEX);
	float ball = distance(VERTEX, centre);
	float facing = clamp(dot(normal, -ray), 0.0, 1.0);

	// The view ray bends into the ball, crosses it and bends out again.
	vec3 inside = refract(ray, normal, 1.0 / ior);
	vec3 leave = VERTEX + inside * (2.0 * ball * dot(inside, -normal));
	vec3 beyond = refract(inside, normalize(centre - leave), ior);
	// The bent ray points to the far side of the centre. Read the frame there, one outline
	// further out: inside the marble's own outline the frame holds the core, not the world.
	vec2 middle = on_frame(PROJECTION_MATRIX, centre);
	vec2 bent = on_frame(PROJECTION_MATRIX, leave + beyond * (reach * ball));
	vec2 here = (SCREEN_UV - middle) * VIEWPORT_SIZE;
	float outline = ball * abs(PROJECTION_MATRIX[1][1]) / -centre.z * 0.5 * VIEWPORT_SIZE.y;
	float far = length((bent - middle) * VIEWPORT_SIZE) + outline * 1.15;
	vec2 at = middle - here / max(length(here), 0.001) * far / VIEWPORT_SIZE;
	vec3 seen = texture(frame, at, blur).rgb;

	// The opaque point behind this pixel: a point inside the ball belongs to the core.
	float depth = textureLod(frame_depth, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	if (distance(behind.xyz / behind.w, centre) < ball * 0.98) {
		seen = textureLod(frame, SCREEN_UV, 0.0).rgb;
	}

	// Glass reflects more and passes less toward the outline. The outline itself is a thin
	// dark line with no reflection, so a bright sky behind the marble does not hide it.
	float f0 = pow((ior - 1.0) / (ior + 1.0), 2.0);
	float mirror = f0 + (1.0 - f0) * pow(1.0 - facing, 5.0);
	float edge = sqrt(1.0 - facing * facing);
	float line = smoothstep(1.0 - outline_width, 1.0, edge);
	ALBEDO = vec3(0.0);
	ROUGHNESS = roughness;
	// The engine's F0 is 0.16 × SPECULAR².
	SPECULAR = sqrt(f0 / 0.16) * (1.0 - line);
	EMISSION = seen * mix(tint, rim_tint, pow(edge, rim_power)) * (1.0 - mirror * (1.0 - line)) * EXPOSURE;
}
