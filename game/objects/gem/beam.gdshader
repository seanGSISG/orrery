// A faint vertical light beam above a gem or on the finish: additive, unshaded, brightest at
// the bottom and soft at its edges. Set the instance parameter `colour`. The mesh is a
// cylinder `height` m tall with its centre at the mesh origin.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

instance uniform vec4 colour : source_color = vec4(1.0);
uniform float height = 30.0;
uniform float strength = 0.2;
/// How fast the beam fades toward its top: 1 fades evenly, more keeps the light low.
uniform float fade = 1.0;
/// The least width of the beam on screen, as a share of the height of the view. It keeps a
/// thin beam visible from far away. 0 turns it off.
uniform float min_width = 0.0;
/// The share of the height over which the beam fades in at its bottom. 0 starts it at once.
uniform float soft_start = 0.0;

varying float rise;

void vertex() {
	rise = clamp(VERTEX.y / height + 0.5, 0.0, 1.0);
	float radius = length(VERTEX.xz);
	float depth = -(MODELVIEW_MATRIX * vec4(0.0, VERTEX.y, 0.0, 1.0)).z;
	// Metres that min_width covers at this depth.
	float least = min_width * depth / PROJECTION_MATRIX[1][1];
	VERTEX.xz *= max(radius, least) / max(radius, 0.00001);
}

void fragment() {
	float edge = abs(dot(NORMAL, VIEW));
	ALBEDO = colour.rgb;
	// Defined for soft_start = 0 too: smoothstep() is not, when its two edges are equal.
	float begun = clamp(rise / max(soft_start, 0.00001), 0.0, 1.0);
	ALPHA = strength * edge * edge * pow(1.0 - rise, fade) * begun * begun * (3.0 - 2.0 * begun);
}
