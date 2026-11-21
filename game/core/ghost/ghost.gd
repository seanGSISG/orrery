class_name Ghost
extends RefCounted
## One recorded run: the marble's position and rotation RATE times a second of level clock
## (docs/plan.md §4.4). Playback reads the samples and never re-simulates, so a ghost looks
## the same on any PC.
##
## Record: call record() once per tick with the level clock, then finish() at the finish.
## Sample i is at time i / RATE; the last sample is at duration. Play back with
## transform_at(time). to_bytes() and from_bytes() give the file format:
##
##   offset  size  value (little endian)
##   0       4     "ORGH"
##   4       2     format version (1)
##   6       2     RATE
##   8       4     sample count, u32
##   12      4     duration, f32
##   16      ...   zstd of count samples: position 3 × f32, rotation quaternion 4 × s16
##                 (x, y, z, w, each × 32767)

const RATE: int = 30
const MAGIC: PackedByteArray = [0x4F, 0x52, 0x47, 0x48]
const VERSION: int = 1
const HEADER: int = 16
const SAMPLE_BYTES: int = 20
## Most samples in a ghost: 3 hours. record() stops one sample short, which keeps room for
## the finish sample, so every recorded ghost loads.
const MAX_SAMPLES: int = RATE * 3 * 3600
## A clock value this close under a sample time counts as that time.
const EPSILON: float = 1e-6

var positions: PackedVector3Array = PackedVector3Array()
var rotations: Array[Quaternion] = []
## Time of the last sample, s.
var duration: float = 0.0


## Returns the number of samples.
func size() -> int:
	return positions.size()


## Adds a sample when time has reached the next sample time. Call it each tick; the first
## call adds sample 0.
func record(time: float, position: Vector3, rotation: Quaternion) -> void:
	if time + EPSILON >= float(size()) / RATE and size() < MAX_SAMPLES - 1:
		_add(position, rotation)
		duration = float(size() - 1) / RATE


## Adds the last sample at time, the finish time. After it, the ghost is complete.
func finish(time: float, position: Vector3, rotation: Quaternion) -> void:
	_add(position, rotation)
	duration = maxf(time, duration)


## Returns the marble's pose at time: a blend of the two samples around it. Before the start
## it is the first sample, after the end the last. Identity for an empty ghost.
func transform_at(time: float) -> Transform3D:
	var last: int = size() - 1
	if last < 0:
		return Transform3D.IDENTITY
	if last == 0 or time >= duration:
		return _pose(last, last, 0.0)
	time = maxf(time, 0.0)
	var i: int = mini(floori(time * RATE), last - 1)
	var start: float = float(i) / RATE
	var end: float = duration if i + 1 == last else float(i + 1) / RATE
	var weight: float = clampf((time - start) / (end - start), 0.0, 1.0) if end > start else 1.0
	return _pose(i, i + 1, weight)


## Returns the ghost in the file format above.
func to_bytes() -> PackedByteArray:
	var samples: PackedByteArray = PackedByteArray()
	samples.resize(size() * SAMPLE_BYTES)
	for i: int in size():
		var at: int = i * SAMPLE_BYTES
		var position: Vector3 = positions[i]
		var rotation: Quaternion = rotations[i].normalized()
		samples.encode_float(at, position.x)
		samples.encode_float(at + 4, position.y)
		samples.encode_float(at + 8, position.z)
		samples.encode_s16(at + 12, roundi(rotation.x * 32767))
		samples.encode_s16(at + 14, roundi(rotation.y * 32767))
		samples.encode_s16(at + 16, roundi(rotation.z * 32767))
		samples.encode_s16(at + 18, roundi(rotation.w * 32767))
	var out: PackedByteArray = MAGIC.duplicate()
	out.resize(HEADER)
	out.encode_u16(4, VERSION)
	out.encode_u16(6, RATE)
	out.encode_u32(8, size())
	out.encode_float(12, duration)
	out.append_array(samples.compress(FileAccess.COMPRESSION_ZSTD))
	return out


## Returns the ghost in bytes, or null when bytes are not a ghost of this format version.
static func from_bytes(bytes: PackedByteArray) -> Ghost:
	if bytes.size() < HEADER or bytes.slice(0, 4) != MAGIC:
		return null
	var count: int = bytes.decode_u32(8)
	if bytes.decode_u16(4) != VERSION or bytes.decode_u16(6) != RATE or count < 1:
		return null
	if count > MAX_SAMPLES:
		return null
	var samples: PackedByteArray = bytes.slice(HEADER).decompress(
		count * SAMPLE_BYTES, FileAccess.COMPRESSION_ZSTD
	)
	if samples.size() != count * SAMPLE_BYTES:
		return null
	var ghost: Ghost = Ghost.new()
	ghost.duration = bytes.decode_float(12)
	for i: int in count:
		var at: int = i * SAMPLE_BYTES
		var position: Vector3 = Vector3(
			samples.decode_float(at), samples.decode_float(at + 4), samples.decode_float(at + 8)
		)
		var rotation: Quaternion = Quaternion(
			samples.decode_s16(at + 12) / 32767.0,
			samples.decode_s16(at + 14) / 32767.0,
			samples.decode_s16(at + 16) / 32767.0,
			samples.decode_s16(at + 18) / 32767.0
		)
		ghost._add(position, rotation)
	return ghost if is_finite(ghost.duration) else null


## Appends one sample with a unit rotation.
func _add(position: Vector3, rotation: Quaternion) -> void:
	positions.append(position)
	rotations.append(rotation.normalized() if rotation.length_squared() > 0.0 else Quaternion())


## Returns the pose weight of the way from sample a to sample b.
func _pose(a: int, b: int, weight: float) -> Transform3D:
	var rotation: Quaternion = rotations[a].slerp(rotations[b], weight)
	return Transform3D(Basis(rotation), positions[a].lerp(positions[b], weight))
