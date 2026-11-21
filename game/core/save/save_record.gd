class_name SaveRecord
extends RefCounted
## Base of the typed sections of the save file. Each script var of a subclass is one key in
## the file, so a new setting needs only a new var with its default. to_dict() gives the
## plain JSON value of each var. fill() reads such a dictionary back and keeps the default of
## each var that is missing or has the wrong type.


## Returns every script var by name, with vectors as [x, y, z] and names as strings.
func to_dict() -> Dictionary[String, Variant]:
	var out: Dictionary[String, Variant] = {}
	for key: String in _keys():
		var value: Variant = get(key)
		if value is Vector3:
			var vector: Vector3 = value
			out[key] = [vector.x, vector.y, vector.z]
		elif value is StringName:
			var name: StringName = value
			out[key] = String(name)
		else:
			out[key] = value
	return out


## Sets each var from the value of its key in data, converted to the var's type. A missing
## key or a value of another type keeps the var as it is.
func fill(data: Dictionary) -> void:
	for property: Dictionary in get_property_list():
		var usage: int = property["usage"]
		var key: String = property["name"]
		if not usage & PROPERTY_USAGE_SCRIPT_VARIABLE or not data.has(key):
			continue
		var type: int = property["type"]
		var value: Variant = _typed(data[key], type)
		if value != null:
			set(key, value)


## Returns the names of the script vars.
func _keys() -> Array[String]:
	var keys: Array[String] = []
	for property: Dictionary in get_property_list():
		var usage: int = property["usage"]
		if usage & PROPERTY_USAGE_SCRIPT_VARIABLE:
			keys.append(property["name"])
	return keys


## Returns value as type, or null when it does not convert without loss of meaning.
static func _typed(value: Variant, type: int) -> Variant:
	var number: float = value if _is_number(value) else NAN
	match type:
		TYPE_BOOL:
			return value if value is bool else null
		TYPE_INT:
			return roundi(number) if is_finite(number) else null
		TYPE_FLOAT:
			return number if is_finite(number) else null
		TYPE_STRING:
			return value if value is String else null
		TYPE_STRING_NAME:
			return StringName(str(value)) if value is String else null
		TYPE_VECTOR3:
			var items: Array = value if value is Array else []
			if items.size() != 3 or not items.all(_is_number):
				return null
			var x: float = items[0]
			var y: float = items[1]
			var z: float = items[2]
			return Vector3(x, y, z)
	return null


## Returns true for a JSON number. JSON reads every number as a float.
static func _is_number(value: Variant) -> bool:
	return value is float or value is int
