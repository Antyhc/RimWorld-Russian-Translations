#!/usr/bin/env python3
"""Preserve an authorized original cover and add only a RUSSIAN bottom overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def make_cover(source, destination, manifest, font_path):
    from PIL import Image, ImageDraw, ImageFont

    meta = json.loads(Path(manifest).read_text(encoding="utf-8-sig"))
    rights = meta.get("rights", {}).get("icon", {})
    if rights.get("status") != "confirmed" or not all(rights.get(x) for x in ("license", "evidence", "attribution")):
        raise ValueError("Icon reuse/modification rights and attribution must be confirmed in manifest")
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ValueError("Output must differ from original; originals are never overwritten")
    if destination.exists():
        raise ValueError("Output already exists; choose a fresh path")
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    if rights.get("source_sha256") != source_sha256:
        raise ValueError("Icon permission must be bound to this exact original source_sha256")
    with Image.open(source) as original:
        if getattr(original, "n_frames", 1) != 1:
            raise ValueError("Animated cover requires a static author-approved original")
        canvas = original.convert("RGBA")
    width, height = canvas.size
    if width < 64 or height < 64:
        raise ValueError("Cover too small for legible overlay")
    # One deterministic bottom band and one word. No scaling/cropping/repainting.
    band_height = max(24, round(height * 0.19))
    band_top = height - band_height
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, band_top, width - 1, height - 1), fill=(0, 0, 0, 150))
    size = max(12, round(band_height * 0.70))
    font = ImageFont.truetype(str(font_path), size)
    while size > 10 and draw.textbbox((0, 0), "RUSSIAN", font=font, stroke_width=1)[2] > width * 0.92:
        size -= 1
        font = ImageFont.truetype(str(font_path), size)
    bounds = draw.textbbox((0, 0), "RUSSIAN", font=font, stroke_width=1)
    x = (width - (bounds[2] - bounds[0])) / 2 - bounds[0]
    y = band_top + (band_height - (bounds[3] - bounds[1])) / 2 - bounds[1]
    draw.text((x, y), "RUSSIAN", font=font, fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    result = Image.alpha_composite(canvas, overlay)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, format="PNG")
    return {"source": str(source), "source_sha256": source_sha256, "output": str(destination), "preview_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "size": [width, height], "unchanged_region": [0, 0, width, band_top], "icon_attribution": rights["attribution"], "rights_evidence": rights["evidence"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True, help="Path to a licensed local bold TTF; same font for every cover")
    args = parser.parse_args()
    print(json.dumps(make_cover(args.source, args.output, args.manifest, args.font), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        sys.exit(2)
