// The shadow of a far house on the land (kit/town.py `ground_shadow`): a flat shape just above
// the ground that darkens what is under it by `strength`. Far scenery casts no real shadow (the
// sun's shadow map is too coarse that far out), so the level script draws each shadow from the
// sun of its sky. It is unshaded black with alpha, so the haze fades it like the ground under
// it. The stencil lets each pixel take one shadow only, so two shadows that overlap do not
// darken twice. (Godot calls stencil support experimental.)
shader_type spatial;
render_mode blend_mix, unshaded, cull_back, depth_draw_never, shadows_disabled;
stencil_mode read, write, compare_not_equal, 1;

// How much the shadow darkens the land: the share of the sunlight that it takes away.
uniform float strength : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	ALBEDO = vec3(0.0);
	ALPHA = strength;
}
