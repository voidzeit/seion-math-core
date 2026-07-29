# Architecture

`src/seion_core/algebra` contains typed laws and identity evaluators. `kernels` adds exact finite weighted models. `geometry`, `variational`, and `projectors` implement declared derived objects. `multiscale`, `operators`, and `cohomology` remain finite/truncated modules. `certification` owns run manifests and artifact hashes. The CLI and PowerShell scripts orchestrate execution without hiding failures.

The evidence path is:

```text
config -> run directory -> final_metrics.json -> generated table/figure -> paper location
```

