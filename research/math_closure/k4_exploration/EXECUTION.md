# Ejecución PMT k4 — 2026-09-09

Rama `codex/pmt-k4-chain-gram`; base
`9f1c6d291ef1bb84d2c50602e80090305538c321`. Cambios sin commit; main y
`.claude/` preservados. Prueba matemática: `CHAIN_GRAM_REPORT.md`.

## Resultado y precisión

La fórmula de cadena y mixto tiene una demostración propuesta completa,
pendiente de revisión independiente. No se promovió ningún resultado
histórico. La ramificación debajo de raíz mantiene igualdad abierta.

| eta | fórmula analítica propuesta C | mejor candidato Powell | SDP flotante C |
|---|---|---|---|
| 0.05 | 2.9937507829 | 2.9874738532 | 2.9937507853 |
| 0.2 | 2.9002068892 | 2.8936355985 | 2.9002068896 |
| 0.5 | 2.3848480035 | 2.3834975339 | 2.3848480047 |
| 0.654653671 | 1.9639610121 | 1.9639610119 | 1.9639610121 |
| 0.8 | 1.6071428571 | 1.6070988731 | 1.6071428571 |
| 1 | 1.2857142857 | 1.2856790982 | 1.2857142857 |

V1: 54 candidatos, todos sin convergencia SLSQP declarada (34 alcanzaron el
límite de iteraciones y 20 informaron restricciones incompatibles). Se
conservan los parámetros reparados, los valores crudos y sus violaciones;
45 salidas crudas tenían una restricción <−1e−8. V2: 24 candidatos Powell,
23 con convergencia declarada y uno sin convergencia. Los 78 candidatos
después de reescalar pasan controles globales de norma y clausura a 1e−10.
No se usan las deficiencias del optimizador como evidencia de paisaje.

Cada corrida reproduce 42 controles: C2, W3 cadena/ramificación y trayectorias
de fase gated de k=2,3,4,6 con aridades 2 y 3. Residuo máximo 6.67e−16.
El control negativo ungated tiene defecto global 1 frente a presupuesto 0.2.

Cada corrida incluye 18 SDPs: tres tamaños activos por seis eta. El máximo
desacuerdo k4 con la fórmula es 2.41e−9 en C. Hay tres avisos del solver por
corrida; la peor holgura PSD observada es −8.28e−10. **No es un certificado
SDP con redondeo dirigido**. V2 conserva también las matrices duales.

## Verificación ejecutada

- 201 pruebas PMT/matemáticas pasaron: C2, M14–M20, M24–M25, M40–M42,
  k−1, Gram, dilatación, norma global, cambios de base complejos y topologías.
- 56 pruebas de gobernanza pasaron.
- Auditoría estructural `yellow`, sin archivos requeridos ausentes; conserva
  avisos preexistentes de duplicados y calidad del paper.
- `governance dedupe-runs` ejecutado: no se borraron corridas.
- Un primer control simbólico falló por comparar estructura de expresiones
  SymPy con `==`; se corrigió a comprobar que la diferencia expandida es
  cero. La identidad matemática no cambió. El resultado final figura arriba.

Los registros se encuentran en `artifacts/pmt_k4_chain/`. El índice verificable
es `artifacts/index/pmt_k4_chain_artifacts.json`. V2 archiva las fuentes exactas
en `source_snapshot/`: sus hashes fueron cotejados con run_manifest.json.
V1 conserva hashes pero precede al mecanismo de snapshot; no se afirma que
el árbol de trabajo actual sea idéntico a todas sus fuentes históricas.
La bibliografía del informe se amplió después del snapshot V2; el snapshot
preserva el texto matemático usado en esa corrida.

## Comandos

En un Python instalado con las dependencias del repositorio:

```powershell
python -m pip install -e ".[test,pmt-research]"
python -m seion_core.cli.main governance context --task "PMT k4 chain Gram"
python scripts/run_pmt_k4_chain.py --config experiments/configs/PMT_K4_CHAIN_GRAM_V1.json --output artifacts/pmt_k4_chain/reproduction-v1-NEW
python scripts/run_pmt_k4_chain.py --config experiments/configs/PMT_K4_CHAIN_GRAM_V2.json --output artifacts/pmt_k4_chain/reproduction-v2-NEW
python -m pytest tests/pmt -q
python -m pytest tests/governance -q
python -m seion_core.cli.main governance audit --json
python -m seion_core.cli.main governance dedupe-runs
```

La lista completa de regresiones ejecutadas consta en el postflight de
`.ai/RUN_HISTORY.md` y `artifacts/pmt_k4_chain/regression.txt` conserva la salida.
El runner rechaza directorios existentes para preservar evidencia. El
resumen de esta corrida se regenera con `python scripts/summarize_pmt_k4_chain.py`.

En esta máquina se usó el ejecutable
`C:/Users/Eliuth Chavero/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
y `PYTHONPATH=tmp/pmt_k4_deps;src;.`; OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1.
Las dependencias se instalaron localmente porque Python no estaba en PATH y
el runtime base carecía de SciPy, SymPy, YAML, pytest y CVXPY. Los manifiestos
registran versiones exactas, sistema, comando, fecha, commit, semillas y
configuración. No se ejecutó GPU.

## Límites

No hay aprobación humana ni afirmación de novedad. La prueba angular está
relacionada específicamente con la literatura de scaled relative graphs;
el informe incluye la comparación. El SDP tiene prueba de equivalencia
variacional, pero sus resultados flotantes son NUMERICAL_CANDIDATE. La
etiqueta CERTIFIED_WITNESS identifica una familia con prueba analítica de
admisibilidad, no la aprobación automática de un teorema. No se hizo push,
merge, publicación ni modificación de main.
