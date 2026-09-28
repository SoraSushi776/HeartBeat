"""Generate HeartBeat icon PNGs from vector geometry."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "resources" / "icons"
BG = (27, 16, 32, 255)
HEART_TOP = (255, 107, 138, 255)
HEART_BOTTOM = (229, 57, 106, 255)
PULSE = (255, 255, 255, 255)


def heart_points(cx: float, cy: float, scale: float) -> list[tuple[float, float]]:
    """Return the classic cardioid heart outline scaled to the icon box."""
    points: list[tuple[float, float]] = []
    for i in range(256):
        theta = math.pi * i / 128.0
        x = 16 * pow(math.sin(theta), 3)
        y = (
            13 * math.cos(theta)
            - 5 * math.cos(2 * theta)
            - 2 * math.cos(3 * theta)
            - math.cos(4 * theta)
        )
        points.append((cx + x * scale, cy - y * scale))
    return points


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    radius = max(2, size * 22 // 100)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=BG)

    s = size / 512.0
    pts = heart_points(256 * s, 250 * s, 11.5 * s)
    mid_y = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0
    top = [p for p in pts if p[1] <= mid_y]
    bottom = [p for p in pts if p[1] >= mid_y]
    if top:
        draw.polygon(top, fill=HEART_TOP)
    if bottom:
        draw.polygon(bottom, fill=HEART_BOTTOM)
    draw.polygon(pts, fill=HEART_TOP)

    width = max(3, int(size * 0.052))
    path = [
        (88 * s, 292 * s),
        (168 * s, 292 * s),
        (208 * s, 198 * s),
        (258 * s, 388 * s),
        (308 * s, 232 * s),
        (348 * s, 292 * s),
        (428 * s, 292 * s),
    ]
    draw.line(path, fill=PULSE, width=width, joint="curve")
    r = max(2, int(size * 0.032))
    x, y = path[2]
    draw.ellipse((x - r, y - r, x + r, y + r), fill=PULSE)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 64, 128, 256, 512):
        draw_icon(size).save(OUT / f"icon_{size}.png")
    draw_icon(512).save(OUT / "icon.png")
    gray = draw_icon(256).convert("LA")
    gray.save(OUT / "icon_mono_256.png")
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
