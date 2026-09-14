# Auditoría de la prueba de la cadena PMT (k=4)

Fecha de observación: 2026-09-10. Rama: `codex/pmt-k4-chain-gram`.
Commit de referencia: `7db99b24b1b562499440f4fb5b250a25b5bb5e8b`.

## Resultado

La auditoría de lectura de `CHAIN_GRAM_REPORT.md`, secciones 3--6, no
encontró una inconsistencia algebraica en la reducción de la cadena a tres
etapas activas. El estado sigue siendo `ADVISORY_PROOF_DRAFT`; esta nota no
es una revisión independiente ni cambia `PROPOSAL_PMT_K4_CHAIN_MIXED_FINITE_ETA_20260909`.

## Puntos comprobados

1. La reducción de las hojas a operadores lineales conserva la norma de la
   ley y reemplaza la clausura por el bloque completo `Q_j A_j P_(j-1)`.
2. La dilatación `V_j=(B_j, sqrt(I-B_j*B_j))` es isométrica y satisface
   `Q'_j V_j P'_(j-1)=(Q_j A_j P_(j-1) pi_(j-1),0)`. Por tanto, la restricción de
   clausura se mantiene sobre todo el subespacio proyectado, no sólo sobre la
   trayectoria observada.
3. Para tres ángulos locales, la distancia angular da
   `||F'_3-R'_3||^2 <= 1+r^2-2r cos(S)`, con
   `r=product_j cos(theta_j)` y `S=sum_j theta_j`. La concavidad de
   `log(cos)` produce `r <= cos(S/3)^3`.
4. La sustitución `z=sin(S/3)^2` produce
   `h(z)=9z-15z^2+7z^3` y `h'(z)=3(1-z)(3-7z)`. El máximo relevante es
   `h(3/7)=81/49`, de donde `G_4 <= 9/7`.
5. El testigo planar con tres fugas iguales alcanza exactamente
   `t^2(9-15t^2+7t^4)`, con `t=min(eta,sqrt(3/7))`, y el lector de
   raíz tiene clausura cero.

## Verificación ejecutada

- `compileall` pasó para `src/seion_core/pmt`,
  `research/math_closure/k4_exploration` y `tests/pmt` usando el runtime
  Python del workspace.
- La identidad algebraica entre la fórmula y `h(t^2)` se comprobó en
  `eta={10^-6,0.05,0.2,0.5,sqrt(3/7),0.8,1}`, con discrepancia absoluta
  menor que `2.3e-16`.
- `git diff --check` pasó.

## Límites que permanecen

- No se ejecutó una nueva suite pytest porque el runtime disponible no incluye
  SciPy; las corridas V1/V2 y la regresión de 201 pruebas conservan su
  evidencia previa en `artifacts/pmt_k4_chain/`.
- No hay certificado SDP con redondeo dirigido.
- La revisión independiente de la prueba sigue pendiente.
- La igualdad para la ramificación debajo de la raíz y para la estrella
  ternaria sigue abierta.
- No se afirma novedad bibliográfica ni promoción de la fórmula a teorema.
