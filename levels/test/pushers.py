"""Pusher fixture for game/test/objects/bumper/test_pushers_fixture.gd: one wide track with a
start, a bumper, a steam vent, a pendulum that swings across the track, and a finish. The test
expects these positions and settings."""

import kit

kit.level(title="Pusher fixture", par=40.0, gold=20.0)

kit.track(at=(0, 0, 0), width=12, length=40)
kit.marker("start", at=(0, 2, 0))

# Settings differ from the defaults, so the fixture test shows that the importer wrote them.
kit.marker("bumper", at=(0, 8, 0), speed=12.0, radius=0.6, height=1.2)
kit.marker("steam_vent", at=(0, 16, 0), lift=6.0, radius=1.2, push=50.0)
# The bob (radius 0.5) passes 5 cm above the track: pivot height = length + radius + 0.05.
kit.marker(
    "pendulum",
    at=(0, 26, 4.05),
    period=3.0,
    swing=50.0,
    length=3.5,
    radius=0.5,
    offset=0.5,
)

kit.marker("finish", at=(0, 36, 0))

kit.shot("overview", at=(16, 2, 10), rotation=(-24, 0, 45))
kit.shot("bumper", at=(4, 3, 3), rotation=(-21, 0, 39))
kit.shot("vent", at=(9, 10, 4), rotation=(-5, 0, 56))
kit.shot("pendulum", at=(0, 17, 3), rotation=(-6, 0, 0))
