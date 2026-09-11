# SafeVision / Rosmaster X3 — Inventario de `api/` y scripts de primer nivel

**Documento:** `docs/inventory.md`
**Fecha:** 2026-09-10
**Rama:** `wip-handoff` · **HEAD:** `ee956ad`
**Método:** `git ls-files`, `git grep` y lectura de fuentes. Sin ejecución.

---

## 0. Cómo leer este documento

### 0.1 Etiquetas de certeza

Las tres del handoff (`docs/handoff-2026-09.md` §0): **CONFIRMADO**,
**IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN**, **RECOMENDACIÓN**.
Donde el trazado no decide, se escribe **INCONCLUSO** y qué lo resolvería.

### 0.2 Las cuatro clasificaciones pedidas

| Etiqueta | Significado exacto usado aquí |
|---|---|
| **usado-por-runtime-actual** | Alcanzable desde el arranque vigente (unidades systemd → `sf_robot_server.py`), por import, `subprocess`, shell, `.launch` o unidad systemd. |
| **usado-solo-por-camino-legacy** | Alcanzable **sólo** desde `api/main_menu.py` o desde el Dashboard SSH antiguo (`api/dashboard_pc_src/`). Nunca desde el runtime vigente. |
| **herramienta** | Utilidad de desarrollo/operación fuera de banda (exportar código, empaquetar, generar árbol, grafo). No participa del runtime ni del menú. |
| **sin-referencias** | `git grep` no encuentra **ningún** import, `subprocess`, `os.system`, `.launch`, menú, unidad systemd ni cron que lo invoque. |

### 0.2-bis CORRECCIÓN POSTERIOR (2026-09-10, verificada en el robot)

> Este inventario se escribió **antes** de tener acceso al robot. La verificación posterior
> (`docs/estado-actual.md` §6) encontró un invocador que vive **fuera del repositorio** y
> que ninguna búsqueda de `git grep` podía ver: **13 alias en `/home/pi/.bashrc:155-170`**.
>
> La clasificación de este documento sigue siendo correcta *en su alcance declarado*
> ("sin referencias **dentro de este repositorio**"), pero **la conclusión práctica cambia**:
> los siguientes ficheros tienen invocador real y **no pueden borrarse**:
>
> `auto_mapeo.sh` · `mapeo_denso.sh` · `mapeo_ligero.sh` · `emisor_sensores.sh` ·
> `generar_arbol.py` · `api/exportar_codigo.sh` · `api/sf_empaquetador.py` ·
> `api/sf_modo_espera.py` · `api/mapas.py` · `api/mapas_2d_iniciar.py` · `api/main_menu.py`
>
> Siguen sin invocador conocido: `iniciar_mapeo.sh`, `probar_red.py` (raíz),
> `escanear_proyecto.sh`, `api/gestionar_mapas.py`, `api/lanzador_streaming.py`,
> `api/menu_red_ccn.py`, `api/sf_mision_pilotada.py`, `api/sf_servidor_descarga.py`.
>
> **Resultado: ningún fichero de `api/` ni de la raíz cumple los criterios de borrado del
> handoff §77.** Queda además confirmado que ni `systemd` ni `cron` invocan nada de `api/`
> (`estado-actual.md` §6).

### 0.3 Advertencia metodológica (importante)

`sin-referencias` significa **"sin referencias dentro de este repositorio"**. No se pudo
inspeccionar el sistema de ficheros de la Raspberry Pi: `~/safevision-raw/` es una copia
de `robot_custom`, **no** del sistema (no contiene `/etc/systemd/`, `crontab`, `.bashrc`
ni alias de shell). Por tanto:

> **Ningún fichero de este inventario cumple todavía los criterios de borrado del handoff
> §77 / `CLAUDE.md` "Deleting code".** Falta cerrar la comprobación de systemd, cron y
> perfiles de shell **en el robot**. Este documento es la mitad de la evidencia, no la
> evidencia completa.

### 0.4 Búsquedas aplicadas a cada fichero

Para cada módulo `X` se ejecutó `git grep -n -E "\bX\b"` sobre todo el repositorio,
excluyendo `grafo/.venv/` (entorno virtual versionado, ruido puro), `codigo_completo.txt`
y `arbol_direcciones.txt` (exports generados, ver §4), `docs/` y `CLAUDE.md`
(documentación). Adicionalmente:

- `git grep -n "systemctl\|systemd"` → único resultado: `network/wifi_manager.sh:46`.
  **CONFIRMADO: ninguna unidad systemd del repositorio referencia nada de `api/`.**
- `git grep -n "cron"` → sin resultados operativos.
- `git grep -n "<nombre>" -- '*.launch'` → **ningún** `.launch` referencia nada de `api/`.

---

## 1. Mapa de alcanzabilidad de `api/`

```
 [ camino legacy — terminal en la Pi ]

 api/main_menu.py                                      ← punto de entrada legacy
   ├─ utils.py                                (import, main_menu.py:7)
   ├─ safevision.py                           (import, main_menu.py:8)
   │    └─ menu_operacion.py                  (subprocess, safevision.py:43)
   │         ├─ misiones/pilotada/robot/sf_mision_pilotada.py
   │         │    (subprocess, menu_operacion.py:38-41)   ►► cruza a misiones/
   │         │      └─ sf_operacion_pilotada.sh  (bash, sf_mision_pilotada.py:250-260)
   │         └─ sf_mision_automatica.py       (subprocess, menu_operacion.py:43) [NO EXISTE]
   │    └─ menu_planificacion.py / menu_validacion.py (safevision.py:39,41) [NO EXISTEN]
   ├─ redes.py                                (import, main_menu.py:9)
   │    ├─ importar_modelo.py  ├─ ver_modelos.py     ├─ ver_parametros.py
   │    ├─ editar_nombre.py    ├─ editar_metadatos.py ├─ eliminar_modelo.py
   │    ├─ exportar_modelo.py  └─ probar_red.py       (imports, redes.py:5-12)
   │                                 └─ orquestador_ccn_pi.py (probar_red.py:36)
   │                                 │     ├─ nodo_yolo_pi.py   (import, :8)
   │                                 │     └─ servidor_web_pi.py (import, :9)
   │                                 └─ orquestador_ccn_pc.py   (os.system, probar_red.py:43)
   ├─ navegacion.py                           (import, main_menu.py:10)
   ├─ wifi.py                                 (import, main_menu.py:11)
   │    └─ network/wifi_manager.sh            (shell, wifi.py:15)
   ├─ mapas.py                                (import, main_menu.py:12)
   │    ├─ mapas_2d_iniciar.py   (os.system, mapas.py:33)
   │    ├─ mapas_2d_guardar.py   (os.system, mapas.py:41)
   │    ├─ mapas_2d_ver.py       (os.system, mapas.py:49)
   │    │    ├─ visor_mapa.py    (scp+ssh, mapas_2d_ver.py:59,84)
   │    │    └─ .pc_config       (lectura/escritura, mapas_2d_ver.py:11,19-31,173-174)
   │    ├─ mapas_2d_editar.py    (os.system, mapas.py:57)
   │    │    └─ robot_map_editor.py (rsync+ssh, mapas_2d_editar.py:8,43,55)
   │    ├─ navegacion_2d.py      (os.system, mapas.py:65)
   │    └─ mapas_3d_*.py         (mapas.py:73,81,89)  [NO EXISTEN]
   ├─ sistema.py                              (import, main_menu.py:13)
   └─ gestor_nodos.py                         (import, main_menu.py:14)

 [ camino legacy — Dashboard SSH en la PC ]

 api/dashboard_pc_src/sf_app_dashboard.py       ← Flask :5000, arranque manual
   ├─ sf_conexion_ssh.py        (import, sf_app_dashboard.py:7)
   │    ├─ api/sf_teleop_teclado.py     (ssh+python3, sf_conexion_ssh.py:64)
   │    ├─ api/sf_teleop_mando.py       (ssh+python3, sf_conexion_ssh.py:71)
   │    └─ api/transmisor_camara_pi.py  (ssh+python3, sf_conexion_ssh.py:63,70,77)
   ├─ sf_motor_inferencia.py    (import, sf_app_dashboard.py:8)
   ├─ templates/index.html      (render_template, sf_app_dashboard.py:17)
   │    ├─ static/app.js        (url_for, index.html:72)
   │    └─ static/style.css     (url_for, index.html:8)
   └─ api/payload/SafeVision_Dashboard.zip  ← producido por sf_empaquetador.py

 [ sin ningún invocador en el repositorio ]

 api/gestionar_mapas.py      api/lanzador_streaming.py     api/menu_red_ccn.py
 api/sf_empaquetador.py      api/sf_mision_pilotada.py     api/sf_modo_espera.py
 api/sf_servidor_descarga.py api/exportar_codigo.sh        api/main_menu.py (*)

 (*) main_menu.py es el punto de entrada: nada dentro del repo lo invoca,
     por definición. Su invocador vive en la Pi. Ver §5.
```

**Conclusión estructural (CONFIRMADO): ningún fichero de `api/` es importado, lanzado ni
referenciado por el runtime vigente.** El runtime vigente consiste en:

```
safevision-roscore.service      → robot/sf_roscore_service.sh
safevision-robot-server.service → robot/sf_robot_server_service.sh
                                  → robot/sf_robot_server.py
                                      import sf_mapping_manager    (sf_robot_server.py:36)
                                      import sf_model_manager      (sf_robot_server.py:37)
                                      import sf_runtime_manager    (sf_robot_server.py:38)
                                      from sf_mission_executor …   (sf_robot_server.py:55-58)
```

**El único punto de contacto entre `api/` y `misiones/` es `api/menu_operacion.py:38-41`**,
que lanza `misiones/pilotada/robot/sf_mision_pilotada.py`. Ese fichero **no está en
`api/`** y por tanto no aparece en la tabla de abajo, pero su supervivencia depende de esa
línea: ver `docs/runtime-boot.md` §3.1.

---

## 2. Tabla — todos los ficheros de `api/`

47 ficheros versionados (`git ls-files api/`) + 1 artefacto presente en disco pero ya
no versionado (`api/payload/SafeVision_Dashboard.zip`).

### 2.1 Menús y utilidades del árbol legacy

| Fichero | Clasificación | Evidencia (`archivo:línea`) |
|---|---|---|
| `api/main_menu.py` | usado-solo-por-camino-legacy | Punto de entrada. Sin invocador en el repo; sólo comentarios de ejemplo en `grafo/scanner.py:75,77,79,284,295,306,766,768,774,805,807,809,811`. **INCONCLUSO** si la Pi lo arranca (ver §5). Importa 7 módulos: `main_menu.py:7-14`. |
| `api/utils.py` | usado-solo-por-camino-legacy | `api/main_menu.py:7`; `api/navegacion.py:3`; `api/sistema.py:3`; `api/wifi.py:4`; `api/gestor_nodos.py:4`; `api/gestionar_mapas.py:6`; `api/navegacion_2d.py:7`. |
| `api/safevision.py` | usado-solo-por-camino-legacy | `api/main_menu.py:8` (`from safevision import menu_safevision`). |
| `api/menu_operacion.py` | usado-solo-por-camino-legacy | `api/safevision.py:43` (`ejecutar_script("menu_operacion.py")` → `subprocess.run`, `api/safevision.py:16-19`). **Es el puente al camino B del runtime**: `api/menu_operacion.py:38-41`. |
| `api/redes.py` | usado-solo-por-camino-legacy | `api/main_menu.py:9`. Importa 8 módulos: `api/redes.py:5-12`. |
| `api/navegacion.py` | usado-solo-por-camino-legacy | `api/main_menu.py:10`. |
| `api/wifi.py` | usado-solo-por-camino-legacy | `api/main_menu.py:11`. Invoca `network/wifi_manager.sh` en `api/wifi.py:15,24,90`. |
| `api/mapas.py` | usado-solo-por-camino-legacy | `api/main_menu.py:12`. Lanza 5 scripts vía `os.system`: `api/mapas.py:33,41,49,57,65`. |
| `api/sistema.py` | usado-solo-por-camino-legacy | `api/main_menu.py:13`. |
| `api/gestor_nodos.py` | usado-solo-por-camino-legacy | `api/main_menu.py:14`. Lanza `.launch` de `yahboomcar_*` por nombre (`api/gestor_nodos.py:13-70`), no del repositorio. |

### 2.2 Gestión de modelos IA (generación anterior)

Todos escriben/leen `/home/pi/robot_custom/modelos`, el **mismo directorio** que usa el
`sf_model_manager.py` vigente (`sf_model_manager.py:15-16`). Comparten **datos**, no código.

| Fichero | Clasificación | Evidencia |
|---|---|---|
| `api/importar_modelo.py` | usado-solo-por-camino-legacy | `api/redes.py:5`. Dir. destino: `api/importar_modelo.py:17`. |
| `api/ver_modelos.py` | usado-solo-por-camino-legacy | `api/redes.py:6`. |
| `api/ver_parametros.py` | usado-solo-por-camino-legacy | `api/redes.py:7`. |
| `api/editar_nombre.py` | usado-solo-por-camino-legacy | `api/redes.py:8`. |
| `api/editar_metadatos.py` | usado-solo-por-camino-legacy | `api/redes.py:9`. |
| `api/eliminar_modelo.py` | usado-solo-por-camino-legacy | `api/redes.py:10`. |
| `api/exportar_modelo.py` | usado-solo-por-camino-legacy | `api/redes.py:11`. |
| `api/probar_red.py` | usado-solo-por-camino-legacy | `api/redes.py:12`. Lanza `orquestador_ccn_pi` (`api/probar_red.py:36-37`) y `orquestador_ccn_pc.py` (`api/probar_red.py:43`). **Ojo: existe un duplicado en la raíz**, ver §3. |

### 2.3 Cadena de inferencia en la Pi (generación anterior)

| Fichero | Clasificación | Evidencia |
|---|---|---|
| `api/orquestador_ccn_pi.py` | usado-solo-por-camino-legacy | `api/probar_red.py:36-37`; también `api/menu_red_ccn.py:34-35` (pero ese menú está huérfano, ver §2.6). |
| `api/nodo_yolo_pi.py` | usado-solo-por-camino-legacy | `api/orquestador_ccn_pi.py:8,32,33,74,88,93`. |
| `api/servidor_web_pi.py` | usado-solo-por-camino-legacy | `api/orquestador_ccn_pi.py:9,24,41,82,98,104`. |
| `api/orquestador_ccn_pc.py` | usado-solo-por-camino-legacy | `api/probar_red.py:43` (`os.system('python3 …/orquestador_ccn_pc.py')`). Flask en `:5000` (`api/orquestador_ccn_pc.py:233`) — **colisiona con el puerto del Dashboard vigente**. |

### 2.4 Mapas 2D / 3D (generación anterior)

| Fichero | Clasificación | Evidencia |
|---|---|---|
| `api/mapas_2d_iniciar.py` | usado-solo-por-camino-legacy | `api/mapas.py:33`. Abre RViz por SSH en la laptop: `api/mapas_2d_iniciar.py:74`. |
| `api/mapas_2d_guardar.py` | usado-solo-por-camino-legacy | `api/mapas.py:41`. |
| `api/mapas_2d_ver.py` | usado-solo-por-camino-legacy | `api/mapas.py:49`. Copia y ejecuta `visor_mapa.py` en la PC: `api/mapas_2d_ver.py:10,59,84`. |
| `api/mapas_2d_editar.py` | usado-solo-por-camino-legacy | `api/mapas.py:57`. Sincroniza y ejecuta `robot_map_editor.py` en la PC: `api/mapas_2d_editar.py:8,43,55`. |
| `api/navegacion_2d.py` | usado-solo-por-camino-legacy | `api/mapas.py:65`. |
| `api/visor_mapa.py` | usado-solo-por-camino-legacy | `api/mapas_2d_ver.py:10,59,84` (se ejecuta **en la PC**, copiado a `/tmp`); también `api/gestionar_mapas.py:27` (pero ese menú está huérfano). |
| `api/robot_map_editor.py` | usado-solo-por-camino-legacy | `api/mapas_2d_editar.py:8,43,55` (se ejecuta **en la PC**). |
| `api/.pc_config` | usado-solo-por-camino-legacy | Leído/escrito por `api/mapas_2d_ver.py:11,19-31,173-174`; leído por `api/exportar_codigo.sh:6,34-40`. Contenido actual: `toscano`. Es **configuración**, no código; ver `docs/security-scan.md` §3.4. |

### 2.5 Dashboard SSH de la PC (generación anterior)

| Fichero | Clasificación | Evidencia |
|---|---|---|
| `api/dashboard_pc_src/sf_app_dashboard.py` | usado-solo-por-camino-legacy | Sin invocador en el repo (se arranca a mano en la PC; Flask `:5000`, `api/dashboard_pc_src/sf_app_dashboard.py:90`). Es la raíz de su propio subárbol: importa `:7` y `:8`, renderiza `:17`. Se distribuye empaquetado por `api/sf_empaquetador.py:9,33`. |
| `api/dashboard_pc_src/sf_conexion_ssh.py` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_app_dashboard.py:7`. **Contiene credenciales embebidas y `AutoAddPolicy`** (`:10-11`, `:20`) → `docs/security-scan.md` §3.1. |
| `api/dashboard_pc_src/sf_motor_inferencia.py` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_app_dashboard.py:8`. **No confundir** con `misiones/pilotada/dashboard_src/sf_motor_inferencia.py`, que es el vigente (`misiones/pilotada/dashboard_src/sf_app_dashboard.py:30`). Son ficheros distintos con el mismo nombre. |
| `api/dashboard_pc_src/templates/index.html` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_app_dashboard.py:17`. |
| `api/dashboard_pc_src/static/app.js` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/templates/index.html:72`. |
| `api/dashboard_pc_src/static/style.css` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/templates/index.html:8`. |
| `api/sf_teleop_teclado.py` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_conexion_ssh.py:64,69,76,82`. Flask `:5002` (`api/sf_teleop_teclado.py:81`). |
| `api/sf_teleop_mando.py` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_conexion_ssh.py:62,71,76,82`. |
| `api/transmisor_camara_pi.py` | usado-solo-por-camino-legacy | `api/dashboard_pc_src/sf_conexion_ssh.py:63,70,77,82`; también `api/lanzador_streaming.py:17,31` (huérfano). Flask `:8080` (`api/transmisor_camara_pi.py:34`). |

### 2.6 Sin referencias dentro del repositorio

Para cada uno se verificó que **las seis búsquedas vuelven vacías**: import, `subprocess`,
`os.system`/shell, `.launch`, menú y unidad systemd/cron.

| Fichero | Clasificación | Evidencia de ausencia |
|---|---|---|
| `api/gestionar_mapas.py` | sin-referencias | `git grep gestionar_mapas` → sólo `api/gestionar_mapas.py:82` (`def menu_gestionar_mapas`) y `:111` (su propio `__main__`). **Duplicado funcional de `api/mapas_2d_ver.py`**, que sí está enganchado a `api/mapas.py:49`. |
| `api/lanzador_streaming.py` | sin-referencias | `git grep lanzador_streaming` → 0 resultados fuera del propio fichero. Lanza `transmisor_camara_pi.py` (`:17,31`), función que ya cubre `sf_conexion_ssh.py`. |
| `api/menu_red_ccn.py` | sin-referencias | `git grep menu_red_ccn` → 0 resultados. Es una copia anterior de `api/probar_red.py` (compárense `api/menu_red_ccn.py:34-35` y `api/probar_red.py:36-37`). |
| `api/sf_empaquetador.py` | sin-referencias | `git grep sf_empaquetador` → 0 resultados. **herramienta** por naturaleza (empaqueta `dashboard_pc_src` → `api/payload/`), pero sin invocador: se ejecuta a mano. |
| `api/sf_mision_pilotada.py` | sin-referencias | `git grep sf_mision_pilotada` → la única referencia (`api/menu_operacion.py:40`) apunta a la **ruta absoluta de `misiones/`**, no a este fichero. Es la versión anterior, superada por `misiones/pilotada/robot/sf_mision_pilotada.py`. Invoca `sf_servidor_descarga.py` (`:40`) y `sf_modo_espera.py` (`:42`) **de `api/`**. |
| `api/sf_modo_espera.py` | sin-referencias | Sólo lo llama `api/sf_mision_pilotada.py:42`, que a su vez está huérfano. El runtime usa `misiones/pilotada/robot/sf_modo_espera.py` (`sf_operacion_pilotada.sh:523,538`). Fichero distinto. |
| `api/sf_servidor_descarga.py` | sin-referencias | Sólo lo llama `api/sf_mision_pilotada.py:40`, huérfano. El camino vigente usa `misiones/pilotada/robot/sf_servidor_descarga.py` (`misiones/pilotada/robot/sf_mision_pilotada.py:56`). Fichero distinto (puerto `8000` vs `8090`). |
| `api/exportar_codigo.sh` | herramienta · sin-referencias | `git grep exportar_codigo` → 0 resultados. Genera `/tmp/codigo_proyecto.txt` y lo envía por `scp` a la PC (`api/exportar_codigo.sh:17-40`). Ver §4. |
| `api/payload/SafeVision_Dashboard.zip` | herramienta (artefacto) · **ya no versionado** | Salida de `api/sf_empaquetador.py:33`. Eliminado del índice en `391eec2`; ignorado por `.gitignore:10` (`**/payload/`). Sigue en disco. **Contiene el fichero con la contraseña SSH** → `docs/security-scan.md` §3.2. |

**Sub-hallazgo (CONFIRMADO):** existen **cuatro pares de ficheros homónimos** entre `api/`
y `misiones/pilotada/robot/` con contenido distinto: `sf_mision_pilotada.py`,
`sf_modo_espera.py`, `sf_servidor_descarga.py` y (entre `api/dashboard_pc_src/` y
`misiones/pilotada/dashboard_src/`) `sf_app_dashboard.py` y `sf_motor_inferencia.py`.
**RECOMENDACIÓN:** en la Fase 1, cualquier movimiento de directorios debe hacerse
comprobando el par completo; un `git grep` por nombre corto da falsos positivos cruzados.

---

## 3. Tabla — scripts de primer nivel

| Fichero | Clasificación | Evidencia |
|---|---|---|
| `auto_mapeo.sh` | sin-referencias (experimento 3D) | `git grep auto_mapeo` → 0 resultados fuera de `docs/` y `CLAUDE.md`. Graba `datos_3d.bag` y lo envía por `scp` a `toscano@192.168.1.76` (`auto_mapeo.sh:18`). IPs fijas en `:33-34`. |
| `mapeo_denso.sh` | sin-referencias (experimento 3D · RTAB-Map) | `git grep mapeo_denso` → 0 resultados. `killall -9 roslaunch rviz roscore` (`:22`); IPs fijas `:8,11`; abre RViz en la PC por SSH (`:67`). **Peligroso junto al runtime vigente**: el `killall` mataría el `roscore` gestionado por systemd. |
| `mapeo_ligero.sh` | sin-referencias (experimento 2D) | `git grep mapeo_ligero` → 0 resultados. Mismo patrón: `killall -9` y RViz remoto (`:41`), IPs fijas (`:8,11`). |
| `iniciar_mapeo.sh` | sin-referencias (experimento 2D) | `git grep iniciar_mapeo` → 0 resultados. IPs fijas (`:9,13`), RViz remoto por SSH (`:43`). |
| `emisor_sensores.sh` | sin-referencias (experimento) | `git grep emisor_sensores` → 0 resultados. IP fija (`:7`), `killall -9 roslaunch rviz roscore` (`:17`). |
| `probar_red.py` (raíz) | sin-referencias · **duplicado obsoleto** | `git grep probar_red` → el único import (`api/redes.py:12`) resuelve a `api/probar_red.py`, porque `api/redes.py` se importa desde `api/` y ese directorio es el `sys.path[0]`. El de la raíz es una versión **anterior**: sus dos ramas de acción están comentadas (`probar_red.py:43-44,49-50`), mientras la de `api/` sí llama a los orquestadores. CONFIRMADO por `diff probar_red.py api/probar_red.py`. |
| `escanear_proyecto.sh` | herramienta · sin-referencias | `git grep escanear_proyecto` → 0 resultados. Genera `codigo_completo.txt` (`:4,11-16`). Ver §4. |
| `generar_arbol.py` | herramienta · sin-referencias | `git grep generar_arbol` → 0 resultados. Genera `arbol_direcciones.txt` y lo sirve por HTTP (`:9-10`). Ver §4. |

### 3.1 Nota sobre los scripts de mapeo 3D/2D de la raíz

Coinciden con la clasificación "Experimentos 3D" del handoff §73 y con la línea de
`CLAUDE.md`: *"Not integrated. Do not build on them."* Este inventario lo confirma con
evidencia: **ninguno es alcanzable desde ningún menú, servicio o script del repositorio**.

**RECOMENDACIÓN (no ejecutar ahora):** en la Fase 1, moverlos a `experiments/` en vez de
borrarlos. Su valor es documental — registran la configuración de RTAB-Map y de la Astra
que hará falta en la Fase 9 (profundidad).

---

## 4. Exports generados: `codigo_completo.txt` y `arbol_direcciones.txt`

| Fichero | Producido por | Estado |
|---|---|---|
| `codigo_completo.txt` | `escanear_proyecto.sh:4,11-16` | Presente en disco, **destrackeado** en `391eec2`, ignorado por `.gitignore:9`. Sigue versionado en `origin/master`. |
| `arbol_direcciones.txt` | `generar_arbol.py:9-10` | Idem, `.gitignore:8`. |

**CONFIRMADO:** ambos son artefactos regenerables. El handoff §4 ya advertía que el
exportador estaba incompleto; se confirma: `escanear_proyecto.sh:11` sólo recoge `*.py` y
`*.sh`, por lo que **`codigo_completo.txt` no contiene ningún `.launch`, `.yaml`, `.html`,
`.js` ni `.css`** — de ahí que el handoff no pudiera auditar los `.launch` ni el frontend.
`api/exportar_codigo.sh:17` sí incluye `*.yaml` y `*.json`, pero sigue sin `.launch`,
`.html` ni `.js`.

**RECOMENDACIÓN:** no reconstruir estos exports. El repositorio Git ya cumple esa función
y `git grep` es superior. Ambos scripts pertenecen a `tools/` en la Fase 1.

---

## 5. Qué falta para poder borrar algo (handoff §77)

Criterios del handoff §77 / `CLAUDE.md` y su estado tras este inventario:

| Criterio | Estado |
|---|---|
| No importado | ✅ verificable aquí — hecho para los 47 ficheros |
| No ejecutado por `subprocess` | ✅ verificable aquí — hecho |
| No ejecutado por shell | ✅ verificable aquí — hecho |
| No referenciado en `.launch` | ✅ verificable aquí — ningún `.launch` referencia `api/` |
| No usado por un menú | ✅ verificable aquí — hecho (§1) |
| **No usado por systemd/cron** | ❌ **no verificable aquí** — requiere el robot |
| No documentado como fallback | ⚠️ parcial: el handoff §44 sugiere leer `api/main_menu.py`, `api/menu_operacion.py`, `api/redes.py` y `api/mapas.py` como parte de la auditoría; eso los documenta como referencia, no como fallback |
| No requerido por tests | ✅ trivialmente: **no existen tests propios** (handoff §56 confirmado). `git ls-files | grep -iE "test|conftest|pytest"` sólo devuelve ficheros de terceros dentro de `grafo/.venv/`; no hay `tests/`, `pytest.ini` ni `conftest.py` del proyecto |
| Acceptance test pasa antes y después | ❌ no ejecutable aquí (handoff §59 requiere hardware) |

**Comprobaciones pendientes, a ejecutar en la Pi por una persona:**

```bash
# ¿alguna unidad o timer referencia api/ ?
grep -rn "robot_custom" /etc/systemd/system/ /lib/systemd/system/ 2>/dev/null
systemctl list-units --all | grep -i safevision

# ¿cron?
crontab -l; sudo crontab -l; ls -la /etc/cron.d/

# ¿el shell arranca main_menu.py?
grep -rn "robot_custom\|main_menu" ~/.bashrc ~/.profile ~/.bash_profile /etc/rc.local 2>/dev/null

# ¿hay procesos legacy vivos ahora mismo?
pgrep -af "api/"
```

Hasta entonces: **RECOMENDACIÓN — no borrar nada de `api/`.** Lo que sí puede proponerse
(Fase 1, `docs/phase1-plan.md`, aún sin escribir) es **mover sin borrar**: `api/` →
`legacy/`, herramientas → `tools/`, experimentos → `experiments/`, dejando el árbol
vigente intacto y verificando que el acceptance test del handoff §59 pasa antes y después.

---

## 6. Resumen numérico

| Clasificación | Ficheros de `api/` | Scripts de raíz |
|---|---:|---:|
| usado-por-runtime-actual | **0** | **0** |
| usado-solo-por-camino-legacy | 39 | 0 |
| herramienta | 2 (`exportar_codigo.sh`, y `sf_empaquetador.py` por naturaleza) | 2 (`escanear_proyecto.sh`, `generar_arbol.py`) |
| sin-referencias | 9 (incluye las 2 herramientas anteriores, contadas también aquí por carecer de invocador) | 6 |

Desglose exacto de los 9 sin referencias en `api/`: `gestionar_mapas.py`,
`lanzador_streaming.py`, `menu_red_ccn.py`, `sf_empaquetador.py`, `sf_mision_pilotada.py`,
`sf_modo_espera.py`, `sf_servidor_descarga.py`, `exportar_codigo.sh` y
`payload/SafeVision_Dashboard.zip`. De ellos, `sf_empaquetador.py` y `exportar_codigo.sh`
son además **herramientas**; `payload/*.zip` es un **artefacto**.

Los 6 sin referencias de la raíz: `auto_mapeo.sh`, `mapeo_denso.sh`, `mapeo_ligero.sh`,
`iniciar_mapeo.sh`, `emisor_sensores.sh`, `probar_red.py`.

`api/main_menu.py` se cuenta como legacy, no como sin-referencias, porque es la **raíz**
del árbol legacy: que nada lo invoque dentro del repositorio es su condición normal.
**INCONCLUSO** si algo lo invoca en la Pi (§5).
