class_name Wash
extends ColorRect
## The ground of a menu: the frame behind it, blurred and darkened toward the night colour
## (wash.gdshader). It fills its parent. Set the three values before it enters the tree.

const SHADER: Shader = preload("res://ui/look/wash.gdshader")

## The blur; each step doubles it, and 0 is sharp.
var blur: float = UiLook.WASH_BLUR
## How much night covers the frame: x at the lightest place, y at the darkest.
var dim: Vector2 = Vector2(0.5, 0.82)
## True: the darkest place is the left edge, for a menu on the left. False: the rim.
var left: bool = false


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	var wash: ShaderMaterial = ShaderMaterial.new()
	wash.shader = SHADER
	wash.set_shader_parameter(&"night", UiLook.NIGHT)
	wash.set_shader_parameter(&"blur", blur)
	wash.set_shader_parameter(&"dim", dim)
	wash.set_shader_parameter(&"left", 1.0 if left else 0.0)
	material = wash
