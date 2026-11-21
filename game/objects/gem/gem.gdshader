// The jewel of a gem (docs/style/README.md): cut glass with a colour and a high index of
// refraction. The jewel is opaque to the renderer, so it has crisp edges under every
// anti-aliasing mode and it writes motion vectors. The shader makes the look of glass itself
// (docs/design/visual-quality.md §11):
// - It follows the view ray into the gem: the ray bends at the facet, the facets inside
//   mirror it (total reflection) until it meets one at a steep angle, and there it leaves.
//   `facets` holds the planes of the cut (GemCut). The gem then shows the sky and the level
//   in the direction of the ray that left, in the colour that the path through the glass
//   gave the light. A long path gives a deep colour, a short path a pale one.
// - The engine reads the surroundings. The shader gives it a normal that mirrors the view
//   ray into the direction to show (through TANGENT and NORMAL_MAP, so NORMAL stays the
//   facet's own normal), and the colour as the tint of a metal.
// - The clearcoat layer is the outside of the glass: it mirrors the surroundings in the
//   facet itself, without a colour.
// - light() adds two glints for each light: one where the path inside leaves toward the
//   light, in the gem's colour, and a white one where the facet mirrors the light.
// - Every colour glows with the same luminance, so no gem is dull in a dark place.
// - A pale line marks each edge of the cut and each place where the path inside changes,
//   and a thin bright rim marks the outline at any distance.
// - A gem of a few pixels shows plain facets, glows more, and the sides that face the
//   camera glint as the gem turns.
// Set the instance parameters `colour` and `lightness`. GemCut sets `facets` and `facet_count`.
shader_type spatial;

const int MAX_FACETS = 64;
// The most mirrors inside the gem that the view ray meets before it must leave.
const int BOUNCES = 4;
// Index of refraction.
const float IOR = 2.2;
// The length of a path through the glass, in metres, that gives the light the full colour,
// and the least and the most depth of colour in units of that length.
const float REACH = 0.3;
const vec2 COLOUR_DEPTH = vec2(0.4, 1.3);
// How bright the gem is where the camera looks straight through it: 0 is black.
const float WINDOW = 0.45;
// How much the colour of the light shifts along the path, as a prism shifts it.
const float DISPERSION = 0.15;
// Luminance of the gem's own glow, and how many times more the far gem glows.
const float GLOW = 0.05;
const float FAR_GLOW = 4.0;
// Roughness of the picture that the inside shows, and of the outside of the glass.
const float INSIDE_ROUGHNESS = 0.08;
const float OUTSIDE_ROUGHNESS = 0.1;
// Half width of the pale line on an edge of the cut, in metres.
const float EDGE_WIDTH = 0.0012;
// Width of the bright rim on the outline, in metres and at least in pixels, and its strength.
const float RIM_WIDTH = 0.006;
const float RIM_PIXELS = 1.2;
const float RIM_STRENGTH = 0.3;
// Strength of the glint where the path inside leaves toward a light, and how narrow it is.
const float FIRE_STRENGTH = 2.0;
const float FIRE_POWER = 40.0;
// Strength of the glint where a facet mirrors a light, and how narrow it is.
const float FLASH_STRENGTH = 1.5;
const float FLASH_POWER = 700.0;
// The size of a pixel on the gem, in metres, at which the picture of the inside starts to
// fade into the plain facet, and at which it is gone.
const vec2 PLAIN = vec2(0.006, 0.02);
// Strength of the glint of the far gem's facets whose side faces the camera, and how narrow
// it is. The gem turns, so its sides glint one after the other: the far gem twinkles.
const float FAR_GLINT = 1.0;
const float FAR_GLINT_POWER = 400.0;
const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

instance uniform vec4 colour : source_color = vec4(1.0);
/// How light this gem is against the other gems: 1 gives every colour the same luminance, as
/// on the style board. The colourblind palette sets it from the colour (Palette.gem_lightness),
/// so that its gems keep their steps of lightness.
instance uniform float lightness = 1.0;
/// One plane per facet, in the gem's own space: xyz is the unit normal that points out of the
/// gem, w is the distance of the plane from the origin in metres.
uniform vec4 facets[MAX_FACETS];
uniform int facet_count = 0;

varying vec3 local_position;
varying vec3 local_eye;
varying flat vec3 local_normal;
// From fragment() to light(), in view space.
varying vec3 leave_view;
varying vec3 facet_view;
varying vec3 fire_tint;

void vertex() {
	local_position = VERTEX;
	local_normal = NORMAL;
	local_eye = (inverse(MODELVIEW_MATRIX) * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
}

void fragment() {
	vec3 look = normalize(local_position - local_eye);
	vec3 facet = normalize(local_normal);
	float pixel = max(length(dFdx(local_position)), length(dFdy(local_position)));

	// The distance on this facet to its nearest edge, and to the nearest edge that is part of
	// the gem's outline (the facet behind that edge looks away from the camera).
	float edge = 1.0;
	float outline = 1.0;
	for (int i = 0; i < facet_count; i++) {
		vec3 other = facets[i].xyz;
		float turn = dot(other, facet);
		// A facet with the same or the opposite normal makes no edge on this facet, and its
		// gap would be a division by zero.
		if (abs(turn) < 0.9999) {
			float gap = (facets[i].w - dot(local_position, other)) / sqrt(1.0 - turn * turn);
			edge = min(edge, gap);
			if (dot(other, look) > 0.0) {
				outline = min(outline, gap);
			}
		}
	}

	// The path of the view ray inside the gem. `seam` and `critical` go to zero where the
	// path changes at once: where the ray meets the edge between two facets, and where it
	// starts to leave a facet that mirrored it before.
	vec3 ray = refract(look, facet, 1.0 / IOR);
	vec3 at = local_position;
	vec3 leave = ray;
	float path = 0.0;
	float seam = 1.0;
	float critical = 1.0;
	for (int bounce = 0; bounce < BOUNCES; bounce++) {
		float near = 1000.0;
		float next = 1000.0;
		vec3 wall = facet;
		for (int i = 0; i < facet_count; i++) {
			float along = dot(ray, facets[i].xyz);
			if (along > 0.0001) {
				float t = (facets[i].w - dot(at, facets[i].xyz)) / along;
				if (t < near) {
					next = near;
					near = t;
					wall = facets[i].xyz;
				} else if (t < next) {
					next = t;
				}
			}
		}
		at += ray * near;
		path += near;
		seam = min(seam, next - near);
		float steep = dot(ray, wall);
		// Positive when the ray leaves; negative when the facet mirrors it.
		float leaves = 1.0 - IOR * IOR * (1.0 - steep * steep);
		critical = min(critical, abs(leaves));
		if (leaves > 0.0) {
			leave = refract(ray, -wall, IOR);
			break;
		}
		ray = reflect(ray, wall);
		leave = ray;
	}
	// A line of 1.5 pixels where the path changes at once. It hides the step between the two
	// pictures, which no anti-aliasing mode smooths inside a facet.
	float seam_pixels = seam / max(fwidth(seam), 0.000001);
	float critical_pixels = critical / max(fwidth(critical), 0.000001);
	float line = 1.0 - clamp(min(seam_pixels, critical_pixels) / 1.5, 0.0, 1.0);
	// The far gem shows plain facets: a pattern smaller than a pixel would flicker.
	float plain = smoothstep(PLAIN.x, PLAIN.y, pixel);

	facet_view = NORMAL;
	leave_view = normalize(mat3(VIEW_MATRIX) * (mat3(MODEL_MATRIX) * leave));
	// 1 when the path sends the light of the camera's side back; -1 when the camera looks
	// straight through the gem. A gem is bright where it sends light back and dark where it
	// is a window.
	float back = dot(leave_view, VIEW);
	// The engine shows the surroundings in the direction `shown`. A direction that points
	// away from the camera is mirrored toward it, because the engine's Fresnel term turns
	// a mirror white at a flat angle.
	vec3 shown = back < 0.0 ? leave_view - 2.0 * back * VIEW : leave_view;

	// The glass takes the other colours out of the light along the path.
	vec3 hue = max(colour.rgb / max(max(colour.r, colour.g), max(colour.b, 0.001)), vec3(0.02));
	vec3 tint = pow(hue, vec3(clamp(path / REACH, COLOUR_DEPTH.x, COLOUR_DEPTH.y)));
	tint *= 1.0 + DISPERSION * cos(TAU * (path * 9.0 + vec3(0.0, 0.33, 0.67)));
	tint *= mix(WINDOW, 1.0, smoothstep(-0.5, 0.5, back));
	tint = mix(tint, pow(hue, vec3(0.9)), plain);
	tint = min(tint * lightness, vec3(1.0));
	// The glint of the path inside goes with the picture of the inside: none on the far gem.
	fire_tint = tint * (1.0 - plain);
	// The outside of the glass mirrors more at a flat angle.
	float f0 = pow((IOR - 1.0) / (IOR + 1.0), 2.0);
	float shine = f0 + (1.0 - f0) * pow(1.0 - clamp(dot(facet_view, VIEW), 0.0, 1.0), 5.0);
	float inside = (1.0 - max(line, plain)) * (1.0 - shine);
	vec3 pale = mix(hue, vec3(1.0), 0.5);
	float edge_line = (1.0 - smoothstep(EDGE_WIDTH - pixel, EDGE_WIDTH + pixel, edge)) * clamp(2.0 * EDGE_WIDTH / pixel, 0.0, 1.0);
	float rim = 1.0 - smoothstep(0.0, max(RIM_WIDTH, RIM_PIXELS * pixel), outline);
	// The sides of the far gem that face the camera glint, whatever their tilt up or down.
	float faces = max(dot(facet, -look), 0.0);
	float turned = dot(normalize(facet.xz + vec2(0.00001)), normalize(-look.xz + vec2(0.00001)));
	float glint = pow(max(turned, 0.0), FAR_GLINT_POWER) * faces * faces * step(0.2, length(facet.xz)) * FAR_GLINT * plain;

	ALBEDO = mix(mix(tint, vec3(1.0), shine), pale, max(0.3 * line * (1.0 - plain), 0.7 * edge_line));
	METALLIC = 1.0;
	ROUGHNESS = INSIDE_ROUGHNESS;
	TANGENT = normalize(mix(facet_view, normalize(shown + VIEW), inside));
	NORMAL_MAP = vec3(1.0, 0.5, 0.0);
	NORMAL_MAP_DEPTH = 1.0;
	CLEARCOAT = 1.0;
	CLEARCOAT_ROUGHNESS = OUTSIDE_ROUGHNESS;
	vec3 own = colour.rgb / max(dot(colour.rgb, LUMA), 0.02);
	float depth_glow = mix(0.5, 1.5, clamp(path / REACH * 0.4, 0.0, 1.0));
	EMISSION = own * GLOW * lightness * mix(depth_glow, FAR_GLOW, plain) + pale * (rim * rim * RIM_STRENGTH + glint);
}

void light() {
	float fire = pow(max(dot(leave_view, LIGHT), 0.0), FIRE_POWER) * FIRE_STRENGTH;
	float flash = pow(max(dot(reflect(-VIEW, facet_view), LIGHT), 0.0), FLASH_POWER) * FLASH_STRENGTH;
	SPECULAR_LIGHT += LIGHT_COLOR * ATTENUATION * (fire_tint * fire + vec3(flash)) / PI;
}
