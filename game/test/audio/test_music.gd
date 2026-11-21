extends GutTest
## Music and buses, with the placeholder loops in res://test/audio/loops/ (120 BPM, 4/4, two
## bars, from tools/audio/sfx/synth_sfx.py). The zone test mixes the stream by hand, so it
## counts frames and does not wait in real time.

const LOOPS: String = "res://test/audio/loops"
const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
## One bar of the placeholder loops: 4 beats at 120 BPM, s.
const BAR: float = 2.0
## Mixing step of the zone test, s.
const STEP: float = 0.01


## Mixes playback for seconds, in steps of STEP.
func _mix(playback: AudioStreamPlayback, seconds: float) -> void:
	var frames: int = roundi(STEP * AudioServer.get_mix_rate())
	for i: int in roundi(seconds / STEP):
		playback.mix_audio(1.0, frames)


## Returns the Music player that plays a stream of class type; null when none does.
func _playing(type: StringName) -> AudioStreamPlayer:
	for node: Node in Music.get_children():
		var music: AudioStreamPlayer = node as AudioStreamPlayer
		if music != null and music.playing and music.stream.get_class() == type:
			return music
	return null


## Stops the music at once and gives the audio thread time to let go of the streams, so
## that no stream is still playing when the tests quit.
func _silence() -> void:
	Music.play(null)
	for node: Node in Music.get_children():
		var music: AudioStreamPlayer = node as AudioStreamPlayer
		if music != null:
			music.stop()
	await wait_seconds(0.1)


func test_tracks_load_with_their_beat_grid() -> void:
	var tracks: Array[AudioStream] = Music.load_tracks(LOOPS)
	assert_eq(tracks.size(), 2, "both loops, in name order")
	for track: AudioStream in tracks:
		var ogg: AudioStreamOggVorbis = track as AudioStreamOggVorbis
		assert_true(ogg.loop, "the .import sets the loop")
		assert_eq(ogg.bpm, 120.0)
		assert_eq(ogg.beat_count, 8)
		assert_eq(ogg.bar_beats, 4)
	assert_eq(Music.load_tracks("res://test/audio/none").size(), 0, "a missing folder has none")


func test_zone_track_changes_only_on_the_next_bar_line() -> void:
	var stream: AudioStreamInteractive = Music.zones(Music.load_tracks(LOOPS))
	var playback: AudioStreamPlaybackInteractive = (
		stream.instantiate_playback() as AudioStreamPlaybackInteractive
	)
	playback.start(0.0)
	_mix(playback, BAR * 1.25)
	assert_eq(playback.get_current_clip_index(), 0)
	playback.switch_to_clip(1)
	var at: float = BAR * 1.25
	while playback.get_current_clip_index() == 0 and at < BAR * 4.0:
		_mix(playback, STEP)
		at += STEP
	assert_eq(playback.get_current_clip_index(), 1, "the switch happens")
	assert_almost_eq(at, BAR * 2.0, STEP * 1.5, "on the bar line after the request, not before")


func test_set_zone_waits_for_the_bar_line() -> void:
	Music.play(Music.zones(Music.load_tracks(LOOPS)))
	var music: AudioStreamPlayer = _playing(&"AudioStreamInteractive")
	assert_not_null(music, "a music player plays the zones")
	if music != null:
		var playback: AudioStreamPlaybackInteractive = (
			music.get_stream_playback() as AudioStreamPlaybackInteractive
		)
		Music.set_zone(7)
		assert_eq(playback.get_current_clip_index(), 0, "no switch before the bar line")
	await _silence()


func test_tier_playlist_shuffles_loops_and_fades() -> void:
	var list: AudioStreamPlaylist = Music.playlist(Music.load_tracks(LOOPS))
	assert_eq(list.stream_count, 2)
	assert_true(list.shuffle)
	assert_true(list.loop)
	assert_eq(list.fade_time, Music.PLAYLIST_FADE)
	assert_null(Music.playlist([]), "no tracks, no playlist")


func test_group_is_the_level_music_else_its_tier() -> void:
	assert_eq(Music.group_of(null), Music.TITLE, "no run plays the title music")
	assert_eq(Music.group, Music.group_of(Game.run), "a group plays from the start")
	var level: Level = FLAT.instantiate() as Level
	level.tier = &"beginner"
	var run: LevelRun = LevelRun.create(level)
	assert_eq(Music.group_of(run), &"beginner")
	level.music = &"ascent"
	assert_eq(Music.group_of(run), &"ascent")
	run.free()


func test_music_plays_on_the_music_bus() -> void:
	Music.play(Music.playlist(Music.load_tracks(LOOPS)))
	var music: AudioStreamPlayer = _playing(&"AudioStreamPlaylist")
	assert_not_null(music, "a music player plays the playlist")
	if music != null:
		assert_eq(music.bus, AudioBuses.MUSIC)
	await _silence()


func test_buses_send_to_master_and_volumes_go_through_settings() -> void:
	for bus: StringName in [AudioBuses.MUSIC, AudioBuses.SFX, AudioBuses.UI]:
		var index: int = AudioServer.get_bus_index(bus)
		assert_gt(index, 0, "%s exists" % bus)
		assert_eq(AudioServer.get_bus_send(index), AudioBuses.MASTER)
	var settings: Settings = Settings.new()
	AudioBuses.set_volume(AudioBuses.SFX, 0.5, settings)
	assert_almost_eq(AudioBuses.volume(AudioBuses.SFX), 0.5, 0.001)
	assert_almost_eq(settings.sfx_volume, 0.5, 0.001, "the settings keep the volume")
	AudioBuses.set_volume(AudioBuses.SFX, 3.0, settings)
	assert_almost_eq(AudioBuses.volume(AudioBuses.SFX), 1.0, 0.001, "clamped to 1")
	settings.music_volume = 0.25
	AudioBuses.apply(settings)
	assert_almost_eq(AudioBuses.volume(AudioBuses.MUSIC), 0.25, 0.001, "apply sets each bus")
	AudioBuses.apply(Settings.new())


func test_a_run_that_game_loads_has_sound_before_its_first_tick() -> void:
	var run: LevelRun = Game.load_level(&"flat")
	run.auto_step = false
	run.feedback.emit(&"gem.collect", 1.0, Vector3.ZERO)
	var gem: AudioStreamPlayer = Music.sfx.player(&"gem") as AudioStreamPlayer
	assert_true(gem.playing, "the SfxPlayer attached when Game added the run")
	Game.remove_child(run)
	run.free()
	Game.run = null
	Music.sfx.attach(null)
