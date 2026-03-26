"""
update_readme.py
Reads the current ozone forecast JSON and rewrites the Top-10 table
in README.md between two sentinel comment markers.
"""

import json
import re
from datetime import datetime, timezone

INPUT_JSON = "output/ozone_forecast_nrw.json"
README_PATH = "README.md"

# Ozone colour scale (µg/m³ upper bound → hex colour)
# Last entry uses float('inf') as sentinel for > 500
COLOUR_SCALE = [
    (20,   "C6E9F3"),
    (40,   "B3DFEB"),
    (60,   "A0D5E3"),
    (80,   "BFDFCD"),
    (100,  "EBEEB3"),
    (120,  "FAE88E"),
    (140,  "F5D362"),
    (160,  "EDB43C"),
    (180,  "E18620"),
    (200,  "D05C0B"),
    (240,  "AA4110"),
    (500,  "852615"),
    (float("inf"), "8526BA"),
]

# Sentinel markers in README.md — everything between them is replaced
MARKER_START = "<!-- TOP10_START -->"
MARKER_END   = "<!-- TOP10_END -->"


def get_colour(value: float) -> str:
    """Return the hex colour for a given ozone value."""
    for upper, colour in COLOUR_SCALE:
        if value <= upper:
            return colour
    return COLOUR_SCALE[-1][1]


def format_datetime(iso: str) -> str:
    """Convert ISO UTC string to readable 'YYYY-MM-DD HH:MM UTC'."""
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def build_top10_block(json_path: str) -> str:
    """Build the markdown block to inject into README.md."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    generated = data.get("generated_at_utc", "")
    base_date = data.get("forecast_base_date", "")

    # Collect today's peak values
    rows = []
    for m in data["municipalities"]:
        today = m["forecast"].get("today", {})
        val = today.get("peak_ozone_ug_m3")
        time = today.get("peak_time_utc")
        if val is not None and time is not None:
            rows.append((m["name"], val, time))

    # Sort descending, take top 10
    rows.sort(key=lambda x: x[1], reverse=True)
    top10 = rows[:10]

    lines = []
    lines.append(MARKER_START)
    lines.append("")
    lines.append(f"## Top 10 — Highest Ozone Values Today ({base_date})")
    lines.append("")
    lines.append(f"*Forecast base: {base_date} 00:00 UTC · Generated: {generated}*")
    lines.append("")

    # HTML table — GitHub Markdown renders inline HTML including bgcolor
    lines.append('<table>')
    lines.append('  <thead>')
    lines.append('    <tr>')
    lines.append('      <th align="left">Municipality</th>')
    lines.append('      <th align="left">Peak time (UTC)</th>')
    lines.append('      <th align="right">O₃ (µg/m³)</th>')
    lines.append('    </tr>')
    lines.append('  </thead>')
    lines.append('  <tbody>')

    for name, val, time_iso in top10:
        colour = get_colour(val)
        time_fmt = format_datetime(time_iso)
        lines.append(f'    <tr bgcolor="#{colour}">')
        lines.append(f'      <td><b>{name}</b></td>')
        lines.append(f'      <td>{time_fmt}</td>')
        lines.append(f'      <td align="right"><b>{val:.1f}</b></td>')
        lines.append(f'    </tr>')

    lines.append('  </tbody>')
    lines.append('</table>')
    lines.append("")

    # Colour legend
    lines.append("### Colour scale")
    lines.append("")
    lines.append('<table>')
    lines.append('  <tr>')
    for upper, colour in COLOUR_SCALE:
        label = f">{int(COLOUR_SCALE[-2][0])}" if upper == float("inf") else f"≤{int(upper)}"
        lines.append(f'    <td bgcolor="#{colour}" align="center"><small>{label}</small></td>')
    lines.append('  </tr>')
    lines.append('</table>')
    lines.append("")
    lines.append(MARKER_END)

    return "\n".join(lines)


def update_readme(readme_path: str, new_block: str) -> None:
    """Replace the content between sentinel markers in README.md."""
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )

    if pattern.search(content):
        updated = pattern.sub(new_block, content)
    else:
        # Markers not found — prepend the block at the top
        updated = new_block + "\n\n" + content

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"README.md updated with Top-10 table.")


if __name__ == "__main__":
    block = build_top10_block(INPUT_JSON)
    update_readme(README_PATH, block)
