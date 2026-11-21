class_name AudioBuses
extends RefCounted
## The audio buses of res://audio/default_bus_layout.tres and their volumes. Music, SFX and UI
## send to Master; a hard limiter on Master keeps the mix from clipping. The settings menu
## (#23) reads and writes each volume here as a linear value 0..1, and Save (#21) stores it.

const MASTER: StringName = &"Master"
const MUSIC: StringName = &"Music"
const SFX: StringName = &"SFX"
const UI: StringName = &"UI"
const ALL: Array[StringName] = [MASTER, MUSIC, SFX, UI]


## Returns the volume of bus, linear 0..1.
static func volume(bus: StringName) -> float:
	return AudioServer.get_bus_volume_linear(_index(bus))


## Sets the volume of bus, linear; it is clamped to 0..1, and 0 is silent.
static func set_volume(bus: StringName, value: float) -> void:
	AudioServer.set_bus_volume_linear(_index(bus), clampf(value, 0.0, 1.0))


## Returns the index of bus; fails loudly when the layout lacks it.
static func _index(bus: StringName) -> int:
	var index: int = AudioServer.get_bus_index(bus)
	assert(index >= 0, "AudioBuses: no bus %s" % bus)
	return index
