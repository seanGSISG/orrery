shader_type canvas_item;
// The ground of a menu: the frame behind it, blurred and darkened toward the night colour.
// Wash draws one full-screen rectangle with it.

uniform sampler2D screen : hint_screen_texture, repeat_disable, filter_linear_mipmap;
uniform vec4 night : source_color = vec4(0.024, 0.039, 0.078, 1.0);
// Each step doubles the blur. The value is for a 1080-line frame; larger frames blur more.
uniform float blur = 4.0;
// How much night covers the frame: x at the lightest place, y at the darkest.
uniform vec2 dim = vec2(0.5, 0.82);
// 0: lightest in the centre, darkest at the rim. 1: darkest at the left edge, for a menu
// that sits on the left.
uniform float left = 0.0;

void fragment() {
	float lod = max(blur + log2(max(1.0 / (SCREEN_PIXEL_SIZE.y * 1080.0), 0.25)), 0.0);
	vec2 reach = SCREEN_PIXEL_SIZE * exp2(lod) * 0.75;
	vec3 back = textureLod(screen, SCREEN_UV, lod).rgb * 2.0;
	for (int i = 0; i < 8; i++) {
		float turn = float(i) * 0.7853982;
		back += textureLod(screen, SCREEN_UV + vec2(cos(turn), sin(turn)) * reach, lod).rgb;
	}
	back /= 10.0;

	float round_cover = mix(dim.x, dim.y, clamp(length((UV - 0.5) / 0.6), 0.0, 1.0));
	// From the left edge: dark, lightest near the middle, then a little darker again.
	float near = mix(dim.y, dim.x, smoothstep(0.0, 0.5, UV.x));
	float side_cover = mix(near, mix(dim.x, dim.y, 0.35), smoothstep(0.5, 1.0, UV.x));
	float cover = mix(round_cover, side_cover, left);
	COLOR = vec4(mix(back, night.rgb, cover), 1.0);
}
