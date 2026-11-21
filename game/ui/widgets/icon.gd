class_name Icon
extends Control
## One icon of Icons in a layout. Make it with Icon.new(name, color, size); set `icon` or
## `color` to change it.

## The name of the icon in Icons; &"" draws nothing.
var icon: StringName = &"":
	set(value):
		icon = value
		queue_redraw()
var color: Color = UiLook.INK:
	set(value):
		color = value
		queue_redraw()


func _init(icon_name: StringName = &"", icon_color: Color = UiLook.INK, side: float = 28.0) -> void:
	icon = icon_name
	color = icon_color
	custom_minimum_size = Vector2(side, side)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size_flags_vertical = Control.SIZE_SHRINK_CENTER


func _draw() -> void:
	Icons.draw(self, icon, size * 0.5, minf(size.x, size.y), color)
