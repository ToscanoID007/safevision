# P03 — Mapeo SLAM con Gmapping

**Para quién es y cuándo leerlo**
Para el estudiante, en la tercera sesión. Es la práctica más larga y la más vistosa.
Requiere P01 y P02.

---

**Duración:** 2-3 horas · **Requisitos previos:** P01, P02

## 1. Competencia

Aplica técnicas de SLAM (*Simultaneous Localization and Mapping*) para construir un mapa
métrico de un entorno real, evaluando la calidad del resultado y relacionando los defectos
observados con las causas físicas que los producen.

## 2. Objetivo

Al terminar, el estudiante será capaz de:

- explicar el problema del SLAM y por qué es circular;
- construir un mapa 2D de ocupación del laboratorio con Gmapping;
- reconocer y **corregir** los defectos típicos (deriva, paredes dobles, bucles abiertos);
- interpretar los ficheros `.yaml` y `.pgm` que componen un mapa;
- explicar el mecanismo de transición y *rollback* entre localización y mapeo.

## 3. Marco teórico

**El problema.** Para saber dónde estás necesitas un mapa; para construir un mapa
necesitas saber dónde estás. SLAM resuelve las dos cosas a la vez, estimando
simultáneamente la trayectoria y el mapa.

**Gmapping** usa un *Rao-Blackwellized Particle Filter*: mantiene muchas hipótesis
(partículas) de la trayectoria del robot, cada una con su propio mapa. Cuando llega un
barrido nuevo, las partículas cuyo mapa lo explica bien reciben más peso; las demás se
descartan. Es un *filtro de partículas* aplicado a trayectorias.

Sus entradas son **odometría** (cuánto cree el robot que se ha movido, a partir de los
encoders y la IMU) y **`/scan`** (qué ve el LiDAR). La odometría sola **deriva**: las
ruedas patinan, sobre todo las omnidireccionales de este robot sobre suelo liso. El LiDAR
corrige esa deriva comparando barridos (*scan matching*).

**Cierre de bucle.** Cuando el robot vuelve a un sitio ya visitado, el algoritmo puede
reconocerlo y corregir de golpe toda la trayectoria acumulada. Es lo que evita que una sala
rectangular salga como un trapecio. **Cerrar bucles es la técnica más importante que
aprenderás en esta práctica.**

**El mapa resultante** es una *rejilla de ocupación*: cada celda es libre, ocupada o
desconocida. Se guarda en dos ficheros inseparables:

| Fichero | Contenido |
|---|---|
| `<nombre>.pgm` | La imagen: negro = ocupado, blanco = libre, gris = desconocido |
| `<nombre>.yaml` | Metadatos: `resolution` (m/píxel), `origin`, umbrales |

**Transición segura.** Mapear y localizarse son incompatibles: ambos quieren publicar
`/map`. Por eso, al iniciar una sesión de mapeo, el sistema apaga AMCL, `move_base` y la
cola de navegación, y al terminar **los restaura automáticamente con el mapa nuevo**. Si
algo falla a medias, hace *rollback* al estado anterior en vez de quedarse a medio camino.

## 4. Material

- Robot con perfil `pilotada` aplicado
- PC con dashboard
- Mando
- **Un recinto cerrado**: laboratorio o aula, con las puertas cerradas
- Cinta métrica (para verificar el mapa después)
- Papel cuadriculado o tableta para dibujar el croquis

## 5. Seguridad

> ⚠️ Lee [`README.md`](README.md) §4.

- El mapeo se hace **teleoperando**: el robot se mueve mucho tiempo seguido.
- Recorre el recinto **antes** que el robot y retira mochilas, cables y sillas sueltas.
- Avisa al resto del grupo de que el robot circulará por toda la sala.
- **Ve despacio.** La prisa es la causa número uno de mapas malos.

## 6. Procedimiento

### Parte A — Croquis previo (15 min)

**A.1** Antes de tocar el robot, **dibuja a mano** un croquis del recinto con sus medidas
aproximadas: paredes, puertas, columnas, mobiliario fijo.

> 📝 **Este croquis es entregable.** Lo compararás con el mapa al final.

**A.2** Planifica el recorrido: por dónde entrarás, qué perímetro seguirás y **dónde
cerrarás el bucle**. Dibújalo sobre el croquis con flechas.

### Parte B — Preparación (15 min)

**B.1** Arranca y aplica el perfil:

```bash
export R=http://<IP-DEL-ROBOT>:8091
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"<MAPA>","control":"mando"}'
```

> **¿Por qué hace falta un mapa para mapear?** Porque el sistema necesita saber **a qué
> perfil y a qué mapa volver** cuando termines. Es parte del mecanismo de *rollback*.

**B.2** Coloca el robot en un punto de referencia claro (una esquina) y **márcalo en el
suelo con cinta**. Anótalo en el croquis.

### Parte C — Sesión de mapeo (45-60 min)

**C.1** Inicia la sesión:

```bash
curl -X POST $R/mapping/session/start \
     -H 'Content-Type: application/json' \
     -d '{"name":"lab_equipoN_intento1"}'
```

**C.2** Verifica:

```bash
curl -s $R/mapping/session/status | python3 -m json.tool
```

*Esperado:* `"mapping": true`, `"state"` distinto de `idle`.

> 📝 **Anota qué pasó con AMCL** (`"amcl": false`). Explica por qué en el reporte.

**C.3** Abre el mapa en vivo en el dashboard y **teleopera siguiendo estas reglas:**

| Regla | Por qué |
|---|---|
| **Despacio y constante** | Gmapping necesita solape entre barridos consecutivos |
| **Giros suaves**, nunca sobre el propio eje a velocidad alta | Los giros bruscos son la causa principal de deriva |
| **Primero el perímetro**, pegado a las paredes a ~1 m | Da geometría fiable para el *scan matching* |
| **Después el centro** | Rellena huecos |
| **Cierra bucles**: vuelve al punto de partida | Permite corregir la deriva acumulada |
| Entra y sal de cada rincón | Las zonas no visitadas quedan grises |

**C.4** Observa el mapa creciendo. Cada 5 minutos, **captura la pantalla**.

> 📝 **Guarda al menos tres capturas intermedias** para mostrar la evolución.

**C.5** Cuando vuelvas al punto de partida marcado con cinta, **obsérvalo con atención**:
¿se cierra el bucle limpiamente o aparecen paredes dobles?

**C.6** Decide:

- **Si el mapa está bien:** `curl -X POST $R/mapping/session/save`
- **Si está mal:** `curl -X POST $R/mapping/session/discard` y **vuelve a C.1**

> **Descartar es normal y es barato.** Un mapa malo arruina todas las prácticas
> siguientes. Se espera que al menos un equipo tenga que repetir.

### Parte D — Verificación del *rollback* (15 min)

**D.1** Justo después de guardar, consulta:

```bash
curl -s $R/runtime/status | python3 -m json.tool | grep -A5 '"profile"'
```

> 📝 **Anota:** ¿volvió al perfil anterior? ¿Con qué mapa?

**D.2** Comprueba que AMCL y `map_server` están de vuelta:

```bash
curl -s $R/runtime/status | python3 -m json.tool | grep -A4 '"localization"'
```

**D.3** Verifica que el mapa nuevo aparece en el catálogo:

```bash
curl -s $R/maps | python3 -m json.tool
```

### Parte E — Análisis del mapa (30 min)

**E.1** Descarga los metadatos:

```bash
curl -s $R/maps/lab_equipoN_intento1/meta | python3 -m json.tool
```

> 📝 **Anota:** `resolution` (m/píxel), `origin`, y las dimensiones en píxeles.

**E.2** Calcula el tamaño real del mapa:

```
ancho_metros = ancho_pixeles × resolution
alto_metros  = alto_pixeles  × resolution
```

**E.3** **Verificación métrica.** Mide con cinta una pared real del laboratorio. Mide esa
misma pared en el mapa (en píxeles) y conviértela a metros.

> 📝 **Tabla de tres mediciones:** medida real, medida en el mapa, error absoluto y
> relativo.

**E.4** Compara el mapa con tu croquis de la parte A. Marca las diferencias.

**E.5** Busca y documenta defectos:

| Defecto | ¿Aparece? | ¿Dónde? | Causa probable |
|---|---|---|---|
| Paredes dobles o gruesas | | | |
| Deriva (paredes no paralelas) | | | |
| Zonas grises (no exploradas) | | | |
| Objetos "fantasma" | | | |
| Puertas abiertas que parecen pasillos | | | |

## 7. Resultados a reportar

1. Croquis dibujado a mano, con el recorrido planificado.
2. Al menos tres capturas de la evolución del mapa.
3. Captura del mapa final.
4. Evidencia del *rollback*: `runtime/status` antes y después de guardar.
5. Metadatos del mapa y cálculo de su tamaño real.
6. **Tabla de verificación métrica** con tres mediciones y sus errores.
7. **Tabla de defectos** con las causas.
8. Si hubo que descartar algún intento: captura del mapa fallido y explicación.

## 8. Preguntas de análisis

1. SLAM se describe como un problema circular ("necesitas el mapa para localizarte y la
   localización para mapear"). **Explica cómo lo rompe un filtro de partículas.**
2. **¿Por qué los giros bruscos degradan el mapa?** Relaciónalo con la odometría de las
   ruedas omnidireccionales y con el *scan matching*.
3. Tu verificación métrica dio un error. **¿De dónde viene?** Enumera al menos tres fuentes
   y di cuál crees que domina.
4. Durante el mapeo, AMCL se apagó. **¿Por qué son incompatibles** AMCL y Gmapping?
   ¿Qué recurso se disputan?
5. El sistema restaura automáticamente el perfil anterior al guardar, y hace *rollback* si
   falla. **¿Por qué es importante** en un sistema que mueve hardware? Describe qué podría
   pasar sin ese mecanismo.

## 9. Rúbrica

| Criterio | Peso | Excelente | Suficiente | Insuficiente |
|---|---:|---|---|---|
| Calidad del mapa | 30 % | Recinto completo, paredes limpias, bucles cerrados | Reconocible con defectos menores | Inservible o incompleto |
| Verificación métrica | 20 % | Tres mediciones con error calculado y discutido | Mediciones sin análisis | Ausente |
| Análisis de defectos | 20 % | Identifica defectos y los relaciona con causas físicas | Los identifica sin explicar | No los identifica |
| Análisis (preguntas) | 20 % | Fundamenta con la teoría | Responde sin profundizar | No responde |
| Seguridad y método | 10 % | Recorrido planificado y ejecutado con cuidado | Improvisado pero seguro | Pone en riesgo al equipo |

> **Nota para el profesor:** un equipo que descarta dos mapas y entrega el tercero bien
> hecho, explicando por qué descartó, **ha aprendido más** que uno que acierta a la
> primera. Valórese en "Análisis de defectos".

---

**Anterior:** [P02](P02-percepcion-lidar.md) · **Siguiente:** [P04 — Localización con AMCL](P04-localizacion-amcl.md)
