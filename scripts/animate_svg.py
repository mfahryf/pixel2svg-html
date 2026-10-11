#!/usr/bin/env python3
"""Transform SVGs into context-aware, object-specific animated vectors and interactive HTML previews.

Subject-Aware Architecture:
1. Category Detection & Layer Analysis:
   - creature / character: Squash & stretch, hop/jump cycles, lagging ears/tails, ground shadow reactivity.
   - vehicle / mechanical: Continuous wheel rotation around centers, chassis suspension bounce, exhaust puffs.
   - nature / botanical: Wind sway, stem deflection, leaf flutter, petal breathing.
   - mechanical / clockwork: Coordinated gear rotations and pendulum/needle oscillations.
   - background: Spatial wave propagation, matrix ripples, ambient breathing.
   - custom: Bespoke CSS keyframes injected directly.

2. Dynamic Subject-Based Naming:
   - Output deliverables are named based on the subject (<subject>_motion.html, <subject>_motion.svg),
     preventing file collisions and overwriting across different subjects.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Animate an SVG based on contextual object semantics or ambient background."
    )
    parser.add_argument("svg", type=Path, help="Input SVG file.")
    parser.add_argument(
        "--out-html",
        type=Path,
        default=None,
        help="Output HTML preview path (defaults to <subject>_motion.html).",
    )
    parser.add_argument(
        "--out-svg",
        type=Path,
        default=None,
        help="Output standalone animated SVG path (defaults to <subject>_motion.svg if requested).",
    )
    parser.add_argument(
        "--category",
        choices=["auto", "creature", "vehicle", "nature", "mechanical", "background", "custom"],
        default="auto",
        help="Animation category (default: auto-detect from semantic layers).",
    )
    parser.add_argument(
        "--preset",
        choices=["wave", "ripple", "breathe", "shimmer", "drift"],
        default="wave",
        help="Preset when category is background (default: wave).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Loop cycle duration in seconds (defaults to category-tailored timing).",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=None,
        help="Motion intensity multiplier (default: 1.0).",
    )
    parser.add_argument(
        "--motion-css",
        type=str,
        default=None,
        help="Path or raw string of custom CSS keyframes to inject for 'custom' category.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Document title for HTML preview (defaults to subject name).",
    )
    parser.add_argument(
        "--palettes",
        type=str,
        default=None,
        help="Path or raw JSON string of LLM-synthesized color themes tailored to layer IDs.",
    )
    parser.add_argument(
        "--motion-styles",
        type=str,
        default=None,
        help="Path or raw JSON string of 2-3 alternative motion styles { 'Style Name': '/* CSS */' }.",
    )
    return parser.parse_args()


def strip_all_namespaces(root: ET.Element) -> None:
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
        for k in list(el.attrib.keys()):
            if "}" in k:
                val = el.attrib.pop(k)
                el.attrib[k.split("}", 1)[1]] = val
            elif k.startswith("ns0:") or k == "xmlns:ns0":
                del el.attrib[k]


def clean_xml_string(raw_xml: str) -> str:
    clean = re.sub(r"</?ns\d+:", lambda m: "</" if m.group(0).startswith("</") else "<", raw_xml)
    clean = clean.replace('xmlns:ns0="http://www.w3.org/2000/svg"', "")
    clean = clean.replace('xmlns:ns1="http://www.w3.org/2000/svg"', "")
    return clean


def extract_viewbox(root: ET.Element) -> Tuple[float, float, float, float]:
    vb = root.attrib.get("viewBox")
    if vb:
        nums = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", vb)]
        if len(nums) == 4:
            return nums[0], nums[1], nums[2], nums[3]

    w = float(re.sub(r"[^0-9.]", "", root.attrib.get("width", "800")) or 800)
    h = float(re.sub(r"[^0-9.]", "", root.attrib.get("height", "600")) or 600)
    return 0.0, 0.0, w, h


def inspect_svg_layers(root: ET.Element) -> Dict[str, Any]:
    """Collect all element IDs, tags, and classify potential semantic roles."""
    ids: List[str] = []
    id_map: Dict[str, ET.Element] = {}
    tags: List[str] = []

    for el in root.iter():
        tag = el.tag.split("}", 1)[-1].lower()
        tags.append(tag)
        eid = el.attrib.get("id")
        if eid:
            ids.append(eid)
            id_map[eid] = el

    return {
        "ids": ids,
        "id_map": id_map,
        "total_elements": len(tags),
        "tags": tags,
    }


def detect_subject_category(layers: Dict[str, Any]) -> str:
    """Analyze IDs and structure to infer semantic subject category."""
    lower_ids = [i.lower() for i in layers["ids"]]
    all_text = " ".join(lower_ids)

    # 1. Vehicle / Mechanical
    vehicle_keywords = ["wheel", "tire", "rim", "chassis", "car", "vehicle", "exhaust", "headlight", "bumper", "hood"]
    if any(k in all_text for k in vehicle_keywords):
        return "vehicle"

    # 2. Creature / Animal / Living Character
    creature_keywords = ["ear", "tail", "leg", "paw", "head", "rabbit", "bunny", "cat", "dog", "bird", "wing", "beak", "eye", "torso", "face"]
    if any(k in all_text for k in creature_keywords):
        return "creature"

    # 3. Nature / Botanical
    nature_keywords = ["stem", "leaf", "petal", "bloom", "flower", "tree", "plant", "branch", "foliage"]
    if any(k in all_text for k in nature_keywords):
        return "nature"

    # 4. Mechanical / Clockwork
    mech_keywords = ["gear", "cog", "needle", "rotor", "clock", "dial", "pendulum"]
    if any(k in all_text for k in mech_keywords):
        return "mechanical"

    # 5. Background / Pattern
    bg_keywords = ["bg", "backdrop", "background", "matrix", "grid", "wave", "sky", "terrain", "pattern"]
    if any(k in all_text for k in bg_keywords) or layers["total_elements"] > 70:
        return "background"

    return "background"


def build_creature_animation(layers: Dict[str, Any], duration: float, amp: float) -> Tuple[str, List[str]]:
    """Synthesizes dynamic jump/hop cycle with squash & stretch, lagging ears, and reactive shadow."""
    active_layers: List[str] = []
    rules: List[str] = []
    ids = layers["ids"]
    lower_map = {i.lower(): i for i in ids}

    # Identify primary groups
    body_id = None
    for cand in ["body", "torso", "main", "rabbit", "character"]:
        for k in lower_map:
            if cand in k:
                body_id = lower_map[k]
                break
        if body_id:
            break

    shadow_id = None
    for k in lower_map:
        if "shadow" in k or "ground" in k:
            shadow_id = lower_map[k]
            break

    ear_ids = [lower_map[k] for k in lower_map if "ear" in k]
    leg_ids = [lower_map[k] for k in lower_map if "leg" in k or "paw" in k or "foot" in k]
    tail_ids = [lower_map[k] for k in lower_map if "tail" in k]

    hop_h = int(24 * amp)
    squash_y = f"{1.0 + (0.12 * amp):.3f}"
    squash_x = f"{1.0 - (0.10 * amp):.3f}"
    stretch_y = f"{1.0 - (0.08 * amp):.3f}"
    stretch_x = f"{1.0 + (0.08 * amp):.3f}"

    # Body keyframes
    rules.append(f"""
@keyframes motion-creature-hop {{
  0%, 100% {{
    transform: translateY(0px) scale(1, 1);
    animation-timing-function: cubic-bezier(0.3, 0.0, 0.2, 1);
  }}
  15% {{
    transform: translateY(3px) scale({squash_y}, {squash_x});
  }}
  35% {{
    transform: translateY(-{hop_h}px) scale({stretch_y}, {stretch_x});
    animation-timing-function: cubic-bezier(0.5, 0.0, 0.8, 0.5);
  }}
  55% {{
    transform: translateY(-{int(hop_h * 1.15)}px) scale(0.98, 1.02);
  }}
  75% {{
    transform: translateY(0px) scale({squash_y}, {squash_x});
  }}
  88% {{
    transform: translateY(-3px) scale(1.0, 1.0);
  }}
}}""")

    if body_id:
        active_layers.append(f"#{body_id} (Hop + Squash & Stretch)")
        rules.append(f"""
#{body_id} {{
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: motion-creature-hop {duration:.2f}s infinite;
}}""")
    else:
        # If no specific body ID, animate the whole SVG mark / root contents
        rules.append(f"""
svg > g:not(#shadow) {{
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: motion-creature-hop {duration:.2f}s infinite;
}}""")
        active_layers.append("Main Figure (Hop + Squash & Stretch)")

    # Ears lag & swing
    if ear_ids:
        rules.append(f"""
@keyframes motion-ear-left {{
  0%, 100% {{ transform: rotate(0deg); }}
  20% {{ transform: rotate(-{int(12 * amp)}deg); }}
  55% {{ transform: rotate({int(7 * amp)}deg); }}
  75% {{ transform: rotate(-{int(14 * amp)}deg); }}
}}
@keyframes motion-ear-right {{
  0%, 100% {{ transform: rotate(0deg); }}
  25% {{ transform: rotate({int(10 * amp)}deg); }}
  55% {{ transform: rotate(-{int(8 * amp)}deg); }}
  75% {{ transform: rotate({int(13 * amp)}deg); }}
}}""")
        for idx, eid in enumerate(ear_ids):
            anim_name = "motion-ear-left" if idx % 2 == 0 else "motion-ear-right"
            active_layers.append(f"#{eid} (Lagging Ear Swing)")
            rules.append(f"""
#{eid} {{
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: {anim_name} {duration:.2f}s ease-in-out infinite;
}}""")

    # Shadow pulse
    if shadow_id:
        active_layers.append(f"#{shadow_id} (Synchronized Ground Shadow)")
        rules.append(f"""
@keyframes motion-shadow-pulse {{
  0%, 100% {{ transform: scale(1.0); opacity: 0.8; }}
  15% {{ transform: scale(1.15); opacity: 0.95; }}
  55% {{ transform: scale(0.65); opacity: 0.35; }}
  75% {{ transform: scale(1.20); opacity: 0.95; }}
}}
#{shadow_id} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: motion-shadow-pulse {duration:.2f}s cubic-bezier(0.4, 0.0, 0.2, 1) infinite;
}}""")

    # Tail wiggle
    for tid in tail_ids:
        active_layers.append(f"#{tid} (Tail Wiggle)")
        rules.append(f"""
@keyframes motion-tail-wag {{
  0%, 100% {{ transform: rotate(0deg); }}
  50% {{ transform: rotate({int(15 * amp)}deg); }}
}}
#{tid} {{
  transform-box: fill-box;
  transform-origin: left center;
  animation: motion-tail-wag {duration * 0.6:.2f}s ease-in-out infinite;
}}""")

    return "\n".join(rules), active_layers


def build_vehicle_animation(layers: Dict[str, Any], duration: float, amp: float) -> Tuple[str, List[str]]:
    """Synthesizes vehicle dynamics: wheel spinning, suspension jitter, exhaust puff."""
    active_layers: List[str] = []
    rules: List[str] = []
    ids = layers["ids"]
    lower_map = {i.lower(): i for i in ids}

    wheel_ids = [lower_map[k] for k in lower_map if any(w in k for w in ["wheel", "tire", "rim"])]
    chassis_ids = [lower_map[k] for k in lower_map if any(w in k for w in ["chassis", "body", "car", "cab"])]
    exhaust_ids = [lower_map[k] for k in lower_map if any(w in k for w in ["exhaust", "smoke", "puff"])]
    shadow_ids = [lower_map[k] for k in lower_map if "shadow" in k]

    wheel_dur = max(0.3, duration * 0.5)

    rules.append(f"""
@keyframes motion-wheel-spin {{
  from {{ transform: rotate(0deg); }}
  to {{ transform: rotate(360deg); }}
}}
@keyframes motion-chassis-jitter {{
  0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
  25% {{ transform: translateY(-{1.5 * amp:.1f}px) rotate(-{0.25 * amp:.2f}deg); }}
  50% {{ transform: translateY({1.0 * amp:.1f}px) rotate({0.20 * amp:.2f}deg); }}
  75% {{ transform: translateY(-{1.8 * amp:.1f}px) rotate(-{0.20 * amp:.2f}deg); }}
}}
@keyframes motion-exhaust-smoke {{
  0% {{ transform: translate(0, 0) scale(0.6); opacity: 0.8; }}
  100% {{ transform: translate(-{25 * amp:.1f}px, -{12 * amp:.1f}px) scale(2.0); opacity: 0; }}
}}""")

    for wid in wheel_ids:
        active_layers.append(f"#{wid} (Wheel Spin)")
        rules.append(f"""
#{wid} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: motion-wheel-spin {wheel_dur:.2f}s linear infinite;
}}""")

    for cid in chassis_ids:
        active_layers.append(f"#{cid} (Suspension Jitter)")
        rules.append(f"""
#{cid} {{
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: motion-chassis-jitter {duration * 0.35:.2f}s ease-in-out infinite;
}}""")

    for eid in exhaust_ids:
        active_layers.append(f"#{eid} (Exhaust Smoke)")
        rules.append(f"""
#{eid} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: motion-exhaust-smoke {duration:.2f}s ease-out infinite;
}}""")

    for sid in shadow_ids:
        active_layers.append(f"#{sid} (Ground Contact Shadow)")
        rules.append(f"""
#{sid} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: motion-chassis-jitter {duration * 0.35:.2f}s ease-in-out infinite;
}}""")

    return "\n".join(rules), active_layers


def build_nature_animation(layers: Dict[str, Any], duration: float, amp: float) -> Tuple[str, List[str]]:
    """Synthesizes botanical sway, leaf flutter, petal breathing."""
    active_layers: List[str] = []
    rules: List[str] = []
    ids = layers["ids"]
    lower_map = {i.lower(): i for i in ids}

    stem_ids = [lower_map[k] for k in lower_map if "stem" in k or "trunk" in k or "branch" in k]
    leaf_ids = [lower_map[k] for k in lower_map if "leaf" in k or "foliage" in k]
    petal_ids = [lower_map[k] for k in lower_map if "petal" in k or "bloom" in k or "flower" in k]

    rules.append(f"""
@keyframes motion-stem-sway {{
  0%, 100% {{ transform: rotate(0deg); }}
  50% {{ transform: rotate({3.5 * amp:.1f}deg); }}
}}
@keyframes motion-leaf-flutter {{
  0%, 100% {{ transform: rotate(0deg) scale(1.0); }}
  33% {{ transform: rotate(-{4.0 * amp:.1f}deg) scale(1.02); }}
  66% {{ transform: rotate({3.0 * amp:.1f}deg) scale(0.98); }}
}}
@keyframes motion-petal-breathe {{
  0%, 100% {{ transform: scale(1.0); }}
  50% {{ transform: scale({1.0 + (0.05 * amp):.3f}); }}
}}""")

    for sid in stem_ids:
        active_layers.append(f"#{sid} (Stem Sway)")
        rules.append(f"""
#{sid} {{
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: motion-stem-sway {duration:.2f}s ease-in-out infinite;
}}""")

    for lid in leaf_ids:
        active_layers.append(f"#{lid} (Leaf Flutter)")
        rules.append(f"""
#{lid} {{
  transform-box: fill-box;
  transform-origin: left bottom;
  animation: motion-leaf-flutter {duration * 0.75:.2f}s ease-in-out infinite;
}}""")

    for pid in petal_ids:
        active_layers.append(f"#{pid} (Petal Breathing)")
        rules.append(f"""
#{pid} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: motion-petal-breathe {duration:.2f}s ease-in-out infinite;
}}""")

    return "\n".join(rules), active_layers


def build_background_animation(
    root: ET.Element, vb: Tuple[float, float, float, float], preset: str, duration: float, amp: float
) -> Tuple[str, List[str]]:
    """Synthesizes spatial phase propagation across vector background elements."""
    active_layers: List[str] = [f"Background Elements (Spatial {preset.title()})"]
    rules: List[str] = []

    # Check for animate_svg_motion_bg module
    try:
        from animate_svg_motion_bg import (
            collect_animated_elements,
            generate_css_keyframes,
            calculate_element_phase,
        )
        keyframes = generate_css_keyframes(duration, amp * 0.35)
        rules.append(keyframes)

        elements = collect_animated_elements(root, vb)
        cx0 = vb[0] + vb[2] / 2
        cy0 = vb[1] + vb[3] / 2
        diag = math.sqrt(vb[2] ** 2 + vb[3] ** 2)

        for idx, (el, cx, cy) in enumerate(elements):
            cls_name = f"mbg-el-{idx}"
            cur_cls = el.attrib.get("class", "").strip()
            el.attrib["class"] = f"{cur_cls} {cls_name}".strip() if cur_cls else cls_name

            phase = calculate_element_phase(preset, cx, cy, cx0, cy0, vb[2], vb[3], diag, 45.0)
            delay = -(phase * duration)

            rules.append(f"""
.{cls_name} {{
  transform-box: fill-box;
  transform-origin: center;
  animation: mbg-{preset} {duration:.2f}s ease-in-out infinite;
  animation-delay: {delay:.3f}s;
}}""")
    except ImportError:
        # Fallback ambient pulse
        rules.append(f"""
@keyframes mbg-ambient-wave {{
  0%, 100% {{ transform: scale({1.0 - 0.15 * amp:.2f}); opacity: 0.85; }}
  50% {{ transform: scale({1.0 + 0.15 * amp:.2f}); opacity: 1.0; }}
}}
svg > g, svg > circle, svg > path:not([id*="bg"]) {{
  transform-box: fill-box;
  transform-origin: center;
  animation: mbg-ambient-wave {duration:.2f}s ease-in-out infinite;
}}""")

    return "\n".join(rules), active_layers


def assemble_motion_css(
    root: ET.Element,
    category: str,
    preset: str,
    duration: float,
    amplitude: float,
    custom_css: Optional[str] = None,
) -> Tuple[str, str, List[str]]:
    """Generates complete CSS keyframes & rules tailored to the subject."""
    layers = inspect_svg_layers(root)
    vb = extract_viewbox(root)

    # Resolve category if auto
    if category == "auto":
        detected_category = detect_subject_category(layers)
    else:
        detected_category = category

    # Default category timings
    if duration is None:
        durations = {
            "creature": 1.6,
            "vehicle": 0.8,
            "nature": 4.5,
            "mechanical": 2.0,
            "background": 5.0,
            "custom": 2.0,
        }
        duration = durations.get(detected_category, 2.0)

    if amplitude is None:
        amplitude = 1.0

    if detected_category == "custom" and custom_css:
        css = custom_css
        active_layers = ["Custom User Keyframes"]
    elif detected_category == "creature":
        css, active_layers = build_creature_animation(layers, duration, amplitude)
    elif detected_category == "vehicle":
        css, active_layers = build_vehicle_animation(layers, duration, amplitude)
    elif detected_category == "nature":
        css, active_layers = build_nature_animation(layers, duration, amplitude)
    elif detected_category == "mechanical":
        # Vehicle mechanics handles gears / wheels similarly
        css, active_layers = build_vehicle_animation(layers, duration, amplitude)
    else:
        css, active_layers = build_background_animation(root, vb, preset, duration, amplitude)

    return css, detected_category, active_layers


def build_standalone_animated_svg(tree: ET.ElementTree, css: str) -> str:
    """Clones tree, embeds pure CSS into <style>, and returns hardware-accelerated SVG string."""
    import copy
    root = copy.deepcopy(tree.getroot())
    strip_all_namespaces(root)

    # Insert or prepend <style>
    style_el = ET.Element("style")
    style_el.text = f"\n/* Hardware-Accelerated Contextual Motion */\n{css}\n"
    root.insert(0, style_el)

    raw_xml = ET.tostring(root, encoding="utf-8").decode("utf-8")
    return clean_xml_string(raw_xml)


def build_interactive_preview_html(
    svg_string: str,
    title: str,
    subject_name: str,
    category: str,
    active_layers: List[str],
    css_rules: str,
    palettes: Optional[Dict[str, Dict[str, str]]] = None,
    motion_styles: Optional[Dict[str, str]] = None,
) -> str:
    """Creates a high-polish, responsive HTML preview with telemetry & HUD controls."""
    safe_title = html.escape(title)
    safe_subject = html.escape(subject_name)
    layers_badge = " ".join([f'<span class="badge layer-badge">{html.escape(l)}</span>' for l in active_layers])

    palettes = palettes or {}
    palettes_json = json.dumps(palettes, ensure_ascii=False)
    has_palettes = len(palettes) > 0
    palette_options = ""
    if has_palettes:
        for idx, name in enumerate(palettes.keys()):
            palette_options += f'<option value="{html.escape(name)}">{html.escape(name)}</option>\\n'

    motion_styles = motion_styles or {"Primary Motion": css_rules}
    motion_styles_json = json.dumps(motion_styles, ensure_ascii=False)
    has_motion_styles = len(motion_styles) > 1
    motion_options = ""
    if has_motion_styles:
        for idx, name in enumerate(motion_styles.keys()):
            motion_options += f'<option value="{html.escape(name)}">{html.escape(name)}</option>\\n'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      --bg: #0a0c10;
      --card-bg: rgba(18, 22, 32, 0.75);
      --border: rgba(255, 255, 255, 0.12);
      --accent: #38bdf8;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background: var(--bg);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }}

    #stage-container {{
      position: relative;
      width: 100%;
      height: 100%;
      display: grid;
      place-items: center;
      padding: 20px;
    }}

    #svg-stage {{
      position: relative;
      transition: border-radius 0.3s ease, box-shadow 0.3s ease;
    }}

    /* 16:9 Cinematic Fit: fits shortest side (cover) with pan navigation */
    #svg-stage.mode-16-9 {{
      width: min(96vw, calc((100vh - 40px) * 16 / 9), 1360px);
      aspect-ratio: 16 / 9;
      overflow: hidden;
      border-radius: 16px;
      background: #000;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.1);
      position: relative;
      cursor: grab;
      user-select: none;
      touch-action: none;
    }}
    #svg-stage.mode-16-9.is-dragging {{
      cursor: grabbing;
    }}

    #pan-canvas {{
      position: absolute;
      left: 0;
      top: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      will-change: transform;
      transform-origin: 0 0;
    }}

    #pan-canvas svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    /* Contained: original bounds */
    #svg-stage.mode-contained {{
      position: relative;
      width: min(96vw, 1360px);
      max-height: 85vh;
      display: flex;
      align-items: center;
      justify-content: center;
      filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.45));
      overflow: visible;
      cursor: default;
    }}

    #svg-stage.mode-contained #pan-canvas {{
      position: static;
      width: 100% !important;
      height: auto !important;
      transform: none !important;
    }}

    #svg-stage.mode-contained svg {{
      width: 100%;
      height: auto;
      max-height: 70vh;
      display: block;
    }}
  </style>

  <!-- Injected Contextual Keyframes (Dynamic Motion Style Switcher) -->
  <style id="motion-css-tag">
    {css_rules}
  </style>

  <style>
    /* Ultra-Slim Translucent Glass HUD Dock: 2 Rows, Nearly Full Screen Width */
    #hud-panel {{
      position: absolute;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      width: calc(100% - 32px);
      max-width: 1320px;
      box-sizing: border-box;
      background: rgba(10, 14, 23, 0.45);
      backdrop-filter: blur(16px) saturate(180%);
      -webkit-backdrop-filter: blur(16px) saturate(180%);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 16px;
      padding: 8px 16px;
      display: flex;
      flex-direction: column;
      gap: 7px;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.50);
      z-index: 100;
      transition: background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
      user-select: none;
    }}
    #hud-panel:hover {{
      background: rgba(10, 14, 23, 0.70);
      border-color: rgba(255, 255, 255, 0.24);
      box-shadow: 0 14px 48px rgba(0, 0, 0, 0.60);
    }}

    .hud-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      gap: 12px;
      white-space: nowrap;
    }}

    .hud-row.hud-row-secondary {{
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 7px;
    }}

    .hud-group-left, .hud-group-center, .hud-group-right {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }}

    .hud-divider {{
      width: 1px;
      height: 16px;
      background: rgba(255, 255, 255, 0.12);
      flex-shrink: 0;
    }}

    .hud-meta-inline {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }}

    .subject-title {{
      font-size: 12px;
      font-weight: 700;
      color: var(--text);
    }}

    .badge {{
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 2px 6px;
      border-radius: 9999px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
      line-height: 1.2;
    }}

    #fps-badge {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 10px;
      color: #10b981;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 1px 5px;
      border-radius: 4px;
      line-height: 1.2;
    }}

    .hud-timer-badge {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 11px;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
      color: #94a3b8;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.2);
      padding: 3px 8px;
      border-radius: 9999px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
      white-space: nowrap;
      height: 24px;
      box-sizing: border-box;
      width: 154px;
      justify-content: center;
      flex-shrink: 0;
    }}

    #loop-time-cur {{
      display: inline-block;
      width: 38px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
    }}

    #loop-time-total {{
      display: inline-block;
      width: 38px;
      text-align: left;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
    }}

    #speed-val {{
      display: inline-block;
      width: 30px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    #pan-val {{
      display: inline-block;
      width: 34px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    .hud-pan-group {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: var(--text-muted);
      transition: opacity 0.2s ease;
      white-space: nowrap;
    }}

    .hud-pan-group.disabled {{
      opacity: 0.3;
      pointer-events: none;
    }}

    .hud-pan-btn-group {{
      display: inline-flex;
      align-items: center;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 9999px;
      padding: 1px 3px;
      gap: 2px;
      height: 24px;
      box-sizing: border-box;
    }}

    .hud-mini-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 10px;
      padding: 2px 5px;
      border-radius: 9999px;
      cursor: pointer;
      line-height: 1;
      transition: all 0.15s ease;
    }}
    .hud-mini-btn:hover {{
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }}
    .hud-mini-btn.active {{
      background: var(--accent);
      color: #000;
      font-weight: 700;
    }}
    .hud-btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      height: 24px;
      white-space: nowrap;
    }}
    .hud-btn:hover {{
      background: rgba(255, 255, 255, 0.20);
      border-color: var(--accent);
      color: #fff;
    }}

    .hud-slider-group {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: var(--text-muted);
      white-space: nowrap;
    }}

    .hud-slider {{
      -webkit-appearance: none;
      appearance: none;
      width: 60px;
      height: 3px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 2px;
      outline: none;
    }}
    .hud-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
      cursor: pointer;
    }}

    .hud-select {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      height: 24px;
      transition: all 0.15s ease;
    }}
    .hud-select:hover, .hud-select:focus {{
      background: rgba(255, 255, 255, 0.18);
      border-color: var(--accent);
    }}
    .hud-select option {{
      background: #181c24;
      color: #fff;
    }}

    /* Export MP4 Modal Dialog */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.70);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}

    .modal-card {{
      width: 100%;
      max-width: 540px;
      background: rgba(18, 24, 38, 0.94);
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 20px;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.08);
      overflow: hidden;
      color: var(--text);
      animation: modalFadeIn 0.2s ease-out;
    }}

    @keyframes modalFadeIn {{
      from {{ opacity: 0; transform: scale(0.96) translateY(8px); }}
      to {{ opacity: 1; transform: scale(1) translateY(0); }}
    }}

    .modal-header {{
      padding: 16px 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .modal-title {{
      font-size: 14px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .modal-subtitle {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 16px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all 0.15s ease;
    }}
    .modal-close:hover {{
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
    }}

    .modal-body {{
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .modal-field {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .modal-label {{
      font-size: 11px;
      font-weight: 600;
      color: #cbd5e1;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .modal-select {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #f1f5f9;
      padding: 7px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
      outline: none;
      transition: border-color 0.15s ease;
    }}
    .modal-select:hover, .modal-select:focus {{
      border-color: var(--accent);
      background: rgba(255, 255, 255, 0.10);
    }}
    .modal-select option {{
      background: #181c24;
      color: #fff;
    }}

    .modal-grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    .modal-radio-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 12px;
    }}

    .modal-radio {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      color: #cbd5e1;
    }}

    .modal-info-box {{
      background: rgba(56, 189, 248, 0.06);
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 10px;
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 11px;
    }}

    .info-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .info-label {{
      color: #94a3b8;
    }}
    .info-val {{
      font-family: ui-monospace, SFMono-Regular, monospace;
      font-weight: 600;
      color: #f1f5f9;
    }}

    .progress-bar-bg {{
      width: 100%;
      height: 6px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 3px;
      overflow: hidden;
    }}

    .progress-bar-fill {{
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, var(--accent), #10b981);
      transition: width 0.1s linear;
    }}

    .modal-footer {{
      padding: 14px 20px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }}

    .modal-btn {{
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      border: none;
    }}

    .modal-btn-secondary {{
      background: rgba(255, 255, 255, 0.08);
      color: #cbd5e1;
      border: 1px solid rgba(255, 255, 255, 0.12);
    }}
    .modal-btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }}

    .modal-btn-primary {{
      background: var(--accent);
      color: #04121d;
      font-weight: 700;
    }}
    .modal-btn-primary:hover {{
      filter: brightness(1.15);
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
    }}
    .modal-btn-primary:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
      filter: none;
    }}
  </style>
</head>
<body>
  <div id="stage-container">
    <div id="svg-stage" class="mode-16-9">
      <div id="pan-canvas">
        {svg_string}
      </div>

      <div id="hud-panel">
        <!-- Row 1: Telemetry, Loop Timer & Customization Controls -->
        <div class="hud-row hud-row-primary">
          <div class="hud-group-left">
            <div class="hud-meta-inline">
              <span class="subject-title">{safe_subject}</span>
              <span class="badge">{category.upper()}</span>
              <span id="fps-badge">60 FPS</span>
            </div>
          </div>

          <div class="hud-group-center">
            <div class="hud-timer-badge" title="1x Loop Cycle Duration (Scales with speed)">
              <span style="opacity: 0.75;">⏱ 1x Loop:</span>
              <span id="loop-time-cur" style="color: var(--accent); font-weight: 700;">00.0s</span>
              <span style="opacity: 0.35;">/</span>
              <span id="loop-time-total" style="color: var(--text);">10.0s</span>
            </div>
          </div>

          <div class="hud-group-right">
            {f'''<div class="hud-motion-group" style="display: flex; align-items: center; gap: 4px;">
              <span style="font-size: 11px; opacity: 0.8;" title="Motion Style">🎬</span>
              <select id="motion-select" class="hud-select" title="Switch Motion Style">
                {motion_options}
              </select>
            </div>''' if has_motion_styles else ''}

            {f'''<div class="hud-palette-group" style="display: flex; align-items: center; gap: 4px;">
              <span style="font-size: 11px; opacity: 0.8;" title="Color Theme">🎨</span>
              <select id="palette-select" class="hud-select" title="Switch Color Theme">
                {palette_options}
              </select>
            </div>''' if has_palettes else ''}
          </div>
        </div>

        <!-- Row 2: Playback Mechanics, Speed, Pan Framing & Actions -->
        <div class="hud-row hud-row-secondary">
          <div class="hud-group-left">
            <button id="toggle-play-btn" class="hud-btn" title="Play / Pause Animation">⏸ Pause</button>
            <div class="hud-slider-group" title="Playback Speed Multiplier">
              <span>⚡</span>
              <input type="range" id="speed-slider" class="hud-slider" min="0.25" max="2.5" step="0.05" value="1.0">
              <span id="speed-val">1.0x</span>
            </div>
          </div>

          <div class="hud-group-center">
            <div id="hud-pan-group" class="hud-pan-group" title="Pan Framing Navigator">
              <span id="pan-label">↔</span>
              <div class="hud-pan-btn-group">
                <button id="pan-btn-min" class="hud-mini-btn" title="Align Min (0%)">◀</button>
                <input type="range" id="pan-slider" class="hud-slider" min="0" max="100" step="1" value="50">
                <button id="pan-btn-mid" class="hud-mini-btn" title="Center (50%)">⯀</button>
                <button id="pan-btn-max" class="hud-mini-btn" title="Align Max (100%)">▶</button>
              </div>
              <span id="pan-val">50%</span>
            </div>
          </div>

          <div class="hud-group-right">
            <button id="toggle-frame-btn" class="hud-btn" title="Toggle 16:9 Canvas / Contained">🔲 16:9</button>
            <button id="export-svg-btn" class="hud-btn" title="Export Standalone Animated SVG">⬇ SVG</button>
            <button id="export-mp4-btn" class="hud-btn" title="Export MP4 Video (Adobe Stock Ready)">🎥 MP4</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Export MP4 Modal Dialog -->
  <div id="export-modal-backdrop" class="modal-backdrop" style="display: none;">
    <div class="modal-card">
      <div class="modal-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 18px;">🎥</span>
          <div>
            <div class="modal-title">Export MP4 Video</div>
            <div class="modal-subtitle">Broadcast-Grade CFR 60 FPS • Adobe Stock Ready</div>
          </div>
        </div>
        <button id="modal-close-btn" class="modal-close" title="Tutup">✕</button>
      </div>

      <div class="modal-body">
        <div class="modal-field">
          <label class="modal-label">Resolusi Video</label>
          <select id="modal-res-select" class="modal-select">
            <option value="1920x1080" selected>1080p Full HD (1920 × 1080) — Standar Adobe Stock</option>
            <option value="3840x2160">4K Ultra HD (3840 × 2160) — Premium Stock</option>
            <option value="1280x720">720p HD (1280 × 720) — File Ringan</option>
          </select>
        </div>

        <div class="modal-grid-2">
          <div class="modal-field">
            <label class="modal-label">Jumlah Loop (xLoop)</label>
            <select id="modal-loops-select" class="modal-select">
              <option value="1">1x Loop</option>
              <option value="2" selected>2x Loops (Rekomendasi Stock: 15–30s)</option>
              <option value="3">3x Loops</option>
              <option value="5">5x Loops</option>
            </select>
          </div>

          <div class="modal-field">
            <label class="modal-label">Framing Visual (Pan)</label>
            <select id="modal-pan-select" class="modal-select">
              <option id="modal-pan-opt-current" value="current" selected>WYSIWYG: Ikuti Pan Layar (50%)</option>
              <option value="center">Reset ke Tengah Sempurna (50%)</option>
            </select>
          </div>
        </div>

        <div class="modal-field">
          <label class="modal-label">Kecepatan Render</label>
          <div class="modal-radio-group">
            <label class="modal-radio">
              <input type="radio" name="modal-speed-mode" value="current" checked>
              <span>Gunakan speed aktif (<span id="modal-speed-mode-display">1.0x</span>)</span>
            </label>
            <label class="modal-radio">
              <input type="radio" name="modal-speed-mode" value="default">
              <span>Reset ke kecepatan normal (1.0x)</span>
            </label>
          </div>
        </div>

        <div class="modal-info-box">
          <div class="info-row">
            <span class="info-label">⏱ Total Durasi:</span>
            <span id="modal-duration-display" class="info-val">20.0s</span>
          </div>
          <div class="info-row">
            <span class="info-label">🎞 Total Frames:</span>
            <span id="modal-frames-display" class="info-val">1200 frames @ 60 FPS</span>
          </div>
          <div class="info-row">
            <span class="info-label">✨ Kualitas:</span>
            <span class="info-val" style="color: #10b981;">Clean Canvas (Tanpa HUD) • Seamless Loop</span>
          </div>
        </div>

        <div id="modal-progress-wrap" style="display: none; margin-top: 6px;">
          <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
            <span id="modal-progress-status" style="color: var(--accent);">Rendering frames...</span>
            <span id="modal-progress-pct" style="font-weight: 700; color: #fff;">0%</span>
          </div>
          <div class="progress-bar-bg">
            <div id="modal-progress-bar" class="progress-bar-fill"></div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button id="modal-cancel-btn" class="modal-btn modal-btn-secondary">Batal</button>
        <button id="modal-start-btn" class="modal-btn modal-btn-primary">Mulai Export MP4</button>
      </div>
    </div>
  </div>

  <script>
    const stage = document.getElementById("svg-stage");
    const panCanvas = document.getElementById("pan-canvas");
    const svgElem = panCanvas.querySelector("svg");
    const speedSlider = document.getElementById("speed-slider");
    const speedVal = document.getElementById("speed-val");
    const toggleFrameBtn = document.getElementById("toggle-frame-btn");
    const togglePlayBtn = document.getElementById("toggle-play-btn");
    const exportBtn = document.getElementById("export-svg-btn");
    const fpsBadge = document.getElementById("fps-badge");

    const panGroup = document.getElementById("hud-pan-group");
    const panLabel = document.getElementById("pan-label");
    const panSlider = document.getElementById("pan-slider");
    const panVal = document.getElementById("pan-val");
    const panBtnMin = document.getElementById("pan-btn-min");
    const panBtnMid = document.getElementById("pan-btn-mid");
    const panBtnMax = document.getElementById("pan-btn-max");

    let is169Mode = true;
    let panProgress = 0.5; // 0.0 to 1.0 (default 50% = centered)
    let panAxis = "x";
    let maxPanX = 0;
    let maxPanY = 0;
    let currentOffsetX = 0;
    let currentOffsetY = 0;

    function getSvgViewBoxDimensions() {{
      if (svgElem.viewBox && svgElem.viewBox.baseVal && svgElem.viewBox.baseVal.width > 0) {{
        return {{
          width: svgElem.viewBox.baseVal.width,
          height: svgElem.viewBox.baseVal.height,
        }};
      }}
      const vbAttr = svgElem.getAttribute("viewBox");
      if (vbAttr) {{
        const parts = vbAttr.trim().split(/[\\s,]+/).map(Number);
        if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {{
          return {{ width: parts[2], height: parts[3] }};
        }}
      }}
      return {{
        width: svgElem.clientWidth || 1000,
        height: svgElem.clientHeight || 562.5,
      }};
    }}

    function applyPanOffset() {{
      if (!is169Mode) return;
      currentOffsetX = -(panProgress * maxPanX);
      currentOffsetY = -(panProgress * maxPanY);

      panCanvas.style.transform = `translate3d(${{currentOffsetX.toFixed(2)}}px, ${{currentOffsetY.toFixed(2)}}px, 0)`;

      const pct = Math.round(panProgress * 100);
      panSlider.value = pct;
      panVal.textContent = `${{pct}}%`;

      panBtnMin.classList.toggle("active", pct <= 2);
      panBtnMid.classList.toggle("active", pct >= 48 && pct <= 52);
      panBtnMax.classList.toggle("active", pct >= 98);
    }}

    function updateFramingAndPan() {{
      if (!is169Mode) {{
        stage.className = "mode-contained";
        panGroup.classList.add("disabled");
        toggleFrameBtn.textContent = "🖼 Contained";
        svgElem.setAttribute("preserveAspectRatio", "xMidYMid meet");
        return;
      }}

      stage.className = "mode-16-9";
      panGroup.classList.remove("disabled");
      toggleFrameBtn.textContent = "🔲 16:9 Canvas";
      svgElem.setAttribute("preserveAspectRatio", "none");

      const stageW = stage.clientWidth;
      const stageH = stage.clientHeight;
      if (!stageW || !stageH) return;

      const vb = getSvgViewBoxDimensions();
      const vbAspect = vb.width / vb.height;
      const stageAspect = stageW / stageH;

      let canvasW, canvasH;

      if (vbAspect >= stageAspect) {{
        // SVG is wider than 16:9 (shortest side is height)
        canvasH = stageH;
        canvasW = stageH * vbAspect;
        panAxis = "x";
        maxPanX = Math.max(0, canvasW - stageW);
        maxPanY = 0;

        panLabel.innerHTML = "↔";
        panLabel.title = "Pan X Axis (Horizontal)";
        panBtnMin.innerHTML = "◀";
        panBtnMin.title = "Align Left (0%)";
        panBtnMax.innerHTML = "▶";
        panBtnMax.title = "Align Right (100%)";
      }} else {{
        // SVG is taller than 16:9 (shortest side is width)
        canvasW = stageW;
        canvasH = stageW / vbAspect;
        panAxis = "y";
        maxPanX = 0;
        maxPanY = Math.max(0, canvasH - stageH);

        panLabel.innerHTML = "↕";
        panLabel.title = "Pan Y Axis (Vertical)";
        panBtnMin.innerHTML = "▲";
        panBtnMin.title = "Align Top (0%)";
        panBtnMax.innerHTML = "▼";
        panBtnMax.title = "Align Bottom (100%)";
      }}

      panCanvas.style.width = `${{canvasW}}px`;
      panCanvas.style.height = `${{canvasH}}px`;

      applyPanOffset();
    }}

    panSlider.addEventListener("input", (e) => {{
      panProgress = Math.max(0, Math.min(1, parseFloat(e.target.value) / 100));
      panCanvas.style.transition = "";
      applyPanOffset();
    }});

    function setPanSmooth(val) {{
      panProgress = val;
      panCanvas.style.transition = "transform 0.25s ease-out";
      applyPanOffset();
      setTimeout(() => {{ panCanvas.style.transition = ""; }}, 250);
    }}

    panBtnMin.addEventListener("click", () => setPanSmooth(0.0));
    panBtnMid.addEventListener("click", () => setPanSmooth(0.5));
    panBtnMax.addEventListener("click", () => setPanSmooth(1.0));

    // Pointer Drag-to-Pan on Stage
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let startOffsetX = 0;
    let startOffsetY = 0;

    stage.addEventListener("pointerdown", (e) => {{
      if (!is169Mode) return;
      if (e.target.closest("#hud-panel")) return;

      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startOffsetX = currentOffsetX;
      startOffsetY = currentOffsetY;

      stage.classList.add("is-dragging");
      panCanvas.style.transition = "none";
      stage.setPointerCapture(e.pointerId);
    }});

    stage.addEventListener("pointermove", (e) => {{
      if (!isDragging || !is169Mode) return;

      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      if (panAxis === "x" && maxPanX > 0) {{
        currentOffsetX = Math.max(-maxPanX, Math.min(0, startOffsetX + dx));
        panProgress = -currentOffsetX / maxPanX;
      }} else if (panAxis === "y" && maxPanY > 0) {{
        currentOffsetY = Math.max(-maxPanY, Math.min(0, startOffsetY + dy));
        panProgress = -currentOffsetY / maxPanY;
      }}

      applyPanOffset();
    }});

    function endDrag(e) {{
      if (!isDragging) return;
      isDragging = false;
      stage.classList.remove("is-dragging");
      try {{
        if (stage.hasPointerCapture(e.pointerId)) {{
          stage.releasePointerCapture(e.pointerId);
        }}
      }} catch (err) {{}}
    }}

    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);

    const resizeObserver = new ResizeObserver(() => {{
      if (is169Mode) {{
        updateFramingAndPan();
      }}
    }});
    resizeObserver.observe(stage);

    toggleFrameBtn.addEventListener("click", () => {{
      is169Mode = !is169Mode;
      updateFramingAndPan();
    }});

    // Palette / Theme Switcher
    const PALETTES = {palettes_json};
    let currentThemeName = Object.keys(PALETTES)[0] || "";

    function applyTheme(themeName) {{
      const theme = PALETTES[themeName];
      if (!theme) return;
      currentThemeName = themeName;
      for (const [id, color] of Object.entries(theme)) {{
        const el = svgElem.querySelector("#" + CSS.escape(id));
        if (el) {{
          el.style.transition = "fill 0.4s ease, stroke 0.4s ease";
          if (el.getAttribute("stroke") && el.getAttribute("stroke") !== "none") {{
            el.setAttribute("stroke", color);
            el.style.stroke = color;
          }} else {{
            el.setAttribute("fill", color);
            el.style.fill = color;
          }}
        }}
      }}
      applySpeed(currentSpeed);
    }}

    const paletteSelect = document.getElementById("palette-select");
    if (paletteSelect) {{
      paletteSelect.addEventListener("change", (e) => {{
        applyTheme(e.target.value);
      }});
    }}

    // Real-time FPS Telemetry
    let frameCount = 0;
    let lastTime = performance.now();
    function trackFps(now) {{
      frameCount++;
      if (now - lastTime >= 1000) {{
        fpsBadge.textContent = `${{frameCount}} FPS`;
        frameCount = 0;
        lastTime = now;
      }}
      requestAnimationFrame(trackFps);
    }}
    requestAnimationFrame(trackFps);

    // Speed Multiplier via Web Animations API (glitch-free continuous playbackRate)
    let currentSpeed = 1.0;
    function applySpeed(speed) {{
      currentSpeed = speed;
      speedVal.textContent = `${{speed.toFixed(1)}}x`;
      const anims = svgElem.getAnimations({{ subtree: true }});
      anims.forEach(anim => {{
        anim.playbackRate = speed;
      }});
    }}

    speedSlider.addEventListener("input", (e) => {{
      applySpeed(parseFloat(e.target.value));
    }});

    // Play / Pause Toggle
    let isPlaying = true;
    togglePlayBtn.addEventListener("click", () => {{
      isPlaying = !isPlaying;
      const anims = svgElem.getAnimations({{ subtree: true }});
      if (anims.length > 0) {{
        anims.forEach(anim => {{
          if (isPlaying) {{
            anim.play();
          }} else {{
            anim.pause();
          }}
        }});
      }}
      const state = isPlaying ? "running" : "paused";
      svgElem.querySelectorAll("*").forEach(el => {{
        el.style.animationPlayState = state;
      }});
      togglePlayBtn.textContent = isPlaying ? "⏸ Pause" : "▶ Play";
    }});

    // Motion Style Switcher
    const MOTION_STYLES = {motion_styles_json};
    let currentMotionStyleName = Object.keys(MOTION_STYLES)[0] || "";

    function applyMotionStyle(styleName) {{
      const css = MOTION_STYLES[styleName];
      if (!css) return;
      currentMotionStyleName = styleName;
      const tag = document.getElementById("motion-css-tag");
      if (tag) {{
        tag.textContent = `\\n${{css}}\\n`;
      }}
      // Force layout/style recalibration so Web Animations picks up newly initialized animations
      void svgElem.offsetHeight;
      applySpeed(currentSpeed);
      baseLoopDuration = 0;
      baseLoopDuration = detectBaseLoopDuration();
    }}

    const motionSelect = document.getElementById("motion-select");
    if (motionSelect) {{
      motionSelect.addEventListener("change", (e) => {{
        applyMotionStyle(e.target.value);
      }});
    }}

    // Export Standalone Animated SVG
    exportBtn.addEventListener("click", () => {{
      const svgClone = svgElem.cloneNode(true);

      // Apply active theme to clone
      if (currentThemeName && PALETTES[currentThemeName]) {{
        const activeTheme = PALETTES[currentThemeName];
        for (const [id, color] of Object.entries(activeTheme)) {{
          const el = svgClone.querySelector("#" + CSS.escape(id));
          if (el) {{
            if (el.getAttribute("stroke") && el.getAttribute("stroke") !== "none") {{
              el.setAttribute("stroke", color);
              el.style.stroke = color;
            }} else {{
              el.setAttribute("fill", color);
              el.style.fill = color;
            }}
          }}
        }}
      }}

      // WYSIWYG Speed Scaling: scale all animation durations if speed != 1.0
      let activeCss = (MOTION_STYLES && currentMotionStyleName && MOTION_STYLES[currentMotionStyleName]) 
        ? MOTION_STYLES[currentMotionStyleName] 
        : `{css_rules}`;

      if (currentSpeed && currentSpeed !== 1.0) {{
        activeCss = activeCss.replace(/(\\b\\d+(?:\\.\\d+)?)\\s*s\\b/g, (match, numStr) => {{
          const num = parseFloat(numStr);
          if (num > 0) {{
            const scaled = num / currentSpeed;
            return `${{scaled.toFixed(2)}}s`;
          }}
          return match;
        }});
      }}

      // WYSIWYG Framing & Pan: If 16:9 mode is active, crop the viewBox to the exact 16:9 framing and pan position
      if (is169Mode) {{
        const vb = getSvgViewBoxDimensions();
        const vbAspect = vb.width / vb.height;
        const targetAspect = 16 / 9;

        let origX = 0, origY = 0;
        const vbAttr = svgElem.getAttribute("viewBox");
        if (vbAttr) {{
          const parts = vbAttr.trim().split(/[\\s,]+/).map(Number);
          if (parts.length === 4) {{
            origX = parts[0] || 0;
            origY = parts[1] || 0;
          }}
        }}

        let cropW = vb.width, cropH = vb.height, cropX = origX, cropY = origY;
        if (vbAspect >= targetAspect) {{
          cropH = vb.height;
          cropW = vb.height * targetAspect;
          const overflow = vb.width - cropW;
          cropX = origX + (panProgress * overflow);
        }} else {{
          cropW = vb.width;
          cropH = vb.width / targetAspect;
          const overflow = vb.height - cropH;
          cropY = origY + (panProgress * overflow);
        }}
        svgClone.setAttribute("viewBox", `${{cropX.toFixed(2)}} ${{cropY.toFixed(2)}} ${{cropW.toFixed(2)}} ${{cropH.toFixed(2)}}`);
        svgClone.setAttribute("width", "1920");
        svgClone.setAttribute("height", "1080");
        svgClone.setAttribute("preserveAspectRatio", "xMidYMid meet");
      }} else {{
        const vb = getSvgViewBoxDimensions();
        svgClone.setAttribute("width", String(vb.width));
        svgClone.setAttribute("height", String(vb.height));
        svgClone.setAttribute("preserveAspectRatio", "xMidYMid meet");
      }}

      const styleEl = document.createElement("style");
      styleEl.textContent = `\\n${{activeCss}}\\n`;
      svgClone.insertBefore(styleEl, svgClone.firstChild);

      const serializer = new XMLSerializer();
      const svgStr = serializer.serializeToString(svgClone);
      const blob = new Blob([svgStr], {{ type: "image/svg+xml;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeMotion = currentMotionStyleName ? `_${{currentMotionStyleName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}}` : "";
      const safeTheme = currentThemeName ? `_${{currentThemeName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}}` : "";
      const frameTag = is169Mode ? "_16x9" : "";
      const speedTag = (currentSpeed !== 1.0) ? `_${{currentSpeed.toFixed(1)}}x` : "";
      a.download = `{safe_subject}${{safeMotion}}${{safeTheme}}${{frameTag}}${{speedTag}}_motion.svg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }});

    // Export MP4 Video Modal & Frame-Stepping Recorder (Adobe Stock Ready)
    const exportMp4Btn = document.getElementById("export-mp4-btn");
    const modalBackdrop = document.getElementById("export-modal-backdrop");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalStartBtn = document.getElementById("modal-start-btn");
    const modalResSelect = document.getElementById("modal-res-select");
    const modalLoopsSelect = document.getElementById("modal-loops-select");
    const modalPanSelect = document.getElementById("modal-pan-select");
    const modalPanVal = document.getElementById("modal-pan-val");
    const modalSpeedDisplay = document.getElementById("modal-speed-mode-display");
    const modalDurationDisplay = document.getElementById("modal-duration-display");
    const modalFramesDisplay = document.getElementById("modal-frames-display");
    const modalProgressWrap = document.getElementById("modal-progress-wrap");
    const modalProgressBar = document.getElementById("modal-progress-bar");
    const modalProgressStatus = document.getElementById("modal-progress-status");
    const modalProgressPct = document.getElementById("modal-progress-pct");

    function updateModalCalculations() {{
      const speedMode = document.querySelector('input[name="modal-speed-mode"]:checked')?.value || "current";
      const activeSpd = speedMode === "current" ? currentSpeed : 1.0;
      if (modalSpeedDisplay) modalSpeedDisplay.textContent = `${{activeSpd.toFixed(1)}}x`;
      const panOpt = document.getElementById("modal-pan-opt-current");
      if (panOpt) panOpt.textContent = `WYSIWYG: Ikuti Pan Layar (${{Math.round(panProgress * 100)}}%)`;

      if (!baseLoopDuration || baseLoopDuration <= 0) {{
        baseLoopDuration = detectBaseLoopDuration();
      }}

      const loops = parseInt(modalLoopsSelect.value, 10) || 1;
      const loopSec = (baseLoopDuration / 1000) / activeSpd;
      const totalSec = loopSec * loops;
      const totalFrames = Math.round(totalSec * 60);

      if (modalDurationDisplay) modalDurationDisplay.textContent = `${{totalSec.toFixed(1)}}s (${{loops}}x loop @ ${{loopSec.toFixed(1)}}s)`;
      if (modalFramesDisplay) modalFramesDisplay.textContent = `${{totalFrames}} frames @ 60 FPS (Constant Frame Rate CFR)`;
    }}

    if (exportMp4Btn && modalBackdrop) {{
      exportMp4Btn.addEventListener("click", () => {{
        modalBackdrop.style.display = "flex";
        updateModalCalculations();
      }});

      modalCloseBtn.addEventListener("click", () => {{
        modalBackdrop.style.display = "none";
      }});

      modalCancelBtn.addEventListener("click", () => {{
        modalBackdrop.style.display = "none";
      }});

      modalLoopsSelect.addEventListener("change", updateModalCalculations);
      modalResSelect.addEventListener("change", updateModalCalculations);
      document.querySelectorAll('input[name="modal-speed-mode"]').forEach(r => {{
        r.addEventListener("change", updateModalCalculations);
      }});

      modalStartBtn.addEventListener("click", async () => {{
        const speedMode = document.querySelector('input[name="modal-speed-mode"]:checked')?.value || "current";
        const activeSpd = speedMode === "current" ? currentSpeed : 1.0;
        const loops = parseInt(modalLoopsSelect.value, 10) || 1;
        const [targetW, targetH] = modalResSelect.value.split("x").map(Number);
        const panMode = modalPanSelect.value;

        if (!baseLoopDuration || baseLoopDuration <= 0) {{
          baseLoopDuration = detectBaseLoopDuration();
        }}

        const loopSec = (baseLoopDuration / 1000) / activeSpd;
        const totalSec = loopSec * loops;
        const fps = 60;
        const totalFrames = Math.round(totalSec * fps);

        // Lock UI
        modalStartBtn.disabled = true;
        modalCancelBtn.disabled = true;
        modalCloseBtn.disabled = true;
        modalProgressWrap.style.display = "block";
        modalProgressBar.style.width = "0%";
        modalProgressPct.textContent = "0%";
        modalProgressStatus.textContent = "Menginisialisasi encoder video MP4...";

        // Offscreen Canvas setup
        const offCanvas = document.createElement("canvas");
        offCanvas.width = targetW;
        offCanvas.height = targetH;
        const ctx = offCanvas.getContext("2d");

        // MediaRecorder setup with H.264 MP4 (or VP9 WebM fallback)
        const stream = offCanvas.captureStream(fps);
        let mime = "video/mp4; codecs=avc1";
        if (!MediaRecorder.isTypeSupported(mime)) mime = "video/mp4";
        if (!MediaRecorder.isTypeSupported(mime)) mime = "video/webm; codecs=vp9";
        if (!MediaRecorder.isTypeSupported(mime)) mime = "video/webm";

        const bitrate = targetW >= 3840 ? 45000000 : 25000000;
        const recorder = new MediaRecorder(stream, {{ mimeType: mime, videoBitsPerSecond: bitrate }});
        const recordedChunks = [];
        recorder.ondataavailable = (e) => {{
          if (e.data && e.data.size > 0) recordedChunks.push(e.data);
        }};

        // Framing & Pan calculations for target 16:9 canvas
        const vb = getSvgViewBoxDimensions();
        const vbAspect = vb.width / vb.height;
        const targetAspect = targetW / targetH;
        let drawW, drawH, drawOffsetX = 0, drawOffsetY = 0;

        if (vbAspect >= targetAspect) {{
          drawH = targetH;
          drawW = targetH * vbAspect;
          const maxOverflow = drawW - targetW;
          const p = (panMode === "center") ? 0.5 : panProgress;
          drawOffsetX = -(p * maxOverflow);
          drawOffsetY = 0;
        }} else {{
          drawW = targetW;
          drawH = targetW / vbAspect;
          const maxOverflow = drawH - targetH;
          const p = (panMode === "center") ? 0.5 : panProgress;
          drawOffsetX = 0;
          drawOffsetY = -(p * maxOverflow);
        }}

        // Pause live animations and reset deterministically to frame 0 (t = 0.0s)
        const anims = svgElem.getAnimations({{ subtree: true }});
        const wasPlaying = isPlaying;
        anims.forEach(a => {{
          a.pause();
          a.currentTime = 0;
        }});

        recorder.start(100);

        // Detect background color from SVG
        const skyEl = svgElem.querySelector("#sky") || svgElem.querySelector("rect");
        const bgColor = (skyEl && skyEl.getAttribute("fill")) ? skyEl.getAttribute("fill") : "#0a0c10";

        const frameDelay = 1000 / fps;

        for (let i = 0; i < totalFrames; i++) {{
          const tElapsedMs = (i / fps) * 1000 * activeSpd;
          anims.forEach(a => {{
            const d = a.effect ? a.effect.getTiming().duration : baseLoopDuration;
            const dur = (typeof d === "number" && d > 0) ? d : baseLoopDuration;
            a.currentTime = tElapsedMs % dur;
          }});

          // Clone SVG and copy computed styles for clean deterministic snapshot
          const clone = svgElem.cloneNode(true);
          const origEls = svgElem.querySelectorAll("*");
          const cloneEls = clone.querySelectorAll("*");
          for (let j = 0; j < origEls.length; j++) {{
            const cs = window.getComputedStyle(origEls[j]);
            if (cs.transform && cs.transform !== "none") {{
              cloneEls[j].style.transform = cs.transform;
              if (cs.transformOrigin) cloneEls[j].style.transformOrigin = cs.transformOrigin;
              if (cs.transformBox) cloneEls[j].style.transformBox = cs.transformBox;
            }}
            if (cs.opacity && cs.opacity !== "1") cloneEls[j].style.opacity = cs.opacity;
            if (cs.filter && cs.filter !== "none") cloneEls[j].style.filter = cs.filter;
          }}

          const svgStr = new XMLSerializer().serializeToString(clone);
          const img = new Image();
          await new Promise((res) => {{
            img.onload = res;
            img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgStr);
          }});

          // Draw clean frame to video canvas
          ctx.fillStyle = bgColor;
          ctx.fillRect(0, 0, targetW, targetH);
          ctx.drawImage(img, drawOffsetX, drawOffsetY, drawW, drawH);

          const pct = Math.round(((i + 1) / totalFrames) * 100);
          modalProgressBar.style.width = `${{pct}}%`;
          modalProgressPct.textContent = `${{pct}}%`;
          modalProgressStatus.textContent = `Rendering frame ${{i + 1}} / ${{totalFrames}}...`;

          await new Promise(r => setTimeout(r, Math.min(16, frameDelay)));
        }}

        modalProgressStatus.textContent = "Finalisasi file MP4...";
        recorder.stop();
        await new Promise(r => recorder.onstop = r);

        const blob = new Blob(recordedChunks, {{ type: mime }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const ext = mime.includes("mp4") ? "mp4" : "webm";
        const safeMotion = currentMotionStyleName ? `_${{currentMotionStyleName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}}` : "";
        const safeTheme = currentThemeName ? `_${{currentThemeName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}}` : "";
        const resLabel = targetH === 2160 ? "4k" : (targetH === 1080 ? "1080p" : "720p");
        a.download = `{safe_subject}${{safeMotion}}${{safeTheme}}_${{loops}}x_${{resLabel}}.${{ext}}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Restore live playback
        if (wasPlaying) {{
          anims.forEach(a => a.play());
        }}

        modalStartBtn.disabled = false;
        modalCancelBtn.disabled = false;
        modalCloseBtn.disabled = false;
        modalProgressWrap.style.display = "none";
        modalBackdrop.style.display = "none";
      }});
    }}

    // 1x Loop Timer Telemetry (Scales Dynamically with Playback Rate)
    const loopTimeCur = document.getElementById("loop-time-cur");
    const loopTimeTotal = document.getElementById("loop-time-total");

    let baseLoopDuration = 0;

    function detectBaseLoopDuration() {{
      const anims = svgElem.getAnimations({{ subtree: true }});
      let maxMs = 0;
      anims.forEach(anim => {{
        const d = anim.effect ? anim.effect.getTiming().duration : null;
        if (typeof d === "number" && d > maxMs && d < 100000) {{
          maxMs = d;
        }}
      }});
      if (maxMs <= 0) {{
        svgElem.querySelectorAll("*").forEach(el => {{
          const comp = window.getComputedStyle(el);
          const dur = parseFloat(comp.animationDuration);
          if (dur > 0 && dur * 1000 > maxMs) {{
            maxMs = dur * 1000;
          }}
        }});
      }}
      return maxMs > 0 ? maxMs : 10000;
    }}

    function updateLoopTimer(now) {{
      if (!baseLoopDuration || baseLoopDuration <= 0) {{
        baseLoopDuration = detectBaseLoopDuration();
      }}

      const totalSec = (baseLoopDuration / 1000) / currentSpeed;
      if (loopTimeTotal) {{
        loopTimeTotal.textContent = `${{totalSec.toFixed(1)}}s`;
      }}

      if (isPlaying && loopTimeCur) {{
        const anims = svgElem.getAnimations({{ subtree: true }});
        const primaryAnim = anims.find(a => a.effect && a.effect.getTiming().duration === baseLoopDuration) || anims[0];

        let curSec = 0;
        if (primaryAnim && typeof primaryAnim.currentTime === "number") {{
          const timelineElapsedMs = (primaryAnim.currentTime) % baseLoopDuration;
          curSec = (timelineElapsedMs / 1000) / currentSpeed;
        }} else {{
          const cycleMs = (now * currentSpeed) % baseLoopDuration;
          curSec = (cycleMs / 1000) / currentSpeed;
        }}

        loopTimeCur.textContent = `${{Math.max(0, curSec).toFixed(1)}}s`;
      }}
      requestAnimationFrame(updateLoopTimer);
    }}
    requestAnimationFrame(updateLoopTimer);

    // Initial framing and speed setup
    updateFramingAndPan();
    applySpeed(1.0);
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    if not args.svg.exists():
        raise SystemExit(f"Input SVG file does not exist: {args.svg}")

    tree = ET.parse(args.svg)
    subject_stem = args.svg.stem
    subject_name = subject_stem.replace("_", " ").title()

    # Dynamic naming defaults
    out_html = args.out_html
    if not out_html:
        out_html = args.svg.with_name(f"{subject_stem}_motion.html")

    out_svg = args.out_svg
    if not out_svg:
        out_svg = args.svg.with_name(f"{subject_stem}_motion.svg")

    title = args.title or f"{subject_name} Motion"

    custom_css = None
    if args.motion_css:
        css_path = Path(args.motion_css)
        if css_path.exists():
            custom_css = css_path.read_text(encoding="utf-8")
        else:
            custom_css = args.motion_css

    # Assemble motion CSS
    css_rules, category, active_layers = assemble_motion_css(
        tree.getroot(),
        category=args.category,
        preset=args.preset,
        duration=args.duration,
        amplitude=args.amplitude,
        custom_css=custom_css,
    )

    # Load LLM-synthesized palettes
    palettes = None
    if args.palettes:
        p_path = Path(args.palettes)
        if p_path.exists():
            palettes = json.loads(p_path.read_text(encoding="utf-8"))
        else:
            palettes = json.loads(args.palettes)
    else:
        # Check automatic candidate paths
        cand1 = args.svg.with_name(f"{subject_stem}_palettes.json")
        cand2 = args.svg.parent / "fit_work" / f"{subject_stem}_palettes.json"
        if cand1.exists():
            palettes = json.loads(cand1.read_text(encoding="utf-8"))
        elif cand2.exists():
            palettes = json.loads(cand2.read_text(encoding="utf-8"))

    # Load LLM-synthesized motion styles (2-3 contextual alternatives)
    motion_styles = None
    if args.motion_styles:
        m_path = Path(args.motion_styles)
        if m_path.exists():
            motion_styles = json.loads(m_path.read_text(encoding="utf-8"))
        else:
            motion_styles = json.loads(args.motion_styles)
    else:
        cand_m1 = args.svg.with_name(f"{subject_stem}_motions.json")
        cand_m2 = args.svg.parent / "fit_work" / f"{subject_stem}_motions.json"
        if cand_m1.exists():
            motion_styles = json.loads(cand_m1.read_text(encoding="utf-8"))
        elif cand_m2.exists():
            motion_styles = json.loads(cand_m2.read_text(encoding="utf-8"))

    if motion_styles and len(motion_styles) > 0:
        first_style_name = next(iter(motion_styles))
        if not custom_css:
            css_rules = motion_styles[first_style_name]

    # 1. Standalone SVG deliverable
    if out_svg:
        out_svg.parent.mkdir(parents=True, exist_ok=True)
        animated_svg_content = build_standalone_animated_svg(tree, css_rules)
        out_svg.write_text(animated_svg_content, encoding="utf-8")
        print(f"Animated SVG saved to: {out_svg}")

    # 2. Interactive HTML preview deliverable
    if out_html:
        out_html.parent.mkdir(parents=True, exist_ok=True)
        import copy
        root_clean = copy.deepcopy(tree.getroot())
        strip_all_namespaces(root_clean)
        for el in list(root_clean.iter()):
            for child in list(el):
                if child.tag == "style" or child.tag.endswith("style"):
                    el.remove(child)
        clean_svg = clean_xml_string(ET.tostring(root_clean, encoding="utf-8").decode("utf-8"))

        html_content = build_interactive_preview_html(
            svg_string=clean_svg,
            title=title,
            subject_name=subject_name,
            category=category,
            active_layers=active_layers,
            css_rules=css_rules,
            palettes=palettes,
            motion_styles=motion_styles,
        )
        out_html.write_text(html_content, encoding="utf-8")
        print(f"Interactive Motion HTML preview saved to: {out_html}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
