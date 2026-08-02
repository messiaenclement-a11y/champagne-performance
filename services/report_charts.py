from __future__ import annotations

from io import BytesIO
from math import cos, pi, sin
from typing import Any

from PIL import Image, ImageDraw, ImageFont

DARK = "#1A2434"
LIGHT = "#04B3EA"
GOLD = "#B8A05A"
GRID = "#D9E1E8"
TEXT = "#334155"
WHITE = "#FFFFFF"


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def radar_comparison_chart(
    labels: list[str],
    first_values: list[float],
    second_values: list[float],
    first_label: str,
    second_label: str,
    first_color: str,
    second_color: str,
    size: int = 760,
) -> bytes:
    """Radar à 7 spots avec deux contextes superposés sur une échelle 0-100 %."""
    image = Image.new("RGB", (size, size), WHITE)
    draw = ImageDraw.Draw(image, "RGBA")
    center = (size / 2, size / 2 + 20)
    radius = size * 0.30
    count = len(labels)

    def point(index: int, ratio: float) -> tuple[float, float]:
        angle = -pi / 2 + (2 * pi * index / count)
        return (
            center[0] + cos(angle) * radius * ratio,
            center[1] + sin(angle) * radius * ratio,
        )

    for level in range(1, 6):
        polygon = [point(index, level / 5) for index in range(count)]
        draw.line(polygon + [polygon[0]], fill=GRID, width=2)

    for index in range(count):
        draw.line([center, point(index, 1)], fill=GRID, width=2)

    def draw_series(values: list[float], color: str) -> None:
        polygon = [
            point(index, max(0.0, min(100.0, float(value))) / 100)
            for index, value in enumerate(values)
        ]
        rgb = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
        draw.polygon(polygon, fill=(*rgb, 45))
        draw.line(polygon + [polygon[0]], fill=(*rgb, 255), width=5, joint="curve")
        for x, y in polygon:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(*rgb, 255))

    draw_series(first_values, first_color)
    draw_series(second_values, second_color)

    label_font = _font(20, True)
    for index, label in enumerate(labels):
        x, y = point(index, 1.17)
        box = draw.textbbox((0, 0), label, font=label_font)
        draw.text(
            (x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2),
            label,
            font=label_font,
            fill=DARK,
        )

    legend_font = _font(18, True)
    legend_y = 20
    legend_items = [(first_label, first_color), (second_label, second_color)]
    total_width = sum(draw.textlength(label, font=legend_font) + 52 for label, _ in legend_items)
    legend_x = (size - total_width) / 2
    for label, color in legend_items:
        draw.rounded_rectangle((legend_x, legend_y + 3, legend_x + 28, legend_y + 17), radius=4, fill=color)
        draw.text((legend_x + 36, legend_y), label, font=legend_font, fill=TEXT)
        legend_x += draw.textlength(label, font=legend_font) + 52

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def progression_chart(points: list[dict[str, Any]], width: int = 1000, height: int = 430) -> bytes:
    image = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 72, width - 30, 35, height - 70
    label_font = _font(20)
    small_font = _font(17)

    for value in range(0, 101, 20):
        y = bottom - (value / 100) * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((12, y - 11), f"{value}%", font=small_font, fill=TEXT)

    if not points:
        message = "Aucune donnée de progression"
        box = draw.textbbox((0, 0), message, font=label_font)
        draw.text(((width - box[2]) / 2, height / 2), message, font=label_font, fill=TEXT)
    else:
        count = len(points)
        xs = [left + ((right - left) * i / max(1, count - 1)) for i in range(count)]
        coords = [
            (x, bottom - (float(item["pct"]) / 100) * (bottom - top))
            for x, item in zip(xs, points)
        ]
        if len(coords) > 1:
            draw.line(coords, fill=LIGHT, width=6, joint="curve")
        for x, y in coords:
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=GOLD)
        for x, item in zip(xs, points):
            label = str(item["label"])
            box = draw.textbbox((0, 0), label, font=small_font)
            draw.text((x - (box[2] - box[0]) / 2, bottom + 18), label, font=small_font, fill=TEXT)
            value = f"{item['pct']:.0f}%"
            vbox = draw.textbbox((0, 0), value, font=small_font)
            y = bottom - (float(item["pct"]) / 100) * (bottom - top)
            draw.text((x - (vbox[2] - vbox[0]) / 2, y - 31), value, font=small_font, fill=DARK)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
