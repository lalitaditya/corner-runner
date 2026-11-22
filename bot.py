"""JSON-lines entry point for the Python decision engine."""

import json
import os
import queue
import sys
import threading
import traceback

from decisions import DefaultParams, New
import protocol
import world


class Bot:
    def __init__(self, message):
        hello = protocol.hello(message)
        params = DefaultParams()
        overrides = json.loads(os.environ.get("BOT_PARAMS") or "{}")
        slots = {name.lower(): name for name in params.__slots__}
        for name, value in overrides.items():
            field = slots.get(name.lower())
            if field is not None:
                setattr(params, field, value)
        directories = (os.environ.get("MECHFIGHT_MAP"), hello.Map.Dir, "/arena", "arena")
        for directory in dict.fromkeys(filter(None, directories)):
            try:
                arena, error = world.Load(directory)
                if error is None and arena is not None:
                    break
            except (OSError, ValueError):
                pass
        else:
            raise FileNotFoundError("could not load the arena map")
        nav = world.NewNav(arena, hello.Config.Mech.get("step_up", 1.2), hello.Config.Mech.get("height", 9))
        self.engine = New(hello, arena, nav, params)
        self.name = params.Name

    def act(self, message):
        return protocol.action(self.engine.Act(protocol.observation(message)))


def serve():
    incoming = queue.SimpleQueue()

    def read_input():
        try:
            for line in sys.stdin.buffer:
                message = json.loads(line)
                incoming.put(message)
                if message.get("type") == "end":
                    return
        finally:
            incoming.put(None)

    reader = threading.Thread(target=read_input, daemon=True)
    reader.start()
    bot = None
    last = {}

    def send(message):
        sys.stdout.write(json.dumps(message, separators=(",", ":"), allow_nan=False) + "\n")
        sys.stdout.flush()

    while True:
        msg = incoming.get()
        newest = None
        while True:
            if msg is None or msg["type"] == "end":
                reader.join()
                return
            if msg["type"] == "hello":
                bot = Bot(msg)
                send({"type": "ready", "name": bot.name})
            elif msg["type"] == "obs":
                newest = msg
            try:
                msg = incoming.get_nowait()
            except queue.Empty:
                break
        if newest is None:
            continue
        try:
            last = bot.act(newest)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            last = {k: v for k, v in last.items() if k in ("move", "boost", "aim")}
            last["tick"] = newest["tick"]
        send(last)


if __name__ == "__main__":
    serve()
