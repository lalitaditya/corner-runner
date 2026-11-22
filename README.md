# Corner Runner

A Python bot for Builders Mech Royale. The practice opponent is a squad of 15 mechs with shared vision. Corner Runner uses the opening to build enough health and damage to take an isolated fight.

- **At spawn** it ranks loose cubes, weapon pickups, crates and drones by their travel time, time to destroy, and proximity to known opponents. A secondary weapon near a source of cubes makes the trip more attractive. If a laser or lightning pickup is within 100 m on the same level and inside the zone, the opening planner gives the weapon priority over farming. It then seeks three cubes for the first two upgrade offers. An approaching attacker or the closing zone can interrupt that route.
- **Once equipped** it looks for a lone opponent it can reach with its weapon, keeps the autocannon on the same target, and collects the dropped cubes when the approach looks clear. For a wounded opponent, it estimates the seconds needed to finish using magazine state, secondary cooldown, range and cube bonuses. It checks other tracked mechs’ aim, motion and projected sightlines before committing to a quick finish. After an elimination, it can collect a nearby cluster of visible cubes inside the zone, provided known opponents are far enough away. At the cube combat-stat cap it stops dedicated cube collection routes and keeps its position for the next engagement. In a duel, the bot projects both its strafe and nearby lightning carriers’ movement over the next 0.8 seconds. It favors paths outside arc range when using its gun or laser, and can still close on its own lightning target.
- **Between fights** it scouts while healthy and uses solid cover to recover when damaged. It drops its rooftop objective at 88% health and checks the next safe zone before continuing. Trees are traversable and can conceal movement at range. Buildings can also stop shots.

## Fighting from a corner

Corner Runner keeps a short history of damage dealt to and received from each tracked opponent. It uses the armor left on both mechs and damage from other shooters to decide whether to trade another burst or seek cover. When a wounded opponent breaks sight, the bot can pursue briefly if the approach stays in the zone and nearby enemies cannot cover it.

During a duel, it estimates when either weapon can deal damage again. It can move behind a wall during a reload, remember the firing position, and return there when a weapon is ready. It checks the aim and sightlines of up to two additional threats before choosing its next step.

## Learned aiming

The gun uses a small motion model fitted offline on opponent tracks from 32 local matches. For a given projectile flight time, the model estimates horizontal displacement from the opponent’s velocity and its change since the preceding observation. The runtime reads 36 pairs of coefficients from `lead_model.py`. The laser uses a separate hitscan calculation. Both run in standard-library Python.

## Run the bot

Build the top-level Dockerfile with `docker build --platform linux/amd64 -t corner-runner .`. The container expects the organizer’s map at `/arena` and communicates over standard input and output. The protocol wrapper in `mechfight.py` comes from the Builders starter kit. See the [competition protocol](https://www.joinbuilders.org/buildathon/tracks/builders/files/protocol.md?inline=1) for the official container check.

## Record a public practice room

With Chrome and uv installed, run `./tools/observe.py --seconds 120`. Use `--room 21` to join a particular public room. The script opens an interactive Chrome window, enters a nickname and joins automatically. The first visit downloads campus graphics, which can take a minute or more.

Each run writes a timestamped folder under `~/Videos/MechRoyale`. The JSON lines contain visible HUD text, clock readings and screenshot filenames. When the HUD displays an alive count, a decrease saves a before/after pair. During a match with the count hidden, the recorder saves an overview every five seconds. The browser tool runs separately from the competition container.
