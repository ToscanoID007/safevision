# Protocolo de validación

**Para quién es y cuándo leerlo**
Para quien vaya a demostrar que el sistema funciona: es la evidencia del objetivo 8 de la
propuesta y la fuente de los resultados del reporte final.
Imprímelo o ábrelo en el portátil **mientras haces las pruebas**, y rellena las celdas
sobre la marcha. Una prueba sin fecha ni responsable no es una prueba.

---

**Origen:** el *acceptance test* del handoff §59, convertido en tablas rellenables y
ampliado con lo verificado en `docs/estado-actual.md`.
**Estado:** **todos los resultados están en `[PENDIENTE]`.** Nadie ha ejecutado este
protocolo todavía. **No se ha inventado ningún resultado.**

---

## 0. Cómo usar este documento

1. Haz las pruebas **en orden**: cada bloque supone que el anterior pasó.
2. Rellena **Resultado**, **Fecha**, **Responsable** y **Evidencia** en cada fila.
3. Usa `OK` / `FALLO` / `N/A` en Resultado. Si falla, anota el mensaje exacto.
4. En **Evidencia** pon algo verificable: nombre del fichero de captura, de la fotografía,
   o la salida de `curl` pegada en el anexo §12.
5. Si una prueba falla, **no sigas** con ese bloque: anótalo y pasa al siguiente.

**Convenciones:** `$R` es `http://<IP-DEL-ROBOT>:8091`. Ejemplo:

```bash
export R=http://192.168.1.13:8091
```

---

## 1. Protocolo de seguridad — **leer antes de empezar**

> ⚠️ **Este robot se mueve solo. Estas reglas no son opcionales.**

### 1.1 Antes de cualquier prueba con movimiento

| # | Requisito |
|---|---|
| 1 | **Área despejada de al menos 2 × 2 m**, sin cables, mochilas ni sillas |
| 2 | El robot **en el suelo**, nunca sobre una mesa (el LiDAR **no ve el borde**) |
| 3 | **Una persona con el mando en las manos**, sin hacer otra cosa |
| 4 | Todos los presentes saben qué se va a probar y por dónde irá el robot |
| 5 | Nadie entre el robot y su objetivo |
| 6 | Batería con carga suficiente (con poca batería los motores fallan antes que la Pi) |

### 1.2 Reparto de papeles

Se necesitan **dos personas como mínimo** para las pruebas de movimiento:

| Papel | Responsabilidad |
|---|---|
| **Operador del mando** | Sostiene el mando. **No toca el teclado.** Su única tarea es poder parar el robot |
| **Operador del dashboard** | Ejecuta las órdenes y anota resultados |

### 1.3 Cómo parar, de más rápido a más lento

1. **Soltar el mando** → el *watchdog* para el robot en **0,5 s**
2. `curl -X POST $R/nav/cancel` → aborta la navegación
3. `curl -X POST $R/mission/cancel` → aborta la misión
4. Quitar la alimentación → último recurso; **no** apaga la Pi limpiamente

### 1.4 Parada de emergencia declarada

> **Antes de empezar, decidid en voz alta quién sostiene el mando y qué palabra se grita
> para detener todo.** Anotadlo aquí:

- Persona con el mando: `[PENDIENTE: nombre]`
- Palabra de parada: `[PENDIENTE: p. ej. "ALTO"]`

### 1.5 Registro de incidentes

| # | Fecha | Qué pasó | Daños | Acción tomada |
|---|---|---|---|---|
| 1 | `[PENDIENTE]` | `[PENDIENTE]` | `[PENDIENTE]` | `[PENDIENTE]` |

---

## 2. Datos de la sesión de validación

| Campo | Valor |
|---|---|
| Fecha de inicio | `[PENDIENTE]` |
| Fecha de término | `[PENDIENTE]` |
| Responsables | `[PENDIENTE: nombres]` |
| Lugar | `[PENDIENTE: laboratorio, aula]` |
| Robot / IP | `[PENDIENTE]` |
| Commit del repositorio | `[PENDIENTE: git log --oneline -1]` |
| Mapa de referencia | `[PENDIENTE: p. ej. HAB2]` |
| Versión del dashboard | `[PENDIENTE: versionado / SafeVision_Dashboard_dev]` |

---

## 3. Arranque y servicios

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| A-1 | Arranque en frío | Apagar, esperar 10 s, encender. Esperar 90 s | El robot arranca y responde a `ping yahboom.local` | `[PENDIENTE]` | | | |
| A-2 | Servicios habilitados | `systemctl is-enabled safevision-roscore safevision-robot-server` | `enabled` en los dos | `[PENDIENTE]` | | | |
| A-3 | Servicios activos | `systemctl status safevision-roscore safevision-robot-server` | `active (running)` en los dos | `[PENDIENTE]` | | | |
| A-4 | Unidades íntegras | `diff` de `/etc/systemd/system/*.service` contra las del repositorio | Idénticas | `[PENDIENTE]` | | | |
| A-5 | Sin procesos residuales | `pgrep -af roslaunch; pgrep -af "api/"` | Vacío tras un arranque limpio | `[PENDIENTE]` | | | |
| A-6 | Robot Server responde | `curl -s $R/health` | JSON con `ros_master: true` | `[PENDIENTE]` | | | |
| A-7 | Estado inicial correcto | `curl -s $R/runtime/status` | `profile.requested: null`, `inferred: "base"` | `[PENDIENTE]` | | | |

> **A-7 documenta el comportamiento esperado, no un fallo:** tras arrancar, el robot no
> tiene perfil. Ver `docs/estado-actual.md` §1.

---

## 4. Prueba V-1 — ¿queda el robot operable?

**La prueba que decide el futuro del dashboard.** Ver `docs/estado-actual.md` §8.

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| V-1a | Aplicar perfil desde el dashboard | Arrancar `~/SafeVision_Dashboard_dev/`, abrir `/pilotada`, elegir mapa y control, aplicar **Pilotada** | El dashboard confirma el perfil (puede tardar hasta 2 min) | `[PENDIENTE]` | | | |
| V-1b | Verificar recursos | `curl -s $R/runtime/status` | `driver`, `core`, `lidar`, `localization`, `pose_exporter`, `navigation`, `nav_queue`, `selector` y `mando` en `active: true` | `[PENDIENTE]` | | | |
| V-1c | Verificar salud | `curl -s $R/health` | `ok: true` (en modo **mando**) | `[PENDIENTE]` | | | |
| V-1d | Alternativa por terminal | `POST $R/runtime/profile` con `{"profile":"pilotada","map":"HAB2","control":"mando"}` | `ok: true` | `[PENDIENTE]` | | | |

> **Si V-1a pasa:** el dashboard de `~/SafeVision_Dashboard_dev/` es el bueno →
> **versionarlo** (`docs/estado-actual.md` §5.5). Es la tarea pendiente número uno.
> **Si falla:** anota en qué recurso se detuvo (`steps[]` lo dice) y consulta
> `docs/solucion-problemas.md` §4.

---

## 5. ROS y sensores

**Precondición:** V-1 superada. Ejecutar en el robot tras `source /opt/ros/melodic/setup.bash`.

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| R-1 | ROS Master | `rosnode list` | Lista sin errores | `[PENDIENTE]` | | | |
| R-2 | Driver | `rosnode list \| grep driver_node` | Presente | `[PENDIENTE]` | | | |
| R-3 | IMU publica | `rostopic hz /imu/imu_data` | Frecuencia estable (>10 Hz) | `[PENDIENTE]` | | | |
| R-4 | EKF publica | `rostopic hz /odom` | Frecuencia estable | `[PENDIENTE]` | | | |
| R-5 | LiDAR publica | `rostopic hz /scan` | ≈10 Hz | `[PENDIENTE]` | | | |
| R-6 | Contenido de `/scan` | `rostopic echo -n 1 /scan` | Rangos plausibles, no todo `inf` | `[PENDIENTE]` | | | |
| R-7 | AMCL activo | `rosnode list \| grep amcl` | Presente | `[PENDIENTE]` | | | |
| R-8 | Árbol TF completo | `rosrun tf view_frames` | `map → odom → base_footprint → base_link → laser` sin huecos | `[PENDIENTE]` | | | |
| R-9 | `move_base` | `rosservice list \| grep make_plan` | `/move_base/make_plan` presente | `[PENDIENTE]` | | | |
| R-10 | Carga de CPU | `top -bn1 \| head -15` con todo activo | Sin saturación sostenida | `[PENDIENTE]` | | | |

---

## 6. Control y seguridad

> ⚠️ **A partir de aquí el robot se mueve.** Aplica el protocolo de la §1.

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| C-1 | Mando | Perfil con `control: mando`. Mover el joystick | El robot se mueve en la dirección esperada | `[PENDIENTE]` | | | |
| C-2 | **Watchdog** | Con el robot en marcha, **soltar el mando** | Se detiene en **≤ 0,5 s** | `[PENDIENTE]` | | | |
| C-3 | Teclado web | `POST $R/runtime/control {"mode":"teclado"}`, luego órdenes repetidas a `/runtime/keyboard` | El robot se mueve | `[PENDIENTE]` | | | |
| C-4 | Watchdog en teclado | Dejar de enviar órdenes | Se detiene en ≤ 0,5 s | `[PENDIENTE]` | | | |
| C-5 | Exclusión mutua | Durante navegación, intentar mover con el mando | El manual no interfiere con `/cmd_vel_nav` | `[PENDIENTE]` | | | |
| C-6 | **Pérdida de red** | Con el robot navegando, desconectar el Wi-Fi de la PC | **El robot sigue navegando** y evitando obstáculos | `[PENDIENTE]` | | | |
| C-7 | Cancelación explícita | `POST $R/nav/cancel` durante la navegación | Se detiene y el selector vuelve a MANUAL | `[PENDIENTE]` | | | |

> **C-2 y C-6 son las dos pruebas de seguridad más importantes del protocolo.** C-2
> demuestra que el robot se detiene solo si el operador suelta el control; C-6, que el
> robot no depende de la PC para navegar con seguridad. Son la demostración práctica de
> la regla "los lazos críticos viven en el robot" (handoff §79).

---

## 7. Cámara e inteligencia artificial

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| I-1 | Vídeo bruto | Abrir `$R/video_feed` en el navegador | Imagen fluida | `[PENDIENTE]` | | | |
| I-2 | Vídeo sin perfil | Consultar `/video_feed` recién arrancado el robot | Funciona igualmente (apertura perezosa) | `[PENDIENTE]` | | | |
| I-3 | Fotogramas por segundo | Medir el flujo durante 30 s | ≈30 fps, ≈4 Mbit/s | `[PENDIENTE]` | | | |
| I-4 | Captura compartida | Abrir el flujo en dos pestañas | Ambas funcionan; la cámara no se abre dos veces | `[PENDIENTE]` | | | |
| I-5 | Reconexión | Desconectar y reconectar la cámara USB | El sistema se recupera o informa claramente | `[PENDIENTE]` | | | |
| I-6 | Catálogo de modelos | `curl -s $R/models` | Lista los modelos con clases y tamaños | `[PENDIENTE]` | | | |
| I-7 | Detección | Mostrar un objeto de una clase entrenada ante la cámara | Aparece la caja con su etiqueta | `[PENDIENTE]` | | | |
| I-8 | Umbral de confianza | Ajustar el umbral en el dashboard | Cambia el número de detecciones | `[PENDIENTE]` | | | |
| I-9 | CPU en la PC | Observar el consumo con YOLO activo | Sostenible sin GPU | `[PENDIENTE]` | | | |

---

## 8. Localización y pose

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| P-1 | Pose sin AMCL | `curl -s $R/map_pose` sin perfil | `localized: false`, sin romperse | `[PENDIENTE]` | | | |
| P-2 | Pose inicial | `POST $R/initialpose` con la posición real | `ok: true` | `[PENDIENTE]` | | | |
| P-3 | Pose disponible | `curl -s $R/map_pose` | `localized: true` con pose coherente | `[PENDIENTE]` | | | |
| P-4 | Pose en el dashboard | Mirar el mapa en la interfaz | El robot aparece donde está de verdad | `[PENDIENTE]` | | | |
| P-5 | Convergencia | Teleoperar 1-2 m y girar | La pose se ajusta y se estabiliza | `[PENDIENTE]` | | | |
| P-6 | Frecuencia | Observar la actualización de la pose | ≈10 Hz | `[PENDIENTE]` | | | |
| P-7 | Deriva | Recorrer 5 m y volver al punto de partida | El error acumulado es aceptable | `[PENDIENTE: definir "aceptable" en cm — medirlo primero]` | | | |

---

## 9. Navegación

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| N-1 | Un punto | Cargar un punto alcanzable y arrancar | Llega y se detiene | `[PENDIENTE]` | | | |
| N-2 | Varios puntos | Cola de 3 puntos | Los recorre en orden; `completed_count` sube | `[PENDIENTE]` | | | |
| N-3 | **Ruta imposible** | Punto dentro de una pared | **Se rechaza al cargar la cola** (`409`), sin mover el robot | `[PENDIENTE]` | | | |
| N-4 | Mapa incorrecto | Cola con un mapa distinto al activo | Se rechaza | `[PENDIENTE]` | | | |
| N-5 | Cancelar | `POST $R/nav/cancel` a mitad de trayecto | Se detiene; selector a MANUAL | `[PENDIENTE]` | | | |
| N-6 | Vaciar | `POST $R/nav/clear` | La cola queda vacía | `[PENDIENTE]` | | | |
| N-7 | **Evasión dinámica** | Interponer una caja **alta (>15 cm)** en el trayecto | El robot la rodea o se detiene sin chocar | `[PENDIENTE]` | | | |
| N-8 | Recovery | Rodear al robot de obstáculos | Ejecuta la recuperación (gira) e informa | `[PENDIENTE]` | | | |
| N-9 | **Límite del LiDAR 2D** | Interponer un obstáculo **por encima** del plano del LiDAR (mesa a 40 cm, patas finas) | **Se espera que NO lo detecte.** Documenta la limitación | `[PENDIENTE]` | | | |

> **N-9 es una prueba de documentación, no de fallo.** Su resultado esperado es negativo:
> demuestra la limitación que justifica la fusión RGB-D (`docs/analisis-alcance.md` §4).
> Hazla **con la mano lista para parar** y con un obstáculo que no dañe al robot.

---

## 10. Mapeo

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| M-1 | Precondición | `POST $R/mapping/session/start` **sin** perfil aplicado | Se rechaza con `409` y un mensaje claro | `[PENDIENTE]` | | | |
| M-2 | Inicio | Con perfil aplicado, iniciar sesión | `mapping: true`; AMCL se retira | `[PENDIENTE]` | | | |
| M-3 | Mapa en vivo | Pilotar y observar `$R/mapping/map` | El mapa crece | `[PENDIENTE]` | | | |
| M-4 | Guardar | `POST $R/mapping/session/save` | Mapa guardado (`.yaml` + `.pgm`) | `[PENDIENTE]` | | | |
| M-5 | **Restaurar tras guardar** | Comprobar `runtime/status` después de M-4 | Vuelve al perfil anterior **con el mapa nuevo**; AMCL y `map_server` de vuelta | `[PENDIENTE]` | | | |
| M-6 | Descartar | Nueva sesión, `POST $R/mapping/session/discard` | Vuelve al perfil anterior con el mapa **anterior** | `[PENDIENTE]` | | | |
| M-7 | **Rollback ante fallo** | Provocar un fallo (p. ej. desconectar el LiDAR durante el inicio) | El sistema restaura el estado anterior, no se queda a medias | `[PENDIENTE]` | | | |
| M-8 | Calidad del mapa | Comparar el mapa con la sala real | Paredes rectas, sin duplicados, bucles cerrados | `[PENDIENTE]` | | | |

---

## 11. Mapas, misiones y apagado

### 11.1 Gestión de mapas

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| G-1 | Listar | `curl -s $R/maps` | Lista correcta | `[PENDIENTE]` | | | |
| G-2 | Renombrar | `POST $R/maps/rename` | Se renombran `.yaml` y `.pgm` juntos | `[PENDIENTE]` | | | |
| G-3 | Duplicar | `POST $R/maps/duplicate` | Copia completa | `[PENDIENTE]` | | | |
| G-4 | Exportar | `GET $R/maps/<n>/export` | `.zip` con los dos ficheros | `[PENDIENTE]` | | | |
| G-5 | Importar | `POST $R/maps/import` con ese `.zip` | Mapa disponible | `[PENDIENTE]` | | | |
| G-6 | Editar | Borrar ruido con el editor del dashboard | Cambio aplicado; copia en `.safevision_edit_backup/` | `[PENDIENTE]` | | | |
| G-7 | Borrar | `POST $R/maps/delete` sobre un mapa de prueba | Desaparece de la lista | `[PENDIENTE]` | | | |

### 11.2 Misiones

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| S-1 | Crear y guardar | Definir puntos y programa; guardar | Aparece en `GET $R/missions` | `[PENDIENTE]` | | | |
| S-2 | Validar — correcta | Validar un programa correcto | Sin errores | `[PENDIENTE]` | | | |
| S-3 | Validar — punto inexistente | `ir("no_existe")` | Error claro, no se guarda | `[PENDIENTE]` | | | |
| S-4 | Simular | Simular la misión | Recorrido dibujado; el robot **no** se mueve | `[PENDIENTE]` | | | |
| S-5 | Preparar | `POST $R/mission/prepare` | Estado `ready` | `[PENDIENTE]` | | | |
| S-6 | Ejecutar `ir` | Misión con dos `ir()` | Recorre ambos puntos | `[PENDIENTE]` | | | |
| S-7 | Ejecutar `esperar` | Misión con `esperar(5)` | Pausa 5 s; estado `waiting` | `[PENDIENTE]` | | | |
| S-8 | Ejecutar `orientar` | Misión con `orientar(90)` | Gira; estado `orienting` | `[PENDIENTE]` | | | |
| S-9 | **`girar()` rechazado** | Misión con `girar(90)`, ejecutar | **Error "Acción todavía no habilitada: girar"** | `[PENDIENTE]` | | | |
| S-10 | **`relocalizar()` rechazado** | Misión con `relocalizar()`, ejecutar | Error equivalente | `[PENDIENTE]` | | | |
| S-11 | Cancelar | `POST $R/mission/cancel` a mitad | Se detiene; estado `cancelled` | `[PENDIENTE]` | | | |
| S-12 | Cancelar durante `esperar` | Cancelar mientras espera | Se interrumpe al instante | `[PENDIENTE]` | | | |
| S-13 | Semántica de `orientar` | `orientar(90)` desde una orientación conocida | **[PENDIENTE: anotar el resultado: ¿ángulo absoluto o relativo? ¿grados? ¿antihorario? Esto CIERRA un pendiente de `docs/lenguaje-misiones.md` §3.3]** | `[PENDIENTE]` | | | |

> **S-9 y S-10 tienen resultado esperado negativo**: comprueban que el sistema **rechaza
> limpiamente** lo que no sabe hacer, en vez de ejecutarlo a medias.

### 11.3 Apagado

| # | Prueba | Procedimiento | Resultado esperado | Resultado | Fecha | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|
| X-1 | Perfil `libre` | `POST $R/runtime/profile {"profile":"libre"}` | LiDAR, AMCL, `move_base` y cola se apagan | `[PENDIENTE]` | | | |
| X-2 | Sin `roslaunch` huérfanos | `pgrep -af roslaunch` tras X-1 | Vacío | `[PENDIENTE]` | | | |
| X-3 | Sin `cmd_vel` residual | `rostopic echo -n 1 /cmd_vel` con el robot parado | Sin órdenes de movimiento | `[PENDIENTE]` | | | |
| X-4 | Cámara liberada | Tras cerrar todos los clientes de vídeo | La cámara se libera o se reutiliza limpiamente | `[PENDIENTE]` | | | |
| X-5 | Apagado limpio | `sudo shutdown -h now` | Se apaga sin corromper la tarjeta | `[PENDIENTE]` | | | |
| X-6 | Ciclo completo | Apagar, encender y repetir A-1…A-7 | Comportamiento idéntico | `[PENDIENTE]` | | | |

---

## 12. Resumen de resultados

Rellenar al terminar.

| Bloque | Pruebas | OK | Fallo | N/A |
|---|---:|---:|---:|---:|
| §3 Arranque y servicios | 7 | `[PENDIENTE]` | | |
| §4 Operabilidad (V-1) | 4 | `[PENDIENTE]` | | |
| §5 ROS y sensores | 10 | `[PENDIENTE]` | | |
| §6 Control y seguridad | 7 | `[PENDIENTE]` | | |
| §7 Cámara e IA | 9 | `[PENDIENTE]` | | |
| §8 Localización | 7 | `[PENDIENTE]` | | |
| §9 Navegación | 9 | `[PENDIENTE]` | | |
| §10 Mapeo | 8 | `[PENDIENTE]` | | |
| §11.1 Mapas | 7 | `[PENDIENTE]` | | |
| §11.2 Misiones | 13 | `[PENDIENTE]` | | |
| §11.3 Apagado | 6 | `[PENDIENTE]` | | |
| **Total** | **87** | | | |

### 12.1 Conclusión de la validación

`[PENDIENTE: redactar tras ejecutar el protocolo. Debe responder: ¿el sistema cumple el
objetivo 8 de la propuesta —"validar el sistema en entornos estructurados"—? ¿Qué
limitaciones se documentaron? ¿Qué quedó sin probar y por qué?]`

### 12.2 Anexo de evidencias

`[PENDIENTE: listar aquí las capturas, fotografías y salidas de terminal, con su nombre de
fichero, para poder citarlas desde el reporte final.]`

---

## 13. Documentos relacionados

- `docs/manual-operacion.md` — cómo se ejecuta cada procedimiento.
- `docs/solucion-problemas.md` — qué hacer cuando una prueba falla.
- `docs/estado-actual.md` — el estado verificado del que parte este protocolo.
- `docs/analisis-alcance.md` — por qué N-9 importa, y qué exigiría la fusión RGB-D.
- `docs/reporte-final.md` §9 — donde se citan estos resultados.
