> **Research snapshot, 2026-11-20.** `docs/plan.md` records the decisions. Where this report and the plan differ, the plan wins.
> No code from the reference projects may be copied into Orrery. OpenMBU in particular is licensed for non-profit fan use only. Use the documented numbers and behaviour as a starting point only.

# Marble-platformer design reference (Marble Blast series and genre)

Purpose: mechanics, numbers, and design lessons for an ORIGINAL marble platformer. Do not copy names, levels, art, music, or code.
Research date: 2026-11-20. Confidence tags: [V] verified in primary source (code/data/official page), [S] single secondary source, [D] derived by me from verified numbers, [?] unverified or conflicting.

## 0. Source key

Source code read locally (shallow clones, SHAs at time of reading):
- OpenMBU (C++ Torque, MBU revival), `3d6516e`: https://github.com/MBU-Team/OpenMBU . License is a "Fan Revival License, not for profit" (NOT MIT). Do not copy code.
  - `game/marble/server/scripts/marble.cs` (marble datablock), `powerUps.cs` (power-up table), `engine/source/game/marble/marblephysics.cpp`, `marble.cpp`, `game/marble/client/scripts/default.bind.cs` (bindings).
- Marble Blast Web (Vanilagy, TypeScript, MIT), `6deead0`: https://github.com/Vanilagy/MarbleBlast . Files: `src/ts/marble.ts`, `level.ts`, `shapes/*.ts`, `physics/*.ts`, `interior.ts`, `storage.ts`, `README.md`, `version_history.md`. Also bundles the original MBG `.mis` mission files in `src/assets/data/missions` (I counted them).
- MBHaxe (RandomityGuy, Haxe, MIT), `14dac11`: https://github.com/RandomityGuy/MBHaxe . Files: `src/Marble.hx`, `AGENTS.md`, `README.md`.
- PlatinumQuest dev repo (TorqueScript, MIT), `2d1395c`: https://github.com/The-New-Platinum-Team/PlatinumQuest-Dev . File: `Marble Blast Platinum/platinum/shared/defaultProperties.cs`.
- DeepWiki was not needed: raw source was available and more exact.

Web sources:
- Wikipedia: https://en.wikipedia.org/wiki/Marble_Blast , https://en.wikipedia.org/wiki/Marble_Blast_Ultra , https://en.wikipedia.org/wiki/Marble_It_Up!_Ultra , https://en.wikipedia.org/wiki/Super_Monkey_Ball_(video_game) , https://en.wikipedia.org/wiki/Marble_Madness , https://en.wikipedia.org/wiki/Hamsterball
- Marble Blast Wiki (Fandom), read through its MediaWiki API (`https://marbleblast.fandom.com/api.php?action=parse&prop=wikitext&page=...`): pages Level, PowerUp, Super Jump, Super Speed, Super Bounce, Shock Absorber, Gyrocopter, Gravity Modifier, Time Travel, Mega Marble, Random PowerUp, Mine, Nuke, Bumper, Duct Fan, Tornado, Trap Door, Oil Slick, Moving Platform, Bouncy Floor, Teleporter, Checkpoint, Out of Bounds, Qualify Time, Gold Time, Silver Time, Ultimate Time, Easter Egg, Gem, Multiplayer, Leaderboards, Marble Blast (XBOX), Marble Blast Platinum, PlatinumQuest, Marble It Up!, Wall Hitting, Edge Hitting, Traplaunching, Speed Tricks, Diagonal Movement, Marble Blast Gold/Ultra level-list pages. Base URL: https://marbleblast.fandom.com/wiki/<Page>. Fandom is community-written: treat as [S].
- Ben Garney, "Marbling It Up" (2018-09-01): https://bengarney.com/2018/09/01/marbling-it-up
- Marble It Up! posts/FAQ: https://marbleitup.com/2019/11/08/1698 , https://marbleitup.com/frequently-asked-questions , https://www.marbleitup.com/
- Steam page (MIU Ultra): https://store.steampowered.com/app/864060/Marble_It_Up/
- Reviews: GameSpot MBU (Gerstmann, 2006-01-27) https://www.gamespot.com/reviews/marble-blast-ultra-review/1900-6143253/ ; GamesRadar MBU https://gamesradar.com/marble-blast-ultra-xbox-live-arcade-review ; HonestGamers MBU https://www.honestgamers.com/4852/xbox-360/marble-blast-ultra/review.html ; NWR MIU (2018) https://www.nintendoworldreport.com/review/48530/marble-it-up-switch-review ; NWR MIU Ultra (2023-08-15, 8.5) https://www.nintendoworldreport.com/review/64582/marble-it-up-ultra-switch-review ; Nintendo Life MIU Ultra https://www.nintendolife.com/reviews/switch-eshop/marble-it-up-ultra ; Gaming Trend MIU https://gamingtrend.com/reviews/hold-onto-your-marbles-marble-it-up-review/ ; Nintendo Life announcement (2018) https://www.nintendolife.com/news/2018/08/marble_it_up_wants_to_be_the_roll-playing_game_of_the_year_on_switch ; VICE opinion piece https://www.vice.com/en/article/the-greatest-xbox-360-game-has-a-spiritual-successor-and-im-upset-nobody-told-me/
- MBU achievements: https://www.trueachievements.com/game/Marble-Blast-Ultra/achievements

Could not fetch (403/blocked or empty): GameSpot/IGN/Eurogamer pages by direct fetch (GameSpot read through Parallel fetch only), Hardcore Gaming 101 MIU article, marbleblast.fandom.com HTML pages (API worked), the NWR 2018 "Marble Madness to the Modern Era" feature (only seen as a search excerpt, URL not confirmed).

---

## 1. Series timeline and scope

| Game | Date / platform | Levels | Notes |
|---|---|---|---|
| Marble Blast | 2002-12-13, PC (Torque engine); Mac/Linux weeks later; retail as "Marble Blaster" 2003-06-24 | n/a | GarageGames + Monster Studios. Inspired by Marble Madness. Started as a multiplayer racer ("Marble Reaction"); MP cut early. [S] Wikipedia Marble Blast |
| Marble Blast Gold (MBG) | 2003-05-09, PC/Mac/Linux | 100 = 24 Beginner, 24 Intermediate, 52 Advanced | Adds Gold Times. I counted 24/24/52 `.mis` files in the Web port's bundled MBG data [V]. Wikipedia date 2003-05-09; other sites disagree (April/June) [?] |
| MBG Xbox (XBLA) | 2005-05-10 | 94 | No tiers: numeric difficulty 1-11 with ski icons. All levels have a qualify time. Online leaderboards, score formula, 12 Easter Eggs. [S] Fandom "Marble Blast (XBOX)" |
| Marble Blast XP (Net Jet) | ~2005-06 | n/a | Adds checkpoints, Silver Times, selectable marbles. [S] |
| Marble Blast Ultra (MBU) | 2006-01-25 (Metacritic says 01-23), Xbox 360 XBLA; delisted Feb 2011 | 60 SP = 20 Beginner / 20 Intermediate / 20 Advanced; 20 MP levels | 756,178 units by Jan 2011. [S] Wikipedia. Many levels recycled from MBG |
| Marble Blast Platinum (MBP) | beta 2007-05, final 2007-12; 1.14 (2009) added online leaderboards + achievements; 1.50 (2013-14) added MP + all 60 MBU levels | 120 official = 25 Beginner, 35 Intermediate, 35 Advanced, 25 Expert | Fan mod of MBG by Matan and "Platinum Team". [S] Fandom MBP |
| PlatinumQuest (PQ) | 2017-07-06, standalone (MBP 2.0.0) | ~138 new levels [S, search snippet]; tutorial + Beginner/Intermediate/Advanced/Expert + Bonus | 9 level modes (Normal, Gem Collection, Gem Hunt, Gem Madness, Gem Quota, Lap, 2D, Consistency, Haste). Fandom PlatinumQuest |
| Marble It Up! (MIU) | Switch 2018-09 (Wikipedia) ; Fandom says 2018-11-16 [?]; Unity 2017 | 40 levels in 4 chapters (up to 11 per chapter) | Team: Mark Frohnmayer, Ben Garney, Alex Swanson (original MB level designer), Matan and Conor (community speedrunners), Solovox (music). Self-funded. |
| Marble It Up: Mayhem! | Apple Arcade, 2019-11-08; partnership ended 2024-08-29 | remixed campaign | Added multiplayer (Gem Hunt, Steal the Crown, etc.) [V] marbleitup.com |
| Marble It Up! Ultra | 2023-08-17 (official post); Switch/PS4/PS5/Xbox/Steam/Epic | "more than 100 levels": 6 primary + 4 bonus chapters (NWR says 60+ in the 6 numbered chapters) | 5 cross-platform MP modes; Metacritic PS5 76, Xbox Series 88 [S]; Steam 93% positive of 1,069 reviews (2026-11 snapshot); Workshop with 200+ levels |
| Unofficial ports/revivals | OpenMBU (MBU), Marble Blast Web, MBHaxe (MBG/MBP/MBU/PQ on Win/Mac/Linux/Web/iOS/Android/Xbox) | — | Marble Blast Web: ~220 original levels + 3,900 community levels (README) [V] |

Date conflicts: Wikipedia MBU article says MIU Ultra "July 2023"; the Wikipedia MIU Ultra infobox and the official post say 2023-08-17. Use 2023-08-17.

---

## 2. Core loop and objectives

Loop: start pad -> "Ready, Set, Go" -> roll, jump, collect, avoid hazards -> reach finish pad (after collecting all gems, if the level has any) -> compare time -> retry for better time.

Facts:
- Start: marble is held above the start pad for 3,500 ms (`GO_TIME = 3500` in Web `level.ts`); XY velocity is zeroed and friction is 0 during the countdown [V]. Timer starts at "Go". Fast-start trick: jump so you land right after "Go" (Fandom Speed Tricks) [S].
- Finish: end pad accepts marble slightly above the pad; touching it without all gems shows a "collect remaining gems" message [S Fandom End Pad/Gem].
- Gems: required to finish when present. In my census of the 100 MBG levels, 42 of 100 levels contain gems (14 of 24 Intermediate; 5 of 24 Beginner; 23 of 52 Advanced), median 4-6.5 gems per gem level, max 18 [D, from `.mis` count of `GemItem`]. MBU/MBP SP use red gems only; MP uses red/yellow/blue = 1/2/5 points. [V Fandom + Wikipedia]
- Time targets, per game:
  - Qualify (MBG; called "Par" in MBP/MBU): finish under it to unlock the next level; otherwise your time is saved but the next level stays locked. In MBG only 22 of 100 levels have a nonzero qualify time (1 Beginner, 8 Intermediate, 13 Advanced; median 57 s and 60 s) [D, from `time` in MissionInfo]. So most MBG levels unlock by just finishing. Xbox Gold: all levels have a qualify time. MBP shows an alarm when qualify time is about to run out.
  - Gold Time (MBG): optional bonus, unlocks nothing. In MBG data: median 5.5 s (Beginner), ~20 s (Intermediate), 30 s (Advanced); where both exist, gold/qualify median ratio is 0.33 (Intermediate) and 0.60 (Beginner/Advanced) [D]. Gold usually needs hidden power-ups or shortcuts (Wikipedia).
  - Silver Time (Marble Blast XP): easier tier below Gold [S].
  - Platinum Time = Gold equivalent; Ultimate Time (MBP, MBU levels in MBP 1.50+): "much more difficult", needs edge hits, wall hits, trap launches. Achievement "Legendary Marbler" = Ultimate on all 120 MBP levels. PQ adds Awesome Time for Gem Madness. [S Fandom]
  - MBU: Par time per level; achievements for all Beginner / Intermediate / Advanced under par. [V TrueAchievements]
  - MIU: bronze / silver / gold / diamond medals; medals unlock marble skins and bonus chapters. [V Gaming Trend, NWR]
  - Xbox MBG score (nice example of a skill-scaled score): `score = (1000 + 1000 * GoldTime / FinalTime) * difficultyRating`, times 3 if under Gold Time. [S Fandom]
- Out of bounds: leaving an "In Bounds" trigger volume (or entering an "Out of Bounds" trigger) starts OOB. Camera locks, text shown, marble respawns after 2,000 ms (`schedule(... + 2000, restart)` in Web `level.ts`). Restart goes to last checkpoint if any, else start pad. In MBG with no checkpoint, the clock restarts [S Fandom OOB].
- Checkpoints (MBXP, MBP, PQ; not in MBG): store gems collected, held power-up, gravity "up" vector and blast charge (Web `level.ts` fields `checkpointCollectedGems`, `checkpointHeldPowerUp`, `checkpointUp`, `checkpointBlast`). Respawning at a checkpoint does not reset the timer. A separate "respawn" key (R) returns you to checkpoint; holding restart ~1 s forces a full restart (Web `level.ts`) [V].
- Level unlocking: previous level in same tier must be qualified (MBG, MBU). PQ unlocks some levels by finishing specific tutorial levels. [S]
- Easter eggs: MBU hides 20 eggs (in 20 of 60 levels; achievements "Egg Seeker" for 1, "Egg Basket" for all 20) [S Wikipedia]. Xbox MBG: 12. [S Fandom]
- Level progression teaches by mechanic: MBG Beginner list is almost one tutorial per mechanic, in this order: rolling, gems, jumping, Super Jump, moving platforms, Super Speed, elevators, air movement, Gyrocopter, Time Travel, Super Bounce, Gravity Modifier, Shock Absorber, a "there and back" gem level, surfaces (mud/grass/space), bumpers, fans, mines, trapdoors, tornado... [V Fandom Gold Beginner list; matches `.mis` startHelpText in Web assets]

---

## 3. Power-ups (all values are from code unless marked)

Held vs instant: Super Jump, Super Speed, Super Bounce, Shock Absorber, Gyrocopter, Mega Marble are stored in a single power-up slot (one slot; picking a new one overrides the old one; picking the same one again is refused) and fired by the "use" button. Time Travel, Gravity Modifier and Blast pickups act instantly (autoUse). Slot is locked while OOB. [S Fandom PowerUp; V Web `power_up.ts` autoUse flags]

| Power-up (MBP/PQ names) | Effect | Numbers |
|---|---|---|
| Super Jump (Jump Boost) | Adds upward velocity along "up" | `+20 m/s` (OpenMBU `boostAmount[1]=20`, `boostMassless 0.7`; Web: `+20`). Stacks with normal jump (jump impulse 7.5). [V] |
| Super Speed (Speed Booster) | Adds speed along camera-forward projected onto last contact surface | `+25 m/s` (OpenMBU `boostAmount[2]=25`; Web uses 24.7 "tuned"; PQ `SuperSpeedVelocity=25`). Direction = camera direction rotated onto last-touched surface normal; also usable as a brake when fired backward. [V] |
| Super Bounce (Marble Recoil) | Raises restitution to 0.9 for a duration | `restitution 0.9`, `5000 ms` (PQ `PowerUpTime3=5000`, Web 5000). Fandom page says 6 s [?: code wins]. Commented out ("currently unused") in OpenMBU's MBU table; Fandom says it is absent from MBU [S]. |
| Shock Absorber (Anti-Recoil) | Near-zero restitution, plus a small velocity boost on contact from spin | `restitution 0.01`, `5000 ms` (PQ `ShockAbsorberRestitution = 0.01`). Lets you land on slopes without bouncing and climb small steps. Absent in MBU [S]. |
| Gyrocopter (Helicopter) | Gravity x0.25 and air acceleration x2 | `5000 ms`; PQ `HelicopterGravityMultiplier=0.25`, `AirAccelerationMultiplier=2`; OpenMBU `gravityMod[5]=0.25`, `airAccel[5]=2`, `duration 5000` [V] |
| Gravity Modifier (Gravity Defier) | Rotates the "up" vector to the arrow direction; camera rotates; instant on pickup | Not pickup-able if already facing that way (Web `anti_gravity.ts`). Camera rotates smoothly in MBU, snaps in MBG [S]. Turns red when out of range. |
| Time Travel (Time Modifier) | Adds bonus time: freezes the displayed clock for the bonus | `+5 s` default (per-pickup override, positive or negative); does NOT respawn (Web `cooldownDuration = Infinity`). Affects Final Time only; elapsed time still runs [V]. In MIU it is replaced by a time-slow pickup [S: Gaming Trend, Nintendo Life]. |
| Mega Marble (MBP, MBU, PQ) | Bigger, heavier marble; shoves other marbles | OpenMBU: `10000 ms`, `sizeScale 2.25`, `massScale 5`, `boostAmount 5` (small hop). Web: radius `0.6666`, +6 m/s up, lasts 10 s. PQ has separate Mega physics set: maxRoll 12, angAccel 60, braking 25, gravity 22, kinetic friction 0.8, maxDotSlide 0.3 [V] |
| Blast / Ultra Blast (MBU, MBP, PQ) | Blast is a self-recharging meter: press to hop up and shove nearby marbles. Ultra Blast pickup fills the meter beyond the natural cap | See section 5 [V] |
| Random PowerUp (MBP) | Picks one of Super Jump / Speed / Gyro / Bounce / Shock / Time at pickup | Web `random_power_up.ts`; loops until it finds one the marble can take [V] |
| PQ-only | Bubble (underwater float up), Anvil (shoots you down: "reverse Super Jump"), Fireball, Teleporter | [S Fandom] |
| MIU | Super jump (arrow up), speed boost (lightning bolt), time slow (pause icon, instant), glide wings (Ultra) | [S Gaming Trend, Nintendo Life] |

---

## 4. Hazards and interactive objects

| Object | Behavior | Numbers (Web port `shapes/*.ts` unless noted) |
|---|---|---|
| Land mine | Explodes on contact, pushes marble away, respawns | Respawn after 5 s. Push strength depends on distance (parabolic fit by RandomityGuy): `v = (r-5)^2 / (-4*0.0714) + 87.5` for r < 10; zero beyond 10.25. Fandom: mine force is similar to bumper; replaced by bumpers in MBU [S]. Census: 268 mines across the 100 MBG levels [D]. |
| Nuke (MBP) | Bigger mine | Respawn 15 s. Force `(1 - d/10) * 100` times offset vector, range 10. "Ported from decompiled MBG" per code comment [V] |
| Bumper (round/triangle) | Sets marble velocity along contact normal to 15 m/s, wiggle animation | `setLinearVelocityInDirection(normal, 15, false)`; restitution 0 (not physics bounce, so Super Bounce/Shock Absorber do not change it) [V code + Fandom] |
| Bouncy floor (MBP) | Same launch idea as bumper | [S] |
| Trap door | Opens on contact after a `timeout`, resets after 5 s; fast roll can cross it | `RESET_TIME 5000 ms`. 173 trapdoors in MBG data [D] |
| Duct fan | Conic force pushing marble away | Range 10 m, arc 2.617 rad (150 deg), strength 40 (`addConicForce(10, 2.617, 40)`). "Roll under it" is the standard counter. Web notes fan force was reworked to be closer to original. |
| Small duct fan | Smaller version | [V file exists] |
| Tornado | Pulls in, then slings upward | Spherical force r=8 strength -60 (suck), r=3 strength +60 (repel), plus upward field force r=3 of 150. Non-collidable. |
| Magnet (MBP) | Pulls marble toward it | Range 10, arc 0.7 rad, strength -90 |
| Oil slick | Near-zero friction patch | friction `0.01` ("friction_none") |
| Surfaces | Friction multiplier table | normal 1.0; grass 1.5; tarmac 0.35; sand 4.0; carpet/rug/water 6.0; ice 0.03; "friction_high" 1.5, "friction_low" 0.2, "friction_none" 0.01; friction ramp yellow 2.0. Restitution table: sand 0.1, grass 0.35, tarmac 0.7 (Web `interior.ts`) [V]. Fandom: ice 3% friction, tarmac 35%, sand 400% — matches. |
| Moving platform / elevator | Pathed interiors: linear, sine-ish, etc. Marble does not move with platform unless supported | Pathed interior; 368 `PathedDefault` entities in the 100 MBG levels [D] |
| Random force (MBP) | Pushes opposite to spin | [S] |
| Teleporter (MBP) | Moves marble to another area on activation | [S] |
| PQ-only | Cannons, water, ice shards (mega marble dispelled by ice shards), physics-modifying triggers, wheels | [S] |

Census of all 100 MBG levels (count of instances; D): mines 268, gems 256, trapdoors 173, Time Travel 107, Gravity Modifier 104, round bumpers 98, duct fans 93, Super Speed 67, Super Jump 61, Gyrocopter 17, Super Bounce 17, triangle bumpers 15, Shock Absorber 12, tornado 8, oil slick 8. Power-ups used most in Advanced levels (Time Travel in 17 of 52, Super Jump in 18, Gravity Modifier in 9).

---

## 5. Controls and camera

Keyboard/mouse (Web port defaults, `storage.ts`): W/A/S/D roll; Space jump; Left mouse use power-up; Right mouse free-look; arrow keys camera; R restart/respawn; E Blast; Esc pause. Mouse sensitivity and invert are options; FOV default 60. Original MBG/PQ: arrow keys or WASD to roll, mouse to look, Space jump, Left click uses power-up (Fandom Camera page confirms mouse or arrow keys for camera) [S].

Gamepad (OpenMBU `default.bind.cs`, Xbox 360): left stick roll; right stick camera, deadzone 0.23; A jump; LT jump; RT and B use power-up; X, LB, RB = Blast (`altTrigger`); Start pause; Back = alt pause; Y = player list in MP [V]. Web port: buttons mapped `jump, use, blast, ...` with d-pad as roll.

Analog scaling: in non-MBG physics (MBU) the input vector is multiplied by 1.538 then clamped to length 1, i.e. about 65% stick deflection gives full speed (OpenMBU `computeMoveForces`). MBG does not normalise the input vector, so diagonal keyboard input is faster (about 1.41x) [D from code; Fandom "Diagonal Movement" says diagonal movement gives extra speed].

Camera: third person, orbits marble. Web port: distance 2.5 units behind marble (PQ `CameraDistance = 2.5`), default pitch 0.45 rad (~26 deg), pitch clamp roughly [-45 deg, +90 deg), raycast from marble to camera to avoid wall clipping, camera locks on OOB and on finish. MBU adds camera lag (`cameraLag 0.2`, `cameraLagMaxOffset 4.2`, `cameraDecay 4`) and camera-shake on hard bounces (soft/medium/hard bounce speed thresholds 3 / 6 / 9 m/s) [V OpenMBU marble.cs].

Air control: yes. Air acceleration `5` (OpenMBU/MBHaxe/PQ `airAccel`); doubled by Gyrocopter. Spin in the air also changes how you bounce off the next surface (Wikipedia: "affects both the marble's acceleration through the air and its momentum when bouncing").

Blast (MBU): meter charges over time; one press does a small up-hop plus shockwave. OpenMBU: usable above 25% charge; natural full charge 30 s (`maxNaturalBlastRecharge 30000`), Ultra Blast refills to 36 s (`blastRechargeTime 36000`, i.e. 120%); blast impulse `boostAmount 8` scaled by charge and `boostMassless`; repulses other marbles within 10 m up to force 60 (`repulseDist 10`, `repulseMax 60`); activation delay 150 ms; resets charge to 0 [V]. Web port differs: 25 s full charge, minimum 0.2, impulse `max(sqrt(b), b) * 10` m/s up, Ultra Blast sets charge to 1.03 [V; conflicts, retail value unverified].

---

## 6. Physics numbers

### 6.1 Canonical constants (match across OpenMBU `marble.cs`, PQ `defaultProperties.cs`, MBHaxe `Marble.hx`)

| Parameter | Value | Notes |
|---|---|---|
| Marble radius | 0.2 (MBG, MBP, PQ); 0.3 (MBU, scaled x1.5) | MBHaxe: `_radius = 0.3` if Ultra. Web: `DEFAULT_RADIUS 0.2`, `ULTRA_RADIUS 0.3`, `MEGA 0.6666` |
| Gravity | 20 m/s^2 | about 2x Earth; Gyro makes it 5 |
| maxRollVelocity | 15 m/s | target speed from input; never slows you if you are already faster (code: `desiredVelocity = current` when current > desired) |
| angularAcceleration | 75 rad/s^2 | clamp on how fast spin approaches target. [D] at r=0.2 that is 15 m/s^2 of roll acceleration, so ~1 s to full speed |
| brakingAcceleration | 30 rad/s^2 | used when no input ("centered"): spin pulled to 0 |
| airAccel | 5 m/s^2 | x2 with Gyrocopter |
| jumpImpulse | 7.5 m/s | along contact normal. Web port uses 7.3 ("seems to fit more than 7.5"). [D] jump apex = 7.5^2 / (2*20) = 1.4 m = 7 marble radii |
| staticFriction / kineticFriction | 1.1 / 0.7 | times surface friction factor |
| bounceKineticFriction | 0.2 | friction applied at bounce contact |
| bounceRestitution | 0.5 | default; Super Bounce 0.9; Shock Absorber 0.01 |
| maxDotSlide | 0.5 (about 30 deg) | shallow-angle impacts slide instead of bouncing |
| minBounceVel | 0.1 | below this closing speed, cancel velocity along normal without bounce |
| minBounceSpeed (sfx/particles) | 3 | MBU soft/medium/hard thresholds 3 / 6 / 9 |
| mass | 1 | Mega: x5 in OpenMBU |
| Power-up boosts | Super Jump +20, Super Speed +25, bumper 15 | all m/s |
| Max angular speed cap | 300 rad/s absolute (Web); 120 rad/s from input (Web) | 12 rev/s => 75.4 rad/s * 0.2 = 15.1 m/s, consistent with maxRollVelocity [D] |

### 6.2 Simulation structure (why it feels the way it does)
- Original Torque engine step (OpenMBU `advancePhysics`): game tick 32 ms (blast energy is stored in `>>5` units), marble sub-step 8 ms (125 Hz), loop until the tick time is consumed. Each sub-step: compute move forces, find contacts, cancel velocity into surfaces (bounce/slide rules), apply gravity and contact friction, integrate, then `testMove` swept-sphere vs collision geometry. [V]
- MBHaxe: 4 ms sub-step (250 Hz), same contact model ported from OpenMBU, custom swept-sphere vs triangle `testMove`; its GJK code exists but is unused (`AGENTS.md`). README claim: ~"99% identical physics" (repo description) [V as claim, not measured by me].
- Web port: fixed 120 Hz with continuous collision detection; own rigid body, GJK convex shapes, octree broadphase, impulse-based friction/restitution response (cites Schornbaum thesis); collisions in the marble code use a ball shape plus two bigger auxiliary shapes (2x radius for items, 1x for triggers). [V]
- Marble as a spinning sphere: input applies angular acceleration toward a target angular velocity, not a linear force; linear motion arises from rolling contact + friction. This is why slopes, ice, and sand feel different with the same input, and why wall-hits, edge-hits and trap-launches (stored spin turning into linear speed) are possible. [V code + Fandom tactics pages]
- Extra "feel" hacks in the Web port, each documented in code comments: extra velocity boost on shallow sliding hits (`diff * 2`), an angular-velocity-based boost on wall hits (`/ (2π) / 15`), shock absorber boost from spin on contact, a sliding timeout after bumper/mine hits so the marble does not stick to the surface, post-finish velocity decay (x0.9 per tick). These are tuned to match the original, not physically derived. [V]

### 6.3 Custom collision vs engine physics: what each project did and why
- Original (Torque, 2003-2006): custom marble physics + sphere vs interior-polygon contact finder. [V OpenMBU]
- Marble Blast Web: v1 used three.js + OimoPhysics (third-party rigid body). v2.4.0 "completely rewrites the physics engine from scratch, ditching the third-party dependency": reasons given are performance (stutter in complex levels, mobile), "fine-grained control", and consistency: very fine continuous collision detection so internal-edge hits "are basically impossible", curved surfaces (pipes, loops) behave. They also fixed delayed input/event handling. Also: older versions caused leaderboard inconsistencies and the leaderboards were reset in 2.6.0 because past physics changes had made scores inconsistent. [V `version_history.md` 2.4.0, README]
- Marble It Up (Unity): "Unity's physics were completely inadequate for our needs. In the end, about half of the game code was for our custom marble physics engine"; "part of the reason we have our own physics is in order to make them unrealistic... bending the laws of physics in just the right way makes things way more fun." Physics support arbitrary rewind (used for level testing, ghost racing, replay and network prediction). Dynamic blob shadow instead of Unity shadows for crisp depth cues; 60 Hz on Switch handheld. [V Garney blog]
- Lesson: every serious marble game ended up writing its own sphere-vs-world solver. Engine rigid bodies give inconsistent contact (internal edge hits, jitter), inconsistent replays, and cannot be bent for feel.

---

## 7. Multiplayer, leaderboards, replays, achievements

- MBU (Xbox 360): up to 8 players, 20 MP levels, one core mode (Gem Hunt: groups of 2-6 gems appear, race to them; red 1, yellow 2, blue 5; 3-6 min rounds; Mega Marble knocks others). Ranked and player matches, overall leaderboard, private games, marble skins and effects. Three DLC packs in 2008 (5 maps each: "Marble It Up" level pack on 2008-10-29, Marble-Fu, Agoraphobia) and 3 extra achievements. 15 achievements, 250 gamerscore. SP leaderboards compare best times (including friends). [S Wikipedia, TrueAchievements, HonestGamers]
- MP modes across series (Fandom Multiplayer): Gem Hunt, Collection, Mega Marble Wars, Co-Op; PQ rule options (teams, quick respawn every 25 s, steal mode, double spawns), rating system starting at 1500; handicaps. MIU Mayhem/Ultra: Gem Hunt, Steal the Crown, soccer, zombies (infection by hit), cross-platform (PC/Switch/Xbox/PlayStation). Lag in MBU MP noted by GamesRadar. [S]
- Replays/ghosts: MBP/PQ record demos (Random power-ups corrupted demos in MBP: a deterministic-replay lesson). MIU: ghost of your best + top players via leaderboards (Nintendo Life announcement); Web port has a replay system storing inputs plus random power-up choices. [S/V]
- Leaderboards: MBU (XBL), MBP (from v1.14, hosted by PhilsEmpire), PQ, MIU global + friends + weekly challenges that apply modifiers to existing levels [V Steam]. 
- Level editing/workshop: MBG shipped an in-game level editor; MIU Steam Workshop has 200+ levels. [V]

---

## 8. Reception and what changed in Marble It Up

Marble Blast Ultra (2006): Metacritic 79 (22 critics per MobyGames). Eurogamer 8/10, GameSpot 6.8, IGN 6.9, OXM US 8.5, TeamXbox 8.7, PALGN 7, Detroit Free Press 4/4 [S Wikipedia].
- Praised: tight, readable physics and controls; time-trial replayability; power-up variety (mega marble, blast); shader/graphics polish; value at 800 MS points; friend-comparison leaderboards (HonestGamers: "tight controls and unflinching resolve"); tutorials teach each move.
- Criticized: GameSpot (Gerstmann): "Super Monkey Ball without the personality", boring multiplayer, lack of variety, dull music, lack of graphical variety. GamesRadar cons: wonky bounciness, multiplayer lag, falling to your death (frustration). Little incentive to return after the campaign (user reviews on GameSpot/Metacritic snippets) [S].

Marble Blast Gold (2003): Wikipedia lists mixed-average reviews for original Marble Blast (Eurogamer 5/10, Macworld 4/5, Inside Mac Games 6.5). Fandom: modding scene (custom levels via Constructor, QuArK, Blender) is the long-term legacy [S].

Marble It Up (2018): Nintendo World Report 7/10: "control of the marble is immaculate, framerate buttery smooth, level design strong", but "over way too quickly", 40 levels done in about an hour, tutorials took too much of the content, only reward after finishing is skins [V]. Gaming Trend: 1.5 hours for 40 levels, medals only unlock skins; physics "can frustrate" in Ultra review.
Marble It Up! Ultra (2023): NWR 8.5; Nintendo Life: more than 100 levels, 20-minute early worlds, "sharp difficulty spike around the third world", jump button "unpredictable in places"; MP modes "fun but fleeting" (NWR). PureNintendo: no local multiplayer is a letdown (search snippet).

What MIU changed vs Marble Blast, and why (sources: Garney blog, reviews, MIU Steam page):
1. Rebuilt engine in Unity with custom physics, 60 Hz, rumble. Why: precise feel on Switch, rewind-based tooling. [V]
2. Medals (bronze/silver/gold/diamond) instead of a single Gold Time; medals gate bonus chapters and cosmetics. Why: broader goal ladder for casual players. [S]
3. Time-slow pickup instead of Time Travel clock freeze; glide wings; gravity-surface floors, bouncy floors, ice. [S]
4. Ghost racing + replays + global/friend leaderboards built in from day one (rewind system generalised). [V]
5. Cosmetic economy (marbles, trails, hats, shards) and Weekly Challenges (modifier-based re-runs of existing levels) for retention. [V Steam, NWR]
6. Cross-platform multiplayer (5 modes) added later (Mayhem 2019, Ultra 2023). [V]
7. Chapters with 10-12 levels, any order, only some needed to unlock the next world, instead of three long difficulty tiers. [S: reviews]

---

## 9. Genre peers (brief)

- Marble Madness (Atari, 1984, Mark Cerny): isometric, 6 courses, trackball, time limit, enemies, Escher-like geometry. Core trait: momentum-based control plus time pressure. [S Wikipedia]
- Super Monkey Ball (Amusement Vision/Sega, 2001): you tilt the whole stage with the analog stick (not the ball); goal with time limit; bananas for points; three tiers Beginner/Advanced/Expert with 10/30/50 floors; no jump in the base game; party-game mini-games; praised for "reductive control system" with subtle depth; Metacritic 87. [V Wikipedia]
- Hamsterball (Raptisoft, 2004): 15 race courses, hamster in a ball, dizziness after short falls, respawn after a delay; "Rodent Rumble" MP arena (knock opponents off); IAA "Computer Downloadable Game of the Year". [V Wikipedia]
- Marble Blast differs from SMB: you steer the marble, not the world; free orbit camera; jump and air control; power-ups; gold-time speedrun culture and moddable levels.
- Others named by sources: Neverball (open-source SMB-like), Switchball, Kororinpa, Mercury Meltdown [S: Wikipedia See also, Nintendo Life comments].

---

## 10. What makes it feel good, and design lessons

Observed from code, wikis and reviews:
1. Responsiveness: input -> angular acceleration with a 75 rad/s^2 cap and 30 braking; instant jump (7.5 impulse). The Web port queues jump/use/blast presses that land between physics ticks and clears the queue after one tick (`jumpQueued`), so no press is dropped, but there is no multi-tick jump buffer or coyote time in that code [V]. The 120-250 Hz sub-stepping keeps contact stable. Jump is allowed whenever any contact normal has a positive up component.
2. Readable level design: rules are taught by one mechanic per tutorial level; hazards have distinct silhouettes (mines, bumpers, fans) and sound; flat pads for start/finish; Garney's crisp blob shadow for depth reading; "In Bounds" volumes make failure obvious; respawn after 2 s keeps retries cheap.
3. Skill ceiling via emergent physics: wall hits, edge hits, trap launches (stored spin or moving platforms squeezing the marble), diagonal movement, fast starts, downhill skipping. Ultimate times are designed around them. Fans/trapdoors/platforms are all "forces on a sphere", so tricks compose.
4. Multiple goal ladders: finish -> qualify -> gold -> ultimate; plus eggs, achievements, ghost/replay, leaderboards.
5. Hazards act on the marble's velocity, not as instant death, so recovery is possible and routes can use hazards (jump off a mine, ride a fan).
6. Short sessions: MBG gold times median 5-30 s; MIU levels finish in under a minute so retry is natural.

Top design lessons for your original game (ordered):
1. Write your own marble solver (sphere vs triangle mesh with CCD, fixed 120-250 Hz). Both Marble Blast Web and Marble It Up abandoned engine rigid bodies; make it deterministic from day one so ghosts, replays, rewind and leaderboards come cheaply.
2. Model the marble as a spinning sphere driven by target angular velocity (maxRoll ~15 m/s at radius 0.2, angular accel ~75, braking ~30, gravity 20, jump ~7.5, air accel ~5, restitution 0.5). Tune from these numbers first. They are proven; the "overshoot never slows you down" rule and sliding rule (shallow hits do not bounce) are what make it feel fair.
3. Teach one mechanic per tutorial level, in order; make hazards modify velocity, never end the run; make OOB respawn fast (about 2 s) and add checkpoints that preserve state but not the clock.
4. Layer goals: a pass threshold, a "skilled" target, and a "needs tricks" target, plus medals and cosmetics. Do not tie unlocks only to the hard targets; MBG shows most levels need no qualify time at all (22 of 100 had one).
5. Ship ghosts, replays, leaderboards and level editor/workshop early; players made 3,900+ Web-port levels and 200+ MIU workshop levels. Avoid MBU's weak spots: thin multiplayer, low visual variety, short content. MIU's 40-level launch was criticised as too short; plan 60+ levels with a real difficulty curve.

---

## 11. Not verified / conflicts

- Retail Blast charge time: OpenMBU 30 s natural (36 s with Ultra Blast), Web port 25 s. Unknown which matches retail MBU. Min blast threshold 25% vs 20%.
- Jump impulse: 7.5 in data (OpenMBU/PQ/MBHaxe), 7.3 in Web port (tuning). Super Speed 25 vs 24.7.
- Super Bounce duration: 5 s in code (PQ/Web), 6 s on Fandom.
- Whether Super Bounce and Shock Absorber appear in MBU: Fandom says no; OpenMBU `PowerUpDefs` has them commented "currently unused"; MBU mission files are not in OpenMBU's repo so I could not check; Wikipedia silent.
- MBG release date (May 9, 2003 on Wikipedia; Giant Bomb April 25; TCRF June 17 international).
- MIU release: Switch September 2018 (Wikipedia) vs 2018-11-16 (Fandom).
- MIU Time Travel -> time slow: one Fandom line plus reviews describing time slow; I did not see the game.
- MBU multiplayer: Wikipedia says one mode (Gem Hunt) with 20 levels and 8 players; Fandom lists additional modes under MBO/MBU/Mobile. Probably other modes belong to MBP/MBO/PQ.
- Per-level counts for MBU Beginner/Intermediate/Advanced (20/20/20) from Fandom lists and Wikipedia; Xbox Gold 94 and the score formula are Fandom-only [S].
- Exact retail MBU frame timing, camera constants (pitch limits, lag), analog curve beyond the 1.538 factor: only from reimplementations.
- Metrics like "42 of 100 MBG levels have gems", "22 of 100 have qualify time", gold-time medians: computed by me from `.mis` files bundled in the Web repo; the Web repo's mission data is a copy of retail files, so I trust it but did not compare against a retail install.
- Speedrun community data (speedrun.com categories, current world records) not researched.
- I did not view the DeepWiki pages or octen CLI; local source clones and wiki APIs covered the same ground.
