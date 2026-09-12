# Manual de operación

**Para quién es y cuándo leerlo**
Para quien va a usar el robot: estudiantes en prácticas, profesor, o quien haga una demo.
Léelo entero la primera vez. Después ve directo al procedimiento que necesites: cada uno es
independiente y dice sus precondiciones.

---

**Formato de cada procedimiento:** precondiciones → pasos → resultado esperado → si falla.
**Verificado:** los estados y respuestas provienen del robot real (`docs/estado-actual.md`).

---

## 0. Seguridad — antes de nada

> ⚠️ **Este robot pesa varios kilos y se mueve solo. Léelo.**

| Regla | Por qué |
|---|---|
| **Área despejada de 2×2 m como mínimo** | Un objetivo mal puesto lo lanza en línea recta |
| **Alguien con el mando en la mano, siempre** | Es la parada de emergencia más rápida |
| **Nunca sobre una mesa** | El LiDAR **no ve el borde**. Se cae |
| **Cables recogidos** | Se enredan en las ruedas omnidireccionales |
| **Avisa en voz alta antes de iniciar navegación** | Quien esté cerca debe saberlo |
| **Nadie entre el robot y su objetivo** | El LiDAR ve piernas, pero no siempre a tiempo |

### 0.1 Cómo parar el robot, de más rápido a más lento

1. **Soltar el mando** → el *watchdog* lo detiene en **0,5 s**.
2. **Botón del mando** → según la configuración de `yahboom_joy`.
3. **`POST /nav/cancel`** o el botón "Cancelar" del dashboard → aborta la navegación.
4. **Quitar la alimentación** → último recurso; no apaga la Pi limpiamente.

> **Lo que hay que entender del *watchdog*:** el robot **sólo se mueve mientras recibe
> órdenes**. Si el Wi-Fi se corta, si el dashboard se cierra o si sueltas el mando, se para
> solo en medio segundo. Es una propiedad del sistema, no un accidente
> (`sf_cmd_vel_selector.py:121-135`).

### 0.2 Lo que el robot NO ve

El LiDAR barre **un solo plano horizontal a 11 cm del suelo**. No detecta:

- superficies de mesa o repisas por encima de ese plano;
- **escalones, desniveles ni bordes**;
- objetos más bajos que el haz;
- obstáculos colgantes.

La cámara RGB-D está montada, pero **su profundidad no alimenta la navegación**
(`docs/analisis-alcance.md` §4). Planifica las prácticas contando con esto.

---

## 1. Arranque

### 1.1 Encender el robot

**Precondiciones:** batería cargada; robot en el suelo, en área despejada.

**Pasos**
1. Enciende el interruptor del Rosmaster X3.
2. Espera **60-90 segundos**. La Pi arranca, se conecta al Wi-Fi y lanza los servicios.
3. Comprueba desde la PC:

```bash
ping -c 3 yahboom.local
```

**Resultado esperado:** responde.

**Si falla:** `docs/red.md` §6.

### 1.2 Verificar que los servicios subieron

```bash
curl -s http://$(getent ahostsv4 yahboom.local | awk 'NR==1{print $1}'):8091/health \
  | python3 -m json.tool
```

**Resultado esperado:** JSON con `"ros_master": true` y `"camera": true`.

> **`"ok": false` aquí es NORMAL.** Significa que todavía no hay perfil aplicado. No es un
> fallo.

**Si no responde:**

```bash
ssh pi@yahboom.local 'systemctl status safevision-roscore safevision-robot-server'
```

Ambos deben decir `active (running)`. Si no: `docs/solucion-problemas.md` §2.

### 1.3 Arrancar el dashboard

```bash
cd ~/safevision
./scripts/run_dashboard.sh
```

Abre <http://127.0.0.1:5000> y escribe en la casilla la **IP exacta** que el script imprime.

**Resultado esperado:** la interfaz muestra el estado del robot y el vídeo.

**Si falla:** `docs/instalacion-pc.md` §7.

---

## 2. Aplicar un perfil — **el paso que deja el robot operable**

> **Éste es el paso que más se olvida.** Tras arrancar, el robot tiene ROS Master y Robot
> Server, pero **ni driver, ni LiDAR, ni navegación**. No se mueve. Hay que aplicar un
> perfil.

| Perfil | Qué enciende | Cuándo usarlo |
|---|---|---|
| `libre` | driver + IMU/EKF + selector + control | Teleoperación sin mapa |
| `pilotada` | lo anterior + LiDAR + AMCL + `move_base` + cola | **El habitual.** Navegación por puntos |
| `automatica` | idéntico a `pilotada` | Antes de ejecutar misiones |
| `mapear` | — | No se aplica aquí: se entra por la sesión de mapeo |

**Precondiciones:** §1 completo; **área despejada** (se encienden los motores); mapa
existente si el perfil es `pilotada`/`automatica`.

### Pasos — opción A: dashboard

Página **Pilotada** (portada, tarjeta 01): elige el mapa (`HAB2` de referencia) y el control, pulsa **Aplicar**. Tarda hasta dos minutos; el registro de la página muestra cada recurso. Verificado a través del dashboard el 2026-09-13 (prueba final PF.2, 54 s).

### Pasos — opción B: terminal

```bash
R=http://192.168.1.13:8091      # sustituye por tu IP

curl -X POST $R/runtime/profile \
     -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'
```

> ⏱️ **Tarda hasta 2 minutos y no imprime nada mientras trabaja. No lo interrumpas.**
> Enciende y verifica seis subsistemas en cadena.

**Resultado esperado:** `{"ok": true, "message": "Mision Pilotada lista con mapa HAB2.", ...}`
Comprueba:

```bash
curl -s $R/runtime/status | python3 -m json.tool | head -40
```

`profile.requested` = `"pilotada"` y `driver`, `core`, `lidar`, `localization`,
`pose_exporter`, `navigation`, `nav_queue`, `selector` todos en `"active": true`.

**Si falla (`409`):** la respuesta trae `steps[]`, que dice **en qué recurso se detuvo**.
Los fallos frecuentes:

| Se detiene en | Causa habitual | Solución |
|---|---|---|
| `driver` | Placa no enciende, `/dev/myserial` ausente | Revisa alimentación del chasis |
| `core` | La IMU no publica | **No muevas el robot** durante el arranque: calibra el giróscopo |
| `lidar` | LiDAR no gira o mudo | `docs/solucion-problemas.md` §4 |
| `localization` | El mapa no existe | `curl -s $R/maps` para ver los nombres reales |
| `navigation` | `move_base` tardó demasiado | Reintenta; la Pi va justa de CPU |

---

## 2-bis. Gestor de nodos (página *Nodos*)

Desde v1.2 el dashboard tiene una página **Nodos** (portada, tarjeta 07; o `/nodos`) que
muestra cada recurso del gestor de runtime con su estado real, su PID, lo que requiere y lo
que depende de él, y permite **arrancarlo o detenerlo por separado**.

| Acción | Efecto |
|---|---|
| *Arrancar* un recurso | Arranca antes sus requisitos que falten, en el orden del gestor |
| *Detener* un recurso | Detiene antes todo lo que depende de él, en orden inverso |
| Detener `driver` | Apaga el robot entero (todo depende del driver) |
| Detener `mando` | Pasa el control al teclado web; *Arrancar* lo devuelve al mando |

**Precondiciones.** Robot conectado. **Con una sesión de mapeo activa todas las acciones se
deshabilitan**: el mapeo tiene su propio ciclo con *rollback* y se gestiona desde *Mapear*.
`ros_master`, `robot_server`, `camera`, `teclado` y `mapping` son de solo lectura.

**Resultado esperado.** El registro de la página muestra cada paso ejecutado (`✓` o `✗`) y la
fila cambia de color. Arrancar una cadena completa tarda hasta un minuto.

**Si falla.** El mensaje indica el recurso concreto que no arrancó; las causas son las de
la sección 2 (`core`: robot movido durante la calibración; `lidar`: USB; `localization`:
sin mapa activo — aplica antes un perfil con mapa).

> Es la alternativa al menú antiguo `api/gestor_nodos.py` de la terminal del robot, que
> lanzaba *launch* de fábrica con los mismos nombres de nodo y pisaba los de SafeVision.
> **No uses ese menú con SafeVision en marcha.**

## 3. Teleoperación

### 3.1 Con mando

**Precondiciones:** perfil aplicado con `"control":"mando"`; mando encendido y emparejado.

**Pasos**
1. Verifica: `curl -s $R/runtime/status | grep -A3 '"mando"'` → `"active": true`,
   `"connected": true`.
2. Mantén pulsado el gatillo/botón de habilitación (según `yahboom_joy`).
3. Mueve el joystick.

**Resultado esperado:** el robot se mueve; al soltar, se detiene en ≤0,5 s.

**Si falla:**
- `"connected": false` → `/dev/input/js0` no existe: reconecta el receptor USB.
- `"active": false` → `curl -X POST $R/runtime/control -d '{"mode":"mando"}' -H 'Content-Type: application/json'`

### 3.2 Con teclado web

**Precondiciones:** perfil aplicado; control en `teclado`.

```bash
curl -X POST $R/runtime/control -H 'Content-Type: application/json' -d '{"mode":"teclado"}'
```

Luego, desde el dashboard (página de pilotaje) o con peticiones repetidas:

```bash
curl -X POST $R/runtime/keyboard -H 'Content-Type: application/json' \
     -d '{"linear_x":0.15,"linear_y":0.0,"angular_z":0.0}'
```

> **Hay que repetirlo sin parar** (el dashboard lo hace a ~10 Hz). Un `curl` suelto produce
> un empujón de medio segundo. Es intencionado.

> ⚠️ **En modo teclado `/health` dirá siempre `ok: false`.** Espera un nodo
> `/yahboom_keyboard` que en este camino no existe. Usa `/runtime/status`. Handoff §15.

---

## 4. Localización: fijar la pose inicial

> **Sin esto la navegación no funcionará**, aunque todo lo demás esté verde.

**Por qué:** AMCL arranca suponiendo que el robot está en el origen del mapa. Si no lo
está, cree estar en un sitio donde no está, y planificará rutas absurdas.

**Precondiciones:** perfil `pilotada`/`automatica` con mapa; robot parado.

**Pasos**
1. Mira dónde está el robot **físicamente** respecto al mapa.
2. En el dashboard: sobre el mapa, marca la posición y arrastra para indicar la
   orientación.
   O por terminal:

```bash
curl -X POST $R/initialpose -H 'Content-Type: application/json' \
     -d '{"x":0.0,"y":0.0,"yaw":0.0}'      # yaw en RADIANES
```

3. **Teleopera el robot un metro y gíralo un poco.** AMCL converge con movimiento.
4. Comprueba:

```bash
curl -s $R/map_pose | python3 -m json.tool
```

**Resultado esperado:** `"localized": true` y una pose coherente con la realidad.

**Si falla:**
- `"localized": false` → AMCL no corre, o el pose exporter no arrancó. Revisa
  `/runtime/status`.
- Pose que "salta" → pose inicial mal puesta: repite el paso 2 con más cuidado.
- Pose que deriva al moverse → el mapa no corresponde a la sala, o el entorno cambió
  mucho. Vuelve a mapear.

---

## 5. Navegación por puntos

**Precondiciones:** §4 completo con `"localized": true`; **área despejada**; alguien con el
mando.

**Pasos**
1. En el dashboard, marca uno o varios puntos sobre el mapa.
2. Carga la cola (el dashboard lo hace; por terminal):

```bash
curl -X POST $R/nav/queue -H 'Content-Type: application/json' \
     -d '{"map":"HAB2","points":[{"id":"0x001","x":1.0,"y":0.5,"yaw":0.0}]}'
```

3. **Avisa en voz alta.**
4. Inicia:

```bash
curl -X POST $R/nav/start
```

5. Sigue el progreso:

```bash
watch -n 1 "curl -s $R/nav/status | python3 -m json.tool | head -20"
```

**Resultado esperado:** `state` pasa a `running`, el robot se mueve, `completed_count`
sube, y al terminar `state` vuelve a `idle` o `done`.

**Si falla:**

| Síntoma | Causa | Solución |
|---|---|---|
| `/nav/queue` da `409` | Un punto no tiene plan (`make_plan` falló) | El punto está en una pared o zona inalcanzable. Muévelo |
| `state: unavailable` | La cola no corre | Aplica el perfil (§2) |
| No se mueve, sin error | Selector en MANUAL | `nav/start` lo conmuta; comprueba `/runtime/status` |
| Gira sobre sí mismo | *Recovery behavior*: se cree bloqueado | Cancela, revisa obstáculos y la pose |
| Se detiene antes de llegar | Obstáculo en el costmap | Mira el costmap en el dashboard |

**Para cancelar en cualquier momento:**

```bash
curl -X POST $R/nav/cancel
```

---

## 6. Mapeo (SLAM con Gmapping)

**Precondiciones:** perfil `pilotada`/`automatica` **ya aplicado con un mapa existente**
(el sistema necesita saber a dónde volver); mando listo; sala ordenada.

> **El mapeo se hace pilotando el robot a mano.** No es automático.

**Pasos**
1. Coloca el robot en un punto de referencia claro (una esquina).
2. Inicia la sesión:

```bash
curl -X POST $R/mapping/session/start -H 'Content-Type: application/json' \
     -d '{"name":"laboratorio_2026"}'
```

3. Comprueba: `curl -s $R/mapping/session/status | python3 -m json.tool` →
   `"mapping": true`.
4. **Pilota el robot despacio** por todo el recinto:
   - velocidad baja y constante;
   - pega el recorrido a las paredes, luego recorre el centro;
   - **evita giros bruscos**: descuadran el mapa;
   - **cierra bucles**: vuelve a puntos ya visitados.
5. Observa el mapa en vivo en el dashboard (`GET /mapping/map`).
6. Cuando esté completo:

```bash
curl -X POST $R/mapping/session/save
```

**Resultado esperado:** el mapa se guarda como `.yaml` + `.pgm`, Gmapping se cierra y
**el sistema vuelve solo al perfil anterior, ya con el mapa nuevo**.

**Para descartar:** `curl -X POST $R/mapping/session/discard` — vuelve al perfil anterior
con el mapa anterior.

**Si falla:**

| Síntoma | Causa | Solución |
|---|---|---|
| `start` da `409` "requiere Pilotada o Automatica" | No hay perfil con mapa | Aplica primero un perfil (§2) |
| `start` da `409` "requiere recursos activos" | Falta algún recurso | `core.missing` lo dice |
| El mapa sale torcido o duplicado | Giros bruscos, deriva de odometría | Descarta y repite más despacio |
| Paredes gruesas o dobles | Bucles mal cerrados | Descarta y cierra bucles |
| Zonas en blanco | El LiDAR no llegó | Acércate más |

> **Nota de diseño:** este flujo tiene *rollback* en cada escalón. Si algo falla a medias,
> el sistema restaura el estado anterior en vez de quedarse a medio camino
> (`docs/arquitectura.md` §5).

---

## 7. Gestión de mapas

**Precondiciones:** ninguna especial (funciona sin perfil).

| Operación | Terminal |
|---|---|
| Listar | `curl -s $R/maps \| python3 -m json.tool` |
| Ver imagen | navegador: `$R/maps/HAB2/image` |
| Metadatos | `curl -s $R/maps/HAB2/meta \| python3 -m json.tool` |
| Renombrar | `curl -X POST $R/maps/rename -H 'Content-Type: application/json' -d '{"name":"viejo","new_name":"nuevo"}'` |
| Duplicar | igual con `/maps/duplicate` |
| Borrar | `curl -X POST $R/maps/delete -H 'Content-Type: application/json' -d '{"name":"x"}'` |
| Exportar | `curl -O -J $R/maps/HAB2/export` |
| Importar | `curl -X POST -F "file=@mapa.zip" $R/maps/import` |

El editor de mapas del dashboard permite borrar ruido y tapar huecos; guarda copia en
`mapping/maps/.safevision_edit_backup/`.

> ⚠️ **No borres el mapa que está en uso** por el perfil activo. Cambia de perfil primero.

---

## 8. Misiones automáticas

**Precondiciones:** perfil `automatica` aplicado, localización correcta (§4), área
despejada.

**Flujo: escribir → validar → simular → guardar → preparar → ejecutar.**

**Pasos**
1. En el dashboard, página "Programar": define los puntos sobre el mapa (cada uno recibe un
   id `0x001`, `0x002`… y puede tener alias).
2. Escribe el programa en el DSL (`docs/lenguaje-misiones.md`):

```python
ir("cocina")
esperar(3)
ir("pasillo")
orientar(90)
```

3. **Validar** — el editor marca errores de sintaxis, puntos inexistentes y usos
   incorrectos.
4. **Simular** — dibuja el recorrido sobre el mapa sin mover el robot. **Hazlo siempre.**
5. **Guardar** (`POST /missions/save`).
6. **Preparar** (`POST /mission/prepare`) → estado `ready`.
7. **Avisa en voz alta** y ejecuta (`POST /mission/start`).
8. Sigue: `curl -s $R/mission/status | python3 -m json.tool`

**Resultado esperado:** `state` recorre `navigating` / `waiting` / `orienting` y termina en
`done`.

**Para cancelar:** `curl -X POST $R/mission/cancel`

**Si falla:**

| Síntoma | Causa | Solución |
|---|---|---|
| `"Acción todavía no habilitada: girar"` | La misión usa `girar()` o `relocalizar()` | **No están implementadas.** Quítalas |
| `start` da error "no está en estado ready" | Falta `prepare` | Ejecuta el paso 6 |
| Se detiene en el primer punto | Sin plan o mala localización | Revisa §4 |

---

## 9. Gestión de modelos de IA

**Precondiciones:** ninguna (el catálogo vive en el robot; la inferencia, en la PC).

| Operación | Terminal |
|---|---|
| Listar | `curl -s $R/models \| python3 -m json.tool` |
| Importar | `curl -X POST -F "file=@modelo.zip" $R/models/import` |
| Renombrar | `curl -X POST $R/models/mi_modelo/rename -H 'Content-Type: application/json' -d '{"name":"nuevo"}'` |
| Metadatos | `PUT $R/models/<n>/metadata` con `nombre_modelo`, `version`, `clases[]` |
| Exportar | `curl -O -J $R/models/yolov/export` |
| Borrar | `curl -X DELETE $R/models/yolov` |

El `.zip` debe contener los pesos (`.pt` o `.torchscript`) y un `.json` con
`nombre_modelo`, `version` y `clases`.

> La detección **no influye en la navegación**: YOLO dibuja, no frena
> (`docs/arquitectura.md` §3).

---

## 10. Apagado seguro

> ⚠️ **No cortes la alimentación sin apagar el sistema.** Se corrompe la microSD.

**Pasos**
1. Cancela lo que esté en marcha:

```bash
curl -X POST $R/nav/cancel
curl -X POST $R/mission/cancel
```

2. Si hay una sesión de mapeo abierta, **guárdala o descártala** (§6). No dejes Gmapping
   abierto.
3. Deja el robot en reposo:

```bash
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' -d '{"profile":"libre"}'
```

4. Cierra el dashboard en la PC: `Ctrl+C`.
5. Apaga la Raspberry Pi limpiamente:

```bash
ssh pi@yahboom.local 'sudo shutdown -h now'
```

6. Espera a que se apaguen los LED de actividad (~15 s) y **entonces** corta el
   interruptor.

---

## 11. Referencia rápida

```bash
R=http://192.168.1.13:8091   # ajusta la IP

curl -s $R/health           | python3 -m json.tool   # salud
curl -s $R/runtime/status   | python3 -m json.tool   # estado real
curl -s $R/map_pose         | python3 -m json.tool   # ¿dónde está?
curl -s $R/nav/status       | python3 -m json.tool   # navegación
curl -s $R/mission/status   | python3 -m json.tool   # misión

# Dejar operable
curl -X POST $R/runtime/profile -H 'Content-Type: application/json' \
     -d '{"profile":"pilotada","map":"HAB2","control":"mando"}'

# PARAR
curl -X POST $R/nav/cancel
```

---

## 12. Documentos relacionados

- `docs/api-robot-server.md` — todos los endpoints.
- `docs/solucion-problemas.md` — síntoma → causa → solución.
- `docs/lenguaje-misiones.md` — el DSL.
- `docs/validacion.md` — protocolo formal de pruebas.
- `docs/practicas/` — prácticas de laboratorio.
