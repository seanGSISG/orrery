shader_type spatial;
// The shader of every kit material (res://materials/). It maps a PBR texture set onto a kit
// piece from three sides in the piece's own space, so a piece needs no UV1 and the texel
// density is the same on every piece: one repeat covers `tile` metres. Kit pieces keep a
// scale of 1, so their own space is in metres.
// - Paving: with a slab size, the top of a piece is cut into slabs in a running bond, and
//   the course lines go on down its sides. Each slab reads a different part of the texture
//   and has its own shade, so the texture shows no repeat. The joints are flush lines of
//   darker stone.
// - Courses: with a wall size, the sides of a piece are cut into courses of blocks in a
//   running bond instead of the paving's course lines: a wall of ashlar.
// - Detail: with a detail size, the normal map is added again at that size for fine grain
//   close to the camera (docs/design/visual-quality.md §6).
// - Turn: turns the texture on the top of a piece a quarter turn, so that a texture with a
//   grain (slates, planks) can run along x or along y.

uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D roughness_map : hint_roughness_r, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// Multiplies the albedo map in linear light. It can be above 1 for a map that is too dark.
uniform vec3 tint = vec3(1.0);
// Metres that one texture repeat covers.
uniform float tile = 1.0;
uniform float roughness_scale = 1.0;
uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float normal_strength = 1.0;
// Metres that one repeat of the detail normal covers; 0 turns the detail off.
uniform float detail_tile = 0.0;
uniform float detail_strength = 0.5;
// Slab size in metres, across and along the piece. (0, 0) turns the paving off.
uniform vec2 slab_size = vec2(0.0);
// Joint width in metres, and how dark the joint is (1 is as bright as the slab).
uniform float joint_width = 0.012;
uniform float joint_shade = 0.5;
// The darkest slab is this much darker than the brightest.
uniform float slab_variation = 0.16;
// Block length and course height on the sides, m. (0, 0) keeps the paving's course lines.
uniform vec2 wall_size = vec2(0.0);
// Turns the top's texture a quarter turn.
uniform bool turn_top = false;

// Albedo limits in linear light (docs/design/visual-quality.md §6): sRGB 30, 240 and 250.
const float ALBEDO_MIN = 0.013;
const float ALBEDO_MAX_DIELECTRIC = 0.871;
const float ALBEDO_MAX_METAL = 0.956;
const float BLEND_SHARPNESS = 8.0;
// A slab size for "no joint in this direction".
const float ENDLESS = 100000.0;

varying vec3 piece_position;
varying vec3 piece_normal;
varying flat float piece_seed;

void vertex() {
	piece_position = VERTEX;
	piece_normal = NORMAL;
	// Two pieces of the same shape get different slabs.
	piece_seed = floor(dot(MODEL_MATRIX[3].xyz, vec3(7.0, 13.0, 29.0)));
}

// Returns three random numbers from 0 to 1 for a slab.
vec3 slab_random(vec2 cell) {
	vec3 p = fract(vec3(cell.xyx + piece_seed) * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.xxy + p.yzz) * p.zyx);
}

// Returns what one side shows at the point `at` on its plane, in metres: the albedo in rgb
// and the roughness in a. `at_dx` and `at_dy` are the screen-space slopes of `at`. `size` is
// the slab size along the two axes of `at`. `bump` gets the slope of the normal map along +x
// and -y of `at`.
vec4 side(vec2 at, vec2 at_dx, vec2 at_dy, vec2 size, out vec2 bump) {
	vec2 uv = at / tile;
	vec2 dx = at_dx / tile;
	vec2 dy = at_dy / tile;
	float shade = 1.0;
	float joint = 0.0;
	vec2 flip = vec2(1.0);
	if (size.x > 0.0 && size.y > 0.0) {
		// Running bond: every second row is half a slab along.
		vec2 slab = vec2(at.x / size.x + 0.5 * mod(floor(at.y / size.y), 2.0), at.y / size.y);
		vec3 random = slab_random(floor(slab));
		// Each slab reads the texture from its own place, mirrored or not along each axis.
		flip = step(0.5, fract(random.z * vec2(17.0, 31.0))) * 2.0 - 1.0;
		uv = uv * flip + random.xy;
		dx *= flip;
		dy *= flip;
		shade = 1.0 - slab_variation * random.z;
		// The distance to the nearest slab edge in metres, against the size of a pixel, so
		// that a far joint fades out and does not shimmer.
		vec2 edge = (0.5 - abs(fract(slab) - 0.5)) * size;
		float pixel = max(length(at_dx), length(at_dy));
		float line = 1.0 - smoothstep(0.5 * (joint_width - pixel), 0.5 * (joint_width + pixel), min(edge.x, edge.y));
		joint = line * clamp(joint_width / pixel, 0.0, 1.0);
	}
	vec3 color = textureGrad(albedo_map, uv, dx, dy).rgb * tint * shade;
	float rough = textureGrad(roughness_map, uv, dx, dy).r * roughness_scale;
	bump = (textureGrad(normal_map, uv, dx, dy).rg * 2.0 - 1.0) * normal_strength;
	if (detail_tile > 0.0) {
		float finer = tile / detail_tile;
		bump += (textureGrad(normal_map, uv * finer, dx * finer, dy * finer).rg * 2.0 - 1.0) * detail_strength;
	}
	color *= mix(1.0, joint_shade, joint);
	rough = mix(rough, max(rough, 0.9), joint);
	bump *= flip * (1.0 - joint);
	return vec4(color, rough);
}

void fragment() {
	vec3 normal = normalize(piece_normal);
	vec3 weight = pow(abs(normal), vec3(BLEND_SHARPNESS));
	weight /= weight.x + weight.y + weight.z;
	vec4 surface = vec4(0.0);
	vec3 bent = normal;
	vec2 bump;
	// The screen-space slopes of the position, taken once before any branch: a slope taken
	// inside a branch is not defined where two neighbour pixels take different branches.
	vec3 p = piece_position;
	vec3 px = dFdx(p);
	vec3 py = dFdy(p);
	// A side that the face does not look at costs no texture reads. In a piece's own space
	// x is across, y is up and -z is along (the glTF axes of the kit's x, z and y).
	bool walled = wall_size.x > 0.0 && wall_size.y > 0.0;
	if (weight.x > 0.001) {
		vec2 size = walled ? wall_size : vec2(slab_size.y, ENDLESS);
		surface += weight.x * side(vec2(-p.z, -p.y), vec2(-px.z, -px.y), vec2(-py.z, -py.y), size, bump);
		bent += weight.x * vec3(0.0, bump.y, -bump.x);
	}
	if (weight.y > 0.001) {
		if (turn_top) {
			// A quarter turn of (x, -z): no mirror, so the normal map keeps its sense.
			surface += weight.y * side(vec2(p.z, p.x), vec2(px.z, px.x), vec2(py.z, py.x), slab_size.yx, bump);
			bent += weight.y * vec3(-bump.y, 0.0, bump.x);
		} else {
			surface += weight.y * side(vec2(p.x, -p.z), vec2(px.x, -px.z), vec2(py.x, -py.z), slab_size, bump);
			bent += weight.y * vec3(bump.x, 0.0, bump.y);
		}
	}
	if (weight.z > 0.001) {
		vec2 size = walled ? wall_size : vec2(slab_size.x, ENDLESS);
		surface += weight.z * side(vec2(p.x, -p.y), vec2(px.x, -px.y), vec2(py.x, -py.y), size, bump);
		bent += weight.z * vec3(bump.x, bump.y, 0.0);
	}
	ALBEDO = clamp(surface.rgb, vec3(ALBEDO_MIN), vec3(mix(ALBEDO_MAX_DIELECTRIC, ALBEDO_MAX_METAL, metallic)));
	ROUGHNESS = clamp(surface.a, 0.0, 1.0);
	METALLIC = metallic;
	NORMAL = normalize((VIEW_MATRIX * vec4(MODEL_NORMAL_MATRIX * normalize(bent), 0.0)).xyz);
}
