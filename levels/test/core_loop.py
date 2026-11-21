"""Core loop fixture (#13): a start, four gems (one of each cut), a checkpoint at the top of a
ramp, the Clockwork Egg on a side floor, and the finish. Play it through the harness to see
the gems, the egg and the finish; the shots frame each one."""

import kit

kit.level(title="Core loop fixture", par=30.0, gold=15.0)

kit.track(at=(0, 0, 0), width=8, length=12)
kit.ramp(at=(0, 12, 0), width=8, length=8, rise=2)
kit.track(at=(0, 20, 2), width=8, length=14)
kit.track(at=(8, 24, 2), width=8, length=8)

kit.marker("start", at=(0, 2, 0))
kit.marker("gem", at=(-2, 6, 0), cut=0)
kit.marker("gem", at=(2, 9, 0), cut=1)
kit.marker("gem", at=(-2, 26, 2), cut=2)
kit.marker("gem", at=(2, 29, 2), cut=3)
kit.marker("checkpoint", at=(0, 22, 2))
kit.marker("egg", at=(10, 28, 2))
kit.marker("finish", at=(0, 32, 2))

# Route bot (#14). First run: every gem in order, a look round at the checkpoint and the egg on
# the side floor. Expert: the gems only, on a smoother line.
kit.marker(
    "route",
    at=(0, 2, 0),
    points=[
        (-2, 6, 0),
        (2, 9, 0),
        (0, 16, 1),
        (0, 22, 2),
        (10, 28, 2),
        (2, 29, 2),
        (-2, 26, 2),
        (0, 32, 2),
    ],
    name="route_first_run",
    kind="first_run",
    actions="3 wait 0.5",
)
kit.marker(
    "route",
    at=(0, 2, 0),
    points=[(-2, 6, 0), (2, 9, 0), (0, 16, 1), (-2, 26, 2), (2, 29, 2), (0, 32, 2)],
    name="route_expert",
    kind="expert",
)

kit.shot("overview", at=(14, -8, 12), rotation=(-32, 0, 35))
kit.shot("gems", at=(0, -2, 1.5), rotation=(-4, 0, 0))
kit.shot("egg", at=(10, 25.5, 2.8), rotation=(-12, 0, 0))
kit.shot("finish", at=(0, 27, 3.5), rotation=(-18, 0, 0))
