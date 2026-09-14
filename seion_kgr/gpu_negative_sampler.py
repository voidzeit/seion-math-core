"""Device-resident filtered negative sampling.

``data.sample_negatives`` walks the batch in Python -- one dict lookup and one
NumPy rejection loop per row -- so a step costs O(batch) host work and the GPU
idles. At batch 4096 that dominates wall clock and pins a CPU core while the
accelerator sits at partial utilisation.

This sampler does the same job with no per-row Python. The filter tables are
flattened once into a CSR-style pair of device tensors plus a dense key index;
each call then draws an oversampled candidate block, tests membership with a
batched ``searchsorted``, and compacts the first ``neg_k`` survivors per row
with a cumulative-sum rank. Everything after construction stays on the device.

Semantics match the reference sampler: candidates are uniform over entities not
listed in the query's known-positive set. For a training triple the gold tail is
itself a known positive, so it is excluded by the same mechanism rather than as
a special case.

This is *not* bit-exact with ``sample_negatives`` -- a different RNG consumption
order cannot be, and no attempt is made to fake it. It is distributionally
equivalent, which is what a negative sampler has to be; the equivalence is
pinned by ``tests/kgr/test_gpu_negative_sampler.py``.
"""

from __future__ import annotations

import numpy as np
import torch

from .data import KnowledgeGraph


class GpuNegativeSampler:
    """Flattened filter tables plus a vectorized rejection sampler."""

    def __init__(self, kg: KnowledgeGraph, device: torch.device, *, oversample: int = 4) -> None:
        if oversample < 2:
            raise ValueError("oversample must be at least 2")
        self.device = device
        self.num_entities = int(kg.num_entities)
        self.num_relations_total = int(kg.num_relations_total)
        self.oversample = int(oversample)
        # Sentinel sorts above every real id, so padded rows stay sorted and
        # searchsorted stays valid without a separate mask.
        self.sentinel = self.num_entities

        keys, values, offsets = [], [], [0]
        for (h, r), tails in kg.tails_of_hr.items():
            keys.append(int(h) * self.num_relations_total + int(r))
            values.append(np.asarray(tails, dtype=np.int64))
            offsets.append(offsets[-1] + len(tails))

        table_size = self.num_entities * self.num_relations_total
        key_index = np.full(table_size, -1, dtype=np.int64)
        if keys:
            key_index[np.asarray(keys, dtype=np.int64)] = np.arange(len(keys), dtype=np.int64)
            flat = np.concatenate(values)
        else:
            flat = np.zeros(0, dtype=np.int64)

        self.key_index = torch.from_numpy(key_index).to(device)
        self.values = torch.from_numpy(flat).to(device)
        self.offsets = torch.from_numpy(np.asarray(offsets, dtype=np.int64)).to(device)

    def _padded_forbidden(self, h: torch.Tensor, r: torch.Tensor) -> torch.Tensor:
        idx = self.key_index[h * self.num_relations_total + r]
        present = idx >= 0
        safe = idx.clamp(min=0)
        starts = self.offsets[safe]
        lengths = torch.where(present, self.offsets[safe + 1] - starts, torch.zeros_like(starts))
        max_len = int(lengths.max().item()) if lengths.numel() else 0
        if max_len == 0:
            return torch.full((h.numel(), 1), self.sentinel, device=self.device, dtype=torch.long)
        ar = torch.arange(max_len, device=self.device)
        positions = (starts.unsqueeze(1) + ar).clamp(max=max(self.values.numel() - 1, 0))
        gathered = self.values[positions] if self.values.numel() else torch.zeros_like(positions)
        return torch.where(ar < lengths.unsqueeze(1), gathered, self.sentinel)

    def sample(
        self,
        h: torch.Tensor,
        r: torch.Tensor,
        neg_k: int,
        generator: torch.Generator | None = None,
    ) -> torch.Tensor:
        """Return ``[B, neg_k]`` filtered negatives for the queries ``(h, r)``."""
        if neg_k <= 0:
            raise ValueError("neg_k must be positive")
        if h.shape != r.shape or h.ndim != 1:
            raise ValueError("h and r must be matching 1-D tensors")

        h = h.to(self.device, torch.long)
        r = r.to(self.device, torch.long)
        batch = h.numel()
        padded = self._padded_forbidden(h, r)
        width = padded.shape[1]

        out = torch.full((batch, neg_k), -1, device=self.device, dtype=torch.long)
        remaining = torch.full((batch,), neg_k, device=self.device, dtype=torch.long)
        draw = max(neg_k * self.oversample, 16)

        # A couple of rounds is plenty: forbidden sets are tiny next to the
        # entity space, so the first oversampled block almost always suffices.
        for _ in range(4):
            candidates = torch.randint(
                0, self.num_entities, (batch, draw), device=self.device,
                dtype=torch.long, generator=generator,
            )
            hit = padded.gather(1, torch.searchsorted(padded, candidates).clamp(max=width - 1))
            valid = hit != candidates
            rank = valid.cumsum(dim=1) - 1
            already = neg_k - remaining
            keep = valid & (rank < remaining.unsqueeze(1))
            if keep.any():
                rows = torch.arange(batch, device=self.device).unsqueeze(1).expand_as(candidates)
                out[rows[keep], (already.unsqueeze(1) + rank)[keep]] = candidates[keep]
                remaining = remaining - keep.sum(dim=1)
            if not bool((remaining > 0).any()):
                break

        # Degenerate rows (a query whose forbidden set covers nearly everything)
        # fall back to unfiltered draws, exactly as the reference sampler does
        # once it exhausts its retry budget.
        if bool((out < 0).any()):
            fallback = torch.randint(
                0, self.num_entities, out.shape, device=self.device,
                dtype=torch.long, generator=generator,
            )
            out = torch.where(out < 0, fallback, out)
        return out
