shader_type spatial;
// Window glass (docs/design/visual-quality.md §6): a near-white tint, and the colour comes from
// what shows through. The blend is premultiplied: the light that the glass scatters is scaled by
// its opacity, but its reflection is not, so a pane over a dark room still mirrors the sky.
render_mode blend_premul_alpha, depth_draw_opaque, cull_back;

uniform vec3 tint : source_color = vec3(0.9, 0.93, 0.94);
uniform float opacity : hint_range(0.0, 1.0) = 0.05;
uniform float roughness : hint_range(0.0, 1.0) = 0.04;

void fragment() {
	ALBEDO = tint * opacity;
	ALPHA = opacity;
	ROUGHNESS = roughness;
	METALLIC = 0.0;
}
