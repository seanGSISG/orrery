extends Node
## Autoload Music: plays the music, and owns the sound-effect player and the menu sounds. It
## has no class_name, because a class_name would hide the autoload. docs/design/audio.md
## tells how to add a track.
##
## - A group is a folder res://audio/music/<group>/ of looping OGG tracks. A run plays the
##   group in its level's `music` field, else the group of its tier; no run plays TITLE.
## - A group plays as a shuffled playlist that fades from track to track. ZONED (Ascent) is
##   different: its tracks are the clips of one AudioStreamInteractive, and set_zone()
##   changes the track on the next bar line.
## - A change of group cross-fades over FADE seconds. A group with no tracks fades out.
## - Each frame it checks Game.run. A new run gets its group's music, and `sfx` attaches to
##   it.

const ROOT: String = "res://audio/music/"
const TITLE: StringName = &"title"
const ZONED: StringName = &"ascent"
## Cross-fade between groups, s.
const FADE: float = 1.5
## Fade between the tracks of a playlist, s.
const PLAYLIST_FADE: float = 2.0
## Cross-fade between Ascent zone tracks, beats; it starts on the bar line.
const ZONE_FADE_BEATS: float = 4.0
const UI_PATH: String = "res://audio/sfx/ui_%s.ogg"
const UI_SOUNDS: Array[StringName] = [&"move", &"select", &"back"]

## The sound effects of the current run.
var sfx: SfxPlayer
## The group that plays now; &"" before the first one.
var group: StringName = &""

## Two music players; a group change fades from one to the other.
var _players: Array[AudioStreamPlayer] = []
var _current: int = 0
var _fades: Array[Tween] = [null, null]
var _ui: Dictionary[StringName, AudioStreamPlayer] = {}
var _run: LevelRun


## Makes the music players, the menu sound players and the SfxPlayer. Music plays on in pause.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i: int in 2:
		var music: AudioStreamPlayer = AudioStreamPlayer.new()
		music.bus = AudioBuses.MUSIC
		add_child(music)
		_players.append(music)
	for sound: StringName in UI_SOUNDS:
		var ui: AudioStreamPlayer = AudioStreamPlayer.new()
		ui.stream = load(UI_PATH % sound) as AudioStream
		ui.bus = AudioBuses.UI
		ui.max_polyphony = 2
		add_child(ui)
		_ui[sound] = ui
	sfx = SfxPlayer.new()
	add_child(sfx)


## Follows Game.run: a new run gets its music and the sound effects.
func _process(_delta: float) -> void:
	var run: LevelRun = Game.run
	if run != _run:
		_run = run
		sfx.attach(run)
		play_group(group_of(run))


## Returns the music group of run: its level's music field, else its tier; TITLE for null.
func group_of(run: LevelRun) -> StringName:
	if run == null:
		return TITLE
	return run.level.music if run.level.music != &"" else run.level.tier


## Plays the tracks of group next, unless it plays already. ZONED plays as zones, the rest as a
## playlist.
func play_group(next: StringName) -> void:
	if next == group:
		return
	group = next
	var tracks: Array[AudioStream] = []
	if next != &"":
		tracks = load_tracks(ROOT + next)
	if next == ZONED:
		play(zones(tracks))
	else:
		play(playlist(tracks))


## Cross-fades from the current music to stream; null fades out to silence.
func play(stream: AudioStream) -> void:
	_fade(_current, 0.0)
	if stream == null:
		return
	_current = 1 - _current
	var music: AudioStreamPlayer = _players[_current]
	music.stream = stream
	music.volume_linear = 0.0
	music.play()
	_fade(_current, 1.0)


## Changes the Ascent track to the one of zone (0 is the first) on the next bar line. Zones
## past the last track keep the last track. Does nothing when no zone stream plays.
func set_zone(zone: int) -> void:
	var music: AudioStreamPlayer = _players[_current]
	var stream: AudioStreamInteractive = music.stream as AudioStreamInteractive
	if stream == null or not music.has_stream_playback():
		return
	var playback: AudioStreamPlaybackInteractive = (
		music.get_stream_playback() as AudioStreamPlaybackInteractive
	)
	playback.switch_to_clip(clampi(zone, 0, stream.clip_count - 1))


## Plays a menu sound: &"move", &"select" or &"back", on the UI bus.
func play_ui(sound: StringName) -> void:
	if not _ui.has(sound):
		push_warning("Music.play_ui: no menu sound %s" % sound)
		return
	_ui[sound].play()


## Returns the audio streams in folder dir, in file name order; empty when dir has none.
func load_tracks(dir: String) -> Array[AudioStream]:
	var tracks: Array[AudioStream] = []
	if not DirAccess.dir_exists_absolute(dir):
		return tracks
	var files: PackedStringArray = ResourceLoader.list_directory(dir)
	files.sort()
	for file: String in files:
		var stream: AudioStream = null
		if not file.ends_with("/"):
			stream = load(dir.path_join(file)) as AudioStream
		if stream != null:
			tracks.append(stream)
	return tracks


## Returns a looping, shuffled playlist of tracks that fades between them; null when empty.
func playlist(tracks: Array[AudioStream]) -> AudioStreamPlaylist:
	if tracks.is_empty():
		return null
	var list: AudioStreamPlaylist = AudioStreamPlaylist.new()
	list.stream_count = tracks.size()
	for i: int in tracks.size():
		list.set_list_stream(i, tracks[i])
	list.shuffle = true
	list.loop = true
	list.fade_time = PLAYLIST_FADE
	return list


## Returns tracks as the clips of one interactive stream that starts on the first clip. Each
## clip loops on its own. A switch waits for the next bar line of the playing clip, then
## cross-fades into the start of the new clip over ZONE_FADE_BEATS. Null when empty.
func zones(tracks: Array[AudioStream]) -> AudioStreamInteractive:
	if tracks.is_empty():
		return null
	var stream: AudioStreamInteractive = AudioStreamInteractive.new()
	stream.clip_count = tracks.size()
	for i: int in tracks.size():
		stream.set_clip_stream(i, tracks[i])
		stream.set_clip_name(i, StringName(tracks[i].resource_path.get_file().get_basename()))
		stream.set_clip_auto_advance(i, AudioStreamInteractive.AUTO_ADVANCE_DISABLED)
	stream.initial_clip = 0
	stream.add_transition(
		AudioStreamInteractive.CLIP_ANY,
		AudioStreamInteractive.CLIP_ANY,
		AudioStreamInteractive.TRANSITION_FROM_TIME_NEXT_BAR,
		AudioStreamInteractive.TRANSITION_TO_TIME_START,
		AudioStreamInteractive.FADE_CROSS,
		ZONE_FADE_BEATS
	)
	return stream


## Fades music player index to the linear volume to over FADE seconds; it stops at 0.
func _fade(index: int, to: float) -> void:
	var music: AudioStreamPlayer = _players[index]
	if _fades[index] != null:
		_fades[index].kill()
	if to == 0.0 and not music.playing:
		return
	var tween: Tween = create_tween()
	tween.tween_property(music, "volume_linear", to, FADE)
	if to == 0.0:
		tween.tween_callback(music.stop)
	_fades[index] = tween
