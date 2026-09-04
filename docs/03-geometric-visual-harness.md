# 03 — Geometric Visual Harness (GVH)

The Geometric Visual Harness is the objective spatial measurement layer of UI-Agentic.

Its job is to turn a real browser-rendered interface into geometry, spatial relations, constraints, stability margins, and regression evidence. It does **not** decide whether a design is aesthetically good.

---

## 1. Fundamental model

A rendered interface is a geometry that depends on environment and state:

```text
G = f(W, H, S, C, Q, T)
```

Where:

- `W`, `H` — viewport dimensions;
- `S` — scroll state;
- `C` — content;
- `Q` — UI state;
- `T` — time/frame.

The browser remains the real forward simulator. GVH measures the output of Flexbox, Grid, intrinsic sizing, wrapping, media/container queries, transforms, clipping, and paint order. It does not replace the browser layout engine with a simplified model.

---

## 2. Spatial precision ladder

A simple box is useful, but not sufficient for every spatial claim.

```text
L0 — LAYOUT BOX
     x / y / width / height + parent-relative coordinates

L1 — FRAGMENTS
     client rects, multiline text fragments, fragmented boxes

L2 — TRANSFORMED REGION
     transform matrix + resulting quad/polygon

L3 — CLIPPED / VISIBLE REGION
     transformed region intersected with ancestor clips and viewport

L4 — LAYERED REGION
     stacking context + paint order + top layer + occlusion relation
```

A result must not claim a higher precision level than the data actually supports.

---

## 3. Coordinate systems

GVH preserves relevant coordinate systems rather than collapsing everything into one number space.

At applicable precision levels, a node can retain:

1. absolute/document or viewport coordinates;
2. local coordinates relative to the parent or scroll container;
3. normalized coordinates relative to the viewport or parent;
4. a coordinate chain through nested scroll containers, iframes, and transforms.

For SVG, the system can retain local geometry plus the transformation into viewport coordinates. For top-layer or pseudo-element cases, explicit scene/layer nodes may be required when measurable.

---

## 4. Opaque surfaces

Some surfaces are not inspectable through normal DOM geometry:

- canvas;
- WebGL;
- video internals;
- cross-origin embedded content.

GVH may verify their external box and relations. It must not claim certified internal geometry unless a dedicated instrumentation/adapter exposes verifiable internal structure.

Unmeasurable required geometry remains `UNKNOWN`.

---

## 5. Z is relational, not one global number

Visual depth is not represented correctly by comparing `z-index` values globally.

Actual layering depends on:

- stacking contexts;
- paint order;
- `z-index` inside the relevant context;
- transforms;
- portals;
- pseudo-elements;
- fixed/sticky positioning;
- clipping ancestors;
- browser top-layer behavior.

GVH therefore models depth as a partial order and occlusion relationship.

Useful relations include:

```text
PAINTED_ABOVE(A, B)
PAINTED_BELOW(A, B)
SAME_STACKING_CONTEXT(A, B)
OCCLUDES(A, B)
NOT_OCCLUDED(node)
CLIPPED_BY(node, ancestor)
OVERLAY_ABOVE_CONTENT(overlay)
```

This allows the system to catch cases where geometry is correct in `x/y` but a menu, tooltip, backdrop, or modal is visually behind or clipped by another surface.

---

## 6. Geometry IR

GVH produces a serializable Geometry Intermediate Representation.

Conceptual example:

```yaml
viewport:
  width: 1440
  height: 900

nodes:
  sidebar:
    parent: app
    box: [0, 0, 264, 900]

  main:
    parent: app
    box: [288, 0, 1152, 900]

  modal:
    parent: overlay-root
    precision: L4
    box: [320, 120, 800, 600]
    fragments: []
    transform_matrix: []
    visible_region: []
    coordinate_chain: [document, viewport]
    layer:
      stacking_context: overlay-root
      top_layer: true
      z_index: 50
      position_mode: fixed

constraints:
  - id: family.app.sidebar-width
    owner: FAMILY
    type: width
    node: sidebar
    expected: 264
    tolerance: 0.5
    strength: required
```

The IR should be serializable, diffable, and linked to the ownership model defined by the stabilization method.

---

## 7. Scene graph and group geometry

The DOM is converted into the smallest spatial graph needed by the rule set.

```text
Page
├── Sidebar
└── Main
    ├── Header
    └── Content
        ├── Card A
        └── Card B
```

### Basic 2D relations

```text
LEFT_OF(A, B)
ABOVE(A, B)
ALIGN_LEFT(A, B)
ALIGN_CENTER(A, B)
GAP_X(A, B) = n
GAP_Y(A, B) = n
CONTAIN(child, parent)
WIDTH(node) = n
HEIGHT(node) = n
RATIO(node) = r
```

### Group constraints

GVH should also reason about collections:

```text
EQUAL_WIDTH(cards[*])
EQUAL_HEIGHT(cards[*])
UNIFORM_GAP_X(cards[*])
UNIFORM_GAP_Y(items[*])
ALIGN_TOP(group[*])
ALIGN_LEFT(group[*])
DISTRIBUTE_X(group[*])
DISTRIBUTE_Y(group[*])
COLUMN_RATIO(left, right) = r
```

A grid can fail as a group even when no individual pair produces an obvious hard violation.

---

## 8. Core spatial measurements

### Alignment residual

```text
r_align = |x_A - x_B|
```

### Gap

```text
g = x_B - (x_A + w_A)
r_gap = |g - g_target|
```

### Containment

Measure overflow against the declared containing region, including padding or safe-area rules when applicable.

### Collision

Use bounding boxes as a broad phase, then use the highest available transformed/clipped region precision when the decision requires it.

The verifier must distinguish:

- intentional overlap;
- valid occlusion;
- invalid collision;
- invalid clipping;
- unknown result due to insufficient geometric precision.

### Group distribution

Measure dimensions, alignment axes, successive gaps, row/column regularity, ratios, and distribution across the collection.

### Layer / occlusion

At an intersection region, compare actual paint order and visible area against the declared relation.

---

## 9. Residual vector

A set of geometric constraints can be represented by residuals:

```text
R = [r₁, r₂, ..., rₙ]
```

Required constraints must remain within their declared tolerances. Soft criteria are evaluated separately and cannot compensate for hard failures.

---

## 10. Hard vs soft geometric constraints

### Hard

Examples:

- unintended overflow;
- unauthorized collision;
- containment violation;
- invalid critical layer order;
- required control partially/fully occluded;
- unauthorized clipping;
- invalid overlay/backdrop/modal order;
- required target minimum;
- safe-area violation;
- explicitly locked width/height/ratio;
- violated parent geometry contract.

### Soft

Examples:

- spacing regularity;
- alignment quality;
- grid consistency;
- balance;
- density;
- symmetry;
- rhythm.

A soft score cannot hide a hard spatial failure.

---

## 11. Stability Margin

One of the most useful GVH concepts is the **distance to the nearest violation**.

Two results may both pass but have very different robustness:

```text
PASS
margin: 0.4px
risk: HIGH
```

versus:

```text
PASS
margin: 37px
risk: LOW
```

A near-zero pass is fragile and should remain visible to the system even when no current violation exists.

---

## 12. Responsive behavior as a domain

For a rendered element:

```text
xᵢ = fᵢ(W)
wᵢ = gᵢ(W)
```

Discrete breakpoint sampling is useful, but some contracts require stronger exploration.

A responsive search can use:

```text
coarse sweep
→ identify suspicious interval
→ adaptive subdivision
→ boundary search
→ critical width
```

Topology changes should be explicit, for example:

```text
Desktop: A LEFT_OF B
Mobile:  A ABOVE B
```

A declared topology transition is not a regression.

---

## 13. Sensitivity

Sensitivity measures how strongly geometry reacts to a small parameter change:

```text
S = ||G(p + ε) - G(p)|| / ε
```

High sensitivity can indicate that a small width/content change may trigger wrapping, reflow, or a topology transition.

Sensitivity complements the Stability Margin.

---

## 14. Controlled perturbation

The harness can explore controlled variations such as:

- viewport width and height;
- text length;
- number of items;
- image presence/absence;
- loading/empty/error states;
- modal/drawer state;
- scroll position;
- late font/image resolution;
- hydration or lazy loading.

Every perturbation must remain within the declared Supported Domain or be labeled as discovery-only.

---

## 15. Temporal geometry

Geometry is not always static:

```text
G₁ → G₂ → G₃ → ...
```

GVH should distinguish intentional motion from forbidden instability.

A static baseline should only be captured after the Measurement Readiness Gate is satisfied.

For animation-specific rules, time should be controlled and `G(t)` evaluated at the required events/instants instead of simply forcing a final frame.

Two identical frames can be a useful practical signal, but they are not universal proof of global temporal stability.

---

## 16. Text is geometry

Text affects layout and must be measured as spatial data when relevant.

Useful measurements include:

- number of lines;
- line/fragment rectangles;
- line width;
- block height;
- wrapping behavior;
- clipping;
- collision caused by text growth.

This helps locate the exact width or content boundary that changes the structure.

---

## 17. Latent design-system inference

Measured values may form clusters:

```text
7.9, 8.0, 8.1   → candidate token: 8
15.8, 16.0      → candidate token: 16
23.9, 24.0      → candidate token: 24
```

The same idea can be applied to:

- alignment axes;
- control sizes;
- measurable radii;
- proportions;
- container widths.

This is an observation, not a normative design token until the design system accepts it.

---

## 18. Geometric fingerprint

A page-level geometric fingerprint can contain:

```text
hierarchy
normalized boxes
fragment geometry
alignment axes
group geometry
gap distribution
proportions
topology
stacking contexts / paint relations
occlusion / clipping map
density
constraint graph
```

The fingerprint helps explain **what changed, where, and by how much**.

---

## 19. Geometry diff vs visual diff

The two are complementary:

```text
GEOMETRIC DIFF
+
PIXEL / PERCEPTUAL / VISUAL DIFF
```

Geometry explains structural drift. Paint/visual analysis captures color, imagery, texture, font rasterization, and design intent that geometry alone cannot represent.

---

## 20. Canonical violation output

Example:

```yaml
violation:
  constraint: page.orders.grid-gap
  owner: PAGE
  detect: rendered
  spatial_domain: group-spacing
  expected: 24
  actual: 20
  residual: 4
  tolerance: 0.5
  stability_margin: -3.5
  viewport: [846, 900]
  state: default
  status: FAIL
```

Layering example:

```yaml
violation:
  constraint: overlay.modal.above-header
  owner: FAMILY
  detect: rendered
  spatial_domain: layer-order
  expected: modal PAINTED_ABOVE header
  actual: header occludes modal
  status: FAIL
```

---

## 21. What GVH does not own

GVH does not decide:

- whether a visual style is attractive;
- whether a brand direction is appropriate;
- whether semantic roles are correct except when geometry depends on them;
- whether keyboard transitions are functionally correct except where required by a cross-layer invariant;
- whether a color/contrast rule passes except through the paint verifier;
- whether a temporal behavior is acceptable except through geometry-specific temporal rules.

GVH is one verification engine inside the larger UI-Agentic architecture.
