"""Arena geometry and navigation for the 2 m campus walk grid."""

from array import array
from hashlib import sha256
import json
import math
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from spatial import Geometry, Grid


class RoofAccess(SimpleNamespace):
    def __init__(self, Ground=0, Edge=0, Climb=0):
        super().__init__(Ground=Ground, Edge=Edge, Climb=Climb)


class Roof(SimpleNamespace):
    def __init__(
        self, ID=0, Z=0.0, Cells=None, Area=0.0, Height=0.0, Inner=0, InnerD=0.0, Access=None, CX=0.0, CY=0.0
    ):
        super().__init__(
            ID=ID,
            Z=Z,
            Cells=Cells or [],
            Area=Area,
            Height=Height,
            Inner=Inner,
            InnerD=InnerD,
            Access=Access or [],
            CX=CX,
            CY=CY,
        )


class Exposure:
    def __init__(self, nav, nx, ny, values):
        self.nav, self.Step, self.NX, self.NY, self.V = nav, 3, nx, ny, values

    def At(self, k):
        return self.V[(k // self.nav.NX // 3) * self.NX + k % self.nav.NX // 3]

    def Cell(self, i, j):
        return min(self.nav.NY - 1, j * 3 + 1) * self.nav.NX + min(self.nav.NX - 1, i * 3 + 1)


def _packed(cells):
    offsets, indices = array("i", [0]), array("i")
    for items in cells:
        indices.extend(items)
        offsets.append(len(indices))
    return offsets, indices


class World:
    def __init__(self, data, terrain, nav_cache):
        bounds, tr = data["bounds"], data["terrain"]
        self.MinX, self.MinY, self.MaxX, self.MaxY = (bounds[k] for k in ("minX", "minY", "maxX", "maxY"))
        self.TMinX, self.TMinY, self.TStep = tr["minX"], tr["minY"], tr.get("step") or 1
        self.NX, self.NY = tr["nx"], tr["ny"]
        self._cache = nav_cache
        self.gx, self.gy = math.floor(self.MinX / 8) * 8 - 8, math.floor(self.MinY / 8) * 8 - 8
        self.gnx, self.gny = (
            math.ceil((self.MaxX - self.gx) / 8) + 2,
            math.ceil((self.MaxY - self.gy) / 8) + 2,
        )
        self.Trees = data["trees"]
        rules = data["rules"]
        self.CanopyBlockT, self.CanopyDensity = rules["canopyBlockT"], rules["canopyDensity"]
        self._prisms = data["prisms"]
        edges, prisms, verts = array("d"), array("d"), array("d")
        holes, starts = array("i", [0]), array("i", [0])
        cells = self.gnx * self.gny
        edge_index, prism_index = [[] for _ in range(cells)], [[] for _ in range(cells)]

        def index_object(index, ident, xmin, ymin, xmax, ymax):
            x0 = max(0, min(self.gnx - 1, math.floor((xmin - self.gx) / 8)))
            x1 = max(0, min(self.gnx - 1, math.floor((xmax - self.gx) / 8)))
            y0 = max(0, min(self.gny - 1, math.floor((ymin - self.gy) / 8)))
            y1 = max(0, min(self.gny - 1, math.floor((ymax - self.gy) / 8)))
            for j in range(y0, y1 + 1):
                for i in range(x0, x1 + 1):
                    index[j * self.gnx + i].append(ident)

        for p in self._prisms:
            ring = p["ring"]
            base, top = p["base"], p["top"]
            if len(ring) < 6:
                continue
            xmin, ymin, xmax, ymax = min(ring[::2]), min(ring[1::2]), max(ring[::2]), max(ring[1::2])
            index_object(prism_index, len(prisms) // 6, xmin, ymin, xmax, ymax)
            prisms.extend((base, top, xmin, ymin, xmax, ymax))
            for loop in [ring, *p.get("holes", [])]:
                verts.extend(loop)
                starts.append(len(verts))
                if len(loop) < 6:
                    continue
                x0, y0 = loop[-2:]
                for x1, y1 in zip(loop[::2], loop[1::2]):
                    if x0 != x1 or y0 != y1:
                        index_object(
                            edge_index,
                            len(edges) // 6,
                            min(x0, x1) - 0.01,
                            min(y0, y1) - 0.01,
                            max(x0, x1) + 0.01,
                            max(y0, y1) + 0.01,
                        )
                        edges.extend((x0, y0, x1, y1, base, top))
                    x0, y0 = x1, y1
            holes.append(len(starts) - 1)
        scale = tr.get("scale") or 0.01
        raw = array("h", terrain[: self.NX * self.NY * 2])
        if len(raw) < self.NX * self.NY:
            raise ValueError("Incomplete terrain heightfield")
        self.TerrainMax = max(raw) * scale
        h = array("f", (v * scale for v in raw))
        tb = array("f")
        for y in range(0, self.NY, 16):
            rows = [h[j * self.NX : (j + 1) * self.NX] for j in range(y, min(y + 17, self.NY))]
            for x in range(0, self.NX, 16):
                tb.append(max(max(row[x : x + 17]) for row in rows))
        self._geo = Geometry(
            self, h, tb, *_packed(edge_index), *_packed(prism_index), holes, starts, edges, prisms, verts
        )
        self.TerrainZ, self.Raycast, self.Visible, self.Floor = (
            self._geo.TerrainZ,
            self._geo.Raycast,
            self._geo.Visible,
            self._geo.Floor,
        )

    def _tree_index(self):
        idx = {}
        trees = self.Trees
        names = trees["fields"]
        values = trees["data"]
        if names:
            for i in range(0, len(values), len(names)):
                t = dict(zip(names, values[i : i + len(names)]))
                x, y = t.get("x", 0), t.get("y", 0)
                cx, cy = t.get("crownX", x), t.get("crownY", y)
                depth = t.get("crownBase", 0)
                z = t.get("z", 0)
                tree = (
                    i,
                    x,
                    y,
                    z,
                    t.get("trunkR", 0),
                    cx,
                    cy,
                    t.get("crownR", 0),
                    (t.get("height", 0) - depth) * 0.5,
                    depth,
                )
                radius = max(tree[4], tree[7])
                for j in range(
                    max(0, math.floor((min(y, cy) - radius - self.gy) / 8)),
                    min(self.gny - 1, math.floor((max(y, cy) + radius - self.gy) / 8)) + 1,
                ):
                    for k in range(
                        max(0, math.floor((min(x, cx) - radius - self.gx) / 8)),
                        min(self.gnx - 1, math.floor((max(x, cx) + radius - self.gx) / 8)) + 1,
                    ):
                        idx.setdefault(j * self.gnx + k, []).append(tree)
        return idx

    def CanopyReach(self, x, y, z, dx, dy, dz, d):
        return self._canopy(x, y, z, dx, dy, dz, d, False)

    def CanopyBlocked(self, x, y, z, bx, by, bz):
        dx, dy, dz = bx - x, by - y, bz - z
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d < 1e-6:
            return False
        return self._canopy(x, y, z, dx / d, dy / d, dz / d, d, True)

    def _canopy(self, x, y, z, dx, dy, dz, d, blocked):
        if not hasattr(self, "_trees"):
            self._trees = self._tree_index()
        if not self._trees:
            return False if blocked else d
        limit = (
            -math.log(self.CanopyBlockT) / self.CanopyDensity
            if self.CanopyDensity > 0 and 0 < self.CanopyBlockT < 1
            else 1e18
        )
        steps = int(d / 4) + 1
        step = d / steps
        prev = -1
        seen = set()
        best = d
        cum = 0.0
        hl = dx * dx + dy * dy
        for s in range(steps + 1):
            t = s * step
            if not blocked and t > best + 8:
                break
            ix = min(max(math.floor((x + dx * t - self.gx) / 8), 0), self.gnx - 1)
            iy = min(max(math.floor((y + dy * t - self.gy) / 8), 0), self.gny - 1)
            cell = iy * self.gnx + ix
            if cell == prev:
                continue
            prev = cell
            for ident, tx, ty, tz, tr, cx, cy, rh, rv, depth in self._trees.get(cell, ()):
                if ident in seen:
                    continue
                if len(seen) < 96:
                    seen.add(ident)
                if tr > 0 and hl > 1e-12:
                    t0 = ((tx - x) * dx + (ty - y) * dy) / hl
                    if (
                        0 < t0 < best
                        and (x + dx * t0 - tx) ** 2 + (y + dy * t0 - ty) ** 2 < tr * tr
                        and tz <= z + dz * t0 <= tz + depth
                    ):
                        if blocked:
                            return True
                        best = t0
                        continue
                if rh <= 0 or rv <= 0:
                    continue
                px, py, pz = (x - cx) / rh, (y - cy) / rh, (z - (tz + depth + rv)) / rv
                vx, vy, vz = dx / rh, dy / rh, dz / rv
                a = vx * vx + vy * vy + vz * vz
                b = 2 * (px * vx + py * vy + pz * vz)
                disc = b * b - 4 * a * (px * px + py * py + pz * pz - 1)
                if disc <= 0 or a < 1e-12:
                    continue
                root = math.sqrt(disc)
                t0 = max(0.0, (-b - root) / (2 * a))
                t1 = min(d, (-b + root) / (2 * a))
                if t1 <= t0:
                    continue
                cum += t1 - t0
                if cum > limit:
                    if blocked:
                        return True
                    tc = (cx - x) * dx + (cy - y) * dy
                    if hl > 1e-12:
                        tc /= hl
                    best = min(best, max(0.0, tc))
        return False if blocked else best

    def InBounds(self, x, y):
        return self.MinX <= x <= self.MaxX and self.MinY <= y <= self.MaxY


def Load(directory):
    p = Path(directory) / "v2"
    try:
        raw = (p / "world.json").read_bytes()
        terrain = (p / "terrain.i16").read_bytes()
        cache = Path(__file__).with_name("campus.nav")
        with ZipFile(cache) as f:
            signature = json.loads(f.read("signature.json"))
        valid = (
            sha256(raw).hexdigest() == signature["world.json"]
            and sha256(terrain).hexdigest() == signature["terrain.i16"]
        )
        return World(json.loads(raw), terrain, cache if valid else None), None
    except (OSError, ValueError) as err:
        return None, err


class Nav:
    def __init__(self, w, step_up, height):
        self.W = w
        self.Cell = 2.0
        self.MinX, self.MinY = math.floor(w.MinX), math.floor(w.MinY)
        self.NX, self.NY = math.ceil((w.MaxX - self.MinX) / 2), math.ceil((w.MaxY - self.MinY) / 2)
        if w._cache and abs(step_up - 1.2) < 1.0e-12 and abs(height - 9) < 1.0e-12:
            with ZipFile(w._cache) as f:
                meta = json.loads(f.read("meta.json"))
                for name, typ in [
                    ("Z", "f"),
                    ("Clear", "f"),
                    ("Head", "f"),
                    ("Roof", "f"),
                    ("Solid", "B"),
                    ("Components", "i"),
                    ("Tops", "f"),
                    ("RoofOf", "i"),
                    ("RoofDist", "h"),
                ]:
                    key = name if name in ("Z", "Clear", "Head", "Roof", "Solid") else "_" + name.lower()
                    setattr(self, key, array(typ, f.read(name)))
                self._roofs = [
                    Roof(**{**r, "Access": [RoofAccess(**a) for a in (r["Access"] or [])]})
                    for r in meta["Roofs"]
                ]
                self._exposure = Exposure(
                    self, meta["ExposureNX"], meta["ExposureNY"], array("f", f.read("Exposure"))
                )
        else:
            self._build(step_up, height)
        self._grid = Grid(self)
        self.WalkLine, self.Index, self.Nearest, self.Walkable, self.PathTo = (
            self._grid.WalkLine,
            self._grid.Index,
            self._grid.Nearest,
            self._grid.Walkable,
            self._grid.PathTo,
        )

    def _build(self, step_up, height):
        """Build the same lattice for alternative map files or chassis dimensions."""
        w = self.W
        nx, ny = self.NX, self.NY
        size = nx * ny
        self.Z, self.Clear, self.Head, self.Roof, self._tops = (array("f") for _ in range(5))
        self.Solid = array("B")
        for k in range(size):
            x, y = self.Pos(k)
            if w.InBounds(x, y):
                z, clear, head, roof, solid, top = w._geo.NavCell(x, y, step_up, height)
            else:
                z, clear, head, roof, solid, top = 0.0, 0.0, 0.0, math.nan, 1, w.Floor(x, y, 1e9)[0]
            self.Z.append(z)
            self.Clear.append(clear)
            self.Head.append(head)
            self.Roof.append(roof)
            self.Solid.append(solid)
            self._tops.append(top)
        grid = Grid(self)
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

        def adjacent(k, cardinal=False):
            i, j = k % nx, k // nx
            for di, dj in (dirs[:4] if cardinal else dirs):
                x, y = i + di, j + dj
                if 0 <= x < nx and 0 <= y < ny:
                    yield y * nx + x

        components = array("i", [0]) * size
        cid = 0
        for k in range(size):
            if components[k] or not grid.Walkable(k, 2.9, 9):
                continue
            cid += 1
            stack = [k]
            components[k] = cid
            while stack:
                here = stack.pop()
                for dest in adjacent(here, True):
                    if not components[dest] and grid.Walkable(dest, 2.9, 9):
                        # The reference joins cells when either direction permits a step.
                        components[dest] = cid
                        stack.append(dest)
        self._components = components
        region = array("i", [-1]) * size
        depth = array("h", [0]) * size
        groups = []
        for k in range(size):
            if region[k] >= 0 or not self.Solid[k] or math.isnan(self.Roof[k]):
                continue
            ident = len(groups)
            cells = []
            z0 = self.Roof[k]
            stack = [k]
            region[k] = ident
            while stack:
                here = stack.pop()
                cells.append(here)
                for dest in adjacent(here, True):
                    if region[dest] >= 0 or not self.Solid[dest] or math.isnan(self.Roof[dest]):
                        continue
                    if abs(self.Roof[dest] - z0) > 0.8 or abs(self.Roof[dest] - self.Roof[here]) > 0.6:
                        continue
                    region[dest] = ident
                    stack.append(dest)
            groups.append(cells)
        roofs = []
        mapping = [-1] * len(groups)
        from collections import deque

        for ident, cells in enumerate(groups):
            z = sum(self.Roof[k] for k in cells) / len(cells)
            min_ground = math.inf
            queue = deque()
            sx = sy = 0.0
            for k in cells:
                i, j = k % nx, k // nx
                x, y = self.Pos(k)
                sx += x
                sy += y
                boundary = i == 0 or j == 0 or i + 1 == nx or j + 1 == ny
                for dest in adjacent(k):
                    if region[dest] != ident:
                        boundary = True
                        if not self.Solid[dest]:
                            min_ground = min(min_ground, self.Z[dest])
                if boundary:
                    queue.append(k)
                    depth[k] = 1
            while queue:
                k = queue.popleft()
                for dest in adjacent(k, True):
                    if region[dest] == ident and not depth[dest]:
                        depth[dest] = depth[k] + 1
                        queue.append(dest)
            inner = max(cells, key=depth.__getitem__)
            inner_d = (depth[inner] - 0.5) * 2
            if len(cells) * 4 < 250 or inner_d < 5:
                continue
            access = []
            for k in cells:
                if depth[k] != 1:
                    continue
                i, j = k % nx, k // nx
                for di, dj in dirs[:4]:
                    xx, yy = i + di, j + dj
                    if not (0 <= xx < nx and 0 <= yy < ny) or self.Solid[yy * nx + xx]:
                        continue
                    for step in (2, 3):
                        xx, yy = i + di * step, j + dj * step
                        if not (0 <= xx < nx and 0 <= yy < ny):
                            break
                        g = yy * nx + xx
                        if self.Solid[g]:
                            break
                        if grid.Walkable(g, 2.7, 9):
                            xi, yi = i - 2 * di, j - 2 * dj
                            edge = yi * nx + xi
                            if 0 <= xi < nx and 0 <= yi < ny and region[edge] == ident:
                                access.append(RoofAccess(g, edge, z - self.Z[g]))
                            break
            if access:
                mapping[ident] = len(roofs)
                roofs.append(
                    Roof(
                        len(roofs),
                        z,
                        cells,
                        len(cells) * 4,
                        0 if min_ground == math.inf else z - min_ground,
                        inner,
                        inner_d,
                        access,
                        sx / len(cells),
                        sy / len(cells),
                    )
                )
        for k, group in enumerate(region):
            if group >= 0:
                region[k] = mapping[group]
            if region[k] < 0:
                depth[k] = 0
        self._roofs, self._roofof, self._roofdist = roofs, region, depth
        ex, ey = (nx + 2) // 3, (ny + 2) // 3
        values = array("f")
        angles = [2 * math.pi * (i + 0.5) / 24 for i in range(24)]
        bearings = [(math.cos(a), math.sin(a)) for a in angles]
        for j in range(ey):
            for i in range(ex):
                c = min(nx - 1, 3 * i + 1) + nx * min(ny - 1, 3 * j + 1)
                if self.Solid[c] or self.Clear[c] < 2.6:
                    values.append(2.0)
                    continue
                total = 0.0
                x, y = self.Pos(c)
                z = self.Z[c] + 8
                for dx, dy in bearings:
                    free = w.Raycast(x, y, z, dx, dy, 0, 200)
                    if free > 45:
                        reach = w.CanopyReach(x, y, z, dx, dy, 0, free)
                        if reach < free:
                            free = max(reach, 45)
                    total += free
                values.append(total / (24 * 200))
        self._exposure = Exposure(self, ex, ey, values)

    def Center(self, i, j):
        return self.MinX + i * 2 + 1, self.MinY + j * 2 + 1

    def CellAt(self, x, y):
        return min(max(int((x - self.MinX) / 2), 0), self.NX - 1), min(
            max(int((y - self.MinY) / 2), 0), self.NY - 1
        )

    def Pos(self, k):
        return self.Center(k % self.NX, k // self.NX)

    def Components(self):
        return self._components

    def Exposure(self):
        return self._exposure

    def Roofs(self):
        return self._roofs, self._roofof

    def RoofDist(self):
        return self._roofdist

    def Tops(self):
        return self._tops

    def TopAt(self, k):
        return self._tops[k]

    def Path(self, sx, sy, tx, ty, r, h, maxExpand, extra):
        return self._grid.search(0, sx, sy, tx, ty, r, h, maxExpand, 0, extra, None, 0, 0)

    def Flood(self, sx, sy, r, h, maxCost, extra, visit):
        self._grid.search(1, sx, sy, 0, 0, r, h, 0, maxCost, extra, visit, 0, 0)

    def SurfacePath(self, sx, sy, sz, tx, ty, maxClimb, bodyR, maxExpand, blocked):
        return self._grid.search(2, sx, sy, tx, ty, bodyR, 0, maxExpand, 0, blocked, None, sz, maxClimb)


NewNav = Nav
