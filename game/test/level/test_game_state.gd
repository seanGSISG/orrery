extends GutTest
## GameState.to_dict() gives the harness plain JSON values for every field.


## Vectors become [x, y, z], names become strings, and every field is there.
func test_to_dict_has_plain_values_for_every_field() -> void:
	var state: GameState = GameState.new()
	state.position = Vector3(1, 2, 3)
	state.level = &"flat"
	var out: Dictionary = state.to_dict()
	var position: Array = out["position"]
	assert_eq(position, [1.0, 2.0, 3.0])
	var level_type: int = typeof(out["level"])
	assert_eq(level_type, TYPE_STRING)
	assert_eq(out.size(), 18)
