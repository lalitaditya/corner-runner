# Corner Runner

The default Dockerfile builds the Go bot for Linux on amd64. The Python bot is available through its existing entry point. The public-room recorder is in `tools/observe.py`.

## Build

```sh
docker build --platform linux/amd64 -t corner-runner .
```

## Check

From the extracted competition kit, run the recorded match stream against the container.

```sh
python3 check/check.py --map-dir /arena -- docker run --rm -i \
  --platform linux/amd64 --cpus 1 --memory 512m --network none \
  --read-only --user 65534:65534 --tmpfs /tmp:rw,size=64m \
  -v "$PWD/arena:/arena:ro" corner-runner
```

The Go executable reads the arena from `/arena` and communicates over standard input and output. Its base module is documented in the [source record](licenses/SOURCE.md).
