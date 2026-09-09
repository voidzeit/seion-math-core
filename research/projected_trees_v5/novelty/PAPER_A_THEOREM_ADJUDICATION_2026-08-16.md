# Paper A — adjudicación bibliográfica theorem-by-theorem

Fecha: 2026-08-16  
Objeto: *Sharp Error Amplification in Recursively Projected Multilinear Computations*  
Autoridad de este documento: auditoría asistida, advisory; no es revisión humana ni aprobación de novedad.  
Estado global obligatorio: **`NOVELTY_NOT_ESTABLISHED`**.

## 1. Pregunta adjudicada y respuesta corta

La pregunta única fue:

> ¿Existe ya un teorema equivalente a la constante sharp
> \(C_3^P(\eta)=W_3(\eta)\), o a la universalidad estructural para todo árbol
> finito con tres vértices internos?

En el corpus primario de texto completo descrito abajo **no se identificó un
teorema equivalente**. En particular, no apareció en una misma declaración la
combinación de:

1. leyes multilineales acotadas aplicadas recursivamente;
2. proyección ortogonal después de cada vértice;
3. presupuesto local de cierre sobre entradas ya proyectadas,
   \(\|(I-P)\mu(P\cdot,\ldots,P\cdot)\|\le\rho=\eta M\);
4. error en la raíz después de proyectar, normalizado por
   \(\rho M^{k-1}L_T\);
5. constante exacta para \(k=3\)
   \[
   W_3(\eta)=
   \begin{cases}
   \sqrt{4-3\eta^2},&0<\eta\le\sqrt{2/3},\\
   2/(\sqrt3\,\eta),&\sqrt{2/3}\le\eta\le1;
   \end{cases}
   \]
6. testigos de dimensión dos que alcanzan la cota; y
7. la misma constante para chain, branching y todo perfil finito de aridades
   con exactamente tres vértices internos.

Ésta es una conclusión negativa sobre un corpus acotado, no una prueba de
novedad. Dos antecedentes reducen de forma importante el margen retórico:

- Zhang--Solomonik ya estudian amplificación worst-case de perturbaciones
  locales en redes tensoriales, con cotas tight, condición de red y testigos;
- HSVD/HT y TT ya tienen cotas explícitas y cuasi-optimalidad para productos de
  proyecciones/truncaciones sobre árboles.

Por ello, Paper A no debe presentar como novedosas en sentido amplio ni la
"propagación de error local en una red tensorial" ni la mera aparición de una
constante dependiente del árbol. La candidatura diferenciada es mucho más
estrecha: **el problema extremal fijo-\(\eta\) de cierre proyectado y su valor
piecewise exacto \(W_3\)**.

## 2. Regla de equivalencia usada

Una fuente sólo se consideró equivalente si coincidía en objeto, hipótesis,
normalización, parámetro, alcance topológico y conclusión sharp. Una cota de
otro error, aunque use árboles y proyecciones ortogonales, se clasificó como
adyacente. En particular:

- error de representación de un tensor \(\neq\) error de una evaluación
  recursiva de leyes;
- error respecto de la mejor aproximación de rango \(\neq\) error respecto de
  la evaluación ambiente no proyectada;
- perturbación independiente de tensores de sitio \(\neq\) defecto de cierre
  de una ley sobre entradas proyectadas;
- una cota asintótica o de primer orden \(\neq\) un supremo exacto para todo
  \(0<\eta\le1\);
- proyección sobre un espacio tangente en tiempo \(\neq\) proyección del output
  de cada ley en un árbol estático.

Los snippets y abstracts se usaron sólo para descubrimiento. Las adjudicaciones
de la tabla siguiente provienen de los textos completos listados en la sección 4.

## 3. Adjudicación theorem-by-theorem

| ours | closest precedent | difference | verdict | full-text location / pages / sections |
|---|---|---|---|---|
| **Expansión exacta por subconjuntos de defectos y cancelación del defecto local de la raíz por \(P(I-P)=0\).** | Zhang--Solomonik, expansión multilineal de perturbaciones de sitios y Theorem 3.5; Grasedyck, Lemmas 14/16 para truncaciones sucesivas. | Zhang--Solomonik perturban los tensores de sitio y controlan el tensor contraído, con una fórmula first-order más \(O(\varepsilon^2)\). Grasedyck suma colas SVD de proyecciones de un tensor fijo. Ninguno usa el mapa de cierre \((I-P)\mu(P\cdot)\), ni compara evaluación ambiente con evaluación recursivamente proyectada, ni obtiene la cancelación especial de la raíz. La expansión multilineal/telescópica en sí es técnica estándar y no debe venderse como contribución autónoma fuerte. | `SUBSTANTIAL_ADJACENT_PRIOR_ART`; equivalencia no identificada; `NOVELTY_NOT_ESTABLISHED`. | Zhang--Solomonik, §§2.4, 3, PDF pp. 5--8, Defs. 2.9--2.11 y Thm. 3.5; Grasedyck, §3, PDF pp. 9--11, Lemmas 14/16 y Thm. 17. |
| **Cota universal proyectada \(C_T^P(\eta)\le k-1\).** | Zhang--Solomonik, Thm. 3.5 y Cors. 3.6, 6.2--6.3; Baboulin--Kaya--Mary--Robeyns, Thm. 3.2; Grasedyck, Thm. 17/Rem. 18; Hackbusch, (27). | Los dos primeros prueban crecimiento lineal de error local/perturbación en redes tensoriales, pero con matrices ambiente, normas de sitios, gauge/canonical form o rounding de precisión finita. HSVD/HT compara truncación con best rank approximation y produce \(\sqrt{2d-3}\), no \(k-1\). Ninguno implica el presupuesto de cierre homogéneo ni la eliminación exacta del término raíz. El antecedente conceptual es fuerte: no afirmar que Paper A introduce por primera vez amplificación lineal local-to-global. | `NO_EQUIVALENT_IDENTIFIED_IN_FULL_TEXT_CORPUS`, con `SUBSTANTIAL_ADJACENT_PRIOR_ART`; `NOVELTY_NOT_ESTABLISHED`. | Zhang--Solomonik, §3, PDF pp. 6--8, y §6.1, pp. 13--15; Baboulin et al., §3.3, PDF pp. 11--13; Grasedyck, §3, pp. 9--11; Hackbusch, §4.6, PDF p. 15, eq. (27). |
| **Exactitud \(k=2\), \(C_2^P(\eta)=1\), y condiciones de igualdad.** | SVD/Eckart--Young en cada matricización; Kayalar--Weinert para la norma exacta de un producto de dos proyecciones, reproducido en Lewis--Malick (5) y Reich--Zalas (3). | Los antecedentes tienen igualdad sharp para aproximación matricial o iteración entre subespacios, pero no para dos leyes bilineales con defecto de cierre y raíz proyectada. La prueba de Paper A es una cadena elemental de desigualdades; aunque no se encontró el mismo enunciado, su valor de novedad independiente es probablemente bajo. | `LIKELY_FOLKLORE_OR_ELEMENTARY_SPECIALIZATION`; equivalencia no identificada; `NOVELTY_NOT_ESTABLISHED`. | Lewis--Malick, §3, PDF p. 7, eqs. (4)--(5), y §4, pp. 8--10; Reich--Zalas, Introduction, PDF pp. 2--3, eqs. (3)--(4). |
| **M13: envelope incondicional de chain \(C_{3,\mathrm{chain}}^P(\eta)\le W_3(\eta)\).** | Zhang--Solomonik, Thm. 3.5 y sistema cuadrático (13)--(14) para worst-case perturbations; exact constants de alternating projections parametrizados por ángulo. | Hay optimización worst-case y acoplamiento por matrices ambiente, pero no el Gram constraint simultáneo \(0\preceq N^*QN\preceq I\), el cuadrado \((q,s)\in[0,\eta]^2\), ni la transición en \(\sqrt{2/3}\). La técnica PSD/Gram y dualidad de norma son estándar; el valor específico de la optimización no fue localizado. | `NO_EQUIVALENT_IDENTIFIED_IN_FULL_TEXT_CORPUS`; `NOVELTY_NOT_ESTABLISHED`. | Zhang--Solomonik, §3, PDF pp. 7--8, Thm. 3.5 y Rem. 3.7; Lewis--Malick, §§3--4, PDF pp. 7--10. |
| **M14: \(C_{3,\mathrm{chain}}^P(\eta)=W_3(\eta)\), con witness real 2D rank-one.** | Zhang--Solomonik, tight worst-case site perturbation y product-state witnesses; Kayalar--Weinert/Lewis--Malick, constantes exactas dependientes de ángulo. | Zhang--Solomonik da tightness first-order/condition-number y algunos bounds tight hasta \(O(\varepsilon^2)\); alternating projections da \(c^{2n-1}\). Ninguno da el error no lineal fijo-\(\eta\), la fórmula piecewise, el plateau de \(G_3=\eta W_3\), ni el witness de tres leyes. | `NO_EQUIVALENT_IDENTIFIED_IN_FULL_TEXT_CORPUS`; candidato central diferenciable, pero `NOVELTY_NOT_ESTABLISHED`. | Zhang--Solomonik, Thm. 3.5 y Cor. 3.8, PDF pp. 7--9; §6.1, pp. 13--15; Lewis--Malick, eq. (5), PDF p. 7. |
| **M15: \(C_{3,\mathrm{branch}}^P(\eta)=W_3(\eta)\), por dualidad nuclear/operator y polar factor.** | Error HT/TT sobre árboles (Grasedyck; Hackbusch; Nouy) y worst-case TN perturbation (Zhang--Solomonik). | La literatura HT trata un tensor fijo y colas de singular values; Zhang--Solomonik trata ambientes de sitios. No se identificó un teorema que scalarice la raíz bilineal, reduzca a la norma nuclear de dos términos ortogonales y alcance exactamente el mismo \(W_3\) que chain. La dualidad nuclear/operator es estándar; la instancia extremal concreta no fue localizada. | `NO_EQUIVALENT_IDENTIFIED_IN_FULL_TEXT_CORPUS`; `NOVELTY_NOT_ESTABLISHED`. | Grasedyck, §§2.3--4, PDF pp. 4--16; Hackbusch, §§4.6--5.3, PDF pp. 14--18; Nouy, §5, PDF pp. 19--23; Zhang--Solomonik, §3, pp. 6--9. |
| **M16: universalidad binaria \(k=3\): chain y branching tienen el mismo \(W_3\) cuando las leyes de los nodos son libres.** | Las formulaciones generales de árboles binarios HT/TTN en Grasedyck, Hackbusch y Ceruti--Lubich--Walach; perturbaciones independientes de nodos en Zhang--Solomonik. | Esas fuentes permiten topologías generales o perturbaciones independientes, pero sus constantes siguen dependiendo de dimensión, entorno, tolerancia, paso temporal o árbol. No prueban igualdad de los dos esqueletos binarios con una función universal fija-\(\eta\). La reducción "sólo hay chain y branch" es combinatoria elemental; el contenido no elemental es heredar las dos igualdades sharp. | `NO_EQUIVALENT_IDENTIFIED`; mecanismo estructural `ELEMENTARY_COROLLARY`, no una segunda gran claim de novedad; `NOVELTY_NOT_ESTABLISHED`. | Grasedyck, §2, PDF pp. 5--8; Hackbusch, §4, PDF pp. 9--15; Ceruti--Lubich--Walach, §§2, 4--6, PDF pp. 4--23; Zhang--Solomonik, Def. 2.9 y Rem. 3.3, PDF pp. 5--9. |
| **M20: todo perfil finito de aridades con exactamente \(k=3\) tiene \(C_{T,\mathrm{ind}}^P(\eta)=W_3(\eta)\), por congelación de hojas proyectadas y embedding con gates.** | Nouy, formatos tree-based de aridad/topología general y nested projections; Ceruti--Lubich--Sulz, TTN general y truncación adaptativa; Hackbusch, tree-based generalization. | Los precedentes tienen árboles no necesariamente binarios y recursiones de proyección/truncación, pero no el lema de effective-law que preserva simultáneamente \(M\) y \(\rho\), ni la clasificación del skeleton interno de tres nodos seguida de un embedding sharp en cada perfil. La parte combinatoria/congelación es natural y puede ser considerada folklore; no se encontró la igualdad universal \(W_3\). | `NO_EQUIVALENT_IDENTIFIED`; universalidad como corolario estructural, no claim autónoma prioritaria; `NOVELTY_NOT_ESTABLISHED`. | Nouy, §§4--5, PDF pp. 14--23, especialmente Thms. 5.5--5.6; Ceruti--Lubich--Sulz, §§4--5 y App. A, PDF pp. 10--16 y 26--29; Hackbusch, §§4--5, PDF pp. 9--18. |
| **M18--M19: para todo árbol fijo, \(\lim_{\eta\downarrow0}C_T^P(\eta)=k-1\).** | Zhang--Solomonik, condition number y tight first-order amplification con product-state witnesses; Baboulin et al., error global lineal en número de operaciones; estabilidad TTN/step-truncation. | Éste es el solapamiento conceptual más fuerte con el régimen pequeño-\(\eta\): ya existen coeficientes first-order tight para perturbaciones locales de redes. Pero los perturbadores, denominadores y admisibilidad difieren, y no se identificó la constante proyectada de cierre ni el witness de leyes que da exactamente \(k-1\) después de cancelar la raíz. El paper debe citar estos antecedentes y evitar lenguaje de "primera amplificación lineal sharp". | `SUBSTANTIAL_ADJACENT_PRIOR_ART`; no equivalencia verificada; `NOVELTY_NOT_ESTABLISHED`. | Zhang--Solomonik, §§3, 6, PDF pp. 6--9 y 13--17; Baboulin et al., Thm. 3.2, PDF pp. 12--13; Ceruti--Lubich--Walach, Thm. 6.1, PDF pp. 21--23. |

## 4. Corpus primario leído en texto completo

| Área | Fuente primaria | Qué se adjudicó | Ubicación de texto completo |
|---|---|---|---|
| HSVD/HT | L. Grasedyck, *Hierarchical Singular Value Decomposition of Tensors*, SIAM J. Matrix Anal. Appl. 31 (2010), DOI [10.1137/090764189](https://doi.org/10.1137/090764189). | Tucker \(\sqrt d\), HT \(\sqrt{2d-3}\), successive projections, leaves-to-root truncation. | [Preprint completo](https://webdoc.sub.gwdg.de/ebook/serien/e/MPI_Math_Nat/preprint2009_27.pdf), §§2.3--5; Lemmas 6, 14, 16; Thm. 17/Rem. 18; Thm. 27. |
| TT | I. Oseledets, *Tensor-Train Decomposition*, SIAM J. Sci. Comput. 33 (2011), DOI [10.1137/090752286](https://doi.org/10.1137/090752286). | TT-SVD error y quasi-optimality \(\sqrt{d-1}\); rounding. | [PDF completo](https://users.math.msu.edu/users/iwenmark/Teaching/CMSE890/TENSOR_oseledets2011.pdf), §2, Thm. 2.2 y Cor. 2.4, PDF pp. 5--6; §3. |
| HT/HOSVD | W. Hackbusch, *Truncation of tensors in the hierarchical format*, SeMA J. 78 (2021), DOI [10.1007/s40324-018-00184-5](https://doi.org/10.1007/s40324-018-00184-5). | HOSVD truncation, quasi-optimalidad y producto ordenado de proyecciones de árbol. | [PDF completo open access](https://link.springer.com/content/pdf/10.1007/s40324-018-00184-5.pdf), §§3.4, 4.6, 5; eqs. (14), (27), PDF pp. 8, 15--18. |
| Tree-based PCA | A. Nouy, *Higher-order principal component analysis for the approximation of tensors in tree-based low-rank formats*, arXiv:1705.00880. | Nested orthogonal/oblique projections, quasi-optimal error y tolerancia en árboles generales. | [PDF completo](https://arxiv.org/pdf/1705.00880), §§3--6; Thms. 5.5, 5.6, 6.8, PDF pp. 21--23, 30--31. |
| TN perturbation | Y. Zhang, E. Solomonik, *On Stability of Tensor Networks and Canonical Forms*, arXiv:2001.01191. | Condición de red, perturbación de sitios, cotas worst-case tight y testigos MPS/PEPS. | [PDF completo](https://arxiv.org/pdf/2001.01191), §§2.4, 3, 6; Thm. 3.5, Cors. 3.6/3.8/6.1--6.5, PDF pp. 5--17. |
| TTN finite precision | M. Baboulin, O. Kaya, T. Mary, M. Robeyns, *Numerical Stability of Tree Tensor Network Operations, and a Stable Rounding Algorithm*, preprint 2025, HAL `hal-04996127`. | Propagación de errores locales por operaciones Split/Merge y estabilidad bajo normalización. | [PDF completo](https://www.lip6.fr/Theo.Mary/doc/TTNstab.pdf), §§2--5; Thms. 2.8, 3.1, 3.2, PDF pp. 5--22. |
| Alternating projections | A. Lewis, J. Malick, *Alternating Projections on Manifolds*, Math. Oper. Res. 33 (2008). | Constante exacta de subespacios \(c^{2n-1}\), extensión local a manifolds y tasa por ángulo. | [PDF completo de autor](https://people.orie.cornell.edu/aslewis/publications/08-alternating.pdf), §§3--5; eq. (5), Thms. 4.1--4.3, PDF pp. 7--13. |
| Projection constants | S. Reich, R. Zalas, *The Optimal Error Bound for the Method of Simultaneous Projections*, arXiv:1704.00308. | Reproduce el exact bound de Kayalar--Weinert y obtiene el exact norm value del método simultáneo. | [PDF completo](https://arxiv.org/pdf/1704.00308), Introduction y §2; eq. (3), Thm. 8, PDF pp. 2--7. |
| DLRA HT/TT | C. Lubich, T. Rohwedder, R. Schneider, B. Vandereycken, *Dynamical Approximation by Hierarchical Tucker and Tensor-Train Tensors*, SIAM J. Matrix Anal. Appl. 34 (2013), DOI [10.1137/120885723](https://doi.org/10.1137/120885723). | Tangent-space Galerkin projection, curvature y quasi-best dynamical error. | [PDF completo de autor](https://www.unige.ch/math/vandereycken/papers/published_Lubich_RSV_2013.pdf), §§3--5; Thms. 5.1--5.3, PDF pp. 17--19. |
| Projector splitting TT | C. Lubich, I. Oseledets, B. Vandereycken, *Time Integration of Tensor Trains*, arXiv:1407.2042. | Splitting del proyector tangente y exactness para trayectorias de rango TT fijo. | [PDF completo](https://arxiv.org/pdf/1407.2042), §§3--5; Thm. 5.1, PDF pp. 16--17. |
| TDVP/DLRA TTN | G. Ceruti, C. Lubich, H. Walach, *Time Integration of Tree Tensor Networks*, arXiv:2002.11392. | Recursión TTN, exactness y error robusto independiente de small singular values. | [PDF completo](https://arxiv.org/pdf/2002.11392), §§4--6; Thms. 5.1 y 6.1, PDF pp. 20--23. |
| Rank-adaptive TTN | G. Ceruti, C. Lubich, D. Sulz, *Rank-Adaptive Time Integration of Tree Tensor Networks*, SIAM J. Numer. Anal. 61 (2023), DOI [10.1137/22M1473790](https://doi.org/10.1137/22M1473790). | Error \(c_0\delta+c_1\varepsilon+c_2h+c_3\vartheta/h\), truncación adaptativa y error de rounding TTN. | [PDF completo](https://arxiv.org/pdf/2201.10291), §5, Thm. 5.1, PDF pp. 15--16; App. A, Thm. A.1, pp. 26--29. |
| Step truncation | A. Rodgers, A. Dektor, D. Venturi, *Adaptive Integration of Nonlinear Evolution Equations on Tensor Manifolds*, J. Sci. Comput. 92 (2022), DOI [10.1007/s10915-022-01868-x](https://doi.org/10.1007/s10915-022-01868-x). | Best/HOSVD truncation, consistencia y global error de integradores rank-adaptive. | [PDF completo](https://arxiv.org/pdf/2008.00155), §§2--4; eq. (7), Lemma 2 y Thm. 1, PDF pp. 3--9. |
| Galerkin bilinear MOR | M. Redmann, I. Pontes Duff, *Full State Approximation by Galerkin Projection Reduced Order Models for Stochastic and Bilinear Systems*, Appl. Math. Comput. 420 (2022), DOI [10.1016/j.amc.2021.126561](https://doi.org/10.1016/j.amc.2021.126561). | Error de estado de un sistema dinámico bilineal reducido por Gramians/Galerkin. | [PDF completo](https://arxiv.org/pdf/2102.07534), §§3--5; Thms. 4.8 y 5.2. |

### Fuente descubierta pero no contada como lectura completa

Kayalar--Weinert, *Error bounds for the method of alternating projections*,
Math. Control Signals Systems 1 (1988), DOI
[10.1007/BF02551235](https://doi.org/10.1007/BF02551235), está tras paywall en
el acceso disponible. No se adjudicó desde el abstract. Su identidad exacta
\(\|(P_NP_M)^n-P_{M\cap N}\|=c(M,N)^{2n-1}\) se verificó en los textos
primarios completos de Lewis--Malick y Reich--Zalas, que la reproducen y
atribuyen explícitamente. La revisión del original sigue siendo una tarea
humana/de biblioteca, aunque su resultado citado no es candidato a equivalencia
con Paper A.

## 5. Diferencias decisivas por familia

### HSVD / HT / TT

El denominador decide la no equivalencia. HSVD/TT prueban, por ejemplo,

\[
\|A-H_r(A)\|_F\le \sqrt{2d-3}\,
\inf_{B\in\mathcal H_r}\|A-B\|_F
\]

(o \(\sqrt{d-1}\) en TT). Paper A prueba una razón contra
\(\rho M^{k-1}L_T\), no contra el mejor tensor de rango dado. En HSVD se
trunca un tensor fijo; en Paper A cada nodo es una ley y la proyección cambia
los inputs recibidos por los ancestros. Los valores \(\sqrt{2d-3}\) y
\(W_3(\eta)\) no son constantes competidoras del mismo problema.

### Perturbación y estabilidad de redes tensoriales

Zhang--Solomonik es el antecedente más cercano: su función de contracción es
multilineal en los tensores de sitio, su error se descompone por ambientes, y
sus cotas pueden ser tight. Sin embargo, su parámetro controla
\(\|\delta^{(i)}\|_F\) respecto de \(\|T^{(i)}\|_F\); Paper A controla sólo la
parte normal de una ley evaluada sobre inputs proyectados. Su Thm. 3.5 es
first-order más \(O(\varepsilon^2)\) para el tensor contraído; no determina el
supremo fixed-\(\eta\) de la diferencia entre evaluación ambiente y evaluación
recursivamente proyectada. Esta diferencia debe explicarse en Paper A, no
suponerse.

### Alternating projections

Aquí sí existen constantes sharp dependientes de un parámetro geométrico:
\(c(M,N)^{2n-1}\). Por tanto es inseguro decir que Paper A es el primer trabajo
con una constante exacta para una computación proyectada. El objeto, no
obstante, es distinto: iteración de proyectores lineales para alcanzar una
intersección, frente a composición de leyes multilineales con inyección local
de defectos de cierre. No hay \(\rho\), leyes por nodo, topología chain/branch
ni optimización \(W_3\).

### DLRA / TDVP / projector splitting / rank adaptivity

Estas fuentes proyectan un campo vectorial sobre el espacio tangente de una
variedad de tensores de rango fijo o adaptativo y analizan error temporal,
exactness, tolerancia y robustez frente a singular values pequeñas. El error
depende de \(h\), tolerancia, remainder tangencial, Lipschitz constants y tiempo.
No es un problema estático de cierre de una ley ni un supremo fijo-\(\eta\).
La recursión leaf-to-root de TTN es un antecedente de arquitectura, no un
teorema que implique \(W_3\).

## 6. Lenguaje seguro para Paper A

Hasta revisión humana, el paper puede decir:

> We determine, for the explicitly defined independent-law class, the exact
> fixed-defect-ratio constant \(W_3(\eta)\) for every finite three-node arity
> profile. Existing HT/TT truncation, tensor-network perturbation, alternating-
> projection, and DLRA/TDVP bounds concern different error objects or
> normalizations.

No puede decir:

- “the first sharp error amplification constant”;
- “the first sharp stability theorem for tensor networks”;
- “no prior work studies local-to-global tensor-network error”;
- “HSVD/TT constants are improved by \(W_3\)”;
- “novel” o “previously unknown” sin adjudicación humana.

La tabla mínima `ours | closest precedent | difference` para la introducción
debe concentrarse en tres filas: (i) HT/TT quasi-optimal truncation, (ii)
Zhang--Solomonik sitewise perturbation/conditioning, y (iii) TTN/DLRA robust
time integration. Alternating projections debe aparecer para evitar una claim
demasiado amplia sobre constantes sharp de proyección.

## 7. Cierre pendiente para una decisión humana

1. Leer el original completo de Kayalar--Weinert mediante biblioteca y cerrar
   su cadena de referencias, aunque no parece candidato directo a \(W_3\).
2. Hacer un citation-graph sweep desde Zhang--Solomonik sobre condition numbers,
   perturbación de contracciones y canonical forms; es el riesgo principal de
   un antecedente equivalente en otra notación.
3. Adjudicar con un experto si la proyección recursiva de Paper A puede
   codificarse como una clase especial de perturbación de tensores de sitio. Si
   puede, identificar exactamente qué parte queda después de especializar el
   Thm. 3.5; si no puede, dejar una proposición explícita con la obstrucción.
4. Revisar literatura de estabilidad de multiplicatividad aproximada en
   álgebras de Banach/operator spaces. No apareció una equivalencia en los
   registros v1/v2/V5, pero el corpus actual no cierra exhaustivamente esa
   familia.
5. Obtener revisión matemática externa de M13--M15 y revisión bibliográfica
   independiente. Una ausencia de match en esta auditoría asistida no puede
   cambiar el estado.

## 8. Veredicto final

\[
\boxed{
\begin{array}{l}
\text{No se identificó un precedente equivalente a }C_3^P(\eta)=W_3(\eta)\\
\text{ni a la igualdad para todo perfil finito de aridades con }k=3.\\
\text{Sí existe prior art sustancial sobre amplificación tight de errores locales}\\
\text{en redes tensoriales y sobre proyección/truncación recursiva.}
\end{array}}
\]

En consecuencia, la posición responsable sigue siendo:

\[
\boxed{\texttt{NOVELTY\_NOT\_ESTABLISHED}.}
\]

