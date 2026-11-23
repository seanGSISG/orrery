"""Ascent fixture, zone 1 of 3 (#27): the ground and three ramps, from 0 to 12 m.

The three fixture zones make one short climb for the Ascent tests
(game/test/modes/ascent/). Each zone is a level of its own, as the real zones are: it has
its own start pad on its own floor, a finish pad at its top and both routes. The zones use
the climb's coordinates, so the mode loads them all at the origin: zone 2 starts beside the
finish of zone 1, on a floor that is flush with it.

The climb is a stair of nine flights. Flight i is 4 m wide, at x = 4 i - 4, and rises from
4 i m to 4 i + 4 m: even flights go north (+y), odd flights go south. A landing joins each
flight to the next. The ground is wide, so a fall from any flight of the climb lands on it.
"""

import kit

kit.level(title="Ascent fixture 1", par=16.4, gold=10.2)

kit.track(at=(8, -12, 0), width=60, length=44, name="ground")
kit.ramp(at=(-4, 4, 0), length=12, rise=4, name="flight_0")
kit.track(at=(-2, 16, 4), width=8, length=4, name="landing_0")
kit.ramp(at=(0, 16, 4), length=12, rise=4, yaw=180, name="flight_1")
kit.track(at=(2, 0, 8), width=8, length=4, name="landing_1")
kit.ramp(at=(4, 4, 8), length=12, rise=4, name="flight_2")
kit.track(at=(4, 16, 12), width=4, length=4, name="top_1")

kit.marker("start", at=(-4, 0, 0))
# A room's light (objects/room_probe), which the climb keeps.
kit.marker("room_probe", at=(20, 0, 0), width=4.0, depth=4.0, height=3.0, name="room")
kit.marker("finish", at=(4, 18, 12))

POINTS = [
    (-4, 4, 0),
    (-4, 16, 4),
    (-4, 18, 4),
    (0, 18, 4),
    (0, 16, 4),
    (0, 4, 8),
    (0, 2, 8),
    (4, 2, 8),
    (4, 4, 8),
    (4, 16, 12),
    (4, 18, 12),
]
kit.marker(
    "route",
    at=(-4, 0, 0),
    points=POINTS,
    name="route_first_run",
    kind="first_run",
    actions="3 wait 1; 7 wait 1; 10 wait 0",
)
# The expert stops at each landing too, but does not wait: a stop makes the turn faster than
# a line through it. Both routes stop on the finish pad: in the climb the pad is gone, and the
# marble must not roll off the top floor.
kit.marker(
    "route",
    at=(-4, 0, 0),
    points=POINTS,
    name="route_expert",
    kind="expert",
    actions="3 wait 0; 7 wait 0; 10 wait 0",
)

kit.shot("overview", at=(-26, -22, 30), rotation=(-22, 0, -52))
kit.shot("ground_view", at=(-10, -8, 3), rotation=(-4, 0, -40))
