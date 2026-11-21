class_name AudioBuses
extends RefCounted
## The audio buses of res://audio/default_bus_layout.tres and their volumes. Music, SFX and UI
## send to Master; a hard limiter on Master keeps the mix from clipping.
##
## Volumes are linear, 0..1, and Settings stores them (master_volume, music_volume,
## sfx_volume, ui_volume). The Music autoload calls apply(Save.settings) at start. The
## settings menu (#23) reads volume(bus), calls set_volume(bus, value, Save.settings), and
## then Save.write() to keep the change.

const MASTER: StringName = &"Master"
const MUSIC: StringName = &"Music"
const SFX: StringName = &"SFX"
const UI: StringName = &"UI"
## Each bus and the Settings var that stores its volume.
const FIELDS: Dictionary[StringName, StringName] = {
	MASTER: &"master_volume",
	MUSIC: &"music_volume",
	SFX: &"sfx_volume",
	UI: &"ui_volume",
}


## Sets the volume of every bus from settings.
static func apply(settings: Settings) -> void:
	for bus: StringName in FIELDS:
		var value: float = settings.get(FIELDS[bus])
		AudioServer.set_bus_volume_linear(_index(bus), clampf(value, 0.0, 1.0))


## Returns the volume of bus, linear 0..1.
static func volume(bus: StringName) -> float:
	return AudioServer.get_bus_volume_linear(_index(bus))


## Sets the volume of bus, clamped to 0..1 (0 is silent), and stores it in settings.
static func set_volume(bus: StringName, value: float, settings: Settings) -> void:
	var clamped: float = clampf(value, 0.0, 1.0)
	AudioServer.set_bus_volume_linear(_index(bus), clamped)
	settings.set(FIELDS[bus], clamped)


## Returns the index of bus; fails loudly when the layout lacks it.
static func _index(bus: StringName) -> int:
	var index: int = AudioServer.get_bus_index(bus)
	assert(index >= 0, "AudioBuses: no bus %s" % bus)
	return index
