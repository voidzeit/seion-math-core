# SRATM Sealed Teacher Closure — forensic report

Date: 2026-08-10. Repository: `C:\Documents\metamaths\seion-math-core`.
Campaign: `SRATM_SEALED_TEACHER_CLOSURE_V1`.

## Verdict

The campaign stopped at the resume gate with:

`RESUME_PROVENANCE_FAILURE`

The step-704 checkpoint is numerically and structurally intact, but its
continuation is not provenance-closed. Therefore the campaign did **not** claim
convergence, did **not** freeze a clean teacher, and did **not** execute fresh
spectral audit, compression, or clean G6.

The valid current output is:

`SEALED_TEACHER_NOT_READY — RESUME_PROVENANCE_FAILURE`

This is not a TEST-leakage failure and not a numerical-divergence failure.

## 1. Initial state and genealogy

### Historical lineage — non-canonical

- Trainer: `seion_kgr/train_spectral_mixture.py`.
- Checkpoint: historical `checkpoint_last.pt`.
- Historical metric: `MRR=0.6116475`.
- Status: `HISTORICAL_UNRECONCILED`.
- TEST usage: `UNKNOWN / NOT_ESTABLISHED`.
- It was not used as a teacher or resume source in this campaign.

### Sealed lineage

- Trainer: `seion_kgr/train_sratm_sealed.py`.
- Run: `runs/SRATM_FB15K237_SEALED_FROM_ZERO_D256_B512_23GB_2026-08-10`.
- Initialization: random from zero, followed by sealed checkpoint resume.
- Loader: `TRAIN_PLUS_VALID_ONLY`.
- Filter policy: `TRAIN_PLUS_VALID_ONLY`.
- Dataset counts: 14,541 entities, 474 total reciprocal relations, 35,070
  full-VALID queries, 17,535 base VALID rows.
- TRAIN SHA256:
  `6e4c2782169af21e9743f3b1d200886f5d595bf6bc504ec1351720949c5cdfae`.
- VALID SHA256:
  `cf6309010852f6a8d47a45df830a426415d1ee6f7a3970a8376ff1fb81db4a5c`.

## 2. Step-704 result actually established

The full VALID audit used the sealed evaluator over all 35,070 queries and all
14,541 entities, with TRAIN+VALID known-positive filters.

| metric | combined | head | tail |
|---|---:|---:|---:|
| MRR | 0.3273196220 | 0.2340104431 | 0.4206288457 |
| H@1 | 0.2674365640 | 0.1773595661 | 0.3575135469 |
| H@3 | 0.3516110778 | 0.2540633082 | 0.4491588175 |
| H@10 | 0.4477331042 | 0.3474194407 | 0.5480467675 |
| mean rank | 2214.8643 | 2430.2246 | 1999.5039 |

Head/tail MRR gap:

`tail - head = 0.1866184026`.

This is a diagnostic observation only. No trajectory exists yet to establish
whether the gap closes with training.

Checkpoint identities:

- `checkpoint_last.pt`: step 704, epoch 3,
  SHA256 `7afd916f7171587cc74654005353734c9fcfc4f381ef720ef7464ca7d6154306`.
- `checkpoint_best.pt`: step 512, epoch 3,
  SHA256 `fe4a426219acc60608a91c4efc701b809eeff8bb517a2ce113da3330ca82ed77`.
- Step 704 remains `CLEAN_INTERMEDIATE`; neither checkpoint is a frozen
  scientific teacher.

## 3. Resume provenance audit

The checkpoint contains every required restoration category:

- model state: present and finite;
- EMA teacher state: present and finite;
- AdamW optimizer state: present;
- scheduler: `NOT_CONFIGURED_IN_RUNNER`;
- RNG: Python, NumPy, Torch, CUDA, and generator snapshots present;
- epoch and step: `epoch=3`, `step=704`;
- sealed protocol: embedded in the checkpoint.

The gate nevertheless stopped because:

1. The prior run manifest records `git_head=cf663bc6…`, while the current
   checkout is `77f2dfe…`.
2. The recorded original commit does not contain
   `seion_kgr/train_sratm_sealed.py`; the current trainer source is therefore
   not recoverable from the recorded git identity.
3. `config.json` was overwritten with `max_steps=256`, while the checkpoint's
   embedded sealed protocol says `max_steps=1024`.
4. The initial provenance file did not capture the pre-resume checkpoint hash.

These are genealogy/configuration conflicts. The gate did not infer that the
current code is equivalent and did not silently select 1024 or 5120 steps.

Evidence: `runs/SRATM_FB15K237_SEALED_FROM_ZERO_D256_B512_23GB_2026-08-10/resume_manifest.json`.

## 4. No-leakage evidence

The executed step-704 audit and the resume gate report:

- TEST opened: `false`;
- TEST read: `false`;
- TEST hashed: `false`;
- forbidden TEST accesses: `0`;
- runtime accesses observed: TRAIN, VALID, and sealed-run checkpoints only;
- vocabulary provenance: TRAIN+VALID;
- filter provenance: TRAIN+VALID;
- reciprocal policy: reciprocal closure from TRAIN, with VALID evaluation under
  the sealed loader.

This is observed runtime evidence, not a universal proof about every unused
loader in the repository.

## 5. Mechanisms audited

The sealed training mechanism is an SRATM relation-adaptive tensor mixture:

- entity/relation dimension `D=256`;
- 8 experts, 2 active experts per relation;
- expert rank 64 and core basis 4;
- batch size 512;
- candidate block 2048;
- hard-negative `K=128`;
- AdamW, learning rate `1e-3`, weight decay `1e-6`;
- InfoNCE weight 1.0, listwise weight 0.25, margin weight 1.0;
- EMA momentum `0.999`;
- relation-prediction weight `0.05`, basis penalty `1e-4`;
- 23 GiB configured VRAM cap.

The training loop combines full-entity hard-negative mining, InfoNCE,
listwise loss, weighted margin loss, basis decorrelation, relation prediction,
and EMA-teacher margin distillation. The runtime sentinel guards common
Python file-open routes and fails closed on TEST-like basenames.

The current runner has no scheduler and no separate full-VALID checkpoint
selection mechanism. Its lightweight in-training audits are not substitutes
for the requested full-VALID schedule.

## 6. Campaign phases not executed

Because the resume gate failed, none of the following artifacts may be
represented as current results:

- `sealed_checkpoint_registry.json`;
- `sealed_learning_curves.csv` or `.md`;
- predeclared full-VALID audits at 1024, 1536, …, 5120;
- convergence/plateau evidence;
- `SEALED_TEACHER_FREEZE_V1`;
- fresh global Tucker, primitive-mixture, or ComplEx spectra/projectors;
- clean compression V2;
- clean G6 against a compressed teacher.

The earlier step-704 audit is retained as evidence and is not deleted or
promoted retrospectively.

## 7. Governance and test status

The broader repository audit remains as recorded in
`.ai/AUDIT_PROFUNDA_2026-08-10.md`: structural governance is yellow; focused
math, governance/certificate/integration, and KGR suites passed in their
recorded executions; the monolithic pytest run was not counted as a pass after
being stopped for duration. Existing dirty worktree changes were preserved.

New governance evidence:

- `.ai/KNOWN_BLOCKERS.md`: blocker `B-0013`.
- `.ai/CURRENT_STATE.md`: resume gate postflight.
- `.ai/TASKS.md`: provenance reconciliation remains open.
- `seion_kgr/prepare_sealed_resume.py`: fail-closed manifest generator.
- `resume_manifest.json`: authoritative stop artifact.

## 8. Permitted and prohibited claims

Permitted:

- “The sealed step-704 checkpoint achieved MRR 0.3273196220 on full VALID
  under the observed TRAIN+VALID-only protocol.”
- “The observed step-704 head/tail MRR gap was 0.1866184026.”
- “The step-704 audit observed zero forbidden TEST accesses.”
- “The checkpoint contains finite model, EMA, optimizer, and RNG state.”
- “Resume provenance is not established because the recorded git/config
  identities conflict.”

Prohibited:

- calling step704 a converged or frozen teacher;
- claiming `SEALED_TEACHER_READY_FOR_SPECTRAL_AUDIT`;
- using `0.6116475` as a clean baseline or tuning target;
- claiming TEST generalization, SOTA, or final KGE quality;
- claiming head/tail gap closure;
- claiming fresh spectra, compression preservation, rank equality, CCR, or G6;
- claiming hardware speedup or changing architecture/hyperparameters to repair
  the provenance issue.

## 9. Answer to the scientific question

The present evidence answers only:

> Under the sealed protocol, a random-initialized SRATM reached an observed
> full-VALID MRR of `0.3273196220` by step 704, with tail MRR materially above
> head MRR, before the continuation was stopped by an unresolved provenance
> conflict.

It does **not** yet answer how good SRATM can become when trained entirely
within the sealed protocol. That question requires a provenance-reconciled
resume or a newly registered continuation campaign.

## Next gate

Reconcile the original trainer source/config identity without opening TEST.
Then create an immutable continuation manifest, explicitly register the
compatible audit schedule, resume from the unchanged step-704 checkpoint, and
only after convergence freeze the teacher before launching fresh spectra,
compression, and G6.
