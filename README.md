# Corner Runner

A Python bot for the Builders Mech Royale competition. It scans for a laser or lightning pickup, collects cubes and upgrades, and chooses fights based on its health, the number of nearby opponents and the distance to the next circle.

Trees are traversable. The bot uses the map’s crown heights and widths to find leafy ground near buildings. It walks quietly there when distant enemies have lost contact. When opponents close in or armor falls, it searches for a building corner or a reachable rooftop that screens it from the nearest threats. The shot calculation uses buildings, bridges and terrain.

## Running the bot

Build the top-level Dockerfile with `docker build --platform linux/amd64 -t corner-runner .`. The container expects the organizer’s arena at `/arena` and communicates over standard input and output. The runtime uses only the Python standard library. The protocol wrapper in `mechfight.py` comes from the Builders starter kit.

The [competition protocol](https://www.joinbuilders.org/buildathon/tracks/builders/files/protocol.md?inline=1) describes the match interface and container check.
