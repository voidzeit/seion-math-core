# Phase 4 S1 broad-screening resource report

- Hardware: NVIDIA RTX PRO 5000 Blackwell Generation Laptop GPU, CUDA 12.8, torch 2.12.0.dev20260408+cu128, 24 logical CPU cores
- Total cells: 320
- Completed: 320
- Failed: 0
- Total sweep wall time: 6316.5s

## Wall time by device x n (mean seconds/cell)

- device=cpu, n=12: count=40, mean=9.444s
- device=cpu, n=24: count=40, mean=9.310s
- device=cpu, n=48: count=40, mean=9.831s
- device=cpu, n=96: count=40, mean=7.904s
- device=cuda, n=12: count=40, mean=30.637s
- device=cuda, n=24: count=40, mean=30.804s
- device=cuda, n=48: count=40, mean=34.501s
- device=cuda, n=96: count=40, mean=25.090s

## GPU/CPU crossover within tested range (n up to 96)

No crossover found up to n=96: CPU remained faster than or comparable to GPU at every tested scale in this run. This extends, not just repeats, the Phase 3 pilot's finding (which only tested up to n=24) -- the pilot's conclusion holds at 4x the ambient dimension tested here.