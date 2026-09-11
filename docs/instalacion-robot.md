# Instalación y recuperación del robot

**Para quién es y cuándo leerlo**
Para quien tenga que restaurar la Raspberry Pi del robot: porque la tarjeta se corrompió,
porque hay que duplicar el equipo, o porque alguien rompió algo y hay que volver atrás.
Léelo **antes** de que haga falta: la §2 (crear la imagen de respaldo) se hace **hoy**,
con el robot funcionando, no el día del desastre.

---

**Robot de referencia:** `yahboom` — Yahboom Rosmaster X3 sobre Raspberry Pi 4
**Estado verificado:** 2026-09-10 (`docs/estado-actual.md`)
**Manifiesto completo de dependencias:** `docs/anexo-dependencias-robot.md`

---

## 0. Lee esto primero

Hay **dos caminos** para dejar un robot funcionando, y **no valen lo mismo**:

| | Camino A — imagen de la tarjeta | Camino B — reconstrucción desde cero |
|---|---|---|
| Qué es | Clonar la microSD actual, que funciona | Instalar todo paso a paso |
| Fiabilidad | **Alta.** Es una copia exacta de algo que funciona | **No validada.** Nadie la ha ejecutado entera |
| Tiempo | 20-40 min de copia | Varias horas, con imprevistos |
| Conserva reglas `udev`, `yahboomcar_ws` compilado, los tres Python, los 451 paquetes | **Sí, todo** | Hay que rehacerlo pieza a pieza |
| **Recomendación** | ✅ **Éste es el camino** | Sólo si no hay imagen |

> **El Camino A es la vía principal, y con diferencia.** El sistema del robot tiene
> demasiadas piezas frágiles y no documentadas en su origen —un Python 3.7.3 compilado a
> mano, tres espacios de trabajo catkin ya construidos, reglas `udev`, 451 paquetes ROS—
> como para confiar en reconstruirlo. **Clona la tarjeta.**

---

## 1. Qué hay dentro del robot (resumen)

| Elemento | Valor |
|---|---|
| Sistema | Ubuntu 18.04.6 LTS (Bionic), `aarch64` |
| Kernel | `5.4.0-1050-raspi` |
| ROS | Melodic, `ros_comm` 1.14.13, 451 paquetes |
| Python del Robot Server | `/usr/local/bin/python3` → **3.7.3** (compilado aparte) |
| Python de ROS | `/usr/bin/python` → 2.7.17 |
| Tarjeta | 59 GB, 29 GB usados (51 %) |
| Servicios | `safevision-roscore`, `safevision-robot-server` (ambos `enabled`) |
| Repositorio | `/home/pi/robot_custom` |
| Espacios catkin | `~/yahboomcar_ws`, `~/software/library_ws`, `~/software/world_canvas` |

Detalle completo, y la explicación de por qué hay tres intérpretes de Python, en
`docs/anexo-dependencias-robot.md`.

---

## 2. Camino A — imagen de la microSD (RECOMENDADO)

### 2.1 Crear la imagen de respaldo — hazlo hoy

Necesitas: la microSD del robot, un lector USB, y un disco con **60 GB libres**.

**Apaga el robot limpiamente antes de sacar la tarjeta:**

```bash
ssh pi@yahboom.local 'sudo shutdown -h now'
```

Espera a que se apaguen los LED, desconecta la alimentación y saca la microSD.

#### Opción 1 — Raspberry Pi Imager (gráfico, más sencillo)

1. Instálalo: `sudo apt install rpi-imager`
2. Conecta la microSD por el lector USB.
3. Abre `rpi-imager` → engranaje / menú → **"Read"** (leer tarjeta a fichero).
   > Si tu versión no tiene "Read", usa la Opción 2. No todas las versiones lo incluyen.
4. Elige la microSD como origen y un fichero destino, por ejemplo
   `~/safevision-robot-2026-09-10.img`.
5. Espera. 20-40 min según el lector.

#### Opción 2 — `dd` (terminal, siempre disponible)

**Identifica la tarjeta con cuidado.** Equivocarse de disco aquí destruye datos.

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL
```

Busca el dispositivo de ~64 GB con particiones `boot` y `writable`. Suele ser
`/dev/sdb` o `/dev/mmcblk0`. **Anótalo y compruébalo dos veces.**

```bash
# Desmonta (NO expulses) cualquier particion montada
sudo umount /dev/sdb1 /dev/sdb2 2>/dev/null || true

# Clona la tarjeta a un fichero. Cambia /dev/sdb por TU dispositivo.
sudo dd if=/dev/sdb of=~/safevision-robot-$(date +%F).img \
        bs=4M status=progress conv=fsync
```

> ⚠️ **`if=` es el origen y `of=` el destino. Invertirlos borra la tarjeta.**
> Antes de pulsar Enter, léelo en voz alta: *"input file, la tarjeta; output file, el
> fichero `.img`"*.

Comprime (la imagen son 59 GB, pero la mayoría son ceros):

```bash
gzip -9 ~/safevision-robot-$(date +%F).img     # queda en ~10-15 GB
sha256sum ~/safevision-robot-*.img.gz > ~/safevision-robot.sha256
```

**Guarda la imagen en dos sitios distintos.** Una copia de seguridad en un solo disco no
es una copia de seguridad.

**[PENDIENTE: crear la imagen y anotar aquí la fecha, el tamaño final y dónde se guarda.]**

### 2.2 Restaurar la imagen en una tarjeta nueva

Usa una microSD **de la misma capacidad o mayor** (64 GB, clase A1/A2, marca conocida).

#### Con Raspberry Pi Imager

1. `rpi-imager` → **"Use custom"** → selecciona tu `.img` o `.img.gz`
2. Elige la microSD destino
3. **Desactiva la personalización del SO** (el engranaje): no debe tocar usuario,
   contraseña ni Wi-Fi, o romperá la configuración existente
4. Escribir y esperar

#### Con `dd`

```bash
# Si esta comprimida:
gunzip -c ~/safevision-robot-2026-09-10.img.gz | \
    sudo dd of=/dev/sdb bs=4M status=progress conv=fsync

# Si no:
sudo dd if=~/safevision-robot-2026-09-10.img of=/dev/sdb \
        bs=4M status=progress conv=fsync

sync
```

> ⚠️ Aquí `of=` **sí** es la tarjeta, y su contenido se destruye. Vuelve a comprobar
> `lsblk`.

### 2.3 Después de restaurar

1. Mete la tarjeta en el robot y enciéndelo. Espera **2 minutos**.
2. Desde la PC:

```bash
ping -c 3 yahboom.local
curl -s http://<IP-del-robot>:8091/health | python3 -m json.tool
```

3. Si la red cambió, reconfigura el Wi-Fi (`docs/red.md` §5).
4. Actualiza el repositorio del robot:

```bash
ssh pi@yahboom.local 'cd ~/robot_custom && git pull'
```

5. Comprueba los servicios:

```bash
ssh pi@yahboom.local 'systemctl is-enabled safevision-roscore safevision-robot-server'
```

Deben decir `enabled` los dos. Si no, ejecuta en el robot:

```bash
cd ~/robot_custom
./misiones/pilotada/systemd/install_services.sh
```

6. Ejecuta el protocolo de `docs/validacion.md`.

---

## 3. Camino B — reconstrucción desde cero

> ⚠️ **NO VALIDADO.** Estos pasos se derivan de inspeccionar el robot funcionando, no de
> haber reconstruido uno. Están **incompletos por definición**: no se pudo capturar el
> contenido de `/etc/udev/rules.d/` ni el procedimiento exacto con que se compiló
> `/usr/local/bin/python3`. Úsalo sólo si no hay imagen, y cuenta con resolver
> imprevistos.

### 3.1 Sistema base

Ubuntu **18.04.6 LTS para Raspberry Pi, 64 bits (`arm64`)**.

> No sirve Raspberry Pi OS, ni Ubuntu 20.04 o posterior: **ROS Melodic sólo tiene paquetes
> oficiales para Bionic**. Cambiar de base obliga a compilar los 451 paquetes.

Tras el primer arranque: usuario `pi`, nombre de equipo `yahboom`, SSH habilitado.

> 🔒 **Pon una contraseña nueva y fuerte.** La contraseña histórica de este robot está
> publicada en GitHub (`docs/security-scan.md`, H-1). No la reutilices.

### 3.2 ROS Melodic

```bash
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" \
    > /etc/apt/sources.list.d/ros-latest.list'
sudo apt install -y curl
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install -y ros-melodic-desktop-full
echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc
```

Los 451 paquetes exactos, con versión, están en `docs/anexo-ros-melodic.txt`. Para
instalarlos todos:

```bash
# En el robot, con anexo-ros-melodic.txt disponible:
awk '{print $1}' anexo-ros-melodic.txt | xargs sudo apt install -y
```

Los que SafeVision necesita sí o sí:

```bash
sudo apt install -y \
  ros-melodic-amcl ros-melodic-move-base ros-melodic-dwa-local-planner \
  ros-melodic-map-server ros-melodic-gmapping ros-melodic-robot-localization \
  ros-melodic-imu-filter-madgwick ros-melodic-rplidar-ros ros-melodic-joy \
  ros-melodic-tf ros-melodic-tf2-ros ros-melodic-actionlib \
  ros-melodic-xacro ros-melodic-robot-state-publisher ros-melodic-joint-state-publisher \
  ros-melodic-depthimage-to-laserscan ros-melodic-depth-image-proc
```

### 3.3 Espacios de trabajo catkin

Los tres son **obligatorios**; los servicios hacen `source` de `yahboomcar_ws` y todos
aparecen en `CMAKE_PREFIX_PATH`:

```
~/yahboomcar_ws           yahboomcar_bringup, _ctrl, _nav, _description, _astra, imu_calib…
~/software/library_ws     astra_camera, astra_launch…
~/software/world_canvas
```

`yahboomcar_ws/src` es material del fabricante. Hay una copia en el portátil de desarrollo
en `~/yahboomcar_ws-src`.

```bash
cd ~/yahboomcar_ws && catkin_make
cd ~/software/library_ws && catkin_make
```

**[PENDIENTE: el origen exacto de `library_ws` y `world_canvas` no está documentado.
Preguntar al profesor o recuperarlos de la imagen de la tarjeta.]**

### 3.4 Python 3.7.3 — el paso más delicado

El Robot Server corre bajo `/usr/local/bin/python3`, que es **Python 3.7.3 compilado
aparte**. Ubuntu 18.04 trae 3.6.9, insuficiente.

```bash
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev

cd /usr/src
sudo wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
sudo tar xzf Python-3.7.3.tgz
cd Python-3.7.3
sudo ./configure --enable-optimizations
sudo make -j4
sudo make altinstall      # altinstall: NO sustituye al python3 del sistema
```

**[PENDIENTE: el procedimiento original no está documentado; estos pasos son la
reconstrucción estándar y NO se han verificado contra este robot.]**

Después, los paquetes de `docs/anexo-pip-freeze.txt`:

```bash
/usr/local/bin/python3 -m pip install flask==2.2.5 requests numpy==1.21.6 \
    opencv-python-headless PyYAML==6.0 rospkg==1.3.0 catkin-pkg==0.4.24
```

> **No instales `torch` ni `ultralytics` en el robot.** Están en el robot actual como
> resto de la generación anterior y **el runtime vigente no los usa**: la inferencia YOLO
> corre en la PC (`docs/anexo-dependencias-robot.md` §3.2).

> **Importante — cómo importa `rospy` Python 3.7.** `rospy` sólo existe en el árbol de
> Python 2 (`/opt/ros/melodic/lib/python2.7/dist-packages`). Los servicios lo consiguen
> mediante `PYTHONPATH`. Funciona porque `rospy` es Python puro. **`tf` no funciona bajo
> 3.7** (extensión C de Python 2), y por eso `sf_pose_exporter.py` se ejecuta con
> `/usr/bin/python`. **No "modernices" ese fichero.** Explicación completa en
> `docs/anexo-dependencias-robot.md` §2.

### 3.5 Reglas `udev`

El sistema depende de dos nombres estables:

```
/dev/rplidar   -> ttyUSB0    (LiDAR)
/dev/myserial  -> ttyUSB1    (placa del chasis)
```

Sin ellos, el LiDAR y el driver fallan cuando el USB se enumera en otro orden.

**[PENDIENTE: capturar el contenido de `/etc/udev/rules.d/` del robot actual (requiere
`sudo cat`, no ejecutado en la sesión de sólo lectura) y pegarlo aquí. Es material del
fabricante Yahboom.]**

Para obtener los identificadores y reconstruirlas:

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -E "idVendor|idProduct|serial" | head
```

### 3.6 Repositorio y servicios

```bash
cd ~
git clone https://github.com/ToscanoID007/safevision.git robot_custom
cd robot_custom
./misiones/pilotada/systemd/install_services.sh
sudo systemctl start safevision-roscore safevision-robot-server
```

> La ruta **debe** ser `/home/pi/robot_custom`: las unidades systemd, los `.launch` y
> `sf_runtime_manager.py` la llevan escrita en absoluto.

### 3.7 Verificación

```bash
systemctl is-enabled safevision-roscore safevision-robot-server   # enabled, enabled
curl -s http://127.0.0.1:8091/health | python3 -m json.tool       # ros_master: true
ls -la /dev/rplidar /dev/myserial /dev/video0 /dev/input/js0      # todos presentes
```

Después, el protocolo completo de `docs/validacion.md`.

---

## 4. Los servicios systemd

`misiones/pilotada/systemd/install_services.sh` copia las dos unidades a
`/etc/systemd/system`, recarga systemd y las habilita. Muestra lo que va a hacer y **pide
confirmación**; no arranca nada por su cuenta.

```bash
cd ~/robot_custom
./misiones/pilotada/systemd/install_services.sh
```

Detalle de qué hace cada unidad y en qué orden: `docs/runtime-boot.md` §2.

> **Recuerda:** con los servicios arrancados el robot **todavía no se mueve**. Levantan el
> ROS Master y el Robot Server; el resto (driver, LiDAR, AMCL, `move_base`) se enciende al
> aplicar un perfil. Ver `docs/manual-operacion.md`.

---

## 5. Mantenimiento periódico

| Cada | Tarea |
|---|---|
| Semana | `git pull` en `~/robot_custom` (el robot **nunca** empuja; ver `CLAUDE.md`) |
| Mes | Comprobar espacio: `df -h /`. Purgar `/home/pi/.ros/log` si crece |
| Trimestre | **Regenerar la imagen de la tarjeta** (§2.1) |
| Tras cada cambio de red | Actualizar `scripts/robot.env` en la PC |

Las microSD se desgastan. Una imagen de hace tres meses es mejor que ninguna, pero una de
hace una semana es mucho mejor.

---

## 6. Documentos relacionados

- `docs/anexo-dependencias-robot.md` — manifiesto completo y los tres Python.
- `docs/runtime-boot.md` — cómo arranca el runtime, paso a paso.
- `docs/red.md` — direcciones, puertos y qué no exponer.
- `docs/validacion.md` — el protocolo de pruebas.
- `docs/security-scan.md` — **léelo antes de reinstalar**: hay credenciales que rotar.
