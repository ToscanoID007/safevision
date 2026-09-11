# SafeVision / Rosmaster X3
## Handoff técnico final auditado
### Continuación, refactorización, contenerización y evolución a nube

**Proyecto:** SafeVision / Rosmaster X3  
**Repositorio observado:** `/home/pi/robot_custom`  
**Plataforma:** Raspberry Pi + Rosmaster X3 + ROS Melodic + Dashboard en PC  
**Estado documental:** septiembre de 2026  
**Snapshot de código consolidado disponible:** 19 de agosto de 2026  
**Grafo histórico disponible:** 8 de agosto de 2026  

---

# 0. Cómo leer este documento

Este documento distingue estrictamente entre tres categorías:

1. **CONFIRMADO**: existe evidencia directa en código, scripts, rutas, endpoints, nodos ROS o historial del proyecto disponible.
2. **IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN**: existe código que implementa la capacidad, pero el snapshot por sí solo no prueba que la función haya sido validada físicamente de extremo a extremo sobre el robot en su estado actual.
3. **RECOMENDACIÓN / ARQUITECTURA PROPUESTA**: recomendación para el siguiente equipo. No debe interpretarse como una decisión ya adoptada por el proyecto.

Esta distinción es crítica para evitar el error de asumir que “existe código” equivale a “funciona actualmente en hardware”.

---

# 1. Resumen ejecutivo

SafeVision es una plataforma de operación, visión artificial, mapeo, navegación y automatización para un robot móvil Yahboom / Rosmaster X3 basado en Raspberry Pi y ROS.

El proyecto comenzó como una colección de menús y utilidades alojadas principalmente en:

```text
/home/pi/robot_custom/api
```

y evolucionó posteriormente hacia una arquitectura más especializada alrededor de:

```text
/home/pi/robot_custom/misiones/pilotada
/home/pi/robot_custom/misiones/automatica
```

La evidencia disponible muestra una transición clara entre dos generaciones arquitectónicas.

## Generación anterior

- Dashboard dependiente de SSH / Paramiko.
- Lanzamiento remoto de scripts desde la PC.
- Cámara servida en `:8080`.
- Teleoperación web mediante `:5002`.
- Código concentrado bajo `api/`.
- Varias operaciones realizadas mediante shell, SSH y procesos externos.

## Generación más reciente

- Robot Server HTTP sobre `:8091`.
- Dashboard local en la PC sobre `127.0.0.1:5000`.
- Dashboard actuando como cliente/proxy del Robot Server.
- Navegación asistida con `move_base`.
- Cola de navegación `sf_nav_queue`.
- Selector explícito entre velocidad manual y navegación.
- Mapping Manager para alternar localización/mapeo.
- Lenguaje de misiones, simulador y runtime automático.
- Separación conceptual entre misión pilotada y misión automática.

El historial del proyecto contiene además el commit:

```text
f9622cd
feat: integra navegacion por puntos en dashboard y migra api a 8091
```

lo que coincide con la evolución observada en el código.

**Conclusión auditada:** `misiones/pilotada/` debe tratarse como la principal candidata a línea arquitectónica vigente. `api/` contiene código anterior, utilidades todavía potencialmente útiles y componentes que deben clasificarse mediante tracing antes de eliminarse.

No debe calificarse todo `api/` como “código muerto” sin verificar dependencias reales.

---

# 2. Objetivo del proyecto

El objetivo general de SafeVision es proporcionar una plataforma capaz de:

- controlar manualmente el robot;
- transmitir video RGB;
- ejecutar visión artificial en tiempo real;
- utilizar modelos YOLO;
- administrar modelos y sus metadatos;
- crear, visualizar, editar y utilizar mapas 2D;
- localizar el robot en un mapa;
- enviar destinos de navegación;
- ejecutar secuencias de destinos;
- programar misiones;
- almacenar misiones;
- ejecutar misiones automáticamente;
- cambiar entre modo manual y navegación;
- crear nuevos mapas;
- evolucionar hacia sensores de profundidad y capacidades de navegación/percepción más avanzadas;
- evolucionar hacia una arquitectura edge/cloud.

El objetivo futuro más amplio puede describirse como:

> SafeVision debe convertirse en una plataforma edge/cloud para operar, observar, mapear, programar y automatizar robots Rosmaster X3, manteniendo en el robot las funciones críticas de control y seguridad y exponiendo hacia capas superiores una interfaz estable para telemetría, mapas, video, IA, navegación y misiones.

Esta última frase es una **dirección arquitectónica recomendada**, no una funcionalidad cloud ya existente.

---

# 3. Fuentes disponibles y limitaciones del snapshot

La auditoría se basa principalmente en dos fuentes internas.

## 3.1 Grafo histórico

Archivo:

```text
robot_custom_grafo_resumen.txt
```

Fecha:

```text
2026-08-08
```

En ese momento detectaba:

```text
67 archivos
155 relaciones
44 .py
8  .sh
6  .yaml
```

Este grafo describe muy bien la arquitectura anterior basada principalmente en `api/`.

No debe utilizarse por sí solo para representar el estado actual, ya que es anterior a buena parte de la implementación de `misiones/pilotada/`.

## 3.2 Export de código consolidado

Archivo:

```text
codigo_proyecto.txt
```

Fecha aproximada del snapshot:

```text
2026-08-19
```

Incluye código moderno como:

```text
misiones/pilotada/robot/sf_robot_server.py
misiones/pilotada/robot/sf_nav_queue.py
misiones/pilotada/robot/sf_mapping_manager.py
misiones/pilotada/robot/sf_cmd_vel_selector.py
misiones/pilotada/robot/sf_pose_exporter.py

misiones/pilotada/dashboard_src/sf_app_dashboard.py
misiones/pilotada/dashboard_src/sf_motor_inferencia.py
misiones/pilotada/dashboard_src/sf_mission_lang.py

misiones/automatica/robot/sf_mission_executor.py
```

---

# 4. Problema importante del exportador actual

El script:

```text
api/exportar_codigo.sh
```

recolecta solamente:

```text
*.py
*.sh
*.yaml
*.json
```

Por tanto, el snapshot consolidado NO contiene necesariamente:

```text
*.launch
*.html
*.css
*.js
*.pgm
*.pt
*.torchscript
*.service
Dockerfile
docker-compose.yml
requirements*.txt
package.xml
CMakeLists.txt
```

Esto tiene una consecuencia crítica:

> El snapshot disponible NO es una copia exhaustiva del repositorio.

Hay referencias en código a múltiples archivos `.launch` que no aparecen en el export.

También sabemos que el Dashboard renderiza templates y utiliza frontend web, pero esos archivos no pueden auditarse a partir de este snapshot.

---

# 5. Contaminación del snapshot con entornos virtuales

El exportador excluye principalmente:

```text
.git
__pycache__
```

pero no excluye:

```text
.venv
venv
site-packages
build
devel
logs
```

Como resultado, el archivo consolidado contiene elementos pertenecientes a:

```text
grafo/.venv/lib/python3.7/site-packages/
```

incluyendo dependencias externas.

Esto hace que:

- el snapshot sea innecesariamente grande;
- el conteo de líneas no represente correctamente el código propio;
- herramientas automáticas puedan interpretar librerías externas como parte del proyecto.

### Acción inmediata recomendada

Reemplazar el export mediante:

```bash
git ls-files
```

o un `MANIFEST` explícito.

Nunca utilizar `.venv` o `site-packages` como fuente del handoff.

---

# 6. Arquitectura funcional observada

```text
                  PC / OPERADOR
┌─────────────────────────────────────────────┐
│ SafeVision Dashboard                       │
│ Flask                                      │
│ 127.0.0.1:5000                            │
│                                             │
│ - UI                                       │
│ - conexión al robot                        │
│ - video                                    │
│ - inferencia YOLO                          │
│ - mapas                                    │
│ - navegación                               │
│ - editor/programador de misiones           │
└──────────────────────┬──────────────────────┘
                       │
                       │ HTTP LAN :8091
                       ▼
              RASPBERRY PI / ROBOT
┌─────────────────────────────────────────────┐
│ SafeVision Robot Server                    │
│ Flask                                      │
│ 0.0.0.0:8091                              │
│                                             │
│ - health                                   │
│ - cámara                                   │
│ - mapas                                    │
│ - mapping                                  │
│ - pose                                     │
│ - navegación                               │
│ - runtime de misiones                      │
└──────────────────────┬──────────────────────┘
                       │ ROS
                       ▼
┌─────────────────────────────────────────────┐
│ ROS Melodic / Yahboom                      │
│                                             │
│ driver                                     │
│ IMU                                        │
│ EKF                                        │
│ LiDAR                                      │
│ AMCL                                       │
│ map_server                                 │
│ move_base                                  │
│ sf_nav_queue                               │
│ sf_cmd_vel_selector                        │
│ teleoperación                              │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
                   HARDWARE
```

---

# 7. Dependencia externa crítica: `yahboomcar_ws`

SafeVision no es autosuficiente dentro de `robot_custom`.

Existe una dependencia fuerte del workspace:

```text
/home/pi/yahboomcar_ws
```

Los scripts cargan:

```bash
source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash
```

Entre los paquetes utilizados aparecen referencias a:

```text
yahboomcar_bringup
yahboomcar_nav
yahboomcar_ctrl
yahboomcar_description

rplidar
map_server
gmapping
move_base
AMCL
robot_localization
imu_filter_madgwick
teleop
```

También existen experimentos anteriores con:

```text
astra_camera
rtabmap_ros
```

### Implicación

Antes de contenerizar debe inventariarse:

```text
/home/pi/yahboomcar_ws/src
```

y distinguir:

- paquetes originales del fabricante;
- paquetes modificados;
- launch files personalizados;
- configuraciones personalizadas;
- dependencias ROS instaladas por sistema.

Copiar únicamente `robot_custom` no reproducirá el runtime.

---

# 8. Hardware observado o contemplado

La evidencia disponible indica uso o soporte de:

```text
Raspberry Pi
Rosmaster X3
LiDAR RPLIDAR
IMU
driver/chasis Yahboom
cámara RGB USB
joystick
Astra/AstraPro en experimentos 3D
```

La cámara RGB del runtime moderno está configurada alrededor de:

```text
/dev/video0
640x480
30 FPS
MJPEG
```

El joystick se espera típicamente en:

```text
/dev/input/js0
```

---

# 9. Estructura conceptual del repositorio

La siguiente estructura NO pretende ser un árbol exhaustivo; representa la organización conceptual observada.

```text
robot_custom/
│
├── api/
│   ├── main_menu.py
│   ├── safevision.py
│   ├── menu_operacion.py
│   ├── redes.py
│   ├── importar_modelo.py
│   ├── exportar_modelo.py
│   ├── editar_metadatos.py
│   ├── editar_nombre.py
│   ├── eliminar_modelo.py
│   ├── ver_modelos.py
│   ├── ver_parametros.py
│   ├── mapas*.py
│   ├── navegacion*.py
│   ├── robot_map_editor.py
│   ├── visor_mapa.py
│   ├── wifi.py
│   ├── sistema.py
│   ├── gestor_nodos.py
│   └── dashboard_pc_src/
│
├── misiones/
│   ├── pilotada/
│   │   ├── robot/
│   │   │   ├── sf_mision_pilotada.py
│   │   │   ├── sf_operacion_pilotada.sh
│   │   │   ├── sf_robot_server.py
│   │   │   ├── sf_pose_exporter.py
│   │   │   ├── sf_cmd_vel_selector.py
│   │   │   ├── sf_nav_queue.py
│   │   │   ├── sf_mapping_manager.py
│   │   │   ├── sf_modo_espera.py
│   │   │   ├── sf_servidor_descarga.py
│   │   │   ├── *.launch
│   │   │   └── nav/
│   │   ├── dashboard_src/
│   │   │   ├── sf_app_dashboard.py
│   │   │   ├── sf_motor_inferencia.py
│   │   │   ├── sf_mission_lang.py
│   │   │   ├── templates/
│   │   │   └── static/
│   │   ├── payload/
│   │   └── logs/
│   ├── automatica/
│   │   └── robot/
│   │       └── sf_mission_executor.py
│   └── programadas/
│       └── *.sfmision
│
├── mapping/
│   └── maps/
├── modelos/
├── network/
│   └── wifi_manager.sh
├── grafo/
└── scripts auxiliares
```

---

# 10. Generación anterior vs arquitectura más reciente

## 10.1 Generación anterior

El Dashboard anterior ubicado en:

```text
api/dashboard_pc_src/
```

utilizaba:

```text
Paramiko
SSH
scripts remotos
```

La conexión SSH contenía configuración embebida y utilizaba:

```python
AutoAddPolicy
```

También lanzaba remotamente:

```text
sf_teleop_teclado.py
sf_teleop_mando.py
transmisor_camara_pi.py
```

con servicios alrededor de:

```text
5002
8080
```

Esta arquitectura debe considerarse una **generación anterior**.

No debe asumirse automáticamente que todos estos archivos pueden eliminarse.

## 10.2 Arquitectura más reciente

El flujo más moderno utiliza:

```text
Dashboard PC
        │
        │ HTTP
        ▼
Robot Server :8091
        │
        ▼
ROS
```

El menú de operación ya redirige la misión pilotada hacia:

```text
/home/pi/robot_custom/misiones/pilotada/robot/sf_mision_pilotada.py
```

Esto constituye evidencia fuerte de que `misiones/pilotada/` es la línea principal de evolución.

---

# 11. Arranque del runtime pilotado

Archivo principal:

```text
misiones/pilotada/robot/sf_operacion_pilotada.sh
```

El launcher inicia el runtime en varias etapas.

## 11.1 ROS Master

Verifica si existe ROS Master y, si no:

```bash
roscore
```

## 11.2 Driver Yahboom

Se inicia el driver y se esperan tópicos/nodos relacionados con movimiento e IMU.

## 11.3 Localización

Se lanza un archivo similar a:

```text
sf_localizacion.launch
```

pasándole el mapa seleccionado.

El runtime espera componentes relacionados con:

```text
/amcl
/ekf_localization
/imu_filter_madgwick
/rplidarNode
```

y verifica datos en tópicos como:

```text
/imu/imu_data
/scan
```

## 11.4 Pose exporter

Se ejecuta:

```text
sf_pose_exporter.py
```

con el objetivo de obtener:

```text
map -> base_footprint
```

y exponer esa pose a capas superiores.

## 11.5 Robot Server

Se inicia:

```text
sf_robot_server.py
```

y se valida alrededor de:

```text
http://127.0.0.1:8091/
```

## 11.6 Selector de velocidades

Se ejecuta:

```text
sf_cmd_vel_selector.py
```

que recibe:

```text
/cmd_vel_manual
/cmd_vel_nav
```

y publica:

```text
/cmd_vel
```

## 11.7 Navegación

Se lanza navegación y se espera:

```text
/move_base
```

## 11.8 Cola de navegación

Se inicia:

```text
sf_nav_queue.py
```

## 11.9 Control

Dependiendo del modo:

```text
sf_control_mando.launch
sf_control_teclado.launch
```

---

# 12. Inconsistencia “Nivel 2 / Nivel 3”

Existe una inconsistencia real entre UI/menús y runtime.

El menú de misión pilotada presenta aproximadamente:

```text
Nivel 2
Pilotaje + Mapa
ACTIVO

Nivel 3
Navegación asistida
FUTURO
```

Sin embargo, el runtime ya inicia:

```text
move_base
sf_nav_queue
```

y maneja navegación por puntos.

### Conclusión

La navegación asistida está **implementada en fuente**.

La etiqueta “FUTURO” está desactualizada.

### Recomendación

Reemplazar niveles por capacidades explícitas.

---

# 13. Robot Server

Archivo:

```text
misiones/pilotada/robot/sf_robot_server.py
```

Es uno de los componentes centrales de la arquitectura moderna.

Tiene varios miles de líneas y concentra:

```text
HTTP
video
mapas
pose
mapping
navegación
misiones
estado
```

Se ejecuta sobre:

```text
0.0.0.0:8091
```

Conceptualmente:

```text
HTTP / JSON / MJPEG
        ↕
       ROS
        ↕
    hardware
```

---

# 14. API observada del Robot Server

El snapshot disponible contiene rutas de las siguientes categorías.

## Diagnóstico

```text
GET /
GET /health
```

## Video

```text
GET /video_feed
```

## Misiones

```text
GET  /missions
POST /missions/save
POST /missions/delete

POST /mission/prepare
GET  /mission/status
POST /mission/start
POST /mission/cancel
```

## Mapas

Operaciones relacionadas con:

```text
listar
imagen
metadata
rename
duplicate
delete
import
export
edit
```

## Pose

```text
GET  /map_pose
POST /initialpose
```

## Mapeo

```text
GET  /mapping/map
GET  /mapping/meta

GET  /mapping/session/status
POST /mapping/session/start
POST /mapping/session/save
POST /mapping/session/discard
```

## Navegación

```text
GET  /nav/status
POST /nav/queue
POST /nav/start
POST /nav/cancel
POST /nav/clear
```

---

# 15. Semántica de `/health`

El Robot Server consulta elementos de ROS y hardware.

Existe una inconsistencia importante entre el concepto de `ready` del Robot Server y la lógica utilizada por `sf_modo_espera.py`.

### Recomendación

Separar:

```text
alive
ready
localized
navigable
camera_ready
control_ready
mapping_ready
```

---

# 16. Video RGB

El Robot Server moderno abre la cámara física y sirve MJPEG.

Configuración observada:

```text
device     /dev/video0
width      640
height     480
fps        30
codec      MJPG
```

El diseño intenta compartir una sola captura física para varios consumidores.

---

# 17. Flujo de inferencia IA

```text
CÁMARA
  │
  ▼
Robot Server
/video_feed :8091
  │
  ▼
Dashboard PC
  │
  ▼
MotorInferencia
  │
  ▼
YOLO
  │
  ▼
frame anotado
  │
  ▼
navegador
```

La arquitectura más reciente ejecuta la inferencia principal en la PC/Dashboard.

---

# 18. Motor de inferencia

Archivo:

```text
misiones/pilotada/dashboard_src/sf_motor_inferencia.py
```

Utiliza:

```python
from ultralytics import YOLO
```

Admite:

```text
modelo .pt
JSON opcional
confidence
```

---

# 19. Gestión de modelos

Existen dos paradigmas.

## 19.1 Gestión anterior persistente

Dentro de `api/` existen utilidades para:

```text
importar
exportar
renombrar
editar metadata
eliminar
listar
ver parámetros
```

y una carpeta persistente:

```text
/home/pi/robot_custom/modelos
```

## 19.2 Dashboard moderno

El backend moderno soporta funciones como:

```text
upload_model
model_info
confidence
```

La carga utiliza almacenamiento temporal.

### Conclusión

El Dashboard moderno todavía no representa por sí solo un registry persistente completo de modelos equivalente al sistema anterior.

---

# 20. Estado de la UI moderna de modelos

El proyecto desarrolló iteraciones visuales para concentrar:

```text
video
modelos
metadatos
clases
versiones JSON
acciones
```

Sin embargo, el export actual no incluye de forma fiable:

```text
templates/*.html
static/*.js
static/*.css
```

Por tanto:

> El estado exacto del frontend moderno de modelos NO puede declararse completamente verificado a partir del snapshot disponible.

---

# 21. Mapas 2D

Directorio principal:

```text
/home/pi/robot_custom/mapping/maps
```

Formato:

```text
nombre.yaml
nombre.pgm
```

---

# 22. Gestión moderna de mapas

El Robot Server moderno contiene funciones relacionadas con:

```text
listar
leer imagen
leer metadata
renombrar
duplicar
eliminar
importar
exportar
editar
```

Esto superpone funcionalidad con herramientas antiguas de `api/`.

No deben eliminarse estas últimas hasta completar tracing y regression tests.

---

# 23. Mapping Manager

Archivo:

```text
sf_mapping_manager.py
```

Permite cambiar entre:

```text
LOCALIZACIÓN
map_server + AMCL
```

y:

```text
MAPEO
Gmapping
```

sin reiniciar necesariamente todo el stack.

Contiene lógica de transición y rollback.

---

# 24. Riesgo del Mapping Manager para Docker

El componente inspecciona información de procesos, incluyendo:

```text
/proc/<pid>/cmdline
```

Esto puede fallar si los nodos relevantes quedan en namespaces de proceso diferentes.

### Recomendación

Reemplazar gradualmente esta detección por:

```text
ROS parameter
servicio
topic
estado explícito
API interna
```

---

# 25. Pose exporter

Archivo:

```text
sf_pose_exporter.py
```

Obtiene:

```text
TF map -> base_footprint
```

y persiste información en archivos temporales similares a:

```text
/tmp/safevision_map_pose.json
/tmp/safevision_initialpose_request.json
/tmp/safevision_initialpose_ack.json
```

### Riesgo

El filesystem temporal se está utilizando como IPC.

Esto dificulta separación por contenedores y multi-robot.

---

# 26. Navegación asistida

La navegación moderna está implementada en fuente mediante:

```text
move_base
sf_nav_queue
sf_cmd_vel_selector
```

Debe revalidarse físicamente en cada baseline.

---

# 27. Selector de velocidades

Archivo:

```text
sf_cmd_vel_selector.py
```

Recibe:

```text
/cmd_vel_manual
/cmd_vel_nav
```

y publica:

```text
/cmd_vel
```

Incluye comportamiento de watchdog y cambio de modo.

Esta lógica debe preservarse durante el refactor.

---

# 28. Cola de navegación

Archivo:

```text
sf_nav_queue.py
```

Utiliza:

```text
actionlib
MoveBaseAction
MoveBaseGoal
/move_base/make_plan
```

Las operaciones incluyen:

```text
load
start
orient
cancel
clear
status
```

Una cola soporta aproximadamente hasta:

```text
50 puntos
```

Antes de ejecutar puede:

- validar mapa;
- validar puntos;
- comprobar ruta.

Durante la ejecución puede:

- monitorizar resultado;
- cancelar;
- intentar recuperación.

---

# 29. Recovery de navegación

La cola contiene mecanismos de recuperación ante fallo.

Debe distinguirse del comando DSL:

```text
relocalizar()
```

El recovery interno y la acción programable de misión no son lo mismo.

---

# 30. Configuración `move_base`

Dentro de:

```text
misiones/pilotada/robot/nav
```

se observan configuraciones propias para:

```text
move_base
DWA
costmap común
global costmap
local costmap
```

El footprint observado es aproximadamente:

```text
x ±0.117 m
y ±0.100 m
```

Estos parámetros deben congelarse como baseline antes de optimizarlos.

---

# 31. Dashboard moderno

Archivo principal:

```text
misiones/pilotada/dashboard_src/sf_app_dashboard.py
```

Corre en:

```text
127.0.0.1:5000
```

Combina:

```text
backend UI
proxy al Robot Server
misiones
mapas
navegación
streaming
inferencia
```

El estado seleccionado del robot se mantiene globalmente.

### Inferencia arquitectónica

Esto sugiere un modelo principal de un robot activo por instancia de Dashboard.

---

# 32. Templates esperados

El backend referencia páginas como:

```text
index.html
automatica.html
programar.html
mapas.html
mapear.html
editar_mapa.html
```

El snapshot disponible no permite auditarlas completamente.

---

# 33. Biblioteca de misiones

En PC aparece una biblioteca local alrededor de:

```text
~/SafeVision_Misiones
```

En Raspberry Pi existe almacenamiento relacionado con:

```text
/home/pi/robot_custom/misiones/programadas
```

Extensión:

```text
.sfmision
```

---

# 34. Formato de misión

Estructura observada:

```json
{
  "format": "safevision-mission",
  "version": 1,
  "name": "nombre",
  "map": "HAB2",
  "code": "...",
  "points": [
    {
      "id": "0x000",
      "alias": "entrada",
      "x": 1.2,
      "y": 0.8,
      "yaw": 0.0
    }
  ],
  "initial_point_id": "0x000",
  "next_point_id": 1
}
```

Los IDs utilizan una representación del estilo:

```text
0x000 ... 0xFFF
```

### Recomendación

Formalizar mediante JSON Schema o Pydantic.

---

# 35. Lenguaje de misiones

Archivo:

```text
sf_mission_lang.py
```

Utiliza:

```python
ast.parse(...)
```

para interpretar un subconjunto restringido con sintaxis similar a Python.

Comandos principales:

```text
ir()
esperar()
orientar()
girar()
relocalizar()
```

También existen estructuras controladas como:

```text
asignaciones
operaciones numéricas
if
for
while
break
pass
range
```

El flujo incluye:

```text
validate_program()
simulate_program()
```

---

# 36. Arquitectura de ejecución de misiones

```text
código
  │
  ▼
validate_program
  │
  ▼
AST
  │
  ▼
simulate_program
  │
  ▼
trace
  │
  ▼
execution plan
  │
  ▼
MissionRuntime
  │
  ▼
sf_nav_queue
  │
  ▼
move_base
```

Esta separación debe conservarse.

---

# 37. Runtime automático

Archivo:

```text
misiones/automatica/robot/sf_mission_executor.py
```

Contiene componentes similares a:

```text
build_execution_plan
MissionRuntime
```

y lógica de:

```text
prepare
start
status
cancel
```

---

# 38. Incompletitud de acciones del DSL

Comandos entendidos por el lenguaje:

```text
ir
esperar
orientar
girar
relocalizar
```

Acciones físicamente admitidas por el runtime observado:

```text
esperar
ir
orientar
```

### Conclusión

Actualmente:

```text
girar()
relocalizar()
```

no deben presentarse como acciones físicas plenamente implementadas de misión automática.

---

# 39. Cámara de profundidad / 3D

Existen scripts experimentales relacionados con:

```text
Astra/AstraPro
depth
RTAB-Map
rosbag
depthimage_to_laserscan
```

Ejemplos:

```text
mapeo_denso.sh
auto_mapeo.sh
emisor_sensores.sh
```

Sin embargo, no se observa integración equivalente dentro del runtime moderno de `misiones/pilotada/`.

El historial del proyecto alcanzó además un:

```text
checkpoint pre-profundidad
```

### Estado

**Profundidad / navegación 3D debe considerarse experimental o pendiente de integración moderna.**

---

# 40. Menús antiguos incompletos

Existen menús con opciones todavía no implementadas o scripts ausentes del snapshot.

Por tanto, los menús de terminal no deben utilizarse como fuente única de verdad sobre capacidades actuales.

---

# 41. Dashboard distribuible

Existe un mecanismo para servir un paquete descargable del Dashboard desde la Pi.

Aparecen nombres del estilo:

```text
SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz
```

y un servicio alrededor de:

```text
8090
```

A futuro debería reemplazarse por un proceso reproducible de release.

---

# 42. Herramienta de grafo

Existe una herramienta web propia bajo:

```text
/home/pi/robot_custom/grafo
```

El comando configurado es:

```bash
grafo
```

y el ejecutable se resolvió en:

```text
/home/pi/.local/bin/grafo
```

La herramienta utiliza actualmente el puerto:

```text
8080
```

Antes de iniciarla:

```bash
sudo ss -ltnp | grep ':8080'
```

Puede utilizarse durante el handoff para inspeccionar relaciones entre archivos.

---

# 43. Componentes prioritarios para auditoría

## Prioridad 1

```text
misiones/pilotada/robot/
misiones/pilotada/dashboard_src/
misiones/automatica/robot/
```

## Prioridad 2

```text
mapping/maps/
misiones/programadas/
modelos/
```

## Prioridad 3

```text
api/
network/
grafo/
scripts experimentales
```

## Dependencia externa obligatoria

```text
/home/pi/yahboomcar_ws
```

---

# 44. Orden recomendado de lectura

```text
1.  sf_operacion_pilotada.sh
2.  sf_robot_server.py
3.  todos los *.launch de misiones/pilotada/robot
4.  sf_cmd_vel_selector.py
5.  sf_nav_queue.py
6.  sf_mapping_manager.py
7.  sf_pose_exporter.py

8.  dashboard_src/sf_app_dashboard.py
9.  dashboard_src/sf_motor_inferencia.py
10. dashboard_src/sf_mission_lang.py

11. dashboard_src/templates/
12. dashboard_src/static/

13. misiones/automatica/robot/sf_mission_executor.py

14. api/main_menu.py
15. api/menu_operacion.py
16. api/redes.py
17. api/mapas.py

18. scripts Astra/RTAB-Map
19. yahboomcar_ws/src
```

---

# 45. Deuda técnica: monolitos

Aproximaciones observadas:

```text
sf_robot_server.py       ~4300 líneas
sf_app_dashboard.py      ~2800
sf_mission_lang.py       ~2400
sf_mapping_manager.py    ~1800
sf_nav_queue.py          ~1260
sf_mission_executor.py   ~1080
```

Se recomienda dividir por dominio.

---

# 46. Validación duplicada

Se observan funciones de validación de misiones repetidas entre Dashboard y Robot Server.

Ejemplos conceptuales:

```text
mission_name_valid
mission_point_id_valid
validate_mission_data
```

### Recomendación

Crear un paquete compartido:

```text
safevision_protocol
```

---

# 47. Configuración hardcodeada

Valores observados:

```text
/home/pi/robot_custom
/home/pi/yahboomcar_ws
/opt/ros/melodic
/dev/video0
/dev/input/js0
8090
8091
5000
11311
```

Se recomienda centralizar configuración.

---

# 48. Estado global en memoria

Dashboard y Robot Server almacenan estado global como:

```text
robot_ip
robot_estado
motor_ia
mission runtime
nav status
camera frame
live map
```

Esto complica:

```text
multi-worker
multiusuario
multi-robot
alta disponibilidad
```

---

# 49. IPC basado en `/tmp`

Existen archivos similares a:

```text
/tmp/safevision_map_pose.json
/tmp/safevision_initialpose_request.json
/tmp/safevision_initialpose_ack.json
/tmp/safevision_active_map.json
```

Esto dificulta separación por contenedores.

---

# 50. Seguridad

El Robot Server escucha en:

```text
0.0.0.0:8091
```

y el código disponible no muestra una capa robusta de autenticación/autorización para todas las operaciones.

### Regla

**No exponer directamente `8091` a Internet.**

Antes de cloud se requiere:

```text
autenticación
autorización
TLS/mTLS
identidad de robot
control de sesión
auditoría
rate limiting
```

---

# 51. Seguridad legacy

La arquitectura SSH anterior contiene credenciales hardcodeadas y `AutoAddPolicy`.

No deben mantenerse en una versión productiva.

---

# 52. Inferencia potencialmente repetida

Si cada cliente abre su propio stream de inferencia, YOLO puede ejecutarse varias veces sobre frames equivalentes.

Arquitectura recomendada:

```text
camera stream
     │
     ▼
single decoder
     │
     ▼
single inference worker
     │
     ▼
latest annotated frame
     │
     ├── cliente 1
     ├── cliente 2
     └── cliente N
```

---

# 53. MJPEG y doble codificación

El flujo actual puede implicar:

```text
Pi:
captura
JPEG encode

red

PC:
JPEG decode
YOLO
JPEG encode

navegador:
decode
```

No debe cambiarse antes de establecer baseline.

Posteriormente evaluar:

```text
WebRTC
GStreamer
H.264/H.265
RTSP
```

---

# 54. Python heterogéneo

El runtime utiliza combinaciones de:

```text
python
python3
/usr/bin/python
```

Antes de Docker documentar:

```text
OS
arquitectura CPU
ROS distro
Python ROS
Python 3
rospy
tf
OpenCV
PyTorch
Ultralytics
```

---

# 55. Dependencias no reproducibles

El snapshot disponible no muestra un manifest completo del runtime.

Esto NO significa que no exista en el repositorio real.

Debe verificarse o crearse:

```text
requirements-dashboard.txt
requirements-edge.txt
package.xml
rosdep
apt packages
versiones del SO
versiones ROS
```

---

# 56. Tests

No se observan pruebas first-party completas del runtime principal en el snapshot disponible.

Prioridades recomendadas:

```text
tests/unit/test_mission_lang.py
tests/unit/test_mission_schema.py
tests/unit/test_map_validation.py
tests/unit/test_navigation_commands.py

tests/integration/test_robot_api.py
tests/integration/test_mission_runtime.py
tests/integration/test_mapping_transition.py

tests/hardware/
```

---

# 57. Decisiones actuales que conviene preservar

```text
separación Dashboard / robot
Robot Server como frontera HTTP-ROS
captura de cámara compartida
selector manual/navigation
watchdog de cmd_vel
cancelación explícita
mapa asociado a cola
prevalidación con make_plan
rollback de mapping
validate -> simulate -> execute
health endpoint
```

---

# 58. Matriz de certeza

| Subsistema | Implementado en fuente | Evidencia histórica | Validación física actual |
|---|---:|---:|---:|
| Control teclado | Sí | Sí | Revalidar |
| Control mando | Sí | Sí | Revalidar |
| Cámara RGB | Sí | Sí | Revalidar |
| Robot Server `8091` | Sí | Sí | Revalidar |
| Dashboard `5000` | Sí | Sí | Revalidar |
| YOLO en PC | Sí | Sí | Revalidar |
| Mapas 2D | Sí | Sí | Revalidar |
| AMCL/localización | Sí | Sí | Revalidar |
| Pose en mapa | Sí | Sí | Revalidar |
| Initial pose | Sí | Sí | Revalidar |
| `move_base` | Sí | Sí | Revalidar |
| Navegación por puntos | Sí | Sí | Revalidar |
| Cola de navegación | Sí | Sí | Revalidar |
| Recovery | Sí | Sí | Revalidar |
| Mapping Gmapping | Sí | Sí | Revalidar |
| Gestión de mapas | Sí | Sí | Revalidar |
| DSL de misiones | Sí | Sí | Revalidar |
| Simulación de misiones | Sí | Sí | Revalidar |
| `ir` automático | Sí | Sí | Revalidar |
| `esperar` automático | Sí | Sí | Revalidar |
| `orientar` automático | Sí | Sí | Revalidar |
| `girar` físico DSL | No completo | Parcial | Pendiente |
| `relocalizar` físico DSL | No completo | Parcial | Pendiente |
| Registry moderno persistente de modelos | Parcial | En evolución | Pendiente |
| UI moderna de modelos | No auditable con snapshot | Sí, en desarrollo | Recuperar frontend |
| Cámara de profundidad moderna | No integrada | Pre-profundidad | Pendiente |
| RTAB-Map moderno | No integrado | Experimental | Pendiente |
| Cloud | No | Intención futura | Pendiente |
| Contenedores | No confirmado | Intención futura | Pendiente |
| Multi-robot real | No confirmado | Conceptual | Pendiente |

---

# 59. Acceptance test antes del refactor

## Arranque
- reboot;
- arranque limpio;
- verificar procesos residuales.

## ROS
- roscore;
- driver;
- IMU;
- EKF;
- LiDAR;
- AMCL;
- TF;
- move_base.

## Control
- teclado;
- mando;
- watchdog;
- stop.

## Cámara
- video raw;
- reconexión;
- FPS;
- CPU.

## Dashboard
- conexión `:8091`;
- health;
- stream.

## IA
- cargar `.pt`;
- cargar JSON;
- confidence;
- detecciones.

## Pose
- `map -> base_footprint`;
- Dashboard;
- initialpose.

## Navegación
- un punto;
- varios puntos;
- cancel;
- clear;
- mapa incorrecto;
- ruta imposible;
- recovery.

## Mapping
- start;
- save;
- discard;
- rollback;
- restaurar AMCL;
- restaurar map_server.

## Mapas
- list;
- rename;
- duplicate;
- import;
- export;
- edit;
- delete.

## Misiones
- crear;
- guardar;
- cargar;
- validar;
- simular;
- prepare;
- start;
- status;
- cancel;
- esperar;
- ir;
- orientar.

## Shutdown
- sin roslaunch huérfanos;
- sin cámara residual;
- sin `cmd_vel` residual.

---

# 60. Recolección inicial obligatoria

```bash
uname -a
cat /etc/os-release
uname -m

python --version
python3 --version

rosversion -d
rosversion -a

pip freeze
pip3 freeze

lsusb
ls -l /dev/video*
ls -l /dev/input/js*
ls -l /dev/tty*

rosnode list
rostopic list
rosservice list

git status
git branch -vv
git log --oneline --decorate -30
```

También capturar árboles limpios de:

```text
robot_custom
yahboomcar_ws/src
```

---

# 61. Uso del grafo durante la auditoría

```bash
type -a grafo
grafo
```

Si `8080` está ocupado:

```bash
sudo ss -ltnp | grep ':8080'
```

Utilizar la herramienta junto con:

```text
git grep
ripgrep
AST analysis
runtime tracing
```

---

# 62. Plan de refactor recomendado

## Fase 0 — congelar baseline

Crear un tag:

```text
pre-refactor-baseline
```

Guardar estado Git y ROS.

## Fase 1 — limpiar repositorio

Separar:

```text
vigente
legacy
tools
tests
deploy
```

## Fase 2 — contratos

Crear:

```text
safevision_protocol
```

con:

```text
RobotHealth
MapMetadata
Mission
MissionPoint
NavigationCommand
NavigationStatus
ModelMetadata
```

## Fase 3 — dividir monolitos

Separar por dominio.

## Fase 4 — configuración

Eliminar valores hardcodeados.

## Fase 5 — tests

Unit + integration + hardware.

## Fase 6 — contenerización edge

Primero equivalencia funcional.

## Fase 7 — desacoplar Dashboard

Separar frontend de lógica local.

## Fase 8 — cloud

Identidad, registry, telemetría, control plane.

## Fase 9 — profundidad

Integrar sobre arquitectura estabilizada.

---

# 63. Contenerización: arquitectura propuesta

Las funciones críticas deben permanecer en edge:

```text
drivers
ROS
IMU
EKF
LiDAR
localización
move_base
cmd_vel selector
watchdogs
navigation
mapping
camera capture
```

Una caída de Internet no debe impedir detener el robot de forma segura.

---

# 64. Cloud: arquitectura propuesta

```text
                         CLOUD
              ┌────────────────────┐
              │ Auth               │
              │ Fleet              │
              │ Missions           │
              │ Maps               │
              │ Models             │
              │ Telemetry          │
              │ Audit              │
              └─────────┬──────────┘
                        │
                 canal seguro
                        │
              ┌─────────▼──────────┐
              │ SafeVision Edge    │
              │ Agent              │
              └─────────┬──────────┘
                        │
                       ROS
                        │
                      Robot
```

Nunca publicar directamente:

```text
ROS Master :11311
Robot Server :8091
```

a Internet.

---

# 65. SafeVision Edge Agent

La recomendación central es hacer evolucionar:

```text
sf_robot_server.py
```

hacia un:

```text
SafeVision Edge Agent
```

modular.

Debe constituir la frontera estable entre:

```text
cloud/dashboard
```

y:

```text
ROS/hardware
```

---

# 66. Comunicación cloud ↔ robot

Recomendación:

el robot inicia una conexión saliente segura.

Opciones:

```text
WebSocket TLS
MQTT TLS
gRPC streaming
VPN + API
```

Cada comando debería llevar identificadores y expiración.

---

# 67. Registry de modelos

No guardar pesos dentro de imágenes Docker.

Arquitectura propuesta:

```text
Object Storage
    ├── weights
    └── metadata

Database
    ├── model_id
    ├── version
    ├── classes
    ├── checksum
    └── assignment
```

---

# 68. Registry de mapas

Tratar:

```text
map.yaml
map.pgm
```

como una unidad versionada.

---

# 69. Registry de misiones

Separar:

```text
MissionDefinition
MissionVersion
MissionRun
MissionEvent
```

---

# 70. Observabilidad

Se recomiendan logs estructurados y métricas.

Métricas:

```text
online
CPU
RAM
temperatura
FPS
ancho de banda
Wi-Fi
battery
navigation failures
recovery count
mission duration
mapping failures
ROS node health
```

---

# 71. Integración de profundidad

Primero verificar:

```text
driver
RGB
depth
camera_info
TF
timestamps
CPU
RAM
USB bandwidth
```

Después decidir entre:

```text
A. depth -> LaserScan
B. point cloud
C. RTAB-Map
D. distancia a detecciones YOLO
E. navegación 3D
```

La estrategia incremental más conservadora es:

```text
Depth Camera
     │
     ▼
depthimage_to_laserscan
     │
     ▼
costmap
     │
     ▼
move_base
```

---

# 72. Riesgos priorizados

## P0

```text
Robot Server sin seguridad suficiente para Internet
snapshot incompleto
launch/frontend no auditados
dependencia no inventariada de yahboomcar_ws
sin baseline hardware actual documentado
```

## P1

```text
duplicidad api / misiones
monolitos
rutas hardcodeadas
estado global
IPC /tmp
health ambiguo
acciones DSL no ejecutables
registry moderno de modelos incompleto
mezcla Python/ROS
```

## P2

```text
MJPEG
doble codificación
inferencia potencialmente repetida
nombres de mapas inconsistentes
menús anteriores desactualizados
exportador contaminado con .venv
```

---

# 73. Clasificación propuesta del código

## Candidato a núcleo vigente

```text
misiones/pilotada/robot
misiones/pilotada/dashboard_src
misiones/automatica/robot
```

## Mantener y revisar

```text
mapping
modelos
misiones/programadas
network
```

## Generación anterior / candidata a legacy

```text
api/dashboard_pc_src
api/sf_conexion_ssh.py
api/transmisor_camara_pi.py
api/sf_teleop_*.py
otras implementaciones duplicadas
```

Esto NO significa que puedan borrarse inmediatamente.

## Tools

```text
grafo
generar_arbol.py
exportar_codigo.sh
```

## Experimentos 3D

```text
mapeo_denso.sh
auto_mapeo.sh
emisor_sensores.sh
scripts Astra/RTAB
```

---

# 74. Estructura objetivo propuesta

Esta estructura es una recomendación, no una decisión actual.

```text
safevision/
│
├── services/
│   ├── edge-api/
│   ├── dashboard-api/
│   ├── inference/
│   └── cloud-api/
│
├── packages/
│   ├── safevision-protocol/
│   ├── safevision-missions/
│   └── safevision-ros/
│
├── ros/
│   ├── launch/
│   ├── config/
│   └── nodes/
│
├── web/
├── config/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── hardware/
├── deploy/
│   ├── docker/
│   ├── compose/
│   └── cloud/
├── tools/
├── legacy/
└── docs/
```

---

# 75. Lo que NO debe hacerse inicialmente

No cambiar simultáneamente:

```text
ROS
Python
contenedores
Dashboard
cloud
navegación
profundidad
```

Primero debe existir un baseline.

Tampoco debe borrarse `api/` de inmediato.

---

# 76. Primera sesión recomendada del desarrollador senior

1. Confirmar estado Git.
2. Inventariar archivos reales con `git ls-files`.
3. Recuperar `.launch`, templates, static y manifests.
4. Inventariar `yahboomcar_ws/src`.
5. Ejecutar `grafo`.
6. Lanzar runtime pilotado sin cambios.
7. Capturar ROS.
8. Completar acceptance test.
9. Crear tag baseline.

---

# 77. Criterios antes de borrar código

Un archivo sólo debe eliminarse si se confirma:

```text
no importado
no ejecutado por subprocess
no ejecutado por shell
no referenciado en launch
no utilizado por menú
no utilizado por systemd/cron
no documentado como fallback
no requerido por tests
```

y el acceptance test pasa antes y después.

---

# 78. Decisión arquitectónica más importante

La frontera más valiosa ya existente es:

```text
ROS / Hardware
      │
      ▼
Robot Server
      │
      ▼
Dashboard / futuro cloud
```

El refactor debería fortalecer esta frontera.

---

# 79. Principio de seguridad fundamental

Los loops críticos deben permanecer locales:

```text
cmd_vel
watchdog
move_base
cancel
emergency stop
drivers
sensores
```

Cloud no debe cerrar directamente el loop de movimiento físico.

---

# 80. Estado final para el siguiente equipo

## Implementado en fuente y prioritario de preservar

```text
control manual
cámara RGB
Robot Server
Dashboard PC
YOLO PC
mapas 2D
AMCL
pose
initial pose
move_base
navegación por puntos
cola
recovery
mapping Gmapping
gestión de mapas
DSL
simulación
runtime automático básico
```

## Parcial o pendiente de consolidación

```text
registry moderno de modelos
UI moderna de modelos
acciones completas del DSL
health consistente
tests
dependency manifests
packaging reproducible
```

## Pendiente / experimental

```text
profundidad integrada
RTAB-Map moderno
navegación 3D
cloud
contenedores
auth
fleet management
multi-robot real
CI/CD
observabilidad central
```

---

# 81. Conclusión

SafeVision ya no debe tratarse como un conjunto aislado de scripts.

La arquitectura más reciente contiene una separación útil:

```text
hardware / ROS
        ↓
Robot Server
        ↓
Dashboard
        ↓
misiones / navegación
```

La principal tarea del próximo equipo es:

```text
1. recuperar el repositorio real completo;
2. congelar baseline;
3. verificar hardware;
4. identificar código vigente mediante tracing;
5. separar generación anterior;
6. formalizar contratos;
7. agregar tests;
8. modularizar;
9. contenerizar edge;
10. agregar seguridad;
11. desacoplar Dashboard;
12. añadir cloud;
13. integrar profundidad.
```

Las dos precauciones principales son:

1. No interpretar el grafo del 8 de agosto como arquitectura actual.
2. No interpretar “implementado en fuente” como “validado físicamente”.

La recomendación central es utilizar el runtime moderno de:

```text
misiones/pilotada/
```

como punto de partida del refactor, tratar:

```text
sf_robot_server.py
```

como precursor del futuro **SafeVision Edge Agent**, y mantener toda operación crítica del robot en el edge.

---

# Apéndice A — Checklist de handoff

```text
[ ] HEAD confirmado
[ ] branch confirmado
[ ] working tree confirmado
[ ] tag baseline creado

[ ] *.launch recuperados
[ ] templates recuperados
[ ] static recuperado
[ ] dependencies recuperadas

[ ] yahboomcar_ws inventariado

[ ] control teclado probado
[ ] control mando probado
[ ] cámara probada
[ ] Dashboard probado
[ ] YOLO probado
[ ] localización probada
[ ] pose probada
[ ] initialpose probado
[ ] navegación 1 punto probada
[ ] navegación cola probada
[ ] cancelación probada
[ ] recovery probado
[ ] mapping start probado
[ ] mapping save probado
[ ] mapping discard probado
[ ] CRUD mapas probado
[ ] DSL validado
[ ] simulador validado
[ ] misión ir probada
[ ] misión esperar probada
[ ] misión orientar probada
[ ] shutdown limpio probado
```

---

# Apéndice B — Fuentes internas utilizadas

```text
robot_custom_grafo_resumen.txt
codigo_proyecto.txt

historial del proyecto SafeVision / Rosmaster X3
sesiones de desarrollo anteriores
estado Git mostrado durante el desarrollo
```

El grafo debe tratarse como fotografía histórica.

El código consolidado debe tratarse como snapshot parcial.

La fuente final de verdad debe ser siempre el repositorio real del robot en el commit/tag confirmado durante el handoff.
