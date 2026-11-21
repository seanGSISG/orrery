class_name GlassPanel
extends PanelContainer
## A frosted glass panel of the HUD: it blurs and tints the game behind it (glass.gdshader).
## Add its content as a child, like any PanelContainer. The tint, edge, radius and blur come
## from UiLook; the content margins come from the theme type GlassPanel.

const SHADER: Shader = preload("res://ui/look/glass.gdshader")
## Room round the panel for its shadow.
const SHADOW: float = 40.0

var _glass: ShaderMaterial = ShaderMaterial.new()


func _init() -> void:
	theme_type_variation = &"GlassPanel"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_glass.shader = SHADER
	_glass.set_shader_parameter(&"margin", SHADOW)
	_glass.set_shader_parameter(&"radius", UiLook.GLASS_RADIUS)
	_glass.set_shader_parameter(&"tint", UiLook.GLASS_TINT)
	_glass.set_shader_parameter(&"edge", UiLook.GLASS_EDGE)
	_glass.set_shader_parameter(&"blur", UiLook.GLASS_BLUR)
	_glass.set_shader_parameter(&"saturation", UiLook.GLASS_SATURATION)
	_glass.set_shader_parameter(&"brightness", UiLook.GLASS_BRIGHTNESS)
	material = _glass
	resized.connect(_on_resized)


## Draws the panel and the room for its shadow as one rectangle for the shader.
func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size).grow(SHADOW), Color.WHITE)


## Gives the shader the new size of the panel.
func _on_resized() -> void:
	_glass.set_shader_parameter(&"size", size)
	queue_redraw()
