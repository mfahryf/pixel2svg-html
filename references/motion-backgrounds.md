# Motion Background Engineering Guide

This guide establishes the architecture, math, performance parameters, and aesthetic criteria for generating loopable, ambient vector motion backgrounds from vectorized SVGs in **Pixel2SVG-HTML**.

---

## 1. Philosophy: Ambient Backgrounds vs. Brand Reveals

Unlike `pixel2motion` (which orchestrates high-energy logo intros, draw-on reveals, and step sequencers), **Pixel2SVG-HTML Motion Backgrounds** are engineered for **continuous ambient immersion**:

| Trait | Motion Background (This Skill) | Logo Reveal (`pixel2motion`) |
| :--- | :--- | :--- |
| **Pacing** | Relaxed, meditative (4s – 10s period) | Snappy, punchy (0.8s – 2.5s) |
| **Looping** | Seamless infinite periodic oscillation | One-shot or segmented play/pause |
| **Cognitive Load** | Subordinate to foreground text & UI | Draws 100% focal attention |
| **Reactivity** | Spatial coordinate waves, optional mouse aura | Keyframe timelines, easing curves |
| **Performance** | Pure CSS GPU compositor (0% JS thread) | Web Animations API / GSAP |

---

## 2. Spatial Phase Propagation Math

The core visual beauty of motion backgrounds stems from **spatial coherence**: elements do not animate in rigid lockstep; instead, an organic wave ripples through the vector elements based on their spatial positions $(x, y)$.

### A. Directional Wave (`wave`)
Project element coordinates onto a wave normal vector $\vec{n} = (\cos\theta, \sin\theta)$:
$$\text{proj}_i = x_i \cos\theta + y_i \sin\theta$$
$$\text{phase}_i = \left(\frac{\text{proj}_i}{\Delta_{\text{max}}} \cdot f\right) \pmod{1}$$
$$\text{delay}_i = -\text{phase}_i \cdot T$$

*Result:* Smooth, continuous waves gliding diagonally across halftone matrices, grids, or dispersed vectors.

### B. Radial Ripple (`ripple`)
Measure Euclidean distance from the geometric centroid $(cx_0, cy_0)$:
$$r_i = \sqrt{(x_i - cx_0)^2 + (y_i - cy_0)^2}$$
$$\text{delay}_i = -\left(\frac{r_i}{R_{\text{max}}} \cdot f \pmod{1}\right) \cdot T$$

*Result:* Hypnotic outward waves like droplets undulating across a liquid pond.

### C. Organic Breathe (`breathe`)
Global expansion/contraction combined with mild center-to-edge latency:
$$\text{delay}_i = -\left(\frac{r_i}{R_{\text{max}}} \cdot 0.35\right) \cdot T$$

*Result:* Living, breathing creature effect without spatial dislocation.

### D. Specular Shimmer (`shimmer`)
A narrow, sharp specular sweep where brightness, scale, and drop-shadow flare up briefly:
$$\text{delay}_i = -\left(\frac{x_i + y_i}{W + H} \pmod{1}\right) \cdot T$$

*Result:* Sleek, futuristic metallic light-glint sweeping across vector edges.

### E. Harmonic Drift (`drift`)
Sinusoidal translation in $(dx, dy)$ coupled with soft scale breathing:
$$\Delta x(t) = A_x \sin(\omega t + \phi_x), \quad \Delta y(t) = A_y \cos(\omega t + \phi_y)$$

*Result:* Weightless celestial floating particles or ambient constellations.

---

## 3. High-Performance CSS & SVG Architecture

To animate thousands of vector elements (such as dense halftone dot grids with 3,000+ circles) smoothly at 60–120 FPS on mobile and low-power devices:

1. **`transform-box: fill-box` and `transform-origin: center`**:
   Allows each SVG child primitive (`<circle>`, `<ellipse>`, `<path>`, `<rect>`) to scale or translate around its own individual bounding box without computing per-element matrices in JS.
2. **Hardware Compositing**:
   Animates strictly `transform` and `opacity` properties, which run directly on the GPU compositor thread without triggering layout reflows (`relayout`) or CPU repaints.
3. **Negative Animation Delays (`animation-delay: -Xs`)**:
   By using negative delays, all elements are already mid-flight when the page loads—preventing initial "stutters" or awkward synchronized starting pops.

---

## 4. Deliverable Formats

1. **Standalone Animated SVG (`logo_motion.svg`)**:
   Contains inline `<style>` and keyframes. Can be directly used in `<img>`, `<object>`, CSS `background-image`, Figma, or video editors.
2. **Interactive HTML Motion Background Preview (`logo_motion.html`)**:
   - Fullscreen full-bleed mode vs Contained card view.
   - Live glassmorphism HUD controls: preset switching, speed multiplier, intensity/amplitude slider.
   - Interactive mouse proximity deflection / excitation.
   - Instant SVG export button.
