# -*- coding: utf-8 -*-
"""
SafeVision - gestion del Wi-Fi del robot desde el dashboard.

Envuelve NetworkManager (nmcli) para:
  - saber en que red esta el robot (cliente o punto de acceso propio);
  - listar las redes al alcance, con su banda;
  - guardar una red nueva con su clave;
  - conectarse a una red guardada u olvidarla.

Reglas de diseno
  * Todas las redes que se guardan desde aqui quedan fijadas a 2.4 GHz
    (802-11-wireless.band bg). Es la banda de mas alcance para un robot que se
    mueve, y la misma en la que el robot levanta su red propia.
  * En modo punto de acceso NO se escanea: escanear tiraria a la laptop
    conectada. Se usa la lista que guardo el vigilante de red
    (sf_red_watchdog.sh) justo antes de levantar el punto de acceso.
  * Las claves nunca se devuelven ni se registran.
  * Cambiar de red se hace en segundo plano: la peticion HTTP responde antes de
    que la conexion se corte. Si la red nueva falla, se vuelve a levantar el
    punto de acceso, y el vigilante lo haria igualmente.

Sin dependencias de ROS: se puede probar con unittest en cualquier maquina.
"""

import json
import os
import subprocess
import threading
import time

IFAZ = "wlan0"
AP_NOMBRE = os.environ.get("SAFEVISION_AP_NOMBRE", "SafeVision-AP")
AP_SSID = "SafeVision-Robot"
AP_IP = "10.42.0.1"
PRIORIDAD = 10

# Escrito por sf_red_watchdog.sh antes de levantar el punto de acceso.
CACHE_ESCANEO = "/tmp/safevision_redes_wifi.txt"
# Mientras exista (y sea reciente) el vigilante no interviene.
CERROJO = "/tmp/safevision_red_ocupada"
CERROJO_TTL = 90

CAMPOS_ESCANEO = "SSID,SIGNAL,SECURITY,FREQ"


# ---------------------------------------------------------------
# Utilidades puras (probadas en tests/robot/test_red_wifi.py)
# ---------------------------------------------------------------
def dividir_terse(linea):
    """Divide una linea de 'nmcli -t -e yes' respetando '\\:' y '\\\\'."""
    campos, actual, escapado = [], [], False
    for c in linea:
        if escapado:
            actual.append(c)
            escapado = False
        elif c == "\\":
            escapado = True
        elif c == ":":
            campos.append("".join(actual))
            actual = []
        else:
            actual.append(c)
    campos.append("".join(actual))
    return campos


def banda_de(freq_texto):
    try:
        mhz = int(str(freq_texto).split()[0])
    except Exception:
        return None
    if 2400 <= mhz < 2500:
        return "2.4"
    if mhz >= 4900:
        return "5"
    return None


def parsear_escaneo(texto):
    """Lista de redes unica por SSID, con la mejor senal y las bandas vistas."""
    redes = {}
    for linea in (texto or "").splitlines():
        if not linea.strip():
            continue
        partes = dividir_terse(linea)
        if len(partes) < 4:
            continue
        ssid, senal, seguridad, freq = partes[0], partes[1], partes[2], partes[3]
        if not ssid or ssid == AP_SSID:
            continue
        try:
            senal = int(senal)
        except Exception:
            senal = 0
        banda = banda_de(freq)
        red = redes.setdefault(ssid, {
            "ssid": ssid, "senal": senal, "seguridad": seguridad or "",
            "bandas": [], "senal_24": None,
        })
        if banda and banda not in red["bandas"]:
            red["bandas"].append(banda)
        if banda == "2.4" and (red["senal_24"] is None or senal > red["senal_24"]):
            red["senal_24"] = senal
        if senal > red["senal"]:
            red["senal"] = senal
            red["seguridad"] = seguridad or red["seguridad"]
    salida = []
    for red in redes.values():
        red["bandas"].sort()
        red["compatible"] = "2.4" in red["bandas"]
        red["abierta"] = red["seguridad"] in ("", "--")
        red["empresarial"] = "802.1X" in red["seguridad"]
        salida.append(red)
    salida.sort(key=lambda r: (not r["compatible"] or r["empresarial"], -(r["senal_24"] or r["senal"])))
    return salida


def validar_ssid(ssid):
    ssid = "" if ssid is None else str(ssid)
    if not ssid.strip():
        return "Escribe el nombre de la red."
    if len(ssid.encode("utf-8")) > 32:
        return "El nombre de la red no puede pasar de 32 bytes."
    if any(ord(c) < 32 for c in ssid):
        return "El nombre de la red tiene caracteres no validos."
    if ssid in (AP_SSID, AP_NOMBRE):
        return "Esa es la red propia del robot; no se configura aqui."
    return None


def validar_clave(clave):
    clave = "" if clave is None else str(clave)
    if clave == "":
        return None  # red abierta
    if len(clave) == 64 and all(c in "0123456789abcdefABCDEF" for c in clave):
        return None
    if not 8 <= len(clave) <= 63:
        return "La clave Wi-Fi debe tener entre 8 y 63 caracteres."
    if any(ord(c) < 32 or ord(c) > 126 for c in clave):
        return "La clave tiene caracteres no validos (solo ASCII imprimible)."
    return None


def orden_agregar(ssid, clave, oculta=False):
    """Argumentos de nmcli para crear el perfil. Fijado a 2.4 GHz."""
    args = [
        "connection", "add", "type", "wifi", "ifname", IFAZ,
        "con-name", ssid, "ssid", ssid,
        "802-11-wireless.band", "bg",
        "connection.autoconnect", "yes",
        "connection.autoconnect-priority", str(PRIORIDAD),
    ]
    if oculta:
        args += ["802-11-wireless.hidden", "yes"]
    if clave:
        args += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", clave]
    return args


# ---------------------------------------------------------------
# Acceso a NetworkManager
# ---------------------------------------------------------------
def _nmcli(args, timeout=20):
    """Ejecuta nmcli con sudo -n. Devuelve (codigo, salida, error)."""
    try:
        proc = subprocess.run(
            ["sudo", "-n", "nmcli"] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "nmcli no respondio a tiempo"
    except Exception as exc:
        return 1, "", str(exc)


def _limpiar_error(texto):
    # nmcli a veces repite la orden en el error; nunca devolver la clave.
    return (texto or "").splitlines()[-1][:200] if texto else ""


def conexion_activa():
    codigo, salida, _ = _nmcli(["-t", "-e", "yes", "-f", "NAME,DEVICE", "connection", "show", "--active"], 10)
    if codigo != 0:
        return None
    for linea in salida.splitlines():
        partes = dividir_terse(linea)
        if len(partes) >= 2 and partes[1] == IFAZ:
            return partes[0]
    return None


def ip_wlan():
    codigo, salida, _ = _nmcli(["-g", "IP4.ADDRESS", "device", "show", IFAZ], 10)
    if codigo != 0 or not salida.strip():
        return None
    return salida.strip().splitlines()[0].split("/")[0].replace("\\", "")


def perfiles_guardados():
    codigo, salida, _ = _nmcli(["-t", "-e", "yes", "-f", "NAME,TYPE", "connection", "show"], 10)
    if codigo != 0:
        return []
    activa = conexion_activa()
    perfiles = []
    for linea in salida.splitlines():
        partes = dividir_terse(linea)
        if len(partes) < 2 or partes[1] != "802-11-wireless" or partes[0] == AP_NOMBRE:
            continue
        nombre = partes[0]
        _c, ssid, _e = _nmcli(["-g", "802-11-wireless.ssid,802-11-wireless.band,connection.autoconnect-priority",
                               "connection", "show", nombre], 10)
        valores = (ssid or "").splitlines()
        perfiles.append({
            "nombre": nombre,
            "ssid": valores[0] if len(valores) > 0 else nombre,
            "banda": (valores[1] if len(valores) > 1 else "") or "auto",
            "prioridad": valores[2] if len(valores) > 2 else "",
            "activa": nombre == activa,
        })
    perfiles.sort(key=lambda p: (not p["activa"], p["nombre"].lower()))
    return perfiles


def estado():
    activa = conexion_activa()
    if activa == AP_NOMBRE:
        modo = "ap"
    elif activa:
        modo = "cliente"
    else:
        modo = "sin_conexion"
    return {
        "ok": True,
        "modo": modo,
        "conexion": activa,
        "ssid": AP_SSID if modo == "ap" else activa,
        "ip": AP_IP if modo == "ap" else ip_wlan(),
        "ap": {"ssid": AP_SSID, "ip": AP_IP},
        "guardadas": perfiles_guardados(),
        "ocupado": _cerrojo_vigente(),
    }


def escanear():
    """Redes al alcance. En modo punto de acceso devuelve la lista guardada."""
    if conexion_activa() == AP_NOMBRE:
        texto, edad = "", None
        try:
            with open(CACHE_ESCANEO) as handle:
                texto = handle.read()
            edad = int(time.time() - os.path.getmtime(CACHE_ESCANEO))
        except Exception:
            pass
        redes = parsear_escaneo(texto)
        if redes:
            aviso = ("El robot esta en su red propia y no puede buscar redes sin "
                     "desconectarte. Esta es la lista que vio al arrancar.")
        else:
            aviso = ("El robot esta en su red propia y no puede buscar redes sin "
                     "desconectarte, y no tiene guardada la lista del arranque. "
                     "Escribe el nombre de la red abajo, o reinicia el robot para que la vea.")
        return {"ok": True, "en_vivo": False, "edad_s": edad if redes else None,
                "aviso": aviso, "redes": redes}
    # Sin --rescan: NetworkManager 1.10 (Ubuntu 18.04) no lo conoce.
    if _nmcli(["device", "wifi", "rescan"], 15)[0] == 0:
        time.sleep(4)
    codigo, salida, err = _nmcli(["-t", "-e", "yes", "-f", CAMPOS_ESCANEO,
                                  "device", "wifi", "list"], 30)
    if codigo != 0:
        return {"ok": False, "message": "No se pudo buscar redes: " + _limpiar_error(err), "redes": []}
    return {"ok": True, "en_vivo": True, "edad_s": 0, "aviso": None, "redes": parsear_escaneo(salida)}


def _cerrojo_vigente():
    try:
        return time.time() - os.path.getmtime(CERROJO) < CERROJO_TTL
    except Exception:
        return False


def _poner_cerrojo():
    try:
        with open(CERROJO, "w") as handle:
            handle.write(str(int(time.time())))
    except Exception:
        pass


def _quitar_cerrojo():
    try:
        os.remove(CERROJO)
    except Exception:
        pass


def _nombres_con_ssid(ssid):
    return [p["nombre"] for p in perfiles_guardados() if p["ssid"] == ssid or p["nombre"] == ssid]


def agregar(ssid, clave, oculta=False):
    """Guarda (o reemplaza) la red. No cambia la conexion actual."""
    error = validar_ssid(ssid) or validar_clave(clave)
    if error:
        return {"ok": False, "message": error}
    activa = conexion_activa()
    for nombre in _nombres_con_ssid(ssid):
        if nombre == activa:
            return {"ok": False, "message": ("'{}' es la red en uso. Conectate a otra antes de "
                                             "cambiar su clave.").format(ssid)}
        _nmcli(["connection", "delete", nombre], 20)
    codigo, _s, err = _nmcli(orden_agregar(ssid, clave, oculta), 30)
    if codigo != 0:
        detalle = _limpiar_error(err)
        if clave:
            detalle = detalle.replace(clave, "***")
        return {"ok": False, "message": "NetworkManager rechazo la red: " + detalle}
    return {"ok": True, "message": "Red '{}' guardada (2.4 GHz).".format(ssid), "nombre": ssid}


def olvidar(nombre):
    if nombre == AP_NOMBRE:
        return {"ok": False, "message": "La red propia del robot no se puede borrar."}
    if nombre not in [p["nombre"] for p in perfiles_guardados()]:
        return {"ok": False, "message": "No hay ninguna red guardada con ese nombre."}
    if nombre == conexion_activa():
        return {"ok": False, "message": "Es la red en uso. Conectate a otra antes de olvidarla."}
    codigo, _s, err = _nmcli(["connection", "delete", nombre], 20)
    if codigo != 0:
        return {"ok": False, "message": "No se pudo borrar: " + _limpiar_error(err)}
    return {"ok": True, "message": "Red '{}' olvidada.".format(nombre)}


def _cambiar_red(nombre):
    _poner_cerrojo()
    try:
        time.sleep(3)  # deja que la respuesta HTTP llegue antes del corte
        codigo, _s, _e = _nmcli(["-w", "40", "connection", "up", nombre], 60)
        if codigo != 0 and nombre != AP_NOMBRE:
            _nmcli(["-w", "30", "connection", "up", AP_NOMBRE], 45)
    finally:
        _quitar_cerrojo()


def conectar(nombre):
    """Cambia de red en segundo plano y responde de inmediato."""
    if _cerrojo_vigente():
        return {"ok": False, "message": "Ya hay un cambio de red en curso."}
    guardadas = [p["nombre"] for p in perfiles_guardados()]
    if nombre != AP_NOMBRE and nombre not in guardadas:
        return {"ok": False, "message": "No hay ninguna red guardada con ese nombre."}
    if nombre == conexion_activa():
        return {"ok": True, "message": "El robot ya esta en '{}'.".format(nombre), "cambio": False}
    hilo = threading.Thread(target=_cambiar_red, args=(nombre,), daemon=True)
    hilo.start()
    destino = AP_SSID if nombre == AP_NOMBRE else nombre
    return {
        "ok": True, "cambio": True, "destino": destino,
        "message": ("El robot se esta cambiando a '{}'. Tu laptop perdera la conexion: "
                    "conectala a '{}' y espera unos 30 segundos. Si la clave fuera "
                    "incorrecta, el robot vuelve a crear su red '{}'.").format(destino, destino, AP_SSID),
    }


def resumen_json():
    return json.dumps(estado(), ensure_ascii=False)
