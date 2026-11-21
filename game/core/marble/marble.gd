class_name Marble
extends Node3D
## The marble and its solver (docs/plan.md §4.2). The node position is the marble centre in
## world space, because LevelRun stays at the origin. LevelRun calls step() once per tick, and
## step() reads only its arguments and this node's own fields. Objects change the marble only
## through add_velocity() and teleport().
##
## Solver v0 (#7) rolls: gravity, contacts, and a spin that input drives, coupled to the
## velocity by friction at the ground. #10 adds jumps, bounces, slides, air control, gravity
## fields and the full sweep at the steps that _substep() marks.

## Rumble and sound: &"marble.land", &"marble.bounce", &"marble.jump" (#10 emits them).
@warning_ignore("unused_signal")
signal feedback(kind: StringName, strength: float, at: Vector3)

## Moment of inertia of a solid sphere, as a factor of mass × radius².
const INERTIA: float = 0.4
## Gap that the response leaves between the marble and a surface, m. A sweep that starts in
## exact contact stops at once for the smallest move into the surface.
const SKIN: float = 0.0001

@export var tuning: MarbleTuning

## Linear velocity, m/s.
var velocity: Vector3 = Vector3.ZERO
## Angular velocity, rad/s.
var spin: Vector3 = Vector3.ZERO
## Opposite of gravity, unit length.
var up: Vector3 = Vector3.UP
## Reference for MarbleInput.camera_yaw; y is up. #10 turns it by the shortest arc when up
## changes.
var frame: Basis = Basis.IDENTITY
## True when the last sub-step had a contact.
var on_ground: bool = false
## After step(): the first contact with each touched object.
var touches: Array[Contact] = []
## After step(): the objects whose triggers overlapped in any sub-step.
var overlaps: Array[LevelObject] = []

@onready var _ball: Node3D = $Ball


## Advances the marble by one tick of dt seconds. Each sub-step moves at most
## max_substep_move radii.
func step(dt: float, input: MarbleInput, world: WorldQuery) -> void:
	touches.clear()
	overlaps.clear()
	var reach: float = tuning.max_substep_move * tuning.radius
	var count: int = clampi(ceili(velocity.length() * dt / reach), 1, tuning.max_substeps)
	for _i: int in count:
		_substep(dt / count, input, world)
	_turn_ball(dt)


## Adds delta_v to the velocity, for example a bumper's push. The spin does not change.
func add_velocity(delta_v: Vector3) -> void:
	velocity += delta_v


## Puts the marble at `at` with new_velocity. The spin becomes the spin that rolls at
## new_velocity on a floor normal to up, so a marble put on the ground does not slip.
func teleport(at: Vector3, new_velocity: Vector3) -> void:
	position = at
	velocity = new_velocity
	spin = up.cross(new_velocity) / tuning.radius


## One sub-step of h seconds, in the order of docs/design/core-runtime.md §3.
func _substep(h: float, input: MarbleInput, world: WorldQuery) -> void:
	# 1. Gravity. #10: the gravity field with the highest priority.
	velocity -= up * tuning.gravity * h
	# 2. Contacts.
	var contacts: Array[Contact] = world.contacts(position)
	on_ground = not contacts.is_empty()
	# 3. Response. The ground is the contact that pushes hardest.
	var ground: Contact = null
	var pressure: float = 0.0
	for contact: Contact in contacts:
		var push: float = _meet(contact)
		if push > pressure:
			ground = contact
			pressure = push
	# 4. Rolling. #10: air control when there is no ground, then the jump.
	if ground != null:
		_roll(ground, pressure, h, input)
	# 5. Sweep. #10: after a hit, use the rest of the move.
	var motion: Vector3 = velocity * h
	position += motion * world.sweep(position, motion)
	# 6. Touched objects and triggers.
	_note(contacts, world)


## Stops the motion into contact and pushes the marble out to SKIN above the surface. Returns
## the speed that it took away along the normal. #10 adds the bounce and the slide here.
func _meet(contact: Contact) -> float:
	if contact.depth > -SKIN:
		position += contact.normal * (contact.depth + SKIN)
	var closing: float = (velocity - contact.velocity).dot(contact.normal)
	if closing >= 0.0:
		return 0.0
	velocity -= contact.normal * closing
	return -closing


## Drives the spin toward the spin that input asks for (braking with no input), and couples
## spin and velocity through friction at ground. pressure is the normal speed that ground took
## away in this sub-step; it limits the friction. While static friction holds, the ground
## turns each spin change into velocity and the marble rolls without slip. Past that limit,
## the contact slips and kinetic friction pulls it back toward rolling.
func _roll(ground: Contact, pressure: float, h: float, input: MarbleInput) -> void:
	var n: Vector3 = ground.normal
	var r: float = tuning.radius
	var relative: Vector3 = velocity - ground.velocity
	relative -= n * relative.dot(n)
	var target: Vector3 = n.cross(_wished_velocity(input, n, relative)) / r
	var rate: float = tuning.braking_acceleration
	if input.move != Vector2.ZERO:
		rate = tuning.angular_acceleration
	var motor: Vector3 = (target - spin).limit_length(rate * h)
	# Velocity of the contact point over the surface. Friction removes it.
	var slip: Vector3 = relative - r * spin.cross(n)
	var grip: float = pressure * ground.surface.friction
	# Of a friction impulse, this part changes the velocity; the rest changes the spin.
	var share: float = INERTIA / (1.0 + INERTIA)
	var change: Vector3 = r * motor.cross(n) - slip * share
	if change.length() <= tuning.static_friction * grip:
		velocity += change
		spin += motor + n.cross(slip) * ((1.0 - share) / r)
		return
	spin += motor
	slip -= r * motor.cross(n)
	change = (-slip * share).limit_length(tuning.kinetic_friction * grip)
	velocity += change
	spin -= n.cross(change) / (INERTIA * r)


## Returns the rolling velocity that input asks for, in the plane of normal n. On each camera
## axis that input pushes along the current velocity, a faster current speed stays the
## target, so input never slows the marble below its current speed.
func _wished_velocity(input: MarbleInput, n: Vector3, current: Vector3) -> Vector3:
	var heading: Basis = frame * Basis(Vector3.UP, input.camera_yaw)
	var right: Vector3 = (heading.x - n * heading.x.dot(n)).normalized()
	var forward: Vector3 = (n * heading.z.dot(n) - heading.z).normalized()
	var x: float = _keep_faster(input.move.x * tuning.max_roll_speed, current.dot(right))
	var y: float = _keep_faster(input.move.y * tuning.max_roll_speed, current.dot(forward))
	return right * x + forward * y


## Returns current instead of wished when both have the same sign and current is faster.
static func _keep_faster(wished: float, current: float) -> float:
	if wished * current > 0.0 and absf(current) > absf(wished):
		return current
	return wished


## Records the first contact with each touched object, and the triggers at the new position.
func _note(contacts: Array[Contact], world: WorldQuery) -> void:
	for contact: Contact in contacts:
		if contact.object != null and not _touched(contact.object):
			touches.append(contact)
	for object: LevelObject in world.overlaps(position):
		if not overlaps.has(object):
			overlaps.append(object)


func _touched(object: LevelObject) -> bool:
	for contact: Contact in touches:
		if contact.object == object:
			return true
	return false


## Turns the visible ball by this tick's spin.
func _turn_ball(dt: float) -> void:
	var rate: float = spin.length()
	if rate > 0.0:
		_ball.basis = (Basis(spin / rate, rate * dt) * _ball.basis).orthonormalized()
