"""Render the factory-startup scene with EEVEE and fail on a blank frame.

Used by tools/setup/check.sh. Run:
  blender -b --factory-startup --python-exit-code 1 --python blender_eevee.py -- <out.png>
"""

import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
engines = {
    e.identifier
    for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
}
scene.render.engine = (
    "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
)
(
    scene.render.resolution_x,
    scene.render.resolution_y,
    scene.render.resolution_percentage,
) = 320, 180, 100
scene.render.filepath = out
bpy.ops.render.render(write_still=True)

px = bpy.data.images.load(out).pixels[:]
lum = [
    0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]
    for i in range(0, len(px), 4 * 7)
]
contrast = max(lum) - min(lum)
print(
    f"EEVEE engine={scene.render.engine} gpu={bpy.context.preferences.system.gpu_backend} contrast={contrast:.3f}"
)
sys.exit(0 if contrast > 0.05 else 1)
