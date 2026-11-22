"""Corner Runner: use campus walls and rooflines to control exposure."""

import math
from arena import Arena
from lead_model import offset
import mechfight as mf


def horizontal(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def toward(a, b, stop=1.4):
    distance = horizontal(a, b)
    if distance < stop:
        return [0, 0]
    return [(b[0] - a[0]) / distance, (b[1] - a[1]) / distance]


class Bot:
    name = "Corner Runner v3"
    loot_range = 160
    staging_weight = 0.8
    camp_after = 100
    cover_hp = 0.48
    farm_cap = 16
    loot_memory = 65
    avoid_radius = 60
    laser_bias = 4
    duel_range = 130

    def __init__(self, hello):
        self.map = Arena(hello["map"]["dir"])
        self.config = hello["config"]
        self.reach = self.config["loot"]["pickup_radius"]
        self.tracks = {}
        self.items = {}
        self.roof = None
        self.roof_retries = {}
        self.next_roof = 0
        self.route_key = None
        self.next_plan = 0
        self.path = []
        self.last_hp = None
        self.last_hit = -100
        self.attackers = {}
        self.crate = None
        self.perched = False
        self.climb = None
        self.escape_top = 0
        self.scan_target = None
        self.scan_time = -99
        self.salvage = None
        self.salvage_until = 0
        self.last_target = None
        self.previous_velocity = {}
        self.cube_memory = {}
        self.healing = False
        self.scanned = set()
        self.next_step = -1
        self.saved_step = None
        self.step_enemy = None
        self.withdraw_until = -1
        self.footing = None
        self.footing_at = -1
        self.jet_until = -1

    def follow(self, pos, key, now, plan):
        if key != self.route_key or now >= self.next_plan:
            self.path = plan()
            self.route_key = key
            self.next_plan = now + 1.1
        while (
            self.path
            and horizontal(pos, self.path[0]) < 2.6
            and (len(self.path[0]) == 2 or self.path[0][2] <= pos[2] + 1.25)
        ):
            self.path.pop(0)
        if self.path and len(self.path[0]) == 3:
            self.climb = self.path[0][2]
        return toward(pos, self.path[0]) if self.path else [0, 0]

    def pick_perch(self, pos, zone, now):
        center = zone["next_center"]
        radius = zone["next_radius"]
        if radius < 20:
            return None
        best, cost = None, math.inf
        for roof in self.map.roofs:
            entry, _, back, top = roof
            launch = self.map.points[entry]
            distance = horizontal(pos, launch)
            if distance > 210 or self.roof_retries.get(entry, 0) > now:
                continue
            offset = horizontal(self.map.points[back], center)
            if offset > radius - 5:
                continue
            rise = top - self.map.floor[entry]
            rank = (
                distance + self.staging_weight * offset - 1.6 * rise - 3 * min(6, self.map.roof_depth[back])
            )
            if rank < cost:
                best, cost = roof, rank
        return best

    def duel_move(self, obs, enemy):
        me = obs["self"]
        p, q = me["pos"], enemy["pos"]
        d = max(1, horizontal(p, q))
        nx, ny = (q[0] - p[0]) / d, (q[1] - p[1]) / d
        secondary = me["weapons"][1]
        arc = secondary and secondary["kind"] == "lightning" and me["energy"] > 10
        desired = 18 if arc else self.duel_range
        radial = max(-1, min(2, (d - desired) / 12))
        side = 1 if int(obs["t"] / 1.35) % 2 else -1
        dx, dy = radial * nx - side * ny, radial * ny + side * nx
        zone = obs["zone"]
        best, rank = [0, 0], -math.inf
        for angle in (0, 0.6, -0.6, 1.2, -1.2, 1.8, -1.8, math.pi):
            cs, sn = math.cos(angle), math.sin(angle)
            tx, ty = dx * cs - dy * sn, dx * sn + dy * cs
            length = max(0.01, math.hypot(tx, ty))
            tx, ty = tx / length, ty / length
            end = (p[0] + tx * 12, p[1] + ty * 12)
            mid = (p[0] + tx * 5, p[1] + ty * 5)
            if not self.map.edges[self.map.cell(end)] or not self.map.edges[self.map.cell(mid)]:
                continue
            value = math.cos(angle) - max(0, horizontal(end, zone["center"]) - zone["radius"] + 4)
            for other, seen in self.tracks.values():
                if other["id"] != enemy["id"] and obs["t"] - seen < 3:
                    value -= max(0, self.avoid_radius - horizontal(end, other["pos"])) * 0.19
            if value > rank:
                best, rank = [tx, ty], value
        escaping = d < desired * 0.72
        return best, (escaping or enemy.get("charging")) and me["energy"] > 28, False

    def risk_to_bystander(self, pos, yaw, pitch, distance, target):
        dx, dy, dz = math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)
        for other, _ in self.tracks.values():
            if other["id"] == target or other["id"] in self.attackers:
                continue
            q = other["pos"]
            x, y, z = q[0] - pos[0], q[1] - pos[1], q[2] + 4.5 - pos[2]
            along = x * dx + y * dy + z * dz
            if (
                0 < along < distance
                and (x - dx * along) ** 2 + (y - dy * along) ** 2 + (z - dz * along) ** 2 < 36
            ):
                return True
        return False

    def ring_move(self, obs, targets):
        me, zone, t = obs["self"], obs["zone"], obs["t"]
        p = me["pos"]
        foe, q = targets[0]
        others = [other for other, seen in self.tracks.values() if other["id"] != foe["id"] and t - seen < 5]
        if self.saved_step and self.step_enemy == foe["id"] and t < self.next_step:
            return self.saved_step
        best, score = None, -math.inf
        desired = 31 if me["weapons"][1] and me["weapons"][1]["kind"] == "lightning" else self.duel_range
        if desired > 50 and "lightning" not in foe["weapons"] and me["cubes"] < 9:
            if len(others) <= 1 and me["hp"] > 1.1 * foe.get("hp", 1400):
                desired = 28 if foe.get("hp", 1400) < 500 else 70
        for i in range(18):
            a = i * math.tau / 18
            dx, dy = math.cos(a), math.sin(a)
            point = (p[0] + 22 * dx, p[1] + 22 * dy)
            n = self.map.cell(point)
            if not self.map.edges[n]:
                continue
            distance = horizontal(point, q)
            cost = 0.35 * abs(desired - distance)
            for other in others:
                d = horizontal(point, other["pos"])
                cost += max(0, 120 - d) * 1.1
            cost += max(0, horizontal(point, zone["center"]) - zone["radius"] + 12) * 3
            if not self.map.shot_clear((p[0], p[1], p[2] + 3), (*point, self.map.floor[n] + 3)):
                cost += 20
            d0 = max(1, horizontal(p, q))
            tangent = ((p[0] - q[0]) * dy - (p[1] - q[1]) * dx) / d0
            cost -= tangent * (1 if int(t / 1.25) % 2 else -1) * 3.4
            if -cost > score:
                score, best = -cost, [dx, dy]
        if best is None:
            return self.duel_move(obs, foe)
        self.step_enemy = foe["id"]
        self.next_step = t + 0.35
        self.saved_step = best, me["energy"] > 30 and horizontal(p, q) < 0.8 * desired, False
        return self.saved_step

    def scout(self, obs):
        now, p, zone = obs["t"], obs["self"]["pos"], obs["zone"]
        if not self.scan_target or now - self.scan_time > 6 or horizontal(p, self.scan_target) < 10:
            angle = (self.config["match"]["mechs"] * 0.7 + now * 1.73 + p[0] * 0.009) % math.tau
            cx, cy = zone["next_center"]
            goals = []
            for i in range(12):
                a = angle + math.tau * i / 12
                end = (p[0] + 65 * math.cos(a), p[1] + 65 * math.sin(a))
                c = self.map.cell(end)
                if self.map.edges[c]:
                    nearest = min(
                        (horizontal(end, other["pos"]) for other, _ in self.tracks.values()), default=170
                    )
                    visited = (round(end[0] / 35), round(end[1] / 35)) in self.scanned
                    goals.append(
                        (
                            horizontal(end, (cx, cy)) * 0.08
                            + i * 0.8
                            + 55 * visited
                            + max(0, 155 - nearest) * 1.4,
                            self.map.points[c],
                        )
                    )
            self.scan_target = min(goals)[1] if goals else zone["next_center"]
            self.scan_time = now
        return self.follow(p, ("scout", *self.scan_target), now, lambda: self.map.travel(p, self.scan_target))

    def farming_move(self, obs, obj):
        me, q = obs["self"], obj["pos"]
        p = me["pos"]
        is_drone = obj.get("kind") == "npc"
        aim_height = self.config["npc"]["height"] * 0.5 if is_drone else 1.3
        drop = p[2] + me["stats"]["muzzle_height"] - (q[2] + aim_height)
        # Leave a few meters for braking before the target passes below the gun's pitch limit.
        spacing = max(10, drop / max(0.1, math.tan(-me["stats"]["min_pitch"])) + 5)
        distance = horizontal(p, q)
        if distance < spacing - 2:
            away = toward(q, p, 0.01)
            if not any(away):
                away = [math.cos(me["aim"][0]), math.sin(me["aim"][0])]
            return away, False, False
        if distance < spacing + 4:
            return [0, 0], False, False
        if distance < 30 and self.map.shot_clear((*p[:2], p[2] + 2), (*q[:2], q[2] + 2)):
            return toward(p, q), False, False
        key = ("drone" if is_drone else "box", obj["id"])
        return self.follow(p, key, obs["t"], lambda: self.map.travel(p, q)), False, False

    def movement(self, obs, eyes, exposed, health, targets):
        me, zone, now = obs["self"], obs["zone"], obs["t"]
        p = me["pos"]
        second = me["weapons"][1]
        speed = me["stats"]["walk_speed"]
        center, radius = zone["next_center"], zone["next_radius"]
        remaining = max(0, zone["shrink_end"] - now)
        outward = horizontal(p, center) - max(0, radius - 10)
        rotate = not me["in_zone"] or outward > 0 and outward / speed * 1.6 + 12 >= remaining
        if rotate:
            self.roof = None
            self.perched = False
            move = self.follow(p, ("zone", *center), now, lambda: self.map.travel(p, center))
            if not any(move):
                move = toward(p, center)
            return move, any(move) and me["grounded"] and me["energy"] > 12, False

        roof = self.roof
        on_roof = (
            roof
            and p[2] >= roof[3] - 1.3
            and abs(p[2] - roof[3]) < 4
            and self.map.top[self.map.cell(p)] >= roof[3] - 1.3
        )
        if (
            roof
            and me["grounded"]
            and abs(p[2] - roof[3]) < 2
            and p[2] - self.map.floor[self.map.cell(p)] > 6
        ):
            self.perched = True
        if self.perched and roof and p[2] >= roof[3] - 3:
            on_roof = True
        # A visible solo supply drop gives a complete reset and a guaranteed upgrade.
        if not on_roof and not targets:
            for drop in obs["drops"]:
                q = drop["pos"]
                d = horizontal(p, q)
                if (
                    d < (125 if health < 0.75 else 65)
                    and drop["lands_in"] < d / speed + 3
                    and horizontal(q, center) < max(10, radius - 4)
                    and all(horizontal(eye, q) > 50 for _, eye in eyes)
                    and drop.get("holder") in (None, me["id"])
                ):
                    if d < drop["radius"] - 0.8:
                        return [0, 0], False, False
                    return (
                        self.follow(p, ("drop", drop["id"]), now, lambda: self.map.travel(p, q)),
                        me["energy"] > 45,
                        False,
                    )
        if self.healing and eyes and not on_roof and health < 0.9:
            pts = [eye for _, eye in eyes]
            key = ("recover", *[i for i, _ in eyes], len(exposed))
            move = self.follow(
                p, key, now, lambda: self.map.refuge(p, zone, pts, me["stats"]["eye_height"] + 1)
            )
            if any(move) or not exposed:
                return move, any(move) and me["energy"] > 20, False
        allowed = ("laser", "lightning")
        # A reachable secondary is worth a short opening detour, before committing to a perch.
        if not on_roof and (not second or second["kind"] != "laser") and health > 0.55:
            candidates = []
            for item, seen in self.items.values():
                q = item["pos"]
                distance = horizontal(p, q)
                if abs(p[2] - q[2]) > 13 or item["kind"] not in allowed:
                    continue
                if second and item["kind"] != "laser":
                    continue
                limit = 50 if targets else self.loot_range
                if (
                    distance <= limit
                    and not any(
                        horizontal(q, foe["pos"]) < 23 and horizontal(q, foe["pos"]) < distance * 0.75
                        for foe, _ in exposed
                    )
                    and horizontal(q, zone["center"]) < zone["radius"] - 5
                ):
                    priority = (
                        distance * (1 if item["kind"] == "laser" else self.laser_bias)
                        + min(15, now - seen) * 0.8
                    )
                    candidates.append((priority, item["id"], q))
            if candidates:
                _, ident, q = min(candidates)
                move = self.follow(p, ("loot", ident), now, lambda: self.map.travel(p, q))
                if horizontal(p, q) < 10:
                    move = toward(p, q, self.reach * 0.6)
                if any(move):
                    return move, me["energy"] > 52, False

        fresh_cube = None
        if not on_roof and me["cubes"] < 14 and health > 0.28:
            options = [
                (horizontal(p, c["pos"]), id, c["pos"])
                for id, (c, _) in self.cube_memory.items()
                if abs(p[2] - c["pos"][2]) <= 4 and horizontal(p, c["pos"]) < 85
            ]
            if options:
                _, _, fresh_cube = min(options)
            elif self.salvage and now < self.salvage_until and abs(self.salvage[2] - p[2]) < 4:
                fresh_cube = self.salvage
            if fresh_cube and any(
                horizontal(foe["pos"], fresh_cube) < (65 if "lightning" in foe["weapons"] else 36)
                and horizontal(p, fresh_cube) > 8
                and horizontal(foe["pos"], fresh_cube) < horizontal(foe["pos"], p)
                for foe, _ in exposed
            ):
                fresh_cube = None
            if fresh_cube and (
                not targets
                or horizontal(p, fresh_cube) < 35
                or min(horizontal(p, q) for _, q in targets) > 58
            ):
                if self.salvage and fresh_cube == self.salvage and horizontal(p, fresh_cube) < 4:
                    self.salvage = None
                if horizontal(p, fresh_cube) < 12:
                    return toward(p, fresh_cube, 1), False, False
                move = self.follow(
                    p, ("salvage", *fresh_cube[:2]), now, lambda: self.map.travel(p, fresh_cube)
                )
                if any(move):
                    return move, me["energy"] > 45, False
        if not on_roof and not targets and health > 0.56 and me["cubes"] < 10:
            drones = [
                n
                for n in obs["mechs"]
                if n["kind"] == "npc"
                and horizontal(p, n["pos"]) < (100 if me["cubes"] < 3 else 45)
                and self.map.clear((*p[:2], p[2] + 7), (*n["pos"][:2], n["pos"][2] + 1.8))
            ]
            if drones:
                drone = min(drones, key=lambda n: horizontal(p, n["pos"]))
                self.crate = drone
                return self.farming_move(obs, drone)
        if targets and not on_roof and health > 0.22 and len(targets) < 4 and now >= self.withdraw_until:
            return self.ring_move(obs, targets)
        self.crate = None
        if not on_roof and not targets and me["cubes"] < self.farm_cap:
            nearby = [
                item
                for item in obs["cubes"]
                if abs(item["pos"][2] - p[2]) < 4 and horizontal(item["pos"], p) < 65
            ]
            if nearby:
                cube = min(nearby, key=lambda item: horizontal(p, item["pos"]))
                q = cube["pos"]
                if horizontal(q, p) < 10:
                    return toward(p, q, 1), False, False
                move = self.follow(p, ("cube", cube["id"]), now, lambda: self.map.travel(p, q))
                if any(move):
                    return move, me["energy"] > 65, False
            if health > 0.65 and me["cubes"] < self.farm_cap:
                crates = [
                    c for c in obs["crates"] if horizontal(c["pos"], p) < 60 and abs(c["pos"][2] - p[2]) < 4
                ]
                if crates:
                    box = min(crates, key=lambda c: horizontal(c["pos"], p))
                    if self.map.clear((*p[:2], p[2] + 7), (*box["pos"][:2], box["pos"][2] + 1.4)):
                        self.crate = box
                        return self.farming_move(obs, box)

        if not roof and not targets and health > 0.66 and now < self.camp_after:
            return self.scout(obs), me["energy"] > 72, False
        if not roof and now >= self.next_roof and (now >= self.camp_after or health < 0.58):
            roof = self.pick_perch(p, zone, now)
            self.roof = roof
            self.perched = False
            self.next_roof = now + 3
            self.roof_start = now
        if roof:
            entry, rim, back, top = roof
            launch, edge, interior = (self.map.points[k] for k in (entry, rim, back))
            if on_roof:
                points = [eye for _, eye in eyes]
                key = ("perch", entry, *[i for i, _ in eyes])
                return (
                    self.follow(
                        p,
                        key,
                        now,
                        lambda: self.map.roof_path(p, roof, points, me["stats"]["eye_height"] + 1),
                    ),
                    False,
                    False,
                )
            if now - self.roof_start < 22 and horizontal(interior, center) < radius:
                if horizontal(p, launch) > 5 and me["grounded"]:
                    move = self.follow(p, ("roof", entry), now, lambda: self.map.travel(p, launch))
                    if any(move):
                        return move, False, False
                if p[2] >= top - 0.3 and not me["grounded"]:
                    return toward(p, interior), False, False
                if horizontal(p, launch) < 12:
                    if me["grounded"] and me["energy"] < 20 + 1.7 * max(0, top - p[2]):
                        return [0, 0], False, False
                    return toward(p, edge), True, me["grounded"]
            self.perched = False
            self.roof_retries[entry] = now + 30
            self.roof = None

        # Reevaluate whenever a second enemy acquires sight or a different one appears.
        key = ("cover", *[e[0] for e in eyes], *center, len(exposed))
        points = [e[1] for e in eyes]
        move = self.follow(
            p, key, now, lambda: self.map.refuge(p, zone, points, me["stats"]["eye_height"] + 1)
        )
        return move, bool(exposed) and any(move) and me["energy"] > 24, False

    def act(self, obs):
        now, me = obs["t"], obs["self"]
        pos = me["pos"]
        health = me["hp"] / me["max_hp"]
        if self.last_hp is not None and me["hp"] < self.last_hp:
            self.last_hit = now
            if health < 0.45:
                self.withdraw_until = now + self.config["mech"]["regen_delay"] + 2
        self.last_hp = me["hp"]
        if health < self.cover_hp and now - self.last_hit < 2:
            self.healing = True
        if health > 0.94:
            self.healing = False
        self.scanned.add((round(pos[0] / 35), round(pos[1] / 35)))
        for enemy in obs["mechs"]:
            if enemy["kind"] == "mech":
                self.tracks[enemy["id"]] = enemy, now
        self.tracks = {i: t for i, t in self.tracks.items() if now - t[1] < 7}
        for e in obs["events"]:
            if e["type"] == "damaged" and e.get("by") is not None:
                self.attackers[e["by"]] = now
            if e["type"] == "hit" and e.get("target") in self.tracks:
                self.attackers[e["target"]] = now
            if e["type"] == "kill":
                track = self.tracks.pop(e["target"], None)
                if track:
                    self.salvage = track[0]["pos"]
                    self.salvage_until = now + 16
            if e["type"] in ("took", "take_failed"):
                self.items.pop(e["id"], None)
        self.cube_memory.update({c["id"]: (c, now) for c in obs["cubes"]})
        self.cube_memory = {
            i: pair
            for i, pair in self.cube_memory.items()
            if now - pair[1] < 6 and (pair[1] == now or horizontal(pos, pair[0]["pos"]) > 10)
        }
        visible_items = {item["id"] for item in obs["pickups"]}
        self.items = {
            i: pair
            for i, pair in self.items.items()
            if i in visible_items
            or horizontal(pos, pair[0]["pos"]) > 12
            or abs(pos[2] - pair[0]["pos"][2]) > 4
        }
        for item in obs["pickups"]:
            self.items[item["id"]] = item, now
        self.items = {i: pair for i, pair in self.items.items() if now - pair[1] < self.loot_memory}

        muzzle = (*pos[:2], pos[2] + me["stats"]["muzzle_height"])
        eyes, exposed = [], []
        for enemy, seen in sorted(self.tracks.values(), key=lambda pair: horizontal(pair[0]["pos"], pos)):
            q = enemy["pos"]
            scale = 1 + self.config["cubes"]["size_per_cube"] * enemy.get("cubes", 0)
            eye = (*q[:2], q[2] + self.config["mech"]["eye_height"] * scale)
            eyes.append((enemy["id"], eye))
            center = (*q[:2], q[2] + self.config["mech"]["height"] * scale * 0.5)
            if seen == now and self.map.shot_clear(muzzle, center):
                exposed.append((enemy, center))
        second = me["weapons"][1]

        # Look for the active pursuer before committing to a fight.
        def pressing(pair):
            foe, q = pair
            d = horizontal(pos, q)
            yaw = math.atan2(pos[1] - q[1], pos[0] - q[0])
            aimed = abs(math.remainder(yaw - foe["aim"][0], math.tau)) < 0.38
            approaching = foe["vel"][0] * math.cos(yaw) + foe["vel"][1] * math.sin(yaw) > 3
            retaliate = now - self.attackers.get(foe["id"], -99) < 10
            return retaliate or d < 30 or (aimed and approaching and d < 55)

        targets = [pair for pair in exposed if pressing(pair)]
        if not targets and second and health > 0.87:
            targets = [
                pair for pair in exposed if pair[0].get("hp", 1400) < 330 and horizontal(pos, pair[1]) < 160
            ]
        if not targets and second and not self.healing and health > 0.72:
            opportunities = []
            for foe, q in exposed:
                distance = horizontal(pos, q)
                if distance > 125:
                    continue
                facing = math.cos(math.atan2(pos[1] - q[1], pos[0] - q[0]) - foe["aim"][0])
                vulnerable = foe.get("hp", 1400) < 530 or (
                    second["kind"] == "laser" and ("mortar" in foe["weapons"] or facing < -0.35)
                )
                isolated = all(
                    other["id"] == foe["id"] or horizontal(q, other["pos"]) > 70
                    for other, _ in self.tracks.values()
                )
                if vulnerable and isolated:
                    opportunities.append((foe, q))
            targets = opportunities

        def removal_cost(pair):
            enemy, point = pair
            dist = horizontal(pos, point)
            direction = math.atan2(pos[1] - point[1], pos[0] - point[0])
            rear = abs(math.remainder(direction - enemy["aim"][0], math.tau)) > math.pi / 2
            efficiency = 1 + 0.4 * rear
            if second and second["kind"] == "laser" and "mortar" in enemy["weapons"]:
                efficiency += 0.45
            return (
                enemy.get("hp", 1400) / efficiency
                + 2 * dist
                - (165 if enemy["id"] == self.last_target else 0)
            )

        targets.sort(key=removal_cost)
        self.last_target = targets[0][0]["id"] if targets else None
        if self.healing and now - self.last_hit > 1.1:
            targets = [
                pair
                for pair in targets
                if horizontal(pos, pair[1]) < 30 or pair[0].get("hp", 1400) < me["hp"] * 0.42
            ]
        self.climb = None
        self.crate = None
        move, boost, jump = self.movement(obs, eyes[:3], exposed, health, targets)
        if now - self.footing_at > 0.85:
            if (
                me["grounded"]
                and any(move)
                and self.footing
                and horizontal(self.footing, pos) < 1
                and not self.perched
                and not jump
                and me["energy"] > 40
            ):
                probe = self.map.cell((pos[0] + move[0] * 7, pos[1] + move[1] * 7))
                self.escape_top = max(pos[2] + 5, min(pos[2] + 32, self.map.top[probe] + 1))
                self.jet_until = now + min(4.4, (self.escape_top - pos[2]) / 9 + 0.5)
            self.footing, self.footing_at = pos[:2], now
        if (
            any(move)
            and not self.perched
            and now < self.jet_until
            and pos[2] < self.escape_top
            and me["energy"] > 5
        ):
            jump, boost = me["grounded"], True
        if self.climb is not None and self.climb > pos[2] + 1.25:
            reserve = (self.climb - pos[2]) * 1.7 + 6
            if me["grounded"] and me["energy"] < reserve:
                move, boost, jump = [0, 0], False, False
            else:
                boost, jump = True, me["grounded"]
        gun, second = me["weapons"]
        act = {"tick": obs["tick"], "move": move, "boost": boost, "jump": jump}
        reachable = [
            i
            for i in obs["pickups"]
            if horizontal(i["pos"], pos) <= self.reach
            and abs(i["pos"][2] - pos[2]) <= 4
            and i["kind"] in (("laser", "lightning"))
        ]
        for item in sorted(reachable, key=lambda i: i["kind"] != "laser"):
            if not second or item["kind"] == "laser" and second["kind"] != "laser":
                act["take"] = item["id"]
                if second:
                    act["drop"] = 1
                break
        offer = obs.get("offer")
        if offer:
            ranks = [
                "plating",
                "armor",
                "nanites",
                "laser_damage",
                "gun_damage",
                "gun_mag",
                "gun_rate",
                "jets",
            ]
            act["pick"] = min(
                range(len(offer["choices"])),
                key=lambda i: (
                    ranks.index(offer["choices"][i]["id"])
                    if offer["choices"][i]["id"] in ranks
                    else len(ranks)
                ),
            )
        if not self.crate and not targets and not self.healing and me["cubes"] < 10:
            # The torso can track a crate or drone independently of movement.
            nearby = []
            for obj in (*obs["crates"], *obs["mechs"]):
                if obj.get("kind") == "mech":
                    continue
                q = obj["pos"]
                d = horizontal(pos, q)
                if d > (80 if obj.get("kind") == "npc" else 55):
                    continue
                if obj.get("kind") == "npc" and d > 42 and now - self.attackers.get(obj["id"], -99) > 2:
                    continue
                if self.map.shot_clear(muzzle, (*q[:2], q[2] + 1.5)):
                    angle = math.atan2(q[1] - pos[1], q[0] - pos[0])
                    nearby.append(
                        (d + 12 * abs(math.remainder(angle - me["aim"][0], math.tau)), obj["id"], obj)
                    )
            if nearby:
                self.crate = min(nearby)[2]
        if targets:
            enemy, target = targets[0]
            velocity = enemy["vel"]
            distance = math.dist(muzzle, target)
            laser = second and second["kind"] == "laser"
            charging = laser and second.get("charge", 0) > 0
            frame = 1 / self.config["match"]["tick_hz"]
            threshold = second["stats"]["charge"] if laser else math.inf
            if laser:
                minimum = second["stats"].get("min_frac", 0.35)
                cube_bonus = 1 + self.config["cubes"]["damage_per_cube"] * min(
                    me["cubes"], self.config["cubes"]["stat_cap"]
                )
                damage = second["stats"]["damage"] * cube_bonus * (1.6 if "mortar" in enemy["weapons"] else 1)
                needed = (1.15 * enemy.get("hp", 1400) / damage - minimum) / (1 - minimum)
                threshold *= min(1, max(0.28, needed))
            beam_aim = charging and second["charge"] + 0.10 >= threshold
            lead = frame if beam_aim else frame + distance / gun["stats"]["speed"]
            prev = self.previous_velocity.get(enemy["id"])
            previous = prev[1] if prev and 0 < now - prev[0] < 0.15 else None
            self.previous_velocity[enemy["id"]] = now, velocity[:]
            tx, ty = (
                (lead * velocity[0], lead * velocity[1]) if beam_aim else offset(velocity, previous, lead)
            )
            dx = target[0] + tx - muzzle[0] - me["vel"][0] * frame
            dy = target[1] + ty - muzzle[1] - me["vel"][1] * frame
            dz = target[2] + velocity[2] * min(0.25, lead) - muzzle[2] - me["vel"][2] * frame
            yaw, pitch = math.atan2(dy, dx), math.atan2(dz, math.hypot(dx, dy))
            act["aim"] = [yaw, pitch]
            aligned = (
                abs(math.remainder(yaw - me["aim"][0], math.tau)) < 0.12 and abs(pitch - me["aim"][1]) < 0.11
            )
            yaw_error = max(
                0, abs(math.remainder(yaw - me["aim"][0], math.tau)) - 0.05 * me["stats"]["turn_rate"]
            )
            pitch_error = max(0, abs(pitch - me["aim"][1]) - 0.05 * me["stats"]["pitch_rate"])
            beam_aligned = yaw_error * distance < 1.8 and pitch_error * distance < 3.5
            fire_primary = aligned and distance < gun["stats"]["range"]
            fire_secondary = False
            if laser and distance < second["stats"]["range"]:
                fire_secondary = not (charging and second["charge"] >= threshold and beam_aligned)
            elif second:
                fire_secondary = aligned and distance < second["stats"]["range"] and me["energy"] > 8
            if self.risk_to_bystander(
                muzzle, *act["aim"], min(gun["stats"]["range"], distance + 12), enemy["id"]
            ):
                fire_primary = False
                if charging:
                    fire_secondary = True
                elif not laser:
                    fire_secondary = False
            act["fire"] = [fire_primary, fire_secondary]
        elif self.crate and health > 0.6:
            box = self.crate
            is_drone = box.get("kind") == "npc"
            v = box.get("vel", (0, 0, 0))
            q = box["pos"]
            distance = horizontal(pos, q)
            laser = second and second["kind"] == "laser"
            lock_laser = laser and second.get("charge", 0) > 0.45
            lead = 0.05 if lock_laser else 0.05 + distance / gun["stats"]["speed"]
            dx = q[0] + v[0] * lead - muzzle[0]
            dy = q[1] + v[1] * lead - muzzle[1]
            dz = q[2] + (1.75 if is_drone else 1.3) - muzzle[2]
            yaw, pitch = math.atan2(dy, dx), math.atan2(dz, math.hypot(dx, dy))
            aligned = (
                abs(math.remainder(yaw - me["aim"][0], math.tau)) < 0.07 and abs(pitch - me["aim"][1]) < 0.07
            )
            alt = False
            if laser and (is_drone or gun["ammo"] < 6):
                alt = not (second.get("charge", 0) >= second["stats"]["charge"] and aligned)
            elif second and second["kind"] == "lightning" and distance < 40 and me["energy"] > 30:
                alt = aligned
            act["aim"] = [yaw, pitch]
            act["fire"] = [aligned, alt]
        else:
            if not second and now < 3 and now - self.last_hit > 1:
                yaw = math.remainder(now * 3.6 + obs["self"]["id"] * 0.3, math.tau)
            elif eyes and (now - self.last_hit < 3 or self.perched):
                q = eyes[0][1]
                yaw = math.atan2(q[1] - pos[1], q[0] - pos[0])
            else:
                bearings = [
                    s
                    for s in obs["sounds"]
                    if s["kind"] in ("gun", "laser_charge", "lightning", "mortar") and s["dist"] == "near"
                ]
                yaw = bearings[0]["bearing"] if bearings else math.remainder(2.8 * now, math.tau)
            act["aim"] = [yaw, 0]
            act["reload"] = gun["ammo"] < 0.6 * gun["stats"]["mag"]
        # Close a gap under foliage at a quiet walk. A nearby pursuer still requires solid cover.
        far_enough = (
            not eyes or min(horizontal(pos, q) for _, q in eyes) > self.config["vision"]["near_range"] + 32
        )
        leafy = self.map.foliage[self.map.cell(pos)] > 0.8
        if (
            leafy
            and far_enough
            and not exposed
            and now - self.last_hit > 5
            and me["in_zone"]
            and self.route_key
            and self.route_key[0] in ("cover", "recover", "perch")
        ):
            fraction = min(1, 0.9 * self.config["sound"]["step_speed"] / me["stats"]["walk_speed"])
            act["move"] = [fraction * u for u in act["move"]]
            act["boost"] = False
        return act


if __name__ == "__main__":
    mf.run(Bot)
