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

Estado al cierre de `v2.0-sistema-validado` (2026-09-13). Las decisiones de alcance las tomó
el estudiante prestador; quedan registradas como tales.

### 4.1 Estudiante, con el robot delante

| # | Qué falta | Dónde |
|---|---|---|
| 1 | Ejecutar el protocolo manual de 87 pruebas y rellenar resultados, fecha, responsable y evidencia | `validacion.md` §3-§11 |
| 2 | Datos de la sesión de validación, persona con el mando, palabra de parada | `validacion.md` §1.4, §2 |
| 3 | Definir el error de deriva aceptable (P-7) y la semántica de `orientar()` (S-13) | `validacion.md`, `lenguaje-misiones.md` §3.3 |
| 4 | Construir el mapa del laboratorio (P03) y anotar su nombre | `estado-actual.md` §2.2, `practicas/README.md` §3 |
| 5 | Crear la imagen de respaldo de la microSD y anotar dónde queda | `instalacion-robot.md` §2.1 |
| 6 | Copiar `/etc/udev/rules.d/` y documentar el origen de `library_ws`/`world_canvas` y la compilación de Python 3.7.3 | `instalacion-robot.md` §3 |
| 7 | Configurar la reserva DHCP en el módem | `red.md` §3 |
| 8 | Probar el `.tar.gz` del dashboard en una PC limpia, o retirarlo | `instalacion-pc.md` §9, `scripts/LEEME-empaquetado.md` |
| 9 | Fotografías, capturas, conclusión cuantitativa, referencias, firmas y datos generales del reporte | `reporte-final.md` §1, §8.4, §10, §12, §13 |
| 10 | Nombres, asesor y periodo en los créditos | `README.md` §15 |
| 11 | Anotar el modelo YOLO disponible en P06 | `practicas/P06-yolo-misiones.md` §4 |

### 4.2 Decisiones tomadas

| Decisión | Resultado | Registrado en |
|---|---|---|
| Fusión RGB-D | Opción A, después de la validación con LiDAR solo; trabajo futuro en esta entrega | `analisis-alcance.md` §4.4, `reporte-final.md` §9.5 |
| `girar()` / `relocalizar()` | Retiradas del validador | `lenguaje-misiones.md` §2 |
| Mapas | Sólo `HAB2`; el del laboratorio se construye en P03 | `estado-actual.md` §2.2 |
| Alias del robot | Los 8 de riesgo desactivados (destructivos, conflictivos y menú antiguo) | `estado-actual.md` §6.1 |
| Servicio de perfil por defecto | No | `solucion-problemas.md` §10.2 |
| Reserva DHCP / Tailscale | Reserva sí (pendiente de hacer); Tailscale no | `red.md` §3, §7.1 |
| Dashboard | Versionada la instantánea completa de desarrollo | `estado-actual.md` §5 |
| `SafeVision.spec` | Versionada en `scripts/` | `scripts/LEEME-empaquetado.md` |
| Credenciales expuestas en GitHub (SSH del robot y PSK del Wi-Fi) | **No se rotan ni se purga el historial**, por decisión del estudiante (2026-09-12). Se mantienen tal cual; el análisis queda en `security-scan.md` como referencia | `security-scan.md` §5 |

### 4.3 Trabajo futuro (código, en su propia rama)

| Mejora | Dónde se describe |
|---|---|
| `ros_master_uri` de `/runtime/status` debe informar del valor real del proceso | `red.md` §4-ter.7 |
| Doble restauración de la localización al cerrar el mapeo (gestor de mapeo + gestor de runtime) | `estado-actual.md` §9-quater |
| Conectar la sesión del dashboard desde cualquier página | `solucion-problemas.md` §10.7 |
| Fusión RGB-D, opción A | `analisis-alcance.md` §4.4 |

## 5. Qué NO está en este alcance

Por decisión expresa del profesor responsable: **sin nube, sin contenedores, sin
refactorización**. El plan de refactorización del handoff (§62) queda documentado como
trabajo futuro en [`reporte-final.md`](reporte-final.md) §11.3, y **no debe iniciarse** sin
que se pida.

Lo que conviene **no tocar** antes de la entrega, con su razón, está en
[`analisis-alcance.md`](analisis-alcance.md) §7.
