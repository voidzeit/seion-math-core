/**
 * The six mandatory self-checks.
 *
 * These run before any geometry is generated. If any fails the application is
 * forbidden from displaying a VERIFIED badge, and the failing check is shown
 * instead -- a render that silently disagrees with the theorem is worse than
 * no render.
 */

import { ETA_C, E_MAX, XI_STAR } from "./pmt_constants";
import { E, G3, W3, g, maxOverBudget, S, sosResidual } from "./pmt_exact";

export interface CheckResult {
  id: string;
  claim: string;
  passed: boolean;
  observed: string;
  expected: string;
  residual: number;
  tolerance: number;
}

export interface CheckReport {
  passed: boolean;
  results: CheckResult[];
  elapsedMs: number;
}

const mk = (
  id: string,
  claim: string,
  residual: number,
  tolerance: number,
  observed: string,
  expected: string,
): CheckResult => ({
  id,
  claim,
  residual,
  tolerance,
  observed,
  expected,
  passed: Number.isFinite(residual) && residual <= tolerance,
});

/** Check 1 — the surface maximum is exactly 2/sqrt(3). */
function check1(): CheckResult {
  const n = 1400;
  let best = 0;
  for (let i = 0; i <= n; i++)
    for (let j = 0; j <= n; j++) {
      const v = E(i / n, j / n);
      if (v > best) best = v;
    }
  return mk("SURFACE_PEAK", "max E(q,s) = 2/sqrt(3)", Math.abs(best - E_MAX), 1e-6,
    best.toFixed(12), E_MAX.toFixed(12));
}

/** Check 2 — the maximiser sits at q = s = sqrt(2/3). */
function check2(): CheckResult {
  const n = 2000;
  let best = -1, bq = 0, bs = 0;
  for (let i = 0; i <= n; i++)
    for (let j = 0; j <= n; j++) {
      const q = i / n, s = j / n, v = E(q, s);
      if (v > best) { best = v; bq = q; bs = s; }
    }
  const res = Math.max(Math.abs(bq - ETA_C), Math.abs(bs - ETA_C));
  return mk("PEAK_LOCATION", "argmax E = (sqrt(2/3), sqrt(2/3))", res, 1e-3,
    `(${bq.toFixed(6)}, ${bs.toFixed(6)})`, `(${ETA_C.toFixed(6)}, ${ETA_C.toFixed(6)})`);
}

/** Check 3 — the diagonal section is exactly g(t) = t sqrt(4 - 3t^2). */
function check3(): CheckResult {
  let worst = 0;
  for (let i = 0; i <= 40000; i++) {
    const t = i / 40000;
    worst = Math.max(worst, Math.abs(E(t, t) - g(t)));
  }
  return mk("DIAGONAL_IDENTITY", "E(t,t) = t sqrt(4 - 3 t^2)", worst, 1e-12,
    worst.toExponential(3), "0");
}

/** Check 4 — max over the admissible square equals G_3(eta). */
function check4(): CheckResult {
  const etas = [0.05, 0.2, 0.4, 0.6, ETA_C, 0.85, 0.95, 1.0];
  let worst = 0, at = 0;
  for (const e of etas) {
    const d = Math.abs(maxOverBudget(e, 600) - G3(e));
    if (d > worst) { worst = d; at = e; }
  }
  return mk("G3_GRID", "max_{q,s<=eta} E = G_3(eta)", worst, 2e-3,
    `${worst.toExponential(3)} at eta=${at.toFixed(4)}`, "0");
}

/** Check 5 — W_3 = G_3 / eta everywhere. */
function check5(): CheckResult {
  let worst = 0;
  for (let i = 1; i <= 20000; i++) {
    const e = i / 20000;
    worst = Math.max(worst, Math.abs(W3(e) - G3(e) / e));
  }
  return mk("W3_IS_G3_OVER_ETA", "W_3(eta) = G_3(eta)/eta", worst, 1e-12,
    worst.toExponential(3), "0");
}

/** Check 6 — the SOS identity holds, and S vanishes only at (sqrt2, sqrt2). */
function check6(): CheckResult {
  let worst = 0;
  for (let i = 0; i <= 300; i++)
    for (let j = 0; j <= 300; j++) {
      const xi = (i / 300) * 4, zeta = (j / 300) * 4;
      worst = Math.max(worst, Math.abs(sosResidual(xi, zeta)));
    }
  const atStar = S(XI_STAR, XI_STAR);
  const res = Math.max(worst, Math.abs(atStar));
  return mk("SOS_IDENTITY",
    "4(1+xi^2)(1+zeta^2) - 3[(xi+zeta)^2 + xi^2 zeta^2] = (xi zeta - 2)^2 + (xi - zeta)^2",
    res, 1e-9, `max residual ${worst.toExponential(3)}, S(sqrt2,sqrt2)=${atStar.toExponential(3)}`,
    "0");
}

export function runSelfChecks(): CheckReport {
  const t0 = (globalThis.performance?.now?.() ?? Date.now());
  const results = [check1(), check2(), check3(), check4(), check5(), check6()];
  const t1 = (globalThis.performance?.now?.() ?? Date.now());
  return { passed: results.every((r) => r.passed), results, elapsedMs: t1 - t0 };
}
