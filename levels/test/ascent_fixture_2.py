"""Ascent fixture, zone 2 of 3 (#27): a ramp, a lift and a ramp, from 12 to 24 m.

See ascent_fixture_1.py for the layout of the climb. This zone starts beside the finish of
zone 1. In place of flight 4 it has a lift: a moving platform that rises 4 m, and a level
walkway from its top. The lift waits 1.5 s at the bottom from cycle time 0 and 1.5 s at the
top from cycle time 4.
"""

import kit

kit.level(title="Ascent fixture 2", par=27.1, gold=19.6)

kit.track(at=(8, 16, 12), width=4, length=4, name="base_2")
kit.ramp(at=(8, 16, 12), length=12, rise=4, yaw=180, name="flight_3")
kit.track(at=(10, 0, 16), width=8, length=4, name="landing_3")
kit.marker(
    "moving_platform",
    at=(12, 6, 16),
    points=[(12, 6, 20)],
    name="lift",
    period=8.0,
    stop=1.5,
)
kit.track(at=(12, 8, 20), width=4, length=8, name="walkway")
kit.track(at=(14, 16, 20), width=8, length=4, name="landing_4")
kit.ramp(at=(16, 16, 20), length=12, rise=4, yaw=180, name="flight_5")
kit.track(at=(16, 0, 24), width=4, length=4, name="top_2")

kit.marker("start", at=(8, 18, 12))
kit.marker("finish", at=(16, 2, 24))

# Both routes stop in front of the lift until it is at the bottom, ride it from its middle and
# leave it at the top. They stop on the finish pad, as in zone 1.
POINTS = [
    (8, 16, 12),
    (8, 4, 16),
    (8, 2, 16),
    (12, 2.5, 16),
    (12, 6, 16),
    (12, 12, 20),
    (12, 18, 20),
    (16, 18, 20),
    (16, 16, 20),
    (16, 4, 24),
    (16, 2, 24),
]
LIFT = "3 wait_until lift 7.7 0.3; 4 wait_until lift 4.0 5.0"
kit.marker(
    "route",
    at=(8, 18, 12),
    points=POINTS,
    name="route_first_run",
    kind="first_run",
    actions=f"2 wait 1; {LIFT}; 7 wait 1; 10 wait 0",
)
kit.marker(
    "route",
    at=(8, 18, 12),
    points=POINTS,
    name="route_expert",
    kind="expert",
    actions=f"2 wait 0; {LIFT}; 7 wait 0; 10 wait 0",
)

kit.shot("lift_view", at=(22, -6, 21), rotation=(-12, 0, 40))
