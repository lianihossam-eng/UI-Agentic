"""Paint P0-P2 — rendered color/luminance contrast evidence."""
import re


def parse_rgb(value):
    match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value or "")
    if not match:
        return None
    return tuple(int(x) for x in match.groups())


def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(c1, c2):
    p1 = parse_rgb(c1)
    p2 = parse_rgb(c2)
    if not p1 or not p2:
        return None
    l1 = luminance(p1)
    l2 = luminance(p2)
    hi = max(l1, l2)
    lo = min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def check_paint(ir):
    text_tags = {"h1", "h2", "h3", "p", "label", "button", "a"}
    candidates = [
        value
        for value in ir["nodes"].values()
        if value.get("visible")
        and value.get("name")
        and (
            value.get("tag") in text_tags
            or value.get("testid") in ("card", "main", "sidebar", "btn", "close", "open-modal")
        )
    ]

    measured = []
    for value in candidates:
        paint = value.get("paint", {})
        color = paint.get("color")
        background = paint.get("effectiveBg") or paint.get("bg")
        ratio = contrast(color, background)
        if ratio is None:
            continue
        measured.append(
            {
                "tag": value.get("tag"),
                "testid": value.get("testid"),
                "name": value.get("name", "")[:80],
                "ratio": round(ratio, 4),
                "color": color,
                "background": background,
            }
        )

    if not measured:
        return [
            {
                "constraint": "paint.contrast.text",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "no-measurable-visible-text-surface",
            }
        ]

    failures = [item for item in measured if item["ratio"] < 4.5]
    minimum = min(item["ratio"] for item in measured)
    return [
        {
            "constraint": "paint.contrast.text",
            "owner": "PAGE",
            "status": "FAIL" if failures else "PASS",
            "expected": 4.5,
            "minimum_ratio": round(minimum, 2),
            "measured_count": len(measured),
            "failure_count": len(failures),
            "failures": failures[:20],
            "samples": measured[:80],
        }
    ]
