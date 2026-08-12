/**
 * Exact constants of the PMT k<=3 core.
 *
 * These are the source of truth. Nothing in the renderer may redefine them,
 * and no value here is fitted, interpolated or measured -- each is a closed
 * form taken from the frozen formalization.
 */

/** Critical closure budget: where the admissible square first reaches the peak. */
export const ETA_C = Math.sqrt(2 / 3); // 0.816496580927726

/** Absolute extremal error at M = L_T = 1, frozen above ETA_C. */
export const E_MAX = 2 / Math.sqrt(3); // 1.1547005383792515

/** Equality point of the SOS identity, in tangent coordinates. */
export const XI_STAR = Math.SQRT2;

/** Transition of the *preliminary* triangle-inequality envelope U_3 -- NOT of W_3. */
export const ETA_STAR = Math.sqrt((Math.sqrt(5) - 1) / 2); // 0.7861513777574233

/** U_3(ETA_STAR) = the golden ratio. Belongs to the discarded bound. */
export const PHI = (1 + Math.sqrt(5)) / 2;

/** Universal bound for k internal vertices. */
export const universalBound = (k: number): number => k - 1;

/**
 * Small-eta expansion of C_3 in the budget-limited branch. From
 * sqrt(4 - 3 eta^2) = 2 sqrt(1 - (3/4)eta^2) and the binomial series
 * sqrt(1-x) = 1 - x/2 - x^2/8 - x^3/16 - ...  with x = (3/4)eta^2:
 *
 *   C_3(eta) = 2 - (3/4)eta^2 - (9/64)eta^4 - (27/512)eta^6 - O(eta^8)
 *
 * The eta^6 coefficient is included because a test that merely *tolerated* the
 * next term would pass against a wrong one; here it is asserted.
 */
export const A3 = 3 / 4;
export const B3 = 9 / 64;
export const C3_6 = 27 / 512;

/**
 * Epistemic status of every visual element. The renderer must attach one of
 * these to anything it draws; there is deliberately no default.
 */
export type Status =
  | "THEOREM"
  | "PROVED"
  | "PROVED_UNDER_ASSUMPTIONS"
  | "NUMERICAL_VALIDATION"
  | "EXPLORATORY"
  | "OPEN_PROBLEM"
  | "FAIL_CLOSED";

export const STATUS_LABEL: Record<Status, string> = {
  THEOREM: "Theorem",
  PROVED: "Proved",
  PROVED_UNDER_ASSUMPTIONS: "Proved under assumptions",
  NUMERICAL_VALIDATION: "Numerical validation",
  EXPLORATORY: "Exploratory — not a theorem",
  OPEN_PROBLEM: "Open problem",
  FAIL_CLOSED: "Fail-closed",
};
