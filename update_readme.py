"""
update_readme.py
Reads the current ozone forecast JSON and rewrites the Top-10 table
in README.md between two sentinel comment markers.

GitHub strips bgcolor/style from HTML tables, so colours are rendered
as inline SVG colour squares embedded via data URIs — the only reliable
way to show colour in a GitHub README table.
"""

import json
import re
import base64
from datetime import datetime

INPUT_JSON = "output/ozone_forecast_nrw.json"
README_PATH = "README.md"

MARKER_START = "<!-- TOP10_START -->"
MARKER_END   = "<!-- TOP10_END -->"

# Ozone colour scale: (upper bound µg/m³, hex, dark-text?)
COLOUR_SCALE = [
    (20,          "C6E9F3", True),
    (40,          "B3DFEB", True),
    (60,          "A0D5E3", True),
    (80,          "BFDFCD", True),
    (100,         "EBEEB3", True),
    (120,         "FAE88E", True),
    (140,         "F5D362", True),
    (160,         "EDB43C", True),
    (180,         "E18620", False),
    (200,         "D05C0B", False),
    (240,         "AA4110", False),
    (500,         "852615", False),
    (float("inf"),"8526BA", False),
]


def get_colour(value: float):
    for upper, colour, dark in COLOUR_SCALE:
        if value <= upper:
            return colour, dark
    return COLOUR_SCALE[-1][1], COLOUR_SCALE[-1][2]


def colour_square_svg(hex_colour: str, size: int = 14) -> str:
    """Return an inline SVG image tag showing a filled colour square."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
        f'<rect width="{size}" height="{size}" rx="2" fill="#{hex_colour}"/>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" alt="#{hex_colour}">'


def format_datetime(iso: str) -> str:
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def build_top10_block(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    generated = data.get("generated_at_utc", "")
    base_date  = data.get("forecast_base_date", "")

    rows = []
    for m in data["municipalities"]:
        today = m["forecast"].get("today", {})
        val  = today.get("peak_ozone_ug_m3")
        time = today.get("peak_time_utc")
        if val is not None and time is not None:
            rows.append((m["name"], val, time))

    rows.sort(key=lambda x: x[1], reverse=True)
    top10 = rows[:10]

    lines = [MARKER_START, ""]
    lines.append(f"## 🏆 Top 10 — Highest Ozone Values Today ({base_date})")
    lines.append("")
    lines.append(f"*Forecast base: {base_date} 00:00 UTC · Generated: {generated}*")
    lines.append("")

    # ── Top-10 table ──────────────────────────────────────────────────────────
    lines.append("| | Municipality | Peak time (UTC) | O₃ (µg/m³) |")
    lines.append("|:---:|:---|:---|---:|")

    for name, val, time_iso in top10:
        colour, _ = get_colour(val)
        square     = colour_square_svg(colour, size=16)
        time_fmt   = format_datetime(time_iso)
        lines.append(f"| {square} | **{name}** | {time_fmt} | **{val:.1f}** |")

    lines.append("")

    # ── Colour legend ─────────────────────────────────────────────────────────
    lines.append("### Colour scale (µg/m³)")
    lines.append("")
    lines.append("| Colour | Range |")
    lines.append("|:---:|:---|")

    prev = 0
    for upper, colour, _ in COLOUR_SCALE:
        square = colour_square_svg(colour, size=14)
        if upper == float("inf"):
            label = f"> 500"
        else:
            label = f"{prev}–{int(upper)}"
        lines.append(f"| {square} | {label} |")
        prev = int(upper)

    lines.append("")
    lines.append(MARKER_END)

    return "\n".join(lines)


def update_readme(readme_path: str, new_block: str) -> None:
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )

    updated = pattern.sub(new_block, content) if pattern.search(content) \
              else new_block + "\n\n" + content

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print("README.md updated with Top-10 table.")


if __name__ == "__main__":
    block = build_top10_block(INPUT_JSON)
    update_readme(README_PATH, block)
