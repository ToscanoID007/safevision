# Índice de documentación

**Para quién es y cuándo leerlo**
Para cualquiera que abra `docs/` y no sepa por dónde empezar.
Localiza aquí el documento que necesitas; cada uno indica en su cabecera para quién es.

---

## 1. Rutas de lectura

**Si vas a usar el robot por primera vez:**
[`../README.md`](../README.md) → [`instalacion-pc.md`](instalacion-pc.md) →
[`manual-operacion.md`](manual-operacion.md)

**Si algo no funciona:**
[`solucion-problemas.md`](solucion-problemas.md) → [`red.md`](red.md) →
[`estado-actual.md`](estado-actual.md)

**Si vas a dar clase:**
[`practicas/README.md`](practicas/README.md) → las prácticas P01-P06

**Si vas a continuar el desarrollo:**
[`estado-actual.md`](estado-actual.md) → [`arquitectura.md`](arquitectura.md) →
[`analisis-alcance.md`](analisis-alcance.md) → [`handoff-2026-09.md`](handoff-2026-09.md)

**Si vas a evaluar el proyecto:**
[`reporte-final.md`](reporte-final.md) → [`analisis-alcance.md`](analisis-alcance.md) →
[`validacion.md`](validacion.md)

**Si vas a reinstalar el robot:**
[`instalacion-robot.md`](instalacion-robot.md) →
[`anexo-dependencias-robot.md`](anexo-dependencias-robot.md)

---

## 2. Todos los documentos

### Estado verificado del sistema

| Documento | Contenido |
|---|---|
| [`estado-actual.md`](estado-actual.md) | **Qué está realmente instalado y corriendo**, verificado en el robot el 2026-09-10. La foto de la que parte todo lo demás |
| [`anexo-dependencias-robot.md`](anexo-dependencias-robot.md) | Manifiesto de dependencias: SO, ROS, los tres intérpretes de Python y por qué son tres |
| [`anexo-ros-melodic.txt`](anexo-ros-melodic.txt) | Los 451 paquetes `ros-melodic-*` con su versión exacta |
| [`anexo-pip-freeze.txt`](anexo-pip-freeze.txt) | Los 106 paquetes de Python del Robot Server |

### Instalación

| Documento | Contenido |
|---|---|
| [`instalacion-pc.md`](instalacion-pc.md) | De un Ubuntu recién instalado a un dashboard funcionando |
| [`instalacion-robot.md`](instalacion-robot.md) | Restaurar la Raspberry Pi: imagen de la microSD (vía principal) o reconstrucción desde cero |
| [`red.md`](red.md) | Cómo se encuentran PC y robot; puertos; qué **no** exponer |

### Operación

| Documento | Contenido |
|---|---|
| [`manual-operacion.md`](manual-operacion.md) | **Manual técnico de operación.** Cada procedimiento con precondiciones, pasos, resultado esperado y qué hacer si falla |
| [`solucion-problemas.md`](solucion-problemas.md) | Síntoma → causa → solución |
| [`lenguaje-misiones.md`](lenguaje-misiones.md) | Referencia del DSL de misiones |
| [`api-robot-server.md`](api-robot-server.md) | Los 44 endpoints del Robot Server, con ejemplos reales |

### Arquitectura

| Documento | Contenido |
|---|---|
| [`arquitectura.md`](arquitectura.md) | Las tres capas, el grafo ROS, los flujos de datos, puertos e IPC |
| [`runtime-boot.md`](runtime-boot.md) | Cómo arranca el runtime, paso a paso, y por qué hay dos caminos |
| [`inventory.md`](inventory.md) | Inventario de `api/` y los scripts de la raíz, con la evidencia de quién los invoca |

### Docencia

| Documento | Contenido |
|---|---|
| [`practicas/README.md`](practicas/README.md) | Índice de la guía de prácticas |
| [`practicas/P01-arranque-teleoperacion.md`](practicas/P01-arranque-teleoperacion.md) | Arranque, teleoperación y anatomía de ROS |
| [`practicas/P02-percepcion-lidar.md`](practicas/P02-percepcion-lidar.md) | Percepción con LiDAR: `/scan` y costmaps |
| [`practicas/P03-mapeo-slam.md`](practicas/P03-mapeo-slam.md) | Mapeo SLAM con Gmapping |
| [`practicas/P04-localizacion-amcl.md`](practicas/P04-localizacion-amcl.md) | Localización con AMCL y pose inicial |
| [`practicas/P05-navegacion-autonoma.md`](practicas/P05-navegacion-autonoma.md) | Navegación autónoma y evasión |
| [`practicas/P06-yolo-misiones.md`](practicas/P06-yolo-misiones.md) | YOLO y misiones programadas |

### Proyecto y evaluación

| Documento | Contenido |
|---|---|
| [`reporte-final.md`](reporte-final.md) | **Reporte técnico final** |
| [`analisis-alcance.md`](analisis-alcance.md) | Propuesta frente a lo implementado; la brecha RGB-D y tres caminos |
| [`validacion.md`](validacion.md) | Protocolo de 87 pruebas, rellenable |
| [`propuesta-servicio-social.md`](propuesta-servicio-social.md) | La propuesta original |

### Auditoría

| Documento | Contenido |
|---|---|
| [`security-scan.md`](security-scan.md) | ⚠️ **Credenciales expuestas.** Leer antes de publicar o entregar |
| [`handoff-2026-09.md`](handoff-2026-09.md) | Handoff técnico auditado (81 secciones). Línea base, no verdad absoluta |

---

## 3. Convenciones

### 3.1 Etiquetas de certeza

Heredadas del handoff §0. Toda afirmación no trivial sobre el comportamiento del sistema
lleva una:

| Etiqueta | Significa |
|---|---|
| **CONFIRMADO** | Evidencia directa: código citado con fichero y línea, o comprobación en el robot |
| **IMPLEMENTADO EN FUENTE, PENDIENTE DE REVALIDACIÓN** | El código existe y es coherente, pero no se ha probado sobre el hardware |
| **RECOMENDACIÓN** | Sugerencia para quien continúe. No es una decisión adoptada |
| **INCONCLUSO** | El trazado no alcanzó a decidir; se indica qué lo resolvería |

> La distinción entre las dos primeras es la que evita el error más común en proyectos
> heredados: confundir *"existe código"* con *"funciona"*.

### 3.2 Marcas `[PENDIENTE: ...]`

Señalan lo que **sólo puede aportar una persona**: nombres, fechas, fotografías,
mediciones o decisiones. Se localizan con:

```bash
grep -rn "\[PENDIENTE:" docs README.md scripts
```

**No se ha inventado ningún dato para rellenarlas.** Ver §4.

---

## 4. Lo que falta, y quién debe resolverlo

**51 marcas accionables.** Agrupadas por responsable.

### 4.1 Estudiante, con el robot delante (19)

Requieren estar físicamente frente al robot o ejecutar pruebas sobre él.

| # | Qué falta | Dónde |
|---|---|---|
| 1 | **Ejecutar la prueba V-1**: ¿queda el robot operable desde el dashboard? | `estado-actual.md` §8, `validacion.md` §4 |
| 2 | **Ejecutar el protocolo completo de validación** (87 pruebas) | `validacion.md` §3-§11 |
| 3 | Rellenar los datos de la sesión de validación (fecha, lugar, responsables, commit) | `validacion.md` §2 |
| 4 | Anotar quién sostiene el mando y la palabra de parada | `validacion.md` §1.4 |
| 5 | Definir qué error de deriva es "aceptable" — medirlo primero | `validacion.md` P-7 |
| 6 | Determinar la semántica de `orientar()`: ¿absoluto o relativo? ¿grados? ¿sentido? | `validacion.md` S-13, `lenguaje-misiones.md` §3.3 |
| 7 | Redactar la conclusión de la validación | `validacion.md` §12.1 |
| 8 | Listar las evidencias generadas | `validacion.md` §12.2 |
| 9 | **Crear la imagen de respaldo de la microSD** y anotar fecha, tamaño y ubicación | `instalacion-robot.md` §2.1 |
| 10 | Copiar `/etc/udev/rules.d/` del robot (necesita `sudo`) | `instalacion-robot.md` §3.5, `anexo-dependencias-robot.md` §5 |
| 11 | Documentar el origen de `library_ws` y `world_canvas` | `instalacion-robot.md` §3.3 |
| 12 | Verificar el procedimiento de compilación de Python 3.7.3 | `instalacion-robot.md` §3.4 |
| 13 | Probar el `.tar.gz` del dashboard en una PC limpia | `instalacion-pc.md` §9, `estado-actual.md` §7 |
| 14 | Fotografías del robot, el laboratorio y las sesiones | `reporte-final.md` §13.F |
| 15 | Capturas del dashboard, el mapa y el costmap con y sin obstáculo | `reporte-final.md` §8.4 |
| 16 | Trasladar los resultados de la validación al reporte | `reporte-final.md` §8.4 |
| 17 | Añadir la conclusión cuantitativa al reporte | `reporte-final.md` §10 |
| 18 | Completar las referencias bibliográficas consultadas | `reporte-final.md` §12 |
| 19 | Anotar el modelo YOLO disponible y sus clases para P06 | `practicas/P06-yolo-misiones.md` §4 |

### 4.2 Profesor — decisiones (14)

| # | Decisión | Dónde |
|---|---|---|
| 20 | **Qué camino tomar con la fusión RGB-D** (entregar, cerrar opción A, o RTAB-Map) | `analisis-alcance.md` §5, `reporte-final.md` §9.5 |
| 21 | Si se acomete la opción A antes de la entrega o se declara trabajo futuro | `analisis-alcance.md` §4.4 |
| 22 | Si `girar()` y `relocalizar()` se implementan o se retiran del lenguaje | `lenguaje-misiones.md` §2 |
| 23 | Qué mapas conservar de los 6 que hay | `estado-actual.md` §2.2 |
| 24 | Renombrar a `legacy_*` los alias del `.bashrc` que ejecutan `killall -9 roscore` | `estado-actual.md` §6.1, `solucion-problemas.md` §10.1 |
| 25 | Si se crea un servicio que aplique un perfil por defecto al arrancar | `solucion-problemas.md` §10.2 |
| 26 | Si se reserva una IP fija para el robot en el router | `red.md` §3 |
| 27 | Si se instala Tailscale y quién administra la cuenta | `red.md` §7.1 |
| 28 | Nombre del mapa de referencia del laboratorio para las prácticas | `practicas/README.md` §3 |
| 29 | Revisar antes de cada semestre si los dos avisos de las prácticas siguen vigentes | `practicas/README.md` §8 |
| 30 | Nombres de los prestadores y números de control | `README.md`, `reporte-final.md` §1 |
| 31 | Nombre y cargo del asesor responsable | `README.md`, `reporte-final.md` §1 |
| 32 | Fechas de inicio y término del servicio social | `README.md`, `reporte-final.md` §1 |
| 33 | Firmas y fechas del formato institucional del TecNM | `reporte-final.md` §13 |

### 4.3 Acciones que no admiten demora (3)

Independientes del alcance técnico. **No deberían quedar abiertas en la entrega.**

| # | Acción | Dónde |
|---|---|---|
| 34 | 🔒 **Rotar la contraseña SSH del robot y la PSK del Wi-Fi.** Están publicadas en la rama por defecto de GitHub | `security-scan.md` §5, `reporte-final.md` §7.9 |
| 35 | **Versionar el dashboard operativo** de `~/SafeVision_Dashboard_dev/` (tras la prueba V-1) | `estado-actual.md` §5.5, `reporte-final.md` §8.3 |
| 36 | Actualizar los apartados del manual que hoy remiten a `curl` porque el botón no está versionado | `manual-operacion.md` §2, `instalacion-pc.md` §7.4 |

> Las marcas restantes hasta 51 son referencias cruzadas a estas mismas tareas desde otros
> documentos, más la nota metodológica de `reporte-final.md` §0 que explica la convención.

---

## 5. Qué NO está en este alcance

Por decisión expresa del profesor responsable: **sin nube, sin contenedores, sin
refactorización**. El plan de refactorización del handoff (§62) queda documentado como
trabajo futuro en [`reporte-final.md`](reporte-final.md) §11.3, y **no debe iniciarse** sin
que se pida.

Lo que conviene **no tocar** antes de la entrega, con su razón, está en
[`analisis-alcance.md`](analisis-alcance.md) §7.
