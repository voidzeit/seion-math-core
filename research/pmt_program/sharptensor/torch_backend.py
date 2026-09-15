"""PyTorch backend (experimental, V1): certified MPO→MPS application with bond truncation.

The module runs the contractions and SVD truncations with ``torch`` on any device, records every local
truncation (residual, norms, slot operator norms) and returns a :class:`sharptensor.certificate.Run`
that :func:`sharptensor.certificate.certify` turns into a certificate.

Scope and status (APPLICATIONS_BOUNDARY §10, §14):

* V1 experimental: the certificate interprets the device computation under the exact-arithmetic
  model; floating-point error of the kernels (cuBLAS/cuSOLVER or CPU LAPACK) is **not** included.
* Validated on CPU only in this repository (GPU experimentation is paused under blocker B-0012).
* Gradients flow through ``torch.linalg.svd``; they are not part of any certificate.
"""

from __future__ import annotations

import math
import time

import torch

from .certificate import Leaf, Node, Run


class CertifiedMpoMpsApply(torch.nn.Module):
    """Apply an MPO to an MPS given as combined site tensors ``W_k`` (shape ``a × p × b``)."""

    def __init__(self, site_tensors, device: str = "cpu", dtype=torch.float64):
        super().__init__()
        self.W = torch.nn.ParameterList(
            [torch.nn.Parameter(torch.as_tensor(T, dtype=dtype, device=device)) for T in site_tensors])
        self.device_name = device
        self.last_run: Run | None = None

    def forward(self, ranks: dict | None = None):
        N = len(self.W)
        dev, dt = self.W[0].device, self.W[0].dtype
        S = torch.ones((1, 1), dtype=dt, device=dev)
        cores = []
        leaves = [Leaf("L0", 1.0)]
        nodes = []
        prev_norm = 1.0
        t0 = time.perf_counter()
        for k in range(1, N + 1):
            T = self.W[k - 1]
            a, p, b = T.shape
            leaves.append(Leaf(f"W{k}", float(torch.linalg.norm(T.detach()))))
            Mloc = torch.einsum("ra,aqb->rqb", S, T)
            r_prev = S.shape[0]
            Mmat = Mloc.reshape(r_prev * p, b)
            U, s, Vh = torch.linalg.svd(Mmat, full_matrices=False)
            name = f"L{k}"
            is_root = k == N
            keep = s.shape[0] if (is_root or ranks is None) else max(0, min(int(ranks.get(name, s.shape[0])), s.shape[0]))
            resid = float(torch.sqrt(torch.sum(s[keep:].detach() ** 2))) if keep < s.shape[0] else 0.0
            U, s_k, Vh = U[:, :keep], s[:keep], Vh[:keep, :]
            cores.append(U.reshape(r_prev, p, keep))
            S = s_k[:, None] * Vh
            k_op = [float(torch.linalg.matrix_norm(T.detach().reshape(a, p * b), ord=2)), None]
            nodes.append(Node(name, [f"L{k - 1}" if k > 1 else "L0", f"W{k}"], 1.0,
                              "analytic: contraction over one index, Cauchy–Schwarz", True,
                              0.0 if is_root else resid, float(torch.linalg.norm(s_k.detach())), is_root,
                              rank=keep, rank_full=int(s.shape[0]), K_op=k_op,
                              K_op_method=f"analytic: x ↦ x·mat(W) has norm ‖mat(W)‖_2 ({dev.type} SVD)",
                              K_op_rigorous=True))
            prev_norm = float(torch.linalg.norm(s_k.detach()))
        self.last_run = Run(leaves, nodes, f"L{N}", meta={"backend": "torch", "device": dev.type,
                                                          "seconds": time.perf_counter() - t0})
        return cores, S

    @staticmethod
    def dense(cores, S):
        Q = torch.ones((1, 1), dtype=S.dtype, device=S.device)
        for C in cores:
            Q = torch.einsum("pr,rqs->pqs", Q, C).reshape(-1, C.shape[2])
        return Q @ S
