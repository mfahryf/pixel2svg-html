#!/usr/bin/env python3
"""Convert an SVG file into a standalone JS-rendered HTML preview."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build standalone HTML that recreates an SVG via JavaScript DOM calls or contextual motion.")
    parser.add_argument("svg", type=Path, help="Input SVG file.")
    parser.add_argument("--out", type=Path, default=None, help="Output HTML file (defaults to <subject>.html or <subject>_motion.html).")
    parser.add_argument("--title", default=None, help="HTML document title (defaults to subject name).")
    parser.add_argument("--motion", action="store_true", help="Generate a context-aware object/background motion HTML preview.")
    parser.add_argument("--motion-bg", action="store_true", help="Generate an ambient motion background HTML preview (backwards compatibility).")
    parser.add_argument(
        "--category",
        choices=["auto", "creature", "vehicle", "nature", "mechanical", "background", "custom"],
        default="auto",
        help="Animation category when --motion is set (default: auto-detect from layers).",
    )
    parser.add_argument(
        "--preset",
        choices=["wave", "ripple", "breathe", "shimmer", "drift"],
        default="wave",
        help="Motion background preset when category is background (default: wave).",
    )
    parser.add_argument("--duration", type=float, default=None, help="Loop duration in seconds.")
    parser.add_argument("--amplitude", type=float, default=None, help="Motion amplitude.")
    return parser.parse_args()


def strip_namespace(name: str) -> str:
    if "}" in name:
        return name.rsplit("}", 1)[1]
    return name


def clean_attrs(attrs: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in attrs.items():
        local = strip_namespace(key)
        if local == "xmlns":
            continue
        cleaned[local] = value
    return cleaned


def node_to_data(element: ET.Element) -> dict:
    node = {
        "tag": strip_namespace(element.tag),
        "attrs": clean_attrs(element.attrib),
        "children": [node_to_data(child) for child in list(element)],
    }
    text = (element.text or "").strip()
    if text:
        node["text"] = text
    return node


def html_for(svg_data: dict, title: str) -> str:
    payload = json.dumps(svg_data, ensure_ascii=False, separators=(",", ":"))
    safe_title = re.sub(r"[<>]", "", title)
    attrs = svg_data.get("attrs", {})
    max_width = re.sub(r"[^0-9.]", "", attrs.get("width", "")) or "1196"
    if not attrs.get("width") and attrs.get("viewBox"):
        values = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", attrs["viewBox"])
        if len(values) == 4:
            max_width = values[2]
    try:
        display_width = f"{float(max_width):.3f}".rstrip("0").rstrip(".")
    except ValueError:
        display_width = max_width
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    html,
    body {{
      width: 100%;
      height: 100%;
      margin: 0;
      background: #ffffff;
    }}

    body {{
      display: grid;
      place-items: center;
    }}

    #logo-root {{
      width: min(100vw, {display_width}px);
    }}

    #logo-root svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
  </style>
</head>
<body>
  <main id="logo-root" aria-label="Vectorized logo"></main>
  <script>
    const SVG_NS = "http://www.w3.org/2000/svg";
    const LOGO = {payload};

    function createSvgNode(node) {{
      const element = document.createElementNS(SVG_NS, node.tag);
      for (const [name, value] of Object.entries(node.attrs || {{}})) {{
        element.setAttribute(name, value);
      }}
      if (node.text) {{
        element.appendChild(document.createTextNode(node.text));
      }}
      for (const child of node.children || []) {{
        element.appendChild(createSvgNode(child));
      }}
      return element;
    }}

    document.getElementById("logo-root").appendChild(createSvgNode(LOGO));
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    tree = ET.parse(args.svg)
    root = tree.getroot()
    if strip_namespace(root.tag) != "svg":
        raise SystemExit(f"Expected SVG root element in {args.svg}")

    # Dynamic subject-based naming defaults
    out = args.out
    if not out:
        if args.motion or args.motion_bg:
            out = args.svg.with_name(f"{args.svg.stem}_motion.html")
        else:
            out = args.svg.with_suffix(".html")

    out.parent.mkdir(parents=True, exist_ok=True)
    title = args.title or args.svg.stem.replace("_", " ").title()

    if args.motion:
        from animate_svg import (
            assemble_motion_css,
            build_interactive_preview_html,
            clean_xml_string,
            strip_all_namespaces,
        )

        root_clean = tree.getroot()
        strip_all_namespaces(root_clean)
        clean_svg = clean_xml_string(ET.tostring(root_clean, encoding="utf-8").decode("utf-8"))
        css_rules, category, active_layers = assemble_motion_css(
            root_clean,
            category=args.category,
            preset=args.preset,
            duration=args.duration,
            amplitude=args.amplitude,
        )
        html_content = build_interactive_preview_html(
            svg_string=clean_svg,
            title=title,
            subject_name=args.svg.stem.replace("_", " ").title(),
            category=category,
            active_layers=active_layers,
            css_rules=css_rules,
        )
    elif args.motion_bg:
        from animate_svg_motion_bg import build_motion_background_html

        html_content = build_motion_background_html(
            tree,
            title=title,
            default_preset=args.preset,
            duration=args.duration or 5.0,
            amplitude=args.amplitude or 0.35,
        )
    else:
        html_content = html_for(node_to_data(root), title)

    out.write_text(html_content, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
