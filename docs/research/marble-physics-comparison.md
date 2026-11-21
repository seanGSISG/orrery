> **Research snapshot, 2026-11-21.** `docs/plan.md` records the decisions. Where this report and the plan differ, the plan wins.
> Orrery is an original game. This report uses the originals for numbers and behaviour only. No original file, level or code was copied into the repo. No tuning value was changed.

# Marble physics: Orrery against the Marble Blast games

Sean's four questions after the feel course: a brake, the speed curve, the gap sizes, and the 1 m gap. This report answers them from published constants and from measurements of our own solver.

## 0. Sources and method

Confidence marks used in every table:

- **[V]** read in a primary or near-primary source: the code of a re-implementation, or a quote of the original game files.
- **[S]** one secondary source (a community wiki, a guide, a forum post).
- **[D]** derived by me from [V] numbers with stated physics.
- **[M]** measured on our solver on 2026-11-21. Marble code and `marble_tuning.tres` were the same on `main` (4bfcd69) and on `plan-1` (e499c09). `kit/pieces.py` changed after the measurement.
- **[E]** my estimate. It can be wrong. The method is stated.

Sources checked:

| Source | What it gave | Date or revision |
|---|---|---|
| OpenMBU (C++ re-implementation of MBU; fan licence, numbers only) `marble.cs`, `marblephysics.cpp`, `marble.cpp`, `default.bind.cs` | MBU datablock, how input, braking, bounce and air control work, the key bindings | `3d6516e` |
| MBHaxe (MIT) `src/Marble.hx` | Same constants; MBU radius 0.3 | `14dac11` |
| Marble Blast Web (MIT) `src/ts/marble.ts` | Jump 7.3 "fits more than 7.5"; no braking field at all | `6deead0` |
| PlatinumQuest dev repo (MIT) `defaultProperties.cs` | MBP/PQ default and Mega marble constants | `2d1395c` |
| Forum post that quotes the `DefaultMarble` datablock from the Marble Blast Gold game files, https://forums.unrealengine.com/t/looking-for-help-building-my-3d-marble-game/97242 | MBG constants (the poster's copy; provenance not provable) [S] | read 2026-11-21 |
| Marble Blast Wiki (Fandom), through its MediaWiki API: Edge Hitting, Jumping, Speed Tricks, Diagonal Movement, Getting Gold Times on Beginner Levels, level pages | Edge hit behaviour, hop speed gain, no gap sizes | read 2026-11-21 |
| GameFAQs MBG guide by imikedaman, 2003-07-05, https://gamefaqs.gamespot.com/mac/922016-marble-blast-gold/faqs/31456 | Fast Start, edge stop trick | 2003 |
| `docs/research/gameplay.md` (2026-11-20) | Earlier numbers, Super Speed as a brake | local |

What I could not do or check:

- I did not read, extract or measure any original level. The originality rule forbids it. So **no gap width of an original level is documented here**. Section 4 gives bounds and an estimate, not data.
- Retail MBU is not available. Its numbers come from two re-implementations. They agree with each other on the constants, so I trust them at medium confidence.
- I did not check whether Marble It Up! has a brake. I did not find one in any source.
- Marble Blast Online, Xbox Gold and Mobile were not checked.

Our solver was measured through `LevelRun` with `MarbleInput`, at 120 Hz, in a throw-away GUT script that is not committed. The gap runs used the real `feel.glb` built from `levels/test/feel.py`.

## 1. How the original marble works, in plain words

These facts come from the OpenMBU physics code, read for behaviour only. [V] unless marked.

- Input sets a **target spin**: spin that rolls the marble at `maxRollVelocity` along the wished direction. The spin moves toward the target at `angularAcceleration` rad/s². On the ground, rolling turns spin into speed. So the linear acceleration is `angularAcceleration × radius`.
- With **no input** (stick centred), the target is zero spin. The spin moves to zero at `brakingAcceleration` rad/s². This is the only use of `brakingAcceleration` that I found. It applies only while the marble grips (no slip).
- With **opposite input**, the target is the full spin the other way. The spin moves at `angularAcceleration`, not at `brakingAcceleration`. So holding back slows the marble 2.5 times faster than letting go (75 against 30 rad/s²).
- Input never lowers a speed that is already above the wished speed on that axis.
- A hit bounces with `restitution = surface × bounceRestitution`. The surface value is 1.0 on normal floor, so the result is 0.5. A hit with closing speed below `maxDotSlide × speed` (0.5) slides instead of bouncing. Below `minBounceVel` (0.1) it does not bounce either.
- The jump sets the speed away from the best contact to `jumpImpulse`. It is a jump along the contact normal.
- In the air, input adds `airAccel` (5 m/s²) in the camera direction **with no speed cap**. Our `_steer` stops at the speed that input asks for on the ground. This is the main difference. See section 2.
- MBG modes do not normalise the input vector. Keyboard diagonal gives 1.41 times the speed (about 21 m/s). The MBU modes in OpenMBU normalise it. MBHaxe does not normalise. [V, sources differ for MBU]

## 2. Side-by-side table

Ours is `game/core/marble_tuning.tres` and `game/core/marble/marble.gd`. "MBU" is Marble Blast Ultra as re-implemented. "MBP/PQ" is Platinum and PlatinumQuest defaults. A level in PQ can override these values (physics modifiers), so these are defaults.

| Quantity | Orrery | MBG (2003) | MBU (2006) | MBP / PQ | Source and confidence |
|---|---|---|---|---|---|
| Radius | 0.2 m | 0.2 m | 0.3 m | 0.2 m | MBG: datablock quote [S]. MBU: OpenMBU scales the marble by 1.5, MBHaxe sets 0.3 [V]. PQ: `defaultProperties.cs` [V] |
| Gravity | 20 m/s² | 20 | 20 | 20 (Mega 22, Gyro x0.25) | Forum quote [S]; OpenMBU, PQ [V] |
| Max roll speed | 15 m/s | 15 | 15 | 15 (Mega 12) | Same sources [V]. Ours measured 15.00 [M] |
| Angular accel | 75 rad/s² | 75 | 75 | 75 (Mega 60) | Same [V] |
| Linear accel on flat ground | 15 m/s² | 15 | 22.5 | 15 | `angularAcceleration × radius` [D] |
| Time 0 to top speed | 0.99 s (99% of top) | 1.0 s | 0.67 s | 1.0 s | Ours [M]. Others [D]: top spin = 15 / r, reached at 75 rad/s² |
| Distance to top speed | 7.4 m | 7.5 m | 5.0 m | 7.5 m | Ours [M]; others [D] |
| Speed curve | Straight line: 3.75, 7.5, 11.25, 15.0 m/s at 0.25, 0.5, 0.75, 1.0 s | Straight line | Straight line | Straight line | Ours [M]. Others [D]: the spin rate is capped, so the line is straight until the cap |
| Braking, stick released | 30 rad/s² = 6 m/s²; stops from 15 m/s in 2.49 s over 18.6 m | Same rate; 2.5 s, 18.75 m | 30 rad/s² = 9 m/s²; 1.67 s, 12.5 m | Same as MBG (Mega 25) | Ours [M]. Others [D] from `brakingAcceleration = 30` [V/S] |
| Braking, stick held back | Stops in 1.00 s over 7.4 m, then rolls back | Same law; 1.0 s, 7.5 m | 0.67 s, 5 m | Same as MBG | Ours [M]. Others [D] |
| Brake button | None | None found | None found | None found | No brake action in OpenMBU bindings [V]; PQ has only the datablock field [V]; the Web port has no braking field in `src/ts` [V]. Not checked in Marble It Up! |
| Jump impulse | 7.5 m/s | 7.5 | 7.5 | 7.5 | [V/S]. The Web port uses 7.3 because it "fits more" [V]. So the retail value may play slightly lower. Medium confidence |
| Jump apex (centre rise, flat, from rest) | 1.44 m (7.2 radii) | 1.41 m [D] (7 radii) | 1.41 m (4.7 radii) | 1.41 m | Ours [M]. Others [D]: `v² / 2g`. At 7.3 the rise is 1.33 m |
| Jump flight time | 0.76 s | 0.75 s [D] | 0.75 s | 0.75 s | Ours [M] |
| Air control | 5 m/s², capped at the ground wish speed | 5 m/s², no cap | 5 m/s², no cap | 5 m/s², Gyro x2 | Ours from code, measured +3.9 m/s in one hop from rest [M]. Others [V] |
| Hop speed gain | None by design (`test_hopping_does_not_gain_speed`) | Yes, "jumping whenever you can will make the marble go faster on each jump" | Yes (same air rule) | Yes | Ours [M]. MBG: Fandom Speed Tricks and the 2003 GameFAQs guide ("Fast Start") [S]; the code rule [V] |
| Diagonal keyboard speed | 15 m/s (input is clamped to length 1) | about 21.2 m/s | 15 m/s in OpenMBU (normalised) | MBHaxe: about 21.2; OpenMBU MBU mode: 15 | Code [V]; Fandom says diagonal movement "gains extra speed" [S]. MBU sources differ |
| Restitution | 0.5 | 0.5 | 0.5 | 0.5 (Super Bounce 0.9) | [V/S]. Rebound from a 2 m drop: ours 0.49 m [M]; the original law gives 0.5 m [D] |
| Rebound height from other drops | 0.5 m drop gives 0.12 m; 1 m gives 0.24 m; 5 m gives 1.22 m | 0.25 of the drop | same | same | Ours [M]; others [D] (height scales with restitution squared) |
| Slide rule | glancing hit slides when closing speed is below 0.5 of speed | `maxDotSlide` 0.5 | 0.5 | 0.5 (Mega 0.3) | [V/S] |
| Friction static / kinetic / bounce | 1.1 / 0.7 / 0.2 | same | same | same | [V/S] |
| Largest gap cleared by a jump from top speed, flat to flat | 11.25 m clean; 11.75 m with an edge hit | about 12.7 m | about 12.7 m | about 12.7 m | Ours [M]. Others [D]: `v × T + 0.5 × 5 × T²` with `T = 0.75 s`, because the air push is uncapped |
| Same, at keyboard-diagonal speed | 16.0 m, if the marble had 21.2 m/s (ours clamps input, so it cannot reach it without a boost) | about 17.3 m | not reachable on normalised input | about 17.3 m (MBHaxe rule) | Ours [M] with a teleported speed. Others [D] |
| Widest gap rolled over without a jump at 15 m/s | 1.7 m, only through an edge hit | similar | similar | similar | Ours [M]. Others [E] |

Reading the table:

- **Everything on the ground matches MBG and PQ.** Top speed, acceleration, braking, jump, gravity, restitution, friction and the slide rule are the same numbers. The 0.99 s is the time to 99% of top speed. Ours reads 15.00 m/s at 1.00 s.
- **Two real differences from the MBG family.** (a) Our air control stops at the ground wish speed, so a hop at top speed gains nothing. The originals add speed in the air and keep it on landing. (b) We clamp diagonal input to length 1. MBG keyboard play does not.
- **MBU is livelier on the ground.** The same spin rates on a 0.3 m ball give 22.5 m/s² of acceleration and 0.67 s to top speed. We copied the 0.2 m family, not MBU.

## 3. Answers

### Q1. Was there a hard brake button?

**No.** I found no brake action in any original or re-implementation.

- OpenMBU's key bindings have roll, camera, jump, use and blast. No brake. PQ's constants file has `BrakingAcceleration` only as a datablock field. The Web port has no braking field in `src/ts`. [V]
- `brakingAcceleration` (30 rad/s²) is the rate at which the spin goes to zero **when no direction is held**. It is 6 m/s² at r = 0.2. That is the slow stop: 2.5 s and 18.75 m from top speed.
- The fast stop in the originals is the **opposite direction**: spin goes to the reverse target at the full 75 rad/s², which is 15 m/s² and about 1 s and 7.5 m. Players then let go at about zero speed. A tip in a 2003 MBG guide says to come "to an almost complete stop" at an edge and hold the opposite direction as you roll off. [S]
- Super Speed fired backward also works as a brake (earlier research, `gameplay.md` §3). [V]

Ours matches: release stops in 2.49 s over 18.6 m, hold-back in 1.00 s over 7.4 m. [M]

### Q2. Same top speed, same time, same curve?

**Yes, for MBG, MBP and PQ.** Ours reaches 15.00 m/s in 0.99 s after 7.4 m, on a straight line (3.75 m/s per quarter second). MBG and PQ give 1.0 s and 7.5 m by the spin-rate cap. [M, D]

- **MBU is faster off the line:** 0.67 s and 5 m, because the ball is 0.3 m. [D, medium confidence]
- **Jump:** same impulse. Ours rises 1.44 m (7.2 radii) in 0.76 s. The originals give 1.41 m. The Web port's 7.3 gives 1.33 m, so retail may be 5 to 8% lower than ours. [M, D]
- **Gravity, restitution, friction:** the same numbers.
- **Air control:** same 5 m/s² but **ours is capped**. In the originals a full-forward hop adds up to 3.75 m/s per hop and keeps it. Ours adds nothing at top speed. This is the one behaviour difference that a player could feel. It is a recorded design rule, so it is a choice and not a bug. [V code, M]

### Q3. Are our gaps (1, 2, 3, 4, 6 m) typical? What is the largest clear?

**Documented gap widths for the originals' Beginner and Intermediate levels: none found.** The wiki pages give no distances. The only way to measure them is to read the level files, which the originality rule forbids. I give bounds and an estimate.

What the physics fixes (the same numbers in all of them, so these bounds apply to the originals too):

| Run-up before the jump | Speed [D, M] | Jump distance (centre travel in the air) |
|---|---|---|
| Standing | 0 | 1.5 m (with air control) |
| 1 m | 5.5 m/s | 4.2 m |
| 2 m | 7.7 m/s | 5.9 m |
| 3 m | 9.5 m/s | 7.2 m |
| 5 m | 12.2 m/s | 9.3 m |
| 7.5 m or more | 15 m/s | 11.4 m |

(Speed from `v = sqrt(2 × 15 × run-up)`; distance = speed × 0.758 s.) A 6 m gap needs about 8 m/s, which is a 2.1 m run-up. [D]

- **Estimate [E, low confidence]:** a Beginner gap is a "learn the jump" gap, so it should be easy from a short run-up: about 2 to 5 m. An Intermediate level that wants speed would use 6 to 10 m. Our 1 to 6 m set is in the right range for Beginner. The 6 m gap is the first one that needs a run-up. We have nothing between 6 m and the 11 m limit, so the feel course does not test the speed-critical jumps. The Fandom page for Jumping says big gaps are crossed "if used with Diagonal Movement", which fits the 16 to 17 m MBG keyboard reach. [S]
- **Largest clear from top speed.** Ours: 11.25 m with a clean landing, jumping at the very edge. 11.75 m survives only through an edge hit. [M] MBG, MBP and PQ at 15 m/s: about 12.7 m. MBG keyboard-diagonal at 21.2 m/s: about 17.3 m. MBU: about 12.7 m. [D]
- **Gaps under about 0.8 m** can be rolled over: the hop is under 0.8 m. Gaps from 0.9 to about 1.9 m cannot be rolled over cleanly. See Q4.

### Q4. Is the 1 m gap result what the physics predicts? Would the originals do the same?

**Yes to the first part. The hop is bigger than "a bit".**

- Sean's formula gives the drop over the gap: `g w² / 2v² = 20 × 1 / (2 × 225) = 4.4 cm`. Right, and small. But the drop is not the point. The marble is a sphere. It hits the far **corner** when its centre is still 0.11 m before the edge and has dropped 3.5 cm. At that point the normal points back and up (34° from vertical). The closing speed along it is 8.5 m/s. That is above the slide limit (0.5 × 15 = 7.5 m/s), so the hit **bounces**. With restitution 0.5 the normal speed change is 1.5 × 8.5 = 12.7 m/s. That takes 7.3 m/s off the forward speed and adds 10.5 m/s upward. [D]
- **Measured on the real `feel.glb`, holding forward from the gap-section checkpoint** (9 m run-up, 15 m/s at the edge): forward speed 15.0 to 7.65 m/s, upward speed 0 to 11.06 m/s. The marble rises about **3 m** (to 3.2 m centre height) and flies 1.1 s. [M]
- **What happens next:** the hop carries the marble over the 2 m gap and the 3 m gap too. It lands on pad 3 (and bounces up again at 5.4 m/s), then lands on pad 4. At full speed it then rolls into the 4 m gap and falls. So "it makes it" is true for gap 1, but gaps 2 and 3 were passed by accident. [M]
- **Gap width against hop (from 15 m/s):** 0.5 m gives a 0.34 m rise; 0.8 m gives 0.78 m; 0.9 m gives 2.4 m; 1.0 m gives 2.8 m (3.0 m on the real course); 1.2 m gives 3.3 m; 1.5 m gives 3.4 m; 1.9 m falls in. The jump from 0.8 to 0.9 m is the point where the corner hit becomes a bounce. [M]
- **Would the originals do the same?** In kind, yes. The numbers (restitution 0.5, slide limit 0.5, sharp polygon corners) are the same, and the community has a name for it: an **edge hit**. "To perform an edge hit, roll towards a gap at high speed. When the marble hits the edge at the end of the gap, it will accelerate upwards." Speedrunners use it as a shortcut in Beginner levels. [S, Fandom Edge Hitting] In **size**, I cannot confirm it. The original solver steps at 8 ms, which is 12 cm of travel at 15 m/s. It may find the corner contact at a different depth and so a different normal. The hop height in retail is unverified. [E]

If you saw a small bounce and not a 3 m hop, check the run: the hop is at the first edge and the camera may have been looking along the lane.

## 4. Recommendations

| # | Recommendation | Confidence |
|---|---|---|
| 1 | **Keep** `max_roll_speed` 15, `angular_acceleration` 75, `gravity` 20, `jump_impulse` 7.5, `restitution` 0.5, friction values and `slide_threshold` 0.5. They equal the MBG/PQ numbers. Sean played the course and said it feels great. | High |
| 2 | **Keep** `braking_acceleration` 30 for now. It is the original's value. The measured stop (2.49 s, 18.6 m) is the original's too. | High |
| 3 | **Do not add a brake before the M1 checkpoint.** No original has one, and holding back already stops in 1.0 s. A button adds a field to `MarbleInput` and to every input source (player, bot, harness). | Medium |
| 4 | **If Sean wants a brake as an original feature** ("grip" while held), build it inside `_roll`: spin target zero at a higher rate **and** more friction while the button is held, with a skid sound and dust. A higher rate alone **does not work**: I tried 120 rad/s² on the current friction (static 1.1) and the marble stopped **slower** than with 75 (2.17 s, against 0.99 s), because the contact slips. With friction doubled the numbers are good: 120 rad/s² stops in 0.62 s over 4.5 m; 150 rad/s² in 0.49 s over 3.6 m. [M, scratch tuning copy, not saved] The theoretical limit on current friction is `static_friction × gravity` = 22 m/s², so 0.68 s over 5.1 m. [D] A brake should not work in the air, and a held brake on a slope should hold the marble (so it must stay inside the friction limit). | Medium |
| 5 | **Simpler alternative to a button** (Sean's rule: a fix should shrink the system): remove `braking_acceleration` and use `angular_acceleration` for release too. Releasing then stops in 1.0 s over 7.5 m. This deletes a value, but it also removes the slow "coast" that the originals have. It is a feel change, so it needs a feel review. | Low |
| 6 | **Decide the air-control rule on purpose.** The originals let hops add speed ("Fast Start", chained jumps) and that is part of their speedrun culture. Ours does not. Keep ours if Orrery should not reward hop chains. If Sean wants the original skill ceiling, remove the cap in `_steer` and keep the "never slow below current speed" rule. This also adds about 1.4 m to the longest jump. Do not change it without a decision. | Medium |
| 7 | **Add gaps to the feel course** between 6 and 11 m, and one at 8 m with a short run-up, to test speed-critical jumps. Add a note to `docs/feel-review.md` that the 1 m gap is an edge-hit launcher at full speed. For Beginner levels, consider a ramp or a lip on gap edges, or tell the designer to avoid gaps of 0.9 to 1.9 m at a run-up over 5 m. These are level-design rules, not tuning. | Medium |
| 8 | **Do not copy MBU's livelier start.** If Sean wants a quicker start, the lever is `angular_acceleration` (100 rad/s² gives 0.75 s). Not now. | Low |
| 9 | **Retail jump height:** the Web port prefers 7.3. If a later feel review says jumps are a little high, try 7.3 first. | Low |

## 5. Facts and estimates, kept apart

Facts with sources: the constants in section 2 marked [V] or [S]; the input, braking and bounce rules in section 1; the Fandom Edge Hitting and Speed Tricks text; the absence of a brake binding.

Measured by us ([M]): the roll curve, the stops, the jump, the air gain, the drops, the 1 m gap run on `feel.glb`, the gap-width hop table, the largest clear jump (jump point scanned in 5 cm steps), the brake rates.

Derived ([D]): everything on a MBG, MBU or PQ row that is not a quote. The method is `v = ω r`, `a = α r`, `T = 2 × 7.5 / 20`, and the corner-hit geometry.

Estimates ([E]): typical gap widths of the originals, retail MBU behaviour, and the original hop height at an edge.

Open points:

- MBU numbers come from re-implementations.
- MBHaxe and OpenMBU disagree on input normalising in MBU.
- No original gap width is documented, and none can be measured under the originality rule.
- The Web port's 7.3 jump is unexplained.
