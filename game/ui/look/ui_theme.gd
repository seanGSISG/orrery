class_name UiTheme
extends RefCounted
## Builds the one Theme of the HUD and the menus from UiLook. Ui sets it on its root, so
## every control below gets it. A screen styles a control only by naming one of the theme
## types below in `theme_type_variation`; it sets no font, colour or style on the node.
##
## Text (Label): Logo, Title, Heading, Subtitle, LevelName, Row, RowFocus, RowAccent, MenuText,
## MenuTextFocus, MenuTextOff, Data (the default Label), DataStrong, DataAccent, Caps,
## CapsStrong, CapsGold, BestTime, BestTimeNone, BigTime, HudTarget, HudTargetGold, GlyphText.
## Panels (PanelContainer): GlyphPad, GlyphKey (button glyphs), GlassPanel (its margins).
## Lines (HSeparator): Rule, RuleStrong.
## Spacing: Gap<n> (BoxContainer) for each n in GAPS, made by row() and column(); Safe
## (MarginContainer), the distance of the content from the screen edges; TableLine
## (MarginContainer), the room round one line of a table.
## MenuItem and LevelNode read their `normal` and `focus` styles from the type MenuItem.

## The gaps between the children of a row or a column.
const GAPS: Array[int] = [0, 8, 14, 24, 44]


## Returns the Theme.
static func build() -> Theme:
	var theme: Theme = Theme.new()
	theme.default_font = UiLook.DATA_FONT
	theme.default_font_size = UiLook.DATA_SIZE
	theme.set_color(&"font_color", &"Label", UiLook.INK_2)
	_text(theme, &"Logo", UiLook.TITLE_FONT, UiLook.LOGO_SIZE, UiLook.INK)
	_text(theme, &"Title", UiLook.TITLE_FONT, UiLook.TITLE_SIZE, UiLook.INK)
	_text(theme, &"Heading", UiLook.TITLE_FONT, UiLook.HEADING_SIZE, UiLook.INK)
	_text(theme, &"Subtitle", UiLook.TITLE_FONT, UiLook.ROW_SIZE, UiLook.INK_2)
	_text(theme, &"LevelName", UiLook.TITLE_FONT, UiLook.LEVEL_NAME_SIZE, UiLook.INK)
	_text(theme, &"Row", UiLook.NAME_FONT, UiLook.ROW_SIZE, UiLook.INK_2)
	_text(theme, &"RowFocus", UiLook.NAME_FONT, UiLook.ROW_SIZE, UiLook.INK)
	_text(theme, &"RowAccent", UiLook.TITLE_FONT, UiLook.ROW_SIZE, UiLook.ACCENT)
	_text(theme, &"MenuText", UiLook.NAME_FONT, UiLook.MENU_SIZE, UiLook.INK_2)
	_text(theme, &"MenuTextFocus", UiLook.NAME_FONT, UiLook.MENU_SIZE, UiLook.INK)
	_text(theme, &"MenuTextOff", UiLook.NAME_FONT, UiLook.MENU_SIZE, UiLook.INK_3)
	_text(theme, &"Data", UiLook.DATA_FONT, UiLook.DATA_SIZE, UiLook.INK_2)
	_text(theme, &"DataStrong", UiLook.DATA_STRONG_FONT, UiLook.DATA_SIZE + 4, UiLook.INK)
	_text(theme, &"DataAccent", UiLook.DATA_STRONG_FONT, UiLook.DATA_SIZE + 4, UiLook.ACCENT)
	var caps: FontVariation = FontVariation.new()
	caps.base_font = UiLook.DATA_FONT
	caps.spacing_glyph = UiLook.CAPS_SPACING
	_text(theme, &"Caps", caps, UiLook.CAPS_SIZE, UiLook.INK_3)
	_text(theme, &"CapsStrong", caps, UiLook.CAPS_SIZE + 3, UiLook.INK)
	_text(theme, &"CapsGold", caps, UiLook.CAPS_SIZE + 3, UiLook.GOLD)
	_text(theme, &"BestTime", UiLook.DATA_STRONG_FONT, UiLook.TIME_SIZE, UiLook.INK)
	_text(theme, &"BestTimeNone", UiLook.DATA_FONT, UiLook.TIME_SIZE, UiLook.INK_3)
	_text(theme, &"BigTime", UiLook.DATA_STRONG_FONT, UiLook.BIG_TIME_SIZE, UiLook.INK)
	_text(theme, &"HudTarget", UiLook.DATA_FONT, UiLook.HUD_TARGET_SIZE, UiLook.INK_2)
	_text(theme, &"HudTargetGold", UiLook.DATA_FONT, UiLook.HUD_TARGET_SIZE, UiLook.GOLD)
	_text(theme, &"GlyphText", UiLook.DATA_STRONG_FONT, UiLook.GLYPH_SIZE, UiLook.INK)
	_panel(theme, &"GlyphPad", _glyph_box(22, Color(UiLook.NIGHT, 0.8)))
	_panel(theme, &"GlyphKey", _glyph_box(8, Color(UiLook.NIGHT, 0.8)))
	_panel(theme, &"GlassPanel", _margins(StyleBoxEmpty.new(), 30.0, 12.0))
	_rule(theme, &"Rule", UiLook.LINE_3, 1)
	_rule(theme, &"RuleStrong", UiLook.LINE, 2)
	for gap: int in GAPS:
		theme.set_type_variation("Gap%d" % gap, &"BoxContainer")
		theme.set_constant(&"separation", "Gap%d" % gap, gap)
	theme.set_type_variation(&"Safe", &"MarginContainer")
	for side: StringName in [&"margin_left", &"margin_right"]:
		theme.set_constant(side, &"Safe", roundi(UiLook.SAFE.x))
	for side: StringName in [&"margin_top", &"margin_bottom"]:
		theme.set_constant(side, &"Safe", roundi(UiLook.SAFE.y))
	theme.set_type_variation(&"TableLine", &"MarginContainer")
	for side: StringName in [&"margin_left", &"margin_right"]:
		theme.set_constant(side, &"TableLine", 8)
	for side: StringName in [&"margin_top", &"margin_bottom"]:
		theme.set_constant(side, &"TableLine", 18)
	theme.set_stylebox(&"normal", &"MenuItem", _margins(StyleBoxEmpty.new(), 30.0, 2.0))
	var focus: BracketStyleBox = BracketStyleBox.new()
	focus.color = UiLook.ACCENT
	focus.fill = UiLook.ACCENT_FILL
	theme.set_stylebox(&"focus", &"MenuItem", focus)
	return theme


## Returns a Label of the theme type variation that shows text (a translation key or final
## text).
static func label(text: String, variation: StringName = &"Data") -> Label:
	var made: Label = Label.new()
	made.text = text
	made.theme_type_variation = variation
	return made


## Returns an HBoxContainer whose children are gap apart; gap is one of GAPS.
static func row(gap: int) -> HBoxContainer:
	assert(gap in GAPS, "UiTheme.row: no Gap%d in the Theme" % gap)
	var made: HBoxContainer = HBoxContainer.new()
	made.theme_type_variation = "Gap%d" % gap
	return made


## Returns a VBoxContainer whose children are gap apart; gap is one of GAPS.
static func column(gap: int) -> VBoxContainer:
	assert(gap in GAPS, "UiTheme.column: no Gap%d in the Theme" % gap)
	var made: VBoxContainer = VBoxContainer.new()
	made.theme_type_variation = "Gap%d" % gap
	return made


## Adds the Label type variation name: font at size in color.
static func _text(theme: Theme, name: StringName, font: Font, size: int, color: Color) -> void:
	theme.set_type_variation(name, &"Label")
	theme.set_font(&"font", name, font)
	theme.set_font_size(&"font_size", name, size)
	theme.set_color(&"font_color", name, color)


## Adds the PanelContainer type variation name with box as its panel.
static func _panel(theme: Theme, name: StringName, box: StyleBox) -> void:
	theme.set_type_variation(name, &"PanelContainer")
	theme.set_stylebox(&"panel", name, box)


## Adds the HSeparator type variation name: a line of color, thickness units thick.
static func _rule(theme: Theme, name: StringName, color: Color, thickness: int) -> void:
	var line: StyleBoxLine = StyleBoxLine.new()
	line.color = color
	line.thickness = thickness
	theme.set_type_variation(name, &"HSeparator")
	theme.set_stylebox(&"separator", name, line)
	theme.set_constant(&"separation", name, thickness)


## Returns the outlined badge of a button glyph: a disc for radius 22, a key cap for less.
static func _glyph_box(radius: int, fill: Color) -> StyleBoxFlat:
	var box: StyleBoxFlat = StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = UiLook.LINE
	box.set_border_width_all(2)
	box.set_corner_radius_all(radius)
	box.corner_detail = 12
	_margins(box, 11.0, 5.0)
	return box


## Sets the content margins of box (left and right, top and bottom) and returns it.
static func _margins(box: StyleBox, sides: float, ends: float) -> StyleBox:
	box.content_margin_left = sides
	box.content_margin_right = sides
	box.content_margin_top = ends
	box.content_margin_bottom = ends
	return box
