#!/usr/bin/env python3
"""Shrink oversized images in place, or check that none are oversized.

  python3 bin/optimize_images.py             # re-encode tracked images over the budget
  python3 bin/optimize_images.py --check     # CI: list images over the budget, exit 1 if any
  python3 bin/optimize_images.py --webp      # also write a .webp next to each JPEG/PNG that lacks one

JPEGs over the budget are resized to --max-edge (long side) and saved at --quality,
progressive, without EXIF (orientation is applied first). PNGs are resized and
re-saved with optimize=True. A file is only replaced when the result is at least
10% smaller or newly fits the budget, so running this twice changes nothing.

Needs Pillow (pip install Pillow). Shared by all the Jekyll sites; keep the copies identical.
"""
import argparse
import os
import subprocess
import sys

EXTS = (".jpg", ".jpeg", ".png")


def tracked_images(paths):
    out = subprocess.run(["git", "ls-files", "-z", "--", *paths], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p.lower().endswith(EXTS + (".webp", ".gif")) and os.path.isfile(p)]


def shrink(path, max_edge, quality, limit):
    from PIL import Image, ImageOps

    before = os.path.getsize(path)
    tmp = path + ".tmp"
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        if max(im.size) > max_edge:
            im.thumbnail((max_edge, max_edge), Image.LANCZOS)
        if path.lower().endswith(".png"):
            im.save(tmp, "PNG", optimize=True)
        else:
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            # step the quality down (not below 70) until the file fits the budget
            for q in range(quality, 69, -4):
                im.save(tmp, "JPEG", quality=q, optimize=True, progressive=True)
                if os.path.getsize(tmp) <= limit:
                    break
    after = os.path.getsize(tmp)
    if after <= before * 0.9 or (before > limit >= after):
        os.replace(tmp, path)
        return before, after
    os.remove(tmp)
    return before, before


def write_webp(path, quality):
    from PIL import Image, ImageOps

    target = os.path.splitext(path)[0] + ".webp"
    if os.path.exists(target):
        return None
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        im.save(target, "WEBP", quality=quality, method=6)
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--max-kb", type=int, default=int(os.environ.get("IMAGE_MAX_KB", 500)))
    ap.add_argument("--max-edge", type=int, default=2000)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--webp", action="store_true")
    a = ap.parse_args()

    limit = a.max_kb * 1024
    files = tracked_images(a.paths)
    over = [p for p in files if os.path.getsize(p) > limit]

    if a.check:
        for p in over:
            print(f"::error file={p}::{os.path.getsize(p) // 1024} KB is over the {a.max_kb} KB image budget "
                  f"(run: python3 bin/optimize_images.py {p})")
        print(f"{len(files)} images checked, {len(over)} over {a.max_kb} KB")
        return 1 if over else 0

    saved = 0
    for p in over:
        if not p.lower().endswith(EXTS):
            continue
        try:
            b, n = shrink(p, a.max_edge, a.quality, limit)
        except Exception as e:  # e.g. a .jpg that is really HTML or a truncated file
            print(f"{p}: skipped, cannot read it as an image ({e.__class__.__name__})")
            continue
        if n < b:
            saved += b - n
            print(f"{p}: {b // 1024} KB -> {n // 1024} KB")
        else:
            print(f"{p}: {b // 1024} KB, could not shrink by 10% (check it by hand)")
    if a.webp:
        for p in files:
            if p.lower().endswith(EXTS):
                t = write_webp(p, a.quality)
                if t:
                    print(f"wrote {t}")
    print(f"saved {saved // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
