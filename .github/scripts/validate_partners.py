#!/usr/bin/env python3
"""Validate partner files in _works/ before they reach the live site.

Usage:
  python3 .github/scripts/validate_partners.py               # check, exit 1 on errors
  python3 .github/scripts/validate_partners.py --report X.csv  # also write a content-gap report

Errors (fail the check): broken front matter, missing required fields, unknown
location/category slugs, missing logo file, description text stored under a key
the page template does not display.
Warnings (reported only): no description text, no phone number.
"""
import csv
import glob
import os
import re
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REQUIRED = ["layout", "title", "category", "category_slug", "location",
            "location_slug", "image", "short_description"]
LOCATIONS = {"craiova", "national", "suceava"}
PHONE_RE = re.compile(r"\+?\d[\d\s.\-]{7,}\d")


def strip_html(value):
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def category_slugs():
    with open(os.path.join(ROOT, "_data", "settings.yml"), encoding="utf-8") as fh:
        settings = yaml.safe_load(fh)
    return {f["slug"] for f in settings["portfolio"]["filters"]}


def front_matter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        raise ValueError("file does not start with '---' front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("front matter is not closed with '---'")
    data = yaml.safe_load(parts[1])
    if not isinstance(data, dict):
        raise ValueError("front matter is empty")
    return data


def main(argv):
    report_path = None
    if "--report" in argv:
        report_path = argv[argv.index("--report") + 1]

    slugs = category_slugs()
    errors, warnings, rows = [], [], []

    for path in sorted(glob.glob(os.path.join(ROOT, "_works", "*.md"))):
        name = os.path.relpath(path, ROOT)
        try:
            d = front_matter(path)
        except Exception as exc:  # noqa: BLE001 - report any parse problem
            errors.append(f"{name}: {exc}".splitlines()[0])
            continue

        for key in REQUIRED:
            if d.get(key) in (None, ""):
                errors.append(f"{name}: missing '{key}'")

        if d.get("location_slug") and d["location_slug"] not in LOCATIONS:
            errors.append(f"{name}: location_slug '{d['location_slug']}' must be one of {sorted(LOCATIONS)}")
        if d.get("category_slug") and d["category_slug"] not in slugs:
            errors.append(f"{name}: category_slug '{d['category_slug']}' is not in _data/settings.yml filters {sorted(slugs)}")

        image = str(d.get("image") or "").split("#")[0].strip()
        if image and not os.path.isfile(os.path.join(ROOT, image)):
            errors.append(f"{name}: image '{image}' does not exist")

        info = d.get("info") or []
        if not isinstance(info, list) or any(not isinstance(i, dict) or "label" not in i or "value" not in i for i in info):
            errors.append(f"{name}: every 'info' entry needs 'label' and 'value' (check indentation)")
            info = []

        desc = d.get("description1") or {}
        if isinstance(desc, dict) and len(strip_html(desc.get("text")).strip(" .")) > 3:
            errors.append(f"{name}: description1 uses 'text', which is not displayed; rename it to 'text1'")

        if d.get("published") is False:
            continue

        body = strip_html(" ".join(str(desc.get(k) or "") for k in ("text1", "text2"))) if isinstance(desc, dict) else ""
        has_text = len(body.strip(" .")) > 3
        info_text = " ".join(strip_html(i.get("value")) for i in info)
        has_phone = bool(PHONE_RE.search(info_text))
        has_discount = any(str(i.get("label", "")).strip().lower() == "reducere" for i in info)
        if not has_text:
            warnings.append(f"{name}: no description text (description1.text1)")
        if not has_phone:
            warnings.append(f"{name}: no phone number in 'info'")
        rows.append({
            "file": name,
            "partner": strip_html(d.get("title")),
            "location": d.get("location_slug", ""),
            "category": d.get("category", ""),
            "has_description": "da" if has_text else "NU",
            "has_phone": "da" if has_phone else "NU",
            "has_discount_field": "da" if has_discount else "NU",
            "short_description": strip_html(d.get("short_description"))[:120],
        })

    if report_path:
        with open(report_path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Report written to {report_path} ({len(rows)} partners)")

    print(f"{len(rows)} published partners checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    for line in errors:
        print(f"ERROR   {line}")
    if "--verbose" in argv:
        for line in warnings:
            print(f"WARNING {line}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
