class_name UiLook
extends RefCounted
## The look of the HUD and the menus: every font, colour and size, in one place. UiTheme
## builds the Theme of the screens from it, and the drawn widgets (rings, icons, glass
## panels) read it directly. To change the look, change the values here.
##
## It is the look that Sean picked from the mockups (docs/ui-mockups/README.md): the orrery
## chart (direction C) for the menus, and glass panels (direction B) with the chart's numerals
## and accent for the HUD.
##
## Sizes are design units: pixels in a 1920 × 1080 window. The window stretches them, and
## Godot draws text and lines again at the real size, so they stay sharp at 4K.

## Level names and menu items.
const NAME_FONT: Font = preload("res://ui/fonts/InstrumentSerif-Regular.ttf")
## Titles.
const TITLE_FONT: Font = preload("res://ui/fonts/InstrumentSerif-Italic.ttf")
## Numbers, small labels and button glyphs.
const DATA_FONT: Font = preload("res://ui/fonts/IBMPlexMono-Regular.ttf")
const DATA_STRONG_FONT: Font = preload("res://ui/fonts/IBMPlexMono-Medium.ttf")

## The dark ground: washes, panels and the fill of hollow marks.
const NIGHT: Color = Color("#060a14")
## Text and lines, and three weaker steps of each.
const INK: Color = Color("#f1ebdb")
const INK_2: Color = Color("#f1ebdbbd")
const INK_3: Color = Color("#f1ebdb7a")
const LINE: Color = Color("#f1ebdbe6")
const LINE_2: Color = Color("#f1ebdb6b")
const LINE_3: Color = Color("#f1ebdb33")
## Focus, and the mark of "now" on a scale.
const ACCENT: Color = Color("#ff8f5e")
## The fill behind a focused item.
const ACCENT_FILL: Color = Color("#ff8f5e26")
## Gold medals, gold times and eggs.
const GOLD: Color = Color("#f4d17e")

## Distance of the content from the left and right edges, and from the top and bottom.
const SAFE: Vector2 = Vector2(96.0, 54.0)
## Width of a thin line and of a strong line (a progress arc, a focus ring).
const THIN: float = 2.0
const STRONG: float = 4.0

## Font sizes of the text styles that UiTheme makes.
const LOGO_SIZE: int = 232
const TITLE_SIZE: int = 96
const HEADING_SIZE: int = 68
const LEVEL_NAME_SIZE: int = 72
const MENU_SIZE: int = 56
const ROW_SIZE: int = 46
const DATA_SIZE: int = 26
const CAPS_SIZE: int = 23
const TIME_SIZE: int = 64
const BIG_TIME_SIZE: int = 112
const GLYPH_SIZE: int = 22
## Extra space between the letters of small capitals.
const CAPS_SPACING: int = 4

## HUD glass panels: the tint over the blurred game, the edge line, the corner radius, the
## blur (each step doubles it; 0 is sharp), the colour boost and the light kept. A tint and
## an edge with alpha 0 give a HUD with no panels.
const GLASS_TINT: Color = Color("#0a101e8a")
const GLASS_EDGE: Color = Color("#f1ebdb3d")
const GLASS_RADIUS: float = 34.0
const GLASS_BLUR: float = 3.0
const GLASS_SATURATION: float = 1.5
const GLASS_BRIGHTNESS: float = 0.75
## Sizes of the HUD numbers: the large part and the small part of a readout.
const HUD_TIME_SIZE: int = 54
const HUD_TIME_SMALL: int = 34
const HUD_GEMS_SIZE: int = 44
const HUD_GEMS_SMALL: int = 30
const HUD_TARGET_SIZE: int = 27

## Menu washes: the blur of the frame behind a menu, and of the title backdrop.
const WASH_BLUR: float = 4.0
const TITLE_BLUR: float = 1.5
