"""Ascent fixture, zone 3 of 3 (#27): three ramps, from 24 to 36 m, and the top deck.

See ascent_fixture_1.py for the layout of the climb. This zone starts beside the finish of
zone 2. It is the last zone, so in Ascent its finish pad is the "to be continued" gate.
"""

import kit

kit.level(title="Ascent fixture 3", par=15.8, gold=9.7)

kit.track(at=(20, 0, 24), width=4, length=4, name="base_3")
kit.ramp(at=(20, 4, 24), length=12, rise=4, name="flight_6")
kit.track(at=(22, 16, 28), width=8, length=4, name="landing_6")
kit.ramp(at=(24, 16, 28), length=12, rise=4, yaw=180, name="flight_7")
kit.track(at=(26, 0, 32), width=8, length=4, name="landing_7")
kit.ramp(at=(28, 4, 32), length=12, rise=4, name="flight_8")
kit.track(at=(28, 16, 36), width=8, length=8, name="top_3")

kit.marker("start", at=(20, 2, 24))
kit.marker("finish", at=(28, 21, 36))

POINTS = [
    (20, 4, 24),
    (20, 16, 28),
    (20, 18, 28),
    (24, 18, 28),
    (24, 16, 28),
    (24, 4, 32),
    (24, 2, 32),
    (28, 2, 32),
    (28, 4, 32),
    (28, 16, 36),
    (28, 21, 36),
]
kit.marker(
    "route",
    at=(20, 2, 24),
    points=POINTS,
    name="route_first_run",
    kind="first_run",
    actions="3 wait 1; 7 wait 1",
)
kit.marker(
    "route",
    at=(20, 2, 24),
    points=POINTS,
    name="route_expert",
    kind="expert",
    actions="3 wait 0; 7 wait 0",
)

kit.shot("gate_view", at=(28, 11, 38.5), rotation=(-8, 0, 0))
kit.shot("top_view", at=(40, 6, 44), rotation=(-24, 0, 38))
