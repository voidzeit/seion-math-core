# V3 run budget

Generated: 2026-07-29T18:11:55.942062+00:00
Source commit: `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`

## Declared counts

| Block | Scientific instances |
|---|---:|
| A | 4,185 |
| B | 2,880 |
| C | 3,456 |
| D | 4,320 |
| E | 96 |
| F | 24 |
| G | 28 |
| H | 480 |
| I | 24 |
| J | 8,400 |

Full core (A--I): **15,493** instances.
Extended performance (J): **8,400** instances.
Exact enumerator: **81,445** ordered shapes.
Nested requested executions: **558,725**.

## Calibration

```json
{
  "cpu_evaluations_per_second": 908.7187473847607,
  "cpu_rotation_tree_evaluations": 200,
  "cpu_seconds": 0.2200901000178419,
  "gpu_calibration": "4096x32 float64 tanh-matmul",
  "gpu_name": "NVIDIA RTX PRO 5000 Blackwell Generation Laptop GPU",
  "gpu_seconds": 0.0019857999868690968,
  "gpu_steps": 50,
  "gpu_steps_per_second": 25178.769428250573
}
```

## Resource gate

Triggered: **True**.
A naive per-instance layout would create about **402,818 files** and **12.3 GiB** at 32 KiB/file.
The optimistic single-device optimizer lower estimate is **21.1 h**.

All scientific axes remain registered.  The full core evaluates every base mathematical instance with rigorous upper bounds and explicit lower constructions.  The complete seed/restart adversarial grid is retained, unmodified, as a resumable extended workload.  This scheduling resolution does not permit an optimality claim.

Per-run artifacts are packaged by block; every master-index row retains its own configuration, tree, mathematical-object, and input hashes.
