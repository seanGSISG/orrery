class_name SfxPlayer
extends Node
## Plays the sound effects of one LevelRun on the SFX bus. The Music autoload owns one and
## attaches it to Game.run; a test makes its own and calls attach(run) and observe(dt).
##
## - Feedback: each LevelRun.feedback kind maps to a sound res://audio/sfx/<sound>.ogg
##   through SOUNDS. The strength (0..1) sets the volume and the pitch. A sound in POSITIONAL
##   plays at the event's position, the others play flat.
## - Voices: each sound has VOICES players of one voice each, used in turn, so each voice
##   keeps its own volume, pitch and position. A sound does not start again within GAP_TICKS
##   of its last start. The limiter on Master catches the rest.
## - Roll: a loop whose volume follows the marble's rolling speed (spin times radius) on the
##   ground, and whose pitch rises with it. It is silent in the air.
## - Respawn: the respawn sound plays when the run comes back from &"respawning" or restarts.
## - A change of run stops every sound of the last run.

const SOUND_PATH: String = "res://audio/sfx/%s.ogg"
## Feedback kind to sound. A kind that is not a key here falls back to its "<type>." key,
## then to its ".<event>" key, so new objects and power-ups get a sound before they get their
## own. A kind with no match plays nothing.
const SOUNDS: Dictionary[StringName, StringName] = {
	&"marble.jump": &"jump",
	&"marble.land": &"land_soft",
	&"marble.bounce": &"bounce",
	&"bumper.hit": &"bumper",
	&"steam_vent.blow": &"steam_vent",
	&"pendulum.hit": &"pendulum",
	&"gem.collect": &"gem",
	&"egg.open": &"egg",
	&"checkpoint.reach": &"checkpoint",
	&"finish.open": &"finish_open",
	&"finish.reach": &"finish_reach",
	&"tile.fall": &"tile_fall",
	&"tile.": &"tile_crack",
	&"trapdoor.": &"trapdoor",
	&".pickup": &"powerup_pickup",
	&".use": &"powerup_use",
}
## marble.land plays land_hard instead of land_soft at this strength and above.
const HARD_LANDING: float = 0.6
const LAND_HARD: StringName = &"land_hard"
const RESPAWN: StringName = &"respawn"
const ROLL: StringName = &"roll"
## Sounds that play where the event happens; the rest play flat, as the marble's own sounds.
const POSITIONAL: Array[StringName] = [
	&"bumper", &"steam_vent", &"pendulum", &"trapdoor", &"tile_crack", &"tile_fall"
]
const VOICES: int = 3
const GAP_TICKS: int = 4
## Volume at strength 0, linear; strength 1 plays at full volume.
const QUIET: float = 0.35
## The roll loop's pitch at rest and at the marble's top rolling speed.
const ROLL_PITCH: Vector2 = Vector2(0.7, 1.4)
## Time constant of the roll volume's approach to its target, s.
const ROLL_SMOOTH: float = 0.05
const SILENT_DB: float = -80.0

## The roll loop player; its volume_db and pitch_scale follow the marble.
var roll: AudioStreamPlayer
## The roll loop's volume, linear 0..1.
var roll_level: float = 0.0

var _run: LevelRun
## Every voice: an AudioStreamPlayer or AudioStreamPlayer3D. A sound's VOICES voices are
## next to each other, from index _first[sound].
var _voices: Array[Node] = []
var _first: Dictionary[StringName, int] = {}
## Sound name to the count of its starts; the next start uses voice count % VOICES.
var _starts: Dictionary[StringName, int] = {}
## Sound name to the run tick of its last start.
var _started: Dictionary[StringName, int] = {}
var _tick: int = 0
var _status: StringName = &""


## Makes the voices of each sound and the roll loop. Pauses with the game.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	var names: Array[StringName] = SOUNDS.values()
	names.append_array([LAND_HARD, RESPAWN])
	for sound: StringName in names:
		if not _first.has(sound):
			_first[sound] = _voices.size()
			_starts[sound] = 0
			for i: int in VOICES:
				_voices.append(_make_voice(sound))
	roll = AudioStreamPlayer.new()
	roll.stream = load(SOUND_PATH % ROLL) as AudioStream
	roll.bus = AudioBuses.SFX
	roll.volume_db = SILENT_DB
	add_child(roll)


## Follows the run once per physics frame.
func _physics_process(delta: float) -> void:
	observe(delta)


## Plays the sounds of run from now on, and stops those of the last run; null stops all.
func attach(run: LevelRun) -> void:
	if is_instance_valid(_run) and _run.feedback.is_connected(_on_feedback):
		_run.feedback.disconnect(_on_feedback)
	_run = run
	_started.clear()
	for voice: Node in _voices:
		_stop(voice)
	roll.stop()
	roll_level = 0.0
	roll.volume_db = SILENT_DB
	if run == null:
		return
	run.feedback.connect(_on_feedback)
	_tick = run.state.tick
	_status = run.state.status
	roll.play()


## Reads the run state after a tick of dt seconds: sets the roll loop and plays the respawn.
func observe(dt: float) -> void:
	if not is_instance_valid(_run):
		return
	var state: GameState = _run.state
	if state.tick < _tick:
		_started.clear()
	if state.tick < _tick or (_status == &"respawning" and state.status == &"playing"):
		_play(RESPAWN, 1.0, state.position)
	_tick = state.tick
	_status = state.status
	var tuning: MarbleTuning = _run.marble.tuning
	var speed: float = clampf(state.spin.length() * tuning.radius / tuning.max_roll_speed, 0.0, 1.0)
	var target: float = speed if state.on_ground else 0.0
	roll_level = lerpf(roll_level, target, 1.0 - exp(-dt / ROLL_SMOOTH))
	roll.volume_db = maxf(linear_to_db(roll_level), SILENT_DB)
	roll.pitch_scale = lerpf(ROLL_PITCH.x, ROLL_PITCH.y, speed)


## Returns the voice of sound that started last, else its first voice: an AudioStreamPlayer
## or AudioStreamPlayer3D. Null for an unknown sound.
func player(sound: StringName) -> Node:
	if not _first.has(sound):
		return null
	return _voices[_first[sound] + (_starts[sound] + VOICES - 1) % VOICES]


## Returns the sound for a feedback kind and strength; &"" when the kind has none.
static func sound_for(kind: StringName, strength: float) -> StringName:
	if kind == &"marble.land" and strength >= HARD_LANDING:
		return LAND_HARD
	var type: StringName = StringName(kind.get_slice(".", 0) + ".")
	var event: StringName = StringName("." + kind.get_slice(".", 1))
	for key: StringName in [kind, type, event]:
		if SOUNDS.has(key):
			return SOUNDS[key]
	return &""


## Plays the sound of one feedback event.
func _on_feedback(kind: StringName, strength: float, at: Vector3) -> void:
	var sound: StringName = sound_for(kind, strength)
	if sound != &"":
		_play(sound, strength, at)


## Starts sound at volume and pitch from strength, at a world position if it is positional.
func _play(sound: StringName, strength: float, at: Vector3) -> void:
	var tick: int = _run.state.tick
	if _started.has(sound) and tick >= _started[sound] and tick - _started[sound] < GAP_TICKS:
		return
	_started[sound] = tick
	var s: float = clampf(strength, 0.0, 1.0)
	var volume: float = linear_to_db(lerpf(QUIET, 1.0, s))
	var pitch: float = lerpf(0.94, 1.06, s) * randf_range(0.97, 1.03)
	var voice: Node = _voices[_first[sound] + _starts[sound] % VOICES]
	_starts[sound] += 1
	var flat: AudioStreamPlayer = voice as AudioStreamPlayer
	if flat != null:
		flat.volume_db = volume
		flat.pitch_scale = pitch
		flat.play()
		return
	var spatial: AudioStreamPlayer3D = voice as AudioStreamPlayer3D
	spatial.global_position = at
	spatial.volume_db = volume
	spatial.pitch_scale = pitch
	spatial.play()


## Stops voice, flat or positional.
func _stop(voice: Node) -> void:
	var flat: AudioStreamPlayer = voice as AudioStreamPlayer
	if flat != null:
		flat.stop()
	var spatial: AudioStreamPlayer3D = voice as AudioStreamPlayer3D
	if spatial != null:
		spatial.stop()


## Makes one voice of sound on the SFX bus: positional or flat.
func _make_voice(sound: StringName) -> Node:
	var stream: AudioStream = load(SOUND_PATH % sound) as AudioStream
	if sound in POSITIONAL:
		var spatial: AudioStreamPlayer3D = AudioStreamPlayer3D.new()
		spatial.stream = stream
		spatial.bus = AudioBuses.SFX
		spatial.unit_size = 8.0
		spatial.max_distance = 80.0
		add_child(spatial)
		return spatial
	var flat: AudioStreamPlayer = AudioStreamPlayer.new()
	flat.stream = stream
	flat.bus = AudioBuses.SFX
	add_child(flat)
	return flat
