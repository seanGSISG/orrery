# HUD and menu design

Status: built in #22. It follows `docs/plan.md` §2.3, §2.4 and §2.13. Where this file and the plan differ, the plan wins.

Terms used in this file:

- **Screen:** what the player sees as one whole. `Game.screen` names it: `title`, `level_select`, `settings`, `play`, `pause` or `results`.
- **Look:** every font, colour and size of the HUD and the menus, in `UiLook`.
- **Design unit:** one pixel in a 1920 × 1080 window. All UI sizes are in design units.

## 1. Files

| Path | What it is |
|---|---|
| `game/ui/ui.gd` | `Ui`, a `CanvasLayer` in `main.tscn`. It shows the screen that `Game.screen` names, and holds the HUD and every `Screen`. |
| `game/ui/screens/` | `Screen` (the base) and one script per menu: title, level select, settings, pause, results. |
| `game/ui/hud/hud.gd` | `Hud`: the gems, the timer and the power-up slot of a level. |
| `game/ui/settings/` | The parts of the settings screen: `SettingsTabs`, `SettingRow`, `OptionRow`, `BindRow`, `ValueMark`. |
| `game/ui/widgets/` | The parts of the screens: `MenuItem`, `LevelNode`, `Dial`, `OrbitMap`, `GlassPanel`, `Wash`, `Hints`, `Icon`, `Readout`. |
| `game/ui/draw/` | `Chart` (rings, arcs, tick marks) and `Icons`: shapes drawn in code, so they stay sharp at any size. |
| `game/ui/look/` | `UiLook` (the look), `UiTheme` (builds the `Theme`), the focus style and the two shaders. |
| `game/ui/levels/` | `LevelCatalog` (the tiers and levels of the level select) and `LevelInfo` (name and target times of a level). |
| `game/ui/backdrop.gd` | `Backdrop`: the live level behind the menus while no level runs. |
| `game/ui/text/en.po` | All English text. |
| `game/ui/fonts/` | Instrument Serif and IBM Plex Mono, with their licenses. |
| `game/core/input/input_glyph.gd` | `InputGlyph`: the button icon of an input action, for the device used last. |

## 2. Screens and flow

`Game` (the autoload) owns the flow. `Game.screen` is the screen that shows, `GameState.screen` reports it, and `Game.screen_changed` tells of a change. To change the screen, set `Game.screen`. `Ui` reacts; it makes no decision of its own, except the two that depend on a frame: the `pause` action, and the change to `results` when the run finishes.

| Screen | Shows | Leaves to |
|---|---|---|
| `title` | Play, Ascent, Settings, Quit | `level_select`, `settings` |
| `level_select` | The levels of one tier on a ring; `tab_prev` and `tab_next` change the tier | `play` (through `Game.load_level`), `title` |
| `settings` | Five tabs: graphics, display, audio, controls, accessibility | The screen that opened it |
| `play` | The level and the HUD | `pause` (the `pause` action), `results` (the run finishes) |
| `pause` | Resume, Restart, Settings, Levels | `play`, `settings`, `level_select` |
| `results` | Time, medal, record, gems, egg; Next, Retry, Levels | `play`, `level_select` |

Rules that `Game` applies at each change (`Game._apply_screen`):

- `title` and `level_select` have no run: to show one ends the current run.
- The scene tree is paused under `pause`, and under `settings` when a run exists. So the run and the sound effects stop, and the music plays on (`docs/design/audio.md`).
- `results` does not pause the tree, so the finish sound plays out. `Ui` stops the marble on the finish. A run that steps itself stops there (`auto_step` false), so player input no longer moves the marble, and it steps again on `play`. A run that its caller steps (a test, the harness) stays with its caller.
- `Game.load_level()` shows `play`. `Game.restart()` restarts the run and shows `play`; the `restart` action calls it on `play`, `pause` and `results`.

The harness steps a run by itself, also under `pause` and `results`: it owns time. It has no command for menu input yet.

### Add a screen

1. Make `game/ui/screens/<name>_screen.gd` that extends `Screen`. Build the controls in `_init()` (call `super()` first). In `open()`, fill them and give one control the focus. Return true from `back()` after you set the screen that B or Esc goes to.
2. Add it to `Ui.screens` under a new name.
3. Set `Game.screen` to that name to show it. If the screen lies over a run and the run must not pause, add the name to the last rule in `Game._apply_screen`.
4. Add its text keys to `en.po`.

### Settings screen (#23)

- `SettingsScreen` builds the rows of one tab at a time from `Save.settings`. `tab_prev` and `tab_next` (LB and RB, Q and E) change the tab, and `settings_defaults` (Y or Backspace) puts the settings of the tab back to their defaults.
- An `OptionRow` holds one value of a list: a choice, a stepper, a scale or a switch (the four looks of the C chart mockup). `ui_left` and `ui_right` step the value; `ui_accept` goes round a choice or a switch.
- A `BindRow` binds one gameplay action (`Bindings.ACTIONS`). A or Enter makes it wait; the next key, mouse button, pad button or stick push becomes the button of its device. B or Esc stops the wait, so those buttons cannot be bound. The menu actions stay fixed.
- Each change goes through `Save.change_settings({key: value})`: it sets the var, calls `Settings.apply()` and writes the file. The harness `set_setting` uses it too.
- **Add a setting:** add a var with its default to `Settings`, put it into the game in `Settings.apply()`, add a row in the tab's `_build_*()` function, and add its text keys to `en.po`.

### Start Ascent (#27)

`TitleScreen.ascent` is the Ascent item. It is off: it shows faint and the focus passes it by. Turn it on with `ascent.set_enabled(true)` and start the mode in `TitleScreen._on_ascent()`.

## 3. HUD

`Hud` shows on `play`. `Ui` calls `Hud.show_state(state, level)` each frame. It has three glass panels inside `Hud.area`, which keeps them off the screen edges: gems (top left), timer with the next target and the par bar (top centre), power-up slot with the glyph of `use` (bottom right).

- The HUD shows only through the run's `FollowCamera`. A screenshot from a level's shot camera (the gallery) has no HUD.
- **Add a panel** (the Ascent height meter, #27): make a control, put it on a `GlassPanel` if it needs a ground, add it to `Hud.area` and anchor it to a free edge (the left edge and the bottom left corner are free). Update it from `GameState` in `show_state()`, or in a method of its own that the mode calls. Take colours and sizes from `UiLook`.

## 4. Look

- `UiLook` (`game/ui/look/ui_look.gd`) holds every font, colour and size as a typed constant. It is the look that Sean picked from the mockups (`docs/ui-mockups/README.md`): the orrery chart (direction C) for the menus, and glass panels (direction B) with the chart's numerals and accent for the HUD.
- `UiTheme.build()` makes the one `Theme` from `UiLook`. `Ui` sets it on its root control.
- A screen styles a control only with a theme type: `label.theme_type_variation = &"Title"`. `ui_theme.gd` lists the types. A screen sets no font, colour or style box on a node. `UiTheme.label()`, `row()` and `column()` make the common controls.
- Drawn widgets (`Dial`, `OrbitMap`, `Icons`, `GlassPanel`) read `UiLook` directly.
- **Change the look:** change the values in `UiLook`. For another focus mark or another glyph badge, change the style boxes in `UiTheme.build()`. A HUD with no panels needs only `GLASS_TINT` and `GLASS_EDGE` with alpha 0.
- **Sharp at 4K:** the project stretches the 2D canvas (`canvas_items`, aspect `expand`) from 1920 × 1080. Godot draws text and lines again at the real size, so nothing is scaled up from a small image. A wider or taller window gives more room, so anchor each control to an edge or to the centre.

## 5. Text

All text is a key of `game/ui/text/en.po` (`TITLE_PLAY`). A `Label` translates its key by itself; code that builds a string calls `tr()`. Level names go through `tr()` too, so a later language file can translate them. `test_ui_text.gd` fails for a key with no English text.

## 6. Input and sounds

- Every screen works with the controller alone and with the keyboard. The focus marks the item that `ui_accept` chooses. `ui_accept` is A, Enter and Space; `ui_cancel` is B and Esc (`project.godot` adds the pad buttons, which Godot leaves out). The D-pad, the left stick and the arrow keys move the focus.
- `FocusButton.link(items)` makes a list of items for the focus, so that it does not depend on where the items are on the screen.
- A move of the mouse over an item gives it the focus. A click chooses it.
- An item is chosen when the button comes up, not when it goes down. So A on Resume does not also make the marble jump.
- `Ui` and the items call `Music.play_ui()`: `move` for a move of the focus, `select` for a choice, `back` for B or Esc.

## 7. Tests and screenshots

- `game/test/ui/` drives the menus with pad and key events (`Input.parse_input_event`) and reads `Game.snapshot().screen`. `UiTest` (`game/test/support/ui_test.gd`) is the base: a new `Ui`, an empty save in `user://test_ui/`, and helpers to tap a button or key and to finish a run.
- The pause screen pauses the scene tree, and GUT cannot wait in a paused tree. A test does not `await` while the game is paused.
- `just ui-shots` saves a screenshot of each screen at 1920 × 1080 and 3840 × 2160 into `build/ui/<height>/`. Look at them after each change to the look.

## 8. Open points

1. **Level catalogue:** `LevelInfo.read()` loads the scene of a level to read its name and times. This is fast for the M1 levels. With 60 levels, the build must write these values into one small file.
2. **Harness:** agents cannot drive the menus through the harness. A command that presses an input action (`press {action}`) fits the one-input-path rule.
3. **Backdrop:** `Backdrop.LEVEL` is a test level until the first campaign level is built (#28).
