# SafeVision / Rosmaster X3 — Arranque real del runtime

**Documento:** `docs/runtime-boot.md`
**Fecha:** 2026-09-10
**Rama:** `wip-handoff` · **HEAD:** `ee956ad` · **Baseline:** tag `pre-refactor-baseline`
**Método:** análisis estático (lectura de fuentes + `git grep` + historia Git).
ROS no está disponible en este entorno; **no se ejecutó nada**.

---

## 0. Cómo leer este documento

Se usan las tres etiquetas de certeza del handoff (`docs/handoff-2026-09.md`, sección 0):

- **CONFIRMADO** — evidencia directa en el código del repositorio, citada con `archivo:línea`.
- **IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN** — el código existe y es coherente,
  pero el repositorio por sí solo no prueba el estado físico en la Raspberry Pi.
- **RECOMENDACIÓN** — sugerencia para el siguiente equipo; no es una decisión adoptada.

Cuando el trazado no alcanza para decidir, se marca explícitamente **INCONCLUSO** y se
indica qué comprobación lo resolvería.

> **Divergencia global con el handoff.** La sección 11 del handoff describe
> `sf_operacion_pilotada.sh` como *"archivo principal"* del arranque pilotado. Esa
> descripción corresponde al tag auditado `safevision-return-2026-08-19-73b187d`
> (commit `73b187d`). Entre ese tag y `HEAD` hay 10 commits, **todos del lado robot**,
> que introducen un segundo camino de arranque basado en systemd y en un gestor de
> recursos en proceso (`sf_runtime_manager.py`). **Donde el código y el handoff
> discrepan, manda el código.**

---

## 1. Resumen ejecutivo

Hoy conviven **dos caminos de arranque mutuamente excluyentes**:

| | Camino A — servicios systemd | Camino B — launcher monolítico |
|---|---|---|
| Entrada | `safevision-roscore.service` + `safevision-robot-server.service` | `sf_operacion_pilotada.sh teclado\|mando [mapa]` |
| Qué arranca al inicio | sólo `roscore` + Robot Server | **todo** el runtime, en 9 etapas |
| Quién arranca driver/LiDAR/AMCL/`move_base` | `sf_runtime_manager.py`, **bajo demanda** vía HTTP | el propio script, al arrancar |
| Selección de mapa | `POST /runtime/profile` (campo `map`) | argumento posicional `$2` |
| Vida del proceso | permanente (`Restart=on-failure`) | ligado a una terminal interactiva |
| Añadido en | `fa8f8b2` (2026-08-20), posterior al tag auditado | pre-existente |

**Camino A es el vigente.** Camino B sigue **presente y alcanzable** desde los menús
antiguos, pero ya no es el que define el arranque del sistema.

---

## 2. Camino A — arranque por servicios systemd (VIGENTE)

### 2.1 `safevision-roscore.service`

Fichero: `misiones/pilotada/systemd/safevision-roscore.service`

```ini
[Unit]
Description=SafeVision ROS Master
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_custom
ExecStart=/home/pi/robot_custom/misiones/pilotada/robot/sf_roscore_service.sh
Restart=on-failure
RestartSec=2
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

**CONFIRMADO:** corre como usuario `pi`, espera red antes de arrancar y se reinicia si falla.

### 2.2 `sf_roscore_service.sh`

Fichero: `misiones/pilotada/robot/sf_roscore_service.sh` (50 líneas)

1. `set -eo pipefail` (línea 2).
2. Hace `source` de `/opt/ros/melodic/setup.bash` y de
   `/home/pi/yahboomcar_ws/devel/setup.bash` (líneas 4-5) →
   **CONFIRMADO: la dependencia externa `yahboomcar_ws` es obligatoria en el arranque.**
3. `resolve_ip()` (líneas 7-24): intenta la IPv4 global de `wlan0`; si falla, cae a
   `hostname -I`.
4. Reintenta hasta **120 veces cada 0,5 s (≈60 s)** esperando una IP (líneas 26-38).
   Sin IP → `exit 1`.
5. Exporta `ROS_IP`, `ROS_MASTER_URI=http://<ip>:11311` y `ROBOT_TYPE=X3` (líneas 42-44).
6. `exec /opt/ros/melodic/bin/roscore -p 11311` (línea 50).

**Consecuencia (CONFIRMADO):** el ROS Master se publica en la IP **de LAN**, no en
`127.0.0.1`. El puerto `11311` queda expuesto en la interfaz de red del robot; esto
refuerza la regla del handoff §50/§64 y de `CLAUDE.md` §5: **nunca exponer `11311` ni
`8091` a Internet**.

### 2.3 `safevision-robot-server.service`

Fichero: `misiones/pilotada/systemd/safevision-robot-server.service`

```ini
[Unit]
After=network-online.target safevision-roscore.service
Requires=safevision-roscore.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_custom/misiones/pilotada/robot
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/pi/robot_custom/misiones/pilotada/robot/sf_robot_server_service.sh
Restart=on-failure
RestartSec=3
TimeoutStopSec=20
KillMode=control-group
```

**CONFIRMADO:**
- `Requires=` + `After=` garantizan el orden `roscore` → Robot Server.
- `WorkingDirectory` apunta a `robot/`, lo cual es **necesario** para que funcionen los
  `import sf_mapping_manager` / `sf_model_manager` / `sf_runtime_manager` de
  `sf_robot_server.py:36-38` (son imports por ruta, sin paquete).
- `KillMode=control-group` mata todo el cgroup al parar el servicio. **Esto importa**:
  los nodos ROS que lanza `sf_runtime_manager._spawn()` usan `start_new_session=True`
  (`sf_runtime_manager.py:179`), lo que los saca de la sesión pero **no** del cgroup de
  systemd. **RESUELTO (verificado 2026-09-13):** sí. Al reiniciar `safevision-robot-server`, `KillMode=control-group` mata **todos** los nodos lanzados por `sf_runtime_manager` (driver, LiDAR, AMCL, `move_base`, cola): tras el reinicio `/runtime/status` mostró los nueve recursos inactivos con el estado en `/tmp` aún diciendo `pilotada`. Desde v1.1 el gestor reconstruye ese estado solo al pedir el perfil (prueba T4.1).

### 2.4 `sf_robot_server_service.sh`

Fichero: `misiones/pilotada/robot/sf_robot_server_service.sh` (74 líneas)

Igual que el de roscore hasta la resolución de IP, y además:

1. Exporta `ROS_IP`, `ROS_MASTER_URI`, `ROBOT_TYPE=X3`, `PYTHONUNBUFFERED=1` (líneas 45-48).
2. Espera a que el Master responda: hasta **80 intentos cada 0,25 s (≈20 s)** de
   `rosnode list` (líneas 52-62). Si no, `exit 1`.
3. `cd /home/pi/robot_custom/misiones/pilotada/robot` (línea 64).
4. `exec /usr/local/bin/python3 sf_robot_server.py --control mando` (líneas 70-74).

**CONFIRMADO — dos hechos relevantes y no documentados en el handoff:**

- El intérprete es **`/usr/local/bin/python3`** (no `/usr/bin/python3` ni el Python de
  Melodic). Es una instalación local de Python 3 en la Pi con `rospy`, `cv2`, `numpy` y
  `flask` disponibles. **PENDIENTE DE REVALIDACIÓN**: qué versión exacta es y cómo se
  construyó; el repositorio no lo documenta ni lo instala.
- El control arranca **siempre fijado a `mando`** (`--control mando`, hardcodeado). No
  hay forma de arrancar el servicio en modo teclado; sólo se puede cambiar después por
  HTTP (`POST /runtime/control`, `sf_robot_server.py:650-696`).

> **Corrección a `CLAUDE.md` §10.** La regla dice que "el código del lado ROS corre bajo
> el Python de Melodic (rospy de la era 2.7)". En `HEAD` eso es falso para casi todo:
> `sf_robot_server.py`, `sf_runtime_manager.py`, `sf_mapping_manager.py`,
> `sf_model_manager.py`, `sf_nav_queue.py`, `sf_cmd_vel_selector.py`,
> `sf_modo_espera.py`, `sf_mision_pilotada.py` y `sf_servidor_descarga.py` declaran
> `#!/usr/bin/env python3`. **La única excepción es `sf_pose_exporter.py`**, que declara
> `#!/usr/bin/env python` y es invocado explícitamente con `/usr/bin/python`
> (`sf_runtime_manager.py:468` y `sf_operacion_pilotada.sh:349`). CONFIRMADO.

### 2.5 Lo que el Robot Server hace al arrancar

`sf_robot_server.py:4984-5057` (`main()`):

1. `argparse` exige `--control {teclado,mando}` y fija `CONTROL_MODE`.
2. `iniciar_nav_bridge()` (`:4486-4520`): `rospy.init_node("safevision_robot_server",
   disable_signals=True)`, publishers `/safevision/nav/command` y `/cmd_vel_manual`,
   subscribers `/safevision/nav/status` y `/map`.
3. `configurar_mapping_manager()` (`:4554-4563`): inyecta dependencias en
   `sf_mapping_manager`.
4. `app.run(host="0.0.0.0", port=8091, threaded=True)` (`PORT = 8091` en `:124`).
5. En el `finally`: `sf_mapping_manager.shutdown()`.

**CONFIRMADO:** al terminar este paso **sólo existen `roscore` y el Robot Server**. No hay
driver, ni LiDAR, ni IMU/EKF, ni AMCL, ni `move_base`, ni selector de `cmd_vel`, ni cola de
navegación, ni control. La cámara sí: `generar_frames()` (`:405-407`) llama a
`iniciar_camara_compartida()` de forma perezosa, en la primera petición a `/video_feed`.

### 2.6 `sf_runtime_manager.py` — el gestor de recursos

Fichero: `misiones/pilotada/robot/sf_runtime_manager.py` (1.610 líneas, **nuevo**, no
cubierto por el handoff).

**No es un ejecutable.** No tiene `if __name__ == "__main__"`. Es un **módulo importado en
proceso** por el Robot Server (`sf_robot_server.py:38`). CONFIRMADO.

Estado persistido en `/tmp` (líneas 15-24):

```
/tmp/safevision_runtime_state.json   perfil solicitado, mapa, control, PIDs "owned"
/tmp/safevision_active_map.json      mapa activo {name, yaml}
/tmp/safevision_runtime_logs/*.log   un log por recurso lanzado
/tmp/safevision_map_pose.json        pose exportada (la borra _stop_pose_exporter)
```

**RECOMENDACIÓN / RIESGO:** todo el estado del runtime vive en `/tmp`. Un reinicio de la
Pi lo borra mientras los servicios systemd vuelven a levantar; el estado reconstruido
queda vacío aunque `roscore` siga. Esto encaja con la deuda "IPC basado en `/tmp`" del
handoff §49 y debería centralizarse en la Fase 4.

**Cómo decide si un recurso está vivo (CONFIRMADO, líneas 234-270).** No se fía del
registro en el Master: hace `lookupNode` y luego `getPid()` contra el nodo. Un nodo
registrado pero muerto cuenta como ausente. Para el LiDAR va más lejos (`_ensure_lidar`,
líneas 363-446): exige además que `/scan` **entregue un mensaje** (`rostopic echo -n 1`),
y si el nodo está registrado pero mudo lo reinicia, con **dos intentos máximo**. Esto es
la "recuperación lidar" del commit `3eb1129`.

**Cómo lanza (`_spawn`, líneas 164-184):** `/bin/bash -lc "<prefijo ROS>; exec <comando>"`,
con `start_new_session=True`, salida redirigida a `/tmp/safevision_runtime_logs/<nombre>.log`
y el PID anotado en el estado. **Cómo mata (`_terminate_owned`, líneas 187-212):**
`SIGINT` → 2 s, `SIGTERM` → 1,5 s, `SIGKILL`, siempre sobre el *process group*.

#### Tabla recurso → qué lanza

| Recurso | Función | Comando real | Nodos esperados |
|---|---|---|---|
| `driver` | `_ensure_driver` (`:517`) | `rosrun yahboomcar_bringup Mcnamu_driver.py /pub_vel:=/vel_raw /pub_imu:=/imu/imu_raw /pub_mag:=/mag/mag_raw` | `/driver_node` |
| `core` | `_ensure_core` (`:549`) | `roslaunch sf_runtime_core.launch` | `/odometry_publisher`, `/imu_filter_madgwick`, `/ekf_localization` + dato en `/imu/imu_data` |
| `selector` | `_ensure_selector` (`:601`) | `python3 sf_cmd_vel_selector.py` | `/sf_cmd_vel_selector` + servicio `/safevision/set_navigation_mode` |
| `lidar` | `_ensure_lidar` (`:363`) | `roslaunch sf_runtime_lidar.launch` | `/rplidarNode`, `/base_link_to_laser` + dato en `/scan` |
| `localization` | `_ensure_localization` (`:449`) | `roslaunch sf_localizacion_mapa.launch map_file:=<yaml>` | `/amcl`, `/sf_map_server` + tópico `/map` |
| `pose_exporter` | `_ensure_pose_exporter` (`:464`) | `/usr/bin/python sf_pose_exporter.py` | `/safevision_pose_exporter` |
| `navigation` | `_ensure_navigation` (`:472`) | `roslaunch sf_navegacion.launch` | `/move_base` + servicio `/move_base/make_plan` |
| `nav_queue` | `_ensure_nav_queue` (`:483`) | `python3 sf_nav_queue.py` | `/sf_nav_queue` |
| `mando` | `_ensure_mando` (`:673`) | `roslaunch sf_control_mando.launch` (exige `/dev/input/js0`) | `/joy_node`, `/yahboom_joy` |
| `teclado` | `set_control_mode` (`:715`) | **ningún proceso**: sólo apaga el mando | — |

#### Perfiles (`apply_profile`, `:1442-1610`)

Cuatro perfiles: `libre`, `pilotada`, `automatica`, `mapear`.

- **Base común** (`_ensure_base`, `:816-923`), obligatoria para todos: `driver` → `core`
  → `selector` → control. Si falla un escalón, aborta con `ok:false` y HTTP 409.
- **`libre`**: apaga en orden `nav_queue` → `navigation` → `pose_exporter` →
  `localization` → `lidar`, borra el mapa activo y verifica que ninguno siga vivo.
- **`pilotada` / `automatica`**: exigen `map` válido (`_safe_map`, `:305-312`: sin `/`,
  `\` ni `..`, y con `<mapa>.yaml` existente en `mapping/maps/`), escriben
  `/tmp/safevision_active_map.json` y encienden en orden `lidar` → `localization` →
  `pose_exporter` → `navigation` → `nav_queue`. Verifican al final que los cinco estén
  activos. **La diferencia entre `pilotada` y `automatica` es sólo la etiqueta del
  mensaje** (`:1596-1600`); levantan exactamente los mismos recursos. CONFIRMADO.
- **`mapear`**: **no se puede aplicar directamente**. `apply_profile("mapear")` sólo
  acepta confirmar un Gmapping ya activo; si no, devuelve *"Mapear se inicia mediante
  `/mapping/session/start`"* (`:1480-1487`).

#### Coreografía de mapeo (CONFIRMADO)

El baile entre `sf_runtime_manager` y `sf_mapping_manager` está en
`sf_robot_server.py:4248-4485`:

```
POST /mapping/session/start
  ├─ MISSION_RUNTIME.status() ................ rechaza si hay misión automática corriendo
  ├─ sf_runtime_manager.prepare_mapping() .... exige perfil pilotada|automatica + mapa
  │                                            y los 7 recursos activos; guarda
  │                                            resume_profile / resume_map_name
  ├─ sf_mapping_manager.start(name) .......... lanza sf_mapeo_gmapping.launch
  │      └─ si falla: shutdown() + restore_after_mapping()  (rollback)
  └─ sf_runtime_manager.mark_mapping_started()
         apaga nav_queue → navigation → pose_exporter y suelta el roslaunch
         de localización; si no puede, discard() + shutdown() + restore  (rollback)

POST /mapping/session/save | /discard
  └─ sf_mapping_manager.save()/discard() → shutdown() → restore_after_mapping()
         → apply_profile(resume_profile, map=<mapa restaurado>)
```

Nótese el orden deliberado (comentario en `sf_runtime_manager.py:1020-1022`):
`nav_queue` se mantiene vivo **durante** `start()` porque `sf_mapping_manager` necesita
publicar el `cancel` de navegación antes de retirar AMCL/`map_server`. Esto implementa
"rollback de mapping" y "mapa asociado a cola" del handoff §57; **no debe romperse**.

### 2.7 Ficheros `.launch` del camino A

| Launch | Contenido | Quién lo usa |
|---|---|---|
| `sf_runtime_core.launch` (124 l.) | `robot_description` (xacro), `joint_state_publisher`, `robot_state_publisher`, `odometry_publisher` (`base_node`), `apply_calib`, `imu_filter_madgwick`, `ekf_localization`. **No** arranca driver, LiDAR, mapa, AMCL, `move_base` ni controles. | sólo `sf_runtime_manager.py:570` |
| `sf_runtime_lidar.launch` (25 l.) | `rplidarNode` (`/dev/rplidar`, 115200, frame `laser`) + TF estática `base_link → laser` `0.0435 0 0.11 3.1416 0 0`. | sólo `sf_runtime_manager.py:403` |
| `sf_localizacion_mapa.launch` (65 l.) | `map_server` (nombre `sf_map_server`) + `include` de `yahboomcar_nav/launch/library/amcl.launch` con `odom_model_type:=omni`; fija `/amcl/update_min_d=0.10` y `update_min_a=0.10`. | `sf_runtime_manager.py:452` y `sf_mapping_manager.py:35` |
| `sf_navegacion.launch` (56 l.) | `move_base` con los 6 YAML de `robot/nav/` **por ruta absoluta**; `remap cmd_vel → /cmd_vel_nav`, `odom → /odom`. | `sf_runtime_manager.py:475` y `sf_operacion_pilotada.sh:456` |
| `sf_control_mando.launch` (40 l.) | `joy_node` + `yahboom_joy` con `remap cmd_vel → /cmd_vel_manual`. | `sf_runtime_manager.py:689` y `sf_operacion_pilotada.sh:515` |
| `sf_mapeo_gmapping.launch` (22 l.) | sólo `include` de `yahboomcar_nav/launch/library/gmapping.launch`. | sólo `sf_mapping_manager.py:29` |

**CONFIRMADO:** `sf_runtime_core.launch` + `sf_runtime_lidar.launch` +
`sf_localizacion_mapa.launch` son, juntos, una **descomposición** de
`sf_localizacion.launch` (177 líneas, camino B), que hacía las tres cosas de golpe. Esa
descomposición es exactamente lo que permite encender y apagar el LiDAR y AMCL sin tirar
la odometría, y por tanto lo que hace posible el ciclo de mapeo.

**Riesgo de contenerización (Fase 6):** las rutas absolutas `/home/pi/robot_custom/...`
están incrustadas en `sf_navegacion.launch:13-41` y en `sf_runtime_manager.py:15-22`.

---

## 3. Camino B — `sf_operacion_pilotada.sh` (legacy, aún alcanzable)

Fichero: `misiones/pilotada/robot/sf_operacion_pilotada.sh` (561 líneas).
Uso: `sf_operacion_pilotada.sh teclado|mando [mapa]` (mapa por defecto `HAB2`, línea 4).

Secuencia declarada como `[n/9]`:

| Etapa | Qué hace | Comprobación / timeout |
|---|---|---|
| 1/9 | `roscore` si no hay Master (l. 196-223) | 20 × 0,5 s |
| 2/9 | `rosrun yahboomcar_bringup Mcnamu_driver.py` (l. 226-264) | **aborta si `/driver_node` ya existe** (l. 228-233); 30 × 0,25 s |
| 3/9 | `roslaunch sf_localizacion.launch map_file:=<yaml>` (l. 267-342) | espera `/amcl` + `/ekf_localization` + `/imu_filter_madgwick` + `/rplidarNode` (80 × 0,5 s), `sleep 7` de calibración IMU, y dato en `/imu/imu_data` y `/scan` |
| 4/9 | `/usr/bin/python sf_pose_exporter.py` (l. 345-375) | 30 × 0,25 s |
| 5/9 | `python3 sf_robot_server.py --control $CONTROL` (l. 378-408) | `curl http://127.0.0.1:8091/`, 40 × 0,25 s |
| 6/9 | `python3 sf_cmd_vel_selector.py` (l. 428-451) | 20 × 0,25 s |
| 7/9 | `roslaunch sf_navegacion.launch` (l. 454-477) | 30 × 0,5 s |
| 8/9 | `python3 sf_nav_queue.py` (l. 480-504) | 20 × 0,25 s |
| 9/9 | `mando`: `sf_control_mando.launch` + `sf_modo_espera.py mando` (l. 506-532) · `teclado`: `sf_modo_espera.py teclado` y luego `sf_control_teclado.launch` en primer plano (l. 534-561) | — |

Cierre: `trap cerrar EXIT/INT/TERM` (l. 144-146) apaga en orden inverso con `SIGINT` →
`sleep 3` → `SIGTERM` → `SIGKILL`, y borra `/tmp/safevision_active_map.json` (l. 88-131).

### 3.1 ¿Sigue siendo alcanzable? — **SÍ** (CONFIRMADO)

Cadena completa, toda ella trazada con `git grep`:

```
api/main_menu.py:8            from safevision import menu_safevision
api/safevision.py:43          ejecutar_script("menu_operacion.py")
api/menu_operacion.py:38-41   subprocess.run([sys.executable,
                              "/home/pi/robot_custom/misiones/pilotada/robot/sf_mision_pilotada.py"])
misiones/pilotada/robot/sf_mision_pilotada.py:250-260
                              ejecutar(["bash", str(ROBOT_DIR/"sf_operacion_pilotada.sh"),
                                        control, mapa])
```

No hay ninguna otra referencia: `git grep sf_operacion_pilotada` sólo devuelve
`CLAUDE.md`, `docs/handoff-2026-09.md` y `sf_mision_pilotada.py:252`.

**Por tanto, según el criterio del handoff §77 y de `CLAUDE.md`, `sf_operacion_pilotada.sh`
NO es código muerto: está referenciado por un menú.** Tampoco lo son
`sf_mision_pilotada.py`, `sf_localizacion.launch` (único consumidor: este script, l. 274) ni
`sf_control_teclado.launch` (único consumidor: este script, l. 560).

### 3.2 Los dos caminos se excluyen entre sí (CONFIRMADO)

- El script **aborta** si `/driver_node` ya está activo (l. 228-233). Con los servicios
  systemd activos *y* un perfil aplicado, el driver ya existe → el camino B falla en la
  etapa 2/9.
- El script arranca **su propio** `sf_robot_server.py` en la etapa 5/9. Si el servicio
  systemd ya escucha en `8091`, el segundo Flask no podrá abrir el puerto.
- El script llama a `sf_modo_espera.py`, que compite por la misma semántica de "listo"
  que `/health`. El handoff §15 ya señalaba esta inconsistencia; sigue viva.

**RECOMENDACIÓN:** tratar el camino B como *fallback manual de laboratorio*, documentarlo
como tal, y **no** eliminarlo hasta que la operación pilotada completa (selección de mapa
+ control) esté disponible en el Dashboard sobre el camino A. Ver §6.

---

## 4. Diagrama de arranque (forma textual)

### 4.1 Arranque de la máquina — lo que ocurre solo

```
                       [ Raspberry Pi enciende ]
                                  │
                       network-online.target
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
        ▼                                                   │
 safevision-roscore.service                                 │ Requires=
   └─ sf_roscore_service.sh                                 │ After=
        ├─ source /opt/ros/melodic/setup.bash               │
        ├─ source ~/yahboomcar_ws/devel/setup.bash          │
        ├─ resolve_ip()  (wlan0 → hostname -I)   ≤60 s      │
        ├─ export ROS_IP / ROS_MASTER_URI / ROBOT_TYPE=X3   │
        └─ exec roscore -p 11311 ───────────────────────────┤
                                                            ▼
                                      safevision-robot-server.service
                                        └─ sf_robot_server_service.sh
                                             ├─ source ROS + yahboomcar_ws
                                             ├─ resolve_ip()          ≤60 s
                                             ├─ espera `rosnode list` ≤20 s
                                             ├─ cd .../pilotada/robot
                                             └─ exec /usr/local/bin/python3
                                                  sf_robot_server.py --control mando
                                                     ├─ rospy.init_node(
                                                     │    safevision_robot_server)
                                                     ├─ pub  /safevision/nav/command
                                                     ├─ pub  /cmd_vel_manual
                                                     ├─ sub  /safevision/nav/status
                                                     ├─ sub  /map
                                                     ├─ sf_mapping_manager.configure()
                                                     └─ Flask 0.0.0.0:8091

  ESTADO RESULTANTE:  roscore  +  Robot Server.  Nada más.
  (la cámara se abre en la primera petición a /video_feed)
```

### 4.2 Puesta en marcha del robot — lo que requiere una orden HTTP

```
  cliente HTTP ──► POST /runtime/profile {"profile":"pilotada","map":"HAB2",
                                          "control":"mando"}
                      │  sf_robot_server.py:622-648
                      ▼
                 sf_runtime_manager.apply_profile()
                      │
                      ├─ _ensure_base()
                      │    ├─ driver     rosrun Mcnamu_driver.py          → /driver_node
                      │    ├─ core       roslaunch sf_runtime_core.launch → /odometry_publisher
                      │    │                                                /imu_filter_madgwick
                      │    │                                                /ekf_localization
                      │    │                                                + dato en /imu/imu_data
                      │    ├─ selector   python3 sf_cmd_vel_selector.py   → /sf_cmd_vel_selector
                      │    │                                                srv set_navigation_mode
                      │    └─ control    set_control_mode("mando")
                      │                   roslaunch sf_control_mando.launch
                      │                     (exige /dev/input/js0)        → /joy_node, /yahboom_joy
                      │
                      ├─ _safe_map("HAB2") + escribe /tmp/safevision_active_map.json
                      │
                      ├─ lidar          roslaunch sf_runtime_lidar.launch → /rplidarNode
                      │                   (+ exige mensaje en /scan; 2 reintentos)
                      ├─ localization   roslaunch sf_localizacion_mapa.launch
                      │                   map_file:=mapping/maps/HAB2.yaml
                      │                                                   → /sf_map_server, /amcl
                      ├─ pose_exporter  /usr/bin/python sf_pose_exporter.py
                      │                                                   → /safevision_pose_exporter
                      ├─ navigation     roslaunch sf_navegacion.launch    → /move_base
                      │                                                     srv /move_base/make_plan
                      └─ nav_queue      python3 sf_nav_queue.py           → /sf_nav_queue

  ESTADO RESULTANTE: runtime pilotado completo.
```

### 4.3 Camino de la velocidad (idéntico en ambos caminos)

```
  mando  → /yahboom_joy ──────────┐
  web    → POST /runtime/keyboard ┤──► /cmd_vel_manual ──┐
                                                         │
  move_base ─────────────────────────► /cmd_vel_nav ─────┤
                                                         ▼
                                         sf_cmd_vel_selector
                                           · modo manual | navigation
                                           · watchdog 0,5 s → Twist() a cero
                                           · srv /safevision/set_navigation_mode
                                             (al pasar a manual publica
                                              /move_base/cancel)
                                                         │
                                                         ▼
                                                     /cmd_vel ──► driver_node
```

**CONFIRMADO** en `sf_cmd_vel_selector.py:19-24` (timeout 0,5 s por defecto), `:68-71`
(timer a 20 Hz), `:121-135` (watchdog) y `:137-167` (cambio de modo + cancel).

---

## 5. Veredicto: cuál launcher está vivo

**Camino A (systemd + `sf_runtime_manager`) es el vigente.**
Etiqueta: **IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN** — el código es
inequívoco; lo que este entorno no puede probar es que las unidades estén *instaladas y
habilitadas* en la Pi.

Evidencia a favor (toda CONFIRMADA en el repositorio):

1. **Cronología.** Los 10 commits posteriores al tag auditado son todos del lado robot y
   construyen el camino A: `22b42c6` (observabilidad y base modular) → `70f96c4`
   (perfiles libre/pilotada) → `0b0d0b3` (independiza runtime, control por API) →
   `fa8f8b2` (**instala servicios permanentes del runtime**, 2026-08-20) → `65be9ab`
   (perfil automática) → `a8a7aea` (perfil mapear) → `3eb1129` (teclado web + recuperación
   LiDAR).
2. **El Robot Server depende del gestor, no al revés.** `sf_robot_server.py:38` importa
   `sf_runtime_manager`, y lo usa en 10 puntos (`:616, :638, :666, :775, :4280, :4310,
   :4324, :4346, :4399, :4451`). El flujo de mapeo — que es funcionalidad actual, usada
   por el Dashboard — **no funciona sin él**.
3. **El camino B no puede coexistir.** Aborta si `/driver_node` existe
   (`sf_operacion_pilotada.sh:228-233`) y reclama el puerto `8091`.
4. **Los `.launch` nuevos sólo los usa el camino A.** `sf_runtime_core.launch` y
   `sf_runtime_lidar.launch` no aparecen en ningún otro sitio.
5. **La copia cruda de la Pi (`~/safevision-raw/`) es idéntica a `HEAD`** en
   `misiones/pilotada/robot/` (`diff -rq` sin diferencias), e incluye
   `misiones/pilotada/systemd/` con ambas unidades. Las marcas de tiempo sitúan los
   scripts de servicio (12:04) y `sf_runtime_manager.py` (14:49) por encima de
   `sf_operacion_pilotada.sh` (16-ago 22:44).

Evidencia que **no** pudo obtenerse (INCONCLUSO):

- No existe en el repositorio **ningún script que instale las unidades**: `git grep
  systemctl` sólo devuelve `network/wifi_manager.sh:46`. La copia a
  `/etc/systemd/system/` y el `systemctl enable` se hicieron a mano en la Pi.
- `~/safevision-raw/` es una copia de `robot_custom`, no del sistema de ficheros de la
  Pi: no contiene `/etc/systemd/`, `crontab` ni `.bashrc`.

**Comprobaciones que lo cerrarían (a ejecutar en el robot, por una persona):**

```bash
systemctl is-enabled safevision-roscore safevision-robot-server
systemctl status    safevision-roscore safevision-robot-server
diff /etc/systemd/system/safevision-roscore.service \
     ~/robot_custom/misiones/pilotada/systemd/safevision-roscore.service
diff /etc/systemd/system/safevision-robot-server.service \
     ~/robot_custom/misiones/pilotada/systemd/safevision-robot-server.service
crontab -l; grep -rn robot_custom ~/.bashrc ~/.profile
/usr/local/bin/python3 -c "import sys, rospy, cv2, flask; print(sys.version)"
```

---

## 6. Divergencias detectadas entre código, handoff y `CLAUDE.md`

| # | Afirmación | Realidad en `HEAD` | Etiqueta |
|---|---|---|---|
| 1 | Handoff §11: `sf_operacion_pilotada.sh` es el arranque del runtime pilotado | Es un camino secundario; el arranque real es systemd + `sf_runtime_manager` | CONFIRMADO |
| 2 | Handoff §44 (orden de lectura): empezar por `sf_operacion_pilotada.sh` | Debe empezarse por las unidades systemd, `sf_robot_server_service.sh` y `sf_runtime_manager.py` | RECOMENDACIÓN |
| 3 | Handoff §45: `sf_robot_server.py` ≈ 4.300 líneas | 5.060 líneas | CONFIRMADO |
| 4 | Handoff §45: `sf_mapping_manager.py` ≈ 1.800 líneas | 1.828 líneas (correcto) | CONFIRMADO |
| 5 | `CLAUDE.md` §10: el código ROS corre bajo el Python 2.7 de Melodic | Sólo `sf_pose_exporter.py`. El resto es Python 3; el Robot Server usa `/usr/local/bin/python3` | CONFIRMADO |
| 6 | `CLAUDE.md`: `sf_runtime_manager.py` "probablemente sustituye partes de `sf_operacion_pilotada.sh`" | Lo sustituye **entero**, y además añade capacidades que el script no tenía (perfiles, apagado selectivo, recuperación de LiDAR, ciclo de mapeo) | CONFIRMADO |
| 7 | Comentario en `sf_robot_server.py:605-608`: *"RUNTIME MANAGER · ETAPA 1 · Observabilidad solamente. No arranca ni detiene nodos."* | Obsoleto: `POST /runtime/profile` arranca y detiene nodos desde `:638` | CONFIRMADO |
| 8 | Handoff §12: la etiqueta "Nivel 3 / Navegación asistida / FUTURO" está desactualizada | Sigue igual en `sf_mision_pilotada.py:284`, y `sf_operacion_pilotada.sh:157` aún imprime `Nivel : 2`. `sf_robot_server.py:458` sigue devolviendo `"level": 2` | CONFIRMADO |

### 6.1 Hallazgo nuevo y relevante: el camino A **no tiene cliente en el repositorio**

`git grep "runtime/profile\|runtime/control\|runtime/status\|runtime/keyboard"` sólo
encuentra definiciones en `sf_robot_server.py` (`:462-464, :612, :623, :651, :763`).
**Ningún consumidor.** Concretamente:

- `misiones/pilotada/dashboard_src/` no menciona `perfil`/`profile` ni `teclado`/`keyboard`
  en ningún `.py`, `.js` o `.html` (búsqueda vacía).
- El último commit que toca `dashboard_src/` es **`73b187d`, es decir el propio tag
  auditado**. `git log 73b187d..HEAD -- misiones/pilotada/dashboard_src/` está vacío.

**Consecuencia (CONFIRMADO):** tal como está `HEAD`, tras el arranque por systemd el robot
queda en `roscore` + Robot Server, y **la única forma documentada de llevarlo a un perfil
operativo es una petición HTTP manual**, por ejemplo:

```bash
curl -X POST http://<ip-robot>:8091/runtime/profile \
     -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'
```

Además, `POST /mapping/session/start` **falla por diseño** si antes no se aplicó un perfil
`pilotada` o `automatica`: `prepare_mapping` exige `requested_profile` en
`("pilotada","automatica")` y un mapa activo (`sf_runtime_manager.py:970-988`), y ese
estado sólo lo escribe `apply_profile`.

**INCONCLUSO:** si existe un Dashboard más nuevo fuera del repositorio (en la PC de
desarrollo, sin commitear) que sí consuma `/runtime/*`. Lo resolvería comparar
`misiones/pilotada/dashboard_src/` con la copia viva de la PC, o preguntar al autor.
Mientras tanto, **la hipótesis más conservadora es que el frontend va por detrás del
backend en 10 commits** y que la operación se está haciendo con `curl` o con un
Dashboard local no versionado.

### 6.2 Inconsistencia de `/health` en modo teclado (CONFIRMADO)

`sf_robot_server.py:563-567`: con `CONTROL_MODE == "teclado"`, `/health` exige el nodo
`/yahboom_keyboard` para dar `control: true`. Pero en el camino A el modo teclado **no
lanza ningún nodo**: `sf_runtime_manager.set_control_mode("teclado")` sólo apaga el mando
(`:750-757`), y `status()` lo reporta como `implementation: "dashboard_keyboard"`
(`:1406-1409`), porque el teclado web publica directo en `/cmd_vel_manual` desde
`POST /runtime/keyboard`.

**Resultado:** en el camino A, modo teclado, `/health` devolverá siempre `ok: false`.
Es la misma familia de problema que el handoff §15 señalaba entre `/health` y
`sf_modo_espera.py`. **RECOMENDACIÓN:** no parchear ahora; resolverlo en la Fase 2
(contrato `RobotHealth`) definiendo `control` en términos de *capacidad de mandar
`cmd_vel_manual`*, no de la presencia de un nodo concreto.

---

## 7. Preguntas que sólo puede responder alguien con acceso al robot

1. ¿Están `safevision-roscore.service` y `safevision-robot-server.service` copiadas en
   `/etc/systemd/system/` y habilitadas (`systemctl is-enabled`)? ¿Coinciden byte a byte
   con las del repositorio?
2. ¿Qué es `/usr/local/bin/python3` (versión, cómo se instaló, qué `rospy` usa) y está
   documentado en algún sitio fuera del repositorio?
3. Al hacer `systemctl stop safevision-robot-server`, ¿mueren también los nodos lanzados
   por `sf_runtime_manager` (driver, LiDAR, AMCL, `move_base`), o quedan huérfanos?
4. ¿Cómo se aplica hoy un perfil en la operación real: `curl`, un Dashboard no
   versionado, o no se usa el camino A todavía?
5. ¿Sigue usándose `api/main_menu.py` en la Pi (por `.bashrc`, un alias o un `cron`), y
   por tanto el camino B?
6. Tras un reinicio completo, con `/tmp` vacío, ¿el sistema queda operativo o requiere
   siempre una acción manual?
7. ¿Existe `/dev/rplidar` como regla `udev` estable? `sf_runtime_lidar.launch:11` depende
   de ese nombre.
8. ¿Existe el directorio `misiones/pilotada/payload/`? `sf_servidor_descarga.py:11-14`
   espera ahí `SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz`; en este repositorio no existe.

---

## 8. Qué NO se hizo en esta sesión

- No se ejecutó ROS, `roslaunch`, `rospy` ni el Robot Server (no están disponibles aquí).
- No se modificó, movió ni borró ningún fichero fuera de `docs/`.
- No se propone ni se inicia ningún refactor: eso corresponde a una sesión posterior,
  después de la revisión humana de este documento, de `docs/inventory.md` y de
  `docs/security-scan.md`.
