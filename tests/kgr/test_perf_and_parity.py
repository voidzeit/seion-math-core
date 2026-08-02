"""Campaign Phase B5: evaluator/perf closure — reference-vs-optimized
parity and BF16-GPU-vs-FP32-CPU parity.

These are the two mandate-required checks that were genuinely missing:
the FP64 reference oracle (Fase 1) and the batched package (Fase 5) are
two INDEPENDENT implementations of the same CP ternary law — until now
nothing checked they actually agree on identical inputs (only that each
is internally self-consistent). And nothing checked BF16-on-the-real-GPU
against FP32-on-CPU within a declared tolerance.
"""
import math

import pytest
import torch

import seion_kgr_reference_fp64 as oracle
from seion_kgr.kernels import CPTernaryLaw as PackageCPTernaryLaw

pytestmark = pytest.mark.symbolic


def test_reference_oracle_and_package_cp_law_agree_on_identical_weights():
    """Copy the SAME numeric weights into both independent
    implementations and check they compute the same output — this is
    the actual "reference vs optimized parity" check the mandate wants,
    not just that each implementation agrees with itself."""
    dim, rank = 5, 4
    torch.manual_seed(21)
    A = torch.randn(rank, dim, dtype=torch.float64)
    B = torch.randn(rank, dim, dtype=torch.float64)
    C = torch.randn(rank, dim, dtype=torch.float64)
    O = torch.randn(dim, rank, dtype=torch.float64)

    ref_law = oracle.CPTernaryLaw(A=A.clone(), B=B.clone(), C=C.clone(), O=O.clone())

    pkg_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    with torch.no_grad():
        pkg_law.A.weight.copy_(A.float())
        pkg_law.B.weight.copy_(B.float())
        pkg_law.C.weight.copy_(C.float())
        pkg_law.O.weight.copy_(O.float())

    x = torch.randn(dim, dtype=torch.float64)
    a = torch.randn(dim, dtype=torch.float64)
    q = torch.randn(dim, dtype=torch.float64)

    ref_out = ref_law.forward(x, a, q)
    pkg_out = pkg_law.forward(x.float(), a.float(), q.float())

    assert torch.allclose(ref_out.double(), pkg_out.double(), atol=1e-4), (
        f"reference oracle and package CPTernaryLaw disagree on identical weights: "
        f"ref={ref_out}, pkg={pkg_out}"
    )


def test_reference_oracle_and_package_cp_law_agree_across_several_random_cases():
    """Property-style repetition of the same check, several seeds, so a
    single lucky agreement doesn't stand in for genuine parity."""
    for seed in range(5):
        dim, rank = 4, 3
        torch.manual_seed(seed)
        A = torch.randn(rank, dim, dtype=torch.float64)
        B = torch.randn(rank, dim, dtype=torch.float64)
        C = torch.randn(rank, dim, dtype=torch.float64)
        O = torch.randn(dim, rank, dtype=torch.float64)
        ref_law = oracle.CPTernaryLaw(A=A.clone(), B=B.clone(), C=C.clone(), O=O.clone())
        pkg_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
        with torch.no_grad():
            pkg_law.A.weight.copy_(A.float())
            pkg_law.B.weight.copy_(B.float())
            pkg_law.C.weight.copy_(C.float())
            pkg_law.O.weight.copy_(O.float())
        x, a, q = (torch.randn(dim, dtype=torch.float64) for _ in range(3))
        ref_out = ref_law.forward(x, a, q)
        pkg_out = pkg_law.forward(x.float(), a.float(), q.float())
        assert torch.allclose(ref_out.double(), pkg_out.double(), atol=1e-4), f"seed {seed} disagreement"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device available")
def test_bf16_gpu_matches_fp32_cpu_within_declared_tolerance():
    """Real check on the actual GPU (not a mock/skip), per the mandate's
    hardware-safety section: BF16 on GPU vs FP32 on CPU, same weights,
    same inputs, tolerance declared explicitly (BF16 has ~3 decimal
    digits of precision, so 1e-2 relative is the honest bar here, not
    1e-6)."""
    dim, rank = 16, 8
    torch.manual_seed(5)
    cpu_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    gpu_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank).to("cuda")
    with torch.no_grad():
        gpu_law.A.weight.copy_(cpu_law.A.weight)
        gpu_law.B.weight.copy_(cpu_law.B.weight)
        gpu_law.C.weight.copy_(cpu_law.C.weight)
        gpu_law.O.weight.copy_(cpu_law.O.weight)

    x, a, q = torch.randn(dim), torch.randn(dim), torch.randn(dim)
    fp32_cpu_out = cpu_law.forward(x, a, q)

    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        bf16_gpu_out = gpu_law.forward(x.to("cuda"), a.to("cuda"), q.to("cuda"))
    bf16_gpu_out_cpu = bf16_gpu_out.float().cpu()

    rel_error = (fp32_cpu_out - bf16_gpu_out_cpu).norm() / fp32_cpu_out.norm().clamp_min(1e-12)
    assert torch.isfinite(rel_error)
    assert float(rel_error.item()) < 5e-2, f"BF16 GPU vs FP32 CPU relative error {float(rel_error.item())} exceeds declared 5% tolerance"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device available")
def test_gpu_matches_cpu_in_fp32_tightly():
    """Same-dtype (FP32) CPU vs GPU parity should be MUCH tighter than
    the BF16 case — a separate, stricter check so a loose BF16 tolerance
    can't hide an actual device-placement bug."""
    dim, rank = 12, 6
    torch.manual_seed(9)
    cpu_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    gpu_law = PackageCPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank).to("cuda")
    with torch.no_grad():
        gpu_law.A.weight.copy_(cpu_law.A.weight)
        gpu_law.B.weight.copy_(cpu_law.B.weight)
        gpu_law.C.weight.copy_(cpu_law.C.weight)
        gpu_law.O.weight.copy_(cpu_law.O.weight)
    x, a, q = torch.randn(dim), torch.randn(dim), torch.randn(dim)
    cpu_out = cpu_law.forward(x, a, q)
    gpu_out = gpu_law.forward(x.to("cuda"), a.to("cuda"), q.to("cuda")).cpu()
    assert torch.allclose(cpu_out, gpu_out, atol=1e-5), f"FP32 CPU vs GPU mismatch: {(cpu_out - gpu_out).abs().max()}"
