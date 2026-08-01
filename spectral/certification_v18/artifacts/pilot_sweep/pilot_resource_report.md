# Pilot sweep resource report

- Hardware: NVIDIA RTX PRO 5000 Blackwell Generation Laptop GPU, CUDA 12.8, torch 2.12.0.dev20260408+cu128, 24 logical CPU cores
- Total cells: 96
- Completed: 96
- Failed: 0
- Total sweep wall time: 945.5s

## Wall time by device

- cpu: n=48, mean=4.944s, sum=237.3s
- cuda: n=48, mean=14.697s, sum=705.5s

## GPU vs CPU

GPU mean wall time 14.697s vs CPU mean 4.944s at this problem scale (n<=24) -- GPU is SLOWER (2.97x). Kernel-launch overhead dominates at this scale; matches the prior single-sample finding (see project memory: RTX PRO 5000, n=24, GPU 835ms vs CPU 19ms). This is a real scheduling input for Phase 4, not a bug: small cells should stay on CPU; only larger n/cp_rank cells should be routed to GPU.
