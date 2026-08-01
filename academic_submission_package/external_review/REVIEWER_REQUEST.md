# Request for independent mathematical review

This is the text to send with the manuscript, and the form in which the reply is wanted.
The point of an external review here is **not** endorsement. It is that somebody other than
the author tries to break the result.

---

## What is being sent

| | |
| --- | --- |
| Manuscript | `papers/01_recursive_projection_of_multilinear_trees.pdf`, 39 pages including complete proofs in Appendix A |
| Companion (optional) | `papers/02_kernel_defined_multilinear_operators.pdf`, 10 pages |
| Known-defect record | `MATHEMATICAL_CORRECTIONS_CLOSED.md` — the defects already found and fixed, so that time is not spent rediscovering them |
| Audit | `mathematical_audit.md` — the author's own result-by-result audit |
| Statement of status | `scholarly_status.md` — what is and is not claimed |

The main result, in one line: for a finite tree of multilinear maps whose intermediate
outputs are orthogonally projected onto prescribed subspaces, with `‖μ_v‖ ≤ M` and
`‖(I−P_v)μ_v(P·,…,P·)‖ ≤ ρ` at every vertex and `k ≥ 1` internal vertices,

```
E^amb ≤ k ρ M^{k−1} L_T      and      E^proj = E^red ≤ (k−1) ρ M^{k−1} L_T,
```

`L_T` being the product of the leaf norms. The reduction from `k` to `k−1` is the removal of
the root closure residual by the final projection.

**The optimality of `k−1` is open and is not claimed.** No claim of originality is made.

---

## Two reviewers are wanted, with different briefs

### Reviewer A — numerical analysis / error propagation

Please concentrate on Sections 3–10 and Appendix A.1–A.3, A.6–A.7:

* the norms, the induction, the exponents, and the constants;
* whether the base cases and degenerate cases (§3.2) are complete;
* whether the ordering theorem's exchange argument really gives a **global** minimum
  (Lemmas A.4–A.5);
* whether the pathwise majorant (Def. 10.1, Cor. 10.2) is correctly separated from the
  bound it majorises;
* whether the representation-error proposition (Prop. 14.1) uses only declared hypotheses
  — this is the correction C-5 in the known-defect record, and a second opinion on it is
  specifically wanted;
* whether the numerical sections are correctly labelled as evidence rather than proof.

### Reviewer B — multilinear algebra / operads / tensor methods

Please concentrate on Sections 3–5, 11, and the relation to the literature:

* the type system and whether the composition is correctly set up;
* the exact local decomposition (Thm. 5.1) — is the `2^a`-term expansion right, and is the
  identification of the empty-subset remainder with the closure residual correct?
* signed combinations and the associator coefficient (Cor. 11.1);
* **whether any of this follows from a theorem you already know**, in any language. This is
  the question the author cannot answer for himself.

---

## Please answer these questions explicitly

A free-form opinion is much less useful than answers to these.

```text
1.  Is the main theorem correct as stated?
2.  Is any hypothesis missing?
3.  Does the proof cover every case, including the degenerate ones in §3.2?
4.  Is there a prior result that implies this one under equivalent hypotheses?
    If so, which, and does it imply the k−1 coefficient or only the k one?
5.  Which statements should be weakened, and to what?
6.  Which parts are standard and should be cited rather than proved?
7.  Is the separation between proved bounds and numerical evidence maintained
    throughout?
8.  Would you recommend posting this as a preprint in its current form?
    If not, what is the minimum that must change first?
```

Question 4 is the most valuable one. A pointer to an antecedent is worth more than an
approval.

---

## What a negative review is worth here

A review that finds an error, a missing hypothesis, or an antecedent is a **success** for
this process, not a failure. Specifically:

* an error found now costs a revision; an error found after publication costs a retraction;
* an antecedent found now repositions the contribution as a specialisation, a new proof, or
  a new application — all of which are publishable;
* a missing hypothesis found now is added; found later it invalidates a theorem.

Please do not soften a finding out of politeness.

---

## What will be done with the reply

Archived, in full, together with:

* the version of the manuscript reviewed, by checksum;
* the author's response to each numbered point;
* the change made, or the reason none was made;
* the before and after versions.

The reviewer's name will not be published without permission. If the review is substantial
the author would like to acknowledge it, and will ask separately.

---

## What is explicitly not being asked

* Not an endorsement, and not a recommendation letter.
* Not an opinion on whether the topic is interesting.
* Not a verdict on originality on its own — that needs the structured comparison in
  `ORIGINALITY_TABLE_TO_COMPLETE.md`, though a pointer to any antecedent is exactly what is
  wanted for question 4.
* Not a review of the software. The computational side is separate and is documented in
  `papers/04_software_and_reproducibility.pdf`.

---

## Time expected

The main theorem and its proof are about 6 pages (§9 and Appendix A.3). A reviewer who reads
only those and answers questions 1–4 would already be providing the essential service.
