# Corner Runner

A Python bot for Builders Mech Royale. It searches for a secondary weapon, collects cubes from reachable crates and drones, and finishes isolated opponents it has already damaged. It backs away when its gun cannot tilt down far enough to hit a nearby drone. When opponents close in or armor falls, it looks for a building corner or roof that screens it from the nearest threats. Dense tree cover is traversable and can help conceal an approach.

## Learned aiming

The gun uses a small motion model fitted offline on opponent tracks from 32 local matches. For a given projectile flight time, the model estimates horizontal displacement from the opponent’s velocity and its change since the preceding observation. The runtime reads 36 pairs of coefficients from `lead_model.py`. The laser uses a separate hitscan calculation. Both run in standard-library Python.

## Run the bot

Build the top-level Dockerfile with `docker build --platform linux/amd64 -t corner-runner .`. The container expects the organizer’s map at `/arena` and communicates over standard input and output. The protocol wrapper in `mechfight.py` comes from the Builders starter kit. See the [competition protocol](https://www.joinbuilders.org/buildathon/tracks/builders/files/protocol.md?inline=1) for the official container check.

## Record a public practice room

With Chrome and uv installed, run `./tools/observe.py --seconds 120`. Use `--room 21` to join a particular public room. The script opens an interactive Chrome window, enters a nickname and joins automatically. The first visit downloads campus graphics, which can take a minute or more.

Each run writes a timestamped folder under `~/Videos/MechRoyale`. The JSON lines contain visible HUD text, clock readings and screenshot filenames. When the HUD displays an alive count, a decrease saves a before/after pair. During a match with the count hidden, the recorder saves an overview every five seconds. The browser tool runs separately from the competition container.
