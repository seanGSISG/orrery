class_name Marble
extends Node3D
## The marble and its solver (docs/plan.md §4.2). The node position is the marble centre in
## world space, because LevelRun stays at the origin. LevelRun calls step() once per tick, and
## step() reads only its arguments and this node's own fields. Objects change the marble only
## through add_velocity() and teleport().
##
## Input drives the spin, and friction at the ground couples the spin to the velocity. A hit
## bounces, slides or stops the marble. The jump and air control change the velocity. Gravity
## comes from the GravityField with the highest priority that the marble overlaps, and up is
## its opposite. Every value comes from MarbleTuning. docs/design/core-runtime.md §3 gives
## the order of one sub-step.

## Rumble and sound. kind is &"marble.land", &"marble.bounce" or &"marble.jump"; strength is
## 0..1; at is the touched point.
signal feedback(kind: StringName, strength: float, at: Vector3)

## Moment of inertia of a solid sphere, as a factor of mass × radius².
const INERTIA: float = 0.4
## Of a friction impulse at the contact point, this part changes the velocity. The rest
## changes the spin.
const SHARE: float = INERTIA / (1.0 + INERTIA)
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
## Reference for MarbleInput.camera_yaw; y is up. It turns by the shortest arc when up
## changes.
var frame: Basis = Basis.IDENTITY
## True when the last sub-step had a contact.
var on_ground: bool = false
## After step(): the first contact with each touched object.
var touches: Array[Contact] = []
## After step(): the objects whose triggers overlapped in any sub-step.
var overlaps: Array[LevelObject] = []

## Gravity for the next sub-step, m/s².
var _gravity: Vector3 = Vector3.ZERO
## True when the last sub-step stood on a floor, so the next hit on a floor is no landing.
var _standing: bool = false

@onready var _ball: Node3D = $Ball


## Advances the marble by one tick of dt seconds. Each sub-step lasts until the marble has
## moved max_substep_move radii at its speed in that sub-step, or until the tick ends. The
## last of max_substeps sub-steps takes the rest of the tick, and the sweep still stops it at
## the first surface.
func step(dt: float, input: MarbleInput, world: WorldQuery) -> void:
	touches.clear()
	overlaps.clear()
	_feel_gravity(world.overlaps(position))
	var left: float = dt
	for i: int in tuning.max_substeps:
		var reach: float = tuning.max_substep_move * tuning.radius
		if i == tuning.max_substeps - 1:
			reach = INF
		left -= _substep(left, reach, input, world)
		if left <= 0.0:
			break
	_turn_ball(dt)


## Adds delta_v to the velocity, for example a bumper's push. The spin does not change.
func add_velocity(delta_v: Vector3) -> void:
	velocity += delta_v


## Puts the marble at `at` with new_velocity. The spin becomes the spin that rolls at
## new_velocity on a floor normal to up, so a marble put on the ground does not slip.
## on_ground is false until the next step finds the contacts. The marble is drawn at `at` at
## once, not on an interpolated path from the old place.
func teleport(at: Vector3, new_velocity: Vector3) -> void:
	position = at
	velocity = new_velocity
	spin = up.cross(new_velocity) / tuning.radius
	on_ground = false
	_standing = false
	reset_physics_interpolation()


## One sub-step of at most `left` seconds that moves the marble at most reach. Returns its
## length in seconds.
func _substep(left: float, reach: float, input: MarbleInput, world: WorldQuery) -> float:
	var h: float = left
	if reach < INF:
		h = minf(left, _span(reach))
	# 1. Contacts.
	var contacts: Array[Contact] = world.contacts(position)
	var landing: bool = not _standing
	on_ground = not contacts.is_empty()
	# 2. Hits, with the velocity from before this sub-step's gravity.
	var hits: Array[Contact] = []
	for contact: Contact in contacts:
		if _hit(contact, h, landing):
			hits.append(contact)
	# 3. Gravity.
	velocity += _gravity * h
	# 4. Support. The ground is the most upward floor that the marble hit, or touched (within
	# 2 SKIN) and presses on. A marble that only closes a gap to the floor still flies.
	var ground: Contact = null
	var pressure: float = 0.0
	for contact: Contact in contacts:
		var push: float = _meet(contact, h)
		var rise: float = contact.normal.dot(up)
		var pressed: bool = push > 0.0 and contact.depth > -2.0 * SKIN
		if rise < tuning.floor_min_up or not (pressed or hits.has(contact)):
			continue
		if ground == null or rise > ground.normal.dot(up):
			ground = contact
			pressure = push
	_standing = ground != null
	# 5. Rolling and the jump on the ground, air control in the air.
	if ground != null:
		_roll(ground, pressure, h, input)
		if input.jump:
			_jump(ground)
	else:
		_steer(input, h)
	# 6. Sweep. An impulse in this sub-step (a jump, a hit by a mover, friction at a bounce)
	# can make the move longer than reach. Then the sub-step ends early.
	var motion: Vector3 = velocity * h
	if motion.length() > reach:
		h *= reach / motion.length()
		motion = velocity * h
	position += motion * world.sweep(position, motion)
	# 7. Touched objects, triggers, and the gravity at the new position.
	_note(contacts, world)
	return h


## Handles a hit on contact's surface when the marble reaches it in this sub-step of h
## seconds. All speeds are relative to the surface. A glancing hit (slide_threshold) or a hit
## slower than min_bounce_speed loses its speed into the surface and slides on; the speed
## along the surface stays. Any other hit bounces with the restitution, and bounce friction
## acts at the contact point. A hit on a floor that ends a flight (landing is true) emits
## marble.land; any other bounce emits marble.bounce. Returns true when the marble hit.
func _hit(contact: Contact, h: float, landing: bool) -> bool:
	var n: Vector3 = contact.normal
	var relative: Vector3 = velocity - contact.velocity
	var closing: float = -relative.dot(n)
	if closing <= 0.0 or closing * h < -contact.depth - SKIN:
		return false
	var bounced: bool = false
	var glancing: bool = closing < tuning.slide_threshold * relative.length()
	if glancing or closing < tuning.min_bounce_speed:
		velocity += n * closing
	else:
		var bounce: float = tuning.restitution * contact.surface.restitution
		velocity += n * closing * (1.0 + bounce)
		var grip: float = tuning.bounce_friction * contact.surface.friction
		_rub(n, contact.velocity, grip * closing * (1.0 + bounce))
		bounced = true
	var strength: float = minf(closing / tuning.hard_impact_speed, 1.0)
	var floor_hit: bool = n.dot(up) >= tuning.floor_min_up
	if landing and floor_hit and closing >= tuning.min_bounce_speed:
		feedback.emit(&"marble.land", strength, contact.point)
	elif bounced:
		feedback.emit(&"marble.bounce", strength, contact.point)
	return true


## Pushes the marble out to SKIN above contact's surface, and stops the part of the motion into
## it that would pass that point in this sub-step of h seconds. So a marble inside the margin
## only closes the gap. Returns the speed taken away along the normal.
func _meet(contact: Contact, h: float) -> float:
	# The depth at the current position: an earlier contact may have pushed the marble out.
	var depth: float = tuning.radius - (position - contact.point).dot(contact.normal)
	if depth > -SKIN:
		position += contact.normal * (depth + SKIN)
	var gap: float = maxf(-depth - SKIN, 0.0)
	var excess: float = (contact.velocity - velocity).dot(contact.normal) - gap / h
	if excess <= 0.0:
		return 0.0
	velocity += contact.normal * excess
	return excess


## Drives the spin toward the spin that input asks for (braking with no input), and couples
## spin and velocity through friction at ground. pressure is the normal speed that ground took
## away in this sub-step; it limits the friction, and the ground's Surface scales it. While
## static friction holds, the ground turns each spin change into velocity and the marble rolls
## without slip. Past that limit, the contact slips and kinetic friction pulls it back toward
## rolling.
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
	var change: Vector3 = r * motor.cross(n) - slip * SHARE
	if change.length() <= tuning.static_friction * grip:
		velocity += change
		spin += motor + n.cross(slip) * ((1.0 - SHARE) / r)
		return
	spin += motor
	_rub(n, ground.velocity, tuning.kinetic_friction * grip)


## Applies friction at the contact point below normal n, on a surface that moves at
## surface_velocity: an impulse of at most limit m/s against the slip of that point. SHARE of
## it changes the velocity and the rest changes the spin.
func _rub(n: Vector3, surface_velocity: Vector3, limit: float) -> void:
	var relative: Vector3 = velocity - surface_velocity
	var slip: Vector3 = relative - n * relative.dot(n) - tuning.radius * spin.cross(n)
	var change: Vector3 = (-slip * SHARE).limit_length(limit)
	velocity += change
	spin -= n.cross(change) / (INERTIA * tuning.radius)


## Jumps off ground along its normal: the speed away from the surface rises to jump_impulse.
## A marble that already moves away faster keeps its speed. A held jump jumps again at the
## next landing. Only a floor is ground (floor_min_up), so a wall or a ceiling gives no jump,
## and one flight cannot jump twice.
func _jump(ground: Contact) -> void:
	var rise: float = tuning.jump_impulse - (velocity - ground.velocity).dot(ground.normal)
	if rise > 0.0:
		velocity += ground.normal * rise
		feedback.emit(&"marble.jump", minf(rise / tuning.jump_impulse, 1.0), ground.point)


## Air control: input accelerates the marble at air_acceleration, relative to the camera, in
## the plane normal to up. It pushes only until the speed along the input direction reaches
## the speed that input asks for on the ground (max_roll_speed at full input), so hops do not
## add speed. A faster marble keeps its speed. The spin does not change in the air.
func _steer(input: MarbleInput, h: float) -> void:
	var axes: Basis = _axes(input, up)
	var push: Vector3 = axes.x * input.move.x + axes.z * input.move.y
	if push.is_zero_approx():
		return
	var along: Vector3 = push.normalized()
	var room: float = tuning.max_roll_speed * push.length() - velocity.dot(along)
	velocity += along * maxf(minf(tuning.air_acceleration * push.length() * h, room), 0.0)


## Returns the rolling velocity that input asks for, in the plane of normal n. Full input asks
## for max_roll_speed on any slope. On each axis that input pushes along the current velocity,
## a faster current speed stays the target, so input never slows the marble below its current
## speed.
func _wished_velocity(input: MarbleInput, n: Vector3, current: Vector3) -> Vector3:
	var axes: Basis = _axes(input, n)
	var x: float = _keep_faster(input.move.x * tuning.max_roll_speed, current.dot(axes.x))
	var y: float = _keep_faster(input.move.y * tuning.max_roll_speed, current.dot(axes.z))
	return axes.x * x + axes.z * y


## Returns the camera's right (x) and forward (z) in the plane of normal n, with y = n. They
## are orthonormal. The camera looks along -z of its heading in frame.
func _axes(input: MarbleInput, n: Vector3) -> Basis:
	var heading: Basis = frame * Basis(Vector3.UP, input.camera_yaw)
	var forward: Vector3 = (n * heading.z.dot(n) - heading.z).normalized()
	return Basis(forward.cross(n), n, forward)


## Returns how long the marble takes to move reach with its speed and the largest steady
## acceleration of a sub-step (gravity, air control and rolling): the root h of
## (speed + acceleration × h) × h = reach. So only an impulse can make a move longer.
func _span(reach: float) -> float:
	var speed: float = velocity.length()
	var steady: float = (
		_gravity.length() + tuning.air_acceleration + tuning.angular_acceleration * tuning.radius
	)
	return 2.0 * reach / (speed + sqrt(speed * speed + 4.0 * steady * reach))


## Returns current instead of wished when both have the same sign and current is faster.
static func _keep_faster(wished: float, current: float) -> float:
	if wished * current > 0.0 and absf(current) > absf(wished):
		return current
	return wished


## Records the first contact with each touched object and the triggers at the new position,
## and takes the gravity there for the next sub-step.
func _note(contacts: Array[Contact], world: WorldQuery) -> void:
	for contact: Contact in contacts:
		if contact.object != null and not _touched(contact.object):
			touches.append(contact)
	var found: Array[LevelObject] = world.overlaps(position)
	for object: LevelObject in found:
		if not overlaps.has(object):
			overlaps.append(object)
	_feel_gravity(found)


## Returns true when touches already holds a contact with object.
func _touched(object: LevelObject) -> bool:
	for contact: Contact in touches:
		if contact.object == object:
			return true
	return false


## Takes the gravity from the GravityField in found with the highest priority, else
## MarbleTuning.gravity straight down. Turns up and frame by the shortest arc to match. A field
## without gravity keeps the last up.
func _feel_gravity(found: Array[LevelObject]) -> void:
	var field: GravityField = null
	for object: LevelObject in found:
		var candidate: GravityField = object as GravityField
		if candidate != null and (field == null or candidate.priority > field.priority):
			field = candidate
	_gravity = Vector3.DOWN * tuning.gravity
	if field != null:
		_gravity = field.gravity_at(position)
	if _gravity.is_zero_approx():
		return
	var new_up: Vector3 = -_gravity.normalized()
	if new_up != up:
		frame = (Basis(Quaternion(up, new_up)) * frame).orthonormalized()
		up = new_up


## Turns the visible ball by this tick's spin. A spin below 1 mrad/s does not show, and its
## length is too small to normalize the axis in 32 bits.
func _turn_ball(dt: float) -> void:
	var rate: float = spin.length()
	if rate > 0.001:
		_ball.basis = (Basis(spin / rate, rate * dt) * _ball.basis).orthonormalized()
