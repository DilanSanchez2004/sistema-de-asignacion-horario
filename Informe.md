# Informe — Sistema de asignación de horarios

> * borrador inicial.
> * En este borrador se habla de el **núcleo del problema** (modelo, restricciones, formulación) y los algoritmos de **búsqueda por amplitud** y **costo uniforme**.
> Lo que esta como (pendiente)* es lo que falta implementar.

---

* Santiago Andrey Morales Valencia - 2380753  
* 
* 

---

## 1. Introducción

El objetivo del proyecto es armar automáticamente el horario de una institución:
decidir **qué día, a qué hora y en qué salón** se dicta cada clase, de modo que no
haya choques (un mismo profesor, un grupo o salón en dos lugares a la vez) intentando respetar las preferencias de los profesores y que no se sobrecargue a los grupos.

Para resolverlo, planteamos el problema como una **búsqueda en un árbol**: la idea es partir de un
horario vacío y poco a poco ir ubicando una clase a la vez hasta tener el horario completo.

---

## 2. Datos del problema

| Elemento   | Qué representa                                        | Ejemplo                    |
|------------|-------------------------------------------------------|----------------------------|
| `Franja`   | Un bloque de horas dentro del día (sin el día)        | `07:00-09:00`              |
| `Salon`    | Un salón disponible                                   | `S1`                       |
| `Profesor` | Un docente y las franjas en las que **no** puede dictar | `Prof_A`, no puede Lunes 07:00 |
| `Clase`    | Una sesión que hay que programar (materia, profesor, grupo) | Cálculo, Prof_A, G1   |

Si una materia tiene varias sesiones a la semana, cada sesión se trata como una `Clase`
distinta (por ejemplo `Calculo-1` y `Calculo-2`).

---

## 3. Representación del estado

La idea es sencilla: **un estado es un horario a medio construir.**

Se representa como una lista con una posición por cada clase. En cada posición hay:

- la **asignación** de esa clase, es decir, la tripleta $(\text{día},\ \text{franja},\ \text{salón})$, o
- `None` si esa clase todavía no se ha ubicado.

Formalmente, si hay $n$ clases:

$$
\text{Estado} = (a_1, a_2, \dots, a_n), \qquad
a_i =
\begin{cases}
\text{None} & \text{si la clase } i \text{ aún no se ha ubicado} \\
(d,\ f,\ s) & \text{si ya se ubicó}
\end{cases}
$$

donde $d$ es un día de $D$ (conjunto de días), $f$ una franja de $F$ (conjunto de franjas)
y $s$ un salón de $S$ (conjunto de salones).

Dicho de otra forma: el conjunto de **todas las tripletas posibles** se escribe
$D \times F \times S$ (todas las combinaciones de un día, una franja y un salón), y cada
posición del estado toma **un valor de ese conjunto o el valor `None`**. Por eso también se
puede escribir de forma compacta como $a_i \in \{\text{None}\} \cup (D \times F \times S)$,
donde la unión $\cup$ significa simplemente “o una cosa o la otra”.

**Ejemplo** con 4 clases, después de dos pasos:

```
( (Lunes, 07:00-09:00, S1),  (Lunes, 09:00-11:00, S1),  None,  None )
     Cálculo                    Álgebra                  Física Química
```

### Elementos del problema

| Elemento            | Definición                                                                 |
|---------------------|----------------------------------------------------------------------------|
| **Estado inicial**  | Todas las posiciones en `None` (horario vacío).                            |
| **Operador**        | Asignar a la siguiente clase libre una tripleta (día, franja, salón).      |
| **Sucesores**       | Solo se generan las asignaciones que **no** producen choques.             |
| **Prueba de meta**  | Ninguna posición es `None` (todas las clases quedaron ubicadas).           |
| **Costo**           | Cada asignación cuesta 1 más una penalización si incumple alguna preferencia (ver sección 5). |

### ¿Por qué esta representación?

- **Es fácil de entender y de verificar:** Si miramos la posición $i$ vamos a saber dónde quedó la clase $i$.
- **Cada clase se asigna exactamente una vez** por cómo está construida la lista; no hace falta revisarlo aparte.
- **Los estados no se pueden modificar después de creados** (son inmutables). Cada paso genera un estado nuevo, así que dos nodos del árbol nunca se “pisan” entre sí. Esto también permite compararlos y guardarlos en conjuntos.
- **Las clases se asignan siempre en el mismo orden** (primero la clase 1, luego la 2, …). Entonces a cada horario se llega por un único camino y no aparecen estados repetidos que solo cambian el orden en que se ubicaron las clases.

---

## 4. Restricciones

### 4.1 Restricciones duras (nunca se pueden romper)

En una misma franja **del mismo día**:

1. Un **salón** no puede tener dos clases.
2. Un **profesor** no puede dictar dos clases.
3. Un **grupo** no puede tener dos clases.
4. Cada clase se programa **exactamente una vez** (lo garantiza la representación).

Estas restricciones se aplican **al generar los sucesores**: si una asignación produce un
choque, ese hijo simplemente no se crea. Por eso todo horario completo que encuentre la búsqueda ya es válido.

### 4.2 Restricciones blandas (se pueden romper, pero cuestan)

| Restricción                                                   | Penalización |
|---------------------------------------------------------------|:------------:|
| (a) El profesor dicta en una franja que marcó como no disponible | $+5$ por cada clase |
| (b) Un grupo tiene más de $N$ clases seguidas el mismo día      | $+3$ por cada clase que pase el límite |

Para la (b), si un grupo tiene una racha de $r$ clases seguidas y el máximo permitido es $N$,
el exceso de esa racha es $\max(0,\ r - N)$. Por ejemplo, con $N = 2$ y cuatro clases seguidas,
el exceso es $2$ y la penalización es $2 \times 3 = 6$.

### 4.3 Detalle de implementación: revisión rápida de choques

Antes de generar los hijos de un nodo, se construye **una sola vez** un índice (`Ocupacion`)
con lo que ya está ocupado: qué salones, profesores y grupos están usados en cada día y franja.
Con ese índice, comprobar si un candidato choca es una consulta directa en un conjunto, sin
recorrer todo el horario cada vez.

Además existe una función de **verificación independiente** (`verificar_completo`) que revisa
todas las restricciones duras comparando las clases de dos en dos. No depende de cómo se generan
los sucesores, así que la usamos en las pruebas para comprobar que los algoritmos no se equivocan.

---

## 5. Función de costo

Cada paso (ubicar una clase) cuesta:

$$
c(\text{paso}) = 1 + \text{penalización blanda que genera ese paso}
$$

Por lo tanto, el costo total $g$ de un horario completo es:

$$
g(\text{horario}) = n + P
$$

donde $n$ es el número de clases y $P$ la penalización total por restricciones blandas.

Como $n$ es igual para todos los horarios completos, **minimizar $g$ es lo mismo que minimizar
las violaciones de preferencias.** Un costo de $g = n$ significa un horario perfecto, sin
penalizaciones.

> **Justificación:** el costo base de 1 hace que todos los pasos cuesten algo positivo, que es
> justo lo que necesita la búsqueda de costo uniforme para funcionar bien. Los pesos (5 y 3)
> reflejan que es más grave poner a un profesor en un horario donde no puede que darle a un
> grupo una clase seguida de más. Los pesos se pueden cambiar al crear el problema.

---

## 6. Espacio de búsqueda

- **Factor de ramificación** $b$: cuántos hijos puede tener un nodo como máximo. Es el número de
  tripletas posibles:

$$
b = |D| \times |F| \times |S|
$$

- **Profundidad de la solución** $d$: siempre igual al número de clases, $d = n$, porque cada
  nivel del árbol ubica una clase.

- **Tamaño máximo del árbol** (si no se descartara ningún choque):

$$
1 + b + b^2 + \dots + b^n = \sum_{k=0}^{n} b^k \approx b^n
$$

**Ejemplo:** con 2 días, 3 franjas y 2 salones, $b = 2 \times 3 \times 2 = 12$. Con 4 clases,
el árbol completo tendría $\sum_{k=0}^{4} 12^k = 22\,621$ nodos. Gracias a que los choques se
descartan al generar los hijos, en la práctica BFS crea solo $9\,013$ nodos (≈ 40 %).

El tamaño crece **exponencialmente** con el número de clases: agregar una clase multiplica el
árbol aproximadamente por $b$. Por eso estos algoritmos solo son prácticos en instancias pequeñas,
y se agregaron **límites de nodos (200 000) y de tiempo (30 s)** para que la interfaz no se congele.

---

## 7. Algoritmos implementados

Ambos algoritmos siguen las reglas que vimos en clase:

- La **prueba de meta** se hace al **sacar** un nodo de la frontera (al expandirlo), no al crearlo.
- **Nodos expandidos** = nodos sacados de la frontera, incluido el nodo meta.
- **Nodos creados** = nodos que entran al árbol, incluida la raíz.
- Si se alcanza un límite, el resultado indica el motivo (`limite_nodos` o `limite_tiempo`);
  si el árbol se agota sin encontrar meta, el motivo es `sin_solucion`.

### 7.1 Búsqueda preferente por amplitud (BFS)

Explora el árbol **por niveles**: primero todos los horarios con 1 clase ubicada, luego todos
los de 2, y así sucesivamente. Usa una **cola FIFO** (el primero que entra es el primero que sale).

- **Completa:** si existe un horario válido, lo encuentra.
- **No es óptima en este problema:** BFS no mira los costos, así que devuelve el *primer*
  horario válido que encuentra, aunque tenga penalizaciones. Solo sería óptima si todos los
  pasos costaran lo mismo.
- **Complejidad:** tiempo y memoria $O(b^d)$.

### 7.2 Búsqueda de costo uniforme (UCS)

Siempre expande el nodo con **menor costo acumulado $g$**. Usa una **cola de prioridad**.

- **Completa y óptima:** como todos los pasos cuestan al menos 1, el primer horario completo
  que sale de la frontera es el de **menor costo**, en otras plabras el que menos preferencias incumple.
- Cuando dos nodos tienen el mismo costo, se desempata por orden de llegada, así que el
  resultado es siempre el mismo al repetir la búsqueda.
- Si no hay restricciones blandas (todos los pasos cuestan 1), se comporta igual que BFS.
- **Complejidad:** $O\!\left(b^{\,1 + \lfloor C^*/\varepsilon \rfloor}\right)$, donde $C^*$ es el
  costo de la solución óptima y $\varepsilon = 1$ el costo mínimo de un paso.

---

## 8. Heurísticas *(pendiente)*

> Aqui va la explicacion de la implementacion de A* y las heurísticas
> (`heuristicas.py`). Se sugiere incluir: qué estima cada heurística, por qué es admisible
> y cómo se compara con costo uniforme.

---

## 9. Pruebas

Las pruebas automáticas están en `test_parte_a.py` y se ejecutan con:

```bash
python -m unittest test_parte_a
```

### 9.1 Pruebas del núcleo y de BFS / costo uniforme

| Prueba | Qué comprueba |
|--------|---------------|
| `test_estado_inicial_y_sucesores_legales` | El estado inicial no es meta y genera $2 \times 3 \times 2 = 12$ hijos, cada uno con costo 1. |
| `test_no_se_generan_conflictos` | Una clase del mismo profesor no se ubica en la misma franja y día, pero sí en la misma franja otro día. |
| `test_valores_legales_y_variable_dinamica` | Los valores legales se reducen al ir asignando, y se puede elegir qué clase asignar (útil para otras estrategias). |
| `test_bfs_y_ucs_encuentran_horario_valido` | Ambos algoritmos encuentran un horario y este pasa la verificación independiente sin errores. |
| `test_bfs_expande_por_niveles` | Con 1 clase, BFS expande 2 nodos y crea 7 (raíz + 6 hijos), como se espera. |
| `test_sin_solucion` | Si es imposible (2 clases del mismo profesor y 1 sola franja), ambos responden `sin_solucion`. |
| `test_limite_de_nodos` | Al alcanzar el límite de nodos, la búsqueda se detiene e informa `limite_nodos`. |
| `test_ucs_optimo_blandas_no_disponible` | UCS evita las franjas no disponibles del profesor y logra costo 4 (sin penalización). |
| `test_ucs_menor_o_igual_que_bfs` | El costo de UCS nunca es mayor que el de BFS. |
| `test_ucs_es_el_minimo_global_por_fuerza_bruta` | Se prueban **todas** las combinaciones posibles y el mejor costo coincide con el de UCS. |
| `test_costo_acumulado_igual_a_costo_total` | El costo sumado paso a paso es igual al costo calculado sobre el horario final. |

Resultado: **todas las pruebas pasan.**

### 9.2 Resultados de las pruebas

Las pruebas usan una instancia pequeña: 4 clases, 2 profesores, 2 grupos, 2 días, 3 franjas
y 2 salones. Como hay 4 clases, un costo de $g = 4$ significa un horario **sin ninguna
penalización**.

| Prueba | Costo BFS | Costo UCS | Nodos creados BFS | Nodos creados UCS |
|---|:---:|:---:|---:|---:|
| `encuentran_horario_valido` (sin preferencias) | 4 | 4 | 9 013 | 9 013 |
| `optimo_blandas_no_disponible` | 14 | **4** | 9 013 | 645 |
| `menor_o_igual_que_bfs` | 20 | **4** | 9 013 | 1 441 |
| `costo_acumulado_igual_a_costo_total` | 20 | **4** | 9 013 | 2 885 |
| `minimo_global_por_fuerza_bruta` | 9 | **9** | 223 | 159 |

En las demás pruebas: `sin_solucion` responde correctamente que no hay horario posible,
`limite_de_nodos` se detiene al llegar al límite, y `expande_por_niveles` crea los 7 nodos
esperados (la raíz y sus 6 hijos).

---

## 10. Análisis de resultados

1. **Los dos algoritmos siempre entregan horarios válidos.** En todas las pruebas donde existe
   solución, el horario encontrado pasa la verificación independiente sin ningún choque. Esto
   confirma que descartar los choques al generar los hijos funciona correctamente.

2. **BFS encuentra un horario válido, pero no el mejor.** Cuando hay preferencias que respetar,
   BFS devuelve el primer horario completo que encuentra sin importar su costo. Por ejemplo, en
   `optimo_blandas_no_disponible` pone a Prof_A dos veces en franjas donde no puede
   (penalización 10), y en `menor_o_igual_que_bfs` además deja a los dos grupos con clases
   seguidas (penalización 16).

3. **Costo uniforme sí encuentra el mejor horario.** En esas mismas pruebas, UCS logra
   penalización **0** ($g = n = 4$). La prueba de **fuerza bruta** lo confirma: se revisaron
   las $6^4 = 1\,296$ combinaciones posibles, de las cuales solo 120 son válidas, y el menor
   costo entre ellas es 9, exactamente el que encontró UCS. En ese caso **no existe un horario
   perfecto**: Prof_A tiene dos clases y solo una franja disponible, así que una penalización
   de 5 es inevitable. Ahí BFS también llegó a costo 9, pero por casualidad, no porque lo
   garantice.

4. **Sin preferencias, BFS y UCS hacen lo mismo.** En `encuentran_horario_valido` todos los
   pasos cuestan 1, así que UCS se comporta igual que BFS: mismos nodos y mismo resultado.

5. **UCS además exploró menos nodos.** Cuando hay preferencias, UCS siempre creó menos nodos
   que BFS, **hasta 14 veces menos** (645 contra 9 013). La razón es que BFS revisa niveles
   completos del árbol antes de llegar al último, mientras que UCS avanza primero por los
   caminos baratos y, si existe un horario perfecto, lo alcanza pronto. Si todas las
   soluciones fueran caras, esta ventaja sería menor.

6. **Los casos límite se manejan bien.** Cuando no hay solución posible, ambos algoritmos
   recorren el árbol completo (solo 3 nodos, porque los choques se detectan enseguida) y
   responden `sin_solucion`. Cuando se alcanza el límite de nodos, la búsqueda se detiene y lo
   informa, en lugar de quedarse colgada.

7. **El costo calculado es correcto.** En `costo_acumulado_igual_a_costo_total`, el costo que
   cada algoritmo fue sumando paso a paso coincide con el costo recalculado sobre el horario
   final (20 para BFS y 4 para UCS).

8. **El tamaño del árbol crece muy rápido.** Con 1 clase se crean 7 nodos; con 4 clases, más de
   9 000. En teoría el árbol completo con 4 clases tendría 22 621 nodos, y descartar los choques
   lo redujo a cerca del 40 %. Aun así, cada clase extra multiplica el árbol aproximadamente
   por $b$, por lo que BFS y UCS solo sirven para instancias pequeñas y para problemas reales
   hacen falta estrategias informadas (sección 8).

---

## 11. Conclusiones (aporte parcial)

- La representación del estado como una lista de asignaciones, con una posición por clase, es
  simple, evita estados repetidos y facilita verificar los resultados.
- Separar las restricciones en **duras** (se descartan al generar) y **blandas** (se cobran en
  el costo) permite que los algoritmos que usan costos busquen el horario que mejor respeta
  las preferencias.
- **Costo uniforme** es la mejor opción de las dos búsquedas no informadas para este problema:
  garantiza el horario con menos penalizaciones. **BFS** solo garantiza un horario válido.
- Ambos algoritmos tienen un costo exponencial, lo que motiva el uso de búsquedas informadas.

> *(pendiente)* Conclusiones generales del grupo, comparación con profundidad iterativa y A*,
> y comentarios sobre la interfaz y el cargador de datos.

---

## 12. Organización del código (aporte parcial)

| Archivo | Contenido |
|---|---|
| `modelo.py` | Datos del problema (`Franja`, `Salon`, `Profesor`, `Clase`), estado (`Estado`, `Asignacion`, `Operador`), árbol (`Nodo`) y `Resultado`. |
| `restricciones.py` | Restricciones duras y blandas, índice de ocupación y verificación independiente. |
| `problema.py` | Formulación del problema: estado inicial, sucesores, prueba de meta y costo. |
| `busquedas.py` | Algoritmos de búsqueda (BFS y costo uniforme en este aporte). |
| `test_parte_a.py` | Pruebas automáticas. |

> *(pendiente)* `cargador.py`, `interfaz.py`, `heuristicas.py` y los demás algoritmos.
