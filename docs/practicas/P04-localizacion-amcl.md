# P04 — Localización con AMCL y pose inicial

**Para quién es y cuándo leerlo**
Para el estudiante, en la cuarta sesión. Requiere tener ya un mapa propio (P03).
Es la práctica más conceptual: se mueve poco el robot y se piensa mucho.

---

**Duración:** 2 horas · **Requisitos previos:** P01, P02, P03 (con mapa construido)

## 1. Competencia

Aplica técnicas de localización probabilística sobre un mapa conocido, evalúa la
convergencia del estimador y diagnostica sus modos de fallo.

## 2. Objetivo

Al terminar, el estudiante será capaz de:

- explicar el funcionamiento de un filtro de partículas aplicado a localización;
- fijar correctamente la pose inicial y justificar por qué es necesaria;
- **medir experimentalmente la convergencia** de AMCL;
- provocar y diagnosticar el fallo de *robot secuestrado* y la ambigüedad por simetría;
- interpretar el árbol de transformadas `map → odom → base_footprint`.

## 3. Marco teórico

**El problema.** Dado un mapa y las lecturas de los sensores, ¿dónde está el robot? La
odometría sola no basta: deriva. El LiDAR ve paredes, pero muchas paredes se parecen entre
sí.

**AMCL** (*Adaptive Monte Carlo Localization*) mantiene una nube de **partículas**, cada
una una hipótesis de pose $(x, y, \theta)$. En cada ciclo:

1. **Predicción:** todas las partículas se mueven según la odometría, con ruido añadido.
2. **Corrección:** cada partícula compara el `/scan` real con el que *debería* ver desde su
   posición en el mapa. Las que concuerdan reciben más peso.
3. **Remuestreo:** se descartan las de poco peso y se duplican las de mucho.

Con el tiempo la nube **converge**: se concentra alrededor de la pose verdadera. Si el robot
está quieto, la nube apenas cambia — **AMCL necesita movimiento para converger**. Es el
resultado más contraintuitivo de esta práctica.

Lo "adaptativo" es que el número de partículas varía: muchas cuando hay incertidumbre,
pocas cuando ya está seguro.

**El árbol de transformadas.**

```
map → odom → base_footprint → base_link → laser
```

| Transformada | Quién la publica | Qué significa |
|---|---|---|
| `map → odom` | **AMCL** | La corrección: cuánto se ha equivocado la odometría |
| `odom → base_footprint` | EKF | Dónde cree el robot que está, integrando ruedas e IMU |
| `base_link → laser` | TF estática | Dónde está montado el LiDAR (aquí: 4,35 cm adelante, 11 cm de alto) |

**Clave:** AMCL **no** mueve el robot ni corrige la odometría. Publica una transformada que
dice "tu odometría está desviada esto". La pose en el mapa es la composición de ambas.

**Modos de fallo:**

| Fallo | Qué ocurre |
|---|---|
| **Pose inicial errónea** | AMCL busca donde no es; puede no recuperarse nunca |
| **Robot secuestrado** | Alguien lo levanta y lo mueve: la odometría no lo registra |
| **Ambigüedad por simetría** | Pasillos iguales: la nube se parte en dos grupos |
| **Mapa desactualizado** | El entorno cambió; las lecturas no casan |

## 4. Material

- Robot con el mapa de P03
- PC con dashboard
- Mando
- Cinta métrica y cinta adhesiva
- Cronómetro

## 5. Seguridad

> ⚠️ Lee [`README.md`](README.md) §4.

- En la parte E **levantarás el robot**. Hazlo con las dos manos, apagando antes el
  movimiento, y **no lo levantes con las ruedas girando**.
- El resto de la práctica es de teleoperación suave.

## 6. Procedimiento

### Parte A — Preparación (15 min)

**A.1** Aplica el perfil **con el mapa que construiste en P03**:

```bash
export R=http://<IP-DEL-ROBOT>:8091
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"lab_equipoN_intento1","control":"mando"}'
```

**A.2** Marca en el suelo con cinta un **punto de referencia A**, y anota sus coordenadas
aproximadas sobre el mapa.

**A.3** Coloca el robot exactamente en A, con una orientación conocida (por ejemplo,
mirando a la pared norte).

### Parte B — Pose sin inicializar (15 min)

**B.1** **Antes de fijar nada**, consulta la pose:

```bash
curl -s $R/map_pose | python3 -m json.tool
```

> 📝 **Anota la respuesta.** ¿Qué dice `localized`?

**B.2** Mira el dashboard: ¿dónde cree el robot que está? Compáralo con dónde está de
verdad.

> 📝 **Captura de pantalla.** Es la evidencia del "antes".

### Parte C — Fijar la pose y medir la convergencia (30 min) ⭐

**C.1** Fija la pose inicial en el dashboard: marca el punto A sobre el mapa y arrastra
para indicar la orientación.

Alternativa por terminal (con `yaw` en **radianes**):

```bash
curl -X POST $R/initialpose -H 'Content-Type: application/json' \
     -d '{"x":0.0,"y":0.0,"yaw":0.0}'
```

**C.2** **Sin mover el robot**, consulta la pose cada 10 s durante un minuto.

> 📝 **Tabla de 6 lecturas.** ¿Cambia algo? Anota tu observación.

**C.3** Ahora **teleopera despacio**: avanza 1 m, gira 90°, avanza 1 m más.

**C.4** Mientras se mueve, consulta la pose cada 5 s.

> 📝 **Tabla de lecturas durante el movimiento.** Cronometra: **¿cuánto tarda desde que
> empiezas a moverte hasta que la pose se estabiliza?**

**C.5** Observa la nube de partículas en el dashboard, si la interfaz la muestra.

> 📝 **Captura del antes y el después** de la convergencia.

> **Conclusión que debes verificar:** AMCL **no converge con el robot parado**. Necesita
> movimiento, porque la información viene de comparar predicción y observación a lo largo
> de una trayectoria.

### Parte D — Precisión de la localización (20 min)

**D.1** Marca un segundo punto **B** en el suelo, a una distancia **medida con cinta** del
punto A (p. ej., 2,00 m exactos).

**D.2** Lleva el robot de A a B teleoperando.

**D.3** Consulta la pose en B y anótala.

**D.4** Calcula la distancia euclídea entre las poses estimadas de A y B:

```
d = sqrt((x_B − x_A)² + (y_B − y_A)²)
```

> 📝 **Compara con la distancia real medida.** ¿Cuál es el error absoluto y el relativo?

**D.5** Repite el trayecto tres veces y calcula la dispersión.

### Parte E — Robot secuestrado (20 min)

> ⚠️ **Apaga el movimiento antes de levantar el robot.** Sujétalo con las dos manos.

**E.1** Con el robot bien localizado en B, **levántalo** y colócalo en el punto A, en la
misma orientación.

**E.2** Sin tocar nada más, consulta la pose.

> 📝 **¿Qué dice el robot? ¿Dónde cree estar?** Captura el dashboard.

**E.3** Teleopera despacio y observa durante un minuto.

> 📝 **¿Se recupera solo? ¿Cuánto tarda? ¿O necesita que le fijes la pose de nuevo?**

**E.4** Si no se recupera, fija la pose manualmente y comprueba que vuelve a funcionar.

### Parte F — Ambigüedad y TF (20 min) — *ampliación con SSH*

**F.1** Si el laboratorio tiene un pasillo o una zona simétrica, coloca el robot allí, fija
una pose deliberadamente ambigua y observa el comportamiento de la nube.

**F.2** Examina el árbol de transformadas:

```bash
ssh pi@yahboom.local
source /opt/ros/melodic/setup.bash
rosrun tf view_frames       # genera frames.pdf
rosrun tf tf_echo /map /base_footprint
```

> 📝 **Anota la transformada `map → base_footprint`** y compárala con la pose que da
> `/map_pose`.

**F.3** Observa la corrección que aplica AMCL:

```bash
rosrun tf tf_echo /map /odom
```

> 📝 **Esta transformada es la corrección de AMCL.** Si vale casi cero, la odometría va
> bien. Anota su valor y explica qué significa.

## 7. Resultados a reportar

1. Pose **antes** de inicializar (respuesta y captura).
2. Tabla de 6 lecturas con el robot parado.
3. Tabla de lecturas durante el movimiento, con el **tiempo de convergencia**.
4. Capturas de la nube de partículas antes y después.
5. **Tabla de precisión** (parte D): tres trayectos A→B con error absoluto y relativo.
6. Resultado del experimento de secuestro, con capturas y tiempo de recuperación.
7. *(Si se hizo F)* Valor de `map → odom` con su interpretación.

## 8. Preguntas de análisis

1. En C.2 el robot estaba parado y la pose apenas cambiaba; en C.4, moviéndose, convergió.
   **Explica por qué AMCL necesita movimiento.** Relaciónalo con los pasos de predicción y
   corrección.
2. AMCL publica `map → odom` y **no** corrige la odometría directamente. **¿Por qué está
   diseñado así?** ¿Qué ventaja tiene separar ambas transformadas?
3. En el experimento de secuestro, ¿se recuperó el robot? **Explica qué hipótesis maneja el
   filtro** en ese momento y por qué es un caso difícil.
4. Tu medición de precisión dio un error. **Distingue** entre el error de la *estimación*
   de AMCL y el error de *tu medición* con cinta métrica. ¿Cómo los separarías
   experimentalmente?
5. Si el laboratorio tuviera dos pasillos idénticos, AMCL podría converger al equivocado.
   **Propón dos formas** de resolver esa ambigüedad: una que use sólo el LiDAR y otra que
   use otro sensor.

## 9. Rúbrica

| Criterio | Peso | Excelente | Suficiente | Insuficiente |
|---|---:|---|---|---|
| Medición de convergencia | 25 % | Tablas completas con tiempo medido y método claro | Tablas incompletas | Sin datos |
| Precisión (parte D) | 20 % | Tres trayectos con errores calculados y dispersión | Un trayecto | Ausente |
| Experimento de secuestro | 20 % | Ejecutado con seguridad, documentado y explicado | Ejecutado sin analizar | No realizado |
| Análisis (preguntas) | 25 % | Fundamenta con la teoría del filtro | Responde sin profundizar | No responde |
| Seguridad | 10 % | Levanta el robot correctamente, sin riesgos | Con recordatorios | Manipulación insegura |

---

**Anterior:** [P03](P03-mapeo-slam.md) · **Siguiente:** [P05 — Navegación autónoma](P05-navegacion-autonoma.md)
