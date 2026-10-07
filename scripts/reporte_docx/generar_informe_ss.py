#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Informe final de Servicio Social segun la guia del ITC (Art. 44-45):
caratula, indice, introduccion, desarrollo de actividades, resultados,
conclusiones, recomendaciones y hoja de firmas. Arial, interlineado 1.5,
texto justificado, cada apartado desde pagina nueva.

Genera un informe por prestador (el informe es individual):
    python3 generar_informe_ss.py [paginas.json]

Requiere python-docx y Pillow. El indice lleva numeros de pagina si se pasa el
JSON que calcula generar_informe_ss.sh (dos pasadas con LibreOffice).
"""
import json
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVID = os.path.join(RAIZ, "docs", "evidencias", "2026-10-03")
IMG = os.path.join(RAIZ, "docs", "entrega", "img")
SALIDA = os.path.join(RAIZ, "docs", "entrega")

PROGRAMA = "Desarrollo de un sistema de navegación autónoma para plataforma móvil Rosmaster X3"
CARRERA = "Ingeniería Mecatrónica"
PERIODO = "Del 2 de marzo al 2 de septiembre de 2026"
RESPONSABLE = "David Díaz Delgado"
CARGO_RESPONSABLE = "Jefe del Departamento de Ingeniería Eléctrica y Electrónica (DIEE)"
LUGAR_FECHA = "Colima, Colima, octubre de 2026"

PRESTADORES = [
    {"nombre": "Andros Jair Toscano Farias", "control": "22460548", "archivo": "informe-servicio-social-andros-toscano"},
    {"nombre": "Luis Adrian Flores Bueno", "control": "22460736", "archivo": "informe-servicio-social-luis-flores"},
]

AZUL = RGBColor(0x1F, 0x38, 0x64)
GRIS = RGBColor(0x59, 0x59, 0x59)

# ---------------------------------------------------------------- contenido
# Cada apartado: lista de bloques ("p", texto) | ("h2", texto) | ("lista", [..])
# | ("tabla", cabecera, filas, anchos_cm) | ("fig", ruta, pie, ancho_cm) | ("pb",)
# En el texto, **negrita** e *cursiva*.

def introduccion(p):
    companero = p["companero"]
    return [
        ("h2", "Significado del servicio social"),
        ("p", "Realizar el servicio social en este programa representó pasar de lo aprendido en el aula a "
              "un sistema real que se mueve, falla y tiene que repararse. Durante seis meses, junto con mi "
              "compañero " + companero + ", trabajé sobre un robot móvil completo: su sistema operativo, sus "
              "sensores, el software que lo controla y la interfaz con la que lo opera una persona. Fue la "
              "primera vez que enfrenté a la vez los tres problemas que definen a la robótica móvil "
              "autónoma: **percibir** el entorno, **saber dónde se está** y **decidir cómo moverse**."),
        ("p", "El aprendizaje más valioso no fue técnico sino de método. Un robot no perdona las "
              "suposiciones: cada afirmación sobre su comportamiento hubo que comprobarla en el equipo, y "
              "varias resultaron falsas hasta que se midieron. Aprendí a diagnosticar con datos, a no cambiar "
              "varias cosas a la vez, a documentar lo que se hace para que otra persona pueda continuarlo y a "
              "llevar un control de versiones riguroso. También aprendí a trabajar en equipo sobre un mismo "
              "sistema, repartiendo tareas y revisando el trabajo del otro."),
        ("p", "Para mi formación en Ingeniería Mecatrónica, el servicio integró en un solo proyecto la "
              "electrónica de los sensores, la mecánica de la plataforma omnidireccional, la programación de "
              "nodos y la inteligencia artificial aplicada a la visión. Me deja la satisfacción de entregar "
              "una herramienta útil para la institución y para los estudiantes que vendrán."),
        ("h2", "Descripción del programa"),
        ("p", "El programa *" + PROGRAMA + "* se desarrolló en el Departamento de Ingeniería Eléctrica y "
              "Electrónica (DIEE) del Instituto Tecnológico de Colima, bajo la supervisión de su jefe de "
              "departamento, " + RESPONSABLE + ". Su objetivo es convertir la plataforma robótica Yahboom "
              "ROSMASTER X3 en un sistema de navegación autónoma completamente operativo, capaz de construir "
              "mapas de su entorno, localizarse en ellos, planificar trayectorias y evitar obstáculos."),
        ("p", "El servicio que ofrece el programa es doble. Por un lado, una **plataforma experimental para "
              "la docencia**: el robot y su documentación permiten que los estudiantes de la especialidad en "
              "Sistemas Mecatrónicos Inteligentes realicen prácticas reales de la asignatura de Percepción e "
              "Inteligencia Artificial, en lugar de limitarse a la simulación. Por otro, un **prototipo de "
              "robot de patrullaje** que puede recorrer rutas automáticas o ser pilotado a distancia, como "
              "apoyo a la supervisión de las instalaciones y del equipo del departamento."),
        ("p", "Los beneficiarios directos son los estudiantes de Ingeniería Mecatrónica, en particular los "
              "de séptimo semestre en adelante que cursan la especialidad, de entre 20 y 24 años de edad, y "
              "los docentes que imparten las asignaturas relacionadas. El personal del departamento es "
              "beneficiario indirecto, por el apoyo a la supervisión."),
        ("h2", "Antecedentes"),
        ("p", "El departamento contaba con la plataforma ROSMASTER X3, pero no con un sistema de "
              "navegación autónoma operativo y documentado. Sin él, los estudiantes no podían desarrollar "
              "competencias prácticas en estimación de pose, construcción de mapas, planificación de "
              "trayectorias y evasión de obstáculos. El robot dependía, además, del conocimiento de quien lo "
              "había configurado: no existían manuales de instalación ni de operación, ni un procedimiento "
              "para recuperarlo en caso de falla. El programa se planteó para resolver esas tres carencias: "
              "funcionamiento, documentación y reproducibilidad."),
    ]


OBJ_ESPECIFICOS = [
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
]


def desarrollo(p):
    return [
        ("h2", "Objetivo general"),
        ("p", "Desarrollar e implementar un sistema de navegación autónoma para la plataforma móvil "
              "ROSMASTER X3 mediante la integración de sensores LiDAR y cámara RGB-D utilizando el "
              "middleware ROS, con la finalidad de generar un prototipo funcional para prácticas académicas "
              "en la asignatura de Percepción e Inteligencia Artificial."),
        ("h2", "Objetivos específicos"),
        ("numerada", OBJ_ESPECIFICOS),
        ("h2", "Actividades realizadas, en orden cronológico"),
        ("p", "El trabajo se organizó en seis etapas: análisis y configuración, integración sensorial, "
              "percepción y mapeo, localización y navegación, validación experimental y documentación. "
              "La tabla resume las actividades de cada mes; a continuación se describen con detalle."),
        ("tabla", ["Mes", "Actividades principales"], [
            ["Marzo", "Revisión del estado actual del robot. Instalación del sistema operativo."],
            ["Abril", "Instalación de ROS. Integración de la cámara RGB."],
            ["Mayo", "Consolidación de ROS y de la cámara; preparación de la integración del LiDAR."],
            ["Junio", "Integración del LiDAR. Calibración de sensores."],
            ["Julio", "Integración de nodos ROS y SLAM, con su configuración. Generación de mapas."],
            ["Agosto", "Localización, navegación autónoma y evasión de obstáculos; pruebas."],
            ["Septiembre", "Manual técnico, guía de prácticas y reporte final."],
        ], [3.2, 12.8]),
        ("h3", "Marzo: revisión del estado actual e instalación del sistema operativo"),
        ("p", "Se revisó el estado en que se encontraba la plataforma: chasis, ruedas omnidireccionales "
              "(mecanum), tarjeta controladora de motores, batería, sensores y la computadora a bordo "
              "Raspberry Pi 4. Se identificaron los componentes, sus conexiones y lo que funcionaba y lo que "
              "no. Con ese diagnóstico se instaló el sistema operativo **Ubuntu 18.04 LTS de 64 bits** para "
              "Raspberry Pi, la base que exige ROS Melodic, y se configuraron el usuario, el nombre de equipo, "
              "la red y el acceso remoto por SSH."),
        ("h3", "Abril: instalación de ROS e integración de la cámara RGB"),
        ("p", "Se instaló **ROS Melodic**, el middleware que organiza el robot como un conjunto de procesos "
              "independientes (nodos) que se comunican por tópicos, junto con los espacios de trabajo del "
              "fabricante. Se integró la cámara: su canal de color se publica como vídeo en directo, que más "
              "adelante alimentaría la interfaz de operación y la detección de objetos con inteligencia "
              "artificial."),
        ("h3", "Mayo: consolidación de ROS y de la cámara"),
        ("p", "Se estabilizó el entorno ROS y se comprobó el funcionamiento continuo de la cámara y de los "
              "nodos base. Se preparó la integración del sensor láser: reglas del sistema para que cada "
              "dispositivo USB conserve siempre el mismo nombre, y revisión de los controladores."),
        ("h3", "Junio: integración del LiDAR y calibración de sensores"),
        ("p", "Se integró el **LiDAR RPLIDAR A1**, que barre 360° a unos 10 Hz y es el sensor principal para "
              "mapear y evitar obstáculos. Se calibraron los sensores de movimiento: la unidad inercial (IMU), "
              "cuya calibración del giróscopo debe hacerse con el robot inmóvil, y la odometría de las ruedas. "
              "Ambas se fusionan con un filtro de Kalman extendido para estimar el movimiento del robot."),
        ("h3", "Julio: integración de nodos, SLAM y generación de mapas"),
        ("p", "Se integraron los nodos de control y se implementó el mapeo simultáneo a la localización "
              "(**SLAM**) con el algoritmo **Gmapping**, configurado según las necesidades del proyecto. Se "
              "desarrolló la gestión de sesiones de mapeo con retorno seguro: si algo falla, el sistema "
              "vuelve solo al estado anterior. Se generaron los primeros mapas de prueba."),
        ("h3", "Agosto: localización, navegación y evasión de obstáculos"),
        ("p", "Se configuraron la localización sobre un mapa conocido (**AMCL**), la planificación de "
              "trayectorias (**move_base** con planificador local **DWA**) y la evasión de obstáculos con "
              "costmaps. Se añadió una cola de navegación que valida cada punto antes de mover el robot, y un "
              "selector de mando con *watchdog* que detiene el robot en medio segundo si deja de recibir "
              "órdenes. Se probaron la teleoperación, la navegación por puntos y las misiones programadas."),
        ("h3", "Septiembre: manual técnico y reporte final"),
        ("p", "Se elaboró la documentación del proyecto: manual técnico de operación, guías de instalación "
              "del robot y de la computadora, guía de solución de problemas, protocolo de validación de 84 "
              "pruebas, guía de seis prácticas de laboratorio (P01 a P06) y el reporte final. Todo quedó "
              "versionado en un repositorio Git, de modo que el sistema pueda reinstalarse y continuarse."),
        ("p", "El sistema resultante se organiza en dos partes: la computadora de control, donde corre la "
              "interfaz web y la inteligencia artificial, y el robot, donde viven los lazos de control críticos, "
              "de modo que el robot sigue siendo seguro aunque se pierda la conexión."),
        ("fig", os.path.join(IMG, "diagrama-1.png"), "Figura 1. Arquitectura del sistema: computadora de control y robot.", 8),
        ("h2", "Recursos utilizados"),
        ("p", "El único material empleado fue la plataforma **Yahboom ROSMASTER X3**, con los componentes "
              "que integra de fábrica. El software es libre y se ejecuta sobre Linux."),
        ("tabla", ["Recurso", "Descripción"], [
            ["Plataforma", "Yahboom ROSMASTER X3, chasis con cuatro ruedas mecanum (omnidireccional)"],
            ["Computadora a bordo", "Raspberry Pi 4 con tarjeta microSD de 64 GB"],
            ["Sensor láser", "LiDAR RPLIDAR A1, 360°, ~10 Hz"],
            ["Cámara", "Orbbec Astra Pro (canal RGB en uso; profundidad disponible)"],
            ["Sensores de movimiento", "IMU y encoders de las ruedas"],
            ["Control manual", "Mando inalámbrico incluido con la plataforma"],
            ["Sistema operativo", "Linux: Ubuntu 18.04 LTS en el robot; Ubuntu en la computadora de control"],
            ["Middleware y algoritmos", "ROS Melodic: Gmapping (SLAM), AMCL (localización), move_base y DWA "
                                        "(navegación), robot_localization (EKF)"],
            ["Lenguajes", "Python 3.7 y 2.7 en el robot; Python 3 en la computadora; HTML y JavaScript"],
            ["Interfaz e IA", "Servidor web Flask; detección de objetos con YOLOv8 (Ultralytics)"],
            ["Control de versiones", "Git y GitHub"],
        ], [4.5, 11.5]),
    ]


def resultados(p):
    def fig(nombre, carpeta=EVID):
        return os.path.join(carpeta, nombre)
    return [
        ("p", "El robot cumple su propósito: **construye el mapa de un lugar, se localiza en él, navega de "
              "forma autónoma hasta los puntos indicados y esquiva los obstáculos**, y puede además pilotarse "
              "a distancia desde una computadora. El resultado se validó en un entorno real el 3 de octubre "
              "de 2026."),
        ("h2", "Cumplimiento de los objetivos específicos"),
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
        ], [1.0, 6.5, 8.5]),
        ("h2", "Validación en un entorno real"),
        ("p", "La prueba se hizo en una vivienda, que funcionó como entorno estructurado. Se ejecutaron 15 "
              "pruebas del protocolo de validación y todas se superaron:"),
        ("tabla", ["Aspecto", "Resultado medido"], [
            ["Mapa construido", "Unos 173 m² de espacio libre registrado, 25 × 19 m, paredes rectas y sin duplicar"],
            ["Precisión de la navegación", "Llegada al punto destino con 0,08 m de error, igual a la tolerancia configurada"],
            ["Evasión de obstáculos", "El robot rodeó un obstáculo colocado en su trayectoria y llegó al destino"],
            ["Seguridad", "El robot se detiene al soltar el mando; la velocidad máxima es ajustable"],
            ["Ciclo de mapeo", "Inicio, guardado y descarte con restauración automática del estado previo"],
        ], [5.0, 11.0]),
        ("p", "La misma sesión permitió detectar y corregir cinco fallos que solo aparecen al operar el "
              "robot en condiciones reales, entre ellos un tiempo de espera insuficiente al iniciar el mapeo, "
              "la calibración del giróscopo con el robot en movimiento y el avance a tirones del mando. "
              "Corregirlos dejó el sistema más robusto."),
        ("fig", fig("05-robot-entre-obstaculos.jpg"), "Figura 2. El robot navegando de forma autónoma entre dos obstáculos.", 13),
        ("fig", fig("01-mapa-casa-luis.png"), "Figura 3. Mapa construido por el robot con SLAM (Gmapping).", 13),
        ("fig", fig("02-mapear-robot-visible.png"), "Figura 4. Interfaz de mapeo: cámara del robot y mapa en construcción.", 15),
        ("fig", fig("03-pilotada-pose-calibrada.png", IMG), "Figura 5. Operación pilotada: cámara, mando y robot localizado en el mapa.", 15),
        ("fig", fig("04-cola-tres-puntos.jpg"), "Figura 6. Ruta automática de tres puntos en ejecución.", 13),
        ("fig", fig("06-obstaculo-y-dashboard.jpg"), "Figura 7. El robot junto al obstáculo y la interfaz de control.", 13),
        ("h2", "Productos entregados"),
        ("lista", [
            "**Plataforma ROSMASTER X3 con navegación autónoma**, operable desde una interfaz web: "
            "pilotaje manual, rutas automáticas, mapeo, cambio de red Wi-Fi y gestión de sus componentes.",
            "**Mapa funcional del entorno**, versionado junto con el sistema.",
            "**Sistema de evasión de obstáculos** basado en LiDAR y costmaps.",
            "**Manual técnico de operación**, guías de instalación, red y solución de problemas.",
            "**Guía de prácticas de laboratorio** con seis prácticas, de la teleoperación a la detección "
            "de objetos con YOLO.",
            "**Reporte técnico final** y **protocolo de validación**, con evidencias.",
            "Repositorio público con todo lo anterior:",
            "https://github.com/ToscanoID007/safevision",
        ]),
    ]


def conclusiones(p):
    return [
        ("p", "El programa dejó al Departamento de Ingeniería Eléctrica y Electrónica un **agente de apoyo "
              "a la seguridad**: un robot de patrullaje capaz de recorrer rutas automáticas sobre un mapa del "
              "lugar y de ser pilotado a distancia cuando se necesita una revisión puntual. Su cámara transmite "
              "lo que ve y puede reconocer objetos con inteligencia artificial, de modo que complementa la "
              "supervisión manual del equipo e instalaciones sin sustituirla. Al estar pensado para operar de "
              "forma continua y desde la red local, amplía la capacidad de vigilancia del personal con un "
              "costo de operación prácticamente nulo."),
        ("p", "El segundo impacto es **académico**. La asignatura de Percepción e Inteligencia Artificial "
              "cuenta ahora con una plataforma real, documentada y con seis prácticas listas para el "
              "laboratorio. Los estudiantes podrán construir mapas, localizar el robot, planificar rutas y "
              "observar las limitaciones reales de los sensores, algo que la simulación no enseña. Las "
              "limitaciones del sistema, como que el LiDAR solo ve un plano horizontal, son medibles y por "
              "tanto enseñables."),
        ("p", "El tercer impacto es la **continuidad**. Antes, operar el robot dependía del conocimiento de "
              "quien lo había configurado. Ahora existen manuales de instalación, de operación y de diagnóstico, "
              "un protocolo de validación y un repositorio con todo el código y su historia. Otros estudiantes "
              "o docentes pueden reinstalarlo, operarlo y mejorarlo sin empezar de cero."),
        ("p", "Para la comunidad tecnológica, el proyecto muestra que con una sola plataforma comercial y "
              "software libre se puede llegar a un sistema autónomo funcional cuando el trabajo se hace con "
              "método: verificar cada afirmación en el equipo real, cambiar una cosa a la vez y documentar. "
              "En lo personal, el servicio fortaleció mis competencias de integración de hardware y software, "
              "diagnóstico de fallas y trabajo en equipo, y cumplió con los objetivos y productos comprometidos "
              "en la propuesta, con la integración de la cámara de profundidad como trabajo futuro."),
        ("p", "Por último, el programa demuestra que el servicio social puede generar valor duradero para la "
              "institución cuando se plantea como un proyecto con objetivos claros y productos verificables. "
              "El robot, sus manuales y sus prácticas quedan a disposición del departamento, y la experiencia "
              "adquirida queda registrada para que futuros prestadores partan de un sistema que funciona y no "
              "de cero."),
    ]


def recomendaciones(p):
    return [
        ("p", "A partir de la experiencia de este programa se proponen las siguientes recomendaciones, "
              "dirigidas a la institución y a quienes den continuidad al proyecto."),
        ("h2", "Para la institución"),
        ("lista", [
            "**Asignar presupuesto al desarrollo del proyecto.** El programa se realizó solo con la plataforma "
            "existente. Un presupuesto modesto permitiría adquirir una batería de repuesto, tarjetas de memoria "
            "de respaldo, un segundo sensor y un área de pruebas delimitada, y extender el uso del robot a más "
            "grupos de forma simultánea.",
            "**Recibir los documentos del servicio social en formato digital.** La entrega y aceptación de "
            "cartas, reportes e informes en papel consume tiempo y recursos. Un trámite digital, con firma "
            "electrónica y seguimiento en línea, agilizaría el proceso para prestadores y responsables.",
            "**Dar continuidad al programa con nuevos prestadores**, para que el robot siga mejorándose y no "
            "quede en desuso al concluir este periodo.",
        ]),
        ("h2", "Para la continuidad técnica del proyecto"),
        ("lista", [
            "**Crear y resguardar una imagen de respaldo de la tarjeta microSD del robot.** Hoy es su único "
            "punto de falla: si la tarjeta se daña, reinstalar desde cero llevaría días.",
            "**Integrar la cámara de profundidad en la evasión de obstáculos.** El hardware y el software ya "
            "están instalados; falta conectarlos como segunda fuente del mapa de costos, para detectar mesas, "
            "escalones y objetos que el LiDAR no ve.",
            "**Completar el protocolo de validación** de 84 pruebas y construir el mapa del propio laboratorio, "
            "donde se impartirán las prácticas.",
            "**Mantener una sola persona responsable del equipo** durante cada sesión y respetar el protocolo de "
            "seguridad: el robot se mueve solo y debe operarse en un área despejada y con el mando a mano.",
            "**Cuidar la batería**: cargarla después de cada uso y apagar el robot de forma ordenada, para no "
            "dañar la tarjeta de memoria.",
        ]),
        ("p", "Atender estas recomendaciones permitirá que el robot se consolide como herramienta permanente "
              "de docencia y de apoyo a la supervisión del departamento."),
    ]


APARTADOS = [
    ("Introducción", introduccion),
    ("Desarrollo de actividades", desarrollo),
    ("Resultados", resultados),
    ("Conclusiones", conclusiones),
    ("Recomendaciones", recomendaciones),
]


# ---------------------------------------------------------------- utilidades docx
def poner_fuente(run, tam=None, negrita=None, cursiva=None, color=None):
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    if tam: run.font.size = Pt(tam)
    if negrita is not None: run.bold = negrita
    if cursiva is not None: run.italic = cursiva
    if color is not None: run.font.color.rgb = color


def texto_con_formato(par, texto, tam=12, color=None):
    """Admite **negrita** y *cursiva*."""
    import re
    for trozo in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", texto):
        if not trozo:
            continue
        if trozo.startswith("**"):
            poner_fuente(par.add_run(trozo[2:-2]), tam, negrita=True, color=color)
        elif trozo.startswith("*"):
            poner_fuente(par.add_run(trozo[1:-1]), tam, cursiva=True, color=color)
        else:
            poner_fuente(par.add_run(trozo), tam, color=color)


def formato_parrafo(par, justificado=True, interlineado=1.5, antes=0, despues=8):
    f = par.paragraph_format
    f.line_spacing = interlineado
    f.space_before = Pt(antes)
    f.space_after = Pt(despues)
    if justificado:
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def salto_pagina(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def sombrear(celda, color):
    tcPr = celda._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def numeracion(doc, par, num_id, nivel=0):
    pPr = par._element.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), str(nivel))
    nid = OxmlElement("w:numId"); nid.set(qn("w:val"), str(num_id))
    numPr.append(ilvl); numPr.append(nid); pPr.append(numPr)


def crear_numeraciones(doc):
    """Crea una definicion de vinetas y otra decimal; devuelve funciones para nuevas instancias."""
    numbering = doc.part.numbering_part.numbering_definitions._numbering
    def abstracto(aid, formato, texto):
        a = OxmlElement("w:abstractNum"); a.set(qn("w:abstractNumId"), str(aid))
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
        for tag, val in (("w:start", "1"), ("w:numFmt", formato), ("w:lvlText", texto), ("w:lvlJc", "left")):
            e = OxmlElement(tag); e.set(qn("w:val"), val); lvl.append(e)
        pPr = OxmlElement("w:pPr"); ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), "567"); ind.set(qn("w:hanging"), "340"); pPr.append(ind); lvl.append(pPr)
        a.append(lvl)
        numbering.insert(0, a)
    abstracto(90, "bullet", "•"); abstracto(91, "decimal", "%1.")
    contador = [100]
    def nueva(aid):
        contador[0] += 1
        n = OxmlElement("w:num"); n.set(qn("w:numId"), str(contador[0]))
        a = OxmlElement("w:abstractNumId"); a.set(qn("w:val"), str(aid)); n.append(a)
        numbering.append(n)
        return contador[0]
    return lambda: nueva(90), lambda: nueva(91)


def campo_pagina(par):
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        run = par.add_run(); poner_fuente(run, 9, color=GRIS)
        if tipo:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tipo); run._element.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = texto
            run._element.append(it)


def anadir_figura(doc, ruta, pie, ancho_cm):
    w, h = Image.open(ruta).size
    alto = ancho_cm * h / w
    if alto > 11:
        ancho_cm = 11 * w / h
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    par.paragraph_format.space_before = Pt(6)
    par.add_run().add_picture(ruta, width=Cm(ancho_cm))
    cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(12)
    poner_fuente(cap.add_run(pie), 10, cursiva=True, color=GRIS)


def anadir_tabla(doc, cabecera, filas, anchos):
    t = doc.add_table(rows=1, cols=len(cabecera))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, c in enumerate(cabecera):
        cel = t.rows[0].cells[i]; cel.text = ""
        par = cel.paragraphs[0]; texto_con_formato(par, "**" + c + "**", 10.5)
        sombrear(cel, "D9E2F3")
    for fila in filas:
        celdas = t.add_row().cells
        for i, c in enumerate(fila):
            celdas[i].text = ""; texto_con_formato(celdas[i].paragraphs[0], c, 10.5)
    t.autofit = False
    grid = t._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(anchos[i] * 567)))
    for fila in t.rows:
        for i, cel in enumerate(fila.cells):
            cel.width = Cm(anchos[i])
            for par in cel.paragraphs:
                par.paragraph_format.space_after = Pt(2); par.paragraph_format.line_spacing = 1.15
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ---------------------------------------------------------------- documento
def construir(prestador, paginas):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
    for lado in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, lado, Cm(2.5))
    sec.different_first_page_header_footer = True
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"; normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal.paragraph_format.line_spacing = 1.5
    for nombre, tam, color in (("Heading 1", 16, AZUL), ("Heading 2", 13, AZUL), ("Heading 3", 12, RGBColor(0x2F, 0x54, 0x96))):
        st = doc.styles[nombre]
        st.font.name = "Arial"; st.font.size = Pt(tam); st.font.bold = True; st.font.color.rgb = color
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial"); st.element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        st.element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        st.paragraph_format.space_before = Pt(12); st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.15; st.paragraph_format.keep_with_next = True
    vinetas, numeradas = crear_numeraciones(doc)

    pie = sec.footer.paragraphs[0]; pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    campo_pagina(pie)
    enc = sec.header.paragraphs[0]; enc.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    poner_fuente(enc.add_run("Instituto Tecnológico de Colima · Reporte final de servicio social"), 9, color=GRIS)

    # A. Caratula
    def centrado(texto, tam=12, negrita=False, color=None, antes=0, despues=4, cursiva=False):
        par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        formato_parrafo(par, justificado=False, interlineado=1.15, antes=antes, despues=despues)
        poner_fuente(par.add_run(texto), tam, negrita=negrita, color=color, cursiva=cursiva)
    centrado("Tecnológico Nacional de México", 16, True, AZUL, antes=30)
    centrado("Instituto Tecnológico de Colima", 15, True, AZUL, despues=60)
    centrado("REPORTE FINAL DE SERVICIO SOCIAL", 18, True, AZUL, despues=50)
    for etiqueta, valor in (("Nombre del alumno", prestador["nombre"]), ("No. de control", prestador["control"]),
                            ("Carrera", CARRERA), ("Programa", PROGRAMA),
                            ("Periodo del servicio social", PERIODO)):
        centrado(etiqueta, 10, True, GRIS, antes=10, despues=2)
        centrado(valor, 13, etiqueta == "Nombre del alumno")
    centrado(LUGAR_FECHA, 12, antes=70)
    salto_pagina(doc)

    # B. Indice
    doc.add_heading("Índice", level=1)
    entradas = [(t, 1) for t, _f in APARTADOS] + [("Hoja de firmas", 1)]
    for titulo, _nivel in entradas:
        par = doc.add_paragraph()
        formato_parrafo(par, justificado=False, interlineado=1.5, despues=4)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(16.59), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        poner_fuente(par.add_run(titulo), 12)
        if paginas.get(titulo):
            poner_fuente(par.add_run("\t" + str(paginas[titulo])), 12)

    # C-G. Apartados
    for titulo, funcion in APARTADOS:
        salto_pagina(doc)
        doc.add_heading(titulo, level=1)
        for bloque in funcion(prestador):
            tipo = bloque[0]
            if tipo == "p":
                par = doc.add_paragraph(); formato_parrafo(par); texto_con_formato(par, bloque[1])
            elif tipo in ("h2", "h3"):
                doc.add_heading(bloque[1], level=2 if tipo == "h2" else 3)
            elif tipo in ("lista", "numerada"):
                nid = vinetas() if tipo == "lista" else numeradas()
                for item in bloque[1]:
                    par = doc.add_paragraph(); formato_parrafo(par, justificado="http" not in item, despues=4)
                    numeracion(doc, par, nid); texto_con_formato(par, item)
            elif tipo == "tabla":
                anadir_tabla(doc, bloque[1], bloque[2], bloque[3])
            elif tipo == "fig":
                anadir_figura(doc, bloque[1], bloque[2], bloque[3])

    # H. Hoja de firmas
    salto_pagina(doc)
    centrado("Instituto Tecnológico de Colima", 14, True, AZUL, antes=10)
    doc.add_heading("Hoja de firmas", level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    def firma(rol, nombre, leyenda):
        centrado(rol, 12, True, antes=60, despues=40)
        centrado("_" * 52, 12, despues=2)
        centrado(nombre, 12, despues=0)
        centrado(leyenda, 10, color=GRIS)
    firma("Prestante de Servicio Social", prestador["nombre"], "Nombre y firma")
    firma("Responsable del programa", RESPONSABLE + ", " + CARGO_RESPONSABLE, "Nombre, firma")
    centrado("Sello de la dependencia", 12, True, antes=70)

    return doc


def main():
    paginas = json.load(open(sys.argv[1])) if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else {}
    for i, p in enumerate(PRESTADORES):
        p["companero"] = PRESTADORES[1 - i]["nombre"]
        doc = construir(p, paginas.get(p["archivo"], {}))
        ruta = os.path.join(SALIDA, p["archivo"] + ".docx")
        doc.save(ruta)
        print("Escrito", os.path.relpath(ruta, RAIZ))
    json.dump([t for t, _ in APARTADOS] + ["Hoja de firmas"],
              open(os.path.join(os.path.dirname(__file__), "titulos_informe.json"), "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
