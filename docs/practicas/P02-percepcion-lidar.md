# P02 — Percepción con LiDAR: `/scan` y costmaps

**Para quién es y cuándo leerlo**
Para el estudiante, en la segunda sesión con el robot.
Requiere haber hecho P01: se supone que ya sabes arrancar el sistema y aplicar un perfil.

---

**Duración:** 2 horas · **Requisitos previos:** P01

## 1. Competencia

Analiza los datos de un sensor LiDAR 2D, comprende cómo se transforman en una
representación del entorno navegable (*costmap*), y **determina experimentalmente los
límites físicos del sensor**.

## 2. Objetivo

Al terminar, el estudiante será capaz de:

- interpretar un mensaje `sensor_msgs/LaserScan`;
- explicar qué es un *costmap* y qué son las capas de obstáculos e inflado;
- relacionar la geometría del robot (*footprint*) con la distancia de seguridad;
- **demostrar experimentalmente qué obstáculos NO detecta un LiDAR 2D** y argumentar por
  qué eso motiva la fusión sensorial.

## 3. Marco teórico

**El LiDAR 2D.** Un RPLIDAR A1 gira a ~5-10 Hz emitiendo un haz láser y midiendo el tiempo
de vuelta. Produce un `LaserScan`: un vector de distancias, una por ángulo, sobre **un
único plano horizontal**. Los campos importantes son `angle_min`, `angle_max`,
`angle_increment`, `range_min`, `range_max` y `ranges[]`. Un valor `inf` significa "no
detecté nada hasta el alcance máximo".

**Ésta es la clave de la práctica:** el sensor ve **una rebanada del mundo**, no el mundo.
En este robot, el LiDAR está a **11 cm del suelo**. Todo lo que no corte ese plano es
invisible.

**El costmap.** `move_base` mantiene una rejilla donde cada celda tiene un *coste*: libre,
ocupada, o "cerca de algo ocupado". Se construye por capas:

| Capa | Qué hace |
|---|---|
| `static_layer` | El mapa guardado (paredes conocidas) |
| `obstacle_layer` | Lo que el LiDAR ve **ahora**: marca ocupado y **limpia** lo que ya no está |
| `inflation_layer` | Engorda los obstáculos con un radio de seguridad |

Hay dos costmaps: el **global** (todo el mapa, para planificar la ruta) y el **local**
(una ventana de 3 × 3 m que se mueve con el robot, para esquivar).

**La inflación y el *footprint*.** El robot no es un punto: mide unos 23 × 20 cm
(`footprint` ±0.117 × ±0.100 m). Si el planificador tratara al robot como un punto, lo
haría rozar las paredes. La capa de inflado añade un margen —aquí, `inflation_radius: 0.30`
m— de modo que el centro del robot nunca se acerque más de esa distancia a un obstáculo.

**Parámetros de este robot** (`misiones/pilotada/robot/nav/sf_costmap_common.yaml`):

```yaml
obstacle_range: 3.0       # hasta 3 m se marcan obstáculos
raytrace_range: 3.5       # hasta 3,5 m se limpian celdas libres
inflation_radius: 0.30
observation_sources: scan # UNA sola fuente: el LiDAR
```

> Fíjate en la última línea: **hay una sola fuente de obstáculos**. La cámara RGB-D del
> robot no contribuye. Volverás sobre esto en la parte D.

## 4. Material

- Robot SafeVision con perfil `pilotada` aplicado
- PC con dashboard
- **Objetos de prueba:**
  - una caja de cartón de ~30 cm de alto
  - una silla o mesa baja **con patas finas** y superficie a ~40 cm
  - un objeto plano y bajo (un libro, una regla gruesa)
  - opcional: algo con superficie de cristal o espejo
- Cinta métrica y cinta adhesiva para marcar el suelo

## 5. Seguridad

> ⚠️ Lee [`README.md`](README.md) §4.

- En esta práctica el robot **casi no se mueve**: la mayoría son mediciones estáticas.
- En la parte D acercarás objetos al robot: hazlo con el robot **parado**.
- Mantén el mando a mano.

## 6. Procedimiento

### Parte A — Preparación (10 min)

**A.1** Arranca el sistema y aplica el perfil (P01, parte B):

```bash
export R=http://<IP-DEL-ROBOT>:8091
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"<MAPA>","control":"mando"}'
```

**A.2** Verifica que el LiDAR publica:

```bash
curl -s $R/runtime/status | python3 -m json.tool | grep -A3 '"lidar"'
```

*Esperado:* `"active": true`.

**A.3** Escucha el LiDAR: debe girar de forma audible y constante.

### Parte B — Anatomía de un `/scan` (25 min) — *requiere SSH*

**B.1** Conéctate al robot:

```bash
ssh pi@yahboom.local
source /opt/ros/melodic/setup.bash
```

**B.2** Mide la frecuencia:

```bash
rostopic hz /scan
```

> 📝 **Anota la frecuencia media.** Déjalo 20 s y haz `Ctrl+C`.

**B.3** Captura un mensaje y examina la cabecera:

```bash
rostopic echo -n 1 /scan | head -20
```

> 📝 **Anota:** `angle_min`, `angle_max`, `angle_increment`, `range_min`, `range_max`.

**B.4** Calcula:
- Número de medidas por barrido = (`angle_max` − `angle_min`) / `angle_increment`
- Resolución angular en grados = `angle_increment` × 180/π

> 📝 **Anota ambos resultados** y compáralos con el tamaño real de `ranges[]`.

**B.5** *Experimento dirigido.* Coloca la caja de cartón exactamente **a 1 m frente al
robot**, medida con cinta métrica. Captura un barrido y busca el valor mínimo:

```bash
rostopic echo -n 1 /scan/ranges | tr ',' '\n' | grep -v inf | sort -n | head -5
```

> 📝 **Anota el valor mínimo y compáralo con 1,00 m.** ¿Cuál es el error?

### Parte C — El costmap (25 min)

**C.1** En el dashboard, abre la vista de mapa con el robot localizado.

**C.2** Coloca la caja a ~1 m del robot, en un punto libre del mapa.

**C.3** Observa el costmap local en la interfaz.

> 📝 **Captura de pantalla.** Identifica: la caja marcada como obstáculo, y el halo de
> inflado a su alrededor.

**C.4** Retira la caja y observa cómo la celda se **limpia** (*raytracing*).

> 📝 **Anota cuánto tarda** en desaparecer.

**C.5** Acerca la caja progresivamente (1,0 m → 0,5 m → 0,3 m) y observa cómo el halo de
inflado se aproxima al robot.

> 📝 **¿A qué distancia el inflado alcanza la posición del robot?** Relaciónalo con
> `inflation_radius: 0.30`.

### Parte D — Los límites del LiDAR 2D (40 min) ⭐

**Es el núcleo de la práctica.** Con el robot **parado** y el costmap a la vista, presenta
cada objeto a 1 m y anota si aparece.

**D.1** Rellena la tabla:

| # | Objeto | Altura aproximada | ¿Corta el plano a 11 cm? | ¿Aparece en el costmap? |
|---|---|---|---|---|
| 1 | Caja de cartón (30 cm) | | | |
| 2 | **Mesa/silla de patas finas** (superficie a 40 cm) | | | |
| 3 | Libro plano en el suelo (~3 cm) | | | |
| 4 | Pierna de una persona | | | |
| 5 | Mochila en el suelo | | | |
| 6 | *(opcional)* Superficie de cristal o espejo | | | |

> ⚠️ **Para el objeto 2, colócalo de forma que las patas queden fuera del haz** (por
> ejemplo, presentando el robot al voladizo de la mesa). Es el caso interesante.

**D.2** Para cada objeto que **no** aparezca, explica por qué.

**D.3** *Demostración final (con el mando en la mano y el dedo listo).* Coloca el objeto 2
de forma que su superficie quede en la trayectoria del robot pero sus patas no. Teleopera
el robot **muy despacio** hacia él.

> ⚠️ **Detén el robot antes del contacto.** El objetivo es **ver que el costmap sigue
> vacío**, no chocar.

> 📝 **Captura del costmap vacío** mientras hay un obstáculo real delante. Es la evidencia
> más valiosa de la práctica.

**D.4** *(Opcional, si hay espejo)* Anota qué ocurre con superficies reflectantes: el láser
puede rebotar y dar lecturas falsas o `inf`.

## 7. Resultados a reportar

1. Frecuencia de `/scan` y los cinco parámetros de cabecera.
2. Cálculo del número de medidas y la resolución angular.
3. Medición de la caja a 1 m y el error obtenido.
4. Capturas del costmap: con obstáculo, sin obstáculo, y con el inflado cerca del robot.
5. **Tabla completa de la parte D**, con la explicación de cada caso.
6. **Captura del costmap vacío con un obstáculo alto presente** (D.3).

## 8. Preguntas de análisis

1. El LiDAR está a 11 cm del suelo. **Dibuja un esquema lateral** del robot frente a una
   mesa de 40 cm con patas finas, marcando el plano del haz. Explica geométricamente por
   qué no la detecta.
2. `inflation_radius` vale 0,30 m y el robot mide 23 × 20 cm. **¿Por qué el radio es mayor
   que el robot?** ¿Qué pasaría con 0,05 m? ¿Y con 1,0 m?
3. La `obstacle_layer` no sólo marca: también **limpia** (`raytrace_range: 3.5`).
   **¿Por qué es necesario limpiar?** ¿Qué ocurriría si sólo marcara?
4. En el costmap local hay una ventana de 3 × 3 m con `rolling_window`. **¿Por qué no usar
   el mapa completo** para esquivar obstáculos?
5. A partir de la tabla de la parte D: **¿qué sensor añadirías** para cubrir los casos no
   detectados? El robot ya lleva una cámara RGB-D montada cuyo canal de profundidad no se
   usa. Describe en tres o cuatro líneas cómo la integrarías y qué riesgo tendría.

> La pregunta 5 no es retórica: es exactamente la decisión de alcance que documenta
> [`../analisis-alcance.md`](../analisis-alcance.md) §4. Compara tu respuesta con la
> recomendación de ese documento.

## 9. Rúbrica

| Criterio | Peso | Excelente | Suficiente | Insuficiente |
|---|---:|---|---|---|
| Análisis del `/scan` | 20 % | Parámetros correctos y cálculos bien hechos | Datos presentes con errores menores | Sin datos |
| Comprensión del costmap | 20 % | Identifica capas e inflado en sus capturas | Identifica el obstáculo pero no el inflado | No interpreta |
| **Tabla de límites (D)** | 30 % | Tabla completa con explicación geométrica de cada caso | Tabla completa sin explicar | Incompleta |
| Análisis (preguntas) | 20 % | Fundamenta y propone una solución razonada en P5 | Responde sin profundizar | No responde |
| Seguridad | 10 % | Cumple sin recordatorios | Necesita recordatorios | Pone en riesgo al equipo |

---

**Anterior:** [P01](P01-arranque-teleoperacion.md) · **Siguiente:** [P03 — Mapeo SLAM](P03-mapeo-slam.md)
