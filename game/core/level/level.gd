class_name Level
extends Node3D
## The root of every level scene. The importer (#8) fills these from the level script's root
## data. Give a Level to LevelRun.create() to play it.

@export var id: StringName = &""
@export var title: String = ""
@export var tier: StringName = &""
## Par time and gold time, s.
@export var par: float = 0.0
@export var gold: float = 0.0
@export var music: StringName = &""
@export var sky: StringName = &""
