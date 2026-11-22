shader_type spatial;
// Open country (objects/land): grass at its true size, and past `meadow` m from the object a
// patchwork of fields with dark hedges between them. Each field is a cell of a jittered grid,
// with its own crop colour. The grass texture is read at two sizes, so it shows no repeat.

uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// Metres that one repeat of the grass texture covers: its true size.
uniform float tile = 1.4;
// The radius of plain meadow round the object, m; the fields start past it.
uniform float meadow = 90.0;
// The mean width of a field, and of a hedge, m.
uniform float field_size = 110.0;
uniform float hedge_width = 2.0;

// Albedo limits in linear light (docs/design/visual-quality.md §6): sRGB 30 and 240.
const float ALBEDO_MIN = 0.013;
const float ALBEDO_MAX = 0.871;
// Crop colours, as factors on the grass texture in linear light: meadow, young wheat,
// stubble, ploughed earth, pasture and hay.
const vec3 CROPS[6] = vec3[6](
	vec3(0.85, 0.85, 1.1),
	vec3(1.25, 1.1, 1.2),
	vec3(2.0, 1.3, 2.1),
	vec3(0.8, 0.45, 1.0),
	vec3(0.55, 0.65, 0.85),
	vec3(1.6, 1.3, 1.5)
);
const vec3 HEDGE = vec3(0.35, 0.5, 0.6);

varying vec3 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// Returns two random numbers from 0 to 1 for a grid cell.
vec2 cell_random(vec2 cell) {
	vec2 p = vec2(dot(cell, vec2(127.1, 311.7)), dot(cell, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}

void fragment() {
	vec2 p = world.xz;
	vec2 dx = dFdx(p);
	vec2 dy = dFdy(p);
	vec3 grass = textureGrad(albedo_map, p / tile, dx / tile, dy / tile).rgb;
	float wide = tile * 6.3;
	grass = mix(grass, textureGrad(albedo_map, p / wide + 0.37, dx / wide, dy / wide).rgb, 0.4);
	// The field of this point: the nearest jittered cell centre. The hedge is where the
	// second nearest centre is almost as near.
	vec2 at = p / field_size;
	vec2 base = floor(at);
	float nearest = 8.0;
	float second = 8.0;
	vec2 field = base;
	for (int j = -1; j <= 1; j++) {
		for (int i = -1; i <= 1; i++) {
			vec2 cell = base + vec2(float(i), float(j));
			float d = length(at - cell - 0.15 - 0.7 * cell_random(cell));
			if (d < nearest) {
				second = nearest;
				nearest = d;
				field = cell;
			} else if (d < second) {
				second = d;
			}
		}
	}
	float border = (second - nearest) * 0.5 * field_size;
	float fields = smoothstep(meadow, meadow * 1.4, length(p - MODEL_MATRIX[3].xz));
	vec3 crop = CROPS[int(cell_random(field + 7.1).x * 5.99)];
	float pixel = max(length(dx), length(dy));
	float hedge = (1.0 - smoothstep(hedge_width - pixel, hedge_width + pixel, border)) * fields;
	vec3 tint = mix(mix(CROPS[0], crop, fields), HEDGE, hedge);
	ALBEDO = clamp(grass * tint, vec3(ALBEDO_MIN), vec3(ALBEDO_MAX));
	ROUGHNESS = 0.95;
	NORMAL_MAP = textureGrad(normal_map, p / tile, dx / tile, dy / tile).rgb;
}
