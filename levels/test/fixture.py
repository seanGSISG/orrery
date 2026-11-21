"""Pipeline fixture for game/test/level/test_level_import.gd: a track, a ramp up to a second
track, one start, three gems, one finish and the four gallery shots. The test expects these
positions and counts."""

import kit

kit.level(title="Pipeline fixture", par=30.0, gold=20.0)

kit.track(at=(0, 0, 0), length=8)
kit.ramp(at=(0, 8, 0), length=8, rise=2)
kit.track(at=(0, 16, 2), length=8)

kit.marker("start", at=(0, 2, 0))
kit.marker("gem", at=(0, 5, 0.3))
kit.marker("gem", at=(0, 12, 1.3))
kit.marker("gem", at=(0, 19, 2.3))
kit.marker("finish", at=(0, 22, 2))
kit.shot("overview", at=(12, -6, 10), rotation=(-30, 0, 40))
kit.shot("start", at=(0, -0.5, 1.2), rotation=(-25, 0, 0))
kit.shot("finish", at=(0, 17, 3.5), rotation=(-17, 0, 0))
# The fixture has no egg; this shot looks at the ramp from the side.
kit.shot("egg", at=(-12, 12, 5), rotation=(-15, 0, -90))

# Route bot (#14). The gems float out of reach, so the bot jumps 0.6 m before each one. The
# take-off speed sets the length of each jump; the last one must land before the end.
for kind, actions in (
    ("first_run", "0 speed 6; 0 jump; 1 speed 6; 1 jump; 2 speed 5; 2 jump"),
    ("expert", "0 speed 9; 0 jump; 1 speed 9; 1 jump; 2 speed 6; 2 jump"),
):
    kit.marker(
        "route",
        at=(0, 2, 0),
        points=[(0, 4.4, 0), (0, 11.4, 0.85), (0, 18.4, 2), (0, 22, 2)],
        name=f"route_{kind}",
        kind=kind,
        actions=actions,
    )
# CI probe: throwaway, do not merge
