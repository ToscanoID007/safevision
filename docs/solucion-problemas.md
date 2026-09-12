# Solución de problemas

**Para quién es y cuándo leerlo**
Para cuando algo no funciona y hace falta una respuesta rápida, sin leer el código.
Busca tu síntoma en el índice, ve a esa sección. Cada entrada es síntoma → causa → solución.

---

**Origen:** los registros reales del robot (`~/safevision-raw/misiones/pilotada/logs/`), la
lógica de *watchdog* y recuperación del código, y la verificación de
`docs/estado-actual.md`.

---

## 0. Los cuatro comandos de diagnóstico

Antes de nada, con `R=http://<IP-DEL-ROBOT>:8091`:

```bash
# 1. ¿Está vivo el robot en la red?
ping -c 3 yahboom.local

# 2. ¿Responde el Robot Server?
curl -s $R/health | python3 -m json.tool

# 3. ¿Qué recursos están encendidos? ← EL MÁS ÚTIL
curl -s $R/runtime/status | python3 -m json.tool

# 4. ¿Qué dicen los servicios?
ssh pi@yahboom.local 'systemctl status safevision-roscore safevision-robot-server'
```

**El 80 % de los problemas se diagnostican con el número 3.**

---

## 1. Índice de síntomas

| Síntoma | Sección |
|---|---|
| `/health` devuelve `"ok": false` | [§2.1](#21-health-devuelve-ok-false) |
| El robot no se mueve, pero todo parece bien | [§2.2](#22-el-robot-no-se-mueve-pero-todo-parece-bien) |
| `"ok": false` en modo teclado, siempre | [§2.3](#23-ok-false-permanente-en-modo-teclado) |
| No encuentro el robot en la red | [§3](#3-red) |
| `/runtime/profile` falla con `409` | [§4](#4-fallos-al-aplicar-un-perfil) |
| El LiDAR no publica | [§4.3](#43-se-detiene-en-lidar) |
| La IMU no publica / `core` falla | [§4.2](#42-se-detiene-en-core) |
| El robot se desvía o cree estar donde no está | [§5](#5-localización) |
| La navegación no arranca o se queda a medias | [§6](#6-navegación) |
| El mapa sale mal | [§7](#7-mapeo) |
| No hay vídeo | [§8](#8-cámara-y-vídeo) |
| La misión no arranca | [§9](#9-misiones) |
| `killall` mató el `roscore` | [§10.1](#101-alguien-ejecutó-un-alias-heredado) |
| Tras reiniciar, el robot no hace nada | [§10.2](#102-tras-reiniciar-el-robot-no-hace-nada) |

---

## 2. Estado y salud

### 2.1 `/health` devuelve `"ok": false`

**Causa más frecuente: es NORMAL.** Recién arrancado, el robot levanta sólo el ROS Master y
el Robot Server. No hay driver, ni LiDAR, ni navegación, y por eso `ok` es `false`.

**Comprobación:**

```bash
curl -s $R/runtime/status | python3 -m json.tool | grep -A4 '"profile"'
```

Si sale `"requested": null` e `"inferred": "base"`, **no hay ningún perfil aplicado**.

**Solución:** aplica un perfil (`docs/manual-operacion.md` §2):

```bash
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'
```

> Esto **no es un fallo del sistema**, es su diseño: el robot no puede moverse hasta que
> alguien lo pide explícitamente. Ver `docs/estado-actual.md` §1.

### 2.2 El robot no se mueve, pero todo parece bien

Por orden:

1. **¿Hay perfil aplicado?** → §2.1.
2. **¿Está el selector en el modo correcto?**

```bash
curl -s $R/runtime/status | python3 -m json.tool | grep -A3 '"selector"'
```

`"active": true` requerido. Si no, falta el perfil.

3. **¿El *watchdog* está parando el robot?** Si teleoperas con `curl` sueltos, el robot
   se para a los 0,5 s. **Es correcto.** Hay que enviar órdenes continuamente (~10 Hz).
4. **¿Está el driver vivo?** `"driver": {"active": true}`. Si no, revisa la alimentación
   del chasis y `/dev/myserial`.
5. **¿Batería baja?** Los motores dejan de responder antes que la Raspberry Pi. Es la causa
   más subestimada.

### 2.3 `"ok": false` permanente en modo teclado

**Causa:** `/health` exige el nodo `/yahboom_keyboard` cuando `control_mode` es `teclado`
(`sf_robot_server.py:563-566`), pero el camino vigente implementa el teclado **desde el
navegador, sin nodo ROS**. El gestor lo reporta como
`"teclado": {"implementation": "dashboard_keyboard"}`.

**Solución:** ignora `/health` en modo teclado y usa `/runtime/status`. No es un fallo real:
es una inconsistencia conocida entre dos formas de medir lo mismo (handoff §15).

---

## 3. Red

Ver `docs/red.md` §6 para el procedimiento completo. Resumen:

| Síntoma | Causa | Solución |
|---|---|---|
| `ping yahboom.local` → `Name or service not known` | mDNS no resuelve | `sudo apt install avahi-daemon libnss-mdns`; o busca la IP con `nmap -sn 192.168.1.0/24` |
| `Destination Host Unreachable` | Redes distintas | Comprueba que ambos estén en el mismo Wi-Fi, no en la de invitados |
| El dashboard dice "IP inválida" | Escribiste `yahboom.local` | **Sólo acepta IPv4.** Usa el número que imprime `run_dashboard.sh` |
| Conectaba ayer y hoy no | La IP cambió (DHCP) | `./scripts/run_dashboard.sh` la resuelve sola. Considera una reserva DHCP |
| `curl` se queda colgado | Cortafuegos o aislamiento de clientes en el AP | Prueba desde otra máquina; revisa el router |

---

## 4. Fallos al aplicar un perfil

`POST /runtime/profile` devuelve `409` y un campo `steps[]` que dice **exactamente en qué
recurso se detuvo**. Empieza siempre por ahí:

```bash
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2"}' | python3 -m json.tool
```

Los registros de cada recurso están en el robot, en `/tmp/safevision_runtime_logs/`:

```bash
ssh pi@yahboom.local 'ls -la /tmp/safevision_runtime_logs/ && tail -30 /tmp/safevision_runtime_logs/lidar.log'
```

### 4.1 Se detiene en `driver`

| Causa | Solución |
|---|---|
| La placa del chasis no está encendida | Interruptor del Rosmaster, no sólo el de la Pi |
| `/dev/myserial` no existe | `ssh pi@yahboom.local 'ls -la /dev/myserial'`. Debe enlazar a `ttyUSB1`. Reconecta el USB |
| Ya hay un `/driver_node` de una sesión anterior | `curl -X POST $R/runtime/profile -d '{"profile":"libre"}' -H 'Content-Type: application/json'` y reintenta |
| Batería baja | Cárgala |

En `driver.log` un arranque correcto se ve así:

```
Rosmaster Serial Opened! Baudrate=115200
----------------create receive threading--------------
```

### 4.2 Se detiene en `core`

`core` son `/odometry_publisher`, `/imu_filter_madgwick` y `/ekf_localization`, **y además
exige que `/imu/imu_data` publique de verdad**.

| Causa | Solución |
|---|---|
| **El robot se movió durante el arranque** | `apply_calib` calibra el giróscopo al inicio: **el robot debe estar quieto**. Reintenta sin tocarlo |
| El driver no publica IMU | Revisa §4.1 primero: `core` depende de `driver` |
| La calibración tarda | El sistema espera hasta 15 s por `/imu/imu_data`. En una Pi cargada puede no bastar: reintenta |

> **La causa número uno es mover el robot mientras arranca.** Déjalo quieto 10 segundos.

### 4.3 Se detiene en `lidar`

El gestor es especialmente estricto aquí: no le basta con que el nodo `/rplidarNode` exista,
**exige un mensaje real en `/scan`**, y si el nodo está vivo pero mudo, lo reinicia (hasta
dos intentos). Es la "recuperación de LiDAR" del código.

| Causa | Solución |
|---|---|
| El LiDAR no gira | Escúchalo. Si no gira: alimentación del USB |
| `/dev/rplidar` no existe | `ssh pi@yahboom.local 'ls -la /dev/rplidar'` → debe enlazar a `ttyUSB0` |
| Gira pero no publica | El puerto serie quedó bloqueado por una sesión anterior. Perfil `libre` y reintenta |
| Se enumeró en otro orden | Las reglas `udev` lo evitan; si faltan, reinstálalas (`docs/instalacion-robot.md` §3.5) |
| Cable USB flojo | Es un fallo muy común y muy poco sospechado |

### 4.4 Se detiene en `localization`

| Causa | Solución |
|---|---|
| El mapa no existe | `curl -s $R/maps` y usa el nombre **exacto** (distingue mayúsculas) |
| El par `.yaml`/`.pgm` está incompleto | Ambos ficheros deben existir en `mapping/maps/` |
| AMCL no arranca | `tail -40 /tmp/safevision_runtime_logs/localization.log` |

### 4.5 Se detiene en `navigation`

| Causa | Solución |
|---|---|
| `move_base` tarda más de 18 s | La Pi va justa. Reintenta |
| Falta el mapa o el LiDAR | `navigation` depende de ambos: revisa §4.3 y §4.4 |

En `navegacion.log` estos avisos son **normales** y no indican fallo:

```
[WARN] global_costmap: Parameter "plugins" not provided, loading pre-Hydro parameters
[WARN] local_costmap:  Parameter "plugins" not provided, loading pre-Hydro parameters
```

Significan que los costmaps usan la configuración clásica en vez de la de capas. Es
intencionado.

---

## 5. Localización

### 5.1 `/map_pose` devuelve `"localized": false`

| Causa | Solución |
|---|---|
| No hay perfil con mapa | §2.1 |
| AMCL no corre | `curl -s $R/runtime/status \| grep -A4 localization` |
| El pose exporter no arrancó | Mira `"pose_exporter"`. Su log: `/tmp/safevision_runtime_logs/pose_exporter.log` |
| No se ha fijado la pose inicial | `docs/manual-operacion.md` §4 |

En `pose_exporter.log`, un arranque correcto:

```
[WARN] Esperando TF map -> base_footprint: "map" passed to lookupTransform ...
[INFO] SafeVision pose/exporter iniciado
[INFO] TF disponible. Exportando pose a 10 Hz
```

> Ese `WARN` inicial es **normal**: el exportador arranca antes de que AMCL publique la
> transformada y reintenta hasta conseguirla.

### 5.2 El robot cree estar donde no está

| Causa | Solución |
|---|---|
| Pose inicial mal fijada | Vuelve a fijarla con cuidado (`docs/manual-operacion.md` §4) |
| AMCL no ha convergido | **Teleopera el robot un metro y gíralo.** AMCL converge con movimiento, no parado |
| El mapa no corresponde a la sala | ¿Cambiaron los muebles? Vuelve a mapear |
| Deriva de odometría | Ruedas omnidireccionales patinan en suelo liso. Es esperable; AMCL debe corregirlo |

### 5.3 La pose "salta" bruscamente

AMCL está resolviendo una ambigüedad: pasillos largos y simétricos producen esto.

**Solución:** fija la pose inicial con más precisión, y mueve el robot por zonas con
geometría distintiva (esquinas, no pasillos vacíos).

---

## 6. Navegación

### 6.1 `/nav/queue` devuelve `409`

**Causa:** algún punto no tiene plan. La cola prevalida cada punto con
`move_base/make_plan` **antes** de aceptar nada.

| Causa concreta | Solución |
|---|---|
| El punto está sobre una pared o en zona negra | Muévelo a espacio libre |
| El punto está demasiado cerca de una pared | La capa de inflado (0,30 m) lo hace inalcanzable. Sepáralo |
| Mala localización | Si el robot cree estar en otro sitio, no hay plan. §5 |
| El mapa de la cola no es el activo | La cola se ata al mapa: usa el mapa en uso |

> **Que se rechace aquí es bueno:** el sistema prefiere decir que no antes de mover el
> robot hacia algo imposible.

### 6.2 `state: "unavailable"`

La cola (`/sf_nav_queue`) no corre → falta el perfil. §2.1.

### 6.3 El robot gira sobre sí mismo y no avanza

Es un ***recovery behavior*** de `move_base`: se cree bloqueado y limpia los costmaps
girando.

| Causa | Solución |
|---|---|
| Obstáculo real que no ve bien | Despeja la zona |
| Costmap sucio por lecturas antiguas | Cancela y reintenta |
| Mala localización | §5 |
| Objetivo inalcanzable | Cancela y elige otro punto |

**Cancela así:** `curl -X POST $R/nav/cancel`

### 6.4 Se detiene antes de llegar

| Causa | Solución |
|---|---|
| Obstáculo detectado en el trayecto | Mira el costmap en el dashboard |
| Tolerancia del objetivo | `move_base` da por bueno el punto dentro de una tolerancia: es normal quedarse a unos centímetros |
| Batería baja | Los motores pierden fuerza antes de que falle la Pi |

### 6.5 Choca con algo que no ve

**Causa casi segura: el obstáculo está fuera del plano del LiDAR.** Barre un único plano a
11 cm del suelo.

No detecta: mesas con patas finas, escalones, objetos bajos, obstáculos colgantes.

**Solución a corto plazo:** despeja la zona de prácticas de esos elementos.
**Solución de fondo:** integrar la profundidad de la cámara RGB-D
(`docs/analisis-alcance.md` §4).

---

## 7. Mapeo

### 7.1 `/mapping/session/start` devuelve `409`

| Mensaje | Causa | Solución |
|---|---|---|
| "requiere Pilotada o Automatica con mapa activo" | No hay perfil aplicado | Aplica un perfil con mapa **antes** de mapear |
| "requiere recursos activos: ..." | Falta algún recurso | La lista dice cuáles; §4 |
| "Cancela la mision automatica..." | Hay una misión en marcha | `curl -X POST $R/mission/cancel` |

> **Parece contradictorio pedir un mapa para mapear**, pero tiene sentido: el sistema
> necesita saber **a qué perfil y a qué mapa volver** cuando termines.

### 7.2 El mapa sale torcido, doble o con paredes gruesas

| Causa | Solución |
|---|---|
| Giros bruscos | Pilota **despacio** y gira suave |
| Bucles sin cerrar | Vuelve a puntos ya visitados |
| Odometría con deriva | Suelo liso + ruedas omni = patinaje. Ve más despacio |
| Velocidad excesiva | Gmapping necesita solape entre barridos |

**Solución:** `POST /mapping/session/discard` y repite. Descartar es barato.

### 7.3 Zonas en blanco

El LiDAR no llegó: alcance limitado (~3,5 m útiles según `obstacle_range`), o el haz no
entró por una puerta estrecha. Acércate más y recorre esas zonas despacio.

### 7.4 Guardé el mapa y el robot se quedó sin navegación

Es un fallo del *rollback*. Tras `save`, el sistema debe restaurar el perfil anterior con el
mapa nuevo.

**Comprobación:** `curl -s $R/runtime/status | python3 -m json.tool | grep -A4 profile`

**Solución:** vuelve a aplicar el perfil a mano:

```bash
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"<mapa_nuevo>","control":"mando"}'
```

---

## 8. Cámara y vídeo

| Síntoma | Causa | Solución |
|---|---|---|
| Sin imagen en el dashboard | El navegador no alcanza `:8091` | Prueba `http://<IP>:8091/video_feed` directo |
| `"camera": false` | `/dev/video0` no existe | `ssh pi@yahboom.local 'ls -la /dev/video*'`. Reconecta el USB |
| Vídeo entrecortado | Wi-Fi saturado (≈4 Mbit/s) | Acércate al punto de acceso |
| La cámara tarda en aparecer | Apertura perezosa, en la primera petición | Normal: espera unos segundos |
| YOLO no dibuja cajas | Falta el modelo en la PC | `curl -s $R/models`; revisa el dashboard |

**Sobre un error que verás en los registros:**

```
[ERROR] global loadsave.cpp:1355 imdecode_(''): can't read header:
OpenCV(5.0.0) ... WebPDecoder::readHeader() Buffer is too small
```

**Causa:** en el robot conviven **tres instalaciones de OpenCV**
(`docs/anexo-dependencias-robot.md` §3.1). Este error concreto aparece al intentar decodificar
una imagen vacía, **no** en el flujo de vídeo, que funciona.

**Solución:** ninguna urgente. No toques las instalaciones de OpenCV antes de tener una
imagen de respaldo de la microSD.

---

## 9. Misiones

| Síntoma | Causa | Solución |
|---|---|---|
| **`Acción todavía no habilitada: girar`** | La misión usa `girar()` o `relocalizar()` | **No están implementadas.** Quítalas. `docs/lenguaje-misiones.md` §2 |
| `La misión no está en estado ready` | Falta `POST /mission/prepare` | Prepara antes de ejecutar |
| `El punto 'X' no existe en esta misión` | Alias mal escrito o punto borrado | Revisa los puntos |
| Se queda en el primer `ir()` | Sin plan, o mala localización | §5 y §6.1 |
| `esperar()` no termina | Está esperando de verdad | `mission/status` muestra el tiempo restante |

---

## 10. Problemas del sistema

### 10.1 Alguien ejecutó un alias heredado

> ⚠️ **Causa real, difícil de diagnosticar y fácil de provocar.**

El `.bashrc` del robot tiene 13 alias heredados (`docs/estado-actual.md` §6). **Dos** de
ellos —`mapeo_denso` y `sensores`— ejecutan scripts que empiezan por:

```bash
killall -9 roslaunch rviz roscore
```

**Si alguien los teclea con los servicios activos, mata el `roscore` gestionado por
systemd.**

Otros dos, `mapeo_ligero` y `mapear`, no matan `roscore` pero lanzan LiDAR y chasis por su
cuenta, compitiendo con el runtime por los mismos dispositivos.

**Síntomas:** todo deja de responder de golpe; `/runtime/status` da `ros_master: false`;
poco después el `roscore` reaparece (systemd lo reinicia) pero **nada funciona**, porque el
Robot Server quedó hablando con un Master nuevo y el estado en `/tmp` quedó obsoleto.

**Solución:**

```bash
ssh pi@yahboom.local 'sudo systemctl restart safevision-robot-server'
```

Y después aplica el perfil de nuevo (§2.1).

**Prevención — ya hay un script listo.** `scripts/robot_desactivar_alias.sh` comenta (no
borra) los **cuatro** alias de riesgo —los dos destructivos y los dos conflictivos—,
guarda copia de seguridad fechada de `~/.bashrc` y muestra el diff. Es idempotente y
reversible. Los scripts siguen ahí: lo que se retira es el atajo, no la herramienta.

Desde la PC, en una sola línea:

```bash
scp scripts/robot_desactivar_alias.sh pi@<IP-ROBOT>:/tmp/ && \
  ssh -t pi@<IP-ROBOT> 'bash /tmp/robot_desactivar_alias.sh && source ~/.bashrc'
```

Pide confirmación antes de tocar nada. Para revertir, el propio script imprime la orden
exacta con la ruta de la copia de seguridad.

### 10.2 Tras reiniciar, el robot no hace nada

**Es el comportamiento esperado.** Los servicios arrancan solos (verificado: llevaban
1 h 55 min activos tras un arranque en frío), pero **el perfil no se aplica solo**: `/tmp`
se vacía en cada reinicio y el estado del runtime nace vacío.

**Solución:** aplica un perfil (§2.1). **Cada vez que se reinicia el robot.**

> Si esto molesta en el día a día, hay dos caminos, ambos pendientes de decisión:
> publicar el dashboard que ya tiene el botón (`docs/estado-actual.md` §5.5), o crear una
> unidad `safevision-runtime-default.service` que aplique un perfil por defecto tras
> arrancar el Robot Server.
> **Decisión tomada:** no se crea un servicio de perfil por defecto. El arranque sin motores es seguro por diseño, y con la página *Pilotada* aplicar el perfil es un clic.

### 10.3 Los servicios no arrancan al encender

```bash
ssh pi@yahboom.local 'systemctl is-enabled safevision-roscore safevision-robot-server'
```

Deben decir `enabled` los dos. Si no:

```bash
ssh pi@yahboom.local 'cd ~/robot_custom && ./misiones/pilotada/systemd/install_services.sh'
```

### 10.4 El disco se llena

```bash
ssh pi@yahboom.local 'df -h / && du -sh ~/.ros/log'
```

Los registros de ROS crecen sin límite. Para purgarlos:

```bash
ssh pi@yahboom.local 'rosclean purge -y'
```

### 10.5 Nada de lo anterior funciona

Por orden, del menos al más drástico:

1. Perfil `libre` y vuelve a aplicar el perfil que quieras.
2. `sudo systemctl restart safevision-robot-server`
3. `sudo systemctl restart safevision-roscore safevision-robot-server`
4. Reinicia el robot: `sudo reboot`
5. Restaura la imagen de la microSD (`docs/instalacion-robot.md` §2.2).

---

## 10.6 Un nodo murió por fuera y el perfil ya no arranca

**Síntoma.** `POST /runtime/profile` responde `409` con *"No se pudo iniciar driver"* (o
`localization`, `core`…) aunque el robot esté bien, y `runtime/status` muestra ese recurso
inactivo. Sólo el vídeo funciona.

**Causa.** Un nodo de SafeVision murió por fuera del gestor. Los dos casos vistos:

1. **Colisión de nombres.** Alguien lanzó un *launch* de fábrica de Yahboom
   (`laser_bringup.launch`, `amcl.launch`…) desde el menú antiguo `api/gestor_nodos.py` o
   desde un script heredado. Registran `driver_node`, `odometry_publisher`, `rplidarNode`
   con los mismos nombres que SafeVision, y ROS mata al que ya estaba (`driver.log`: *"new
   node registered with same name"*).
2. **`rosnode kill`, un apagado a medias o una caída del nodo.**

Hasta `v1-validado-pilotada`, el gestor daba por vivo al proceso muerto (zombi) y se negaba
a relanzarlo. **Desde `v1.1-gestor-robusto` se recupera solo**: basta con volver a pedir el
perfil (verificado: driver, LiDAR y AMCL matados a propósito, relanzados en 16-18 s).

**Qué hacer.** Volver a aplicar el perfil desde la página *Pilotada* o con
`POST /runtime/profile`. Y **no usar el menú antiguo ni los scripts heredados con SafeVision
en marcha**: no consultan al gestor y pisan sus nodos.

**Verificación de la versión.** En el robot: `cd ~/robot_custom && git describe --tags`.
Debe ser `v1.1-gestor-robusto` o posterior.

## 10.7 "Robot no conectado" nada más arrancar el dashboard

**Síntoma.** Recién arrancado el dashboard, las páginas *Mapear*, *Mapas* o *Programar*
responden *"Robot no conectado"* aunque el robot esté en la red.

**Causa.** La sesión del dashboard se asocia al robot al visitar **Pilotada** o **Nodos**,
que toman la dirección del entorno (`run_dashboard.sh` la exporta). Las demás páginas no lo
hacen por sí solas.

**Qué hacer.** Abre primero la portada, *Pilotada* o *Nodos*. Es un comportamiento
heredado del dashboard; queda como mejora futura conectar en cualquier página.

## 11. Dónde están los registros

| Qué | Dónde |
|---|---|
| Servicios systemd | `journalctl -u safevision-robot-server -n 100` |
| Recursos del runtime | `/tmp/safevision_runtime_logs/*.log` (en el robot) |
| Nodos ROS | `~/.ros/log/` (en el robot) |
| Dashboard | la terminal donde corre `run_dashboard.sh` |
| Camino heredado | `misiones/pilotada/logs/` (sólo si se usó el script antiguo) |

> **`/tmp/safevision_runtime_logs/` se borra al reiniciar.** Si quieres conservar un
> registro de un fallo, cópialo antes.

---

## 12. Documentos relacionados

- `docs/manual-operacion.md` — procedimientos normales.
- `docs/estado-actual.md` — qué está realmente instalado y corriendo.
- `docs/red.md` — diagnóstico de red.
- `docs/api-robot-server.md` — significado de cada respuesta.
