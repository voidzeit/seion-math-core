"""Hardware-optimized batched primitives for the M39 associator searches.

Three optimizations over the first GPU version, all measured on this machine
(RTX PRO 5000 Blackwell, 24 GB, torch float64):

1. TOP SINGULAR VECTOR VIA eigh ON THE GRAM MATRIX.
   The alternating maximization only needs the leading right singular vector of
   a (D_out x D_slot) matrix, which is the leading eigenvector of M^T M. Full
   SVD computes an entire decomposition and throws almost all of it away.
   Measured at N = 16384, D = 4:  full SVD 120.7 ms, eigh(Gram) 10.1 ms --
   a 12x speedup at a maximum directional discrepancy of 6.9e-14, i.e. exact.
   Power iteration was also tried and REJECTED: 9-39x faster still, but with a
   maximum error of 0.85 even at 80 iterations, because near-degenerate leading
   singular values make it converge to the wrong direction on part of the batch.
   Speed that returns a wrong extremizer is not usable in a supremum search.

2. CHUNKING. cusolver's batched symmetric eigensolver fails above roughly
   30k matrices per call, and fragments earlier under memory pressure. Calls
   are chunked at 16384, which benchmarked at 10 ms warm.

3. PER-ELEMENT PROJECTORS AND ETA. The sweep runs over (rank, eta) cells that
   share a dimension, so instead of one launch per cell they are folded into
   the batch axis: the projector becomes (N, D, D) and eta becomes (N,). One
   set of kernel launches then covers every (rank, eta) combination at a given
   D, which is what actually saturates a GPU whose tensors are this small.

float64 is kept throughout. On this card it is only ~1.9x slower than float32
for these shapes, which does not justify introducing a precision question into
a search whose whole purpose is to certify a bound.
"""

from __future__ import annotations

import torch

DTYPE = torch.float64
EIGH_CHUNK = 16384


def top_right_singular(mat: torch.Tensor) -> torch.Tensor:
    """Leading right singular vector of each (out, slot) matrix in a batch.

    Computed as the leading eigenvector of M^T M. Chunked to stay inside
    cusolver's batched-eigensolver limits.
    """
    gram = torch.einsum("nij,nik->njk", mat, mat)
    gram = 0.5 * (gram + gram.transpose(1, 2))          # enforce exact symmetry
    gram = torch.nan_to_num(gram)
    if gram.shape[0] <= EIGH_CHUNK:
        return torch.linalg.eigh(gram)[1][:, :, -1]
    pieces = [torch.linalg.eigh(part)[1][:, :, -1]
              for part in gram.split(EIGH_CHUNK, dim=0)]
    return torch.cat(pieces, dim=0)


_SPECS = [("noacd,nc,nd->noa", (1, 2)),
          ("noacd,na,nd->noc", (0, 2)),
          ("noacd,na,nc->nod", (0, 1))]


def batched_op_norm(tensor, *, post=None, restrict=None, iters=20, restarts=3,
                    seed=0):
    """Per-element operator norm of a batch of ternary laws.

    `post` and `restrict`, when given, are per-element (N, D, D). Returns the
    norms and the maximizing vectors; the caller applies the envelope theorem
    by treating the vectors as constants, since differentiating through the
    maximization produces non-finite values within a few optimizer steps.

    Restarts matter for correctness, not just quality: a single start
    UNDERESTIMATES the norm, and `make_feasible` divides by it, so an
    underestimate pushes the law outside the admissible class entirely.
    """
    batch, dim = tensor.shape[0], tensor.shape[1]
    device = tensor.device
    generator = torch.Generator(device=device).manual_seed(seed)

    def unit():
        v = torch.randn(batch, dim, dtype=DTYPE, device=device, generator=generator)
        if restrict is not None:
            v = torch.einsum("nij,nj->ni", restrict, v)
        return v / v.norm(dim=1, keepdim=True).clamp_min(1e-12)

    best_vectors, best_norm = None, None
    with torch.no_grad():
        frozen = tensor.detach()
        for _ in range(restarts):
            vectors = [unit() for _ in range(3)]
            for _ in range(iters):
                for slot, (spec, others) in enumerate(_SPECS):
                    mat = torch.einsum(spec, frozen,
                                       vectors[others[0]], vectors[others[1]])
                    if post is not None:
                        mat = torch.einsum("nqo,noa->nqa", post, mat)
                    if restrict is not None:
                        mat = torch.einsum("noa,naj->noj", mat, restrict)
                    candidate = top_right_singular(mat)
                    if restrict is not None:
                        candidate = torch.einsum("nij,nj->ni", restrict, candidate)
                        norms = candidate.norm(dim=1, keepdim=True)
                        candidate = torch.where(norms > 1e-12,
                                                candidate / norms.clamp_min(1e-12),
                                                vectors[slot])
                    vectors[slot] = candidate
            value = torch.einsum("noacd,na,nc,nd->no", frozen, *vectors)
            if post is not None:
                value = torch.einsum("nqo,no->nq", post, value)
            norm = value.norm(dim=1)
            if best_norm is None:
                best_norm, best_vectors = norm, vectors
            else:
                better = norm > best_norm
                best_norm = torch.where(better, norm, best_norm)
                best_vectors = [torch.where(better.unsqueeze(1), new, old)
                                for new, old in zip(vectors, best_vectors)]

    value = torch.einsum("noacd,na,nc,nd->no", tensor, *best_vectors)
    if post is not None:
        value = torch.einsum("nqo,no->nq", post, value)
    return value.norm(dim=1), best_vectors


def make_feasible(raw, projector, normal, eta, restrict=None, seed=0, quality=1):
    """Batched projection onto the admissible class.

    Unit operator norm, then the normal output component shrunk until the
    projected closure defect satisfies rho_v^proj <= eta elementwise. `eta` is
    per-element (N,), so one call covers a whole sweep of closure budgets.
    """
    iters, restarts = 20 * quality, 3 * quality
    norms, _ = batched_op_norm(raw, seed=seed, iters=iters, restarts=restarts)
    tensor = raw / norms.clamp_min(1e-12).view(-1, 1, 1, 1, 1)
    closure, _ = batched_op_norm(tensor, post=normal, restrict=restrict,
                                 seed=seed + 1, iters=iters, restarts=restarts)
    scale = torch.where(closure > eta, eta / closure.clamp_min(1e-12),
                        torch.ones_like(closure)).view(-1, 1, 1, 1, 1)
    tang = torch.einsum("nqo,noacd->nqacd", projector, tensor)
    norm_part = torch.einsum("nqo,noacd->nqacd", normal, tensor)
    return tang + scale * norm_part


def contract3(tensor, a, b, c):
    return torch.einsum("noacd,na,nc,nd->no", tensor, a, b, c)


def coordinate_projectors(ranks, dim, device):
    """(N, D, D) diagonal projectors from a per-element rank vector."""
    index = torch.arange(dim, device=device).view(1, dim)
    mask = (index < ranks.view(-1, 1)).to(DTYPE)
    return torch.diag_embed(mask)
