# Contextual Motion & Object Kinematics Guide

This guide establishes the architecture, layer naming standards, pivot-point physics, and animation recipes for generating **subject-aware, context-specific vector animations** in **Pixel2SVG-HTML**.

---

## 1. Core Philosophy: Contextual vs. Generic Motion

Never apply a one-size-fits-all preset without understanding what the SVG represents:
- **Analyze First**: Inspect the subject's semantics before writing animation code.
- **Form Follows Function**: A rabbit hops, a car rolls, a flower sways, a gear rotates, and a starry matrix ripples.
- **Layer-Driven Independence**: Elements must be separated into semantic layers so that individual anatomical or mechanical components can move with appropriate degrees of freedom.
- **No Overwriting**: Every output is named dynamically after the subject (`<subject>.svg`, `<subject>.html`, `<subject>_motion.html`, `<subject>_motion.svg`).

---

## 2. Semantic Layer Naming & SVG Structuring Standards

When generating or fitting the vector SVG, you **MUST** structure elements into meaningful groups (`<g id="...">`) and paths (`<path id="...">` / `<circle id="...">`).

### Standard Layer Naming Conventions

| Category | Recommended Layer IDs | Kinematic Role |
| :--- | :--- | :--- |
| **Living Creature / Animal** (e.g. Rabbit, Cat, Bird) | `#body`, `#head`, `#ear_left`, `#ear_right`, `#leg_front`, `#leg_back`, `#tail`, `#eye`, `#shadow` | Body translates along jump arc; ears lag behind; legs extend/tuck; shadow pulses inversely with height. |
| **Vehicle / Mechanical** (e.g. Car, Bicycle, Train) | `#chassis`, `#body`, `#wheel_front`, `#wheel_back`, `#rim_front`, `#rim_back`, `#shadow`, `#exhaust`, `#headlight` | Wheels rotate $360^\circ$ around centers; chassis jitters on suspension; shadow tracks ground contact. |
| **Nature / Botanical** (e.g. Flower, Tree, Plant) | `#stem`, `#leaf_left`, `#leaf_right`, `#petal_group`, `#bloom`, `#dewdrop`, `#roots` | Stem bends along cubic arc; leaves flutter; petals breathe/bloom gently. |
| **Mechanical / Clockwork** (e.g. Gears, Watch, Compass) | `#gear_large`, `#gear_small`, `#needle`, `#casing`, `#rotor` | Meshed gears rotate in opposing directions at exact gear tooth ratios. |
| **Character / Humanoid** | `#torso`, `#head`, `#arm_left`, `#arm_right`, `#leg_left`, `#leg_right`, `#shadow` | Walk/idle cycle with alternating limb swing and secondary spine bobbing. |
| **Ambient Pattern / Backdrop** (when subject is background) | `#sky`, `#clouds`, `#mountains`, `#ground`, `#matrix_dots`, `#wave_band` | Parallax drift, wave propagation, or ambient depth breathing matching the visual perspective. |

---

## 3. Pivot Points & Transform Origins

To prevent moving parts from detaching or rotating awkwardly, set precise pivot points:

1. **Self-Contained Elements (Wheels, Eyes, Dots)**:
   ```css
   #wheel_front, #wheel_back {
     transform-box: fill-box;
     transform-origin: center;
   }
   ```
2. **Hinged Limbs (Ears, Legs, Stems, Arms)**:
   - For an ear attached at the base:
     ```css
     #ear_left, #ear_right {
       transform-box: fill-box;
       transform-origin: bottom center; /* Pivot from the root connection */
     }
     ```
   - For a pendular limb or tail:
     ```css
     #tail {
       transform-box: fill-box;
       transform-origin: top left; /* Pivot from root of tail */
     }
     ```
3. **Contact Shadow**:
   ```css
   #shadow {
     transform-box: fill-box;
     transform-origin: center;
   }
   ```

---

## 4. Subject-Specific Kinematics Recipes

### A. Creature / Rabbit Hop Cycle

A realistic rabbit hop uses **Squash & Stretch**, an airborne parabolic arc, lagging ears, and a reactive ground shadow.

```css
/* Body Jump Arc + Squash & Stretch */
@keyframes rabbit-hop {
  0%, 100% {
    transform: translateY(0px) scale(1, 1);
    animation-timing-function: cubic-bezier(0.3, 0.0, 0.2, 1); /* Push off ground */
  }
  15% {
    transform: translateY(4px) scale(1.12, 0.88); /* Squash anticipation */
  }
  30% {
    transform: translateY(-24px) scale(0.92, 1.10); /* Airborne stretch */
    animation-timing-function: cubic-bezier(0.5, 0.0, 0.8, 0.5); /* Gravity fall */
  }
  55% {
    transform: translateY(-30px) scale(0.96, 1.05); /* Peak height */
  }
  75% {
    transform: translateY(0px) scale(1.15, 0.85); /* Ground impact squash */
  }
  88% {
    transform: translateY(-4px) scale(0.98, 1.02); /* Rebound recovery */
  }
}

/* Ears Lagging Inertia */
@keyframes rabbit-ears {
  0%, 100% { transform: rotate(0deg); }
  20% { transform: rotate(-12deg); } /* Flung backwards during liftoff */
  55% { transform: rotate(8deg); }   /* Rising forward at peak */
  75% { transform: rotate(-15deg); } /* Whipped back on hard landing */
}

/* Ground Shadow Reaction */
@keyframes rabbit-shadow {
  0%, 100% { transform: scale(1.0); opacity: 0.8; }
  15% { transform: scale(1.15); opacity: 0.95; } /* Pressed down */
  55% { transform: scale(0.65); opacity: 0.35; } /* High in air: smaller, lighter */
  75% { transform: scale(1.2); opacity: 0.95; }  /* Landing */
}
```

---

### B. Vehicle / Car Drive Cycle

A vehicle requires smooth wheel rotation, high-frequency chassis suspension jitter, and subtle acceleration tilt.

```css
/* Continuous Wheel Rotation */
@keyframes wheel-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Chassis Suspension Bobbing & Jitter */
@keyframes chassis-suspension {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  25% { transform: translateY(-1.5px) rotate(-0.3deg); }
  50% { transform: translateY(1.0px) rotate(0.2deg); }
  75% { transform: translateY(-2.0px) rotate(-0.2deg); }
}

/* Exhaust Smoke Puff */
@keyframes exhaust-puff {
  0% { transform: translate(0, 0) scale(0.5); opacity: 0.8; }
  100% { transform: translate(-30px, -15px) scale(2.0); opacity: 0; }
}

#wheel_front, #wheel_back {
  transform-box: fill-box;
  transform-origin: center;
  animation: wheel-spin 0.6s linear infinite;
}

#chassis, #body {
  animation: chassis-suspension 0.4s ease-in-out infinite;
}

#exhaust {
  transform-box: fill-box;
  transform-origin: center;
  animation: exhaust-puff 1.2s ease-out infinite;
}
```

---

### C. Nature / Botanical Sway & Pulse

For plants, flowers, and organic elements, motion should feel like a gentle summer breeze.

```css
@keyframes stem-sway {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(3.5deg); }
}

@keyframes petal-breathe {
  0%, 100% { transform: scale(1.0); }
  50% { transform: scale(1.05); }
}

#stem {
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: stem-sway 4.5s ease-in-out infinite;
}

#petal_group, #bloom {
  transform-box: fill-box;
  transform-origin: center;
  animation: petal-breathe 4.5s ease-in-out infinite;
}
```

---

### D. Ambient Background (When Subject Is a Background)

If the graphic is determined to be an environmental background (halftone matrix, landscape, sky, waves):
- Do **not** apply rigid arbitrary presets.
- **Reason about the visual flow**:
  - Halftone dot matrix $\to$ diagonal wave propagation with spatial latency.
  - Sea / Lake waves $\to$ horizontal sinusoidal translation and vertical undulation.
  - Clouds / Sky $\to$ smooth horizontal parallax drift.
  - Celestial stars / constellations $\to$ organic phase-scattered twinkling.

---

## 5. Overscan Bleed Geometry & 16:9 Aspect Ratio Canvas

To prevent edge cutoffs during motion translations and maintain cinematic aesthetics:

### A. Overscan Bleed Geometry (SVG Vector Level)
Whenever background, terrain, water, ridge, or edge-touching elements move via `translate(dx, dy)` or `scale()`:
1. **Never clamp paths strictly at $[0, W]$ and $[0, H]$**. Translating by $+10\text{px}$ or $-10\text{px}$ will expose empty margins where the path detaches from the viewport edge.
2. **Extend geometry with an overscan bleed buffer ($\ge 5\% - 10\%$)**:
   - For width $W$, extend curves from $x = -X_{\text{bleed}}$ to $x = W + X_{\text{bleed}}$ (e.g. for $W = 715\text{px}$, extend from $-40\text{px}$ to $+755\text{px}$).
   - For bottom-closed ridges, close the path down past the bottom edge: $y = H + Y_{\text{bleed}}$ (e.g. $y = 260\text{px}$ for $H = 240\text{px}$).
   - For sky/backdrop rects, extend: `x="-40" y="-20" width="795" height="280"`.
3. This guarantees that translations and wave oscillations never reveal ugly straight-line cuts or background leaks.

### B. 16:9 Cinematic Canvas Presentation (Stage Framing Level)
To present animations with modern widescreen framing:
1. **Stage Aspect Ratio 16:9**: The interactive HTML container uses `aspect-ratio: 16 / 9; overflow: hidden; border-radius: 16px;`.
2. **Fit Shortest Side (`cover` / `pan-canvas`)**:
   - The shortest dimension of the SVG fits the corresponding dimension of the 16:9 frame exactly ($100\%$).
   - The longer dimension naturally bleeds outside the frame and is cleanly masked by `overflow: hidden`.
   - SVG attribute: `preserveAspectRatio="none"` or sized container ensures no letterboxing bars and completely seamless edge-to-edge immersion.

### C. Pan & Viewport Framing Alignment
When fitting the shortest side of an SVG into a 16:9 canvas, the longest side extends beyond the viewport bounds (e.g. panoramic landscapes overflow horizontally; tall portraits overflow vertically):
1. **Drag-to-Pan Direct Manipulation**: Users can click/touch and drag directly on the stage (`#svg-stage`). The canvas tracks pointer deltas and translates the underlying `#pan-canvas` in real-time.
2. **HUD Pan Slider (0% - 100%)**: A continuous slider gives precise scrubbing across the full overflow range:
   - $0\%$: Aligns minimum edge (Left / Top).
   - $50\%$: Centers the artwork symmetrically.
   - $100\%$: Aligns maximum edge (Right / Bottom).
3. **Quick Snapping Presets**: One-click quick alignment buttons (`◀ / ▲`, `⯀`, `▶ / ▼`) allow instant framing switches.
4. **Adaptive Axis Orientation**: Automatically detects whether horizontal ($X$) or vertical ($Y$) overflow dominates based on the SVG's viewBox aspect ratio relative to $16:9$.

### D. Glitch-Free Speed Scaling (Web Animations API)
Why mutating CSS `animation-duration` dynamically fails:
1. *Compounding Arithmetic*: Reading `getComputedStyle(el).animationDuration` on each input tick divides an already mutated number, resulting in recursive runaway shrinkage.
2. *Timeline Phase Teleportation*: In CSS, modifying duration forces the browser to recalculate `currentTime % newDuration`. The progress percentage jumps instantaneously to an unrelated phase of the keyframe cycle, producing visible stutters and jumps.

### E. Infinite Looping, Multi-Motion Concepts & Anti-Jitter Timer Telemetry
All contextual animations are configured with `animation-iteration-count: infinite`.

#### 1. Multi-Motion Concepts (3 Distinct Motion Styles per Subject)
Rather than a single static motion pattern, the LLM crafts **3 distinct conceptual interpretations**:
1. **Canonical Ambient Flow**: The natural, serene baseline motion (e.g., gentle parallax drift, solar radiance breathing).
2. **Environmental / Narrative Transit**: A dramatic physical event changing the scene (e.g., solar transit where the sun descends in an arc behind dunes, sky darkening into sunset gold, ridges casting dusk shadows).
3. **Chromatic Flare & Micro-Perturbation**: Dynamic color transformations, optical phenomena, or heatwave effects (e.g., sun flaring through amber to rose-crimson with atmospheric glow, dunes exhibiting subtle mirage heatwave skew).

Schema (`<subject>_motions.json`):
```json
{
  "Ambient Parallax": "/* CSS Keyframes */",
  "Solar Transit (Sunset Arc)": "/* CSS Keyframes */",
  "Chromatic Flare & Mirage": "/* CSS Keyframes */"
}
```

#### 2. Dynamic 1x Loop Timer & Anti-Jitter Stability
1. **Dynamic Scaling**: The system detects the primary/longest cycle duration ($T_{\text{base}}$) across all active layers for the currently selected style. At playback rate $S$:
   $$T_{\text{eff}} = \frac{T_{\text{base}}}{S}$$
2. **Real-time HUD Telemetry**: Displays `⏱ 1x Loop: [curSec] / [totalSec]`. When motion styles or speeds switch, total loop time recalculates on the next frame.
3. **Anti-Jitter Geometry (Digit Width Lock)**:
   - Variable-width glyph fonts cause the timer badge to twitch and stretch when numbers increment (e.g. `0.9s` to `1.0s` or `9.9s` to `10.0s`).
   - Fix: apply `font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; font-family: monospace;` with explicit width locks:
     - `.hud-timer-badge`: fixed `width: 154px; justify-content: center; flex-shrink: 0;`
     - `#loop-time-cur`: `width: 38px; text-align: right;`
     - `#loop-time-total`: `width: 38px; text-align: left;`
     - `#speed-val`: `width: 30px; text-align: right;`
     - `#pan-val`: `width: 34px; text-align: right;`
   - This ensures the HUD dimensions remain completely static and jitter-free at all times.

### F. Ultra-Slim Translucent Glass HUD Dock (2-Row Wide Layout)
To prevent UI controls from obstructing the artwork while maximizing spacious usability:
1. **In-Stage Placement**: The HUD dock floats directly inside the lower portion of `#svg-stage` (`position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); width: calc(100% - 32px); max-width: 1320px;`). It spans ~93-96% of the screen width ("hampir 1 lebar layar"), providing expansive, uncrowded controls.
2. **Glassmorphic Transparency**: Styled with `background: rgba(10, 14, 23, 0.45);` and `backdrop-filter: blur(16px) saturate(180%); border-radius: 16px;`, allowing moving vector shapes, dunes, and shadows to remain visible through the frosted glass.
3. **Structured 2-Row Architecture**:
   - **Row 1 (Telemetry, Loop Timer & Customization Controls)**:
     - Left: Subject Title + Category Badge + FPS Counter.
     - Center: Stabilized `⏱ 1x Loop: [cur] / [total]` badge.
     - Right: `🎬 Motion Style` switcher + `🎨 Color Theme` palette switcher.
   - **Row 2 (Playback Mechanics, Speed, Pan Framing & Actions)**:
     - Left: `⏸ Play/Pause` + `⚡` Speed multiplier slider and readout.
     - Center: `↔` Pan navigation slider with min, mid, and max buttons.
     - Right: `🔲 16:9 Canvas` framing toggle + `⬇ SVG` standalone exporter.

---

## 6. LLM Contextual Semantic Palette Protocol

Because the LLM analyzes the artwork's semantic anatomy, it generates **3–5 tailored color schemes** mapped 1-to-1 to the layer IDs, avoiding mismatched generic presets:

### A. Semantic Role Reasoning
1. **Light Sources (`#sun`, `#light`, `#moon`, `#glow`)**:
   - Daylight: warm white/gold (`#ffffff`, `#fff8e7`).
   - Night / Blue Hour: pale silver / moonlit cyan (`#e2e8f0`, `#cbd5e1`).
   - Sunset: deep amber / blazing gold (`#fde047`, `#fbbf24`).
2. **Shadows & Contacts (`#shadow`)**:
   - Maintain appropriate darkness or alpha opacity regardless of theme.
3. **Primary Forms & Secondary Accents**:
   - Preserve readability and atmospheric perspective (far elements softer/hazier, near elements contrasty).

### B. Schema (`<subject>_palettes.json`)
```json
{
  "Theme Name 1": {
    "layer_id_1": "#hexcolor",
    "layer_id_2": "#hexcolor"
  },
  "Theme Name 2": {
    "layer_id_1": "#hexcolor",
    "layer_id_2": "#hexcolor"
  }
}
```

---

## 7. Deliverable & File Naming Protocol

Outputs must never overwrite generic filenames:
- Source: `[source_file].png`
- Vector SVG: `<subject>.svg` (e.g. `rabbit.svg`, `car.svg`, `lotus.svg`, `halftone_wave.svg`)
- Vanilla DOM HTML: `<subject>.html`
- Contextual Palettes: `outputs/<subject>/fit_work/<subject>_palettes.json`
- Interactive Motion Preview: `<subject>_motion.html`
- Standalone Animated SVG: `<subject>_motion.svg`
- Broadcast Video Deliverables: `<subject>_<loops>x_<res>.<mp4|mov>` (e.g. `mountain_sunrise_2x_1080p.mp4`)
- Iteration Artefacts: `outputs/<subject>/fit_iterations/` and `outputs/<subject>/fit_work/`

---

## 8. Adobe Stock & Broadcast Video Export Engine

To enable seamless commercial stock monetization (Adobe Stock, Shutterstock, Pond5, Getty Images):

### A. Adobe Stock Footage Acceptance Criteria
1. **Strict Constant Frame Rate (CFR 60.000 FPS)**:
   - Automated stock ingest servers (Adobe Stock) **strictly reject Variable Frame Rate (VFR)** files.
   - Using browser screen recording or unthrottled MediaRecorder produces VFR files with timestamp jitter.
   - The export engine uses headless Chromium with Web Animations API deterministic frame stepping (`anim.currentTime = t_ms`), piping frames directly to FFmpeg `libx264` / `prores_ks` at exactly `60/1` CFR.
2. **Standard Broadcast Color Space (Rec.709)**:
   - Tagged with `color_primaries=bt709`, `color_transfer=bt709`, `color_space=bt709`.
   - Verified via `ffprobe -show_entries stream=color_space,color_primaries,color_transfer`.
3. **Clean Canvas Guarantee**:
   - Zero UI controls, HUD bars, telemetry badges, or cursors visible in the video frame.
4. **Duration & Loop Sweet Spot**:
   - Stock footage accepts durations between 5 seconds and 60 seconds.
   - 2x loop cycles of a 10s animation ($20.0\text{s}$, 1200 frames) or 3x cycles ($30.0\text{s}$, 1800 frames) hit the ideal stock footage buyer preference.
5. **Resolution Standards**:
   - 1080p Full HD ($1920 \times 1080$, standard commercial asset).
   - 4K Ultra HD ($3840 \times 2160$, premium stock asset).

### B. Speed & Pan Framing Behavior: WYSIWYG vs Normal Reset
1. **Loop Duration: Relative to Speed by Default**:
   - If the user speeds up the animation (e.g. $1.5\text{x}$), a 10s base loop takes $6.67\text{s}$.
   - The HUD modal defaults to the active speed for true WYSIWYG playback, while providing a 1-click radio option to reset to standard $1.0\text{x}$ normal speed.
2. **Visual Framing: Relative to Pan by Default**:
   - When SVGs with aspects wider than 16:9 (e.g. panoramic 2.37:1) are fitted into 1080p/4K frames, the active pan position on screen ($0\% - 100\%$) is preserved in the video render.
   - A dropdown option allows resetting instantly to perfect center ($50\%$).

