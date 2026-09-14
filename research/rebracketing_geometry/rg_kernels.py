"""Restart-batched operator-norm kernel for the rebracketing searches.

`m39_gpu_kernels.batched_op_norm` batches over configurations but loops over
restarts **sequentially**, so a call costs `restarts * iters * 3` kernel
launches regardless of how little work each one does. At these tensor sizes
that loop, not the arithmetic, is the entire cost: a quality-6 admissibility
audit is ~260k launch groups and takes minutes, which in practice caps how
strongly a reported configuration can be re-checked.

This folds restarts into the batch too, as a second axis carried through the
einsums, so the launch count drops by a factor of `restarts` and a much
stronger audit becomes affordable. The tensor itself is NOT replicated across
restarts -- only the slot vectors are -- so memory grows with
`configurations * restarts * D`, not `* D^4`.

Semantics are identical to the M39 kernel: alternating maximization over the
three slots, each sweep replacing one slot by the leading right singular vector
of the matrix formed from the other two, reported as the best over restarts.
The M39 kernel is deliberately left untouched; it is what the M39 results were
produced with.

`contract3` and `coordinate_projectors` are re-implemented here rather than
imported, so that everything under research/rebracketing_geometry/ runs without
the M39 scripts present. The M40-M42 closure has to be reproducible on its own.

THREE TIME SCALES, THREE DIFFERENT PROBLEMS
-------------------------------------------
Estimating this norm inside a search needs three separate mechanisms, and
collapsing them is how the campaign got into trouble:

  every step     warm continuation + a cold fraction. Warm tracks the maximizer
                 as the law moves; the cold fraction detects branch switching.
  every K steps  a full cold solve, to stop drift accumulating across a long
                 run of purely local refinements.
  final          converged grading, at high restarts, on the reported
                 configuration only.

The first two make the SEARCH efficient and are `ROBUSTIFIED, NOT CERTIFIED`:
measured on this repository, warm-only underestimates by 24% after an abrupt
change of dominant maximizer, and warm+cold still by 2.6%. An underestimate is
never harmless here -- every caller DIVIDES by this value to enforce
admissibility, so it silently admits an inadmissible law and inflates its score.
Only the third mechanism may set a number that leaves the harness.
"""

from __future__ import annotations

import torch

DTYPE = torch.float64
EIGH_CHUNK = 16384

_SPECS = [("noacd,nrc,nrd->nroa", (1, 2)),
          ("noacd,nra,nrd->nroc", (0, 2)),
          ("noacd,nra,nrc->nrod", (0, 1))]


def _top_right_singular(mat: torch.Tensor) -> torch.Tensor:
    """Leading right singular vector of each (out, slot) matrix in a stack.

    Via the leading eigenvector of `M^T M`: the alternating maximization needs
    only that vector, and a full SVD computes an entire decomposition to throw
    almost all of it away. Chunked to stay inside cuSOLVER's batched limits.
    """
    gram = torch.einsum("bij,bik->bjk", mat, mat)
    gram = 0.5 * (gram + gram.transpose(1, 2))          # exact symmetry
    gram = torch.nan_to_num(gram)
    if gram.shape[0] <= EIGH_CHUNK:
        return torch.linalg.eigh(gram)[1][:, :, -1]
    pieces = [torch.linalg.eigh(part)[1][:, :, -1]
              for part in gram.split(EIGH_CHUNK, dim=0)]
    return torch.cat(pieces, dim=0)


def contract3(tensor: torch.Tensor, a: torch.Tensor, b: torch.Tensor,
              c: torch.Tensor) -> torch.Tensor:
    """Batched mu(a, b, c) for tensor[batch, out, slot1, slot2, slot3]."""
    return torch.einsum("noacd,na,nc,nd->no", tensor, a, b, c)


def coordinate_projectors(ranks: torch.Tensor, dim: int,
                          device) -> torch.Tensor:
    """(N, D, D) diagonal orthogonal projectors from a per-element rank vector.

    Ran(P) is the FIRST `rank` coordinates -- the convention every witness in
    this directory is expressed in.
    """
    index = torch.arange(dim, device=device).view(1, dim)
    mask = (index < ranks.view(-1, 1)).to(DTYPE)
    return torch.diag_embed(mask)


def op_norms(tensor: torch.Tensor, *, post=None, restarts: int = 8,
             iters: int = 40, seed: int = 0, warm=None,
             return_vectors: bool = False, cold_fraction: float = 0.25):
    """Per-configuration operator norm, restarts carried as a batch axis.

    `post`, when given, is a per-configuration (N, D, D) matrix applied to the
    output -- used to measure the closure defect `||(I-P) mu(...)||`.

    Restarts are not a quality knob to be economized: a single start can stall
    on a saddle and UNDERESTIMATE the norm, and every caller here DIVIDES by
    this value to enforce admissibility, so an underestimate silently pushes a
    law outside the admissible class.
    """
    count, dim = tensor.shape[0], tensor.shape[1]
    device = tensor.device

    if warm is not None:
        # Warm start from the previous step's maximizers. These are DIRECTIONS,
        # not graph nodes, so they are safe to carry across steps -- unlike the
        # scale factors themselves, which must be recomputed every step because
        # a graph cannot be cached. Under a slowly moving law the maximizer
        # moves slowly too, so a handful of iterations suffices.
        #
        # But local refinement only tracks the maximizer it started on. If the
        # DOMINANT one changes -- branch switching, near-degenerate maximizers,
        # an abrupt move of the tensor -- a warm start happily follows the one
        # that stopped being dominant and silently UNDERestimates the norm,
        # which is exactly the failure this whole diagnosis was about. So a
        # fraction of the restarts is always re-drawn cold, and since the
        # reported value is the max over restarts, a cold one that finds a
        # better maximizer overrides every stale warm one.
        vectors = [v.detach().clone() for v in warm]
        cold = max(1, int(restarts * cold_fraction))
        if cold and vectors[0].shape[1] >= cold:
            generator = torch.Generator(device=device).manual_seed(seed)
            for slot in range(3):
                block = torch.randn(count, cold, dim, dtype=DTYPE,
                                    device=device, generator=generator)
                block = block / block.norm(dim=2,
                                           keepdim=True).clamp_min(1e-12)
                vectors[slot] = torch.cat([vectors[slot][:, cold:, :], block],
                                          dim=1)
    else:
        generator = torch.Generator(device=device).manual_seed(seed)
        vectors = []
        for _ in range(3):
            block = torch.randn(count, restarts, dim, dtype=DTYPE,
                                device=device, generator=generator)
            vectors.append(block
                           / block.norm(dim=2, keepdim=True).clamp_min(1e-12))

    frozen = tensor.detach()
    with torch.no_grad():
        for _ in range(iters):
            for slot, (spec, others) in enumerate(_SPECS):
                mat = torch.einsum(spec, frozen, vectors[others[0]],
                                   vectors[others[1]])
                if post is not None:
                    mat = torch.einsum("nqo,nroa->nrqa", post, mat)
                shape = mat.shape
                flat = mat.reshape(shape[0] * shape[1], shape[2], shape[3])
                vectors[slot] = _top_right_singular(flat).reshape(
                    count, restarts, dim)

    # The maximizing directions are found under no_grad and then held FIXED,
    # but the returned value is contracted against the LIVE tensor. That is the
    # envelope theorem: d/dt ||mu_t||_op = d/dt <mu_t, v*> at fixed maximizer.
    # Contracting `frozen` here instead would return a number detached from the
    # graph, and any caller that DIVIDES by this norm would then be optimizing a
    # surrogate with the normalization frozen -- whose ascent direction is not
    # the true one wherever the constraint is active.
    values = torch.einsum("noacd,nra,nrc,nrd->nro", tensor, *vectors)
    if post is not None:
        values = torch.einsum("nqo,nro->nrq", post, values)
    best = values.norm(dim=2)
    index = best.detach().argmax(dim=1)
    norms = best.gather(1, index.view(-1, 1)).squeeze(1)
    return (norms, vectors) if return_vectors else norms
