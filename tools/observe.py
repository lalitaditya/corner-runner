#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.65.2"]
# ///
"""Open a public Mech Royale room in Chrome and save its visible scoreboard and elimination frames."""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Error, sync_playwright

ALIVE = re.compile(r"\bALIVE\s+(\d{1,2})\s*/\s*(\d{1,2})\b", re.I)
MATCH = re.compile(r"\bROOM\s+(\d+)\s*[·•-]\s*MATCH\s+(\d+)", re.I)
CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b")


def record(page, folder, seconds):
    deadline = time.monotonic() + seconds
    previous = None
    count = 0
    next_overview = 0
    samples = 0
    with (folder / "hud.jsonl").open("w", buffering=1) as log:
        while time.monotonic() < deadline and not page.is_closed():
            texts = []
            for frame in page.frames:
                try:
                    texts.append(frame.locator("body").inner_text(timeout=3000))
                except Error:
                    if not frame.is_detached() and not page.is_closed():
                        raise
            hud = "\n".join(texts)
            current = ALIVE.search(hud)
            match = MATCH.search(hud)
            match_id = "-".join(match.groups()) if match else None
            alive = int(current[1]) if current else None
            row = dict(
                time=datetime.now().astimezone().isoformat(timespec="seconds"),
                room_match=match_id,
                alive=alive,
                clocks=CLOCK.findall(hud),
                hud=hud,
            )
            samples += 1
            if not current and time.monotonic() >= next_overview:
                row["frame"] = f"overview-{samples:04d}.jpg"
                page.screenshot(path=folder / row["frame"], quality=70, timeout=8000)
                next_overview = time.monotonic() + (5 if match else 20)
            if current:
                count += 1
                frame = page.screenshot(type="jpeg", quality=70, timeout=8000)
                stamp = f"{count:04d}"
                if previous is None or previous[0] != match_id or alive > previous[1]:
                    row["frame"] = f"{stamp}-start.jpg"
                    (folder / row["frame"]).write_bytes(frame)
                elif alive < previous[1]:
                    row["before"], row["frame"] = f"{stamp}-before.jpg", f"{stamp}-after.jpg"
                    (folder / row["before"]).write_bytes(previous[2])
                    (folder / row["frame"]).write_bytes(frame)
                    row["eliminations_since_sample"] = previous[1] - alive
                    print(f"{row['time']}   {previous[1]} → {alive} alive", flush=True)
                previous = match_id, alive, frame
            else:
                previous = None
            log.write(json.dumps(row, ensure_ascii=False) + "\n")
            page.wait_for_timeout(1500)
    print(f"Saved {samples} samples ({count} with an alive count) in {folder}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--room", type=int, help="public room number, e.g. 3")
    parser.add_argument("--out", type=Path, default=Path.home() / "Videos" / "MechRoyale")
    args = parser.parse_args()
    if args.seconds <= 0 or (args.room is not None and not 1 <= args.room <= 999):
        parser.error("Use a positive duration and a room from 1 to 999.")
    folder = args.out / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    folder.mkdir(parents=True)
    print(f"Saving observations to {folder}", flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            Path.home() / ".cache" / "corner-observer",
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--enable-unsafe-swiftshader"],
        )
        page = browser.pages[0]
        try:
            url = "https://play.joinbuilders.org/" + (f"#room-{args.room}" if args.room else "")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            name = page.locator('input[autocomplete="nickname"]:visible')
            joined = page.get_by_text("Invite a friend: copy link", exact=True)
            name.or_(joined).first.wait_for(timeout=60000)
            if name.is_visible():
                name.fill("ArenaObserver")
                page.get_by_text("Join" if args.room else "Play now", exact=True).click()
            record(page, folder, args.seconds)
        except KeyboardInterrupt:
            pass
        except Error:
            if not page.is_closed():
                raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
