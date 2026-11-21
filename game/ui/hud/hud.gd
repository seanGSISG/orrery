class_name Hud
extends Control
## The HUD of a level: the gems (top left), the timer with its targets (top centre) and the
## held power-up (bottom right), each on a glass panel. Ui shows it on the &"play" screen and
## calls show_state() each frame; it has no input.
##
## The three corners are free for more: a mode adds its own panel to `area`, which keeps the
## panels off the screen edges, and anchors it there. #27 adds the Ascent height meter to the
## left edge this way.

## Width of the timer panel, and the side of the power-up slot.
const TIMER_WIDTH: float = 430.0
const SLOT_SIDE: float = 116.0

## The parent of the panels: it fills the screen inside the safe margins.
var area: Control = Control.new()

## The gems collected and the gems of the level: "3" and "/5".
var gems: Readout = Readout.new(UiLook.HUD_GEMS_SIZE, UiLook.HUD_GEMS_SMALL)
## The level clock: "0:42" and ".37".
var time: Readout = Readout.new(UiLook.HUD_TIME_SIZE, UiLook.HUD_TIME_SMALL)
## The icon of the held power-up; its `icon` is &"" for an empty slot.
var power_up: Icon = Icon.new(&"", UiLook.INK, 60.0)

var _target_icon: Icon = Icon.new(&"star", UiLook.GOLD, 22.0)
var _target: Label = UiTheme.label("", &"HudTargetGold")
var _bar: ParBar = ParBar.new()
var _slot: GlassPanel = GlassPanel.new()
var _use: InputGlyph = InputGlyph.new()


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var margin: MarginContainer = MarginContainer.new()
	margin.theme_type_variation = &"Safe"
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(area)
	add_child(margin)
	area.add_child(_build_gems())
	area.add_child(_build_timer())
	_build_slot()


## Shows the gems, the clock and the held power-up of state, against the target times of
## level.
func show_state(state: GameState, level: Level) -> void:
	gems.show_text(str(state.gems_collected), "/%d" % state.gems_total)
	time.show_text(TimeText.minutes(state.timer), TimeText.hundredths(state.timer))
	_bar.show_times(state.timer, level.gold, level.par)
	# The target is the gold time, then the par time, then nothing.
	var gold_open: bool = level.gold > 0.0 and state.timer <= level.gold
	var par_open: bool = level.par > 0.0 and state.timer <= level.par
	_target_icon.visible = gold_open or par_open
	_target.visible = gold_open or par_open
	_target_icon.icon = &"star" if gold_open else &"check"
	_target_icon.color = UiLook.GOLD if gold_open else UiLook.INK_2
	_target.theme_type_variation = &"HudTargetGold" if gold_open else &"HudTarget"
	_target.text = TimeText.target(level.gold if gold_open else level.par)
	var held: bool = state.power_up != &""
	power_up.icon = state.power_up
	_use.modulate.a = 1.0 if held else 0.0
	_slot.modulate.a = 1.0 if held else 0.45


## Builds the gems panel, in the top left corner.
func _build_gems() -> Control:
	var panel: GlassPanel = GlassPanel.new()
	var row: HBoxContainer = UiTheme.row(14)
	row.add_child(Icon.new(&"gem", UiLook.GOLD, 34.0))
	row.add_child(gems)
	panel.add_child(row)
	return panel


## Builds the timer panel, in the top centre: the clock and the target, over the par bar.
func _build_timer() -> Control:
	var panel: GlassPanel = GlassPanel.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.custom_minimum_size.x = TIMER_WIDTH
	var column: VBoxContainer = UiTheme.column(8)
	var row: HBoxContainer = UiTheme.row(14)
	time.size_flags_horizontal = Control.SIZE_EXPAND
	row.add_child(time)
	row.add_child(_target_icon)
	row.add_child(_target)
	column.add_child(row)
	column.add_child(_bar)
	panel.add_child(column)
	return panel


## Builds the power-up slot, in the bottom right corner, with the glyph of `use` on its lower
## edge.
func _build_slot() -> void:
	_slot.custom_minimum_size = Vector2(SLOT_SIDE, SLOT_SIDE)
	_slot.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	_slot.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_slot.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_slot.offset_top -= InputGlyph.SIDE * 0.5
	_slot.offset_bottom -= InputGlyph.SIDE * 0.5
	power_up.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_slot.add_child(power_up)
	area.add_child(_slot)
	_use.action = &"use"
	_use.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	_use.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_use.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_use.offset_left -= SLOT_SIDE * 0.5
	_use.offset_right -= SLOT_SIDE * 0.5
	area.add_child(_use)
