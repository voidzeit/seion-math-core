# Literature / leaderboard snapshot

**Status: not taken in this campaign.** Gate 13 (this campaign) executes
only 13.0-13.2 (freeze, router activation, reasoner vectorization) — no
external benchmark comparison or SOTA claim is made, so a frozen literature
snapshot is not yet required (mission brief §11 requirement 1 applies to
Gate 13.10, not to this campaign's scope).

Before Gate 13.10 (SOTA comparison) executes in a future campaign, this
file must be replaced with a dated snapshot of:

- FB15K-237 and WN18RR leaderboard entries for directly comparable
  protocols (filtered MRR/Hits@K, transductive, no extra training data).
- At least three strong external baselines re-run in this repo's own
  evaluator (mission brief §11 requirement 3) rather than citing published
  numbers from a different evaluation harness.
- The exact date the snapshot was taken, since leaderboards move.

Leaving this as an open placeholder rather than a filled-in-looking table
is deliberate: filling it now, before 13.10 is in scope, would risk the
exact "documentation substituting for execution" failure mode this
project's own methodology is built to catch.
