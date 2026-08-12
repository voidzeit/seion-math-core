# PMT Mathematical Observatory

Interactive GPU instrument for the **k = 3** sharp constant of Projected
Multilinear Trees.

> **Phase A only.** This delivers the first gate of the specification: renderer,
> extremal mountain, η, admissible square, critical point, diagonal, G₃, W₃,
> self-checks and benchmark. Gates 2–4 (root cancellation, k=2 gates, SOS,
> chain/branching, universal k−1, small-η, k=4 lab, DAG, obstruction,
> orthogonality, same-law, tree space) are **not built here**. The static figure
> and the 2D atlas in `../figures/` cover several of them in the meantime.

## Run

```powershell
cd papers\projected_multilinear_trees\visualizer
npm install
npm run dev          # http://localhost:5173
```

```powershell
npm run test         # 16 mathematical tests, no browser needed
npm run build        # tsc --noEmit + vite build -> dist/
```

Works offline after `npm install`. Three dev dependencies (vite, typescript,
vitest); no runtime dependencies, no cloud services.

## Architecture

```
src/math/       source of truth — no rendering, no DOM
  pmt_constants.ts   closed forms: eta_c, E_max, eta_star, phi, series coefficients
  pmt_exact.ts       E(q,s), g, G_3, W_3, U_3, f, S, sosResidual, regime
  pmt_checks.ts      the six mandatory self-checks
src/gl/
  renderer.ts        WebGL2: shaders, indexed mesh, camera, matrices
src/main.ts          wiring, controls, telemetry, plot
tests/               vitest over the math layer alone
```

The view is never the source of truth. The renderer imports `math/` and cannot
redefine a constant; the surface heights are evaluated from the same functions
the tests exercise.

**Order of operations is enforced:** mathematics → self-check → geometry →
render. If any check fails, `main.ts` replaces the stage with
`MATHEMATICAL_SELF_CHECK_FAILED` and refuses to display a VERIFIED badge.

## Why WebGL2 and not Three.js / WebGPU

The specification prefers WebGPU "if the chosen stack is sufficiently stable and
reproducible", with a Three.js preference. Both were declined deliberately:

- **Three.js** would add a large dependency for a scene that is one parametric
  surface plus a handful of line strips — perhaps 2% of the library used, and
  its WebGPU backend is its least settled part.
- **A hand-written WebGPU backend** would double the renderer for no measurable
  gain on 524k static triangles, and would be the least reproducible component
  across drivers.

WebGL2 gives real GPU rasterisation, depth testing, MSAA and per-fragment
shading with a three-package dependency tree. WebGPU availability **is**
detected and reported in telemetry (`webgpu present`), so the decision is
visible rather than hidden.

## Self-checks

**Seven** checks. Six run in float64 (JavaScript numbers are IEEE-754 binary64) before any
geometry is generated:

| id | claim | tolerance |
|---|---|---|
| `SURFACE_PEAK` | max E(q,s) = 2/√3 | 1e-6 |
| `PEAK_LOCATION` | argmax at (√(2/3), √(2/3)) | 1e-3 |
| `DIAGONAL_IDENTITY` | E(t,t) = t√(4−3t²) | 1e-12 |
| `G3_GRID` | max over [0,η]² = G₃(η), eight η | 2e-3 |
| `W3_IS_G3_OVER_ETA` | W₃ = G₃/η | 1e-12 |
| `SOS_IDENTITY` | the extremal identity, and S(√2,√2) = 0 | 1e-9 |
| `GPU_SURFACE_MATCHES_MATH` | the shader's `surf()` equals `math.E` over 3,726 probes | 2e-6 |

The seventh is a **render** check, not a math one. `SURF_GLSL` is a second
implementation of `E(q,s)` — in float32, on the GPU — so a divergence between
the drawn surface and the tested mathematics would be invisible to any test of
the math layer. Transform feedback reads the shader's own output back and
compares it. Measured worst deviation: **1.27e-7**, i.e. float32 rounding.

This check earned its place on its first run: it failed with a deviation of
exactly 2/√3, which is what you get when the capture writes nothing. The cause
was a real WebGL2 defect in the probe — a buffer left bound to `ARRAY_BUFFER`
cannot also serve as a transform-feedback target. Without the check the surface
would have rendered fine and the verification would have been decorative.

`npm run test` additionally asserts the η⁶ coefficient **27/512** rather than
merely tolerating it — an earlier version tolerated it and hid a wrong guess.

## Measured

Verified in-browser at 1099×693:

- renderer WebGL2, MSAA max 8, DPR 1.0
- auto-selected quality **ULTRA 512×512 = 524,288 triangles**
- self-checks 7/7 (six math + one render)
- 576/576 sampled framebuffer pixels non-blank across 95 distinct colours
- η = 0.95 → t_opt froze at 0.816497, G₃ = 1.154701, regime `geometry-limited`

**GPU caveat:** the embedded browser resolved to
`ANGLE (Intel, Intel(R) Graphics, D3D11)` — the integrated adapter, not the
RTX PRO 5000. `powerPreference: "high-performance"` is a hint browsers may
ignore. To use the discrete GPU, launch the browser with it selected in Windows
Graphics Settings, or via the NVIDIA control panel. The workload is small enough
that ULTRA still auto-selected on the integrated adapter.

## Epistemic contract

Every constant carries a `Status` from `pmt_constants.ts`. Phase A draws only
`THEOREM`-status objects: the surface, its peak, the admissible square, the
diagonal, G₃ and W₃ are all part of the frozen k≤3 core.

Nothing in this build draws a k ≥ 4 quantity. When the k=4 lab is added it must
read numbers from versioned artifacts and label them `NUMERICAL_EXPLORATION`
until a theorem exists — `a_T` is unknown and no curve may be invented for it.

## Reproducible views

The URL carries the full view state, so a manuscript figure can cite the link
that produced it:

```
?eta=0.900000&layers=diagonal,peak&az=-1.2000&el=0.6000&dist=2.8000
```

η, active layers and camera are read on load and rewritten on every change.
`state` copies the same thing as JSON plus the link.

## Rendering notes

The surface is opaque everywhere. Unreachable terrain is **desaturated toward
the ground**, not made translucent: alpha blending against a depth-tested mesh
is order-dependent, and an unsorted transparent surface renders incorrectly.
Blending is explicitly disabled.

## Not implemented

Gates 2–4 of the specification, and SVG export of the 2D overlays.
