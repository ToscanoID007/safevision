# Guía de prácticas de laboratorio

**Para quién es y cuándo leerlo**
Para el profesor que planifica el curso y para el estudiante que va a hacer la práctica.
El profesor lo lee entero antes del semestre; el estudiante lee el índice y va a su práctica.

---

**Asignatura:** Percepción e Inteligencia Artificial
**Carrera:** Ingeniería Mecatrónica — Especialidad en Sistemas Mecatrónicos Inteligentes
**Institución:** TecNM — Instituto Tecnológico de Colima
**Plataforma:** Robot móvil SafeVision / ROSMASTER X3

---

## 1. Las seis prácticas

| # | Práctica | Duración | Se apoya en |
|---|---|---|---|
| [P01](P01-arranque-teleoperacion.md) | Arranque, teleoperación y anatomía de un sistema ROS | 2 h | — |
| [P02](P02-percepcion-lidar.md) | Percepción con LiDAR: `/scan` y costmaps | 2 h | P01 |
| [P03](P03-mapeo-slam.md) | Mapeo SLAM con Gmapping | 2-3 h | P01, P02 |
| [P04](P04-localizacion-amcl.md) | Localización con AMCL y pose inicial | 2 h | P03 |
| [P05](P05-navegacion-autonoma.md) | Navegación autónoma y evasión de obstáculos | 2-3 h | P04 |
| [P06](P06-yolo-misiones.md) | Detección con YOLO y misiones programadas | 3 h | P05 |

**Son acumulativas.** P03 necesita el mapa que no existe si no se hizo P02; P05 necesita la
localización de P04. Conviene respetar el orden.

## 2. Qué necesita el estudiante

**Imprescindible:**
- PC con el dashboard instalado (`docs/instalacion-pc.md`)
- Robot encendido y en la misma red (`docs/red.md`)
- El `docs/manual-operacion.md` a mano

**Opcional pero recomendable a partir de P02:**
- Acceso SSH al robot, para ver los tópicos ROS de verdad

Todas las prácticas se pueden completar **sólo con el dashboard**. Los apartados que
requieren SSH están marcados como *ampliación* y pueden omitirse.

## 3. Antes de la primera sesión — para el profesor

| # | Preparación |
|---|---|
| 1 | Verificar que el robot arranca y responde (`docs/validacion.md` §3) |
| 2 | Tener **un mapa de referencia bueno** del laboratorio, ya construido |
| 3 | Tener **un modelo YOLO** cargado y probado (para P06) |
| 4 | Delimitar el área de pruebas: **2 × 2 m como mínimo**, despejada |
| 5 | Revisar el protocolo de seguridad (§4) con el grupo |
| 6 | Cargar la batería del robot |

**[PENDIENTE: decidir el nombre del mapa de referencia del laboratorio y anotarlo en cada
práctica donde ahora dice `<MAPA>`.]**

## 4. Seguridad — obligatorio en todas las prácticas

> ⚠️ **El robot se mueve solo y pesa varios kilos.**

| Regla | Por qué |
|---|---|
| Área despejada de **2 × 2 m** | Un objetivo mal puesto lo lanza en línea recta |
| **Siempre alguien con el mando** | Es la parada de emergencia más rápida (0,5 s) |
| **Nunca sobre una mesa** | El LiDAR no ve el borde. Se cae |
| Mochilas y cables fuera del área | Se enredan en las ruedas |
| Avisar en voz alta antes de mover | Quien esté cerca debe saberlo |
| Nadie entre el robot y su objetivo | El LiDAR ve piernas, pero no siempre a tiempo |

**Cómo parar, de más rápido a más lento:**
1. Soltar el mando → el *watchdog* lo para en 0,5 s
2. Botón "Cancelar" del dashboard
3. Quitar la alimentación (último recurso)

### 4.1 Lo que el robot NO ve — dilo el primer día

El LiDAR barre **un único plano horizontal a 11 cm del suelo**. No detecta mesas por
encima de esa altura, escalones, objetos bajos ni obstáculos colgantes.

No es un defecto del montaje: es la limitación de un LiDAR 2D, y es justo lo que
**P02 pide comprobar experimentalmente**.

## 5. Formato común

Cada práctica tiene la misma estructura:

1. **Competencia** — qué capacidad desarrolla, en el lenguaje del programa de estudios
2. **Objetivo** — qué se logra al terminar
3. **Marco teórico** — máximo una página
4. **Material**
5. **Seguridad** — lo específico de esa práctica
6. **Procedimiento** — pasos numerados, con resultado esperado
7. **Resultados a reportar** — lo que se entrega
8. **Preguntas de análisis** — 5, para el reporte
9. **Rúbrica** — cómo se califica

## 6. Rúbrica general

Salvo que la práctica indique otra cosa:

| Criterio | Peso | Excelente (100) | Suficiente (70) | Insuficiente (0) |
|---|---:|---|---|---|
| Ejecución | 30 % | Completa el procedimiento sin ayuda | Lo completa con ayuda puntual | No lo completa |
| Evidencias | 20 % | Capturas claras y bien rotuladas | Presentes pero incompletas | Ausentes |
| Análisis | 30 % | Responde con fundamento y relaciona con la teoría | Responde correctamente pero sin profundidad | No responde o es incorrecto |
| Seguridad | 20 % | Cumple el protocolo sin recordatorios | Necesita recordatorios | Pone en riesgo al equipo o a las personas |

> **El criterio de seguridad no se negocia.** Una práctica con un incidente evitable se
> califica como insuficiente en ese criterio, por muy bien que salga lo demás.

## 7. Documentación de apoyo

| Documento | Cuándo consultarlo |
|---|---|
| [`../manual-operacion.md`](../manual-operacion.md) | Procedimientos completos |
| [`../solucion-problemas.md`](../solucion-problemas.md) | **Cuando algo no funciona** |
| [`../arquitectura.md`](../arquitectura.md) | Para entender por qué |
| [`../api-robot-server.md`](../api-robot-server.md) | Para las ampliaciones por terminal |
| [`../lenguaje-misiones.md`](../lenguaje-misiones.md) | P06 |
| [`../red.md`](../red.md) | Cuando la PC no encuentra al robot |

## 8. Nota sobre el estado del sistema

Hay dos cosas que el estudiante encontrará y conviene anticipar:

1. **Tras encender, el robot no se mueve hasta aplicar un perfil.** No es un fallo: es el
   diseño. Se explica en P01 y es una buena oportunidad para hablar de arranque seguro.
2. **`girar()` y `relocalizar()` se aceptan al escribir una misión pero no se ejecutan.**
   Está documentado en P06. Si alguien las usa, el sistema rechaza la misión con un
   mensaje claro.

**[PENDIENTE: revisar estos dos puntos antes de cada semestre; pueden haberse resuelto.]**
