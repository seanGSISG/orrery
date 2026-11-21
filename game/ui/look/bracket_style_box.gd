class_name BracketStyleBox
extends StyleBox
## A focus mark: four corner brackets round the item, over a faint fill. UiTheme puts it in
## the Theme as the `focus` style, so a control draws it like any other StyleBox.

## Colour of the brackets.
@export var color: Color = Color.WHITE
## Colour behind the item.
@export var fill: Color = Color.TRANSPARENT
## Length of each arm of a bracket, and its width.
@export var arm: float = 26.0
@export var width: float = 3.0


## Draws the fill and the four brackets in rect.
func _draw(to_canvas_item: RID, rect: Rect2) -> void:
	RenderingServer.canvas_item_add_rect(to_canvas_item, rect, fill)
	var reach: Vector2 = Vector2(minf(arm, rect.size.x * 0.5), minf(arm, rect.size.y * 0.5))
	for corner: Vector2 in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1)]:
		var at: Vector2 = rect.position + rect.size * corner
		# Each arm runs from the corner toward the middle of the rectangle.
		var along: Vector2 = Vector2(1.0 - 2.0 * corner.x, 1.0 - 2.0 * corner.y)
		var across: Rect2 = Rect2(at, Vector2(reach.x * along.x, width * along.y)).abs()
		var down: Rect2 = Rect2(at, Vector2(width * along.x, reach.y * along.y)).abs()
		RenderingServer.canvas_item_add_rect(to_canvas_item, across, color)
		RenderingServer.canvas_item_add_rect(to_canvas_item, down, color)
