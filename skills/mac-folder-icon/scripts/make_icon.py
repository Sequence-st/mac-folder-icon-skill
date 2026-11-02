#!/usr/bin/env python3
"""Turn one generated folder picture (white background) into a folder icon for macOS and Windows.

    python3 make_icon.py <generated.png> <output_folder> [--name NAME] [--no-repair] [--keep-all] [--no-edge-fix]

Steps
  1. outline repair  : redraws the outer outline only where it is really missing (same colour as the fill);
                       light or sketchy pencil lines are left alone. Colour/width come from the line next to the gap
  2. cutout          : removes the white background, un-mixing the soft edge so no light halo is left
  3. largest piece   : keeps only the biggest piece (drops stray specks and corner watermarks)
  4. fit             : scales to the size and position of the default macOS folder
  4b. outline check  : counts see-through pixels 2-6 px inside the outline (a light pencil line lets the desktop
                       shine through = whitish speckles). Above 300 it cuts out again with a shallow edge and fills
                       the outer line strip with the picture's own line colour; the fix is kept only if it is
                       clearly better, not more jagged (+15% max) and adds no light rim
  5. check board     : <name>_check.jpg = result on dark/light + 3x corner zooms

Outputs in <output_folder>: <name>_1024.png, <name>_512.png (macOS), <name>.ico (Windows, 16-256 px),
         <name>_check.jpg, <name>_report.json
Needs: Python 3.9+, Pillow, numpy (OpenCV is used if present, not required).
"""
import argparse
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgops as ops  # noqa: E402

NEAR_WHITE = 40          # a pixel within 40 of pure white counts as background-ish
FOLDER_WIDTH = 0.90      # default macOS folder spans x 0.036..0.963 of the icon
FOLDER_BOTTOM = 0.880    # and its bottom edge sits at y 0.880
MAX_SIDE = 2048


def load_rgb(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    im = im.convert("RGB")
    if max(im.size) > MAX_SIDE:
        s = MAX_SIDE / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return np.array(im)


def background(a):
    mn = a.astype(np.int16).min(axis=2)
    near = (255 - mn) < NEAR_WHITE
    return ops.border_connected(near)


# ---------------------------------------------------------------- 1. outline repair
LINE_CONTRAST = 8        # colour distance edge strip vs. well inside. Measured: real (even light) lines >= 10.7, erased line 0.1-0.4


def repair_outline(a):
    """Redraw the outer outline only where it is really missing.

    A spot counts as "missing" when the strip along the edge has the same colour as the fill
    right inside it (no line at all). A light or sketchy pencil line still differs from the
    fill, so it is left alone. The colour and width of a redrawn piece are measured from the
    real line on both sides of that gap.
    """
    f = a.astype(np.float32)
    lum = f.mean(axis=2)
    bg = background(a)
    obj = ops.open3(~bg)
    ys, xs = np.nonzero(obj)
    if len(xs) < 1000:
        return a, {"skipped": "no object found"}
    objw = int(xs.max() - xs.min())
    D = int(max(6, round(0.006 * objw)))          # edge strip depth (about one line width)
    c = ops.outer_contour(obj)
    dfg = ops.dist_to(~obj, 4 * D + 2)
    edge = obj & (dfg >= 3) & (dfg <= D)              # skip the 2 px soft rim
    inner = obj & (dfg >= 2.5 * D) & (dfg <= 4 * D)   # past even a thick line
    r = 4 * D
    em = box_mean(f, edge, r)
    im = box_mean(f, inner, r)
    inner_n = box_mean(inner[..., None].astype(np.float32), np.ones_like(inner), r)[..., 0]
    cx, cy = c[:, 0], c[:, 1]
    contrast = np.sqrt(((em[cy, cx] - im[cy, cx]) ** 2).sum(axis=1))
    ok = (contrast >= LINE_CONTRAST) | (inner_n[cy, cx] < 0.05)   # thin parts with no inside: leave
    N = len(c)
    info = {"edge_strip_px": D, "contour_len": int(N),
            "line_contrast_median": round(float(np.median(contrast)), 1)}
    start = int(np.argmax(ok)) if ok.any() else 0
    seq = np.roll(ok, -start)
    cc = np.roll(c, -start, axis=0)
    min_run = max(10, 3 * D)
    runs, j = [], 0
    while j < N:
        if not seq[j]:
            k = j
            while k < N and not seq[k]:
                k += 1
            if k - j > min_run:
                runs.append((j, k))
            j = k
        else:
            j += 1
    gap_len = sum(e - s for s, e in runs)
    info["gaps"] = [{"x": int(cc[s][0]), "y": int(cc[s][1]), "len": int(e - s)} for s, e in runs]
    if not runs:
        return a, info
    if gap_len > 0.35 * N:
        info["skipped"] = "outline missing on %.0f%% of the edge (no-outline style?) - not repaired" % (100.0 * gap_len / max(N, 1))
        return a, info

    def local_line(idx, gap_idx):
        """Colour, width and centre-line helper measured from the real line around contour points idx."""
        pts, gp = cc[idx], cc[gap_idx]
        m = np.zeros(obj.shape, bool)
        m[pts[:, 1], pts[:, 0]] = True
        g = np.zeros(obj.shape, bool)
        g[gp[:, 1], gp[:, 0]] = True
        away = ~ops.dilate(g, 3 * D)                       # measure only on the real line, not inside the gap
        near = ops.dilate(m, r) & edge & away
        vals = lum[near]
        if vals.size < 20:
            return None
        lo = np.percentile(vals, 10)
        area = ops.dilate(m, r) & obj & away
        hi = float(np.median(lum[area & inner])) if (area & inner).any() else 255.0
        lineish = lum <= lo + 0.5 * max(hi - lo, 1)
        dk = np.round(dfg).astype(int)
        width = 0
        for k in range(1, 4 * D):                          # depth profile: how deep the line goes
            sl = area & (dk == k)
            if sl.sum() >= 20 and lineish[sl].mean() >= 0.4:
                width = k
        if width < 2:
            return None
        line = area & lineish & (dfg <= width + 1)
        col = np.median(f[line & (lum <= lo + 0.25 * max(hi - lo, 1))], axis=0)
        return col, float(np.clip(width, 2, 40)), line

    fixed = a.copy()
    info["redrawn"] = []
    for s, e in runs:
        span = 3 * D
        side = np.r_[np.arange(max(0, s - span), s), np.arange(e, min(N, e + span))]
        side = side[seq[side]] if len(side) else side
        got = local_line(side, np.arange(s, e)) if len(side) >= 6 else None
        if got is None:
            continue
        col, width, line = got

        colt = tuple(int(v) for v in col)
        thick = int(round(width))
        # follow the edge, pushed inward by half a line so the new stroke lines up with the old one
        ext = r                                                # the gap test averages over r px, so the real gap is ~r longer each side
        seg = ops.rdp(cc[max(0, s - ext):min(N, e + ext)], 2).astype(float)
        if len(seg) < 2:
            continue
        tan = np.gradient(seg, axis=0)
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        nrm /= np.maximum(np.hypot(*nrm.T)[:, None], 1e-6)
        probe = np.clip((seg + 3 * nrm).round().astype(int), 0, [obj.shape[1] - 1, obj.shape[0] - 1])
        flip = ~obj[probe[:, 1], probe[:, 0]]
        nrm[flip] *= -1                                       # make every normal point into the picture
        ops.draw_polyline(fixed, seg + nrm * (thick / 2.0), colt, thick)
        info["redrawn"].append({"len": int(e - s), "color": "#%02X%02X%02X" % colt, "px": thick})
    return fixed, info


# ---------------------------------------------------------------- 2-3. cutout
def cutout(a, keep_all=False, edge=6):
    """edge = how deep (px) into the picture the white un-mixing may reach (6 = old default)."""
    f = a.astype(np.float32)
    W = np.array([255, 255, 255], np.float32)
    bg = background(a)
    dfg = ops.dist_to(bg, 8)      # object pixels: distance to background
    dbg = ops.dist_to(~bg, 4)     # background pixels: distance to object
    ring = (~bg) & (dfg >= 1) & (dfg <= 5)
    lr = f[ring].mean(axis=1)
    O = np.median(f[ring][lr <= np.percentile(lr, 30)], axis=0)   # outline colour just inside the edge
    inner = (~bg) & (dfg > 8)
    fill = np.median(f[inner], axis=0) if inner.any() else O
    outlined = O.mean() < fill.mean() - 25        # a clearly darker line runs around the picture
    alpha = np.where(bg, 0.0, 1.0).astype(np.float32)
    rgb = f.copy()
    if outlined:
        # every edge pixel is white mixed with the outline colour -> un-mix along white->outline
        v = W - O
        vv = float((v * v).sum())
        zone = ((~bg) & (dfg <= edge)) | (bg & (dbg <= 3))
        proj = ((W - f) * v).sum(axis=2) / vv
        alpha[zone] = np.clip(proj[zone], 0, 1)
        alpha[(~bg) & (dfg > edge)] = 1.0
        ref = np.broadcast_to(O, f.shape)
    else:
        # no outline: edge pixels are white mixed with whatever colour sits just inside them
        band = (~bg) & (dfg >= 3) & (dfg <= 7)
        ref = box_mean(f, band, 9)
        rv = W - ref
        rvv = np.maximum((rv * rv).sum(axis=2), 1.0)
        proj = ((W - f) * rv).sum(axis=2) / rvv
        zone = ((~bg) & (dfg <= 3)) | (bg & (dbg <= 3))
        lighter = f.mean(axis=2) > ref.mean(axis=2) + 6
        alpha[zone] = np.where(lighter[zone] | bg[zone], np.clip(proj[zone], 0, 1), 1.0)
    m = zone & (alpha > 0.01)
    fg = (f - (1 - alpha[..., None]) * W) / np.maximum(alpha[..., None], 1e-3)
    rgb[m] = np.clip(fg[m], 0, 255)

    removed = []
    if not keep_all:
        comps = ops.components(alpha > 0.02)
        if comps:
            keep = comps[0][1]
            for area, cm in comps[1:]:
                ys, xs = np.nonzero(cm)
                removed.append({"area": area, "x": int(xs.mean()), "y": int(ys.mean())})
            alpha[~keep] = 0
    rgba = np.dstack([rgb, alpha * 255]).round().astype(np.uint8)
    ys, xs = np.nonzero(~bg)
    objw = int(xs.max() - xs.min()) if len(xs) else 0
    return rgba, {"outlined": bool(outlined), "outline_rgb": [int(x) for x in O], "removed_pieces": removed,
                  "object_width": objw}


def box_mean(vals, mask, r):
    """Mean of vals over mask pixels inside a (2r+1) square window (vals: HxWxC float)."""
    def bsum(x):
        p = np.pad(x, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (x.ndim - 2))
        c = p.cumsum(0).cumsum(1)
        k = 2 * r + 1
        return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    m = mask.astype(np.float64)
    s = bsum(vals * m[..., None])
    n = bsum(m)[..., None]
    out = s / np.maximum(n, 1)
    return np.where(n > 0, out, vals).astype(np.float32)


# ---------------------------------------------------------------- 4. fit to macOS folder
def fit(rgba, S=1024):
    im = Image.fromarray(rgba)
    a = rgba[..., 3]
    ys, xs = np.nonzero(a > 5)
    crop = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    tw = round(S * FOLDER_WIDTH)
    th = round(crop.height * tw / crop.width)
    max_h = round(S * (FOLDER_BOTTOM - 0.02))
    if th > max_h:                      # very tall picture: fit the height instead
        th = max_h
        tw = round(crop.width * th / crop.height)
    crop = crop.resize((tw, th), Image.LANCZOS)
    top = round(S * FOLDER_BOTTOM) - th
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.alpha_composite(crop, ((S - tw) // 2, top))
    arr = np.array(out)
    crumbs = 0
    for area, cm in ops.components(arr[..., 3] > 5)[1:]:   # 1-5 px crumbs left by resizing
        if area < 30:
            arr[cm, 3] = 0
            crumbs += 1
    return Image.fromarray(arr), {"width": tw, "height": th, "top": round(top / S, 3), "crumbs_removed": crumbs}


# ---------------------------------------------------------------- 4b. outer line check / fix
EDGE_TRANSLUCENT_LIMIT = 300   # see-through px in the outer line strip (1024 icon) above this -> try the fix
ROUGH_LIMIT = 1.15             # keep the fix only if the edge gets at most 15% more jagged
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def _inside_depth(alpha, rmax):
    """Distance (px) from every solid pixel to the outside of the picture."""
    return ops.dist_to(alpha <= 127, rmax)


def edge_translucent(icon):
    """Pixels 2-6 px inside the outline that are still see-through (alpha < 230).

    A soft 1-2 px rim is normal anti-aliasing. See-through pixels deeper than that let the
    desktop colour shine through the line, so a light pencil line looks speckled ("whitish")
    on a blue desktop. The old light-halo test does not catch this.
    """
    a = np.array(icon)[..., 3].astype(np.float32)
    d = _inside_depth(a, 7)
    return int(((d >= 2) & (d <= 6) & (a < 230)).sum())


def edge_roughness(icon, up=4, win=13):
    """Average distance (px) between the outline and a smoothed copy of it. Higher = more stair-steps."""
    a = np.array(icon)[..., 3]
    big = np.array(Image.fromarray(a).resize((a.shape[1] * up, a.shape[0] * up), Image.BILINEAR)) > 127
    c = ops.outer_contour(big).astype(np.float32)
    if len(c) < 3 * win:
        return 0.0
    k = np.ones(win) / win
    sm = np.stack([np.convolve(np.r_[c[-win:, i], c[:, i], c[:win, i]], k, "same")[win:-win] for i in (0, 1)], 1)
    return float(np.hypot(*(c - sm).T).mean() / up)


def even_outline(icon):
    """Fill the outer line strip with the picture's own line colour (only pixels lighter than the line).

    Alpha is not touched, so the anti-aliased rim stays smooth.
    """
    im = np.array(icon).astype(np.float32)
    rgb, a = im[..., :3], im[..., 3]
    d = _inside_depth(a, 16)
    lum = rgb @ LUMA
    band = (d >= 1.5) & (d <= 9)
    if band.sum() < 100:
        return icon, {"skipped": "no outline strip"}
    base = np.percentile(lum[band], 8)
    col = np.median(rgb[band & (lum <= base + 12)], axis=0)
    cl = float(col @ LUMA)
    dark = (lum <= cl + 35) & (a > 127)
    prof = [float(dark[(d > k - 0.5) & (d <= k + 0.5)].mean()) for k in range(1, 16)]
    line_w = max([k for k, v in enumerate(prof, 1) if v >= 0.5] or [3])
    w = max(3, line_w - 2)                                   # stay inside the real line
    s = (np.clip(w - d + 0.5, 0, 1) * (a > 8))[..., None]
    lighter = (lum > cl)[..., None]
    new = np.where(lighter, rgb * (1 - s) + col * s, rgb)
    out = Image.fromarray(np.dstack([new, a]).clip(0, 255).astype(np.uint8))
    return out, {"line_color": "#%02X%02X%02X" % tuple(int(v) for v in col), "line_px": line_w, "filled_px": w}


def fix_outer_edge(fixed, keep_all, icon, cut_info):
    """If the outer line is see-through, cut out again with a shallow edge and even the line colour.

    Keeps the new result only when it is clearly less see-through, not more jagged and has no new light rim.
    """
    t0 = edge_translucent(icon)
    info = {"translucent_px": t0, "limit": EDGE_TRANSLUCENT_LIMIT}
    if not cut_info.get("outlined"):
        info["result"] = "skipped (no outline)"
        return icon, None, info
    if t0 <= EDGE_TRANSLUCENT_LIMIT:
        info["result"] = "ok as is"
        return icon, None, info
    E = max(2.0, 0.0015 * cut_info.get("object_width", 1000))
    rgba2, cut2 = cutout(fixed, keep_all, edge=E)
    icon2, fit2 = fit(rgba2)
    icon2, ev = even_outline(icon2)
    t1 = edge_translucent(icon2)
    r0, r1 = edge_roughness(icon), edge_roughness(icon2)
    h0, h1 = halo_pixels(icon), halo_pixels(icon2)
    info.update({"edge_depth": round(E, 1), "after_px": t1, "rough_before": round(r0, 4), "rough_after": round(r1, 4),
                 "halo_before": h0, "halo_after": h1, "even": ev})
    keep = t1 <= 0.25 * t0 and r1 <= r0 * ROUGH_LIMIT and h1 <= h0 + 20
    if keep:
        info["result"] = "fixed"
        return icon2, fit2, info
    info["result"] = "fix rejected (kept original): " + ", ".join(
        n for n, bad in [("still see-through", t1 > 0.25 * t0), ("more jagged", r1 > r0 * ROUGH_LIMIT),
                         ("new light rim", h1 > h0 + 20)] if bad)
    return icon, None, info


# ---------------------------------------------------------------- 5. check board
def halo_pixels(icon):
    """Soft edge pixels that are clearly lighter than the solid colour right inside them (= white left over)."""
    a = np.array(icon).astype(np.float32)
    al = a[..., 3]
    edge = (al > 25) & (al < 230)
    solid = al >= 250
    inside = box_mean(a[..., :3], solid, 4).mean(axis=2)
    lum = a[..., :3].mean(axis=2)
    has_inside = box_mean(solid[..., None].astype(np.float32), np.ones_like(solid), 4)[..., 0] > 0
    return int((edge & has_inside & (lum > inside + 25) & (lum > 160)).sum())


def checker(size, sq=16):
    y, x = np.mgrid[0:size[1], 0:size[0]]
    v = np.where(((x // sq) + (y // sq)) % 2 == 0, 236, 214).astype(np.uint8)
    return Image.fromarray(np.dstack([v, v, v]))


def check_board(src_rgb, icon, path, lines):
    def font(sz):
        try:
            return ImageFont.load_default(size=sz)
        except TypeError:
            return ImageFont.load_default()
    P = 420
    dark = Image.new("RGB", icon.size, (30, 30, 32))
    dark.paste(icon, (0, 0), icon)
    light = checker(icon.size)
    light.paste(icon, (0, 0), icon)
    src = Image.fromarray(src_rgb)
    src.thumbnail((P, P), Image.LANCZOS)
    a = np.array(icon)[..., 3]
    ys, xs = np.nonzero(a > 5)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    ym = (y0 + y1) // 2
    Z, z = 150, 3
    py, px = np.nonzero(a > 128)

    def nearest(tx, ty):  # the real edge of the picture closest to a bounding-box point
        i = int(np.argmin((px - tx) ** 2 + (py - ty) ** 2))
        return int(px[i]), int(py[i])
    spots = [(n,) + nearest(tx, ty) for n, tx, ty in
             [("top-left", x0, y0), ("top-right", x1, y0), ("left", x0, ym), ("right", x1, ym),
              ("bottom-left", x0, y1), ("bottom-right", x1, y1)]]
    W = 20 + 3 * (P + 20)
    H = 60 + P + 40 + 2 * (Z * z // 2 + 40) + 20 + 22 * len(lines)
    board = Image.new("RGB", (W, H), (250, 250, 250))
    d = ImageDraw.Draw(board)
    f1 = font(20)
    for i, (name, im) in enumerate([("input", src), ("result on dark", dark.resize((P, P), Image.LANCZOS)),
                                    ("result on light", light.resize((P, P), Image.LANCZOS))]):
        x = 20 + i * (P + 20)
        d.text((x, 20), name, fill=(40, 40, 40), font=f1)
        board.paste(im, (x, 60))
    zs = Z * z // 2
    yb = 60 + P + 40
    for i, (name, cx, cy) in enumerate(spots):
        cx = min(max(cx, Z // 4), icon.width - Z // 4)
        cy = min(max(cy, Z // 4), icon.height - Z // 4)
        crop = dark.crop((cx - Z // 4, cy - Z // 4, cx - Z // 4 + Z // 2, cy - Z // 4 + Z // 2)).resize((zs, zs), Image.NEAREST)
        x = 20 + (i % 3) * (P + 20)
        y = yb + (i // 3) * (zs + 40)
        d.text((x, y - 24), name + " x3", fill=(40, 40, 40), font=f1)
        board.paste(crop, (x, y))
    y = yb + 2 * (zs + 40)
    for t in lines:
        d.text((20, y), t, fill=(20, 20, 20), font=f1)
        y += 22
    board.save(path, quality=90)


def main():
    for st in (sys.stdout, sys.stderr):  # agents read UTF-8; Windows pipes default to the local code page
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("outdir")
    ap.add_argument("--name")
    ap.add_argument("--no-repair", action="store_true", help="skip outline repair")
    ap.add_argument("--keep-all", action="store_true", help="keep every piece, not only the largest")
    ap.add_argument("--no-edge-fix", action="store_true", help="skip the see-through outline check/fix")
    args = ap.parse_args()
    t0 = time.time()
    name = args.name or os.path.splitext(os.path.basename(args.input))[0]
    os.makedirs(args.outdir, exist_ok=True)
    a = load_rgb(args.input)
    report = {"input": os.path.abspath(args.input), "size": [int(a.shape[1]), int(a.shape[0])],
              "opencv": ops.HAVE_CV2}
    if args.no_repair:
        fixed, report["repair"] = a, {"skipped": "--no-repair"}
    else:
        fixed, report["repair"] = repair_outline(a)
    rgba, report["cutout"] = cutout(fixed, args.keep_all)
    icon, report["fit"] = fit(rgba)
    if args.no_edge_fix:
        report["edge"] = {"translucent_px": edge_translucent(icon), "result": "skipped (--no-edge-fix)"}
    else:
        icon, fit2, report["edge"] = fix_outer_edge(fixed, args.keep_all, icon, report["cutout"])
        if fit2:
            report["fit"] = fit2
    out1024 = os.path.join(args.outdir, name + "_1024.png")
    out512 = os.path.join(args.outdir, name + "_512.png")
    icon.save(out1024)
    icon.resize((512, 512), Image.LANCZOS).save(out512)
    out_ico = os.path.join(args.outdir, name + ".ico")
    icon.save(out_ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    report["halo_px"] = halo_pixels(icon)
    report["see_through_px"] = edge_translucent(icon)
    report["outputs"] = [out1024, out512, out_ico]
    rep = report["repair"]
    ed = report["edge"]
    edge_line = "see-through outline px: %d (limit %d) -> %s" % (ed["translucent_px"], EDGE_TRANSLUCENT_LIMIT, ed["result"])
    if "after_px" in ed:
        edge_line += " | after %d, jagged %.3f->%.3f" % (ed["after_px"], ed["rough_before"], ed["rough_after"])
    lines = [
        "outline repair: " + (rep.get("skipped") or "%d gap(s) redrawn %s" % (len(rep.get("redrawn", [])), [g["len"] for g in rep["gaps"]][:6])),
        edge_line,
        "removed pieces (specks / watermark): %d %s" % (len(report["cutout"]["removed_pieces"]),
                                                        [p["area"] for p in report["cutout"]["removed_pieces"]][:6]),
        "light halo pixels on edge: %d (0 is best)" % report["halo_px"],
        "folder fit: width %d, height %d, top %.3f   opencv=%s" % (report["fit"]["width"], report["fit"]["height"],
                                                                 report["fit"]["top"], ops.HAVE_CV2),
    ]
    check = os.path.join(args.outdir, name + "_check.jpg")
    check_board(a, icon, check, lines)
    report["check_board"] = check
    report["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(args.outdir, name + "_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: report[k] for k in ("outputs", "check_board", "halo_px", "see_through_px", "seconds", "opencv")}, ensure_ascii=False))
    for t in lines:
        print(" -", t)


if __name__ == "__main__":
    main()
