# Auditoría profunda de resultados y mecanismos — 2026-08-10

## 0. Dictamen ejecutivo

El repositorio es internamente fuerte como núcleo finito, suite de
verificación y archivo de evidencia, pero no está listo para una afirmación
global, publicación aprobada, certificación KGE final ni claim de aceleración
hardware. El estado correcto es:

| Dominio | Estado auditado | Qué sí queda establecido | Qué sigue abierto |
|---|---|---|---|
| Núcleo algebraico finito | Verde técnico / alcance finito | Definiciones, identidades exactas, reducción y tests | Límite continuo, universalidad, novedad |
| V2 reducción-preservación | Verificado en régimen declarado | 180 runs históricas, 100 instancias únicas, 60 bounds y 5 filas CPU/GPU | Novedad y metadata de autor |
| V3 árboles multilineales | Técnico pass, release fail-closed | 81,445 ocurrencias, 80,870 hashes matemáticos, 15,493 instancias deduplicadas | Sharpness fija, certificación global completa, matriz extendida |
| V4/V5 árboles y DAGs | Progreso matemático sustantivo | Constantes exactas en varias clases y certificados finitos | Clases same-law/gated restantes, novedad, revisión humana, formalización |
| Aplicación adaptive tensor network | Negativa/contextual | Certificados reproducibles y equivalencia de ejecución | Superioridad de allocator, runtime/memory a error igual |
| Spectral v18 legado | Fail-closed | Algunos bloques estructurales/certificados | Dynamic explanation, interscale, persistence, reproducibilidad |
| KGE/SRATM | Evidencia fuerte pero no final | Full VALID observado, G6A certificado, no TEST observado | G6B/G6C, selector histórico, TEST, hardware, B-0012 |

La conclusión más importante es que el repositorio contiene resultados reales,
pero de distinta naturaleza. No deben mezclarse:

1. `PROVED`/`PROVED_UNDER_ASSUMPTIONS`: resultados matemáticos con hipótesis
   explícitas.
2. `COMPUTER_ALGEBRA_VERIFIED`/`FINITE_DIMENSION_EXHAUSTIVE`: verificación
   determinista de un dominio finito.
3. `NUMERICALLY_TESTED`/`EMPIRICAL`/`OBSERVED`: hechos de runs concretos.
4. `DECLARED`/`OPEN`/`CONJECTURE`: agenda o frontera, no evidencia ejecutada.

El informe se basa en los registries, manifiestos y artefactos canónicos; no
convierte resultados históricos en resultados nuevos.

## 1. Alcance y estado de la auditoría

- Repositorio canónico: `C:\Documents\metamaths\seion-math-core`.
- Rama/HEAD al cierre del informe: `campaign/gate13-closeout` /
  `77f2dfeab466ed8f31193a2a3f20e8c1604a90a0`.
- El HEAD avanzó durante la sesión por trabajo del usuario desde `cf663bc`;
  no se reescribió ni se descartó ese cambio.
- Worktree dirty por archivos ya existentes y por el flujo de auditoría del
  usuario. El archivo de este informe es una adición de esta revisión.
- Inventario físico: 9,531 archivos y aproximadamente 17.33 GB; la mayor parte
  son checkpoints `.pt`. Hay 534 archivos Python, 472 YAML, 3,267 JSON,
  408 CSV, 233 PDF, 231 TEX y 26 Parquet.

Comandos ejecutados o comprobaciones directas:

- `python -m seion_core.cli.main governance context --task ...`: contexto
  compilado correctamente.
- `python -m seion_core.cli.main governance audit --json`: audit estructural
  `yellow`, sin archivos requeridos ausentes.
- `python -m seion_core.cli.main governance dedupe-runs`: 181 históricos,
  9 instancias científicas únicas, 8 grupos duplicados, 172 registros
  duplicados; 179 `COMPLETE` y 2 `FAILED_RUNTIME` históricas.
- `python -m compileall -q ...`: pass.
- `git diff --check`: pass.
- `scripts/verify_projected_graphs_v5_papers.ps1`: 3 PDFs renderizados y
  auditados.
- `tests/math_closure`: 67/67 pass en ejecución actual.
- `tests/governance tests/certificates tests/integration`: 58/58 pass en
  ejecución actual.
- Suite KGR focalizada sobre leakage, SRATM, G6, reconciliación, full-entity,
  SOTA y spectral mixture: 18/18 pass en ejecución actual.
- Escaneo de secretos del mecanismo canónico: `PASS`, cero hallazgos.
- Integridad de referencias de claims/teoremas: 180 rutas comprobadas, 0
  ausentes.
- Integridad de hashes V3: 497 archivos comprobados, 0 discrepancias.
- Integridad de manifests SRATM/G6/no-leakage/provenance: 4 manifests,
  44 entradas comprobadas, 0 discrepancias.

La suite monolítica `python -m pytest -q` y una ejecución redundante de
`tests/kgr` fueron iniciadas pero detenidas por duración para no competir con
un proceso SRATM del usuario. No se cuentan como pass. El resultado actual
que sí tiene autoridad es el de las suites focalizadas anteriores y los gates
históricos explícitamente registrados.

## 2. Arquitectura y mecanismos implementados

### 2.1 Núcleo `src/seion_core`

El núcleo contiene 171 módulos Python, aproximadamente 12,349 líneas, 621
funciones y 107 clases. Sus mecanismos son:

- **Álgebra tipada:** `NaryLaw`, `TypedNaryLaw`, `TernaryLaw`,
  `StructuralTensor`, leyes sparse/CP y composición parcial.
- **Defectos e identidades:** asociadores de cinco entradas, anchored y
  operádicos; conmutador, Jacobiator, Filippov, Akivis, simetrías y defectos
  cíclicos.
- **Geometría:** acciones izquierdas, curvatura inducida/constitutiva,
  métricas de Stiefel, ángulos principales y proyección tangente.
- **Proyectores:** baselines random/PCA/SVD/spectral, reducción/lifting de
  leyes, leakage, certificados y snapping espectral.
- **Cohomología y operadores:** complejos de cadenas, compatibilidad,
  operador inducido, Hodge discreto, truncación y Fourier del toro.
- **Kernels y multiescala:** espacios de medida, cuadratura, kernels
  discretos/integrales, convergencia, transporte, alineamiento y persistence.
- **Numerics:** normas, condicionamiento, precisión, muestreo y snapshots de
  reproducibilidad.
- **Gobernanza/certificación:** autoridad, claims lint, manifests, hashes,
  matriz canónica, reportes, contratos de evidencia, state machines, locks,
  deduplicación y audit.
- **Orquestación:** lifecycle `intake -> context -> plan -> change -> verify
  -> evidence -> postflight -> release`, sesiones, leases y roles.

### 2.2 V2: reducción y preservación

El mecanismo de V2 tiene dos evaluadores que deben coincidir:

- referencia por contracciones explícitas;
- backend acelerado por `einsum`/`tensordot`.

La reducción exacta usa una inclusión isométrica `Q`, invariancia de cada ley
y composición de árbol tipada. La capa aproximada propaga el residual de
closure mediante una recurrencia de árbol. El snapping spectral usa un gap
positivo y un bound conservador tipo Davis–Kahan. Los controles retirando
hipótesis son parte del diseño, no excepciones escondidas.

### 2.3 V3: árboles multilineales y evidencia

V3 añade:

- gramática de árboles ordered/typed y hashes canónicos;
- evaluación ambient, projected y reduced-coordinate;
- expansión exacta por subconjuntos de errores locales;
- certificados ambient/projected/path-sum/mixed-mask;
- orden óptimo de telescoping;
- norm bounds de Frobenius, rank-one y lower bounds;
- CP projection budgets, signed forests, associator/Jacobiator/Filippov;
- intervalos, SOS, extremizers, búsqueda adversarial y parity CPU/GPU;
- run schema, environment/hardware inventory, hashes y validación de
  artefactos.

### 2.4 V4/V5: fuente, DAG, sharpness y asignación

V4/V5 separan mecanismos que con frecuencia se confunden:

- aproximación de ley, closure e interacción son presupuestos distintos;
- source-aware DAG y source-polynomial preservan fuentes repetidas mediante
  multiíndices y truncación finita;
- signed certificates permiten cancelación explícita sin asumir identidad;
- norm enclosures validados son límites conservadores, no normas óptimas;
- el DAG bounded-domain certificate propaga `U`, `A` y `D` por orden topológico;
- la asignación rank-independent se resuelve por knapsack DP separable;
- la rank-aware es acoplada y sólo tiene optimización exhaustiva en casos
  pequeños;
- el path constant exacto cuenta fan-out, slots repetidos y multiplicidad de
  caminos;
- los witnesses de producto complejo prueban sharpness asintótica en clases
  declaradas, no para toda clase que se parezca informalmente.

### 2.5 KGR, TTN y SRATM

Los mecanismos de aplicación incluyen:

- carga de KG, mapeo de entidades/relaciones, reciprocal closure y filtros;
- scorers DistMult, ComplEx, CP y TuckER;
- path reasoner y versión batched con frontier CSR/top-k;
- structural kernel, geometry curriculum, attribution y module ablation;
- projectors Stiefel y closure audits;
- whitening exacto de candidatos, pseudoinversa support-safe, projectors
  espectrales, Ky-Fan ranks, water-filling, prefix-DP, Lagrangian allocation,
  ranking certificates y Grassmann diagnostics;
- SRATM con relation-adaptive spectral mixture, branch fusion y compressed
  candidate scoring;
- SOTA discovery separada con full-entity hard-negative mining por bloques,
  InfoNCE, margin loss, EMA teacher, entity queue, retriever unions, query
  gate, ensembles y distillation;
- frontera explícita entre Programa A (teacher mutable/selección VALID) y
  Programa B (student posterior a freeze, sin modificar teacher);
- auditoría de leakage estática, sentinel runtime, split provenance,
  reciprocal audit, duplicate audit y artifact DAG.

## 3. Resultados matemáticos extraídos

### 3.1 Registro base y V2

El registro base contiene 8 entradas:

- definiciones de ley n-aria y convenciones de asociador;
- identidad probada de curvatura estándar como diferencia de asociadores;
- descenso de operador compatible a cohomología bajo hipótesis explícitas;
- closure conocido verificado numéricamente;
- recovery de projector sólo empírico;
- límite continuo declarado como abierto;
- discontinuidad de snapping sin gap refutada por contraejemplo.

V2 registra 5 teoremas/proposiciones: reducción exacta, herencia de
identidades polinomiales, recurrencia de closure aproximado, estabilidad de
snapping con gap y descenso a cohomología. La política V2 declara
explícitamente que son resultados conocidos/auxiliares y no novedad.

Evidencia V2 histórica:

- 180 runs completas;
- 100 instancias científicas únicas;
- 60 filas de bounds sin violaciones;
- 5 filas CPU/GPU, error absoluto máximo `1.4210854715202004e-14`;
- 39 tests en el snapshot V2;
- la auditoría estricta continúa cerrada por novedad y metadata ORCID/email.

### 3.2 V3

El registro V3 contiene 14 entradas: una `PROVED` y 13
`PROVED_UNDER_ASSUMPTIONS`. Incluye la expansión exacta de errores locales,
el bound ambient `k`, el bound projected-root `k-1`, el orden óptimo de
telescoping, certificados mixed/path, asociador ternario y familias gated.

Resultados de ejecución histórica:

- 81,445 ocurrencias de árboles;
- 80,870 hashes matemáticos únicos;
- 15,493 instancias científicas deduplicadas;
- 1,530 máscaras de leakage;
- 18 figuras vectoriales y 16 tablas obligatorias más una suplementaria;
- 37 páginas PDF inspeccionadas;
- ningún violation del theorem bound registrado;
- parity CPU/GPU float64 pass.

La matriz extendida no está completa: 4/460,800 trayectorias del optimizador
y 0/8,400 celdas de performance. Por eso `release_gate_v3.json` marca
`FAIL_CLOSED_NOVELTY` con 9/15 gates pass. También quedan abiertas la
sharpness fija, la certificación global independiente, la novedad y la
revisión humana.

### 3.3 V5: resultados exactos y fronteras

V5 contiene 41 entradas. La clasificación exacta es 31
`PROVED_UNDER_ASSUMPTIONS`, 2 `PROVED`, 1 `PROVED_NON_ATTAINMENT`, 2 lower
bounds certificados, 1 conjectura, 4 aperturas/estados históricos y los
certificados finitos/DAG restantes. Las 41 entradas tienen
`NOVELTY_NOT_ESTABLISHED`; 36 tienen `PENDING_HUMAN_REVIEW`.

Resultados centrales cerrados dentro de sus clases declaradas:

- **k=2 general:** `C_2^P(eta)=1` para la clase binaria real finita con leyes
  independientes o repetidas, projector ortogonal y `0<eta<=1`.
- **k=2 gated-planar:** la construcción homogénea tiene error exacto
  `E_proj=eta^2`; sólo satura el bound universal en `eta=1`.
- **k=2 igualdad:** existe una caracterización iff mediante saturación del
  operador exterior, del closure y de la imagen proyectada en el root.
- **k=3 envelope:** el bound universal refinado `U_3(eta)` es estrictamente
  menor que 2 para `eta>0`, pero no es globalmente attained por la cadena.
- **k=3 chain/branch:** el valor exacto para leyes independientes es
  `W_3(eta)`:

  ```text
  W_3(eta) = sqrt(4 - 3 eta^2),       0 < eta <= sqrt(2/3)
           = 2/(sqrt(3) eta),          sqrt(2/3) <= eta <= 1.
  ```

- **k=3 endpoint:** en `eta=1`, el valor es `2/sqrt(3)`, estrictamente menor
  que `sqrt(2)`.
- **k=3 arbitrary finite arity:** con exactamente tres nodos internos, todos
  los perfiles de aridad tienen el mismo `W_3` bajo el mecanismo de leaf
  freezing/effective-law reduction.
- **same-law tagged:** la simulación direct-sum de los witnesses de cadena y
  branching cierra la clase tagged same-law con rank suficiente.
- **same-law rank-one:** el régimen de alta eta queda cerrado; el régimen de
  baja eta se reduce exactamente a un problema de operador unary, pero su
  valor extremal permanece abierto.
- **árbol binario/arity general:** para cada árbol finito fijo,
  `lim_{eta->0} C_T(eta)=k-1` en la clase independent-law declarada.
- **DAG:** el path constant exacto es la suma de fuentes ponderadas por todos
  los productos de ganancias source-to-root; la sharpness asintótica es
  `K(G)` para cada DAG finito independiente declarado.
- **shared diamond:** el coeficiente asintótico exacto es 4.
- **growing trees:** existe una obstrucción certificada a un bound
  nodewise de dimensión/rank value-preserving uniforme en tamaño no acotado;
  no elimina variantes root-only o same-law.

Lo que estos teoremas no dicen: no prueban sharpness para leyes arbitrarias
en todo k, no resuelven las clases same-law/gated no declaradas, no crean una
teoría de límite continuo y no establecen novedad por estar implementados.

## 4. Resultados numéricos y aplicados

### 4.1 Allocators y DAGs

- Probe de fitted pathwise majorant: DP exacto para el majorant declarado;
  reducción de true error observada media `0.3400` en chain y `0.3560` en
  balanced, pero factores empíricos no son normas globales.
- Certificate finite-batch: no-worse fraction del bound `1.0` en ambas
  topologías; reducción RMS held-out observada `0.2432`/`0.2250` contra
  `pathwise_global`; no equivale a superioridad de true error universal.
- Certificate bounded-domain global: holds `1.0` en 240 registros; mejora RMS
  media `0.0148`/`0.0135`; enclosure Frobenius conservadora.
- Level 1 aplicado: Pearson `0.9334132264`, Spearman `0.9216239741`; el
  pathwise correlaciona con `singular_energy`, pero pierde ante `uniform` y
  `local_error_greedy` en comparaciones de presupuesto igual.
- Level 4 shared-DAG: ambos certificados sostuvieron 140/140 casos; el
  allocator rank-aware sólo ganó 16.4% de comparaciones held-out y tuvo
  reducción media `-0.007448`.
- Level 5 matched tolerance: selección por VALID y test independiente
  reproducible, pero transferencia parcial y policies certificadas con más
  contraction units que uniform en promedio.

Dictamen aplicado: `PREDICTIVE_BUT_NOT_POLICY_SUPERIOR`. No hay claim de
superioridad tecnológica, memoria o runtime a error verdadero igual.

### 4.2 Score-space TTN

En el checkpoint D128/E10 de FB15K-237:

- 237 relaciones, 14,541 entidades, dimensión 128.
- A tolerancia `0.0005`, rank uniform 17 y rank spectral promedio
  `9.1864652812`.
- Gap espectral de recurso `G_spectral=1.8505485494` y saving oracle relativo
  `45.959691%`.
- Effective rank: mediana `1.0277785`, máximo `1.6399794`.
- Grassmann fixed-rank-3: mediana `0.00131035`, máximo `0.0983274`.
- Estos números son oracle Frobenius sobre queries/entidades almacenadas; no
  son universalidad ni ranking preservation.

Benchmarks score-only de ejecución muestran variabilidad por executor:

- En una sonda no optimizada, finite-query certificate dio `1.046x` p50
  contra `full_matched`.
- En stress con batching relation-batch 32, uniform `1.011x`, spectral
  `1.017x`, certificate `1.124x`; repeat-index p05 `0.741x`, `0.807x`,
  `1.005x`.
- Ninguno llega al gate robusto median `>=1.5x` y lower bound >1.
- `full_dense` `8x`/`26.5x` es referencia de implementación y no speedup de
  compresión.

### 4.3 Discovery y SRATM

La pista accuracy-first está separada de certificación.

- D256, 8 expertos, 2 activos, rank 64, core basis 4, batch 512, hardK 64,
  seed 42: run detenida por usuario en step 4800; mejor pilot VALID de 512
  queries en step 4608: MRR `0.1778151`, H@1 `0.1523438`, H@3 `0.1953125`,
  H@10 `0.2167969`, mean rank `3130.69`.
- Run D256 2048 steps: pilot MRR histórico máximo `0.133131` en step 1536.
- Run LR `3e-4`, hardK 128: pilot MRR `0.076279`; no finalista.
- Ninguna de estas runs permite SOTA, TEST, certificate o generalization claim.

Para SRATM step 4600:

- Full VALID observado en 35,070 queries: MRR `0.611648`, H@1
  `0.578072`, H@3 `0.623325`, H@10 `0.677645`, mean rank `375.85`.
- Integridad: parámetros finitos, scores finitos, candidate shape `[4,128]`,
  fusion row-sum error `1.19e-7`, orthonormality error `8.94e-7`.
- G6 all-entity con filtros TRAIN+VALID-only y 14,541 entidades: 0 violaciones
  sobre `509,952,870` candidate scores y `max(error-bound)=3.21865e-6`.
- Control full-rank sellado: MRR `0.3958612`.
- Uniform-medium compressed: MRR `0.3674372`, delta `-0.0284240`, CCR@1
  `0.317879`, CCR@3 `0.266039`, CCR@10 `0.189050`, rank equality
  `0.585800`.
- Por tanto G6A (validity of certificate) pasa observado; G6B (predictive
  preservation) falla contra el control sellado; G6C (reconciliación histórica)
  está bloqueado.

### 4.4 Leakage y protocolo histórico

El audit `SRATM_NO_LEAKAGE_AUDIT_V1D` observó:

- runtime forbidden TEST access: 0;
- train-valid overlap: 0;
- reciprocal failures: 0;
- static/runtime split gates: pass;
- vocabulary: TRAIN+VALID transductive universe;
- checkpoint selector: artifact-backed pero no reconstruido desde selector log;
- otros loaders del repositorio aún tienen defaults que mencionan TEST, pero no
  fueron ejecutados por esta campaña.

El `0.6116475463` histórico sigue siendo observado pero no reconciliado.
`checkpoint_last.pt` es step 4600 y coincide con el SHA auditado; `best.pt` es
step 4608 y es distinto. La fuente actual requiere `--test` para el loader
histórico y construye vocabulario/filtros TRAIN+VALID+TEST, mientras la
campaña sellada usa TRAIN+VALID. Faltan command exacto, rank trace, filter
counts, candidate universe, tie policy y runtime snapshot. Esto deja el uso
histórico de TEST en `UNKNOWN_NOT_ESTABLISHED`, no en PASS ni en prueba de
leakage.

## 5. Spectral certification v18 legado

`final_gate_evaluation.json` es explícitamente fail-closed:

- A projector: `STRUCTURAL_IDENTITY_PASS`;
- B commutator: `FAIL`;
- C Beals: sanity numérica;
- D snapping: screening empírico;
- E interscale: `FAIL`;
- F rigidity: screening empírico;
- G n-ary closure: pass estadístico para la configuración;
- H associator: screening empírico;
- I reduced tensor: certificado exacto;
- J tensor interscale: `FAIL`;
- K HOSVD: screening empírico;
- L gauge canonicalization: certificado exacto;
- M persistent factorization: `FAIL`;
- N cyclic law: identidad estructural.

El estado final es `FAIL_CLOSED_PROJECTOR_GATE_NOT_ESTABLISHED`. Las ablations
de B muestran que closure y associator pueden optimizarse por separado y no
explican automáticamente el commutator; E falla en parte de la comparación
12->24; la persistencia no queda establecida por una sola trayectoria.

## 6. Auditoría de gobernanza, papers y revisión

La auditoría estructural es `yellow`, no `green` de release. Los archivos
requeridos están presentes y los contratos de runs son completos, pero:

- hay 8 grupos de duplicados; nunca usar promedios históricos sin el índice
  deduplicado;
- el paper quality report marca release readiness falso;
- V3 tiene 6 blockers de release y 9/15 gates pass;
- el snapshot V5 no tiene revisión humana independiente;
- los cuatro “reviewers” V3 son automatizados: tres recomiendan
  `MAJOR_REVISION`, uno `ACCEPTABLE_AS_RESEARCH_DRAFT`;
- novedad sigue `NOVELTY_NOT_ESTABLISHED` en todas las 41 entradas V5;
- ORCID y contacto de autor siguen sin verificación.

### Hallazgo de drift de revisión

`scripts/verify_projected_trees_v5_review_manifest.ps1` falla actualmente:

```text
claims/theorem_registry_v5.yaml
expected B08E9460...AFB92C
actual   43483A25...A5A901
```

El manifiesto dice que cualquier cambio requiere regenerar hashes y crear un
snapshot fechado nuevo. El drift no implica por sí mismo una modificación
incorrecta; sí invalida el paquete congelado como snapshot exacto. El informe
no actualiza el hash automáticamente.

## 7. Riesgos y blockers priorizados

### P0 — no continuar con claims de release

- **B-0012:** dos bugchecks Windows (`0x00020001` y `0x0000001E`), con WER
  asociado a IOMMU/Intel y pool tracking. El dump principal existe pero está
  protegido; no hay debugger en PATH. GPU largo y hardware claims quedan
  pausados.
- **G6C histórico:** MRR `0.6116475` sin protocolo reconstruido.
- **V5 review drift:** manifiesto congelado no coincide con registry actual.

### P1 — bloquean claims científicos fuertes

- novedad no establecida y revisión humana ausente;
- sharpness fixed-eta/gated/same-law restante;
- matriz V3 extendida 4/460,800 y 0/8,400;
- G6B compressed MRR cae frente al control sellado;
- hardware robust speedup debajo del gate y B-0011 supera 300 s;
- selección de checkpoint sin selector log reconstruido.

### P2 — deuda técnica/documental

- defaults TEST en loaders alternativos;
- ausencia de formalización Lean/lake;
- figures históricas diagnósticas fuera de los nuevos pipelines;
- metadata de autor incompleta;
- suite completa actual no cerrada en esta auditoría por duración.

## 8. Próximos pasos correctos

1. Resolver B-0012 con acceso a dump/debugger, revisión BIOS/IOMMU y drivers;
   después CPU smoke, GPU canary pequeño y sólo luego una escalada checkpointed.
2. Congelar un nuevo review manifest V5 después de revisar el diff exacto del
   theorem registry; no sustituir silenciosamente el hash anterior.
3. Recuperar selector log, rank traces, filter counts y command/runtime
   histórico sin abrir TEST; si no es posible, archivar G6C como irreconciliable.
4. Mantener TEST cerrado hasta que G0--G9 y el protocolo confirmatorio V1
   estén ejecutados bajo una sola convención.
5. No seleccionar teacher/student, compresión ni hardware con el MRR histórico
   `0.6116475`; usar el control sellado `0.3958612` hasta reconciliación.
6. Para allocator/DAG, ejecutar el estudio preregistrado a error verdadero
   igual con semillas independientes, memoria y wall-clock; la evidencia
   actual no avala superioridad.
7. Tratar los resultados V5 como theorem packages condicionados hasta revisión
   humana; no convertir tests o certificados numéricos en aprobación.

## 9. Archivos de autoridad

- Estado y decisiones: `.ai/CURRENT_STATE.md`, `.ai/TASKS.md`,
  `.ai/KNOWN_BLOCKERS.md`, `.ai/DECISIONS.md`.
- Contrato: `AGENTS.md`, `governance/AUTHORITY_LADDER.yaml`,
  `governance/DEVELOPMENT_LIFECYCLE.yaml`.
- Claims: `claims/claims_registry.yaml`,
  `claims/theorem_registry_v2.yaml`, `claims/theorem_registry_v3.yaml`,
  `claims/theorem_registry_v5.yaml`.
- Experimentos: `experiments/configs/` y `experiments/matrices/`.
- Runs y hashes: `runs/`, `artifacts/index/`, `artifacts/runs_v3/`.
- KGE: `seion_kgr/`, `runs/SRATM_*`, `runs/TTN_*`.
- Review V5: `research/projected_trees_v5/review/`.
- Papers: `papers/`, `paper/`.

## 10. Postflight de esta auditoría

- Fecha: 2026-08-10.
- Rama/commit: `campaign/gate13-closeout` / `77f2dfe...`.
- Resultado: `AUDIT_COMPLETE_WITH_SCIENTIFIC_AND_SAFETY_BLOCKERS`.
- Cambios propios: este informe; no se eliminaron ni reescribieron runs,
  checkpoints, dumps, artefactos fallidos o cambios del usuario.
- Limitación principal: la suite monolítica completa se detuvo por duración;
  se reportan sólo las suites focalizadas actuales y las ejecuciones históricas
  con manifest/provenance.
