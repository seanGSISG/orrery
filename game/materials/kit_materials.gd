@tool
class_name KitMaterials
extends Object
## The kit material library: the look of each kit material name. A level script names a
## material (kit/surfaces.py: limestone, brass, gold) and LevelConverter gives those faces the
## material that find() returns. Every material uses res://materials/kit_surface.gdshader.
##
## SET picks the material set: A, B or C of the style board.
## - "a": honey limestone and aged brass. Sean approved it on 2026-11-21. Its brass is
##   ambientCG Metal048C (Sean's pick of 2026-11-22). The polished brass (brass_polished) and the
##   gold stay on Metal048A; the kit brass differs from them by its texture, tint and roughness.
## - "b": cream limestone and satin brass.
## - "c": weathered grey stone and dark bronze.
## A set is the folder res://materials/<set>/. A material that every set shares is in
## res://materials/. After a change of SET, run `just build-levels` and `just bake`.
## docs/design/visual-quality.md §10 gives the dawn sky and sun that go with each set.

const SET: String = "a"
const PATHS: Array[String] = ["res://materials/%s/%%s.tres" % SET, "res://materials/%s.tres"]


## Returns the material of a kit material name, or null when no set has it.
static func find(name: String) -> Material:
	for pattern: String in PATHS:
		var path: String = pattern % name
		if ResourceLoader.exists(path):
			return load(path) as Material
	return null
