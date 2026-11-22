"""Compare all gameplay actions on the official kit recording with the pinned engine."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import select
import subprocess
from uuid import uuid4


STREAM_SHA256 = "0fa2aa93f02fb93152f0681cdddfc023d48c3da5fe54e8e7fe6172d08b028321"
# Captured from revision a484109a70db447abd390ffe871c32026cd15d7e.
ACTIONS_SHA256 = "cad46cb3e3021ba64fdf355227cc9545222e6e570060f7435f5e12fd52b65768"


def canonical_action(action):
    action.pop("debug", None)
    # JSON numbers differing only in notation or the sign of zero represent the same vector.
    for field in ("move", "aim"):
        if field in action:
            action[field] = [float(value) + 0.0 for value in action[field]]
    return (json.dumps(action, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def replay(kit, image):
    with gzip.open(kit / "check" / "stream.jsonl.gz", "rb") as source:
        stream = source.read()
    if hashlib.sha256(stream).hexdigest() != STREAM_SHA256:
        raise ValueError("This kit has a different recording from the one used for the reference.")

    name = "decision-check-" + uuid4().hex
    command = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--name",
        name,
        "--platform",
        "linux/amd64",
        "--cpus",
        "1",
        "--memory",
        "512m",
        "--memory-swap",
        "512m",
        "--network",
        "none",
        "--cap-drop",
        "ALL",
        "--pids-limit",
        "128",
        "--read-only",
        "--user",
        "65534:65534",
        "--tmpfs",
        "/tmp:rw,size=64m",
        "-v",
        f"{kit.resolve() / 'arena'}:/arena:ro",
        image,
    ]
    digest = hashlib.sha256()
    count = 0
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        try:
            for line in stream.splitlines():
                message = json.loads(line)
                kind = message["type"]
                if kind == "hello":
                    message["map"]["dir"] = "/arena"
                    line = json.dumps(message).encode()
                process.stdin.write(line + b"\n")
                process.stdin.flush()
                if kind == "end":
                    break
                if not select.select([process.stdout], [], [], 10)[0]:
                    raise TimeoutError(f"No reply to {kind} at tick {message.get('tick')}")
                reply = json.loads(process.stdout.readline())
                if kind == "hello":
                    if reply.get("type") != "ready":
                        raise ValueError(f"Expected ready, received {reply!r}")
                else:
                    if reply.get("tick") != message["tick"]:
                        raise ValueError(f"Expected tick {message['tick']}, received {reply!r}")
                    digest.update(canonical_action(reply))
                    count += 1
            process.stdin.close()
            if process.wait(timeout=10):
                raise RuntimeError(f"Container exited with status {process.returncode}")
            if process.stdout.read().strip():
                raise ValueError("Bot emitted additional output after the last action.")
        finally:
            if process.poll() is None:
                subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, check=False)
                process.kill()
    return count, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path, help="path to the extracted mechfight-kit directory")
    parser.add_argument("--image", default="mech-royale-python", help="Docker image to test")
    args = parser.parse_args()
    count, digest = replay(args.kit, args.image)
    if digest != ACTIONS_SHA256:
        raise SystemExit(
            f"Mismatch on the {count}-action recording.\nExpected {ACTIONS_SHA256}\nGot      {digest}"
        )
    print(f"PASS: all {count} gameplay actions matched ({digest}).")


if __name__ == "__main__":
    main()
