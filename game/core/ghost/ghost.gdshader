// Ghost marble look: each part of the marble's skin in one pale colour, see-through and
// brighter at its rim. The shapes inside the skin show the roll, and the real marble stays
// clear behind the ghost. All parts have one colour and write no depth, so the order in
// which they draw does not change the picture.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, unshaded, shadows_disabled;

uniform vec3 color : source_color = vec3(0.5, 0.78, 1.0);
/// How solid a part is where it faces the camera, and how much more at its rim.
uniform float alpha : hint_range(0.0, 1.0) = 0.22;
uniform float rim_alpha : hint_range(0.0, 1.0) = 0.55;

void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALBEDO = color;
	ALPHA = clamp(alpha + rim * rim_alpha, 0.0, 1.0);
}
