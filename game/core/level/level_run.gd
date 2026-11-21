class_name LevelRun
extends Node3D
## Plays one level and owns its time: one step() is one tick (docs/design/core-runtime.md §3).
## Make one with LevelRun.create(level) and add it to the tree at the world origin; _ready()
## starts the run. The game steps it from _physics_process while auto_step is true. Tests and
## the harness set auto_step to false and call step() in a plain loop.

## Every object's and the marble's feedback, re-emitted for audio and rumble.
signal feedback(kind: StringName, strength: float, at: Vector3)
## At the end of each step(), when state holds the new tick. It comes once per tick, also
## when the harness or a test steps many ticks in one frame.
signal stepped

const MARBLE: PackedScene = preload("res://core/marble/marble.tscn")

var level: Level
var marble: Marble
## The first start pad in the level; null when it has none.
var start: StartPad
var rules: Rules
var slot: PowerUpSlot
## Every LevelObject in the level, in tree order.
var objects: Array[LevelObject] = []
var state: GameState = GameState.new()
## The input of the last tick. The camera reads camera_yaw and camera_pitch here.
var last_input: MarbleInput = MarbleInput.new()
## False: only explicit step() calls advance the run.
var auto_step: bool = true
## False: the player's `restart` action does nothing (Game.restart()). Ascent sets it, because
## a restart there would throw a long climb away. restart() itself always works.
var restartable: bool = true

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


## Adds the marble, finds the objects, makes the rules and starts the run.
func _ready() -> void:
	_dt = 1.0 / Engine.physics_ticks_per_second
	marble = MARBLE.instantiate() as Marble
	add_child(marble)
	marble.feedback.connect(feedback.emit)
	_collect(level)
	rules = Rules.new(self)
	var tuning: MarbleTuning = marble.tuning
	_world = WorldQuery.new(get_world_3d().direct_space_state, tuning.radius, tuning.contact_margin)
	restart()


## Steps the run once per physics frame with the player's input while auto_step is true.
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
	last_input = input
	rules.after_step()
	_write_state()
	stepped.emit()


## Starts again at t = 0 at once: every object resets, the rules and the power-up slot start
## empty, and the marble sits still on the start pad. The `restart` action calls it.
func restart() -> void:
	_tick = 0
	_inside.clear()
	for object: LevelObject in objects:
		object.reset(true)
	slot = PowerUpSlot.new(self)
	marble.teleport(spawn_point(start), Vector3.ZERO)
	rules.reset()
	state.level = level.id
	state.status = &"playing"
	_write_state()


## Puts the marble still at `at` after a reset(false) on every object. The clock, the gems
## and the power-up slot stay. Marble.teleport() resets the physics interpolation, so the
## marble does not slide across the level on screen.
func respawn(at: Vector3) -> void:
	_inside.clear()
	for object: LevelObject in objects:
		object.reset(false)
	marble.teleport(at, Vector3.ZERO)
	_write_state()


## Continues a saved run (Ascent): the run is at tick, so every mover has the pose of that
## time, the level clock shows clock s, and the marble is at `at` with new_velocity. Call it
## in place of the first step, on a run that has just started.
func resume(tick: int, clock: float, at: Vector3, new_velocity: Vector3) -> void:
	_tick = tick
	for object: LevelObject in objects:
		object.advance(self, _tick * _dt)
	rules.set_clock(clock)
	marble.teleport(at, new_velocity)
	_write_state()


## Puts the marble at `at` with new_velocity, and writes the state at once. The harness
## `teleport` command calls it.
func teleport(at: Vector3, new_velocity: Vector3) -> void:
	marble.teleport(at, new_velocity)
	_write_state()


## The marble centre that rests on pad: one radius above its origin, along its up. Above the
## world origin when pad is null.
func spawn_point(pad: LevelObject) -> Vector3:
	if pad == null:
		return Vector3.UP * marble.tuning.radius
	return pad.global_position + pad.global_basis.y.normalized() * marble.tuning.radius


## Finds every LevelObject under node, re-emits its feedback, and keeps the first start pad.
func _collect(node: Node) -> void:
	var object: LevelObject = node as LevelObject
	if object != null:
		objects.append(object)
		object.feedback.connect(feedback.emit)
		if start == null and object is StartPad:
			start = object as StartPad
	for child: Node in node.get_children():
		_collect(child)


## Copies the marble and the tick into the state.
func _write_state() -> void:
	state.tick = _tick
	state.position = marble.position
	state.velocity = marble.velocity
	state.spin = marble.spin
	state.up = marble.up
	state.frame = marble.frame
	state.on_ground = marble.on_ground
