// A faint vertical light beam above a gem: additive, unshaded, brightest at the bottom and
// soft at its edges. Set the instance parameter `colour`. The mesh is a cylinder `height` m
// tall with its centre at the mesh origin.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

instance uniform vec4 colour : source_color = vec4(1.0);
uniform float height = 30.0;
uniform float strength = 0.2;

varying float rise;

void vertex() {
	rise = clamp(VERTEX.y / height + 0.5, 0.0, 1.0);
}

void fragment() {
	float edge = abs(dot(NORMAL, VIEW));
	ALBEDO = colour.rgb;
	ALPHA = strength * edge * edge * (1.0 - rise);
}
