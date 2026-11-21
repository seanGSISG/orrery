class_name AscentFlag
extends Node3D
## The flag at the best height of Ascent: a pole with a gold pennant that turns its face to
## the camera, and a thin beam above it, so that the marble sees it from far below. Its origin
## is the foot of the pole, on the floor. The Ascent mode puts it in place and shows it; it has
## no physics.

const BEAM: Shader = preload("res://objects/gem/beam.gdshader")
## The colour of gold medals and records in the HUD (UiLook.GOLD).
const GOLD: Color = Color("#f4d17e")
const POLE: Color = Color(0.2, 0.15, 0.1)
## Height of the pole, and length and height of the pennant, m.
const POLE_HEIGHT: float = 2.0
const PENNANT: Vector2 = Vector2(1.0, 0.56)
## Height of the beam above the foot, and its radius, m.
const BEAM_HEIGHT: float = 16.0
const BEAM_RADIUS: float = 0.12


## Builds the pole, the pennant and the beam.
func _init() -> void:
	var pole: MeshInstance3D = MeshInstance3D.new()
	var shaft: CylinderMesh = CylinderMesh.new()
	shaft.top_radius = 0.025
	shaft.bottom_radius = 0.035
	shaft.height = POLE_HEIGHT
	shaft.radial_segments = 8
	shaft.material = _paint(POLE, false)
	pole.mesh = shaft
	pole.position.y = POLE_HEIGHT * 0.5
	add_child(pole)
	var cloth: MeshInstance3D = MeshInstance3D.new()
	cloth.mesh = _pennant()
	cloth.position.y = POLE_HEIGHT
	cloth.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(cloth)
	var beam: MeshInstance3D = MeshInstance3D.new()
	var column: CylinderMesh = CylinderMesh.new()
	column.top_radius = BEAM_RADIUS
	column.bottom_radius = BEAM_RADIUS
	column.height = BEAM_HEIGHT
	column.radial_segments = 16
	column.rings = 1
	column.cap_top = false
	column.cap_bottom = false
	var glow: ShaderMaterial = ShaderMaterial.new()
	glow.shader = BEAM
	glow.set_shader_parameter(&"height", BEAM_HEIGHT)
	glow.set_shader_parameter(&"strength", 0.5)
	column.material = glow
	beam.mesh = column
	beam.position.y = BEAM_HEIGHT * 0.5
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	beam.set_instance_shader_parameter(&"colour", GOLD)
	add_child(beam)


## Returns the pennant: a triangle from the top of the pole, which turns round the pole to
## face the camera.
static func _pennant() -> ArrayMesh:
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	tool.set_normal(Vector3.BACK)
	tool.add_vertex(Vector3.ZERO)
	tool.add_vertex(Vector3(PENNANT.x, -PENNANT.y * 0.5, 0.0))
	tool.add_vertex(Vector3(0.0, -PENNANT.y, 0.0))
	tool.set_material(_paint(GOLD, true))
	return tool.commit()


## Returns a plain material of color. pennant makes it glow and turn round the upright axis
## to the camera, so that the pennant reads at its full size against a dark wall and against
## the sky.
static func _paint(color: Color, pennant: bool) -> StandardMaterial3D:
	var paint: StandardMaterial3D = StandardMaterial3D.new()
	paint.albedo_color = color
	paint.roughness = 0.7
	if pennant:
		paint.cull_mode = BaseMaterial3D.CULL_DISABLED
		paint.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
		paint.emission_enabled = true
		paint.emission = color
		paint.emission_energy_multiplier = 0.8
	return paint
