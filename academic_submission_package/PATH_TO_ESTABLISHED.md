# Path to an established result

Where the work stands against the four filters, what is done, and what the next action is.

```
correctness  →  bounded originality  →  independent verification  →  publication and scrutiny
    ✅ closed       ⬜ not started          ⬜ not started               ⬜ not started
```

The contribution being carried through is one article:

> **Error propagation under recursive orthogonal projection of finite multilinear
> composition trees**, whose principal result is
> `E^amb ≤ kρM^{k−1}L_T` and `E^proj = E^red ≤ (k−1)ρM^{k−1}L_T`.

Everything analytic — kernels, cochain complexes, spectral truncation, Markov operators —
is in a separate companion, and the continuum, pseudodifferential and microlocal material
appears only as questions. That separation is already in place.

---

## Filter 1 — correctness: **closed**

| Requirement | Status |
| --- | --- |
| Known mathematical defects repaired | 8 in document 01, 7 in document 02; all closed, recorded in `MATHEMATICAL_CORRECTIONS_CLOSED.md` |
| Admissible class stated in one place | §3.1, hypotheses (H1)–(H7), with the exact meaning of `M`, `ρ`, `L_T` |
| Degenerate cases treated | §3.2: `k = 0`, `k = 1`, `M = 0`, `ρ = 0`, `a_v = 1`, `L_T = 0` |
| Pathwise formula stated correctly | majorant `B̂` defined by equality; `B ≤ B̂` proved; closed form is an identity for `B̂` |
| Representation error uses only declared hypotheses | insertion point changed from `F_μ̂` to `R_μ`; the result is simpler and strictly tighter |
| Every proof audited | 25 statements, result by result, in `mathematical_audit.md` |
| Numerical statements traced to source data | 23 traced, 4 corrected |

**Nothing further is needed here before an external reviewer sees it.**

Note that optimality of `k−1` is **not** a correctness requirement. `C_T^proj(η) ≤ k−1` is
proved; `C_T^proj(η) = k−1` is open, and a theorem does not stop being correct for failing
to be optimal. The only outcome that would force a repositioning is the discovery that the
bound follows from a known more general theorem — which is filter 2, not filter 1.

## Filter 2 — bounded originality: **not started**

| Requirement | Status | Instrument |
| --- | --- | --- |
| Theorem-by-theorem comparison, 12 rows | **empty** | `external_review/ORIGINALITY_TABLE_TO_COMPLETE.md` |
| Eleven areas searched | not done | the coverage list in that file |
| Verdict per result by a human specialist | none | — |

The instrument is prepared: twelve rows, one per statement, each requiring the closest
antecedent, its hypotheses, its conclusion and the real difference, with one of six
verdicts. The rules forbid reaching a verdict from a keyword search, and forbid recording
absence of a match as `new`.

**Row O-4 is the one that matters.** If `k−1` follows from a known general theorem under
equivalent hypotheses, the article is repositioned as a specialisation, a new proof, or a
new application. All three are publishable and none would make anything incorrect.

This filter cannot be passed by the author alone, and cannot be passed by an automated
tool.

## Filter 3 — independent verification: **not started**

Two separate things are needed, and neither substitutes for the other.

### 3a. Mathematical review by two people

| Requirement | Status | Instrument |
| --- | --- | --- |
| Reviewer with a numerical-analysis brief | not sent | `external_review/REVIEWER_REQUEST.md` |
| Reviewer with a multilinear-algebra / operads brief | not sent | same |
| Structured reply to eight numbered questions | none | same |
| Reply, response, change and both versions archived | not applicable yet | — |

The request asks for answers to eight specific questions rather than an opinion, states
that a finding is a success rather than a failure, and names question 4 — *is there a prior
result that implies this one?* — as the most valuable.

### 3b. Computational reproduction

| Requirement | Status | Instrument |
| --- | --- | --- |
| First reproduction, by the author, in a clean environment | **not done** | `clean_room/Containerfile`, `clean_room/reproduce.sh` |
| Second reproduction, by another person | not done | same |
| Report with environment, commands, timings, checksums, differences | template produced by the script | — |

The container is built from a clean base and contains no part of the package until the
final copy. The script reproduces the **minimal supporting set**: package checksums, the
re-derivation of the classification, all nine figures with per-figure checksum comparison,
and all five manuscript builds with the acceptance checks — and it exits nonzero if any
check fails.

It deliberately does **not** attempt the 460 800 unexecuted optimiser trajectories, the two
unexecuted sweep stages, or the GPU measurements. None is needed to check the manuscripts.

The script has not yet been executed inside a container, because no container runtime is
available on the machine that assembled this package. That is the immediate next action for
this filter.

## Filter 4 — publication and community scrutiny: **not started**

| Step | Status |
| --- | --- |
| Numbered, frozen version with code, data and checksums | the package is assembled and checksummed; not yet frozen under a version number |
| Deposited with a persistent identifier | not done |
| Preprint posted | not done |
| Submitted to a journal | not done |
| Referee reports answered | not applicable |
| Reproduced, cited or used by others | not applicable |

The status block to accompany any public version:

```text
Theorem status .......... proved under stated assumptions (§3.1)
Optimality of k−1 ....... open
Mathematical review ..... pending
Computational repro ..... pending
Originality assessment .. pending
```

---

## The minimum path, and where it stands

| | Step | Status |
| --- | --- | --- |
| 1 | Repair the known defects | **done** |
| 2 | Freeze one principal contribution | **done** — document 01; analytic material separated into 02 |
| 3 | Audit the literature, theorem by theorem | table prepared, **empty** |
| 4 | Obtain two external mathematical reviews | request prepared, **not sent** |
| 5 | Perform a clean reproduction | kit prepared, **not executed** |
| 6 | Publish a preprint and a versioned package | **not done** |
| 7 | Submit for peer review | **not done** |
| 8 | Incorporate corrections and publish | **not done** |

Steps 1 and 2 were the ones that could be completed by editorial and mathematical work on
the existing material. Steps 3, 4 and 5 need people other than the author; step 5's first
half needs only a container runtime.

**The bottleneck is no longer producing documents. It is finding competent contradictors** —
people whose task is to find an error, an antecedent, or a missing hypothesis.

---

## Questions a referee will ask, and where each is answered

| Question | Where |
| --- | --- |
| Is the proof correct? | Appendix A, complete; `mathematical_audit.md` for the audit |
| Is the result new? | **not answered.** `literature_audit.md` says so explicitly |
| Is it significant enough? | not argued; the article claims an upper bound and an exact decomposition, nothing more |
| Is it well situated in the literature? | §2 and Table 2.1; the comparison is of overlap, not of priority |
| Is it more than an immediate consequence of `P(I−P) = 0`? | §5 and Remark 9.3. The identity `P r_ϱ = 0` is what removes the root source; the content is the **exact local decomposition** that makes the induction go through with heterogeneous types, arities and maps, and the fact that the propagated terms are exactly `k−1` in number. Whether that is enough is a referee's judgement, and the article does not pre-empt it |
| Do the numerical sections add anything? | §16 reports what was checked; the article is explicit that none of it is proof |
| Why typed trees and heterogeneous maps? | §3; the hypotheses are uniform only in `M` and `ρ`, and everything else may vary vertex to vertex. Whether that generality earns its keep is a fair question and is **not** currently argued in the article |

The last row is a gap worth closing before submission: the article does not yet explain why
the typed, heterogeneous formulation is worth having rather than the uniform one. That is a
writing task, not a mathematical one.

---

## Deliberately out of scope

The following would each be a separate research campaign and none is required for the four
filters above:

* determining `C_T^proj(η)` exactly, at `k = 2`, at `k = 3`, or in general;
* the symbolic status of the six-term generalised Jacobi expression;
* continuum limits, pseudodifferential classes, microlocal regularity;
* an external application — adaptive rank allocation in a hierarchical tensor network, or
  in low-rank adaptation of large models, or in reduced-order neural operators.

An application would raise the significance of the work considerably, and the tree tensor
network is the natural first target because it matches the theorem's hypotheses without any
extension. But it is not a prerequisite for establishing the theorem, and attempting it
before filters 2 and 3 would risk building on a result whose originality and correctness
have not been independently checked.
