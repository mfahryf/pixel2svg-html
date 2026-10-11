---
name: pixel2svg-html
description: Convert raster logos, graphics, and illustrations (PNG/JPG/WebP/screenshots) into clean, smooth, minimal-complexity SVG with semantic layer naming, standalone JS-rendered HTML, and context-aware object/background animations (hopping creatures, moving vehicles, botanical sway, or ambient motion backgrounds). Uses a lowest-complexity-first fitting workflow with overlay QA, edge smoothness as primary gate, IoU optimization, Bezier audits, dynamic subject-based deliverable naming (<subject>.svg, <subject>_motion.html), and a default 10-iteration budget. If the user asks for multi-stage atomic reveals or step sequencers, switch to pixel2motion.
---

# Pixel2SVG-HTML (v3.0)

Turn any raster logo, graphic, or illustration into:

- `<subject>.svg` — minimal, smooth, editable vector with **mandatory semantic layer naming** (`#body`, `#head`, `#ear_left`, `#wheel_front`, `#chassis`, `#shadow`, `#bg`, etc.)
- `<subject>.html` — standalone HTML that recreates the SVG via JavaScript DOM calls
- Optional: `<subject>_motion.html` & `<subject>_motion.svg` — **context-aware object motion** (e.g. creature hop with squash-and-stretch, vehicle drive with rotating wheels, botanical sway, or ambient background flow)
- `final_render.png`, `html_render.png`, overlay iterations + `overlay_progress_strip.png`
- Resumable fit state in `outputs/<subject>/fit_work/` and overlays in `outputs/<subject>/fit_iterations/` (preventing accidental overwriting across different subjects)

The governing rule is **lowest smooth complexity that passes visual QA** paired with **semantic layer structuring**. Do not maximize pixel-fit by default: start with the simplest editable geometry that explains the mark, escalate only when an overlay shows a structural mismatch. Edge smoothness is the primary hard gate for ordinary logos. IoU is a diagnostic metric to be pushed as high as practical, without a fixed global pass/fail value.

---

## Dynamic Subject-Based Deliverable Naming

Deliverables must **never** be hardcoded to generic names that overwrite each other across different runs. Derive `<subject>` from the subject's identity (e.g., `rabbit`, `sports_car`, `lotus`, `halftone_wave`):

- Vector deliverable: `<subject>.svg`
- Vanilla DOM HTML: `<subject>.html`
- Contextual Motion Preview: `<subject>_motion.html`
- Standalone Animated SVG: `<subject>_motion.svg`
- Iteration QA & Work directory: `outputs/<subject>/fit_iterations/` and `outputs/<subject>/fit_work/`

---

## Mandatory Semantic Layer Naming & Pivoting

When constructing or fitting the SVG, **never flatten the entire artwork into a single monolithic path** when the subject consists of movable or identifiable parts. Group shapes into semantic layers with descriptive `id` attributes:

1. **Living Creatures / Animals** (e.g., Rabbit, Cat, Bird):
   - `#body`, `#head`, `#ear_left`, `#ear_right`, `#leg_front`, `#leg_back`, `#tail`, `#shadow`
2. **Vehicles / Mechanical** (e.g., Car, Bicycle, Train, Clock):
   - `#chassis`, `#body`, `#wheel_front`, `#wheel_back`, `#rim_front`, `#rim_back`, `#exhaust`, `#headlight`, `#shadow`
3. **Nature / Botanical** (e.g., Flower, Tree, Water):
   - `#stem`, `#leaf_left`, `#leaf_right`, `#petal_group`, `#bloom`, `#roots`
4. **Mechanical / Gears**:
   - `#gear_large`, `#gear_small`, `#needle`, `#casing`, `#rotor`
5. **Background / Pattern**:
   - `#sky`, `#clouds`, `#mountains`, `#ground`, `#matrix_dots`, `#wave_band`, `#backdrop`

### Anchor & Pivot Points
Ensure child elements specify or inherit proper transform anchors:
- Wheels & rotating centers: `transform-box: fill-box; transform-origin: center;`
- Limbs, ears, stems: `transform-box: fill-box; transform-origin: bottom center;` (or joint connection point)
- Pendulums & tails: `transform-box: fill-box; transform-origin: top left;`
Read `references/contextual-motion-kinematics.md` for complete kinematic formulas and anchor tables.

### Overscan Bleed, 16:9 Canvas Framing, Pan & Translucent HUD Dock
To prevent edge cutoffs during motion translations and maintain cinematic aesthetics:
1. **Overscan Bleed Geometry ($\ge 5\% - 10\%$)**: For any background, terrain, ridge, or edge-touching element that moves via `translate(dx, dy)` or `scale()`, never clamp coordinates strictly at the viewBox edges ($x=0$ to $W$). Extend geometry outwards by an overscan buffer (e.g. $x \in [-40, W+40]$, $y \in [-20, H+20]$) so translations never reveal unsightly edge cutoffs or background gaps.
2. **16:9 Cinematic Canvas Framing**: Interactive motion previews (`<subject>_motion.html`) present the animated graphic inside a responsive 16:9 canvas frame (`aspect-ratio: 16 / 9; overflow: hidden;`). Sizing fits the **shortest side** of the SVG, ensuring seamless edge-to-edge presentation without letterboxing bars.
3. **Pan & Viewport Framing Alignment**: When the shortest side is fitted, the longest side overflows. The interactive preview provides:
   - **Direct drag-to-pan** with mouse or touch.
   - **HUD Pan Slider (0% - 100%)** with quick snapping presets (`◀ / ▲`, `⯀`, `▶ / ▼`).
   - Adaptive axis orientation ($X$ for panoramic landscapes, $Y$ for tall portraits).
4. **Infinite Looping & Dynamic 1x Loop Timer**: All generated contextual vector animations loop continuously (`infinite`). The HUD provides a real-time **⏱ 1x Loop Timer** badge (`curSec / totalSec`) that dynamically rescales total loop duration and tick rate whenever the speed multiplier changes.
5. **Ultra-Slim Translucent Glass HUD Dock**: Controls float inside the lower canvas as an ultra-slim frosted glass capsule dock (`background: rgba(10, 14, 23, 0.40); backdrop-filter: blur(14px);`), allowing the motion and layers behind the HUD to remain clearly visible at all times.
6. **Glitch-Free Speed Scaling**: Speed control uses native Web Animations API `anim.playbackRate = speed` (`svgElem.getAnimations({ subtree: true })`), preventing the cumulative compounding errors and keyframe phase teleportation stutters caused by CSS `animation-duration` manipulation.

---

## Subject Categorization & Motion Reasoning Protocol

When motion animation is requested (`--motion` / `scripts/animate_svg.py`), the AI must not blindly apply generic wave presets. Instead, execute this 3-step reasoning:

### 1. Subject Categorization
Inspect the SVG layers and shape semantics:
- **Creature / Character**: Animal, human, or mascot with articulated limbs, ears, or wings.
- **Vehicle / Mechanical**: Wheeled vehicles, engines, rolling bodies, or clockwork.
- **Nature / Botanical**: Flora, leaves, petals, trees, fluid streams.
- **Brand Symbol / Icon**: Emblems, geometric logos, badges, tech marks.
- **Ambient Pattern / Backdrop**: Grids, halftone dot fields, skies, landscapes, abstract backgrounds.

### 2. Contextual Motion Reasoning
Ask: *"Animasi apa yang paling cocok dan alami untuk subjek ini?"*
- **Rabbit / Creature**: Hop/jump cycle with **Squash & Stretch** (`scale(1.12, 0.88)` anticipation on ground, `translateY(-25px)` airborne stretch, landing impact), lagging ears swinging with inertia, and ground shadow shrinking/expanding inversely with jump height.
- **Car / Vehicle**: Continuous $360^\circ$ wheel rotation centered on axles, high-frequency chassis suspension jitter (`translateY(-1.5px)` to `1.0px`), ground contact vibration, and trailing exhaust smoke puffs.
- **Flower / Plant**: Gentle wind sway (`rotate(3.5deg)` anchored at stem base) and rhythmic petal breathing.
- **Background / Pattern**: Custom wave flow, radial ripple, or parallax drift tailored specifically to the visual orientation of the graphic.

### 3. LLM Contextual Semantic Palette Synthesis
Because the LLM knows the exact semantics and count of each layer (e.g. which element is `#sun` / light source, which is `#shadow`, which is body, which is background), the AI synthesizes **3 to 5 curated color themes** tailored 1-to-1 to the layer IDs:
- Themes should explore distinct aesthetic moods (e.g. `Original`, `Midnight / Blue Hour`, `Sunset Violet`, `Earthy Sage`, `Monochrome Noir`).
- Light sources adapt naturally (e.g. `#sun` becomes a silvery moon `#e2e8f0` in Midnight, gold `#fde047` in Sunset).
- Save themes in `outputs/<subject>/fit_work/<subject>_palettes.json` and pass via `--palettes`.
- The HTML preview renders an interactive **🎨 Palette Switcher** in the HUD, and SVG exports preserve the active theme!

### 4. Motion Delivery
Generate `<subject>_motion.html` (interactive preview with telemetry, HUD controls, palette switcher, 16:9 framing, play/pause, speed slider) and `<subject>_motion.svg` (pure CSS GPU compositor).

---

## Complexity Ladder

Use the lowest level that matches the source faithfully:

1. **Primitives**: circles, ellipses, rects, lines, simple arcs, transforms.
2. **Primitive composites**: boolean-like combinations of a few primitives or masks.
3. **Few-curve analytic paths**: a small number of cubic segments for smooth ribbons, swooshes, C-marks, leaves, waves. For closed and/or self-intersecting variable-width ribbons (∞ marks, scripts), use the centerline-scaffold recipe: `references/ribbon-fitting.md` + `scripts/fit_ribbon_centerline.py` (playbook §8).
4. **Smoothed outline paths**: more knots only where the source has real shape changes; preserve G1 tangent continuity, no noisy handle flips.
5. **Trace-derived paths**: only for irregular silhouettes where simpler geometry fails (`scripts/raster_logo_trace.py` as measurement starter). Trace output is a measurement aid, never final art without smoothing.

If a higher-complexity version improves only antialiasing or minor pixel coverage, keep the lower one. Prefer live SVG `<text>` for wordmarks unless exact letterforms are required.

---

## Smoothness And Fit Gate

IoU must not hide bad vector craft. A smooth source must ship as smooth vector geometry; the final SVG fails if intended smooth edges visibly stair-step, chatter, use pixel-grid orthogonal runs, contain noisy trace knots, or look like a bitmap mask at 200-400% zoom, even when IoU is numerically high.

- Pixel-grid contours from threshold masks are acceptable only as starter measurements or for genuinely pixel-art logos.
- Smooth parts should use primitives, arcs, ellipses, or cubic paths with the lowest complexity that preserves silhouette, width profile, extrema, and negative space.
- Compute and record IoU every iteration, but do not use a fixed global pass/fail value. Optimize IoU upward after smoothness and structural correctness are protected.
- Binary-mask metrics over GRADIENT-filled parts inflate pixel diffs even when visually faithful — judge such parts structurally and visually.

---

## Workflow

1. **Measure first.** Locate source; extract masks, centers/radii, edge samples. Read `references/fitting-playbook.md` BEFORE writing fit code.
2. **Choose fitting strategy from ladder.** Primitives for geometric shapes; filled outlines for ribbons; semantic IDs for all distinct components.
3. **Generate low-complexity first artifact.**
   - Output: `<subject>.svg` with correct `viewBox` and semantic layer IDs.
   - Run overlay QA:
     `python3 scripts/render_overlay.py <subject>.svg source.png --out outputs/<subject>/fit_iterations/01_first_overlay.png --render-out outputs/<subject>/final_render.png`
   - Store all fit code in `outputs/<subject>/fit_work/`.
4. **Inspect with multimodal vision & Bezier audit.** Check edge smoothness, silhouette, and G1 continuity (`scripts/svg_path_audit.py`).
5. **Iterate — max 10 iterations.** One change per iteration; save `NN_name_overlay.png`.
6. **Evaluate and ship deliverables:**
   - Static DOM HTML:
     `python3 scripts/svg_to_js_html.py <subject>.svg --out <subject>.html`
   - Contextual Motion HTML & Animated SVG (when motion is requested):
     - Generate `<subject>_motions.json` with 3 distinct motion concepts (ambient, environmental transit, chromatic flare/mirage).
     - Generate `<subject>_palettes.json` with 3-5 LLM-tailored color schemes.
     - Compile motion deliverables:
       `python3 scripts/animate_svg.py <subject>.svg --category custom --motion-styles outputs/<subject>/fit_work/<subject>_motions.json --palettes outputs/<subject>/fit_work/<subject>_palettes.json --out-html <subject>_motion.html --out-svg <subject>_motion.svg`
   - Build progress strip: `outputs/<subject>/overlay_progress_strip.png`.

---

## Bundled Scripts

```bash
# 1. Measurement / starter trace
python3 scripts/raster_logo_trace.py source.png --out outputs/<subject>

# 2. Render + cyan overlay + IoU metrics in one step (Chrome/Edge headless)
python3 scripts/render_overlay.py <subject>.svg source.png \
  --out outputs/<subject>/fit_iterations/01_overlay.png \
  --render-out outputs/<subject>/final_render.png \
  --report outputs/<subject>/fit_metrics.json

# 3. Bezier smoothness audit (kinks > 8° flagged)
python3 scripts/svg_path_audit.py <subject>.svg \
  --out-svg outputs/<subject>/bezier_segments.svg \
  --report outputs/<subject>/bezier_audit.json

# 4. JS-rendered standalone HTML deliverable (auto-named <subject>.html)
python3 scripts/svg_to_js_html.py <subject>.svg

# 5. Context-aware object motion (auto-detects creature, vehicle, nature, or background)
python3 scripts/animate_svg.py <subject>.svg

# With multi-style motion options and LLM color palettes:
python3 scripts/animate_svg.py <subject>.svg \
  --motion-styles outputs/<subject>/fit_work/<subject>_motions.json \
  --palettes outputs/<subject>/fit_work/<subject>_palettes.json

# Or specify category and parameters explicitly:
python3 scripts/animate_svg.py <subject>.svg --category creature --duration 1.6 --amplitude 1.0
python3 scripts/animate_svg.py <subject>.svg --category vehicle --duration 0.8
python3 scripts/animate_svg.py <subject>.svg --category background --preset wave

# 6. Combined HTML generation with motion flag:
python3 scripts/svg_to_js_html.py <subject>.svg --motion

# 7. End-of-run progress strip
python3 scripts/overlay_progress_strip.py --source source.png \
  --dir outputs/<subject>/fit_iterations --pattern "*overlay*.png" \
  --final-image outputs/<subject>/final_render.png \
  --out outputs/<subject>/overlay_progress_strip.png

# 8. Broadcast & Adobe Stock Video Export (CLI)
# 1080p Full HD @ 60 FPS CFR, 2 loops, H.264 Rec.709:
python3 scripts/export_video.py <subject>_motion.html --preset adobe-stock --res 1080p --loops 2

# 4K UHD Ultra High Definition:
python3 scripts/export_video.py <subject>_motion.html --res 4k --loops 2

# Apple ProRes 422 HQ broadcast master (.mov):
python3 scripts/export_video.py <subject>_motion.html --codec prores --out <subject>_prores.mov
```

---

## Acceptance Criteria

- `<subject>.svg` exists, contains **semantic layer IDs**, and renders cleanly.
- `<subject>.html` exists, recreates the SVG via JavaScript DOM calls, and has been verified in a browser.
- Deliverables use `<subject>` naming and do not overwrite previous outputs or other subjects.
- If motion is requested:
  - `<subject>_motion.html` and `<subject>_motion.svg` exist.
  - Generates **3 distinct contextual motion styles** (1 canonical/ambient + 2 creative alternatives, e.g. sunset arc transit, chromatic flare shimmer) accessible via a HUD switcher.
  - Infinite looping (`infinite`) with dynamic **⏱ 1x loop timer** that rescales its duration and elapsed time with playback speed.
  - HUD dimensions remain strictly jitter-free when timer digits increment (`font-variant-numeric: tabular-nums` and locked widths).
  - Ultra-slim translucent frosted glass dock (2-row wide console spanning ~94% screen width, `backdrop-filter: blur(16px)`) floating inside the stage, keeping moving artwork visible behind it.
  - 16:9 cinematic framing with shortest-side cover fit and interactive drag/slider pan navigation.
  - 100% WYSIWYG Standalone SVG Exporter (`⬇ SVG`):
    - **Color Palette**: Active theme colors mapped directly to inline fills/strokes.
    - **Motion Style**: Active keyframes & animation rules embedded into `<style>`.
    - **Speed Multiplier**: Keyframe durations dynamically scaled by `1 / currentSpeed` (e.g. 2.0x scales 10s to 5.00s).
    - **Framing & Pan**: If in `🔲 16:9 Canvas` mode, `viewBox` is dynamically cropped to 16:9 aspect at the exact pan coordinate; if in `🖼 Contained` mode, original full vector bounds are preserved.
  - In-HUD **🎥 MP4 Export Modal**:
    - Resolution options: 1080p Full HD (Adobe Stock standard), 4K UHD, 720p HD.
    - xLoop selection (1x, 2x recommended, 3x, 5x).
    - Visual framing: WYSIWYG pan alignment vs Center reset (50%).
    - Speed mode: Active speed vs 1.0x normal reset.
    - Real-time telemetry: Total duration in seconds, total frames @ 60 FPS CFR, clean canvas guarantee.
    - Progress bar and client-side browser download.
  - Broadcast CLI Exporter (`scripts/export_video.py`):
    - Strict Constant Frame Rate (CFR) 60.000 FPS without dropped frames or VFR timing jitter.
    - Adobe Stock technical compliance: Rec.709 color matrix (`bt709`), H.264 High Profile 4:2:0 CRF 16 or Apple ProRes 422 HQ `.mov`, `faststart` atom, and 100% clean canvas (HUD hidden during capture).
  - Smooth 60 FPS GPU-accelerated CSS keyframes (`transform-box: fill-box; transform-origin: ...`).
- Final overlay and progress strip viewed and reported with honest residual explanations.

---

## References

- `references/contextual-motion-kinematics.md` — Object kinematics guide: semantic layer standards, pivot points, squash-and-stretch formulas, wheel rotations, suspension jitter, alternative motion style architectures, 2-row wide HUD console, timer telemetry, and Adobe Stock video export specifications.
- `references/fitting-playbook.md` — Field-tested fitting strategies: measurement, feature windows, boundary-from-source, G1 repair, feedback corrections.
- `references/ribbon-fitting.md` — Closed/self-intersecting variable-width ribbons.
- `references/motion-backgrounds.md` — Ambient motion background math and spatial phase propagation.

---

## Changelog

### v3.2 — Adobe Stock & Broadcast Video Export Engine + 4D WYSIWYG SVG Exporter
- **100% WYSIWYG Standalone SVG Export**:
  - Exports SVG matching screen state across all 4 visual & temporal dimensions: active palette colors, active motion keyframes, active speed multiplier (CSS duration scaled), and active 16:9 pan framing (`viewBox` cropped to 16:9 or full bounds in Contained mode).
- **In-HUD Export MP4 Modal Dialog**:
  - Modal with resolution selection (1080p Full HD Adobe Stock standard, 4K UHD, 720p), xLoop count (1x, 2x, 3x, 5x), Visual Framing (WYSIWYG Pan vs Center Reset), and Speed Mode (active speed vs 1.0x normal).
  - Real-time telemetry displaying total duration in seconds, total frame count @ 60 FPS CFR, and clean canvas guarantee.
  - Client-side MediaRecorder encoder with progress bar and instant browser download.
- **Broadcast-Grade CLI Video Exporter (`scripts/export_video.py`)**:
  - Headless Playwright + FFmpeg 8.0.1 engine for broadcast stock footage.
  - Strict Constant Frame Rate (CFR) 60.000 FPS without dropped frames or VFR timing jitter.
  - Full Adobe Stock & broadcast compliance: Rec.709 color matrix (`bt709`), H.264 High Profile 4:2:0 CRF 16 or Apple ProRes 422 HQ `.mov`, `faststart` atom, and 100% clean canvas (HUD hidden during capture).
  - WYSIWYG pan alignment preserving exact on-screen framing.

### v3.1 — Multi-Concept Motion & Anti-Jitter Telemetry
- **Multi-Concept Motion Synthesizer (3 Alternative Motion Styles)**:
  - Supports 3 distinct motion styles per subject switchable on the fly via `<style id="motion-css-tag">` without page reloads.
- **Dynamic 1x Loop Timer & Anti-Jitter HUD Metrics**:
  - Added real-time 1x loop timer (`⏱ 1x Loop: X.Xs / Y.Ys`) dynamically tracking cycle duration and playback rate.
  - Enforced monospace tabular numbers (`font-variant-numeric: tabular-nums; font-feature-settings: "tnum"`) with strict width bounding to eliminate horizontal layout jitter when digits change.
- **Ultra-Slim In-Stage Frosted Glass Dock (2-Row Wide Console)**:
  - Structured into 2 distinct spacious rows spanning ~94% screen width ("hampir 1 lebar layar") directly inside the animation canvas, with high transparency (`rgba(10, 14, 23, 0.45)`) and backdrop blur (`16px`).
- **16:9 Cinematic Fit & Interactive Pan Navigation**:
  - Fits shortest side to 16:9 canvas to prevent cutoffs, with drag-to-pan, pan slider, and alignment buttons.
- **Glitch-Free Continuous Playback Rate**:
  - Web Animations API `anim.playbackRate` ensures smooth speed changes without keyframe phase jumps.
