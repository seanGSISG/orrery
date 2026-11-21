class_name HarnessLog
extends Logger
## Keeps the last LIMIT engine log lines (prints, warnings and errors) for the `logs` command.
## Add it with OS.add_logger(). The engine can log from any thread, so a mutex guards it.

const LIMIT: int = 2000

## Sequence number of the next line. The first line is 1.
var _next: int = 1
var _lines: Array[Dictionary] = []
var _mutex: Mutex = Mutex.new()


## Returns the kept lines with a sequence number above since, oldest first, as
## {seq, text, error}.
func since(seq: int) -> Array[Dictionary]:
	_mutex.lock()
	var out: Array[Dictionary] = []
	for line: Dictionary in _lines:
		var line_seq: int = line["seq"]
		if line_seq > seq:
			out.append(line)
	_mutex.unlock()
	return out


func _log_message(message: String, error: bool) -> void:
	_add(message.trim_suffix("\n"), error)


func _log_error(
	function: String,
	file: String,
	line: int,
	code: String,
	rationale: String,
	_editor_notify: bool,
	error_type: int,
	_script_backtraces: Array[ScriptBacktrace]
) -> void:
	var kind: String = "WARNING" if error_type == ERROR_TYPE_WARNING else "ERROR"
	var text: String = rationale if not rationale.is_empty() else code
	_add("%s: %s (%s:%d in %s)" % [kind, text, file, line, function], true)


func _add(text: String, error: bool) -> void:
	_mutex.lock()
	_lines.append({"seq": _next, "text": text, "error": error})
	_next += 1
	if _lines.size() > LIMIT:
		_lines.pop_front()
	_mutex.unlock()
