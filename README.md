# Mech Royale

A Python port of the Mech Royale decision engine at [revision a484109](https://github.com/ahmad-ovh/Buildathon/tree/a484109a70db447abd390ffe871c32026cd15d7e). The container runs the Python policy for every observation. A compiled Cython extension accelerates geometric queries and pathfinding on the campus map.

## Build and run

Build for the scoring platform:

```sh
docker build --platform linux/amd64 -t mech-royale-python .
```

From the organizer’s extracted kit directory, exercise the normal entry point under the competition limits:

```sh
python3 check/check.py --map-dir /arena -- docker run --rm -i \
  --platform linux/amd64 --cpus 1 --memory 512m --memory-swap 512m \
  --network none --cap-drop ALL --pids-limit 128 --read-only --user 65534:65534 \
  --tmpfs /tmp:rw,size=64m -v "$PWD/arena:/arena:ro" mech-royale-python
```

From this repository, replay all 300 actions in the kit recording and compare their digest with the reference engine:

```sh
python3 tools/check_decisions.py /path/to/mechfight-kit
```

## Implementation

- `bot.py` reads the JSON-lines stream, initializes the match and dispatches the newest observation to the engine.
- `decisions.py` implements match memory, target selection, firing and reload timing, movement, cover, roof access, equipment and upgrades. Its default gameplay parameters match the pinned revision.
- `protocol.py` decodes game messages and serializes actions at the reference engine’s movement and aiming precision.
- `world.py` and `spatial.pyx` implement terrain, obstacles, tree crowns and navigation. The map fingerprint determines whether the precomputed campus data applies.
- `gorandom.py` reproduces the reference random stream for the match seed and slot.

The Docker build uses Cython and setuptools. The policy port’s notice is in `licenses/engine-MIT.txt`. The random number generator’s notice is in `licenses/Go-BSD.txt`.

## Record a public practice room

With Chrome and uv installed, run `./tools/observe.py --seconds 120`. Use `--room 21` to join a particular public room. Recordings are written under `~/Videos/MechRoyale`. This tool runs separately from the competition container.
