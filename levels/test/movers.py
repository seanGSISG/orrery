"""Mover fixture for game/test/objects/moving_platform/test_movers_fixture.gd: a start track,
a moving platform that carries the marble 12 m forward, a turning gear beyond it and a finish
track. The test expects these positions and settings."""

import kit

kit.level(title="Mover fixture", par=40.0, gold=20.0)

kit.track(at=(0, 0, 0), length=8)
kit.marker("start", at=(0, 2, 0))

# The deck (4 x 4 m) starts flush with the end of the start track and stops flush with the gear.
kit.marker(
    "moving_platform",
    at=(0, 10, 0),
    points=[(0, 22, 0)],
    period=9.0,
    stop=1.5,
)
kit.marker("turning_gear", at=(0, 26.1, 0), period=6.0, radius=2.1, teeth=10)

kit.track(at=(0, 28.2, 0), length=8)
kit.marker("finish", at=(0, 34, 0))

# Route bot (#14). The deck waits at the start from cycle time 0 to 1.5 s and at the far end
# from 4.5 to 6 s. First run: wait at the end of the track for the deck to come back, ride it,
# cross the gear. Expert: board the deck in its first stop.
kit.marker(
    "route",
    at=(0, 2, 0),
    points=[(0, 7, 0), (0, 10, 0), (0, 26.1, 0), (0, 34, 0)],
    name="route_first_run",
    kind="first_run",
    actions="0 wait_until moving_platform_00 8.6 0.2; 1 wait_until moving_platform_00 4.5 5.6",
)
kit.marker(
    "route",
    at=(0, 2, 0),
    points=[(0, 10, 0), (0, 26.1, 0), (0, 34, 0)],
    name="route_expert",
    kind="expert",
    actions="0 wait_until moving_platform_00 4.5 5.6",
)

kit.shot("overview", at=(14, 4, 12), rotation=(-35, 0, 75))
kit.shot("platform", at=(7, 9, 4), rotation=(-25, 0, 60))
kit.shot("gear", at=(6, 21, 5), rotation=(-35, 0, 50))
