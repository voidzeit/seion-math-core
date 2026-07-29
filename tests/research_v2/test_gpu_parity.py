from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")


@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is not available")
def test_torch_cpu_gpu_einsum_parity() -> None:
    generator = np.random.default_rng(606)
    tensor = generator.normal(size=(5, 4, 4, 4)).astype(np.float64)
    vectors = [generator.normal(size=4).astype(np.float64) for _ in range(3)]
    cpu_tensor = torch.from_numpy(tensor)
    cpu_vectors = [torch.from_numpy(vector) for vector in vectors]
    gpu_tensor = cpu_tensor.cuda()
    gpu_vectors = [vector.cuda() for vector in cpu_vectors]
    cpu_value = torch.einsum("oabc,a,b,c->o", cpu_tensor, *cpu_vectors)
    gpu_value = torch.einsum("oabc,a,b,c->o", gpu_tensor, *gpu_vectors).cpu()
    np.testing.assert_allclose(cpu_value.numpy(), gpu_value.numpy(), rtol=1e-12, atol=1e-12)
