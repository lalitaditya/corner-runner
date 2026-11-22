"""Coarse ground navigation on the campus map supplied at match start."""

import heapq
import json
import math
from array import array
from collections import deque
from pathlib import Path


class Arena:
    step = 6

    def __init__(self, directory):
        folder = Path(directory) / "v2"
        world = json.loads((folder / "world.json").read_bytes())
        terrain = world["terrain"]
        heights = array("h", (folder / "terrain.i16").read_bytes())
        bounds = world["bounds"]
        self.x0 = math.ceil(bounds["minX"]) + 3
        self.y0 = math.ceil(bounds["minY"]) + 3
        self.width = int((bounds["maxX"] - self.x0 - 3) / self.step) + 1
        height = int((bounds["maxY"] - self.y0 - 3) / self.step) + 1
        self.points = [
            (self.x0 + i * self.step, self.y0 + j * self.step)
            for j in range(height)
            for i in range(self.width)
        ]
        self.floor = []
        for x, y in self.points:
            i = round((x - terrain["minX"]) / terrain["step"])
            j = round((y - terrain["minY"]) / terrain["step"])
            self.floor.append(heights[j * terrain["nx"] + i] * terrain["scale"])
        # A finer collision raster resolves narrow gaps and roof edges when aiming.
        self.ray_x = terrain["minX"]
        self.ray_y = terrain["minY"]
        self.ray_width = (terrain["nx"] + 1) // 2
        self.ray_height = (terrain["ny"] + 1) // 2
        self.ray_step = terrain["step"] * 2
        self.ray_floor = array(
            "f",
            (
                heights[j * 2 * terrain["nx"] + i * 2] * terrain["scale"]
                for j in range(self.ray_height)
                for i in range(self.ray_width)
            ),
        )
        self.ray_base = array("f", [1e6]) * len(self.ray_floor)
        self.ray_top = array("f", [-1e6]) * len(self.ray_floor)
        for solid in world["prisms"]:
            rings = [solid["ring"], *solid["holes"]]
            ring = rings[0]
            first = max(0, math.ceil((min(ring[1::2]) - self.ray_y) / self.ray_step))
            last = min(self.ray_height - 1, math.floor((max(ring[1::2]) - self.ray_y) / self.ray_step))
            for j in range(first, last + 1):
                y = self.ray_y + j * self.ray_step
                cuts = []
                for loop in rings:
                    ax, ay = loop[-2:]
                    for bx, by in zip(loop[::2], loop[1::2]):
                        if (ay > y) != (by > y):
                            cuts.append(ax + (bx - ax) * (y - ay) / (by - ay))
                        ax, ay = bx, by
                cuts.sort()
                for left, right in zip(cuts[::2], cuts[1::2]):
                    lo = max(0, math.ceil((left - self.ray_x) / self.ray_step))
                    hi = min(self.ray_width - 1, math.floor((right - self.ray_x) / self.ray_step))
                    for k in range(j * self.ray_width + lo, j * self.ray_width + hi + 1):
                        self.ray_base[k] = min(self.ray_base[k], solid["base"])
                        self.ray_top[k] = max(self.ray_top[k], solid["top"])
        self.top = self.floor.copy()
        blocked = set()
        for solid in world["prisms"]:
            rings = [solid["ring"], *solid["holes"]]
            ymin, ymax = min(rings[0][1::2]), max(rings[0][1::2])
            for j in range(
                max(0, math.ceil((ymin - self.y0) / self.step)),
                min(height, math.floor((ymax - self.y0) / self.step) + 1),
            ):
                y = self.y0 + j * self.step
                cuts = []
                for ring in rings:
                    ax, ay = ring[-2:]
                    for bx, by in zip(ring[::2], ring[1::2]):
                        if (ay > y) != (by > y):
                            cuts.append(ax + (y - ay) * (bx - ax) / (by - ay))
                        ax, ay = bx, by
                cuts.sort()
                for left, right in zip(cuts[::2], cuts[1::2]):
                    for i in range(
                        max(0, math.ceil((left - self.x0) / self.step)),
                        min(self.width, math.floor((right - self.x0) / self.step) + 1),
                    ):
                        n = j * self.width + i
                        if solid["base"] < self.floor[n] + 9 and solid["top"] > self.floor[n] + 1.2:
                            blocked.add(n)
                            self.top[n] = max(self.top[n], solid["top"])
        self.edges = [[] for _ in self.points]
        self.cover = set()
        for n in range(len(self.points)):
            if n in blocked:
                continue
            i, j = n % self.width, n // self.width
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if not (0 <= i + di < self.width and 0 <= j + dj < height):
                    continue
                m = n + di + dj * self.width
                if m in blocked:
                    if self.top[m] > self.floor[n] + 8:
                        self.cover.add(n)
                elif abs(self.floor[m] - self.floor[n]) < self.step:
                    self.edges[n].append(m)

        # Keep map routes a mech-width from walls when room permits.
        self.near_wall = set(self.cover)
        self.roof_depth = [0] * len(self.points)
        fringe = deque()
        for n in blocked:
            if any(
                not 0 <= k < len(self.top) or abs(self.top[n] - self.top[k]) > 1.2
                for k in (n - 1, n + 1, n - self.width, n + self.width)
            ):
                self.roof_depth[n] = 1
                fringe.append(n)
        while fringe:
            n = fringe.popleft()
            for k in (n - 1, n + 1, n - self.width, n + self.width):
                if 0 <= k < len(self.top) and k in blocked and not self.roof_depth[k]:
                    self.roof_depth[k] = self.roof_depth[n] + 1
                    fringe.append(k)
        self.roofs = []
        for n in self.cover:
            for off in (1, -1, self.width, -self.width):
                rim, inside, back = n + off, n + 2 * off, n + 3 * off
                if not all(0 <= k < len(self.points) for k in (rim, inside, back)):
                    continue
                rise = self.top[rim] - self.floor[n]
                if 11 <= rise <= 40 and all(abs(self.top[k] - self.top[rim]) < 1.2 for k in (inside, back)):
                    self.roofs.append((n, inside, back, self.top[rim]))

        self.foliage = [0.0] * len(self.points)
        trees = world["trees"]
        names, data = trees["fields"], trees["data"]
        for i in range(0, len(data), len(names)):
            t = dict(zip(names, data[i : i + len(names)]))
            radius, cx, cy = t["crownR"], t.get("crownX", t["x"]), t.get("crownY", t["y"])
            cell = self.cell((cx, cy))
            reach = math.ceil(radius / self.step)
            for dj in range(-reach, reach + 1):
                for di in range(-reach, reach + 1):
                    k = cell + di + dj * self.width
                    if not 0 <= k < len(self.points):
                        continue
                    x, y = self.points[k]
                    span = radius * radius - (x - cx) ** 2 - (y - cy) ** 2
                    h = self.top[k] + 7 - t["z"]
                    if span > 0 and t["crownBase"] < h < t["height"]:
                        self.foliage[k] += math.sqrt(span) * world["rules"]["canopyDensity"]
        self.surface = [[] for _ in self.points]
        for n in range(len(self.points)):
            x, y = n % self.width, n // self.width
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                if not (0 <= x + dx < self.width and 0 <= y + dy < height):
                    continue
                m = n + dx + dy * self.width
                climb = self.top[m] - self.top[n]
                if climb > 38:
                    continue
                if (
                    dx
                    and dy
                    and max(self.top[n + dx], self.top[n + dy * self.width])
                    > max(self.top[n], self.top[m]) + 1.2
                ):
                    continue
                cost = (
                    self.step * (1.42 if dx and dy else 1)
                    + max(0, climb - 1) * 3.8
                    + max(0, -climb - 6) * 0.4
                )
                if self.roof_depth[m] == 1 or m in self.near_wall:
                    cost += 2
                self.surface[n].append((m, cost))

    def travel(self, pos, goal):
        start, end = self.cell(pos), self.cell(goal)
        if start == end:
            return [(*goal[:2], self.top[end])]
        gx, gy = self.points[end]
        queue, parent, costs = [(0, 0, start)], {start: None}, {start: 0}
        while queue and len(parent) < 6500:
            _, cost, n = heapq.heappop(queue)
            if n == end:
                route = []
                while parent[n] is not None:
                    route.append((*self.points[n], self.top[n]))
                    n = parent[n]
                return route[::-1]
            if cost != costs[n]:
                continue
            for m, edge in self.surface[n]:
                new = cost + edge
                if new < costs.get(m, math.inf):
                    costs[m], parent[m] = new, n
                    x, y = self.points[m]
                    heapq.heappush(queue, (new + math.hypot(x - gx, y - gy), new, m))
        return []

    def cell(self, pos):
        i = max(0, min(self.width - 1, round((pos[0] - self.x0) / self.step)))
        j = max(0, min(len(self.points) // self.width - 1, round((pos[1] - self.y0) / self.step)))
        return j * self.width + i

    def clear(self, a, b):
        """Sample solid heights between two positions at torso height."""
        steps = max(1, math.ceil(math.dist(a[:2], b[:2]) / self.step))
        dx, dy, dz = ((end - start) / steps for start, end in zip(a, b))
        x, y, z = a
        for _ in range(1, steps):
            x, y, z = x + dx, y + dy, z + dz
            if self.top[self.cell((x, y))] >= z:
                return False
        return True

    def shot_clear(self, a, b):
        steps = max(1, math.ceil(math.dist(a[:2], b[:2]) / 2.8))
        x, y, z = a
        dx, dy, dz = ((q - u) / steps for u, q in zip(a, b))
        w = self.ray_width
        for _ in range(1, steps):
            x += dx
            y += dy
            z += dz
            i = round((x - self.ray_x) / self.ray_step)
            j = round((y - self.ray_y) / self.ray_step)
            if not (0 <= i < w and 0 <= j < self.ray_height):
                return False
            k = j * w + i
            if self.ray_floor[k] >= z or self.ray_base[k] <= z <= self.ray_top[k]:
                return False
        return True

    def walk_from(self, pos):
        n = self.cell(pos)
        if self.edges[n]:
            return n
        x, y = n % self.width, n // self.width
        ring = (
            n + dx + dy * self.width
            for dy in range(-3, 4)
            for dx in range(-3, 4)
            if 0 <= x + dx < self.width and 0 <= y + dy < len(self.points) // self.width
        )
        return min(
            (m for m in ring if self.edges[m]), key=lambda m: math.dist(pos[:2], self.points[m]), default=n
        )

    def trace(self, parent, n):
        path = []
        while parent[n] is not None:
            path.append(self.points[n])
            n = parent[n]
        return path[::-1]

    def roof_path(self, pos, roof, eyes, height):
        """Stay inside one connected roof and use its far edge to mask the mech's head."""
        _, rim, back, elevation = roof
        start = self.cell(pos)
        if abs(self.top[start] - elevation) > 1.3:
            return [self.points[rim]]
        parents = {start: None}
        queue = deque([(start, 0)])
        best, value = start, -math.inf
        while queue:
            cell, depth = queue.popleft()
            x, y = self.points[cell]
            head = (x, y, elevation + height)
            seen = sum(self.clear(head, eye) for eye in eyes)
            score = (
                -85 * seen
                + min(6, self.roof_depth[cell]) * 3
                - 0.06 * math.dist(self.points[cell], self.points[back])
            )
            score -= depth * 0.85
            if self.roof_depth[cell] < 2:
                score -= 17
            if score > value:
                best, value = cell, score
            if depth < 7:
                for m in (cell + 1, cell - 1, cell + self.width, cell - self.width):
                    if (
                        0 <= m < len(self.top)
                        and m not in parents
                        and abs(self.top[m] - elevation) < 1.2
                        and self.top[m] - self.floor[m] > 8
                    ):
                        parents[m] = cell
                        queue.append((m, depth + 1))
        return self.trace(parents, best)

    def refuge(self, pos, zone, threats, height):
        start = self.walk_from(pos)
        parents = {start: None}
        queue = deque([(start, 0)])
        best, best_score = start, -math.inf
        safe_radius = max(0, zone["next_radius"] - 15)
        while queue:
            cell, depth = queue.popleft()
            x, y = self.points[cell]
            score = -2 * max(0, math.dist((x, y), zone["next_center"]) - safe_radius)
            score -= 4 * max(0, math.dist((x, y), zone["center"]) - zone["radius"] + 2)
            score -= depth * 1.5
            distant = all(math.dist((x, y), eye[:2]) > 78 for eye in threats)
            leafy = self.foliage[cell] > 1.1 and distant
            if cell in self.cover or cell == start or leafy:
                if cell in self.cover:
                    score += 16
                    if all(math.dist((x, y), eye[:2]) > 65 for eye in threats):
                        score += min(3, self.foliage[cell])
                if leafy:
                    score += min(4, self.foliage[cell]) * 1.2
                # An opponent can spot a mech by its head even when its gun is screened.
                head = (x, y, self.floor[cell] + height)
                for eye in threats:
                    score -= 55 if self.clear(head, eye) else 0
                    score -= max(0, 52 - math.dist((x, y), eye[:2])) * 0.8
                if score > best_score:
                    best, best_score = cell, score
            elif not threats and score > best_score:
                best, best_score = cell, score
            if depth < 15:
                for m in self.edges[cell]:
                    if m not in parents:
                        parents[m] = cell
                        queue.append((m, depth + 1))
        return self.trace(parents, best)
