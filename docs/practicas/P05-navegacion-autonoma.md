# P05 — Navegación autónoma y evasión de obstáculos

**Para quién es y cuándo leerlo**
Para el estudiante, en la quinta sesión. Es la práctica donde el robot **se mueve solo**:
la que más disciplina de seguridad exige.
Requiere P01-P04.

---

**Duración:** 2-3 horas · **Requisitos previos:** P01, P02, P03, P04

## 1. Competencia

Configura y opera un sistema de planificación de trayectorias en dos niveles, evalúa el
comportamiento del planificador local ante obstáculos imprevistos y determina los límites de
la evasión basada en un sensor 2D.

## 2. Objetivo

Al terminar, el estudiante será capaz de:

- distinguir planificación **global** y **local**, y explicar por qué hacen falta ambas;
- enviar objetivos de navegación y encadenarlos en una cola;
- **evaluar experimentalmente** la evasión de obstáculos dinámicos;
- explicar los comportamientos de recuperación (*recovery*);
- **documentar con evidencia** el caso en que la evasión falla, y proponer la solución.

## 3. Marco teórico

**Dos niveles.** Navegar no es un solo problema:

| Nivel | Quién | Qué resuelve | Con qué |
|---|---|---|---|
| **Global** | *global planner* | La ruta completa desde donde estoy hasta el objetivo | Costmap global (mapa estático + obstáculos conocidos) |
| **Local** | **DWA** | Qué velocidad mando **ahora mismo** | Costmap local (ventana 3×3 m que sigue al robot) |

El global traza la ruta una vez (y la replanifica si algo cambia mucho); el local decide 20
veces por segundo qué hacer con lo que ve ahora.

**DWA** (*Dynamic Window Approach*). En cada ciclo:

1. Toma el conjunto de velocidades $(v, \omega)$ **alcanzables** en el próximo instante,
   dadas las aceleraciones máximas del robot — la "ventana dinámica".
2. Para cada pareja, **simula** la trayectoria resultante durante un horizonte corto.
3. Descarta las que chocan según el costmap local.
4. Puntúa las restantes: proximidad a la ruta global, avance hacia el objetivo, distancia a
   obstáculos.
5. Manda la mejor.

Es un método **reactivo**: no planifica a largo plazo, pero responde en milisegundos a algo
que aparece delante.

**Comportamientos de recuperación.** Si `move_base` no encuentra salida, ejecuta una
secuencia: limpiar el costmap, girar en el sitio para "mirar" alrededor, limpiar de forma
más agresiva, y finalmente abortar. **Si ves al robot girando sobre sí mismo sin avanzar,
está en recuperación**, no averiado.

**La cola de navegación de SafeVision** añade una capa propia: antes de aceptar un punto,
lo **prevalida** con el servicio `make_plan`. Si no existe ruta, lo rechaza **sin mover el
robot**. Y ata la cola al mapa activo: no se pueden ejecutar puntos de otro mapa.

**El límite que vas a medir.** El costmap local se alimenta de **una sola fuente**: el
LiDAR 2D, a 11 cm del suelo. DWA sólo puede esquivar lo que está en el costmap. Lo que el
LiDAR no ve, DWA no lo evita. Lo comprobaste estáticamente en P02; aquí lo verás **con el
robot en movimiento**.

## 4. Material

- Robot localizado en su mapa (P04)
- PC con dashboard
- Mando — **en las manos de una persona durante toda la práctica**
- Obstáculos:
  - **caja de cartón grande** (>30 cm de alto) — obstáculo "visible"
  - **mesa o silla de patas finas**, superficie a ~40 cm — obstáculo "invisible"
  - conos o botellas para delimitar
- Cinta métrica, cinta adhesiva, cronómetro

## 5. Seguridad

> ⚠️ **Ésta es la práctica de mayor riesgo del curso. Léelo entero.**

| # | Regla |
|---|---|
| 1 | **Área de 3 × 3 m como mínimo**, delimitada con cinta en el suelo |
| 2 | **Una persona dedicada exclusivamente al mando.** No anota, no fotografía, no habla por teléfono |
| 3 | Antes de cada objetivo, **se avisa en voz alta**: *"lanzando a punto 2"* |
| 4 | **Nadie dentro del área** mientras el robot navega |
| 5 | Los obstáculos se colocan **con el robot detenido**, salvo en la parte D, que se hace con procedimiento específico |
| 6 | Si algo va mal: **soltar el mando** (para en 0,5 s) o `POST /nav/cancel` |

### 5.1 Palabra de parada

Antes de empezar, acordad en voz alta una palabra (p. ej. **"ALTO"**). Quien la diga,
detiene todo, sea quien sea.

## 6. Procedimiento

### Parte A — Preparación (15 min)

**A.1** Aplica el perfil con tu mapa y **localiza el robot correctamente** (P04).

```bash
export R=http://<IP-DEL-ROBOT>:8091
curl -s $R/map_pose | python3 -m json.tool
```

*Esperado:* `"localized": true` y pose coherente.

> ⚠️ **No sigas si la localización no es buena.** Un robot mal localizado navegando es
> peligroso: irá a donde *cree* que está el punto.

**A.2** Delimita el área con cinta y retira todo lo que no sea obstáculo de la práctica.

**A.3** Marca en el suelo **tres puntos**: P1, P2, P3, separados al menos 1,5 m, y anota sus
coordenadas en el mapa.

### Parte B — Un objetivo (25 min)

**B.1** Carga un solo punto en la cola:

```bash
curl -X POST $R/nav/queue -H 'Content-Type: application/json' \
     -d '{"map":"lab_equipoN_intento1","points":[{"id":"0x001","x":1.0,"y":0.5,"yaw":0.0}]}'
```

> 📝 **Anota la respuesta.** Si devuelve `409`, el punto no es alcanzable: elige otro y
> anota por qué crees que fue rechazado.

**B.2** **Avisa en voz alta.** Comprueba que no hay nadie en el área.

**B.3** Lanza y cronometra:

```bash
curl -X POST $R/nav/start
```

**B.4** Observa: ¿la trayectoria es recta o curva? ¿Frena al llegar?

> 📝 **Anota:** tiempo hasta llegar, y la distancia entre donde paró y el punto marcado en
> el suelo (mide con cinta).

**B.5** Repite tres veces desde la misma posición de partida.

> 📝 **Tabla de tres repeticiones:** tiempo y error de llegada. Calcula la media.

### Parte C — Cola de varios puntos (20 min)

**C.1** Carga los tres puntos:

```bash
curl -X POST $R/nav/queue -H 'Content-Type: application/json' \
     -d '{"map":"lab_equipoN_intento1","points":[
          {"id":"0x001","x":1.0,"y":0.5,"yaw":0.0},
          {"id":"0x002","x":2.0,"y":1.5,"yaw":1.57},
          {"id":"0x003","x":0.5,"y":2.0,"yaw":3.14}]}'
```

**C.2** Avisa, lanza y sigue el progreso:

```bash
watch -n 1 "curl -s $R/nav/status | python3 -m json.tool | head -20"
```

> 📝 **Captura de `nav/status`** en mitad del recorrido, mostrando `remaining` y
> `completed`.

**C.3** **A mitad de recorrido, cancela:**

```bash
curl -X POST $R/nav/cancel
```

> 📝 **¿Cuánto tarda en detenerse? ¿Qué pasa con la cola?** Anótalo.

### Parte D — Evasión de obstáculo visible (30 min) ⭐

**D.1** Lanza el robot hacia un punto alejado, en línea recta despejada.

**D.2** Cuando lleve recorrido **un tercio** del trayecto, una persona coloca la **caja
grande** en su camino, **a al menos 1,5 m por delante del robot**, y **se retira
inmediatamente fuera del área**.

> ⚠️ **La persona que coloca la caja no se queda en el área.** Coloca y sale.

**D.3** Observa el comportamiento.

> 📝 **Anota:** ¿a qué distancia reaccionó? ¿La rodeó o se detuvo? ¿Replanificó la ruta?
> ¿Llegó al objetivo?

**D.4** **Captura el costmap local** con la caja marcada.

**D.5** Repite con la caja más cerca de una pared, de forma que el hueco sea estrecho
(~50 cm).

> 📝 **¿Pasa o lo considera bloqueado?** Relaciónalo con `inflation_radius: 0.30` y con el
> ancho del robot (20 cm).

### Parte E — Recuperación (20 min)

**E.1** Lanza el robot a un objetivo y **rodéalo de obstáculos** por tres lados, dejando
sólo el camino de vuelta (colocando con el robot detenido).

**E.2** Observa.

> 📝 **¿Gira sobre sí mismo? ¿Cuánto tarda en abortar? ¿Qué dice `nav/status`?**
> Captura el mensaje de error.

**E.3** Retira los obstáculos y comprueba si se recupera solo.

### Parte F — El límite del LiDAR 2D (30 min) ⭐⭐

> ⚠️ **Procedimiento especial. Lee los tres pasos antes de empezar.**
> El objetivo es **demostrar que el robot NO detecta el obstáculo**, así que hay que
> pararlo a mano antes del contacto.

**F.1** Coloca la **mesa/silla de patas finas** de modo que su **superficie** invada la
trayectoria del robot, pero **sus patas queden fuera** del camino.

**F.2** Verifica primero con el robot **parado** que el costmap está vacío en esa zona.

> 📝 **Captura del costmap vacío** con el obstáculo físicamente presente.

**F.3** La persona del mando se coloca **junto al robot, con el dedo en el control**.
Lanza un objetivo al otro lado de la mesa **a la velocidad más baja posible** y
**detén el robot manualmente cuando esté a 20 cm del obstáculo**.

> ⚠️ **No dejes que choque.** La evidencia es que el costmap sigue vacío y que el robot
> avanzaba sin reducir velocidad, no el golpe.

> 📝 **Anota:** ¿redujo la velocidad? ¿Apareció algo en el costmap? ¿Qué habría ocurrido
> sin intervención?

**F.4** Repite con la **caja alta** en el mismo sitio (esta sí es visible) y compara.

> 📝 **Captura comparativa:** costmap con la caja (obstáculo marcado) y costmap con la mesa
> (vacío). **Es la evidencia principal de la práctica.**

## 7. Resultados a reportar

1. Tabla de tres repeticiones de la parte B: tiempo y error de llegada.
2. Captura de `nav/status` durante la ejecución de la cola, y tras cancelar.
3. Descripción del comportamiento de evasión (D.3) con distancia de reacción.
4. Captura del costmap con la caja detectada.
5. Resultado del paso estrecho (D.5) con su justificación numérica.
6. Descripción y captura del comportamiento de recuperación.
7. **Capturas comparativas de la parte F**: costmap con caja vs. costmap con mesa.
8. Conclusión razonada sobre los límites de la evasión con un sensor 2D.

## 8. Preguntas de análisis

1. **¿Por qué hacen falta dos planificadores?** ¿Qué ocurriría con sólo el global? ¿Y con
   sólo el local?
2. DWA simula trayectorias y elige la mejor. **¿Por qué "ventana dinámica"?** ¿Qué papel
   juegan las aceleraciones máximas del robot?
3. En D.5, con un hueco de 50 cm, el robot mide 20 cm de ancho y la inflación es de 30 cm.
   **Calcula** si debería pasar, y compáralo con lo observado. Si no coincide, explica por
   qué.
4. La cola prevalida cada punto con `make_plan` y rechaza los inalcanzables **antes** de
   mover el robot. **¿Qué ventaja tiene rechazar antes en vez de intentarlo y fallar?**
   Piensa en términos de seguridad y de experiencia de uso.
5. A partir de la parte F: **el robot no detectó la mesa.** Propón una solución concreta
   usando la cámara RGB-D que el robot ya tiene montada. Indica: qué dato usarías, en qué
   parte del sistema lo integrarías, y **qué riesgo** tendría (piensa en el suelo
   reflectante y en la CPU de la Raspberry Pi).

> La pregunta 5 corresponde a una decisión real y abierta del proyecto. Compara tu
> propuesta con [`../analisis-alcance.md`](../analisis-alcance.md) §4.

## 9. Rúbrica

| Criterio | Peso | Excelente | Suficiente | Insuficiente |
|---|---:|---|---|---|
| Navegación y cola | 20 % | Ejecuta B y C completas con mediciones | Las ejecuta sin medir | No las completa |
| Evasión (parte D) | 20 % | Documenta la reacción con distancias y capturas | Describe sin medir | No la realiza |
| **Parte F (límite 2D)** | 25 % | Evidencia comparativa clara y conclusión razonada | Realiza la prueba sin comparar | No la realiza |
| Análisis (preguntas) | 20 % | Cálculo correcto en P3 y propuesta fundada en P5 | Responde sin profundizar | No responde |
| **Seguridad** | 15 % | Protocolo impecable: área delimitada, avisos, mando dedicado | Necesita recordatorios | **Cualquier contacto no controlado o persona en el área** |

> **El criterio de seguridad puede reprobar la práctica por sí solo.** Un choque no
> controlado, o alguien dentro del área con el robot navegando, es insuficiente
> independientemente del resto.

---

**Anterior:** [P04](P04-localizacion-amcl.md) · **Siguiente:** [P06 — YOLO y misiones](P06-yolo-misiones.md)
