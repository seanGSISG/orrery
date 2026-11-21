extends Node
## The debug harness (docs/plan.md §4.5): a JSON-RPC 2.0 server on 127.0.0.1 that lets an
## agent drive the game from outside. Each request and each response is one line of JSON.
## main.gd adds it to the root only in a debug build, and only with the user argument
## --harness-port=<port>. tools/harness/ is the client.
##
## The harness owns time. It turns off the run's auto_step and steps the run itself, so that
## pause, step and set_time_scale count real ticks (docs/design/core-runtime.md §3, F14).
## The harness input (HarnessSource) replaces the player's input and goes through InputHub
## like it.

const HOST: String = "127.0.0.1"
const PORT_ARG: String = "--harness-port="
## A request line longer than this closes the connection.
const MAX_LINE: int = 1 << 20

const PARSE_ERROR: int = -32700
const INVALID_REQUEST: int = -32600
const METHOD_NOT_FOUND: int = -32601
const INVALID_PARAMS: int = -32602
## The command needs a level run, and no level is loaded.
const NO_RUN: int = -32000
## The level, camera shot or setting does not exist.
const NOT_FOUND: int = -32001
## The command is a stub until a later ticket.
const NOT_AVAILABLE: int = -32002
## The display renders nothing (godot --headless), so there is no frame to save.
const NO_FRAME: int = -32003

var paused: bool = false
## Ticks per physics frame while not paused.
var time_scale: float = 1.0

var _server: TCPServer = TCPServer.new()
var _clients: Array[Client] = []
var _source: HarnessSource = HarnessSource.new()
var _log: HarnessLog = HarnessLog.new()
## Ticks owed to the run; set_time_scale below 1 makes fractions.
var _owed: float = 0.0
var _commands: Dictionary[String, Callable] = {
	"ping": _ping,
	"quit": _quit,
	"load_level": _load_level,
	"load_mode": _load_mode,
	"state": _state,
	"input": _input_command,
	"step": _step,
	"pause": _pause,
	"resume": _resume,
	"set_time_scale": _set_time_scale,
	"teleport": _teleport,
	"screenshot": _screenshot,
	"logs": _logs,
	"set_setting": _set_setting,
}


## Returns the port in the user arguments, or 0 when there is none.
static func port_in(args: PackedStringArray) -> int:
	for arg: String in args:
		if arg.begins_with(PORT_ARG):
			return arg.trim_prefix(PORT_ARG).to_int()
	return 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	# Run before LevelRun._physics_process, so that a new run never steps itself.
	process_physics_priority = -100
	OS.add_logger(_log)
	InputHub.use_source(_source)
	var port: int = port_in(OS.get_cmdline_user_args())
	var error: Error = _server.listen(port, HOST) if port > 0 else ERR_INVALID_PARAMETER
	if error != OK:
		push_error("Harness: cannot listen on %s:%d (%s)" % [HOST, port, error_string(error)])
		return
	print("ORRERY harness listening on %s:%d" % [HOST, port])


func _exit_tree() -> void:
	OS.remove_logger(_log)
	_server.stop()


func _physics_process(_delta: float) -> void:
	var run: LevelRun = Game.run
	if run == null:
		return
	run.auto_step = false
	if paused:
		return
	_owed += time_scale
	while _owed >= 1.0:
		_owed -= 1.0
		run.step(InputHub.next_input(run.state))


func _process(_delta: float) -> void:
	while _server.is_connection_available():
		_clients.append(Client.new(_server.take_connection()))
	for client: Client in _clients.duplicate():
		if not client.receive():
			_clients.erase(client)
		elif not client.busy:
			_serve(client)


## Answers every complete line in the client's buffer, in order. A command that waits for a
## frame (screenshot) holds the next lines until it has answered.
func _serve(client: Client) -> void:
	client.busy = true
	var line: String = client.next_line()
	while line != "":
		var reply: String = await _reply(line)
		if reply != "":
			client.send(reply)
		line = client.next_line()
	client.busy = false


## Returns the response line for one request line, or "" for a notification.
func _reply(line: String) -> String:
	var json: JSON = JSON.new()
	if json.parse(line) != OK:
		return _response(null, Failure.new(PARSE_ERROR, json.get_error_message()))
	if not json.data is Dictionary:
		return _response(null, Failure.new(INVALID_REQUEST, "the request is not an object"))
	var request: Dictionary = json.data
	var id: Variant = _plain_id(request.get("id"))
	var method: Variant = request.get("method")
	var params: Variant = request.get("params", {})
	var result: Variant
	var version: Variant = request.get("jsonrpc")
	if not (version is String and version == "2.0") or not method is String:
		result = Failure.new(INVALID_REQUEST, "a request needs jsonrpc 2.0 and a method")
	elif not _commands.has(method):
		result = Failure.new(METHOD_NOT_FOUND, "no method %s" % method)
	elif not params is Dictionary:
		result = Failure.new(INVALID_PARAMS, "params must be an object")
	else:
		var command: Callable = _commands[method]
		var fields: Dictionary = params
		result = await command.call(Params.new(fields))
	if not request.has("id"):
		return ""
	return _response(id, result)


static func _response(id: Variant, result: Variant) -> String:
	var out: Dictionary = {"jsonrpc": "2.0", "id": id}
	var failure: Failure = result if result is Failure else null
	if failure != null:
		out["error"] = {"code": failure.code, "message": failure.message}
	else:
		out["result"] = result
	return JSON.stringify(out, "", false, true)


## JSON numbers parse as floats; give an integer id back as an integer.
static func _plain_id(id: Variant) -> Variant:
	if id is float:
		var number: float = id
		if number == floorf(number):
			return int(number)
	return id


static func _no_run() -> Failure:
	return Failure.new(NO_RUN, "no level is loaded; call load_level first")


func _ping(_params: Params) -> Variant:
	return "pong"


## Answers, then quits after the answer is sent.
func _quit(_params: Params) -> Variant:
	get_tree().quit.call_deferred()
	return {}


func _load_level(params: Params) -> Variant:
	var id: String = params.text("id", "", true)
	if params.failed():
		return params.failure
	var run: LevelRun = Game.load_level(StringName(id))
	if run == null:
		return Failure.new(NOT_FOUND, "no level %s" % id)
	run.auto_step = false
	_owed = 0.0
	return Game.snapshot().to_dict()


func _load_mode(_params: Params) -> Variant:
	return Failure.new(NOT_AVAILABLE, "load_mode: modes arrive with #22 and #27")


func _state(_params: Params) -> Variant:
	return Game.snapshot().to_dict()


## Holds move, jump, use and camera [yaw, pitch] for frames ticks (default: until the next
## input). A left-out camera keeps the current angles.
func _input_command(params: Params) -> Variant:
	var input: MarbleInput = MarbleInput.new()
	input.move = params.vector2("move", Vector2.ZERO)
	input.jump = params.flag("jump", false)
	input.use = params.flag("use", false)
	var camera: Vector2 = params.vector2("camera", _source.camera())
	input.camera_yaw = camera.x
	input.camera_pitch = camera.y
	var frames: int = params.integer("frames", -1)
	if params.failed():
		return params.failure
	_source.hold(input, frames)
	return {"frames": frames}


## Steps the run frames ticks at once and pauses it.
func _step(params: Params) -> Variant:
	var frames: int = params.integer("frames", 1)
	if frames < 1:
		params.fail("frames must be at least 1")
	if params.failed():
		return params.failure
	var run: LevelRun = Game.run
	if run == null:
		return _no_run()
	paused = true
	run.auto_step = false
	for _i: int in frames:
		run.step(InputHub.next_input(run.state))
	return Game.snapshot().to_dict()


func _pause(_params: Params) -> Variant:
	paused = true
	return {"paused": paused}


func _resume(_params: Params) -> Variant:
	paused = false
	_owed = 0.0
	return {"paused": paused}


func _set_time_scale(params: Params) -> Variant:
	var scale: float = params.number("scale", 1.0, true)
	if scale < 0.0 or scale > 64.0:
		params.fail("scale must be in 0..64")
	if params.failed():
		return params.failure
	time_scale = scale
	return {"scale": time_scale}


## Puts the marble at position with velocity (default still). GameState shows it after the
## next tick, because only the run writes GameState.
func _teleport(params: Params) -> Variant:
	var at: Vector3 = params.vector3("position", Vector3.ZERO, true)
	var velocity: Vector3 = params.vector3("velocity", Vector3.ZERO)
	if params.failed():
		return params.failure
	var run: LevelRun = Game.run
	if run == null:
		return _no_run()
	run.marble.teleport(at, velocity)
	return {}


## Saves the next rendered frame as a PNG at path (default user://screenshots/). With shot,
## it renders from the level's Camera3D of that name. blank is true when the frame has
## almost one colour.
func _screenshot(params: Params) -> Variant:
	var path: String = params.text("path", "")
	var shot: String = params.text("shot", "")
	if params.failed():
		return params.failure
	# The headless display server never draws, so frame_post_draw never comes.
	if DisplayServer.get_name() == "headless":
		return Failure.new(NO_FRAME, "no rendered frame; godot --headless renders nothing")
	var found: Variant = _shot_camera(shot)
	if found is Failure:
		return found
	var camera: Camera3D = found
	var image: Image = await _render(camera)
	if image == null or image.is_empty():
		return Failure.new(NO_FRAME, "the viewport gave no image")
	if path == "":
		var stem: String = shot if shot != "" else "frame"
		path = "user://screenshots/%s-%d.png" % [stem, Time.get_ticks_msec()]
	return _save(image, ProjectSettings.globalize_path(path))


## Returns the level's Camera3D named shot, null for no shot, or a Failure.
static func _shot_camera(shot: String) -> Variant:
	if shot == "":
		return null
	var run: LevelRun = Game.run
	if run == null:
		return _no_run()
	var found: Array[Node] = run.level.find_children(shot, "Camera3D", true, false)
	if found.is_empty():
		return Failure.new(NOT_FOUND, "no Camera3D named %s in the level" % shot)
	return found[0]


## Waits for the next drawn frame and returns it, seen from camera when it is set.
func _render(camera: Camera3D) -> Image:
	var viewport: Viewport = get_viewport()
	var before: Camera3D = viewport.get_camera_3d()
	if camera != null:
		camera.make_current()
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image: Image = viewport.get_texture().get_image()
	if camera != null and before != null:
		before.make_current()
	return image


## Writes image to path and returns the screenshot result.
static func _save(image: Image, path: String) -> Variant:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var error: Error = image.save_png(path)
	if error != OK:
		return Failure.new(INVALID_PARAMS, "cannot save %s (%s)" % [path, error_string(error)])
	return {
		"path": path,
		"width": image.get_width(),
		"height": image.get_height(),
		"blank": _blank(image),
		"adapter": RenderingServer.get_video_adapter_name(),
	}


## True when the luminance of a sample grid varies by less than 0.02.
static func _blank(image: Image) -> bool:
	var low: float = 1.0
	var high: float = 0.0
	for y: int in range(0, image.get_height(), 8):
		for x: int in range(0, image.get_width(), 8):
			var lum: float = image.get_pixel(x, y).get_luminance()
			low = minf(low, lum)
			high = maxf(high, lum)
	return high - low < 0.02


## Returns the log lines after sequence number since (default 0: all kept lines).
func _logs(params: Params) -> Variant:
	var since: int = params.integer("since", 0)
	if params.failed():
		return params.failure
	return {"lines": _log.since(since)}


## Sets an existing project setting, converted to the type it has. #23 routes this through
## the settings store.
func _set_setting(params: Params) -> Variant:
	var key: String = params.text("key", "", true)
	var value: Variant = params.any("value")
	if params.failed():
		return params.failure
	if not ProjectSettings.has_setting(key):
		return Failure.new(NOT_FOUND, "no setting %s" % key)
	var old: Variant = ProjectSettings.get_setting(key)
	ProjectSettings.set_setting(key, type_convert(value, typeof(old)))
	return {"key": key, "value": ProjectSettings.get_setting(key)}


## A JSON-RPC error: code and message.
class Failure:
	extends RefCounted
	var code: int
	var message: String

	func _init(error_code: int, error_message: String) -> void:
		code = error_code
		message = error_message


## Typed reads of a request's params. A read of a wrong type or of a missing required key
## records failure and returns the default; check failed() before you act.
class Params:
	extends RefCounted
	var failure: Failure
	var _data: Dictionary

	func _init(data: Dictionary) -> void:
		_data = data

	## True after a read failed.
	func failed() -> bool:
		return failure != null

	## Records the first failure as invalid params.
	func fail(message: String) -> void:
		if failure == null:
			failure = Failure.new(INVALID_PARAMS, message)

	func text(key: String, default: String, required: bool = false) -> String:
		var value: Variant = _read(key, TYPE_STRING, required)
		return value if value is String else default

	func flag(key: String, default: bool) -> bool:
		var value: Variant = _read(key, TYPE_BOOL, false)
		return value if value is bool else default

	func number(key: String, default: float, required: bool = false) -> float:
		var value: Variant = _read(key, TYPE_FLOAT, required)
		return value if value is float else default

	func integer(key: String, default: int) -> int:
		var value: float = number(key, default)
		if value != floorf(value):
			fail("%s must be an integer" % key)
		return int(value)

	func vector2(key: String, default: Vector2) -> Vector2:
		var parts: PackedFloat64Array = _numbers(key, 2, false)
		return Vector2(parts[0], parts[1]) if parts.size() == 2 else default

	func vector3(key: String, default: Vector3, required: bool = false) -> Vector3:
		var parts: PackedFloat64Array = _numbers(key, 3, required)
		return Vector3(parts[0], parts[1], parts[2]) if parts.size() == 3 else default

	## Any JSON value; the key is required.
	func any(key: String) -> Variant:
		if not _data.has(key):
			fail("%s is required" % key)
		return _data.get(key)

	func _read(key: String, type: Variant.Type, required: bool) -> Variant:
		if not _data.has(key):
			if required:
				fail("%s is required" % key)
			return null
		var value: Variant = _data[key]
		if typeof(value) != type:
			fail("%s must be a %s" % [key, type_string(type)])
			return null
		return value

	func _numbers(key: String, size: int, required: bool) -> PackedFloat64Array:
		var value: Variant = _read(key, TYPE_ARRAY, required)
		var out: PackedFloat64Array = []
		if value == null:
			return out
		var items: Array = value
		for item: Variant in items:
			if item is float:
				var part: float = item
				out.append(part)
		if out.size() != size or items.size() != size:
			fail("%s must be %d numbers" % [key, size])
			out.clear()
		return out


## One TCP connection and its unread bytes.
class Client:
	extends RefCounted
	## True while the harness answers this client's lines.
	var busy: bool = false
	var _peer: StreamPeerTCP
	var _buffer: PackedByteArray = []

	func _init(peer: StreamPeerTCP) -> void:
		_peer = peer

	## Reads the waiting bytes. Returns false when the connection is gone or sent a line
	## longer than MAX_LINE.
	func receive() -> bool:
		_peer.poll()
		if _peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			return false
		var count: int = _peer.get_available_bytes()
		if count > 0:
			var got: Array = _peer.get_data(count)
			var bytes: PackedByteArray = got[1]
			_buffer.append_array(bytes)
		if _buffer.size() > MAX_LINE and _buffer.find(10) < 0:
			_peer.disconnect_from_host()
			return false
		return true

	## Removes and returns the next complete line that is not empty, or "".
	func next_line() -> String:
		var end: int = _buffer.find(10)
		while end >= 0:
			var line: String = _buffer.slice(0, end).get_string_from_utf8().strip_edges()
			_buffer = _buffer.slice(end + 1)
			if line != "":
				return line
			end = _buffer.find(10)
		return ""

	func send(line: String) -> void:
		_peer.put_data((line + "\n").to_utf8_buffer())
