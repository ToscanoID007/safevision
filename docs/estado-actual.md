# Estado operativo real del robot

**Para quién es y cuándo leerlo**
Para quien va a operar, mantener o continuar SafeVision y necesita saber qué está
realmente instalado y funcionando en el robot, no qué debería estar.
Léelo antes de instalar nada, antes de dar por buena cualquier prueba, y antes de
prometerle algo al profesor. Es la foto verificada; el resto de documentos se apoyan en ella.

---

**Fecha de la verificación:** 2026-09-10 (el Robot Server respondió con
`Date: Fri, 11 Sep 2026 04:45:43 GMT`)
**Robot:** `yahboom.local` → **192.168.1.13**
**Rama:** `docs/entrega` · **Base:** `wip-handoff` (`ee956ad`)
**Método:** peticiones HTTP GET de sólo lectura al Robot Server + análisis estático del
repositorio + búsqueda de sólo lectura en `/home/toscano`.

> **Alcance de esta verificación.** Se verificó **en el robot real**, por SSH de sólo
> lectura y por peticiones HTTP GET. El propietario del equipo autorizó expresamente el uso
> de la contraseña para esta sesión. No se ejecutó ninguna orden que mueva el robot o
> cambie su estado: nada de `sudo`, `systemctl start|stop|enable`, `roslaunch`, `rosrun`,
> `rostopic pub` ni peticiones HTTP distintas de GET. Lo que sigue es observación, no
> intervención.

Etiquetas de certeza (handoff §0): **CONFIRMADO** · **IMPLEMENTADO EN FUENTE, PENDIENTE DE
REVALIDACIÓN** · **RECOMENDACIÓN**. Se añade **[PENDIENTE]** para lo que debe aportar una
persona.

---

## 1. Conclusión (lo único que hay que recordar)

**Tras un arranque en frío, el robot NO queda operable desde el dashboard versionado en
este repositorio. Hace falta un paso manual.** **CONFIRMADO en el robot, hoy, sobre un
arranque en frío real:** el equipo llevaba `1h 55min` encendido, con los dos servicios
systemd activos desde el arranque, y el perfil seguía en `null`.

El robot arranca solo hasta aquí:

- ROS Master vivo (`ros_master: true`)
- Robot Server vivo y sirviendo en `:8091`
- Cámara detectada y transmitiendo vídeo
- Mando físico conectado (`joystick: true`)

Y se queda ahí. **Ningún recurso de movimiento está activo:** driver, core (IMU/EKF/odometría),
LiDAR, localización (AMCL), `move_base`, cola de navegación y selector de `cmd_vel`
aparecen todos `inactive`, y el perfil solicitado es `null`.

El paso manual que falta es **aplicar un perfil de runtime**:

```bash
curl -X POST http://192.168.1.13:8091/runtime/profile \
     -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'
```

**Pero hay una vuelta de tuerca decisiva, y es buena noticia:** ese botón **ya existe**,
sólo que **nunca se subió al repositorio**. En el portátil, en
`~/SafeVision_Dashboard_dev/`, hay una versión del dashboard **un día más nueva** que la
versionada, con una página `/pilotada` y los cuatro proxies `/runtime/*` que faltan.
Ver §5. **Ese es el hallazgo más importante de esta sesión.**

Por tanto el problema real no es *"falta funcionalidad"* sino ***"la funcionalidad que
funciona no está versionada"***. Se arregla publicando, no programando.

---

## 2. Qué está corriendo ahora mismo (CONFIRMADO)

`GET http://192.168.1.13:8091/health`:

```json
{
  "ok": false,
  "control_mode": "mando",
  "ros_master": true,
  "driver": false,
  "lidar": false,
  "camera": true,
  "control": false,
  "joystick": true,
  "map": { "enabled": false, "level": 2 },
  "ip": "192.168.1.13",
  "level": 2
}
```

`GET http://192.168.1.13:8091/runtime/status` (resumen):

| Recurso | Estado | Lectura |
|---|---|---|
| `ros_master` | **active** | `roscore` vivo en `http://192.168.1.13:11311` |
| `robot_server` | **active** | puerto 8091 |
| `camera` | **active** | `/dev/video0` o `/dev/video1` presente |
| `mando` | inactive (`connected: true`) | el joystick está enchufado pero los nodos no corren |
| `driver` | inactive | sin `/driver_node` |
| `core` | inactive | faltan `/odometry_publisher`, `/imu_filter_madgwick`, `/ekf_localization` |
| `lidar` | inactive | sin `/rplidarNode` ni `/scan` |
| `localization` | inactive | sin `/amcl` ni `/sf_map_server` |
| `pose_exporter` | inactive | — |
| `selector` | inactive | sin `/sf_cmd_vel_selector` |
| `navigation` | inactive | sin `/move_base` |
| `nav_queue` | inactive | sin `/sf_nav_queue` |
| `mapping` | inactive | sin `/slam_gmapping` |
| `teclado` | inactive | `implementation: "dashboard_keyboard"` |

Y el bloque de perfil, que es la prueba directa:

```json
"profile": { "requested": null, "inferred": "base", "map": null },
"manager_version": 5,
"mode": "active_profiles",
"hostname": "yahboom"
```

`requested: null` significa literalmente que **nadie ha aplicado nunca un perfil desde que
arrancó el Robot Server**. `inferred: "base"` es el escalón más bajo por encima de "off".

Esto **confirma empíricamente** lo que la sesión anterior dedujo sólo leyendo el código
(`runtime-boot.md` §6.1). La deducción era correcta.

### 2.1 Lo que sí funciona hoy sin tocar nada

| Comprobación | Resultado | Certeza |
|---|---|---|
| `GET /` | responde, `service: SafeVision Robot Server` | CONFIRMADO |
| `GET /video_feed` | HTTP 200, `multipart/x-mixed-replace`, ~2,5 MB en 5 s (≈4 Mbit/s) | CONFIRMADO |
| `GET /maps` | 6 mapas: `HAB2`, `Hab2Tos`, `Habitacion_toscano`, `habitacion_toscano`, `habitacion_toscano2`, `nombre_de_tu_mapa` | CONFIRMADO |
| `GET /models` | modelo `yolov` (4 clases: persona, telefono, lentes, botas) + `yolov8n` | CONFIRMADO |
| `GET /missions` | 1 misión: `Prueba_Sync_Pi.sfmision` | CONFIRMADO |
| `GET /mission/status` | `state: idle` | CONFIRMADO |
| `GET /nav/status` | `state: unavailable` — coherente, la cola no corre | CONFIRMADO |
| `GET /mapping/session/status` | `state: idle`, faltan `/rplidarNode`, `/ekf_localization`, `/odometry_publisher` | CONFIRMADO |
| `GET /map_pose` | `localized: false` — coherente, AMCL no corre | CONFIRMADO |

**Observación para el profesor:** la cámara y todo el catálogo (mapas, modelos, misiones)
funcionan desde el primer segundo. Lo que no arranca solo es la parte que mueve el robot.
Es, de hecho, un comportamiento **seguro por defecto**: el robot no puede moverse hasta
que alguien lo pide explícitamente.

### 2.2 Higiene de datos (RECOMENDACIÓN, no urgente)

De los 6 mapas, cuatro son claramente pruebas y uno es un nombre de ejemplo sin limpiar
(`nombre_de_tu_mapa`); tres son variantes de "habitación toscano" que difieren sólo en
mayúsculas. Antes de la entrega conviene dejar **un solo mapa bueno y documentado**
(`HAB2` es el que el código usa por defecto, `sf_operacion_pilotada.sh:4`) y borrar el
resto desde el dashboard. No es un defecto técnico; es presentación.
**[PENDIENTE: decisión del profesor o del estudiante sobre qué mapas conservar.]**

---

## 3. Versiones e intérprete (CONFIRMADO en el robot)

| Elemento | Valor |
|---|---|
| Sistema | **Ubuntu 18.04.6 LTS (Bionic Beaver)**, `aarch64` |
| Kernel | `5.4.0-1050-raspi` |
| ROS | **Melodic**, `ros_comm` 1.14.13, **451** paquetes `ros-melodic-*` |
| `/usr/local/bin/python3` | **3.7.3** — ejecuta el Robot Server |
| `/usr/bin/python3` | 3.6.9 — el de Ubuntu; **SafeVision no lo usa** |
| `/usr/bin/python` | 2.7.17 — ejecuta `roscore` y `sf_pose_exporter.py` |
| Flask / Werkzeug | 2.2.5 / 2.2.3 |
| Disco raíz | 59 GB, 29 GB usados (51 %) |

La cabecera HTTP del propio servidor lo confirma sin necesidad de entrar:
`Server: Werkzeug/2.2.3 Python/3.7.3`.

### 3.1 Por qué hay tres Python, y por qué no se pueden unificar

Éste es el detalle menos evidente del sistema y el que más fácilmente se rompe al
"modernizar". **CONFIRMADO por prueba directa en el robot.**

`rospy` está instalado **sólo** en el árbol de Python 2
(`/opt/ros/melodic/lib/python2.7/dist-packages/rospy`). El servicio hace que Python 3.7
lo importe desde ahí mediante `PYTHONPATH` (capturado de `/proc/<pid>/environ`).
Funciona porque `rospy`, `actionlib` y los paquetes de mensajes son **Python puro**.

Lo que **no** funciona bajo Python 3.7:

```
>>> import tf
from ._tf2 import *
ImportError: dynamic module does not define module export function (PyInit__tf2)
```

`tf` arrastra `_tf2.so`, una extensión C **compilada para Python 2**.

Y `sf_pose_exporter.py` es **el único fichero del runtime que importa `tf`** (línea 10;
comprobado con `grep` sobre todo `misiones/*/robot/*.py`). De ahí que sea el único con
`#!/usr/bin/env python` y que se invoque con `/usr/bin/python`.

> **No es código heredado ni un descuido: es obligatorio.** Quien pase
> `sf_pose_exporter.py` a Python 3 romperá la pose del robot en el mapa.
> Corrige la regla 10 de `CLAUDE.md`, que lo tenía al revés.

Detalle completo en `docs/anexo-dependencias-robot.md` §2.

### 3.2 Dos avisos del manifiesto

1. **Tres OpenCV instalados a la vez** (`opencv-python` 5.0.0.93,
   `opencv-python-headless` 5.0.0.93 y `opencv-contrib-python` 4.5.4.60). Hay una traza
   real del conflicto en `robot_server.log`. El vídeo funciona hoy; **no tocar antes de la
   entrega**, y sólo después de respaldar la SD.
2. **`torch` 1.13.1 y `ultralytics` 8.0.145 están instalados en el robot**, aunque el
   runtime vigente no los importa. Son restos de la generación anterior
   (`api/nodo_yolo_pi.py`). Contradice lo que asume el handoff §17-18. No desinstalar
   ahora; anotarlo como deuda.

---

## 4. Servicios systemd (CONFIRMADO)

Las dos unidades **están instaladas, habilitadas y son idénticas a las del repositorio**:

```
$ systemctl is-enabled safevision-roscore safevision-robot-server
enabled
enabled

$ diff /etc/systemd/system/safevision-roscore.service \
       ~/robot_custom/misiones/pilotada/systemd/safevision-roscore.service
roscore: IDENTICO
robot-server: IDENTICO
```

```
● safevision-roscore.service — SafeVision ROS Master
   Loaded: loaded (/etc/systemd/system/safevision-roscore.service; enabled)
   Active: active (running) since Fri 2026-09-11 10:52:15 CST; 1h 55min ago
 Main PID: 2097 (roscore)

● safevision-robot-server.service — SafeVision Robot Server
   Loaded: loaded (/etc/systemd/system/safevision-robot-server.service; enabled)
   Active: active (running) since Fri 2026-09-11 10:52:15 CST; 1h 55min ago
 Main PID: 2101 (/usr/local/bin/python3 .../sf_robot_server.py --control mando)
```

**Esto cierra la pregunta abierta de la sesión anterior, y de la forma más contundente
posible.** El `uptime` del equipo era `1:55` y ambos servicios llevaban `1h 55min`
activos: **arrancaron solos en el arranque en frío**. Y sin embargo
`profile.requested` seguía siendo `null` casi dos horas después.

> No es una suposición sobre qué pasaría tras un reinicio: **es lo que pasó**.
> El robot lleva dos horas encendido, con los servicios correctos, sin poder moverse.

El camino de arranque descrito en `runtime-boot.md` §2 queda así **CONFIRMADO de extremo a
extremo**, incluida la parte que era sólo inferencia.

---

## 5. El dashboard no versionado — hallazgo principal
**CONFIRMADO.** En el portátil existe una copia de trabajo del dashboard **más nueva que
la versionada**, y es la que tiene el control de perfiles.

### 5.1 Qué se encontró

| | Repositorio (`misiones/pilotada/dashboard_src/`) | Portátil (`~/SafeVision_Dashboard_dev/`) |
|---|---|---|
| Último cambio | 2026-08-19 15:59 (commit `73b187d`, **el propio tag auditado**) | 2026-08-20 17:37 |
| `sf_app_dashboard.py` | 4.112 líneas | **4.315 líneas** |
| Rutas Flask | 66 | **71** |
| Página de pilotaje | — | `templates/pilotada_v2.html` (12,9 kB) |
| JS de pilotaje | — | `static/pilotada_v2.js` (50,9 kB) + `pilotada_v2.css` (20,4 kB) |
| JS de portada | — | `static/home.js` (21,4 kB) |
| `templates/index.html` | 9,3 kB | **21,5 kB** |
| `static/app.js` | 135,1 kB | **168,8 kB** |
| `static/automatica.js` | 151,1 kB | **176,2 kB** |
| `static/style.css` | 19,9 kB | **27,3 kB** |
| Modelo 3D del robot | — | `static/robot_x3/` |

### 5.2 Diferencia de rutas: es un superconjunto estricto

```
Sólo en la versión del portátil (5 rutas nuevas):
  + /pilotada
  + /runtime/status
  + /runtime/profile
  + /runtime/control
  + /runtime/keyboard

Sólo en la versión del repositorio: (ninguna)
```

**Nada se eliminó.** La versión del portátil añade exactamente la capa que faltaba.

### 5.3 Los proxies que cierran la brecha

En `~/SafeVision_Dashboard_dev/sf_app_dashboard.py`:

| Línea | Ruta del dashboard | Reenvía a | Timeout |
|---|---|---|---|
| 1555-1558 | `GET /runtime/status` | `GET :8091/runtime/status` | 4 s |
| 1566-1595 | `POST /runtime/profile` | `POST :8091/runtime/profile` (`profile`, `map`, `control`) | **120 s** |
| 1599-1613 | `POST /runtime/control` | `POST :8091/runtime/control` (`mode`) | 45 s |
| 1618-1642 | `POST /runtime/keyboard` | `POST :8091/runtime/keyboard` (`linear_x`, `linear_y`, `angular_z`) | 3 s |

Y en `static/pilotada_v2.js` se consumen desde la interfaz: `/runtime/status` (líneas 338,
733, 750) y `/runtime/profile` (líneas 409, 912).

El timeout de 120 s en `profile` es coherente con lo que tarda `apply_profile` en encender
driver + core + LiDAR + AMCL + `move_base` + cola, con sus esperas de verificación
(`runtime-boot.md` §2.6). Es decir: **quien escribió esto lo probó contra el robot real.**

### 5.4 Historial: hay 38 copias de seguridad fechadas

`~/SafeVision_Backups/` contiene 38 directorios con marca de tiempo, del 2026-08-18 al
2026-08-20, varios con `SHA256SUMS`. El más reciente,
`safevision_stable_pre_depth_20260820_174318/`, coincide en nombre con la etiqueta
`checkpoint-safevision-estable-pre-frontal-depth` del repositorio.

Interpretación (**RECOMENDACIÓN**, no certeza): el desarrollo del frontend se estaba
respaldando por copia de directorio en vez de por Git, y la última tanda de trabajo
(20 de agosto) nunca llegó a un commit. No es descuido del runtime: los 10 commits
posteriores al tag auditado son todos del lado robot.

### 5.5 Qué hacer con esto

**RECOMENDACIÓN (decisión del profesor / del estudiante; NO ejecutada en esta sesión):**

1. Verificar que `~/SafeVision_Dashboard_dev/` arranca y opera el robot (§8, prueba V-1).
2. Si funciona, **versionarlo** en una rama propia —
   `feature/dashboard-pilotada-v2` — copiando `sf_app_dashboard.py`, `templates/pilotada_v2.html`,
   `static/pilotada_v2.{js,css}`, `static/home.js`, `static/robot_x3/` y las versiones
   nuevas de `index.html`, `app.js`, `automatica.js`, `style.css`.
   Excluir la basura acumulada en ese directorio: `.safevision_dashboard.log` (21 MB),
   `__pycache__/`, `.venv/`, `build/`, `dist/`, `*.backup_*`, `programar.htmlyahboom`, y
   los ficheros vacíos `torch`, `torch==2.4.1`, `torchvision`, `triton`, `--index-url`
   (creados por un `pip install` mal escrito).
3. Sólo entonces decidir si `misiones/pilotada/dashboard_src/` se reemplaza.

**Esta sesión no lo hizo** porque las reglas de trabajo prohíben modificar fuentes fuera de
`docs/` y `scripts/`, y porque el paso 1 exige una persona frente al robot.

> **Consecuencia para la Fase 3 del encargo:** la Fase 3 estaba condicionada a que *no*
> existiera un dashboard más nuevo. Existe. **La Fase 3 no se ejecuta**: escribir un
> proxy nuevo duplicaría, peor, algo ya escrito y probado. Lo pendiente es publicarlo.

---

## 6. ¿Arranca `api/main_menu.py` solo en la Pi? — No, pero está a un comando (CONFIRMADO)

**Respuesta corta: no arranca solo, y a la vez no puede borrarse.**

| Vía | Resultado |
|---|---|
| systemd | **No.** Sólo dos unidades mencionan `robot_custom`, y son las de SafeVision |
| `cron` | **No.** `no crontab for pi`; `/etc/cron.d/` sólo trae ficheros del sistema |
| `.profile` / `.bash_profile` | **No.** Sin referencias |
| Procesos vivos | **Ninguno.** `pgrep -af "api/"` vacío |
| **`.bashrc`** | **Sí — 13 alias** |

En `/home/pi/.bashrc:155-170`:

```bash
alias api='python3 ~/robot_custom/api/main_menu.py'
alias api_sfv='python3 ~/robot_custom/api/main_menu.py'
alias mapeo_ligero='~/robot_custom/mapeo_ligero.sh'
alias mapeo_denso='~/robot_custom/mapeo_denso.sh'
alias sensores='~/robot_custom/emisor_sensores.sh'
alias mapear='~/robot_custom/auto_mapeo.sh'
alias vercodigo="cat /home/pi/robot_custom/codigo_completo.txt"
alias menu_mapas='python3 /home/pi/robot_custom/api/mapas.py'
alias mapear_2d='python3 /home/pi/robot_custom/api/mapas_2d_iniciar.py'
alias rcode='/home/pi/robot_custom/api/exportar_codigo.sh'
alias rdirec='python3 ~/robot_custom/generar_arbol.py'
alias pack_SF_m='python3 /home/pi/robot_custom/api/sf_empaquetador.py'
alias sf_modo_espera='python3 /home/pi/robot_custom/api/sf_modo_espera.py'
```

### 6.1 Esto corrige el inventario de la sesión anterior

`docs/inventory.md` clasificó varios ficheros como **sin-referencias** porque ninguna
búsqueda *dentro del repositorio* los encontraba. Era correcto en su alcance, y aun así la
conclusión práctica cambia: **esos ficheros sí tienen un invocador — vive fuera del
repositorio, en el `.bashrc` del robot.**

Ficheros afectados, que pasan de *sin-referencias* a **alcanzables por alias**:

`auto_mapeo.sh` · `mapeo_denso.sh` · `mapeo_ligero.sh` · `emisor_sensores.sh` ·
`generar_arbol.py` · `api/exportar_codigo.sh` · `api/sf_empaquetador.py` ·
`api/sf_modo_espera.py` · `api/mapas.py` · `api/mapas_2d_iniciar.py` · `api/main_menu.py`

Sigue sin tener invocador: `iniciar_mapeo.sh`, `probar_red.py` (el de la raíz),
`escanear_proyecto.sh`, `api/gestionar_mapas.py`, `api/lanzador_streaming.py`,
`api/menu_red_ccn.py`, `api/sf_mision_pilotada.py`, `api/sf_servidor_descarga.py`.

**Conclusión operativa: ningún fichero de `api/` ni de la raíz cumple los criterios de
borrado del handoff §77.** El criterio *"no documentado como fallback"* falla: 13 alias en
el `.bashrc` del usuario que opera el robot son documentación de facto, y memoria muscular.
Esto **confirma la regla 1 de `CLAUDE.md`** desde la evidencia, no desde la precaución.

> **Riesgo real, no teórico.** Hay dos niveles, verificados con `grep` sobre los scripts:
>
> | Nivel | Alias | Script | Qué hace |
> |---|---|---|---|
> | **Destructivo** | `mapeo_denso`, `sensores` | `mapeo_denso.sh`, `emisor_sensores.sh` | Empiezan por `killall -9 roslaunch rviz roscore` |
> | Conflictivo | `mapeo_ligero`, `mapear` | `mapeo_ligero.sh`, `auto_mapeo.sh` | No matan `roscore`, pero lanzan LiDAR y chasis por su cuenta |
>
> Si alguien teclea uno de los **destructivos** con los servicios activos, **matará el
> `roscore` gestionado por systemd**. `systemd` lo reiniciará (`Restart=on-failure`), pero el
> Robot Server quedará hablando con un Master nuevo y el estado en `/tmp` quedará
> desincronizado: todo deja de responder sin un error claro.
>
> **SOLUCIÓN PREPARADA:** `scripts/robot_desactivar_alias.sh` comenta (no borra) los
> **cuatro** alias de riesgo de ambos niveles, con copia de seguridad fechada y diff.
> Es idempotente y reversible; los scripts siguen accesibles por su ruta completa.
> Instrucciones en `docs/solucion-problemas.md` §10.1.
>
> **Corrección respecto a la primera versión de este documento:** se dijo que eran *tres*
> los alias destructivos, incluyendo `mapeo_ligero`. Es **falso**: `mapeo_ligero.sh` no
> contiene ningún `killall`. Son **dos**.

---

## 7. Dispositivos y estado del repositorio en el robot (CONFIRMADO)

| Dispositivo | Destino | Uso |
|---|---|---|
| `/dev/rplidar` | → `ttyUSB0` | LiDAR. Es una regla `udev`: el nombre es estable |
| `/dev/myserial` | → `ttyUSB1` | placa del chasis |
| `/dev/video0`, `/dev/video1` | — | cámara RGB USB |
| `/dev/input/js0` | — | mando (presente y detectado) |

**Repositorio en el robot:** `/home/pi/robot_custom` está en `ec0c02b`, **2 commits por
detrás** del portátil. Le faltan `391eec2` y `ee956ad`, que sólo tocan documentación y
`.gitignore`: **el robot está funcionalmente al día.** Conviene sincronizarlo desde GitHub
antes de la entrega (nunca al revés — `CLAUDE.md`).

**[PENDIENTE: copiar `/etc/udev/rules.d/` al reconstruir la tarjeta; requiere `sudo cat`,
no ejecutado en esta sesión de sólo lectura.]**

**Paquete del dashboard:** existe
`misiones/pilotada/payload/SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz` (395 MB, 8 ago),
que es lo que sirve `sf_servidor_descarga.py` en el puerto 8090. Es anterior a todo el
trabajo de frontend del 19-20 de agosto, así que **no incluye la página `/pilotada`**.
**[PENDIENTE: verificar que ese paquete arranca en una PC limpia; no se probó.]**

---

## 8. Prueba V-1 — ¿queda operable el robot? (para una persona, con el robot a la vista)

Es la prueba que cierra la conclusión de la §1 y decide el futuro del dashboard.
Procedimiento completo y con criterios de fallo en `docs/validacion.md`.

**Precondiciones:** robot sobre el suelo, **espacio despejado de 2×2 m**, mando a mano,
alguien con el dedo en la parada de emergencia.

1. Arrancar `~/SafeVision_Dashboard_dev/` en la PC y abrir `http://127.0.0.1:5000/pilotada`.
2. Seleccionar mapa `HAB2` y control `mando`, y aplicar el perfil **Pilotada**.
3. Esperar. Puede tardar hasta 2 minutos (timeout de 120 s, §5.3).
4. Verificar desde la PC:

```bash
curl -s http://192.168.1.13:8091/runtime/status | python3 -m json.tool | head -40
curl -s http://192.168.1.13:8091/health        | python3 -m json.tool
```

**Resultado esperado:** `profile.requested: "pilotada"`, `profile.map: "HAB2"`, y
`driver`, `core`, `lidar`, `localization`, `pose_exporter`, `navigation`, `nav_queue`,
`selector` y `mando` todos `active`. En `/health`, `ok: true`.

**Si sale bien:** el dashboard del portátil es el bueno → versionarlo (§5.5).
**Si falla:** anotar en qué recurso se detiene (`steps[]` de la respuesta lo dice) y
consultar `docs/solucion-problemas.md`.

**[PENDIENTE: ejecutar V-1 y registrar el resultado en `docs/validacion.md`.]**

---

## 9. Resumen de certezas

| Afirmación | Certeza |
|---|---|
| Tras el arranque sólo hay `roscore` + Robot Server; ningún recurso de movimiento | **CONFIRMADO** (arranque en frío real, 1h55min) |
| Hace falta un `POST /runtime/profile` para dejar el robot operable | **CONFIRMADO** |
| El dashboard versionado no puede hacer ese POST | **CONFIRMADO** (diff de rutas, §5.2) |
| Existe un dashboard sin versionar que sí puede | **CONFIRMADO** (`~/SafeVision_Dashboard_dev/`) |
| Ese dashboard funciona contra el robot real | **PENDIENTE DE REVALIDACIÓN** (prueba V-1) |
| Las dos unidades systemd están instaladas, habilitadas e idénticas al repositorio | **CONFIRMADO** |
| El Robot Server corre bajo Python 3.7.3; `roscore` bajo Python 2.7.17 | **CONFIRMADO** |
| `sf_pose_exporter.py` **debe** seguir en Python 2 (extensión C de `tf`) | **CONFIRMADO** por prueba de importación |
| Ubuntu 18.04.6 aarch64, ROS Melodic, 451 paquetes `ros-melodic-*` | **CONFIRMADO** |
| `api/main_menu.py` no arranca solo, pero 13 alias del `.bashrc` lo invocan | **CONFIRMADO** |
| Ningún fichero de `api/` cumple los criterios de borrado del handoff §77 | **CONFIRMADO** |
| `torch`/`ultralytics` instalados en el robot sin que el runtime los use | **CONFIRMADO** |
| Cámara, mapas, modelos y misiones responden sin tocar nada | **CONFIRMADO** |

### 9.1 Lo que queda pendiente, y de quién depende

| Pendiente | Quién |
|---|---|
| Ejecutar la prueba V-1 con el robot a la vista | estudiante en el robot |
| Verificar y versionar `~/SafeVision_Dashboard_dev/` | estudiante + profesor |
| Decidir qué mapas conservar de los 6 | profesor |
| Renombrar los alias peligrosos a `legacy_*` | profesor |
| Copiar `/etc/udev/rules.d/` para la reconstrucción (necesita `sudo`) | estudiante en el robot |
| Probar el `.tar.gz` del dashboard en una PC limpia | estudiante |

---

## 10. Documentos relacionados

- `docs/runtime-boot.md` — cómo arranca el runtime y por qué hay dos caminos.
- `docs/inventory.md` — qué hay en `api/` y qué lo invoca.
- `docs/security-scan.md` — credenciales expuestas; leer antes de publicar nada.
- `docs/analisis-alcance.md` — qué pide la propuesta frente a qué existe.
- `docs/validacion.md` — las pruebas, incluida V-1.
