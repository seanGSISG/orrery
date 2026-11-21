// Ghost marble look: the marble's two-octant pattern in pale blue, see-through, brighter at
// the rim, so that the roll shows and the real marble stays clear behind it.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, unshaded, shadows_disabled;

uniform vec3 color_a : source_color = vec3(0.7, 0.9, 1.0);
uniform vec3 color_b : source_color = vec3(0.3, 0.55, 0.95);
uniform float alpha : hint_range(0.0, 1.0) = 0.35;

varying vec3 local;

void vertex() {
	local = VERTEX;
}

void fragment() {
	float side = step(0.0, local.x) + step(0.0, local.y) + step(0.0, local.z);
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALBEDO = mix(color_a, color_b, mod(side, 2.0)) + rim * 0.4;
	ALPHA = clamp(alpha + rim * 0.4, 0.0, 1.0);
}
