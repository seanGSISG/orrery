class_name LevelRun
extends Node3D
## Plays one level and owns its time: one step() is one tick (docs/design/core-runtime.md §3).
## Make one with LevelRun.create(level) and add it to the tree at the world origin; _ready()
## starts the run. The game steps it from _physics_process while auto_step is true. Tests and
## the harness set auto_step to false and call step() in a plain loop.

## Every object's and the marble's feedback, re-emitted for audio and rumble.
signal feedback(kind: StringName, strength: float, at: Vector3)

const MARBLE: PackedScene = preload("res://core/marble/marble.tscn")

var level: Level
var marble: Marble
var rules: Rules
var slot: PowerUpSlot
## Every LevelObject in the level, in tree order.
var objects: Array[LevelObject] = []
var state: GameState = GameState.new()
## The input of the last tick. The camera reads camera_yaw and camera_pitch here.
var last_input: MarbleInput = MarbleInput.new()
## False: only explicit step() calls advance the run.
var auto_step: bool = true

var _world: WorldQuery
var _tick: int = 0
var _dt: float = 0.0
## Objects whose triggers the marble overlapped in the last tick.
var _inside: Array[LevelObject] = []


## Returns a run of level that has not started. Add it to the tree to start it.
static func create(level: Level) -> LevelRun:
	var run: LevelRun = LevelRun.new()
	run.level = level
	run.add_child(level)
	return run


func _ready() -> void:
	_dt = 1.0 / Engine.physics_ticks_per_second
	marble = MARBLE.instantiate() as Marble
	add_child(marble)
	marble.feedback.connect(feedback.emit)
	_collect(level)
	rules = Rules.new(self)
	slot = PowerUpSlot.new(self)
	var tuning: MarbleTuning = marble.tuning
	_world = WorldQuery.new(get_world_3d().direct_space_state, tuning.radius, tuning.contact_margin)
	restart()


func _physics_process(_delta: float) -> void:
	if auto_step:
		step(InputHub.next_input(state))


## Advances the run by one tick with input.
func step(input: MarbleInput) -> void:
	_tick += 1
	var t: float = _tick * _dt
	slot.before_step(input)
	for object: LevelObject in objects:
		object.advance(self, t)
	marble.step(_dt, input, _world)
	for contact: Contact in marble.touches:
		contact.object.on_touch(self, contact)
	for object: LevelObject in marble.overlaps:
		object.on_overlap(self, not _inside.has(object))
	_inside = marble.overlaps.duplicate()
	rules.after_step()
	last_input = input
	_write_state()


## Starts again at t = 0: every object resets, and the marble sits still on the start pad.
func restart() -> void:
	_tick = 0
	_inside.clear()
	for object: LevelObject in objects:
		object.reset(true)
	marble.teleport(_start_position(), Vector3.ZERO)
	rules.reset(true)
	state.level = level.id
	state.status = &"playing"
	_write_state()


## Puts the marble still at `at` after a reset(false) on every object. The clock runs on.
func respawn(at: Vector3) -> void:
	_inside.clear()
	for object: LevelObject in objects:
		object.reset(false)
	marble.teleport(at, Vector3.ZERO)
	_write_state()


## The marble centre on the first start pad, else above the origin.
func _start_position() -> Vector3:
	var above: Vector3 = Vector3.UP * marble.tuning.radius
	for object: LevelObject in objects:
		if object is StartPad:
			return object.global_position + above
	return above


## Finds every LevelObject under node and re-emits its feedback.
func _collect(node: Node) -> void:
	var object: LevelObject = node as LevelObject
	if object != null:
		objects.append(object)
		object.feedback.connect(feedback.emit)
	for child: Node in node.get_children():
		_collect(child)


func _write_state() -> void:
	state.tick = _tick
	state.position = marble.position
	state.velocity = marble.velocity
	state.spin = marble.spin
	state.up = marble.up
	state.on_ground = marble.on_ground
