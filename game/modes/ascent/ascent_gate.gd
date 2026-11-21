class_name AscentGate
extends Node3D
## The "to be continued" gate of Ascent: a brass ring that stands on the last finish pad of
## the climb, with a smaller ring that turns in it and the words above it. The marble rolls
## through the ring onto the pad, and the pad ends the run. The Ascent mode adds the gate to
## that Finish, so its origin is the middle of the pad and its opening faces along the pad's
## forward axis. It has no physics.

## The text key of the words.
const TEXT: String = "ASCENT_GATE"
const BRASS: Color = Color(0.83, 0.62, 0.27)
## The colour of gold medals and records in the HUD (UiLook.GOLD).
const GOLD: Color = Color("#f4d17e")
const INK: Color = Color("#f1ebdb")
const NIGHT: Color = Color("#060a14")
const FONT: Font = preload("res://ui/fonts/InstrumentSerif-Italic.ttf")
## Radius of the ring to the middle of its tube, and the radius of the tube, m.
const RADIUS: float = 1.9
const TUBE: float = 0.11
## Seconds for one turn of the inner ring.
const TURN_PERIOD: float = 14.0

var _inner: MeshInstance3D


## Builds the two rings, the veil in the opening and the words.
func _init() -> void:
	var brass: StandardMaterial3D = StandardMaterial3D.new()
	brass.albedo_color = BRASS
	brass.metallic = 1.0
	brass.roughness = 0.32
	# The lowest part of the ring lies in the floor, so the marble rolls over no step.
	var center: Vector3 = Vector3.UP * (RADIUS - TUBE * 0.5)
	var outer: MeshInstance3D = _ring(RADIUS, TUBE, brass)
	outer.position = center
	outer.rotation.x = PI / 2.0
	add_child(outer)
	_inner = _ring(RADIUS * 0.78, TUBE * 0.55, brass)
	_inner.position = center
	_inner.rotation = Vector3(PI / 2.0, 0.0, 0.5)
	add_child(_inner)
	var veil: MeshInstance3D = MeshInstance3D.new()
	var disc: CylinderMesh = CylinderMesh.new()
	disc.top_radius = RADIUS - TUBE
	disc.bottom_radius = RADIUS - TUBE
	disc.height = 0.002
	disc.radial_segments = 48
	var light: StandardMaterial3D = StandardMaterial3D.new()
	light.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	light.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	light.cull_mode = BaseMaterial3D.CULL_DISABLED
	light.albedo_color = Color(GOLD, 0.14)
	light.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	disc.material = light
	veil.mesh = disc
	veil.position = center
	veil.rotation.x = PI / 2.0
	veil.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(veil)
	var words: Label3D = Label3D.new()
	words.text = TEXT
	words.font = FONT
	words.font_size = 160
	words.pixel_size = 0.0034
	words.modulate = INK
	words.outline_modulate = Color(NIGHT, 0.85)
	words.outline_size = 18
	words.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	words.position = Vector3.UP * (RADIUS * 2.0 + 0.45)
	add_child(words)


## Turns the inner ring round the upright axis.
func _process(delta: float) -> void:
	_inner.rotate(Vector3.UP, delta / TURN_PERIOD * TAU)


## Returns a ring mesh of radius (to the middle of the tube) and tube radius, flat in its own
## x-z plane.
static func _ring(radius: float, tube: float, material: Material) -> MeshInstance3D:
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = radius - tube
	torus.outer_radius = radius + tube
	torus.rings = 96
	torus.ring_segments = 16
	torus.material = material
	var ring: MeshInstance3D = MeshInstance3D.new()
	ring.mesh = torus
	return ring
