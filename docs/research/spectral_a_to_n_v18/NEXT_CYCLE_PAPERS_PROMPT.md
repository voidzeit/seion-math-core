# Prompt para el siguiente ciclo de ejecución — Producción completa de papers

Este documento es el prompt de arranque para la próxima sesión/ciclo cuyo
único objetivo es **expandir los papers cortos existentes a versión
completa/publicable**, incorporando todos los datos nuevos ya generados y
llenando explícitamente los huecos conocidos — sin inventar contenido no
soportado por evidencia real.

Copiar y pegar este archivo completo como mensaje inicial de la próxima
sesión (o pasar la ruta del archivo).

---

## 0. Regla que gobierna todo el ciclo

> Cada afirmación termina en `PROVED`, `CERTIFIED`, `REFUTED` u `OPEN` con
> frontera exacta. Ningún número empírico se presenta como prueba. Si una
> sección no puede completarse con evidencia real en este ciclo (ej.
> búsqueda de literatura, sweep multi-celda), se declara `OPEN` /
> `NOVELTY_UNESTABLISHED` explícitamente — nunca se rellena con contenido
> inventado ni se omite en silencio.

## 1. Estado actual — qué existe y dónde está

Rama: `research/spectral-a-to-n-v18` (PR #2, CI verde:
`governance`/`test`/`packaging`/`spectral-test`, 85 tests en
`spectral/certification_v18/tests`).

Rama separada `infra/agent-graph-loop-v1` (committeada localmente, **aún
no pusheada** a la fecha de este documento): sistema ejecutable de
lifecycle/agentes (`src/seion_core/orchestration/`,
`docs/orchestration/AGENT_GRAPH_LOOP.md`) — dato NUEVO que Paper 3 todavía
no incluye. Confirmar con el usuario si ya se pusheó antes de asumir su
estado.

### Papers actuales (versión corta/borrador ejecutivo — TODOS COMPILAN)

| Paper | Ubicación | Estado actual | Objetivo este ciclo |
|---|---|---|---|
| 1 — Track T (matemática pura) | *(no existe)* | Deliberadamente no escrito — ver `PAPER_2_DEFERRAL_DECISION.md` | Fuera de alcance este ciclo (ver sección 5) |
| 2 — Certificación A-N | `papers/a_to_n_certification_v18/main.tex` | 4 páginas | Expandir a 20-30 páginas |
| 3 — Software/reproducibilidad | `papers/software_reproducibility_v5/main.tex` | 3 páginas | Expandir a 15-25 páginas |
| Atlas visual | `papers/supplementary_visual_atlas_v18/main.tex` | 6 páginas, 7 figuras | Expandir a 25-40 páginas, 20-30 figuras |

### Fuentes de datos reales a usar (no re-derivar, no inventar)

- `spectral/certification_v18/blocks/BLOCK_*_FINDINGS.md` — 14 documentos,
  uno por bloque A-N, cada uno con el hallazgo completo, números exactos y
  veredicto. El paper corto actual solo usa 1-2 párrafos de cada uno.
- `spectral/certification_v18/artifacts/*.json` — `block_b_ablation_matrix.json`,
  `block_e_interscale_experiment.json`, `final_gate_evaluation.json`
  (resultado ejecutado, no narrado).
- `docs/research/spectral_a_to_n_v18/TRUTH_AND_NOVELTY_REPORT.md` — tabla
  completa de veredictos por bloque, ya en la taxonomía
  PROVED/CERTIFIED/REFUTED/OPEN.
- `docs/research/spectral_a_to_n_v18/FINAL_DELIVERY_REPORT.md` — conteos
  exactos de hardware, tests, commits, huecos honestos.
- `docs/orchestration/AGENT_GRAPH_LOOP.md` (rama `infra/agent-graph-loop-v1`)
  — el sistema nuevo que Paper 3 debe incorporar.
- `spectral/legacy/v17/legacy_*` — evidencia legacy ya ingerida (lineage,
  dedup, reclasificación) para la sección de reanálisis histórico de Paper 2.

## 2. Paper 2 — Certificación A-N (expandir de 4 → 20-30 páginas)

Contenido a **agregar** (no reescribir lo que ya está, expandirlo):

1. **Sección por bloque completa** (actualmente 1 párrafo cada uno):
   para cada uno de los 14 bloques, usar el contenido íntegro de su
   `BLOCK_*_FINDINGS.md` — definición formal, supuestos, métrica, umbral,
   controles positivos/negativos/adversariales, política de precisión,
   status determinístico/estocástico, significado exacto de PASS y sus
   no-implicaciones, esquema de artefacto.
2. **Tablas completas** — no solo la tabla de ablación de Block B; agregar
   tablas equivalentes para closure (G), associator (H), HOSVD (K), gauge
   (L), GJI (N).
3. **Matriz theorem-to-theorem de novelty** (Fase 5 del plan de cierre):
   para cada mejora metodológica reclamada (principal angles vs.
   Procrustes vacío, la corrección del loss no-invariante en Block F, el
   mecanismo de conflicto identificado en Block B), buscar el teorema/
   técnica previo más cercano en la literatura real — **esta búsqueda
   debe ejecutarse de verdad** (no simularse). Si no se puede completar
   en este ciclo, la columna de veredicto queda `NOVELTY_UNESTABLISHED`
   explícitamente, con nota de qué falta.
4. **Sección de reanálisis legacy completa** usando
   `spectral/legacy/v17/legacy_run_dedup_report.md` y
   `legacy_claim_reclassification.yaml` en detalle (el paper corto solo
   la resume en el §1).
5. **Sección "Future work" honesta**: sweep multi-celda nunca ejecutado
   (Fase 2 del plan de cierre), Track T pendiente, revisión externa
   adversarial pendiente (Fase 9), sharpness de H y N sin resolver.
6. **Apéndice reproducible**: comandos exactos, hashes de commit, versión
   de Python/torch, hardware.

## 3. Paper 3 — Software/reproducibilidad (expandir de 3 → 15-25 páginas)

Contenido a **agregar**:

1. **El sistema agent-graph-loop completo** (dato NUEVO, no estaba en el
   paper corto): `governance/DEVELOPMENT_LIFECYCLE.yaml` como grafo
   ejecutable, los 15 roles y su binding a stages, el mecanismo de lease
   liveness-aware, el loop de reintento capado en verify. Fuente:
   `docs/orchestration/AGENT_GRAPH_LOOP.md` +
   `src/seion_core/orchestration/*.py` (rama `infra/agent-graph-loop-v1`
   — confirmar si ya está mergeada/pusheada antes de citarla como si
   estuviera en `main`).
2. **SBOM real** — generar uno (`pip-audit`/`cyclonedx-py` o equivalente),
   no solo mencionarlo como pendiente.
3. **Reporte de seguridad real** — ejecutar `pip-audit` (o similar) contra
   las dependencias declaradas; si no se puede ejecutar en este ciclo,
   dejarlo como `OPEN` con la razón exacta, no omitirlo.
4. **Benchmark CPU/GPU más completo** — actualmente solo 1 comparación
   (Block A/B, n=24). Ampliar a más de un tamaño de problema si el tiempo
   lo permite; si no, declarar explícitamente el alcance limitado actual.
5. **Empaquetado / dataset DOI-ready** — estructura de `dataset/` como la
   describe la Fase 6 del plan de cierre (aunque sea solo el esqueleto de
   carpetas + un README, si no hay tiempo de poblarlo completo).

## 4. Atlas visual (expandir de 6 → 25-40 páginas, 7 → 20-30 figuras)

La sección "What is intentionally not included here" del atlas actual
(`papers/supplementary_visual_atlas_v18/main.tex`, §2) ya enumera
exactamente lo que falta — usarla como lista de trabajo literal:

1. Mapas de fase de topología/dimensión/eta y la geometría k vs. k-1 —
   **pertenecen a Track T, quedan fuera de este ciclo** (ver §5).
2. Diagrama completo de gauge-orbit (más allá del ejemplo único en
   `BLOCK_L_FINDINGS.md`) y atlas de permutación/signo de GJI — los datos
   ya existen en `spectral/certification_v18/blocks/`, solo falta
   convertirlos en figura. **Sí es alcanzable este ciclo.**
3. Superficies de máximos adversariales de closure/associator sobre una
   grilla barrida — requiere ejecutar el sweep (no solo una
   configuración); si no se ejecuta el sweep completo en este ciclo,
   generar al menos 2-3 configuraciones adicionales (no solo 1) para
   mostrar variación, y declarar el resto `OPEN`.
4. Precisión/paridad CPU-GPU en más de un bloque y dimensión — repetir el
   experimento de paridad (ya construido y probado en el paper 3) para
   2-3 bloques adicionales.

Cada figura nueva: SVG + PDF vectorial + PNG 300-600 DPI + manifest de
proveniencia + hash, siguiendo `papers/supplementary_visual_atlas_v18/generate_figures.py`
como plantilla (paleta Okabe-Ito, accesible).

## 5. Paper 1 — Track T (Projected Error Geometry): FUERA de este ciclo

Track T requiere trabajo matemático real (cerrar k=1 exacto, resolver
k=2, resolver k=3 — Fase 4 del plan de cierre) **antes** de que exista
contenido real para un paper. Este ciclo **no debe fingir** un Paper 1 con
matemática inventada. Si en algún punto de este ciclo se decide retomar
Track T, debe tratarse como un sub-ciclo separado con su propia
verificación (símbolico + exacto + interval + adversarial), no como una
sección más de este ciclo de "producción de papers".

## 6. Reglas de ejecución heredadas (de sesiones anteriores de este mismo proyecto)

- Confirmar scope una vez, luego ejecutar de forma autónoma sin volver a
  preguntar por ritmo — reservar preguntas solo para: operaciones
  destructivas/irreversibles, credenciales/hardware faltantes, ambigüedad
  matemática genuina, o un costo que exceda órdenes de magnitud lo
  razonable.
- Nunca sustituir ejecución real por documentación (ej.: no narrar una
  búsqueda de literatura que no se hizo; declararla `OPEN` en su lugar).
- Compilar cada paper con `pdflatex` dos veces y **inspeccionar cada
  página visualmente** antes de darlo por terminado (ya se hizo así para
  las 3 versiones cortas — mantener el estándar).
- Commits en hitos coherentes, con mensajes informativos; pedir
  confirmación explícita antes de hacer push u abrir/actualizar un PR
  (no asumir que un push anterior autoriza el siguiente).
- Usar el propio sistema `governance lifecycle` (rama
  `infra/agent-graph-loop-v1`) para conducir este ciclo si ya está
  disponible en la rama de trabajo — es exactamente el caso de uso para
  el que se construyó (plan → change → verify → evidence → postflight →
  release), aunque es opcional, no obligatorio.

## 7. Entregable esperado de este ciclo

- Papers 2, 3 y Atlas expandidos, compilados en PDF, cada página
  inspeccionada.
- Ninguna cita de literatura inventada: si la búsqueda real no se pudo
  completar, la sección de prior art dice explícitamente
  `NOVELTY_UNESTABLISHED — pending literature search`, con lo que sí se
  intentó y lo que falta.
- Un reporte corto al final listando exactamente qué se expandió, qué
  quedó `OPEN`, y qué se recomienda para el ciclo siguiente (Track T,
  sweep completo, revisión externa).
