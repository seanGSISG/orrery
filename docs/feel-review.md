# Feel review (#19)

Play the feel-review course with the Xbox controller. Tune the marble, the camera and the input until they feel right. Then save the values and sign off in #19.

## Start

1. Connect the controller.
2. Run `just feel`. It builds the course (`levels/test/feel.py`) and opens it in a window.
3. Roll the loop once with the default values before you change a value.

## Controls

| Action | Controller | Keyboard |
|---|---|---|
| Roll | Left stick | W A S D |
| Turn the camera | Right stick | Mouse (click the window first) |
| Jump | A | Space |
| Restart from the start | View | R |
| Open or close the tuning overlay | Hold LB, then press Y | F1 |
| Select a value | D-pad up or down | Up or Down arrow |
| Change the value (hold to repeat) | D-pad left or right | Left or Right arrow |
| Save the changed values | RB | F5 |

The overlay shows the speed of the marble. A `*` after a value shows that the value is changed and not saved. The game continues while the overlay is open, so you can roll and tune at the same time. When the marble falls, it starts again at the last checkpoint.

## Stations

The loop goes counter-clockwise. A yellow sign shows the number and the name of each station.

| Station | Try this | Report this |
|---|---|---|
| 1 Flat | Roll from the start to full speed. Release the stick and count the stripes until the marble stops (one stripe is 5 m). Turn hard at full speed. | Time to full speed. Top speed. Braking distance. Grip in turns. |
| 2 Slope 10 | Roll up and down. Stop on the slope. | Does the marble climb easily? Does it hold still on the slope? |
| 3 Slope 20 | Same as station 2. | Same as station 2. |
| 4 Slope 30 | Same as station 2. Try to climb from a stop. | Can you climb it from a stop? Is the top too fast or too slow? |
| 5 Wall 90 | Roll into the wall straight on and at a shallow angle. Roll along it. | Bounce height. Does a shallow hit slide? Does the marble stick to the wall? |
| 6 Wall 60 | Roll into the face and up it. | Does it act like a wall or like a steep floor? |
| 7 Wall 45 | Roll up the face and onto the top. | Same as station 6. |
| 8 Thin wall | Stop against the wall. Turn the camera to the far side of the wall. | Can you see the marble? (camera case from #11) |
| 9 V seam | Roll along the bottom of the V. Stop in it. | Does the marble stick, shake or jump in the seam? |
| 10 Gaps | Jump the gaps of 1, 2, 3, 4 and 6 m. Steer in the air. Then jump the gaps of 8 and 10 m from full speed: roll 8 m or more from rest on the pad before the gap, and jump at the very edge. Roll the 1 m gap at walking speed and at full speed. | Which gaps are easy, which are hard? Jump height. Air control. Can you clear 8 m and 10 m, and is the edge timing fair? Does the 1 m gap launch the marble at full speed? |
| 11 Steps | Jump up the steps of 0.5, 0.8, 1.0 and 1.2 m. | Which steps can you jump up? Does a step stop the marble hard? |
| 12 Platform | Ride the moving platform. Roll on it while it moves. | Does the platform carry the marble well? Do you slide off when it stops? |
| 13 Gear | Ride the turning gear and roll off it. | Does the gear carry the marble? Is it easy to roll off? |
| 14 Bumpers | Roll into the bumpers slowly and at full speed. | Is the push too strong or too weak? Is the rumble correct? |

Notes on station 10:

- The marble needs about 7.4 m from rest to reach full speed (15 m/s). The pads before the 8 and 10 m gaps are 14 m long, and a checkpoint on each one starts the run-up from rest. A marble at full speed clears 11.25 m at most, so the 10 m gap leaves little room. A jump a little before the edge is better than a jump after it.
- The 1 m gap is too narrow to fall into at full speed. The marble hits the far corner (an edge hit), hops about 3 m and carries over the gaps of 2 and 3 m. At walking speed (stick pushed a little, 2 to 4 m/s) the marble falls in, so try both speeds.
- Every pad after the gaps of 6, 8 and 10 m is long enough to stop on (full brake takes 7.4 m).

Do these checks on all of the course:

- **Camera.** Is the distance correct? Is the camera too fast or too slow when it moves back after a wall? Does the camera shake too much on a hard landing?
- **Field of view.** The camera uses 75 degrees. `docs/design/visual-quality.md` uses 70. Try `fov` from 65 to 85 and save the best value.
- **Input.** Is the stick dead zone too large or too small? Is the camera turn speed correct? Is the rumble on a landing too strong?

## Save

1. Press RB (or F5). The overlay shows how many values it saved.
2. Save writes each changed value into the file that holds its default. It changes only the line of that value:
   - marble values: `game/core/marble_tuning.tres`
   - camera values: `game/core/camera/follow_camera.gd` (`fov` is the line `field_of_view`)
   - `dead_zone`: `game/core/input/input_hub.gd`
   - `look_sensitivity`, `invert_y`: `game/core/input/player_source.gd`
   - `rumble`: `game/core/input/rumble.gd`
3. Run `git diff` to see the changes. Commit them, or tell the agent to commit them.

## Report

Write one line for each problem in #19, with the station number. Examples:

- "Station 2 feels icy: the marble slides back when I stop. static_friction 1.1 → 1.3 fixed it."
- "Station 10: the 6 m gap is too easy at full speed."
- "Station 10: the 10 m gap is too hard. I need to jump before the edge."
- "fov 70 is better."

When the feel is correct, commit the saved values and write "Signed off" in #19.

## Limits

- The course has one surface type (`default`), because M1 has no other surface type yet.
- The overlay does not show `radius`, `mass` or the solver limits. They are not feel values.
- The overlay is in debug builds only. The release exports do not contain `game/debug/`.
