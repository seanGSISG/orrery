# Lightmap bake spike (2026-11-20)

Reference only, not wired into the game. Proves that Godot 4.7.2 LightmapGI bakes by script on the RTX 5090:
an EditorPlugin (`addons/lightmap_baker/plugin.gd`) started with
`gamescope --backend headless -W 1280 -H 720 -- godot --editor --path <proj> -- --bake-lightmaps res://level/a.glb`
opens each imported scene as an inherited scene, gives its LightmapGI a saved `.lmbake`, selects the node and calls
the bound `LightmapGIEditorPlugin._bake`. `bake.sh` wraps it and checks the log line `BAKE done: N of N baked`
(gamescope's exit code is not reliable). Ticket #24 turns this into `just bake`.
