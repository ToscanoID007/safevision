#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Informe final de Servicio Social del EQUIPO (Luis Adrian Flores Bueno y Andros
Jair Toscano Farias), con la estructura de la guia del ITC (Art. 44-45) y el
diseno del documento de referencia 'Diseno Mecanico Entrega Final.docx':
encabezado y pie institucionales (plantilla_itc.docx), titulos en negrita
cursiva, tablas con cabecera azul oscuro y cuerpo azul claro, tabla de
ilustraciones con miniaturas y pies 'Fig N.'.

    python3 generar_informe_equipo.py [paginas.json]

Requiere python-docx y Pillow. Las paginas del indice y de la tabla de
ilustraciones se calculan con generar_informe_equipo.sh (dos pasadas).
"""
import json
import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
EVID = os.path.join(RAIZ, "docs", "evidencias", "2026-10-03")
IMG = os.path.join(RAIZ, "docs", "entrega", "img")
SALIDA_DIR = os.path.join(RAIZ, "docs", "entrega")
HOJA_FIRMAS = os.path.join(IMG, "hoja-firmas-itc.png")   # pagina 3 de la guia del ITC, tal cual
PLANTILLA = os.path.join(AQUI, "plantilla_itc.docx")

PROGRAMA = "Desarrollo de plataforma móvil para un sistema de navegación autónoma, Rosmaster X3"
CARRERA = "Ingeniería Mecatrónica"
PERIODO = "Del 2 de marzo al 2 de septiembre de 2026"
RESPONSABLE = "David Díaz Delgado"
CARGO = "Jefe del Departamento de Ingeniería Eléctrica y Electrónica (DIEE)"
FECHA = "Colima, Colima, octubre de 2026"
# El informe es individual (la guia habla del prestante en singular): uno por alumno,
# mismo contenido y diseno. El proyecto se hizo en equipo y el texto lo dice.
ALUMNOS = [
    {"nombre": "Flores Bueno Luis Adrian", "nombre_natural": "Luis Adrian Flores Bueno", "control": "22460736",
     "archivo": "informe-servicio-social-luis-flores"},
    {"nombre": "Toscano Farias Andros Jair", "nombre_natural": "Andros Jair Toscano Farias", "control": "22460548",
     "archivo": "informe-servicio-social-andros-toscano"},
]

AZUL_OSCURO, AZUL_CABECERA, AZUL_CLARO = "073763", "1C4587", "C9DAF8"
GRIS = RGBColor(0x59, 0x59, 0x59)

# ---------------------------------------------------------------- figuras
FIGURAS = {
    "arquitectura": (os.path.join(IMG, "diagrama-1.png"), "Arquitectura del sistema: computadora de control y robot."),
    "obstaculos": (os.path.join(EVID, "05-robot-entre-obstaculos.jpg"), "El robot navegando de forma autónoma entre dos obstáculos."),
    "mapa": (os.path.join(EVID, "01-mapa-casa-luis.png"), "Mapa construido por el robot con SLAM (Gmapping)."),
    "mapear": (os.path.join(EVID, "02-mapear-robot-visible.png"), "Interfaz de mapeo: cámara del robot y mapa en construcción."),
    "pilotada": (os.path.join(IMG, "03-pilotada-pose-calibrada.png"), "Operación pilotada: cámara, mando y robot localizado en el mapa."),
    "ruta": (os.path.join(EVID, "04-cola-tres-puntos.jpg"), "Ruta automática de tres puntos en ejecución."),
    "dashboard": (os.path.join(EVID, "06-obstaculo-y-dashboard.jpg"), "El robot junto al obstáculo y la interfaz de control."),
}
ORDEN_FIG = []  # se llena al construir: [(clave, numero)]

# ---------------------------------------------------------------- contenido
INTRODUCCION = [
    ("h2", "1.1 Significado del servicio social"),
    ("equipo",),
    ("p", "Realizar el servicio social en este programa representó para nosotros pasar de lo aprendido en el "
          "aula a un sistema real que se mueve, falla y tiene que repararse. Durante seis meses trabajamos como "
          "equipo sobre un robot móvil completo: su sistema operativo, sus sensores, el software que lo controla "
          "y la interfaz con la que lo opera una persona. Fue la primera vez que enfrentamos a la vez los tres "
          "problemas que definen a la robótica móvil autónoma: **percibir** el entorno, **saber dónde se está** "
          "y **decidir cómo moverse**."),
    ("p", "El aprendizaje más valioso no fue solo técnico sino de método. Un robot no perdona las suposiciones: "
          "cada afirmación sobre su comportamiento la comprobamos en el equipo, y varias resultaron falsas hasta "
          "que se midieron. Aprendimos a diagnosticar con datos, a no cambiar varias cosas a la vez, a documentar "
          "lo que hacíamos para que otra persona pueda continuarlo y a llevar un control de versiones riguroso. "
          "Trabajar en pareja sobre un mismo sistema nos obligó a repartir tareas, revisar el trabajo del otro y "
          "acordar decisiones técnicas."),
    ("p", "Para nuestra formación en Ingeniería Mecatrónica, el servicio integró en un solo proyecto la "
          "electrónica de los sensores, la mecánica de la plataforma omnidireccional, la programación de nodos y "
          "la inteligencia artificial aplicada a la visión. Nos deja la satisfacción de entregar una herramienta "
          "útil para la institución y para los estudiantes que vendrán."),
    ("h2", "1.2 Descripción del programa"),
    ("p", "El programa *" + PROGRAMA + "* se desarrolló en el Departamento de Ingeniería Eléctrica y Electrónica "
          "(DIEE) del Instituto Tecnológico de Colima, bajo la supervisión de su jefe de departamento, "
          + RESPONSABLE + ". Su objetivo es convertir la plataforma robótica Yahboom ROSMASTER X3 en un sistema de "
          "navegación autónoma completamente operativo, capaz de construir mapas de su entorno, localizarse en "
          "ellos, planificar trayectorias y evitar obstáculos."),
    ("p", "El servicio que ofrece el programa es doble. Por un lado, una **plataforma experimental para la "
          "docencia**: el robot y su documentación permiten que los estudiantes de la especialidad en Sistemas "
          "Mecatrónicos Inteligentes realicen prácticas reales de la asignatura de Percepción e Inteligencia "
          "Artificial, en lugar de limitarse a la simulación. Por otro, un **prototipo de robot de patrullaje** "
          "que puede recorrer rutas automáticas o ser pilotado a distancia, como apoyo a la supervisión de las "
          "instalaciones y del equipo del departamento."),
    ("p", "Los beneficiarios directos son los estudiantes de Ingeniería Mecatrónica, en particular los de "
          "séptimo semestre en adelante que cursan la especialidad, de entre 20 y 24 años, y los docentes que "
          "imparten las asignaturas relacionadas. El personal del departamento es beneficiario indirecto, por el "
          "apoyo a la supervisión."),
    ("p", "Los controles administrativos del programa son los del servicio social del Instituto: carta de "
          "presentación y carta de aceptación al inicio, plan de trabajo con objetivos y cronograma (la propuesta "
          "del proyecto), reportes bimestrales de actividades durante los seis meses, carta de término y este "
          "informe final. Están orientados a los prestadores de servicio social, estudiantes de Ingeniería "
          "Mecatrónica, y a su responsable de programa en el DIEE. Como control técnico, todo el trabajo quedó "
          "registrado en un repositorio Git, con la fecha y la descripción de cada cambio, y los resultados de "
          "las pruebas en un protocolo de validación."),
    ("h2", "1.3 Antecedentes"),
    ("p", "El departamento contaba con la plataforma ROSMASTER X3, pero no con un sistema de navegación "
          "autónoma operativo y documentado. Sin él, los estudiantes no podían desarrollar competencias prácticas "
          "en estimación de pose, construcción de mapas, planificación de trayectorias y evasión de obstáculos. "
          "El robot dependía, además, del conocimiento de quien lo había configurado: no existían manuales de "
          "instalación ni de operación, ni un procedimiento para recuperarlo en caso de falla. El programa se "
          "planteó para resolver esas tres carencias: funcionamiento, documentación y reproducibilidad."),
]

DESARROLLO = [
    ("h2", "2.1 Objetivo general"),
    ("p", "Desarrollar e implementar un sistema de navegación autónoma para la plataforma móvil ROSMASTER X3 "
          "mediante la integración de sensores LiDAR y cámara RGB-D utilizando el middleware ROS, con la "
          "finalidad de generar un prototipo funcional para prácticas académicas en la asignatura de Percepción "
          "e Inteligencia Artificial."),
    ("h2", "2.2 Objetivos específicos"),
    ("numerada", [
        "Integrar los sensores LiDAR y cámara RGB-D a la plataforma ROSMASTER X3.",
        "Configurar el entorno de desarrollo bajo ROS.",
        "Implementar algoritmos de percepción del entorno.",
        "Desarrollar un sistema de mapeo mediante técnicas SLAM.",
        "Implementar algoritmos de localización del robot.",
        "Diseñar e implementar algoritmos de planificación de trayectorias.",
        "Desarrollar estrategias de evasión de obstáculos.",
        "Validar el sistema en entornos estructurados.",
        "Documentar la arquitectura del sistema.",
        "Elaborar manuales de uso para prácticas de laboratorio.",
    ]),
    ("h2", "2.3 Actividades realizadas, en orden cronológico"),
    ("p", "El trabajo se organizó en seis etapas: análisis y configuración, integración sensorial, percepción y "
          "mapeo, localización y navegación, validación experimental y documentación. La tabla resume las "
          "actividades de cada mes; a continuación se describen con detalle."),
    ("tabla", ["Mes", "Actividades principales"], [
        ["Marzo", "Revisión del estado actual del robot. Instalación del sistema operativo."],
        ["Abril", "Instalación de ROS. Integración de la cámara RGB."],
        ["Mayo", "Consolidación de ROS y de la cámara; preparación de la integración del LiDAR."],
        ["Junio", "Integración del LiDAR. Calibración de sensores."],
        ["Julio", "Integración de nodos ROS y SLAM, con su configuración. Generación de mapas."],
        ["Agosto", "Localización, navegación autónoma y evasión de obstáculos; pruebas."],
        ["Septiembre", "Manual técnico, guía de prácticas y reporte final."],
    ], [3.3, 12.2], "Tabla 1. Actividades por mes."),
    ("h3", "Marzo: revisión del estado actual e instalación del sistema operativo"),
    ("p", "Revisamos el estado en que se encontraba la plataforma: chasis, ruedas omnidireccionales (mecanum), "
          "tarjeta controladora de motores, batería, sensores y la computadora a bordo Raspberry Pi 4. "
          "Identificamos los componentes, sus conexiones y lo que funcionaba y lo que no. Con ese diagnóstico "
          "instalamos el sistema operativo **Ubuntu 18.04 LTS de 64 bits** para Raspberry Pi, la base que exige "
          "ROS Melodic, y configuramos el usuario, el nombre de equipo, la red y el acceso remoto por SSH."),
    ("h3", "Abril: instalación de ROS e integración de la cámara RGB"),
    ("p", "Instalamos **ROS Melodic**, el middleware que organiza el robot como un conjunto de procesos "
          "independientes (nodos) que se comunican por tópicos, junto con los espacios de trabajo del fabricante. "
          "Integramos la cámara: su canal de color se publica como vídeo en directo, que más adelante alimentaría "
          "la interfaz de operación y la detección de objetos con inteligencia artificial."),
    ("h3", "Mayo: consolidación de ROS y de la cámara"),
    ("p", "Estabilizamos el entorno ROS y comprobamos el funcionamiento continuo de la cámara y de los nodos "
          "base. Preparamos la integración del sensor láser: reglas del sistema para que cada dispositivo USB "
          "conserve siempre el mismo nombre, y revisión de los controladores."),
    ("h3", "Junio: integración del LiDAR y calibración de sensores"),
    ("p", "Integramos el **LiDAR RPLIDAR A1**, que barre 360° a unos 10 Hz y es el sensor principal para mapear "
          "y evitar obstáculos. Calibramos los sensores de movimiento: la unidad inercial (IMU), cuya calibración "
          "del giróscopo debe hacerse con el robot inmóvil, y la odometría de las ruedas. Ambas se fusionan con un "
          "filtro de Kalman extendido para estimar el movimiento del robot."),
    ("h3", "Julio: integración de nodos, SLAM y generación de mapas"),
    ("p", "Integramos los nodos de control e implementamos el mapeo simultáneo a la localización (**SLAM**) con "
          "el algoritmo **Gmapping**, configurado según las necesidades del proyecto. Desarrollamos la gestión de "
          "sesiones de mapeo con retorno seguro: si algo falla, el sistema vuelve solo al estado anterior. "
          "Generamos los primeros mapas de prueba."),
    ("h3", "Agosto: localización, navegación y evasión de obstáculos"),
    ("p", "Configuramos la localización sobre un mapa conocido (**AMCL**), la planificación de trayectorias "
          "(**move_base** con planificador local **DWA**) y la evasión de obstáculos con mapas de costos. Añadimos "
          "una cola de navegación que valida cada punto antes de mover el robot, y un selector de mando con "
          "*watchdog* que detiene el robot en medio segundo si deja de recibir órdenes. Probamos la teleoperación, "
          "la navegación por puntos y las misiones programadas."),
    ("h3", "Septiembre: manual técnico y reporte final"),
    ("p", "Elaboramos la documentación del proyecto: manual técnico de operación, guías de instalación del robot "
          "y de la computadora, guía de solución de problemas, protocolo de validación de 84 pruebas, guía de seis "
          "prácticas de laboratorio (P01 a P06) y el reporte final. Todo quedó versionado en un repositorio Git, "
          "de modo que el sistema pueda reinstalarse y continuarse."),
    ("p", "El sistema resultante se organiza en dos partes: la computadora de control, donde corren la interfaz "
          "web y la inteligencia artificial, y el robot, donde viven los lazos de control críticos, de modo que el "
          "robot sigue siendo seguro aunque se pierda la conexión."),
    ("fig", "arquitectura", 8),
    ("h2", "2.4 Recursos utilizados"),
    ("p", "El único material empleado fue la plataforma **Yahboom ROSMASTER X3**, con los componentes que integra "
          "de fábrica. El software es libre y se ejecuta sobre Linux."),
    ("tabla", ["Recurso", "Descripción"], [
        ["Plataforma", "Yahboom ROSMASTER X3, chasis con cuatro ruedas mecanum (omnidireccional)"],
        ["Computadora a bordo", "Raspberry Pi 4 con tarjeta microSD de 64 GB"],
        ["Sensor láser", "LiDAR RPLIDAR A1, 360°, ~10 Hz"],
        ["Cámara", "Orbbec Astra Pro (canal RGB en uso; profundidad disponible)"],
        ["Sensores de movimiento", "IMU y encoders de las ruedas"],
        ["Control manual", "Mando inalámbrico incluido con la plataforma"],
        ["Sistema operativo", "Linux: Ubuntu 18.04 LTS en el robot; Ubuntu en la computadora de control"],
        ["Middleware y algoritmos", "ROS Melodic: Gmapping (SLAM), AMCL (localización), move_base y DWA (navegación), robot_localization (EKF)"],
        ["Lenguajes", "Python 3.7 y 2.7 en el robot; Python 3 en la computadora; HTML y JavaScript"],
        ["Interfaz e IA", "Servidor web Flask; detección de objetos con YOLOv8 (Ultralytics)"],
        ["Control de versiones", "Git y GitHub"],
    ], [4.6, 10.9], "Tabla 2. Recursos utilizados."),
]

RESULTADOS = [
    ("p", "El robot cumple su propósito: **construye el mapa de un lugar, se localiza en él, navega de forma "
          "autónoma hasta los puntos indicados y esquiva los obstáculos**, y puede además pilotarse a distancia "
          "desde una computadora. El resultado se validó en un entorno real el 3 de octubre de 2026."),
    ("h2", "3.1 Cumplimiento de los objetivos específicos"),
    ("tabla", ["#", "Objetivo", "Resultado"], [
        ["1", "Integrar LiDAR y cámara RGB-D", "Parcial: LiDAR integrado; de la cámara se usa el canal de color"],
        ["2", "Configurar el entorno ROS", "Cumplido"],
        ["3", "Percepción del entorno", "Cumplido: LiDAR, cámara y detección de objetos con IA"],
        ["4", "Mapeo SLAM", "Cumplido: mapas con Gmapping y retorno seguro ante fallos"],
        ["5", "Localización", "Cumplido: AMCL con calibración de la pose desde la interfaz"],
        ["6", "Planificación de trayectorias", "Cumplido: move_base con planificador DWA"],
        ["7", "Evasión de obstáculos", "Cumplido con el LiDAR 2D; sin aporte de la profundidad"],
        ["8", "Validación en entornos estructurados", "15 pruebas superadas en entorno real"],
        ["9", "Documentar la arquitectura", "Cumplido"],
        ["10", "Manuales para prácticas", "Cumplido: seis prácticas de laboratorio"],
    ], [1.0, 6.3, 8.2], "Tabla 3. Cumplimiento de los objetivos específicos."),
    ("h2", "3.2 Validación en un entorno real"),
    ("p", "La prueba se hizo en una vivienda, que funcionó como entorno estructurado. Se ejecutaron 15 pruebas del "
          "protocolo de validación y todas se superaron:"),
    ("tabla", ["Aspecto", "Resultado medido"], [
        ["Mapa construido", "Unos 173 m² de espacio libre registrado, 25 × 19 m, paredes rectas y sin duplicar"],
        ["Precisión de la navegación", "Llegada al punto destino con 0,08 m de error, igual a la tolerancia configurada"],
        ["Evasión de obstáculos", "El robot rodeó un obstáculo colocado en su trayectoria y llegó al destino"],
        ["Seguridad", "El robot se detiene al soltar el mando; la velocidad máxima es ajustable"],
        ["Ciclo de mapeo", "Inicio, guardado y descarte con restauración automática del estado previo"],
    ], [4.8, 10.7], "Tabla 4. Resultados de la validación."),
    ("p", "La misma sesión permitió detectar y corregir cinco fallos que solo aparecen al operar el robot en "
          "condiciones reales, entre ellos un tiempo de espera insuficiente al iniciar el mapeo, la calibración "
          "del giróscopo con el robot en movimiento y el avance a tirones del mando. Corregirlos dejó el sistema "
          "más robusto."),
    ("fig", "obstaculos", 12.5),
    ("fig", "mapa", 12.5),
    ("fig", "mapear", 14.5),
    ("fig", "pilotada", 14.5),
    ("fig", "ruta", 12.5),
    ("fig", "dashboard", 12.5),
    ("h2", "3.3 Productos entregados"),
    ("lista", [
        "**Plataforma ROSMASTER X3 con navegación autónoma**, operable desde una interfaz web: pilotaje manual, "
        "rutas automáticas, mapeo, cambio de red Wi-Fi y gestión de sus componentes.",
        "**Mapa funcional del entorno**, versionado junto con el sistema.",
        "**Sistema de evasión de obstáculos** basado en LiDAR y mapas de costos.",
        "**Manual técnico de operación**, guías de instalación, red y solución de problemas.",
        "**Guía de prácticas de laboratorio** con seis prácticas, de la teleoperación a la detección de objetos con YOLO.",
        "**Reporte técnico final** y **protocolo de validación**, con evidencias.",
        "Repositorio público con todo lo anterior:",
        "https://github.com/ToscanoID007/safevision",
    ]),
]

CONCLUSIONES = [
    ("p", "El programa dejó al Departamento de Ingeniería Eléctrica y Electrónica un **agente de apoyo a la "
          "seguridad**: un robot de patrullaje capaz de recorrer rutas automáticas sobre un mapa del lugar y de "
          "ser pilotado a distancia cuando se necesita una revisión puntual. Su cámara transmite lo que ve y puede "
          "reconocer objetos con inteligencia artificial, de modo que complementa la supervisión manual del equipo "
          "e instalaciones sin sustituirla. Al estar pensado para operar de forma continua y desde la red local, "
          "amplía la capacidad de vigilancia del personal con un costo de operación prácticamente nulo."),
    ("p", "El segundo impacto es **académico**. La asignatura de Percepción e Inteligencia Artificial cuenta ahora "
          "con una plataforma real, documentada y con seis prácticas listas para el laboratorio. Los estudiantes "
          "podrán construir mapas, localizar el robot, planificar rutas y observar las limitaciones reales de los "
          "sensores, algo que la simulación no enseña. Las limitaciones del sistema, como que el LiDAR solo ve un "
          "plano horizontal, son medibles y por tanto enseñables."),
    ("p", "El tercer impacto es la **continuidad**. Antes, operar el robot dependía del conocimiento de quien lo "
          "había configurado. Ahora existen manuales de instalación, de operación y de diagnóstico, un protocolo "
          "de validación y un repositorio con todo el código y su historia. Otros estudiantes o docentes pueden "
          "reinstalarlo, operarlo y mejorarlo sin empezar de cero."),
    ("p", "Para la comunidad tecnológica, el proyecto muestra que con una sola plataforma comercial y software "
          "libre se puede llegar a un sistema autónomo funcional cuando el trabajo se hace con método: verificar "
          "cada afirmación en el equipo real, cambiar una cosa a la vez y documentar. Como equipo, el servicio "
          "fortaleció nuestras competencias de integración de hardware y software, diagnóstico de fallas y trabajo "
          "colaborativo, y cumplimos con los objetivos y productos comprometidos en la propuesta, con la "
          "integración de la cámara de profundidad como trabajo futuro."),
    ("p", "Por último, el programa demuestra que el servicio social puede generar valor duradero para la "
          "institución cuando se plantea como un proyecto con objetivos claros y productos verificables. El robot, "
          "sus manuales y sus prácticas quedan a disposición del departamento, y la experiencia adquirida queda "
          "registrada para que futuros prestadores partan de un sistema que funciona y no de cero."),
]

RECOMENDACIONES = [
    ("p", "A partir de la experiencia de este programa proponemos las siguientes recomendaciones, dirigidas a la "
          "institución y a quienes den continuidad al proyecto."),
    ("h2", "5.1 Para la institución"),
    ("lista", [
        "**Asignar presupuesto al desarrollo del proyecto.** El programa se realizó solo con la plataforma "
        "existente. Un presupuesto modesto permitiría adquirir una batería de repuesto, tarjetas de memoria de "
        "respaldo, un segundo sensor y un área de pruebas delimitada, y extender el uso del robot a más grupos de "
        "forma simultánea.",
        "**Recibir los documentos del servicio social en formato digital.** La entrega y aceptación de cartas, "
        "reportes e informes en papel consume tiempo y recursos. Un trámite digital, con firma electrónica y "
        "seguimiento en línea, agilizaría el proceso para prestadores y responsables.",
        "**Dar continuidad al programa con nuevos prestadores**, para que el robot siga mejorándose y no quede en "
        "desuso al concluir este periodo.",
    ]),
    ("h2", "5.2 Para la continuidad técnica del proyecto"),
    ("lista", [
        "**Crear y resguardar una imagen de respaldo de la tarjeta microSD del robot.** Hoy es su único punto de "
        "falla: si la tarjeta se daña, reinstalar desde cero llevaría días.",
        "**Integrar la cámara de profundidad en la evasión de obstáculos.** El hardware y el software ya están "
        "instalados; falta conectarlos como segunda fuente del mapa de costos, para detectar mesas, escalones y "
        "objetos que el LiDAR no ve.",
        "**Completar el protocolo de validación** de 84 pruebas y construir el mapa del propio laboratorio, donde "
        "se impartirán las prácticas.",
        "**Mantener una persona responsable del equipo** durante cada sesión y respetar el protocolo de seguridad: "
        "el robot se mueve solo y debe operarse en un área despejada y con el mando a mano.",
        "**Cuidar la batería**: cargarla después de cada uso y apagar el robot de forma ordenada, para no dañar la "
        "tarjeta de memoria.",
    ]),
    ("p", "Atender estas recomendaciones permitirá que el robot se consolide como herramienta permanente de "
          "docencia y de apoyo a la supervisión del departamento."),
]

APARTADOS = [
    ("1. Introducción.", INTRODUCCION),
    ("2. Desarrollo de actividades.", DESARROLLO),
    ("3. Resultados.", RESULTADOS),
    ("4. Conclusiones.", CONCLUSIONES),
    ("5. Recomendaciones.", RECOMENDACIONES),
]


# ---------------------------------------------------------------- utilidades
def fuente(run, tam=12, negrita=None, cursiva=None, color=None):
    run.font.name = "Arial"
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), "Arial")
    run.font.size = Pt(tam)
    if negrita is not None: run.bold = negrita
    if cursiva is not None: run.italic = cursiva
    if color is not None: run.font.color.rgb = color


def texto(par, t, tam=12, negrita=False, cursiva=False, color=None):
    for trozo in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", t):
        if not trozo:
            continue
        if trozo.startswith("**"):
            fuente(par.add_run(trozo[2:-2]), tam, True, cursiva, color)
        elif trozo.startswith("*"):
            fuente(par.add_run(trozo[1:-1]), tam, negrita, True, color)
        else:
            fuente(par.add_run(trozo), tam, negrita, cursiva, color)


def formato(par, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, inter=1.5, antes=0, despues=8):
    par.alignment = alin
    f = par.paragraph_format
    f.line_spacing = inter; f.space_before = Pt(antes); f.space_after = Pt(despues)


def salto(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def sombra(celda, color):
    tcPr = celda._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def titulo(doc, t, nivel):
    par = doc.add_paragraph()
    par.paragraph_format.keep_with_next = True
    tam = {1: 14, 2: 12, 3: 12}[nivel]
    formato(par, WD_ALIGN_PARAGRAPH.LEFT, 1.15, antes=16 if nivel == 1 else 12, despues=8)
    if nivel == 1:
        par.style = doc.styles["Heading 1"]
        par.paragraph_format.left_indent = Cm(0)
    texto(par, t, tam, negrita=True, cursiva=nivel < 3, color=None if nivel < 3 else RGBColor(0x1C, 0x45, 0x87))
    return par


def numeraciones(doc):
    numbering = doc.part.numbering_part.numbering_definitions._numbering
    def abstracto(aid, formato_n, txt):
        a = OxmlElement("w:abstractNum"); a.set(qn("w:abstractNumId"), str(aid))
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
        for tag, val in (("w:start", "1"), ("w:numFmt", formato_n), ("w:lvlText", txt), ("w:lvlJc", "left")):
            e = OxmlElement(tag); e.set(qn("w:val"), val); lvl.append(e)
        pPr = OxmlElement("w:pPr"); ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), "720"); ind.set(qn("w:hanging"), "360"); pPr.append(ind); lvl.append(pPr)
        a.append(lvl)
        primero_num = numbering.find(qn("w:num"))
        if primero_num is not None: primero_num.addprevious(a)
        else: numbering.append(a)
    abstracto(190, "bullet", "●"); abstracto(191, "decimal", "%1.")
    cont = [300]
    def nueva(aid):
        cont[0] += 1
        n = OxmlElement("w:num"); n.set(qn("w:numId"), str(cont[0]))
        a = OxmlElement("w:abstractNumId"); a.set(qn("w:val"), str(aid)); n.append(a)
        numbering.append(n); return cont[0]
    return (lambda: nueva(190)), (lambda: nueva(191))


def numerar(par, nid):
    pPr = par._element.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    il = OxmlElement("w:ilvl"); il.set(qn("w:val"), "0")
    ni = OxmlElement("w:numId"); ni.set(qn("w:val"), str(nid))
    numPr.append(il); numPr.append(ni); pPr.append(numPr)


def tabla(doc, cab, filas, anchos, pie=None, miniaturas=None):
    t = doc.add_table(rows=1, cols=len(cab))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = doc.styles["Table Grid"] if "Table Grid" in [s.name for s in doc.styles] else t.style
    for i, c in enumerate(cab):
        cel = t.rows[0].cells[i]; cel.text = ""
        par = cel.paragraphs[0]; formato(par, WD_ALIGN_PARAGRAPH.LEFT, 1.0, 2, 2)
        texto(par, c, 10.5, negrita=True, cursiva=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        sombra(cel, AZUL_CABECERA); cel.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for k, fila in enumerate(filas):
        celdas = t.add_row().cells
        for i, c in enumerate(fila):
            celdas[i].text = ""
            par = celdas[i].paragraphs[0]
            formato(par, WD_ALIGN_PARAGRAPH.CENTER if miniaturas else WD_ALIGN_PARAGRAPH.LEFT, 1.0, 2, 2)
            texto(par, c, 10.5)
            if miniaturas and i == 0 and miniaturas[k]:
                p2 = celdas[i].add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p2.add_run().add_picture(miniaturas[k], height=Cm(1.6))
            sombra(celdas[i], AZUL_CLARO); celdas[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    t.autofit = False
    for i, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(anchos[i] * 567)))
    for fila in t.rows:
        for i, cel in enumerate(fila.cells):
            cel.width = Cm(anchos[i])
    # bordes oscuros como la referencia
    tblPr = t._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + lado)
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6"); e.set(qn("w:color"), AZUL_OSCURO)
        bordes.append(e)
    tblPr.append(bordes)
    if pie:
        cap = doc.add_paragraph(); formato(cap, WD_ALIGN_PARAGRAPH.CENTER, 1.0, 4, 12)
        texto(cap, pie, 10, cursiva=True)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(4)


def figura(doc, clave, ancho):
    ruta, desc = FIGURAS[clave]
    n = len(ORDEN_FIG) + 1
    ORDEN_FIG.append((clave, n))
    w, h = Image.open(ruta).size
    if ancho * h / w > 10.5:
        ancho = 10.5 * w / h
    par = doc.add_paragraph(); formato(par, WD_ALIGN_PARAGRAPH.CENTER, 1.0, 8, 2)
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(ruta, width=Cm(ancho))
    cap = doc.add_paragraph(); formato(cap, WD_ALIGN_PARAGRAPH.CENTER, 1.0, 2, 12)
    texto(cap, "Fig %d. %s" % (n, desc), 10, cursiva=True)


def linea_indice(doc, t, pagina, sangria=0.0, tam=11):
    par = doc.add_paragraph(); formato(par, WD_ALIGN_PARAGRAPH.LEFT, 1.0, 2 if sangria else 5, 0)
    par.paragraph_format.left_indent = Cm(sangria)
    par.paragraph_format.tab_stops.add_tab_stop(Cm(15.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    texto(par, t, tam, negrita=True, cursiva=True)
    if pagina:
        fuente(par.add_run("\t" + str(pagina)), tam, True, True)


# ---------------------------------------------------------------- documento
def construir(alumno, companero, paginas):
    doc = Document(PLANTILLA)
    from docx.enum.style import WD_STYLE_TYPE
    normal = doc.styles.default(WD_STYLE_TYPE.PARAGRAPH)
    normal.font.name = "Arial"; normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    vinetas, numeradas = numeraciones(doc)
    ORDEN_FIG.clear()

    def centro(t, tam=12, negrita=True, cursiva=False, antes=6, despues=4, alin=WD_ALIGN_PARAGRAPH.CENTER, inter=1.15):
        par = doc.add_paragraph(); formato(par, alin, inter, antes, despues)
        texto(par, t, tam, negrita=negrita, cursiva=cursiva)
        return par

    # A. Caratula (diseno de la referencia + datos que exige la guia)
    centro("Tecnológico Nacional de México", 13, antes=0, despues=0)
    centro("Instituto Tecnológico de Colima", 13, antes=0, despues=10)
    centro("REPORTE FINAL DE SERVICIO SOCIAL", 16, cursiva=True, antes=4, despues=4)
    centro(PROGRAMA, 13, cursiva=True, antes=2, despues=8)
    par = doc.add_paragraph(); formato(par, WD_ALIGN_PARAGRAPH.CENTER, 1.0, 4, 4)
    par.add_run().add_picture(FIGURAS["obstaculos"][0], width=Cm(7.0))
    centro(CARRERA + ".", 12, cursiva=True, antes=4, despues=10)
    centro("Responsable del programa:", 12, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, antes=8, despues=0)
    centro(RESPONSABLE + ", " + CARGO + ".", 12, cursiva=True, alin=WD_ALIGN_PARAGRAPH.LEFT, antes=4, despues=6)
    centro("Alumno:", 12, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, antes=8, despues=0)
    centro(alumno["nombre"] + ".", 12, alin=WD_ALIGN_PARAGRAPH.LEFT, antes=6, despues=0)
    centro("No. de control:", 12, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, antes=8, despues=0)
    centro(alumno["control"] + ".", 12, cursiva=True, alin=WD_ALIGN_PARAGRAPH.LEFT, antes=4, despues=0)
    centro("Periodo del servicio social:", 12, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, antes=12, despues=0)
    centro(PERIODO + ".", 12, cursiva=True, alin=WD_ALIGN_PARAGRAPH.LEFT, antes=4, despues=0)
    centro(FECHA, 12, alin=WD_ALIGN_PARAGRAPH.RIGHT, antes=10, despues=0)
    salto(doc)

    # B. Indice
    titulo(doc, "Índice.", 1)
    linea_indice(doc, "Tabla de ilustraciones.", paginas.get("Tabla de ilustraciones."))
    for t, bloques in APARTADOS:
        linea_indice(doc, t, paginas.get(t))
        for b in bloques:
            if b[0] == "h2":
                linea_indice(doc, b[1], paginas.get(b[1]), sangria=0.9, tam=10.5)
    linea_indice(doc, "Hoja de firmas.", paginas.get("Hoja de firmas."))
    salto(doc)

    # Tabla de ilustraciones (como la referencia, con miniaturas)
    titulo(doc, "Tabla de ilustraciones.", 1)
    claves = []
    for _t, bloques in APARTADOS:
        claves += [b[1] for b in bloques if b[0] == "fig"]
    filas = [["Fig %d." % (i + 1), FIGURAS[c][1], str(paginas.get("Fig %d." % (i + 1), ""))] for i, c in enumerate(claves)]
    tabla(doc, ["Código", "Descripción de la ilustración / figura", "Página"], filas, [4.2, 8.8, 2.5],
          miniaturas=[FIGURAS[c][0] for c in claves])

    # C-G. Apartados
    for t, bloques in APARTADOS:
        salto(doc)
        titulo(doc, t, 1)
        for b in bloques:
            tipo = b[0]
            if tipo == "equipo":
                par = doc.add_paragraph(); formato(par)
                texto(par, "Este informe corresponde a **" + alumno["nombre_natural"] + "**. El programa se realizó "
                      "en equipo con " + companero["nombre_natural"] + ", por lo que las actividades y resultados que "
                      "se describen son el trabajo de ambos prestadores.")
            elif tipo == "p":
                par = doc.add_paragraph(); formato(par); texto(par, b[1])
            elif tipo == "h2":
                titulo(doc, b[1], 2)
            elif tipo == "h3":
                titulo(doc, b[1], 3)
            elif tipo in ("lista", "numerada"):
                nid = vinetas() if tipo == "lista" else numeradas()
                for item in b[1]:
                    par = doc.add_paragraph()
                    formato(par, WD_ALIGN_PARAGRAPH.LEFT if "http" in item else WD_ALIGN_PARAGRAPH.JUSTIFY, 1.5, 0, 4)
                    numerar(par, nid); texto(par, item)
            elif tipo == "tabla":
                tabla(doc, b[1], b[2], b[3], b[4])
            elif tipo == "fig":
                figura(doc, b[1], b[2])

    # H. Hoja de firmas: la de la guia del ITC tal cual (pagina 3), a pagina completa
    from docx.enum.section import WD_SECTION
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    for parte in (sec.header, sec.footer, sec.first_page_header, sec.first_page_footer):
        parte.is_linked_to_previous = False
    sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Cm(0)
    sec.header_distance = sec.footer_distance = Cm(0)
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f = par.paragraph_format; f.space_before = Pt(0); f.space_after = Pt(0); f.line_spacing = 1.0
    par.add_run().add_picture(HOJA_FIRMAS, width=Cm(21.5))
    return doc


def main():
    paginas = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else {}
    for k, alumno in enumerate(ALUMNOS):
        doc = construir(alumno, ALUMNOS[1 - k], paginas)
        ruta = os.path.join(SALIDA_DIR, alumno["archivo"] + ".docx")
        doc.save(ruta)
        print("Escrito", os.path.relpath(ruta, RAIZ), "-", len(ORDEN_FIG), "figuras")
    titulos = ["Tabla de ilustraciones."] + [t for t, _ in APARTADOS]
    titulos_h2 = [b[1] for _t, bl in APARTADOS for b in bl if b[0] == "h2"]
    json.dump({"titulos": titulos, "subtitulos": titulos_h2, "figuras": ["Fig %d." % n for _c, n in ORDEN_FIG],
               "firmas": "Hoja de firmas."}, open(os.path.join(AQUI, "titulos_informe.json"), "w", encoding="utf-8"),
              ensure_ascii=False)


if __name__ == "__main__":
    main()
