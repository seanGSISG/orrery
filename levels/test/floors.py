"""Floor fixture for game/test/objects/trapdoor/ and game/test/objects/crumbling_tiles/: a
start track, a trapdoor, a short track, a strip of crumbling tiles and a finish track. Nothing
is under the loose floors, so a marble that falls goes out of bounds. The tests expect these
positions and settings."""

import kit

kit.level(title="Floor fixture", par=30.0, gold=15.0)

kit.track(at=(0, 0, 0), length=8)
kit.marker("start", at=(0, 2, 0))

# The door (4 x 4 m) fills the gap from y = 8 to 12, flush with both tracks.
kit.marker("trapdoor", at=(0, 10, 0), delay=0.5, close_after=4.0)
kit.track(at=(0, 12, 0), length=4)

# A strip of 2 x 4 tiles of 2 m from y = 16 to 24.
kit.marker("crumbling_tiles", at=(0, 20, 0), width=4.0, depth=8.0, tile=2.0, delay=0.6)

kit.track(at=(0, 24, 0), length=8)
kit.marker("finish", at=(0, 30, 0))

kit.shot("overview", at=(12, 2, 9), rotation=(-35, 0, 60))
kit.shot("trapdoor", at=(5, 4, 4), rotation=(-35, 0, 45))
kit.shot("tiles", at=(6, 14, 4), rotation=(-30, 0, 50))
