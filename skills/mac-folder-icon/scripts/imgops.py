"""Small image helpers for make_icon.py.

Uses OpenCV when it is installed, and falls back to plain numpy + Pillow when it is not.
Set MFI_NO_CV2=1 to force the numpy path (used for testing).
"""
import os
import numpy as np
from PIL import Image, ImageDraw

try:
    if os.environ.get("MFI_NO_CV2"):
        raise ImportError
    import cv2  # optional
    HAVE_CV2 = True
except ImportError:  # pragma: no cover
    cv2 = None
    HAVE_CV2 = False


# ---------- basic morphology (square windows, exact, via cumulative sums) ----------
def _box_any(m, r):
    """True where any pixel in the (2r+1)x(2r+1) window is True."""
    if r <= 0:
        return m.copy()
    a = m.astype(np.int32)
    p = np.pad(a, r)
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s > 0


def dilate(m, r):
    if HAVE_CV2:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        return cv2.dilate(m.astype(np.uint8), k) > 0
    return _box_any(m, r)


def erode(m, r):
    if HAVE_CV2:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        return cv2.erode(m.astype(np.uint8), k) > 0
    return ~_box_any(~m, r)


def open3(m):
    return dilate(erode(m, 1), 1)


# ---------- connected regions ----------
def _shift(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


def _grow(seed, allowed, max_iter=100000):
    """Morphological reconstruction (4-neighbour) of seed inside allowed."""
    cur = seed & allowed
    for i in range(max_iter):
        nxt = cur | ((_shift(cur, 1, 0) | _shift(cur, -1, 0) | _shift(cur, 0, 1) | _shift(cur, 0, -1)) & allowed)
        if np.array_equal(nxt, cur):
            return cur
        cur = nxt
    return cur


def _pool(m, f, mode):
    h, w = m.shape
    H, W = (h + f - 1) // f, (w + f - 1) // f
    p = np.zeros((H * f, W * f), bool) if mode == "any" else np.ones((H * f, W * f), bool)
    p[:h, :w] = m
    b = p.reshape(H, f, W, f)
    return b.any(axis=(1, 3)) if mode == "any" else b.all(axis=(1, 3))


def _up(m, f, shape):
    return np.repeat(np.repeat(m, f, 0), f, 1)[: shape[0], : shape[1]]


def border_connected(m):
    """Pixels of mask m that are connected (4-neighbour) to the image border."""
    if HAVE_CV2:
        n, lab = cv2.connectedComponents(m.astype(np.uint8), connectivity=4)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        return np.isin(lab, list(border)) & m
    f = 4
    low = _pool(m, f, "all")  # a block counts only if fully inside m (no leaking through thin lines)
    seed = np.zeros_like(low)
    seed[0, :], seed[-1, :], seed[:, 0], seed[:, -1] = low[0, :], low[-1, :], low[:, 0], low[:, -1]
    low_bg = _grow(seed, low)
    s = _up(low_bg, f, m.shape) & m
    edge = np.zeros_like(m)
    edge[0, :], edge[-1, :], edge[:, 0], edge[:, -1] = m[0, :], m[-1, :], m[:, 0], m[:, -1]
    return _grow(s | edge, m, max_iter=4000)


def components(m, min_area=1):
    """Return list of (area, mask) for 8-connected components, largest first."""
    if HAVE_CV2:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
        out = [(int(st[i, cv2.CC_STAT_AREA]), lab == i) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= min_area]
        return sorted(out, key=lambda t: -t[0])
    f = 4
    low = _pool(m, f, "any")
    left = low.copy()
    out = []
    while left.any():
        y, x = np.unravel_index(np.argmax(left), left.shape)
        seed = np.zeros_like(left)
        seed[y, x] = True
        comp = _grow8(seed, left)
        left &= ~comp
        full = _up(comp, f, m.shape) & m
        a = int(full.sum())
        if a >= min_area:
            out.append((a, full))
    return sorted(out, key=lambda t: -t[0])


def _grow8(seed, allowed):
    cur = seed & allowed
    while True:
        d = cur | _shift(cur, 1, 0) | _shift(cur, -1, 0) | _shift(cur, 0, 1) | _shift(cur, 0, -1)
        d = d | _shift(cur, 1, 1) | _shift(cur, 1, -1) | _shift(cur, -1, 1) | _shift(cur, -1, -1)
        nxt = d & allowed
        if np.array_equal(nxt, cur):
            return cur
        cur = nxt


# ---------- distance to a mask (small radius) ----------
def dist_to(target, rmax):
    """Euclidean distance from every pixel to the nearest True pixel of target, capped at rmax+1."""
    if HAVE_CV2:
        d = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 5)
        return np.minimum(d, rmax + 1)
    d = np.full(target.shape, float(rmax + 1), np.float32)
    for dy in range(-rmax, rmax + 1):
        for dx in range(-rmax, rmax + 1):
            dd = (dx * dx + dy * dy) ** 0.5
            if dd > rmax:
                continue
            s = _shift(target, dy, dx)
            d = np.where(s & (dd < d), dd, d)
    return d


# ---------- outer contour (ordered points) ----------
def outer_contour(obj):
    """Ordered (x, y) points around the largest object, as an (N, 2) int array."""
    if HAVE_CV2:
        cnts, _ = cv2.findContours(obj.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return max(cnts, key=cv2.contourArea)[:, 0, :]
    comps = components(obj)
    m = comps[0][1]
    p = np.pad(m, 1)
    ys, xs = np.nonzero(p)
    i = np.lexsort((xs, ys))[0]
    start = (int(xs[i]), int(ys[i]))  # top-most, then left-most pixel
    # Moore neighbour tracing, clockwise (y points down)
    nb = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
    idx = {d: k for k, d in enumerate(nb)}
    c, b = start, (start[0] - 1, start[1])  # b = last background pixel looked at
    pts = [start]
    for _ in range(4 * int(m.sum()) + 16):
        bi = idx[(b[0] - c[0], b[1] - c[1])]
        prev, found = b, None
        for k in range(1, 9):
            d = (bi + k) % 8
            q = (c[0] + nb[d][0], c[1] + nb[d][1])
            if p[q[1], q[0]]:
                found = q
                break
            prev = q
        if found is None:
            break
        b, c = prev, found
        if c == start:
            break
        pts.append(c)
    return np.array(pts, int) - 1


def rdp(pts, eps):
    """Ramer-Douglas-Peucker simplification of an open polyline."""
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.hypot(*ab)
    if n == 0:
        d = np.hypot(*(pts - a).T)
    else:
        d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / n
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([rdp(pts[: i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.vstack([a, b])


# ---------- drawing ----------
def draw_polyline(rgb, pts, color, thick):
    """Anti-aliased thick polyline drawn onto an RGB uint8 array (in place)."""
    pts = np.asarray(pts, float)
    if HAVE_CV2:
        cv2.polylines(rgb, [pts.round().astype(np.int32).reshape(-1, 1, 2)], False, color, thickness=int(thick), lineType=cv2.LINE_AA)
        return rgb
    S = 4
    pad = thick + 4
    x0, y0 = int(max(0, pts[:, 0].min() - pad)), int(max(0, pts[:, 1].min() - pad))
    x1, y1 = int(min(rgb.shape[1], pts[:, 0].max() + pad)), int(min(rgb.shape[0], pts[:, 1].max() + pad))
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", (w * S, h * S), 0)
    dr = ImageDraw.Draw(mask)
    q = [((x - x0 + 0.5) * S, (y - y0 + 0.5) * S) for x, y in pts]
    dr.line(q, fill=255, width=int(thick * S), joint="curve")
    r = thick * S / 2
    for x, y in (q[0], q[-1]):
        dr.ellipse((x - r, y - r, x + r, y + r), fill=255)
    a = np.asarray(mask.resize((w, h), Image.LANCZOS), np.float32)[..., None] / 255.0
    region = rgb[y0:y1, x0:x1].astype(np.float32)
    rgb[y0:y1, x0:x1] = (region * (1 - a) + np.array(color, np.float32) * a).round().astype(np.uint8)
    return rgb


def line_thickness(dark, region):
    """Rough outline thickness: 2 x the 90th-percentile distance from a dark pixel to the line edge."""
    sel = dark & region
    if not sel.any():
        return None
    if HAVE_CV2:
        d = cv2.distanceTransform(dark.astype(np.uint8), cv2.DIST_L2, 5)
        return float(np.percentile(d[sel], 90))
    total = int(sel.sum())
    cur = dark.copy()
    for k in range(1, 40):
        cur = erode(cur, 1)
        if int((cur & region).sum()) < 0.1 * total:
            return float(k)
    return 40.0
