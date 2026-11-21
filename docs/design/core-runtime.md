# Core runtime design

Status: accepted 2026-11-20 (chief of staff, technical). It covers the M1 tickets #7 to #13. Where this file and `docs/plan.md` differ, the plan wins. The two deviations in §10 need Sean's approval first.

Terms used in this file:

- **Tick:** one physics step, 1/120 s.
- **Sub-step:** one part of a tick. The marble moves at most half its radius per sub-step.
- **Run:** a `LevelRun` node. It plays one level.
- **State:** the `GameState` snapshot.
- **Source:** an `InputSource`. It makes one `MarbleInput` per tick.
- **Solid:** a collider that the marble can touch.
- **Trigger:** an `Area3D` on the trigger layer.
- **Mover:** an object that moves a Solid each tick.
- **Contract PR:** the first PR of #7. It adds every shared file.

## 1. Decisions

1. **The run owns time.** `LevelRun.step(input)` advances the level by one tick. The game calls it from `_physics_process`. Tests and the harness call it directly in a plain loop. Queries do not need a physics frame (F9, F10). In GUT, 600 ticks take 9.7 ms (F13).
2. **Jolt only answers questions.** The marble is not a physics body. Only `WorldQuery` calls Jolt. It uses `intersect_shape`, `collide_shape` and `cast_motion`.
3. **Movers move their own Solids.** A `Solid` is a `StaticBody3D`. `Solid.move()` sets the server transform at once, and it records the surface velocity in `constant_linear_velocity` and `constant_angular_velocity`. The solver reads `Solid.velocity_at(point)`. The design does not use `AnimatableBody3D` (plan deviation A, §10).
4. **One boundary.** `MarbleInput` goes in and `GameState` comes out. GUT tests and the harness read the same `GameState`. The harness sends `GameState.to_dict()` as JSON.
5. **Objects are scenes with `@export` settings and four hooks.** The importer writes the marker settings into the `@export` vars. Objects emit `feedback(kind, strength, at)` for rumble and sound.
6. **Contract first.** The contract PR adds all shared types, stubs and placeholder objects. After it merges, #8 to #13 work in parallel and do not edit the same files.
7. **Turn on `physics/jolt_physics_3d/queries/use_enhanced_internal_edge_removal`.** Without it, the marble drifts on flat trimesh floors (F7).

## 2. Engine facts

Each fact comes from a prototype: Godot 4.7.2, Jolt, 120 ticks per second, headless, on the dev machine. The prototypes were throwaway projects and are not in the repo. VERIFIED means measured. ASSUMED means not measured.

**Contacts**

| # | Fact | Status |
|---|---|---|
| F1 | `collide_shape` gives contact points. It gives no collider and no normal. It returns pairs `[point on the query shape grown by margin, point on the collider]`, with one pair for each touched triangle. A floor-wall corner gives 2 pairs. A grid vertex gives 6 identical pairs. | VERIFIED |
| F2 | A separated contact needs `margin`. With a 0.005 m gap, margin 0.02 finds the contact and margin 0 finds nothing. | VERIFIED |
| F3 | `get_rest_info` gives only one contact, the deepest: `point`, `normal`, `rid`, `collider_id`, `shape`, `linear_velocity`. For an `AnimatableBody3D` moved in physics frames, `linear_velocity` is the point velocity: platform 3 m/s → 2.99995; gear 1 rad/s at r = 1.5 m → 1.49999 m/s. In a corner it gives only the wall. | VERIFIED |
| F4 | `intersect_shape` gives colliders only (`rid`, `collider`, `collider_id`, `shape`). It can repeat a body: one trimesh at a corner gave 2 entries. With `collide_with_areas` it finds an `Area3D`, also when `monitoring` and `monitorable` are false. | VERIFIED |
| F5 | `cast_motion` returns `[safe, unsafe]` fractions and does not tunnel. A 30 m drop stops at y = 0.2026 (radius 0.2, floor at 0). One 500 m sweep stops at a thin one-sided floor at y = −9.7987 (expected −9.8). It ignores a shape that the sphere already overlaps, also when the motion goes deeper (y = 0.199, 1 mm down: safe 1). From exact contact (gap 0), the smallest motion into the surface gives safe 0; a motion along the surface gives safe 1. So the response leaves a 0.1 mm gap (#7). | VERIFIED |
| F6 | Back faces do not collide in any sphere query. The front of triangle (a, b, c) faces along `(c - a).cross(b - a)`. A sweep from below passes through a one-sided floor. | VERIFIED |
| F7 | With the default `queries/use_enhanced_internal_edge_removal=false`, a sphere 3 cm from an internal edge also gets the neighbour triangle's edge point, with a normal tilted by 0.15 to 0.20. A test marble at 15 m/s drifted sideways at 0.89 m/s after 5 s. With `true`, the extra contacts go away from 4 mm on and the drift is 0.0008 m/s. Closer than about 2 mm, `true` still gives the edge point, with a normal tilted by about d/r (0.007 at 2 mm); the merge rule in §3 keeps the face contact (#7). Concave corners, outer ledge edges and wall tops still give contacts. The cost goes from 4.2 to 6.0 µs per tick. A home-made coplanar filter only halved the drift (0.46 m/s). | VERIFIED |
| F8 | Cost per call against a 4000-triangle trimesh: `collide_shape` 1.5 µs, `get_rest_info` 1.8 µs, `intersect_shape` 2.1 µs, `cast_motion` 2.6 µs. | VERIFIED |

**When queries work**

| # | Fact | Status |
|---|---|---|
| F9 | Queries work in `_physics_process`, in `_process` and in a GUT test function. They work many times per frame: 2400 calls of each type ran in one frame with correct results. | VERIFIED |
| F10 | A body is in the space as soon as it enters the tree, before any physics step. `free()` removes it at once. Changes to `CollisionShape3D.disabled` and `collision_layer` apply at once. | VERIFIED |
| F11 | A node transform write (`position`, `global_transform`) reaches the physics server only at the next frame. This is true for static and kinematic bodies. `PhysicsServer3D.body_set_state(BODY_STATE_TRANSFORM, …)` applies at once to a static body, but not to a kinematic body (`AnimatableBody3D`). | VERIFIED |
| F12 | In a `--script` SceneTree, `_initialize()` runs before the root enters the tree, so queries there find nothing. This affects prototypes and tools only. | VERIFIED |

**Simulated time**

| # | Fact | Status |
|---|---|---|
| F13 | Wall time for 1 simulated second, headless: real-time default 1000 ms. Physics frames with `--fixed-fps 120`: 2.3 ms. Direct `step()` loop: 0.5 to 0.7 ms with the bare solver, and 1.6 ms with the full contract prototype (600 ticks in 9.7 ms inside GUT). | VERIFIED |
| F14 | `Engine.time_scale` does not add ticks. At 8, it keeps 120 ticks per real second and makes each tick's delta 0.0667 s. Do not use it for tests or the harness. | VERIFIED |
| F15 | In one process, the same start and the same inputs give bit-identical position and velocity after 600 ticks. Across processes and operating systems it is not checked, so the CLAUDE.md tolerance rule stays. | VERIFIED / ASSUMED |
| F16 | A GUT test can step a run 600 times without awaits. `add_child_autofree` removes the run's bodies before the next test starts: each test saw exactly 1 floor. 10 tests took 0.47 s of GUT time, and a 6-test process took 0.93 s from start to exit. | VERIFIED |

**Other facts**

| # | Fact | Status |
|---|---|---|
| F17 | `Vector3` components are 32-bit. 0.2 serializes as 0.200000002980232. Harness clients compare with tolerances. | VERIFIED |
| F18 | `JSON.stringify` sorts the keys. | VERIFIED |
| F19 | The #4 strict settings reject these: a Variant passed to `int()`, to `String()` or to a GUT assert; `as` on a Variant; a method named `_set` (it clashes with `Object._set`). Fix: assign the Variant to a typed variable first. These compile: typed access to an autoload, `const T: MarbleTuning = preload("res://core/marble_tuning.tres")`, and `instantiate() as Level`. | VERIFIED |
| F20 | Other scripts see a new `class_name` only after `--import`. `just test` already imports first. GUT exits 0 when a test script fails to parse. The #4 check for `Parse Error` catches this. | VERIFIED |
| F21 | An empty hook call costs 0.05 µs, so 200 objects add 10 µs per tick. Objects do not need to opt in to hooks. | VERIFIED |
| F22 | A collider inside an instanced object scene has `owner` set to the object root. | VERIFIED |
| F23 | When a mover puts the sphere centre inside a convex Solid (`BoxShape3D`), `collide_shape` still gives one pair: the first point is the centre minus (radius + margin) along the outward face normal, and the second is on the nearest face. So `centre - point` points into the Solid, and `point - first` points out. A trimesh (`ConcavePolygonShape3D`) gives no pair once the centre passes its face, because the inside faces are back faces (F6). | VERIFIED (#10) |
| F24 | `intersect_shape` finds an `Area3D` box under a turned, non-uniformly scaled node at the scaled size (scale (4, 2, 6): hits up to 0.2 m outside each face, misses at 0.3 m). A field volume can be a 1 m cube that the node scales. | VERIFIED (#10) |
| A1 | The Blender glTF exporter writes custom-property vectors unchanged, in Blender's Z-up axes. Use child empties for positions and paths, because the exporter converts their transforms. | ASSUMED |
| A2 | Shape queries do not tell which triangle, and so which material, a contact is on. So each surface type needs its own `Solid`. | ASSUMED |
| A3 | Jolt can move dozens of static bodies each tick at a low cost. | ASSUMED |
| A4 | Imported `-col` trimeshes keep the mesh winding, so the faces point outward. The #8 fixture test checks this. | ASSUMED |

## 3. The tick

`LevelRun.step(input)` runs these steps in this order:

1. `tick += 1` and `t = tick * dt`. `t` is run time. `restart()` sets it to 0.
2. `slot.before_step(input)`: use the held power-up (#17).
3. `object.advance(self, t)` for every object. Movers call `Solid.move()` here.
4. `marble.step(dt, input, world)`: the sub-steps (below).
5. `object.on_touch(self, contact)` for each touched object, and `object.on_overlap(self, first)` for each overlapped object.
6. `rules.after_step()`: clock, out of bounds, respawn, finish (#13).
7. Write `state` and keep `last_input = input`.

**Sub-steps** (#10):

- A sub-step lasts until the marble could move `max_substep_move·r` with its speed at the start of the sub-step and the largest steady acceleration (gravity, air control, rolling), or until the tick ends. At 15 m/s a tick has 2 sub-steps. The last of `max_substeps` (16) sub-steps takes the rest of the tick, so above 192 m/s it moves more than r/2. The sweep still stops it at the first surface (F5).
- Each sub-step does these steps:
  1. Find contacts.
  2. Hits, with the velocity from before this sub-step's gravity, relative to `contact.velocity`, for each contact that the marble reaches in this sub-step. A glancing hit (speed into the surface below `slide_threshold` × speed) or a hit below `min_bounce_speed` loses its speed into the surface and slides on. Any other hit bounces with `restitution` × `Surface.restitution`, and bounce friction acts at the contact point. The first hit on a floor that ends a flight (the last sub-step had no ground) emits `marble.land`; any other bounce emits `marble.bounce`.
  3. Apply gravity from the field with the highest priority, or else the tuning gravity (straight down). Up is the opposite of the gravity, and `Marble.frame` turns by the shortest arc to match.
  4. Support: push out to `Marble.SKIN` (0.1 mm) above each surface, because a sweep from exact contact stops at once (F5), and stop only the motion that would pass the surface in this sub-step. The ground is the most upward floor (normal · up ≥ `floor_min_up`) that the marble hit or presses on. Walls and ceilings give no rolling, no jump and no landing.
  5. On the ground: rolling with friction (`Surface.friction` scales it), then the jump. The jump raises the speed away from the ground to `jump_impulse` along the ground normal. A held jump jumps again at each landing. In the air: air control, up to the speed that input asks for on the ground, so hops do not add speed. The spin does not change in the air.
  6. Sweep the move with `cast_motion`. An impulse in the sub-step (a jump, a hit by a mover, friction at a bounce) can make this one move longer than `max_substep_move·r`; the sweep still stops it at the first surface, and the next sub-step is short again. The forces act for exactly the sub-step's time.
  7. Collect the touched objects and the overlapped triggers, and take the gravity at the new position for the next sub-step.

**Contact rules** (`WorldQuery`):

- Call `intersect_shape` on the solid layer with margin `contact_margin` (0.01) and at most 32 results, then keep the unique `Solid`s. Use 32, because one body can fill several entries (F4).
- For each Solid, call `collide_shape` (at most 16 pairs) with the other Solids in `exclude`. The second point of each pair is on the Solid. The first is the point of the grown sphere that is deepest past the surface (F23).
- `normal = (centre - point).normalized()`. `depth = radius - distance`. The depth is negative when the contact is inside the margin. When a mover put the centre inside a convex Solid (`point - first` points against the normal, F23), the normal flips and `depth = radius + distance`, so the response pushes the marble out of the Solid, not deeper in.
- Merge the contacts of one Solid whose normals almost agree (`dot > 0.9998`), and keep the deeper contact with its point and normal. This removes the duplicates from F1 and the edge points close to an internal edge (F7). Contacts of different Solids stay apart, so a flush object keeps its touch.
- Sweep with `cast_motion` and margin 0.
- Find overlaps with `intersect_shape` on the trigger layer, areas only, then use `collider.owner as LevelObject`.
- Physics layers: layer 1 is `solid` (mask value 1) and layer 2 is `trigger` (mask value 2). Name them in `project.godot`.

**Callers of `step()`**

| Caller | How it steps |
|---|---|
| Game | In `_physics_process`, while `auto_step` is true: `step(InputHub.next_input(state))` |
| GUT test | Set `auto_step = false`, then loop `run.step(input)` |
| Harness `step {frames}` | Set `auto_step = false`, then loop `run.step(InputHub.next_input(run.state))` |
| Harness `pause` / `resume` | Set `auto_step` |
| Harness `set_time_scale {scale}` | Run `scale` ticks per physics frame with an accumulator. Do not use `Engine.time_scale` (F14) |
| Route bot level test | Loop at full speed, headless |

## 4. Types

These are the shapes only; the bodies are left out. Every name below is final for the contract PR.

```gdscript
# core/input/marble_input.gd
class_name MarbleInput
extends RefCounted
var move: Vector2 = Vector2.ZERO   # x = right, y = forward, relative to camera_yaw; length 0..1
var jump: bool = false             # true while held
var use: bool = false              # true while held
var camera_yaw: float = 0.0        # radians around up, absolute, measured in Marble.frame
var camera_pitch: float = 0.0      # radians, absolute; negative looks down

# core/input/input_source.gd
class_name InputSource
extends RefCounted
func next_input(_state: GameState) -> MarbleInput   # called once per tick
func handle_event(_event: InputEvent) -> void       # the hub forwards unhandled input events

# core/input/input_hub.gd: autoload InputHub (no class_name; a class_name would hide the autoload)
extends Node
var device: StringName = &"keyboard"               # last physical device: &"keyboard" or &"pad"
func use_source(source: InputSource) -> void       # makes source the only active source
func next_input(state: GameState) -> MarbleInput

# core/marble/marble_tuning.gd; the instance is core/marble_tuning.tres (plan §4.2)
class_name MarbleTuning
extends Resource
@export var radius: float = 0.2
@export var mass: float = 1.0
@export var gravity: float = 20.0
@export var max_roll_speed: float = 15.0
@export var angular_acceleration: float = 75.0
@export var braking_acceleration: float = 30.0
@export var air_acceleration: float = 5.0
@export var jump_impulse: float = 7.5
@export var floor_min_up: float = 0.1   # a floor's normal has at least this dot with up
@export var static_friction: float = 1.1
@export var kinetic_friction: float = 0.7
@export var bounce_friction: float = 0.2
@export var restitution: float = 0.5
@export var slide_threshold: float = 0.5
@export var min_bounce_speed: float = 0.1
@export var hard_impact_speed: float = 20.0   # feedback strength 1 at this speed into a surface
@export var max_substep_move: float = 0.5   # times radius
@export var max_substeps: int = 16
@export var contact_margin: float = 0.01

# core/marble/marble.gd; the node position is the marble centre
class_name Marble
extends Node3D
signal feedback(kind: StringName, strength: float, at: Vector3)   # &"marble.land", &"marble.bounce", &"marble.jump"
@export var tuning: MarbleTuning
var velocity: Vector3
var spin: Vector3                    # angular velocity, rad/s
var up: Vector3 = Vector3.UP         # opposite of gravity
var frame: Basis = Basis.IDENTITY    # yaw reference; y = up; turns by the shortest arc when up changes
var on_ground: bool                  # true when the last sub-step had a contact
var touches: Array[Contact]          # after step(): the first contact for each touched object
var overlaps: Array[LevelObject]     # after step(): objects whose triggers overlapped in any sub-step
func step(dt: float, input: MarbleInput, world: WorldQuery) -> void   # reads only its arguments and own fields
func add_velocity(delta_v: Vector3) -> void
func teleport(at: Vector3, new_velocity: Vector3) -> void   # spin becomes the spin that rolls at new_velocity on a floor normal to up

# core/marble/world_query.gd: the only code that calls Jolt; read-only
class_name WorldQuery
extends RefCounted
func _init(space: PhysicsDirectSpaceState3D, radius: float, margin: float) -> void
func contacts(center: Vector3) -> Array[Contact]
func sweep(center: Vector3, motion: Vector3) -> float    # safe fraction, 0..1
func overlaps(center: Vector3) -> Array[LevelObject]

# core/marble/contact.gd
class_name Contact
extends RefCounted
var point: Vector3        # on the surface
var normal: Vector3       # from point toward the marble centre, unit length
var depth: float          # radius - distance
var velocity: Vector3     # surface velocity at point
var surface: Surface      # never null
var object: LevelObject   # null for plain level geometry

# core/level/solid.gd
class_name Solid
extends StaticBody3D
const DEFAULT_SURFACE: Surface = preload("res://core/level/default_surface.tres")
@export var surface: Surface = DEFAULT_SURFACE
func move(to: Transform3D, linear: Vector3, angular: Vector3) -> void   # node + server transform, and velocities
func velocity_at(point: Vector3) -> Vector3   # constant_linear_velocity + constant_angular_velocity.cross(point - origin)

# core/level/surface.gd; one shared .tres file per surface type
class_name Surface
extends Resource
@export var id: StringName = &"default"
@export var friction: float = 1.0      # scales static and kinetic friction
@export var restitution: float = 1.0   # scales restitution

# core/gravity/gravity_field.gd (#10); the object has a trigger for its volume
class_name GravityField
extends LevelObject
@export var priority: int = 0
func gravity_at(point: Vector3) -> Vector3
# UniformGravity (#10): @export var strength: float = 20.0; gravity -global_basis.y * strength.
# core/gravity/uniform_gravity.tscn: a 1 m cube volume; turn the node to aim, scale it to size (F24).
# PointGravity (M3): toward global_position.

# core/level/level_object.gd
class_name LevelObject
extends Node3D
signal feedback(kind: StringName, strength: float, at: Vector3)   # kind "<type>.<event>", strength 0..1
func reset(_restart: bool) -> void                     # start state; restart is false for a checkpoint respawn
func advance(_run: LevelRun, _t: float) -> void        # each tick, before the marble moves
func on_touch(_run: LevelRun, _contact: Contact) -> void  # the marble touched one of this object's Solids
func on_overlap(_run: LevelRun, _first: bool) -> void  # the marble overlaps a trigger; first on the entry tick

# core/level/level.gd: root of every level scene; the importer fills it
class_name Level
extends Node3D
@export var id: StringName
@export var title: String
@export var tier: StringName
@export var par: float
@export var gold: float
@export var music: StringName
@export var sky: StringName

# core/level/level_run.gd
class_name LevelRun
extends Node3D
signal feedback(kind: StringName, strength: float, at: Vector3)   # every object's and the marble's feedback
var level: Level
var marble: Marble
var rules: Rules
var slot: PowerUpSlot
var objects: Array[LevelObject]
var state: GameState
var last_input: MarbleInput     # the camera reads camera_yaw and camera_pitch here
var auto_step: bool = true      # false: only explicit step() calls advance the run
static func create(level: Level) -> LevelRun   # add the result to the tree; _ready() starts the run
func step(input: MarbleInput) -> void          # one tick, in the order of §3
func restart() -> void                         # t = 0, reset(true) on every object, marble on the start pad
func respawn(at: Vector3) -> void              # reset(false) on every object, marble at `at`; the clock runs on

# core/level/rules.gd: stub from #7, logic from #13
class_name Rules
extends RefCounted
func _init(run: LevelRun) -> void
func reset(restart: bool) -> void   # the stub counts Gem objects into state.gems_total
func after_step() -> void
func collect_gem() -> void
func reach_checkpoint(checkpoint: LevelObject) -> void
func reach_finish() -> void
func find_egg() -> void

# core/level/power_up_slot.gd: stub from #7, logic from #17
class_name PowerUpSlot
extends RefCounted
var held: StringName = &""
func _init(run: LevelRun) -> void
func take(id: StringName) -> bool              # false when the slot is full; the pickup stays
func before_step(input: MarbleInput) -> void   # on a new use press: apply the effect and empty the slot

# core/game.gd: autoload Game (no class_name); #22 adds the menu screens
extends Node
var run: LevelRun                   # null in menus
var screen: StringName = &"play"
func load_level(id: StringName) -> LevelRun   # res://levels/built/<id>.glb, else res://test/levels/<id>.tscn
func snapshot() -> GameState        # run.state (or a new GameState) with screen and input_device filled in
# Game also maps the `restart` action to run.restart().
```

The camera (#7 basic, then #11) has one seam: `follow(state: GameState, input: MarbleInput, dt: float) -> void`. A test can give it a `GameState` with any `up`, so #11 does not wait for the gravity fields of #10.

## 5. Object contract

- **Files:** `game/objects/<type>/<type>.tscn` and `<type>.gd`. `<type>` is the marker type, for example `gem`, `start`, `finish`, `moving_platform`. The root script extends `LevelObject`. The class name can differ from the type (`StartPad` in `objects/start/`). The importer finds the scene by this name rule, so there is no registry file.
- **Settings:** the `@export` vars of the root are the typed settings. The importer (#8) reads each key of the marker dictionary except `type`. The key must name an `@export` var, and the value must convert to the var's type (int to float is allowed). If not, the import fails and gives the level id and the node name. The run never sees the dictionary.
- **Positions and paths:** use the marker's own transform and its child empties, not vector settings (A1). The importer turns the child empties into `Marker3D` children of the object, in name order. A platform path is a list of these children.
- **Colliders:** use a `Solid` for every part the marble touches. Use an `Area3D` on the trigger layer, with `monitoring` and `monitorable` off, for each volume (F4).
- **Time:** an object that moves calculates its pose from `t` in `advance()`. It does not drive collision with `AnimationPlayer` or timers. `restart()` sets `t` to 0, so movers return to their start pose without extra code.
- **Allowed actions:** an object changes the game only through these calls: `run.marble.add_velocity()`, `run.marble.teleport()`, `run.rules.*`, `run.slot.take()`, `Solid.move()`, changes to its own `collision_layer`, and `feedback.emit()`.
- **Feedback:** `kind` is `&"<type>.<event>"`, for example `&"bumper.hit"`. `strength` is 0..1, and `at` is a world position. `LevelRun.feedback` re-emits every object's and the marble's feedback. Audio (#25) and rumble (#18) connect there. Kinds are strings, so no shared enum file gets an edit from every object ticket.
- **Tests:** an object test reads `run.state` and watches `run` for `feedback` with GUT `watch_signals`.

| Object | Hooks it uses |
|---|---|
| Bumper | `on_touch`: `run.marble.add_velocity(contact.normal * strength)`, emit `bumper.hit` |
| Steam Vent | `on_overlap`: `add_velocity(axis * acceleration * dt)` each tick |
| Pendulum, platform, gear | `advance`: `Solid.move(pose(t), velocity, angular_velocity)`; the solver handles the hit or the carry |
| Trapdoor | `on_touch`: start the drop; `advance`: hinge pose; it resets after 5 s |
| Crumbling Tiles | `on_touch`: start the timer, then `collision_layer = 0`; `reset(false)` brings the tiles back |
| Gem, checkpoint, finish, egg | `on_overlap(first)`: `run.rules.collect_gem()` and the other rule calls |
| Coil Spring pickup | `on_overlap(first)`: hide only if `run.slot.take(&"coil_spring")` returns true |

## 6. Observable state

`GameState` (`core/level/game_state.gd`) is a `RefCounted` that has only the fields below. `to_dict()` walks the script variables, so a new field reaches the JSON without other edits. Vectors become `[x, y, z]` and StringNames become strings. The harness sends `Game.snapshot().to_dict()` unchanged. Each field has one writer.

| Field | Type | Meaning | Writer |
|---|---|---|---|
| `tick` | int | ticks since the start or restart | run (#7) |
| `level` | StringName | level id; `""` in menus | run (#7) |
| `status` | StringName | `none`, `playing`, `respawning` or `finished` | run (#7: `none`, `playing`); rules (#13: the others) |
| `screen` | StringName | `play` now; #22 adds `title`, `level_select`, `settings`, `pause` | Game |
| `input_device` | StringName | `keyboard` or `pad` | `Game.snapshot()`, from `InputHub.device` |
| `position` | Vector3 | marble centre, world space, m | run, from marble (#7) |
| `velocity` | Vector3 | m/s | run, from marble (#7) |
| `spin` | Vector3 | angular velocity, rad/s | run, from marble (#7) |
| `up` | Vector3 | unit vector, opposite of gravity | run, from marble (#7, #10) |
| `on_ground` | bool | the last sub-step had a contact | run, from marble (#7) |
| `gems_collected` | int | gems collected in this run | rules (#13) |
| `gems_total` | int | gems in the level | rules (the stub counts them, #7) |
| `timer` | float | level clock, s | rules (#13) |
| `medal` | StringName | `none`, `qualified` or `gold`; set at the finish | rules (#13) |
| `power_up` | StringName | held power-up id; `""` when empty | slot (#17) |
| `checkpoint` | StringName | node name of the last checkpoint; `""` means the start pad | rules (#13) |
| `egg_found` | bool | the egg was found in this run | rules (#13) |
| `height` | float | Ascent: m above the climb start, along up; 0 elsewhere | Ascent mode (#27) |

The brief listed 13 fields. Five fields are new, and each one has a use in a ticket:

- `tick`: harness step checks and respawn timing.
- `level`: checks that `load_level` loaded the level.
- `up`: #10 and #11.
- `medal`: #13.
- `egg_found`: #13.

## 7. Layout and file ownership

```
game/
├── project.godot              #4; #7 edits it once (see below)
├── core/
│   ├── game.gd                #7 (autoload Game)
│   ├── marble_tuning.tres     #7 creates it; #10 tunes it
│   ├── input/                 #7: marble_input, input_source, input_hub, player_source (#18 adds the pad later)
│   ├── marble/                #7, then #10: marble.gd/.tscn, marble_tuning.gd, world_query.gd, contact.gd
│   ├── gravity/               #10: gravity_field.gd, uniform_gravity.gd/.tscn
│   ├── camera/                #7 follow_camera.gd, then #11: orbit camera, blob shadow
│   └── level/                 #7: level, level_run, level_object, solid, surface, default_surface.tres, game_state
│       ├── rules.gd           stub from #7, then #13
│       └── power_up_slot.gd   stub from #7, then #17
├── objects/
│   ├── start/                 #7
│   ├── gem/ finish/ checkpoint/ egg/      placeholder scenes from #7, then #13
│   └── moving_platform/ turning_gear/     #12
├── levels/                    #8: level_import.gd (post-import script), built/ (ignored by git)
├── harness/                   #9 (the route bot from #14 goes here later)
└── test/
    ├── support/run_test.gd    #7
    ├── levels/flat.tscn       #7; every other test level has one owner, its creator (#10: physics.tscn, pusher.gd)
    ├── core/                  test_marble_roll and test_player_source #7, test_marble_physics #10, test_camera #11
    ├── level/                 test_game_state #7, test_level_import #8, test_rules #13
    ├── objects/<type>/        the owner of objects/<type>/
    └── harness/               #9
```

Outside `game/`, #8 owns `kit/`, `levels/` and `tools/blender/`, and #9 owns `tools/harness/`.

Rules:

1. One file has one owner. To change another ticket's file, ask its owner. To call its public API, no request is necessary.
2. **Order:** the #7 PR merges first. It holds the contract files and the v0 solver. After that, #8, #9, #10, #11, #12 and #13 run in parallel. Then #10 owns `core/marble/` and the tuning file. The carry tests of #12 use that friction, so #10 keeps them green.
3. **Shared one-time edits from #7 in `project.godot`:**
   - the autoloads `Game` and `InputHub`;
   - the layer names `solid` and `trigger`;
   - the Jolt query setting from §1, item 7;
   - the input actions for #7's keys.

   Later autoloads (Save in #21, Music in #25) add one line each. If two edits conflict there, keep both lines.
4. **justfile:** #7 adds `run` and #8 adds `build-levels`, each as its own block. The CI workflow gets one new job, from #8.
5. **Kit:** #8 builds one generic marker helper, `marker(type, **settings)`. Then object tickets do not need to edit `kit/`.
6. **Test levels:** make a new test level. Do not edit a test level that another ticket owns.
7. **GLOSSARY.md:** #7 adds MarbleInput, InputSource, LevelRun, GameState, Solid, LevelObject, tick and sub-step.

## 8. Test pattern

Every run test extends `RunTest` and uses only the boundary: `start_run`, `MarbleInput`, `run.step` and `run.state`. A test may use `run.marble.teleport()`, because the harness `teleport` command uses the same call. The code below passed in the prototype, as written, under the #4 strict settings with GUT 9.7.1. The prototype solver was a placeholder.

```gdscript
# test/support/run_test.gd (#7)
class_name RunTest
extends GutTest
## Base for tests that drive a LevelRun through MarbleInput and read GameState.

var run: LevelRun


## Loads level, adds extra nodes to it, and starts a run that only steps when told.
func start_run(level: PackedScene, extra: Array[Node3D] = []) -> LevelRun:
	var root: Level = level.instantiate() as Level
	for node: Node3D in extra:
		root.add_child(node)
	run = LevelRun.create(root)
	run.auto_step = false
	add_child_autofree(run)
	return run


## Steps the run for seconds of simulated time with one held input.
func hold(input: MarbleInput, seconds: float) -> void:
	for i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(input)


## A MarbleInput that rolls along move (x right, y forward).
func rolling(move: Vector2) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.move = move
	return input
```

```gdscript
# test/core/test_marble_roll.gd (#7)
extends RunTest
## Rolling feel, through the boundary only: MarbleInput in, GameState out.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")


func before_each() -> void:
	start_run(FLAT)


func test_reaches_top_speed_in_expected_time() -> void:
	var expected: float = TUNING.max_roll_speed / (TUNING.angular_acceleration * TUNING.radius)
	hold(rolling(Vector2(0, 1)), expected * 0.5)
	assert_almost_eq(run.state.velocity.length(), TUNING.max_roll_speed * 0.5, 0.5)
	hold(rolling(Vector2(0, 1)), expected * 0.6)
	assert_almost_eq(run.state.velocity.length(), TUNING.max_roll_speed, 0.1)
	assert_true(run.state.on_ground)


func test_input_never_lowers_speed() -> void:
	run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3(0, 0, -25))
	hold(rolling(Vector2(0, 1)), 0.5)
	assert_gte(run.state.velocity.length(), 24.99)
```

An object test adds the object with `start_run(FLAT, [bumper])`, rolls the marble into it and checks `run.state.velocity`. It checks the feedback with `watch_signals(run)` and `assert_signal_emit_count(run, "feedback", 1)`.

`flat.tscn` has a `Level` root, a `Solid` floor with a `ConcavePolygonShape3D` whose faces point up (F6), and a `start` object at the origin. For a trimesh built in code, use `Mesh.create_trimesh_shape()` or follow the winding rule in F6.

## 9. Rejected alternatives

| Alternative | Why it was rejected |
|---|---|
| Physics frames drive the marble, and tests `await wait_physics_frames()` with `--fixed-fps 120` | It works (F13 measured 2.3 ms per simulated second, and F3 gives point velocities). But every test needs awaits and a command-line flag, the order inside a tick depends on node order, and kinematic transforms lag one tick (F11). It is the fallback if Sean rejects deviation A |
| `Engine.time_scale` to make tests faster | It changes dt, not the number of ticks (F14) |
| `AnimatableBody3D` movers | Their transform changes reach queries one frame late (F11). The solver gets the velocity from `Solid` instead |
| `get_rest_info` as the contact query | It gives one contact per call and misses corners (F3) |
| A home-made filter for internal edges | It only halved the drift (F7) |
| `Area3D` signals for triggers | The marble would need to be a body, and the signals arrive at the physics step, not inside `step()` |
| A shared enum for feedback kinds | Every object ticket would edit one file |
| Marker settings as a Dictionary at run time | That is an untyped seam. The importer writes the `@export` vars instead |
| Tests in `objects/<type>/` (plan §4.1) | The #4 exports exclude only `test/*`, and GUT scans only `res://test/`. Deviation B |
| `PhysicsServer3D.body_test_motion` | Not prototyped. It needs the marble to be a body |

## 10. Open risks and decisions

1. **Deviation A (Sean):** plan §4.2 and issue #1 say that movers are animatable bodies and that the engine gives their velocity. This design uses `Solid` (`StaticBody3D`) bodies that code moves, and the velocity comes from `Solid`. The fallback is the first rejected alternative.
2. **Deviation B (Sean):** object tests live in `test/objects/<type>/`, not in `objects/<type>/`.
3. **Order:** plan §7 says that one agent builds Phase 1 in order. Parallel work is safe only after the #7 PR merges.
4. **#8 must split collision by surface type** (one `Solid` for each material, A2). #8 must also check face winding with its fixture (A4).
5. **Marker vectors:** use child empties for positions and paths (A1).
6. **Render smoothness:** the run steps at 120 Hz. Displays faster than 120 Hz need physics interpolation or camera smoothing (#11, #24). Harness `step` bursts draw no frames between ticks.
7. **Pose from time:** movers calculate their pose from `t`. An object authored with `AnimationPlayer` cannot drive collision. This is fine for the M1 set. Check it again for the M3 objects.
8. **Held buttons:** `jump` and `use` are held states. The code that reads them finds the press. A held jump repeats: the marble jumps again at each landing (#10).
9. **Precision:** JSON vectors carry 32-bit noise (F17). Cross-OS repeatability is not checked (F15).
