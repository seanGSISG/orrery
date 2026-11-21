class_name Egg
extends LevelObject
## The `egg` marker: the level's hidden Clockwork Egg, 0.6 m tall. Put the marker on the floor.
## When the marble finds it, it tells the rules once and opens in OPEN_TIME: the lid tips back
## and a small gear rises and spins. A restart closes it again; a checkpoint respawn keeps it
## open.

## Time to open, s.
const OPEN_TIME: float = 0.8
## Widest radius and the height of the widest ring, m. The shell is below it, the lid above.
const RADIUS: float = 0.2
const WAIST: float = 0.3
## Half-heights of the shell and the lid, m.
const SHELL: float = 0.25
const LID: float = 0.35
## The open lid's angle around the hinge at the back, rad.
const LID_ANGLE: float = 1.9
## Gear spin while open, rad/s.
const GEAR_SPIN: float = 3.0

var _found: bool = false
## Run time when the egg was found; negative until the next advance() after the find.
var _found_at: float = -1.0

@onready var _shell: MeshInstance3D = $Shell
@onready var _lid: MeshInstance3D = $Hinge/Lid
@onready var _hinge: Node3D = $Hinge
@onready var _gear: Node3D = $Gear


## Builds the shell and the lid as two halves of one egg.
func _ready() -> void:
	_shell.mesh = _lathe(-PI / 2, 0.0, SHELL)
	_lid.mesh = _lathe(0.0, PI / 2, LID)


## Closes the egg again at a restart. A checkpoint respawn keeps it open.
func reset(restart: bool) -> void:
	if restart:
		_found = false
		_found_at = -1.0
		_pose(0.0, 0.0)


## Plays the opening from the run time.
func advance(_run: LevelRun, t: float) -> void:
	if not _found:
		return
	if _found_at < 0.0:
		_found_at = t
	_pose(clampf((t - _found_at) / OPEN_TIME, 0.0, 1.0), t)


## Finds the egg once: tells the rules and starts the opening.
func on_overlap(run: LevelRun, _first: bool) -> void:
	if _found:
		return
	_found = true
	run.rules.find_egg()
	feedback.emit(&"egg.open", 1.0, _hinge.global_position)


## Sets the lid and the gear for open (0 closed, 1 open) at run time t.
func _pose(open: float, t: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, open)
	_hinge.rotation.x = -LID_ANGLE * eased
	_gear.visible = open > 0.0
	_gear.position.y = lerpf(0.2, WAIST + 0.2, eased)
	_gear.rotation.y = t * GEAR_SPIN


## A smooth band of the egg between the angles from and to (-PI/2 is the bottom tip, 0 the
## widest ring, PI/2 the top tip). half is the half-height on that side of the widest ring.
static func _lathe(from: float, to: float, half: float) -> ArrayMesh:
	const SEGMENTS: int = 24
	const RINGS: int = 8
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k: int in RINGS:
		var low: float = lerpf(from, to, float(k) / RINGS)
		var high: float = lerpf(from, to, float(k + 1) / RINGS)
		for i: int in SEGMENTS:
			var a: float = TAU * i / SEGMENTS
			var b: float = TAU * ((i + 1) % SEGMENTS) / SEGMENTS
			var top_a: Vector3 = _egg_point(high, a, half)
			var top_b: Vector3 = _egg_point(high, b, half)
			var bottom_a: Vector3 = _egg_point(low, a, half)
			var bottom_b: Vector3 = _egg_point(low, b, half)
			for corner: Vector3 in [top_a, bottom_a, bottom_b, top_a, bottom_b, top_b]:
				tool.add_vertex(corner)
	tool.index()
	tool.generate_normals()
	return tool.commit()


## The point of the egg surface at latitude lat and longitude lon.
static func _egg_point(lat: float, lon: float, half: float) -> Vector3:
	var ring: float = RADIUS * cos(lat)
	return Vector3(cos(lon) * ring, WAIST + half * sin(lat), sin(lon) * ring)
