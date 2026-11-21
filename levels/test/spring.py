"""Coil Spring fixture (#17) for game/test/objects/coil_spring/test_coil_spring.gd: two Coil
Springs in front of the start pad, and a ledge 5 m above the floor that a jump cannot reach.
Take a spring, roll forward and press use: the marble rises 10 m and lands on the ledge. The
test expects these positions and settings."""

import kit

kit.level(title="Coil Spring fixture", par=20.0, gold=10.0)

kit.track(at=(0, 0, 0), width=8, length=24)
kit.marker("start", at=(0, 2, 0))
kit.marker("coil_spring", at=(-1.5, 6, 0))
kit.marker("coil_spring", at=(1.5, 6, 0), launch_speed=18.0, respawn_delay=3.0)

# The ledge hangs over the far end of the floor, with its top 5 m up.
kit.track(at=(0, 14, 5), width=8, length=10)
kit.marker("checkpoint", at=(0, 16, 5))
kit.marker("finish", at=(0, 21, 5))

kit.shot("overview", at=(16, -6, 10), rotation=(-25, 0, 55))
kit.shot("springs", at=(0, 3.2, 1.0), rotation=(-6, 0, 0))
kit.shot("ledge", at=(10, 4, 4), rotation=(-5, 0, 60))
