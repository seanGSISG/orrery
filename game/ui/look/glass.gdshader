shader_type canvas_item;
// A frosted glass panel: the frame behind it, blurred, under a tint, with a thin edge line,
// round corners and a soft shadow. GlassPanel draws one rectangle with it: the panel plus
// `margin` on each side for the shadow. Sizes are in canvas units.

uniform sampler2D screen : hint_screen_texture, repeat_disable, filter_linear_mipmap;
uniform vec2 size = vec2(100.0);
uniform float margin = 0.0;
uniform float radius = 34.0;
uniform vec4 tint : source_color = vec4(0.04, 0.06, 0.12, 0.54);
uniform vec4 edge : source_color = vec4(1.0, 1.0, 1.0, 0.24);
// Each step doubles the blur. The value is for a 1080-line frame; larger frames blur more.
uniform float blur = 3.0;
uniform float saturation = 1.5;
uniform float brightness = 0.75;
uniform float shadow = 0.3;

// Signed distance from p to a rounded box of half extents half: negative inside.
float box(vec2 p, vec2 half, float r) {
	vec2 q = abs(p) - half + r;
	return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void fragment() {
	// The alpha of the node's modulate, so that a panel can fade.
	float fade = COLOR.a;
	vec2 p = (UV - 0.5) * (size + 2.0 * margin);
	float d = box(p, size * 0.5, min(radius, min(size.x, size.y) * 0.5));
	float aa = max(fwidth(d), 0.0001);
	float inside = 1.0 - smoothstep(-aa, 0.0, d);

	float lod = max(blur + log2(max(1.0 / (SCREEN_PIXEL_SIZE.y * 1080.0), 0.25)), 0.0);
	vec2 reach = SCREEN_PIXEL_SIZE * exp2(lod) * 0.75;
	vec3 back = textureLod(screen, SCREEN_UV, lod).rgb * 2.0;
	for (int i = 0; i < 8; i++) {
		float turn = float(i) * 0.7853982;
		back += textureLod(screen, SCREEN_UV + vec2(cos(turn), sin(turn)) * reach, lod).rgb;
	}
	back /= 10.0;
	float grey = dot(back, vec3(0.299, 0.587, 0.114));
	back = mix(vec3(grey), back, saturation) * brightness;

	vec3 glass = mix(back, tint.rgb, tint.a);
	// A line just inside the border, brighter at the top, like light on a glass rim.
	float rim = smoothstep(-1.5 - aa, -1.5, d);
	float lift = mix(1.0, 0.5, clamp(p.y / size.y + 0.5, 0.0, 1.0));
	glass = mix(glass, edge.rgb, edge.a * rim * lift);

	// The shadow is black round the panel, and a little stronger below it.
	float cast = shadow * exp(-pow(max(d, 0.0) / max(margin * 0.42, 0.001), 2.0));
	cast *= mix(0.55, 1.0, clamp(p.y / size.y + 0.5, 0.0, 1.0));
	// A tint and an edge with no alpha mean no panel at all.
	float on = step(0.001, tint.a + edge.a);
	float alpha = on * (inside + (1.0 - inside) * cast);
	COLOR = vec4(glass * inside / max(inside + (1.0 - inside) * cast, 0.0001), alpha * fade);
}
