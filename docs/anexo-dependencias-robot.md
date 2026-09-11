# Anexo — Manifiesto de dependencias del robot

**Para quién es y cuándo leerlo**
Para quien tenga que reconstruir la Raspberry Pi desde cero, o averiguar por qué algo que
funcionaba dejó de hacerlo tras actualizar un paquete.
Léelo junto a `instalacion-robot.md`. No es una lista de deseos: es lo que había instalado
y funcionando el 2026-09-10.

---

**Origen:** capturado por SSH del robot `yahboom` (192.168.1.13) el 2026-09-10.
**Certeza:** CONFIRMADO — salida literal de `dpkg -l` y `pip freeze`.

Este anexo es el manifiesto que el handoff §55 daba por inexistente.

---

## 1. Sistema base

| Elemento | Valor |
|---|---|
| Distribución | **Ubuntu 18.04.6 LTS (Bionic Beaver)** |
| Arquitectura | `aarch64` (ARM 64 bits) |
| Kernel | `5.4.0-1050-raspi` |
| Equipo | `yahboom` |
| Disco raíz | `/dev/mmcblk0p2`, 59 GB totales, 29 GB usados (51 %) |
| ROS | **Melodic Morenia**, `ros_comm` 1.14.13 |
| Paquetes `ros-melodic-*` instalados | **451** (ver §4) |

> No es Raspberry Pi OS: es **Ubuntu 18.04 de 64 bits para Raspberry Pi**. Importa, porque
> ROS Melodic sólo tiene paquetes oficiales para Bionic. Cualquier reinstalación debe usar
> esta misma base o perderá los 451 paquetes binarios y tendrá que compilarlos.

## 2. Los tres intérpretes de Python, y por qué son tres

**CONFIRMADO.** Esto es lo más importante y lo menos evidente de todo el sistema.

| Ruta | Versión | Papel |
|---|---|---|
| `/usr/bin/python` | **2.7.17** | El de ROS Melodic. Ejecuta `roscore` y `sf_pose_exporter.py` |
| `/usr/bin/python3` | 3.6.9 | El de Ubuntu 18.04. **No lo usa SafeVision** |
| `/usr/local/bin/python3` | **3.7.3** | Compilado aparte. Ejecuta el **Robot Server** y el resto de nodos SafeVision |

### 2.1 Cómo puede Python 3.7 usar `rospy` si ROS Melodic es Python 2

`rospy` está instalado **sólo** en el árbol de Python 2:

```
/opt/ros/melodic/lib/python2.7/dist-packages/rospy
```

El truco está en la variable `PYTHONPATH` del servicio, capturada del proceso vivo
(`/proc/<pid>/environ`):

```
PYTHONPATH=/home/pi/yahboomcar_ws/devel/lib/python2.7/dist-packages
          :/home/pi/software/library_ws/devel/lib/python2.7/dist-packages
          :/home/pi/software/world_canvas/devel/lib/python2.7/dist-packages
          :/opt/ros/melodic/lib/python2.7/dist-packages
ROS_PYTHON_VERSION=2
```

Python 3.7 importa desde ese árbol de Python 2. **Funciona porque `rospy`, `actionlib`,
`rosgraph`, `genpy` y los paquetes de mensajes son Python puro** y compatibles 2/3.

Verificado en el robot con ese `PYTHONPATH`:

| Módulo | `/usr/local/bin/python3` (3.7.3) |
|---|---|
| `rospy` | ✅ importa |
| `actionlib` | ✅ importa |
| `cv2` | ✅ 5.0.0 |
| `tf` | ❌ **falla** |

El fallo de `tf` es exacto y explica toda la arquitectura:

```
from ._tf2 import *
ImportError: dynamic module does not define module export function (PyInit__tf2)
```

`tf` depende de `_tf2.so`, una **extensión C compilada para Python 2**. No hay forma de
cargarla desde Python 3.

### 2.2 Consecuencia: por qué `sf_pose_exporter.py` es el único fichero con Python 2

`sf_pose_exporter.py` es **el único fichero de todo el runtime que importa `tf`**
(línea 10; verificado con `grep` sobre `misiones/*/robot/*.py`). Por eso, y sólo por eso,
se declara `#!/usr/bin/env python` y se invoca explícitamente con `/usr/bin/python`
(`sf_runtime_manager.py:468`, `sf_operacion_pilotada.sh:349`).

**No es un descuido ni código heredado: es una decisión obligada.** Cualquiera que
"modernice" ese fichero a Python 3 romperá la exportación de pose, y con ella la posición
del robot en el mapa del dashboard.

**RECOMENDACIÓN:** si algún día hay que quitar esa dependencia, la vía es sustituir `tf`
por `tf2_ros` con consultas al servicio de TF, o leer la pose de `/amcl_pose` en lugar de
la transformada `map → base_footprint`. Ninguna de las dos es trivial; no es una tarea de
limpieza.

## 3. Paquetes de Python en `/usr/local/bin/python3` (3.7.3)

106 paquetes en total. Los relevantes:

| Paquete | Versión | Nota |
|---|---|---|
| `Flask` | 2.2.5 | sirve `:8091` |
| `Werkzeug` | 2.2.3 | visible en la cabecera HTTP del Robot Server |
| `numpy` | 1.21.6 | |
| `opencv-python` | **5.0.0.93** | ver aviso abajo |
| `opencv-contrib-python` | 4.5.4.60 | **convive con la anterior** |
| `opencv-python-headless` | 5.0.0.93 | **tercera copia de OpenCV** |
| `Pillow` | 8.4.0 | |
| `PyYAML` | 6.0 | |
| `torch` | **1.13.1** | ver aviso abajo |
| `torchvision` | 0.14.1 | |
| `ultralytics` | **8.0.145** | |
| `rospkg` | 1.3.0 | |
| `catkin-pkg` | 0.4.24 | |
| `catkin-tools` | 0.8.2 | |

La lista completa está en `anexo-pip-freeze.txt`.

### 3.1 Aviso 1 — tres OpenCV instalados a la vez

`opencv-python`, `opencv-python-headless` y `opencv-contrib-python` conviven, y las dos
primeras son **5.0.0.93**, una versión muy por delante de lo habitual en este tipo de
equipo. Cuál gana depende del orden de `sys.path`.

Hay una traza real de este conflicto en los registros
(`~/safevision-raw/misiones/pilotada/logs/robot_server.log`):

```
[ERROR] global loadsave.cpp:1355 imdecode_(''): can't read header:
OpenCV(5.0.0) ... WebPDecoder::readHeader() Buffer is too small
```

**IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN:** el error aparece en la decodificación
de una imagen vacía, no en el flujo de vídeo (que hoy funciona: `/video_feed` entrega
≈4 Mbit/s). **RECOMENDACIÓN:** dejar una sola instalación —
`opencv-python-headless` es la adecuada en un robot sin escritorio— pero **sólo después**
de crear la imagen de respaldo de la SD, y revalidando la cámara. No tocar antes de la
entrega.

### 3.2 Aviso 2 — `torch` y `ultralytics` están instalados en el robot

**CONFIRMADO**, y contradice lo que asume el handoff (§17-18: la inferencia YOLO corre en
la PC).

`torch` 1.13.1 + `torchvision` + `ultralytics` 8.0.145 ocupan varios cientos de MB en la
tarjeta y **no los usa el runtime vigente**: `sf_robot_server.py` no importa ninguno de los
tres (sólo `cv2` y `numpy`). Son, casi con seguridad, restos de la generación anterior,
cuando `api/nodo_yolo_pi.py` hacía inferencia local (`inventory.md` §2.3).

**RECOMENDACIÓN:** no desinstalarlos ahora. Ocupan espacio (hay 28 GB libres) pero
desinstalar `torch` en ARM es fácil de hacer mal y no aporta nada antes de la entrega.
Anotarlo como deuda.

## 4. Paquetes ROS instalados

451 paquetes `ros-melodic-*`. La lista completa, con versión exacta, está en
`anexo-ros-melodic.txt`, generada con:

```bash
dpkg -l | grep "^ii  ros-melodic" | awk '{printf "%s  %s\n", $2, $3}' | sort
```

Los que SafeVision usa directamente:

| Paquete | Para qué |
|---|---|
| `ros-melodic-amcl` | localización (perfil pilotada/automatica) |
| `ros-melodic-move-base` | planificación y navegación |
| `ros-melodic-dwa-local-planner` | planificador local (`nav/sf_dwa.yaml`) |
| `ros-melodic-map-server` | publica `/map` desde el `.yaml` |
| `ros-melodic-gmapping` | SLAM 2D |
| `ros-melodic-robot-localization` | EKF (`/ekf_localization`) |
| `ros-melodic-imu-filter-madgwick` | fusión IMU |
| `ros-melodic-rplidar-ros` | LiDAR |
| `ros-melodic-joy` | mando |
| `ros-melodic-tf` / `tf2-ros` | transformadas (pose exporter) |
| `ros-melodic-actionlib` | interfaz de acción con `move_base` |
| `ros-melodic-xacro`, `robot-state-publisher`, `joint-state-publisher` | modelo URDF y TF |

Además, **fuera de apt**, el espacio de trabajo obligatorio:

```
/home/pi/yahboomcar_ws        (yahboomcar_bringup, yahboomcar_ctrl, yahboomcar_nav,
                               yahboomcar_description, imu_calib …)
/home/pi/software/library_ws
/home/pi/software/world_canvas
```

**CONFIRMADO** por `CMAKE_PREFIX_PATH` del proceso vivo. Los tres se cargan en el arranque
de los servicios. Una copia de `yahboomcar_ws/src` vive en el portátil en
`~/yahboomcar_ws-src`.

## 5. Dispositivos

**CONFIRMADO** (`ls -la /dev/...`):

| Dispositivo | Destino | Uso |
|---|---|---|
| `/dev/rplidar` | → `ttyUSB0` | LiDAR (`sf_runtime_lidar.launch:11`) |
| `/dev/myserial` | → `ttyUSB1` | placa del chasis (driver Yahboom) |
| `/dev/video0`, `/dev/video1` | — | cámara RGB USB |
| `/dev/input/js0` | — | mando |

Los enlaces `rplidar` y `myserial` son **reglas `udev`**: por eso el sistema no depende del
orden en que se enumeren los puertos USB. Es un detalle que hay que preservar en cualquier
reinstalación. **[PENDIENTE: copiar el contenido de `/etc/udev/rules.d/` al reconstruir;
requiere `sudo cat`, no ejecutado en esta sesión.]**

## 6. Estado del repositorio en el robot

**CONFIRMADO:** `/home/pi/robot_custom` está en el commit `ec0c02b`, es decir **2 commits
por detrás** de `wip-handoff` en el portátil (`ee956ad`). Le faltan:

- `391eec2` — deja de versionar exports y añade el handoff auditado
- `ee956ad` — añade `CLAUDE.md`

Ninguno de los dos toca código de ejecución, así que **el robot está funcionalmente al
día**. Aun así conviene sincronizarlo antes de la entrega: `git pull` desde GitHub
(nunca al revés — ver `CLAUDE.md`).

## 7. El paquete del dashboard para Ubuntu 18.04

**CONFIRMADO:**

```
/home/pi/robot_custom/misiones/pilotada/payload/
    SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz    395 MB    (8 ago 2026)
```

Existe y pesa 395 MB. Es lo que sirve `sf_servidor_descarga.py` en el puerto **8090**
(`sf_servidor_descarga.py:9-14`), y explica por qué ese script comprueba la existencia del
fichero antes de ofrecer la descarga.

Es una vía de distribución **ya montada** para una PC con Ubuntu 18.04 que no quiera
instalar dependencias a mano. **[PENDIENTE: verificar que el paquete arranca en una PC
limpia; no se ha probado en esta sesión.]** Nótese que es anterior (8 de agosto) a todo el
trabajo de dashboard de los días 19 y 20, así que **no incluye la página `/pilotada`**.
