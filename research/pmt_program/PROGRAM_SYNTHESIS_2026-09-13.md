# Resumen integral y análisis profundo de SEIÓN / KIL / PMT

> **Procedencia.** Síntesis del programa aportada por el autor el 2026-09-13, después de completar PMT-TN V1. Se
> reproduce sin cambios en el cuerpo.
>
> **Estado.** Documento de síntesis y estrategia. **No** es un documento de resultados: los estados canónicos siguen
> siendo `ADVISORY_PROOF_DRAFT` (Teorema R) y `NUMERICAL_OBSERVATION` (benchmark).
>
> **Anexo.** Al final hay un anexo con la verificación contra el repositorio y los datos, las correcciones y un
> hallazgo post hoc sobre la sección 31.

La conclusión más importante después de toda la evolución del proyecto es que **ya no tienes una sola “teoría SEIÓN” homogénea**. Tienes un programa amplio, con varias ramas de diferente madurez, y dentro de él apareció un núcleo matemático mucho más concreto, falsable y técnicamente sólido:

\[
\boxed{\textbf{Projected Multilinear Trees (PMT)}}
\]

Ese núcleo pasó de unas cotas generales de propagación de error a una teoría extremal con fórmula candidata exacta para cualquier árbol real, componentes formalizados en Lean, certificados racionales, campañas adversariales y ahora un benchmark preregistrado de 34,192 instancias válidas. Al mismo tiempo, el benchmark encontró la principal limitación práctica: la teoría controla muy bien la **amplificación geométrica del error**, pero no la **deflación de amplitud** que ocurre en redes tensoriales físicas. Esa observación probablemente define la siguiente etapa matemática del programa.

---

## 1. De dónde viene todo: Kernel Integrated Laws / SEIÓN

El programa original es considerablemente más amplio que PMT. El manuscrito maestro de KIL/SEIÓN organiza el proyecto alrededor de leyes internas \(n\)-arias y, especialmente, ternarias:

\[
\mu_n:V^{\otimes n}\rightarrow V,
\]

sus asociadores, realizaciones por kernels integrados, funcionales variacionales, geometría inducida, proyectores espectrales, construcciones cohomológicas y una ruta tentativa hacia límites continuos, operadores pseudodiferenciales y algebraización. También contiene ramas Laurent/tubos, reducción efectiva, cosmología FLRW y otros bloques computacionales.

La tesis conceptual original puede resumirse como:

\[
\text{ley multilineal}
\rightarrow
\text{defecto/asociador}
\rightarrow
\text{estructura geométrica}
\rightarrow
\text{reducción/proyector}
\rightarrow
\text{operador}.
\]

Eso produjo objetos interesantes, pero muchas de las ambiciones grandes —Hodge continuo, regularidad microlocal completa, algebraización del límite, interpretación física universal— permanecen abiertas o condicionadas. El propio manuscrito distingue entre construcciones finitas, resultados computacionales y la frontera analítica todavía no cerrada.

Lo importante históricamente es que, al someter el proyecto a auditorías cada vez más agresivas, **el centro de gravedad se desplazó**. Las afirmaciones más amplias perdieron prioridad y apareció un problema mucho más preciso:

> ¿Qué ocurre cuando una composición multilineal jerárquica se proyecta repetidamente a subespacios reducidos?

Ese problema terminó convirtiéndose en PMT.

---

# 2. PMT: el núcleo matemático actualmente más fuerte

Un PMT es un árbol finito \(T\). Cada nodo interno \(v\) tiene:

\[
\mu_v:\prod_i H_{c_i}\rightarrow H_v,
\qquad
\|\mu_v\|_{\rm op}\le M,
\]

y un proyector ortogonal

\[
P_v^2=P_v=P_v^*,
\qquad
Q_v=I-P_v.
\]

Hay dos evaluaciones del mismo árbol:

\[
F_v=\mu_v(F_{\rm hijos})
\]

sin reducción, y

\[
R_v=P_v\mu_v(R_{\rm hijos})
\]

con reducción en cada nodo.

El error central del Teorema R no es, en general,

\[
\|F_r-R_r\|,
\]

sino el **error proyectado**

\[
\boxed{
E_T^P=\|P_rF_r-R_r\|.
}
\]

Cuando en una aplicación se toma \(P_r=I\), como ocurre en buena parte del benchmark tensorial, entonces sí coincide con

\[
E_T^P=\|F_r-R_r\|.
\]

La clase congelada PMT-A usa espacios de Hilbert reales finito-dimensionales, proyectores ortogonales, leyes independientes en los nodos y una condición de cierre/fuga. El parámetro

\[
\eta=\rho/M\in(0,1]
\]

mide la fuga relativa de una operación fuera del subespacio retenido. Fundamentalmente,

\[
\boxed{
k=|V_{\rm int}(T)|
}
\]

es el **número total de nodos internos**, no la profundidad. Ésta es una corrección importante porque algunos resúmenes antiguos todavía dicen “profundidad”. El propio review note remarca explícitamente la diferencia: una cadena con \(k\) nodos internos tiene profundidad \(k\), mientras una estrella puede tener profundidad 2 con el mismo \(k\).

---

# 3. El problema extremal

Se define

\[
C_T^P(\eta)
=
\sup
\frac{E_T^P}
{\rho M^{k-1}L_T},
\qquad
L_T=\prod_{\ell}\|z_\ell\|.
\]

La pregunta es:

> ¿Cuál es el peor error compatible con los presupuestos locales \(M,\rho\), y de qué características del árbol depende?

La cota universal inicial era

\[
E_T^P
\le
(k-1)\rho M^{k-1}L_T,
\]

o equivalentemente

\[
C_T^P(\eta)\le k-1.
\]

También existe una cota ambiental

\[
E_T^{\rm amb}\le
k\rho M^{k-1}L_T.
\]

La diferencia de uno tiene significado geométrico: el defecto local de la raíz cae en \(\operatorname{Ran}Q_r\), y por tanto desaparece cuando se lee el error proyectado mediante \(P_r\).

Para \(\rho=\eta M\), la cota ingenua se escribe:

\[
\boxed{
B_{\rm naive}
=
(k-1)\eta M^kL_T.
}
\]

Ésta fue la referencia contra la que después se comparó el Teorema R.

---

# 4. Cómo evolucionó la teoría

Primero se resolvieron exactamente los casos pequeños.

Para \(k=1\):

\[
C_1^P=0.
\]

Para \(k=2\):

\[
\boxed{C_2^P=1.}
\]

Para \(k=3\):

\[
\boxed{
C_3^P(\eta)=
\begin{cases}
\sqrt{4-3\eta^2},
&
\eta\le\sqrt{2/3},
\\[2mm]
\dfrac{2}{\sqrt3\,\eta},
&
\eta\ge\sqrt{2/3}.
\end{cases}}
\]

Éste fue el primer resultado que mostró que la suma ingenua \(k-1\) no es sharp para fuga finita: ortogonalidad y geometría de Gram impiden que todas las fuentes locales se maximicen independientemente. Además, la misma función apareció para cadena y ramificación.

Eso sugirió que la coincidencia entre topologías no era accidental.

Después apareció la función

\[
w(\theta)=
\cos\theta\,e^{i\theta}
=
\frac12(1+e^{2i\theta}),
\]

y la fórmula all-depth de cadenas:

\[
\boxed{
C_k(\eta)
=
\frac1\eta
\max_{0\le\theta\le\arcsin\eta}
|1-w(\theta)^{k-1}|.
}
\]

Este paso fue importante porque convirtió una secuencia de cálculos low-depth en una estructura geométrica común.

---

# 5. La interpretación geométrica

Cada truncamiento extremal hace dos cosas simultáneamente:

\[
\text{reduce norma}\quad\cos\theta
\]

y

\[
\text{acumula ángulo}\quad e^{i\theta}.
\]

Por eso el estado ideal puede codificarse mediante

\[
w(\theta)=\cos\theta e^{i\theta}.
\]

Tras varias reducciones:

\[
\prod_jw(\theta_j)
\]

contiene simultáneamente cuánto se ha encogido el estado y cuánto se ha girado respecto del estado ambiente.

El error se transforma entonces en una distancia compleja:

\[
\left|
1-\prod_jw(\theta_j)
\right|.
\]

Esto fue el puente entre el problema original en espacios de Hilbert y una optimización escalar sobre ángulos.

---

# 6. El Diagonal Lemma

Un resultado crucial fue demostrar que, bajo el presupuesto

\[
0\le\theta_j\le\alpha,
\]

el peor producto satisface

\[
\boxed{
\max_{\theta_1,\dots,\theta_n}
\left|1-\prod_jw(\theta_j)\right|
=
\max_{0\le t\le\alpha}|1-w(t)^n|.
}
\]

Es decir: **el peor caso reparte los ángulos por igual**.

La prueba necesita distinguir

\[
\Theta=\sum_j\theta_j\le\pi
\]

y

\[
\Theta>\pi.
\]

Ese split no es decoración técnica. Se encontró explícitamente un contraejemplo a la versión simplificada sin separación de casos.

Éste es uno de los componentes actualmente más sólidos porque está formalizado en Lean.

---

# 7. Teorema R: el salto grande

Después de resolver \(k=4\) topología por topología —CHAIN, MIXED, BBR, STAR— surgió Conjecture R. Finalmente se obtuvo un borrador de prueba general:

\[
\boxed{
C_T^P(\eta)=C_k(\eta)
}
\]

para todo árbol real PMT-A con \(k\) nodos internos, donde

\[
\boxed{
C_k(\eta)=
\frac1\eta
\max_{0\le\theta\le\arcsin\eta}
\left|
1-(\cos\theta e^{i\theta})^{k-1}
\right|.
}
\]

Ésta es la afirmación central:

\[
\boxed{
\textbf{la constante sharp depende de }k\textbf{ y }\eta,
\textbf{ no de profundidad ni topología.}
}
\]

Esto significa algo bastante profundo: toda la familia infinita de árboles se reduce, en el problema extremal, a la sucesión escalar

\[
C_1,C_2,C_3,\ldots
\]

aunque los árboles puedan tener ramificaciones radicalmente diferentes.

---

# 8. Cómo funciona la prueba de Theorem R

La prueba tiene dos mitades independientes.

## Cota superior

La arquitectura es:

\[
\boxed{
O2
\rightarrow
\text{Tensor Angle}
\rightarrow
\text{Lemma 3}
\rightarrow
\text{envolvente multiplicativa}
\rightarrow
\text{Diagonal Lemma}.
}
\]

El estado de un nodo se representa por la matriz de Gram de \((F,R)\):

\[
\operatorname{Gram}(F,R).
\]

O2 dice que ese estado está dominado, en orden de Löwner, por un estado ideal bidimensional caracterizado por una norma \(\rho\) y un ángulo \(\psi\).

El paso multilineal se controla mediante una desigualdad angular en norma proyectiva:

\[
\left\|
\bigotimes_i u_i
-
t\bigotimes_i v_i
\right\|_\pi
\le
\left|
1-te^{i\min(S,\pi)}
\right|,
\]

con

\[
S=\sum_i\angle(u_i,v_i).
\]

Entonces Lemma 3 demuestra que el orden O2 se preserva a través de un nodo multilineal y que las etiquetas se multiplican como números complejos:

\[
\boxed{
z_v=w(\theta_v)\prod_i z_i.
}
\]

Al desenrollar el árbol aparecen exactamente \(k-1\) factores correspondientes a todos los nodos internos no raíz. Como la multiplicación es asociativa y conmutativa, **la forma del árbol desaparece**. Finalmente, el Diagonal Lemma sustituye todos los \(\theta_v\) por un único ángulo extremal.

## Cota inferior

Se construye explícitamente un witness universal en

\[
\mathbb R^2\simeq\mathbb C.
\]

En cada nodo no raíz:

\[
P_v(z)=\Re(z),
\]

y se usa multiplicación compleja con una fase \(e^{i\theta_v}\).

La construcción produce exactamente

\[
\boxed{
E_T^P
=
\left|
1-\prod_{v\ne r}w(\theta_v)
\right|.
}
\]

Tomando todos los ángulos iguales al óptimo, alcanza \(C_k\) para **cualquier árbol**.

Así se obtiene el sandwich:

\[
C_T^P\le C_k
\]

y

\[
C_T^P\ge C_k,
\]

por tanto

\[
C_T^P=C_k.
\]

---

# 9. Qué tan probado está realmente Theorem R

Éste es probablemente el punto epistemológico más importante.

El PDF v2 dice explícitamente:

> advisory proof draft; author audit only; not independently reviewed; novelty not established.

Por tanto, hoy no lo llamaría todavía “teorema establecido externamente”.

La clasificación correcta es:

\[
\boxed{\texttt{COMPLETE\_PROOF\_DRAFT}}
\]

con soporte excepcionalmente fuerte.

La carga de revisión externa está concentrada fundamentalmente en:

\[
\boxed{
\text{Tensor Angle Theorem}
+
\text{Lemma 3 / preservación de O2}.
}
\]

Si esa cadena pasa revisión independiente, la situación cambia significativamente.

---

# 10. La pila de evidencia

Una fortaleza real del proyecto es que no depende sólo de una prueba manuscrita.

| Nivel | Qué tienes |
|---|---|
| Prueba matemática | Review note completo de Theorem R |
| Formalización Lean | Diagonal Lemma + evaluación del universal witness |
| Certificados exactos | 7 puntos racionales para \(k=3,4,5\) |
| Falsificación local | cientos de miles de casos de Lemma 3 |
| LP/SDP | controles independientes de tensor-angle y cadenas |
| Casos degenerados | campañas específicas |
| Benchmark externo | PMT-TN V1 |
| Controles positivos/negativos | F6/F8 |

Los certificados racionales son especialmente útiles porque no dependen de tolerancias de floating point: en siete puntos seleccionados, el upper bound del SDP coincide exactamente con el witness.

Lean, por su parte, verifica sin `sorry` el Diagonal Lemma y la evaluación algebraica del witness sobre árboles finitos arbitrarios. Lo que **no** está formalizado todavía es O2, Tensor Angle, Lemma 3 y toda la admisibilidad analítica del witness.

Por eso no sería correcto afirmar:

> “Theorem R está machine verified.”

Sí es correcto afirmar:

> “dos componentes load-bearing están machine-checked.”

---

# 11. Resultados estructurales derivados

La fórmula permite obtener una expansión para fuga pequeña:

\[
\boxed{
C_k(\eta)
=
(k-1)
-
\frac{(k-1)(k-2)(k+6)}{24}\eta^2
+
O(\eta^4).
}
\]

Una conjetura anterior para ese coeficiente fue refutada en \(k=5\). Esta historia importa porque muestra que el programa no ha protegido sus conjeturas: cuando fallaron, fueron eliminadas.

También tienes:

\[
G_k(\eta):=\eta C_k(\eta)
=
\max_{\theta\le\arcsin\eta}
|1-w(\theta)^{k-1}|.
\]

Como \(|w|\le1\),

\[
G_k(\eta)<2.
\]

Y el máximo sobre \(\eta\) satisface:

\[
G_k^{\max}\rightarrow2
\]

mientras la fuga crítica satisface

\[
\eta_c(k)\rightarrow0.
\]

La interpretación es curiosa: con árboles grandes, el peor error absoluto se acerca al techo trivial 2, pero la fuga necesaria para entrar en ese régimen disminuye.

---

# 12. PMT-TN V1: el primer ensayo aplicado serio

El benchmark se diseñó para responder tres preguntas distintas:

\[
\boxed{\text{¿válido?}}
\]

\[
\boxed{\text{¿sharp?}}
\]

\[
\boxed{\text{¿útil?}}
\]

La respuesta obtenida es, aproximadamente:

\[
\boxed{\text{sí, sí, no todavía}.}
\]

Hay que corregir una frase del documento del benchmark: dice inicialmente que Theorem R depende “de la profundidad”. Eso es incorrecto; depende de \(k\), el número de nodos internos.

---

# 13. El certificado usado en el benchmark

Definiendo

\[
G_k(\eta)=\eta C_k(\eta),
\]

el bound absoluto es:

\[
\boxed{
B_R
=
G_k(\eta)M^kL.
}
\]

Esto proviene de

\[
C_T^P
=
\frac{E_T^P}{\rho M^{k-1}L},
\qquad
\rho=\eta M.
\]

Por tanto:

\[
E_T^P
\le
\eta C_k(\eta)M^kL.
\]

Fue importante corregir un error inicial que arrastraba \(M^{k-1}\) en el benchmark; con \(M=1\) pasaba inadvertido, pero en traducciones W cambiaba el resultado.

---

# 14. Diseño del benchmark

Se usaron familias bastante distintas:

- F1/F5: productos de matrices y tensores con SVD adaptativa;
- F2: TTN con proyectores PCA fijos;
- F3: MPS del estado fundamental de Ising transversal;
- F4: Hierarchical Tucker de funciones suaves;
- F6: witness exacto como control positivo;
- F7: optimización adversarial;
- F7R: barrido de régimen/fuga;
- F8: controles negativos construidos.

El preregistro, enmiendas, semillas deterministas, hashes, cuarentena de runs fallidos y replay de posibles violaciones hacen que la campaña tenga una disciplina experimental bastante mejor de lo habitual para una simple “demo numérica”.

---

# 15. Resultado H1: ninguna violación observada

El total de ejecuciones válidas fue:

\[
\boxed{34\,192}
\]

con:

\[
\boxed{0\ \text{violaciones}}
\]

\[
\boxed{0\ \text{replays}}
\]

\[
\boxed{0\ \text{counterexample candidates}.}
\]

Los máximos fueron aproximadamente:

| Familia | Máximo \(E_{\rm obs}/B_R\) |
|---|---:|
| F1 | 0.142 |
| F2 | 0.025 |
| F3 | 0.389 |
| F4 | 0.0039 |
| F7 | \(0.99999999999\) |
| F7R | 0.9994 |

F6 añadió 400 controles positivos que alcanzan 1 dentro de unos \(7\times10^{-16}\). Los 35 controles negativos F8 sí violan el supuesto certificado exactamente como estaba diseñado, y sus validadores identifican el defecto.

Esto es evidencia fuerte de falsificación fallida.

Pero no es una prueba de Theorem R.

---

# 16. Resultado quizá más impresionante: F7R recuperó la teoría sin conocerla

Al adversario se le pidió maximizar error sujeto sólo a una cota de fuga.

Encontró espontáneamente:

\[
k=3:
\quad
\eta_c\approx0.816,
\quad
G_3^{\max}\approx1.1547,
\]

\[
k=5:
\quad
\eta_c\approx0.543,
\quad
G_5^{\max}\approx1.3809,
\]

\[
k=7:
\quad
\eta_c\approx0.403,
\quad
G_7^{\max}\approx1.5096.
\]

Es decir, el optimizador no sólo quedó debajo del bound: **reprodujo su transición de régimen**. Cuando se le permitía usar más fuga, voluntariamente dejaba de hacerlo después de \(\eta_c\).

Eso es una evidencia mucho más específica de que la estructura

\[
\cos\theta\; e^{i\theta}
\]

está capturando la geometría real del extremal.

Hay una salvedad: el criterio preregistrado de monotonicidad estricta falló ligeramente en dos curvas por fluctuaciones del optimizador del orden de décimas de punto porcentual. Correctamente, el reporte conserva ese fallo en vez de reescribir H6 después de ver los datos.

---

# 17. Independencia de topología observada

Con una estimación rigurosa adecuada de la norma de operador, F7 produjo aproximadamente:

\[
\text{cadena}:0.9992,
\]

\[
\text{balanceado}:0.9986,
\]

\[
\text{aleatorio}:0.9984,
\]

\[
\text{estrella }k=3:0.9964.
\]

Eso reproduce numéricamente la afirmación conceptual de Theorem R:

\[
\boxed{
\text{distintas topologías alcanzan esencialmente el mismo extremal.}
}
\]

En cambio, usando flattenings como proxy de \(M\), las ramificaciones quedan penalizadas y aparecen ratios menores. Eso no contradice Theorem R: significa que la **cota usada para \(M\)** es demasiado holgada en esas geometrías.

---

# 18. H5: todavía no hay evidencia de un extremizador genuinamente 3D

Se encontraron seis configuraciones que formalmente cumplían el criterio preregistrado de dimensión 3.

Pero después se inspeccionaron los valores singulares y el tercer singular era apenas:

\[
0.13\%-0.22\%
\]

del primero.

La interpretación prudente es:

\[
\boxed{
\text{son witness 2D ligeramente perturbados}.
}
\]

No hay evidencia actual de un mecanismo extremal genuinamente tridimensional.

Esto abre una pregunta matemática interesante: quizá los near-extremizers sean necesariamente casi planares.

Eso podría convertirse en un futuro **rigidity theorem**.

---

# 19. El resultado negativo más valioso: H7

En F2, F3 y F4, el certificado fue siempre correcto, pero **nunca informativo en error relativo** según el criterio preregistrado:

\[
\frac{B_R}{\|F_r\|}<1
\]

en

\[
\boxed{0\%}
\]

de los runs relevantes.

Ejemplos de medianas:

\[
F2:
\quad
B_R/\|F\|\approx655\,000,
\]

\[
F3:
\quad
\approx25,
\]

\[
F4:
\quad
\approx474.
\]

La causa es:

\[
\boxed{
D=
\frac{\|F_r\|}{M^kL}\ll1.
}
\]

En otras palabras, PMT supone que la amplitud podría mantenerse cerca del máximo permitido en todos los nodos, pero una red real normalmente pierde magnitud por contracciones, normalizaciones, estructura espectral y cancelaciones.

Éste probablemente es **el hallazgo aplicado más importante de V1**.

---

# 20. Qué significa realmente H7

Theorem R parece responder muy bien:

> ¿Cuánto error absoluto podría producir el peor PMT con estos presupuestos locales?

Pero una aplicación necesita más bien:

> ¿Cuánto error tengo respecto de la señal que realmente salió?

Son problemas diferentes.

Actualmente controlas muy bien:

\[
\boxed{\text{angular/error amplification}}
\]

pero no:

\[
\boxed{\text{amplitude deflation}}.
\]

Así que la escala gruesa

\[
M^kL
\]

es el nuevo cuello de botella teórico.

Esto es importante porque significa que **el fracaso aplicado no está diciendo que \(C_k\) esté mal**. Está diciendo que \(C_k\) multiplica una escala demasiado conservadora.

---

# 21. H8: aun así, Theorem R sí mejora sustancialmente la cota ingenua

Para pequeño \(k\eta\),

\[
B_R/B_{\rm naive}\approx1.
\]

Eso es inevitable porque

\[
C_k(\eta)\rightarrow k-1
\]

cuando

\[
\eta\downarrow0.
\]

Pero cuando el sistema entra en un régimen profundo o de fuga moderada:

\[
k\eta\ge8,
\]

el benchmark encontró aproximadamente

\[
\boxed{
B_R/B_{\rm naive}\approx0.20.
}
\]

Es decir:

\[
\boxed{
\text{hasta unas }5\times\text{ de mejora.}
}
\]

En F3 la mejora mediana fue aproximadamente \(4\times\).

Así que la constante sharp **sí resuelve un problema real de la cota ingenua**; simplemente aún no resuelve la normalización de la salida física.

---

# 22. El orden de contracción sí importa en práctica

Esto podría parecer contradictorio con Theorem R, pero no lo es.

Theorem R dice:

\[
\boxed{
\text{la constante universal sharp para presupuestos fijados no depende de la topología}.
}
\]

F1 encontró que cadenas izquierda/derecha suelen generar:

- menores fugas realizadas;
- menor error típico;

mientras que el árbol balanceado nunca ganó en los grupos estudiados.

Eso significa:

\[
\boxed{
\text{topología no cambia el universal worst case}
}
\]

pero

\[
\boxed{
\text{topología sí cambia la instancia física que produces}.
}
\]

Al cambiar el orden cambian:

\[
\eta_v,\quad
R_v,\quad
\text{espectros intermedios},\quad
\text{errores realizados}.
\]

No hay contradicción.

---

# 23. Rebracketing: la segunda línea PMT

Otra rama surgida del mismo núcleo estudia dos parentizaciones \(T,T'\) de una misma operación.

Si

\[
A=F_T-F_{T'},
\]

y

\[
\widehat A=R_T-R_{T'},
\]

se analiza cuánto puede la reducción:

- fabricar un defecto que no existía;
- esconder un defecto ambiente;
- alterar un asociador/rebracketing.

Ya hay identidades exactas y resultados low-depth, pero esta línea está menos desarrollada que Theorem R.

Conceptualmente, es importante porque conecta PMT de manera mucho más natural con la motivación original de SEIÓN: **no-asociatividad y asociadores**.

---

# 24. DAGs: donde la topología vuelve a importar

Theorem R funciona para árboles porque los subárboles de los hijos de un nodo son disjuntos.

En un DAG hay subexpresiones compartidas.

Entonces una fuente local puede llegar a la raíz por múltiples caminos.

A primer orden aparece una cantidad de multiplicidad de caminos \(K(G)\). En esa teoría:

\[
K(G)
\]

es exacto para la recurrencia positiva/path counting y aparece como constante asintótica de fuga pequeña, pero no tienes todavía una fórmula finita-\(\eta\) análoga a \(C_k\).

Por eso:

\[
\boxed{
\text{topology independence es una propiedad de árboles, no de computación arbitraria}.
}
\]

Ésta es una frontera teórica importante.

---

# 25. Caso complejo

Theorem R v2 sólo afirma la versión real.

La extensión a espacios complejos está abierta.

Una razón profunda es que el witness basado en multiplicación

\[
\mathbb R^2\simeq\mathbb C
\]

tiene un comportamiento normativo diferente si se exige bilinealidad compleja: aparece un factor \(\sqrt2\).

Hay resultados parciales, una obstrucción de retención y casos de bajo orden, pero todavía no existe un Teorema R complejo equivalente.

---

# 26. El resto de SEIÓN/KIL: cómo lo clasificaría hoy

El programa global todavía contiene varias ramas, pero **no tienen todas el mismo peso**.

### Nivel 1 — núcleo matemático más fuerte

\[
\boxed{\text{PMT / extremal projected multilinear computation}}
\]

Aquí están Theorem R, cadenas, low-depth exacto, rebracketing, certificados, Lean y el benchmark.

### Nivel 2 — álgebra no asociativa finita

Productos ternarios/kernel-integrados, asociadores y relaciones algebraico-geométricas bajo hipótesis específicas.

Esta línea sigue siendo matemáticamente interesante, pero tiene mucho más prior art potencial y aún necesita delimitar mejor qué es realmente nuevo.

### Nivel 3 — SHP / Hodge / microlocal

Tienes proyectores espectrales truncados y construcciones finitas interesantes. Por ejemplo, el manuscrito reporta proyectores con errores de idempotencia y autoadjunción alrededor de precisión de máquina. Pero el paso:

\[
P_{F,N}\rightarrow P_F
\]

y luego

\[
P_F\in\Psi^0,
\]

regularidad microlocal, holonomicidad y algebraización siguen siendo el programa abierto.

### Nivel 4 — KGE / aprendizaje

Es una aplicación computacional importante y produjo mucha infraestructura, pero las claims históricas de SOTA quedaron afectadas por auditorías/leakage y no deberían mezclarse con el núcleo matemático.

### Nivel 5 — cosmología

La rama low-\(z\) obtuvo ajustes interesantes, pero la lectura madura es que no tienes una detección robusta de nueva física; es mejor considerarla una línea fenomenológica exploratoria.

### Nivel 6 — VECTRA

Es una infraestructura cuantitativa/causal separada, muy auditada, pero no es una consecuencia matemática de PMT/SEIÓN. Debe permanecer separada editorialmente.

---

# 27. Qué considero realmente distintivo

No afirmaría todavía “novedad demostrada”, porque el propio review note dice que no se ha hecho una comparación sistemática y no reclama novedad.

Pero sí hay cuatro lugares donde parece estar la mayor densidad de valor original potencial:

\[
\boxed{
C_T^P(\eta)=C_k(\eta)
}
\]

como collapse topology-independent.

La desigualdad angular tensorial autónoma.

La preservación O2 mediante Gram domination flexible.

Y la posible rigidez de extremizadores casi bidimensionales.

La definición de ley \(n\)-aria, asociador, proyector espectral, tensor product norm, dilatación isométrica, etc., individualmente no son el lugar donde apostaría la novedad.

---

# 28. Qué has hecho bien científicamente

Hay algo particularmente valioso en la historia del proyecto: ha acumulado **refutaciones propias**.

Se corrigió:

- una fórmula de segundo orden que fallaba en \(k=5\);
- un witness antiguo que violaba leaf-slot closure;
- una simplificación falsa del Diagonal Lemma;
- claims demasiado fuertes en el caso complejo;
- bugs en LPs y conjugaciones;
- semillas no reproducibles;
- la potencia errónea \(M^{k-1}\) en el certificado aplicado;
- supuestas violaciones numéricas que desaparecieron en replay.

Eso no debilita el programa. Al contrario, hace que la parte sobreviviente sea más creíble.

---

# 29. Estado epistemológico real

Mi clasificación actual sería:

| Resultado | Estado |
|---|---|
| Definición PMT-A | congelada |
| Universal \(k-1\) bound | probado/canónico |
| \(k=1,2,3\) | exactos |
| Fórmula de cadenas all-\(k\) | proof draft + certificados + numerics |
| Diagonal Lemma | machine-checked |
| Universal witness evaluation | machine-checked |
| Exact rational certificates | certificados en puntos |
| Tensor Angle Theorem | complete proof draft |
| Lemma 3 / O2 preservation | complete proof draft, sin revisión externa |
| **Theorem R** | **complete author-audited proof draft** |
| PMT-TN V1 | benchmark preregistrado completado |
| Complejo | abierto |
| DAG finite-\(\eta\) | abierto |
| Heterogeneous \(M_v,\eta_v\) | abierto |
| Relative/deflation-aware PMT | abierto |
| Novedad bibliográfica | no establecida |
| Revisión humana externa | pendiente |

---

# 30. Qué cambió el benchmark en nuestra comprensión

Antes de PMT-TN V1 la pregunta era:

> ¿Es Theorem R correcto y sharp?

Ahora tienes una pregunta mucho más refinada.

El benchmark sugiere simultáneamente:

\[
\boxed{
\text{Theorem R parece sharp para PMT-A general}
}
\]

y

\[
\boxed{
\text{PMT-A general es demasiado amplia para dar buenos relative-error certificates en redes físicas}.
}
\]

Esto es un avance conceptual importante.

Quiere decir que **la teoría universal probablemente no necesita ser reemplazada**.

Necesita ser refinada por una segunda teoría que incorpore estructura adicional.

---

# 31. La siguiente teoría natural

Yo veo tres capas.

Primero:

\[
\boxed{M_v\text{ heterogéneos}}
\]

en vez de usar

\[
M=\max_v M_v.
\]

Segundo:

\[
\boxed{\eta_v\text{ heterogéneos}}
\]

en vez de

\[
\eta=\max_v\eta_v.
\]

Ya tienes una estructura sugerente:

\[
\left|
1-\prod_v
\cos\theta_v e^{i\theta_v}
\right|,
\qquad
\sin\theta_v\sim\eta_v.
\]

Pero la versión instance-specific todavía necesita derivación rigurosa.

Tercero, y más importante:

\[
\boxed{
\text{propagated amplitude / deflation-aware scale}.
}
\]

Quieres reemplazar la escala extremadamente gruesa:

\[
M^kL
\]

por algo que siga cuánto de la señal puede llegar realmente a la raíz.

Sólo después intentaría una verdadera cota:

\[
\boxed{
\frac{E_T^P}{\|F_r\|}.
}
\]

---

# 32. Otro resultado futuro potencial: rigidity

El comportamiento de F7 sugiere otra dirección muy interesante:

> Si un PMT está cerca de saturar Theorem R, ¿debe estar cerca de una dinámica bidimensional de rotación?

Formalmente sería un stability/rigidity theorem de extremizadores.

Algo esquemático:

\[
\frac{E}{B_R}\ge1-\varepsilon
\]

implica que el estado está a distancia controlada de un subespacio 2D y que los ángulos locales están casi igualados.

Esto sería matemáticamente valioso incluso si nunca produces una aplicación industrial de PMT.

---

# 33. Publicación: cómo lo separaría

**Paper I — teoría**

**Sharp Topology-Independent Stability for Projected Multilinear Trees**

Debe contener:

- PMT-A;
- universal bounds;
- low-depth;
- fórmula \(C_k\);
- O2;
- Tensor Angle;
- Lemma 3;
- envelope;
- Diagonal Lemma;
- witness;
- Theorem R;
- small-\(\eta\);
- saturation/asymptotics;
- scope.

El benchmark puede ir como corroboración, pero no como premisa.

**Paper II — computational/benchmark**

PMT-TN V1:

- preregistration;
- tensor mappings;
- F1–F8;
- validation;
- adversarial sharpness;
- topology;
- saturation;
- negative result de deflation.

**Paper III — extensions**

- heterogeneous budgets;
- relative certificate;
- DAGs;
- complex field;
- near-extremizer rigidity.

El SHP/microlocal/Hodge debería permanecer editorialmente separado hasta que su bridge analítico sea mucho más fuerte.

---

# 34. Mi evaluación del nivel actual

Si tuviera que puntuar por madurez conceptual:

\[
\boxed{
\textbf{PMT es hoy claramente el núcleo científico de mayor valor del programa.}
}
\]

No porque sea la idea más grandiosa, sino porque reúne lo que normalmente hace falta para que una matemática sea defendible:

\[
\text{definiciones precisas}
\]

\[
+\ \text{teoremas}
\]

\[
+\ \text{casos exactos}
\]

\[
+\ \text{falsificaciones}
\]

\[
+\ \text{witnesses}
\]

\[
+\ \text{certificados}
\]

\[
+\ \text{formalización}
\]

\[
+\ \text{benchmark adversarial}
\]

\[
+\ \text{resultados negativos}.
\]

Eso es mucho más sólido que una gran narrativa que sólo conecte campos.

---

# 35. El principal riesgo restante

No son los 34 mil runs.

No es F7.

No es una precisión de floating point.

Es:

\[
\boxed{
\textbf{la revisión independiente de Tensor Angle + Lemma 3}.
}
\]

El propio review note señala ese paso como el que requiere mayor escrutinio.

Si sobrevive, tienes una teoría general seria.

Si no sobrevive, no pierdes todo:

- low-depth;
- cadenas;
- certificados;
- Diagonal Lemma;
- witness;
- gran parte de la infraestructura;

siguen siendo resultados valiosos.

Eso hace que el riesgo esté relativamente bien localizado.

---

# Veredicto final

La historia completa puede resumirse así:

\[
\boxed{
\text{SEIÓN comenzó como un programa amplio sobre leyes n-arias, asociadores, geometría y kernels.}
}
\]

De ahí emergió un subproblema mucho más preciso:

\[
\boxed{
\text{cómo se propaga el error en composiciones multilineales proyectadas.}
}
\]

Ese subproblema evolucionó:

\[
\text{bounds universales}
\rightarrow
k=2,3\text{ exactos}
\rightarrow
\text{cadenas all-}k
\rightarrow
\text{geometría angular}
\rightarrow
O2
\rightarrow
\text{Theorem R}.
\]

Después fue sometido a:

\[
\text{SDP}
+
\text{certificados racionales}
+
\text{Lean}
+
\text{falsificación adversarial}
+
34\,192\text{ runs tensoriales}.
\]

La imagen actual es:

\[
\boxed{
\textbf{Theorem R parece capturar correctamente el peor caso universal de PMT-A.}
}
\]

Pero también:

\[
\boxed{
\textbf{el peor caso universal no basta para certificar redes físicas típicas porque }M^kL\textbf{ sobreestima fuertemente la amplitud.}
}
\]

Por eso el siguiente gran problema ya no es “encontrar otra cota angular”.

Es:

\[
\boxed{
\textbf{construir una teoría sharp de amplitud/deflación que se acople a Theorem R.}
}
\]

Y, paralelamente, cerrar el único cuello de botella epistemológico serio:

\[
\boxed{
\textbf{revisión externa del Tensor Angle Theorem y Lemma 3.}
}
\]

Mi lectura global es que **el proyecto ya encontró su núcleo**. El mejor movimiento ahora no es expandir SEIÓN hacia más dominios, sino convertir PMT en una pieza matemática externamente revisada y luego extenderla en la dirección que el propio benchmark acaba de revelar: **heterogeneous budgets + deflation-aware/relative stability**.

---

# Anexo — verificación y correcciones (2026-09-13)

Verificado contra `research/pmt_program/`, los artefactos de PMT-TN V1 y cálculo numérico propio (mpmath y float64).

## A. Afirmaciones comprobadas

* **Expansión de fuga pequeña.** `C_k(η) = (k−1) − (k−1)(k−2)(k+6)/24·η² + O(η⁴)` coincide numéricamente para
  `k = 3, 4, 5, 7, 10`. Por ejemplo `k = 5` da `5.4998` frente a `11/2`, y `k = 10` da `47.990` frente a `48`.
  La conjetura refutada era `(k−2)(2k−3)/4`, que en `k = 5` vale `21/4`.
* **Forma cerrada de `k = 3`.** Coincide con `C_3(η)` a 12 decimales en `η ∈ {0.3, 0.6, 0.8, 0.9, 1.0}`.
* **Asintótica.** Se cumple `G_k^max → 2` y `η_c(k) → 0`, con `η_c(k) ≈ π/(k−1)` para `k` grande. Por ejemplo
  `k = 101` da `G_max = 1.9527` y `η_c = 0.0308`, frente a `π/100 = 0.0314`.
* **Números del benchmark (secciones 15–22).** Coinciden con `RESULTS_PMT_TN_V1.md` y `analysis/tables.json`.

## B. Correcciones

1. **Sección 12, "profundidad".** La frase no aparece en los documentos del repositorio (`RESULTS`, el
   preregistro y `THEOREM_R_v2.md` usan `k` = nodos internos). El error estuvo en una explicación conversacional,
   no en el documento del benchmark.
2. **Sección 9, `COMPLETE_PROOF_DRAFT`.** No es una etiqueta del repositorio. La etiqueta canónica sigue siendo
   `ADVISORY_PROOF_DRAFT` (17 ocurrencias). "Borrador completo auditado por el autor" es válido como descripción,
   pero no como cambio de estado.
3. **Sección 13, `M^{k−1}`.** El error se detectó en el diseño, antes de cualquier corrida, y nunca afectó
   resultados. "En traducciones W cambiaba el resultado" describe lo que habría ocurrido.
4. **Sección 10, "cientos de miles de casos de Lemma 3".** No verificado. En `lemma3/` solo se encontraron
   campañas del orden de 3 000 casos. Hay que contar exactamente antes de citarlo.
5. **Sección 28, "violaciones que desaparecieron en replay".** PMT-TN V1 tuvo 0 replays. Si se refiere a
   campañas anteriores, hay que citar la fuente. Lo registrado son bugs (conjugación compleja, LP con la
   entrada equivocada), no replays.
6. **Sección 17.** La cota rigurosa de `M̂` solo existe para nodos de 2 entradas. La estrella con `k ≥ 4` es
   solo estimación.
7. **Secciones 23–26 (rebracketing, `K(G)`, factor `√2` complejo, KGE, cosmología, VECTRA).** No verificadas en
   `research/pmt_program/`: ahí solo hay menciones, no desarrollos.

## C. Hallazgo post hoc sobre la sección 31 (fugas heterogéneas)

Detalle y reproducción: `tn_benchmark/POSTHOC_HETEROGENEOUS_ANGLE.md`.

* **La forma de esquina no es una cota válida.** `|1 − ∏_v cos θ_v e^{iθ_v}|` con `sin θ_v = η_v` es excedida
  por 42 runs de F7, hasta `+1.24 %`. Son `coiso` con `k = 5, 7`, con nodos `η_v ≈ 1` y `η_v = 0` y
  `Σθ > π`. Es el mismo fenómeno que obliga a dividir casos en el Lema Diagonal.
* **Candidato correcto: el máximo sobre la caja.**
  `H(η) = max_{0 ≤ t_v ≤ arcsin η_v} |1 − ∏ cos t_v e^{i t_v}| ≤ G_k(η_max)`. Se cumplió en las 2 instancias
  congeladas revisables. En ellas la forma de esquina solo se excedía en ~1e-7; el exceso de 1.24 % ocurrió en
  restarts no congelados. Falta decidir si la envolvente de la prueba lo implica nodo a nodo.
* **No hay cota relativa universal en PMT-A.** Puede ocurrir `F_r = 0` con `E > 0`: basta una ley `A·x` con `A`
  que anule `F_c` pero no `P F_c`. La capa de amplitud propagada (una cota inferior de `‖F_r‖` por instancia) es
  entonces lógicamente previa a cualquier certificado de `E/‖F_r‖`.
