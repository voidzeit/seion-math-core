/**
 * PMT Mathematical Observatory — Phase A.
 *
 * Order of operations is the contract: mathematics -> self-check -> geometry
 * -> render. If the self-checks fail the instrument refuses to draw and shows
 * MATHEMATICAL_SELF_CHECK_FAILED instead of a surface.
 */

import { ETA_C, E_MAX, STATUS_LABEL } from "./math/pmt_constants";
import { E as Eexact, G3, W3, deficit3, regime, tOpt } from "./math/pmt_exact";
import { runSelfChecks } from "./math/pmt_checks";
import { Observatory, QUALITIES, type CameraState, type Quality } from "./gl/renderer";

const $ = (id: string) => document.getElementById(id)!;
const CRIT: [number, number, number, number] = [0.91, 0.28, 0.31, 1];

/* ---------------------------------------------------- 1. mathematics */
const report = runSelfChecks();
const checksEl = $("checks");
checksEl.innerHTML = report.results
  .map((r) => `<div class="chk ${r.passed ? "ok" : "bad"}">
      <span class="cid">${r.passed ? "PASS" : "FAIL"}</span>
      <span class="cname">${r.id}</span>
      <span class="cres mono">${r.residual.toExponential(2)} &le; ${r.tolerance.toExponential(0)}</span>
    </div>`)
  .join("");
$("checkTime").textContent = `${report.elapsedMs.toFixed(0)} ms · float64`;

if (!report.passed) {
  $("stage").innerHTML =
    `<div class="fatal"><div class="fatalTitle">MATHEMATICAL_SELF_CHECK_FAILED</div>
     <p>The instrument will not render a surface it cannot certify. Failing checks:
     ${report.results.filter((r) => !r.passed).map((r) => r.id).join(", ")}.</p></div>`;
  $("verifiedBadge").textContent = "NOT VERIFIED";
  $("verifiedBadge").className = "vbadge bad";
  throw new Error("MATHEMATICAL_SELF_CHECK_FAILED");
}
// The math badge is provisional until the renderer has also been checked; the
// GPU runs a second implementation of the surface, in float32.
$("verifiedBadge").textContent = "math 6/6 · checking render";
$("verifiedBadge").className = "vbadge ok";

/* ------------------------------------------- 2. geometry and renderer */
const canvas = $("gl") as HTMLCanvasElement;
let obs: Observatory;
try {
  obs = new Observatory(canvas, QUALITIES[1]);
} catch (e) {
  $("stage").innerHTML = `<div class="fatal"><div class="fatalTitle">WEBGL2_UNAVAILABLE</div>
    <p>This instrument requires WebGL2 for real GPU rasterisation. ${String(e)}</p></div>`;
  throw e;
}

/**
 * Render self-check: does the GPU's surface agree with the tested one?
 *
 * `SURF_GLSL` duplicates `math/pmt_exact.E`. Transform feedback reads the
 * shader's own output back so the two can be compared. float32 gives roughly
 * 1e-7 relative precision, so the tolerance is set there — anything larger is
 * a genuine divergence, not rounding.
 */
function renderSelfCheck(): { passed: boolean; worst: number; n: number; tol: number } {
  const probes: number[] = [];
  const N = 61;
  for (let i = 0; i < N; i++)
    for (let j = 0; j < N; j++) probes.push(i / (N - 1), j / (N - 1));
  // include the points the theorem actually cares about
  probes.push(ETA_C, ETA_C, 1, 1, 0, 0, ETA_C, 0.2, 0.999, 0.999);
  const pts = new Float32Array(probes);
  const gpu = obs.probeSurface(pts);
  let worst = 0;
  for (let i = 0; i < gpu.length; i++) {
    const d = Math.abs(gpu[i] - Eexact(pts[2 * i], pts[2 * i + 1]));
    if (d > worst) worst = d;
  }
  const tol = 2e-6;
  return { passed: worst <= tol, worst, n: gpu.length, tol };
}

/**
 * Pick a mesh resolution, conservatively.
 *
 * Timing draw calls with `gl.finish()` proved not to measure execution on this
 * stack: an 8.4M-triangle mesh reported 0.03 ms/frame, faster than a 32k one,
 * and the ladder was not monotone. Those numbers were measuring submission, not
 * work, so they are not used. Auto-selection therefore stops at ULTRA, which is
 * verified interactive; EXTREME and INSANE remain available manually for anyone
 * who wants to push the mesh and watch the real frame counter.
 */
const AUTO_MAX = 3; // index of ULTRA

function autoQuality(): Quality {
  let chosen = QUALITIES[0];
  for (let i = 0; i <= AUTO_MAX; i++) {
    const q = QUALITIES[i];
    obs.setQuality(q);
    const t0 = performance.now();
    for (let f = 0; f < 6; f++) draw(0.5);
    if ((performance.now() - t0) / 6 <= 16.6) chosen = q; else break;
  }
  obs.setQuality(chosen);
  return chosen;
}

/**
 * A view is reproducible only if it can be handed to someone else. The URL
 * carries eta, camera and layers, so a figure in the manuscript can cite the
 * exact link that produced it.
 */
function readUrlState(): { eta: number; layers: Record<string, boolean>; cam?: CameraState } {
  const p = new URLSearchParams(location.search);
  const num = (k: string, d: number) => {
    const v = parseFloat(p.get(k) ?? "");
    return Number.isFinite(v) ? v : d;
  };
  const layers = (p.get("layers") ?? "").split(",").filter(Boolean);
  const has = (k: string) => (p.has("layers") ? layers.includes(k) : true);
  const out: { eta: number; layers: Record<string, boolean>; cam?: CameraState } = {
    eta: Math.min(1, Math.max(0.02, num("eta", 0.4))),
    layers: { diagonal: has("diagonal"), square: has("square"),
              peak: has("peak"), axis: has("axis") },
  };
  if (p.has("az")) out.cam = { az: num("az", -0.86), el: num("el", 0.52), dist: num("dist", 3.1) };
  return out;
}

function writeUrlState(): void {
  const p = new URLSearchParams();
  p.set("eta", eta.toFixed(6));
  p.set("layers", Object.entries(state).filter(([, v]) => v).map(([k]) => k).join(","));
  p.set("az", obs.cam.az.toFixed(4));
  p.set("el", obs.cam.el.toFixed(4));
  p.set("dist", obs.cam.dist.toFixed(4));
  history.replaceState(null, "", `${location.pathname}?${p}`);
}

const initial = readUrlState();
let eta = initial.eta;
const state = { ...initial.layers } as { diagonal: boolean; square: boolean; peak: boolean; axis: boolean };
const dark = () => {
  const forced = document.documentElement.getAttribute("data-theme");
  if (forced) return forced === "dark";
  return matchMedia("(prefers-color-scheme: dark)").matches;
};

function draw(e: number): void {
  obs.render(e, { ...state, dark: dark(), emax: E_MAX, critical: CRIT });
}

/* --------------------------------------------------- 3. derived plot */
const plot = $("plot") as HTMLCanvasElement;
function drawPlot(): void {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = plot.clientWidth, h = plot.clientHeight;
  plot.width = w * dpr; plot.height = h * dpr;
  const c = plot.getContext("2d")!;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, w, h);
  const cs = (n: string) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const L = 46, R = 14, T = 12, B = 22, pw = w - L - R, ph = h - T - B;
  const X = (v: number) => L + v * pw, Y = (v: number) => T + ph - (v / 2.15) * ph;

  c.strokeStyle = cs("--grid"); c.lineWidth = 1;
  for (const v of [0, 0.5, 1, 1.5, 2]) {
    c.beginPath(); c.moveTo(L, Y(v)); c.lineTo(L + pw, Y(v)); c.stroke();
    c.fillStyle = cs("--dim"); c.font = "9.5px ui-monospace,Menlo,monospace";
    c.textAlign = "right"; c.fillText(v.toFixed(1), L - 6, Y(v) + 3);
  }
  const curve = (f: (e: number) => number, col: string, lw: number) => {
    c.beginPath();
    for (let i = 0; i <= 400; i++) {
      const e = 0.005 + 0.995 * (i / 400);
      i ? c.lineTo(X(e), Y(f(e))) : c.moveTo(X(e), Y(f(e)));
    }
    c.strokeStyle = col; c.lineWidth = lw; c.stroke();
  };
  curve(W3, "#5E8C7A", 1.9);
  curve(G3, cs("--crit"), 2.3);
  c.setLineDash([3, 3]); c.globalAlpha = .5;
  c.beginPath(); c.moveTo(X(ETA_C), T); c.lineTo(X(ETA_C), T + ph);
  c.strokeStyle = cs("--crit"); c.lineWidth = 1.2; c.stroke();
  c.setLineDash([]); c.globalAlpha = 1;
  c.beginPath(); c.moveTo(X(eta), T); c.lineTo(X(eta), T + ph);
  c.strokeStyle = cs("--text"); c.globalAlpha = .55; c.lineWidth = 1.1; c.stroke();
  c.globalAlpha = 1;
  for (const [f, col] of [[G3, cs("--crit")], [W3, "#5E8C7A"]] as [(e: number) => number, string][]) {
    c.beginPath(); c.arc(X(eta), Y(f(eta)), 3.8, 0, 7); c.fillStyle = col; c.fill();
  }
  c.fillStyle = cs("--dim"); c.font = "9.5px ui-monospace,Menlo,monospace";
  c.textAlign = "left"; c.fillText("G₃ absolute", L + 6, T + 11);
  c.fillStyle = "#5E8C7A"; c.fillText("W₃ constant", L + 6, T + 23);
  c.fillStyle = cs("--dim"); c.textAlign = "center"; c.fillText("η", L + pw / 2, h - 5);
}

/* ------------------------------------------------------- 4. readouts */
function sync(): void {
  const t = tOpt(eta), reg = regime(eta), locked = reg !== "budget-limited";
  ($("etaOut")).textContent = eta.toFixed(6);
  ($("tOut")).textContent = t.toFixed(6);
  ($("gOut")).textContent = G3(eta).toFixed(6);
  ($("wOut")).textContent = W3(eta).toFixed(6);
  ($("dOut")).textContent = deficit3(eta).toExponential(3);
  ($("regOut")).textContent = reg;
  $("regBox").className = "regime" + (locked ? " locked" : "");
  $("regWhy").textContent = locked
    ? "The admissible square already contains the global extremizer. Enlarging it reaches only lower terrain, so the absolute supremum over the class is frozen at 2/√3."
    : "The corner of the square is the best reachable point, so the extremizer spends the whole budget: t = η.";
  draw(eta);
  drawPlot();
  writeUrlState();
}

/* -------------------------------------------------------- 5. controls */
($("eta") as HTMLInputElement).addEventListener("input", (ev) => {
  eta = parseFloat((ev.target as HTMLInputElement).value); sync();
});
$("toEtaC").addEventListener("click", () => {
  eta = ETA_C; ($("eta") as HTMLInputElement).value = String(ETA_C); sync();
});
for (const k of ["diagonal", "square", "peak", "axis"] as const) {
  const el = $("t_" + k) as HTMLInputElement;
  el.addEventListener("change", () => { (state as any)[k] = el.checked; draw(eta); });
}
const qSel = $("quality") as HTMLSelectElement;
QUALITIES.forEach((q, i) => qSel.add(new Option(`${q.name} · ${q.n}×${q.n}`, String(i))));
qSel.addEventListener("change", () => {
  obs.setQuality(QUALITIES[parseInt(qSel.value)]); updateTelemetry(); draw(eta);
});
$("reset").addEventListener("click", () => {
  obs.cam = { az: -0.86, el: 0.52, dist: 3.1 }; draw(eta);
});
$("present").addEventListener("click", () => {
  document.body.classList.toggle("present");
  requestAnimationFrame(() => sync());
});
$("shot").addEventListener("click", () => {
  draw(eta);
  const a = document.createElement("a");
  a.download = `pmt_eta_${eta.toFixed(4)}.png`;
  a.href = canvas.toDataURL("image/png"); a.click();
});
$("snap").addEventListener("click", () => {
  const s = { mode: "extremal_mountain", eta, camera: obs.cam, layers: { ...state },
              quality: obs.quality.name, selfChecks: report.passed ? "PASS" : "FAIL" };
  navigator.clipboard?.writeText(JSON.stringify({ ...s, url: location.href }, null, 2));
  const b = $("snap"); const o = b.textContent; b.textContent = "copied";
  setTimeout(() => (b.textContent = o), 1200);
});

let drag: { x: number; y: number } | null = null;
canvas.addEventListener("pointerdown", (e) => {
  drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  if (!drag) return;
  obs.cam.az -= (e.clientX - drag.x) * 0.008;
  obs.cam.el = Math.max(-0.2, Math.min(1.42, obs.cam.el + (e.clientY - drag.y) * 0.006));
  drag = { x: e.clientX, y: e.clientY }; draw(eta);
});
canvas.addEventListener("pointerup", () => { drag = null; writeUrlState(); });
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  obs.cam.dist = Math.max(1.5, Math.min(7, obs.cam.dist * (e.deltaY > 0 ? 1.06 : 0.94)));
  draw(eta);
}, { passive: false });

/* ------------------------------------------------------ 6. telemetry */
let frames = 0, acc = 0, last = performance.now();
function updateTelemetry(): void {
  $("tel").innerHTML = [
    ["renderer", obs.info.api.toUpperCase()],
    ["webgpu present", String(obs.info.webgpuAvailable)],
    ["gpu", obs.info.renderer.slice(0, 46)],
    ["mesh", `${obs.quality.n}×${obs.quality.n}`],
    ["triangles", obs.triangles.toLocaleString()],
    ["msaa max", String(obs.info.maxSamples)],
    ["dpr", obs.info.dpr.toFixed(2)],
  ].map(([k, v]) => `<div class="tl"><span>${k}</span><b class="mono">${v}</b></div>`).join("");
}
function loop(now: number): void {
  acc += now - last; last = now; frames++;
  if (acc >= 500) {
    $("fps").textContent = `${(frames * 1000 / acc).toFixed(0)} fps · ${(acc / frames).toFixed(1)} ms`;
    frames = 0; acc = 0;
  }
  requestAnimationFrame(loop);
}

if (initial.cam) obs.cam = initial.cam;
($("eta") as HTMLInputElement).value = String(eta);
for (const k of ["diagonal", "square", "peak", "axis"] as const)
  ($("t_" + k) as HTMLInputElement).checked = state[k];

const q = autoQuality();
qSel.value = String(QUALITIES.indexOf(q));

const rcheck = renderSelfCheck();
checksEl.insertAdjacentHTML("beforeend",
  `<div class="chk ${rcheck.passed ? "ok" : "bad"}">
     <span class="cid">${rcheck.passed ? "PASS" : "FAIL"}</span>
     <span class="cname">GPU_SURFACE_MATCHES_MATH</span>
     <span class="cres mono">${rcheck.worst.toExponential(2)} &le; ${rcheck.tol.toExponential(0)}</span>
   </div>`);
if (!rcheck.passed) {
  $("verifiedBadge").textContent = "RENDER CHECK FAILED";
  $("verifiedBadge").className = "vbadge bad";
  $("stage").innerHTML =
    `<div class="fatal"><div class="fatalTitle">RENDER_SELF_CHECK_FAILED</div>
     <p>The GPU surface disagrees with the tested mathematics by
     ${rcheck.worst.toExponential(3)} over ${rcheck.n} probes. The instrument will
     not present a surface it cannot certify.</p></div>`;
  throw new Error("RENDER_SELF_CHECK_FAILED");
}
$("verifiedBadge").textContent = `VERIFIED · math 6/6 · gpu ${rcheck.n} probes`;
$("verifiedBadge").className = "vbadge ok";

updateTelemetry();
// Report the adapter that actually served this context (dev only). See the
// gpu-report plugin in vite.config.ts for why eyeballing a panel is not enough.
if (import.meta.env.DEV) {
  fetch("/__gpu", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      renderer: obs.info.renderer, vendor: obs.info.vendor,
      api: obs.info.api, webgpuAvailable: obs.info.webgpuAvailable,
      maxSamples: obs.info.maxSamples, dpr: obs.info.dpr,
      quality: obs.quality.name, triangles: obs.triangles,
      mathChecks: `${report.results.filter((r) => r.passed).length}/${report.results.length}`,
      renderCheck: { passed: rcheck.passed, worst: rcheck.worst, probes: rcheck.n },
      userAgent: navigator.userAgent,
    }),
  }).catch(() => { /* the instrument works with or without the report */ });
}

$("statusLine").textContent =
  `${STATUS_LABEL.THEOREM} · C₃ᴾ·ᶠⁱⁿ(η) = W₃(η) — frozen k≤3 core`;
addEventListener("resize", sync);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", sync);
sync();
requestAnimationFrame(loop);
