# HUD and menu mockups (#6)

Static mockups of the HUD and every menu in three directions. Sean picks from `index.html`. Nothing here is game code.

| Path | Content |
|---|---|
| `index.html` | The review page: the three directions, then each screen side by side |
| `a-brass/`, `b-glass/`, `c-chart/` | One direction each: `theme.css` and one HTML file per screen |
| `shared/base.css` | The 1920 × 1080 frame, the safe area, the backdrops, the icon shapes, the size of the button glyphs |
| `backdrops/` | Three style-board mood images and one frame from the current build (`flat` test level, through the harness) |
| `png/`, `thumbs/` | Render output: full-size PNG and a WebP thumbnail per screen |

## Change the look

- The palette and the fonts of a direction are the custom properties in `:root` of its `theme.css`. Change them there and render again.
- The fonts load from Google Fonts. All are under the SIL Open Font License: Cinzel and Spectral (A), Outfit (B), IBM Plex Mono and Instrument Serif (C). Add the chosen fonts to `docs/licenses.md` when they enter the game.

## Render

```sh
uv run docs/ui-mockups/render.py          # every screen
uv run docs/ui-mockups/render.py b- hud   # only the names that contain "b-" or "hud"
```

The script needs Google Chrome and network access to Google Fonts. `hud.html#keys` is the same HUD page with keyboard glyphs on the build frame; the script renders it as `*-hud-keys.png`.
