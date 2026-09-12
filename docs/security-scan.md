# SafeVision / Rosmaster X3 — Barrido de secretos y exposición

**Documento:** `docs/security-scan.md`
**Fecha:** 2026-09-10
**Rama:** `wip-handoff` · **HEAD:** `ee956ad`
**Alcance:** árbol de trabajo completo (incluyendo ficheros no versionados) **e historia
Git completa** (`--all`), 159 ficheros distintos añadidos alguna vez fuera de
`grafo/.venv/`.
**Naturaleza:** informe. **No se eliminó, rotó ni modificó nada.**

---

## 0. Nota sobre redacción de valores

Este documento **no reproduce los valores de los secretos**, aunque estén hoy en el
repositorio: hacerlo los duplicaría en un fichero versionado y los propagaría a cualquier
purga futura de la historia. En su lugar se da **fichero, línea y un prefijo** suficiente
para identificarlos sin ampliarlos. Quien tenga acceso al repositorio puede leerlos en su
sitio; quien no lo tenga, no debería obtenerlos de aquí.

Etiquetas de certeza: las tres del handoff §0 (**CONFIRMADO**, **IMPLEMENTADO EN FUENTE,
PENDIENTE DE REVALIDACIÓN**, **RECOMENDACIÓN**), más **INCONCLUSO** cuando el trazado no
decide.

---

## 1. Veredicto en una línea

**Sí: hay secretos reales en commits que están publicados en GitHub, en la rama por
defecto.** Son dos — una contraseña SSH del robot y una PSK de Wi-Fi doméstica — y ambas
están en el árbol de `origin/master`, no sólo en la historia. **CONFIRMADO.**

---

## 2. Resumen de hallazgos

| # | Hallazgo | Severidad | ¿En el árbol de `HEAD`? | ¿En la historia? | ¿Publicado en GitHub? |
|---|---|---|---|---|---|
| H-1 | Contraseña SSH del robot en claro + `AutoAddPolicy` | **Crítica** | **Sí** (versionado) | Sí | **Sí** (todas las ramas de `origin`) |
| H-2 | PSK de Wi-Fi doméstica en claro (netplan) | **Crítica** | No (ignorado, presente en disco) | Sí | **Sí** (todas las ramas de `origin` salvo `wip-handoff`) |
| H-3 | Copia de H-1 dentro de un `.zip` binario versionado | **Crítica** | No (ignorado, presente en disco) | Sí | **Sí** (ídem H-2) |
| H-4 | PSK de Wi-Fi pasada por línea de órdenes a `nmcli` | Alta | Sí | Sí | Sí |
| H-5 | Inyección de shell con la PSK como entrada del usuario | Alta | Sí | Sí | Sí |
| H-6 | Ausencia total de autenticación en `:8091`, `:5000`, `:8080`, `:5002`, `:8000`, `:8090` | Alta | Sí | Sí | Sí |
| H-7 | `roscore` escuchando en la IP de LAN (`:11311`), sin control de acceso | Alta | Sí | Sí | Sí |
| H-8 | IPs de LAN, nombres de usuario y rutas personales incrustados | Media | Sí | Sí | Sí |
| H-9 | Nombre de usuario de la PC persistido en `api/.pc_config` | Baja | Sí | Sí | Sí |
| H-10 | Entorno virtual completo versionado (`grafo/.venv`, 838 ficheros) | Media | Sí | Sí | Sí |
| H-11 | Correo personal del autor en todos los commits | Informativa | — | Sí | Sí |

**No se encontró** (búsquedas con resultado vacío, ver §6): claves privadas SSH o TLS,
`id_rsa`, `authorized_keys`, `.pem`/`.key` del proyecto, tokens de GitHub (`ghp_`,
`github_pat_`), claves AWS (`AKIA`), claves de Google (`AIza`), tokens de Slack (`xox*`),
cabeceras `Authorization: Bearer`, `client_secret`, ni ficheros `.env`.

---

## 3. Hallazgos en detalle

### 3.1 H-1 — Contraseña SSH del robot en claro, y `AutoAddPolicy` · **CRÍTICA**

**Fichero:** `api/dashboard_pc_src/sf_conexion_ssh.py`
**Estado:** versionado y presente en `HEAD`.

```
:10   self.usuario  = "pi"
:11   self.password = "yah……"        ← contraseña del usuario pi del robot, en claro
:12   self.puerto   = 22
:20   self.cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
:21-27 connect(hostname=…, username=…, password=…)
```

Dos problemas independientes:

1. **Credencial embebida.** Es la contraseña por defecto de fábrica de los equipos
   Yahboom. Cualquiera que haya leído este repositorio tiene acceso `pi@robot` por SSH si
   alcanza la red del robot. **CONFIRMADO.**
2. **`AutoAddPolicy`.** Acepta cualquier clave de host sin verificar, lo que anula la
   protección contra *man-in-the-middle* dentro de la LAN. **CONFIRMADO.**

Esto es exactamente lo que describe el handoff §51 y lo que prohíbe reintroducir
`CLAUDE.md` §6. Lo nuevo que aporta este barrido es que **sigue versionado en `HEAD`**, no
sólo en la historia.

**Superficie de uso.** El fichero es la base del Dashboard SSH antiguo
(`api/dashboard_pc_src/sf_app_dashboard.py:7`) y lanza procesos remotos en el robot
(`:62-83`). Ver `docs/inventory.md` §2.5: está clasificado como
*usado-solo-por-camino-legacy*.

### 3.2 H-2 — PSK de Wi-Fi doméstica en claro · **CRÍTICA**

**Fichero:** `backups/02-wifi.yaml.bak` (copia de un `netplan` de la Pi)
**Estado en `HEAD`:** **no versionado** — eliminado del índice en `391eec2` e ignorado por
`.gitignore:13` (`*.bak`). **Sigue presente en el disco de trabajo.**

```
:8    "INFINITUM…"      ← SSID de la red doméstica
:9    password: "XXJ……" ← PSK WPA en claro
```

**Trazabilidad completa (CONFIRMADO):**

| Evento | Commit | Fecha |
|---|---|---|
| Añadido | `6e9f766` — *"version del codigo del robot casi completa…"* | 2026-08-08 |
| Eliminado del índice | `391eec2` — *"chore: untrack exports and artifacts…"* | (post-tag) |

`git log --all -S'<PSK>'` devuelve exactamente esos dos commits, y ningún otro.

**Punto crítico:** `391eec2` sólo lo quitó de la rama `wip-handoff`. **El fichero sigue en
el árbol de `origin/master` y de las otras 9 ramas remotas** (§4). Quitar un fichero del
índice **no lo borra de la historia ni de las demás ramas**.

### 3.3 H-3 — La misma contraseña SSH, dentro de un `.zip` binario · **CRÍTICA**

**Fichero:** `api/payload/SafeVision_Dashboard.zip` (7.645 bytes)
**Estado en `HEAD`:** no versionado (`.gitignore:10`, `**/payload/`); presente en disco.

Generado por `api/sf_empaquetador.py:33` (`shutil.make_archive` de `api/dashboard_pc_src/`).
Contiene 8 entradas, entre ellas **`sf_conexion_ssh.py` con la contraseña en la línea 11**
(verificado descomprimiendo la copia histórica del tag auditado).

**Por qué importa aparte de H-1:** es un **blob binario**. Los escáneres de secretos
basados en texto y los `grep` sobre el árbol **no lo ven**. Cualquier plan de purga que se
limite a los `.py` lo dejaría atrás.

### 3.4 H-4 y H-5 — Manejo de la PSK de Wi-Fi en tiempo de ejecución · **ALTA**

**H-4 — PSK en la línea de órdenes.** `network/wifi_manager.sh:22`:

```bash
OUTPUT=$(sudo nmcli dev wifi connect "$SSID" password "$PASS" 2>&1)
```

La contraseña queda visible en `/proc/<pid>/cmdline` para cualquier usuario local mientras
dure el proceso, y en los registros de auditoría de `sudo`. **CONFIRMADO.**
**RECOMENDACIÓN:** `nmcli --ask`, o `nmcli connection add` con la clave en un fichero de
permisos `0600`.

**H-5 — Construcción de la orden por concatenación.** `api/wifi.py:88-90`:

```python
password = leer_entrada(" Contraseña para '" + red_elegida + "': ").strip()
res = ejecutar(script_sh + ' connect_new "' + red_elegida + '" "' + password + '"')
```

y `api/utils.py:7-8` ejecuta eso con `subprocess.check_output(comando, shell=True)`. Una
PSK o un SSID que contengan `"` o `` ` `` escapan de las comillas y ejecutan órdenes
arbitrarias **con `sudo`**, porque `wifi_manager.sh` invoca `sudo nmcli`. **CONFIRMADO por
lectura de fuente; IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN** en cuanto a si
`sudo` está configurado sin contraseña en la Pi (no verificable desde aquí).

Además, la PSK queda en el historial de la shell si alguien invoca el script a mano.

### 3.5 H-6 — Ningún servicio HTTP tiene autenticación · **ALTA**

`git grep -E "secret_key|SECRET_KEY|auth|login|Basic "` sobre todo el código del proyecto
(excluyendo `grafo/.venv`) **no devuelve una sola línea de autenticación**. Los servicios
que se exponen son:

| Puerto | Servicio | Bind | Fichero |
|---:|---|---|---|
| 8091 | **Robot Server (vigente)** | `0.0.0.0` | `sf_robot_server.py:124`, `:5047-5053` |
| 5000 | Dashboard vigente | `127.0.0.1` (por diseño) | `misiones/pilotada/dashboard_src/` |
| 5000 | Dashboard SSH legacy | `0.0.0.0` | `api/dashboard_pc_src/sf_app_dashboard.py:90` |
| 5000 | Orquestador CNN PC legacy | `0.0.0.0` | `api/orquestador_ccn_pc.py:233` |
| 8080 | Cámara legacy | `0.0.0.0` | `api/transmisor_camara_pi.py:34` |
| 5002 | Teleoperación web legacy | `0.0.0.0` | `api/sf_teleop_teclado.py:81` |
| 8090 | Descarga de Dashboard (vigente) | `0.0.0.0` | `misiones/pilotada/robot/sf_servidor_descarga.py:9` |
| 8000 | Descarga legacy | `0.0.0.0` | `api/sf_servidor_descarga.py:31` |
| 11311 | ROS Master | IP de LAN | `sf_roscore_service.sh:50` |

El Robot Server en `:8091` acepta sin credencial alguna, entre otros:
`POST /runtime/profile` (arranca y detiene nodos ROS), `POST /runtime/control`,
`POST /runtime/keyboard` (**publica `Twist` en `/cmd_vel_manual`, es decir mueve el
robot**), `POST /nav/start`, `POST /mapping/session/start`, `POST /maps/…/delete`,
`POST /models/…/delete`. **CONFIRMADO.**

Esto confirma el handoff §50 y refuerza `CLAUDE.md` §5: **`8091` y `11311` no deben
exponerse a Internet; el acceso remoto va exclusivamente por Tailscale/VPN.** Con un
`POST` sin autenticar capaz de mover el robot, la frontera de red **es** la frontera de
seguridad.

**Observación adicional (severidad baja, riesgo operativo alto):** `api/lanzador_streaming.py`,
`api/sf_teleop_*.py` y `api/transmisor_camara_pi.py` siguen en el repositorio y siguen
escuchando en `0.0.0.0`. Si alguien los arranca por costumbre junto al runtime vigente,
abren un segundo camino de control del robot **sin pasar por el selector de `cmd_vel` ni
por su watchdog**, lo que viola el principio del handoff §79 (`CLAUDE.md` §4).

### 3.6 H-7 — `roscore` en la IP de LAN · **ALTA**

`sf_roscore_service.sh:7-24` resuelve la IPv4 global de `wlan0` y `:42-43` exporta
`ROS_MASTER_URI=http://<ip-lan>:11311` antes de `exec roscore -p 11311` (`:50`).

ROS 1 **no tiene autenticación ni cifrado**. Cualquiera en la misma red puede registrar
nodos, publicar en `/cmd_vel_manual` o `/cmd_vel_nav`, llamar a
`/safevision/set_navigation_mode` y mover el robot. **CONFIRMADO.**

Es una propiedad de ROS 1, no un defecto del proyecto, pero fija el requisito: **la red
del robot debe tratarse como perímetro de confianza**, y por eso la regla de la VPN no es
negociable.

### 3.7 H-8 — IPs de LAN, usuarios y rutas personales incrustados · **MEDIA**

Direcciones fijas `192.168.1.75` (Pi) y `192.168.1.76` (portátil), usuario `toscano`, y en
`backups/start_hybrid_mapping.sh.old:19-20` una tercera, `192.168.1.69`.

| Fichero | Líneas |
|---|---|
| `auto_mapeo.sh` | `:18` (`scp … toscano@192.168.1.76`), `:33`, `:34` |
| `iniciar_mapeo.sh` | `:9`, `:13`, `:43` (`ssh -t toscano@…`) |
| `mapeo_ligero.sh` | `:8`, `:11`, `:41` |
| `mapeo_denso.sh` | `:8`, `:11`, `:67` |
| `emisor_sensores.sh` | `:7` |
| `api/exportar_codigo.sh` | `:31` |
| `api/gestionar_mapas.py` | `:20` |
| `api/mapas_2d_editar.py` | `:12`, `:43`, `:55` |
| `api/mapas_2d_iniciar.py` | `:10`, `:74` |
| `api/mapas_2d_ver.py` | `:16` |
| `api/navegacion_2d.py` | `:10`, `:20`, `:26` |
| `backups/start_hybrid_mapping.sh.old` | `:19`, `:20` |
| `misiones/pilotada/dashboard_src/templates/index.html` | `:89` (sólo `placeholder`, inocuo) |
| `api/dashboard_pc_src/templates/index.html` | `:21` (sólo `placeholder`, inocuo) |

No son secretos, pero sí **información de la topología de la red doméstica**, y combinados
con la PSK de H-2 y la contraseña de H-1 forman un conjunto utilizable. Son además el
obstáculo técnico de las Fases 4 y 6 (configuración y contenerización). **CONFIRMADO.**

### 3.8 H-9 — `api/.pc_config` · **BAJA**

Fichero de una línea con el nombre de usuario de la PC (`toscano`). Escrito por
`api/mapas_2d_ver.py:19-31` y leído por `api/exportar_codigo.sh:34-40`. No contiene
contraseñas. Se lista porque el enunciado lo pedía explícitamente y porque **su nombre
sugiere que podría contenerlas**: cualquier evolución que le añada credenciales sería un
error, ya que está versionado. **CONFIRMADO: hoy no contiene ningún secreto.**

### 3.9 H-10 — Entorno virtual versionado · **MEDIA**

`grafo/.venv/` está versionado con **838 ficheros** en `HEAD`, añadidos en `75c2eb5`
(2026-08-08). No contiene secretos del proyecto: los dos únicos aciertos de los patrones
de búsqueda son falsos positivos — el paquete de CA de `certifi`
(`pip/_vendor/certifi/cacert.pem`, certificados **públicos**) y la subcadena `sk-` dentro
de la palabra `disk-` en código de Flask y pip. **CONFIRMADO.**

Sigue siendo un problema de higiene y de cadena de suministro: fija versiones de terceros
imposibles de auditar por `requirements.txt` y añade ruido a todo `git grep` (por eso se
excluye en `docs/inventory.md` §0.4). Coincide con el handoff §5.

### 3.10 H-11 — Correo del autor en la historia · **INFORMATIVA**

Todos los commits (`git log --all --format='%ae'`) usan un único correo personal. Es
normal en Git y no es un secreto; se anota sólo porque el repositorio está en GitHub y
`CLAUDE.md` menciona una futura fase cloud con identidad y auditoría.

---

## 4. ¿Hay secretos en commits publicados en GitHub? — **SÍ**

**CONFIRMADO.** Remoto: `origin = git@github.com:ToscanoID007/safevision.git`.

Presencia de cada fichero sensible **en el árbol** de cada rama remota
(`git ls-tree -r --name-only <rama>`):

| Rama remota | `sf_conexion_ssh.py` (H-1) | `02-wifi.yaml.bak` (H-2) | `SafeVision_Dashboard.zip` (H-3) |
|---|:--:|:--:|:--:|
| `origin/master` | ✔ | ✔ | ✔ |
| `origin/release/safevision-v1` | ✔ | ✔ | ✔ |
| `origin/refactor/pilotada-v3` | ✔ | ✔ | ✔ |
| `origin/refactor/pilotada-v2` | ✔ | ✔ | ✔ |
| `origin/refactor/dashboard-v2` | ✔ | ✔ | ✔ |
| `origin/refactor/programacion-v1` | ✔ | ✔ | ✔ |
| `origin/feature/dashboard-mapas-v1` | ✔ | ✔ | ✔ |
| `origin/feature/dwa-frontal-bias-v2` | ✔ | ✔ | ✔ |
| `origin/backup/pilotada-v3-59e04bc` | ✔ | ✔ | ✔ |
| `origin/backup/pilotada-v3-d5444f3` | ✔ | ✔ | ✔ |
| `origin/wip-handoff` | ✔ | — | — |

Y en la **historia alcanzable**: `git branch -a --contains 6e9f766` (el commit que
introdujo la PSK) lista **todas** las ramas de `origin` y de `pi`. Es decir: aunque se
borraran de todos los árboles, los blobs seguirían recuperables desde cualquier clon.

**Consecuencias operativas (CONFIRMADO):**

- La contraseña SSH del robot (H-1) es pública para cualquiera con acceso de lectura al
  repositorio, y está en la rama por defecto.
- La PSK de la red Wi-Fi doméstica (H-2) también, salvo en `wip-handoff`.
- `391eec2` **no mitigó nada** fuera de `wip-handoff`.

**INCONCLUSO:** si el repositorio de GitHub es público o privado, y si hay *forks*,
*mirrors* o clones fuera de control. Requiere abrir la página del repositorio o
`gh repo view --json visibility,forkCount`; este entorno no tiene red. **Esta pregunta
determina la urgencia de todo lo anterior.**

**INCONCLUSO:** si las 42 etiquetas locales (`safevision-v1.0.0`,
`checkpoint-*`, `pre-refactor-baseline`, …) están empujadas a `origin`. Si lo están,
constituyen referencias adicionales que mantienen vivos los blobs aunque se reescriban las
ramas. Se comprueba con `git ls-remote --tags origin`.

---

## 5. Qué haría falta para remediarlo (RECOMENDACIÓN — no ejecutar en esta sesión)

> **Decisión (2026-09-12, estudiante prestador):** no se rota ninguna credencial ni se
> reescribe el historial. Todo se mantiene igual. Esta sección se conserva como análisis
> y como guía por si la decisión cambia. El repositorio es público (comprobado ese día
> con la API de GitHub sin credenciales).

En este orden. Los pasos 1 y 2 son urgentes y **no** requieren tocar el repositorio.

1. **Rotar, antes que borrar.** Un secreto publicado se considera comprometido de forma
   permanente; purgar la historia sin rotar da una falsa sensación de seguridad.
   - Cambiar la contraseña del usuario `pi` en la Raspberry Pi y **pasar a autenticación
     por clave pública**, con `PasswordAuthentication no` en `sshd_config`.
   - Cambiar la PSK del router doméstico.
2. **Confirmar la visibilidad del repositorio en GitHub.** Si es público, el paso 1 pasa a
   ser inmediato. Si es privado, sigue siendo necesario, pero con otro plazo.
3. **Eliminar del árbol vigente** `api/dashboard_pc_src/sf_conexion_ssh.py`, o como mínimo
   sustituir las credenciales por lectura de entorno (`SAFEVISION_SSH_USER` /
   `SAFEVISION_SSH_KEY`) y cambiar `AutoAddPolicy` por `RejectPolicy` con `known_hosts`.
   **Atención:** ese fichero está clasificado como *usado-solo-por-camino-legacy* en
   `docs/inventory.md` §2.5 y sostiene el Dashboard SSH antiguo; su eliminación está
   sujeta a los criterios del handoff §77 y de `CLAUDE.md` §1. **Neutralizar el secreto
   no requiere borrar el fichero**, y esa es la vía recomendada por ahora.
4. **Borrar del disco** `backups/02-wifi.yaml.bak` y `api/payload/SafeVision_Dashboard.zip`
   (ya ignorados, ya sin valor) — después de la rotación, no antes.
5. **Alinear las otras ramas remotas.** `391eec2` sólo limpió `wip-handoff`. Decidir, con
   el autor, si `master` y las ramas `refactor/*`, `feature/*`, `backup/*` y `release/*`
   siguen siendo necesarias; las que no, borrarlas del remoto reduce la superficie de un
   solo golpe.
6. **Reescribir la historia sólo si el repositorio es público** (`git filter-repo
   --invert-paths --path backups/02-wifi.yaml.bak --path api/payload/`). Es una operación
   destructiva que invalida todos los clones y todas las etiquetas; requiere decisión
   humana explícita y coordinación con el remoto `pi`. **No debe hacerla un agente.**
7. **Añadir un guardarraíl** en la Fase 1: `.gitignore` para `*.bak`, `*.zip` y `payload/`
   ya existe (`.gitignore:10-15`); falta un `pre-commit` con detección de secretos.
8. **Higiene Fase 4:** externalizar IPs, usuarios y rutas (H-8) a configuración, y
   `grafo/.venv` (H-10) a `.gitignore` + `requirements.txt`.

**Nada de lo anterior debe hacerse en el mismo cambio que un refactor** (`CLAUDE.md` §2,
handoff §75): un eje cada vez.

---

## 6. Búsquedas realizadas (para poder reproducirlas)

Sobre el árbol de trabajo, incluyendo ficheros no versionados:

```bash
git grep -n -I -E "password|passwd|contraseña|secret|token|api_key|apikey|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa|PRIVATE KEY"
git grep -n -I -E "192\.168\.|10\.[0-9]+\.|172\.(1[6-9]|2[0-9]|3[01])\."
git grep -n -I -E "secret_key|SECRET_KEY|auth|login|Basic "
grep -rn -E "192\.168\.|toscano@|pi@" --include="*.sh" --include="*.py" .
```

Sobre la historia completa:

```bash
git log --all --oneline -S'<patrón>'                       # por contenido
git log --all --diff-filter=A --name-only --format='' | sort -u   # todo fichero añadido
git branch -a --contains <commit>                          # alcanzabilidad
git ls-tree -r --name-only <rama> | grep <fichero>          # presencia en árbol
```

Patrones probados en la historia y su resultado:

| Patrón | Commits |
|---|---:|
| `AKIA` (AWS) | 0 |
| `ghp_` (GitHub) | 0 |
| `github_pat_` | 0 |
| `xox[baprs]-` (Slack) | 0 |
| `AIza` (Google) | 0 |
| `Authorization: Bearer` | 0 |
| `client_secret` | 0 |
| `BEGIN RSA PRIVATE KEY` | 0 |
| `BEGIN OPENSSH PRIVATE KEY` | 0 |
| `PRIVATE KEY` | 0 |
| `BEGIN CERTIFICATE` | 1 → falso positivo (`certifi/cacert.pem` en `grafo/.venv`) |
| `sk-` | 1 → falso positivo (`disk-` en Flask/pip dentro de `grafo/.venv`) |
| `password = "` | 2 → `6e9f766` (H-1) y `75c2eb5` (falso positivo en `grafo/.venv`) |
| `password: "` | 2 → `6e9f766` y `391eec2` (H-2: alta y baja del mismo fichero) |

Nombres de fichero sensibles buscados entre los 159 ficheros añadidos alguna vez
(`id_rsa`, `*.pem`, `*.key`, `*.p12`, `authorized_keys`, `known_hosts`, `.env`,
`credentials`): **el único acierto es `grafo/.venv/.../certifi/cacert.pem`**, un paquete de
CA públicas. No hay claves privadas en la historia. **CONFIRMADO.**

---

## 7. Preguntas que sólo puede responder una persona

1. **¿El repositorio de GitHub es público o privado?** ¿Tiene *forks* o *mirrors*?
   Determina la urgencia de todo el §5.
2. ¿La contraseña de `pi@` en el robot sigue siendo la que aparece en
   `sf_conexion_ssh.py:11`? ¿Y la PSK del router sigue siendo la de
   `backups/02-wifi.yaml.bak:9`?
3. ¿Están las etiquetas locales empujadas a `origin` (`git ls-remote --tags origin`)?
4. ¿Siguen siendo necesarias las 10 ramas remotas antiguas, o pueden eliminarse?
5. ¿Está `sudo` configurado sin contraseña en la Pi? Decide la gravedad real de H-5.
6. ¿Está `:8091` accesible desde fuera de la LAN — reenvío de puertos en el router, UPnP,
   Tailscale con ACL abierta? (`CLAUDE.md` §5 lo prohíbe; conviene verificarlo, no
   suponerlo.)
7. ¿Se sigue usando el Dashboard SSH antiguo (`api/dashboard_pc_src/`)? Si no, H-1 puede
   neutralizarse sin coste operativo.
8. ¿Hay copias del `.zip` de H-3 distribuidas a terceros?

---

## 8. Lo que este documento **no** hizo

- No se eliminó, movió ni modificó ningún fichero fuera de `docs/`.
- No se rotó ninguna credencial ni se tocó la historia de Git.
- No se contactó con ningún servicio externo ni se comprobó la visibilidad del repositorio
  en GitHub (sin red en este entorno).
- No se reprodujeron los valores de los secretos; ver §0.
