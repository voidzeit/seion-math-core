/**
 * The PMT mathematics, independent of any renderer.
 *
 * JavaScript numbers are IEEE-754 binary64, so every evaluation here is
 * float64 by construction -- the precision the self-checks require. No value
 * in this file is fitted or approximated; each is the closed form from the
 * frozen k<=3 core.
 */

import { ETA_C, E_MAX, ETA_STAR } from "./pmt_constants";

/**
 * The extremal landscape.
 *
 * E(q,s)^2 = q^2 + (1-q^2)s^2 + 2 q sqrt(1-q^2) s sqrt(1-s^2)
 *
 * q = ||D_1|| is the first leakage, s = ||Q y|| the effective second one. This
 * surface does NOT depend on eta: the closure budget only decides how much of
 * it is reachable, which is the whole content of the phase transition.
 */
export function E(q: number, s: number): number {
  const cq = 1 - q * q;
  const cs = 1 - s * s;
  if (cq < 0 || cs < 0) return NaN;
  return Math.sqrt(q * q + cq * s * s + 2 * q * Math.sqrt(cq) * s * Math.sqrt(cs));
}

/** Diagonal section q = s = t. Equals E(t,t) identically. */
export function g(t: number): number {
  return t * Math.sqrt(4 - 3 * t * t);
}

/** The optimiser inside the admissible square, min(eta, eta_c). */
export function tOpt(eta: number): number {
  return Math.min(eta, ETA_C);
}

/** Absolute extremal error at M = L_T = 1. Frozen at E_MAX above eta_c. */
export function G3(eta: number): number {
  return eta <= ETA_C ? eta * Math.sqrt(4 - 3 * eta * eta) : E_MAX;
}

/** The sharp constant. W_3 = G_3 / eta -- the decay above eta_c is the division. */
export function W3(eta: number): number {
  return eta <= ETA_C ? Math.sqrt(4 - 3 * eta * eta) : E_MAX / eta;
}

/**
 * The preliminary triangle-inequality envelope. Kept because the visualiser
 * shows the gap between it and W_3; it is NOT the constant.
 */
export function U3(eta: number): number {
  return eta <= ETA_STAR
    ? 1 + Math.sqrt(1 - eta * eta)
    : Math.sqrt(1 + eta * eta) / eta;
}

/** Deficit against the universal bound, for the small-eta microscope. */
export function deficit3(eta: number): number {
  return 2 - W3(eta);
}

/** f(xi,zeta) in tangent coordinates; bounded by 4/3 with equality at (sqrt2, sqrt2). */
export function f(xi: number, zeta: number): number {
  const num = (xi + zeta) * (xi + zeta) + xi * xi * zeta * zeta;
  const den = (1 + xi * xi) * (1 + zeta * zeta);
  return num / den;
}

/** The sum of squares: S >= 0, vanishing only at xi = zeta = sqrt2. */
export function S(xi: number, zeta: number): number {
  const a = xi * zeta - 2;
  const b = xi - zeta;
  return a * a + b * b;
}

/**
 * Residual of the fundamental extremal identity
 *   4(1+xi^2)(1+zeta^2) - 3[(xi+zeta)^2 + xi^2 zeta^2] = (xi zeta - 2)^2 + (xi - zeta)^2
 * Must be zero to rounding for every (xi, zeta).
 */
export function sosResidual(xi: number, zeta: number): number {
  const lhs =
    4 * (1 + xi * xi) * (1 + zeta * zeta) -
    3 * ((xi + zeta) * (xi + zeta) + xi * xi * zeta * zeta);
  return lhs - S(xi, zeta);
}

/** Map a leakage magnitude to its tangent coordinate: q = sin(alpha), xi = tan(alpha). */
export function toTangent(q: number): number {
  return q / Math.sqrt(1 - q * q);
}

/**
 * Brute-force maximum of E over the admissible square [0, eta]^2.
 * Used only by the self-checks: the renderer consumes G3() directly.
 */
export function maxOverBudget(eta: number, n = 700): number {
  let m = 0;
  for (let i = 0; i <= n; i++) {
    const q = (eta * i) / n;
    for (let j = 0; j <= n; j++) {
      const v = E(q, (eta * j) / n);
      if (v > m) m = v;
    }
  }
  return m;
}

/** Where the reachable maximum sits, for the marker on the surface. */
export function reachablePeak(eta: number): { q: number; s: number; z: number } {
  const t = tOpt(eta);
  return { q: t, s: t, z: E(t, t) };
}

/** Regime label. Purely derived; no threshold is tuned. */
export function regime(eta: number): "budget-limited" | "critical" | "geometry-limited" {
  if (Math.abs(eta - ETA_C) < 1e-9) return "critical";
  return eta < ETA_C ? "budget-limited" : "geometry-limited";
}
