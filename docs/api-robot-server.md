# API del Robot Server

**Para quién es y cuándo leerlo**
Para quien integre algo con el robot, depure el dashboard, o necesite operar sin interfaz
gráfica desde una terminal.
Consúltalo como referencia; no hace falta leerlo entero.

---

**Origen:** generado leyendo `misiones/pilotada/robot/sf_robot_server.py` (5.060 líneas) en
`HEAD`, no el handoff. Las respuestas de ejemplo son **capturas reales** del robot
(192.168.1.13) el 2026-09-10, salvo donde se indique.

**Base:** `http://<IP-DEL-ROBOT>:8091`
**Formato:** JSON, salvo `/video_feed` (MJPEG) y las exportaciones (binario).
**Autenticación:** **ninguna.** Ver §9.

---

## 1. Índice de los 46 endpoints

| Método | Ruta | Sección |
|---|---|---|
| GET | `/` | [Diagnóstico](#2-diagnóstico) |
| GET | `/health` | [Diagnóstico](#2-diagnóstico) |
| GET | `/runtime/status` | [Runtime](#3-runtime) |
| POST | `/runtime/profile` | [Runtime](#3-runtime) |
| POST | `/runtime/control` | [Runtime](#3-runtime) |
| POST | `/runtime/keyboard` | [Runtime](#3-runtime) |
| GET | `/runtime/resources` | [Runtime](#3-runtime) |
| POST | `/runtime/resource/<nombre>` | [Runtime](#3-runtime) |
| GET | `/video_feed` | [Vídeo](#4-vídeo) |
| GET | `/maps` | [Mapas](#5-mapas) |
| GET | `/maps/<nombre>/image` | [Mapas](#5-mapas) |
| GET | `/maps/<nombre>/meta` | [Mapas](#5-mapas) |
| GET | `/maps/<nombre>/export` | [Mapas](#5-mapas) |
| POST | `/maps/rename` | [Mapas](#5-mapas) |
| POST | `/maps/duplicate` | [Mapas](#5-mapas) |
| POST | `/maps/delete` | [Mapas](#5-mapas) |
| POST | `/maps/import` | [Mapas](#5-mapas) |
| POST | `/maps/<nombre>/edit` | [Mapas](#5-mapas) |
| GET | `/map_pose` | [Pose](#6-pose-y-localización) |
| POST | `/initialpose` | [Pose](#6-pose-y-localización) |
| GET | `/mapping/map` | [Mapeo](#7-mapeo-slam) |
| GET | `/mapping/meta` | [Mapeo](#7-mapeo-slam) |
| GET | `/mapping/session/status` | [Mapeo](#7-mapeo-slam) |
| POST | `/mapping/session/start` | [Mapeo](#7-mapeo-slam) |
| POST | `/mapping/session/save` | [Mapeo](#7-mapeo-slam) |
| POST | `/mapping/session/discard` | [Mapeo](#7-mapeo-slam) |
| GET | `/nav/status` | [Navegación](#8-navegación) |
| POST | `/nav/queue` | [Navegación](#8-navegación) |
| POST | `/nav/start` | [Navegación](#8-navegación) |
| POST | `/nav/cancel` | [Navegación](#8-navegación) |
| POST | `/nav/clear` | [Navegación](#8-navegación) |
| GET | `/missions` | [Misiones](#9-misiones) |
| POST | `/missions/save` | [Misiones](#9-misiones) |
| POST | `/missions/delete` | [Misiones](#9-misiones) |
| POST | `/mission/prepare` | [Misiones](#9-misiones) |
| GET | `/mission/status` | [Misiones](#9-misiones) |
| POST | `/mission/start` | [Misiones](#9-misiones) |
| POST | `/mission/cancel` | [Misiones](#9-misiones) |
| GET | `/models` | [Modelos](#10-modelos) |
| GET | `/models/<nombre>` | [Modelos](#10-modelos) |
| GET | `/models/<nombre>/export` | [Modelos](#10-modelos) |
| GET | `/models/<nombre>/artifact/<ext>` | [Modelos](#10-modelos) |
| POST | `/models/import` | [Modelos](#10-modelos) |
| POST | `/models/<nombre>/rename` | [Modelos](#10-modelos) |
| PUT | `/models/<nombre>/metadata` | [Modelos](#10-modelos) |
| DELETE | `/models/<nombre>` | [Modelos](#10-modelos) |

**Convención de errores:** casi todos devuelven `{"ok": false, "error": "..."}` con código
`400` (petición inválida), `404` (no existe) o `409` (conflicto de estado). Los endpoints de
mapas usan `{"status": "error", "message": "..."}`.

---

## 2. Diagnóstico

### `GET /` — identificación

```bash
curl -s http://192.168.1.13:8091/ | python3 -m json.tool
```

```json
{
  "service": "SafeVision Robot Server",
  "level": 2,
  "ip": "192.168.1.13",
  "video": "/video_feed",
  "health": "/health",
  "runtime": "/runtime/status",
  "runtime_profile": "/runtime/profile",
  "runtime_control": "/runtime/control"
}
```

> `"level": 2` es una etiqueta heredada de los antiguos "Niveles" y **está
> desactualizada**: la navegación asistida ("Nivel 3") funciona. Ver handoff §12.

### `GET /health` — salud resumida

```bash
curl -s http://192.168.1.13:8091/health | python3 -m json.tool
```

```json
{
  "ok": false,
  "level": 2,
  "ip": "192.168.1.13",
  "control_mode": "mando",
  "ros_master": true,
  "driver": false,
  "lidar": false,
  "camera": true,
  "control": false,
  "joystick": true,
  "map": { "enabled": false, "level": 2 }
}
```

| Campo | Significa |
|---|---|
| `ok` | `ros_master && driver && control && camera` (y `joystick` si el control es mando) |
| `ros_master` | responde el Master por XML-RPC |
| `driver` | existe el nodo `/driver_node` |
| `lidar` | existe el tópico `/scan` |
| `camera` | existe `/dev/video0` o `/dev/video1` |
| `control` | `/yahboom_joy` (mando) o `/yahboom_keyboard` (teclado) |
| `map.enabled` | hay `/map` **y** `/amcl` |

> ⚠️ **Dos avisos importantes.**
> 1. `ok: false` recién arrancado es **normal**: no se ha aplicado ningún perfil.
> 2. **En modo teclado, `ok` nunca será `true`.** `/health` exige el nodo
>    `/yahboom_keyboard` (`sf_robot_server.py:563-566`), pero el camino vigente implementa
>    el teclado desde el navegador, **sin nodo ROS**. Es una inconsistencia conocida
>    (handoff §15). Para el estado real usa `/runtime/status`.

---

## 3. Runtime

Encienden y apagan recursos del robot. **Son los que dejan el robot operable.**

### `GET /runtime/status` — estado detallado

La fuente de verdad. Más fiable que `/health`.

```bash
curl -s http://192.168.1.13:8091/runtime/status | python3 -m json.tool
```

```json
{
  "ok": true,
  "manager_version": 5,
  "mode": "active_profiles",
  "hostname": "yahboom",
  "ros_master_uri": "http://192.168.1.13:11311",
  "control_mode": "mando",
  "profile": { "requested": null, "inferred": "base", "map": null },
  "resources": {
    "ros_master":    { "active": true,  "state": "active" },
    "robot_server":  { "active": true,  "state": "active", "port": 8091 },
    "camera":        { "active": true,  "state": "active" },
    "driver":        { "active": false, "state": "inactive" },
    "core":          { "active": false, "state": "inactive",
                       "nodes": ["/ekf_localization","/imu_filter_madgwick","/odometry_publisher"] },
    "lidar":         { "active": false, "state": "inactive" },
    "localization":  { "active": false, "state": "inactive", "amcl": false, "map_server": false },
    "pose_exporter": { "active": false, "state": "inactive" },
    "selector":      { "active": false, "state": "inactive" },
    "navigation":    { "active": false, "state": "inactive" },
    "nav_queue":     { "active": false, "state": "inactive" },
    "mando":         { "active": false, "state": "inactive", "connected": true },
    "teclado":       { "active": false, "state": "inactive", "implementation": "dashboard_keyboard" },
    "mapping":       { "active": false, "state": "inactive" }
  }
}
```

`profile.requested` es el perfil pedido; `profile.inferred` se deduce de los recursos vivos
(`off` → `base` → `libre` → `navegacion` → `mapear`).

### `POST /runtime/profile` — **aplicar un perfil**

**El endpoint más importante del sistema.** Sin él, el robot no se mueve.

| Campo | Tipo | Obligatorio | Valores |
|---|---|---|---|
| `profile` | texto | sí | `libre`, `pilotada`, `automatica`, `mapear` |
| `map` | texto | sí para `pilotada`/`automatica` | nombre sin extensión, p. ej. `HAB2` |
| `control` | texto | no | `mando` o `teclado` |

```bash
curl -X POST http://192.168.1.13:8091/runtime/profile \
     -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'
```

Respuesta correcta (`200`):

```json
{
  "ok": true,
  "message": "Mision Pilotada lista con mapa HAB2.",
  "steps": [
    {"resource": "lidar",         "ok": true},
    {"resource": "localization",  "ok": true},
    {"resource": "pose_exporter", "ok": true},
    {"resource": "navigation",    "ok": true},
    {"resource": "nav_queue",     "ok": true}
  ],
  "status": { "...": "igual que /runtime/status" }
}
```

Error (`409`): `ok:false` y `steps` indica **en qué recurso se detuvo**. Es la mejor pista
para diagnosticar.

> ⏱️ **Puede tardar hasta 2 minutos.** Enciende driver, IMU/EKF, LiDAR, AMCL, `move_base` y
> la cola, verificando cada uno. El dashboard usa un *timeout* de 120 s. **No lo
> interrumpas.**
>
> ⚠️ `mapear` **no** se aplica por aquí: devuelve *"Mapear se inicia mediante
> /mapping/session/start"*.

### `POST /runtime/control` — cambiar el control

```bash
curl -X POST http://192.168.1.13:8091/runtime/control \
     -H 'Content-Type: application/json' -d '{"mode":"teclado"}'
```

`mode`: `mando` (lanza `joy_node` + `yahboom_joy`; exige `/dev/input/js0`) o `teclado`
(apaga el mando; el control pasa al navegador).

### `POST /runtime/keyboard` — teclado web

Publica un `Twist` en `/cmd_vel_manual`. **Mueve el robot.**

| Campo | Rango | Por defecto |
|---|---|---|
| `linear_x` | −1,0 … 1,0 m/s | 0.0 |
| `linear_y` | −1,0 … 1,0 m/s (el X3 es omnidireccional) | 0.0 |
| `angular_z` | −5,0 … 5,0 rad/s | 0.0 |

```bash
curl -X POST http://192.168.1.13:8091/runtime/keyboard \
     -H 'Content-Type: application/json' \
     -d '{"linear_x":0.15,"linear_y":0.0,"angular_z":0.0}'
```

> **Hay que repetirlo continuamente.** El *watchdog* del selector para el robot a los 0,5 s
> sin órdenes. Un solo `curl` produce un empujón mínimo, no un movimiento sostenido. Es
> **intencionado**: así el robot se detiene si el operador se desconecta.

---

### `GET /runtime/resources` — recursos individuales (v1.2)

Lista de los 14 recursos que conoce el gestor, con estado real, PID poseído, requisitos que
faltan, dependientes activos y acciones permitidas. Es lo que consume la página *Nodos*.

```json
{"ok": true, "mapping_active": false,
 "profile": {"requested": "pilotada", "inferred": "navegacion", "map": "HAB2"},
 "start_order": ["driver","core","selector","mando","lidar","localization","pose_exporter","navigation","nav_queue"],
 "resources": [
   {"name": "lidar", "active": true, "pid": 21941, "read_only": false,
    "deps": ["driver"], "missing_deps": [],
    "dependents": ["localization","pose_exporter","navigation","nav_queue"],
    "active_dependents": ["localization","pose_exporter","navigation","nav_queue"],
    "can_start": false, "can_stop": true, "reason": ""}
 ]}
```

### `POST /runtime/resource/<nombre>` — arrancar o detener un recurso (v1.2)

Body: `{"action": "start"}` o `{"action": "stop"}`.

```bash
curl -X POST $R/runtime/resource/lidar -H 'Content-Type: application/json' -d '{"action":"stop"}'
```

```json
{"ok": true, "message": "lidar detenido.",
 "steps": [{"resource":"nav_queue","ok":true},{"resource":"navigation","ok":true},
           {"resource":"pose_exporter","ok":true},{"resource":"localization","ok":true},
           {"resource":"lidar","ok":true}]}
```

*Arrancar* resuelve antes los requisitos que falten (`start navigation` → `lidar`,
`localization`, `navigation`); *detener* apaga antes los dependientes en orden inverso.
Errores: `409` con `steps` hasta el paso que falló; `409` si hay una sesión de mapeo activa,
si el recurso es de solo lectura o no existe; `400` si la acción no es `start`/`stop`.
Verificado en el robot (T6, 2026-09-13).

## 4. Vídeo

### `GET /video_feed` — MJPEG

```bash
# En el navegador:
http://192.168.1.13:8091/video_feed
```

`Content-Type: multipart/x-mixed-replace; boundary=frame`. 640×480, ~30 fps, JPEG de
calidad 70, ≈4 Mbit/s (medido).

Es un flujo **infinito**: con `curl` hay que limitarlo (`--max-time`). La captura física es
única y compartida; varios clientes no multiplican el consumo. Funciona sin perfil aplicado.

---

## 5. Mapas

### `GET /maps`

```json
{"maps": [
  {"name": "HAB2", "image": "/maps/HAB2/image"},
  {"name": "Hab2Tos", "image": "/maps/Hab2Tos/image"}
]}
```

### `GET /maps/<nombre>/image`
PNG del mapa (convertido del `.pgm`).

### `GET /maps/<nombre>/meta`
Metadatos del `.yaml`: `resolution`, `origin`, `negate`, `occupied_thresh`, `free_thresh`,
y dimensiones en píxeles.

### `GET /maps/<nombre>/export`
Descarga un `.zip` con el par `.yaml` + `.pgm`.

### `POST /maps/rename` · `POST /maps/duplicate`
Body: `{"name": "actual", "new_name": "nuevo"}`

### `POST /maps/delete`
Body: `{"name": "HAB2"}`. **Irreversible.**

### `POST /maps/import`
`multipart/form-data`, campo `file` = `.zip` con el par `.yaml` + `.pgm`.

```bash
curl -X POST -F "file=@mapa.zip" http://192.168.1.13:8091/maps/import
```

### `POST /maps/<nombre>/edit`
Aplica una edición de píxeles sobre el `.pgm` (borrar ruido, tapar huecos). Guarda copia
en `mapping/maps/.safevision_edit_backup/`.

> Los mapas son **parejas** `.yaml` + `.pgm`. Nunca separarlas (`CLAUDE.md` 7).

---

## 6. Pose y localización

### `GET /map_pose`

Con AMCL activo:

```json
{"ok": true, "localized": true,
 "pose": {"x": 1.234, "y": -0.567, "yaw": 1.5708},
 "map": "HAB2"}
```

Sin AMCL (capturado hoy):

```json
{"ok": false, "localized": false, "error": "Pose AMCL no disponible"}
```

Lee `/tmp/safevision_map_pose.json`, que `sf_pose_exporter.py` escribe a 10 Hz.

### `POST /initialpose` — fijar la pose inicial

| Campo | Tipo | Unidad |
|---|---|---|
| `x` | número | metros, marco `map` |
| `y` | número | metros |
| `yaw` | número | **radianes** |

```bash
curl -X POST http://192.168.1.13:8091/initialpose \
     -H 'Content-Type: application/json' -d '{"x":0.0,"y":0.0,"yaw":0.0}'
```

Los tres son obligatorios y deben ser finitos; si no, `400`.

> **Cuándo usarlo:** siempre, tras aplicar un perfil con mapa. AMCL arranca suponiendo el
> origen; si el robot está en otro sitio, la pose es falsa y la navegación fallará. Ver
> `docs/manual-operacion.md`.

---

## 7. Mapeo (SLAM)

### `GET /mapping/session/status`

```json
{"state": "idle", "mapping": false, "configured": true,
 "name": null, "current_map": null, "restore_map": null,
 "slam_gmapping": false, "map_from_gmapping": false,
 "amcl": false, "map_server": false,
 "core": {"ok": false, "missing": ["/rplidarNode","/ekf_localization","/odometry_publisher"]},
 "message": "Mapeo detenido"}
```

`core.missing` dice exactamente qué falta para poder mapear.

### `POST /mapping/session/start`

Body: `{"name": "mi_mapa_nuevo"}`

**Precondiciones** (si no, `409`):
- perfil `pilotada` o `automatica` activo, con mapa;
- los 7 recursos activos;
- ninguna misión automática en marcha.

### `POST /mapping/session/save`
Guarda el mapa con `map_saver`, cierra Gmapping y **restaura el perfil anterior con el mapa
nuevo**.

### `POST /mapping/session/discard`
Descarta y restaura el perfil anterior con el mapa anterior.

### `GET /mapping/map` · `GET /mapping/meta`
Mapa en vivo (PNG) y sus metadatos, mientras Gmapping construye.

---

## 8. Navegación

### `GET /nav/status`

```json
{"state": "unavailable", "running": false, "available": false,
 "map": null, "active_map": null,
 "remaining": [], "remaining_count": 0,
 "completed": [], "completed_count": 0,
 "current": null, "operation": null,
 "message": "Cola de navegación no disponible"}
```

`state`: `unavailable` (la cola no corre) · `idle` · `loaded` · `running` · `paused` ·
`done` · `error`.

### `POST /nav/queue` — cargar la cola

| Campo | Tipo |
|---|---|
| `map` | texto: mapa al que pertenecen los puntos |
| `points` | lista de `{"id": "0x001", "x": 1.2, "y": 3.4, "yaw": 0.0}` |

```bash
curl -X POST http://192.168.1.13:8091/nav/queue \
     -H 'Content-Type: application/json' \
     -d '{"map":"HAB2","points":[{"id":"0x001","x":1.0,"y":0.5,"yaw":0.0}]}'
```

Cada punto se **prevalida con `move_base/make_plan`**: si no hay plan, se rechaza sin
mover el robot.

### `POST /nav/start` · `/nav/cancel` · `/nav/clear`
Sin cuerpo. `start` pasa el selector a NAVEGACIÓN; `cancel` aborta, publica
`/move_base/cancel` y vuelve a MANUAL; `clear` vacía la cola.

---

## 9. Misiones

### `GET /missions`

```json
{"ok": true, "missions": [{"name": "Prueba_Sync_Pi", "filename": "Prueba_Sync_Pi.sfmision"}]}
```

### `POST /missions/save`
Cuerpo: el objeto misión completo (`name`, `map`, `points`, `code`…). Se valida con
`validate_mission_data()` antes de escribir; si falla, `400` con el motivo.

### `POST /missions/delete`
Body: `{"name": "Prueba_Sync_Pi"}`

### `POST /mission/prepare`

| Campo | Tipo |
|---|---|
| `mission` | objeto misión |
| `trace` | plan de ejecución producido por el simulador |

Deja la misión en estado `ready`. **Obligatorio antes de `start`.**

### `GET /mission/status`

```json
{"ok": true, "state": "idle", "running": false,
 "mission": null, "map": null, "initial_point_id": null,
 "action_index": 0, "action_count": 0, "current_action": null,
 "message": "Sin misión preparada"}
```

`state`: `idle` · `ready` · `navigating` · `waiting` · `orienting` · `done` · `error` ·
`cancelled`.

### `POST /mission/start` · `POST /mission/cancel`
Sin cuerpo.

> ⚠️ `start` **rechaza** cualquier misión que contenga `girar()` o `relocalizar()`:
> *"Acción todavía no habilitada"* (`sf_mission_executor.py:596-615`). Sólo se ejecutan
> `ir`, `esperar` y `orientar`. Ver `docs/lenguaje-misiones.md`.

---

## 10. Modelos

| Endpoint | Qué hace |
|---|---|
| `GET /models` | catálogo con artefactos, tamaños, clases y metadatos |
| `GET /models/<nombre>` | un modelo |
| `GET /models/<nombre>/export` | `.zip` con pesos + `.json` |
| `GET /models/<nombre>/artifact/<ext>` | un artefacto suelto (`pt`, `torchscript`, `json`) |
| `POST /models/import` | `multipart/form-data`, campo `file` = `.zip` |
| `POST /models/<nombre>/rename` | body `{"name": "nuevo"}` |
| `PUT /models/<nombre>/metadata` | body con `nombre_modelo`, `version`, `clases[]` |
| `DELETE /models/<nombre>` | borra modelo y metadatos |

Ejemplo real de `GET /models`:

```json
{"models": [{
  "name": "yolov",
  "display_name": "YOLOv8 Prueba (Persona, Telefono, Lentes, Botas)",
  "version": "1.0",
  "classes": ["persona","telefono","lentes","botas"],
  "class_count": 4,
  "primary": "yolov.pt", "primary_extension": ".pt",
  "activatable": true, "mb": 18.647,
  "artifacts": [
    {"name": "yolov.pt", "extension": ".pt", "mb": 6.232},
    {"name": "yolov.torchscript", "extension": ".torchscript", "mb": 12.416},
    {"name": "yolov.json", "extension": ".json", "mb": 0.0}
  ]
}]}
```

> Los modelos viven en el robot pero **la inferencia corre en la PC**: el dashboard los
> descarga. Los pesos (`*.pt`, `*.torchscript`) **no se versionan** (`CLAUDE.md` 7).

---

## 11. Seguridad — léelo antes de integrar nada

> 🔒 **No hay autenticación de ningún tipo.** Se verificó: `git grep` de
> `secret_key|auth|login` no devuelve una sola línea en el código del proyecto
> (`docs/security-scan.md` H-6).

Quien alcance el puerto 8091 puede mover el robot (`/runtime/keyboard`), encender motores
(`/runtime/profile`), borrar mapas y borrar modelos. Sin credenciales, sin registro de
auditoría, sin límite de peticiones.

**Por tanto:**

- ❌ **Nunca** expongas 8091 a Internet ni abras puertos en el router.
- ✅ Acceso remoto sólo por VPN o Tailscale (`docs/red.md` §7).
- ✅ Trata la red del laboratorio como la única frontera de seguridad que existe.

Es la regla 5 de `CLAUDE.md` y las secciones §50 y §64 del handoff.

---

## 12. Recetas útiles

```bash
R=http://192.168.1.13:8091

# Estado completo
curl -s $R/runtime/status | python3 -m json.tool

# Dejar el robot operable (tarda hasta 2 min)
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'

# Fijar la pose inicial en el origen
curl -X POST $R/initialpose -H 'Content-Type: application/json' \
     -d '{"x":0,"y":0,"yaw":0}'

# ¿Dónde está el robot?
curl -s $R/map_pose | python3 -m json.tool

# Enviar a un punto
curl -X POST $R/nav/queue -H 'Content-Type: application/json' \
     -d '{"map":"HAB2","points":[{"id":"0x001","x":1.0,"y":0.5,"yaw":0.0}]}'
curl -X POST $R/nav/start

# PARADA: cancelar navegación
curl -X POST $R/nav/cancel

# Apagar todo lo que mueve, dejando el servidor vivo
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"libre"}'
```

---

## 13. Documentos relacionados

- `docs/manual-operacion.md` — procedimientos completos.
- `docs/arquitectura.md` — qué hay detrás de cada endpoint.
- `docs/lenguaje-misiones.md` — el DSL.
- `docs/solucion-problemas.md` — cuando algo devuelve `409`.
