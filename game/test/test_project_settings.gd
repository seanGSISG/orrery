extends GutTest
## Checks the engine settings that docs/plan.md fixes: Jolt physics at 120 ticks per
## second, and strict typing warnings that stop the build.

const STRICT_WARNINGS: PackedStringArray = [
	"untyped_declaration",
	"inferred_declaration",
	"unsafe_property_access",
	"unsafe_method_access",
	"unsafe_cast",
	"unsafe_call_argument",
	"unsafe_void_return",
]
const WARNING_ERROR: int = 2


## The project names Jolt explicitly and the engine ticks physics 120 times per second.
func test_physics_runs_jolt_at_120_ticks() -> void:
	var engine: String = ProjectSettings.get_setting("physics/3d/physics_engine")
	assert_eq(engine, "Jolt Physics")
	assert_eq(Engine.physics_ticks_per_second, 120)


## Each strict typing warning is an error.
func test_strict_typing_warnings_are_errors() -> void:
	for warning: String in STRICT_WARNINGS:
		var level: int = ProjectSettings.get_setting("debug/gdscript/warnings/" + warning)
		assert_eq(level, WARNING_ERROR, warning)
