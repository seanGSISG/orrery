shader_type spatial;
// Open country (objects/land): grass at its true size, in closes (small grass fields) round
// the object, and past `meadow` m farmland. The farmland is a grid of blocks, turned a little,
// whose rows are offset at random. Hedges with trees in them bound each block. A block is cut
// into two to five strips, each a field with its own crop, a grass margin between two fields,
// and rows along the field where the crop has them. A few blocks are woods. The closes are the
// same at a third of the size. Low-frequency noise shades all of it, so that no area is one
// flat colour. Every line fades to its share of a pixel, so far land does not shimmer or
// darken. The pattern uses world positions, so it stays put.

uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// Metres that one repeat of the grass texture covers: its true size.
uniform float tile = 1.4;
// The radius of the closes round the object, m; the farmland starts past it.
uniform float meadow = 90.0;
// The size of a block of fields, m, and the turn of the grid, radians.
uniform vec2 block = vec2(240.0, 170.0);
uniform float turn = 0.3;
// The width of a hedge, of a grass margin between two fields, and of a hedge tree, m.
uniform float hedge_width = 1.4;
uniform float margin_width = 1.5;
uniform float tree_width = 8.0;
// The space between two hedge trees, m, and the share of the places that have one.
uniform float tree_spacing = 16.0;
uniform float tree_share = 0.45;

// Albedo limits in linear light (docs/design/visual-quality.md §6): sRGB 30 and 240.
const float ALBEDO_MIN = 0.013;
const float ALBEDO_MAX = 0.871;
// The mean colour of the grass texture, linear: the texture gives detail round it.
const vec3 GRASS_MEAN = vec3(0.125, 0.159, 0.033);
// Albedos in linear light. Crops, from sRGB: young wheat (82, 104, 48), ripe wheat
// (138, 124, 72), stubble (132, 120, 84), ploughed earth (92, 76, 58), pasture (74, 94, 48) and
// hay (118, 114, 70).
const vec3 MEADOW = vec3(0.110, 0.141, 0.032);
const vec3 CROPS[6] = vec3[6](
	vec3(0.084, 0.138, 0.030),
	vec3(0.254, 0.202, 0.065),
	vec3(0.231, 0.188, 0.089),
	vec3(0.107, 0.072, 0.042),
	vec3(0.069, 0.112, 0.030),
	vec3(0.181, 0.168, 0.061)
);
// The rows of each crop: their spacing, m (0 for none), and how much they change the colour.
const vec2 ROWS[6] = vec2[6](
	vec2(20.0, 0.12),
	vec2(20.0, 0.10),
	vec2(6.0, 0.10),
	vec2(1.2, 0.22),
	vec2(0.0, 0.0),
	vec2(4.0, 0.14)
);
const vec3 MARGIN = vec3(0.127, 0.162, 0.045);
const vec3 HEDGE = vec3(0.042, 0.065, 0.021);
const vec3 WOOD = vec3(0.030, 0.048, 0.018);
// Where each crop's share of the fields ends, in the order of CROPS: green crops and pasture
// are the most common.
const float SHARES[6] = float[6](0.22, 0.36, 0.48, 0.62, 0.86, 1.0);
// The share of blocks that are woods.
const float WOODS = 0.08;
// The size of a block of closes, as a share of a block of farmland.
const float CLOSES = 0.3;

varying vec3 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// Returns four random numbers from 0 to 1 for a whole-number point.
vec4 random(vec2 p) {
	vec4 q = fract(p.xyxy * vec4(0.1031, 0.1030, 0.0973, 0.1099));
	q += dot(q, q.wzxy + 33.33);
	return fract((q.xxyz + q.yzzw) * q.zywx);
}

// Value noise from 0 to 1 with features about one unit across.
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = random(i).x;
	float b = random(i + vec2(1.0, 0.0)).x;
	float c = random(i + vec2(0.0, 1.0)).x;
	float d = random(i + vec2(1.0, 1.0)).x;
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// Returns how much of a pixel `pixel` m wide a line `width` m wide covers, at the distance
// `d` m from its middle: 1 on a near line, and a line's share of the pixel on a far one.
float line(float d, float width, float pixel) {
	float inside = 1.0 - smoothstep(0.5 * (width - pixel), 0.5 * (width + pixel), d);
	return inside * clamp(width / pixel, 0.0, 1.0);
}

// Returns how strongly rows `spacing` m apart show at the coordinate `across`, from -1 to 1;
// rows narrower than two pixels fade out.
float rows(float across, float spacing, float pixel) {
	if (spacing <= 0.0) {
		return 0.0;
	}
	float fade = 1.0 - smoothstep(0.25 * spacing, 0.5 * spacing, pixel);
	return sin(TAU * across / spacing) * fade;
}

// Returns the distance from q to the nearest hedge tree on the line `edge` (a block edge at
// that coordinate of `along`'s other axis), with trees along `along`. `side` names the line.
float tree(float along, float across, float side) {
	float slot = floor(along / tree_spacing);
	vec4 r = random(vec2(slot, side * 7.13));
	if (r.x > tree_share) {
		return 1e6;
	}
	float centre = (slot + 0.25 + 0.5 * r.y) * tree_spacing;
	return length(vec2(along - centre, across)) / (0.6 + 0.8 * r.z);
}

// Returns the colour of farmland at `from` (m from the object) on the turned grid of blocks of
// `size` m. Each row of blocks is offset along the grid at random, and each block is cut into
// strips. Closes, the small fields round a town, hold only grass crops and no woods, and their
// hedges are thinner.
vec3 fields(vec2 from, vec2 size, float pixel, bool closes) {
	vec2 q = mat2(vec2(cos(turn), sin(turn)), vec2(-sin(turn), cos(turn))) * from;
	float seed = closes ? 50.0 : 0.0;
	float row = floor(q.y / size.y);
	vec2 shifted = vec2(q.x + random(vec2(row, 3.7 + seed)).x * size.x, q.y);
	vec2 cell = floor(shifted / size);
	vec2 f = shifted / size - cell;
	vec4 r = random(cell + seed);

	// The fields of a block: strips across one of its axes.
	bool across_x = r.x < 0.5;
	float count = 2.0 + floor(r.y * 4.0);
	float s = (across_x ? f.x : f.y) * count;
	float strip = floor(s);
	float strip_width = (across_x ? size.x : size.y) / count;
	float in_strip = (s - strip) * strip_width;
	vec4 field = random(cell * 8.0 + strip + 0.5 + seed);
	int crop = 5;
	for (int i = 4; i >= 0; i--) {
		crop = field.x < SHARES[i] ? i : crop;
	}
	if (closes) {
		crop = field.x < 0.5 ? 4 : field.x < 0.75 ? 0 : 5;
	}
	vec3 colour = CROPS[crop] * (0.92 + 0.16 * field.y);
	colour *= 1.0 + ROWS[crop].y * rows(in_strip, ROWS[crop].x, pixel);
	float margin = line(min(in_strip, strip_width - in_strip), 2.0 * margin_width, pixel);
	colour = mix(colour, MARGIN, margin);
	if (closes) {
		colour = mix(colour, MEADOW, 0.4);
	} else if (r.z < WOODS) {
		colour = WOOD * (0.75 + 0.5 * noise(from / 9.0));
	}

	// Hedges and hedge trees on the block edges.
	vec2 edge = min(f, 1.0 - f) * size;
	float width = closes ? 0.6 * hedge_width : hedge_width;
	float hedge = line(min(edge.x, edge.y), 2.0 * width, pixel);
	float side_x = round(shifted.x / size.x) + 101.0 * row + seed;
	float side_y = round(q.y / size.y) + seed;
	float to_tree = min(tree(q.y, edge.x, side_x), tree(q.x, edge.y, side_y + 0.5));
	// A tree's crown: soft at its edge, and darker in its middle.
	float crown = 1.0 - smoothstep(0.25 * tree_width - pixel, 0.5 * tree_width + pixel, to_tree);
	hedge = max(hedge, crown * clamp(tree_width / pixel, 0.0, 1.0) * (0.75 + 0.25 * crown));
	return mix(colour, HEDGE * (0.8 + 0.4 * field.z), hedge);
}

void fragment() {
	vec2 p = world.xz;
	vec2 dx = dFdx(p);
	vec2 dy = dFdy(p);
	float pixel = max(length(dx), length(dy));
	vec3 grass = textureGrad(albedo_map, p / tile, dx / tile, dy / tile).rgb;
	float wide = tile * 6.3;
	grass = mix(grass, textureGrad(albedo_map, p / wide + 0.37, dx / wide, dy / wide).rgb, 0.4);
	vec3 detail = grass / GRASS_MEAN;

	// Closes round the object, and the farmland past the meadow.
	vec2 from = p - MODEL_MATRIX[3].xz;
	float farmland = smoothstep(meadow, meadow * 1.4, length(from));
	vec3 colour = vec3(0.0);
	if (farmland < 1.0) {
		colour = fields(from, block * CLOSES, pixel, true);
	}
	if (farmland > 0.0) {
		colour = mix(colour, fields(from, block, pixel, false), farmland);
	}
	// Shading: patches of grass at about 15 m, brightness at about 70 m, and dry or green
	// ground at about 250 m.
	colour *= 0.9 + 0.2 * noise(p / 15.0);
	colour *= 0.88 + 0.24 * noise(p / 70.0);
	colour *= mix(vec3(0.94, 1.02, 1.08), vec3(1.08, 0.99, 0.84), noise(p / 250.0 + 11.0));
	ALBEDO = clamp(colour * detail, vec3(ALBEDO_MIN), vec3(ALBEDO_MAX));
	ROUGHNESS = 0.95;
	NORMAL_MAP = textureGrad(normal_map, p / tile, dx / tile, dy / tile).rgb;
}
