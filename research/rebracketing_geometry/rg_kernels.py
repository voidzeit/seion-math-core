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
             iters: int = 40, seed: int = 0) -> torch.Tensor:
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
    generator = torch.Generator(device=device).manual_seed(seed)

    vectors = []
    for _ in range(3):
        block = torch.randn(count, restarts, dim, dtype=DTYPE, device=device,
                            generator=generator)
        vectors.append(block / block.norm(dim=2, keepdim=True).clamp_min(1e-12))

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

    values = torch.einsum("noacd,nra,nrc,nrd->nro", frozen, *vectors)
    if post is not None:
        values = torch.einsum("nqo,nro->nrq", post, values)
    return values.norm(dim=2).max(dim=1).values
