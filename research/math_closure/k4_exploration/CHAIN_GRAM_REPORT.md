# Cadena PMT k=4: Gram, dilatación y constante a fuga finita

Fecha: 2026-09-09. Rama `codex/pmt-k4-chain-gram`.
**Estado: demostración propuesta, ADVISORY_PROOF_DRAFT, pendiente de revisión
independiente.** No modifica la clasificación histórica de M14–M20 ni aprueba
un teorema oficial o una publicación. Los resultados numéricos son controles
de implementación, no premisas de la demostración.

## 1. Clase y resultado propuesto

Se usa el canon `papers/projected_multilinear_trees/CANONICAL_FORMALIZATION.md`,
Definitions 1–7: espacios de Hilbert finitos reales o complejos, proyectores
ortogonales, leyes independientes de norma multilineal inducida <=1, hojas
ambientales unitarias (proyector extendido I), y clausura <=eta sobre **todo**
el producto de subespacios proyectados. El presupuesto eta pertenece a (0,1];
no obliga a que cada defecto agote el presupuesto. La norma multilineal es el
supremo sobre productos de bolas unitarias, no una norma de matricización.

Para la cadena de cuatro vértices internos, la demostración de §§3–6 da

\[
C_{4,\mathrm{chain}}^{P,\mathrm{fin}}(\eta)=
\begin{cases}
\sqrt{9-15\eta^2+7\eta^4},&0<\eta\le\sqrt{3/7},\\
9/(7\eta),&\sqrt{3/7}\le\eta\le1.
\end{cases} \tag{1}
\]

El error absoluto se satura en 9/7. Se proporciona tanto una cota superior
para todas las dimensiones/rangos como un testigo planar admisible. La
implementación numérica de (1) vive en el módulo de investigación
`chain_analysis.py`, sin cambiar el contrato público `K4_FRONTIER`.

## 2. Auditoría de los contratos reproducidos

| Contrato | Uso y límite |
|---|---|
| M14–M16 | W3 exacta en cadena/ramificación independientes; testigos y pruebas de Gram/polar |
| M17 | C2=1, incluso en la subclase repetida contractiva descrita allí |
| M18–M19 | límite k−1; se reproducen trayectorias con la corrección de hojas siguiente |
| M20 | fijar hojas conserva normas y clausura; gates de norma uno insertan aridades extra |
| M24–M25 | certificados por muestra, originalmente raíz sin proyección; para E^P se aplica P a la ley raíz; no son cotas sharp de clase |
| M39 | búsqueda experimental de pares de árboles; no es un teorema de k4 |
| M40–M42 | J2=H2=2 y Sigma2 por regímenes, problema de pares distinto del presente |

**Conflicto histórico de hojas.** M18/M19 usan `exp(i theta) prod z_i`
también en slots de hojas. Con el canon actual (hojas ambientales) su defecto
en un nodo inferior es 1: basta fijar todos los argumentos salvo uno a 1 y
variar la fase del restante. No basta comprobar el valor en las hojas elegidas.
La corrección admisible es sustituir cada slot de hoja por su coordenada real
e0, un funcional real de norma uno, y multiplicar complejamente sólo los
slots de hijos internos. En entradas proyectadas todos esos factores son
reales; el defecto es <=sin(theta). Las trayectorias F y R no cambian.
`pmt/phase.py` implementa esta familia independiente, sin editar los registros
históricos. La distinción se registra también en `.ai/KNOWN_BLOCKERS.md`.

La multiplicación compleja aquí es una ley **real** sobre R². No debe
complejificarse sin comprobar de nuevo la norma multilineal. El testigo lineal
de §6 sí se complejifica: matrices reales con la misma norma espectral y gates
coordenados complejos lineales.

El optimizador histórico k4 estima normas multilineales por maximización
alternante o malla finita. Sus comentarios de factibilidad global no son una
certificación del supremo. El estudio nuevo usa normas espectrales de matrices
completas, y aun así etiqueta su aritmética flotante como numérica.

## 3. Reducción exacta de la cadena a operadores

Fijar las hojas laterales unitarias produce contracciones A2,A3,A4 y no aumenta
`||Q_j A_j P_(j-1)||`. En el primer nodo basta representar su valor f por
`A1: K -> H1, A1(s)=sf`, con x=1 y P0=I. Entonces ||A1||=||f||<=1 y
||Q1 A1||<=eta por la clausura ambiental en las hojas. Recíprocamente,
`mu_j(z,s)=s A_j z`, con una hoja escalar unitaria, realiza cualquier cadena
lineal admisible; slots adicionales reciben gates de norma uno.

Es una equivalencia del supremo de la clase independiente de cadena, no una
equivalencia automática de árboles ramificados o leyes compartidas.

Definir F0=R0=x y
Fj=Aj F(j−1), Rj=Pj Aj R(j−1). Para ej=Fj−Rj,
`ej = Aj e(j−1) + dj`, `dj=Qj Aj R(j−1)`.
La raíz satisface `E^P=||P4 A4 e3||<=||e3||`. Toda e3 puede leerse sin pérdida
mediante una contracción de rango uno hacia Ran(P4), con clausura raíz cero.
Por tanto G4 es exactamente el supremo de ||e3|| para tres etapas activas.

## 4. Lema de dilatación que preserva el presupuesto global

Sea una cadena admisible arbitraria. Construir espacios ampliados
`H'_0=H0`, `H'_j=Hj direct-sum H'_(j−1)`. Sea pi_j la extracción de la primera
componente Hj. Tomar pi_0=I, P'_0=I y, recursivamente,

\[
B_j=A_j\pi_{j-1},\quad
V_j z=(B_jz,(I-B_j^*B_j)^{1/2}z),\quad
P'_j=P_j\oplus I. \tag{2}
\]

Como B_j es contractivo, la raíz cuadrada positiva existe y V_j*V_j=I:
**V_j es una isometría**. Además pi_j V_j=A_j pi_(j−1) y
pi_j P'_j=P_j pi_j. Las evaluaciones ampliadas F'_j,R'_j preservan en sus
primeras coordenadas F_j,R_j, respectivamente. En consecuencia
`||e3|| <= ||F'_3-R'_3||`.

Crucialmente, Q'_j=Q_j direct-sum 0 y

\[
Q'_j V_j P'_{j-1}=(Q_j A_j P_{j-1}\pi_{j-1},0),
\quad \|Q'_j V_j P'_{j-1}\|\le\eta. \tag{3}
\]

Para j=1 se interpreta P0=pi0=I. (3) es una identidad de operadores sobre
**todo** Ran(P'_(j−1)), incluidos los nuevos ejes retenidos. La dilatación no
introduce una condición de clausura sólo sobre la trayectoria. Los espacios
siguen siendo finitos y la clase permite leyes y proyectores independientes.

## 5. Cota superior mediante ángulos

Normalizar ||x||=1. Para la cadena isométrica, ||F'_j||=1. Si R'_j!=0,
definir r_j=||R'_j|| y theta_j como el ángulo real entre V_j R'_(j−1) y
R'_j. Ortogonalidad y (3) implican

\[
0\le\theta_j\le\arcsin\eta,\quad
r_j=r_{j-1}\cos\theta_j,\quad
r_3=\prod_{j=1}^3\cos\theta_j=:r. \tag{4}
\]

El ángulo real usa Re<.,.> en el caso complejo. Las isometrías preservan
ese ángulo. Por la desigualdad triangular de la distancia angular en la
esfera, el ángulo phi entre F'_3 y R'_3 satisface
`phi <= min(S,pi)`, donde S=theta1+theta2+theta3.

Supongamos primero S<=pi. Entonces

\[
\|F'_3-R'_3\|^2\le1+r^2-2r\cos S. \tag{5}
\]

Por concavidad de log cos en [0,pi/2),
`r <= cos(S/3)^3 =: b`. Si S<pi/2, también r>=cos S: la identidad de
cos(a+b), aplicada sucesivamente a ángulos no negativos con suma <pi/2,
da cos S<=prod cos theta_j. Por tanto la derivada en r de
`1+r²−2r cos S` es no negativa en [r,b]. Si S>=pi/2 la misma conclusión
se sigue de cos S<=0. En ambos casos (5) es <=`1+b²−2b cos S`.

Poner t=sin(S/3). Usando cos(3a)=4 cos³a−3 cos a,

\[
1+\cos^6(S/3)-2\cos^3(S/3)\cos S
=9t^2-15t^4+7t^6=:h(t^2). \tag{6}
\]

Aquí t<=eta, ya que S/3<=arcsin eta y S/3<=pi/3. Si z=t²,

\[
h'(z)=3(1-z)(3-7z),\qquad h(3/7)=81/49. \tag{7}
\]

Así el máximo admisible en esta región es h(min(eta²,3/7)).

Si S>=pi, Jensen da r<=cos(S/3)^3<=1/8 y
`||F'_3-R'_3||<=1+r<=9/8<9/7`. Esta región exige eta>=sin(pi/3),
por lo que el máximo 9/7 de (7) ya es admisible. Si algún R'_j=0, las
etapas posteriores mantienen R'=0 y el error es 1; una caída a cero desde
un R' no nulo exige eta=1, de modo que también queda cubierta por 9/7.
Los extremos theta_j=pi/2 se tratan así o por continuidad.

De §§3–5 se obtiene para la clase original entera

\[
G_4(\eta)^2\le h(\min\{\eta^2,3/7\}). \tag{8}
\]

No se ha supuesto dimensión dos, rango uno, saturación de normas ni
alineamiento de fuentes para deducir (8).

## 6. Testigo que alcanza la cota

P=diag(1,0), t=min(eta,sqrt(3/7)), c=sqrt(1−t²), x=1. Tomar

\[
A_1s=s(c,t)^T,\quad
A_2=A_3=\begin{pmatrix}c&-t\\t&c\end{pmatrix},\quad P_1=P_2=P_3=P.
\]

Las normas son 1, ||Q1 A1||=t, ||Qj Aj P||=t para j=2,3, sobre todo
el subespacio reducido. F3=(cos(3 arcsin t),sin(3 arcsin t)) y R3=c³e0,
por lo que

\[
e_3=(-3ct^2,3t-4t^3),\quad \|e_3\|^2=t^2(9-15t^2+7t^4).
\]

Tomar A4=e0 e3*/||e3||, P4=P. Tiene norma 1, clausura cero y lee
||e3|| exactamente. El lift bilineal de §3 verifica la admisibilidad
multilineal global, incluso en el primer nodo con hojas ambientales.
Esto alcanza (8) y prueba (1), sujeto a la revisión independiente del texto.

Los tres vectores fuente en el nivel 3 son, en orden de nacimiento,
`u1=t A3 A2 e1`, `u2=ct A3 e1`, `u3=c²t e1`. Son correlacionados;
su Gram completo, no sólo su diagonal, reconstruye ||e3||².

La región de igualdad usa ángulos locales iguales y una trayectoria planar
que satura la desigualdad angular. Es una familia suficiente de igualdad,
no una clasificación de todos los extremizadores y dilataciones posibles.

## 7. Estado de Gram y SDP exacto como problema variacional

Sea X_j=(R_j,u1,...,uj), con las fuentes transportadas hasta j.
Guardar GP_j=Gram(P_j X_j) y GQ_j=Gram(Q_j X_j). El Gram de X_j es
GP_j+GQ_j y el de sus partes separadas es diag(GP_j,GQ_j).

En la etapa j, con n=j y entrada X_(j−1) de longitud n, introducir
HP_j,HQ_j, ambos de tamaño 2n, Gram de las imágenes P_j A_j y Q_j A_j
de la lista `(P_(j−1)X_(j−1), Q_(j−1)X_(j−1))`. Imponer

\[
HP_j,HQ_j\succeq0,\quad
HP_j+HQ_j\preceq\operatorname{diag}(GP_{j-1},GQ_{j-1}),\quad
(HQ_j)_{PP}\preceq\eta^2 GP_{j-1}. \tag{9}
\]

Los selectores T_P,T_Q forman la siguiente lista: R nuevo es P A R;
cada fuente antigua es A(Pu+Qu); la última fuente es Q A R.
Así GP_j=T_P* HP_j T_P y GQ_j=T_Q* HQ_j T_Q, con matrices constantes
implementadas en `selectors`. Inicialmente GP0=[1],GQ0=[0]. Maximizar
`a*(GP3+GQ3)a`, a=(0,1,1,1), es un SDP afín.

**Necesidad**: (9) es la contractividad aplicada a todas las combinaciones
lineales de la lista; la última LMI es la clausura en todo su span proyectado.

**Suficiencia**: factorizar los Gram positivos en espacios ortogonales P y Q.
La desigualdad de Gram asegura que el mapa definido por la lista de imágenes
es consistente (todo vector nulo tiene imagen nula) y contractivo en el span.
La última LMI controla su bloque Q sobre todas las combinaciones de la lista P,
incluidas sus dependencias lineales. La suma de los spans P y Q es ortogonal,
y la extensión por cero fuera de ella conserva contractividad y clausura.
Se itera este argumento y se añade la lectura raíz de §3. No se ha impuesto
clausura sólo en R. Esto demuestra la equivalencia variacional exacta; **el
número que devuelve un solver flotante sigue sin ser una cota certificada**.

**Compresión de soporte**: en cada j comprimir ortogonalmente sobre
`W_j=span{R_j,P_j ui,Q_j ui:1<=i<=j}`. Es P_j-invariante, P_j uj=0,
Q_j R_j=0, y por tanto dim W_j<=2j (rango y corango <=j). Las leyes
`Pi_j A_j|W_(j−1)` preservan R y todas las fuentes, y no aumentan ni norma
ni clausura porque Pi_j conmuta con P_j. Para k4 basta soporte 2,4,6 antes
de la raíz. Se pueden añadir direcciones sin uso para proyectores propios.
Es una especialización con fuentes del teorema previo
`dimension_rank/fixed_tree_support_compression.tex`, no una afirmación de que
la compresión finita sea nueva en este repositorio.

## 8. Asintótica y referencia de fase

La familia de fase con lectura normal da |3eta−4eta³|. La lectura del error
completo de §6 mejora esa cota, y (1) da una función analítica en eta² cerca
de cero, lo que **justifica**, en lugar de suponer, la ausencia de términos
impares en C y del término de orden dos en E:

\[
C_{4,\mathrm{chain}}^P(\eta)=3-\tfrac52\eta^2+\tfrac18\eta^4+O(\eta^6),
\quad E=3\eta-\tfrac52\eta^3+O(\eta^5).
\]

Por tanto el coeficiente propuesto con prueba es a_chain=5/2. La sola
familia de fase habría dado únicamente a<=4. Como control independiente,
el argumento más débil `||e3||<=||e2||+eta||R2||` y M14 da
`C4<=1+W3<3`; no se usa para afirmar la igualdad de (1).

## 9. Evidencia ejecutada y comandos

El generador `scripts/run_pmt_k4_chain.py` escribe una carpeta nueva por
ejecución, nunca sobreescribe una corrida. Contiene configuración,
run_manifest.json, final_metrics.json, certificate.json, artifact_hashes.json,
candidatos completos, Gram, estados del solver y controles negativos.
La clasificación CERTIFIED_WITNESS se reserva a las familias definidas por
fórmulas con prueba de norma/clausura; las matrices flotantes que las
aproximan se verifican por separado con tolerancia declarada.

Consultar `EXECUTION.md` para comandos, entorno, resultados y limitaciones
de esta ejecución. No hay certificado numérico de redondeo dirigido del SDP;
la cota superior de (8) procede exclusivamente de la prueba analítica.

## 10. Literatura y fronteras

Comparación acotada, sin afirmación de novedad:

* Ryu–Hannah–Yin, *Scaled Relative Graph: Nonexpansive operators via 2D
  Euclidean Geometry*, https://arxiv.org/abs/1902.09788, §4.5, Theorem 7 y
  Fact 16: composición por geometría de módulos y ángulos; para dos
  operadores firmemente no expansivos aparece la región radial
  `r<=cos²(phi/2)`. Su Fact 17 contiene la desigualdad triangular esférica
  usada en §5. Este es un antecedente específico del mecanismo angular,
  no sólo una referencia general a proyecciones. La dilatación que conserva
  el presupuesto PMT (3) y el análisis del presupuesto eta requieren la
  comparación adicional de clases antes de cualquier afirmación de novedad.

* Vandenberghe–Boyd, *Semidefinite Programming* (1996),
  https://stanford.edu/~boyd/papers/sdp.html: marco de objetivos lineales y
  LMIs. No identifica la clase PMT ni prueba (1).
* Oikhberg, *Products of Orthogonal Projections* (1999),
  https://citeseerx.ist.psu.edu/document?doi=da32e7851730050b77f0aa22a26b6efaaaa86736&repid=rep1&type=pdf:
  factorización de contracciones por proyecciones. Su problema declarado es
  de representación y número de factores; aquí se controla el error tras
  tres etapas y un presupuesto global de fuga en cada una. No se ha hecho
  una auditoría exhaustiva de todas sus consecuencias ni de sus referencias.
* *Nearly Optimal Bounds for Cyclic Forgetting* (NeurIPS 2023),
  https://papers.nips.cc/paper_files/paper/2023/file/d72ae75abaa70a3b19c5d4f436c680d1-Paper-Conference.pdf:
  estudia productos de proyecciones y `A^m(I-A)`, una frontera relacionada
  que debe revisarse antes de atribuir novedad a la reducción angular.

La igualdad para topologías ramificadas exige otro argumento; el caso mixto
se aborda en §11 después de caracterizar la cadena. La
dilatación (2) usa un solo operador por etapa: no establece que una ley
bilineal contractiva admita un lift isométrico respecto de la norma producto.
No se extrapola (1) a esas topologías, leyes compartidas, dimensiones/rangos
fijados, proyectores oblicuos o límites de árboles crecientes.

## 11. Comparación posterior: topología mixta y frontera restante

Los árboles **binarios no planos** de cuatro nodos internos tienen tres
formas: cadena, mixto (un hijo con dos operaciones y otro con una), y
ramificación debajo de la raíz (dos operaciones hermanas, su padre y raíz).
La estrella de tres hijos internos tiene raíz ternaria y no pertenece a esa
lista binaria. Las siguientes conclusiones son adicionales y también
ADVISORY_PROOF_DRAFT.

**Mixto: misma constante que (1).** Dilatar por (2) las dos etapas de la
primera rama y la etapa de la segunda. Extender la ley bilineal raíz por las
extracciones pi de las coordenadas originales. Esto preserva exactamente
su error proyectado y no aumenta su norma. Escalarizar su salida en una
dirección unitaria produce una forma bilineal B de norma <=1. En los planos
reales de los pares de entrada escribir F_a,F_b unitarios, R_a=r_a v_a,
R_b=r_b v_b, con v_a,v_b unitarios y ángulos alfa,beta respecto de F_a,F_b.
La dualidad norma espectral/nuclear da

\[
|B(F_a,F_b)-B(R_a,R_b)|\le
\|F_aF_b^T-r_a r_b v_av_b^T\|_*.
\]

En bases ortonormales de esos planos, la norma nuclear al cuadrado es
`1+r²−2r cos(alfa)cos(beta)+2r sin(alfa)sin(beta)`
`=1+r²−2r cos(alfa+beta)`, donde r=r_a r_b. Esto sigue de
`||K||_*²=||K||_F²+2|det K|`, válido también en los casos de rango uno
por continuidad. Se usan planos reales incluso para una realización
compleja, aplicando Re<z,mu> como forma bilineal real; su norma sigue <=1.

Por la dilatación, alfa<=theta1+theta2, beta<=theta3,
`r=prod cos theta_j`. Cuando S=sum theta_j<=pi, alfa+beta<=S y la
monotonía de cos en [0,pi] da exactamente (5). Si S>=pi usar
`||K||_*<=1+r<=9/8` como antes. Así §§5–6 producen la misma cota superior.

Para alcanzarla tomar una rama de dos rotaciones (primera operación gated),
otra rama con valor (c,t), todos los proyectores de rango uno y el polar
de K como forma bilineal raíz de salida en e0. Los ángulos son 2theta y
theta, con 3theta<=3arcsin(sqrt(3/7))<pi, r=c³. El error es (6),
las normas son 1 y los defectos t,t,t,0. Este testigo **sí** se extiende
a leyes complejas multilineales por usar únicamente matrices y gates,
con iguales normas espectrales. `topology_witnesses.py` lo implementa.

**Ramificación debajo de raíz: igualdad aún abierta en este estudio.** La
misma familia de fase gated, con la lectura óptima del error del padre,
alcanza la cota inferior (1) sobre R². En el padre hay una ley bilineal
vectorial; no se ha demostrado que admita la dilatación isométrica usada
para operadores lineales. La cota superior segura es `1+W3(eta)`: el
transporte bilineal de los dos hijos tiene cota absoluta eta W3 por el
argumento nuclear M15, y el defecto local añade a lo sumo eta.

Para la clase compleja esa cota superior sigue siendo válida, pero no se
afirma que la multiplicación real del testigo conserve su norma al
complejificarla. La inferior real (1) no se transfiere automáticamente a
esa clase mediante esa construcción. La estrella ternaria queda sin
comparación exacta. No se declara diferencia de constantes entre topologías
ni igualdad general a partir de coincidencias numéricas.
