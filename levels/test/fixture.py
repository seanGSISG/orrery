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
