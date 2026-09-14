/**
 * The mathematics is tested independently of any rendering.
 *
 * If these fail, the instrument is not allowed to claim VERIFIED, and the
 * failure is a real mathematical disagreement rather than a drawing bug.
 */

import { describe, expect, it } from "vitest";
import { A3, B3, C3_6, ETA_C, ETA_STAR, E_MAX, PHI, XI_STAR } from "../src/math/pmt_constants";
import {
  E, G3, U3, W3, deficit3, f, g, maxOverBudget, regime, reachablePeak, S, sosResidual, tOpt,
} from "../src/math/pmt_exact";
import { runSelfChecks } from "../src/math/pmt_checks";

describe("constants", () => {
  it("eta_c and E_max are the closed forms", () => {
    expect(ETA_C).toBeCloseTo(0.816496580927726, 15);
    expect(E_MAX).toBeCloseTo(1.1547005383792515, 15);
    expect(XI_STAR).toBeCloseTo(Math.SQRT2, 15);
  });

  it("eta_star is distinct from eta_c and gives the golden ratio on U_3", () => {
    expect(ETA_STAR).toBeLessThan(ETA_C);           // the two transitions differ
    expect(U3(ETA_STAR)).toBeCloseTo(PHI, 12);
    expect(W3(ETA_C)).toBeCloseTo(Math.SQRT2, 12);
  });
});

describe("surface", () => {
  it("diagonal section equals g(t) exactly", () => {
    for (let i = 0; i <= 2000; i++) {
      const t = i / 2000;
      expect(Math.abs(E(t, t) - g(t))).toBeLessThan(1e-13);
    }
  });

  it("global maximum is 2/sqrt(3) at (sqrt(2/3), sqrt(2/3))", () => {
    let best = -1, bq = 0, bs = 0;
    for (let i = 0; i <= 1200; i++)
      for (let j = 0; j <= 1200; j++) {
        const q = i / 1200, s = j / 1200, v = E(q, s);
        if (v > best) { best = v; bq = q; bs = s; }
      }
    expect(Math.abs(best - E_MAX)).toBeLessThan(1e-6);
    expect(Math.abs(bq - ETA_C)).toBeLessThan(2e-3);
    expect(Math.abs(bs - ETA_C)).toBeLessThan(2e-3);
  });

  it("is symmetric in its two leakages", () => {
    for (const [q, s] of [[0.1, 0.7], [0.33, 0.9], [0.5, 0.5], [0.81, 0.2]])
      expect(Math.abs(E(q, s) - E(s, q))).toBeLessThan(1e-14);
  });
});

describe("W_3 and G_3", () => {
  it("max over the admissible square equals G_3", () => {
    for (const e of [0.05, 0.2, 0.5, ETA_C, 0.9, 1.0])
      expect(Math.abs(maxOverBudget(e, 500) - G3(e))).toBeLessThan(2e-3);
  });

  it("W_3 = G_3 / eta", () => {
    for (let i = 1; i <= 5000; i++) {
      const e = i / 5000;
      expect(Math.abs(W3(e) - G3(e) / e)).toBeLessThan(1e-13);
    }
  });

  it("G_3 is frozen above eta_c and W_3 decays as a pure division", () => {
    for (const e of [ETA_C, 0.85, 0.9, 0.95, 1.0]) {
      expect(Math.abs(G3(e) - E_MAX)).toBeLessThan(1e-12);
      expect(Math.abs(W3(e) - E_MAX / e)).toBeLessThan(1e-12);
    }
  });

  it("is continuous at the transition and strictly below the universal bound", () => {
    expect(Math.abs(W3(ETA_C - 1e-9) - W3(ETA_C + 1e-9))).toBeLessThan(1e-7);
    for (let i = 1; i <= 1000; i++) expect(W3(i / 1000)).toBeLessThan(2);
  });

  it("the extremizer stops spending its budget above eta_c", () => {
    expect(tOpt(0.4)).toBeCloseTo(0.4, 15);              // budget-limited
    expect(tOpt(0.95)).toBeCloseTo(ETA_C, 15);           // geometry-limited
    expect(reachablePeak(0.95).z).toBeCloseTo(E_MAX, 12);
    expect(regime(0.4)).toBe("budget-limited");
    expect(regime(0.95)).toBe("geometry-limited");
  });
});

describe("SOS identity", () => {
  it("holds identically", () => {
    for (let i = 0; i <= 200; i++)
      for (let j = 0; j <= 200; j++)
        expect(Math.abs(sosResidual((i / 200) * 5, (j / 200) * 5))).toBeLessThan(1e-9);
  });

  it("S vanishes only at (sqrt2, sqrt2) and f is bounded by 4/3 there", () => {
    expect(S(XI_STAR, XI_STAR)).toBeLessThan(1e-24);
    expect(f(XI_STAR, XI_STAR)).toBeCloseTo(4 / 3, 12);
    for (let i = 0; i <= 400; i++)
      for (let j = 0; j <= 400; j++) {
        const xi = (i / 400) * 6, zeta = (j / 400) * 6;
        expect(f(xi, zeta)).toBeLessThanOrEqual(4 / 3 + 1e-12);
      }
  });
});

describe("small-eta asymptotics", () => {
  it("the two-term series leaves exactly the eta^6 coefficient behind", () => {
    // A tolerance-only test would pass against a wrong next coefficient, so the
    // residual of the two-term series is compared against 27/512 directly.
    for (const e of [0.05, 0.1, 0.2]) {
      const series2 = 2 - A3 * e * e - B3 * e ** 4;
      const residual = series2 - W3(e);          // positive: series overshoots
      expect(residual / e ** 6).toBeCloseTo(C3_6, 2);
    }
  });

  it("matches the three-term series to O(eta^8)", () => {
    for (const e of [0.02, 0.05, 0.1, 0.2]) {
      const series3 = 2 - A3 * e * e - B3 * e ** 4 - C3_6 * e ** 6;
      expect(Math.abs(W3(e) - series3)).toBeLessThan(0.05 * e ** 8 + 1e-15);
    }
  });

  it("deficit/eta^2 converges to 3/4", () => {
    expect(deficit3(1e-4) / 1e-8).toBeCloseTo(A3, 6);
  });
});

describe("mandatory self-check report", () => {
  it("all six checks pass", () => {
    const r = runSelfChecks();
    for (const c of r.results)
      expect(c.passed, `${c.id}: observed ${c.observed}, expected ${c.expected}`).toBe(true);
    expect(r.passed).toBe(true);
    expect(r.results).toHaveLength(6);
  });
});
