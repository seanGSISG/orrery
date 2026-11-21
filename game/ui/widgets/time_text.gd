class_name TimeText
extends RefCounted
## Writes level times as text. Hundredths are cut, not rounded, so the text never shows a
## better time than the clock.


## Returns seconds as minutes, seconds and hundredths: "0:46.82".
static func full(seconds: float) -> String:
	return minutes(seconds) + hundredths(seconds)


## Returns seconds as a target time: "0:48" for whole seconds, else all of it, "0:46.82".
static func target(seconds: float) -> String:
	return full(seconds).trim_suffix(".00")


## Returns seconds as a difference: "4.38" under one minute, "1:04.38" from one minute.
static func difference(seconds: float) -> String:
	return full(seconds).trim_prefix("0:").trim_prefix("0")


## Returns seconds as minutes and seconds, with the hundredths cut off: "0:46".
static func minutes(seconds: float) -> String:
	var whole: int = floori(_hundredths(seconds) / 100.0)
	return "%d:%02d" % [floori(whole / 60.0), whole % 60]


## Returns the hundredths of seconds with their point: ".82".
static func hundredths(seconds: float) -> String:
	return ".%02d" % (_hundredths(seconds) % 100)


## Returns seconds in whole hundredths. The small sum hides float error in tick counts.
static func _hundredths(seconds: float) -> int:
	return floori(maxf(seconds, 0.0) * 100.0 + 0.0001)
