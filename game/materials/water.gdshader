shader_type spatial;
// Still water (water.tres): a dark green body that lets the floor show through, the 2%
// reflection of water (IOR 1.33), and slow ripples that tilt the surface a little, so the
// sky's reflection breaks up as on real water. The blend is premultiplied, as in glass.gdshader:
// the reflection is not scaled by the opacity.
render_mode blend_premul_alpha, depth_draw_opaque, cull_back;

uniform vec3 tint : source_color = vec3(0.16, 0.22, 0.2);
uniform float opacity : hint_range(0.0, 1.0) = 0.45;
uniform float roughness : hint_range(0.0, 1.0) = 0.05;
// Godot's SPECULAR: 0.35 reflects 2% head-on.
uniform float specular : hint_range(0.0, 1.0) = 0.35;
// The largest tilt of the surface, as a slope.
uniform float ripple = 0.06;

varying vec3 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world.xz;
	// Three slow waves, 0.6 to 1.1 m long, across one another.
	vec2 slope = vec2(0.0);
	slope += vec2(5.7, 2.1) * cos(dot(p, vec2(5.7, 2.1)) + TIME * 1.1);
	slope += vec2(-3.2, 6.4) * cos(dot(p, vec2(-3.2, 6.4)) + TIME * 1.4);
	slope += vec2(9.1, -4.3) * cos(dot(p, vec2(9.1, -4.3)) + TIME * 1.7) * 0.5;
	slope *= ripple / 9.0;
	vec3 up = vec3(-slope.x, 1.0, -slope.y);
	NORMAL = normalize((VIEW_MATRIX * vec4(up, 0.0)).xyz);
	ALBEDO = tint * opacity;
	ALPHA = opacity;
	ROUGHNESS = roughness;
	METALLIC = 0.0;
	SPECULAR = specular;
}
