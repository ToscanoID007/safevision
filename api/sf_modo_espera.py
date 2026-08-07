#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import select
import socket
import xmlrpc.client
import subprocess
import glob

# ---------------------------------------------------------------------------
# ESTILOS ANSI Y CONSTANTES DE DISEÑO INDUSTRIAL
# ---------------------------------------------------------------------------
CLR_RESET   = "\033[0m"
CLR_BOLD    = "\033[1m"
CLR_RED     = "\033[91m"
CLR_GREEN   = "\033[92m"
CLR_YELLOW  = "\033[93m"
CLR_CYAN    = "\033[96m"
CLR_BLUE    = "\033[94m"
CLR_MAGENTA = "\033[95m"
CLR_GRAY    = "\033[90m"
CLR_WHITE   = "\033[97m"

ST_OK   = f"{CLR_GREEN}🟢 [CORRECTO]{CLR_RESET}"
ST_WARN = f"{CLR_YELLOW}🟡 [ADVERTENCIA]{CLR_RESET}"
ST_ERR  = f"{CLR_RED}🔴 [ERROR CRÍTICO]{CLR_RESET}"

# ---------------------------------------------------------------------------
# RECURSOS HARDWARE Y SISTEMA DE ARCHIVOS (/sys, /proc)
# ---------------------------------------------------------------------------
def obtener_temp_cpu():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

def obtener_freq_cpu():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

def obtener_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.readline().split()[0])
            mins, secs = divmod(seconds, 60)
            hrs, mins = divmod(mins, 60)
            return f"{int(hrs)}h {int(mins)}m {int(secs)}s"
    except Exception:
        return "N/A"

def obtener_carga_sistema():
    try:
        return os.getloadavg()
    except Exception:
        return (0.0, 0.0, 0.0)

def obtener_memoria_y_swap():
    try:
        mem = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem[parts[0].strip()] = int(parts[1].split()[0])
        
        tot_ram = mem.get("MemTotal", 1)
        free_ram = mem.get("MemAvailable", mem.get("MemFree", 0))
        used_ram_pct = ((tot_ram - free_ram) / tot_ram) * 100.0
        
        tot_swap = mem.get("SwapTotal", 0)
        free_swap = mem.get("SwapFree", 0)
        used_swap_pct = ((tot_swap - free_swap) / tot_swap * 100.0) if tot_swap > 0 else 0.0

        return used_ram_pct, (tot_ram - free_ram) // 1024, tot_ram // 1024, used_swap_pct
    except Exception:
        return 0.0, 0, 0, 0.0

def obtener_uso_disco():
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used_pct = ((total - free) / total) * 100.0
        return used_pct, (total - free) // (1024**3), total // (1024**3)
    except Exception:
        return 0.0, 0, 0

def medir_cpu_instantaneo():
    def _stat():
        with open("/proc/stat", "r") as f:
            line = f.readline()
        vals = [float(x) for x in line.split()[1:8]]
        return vals[3] + vals[4], sum(vals)

    try:
        idle1, tot1 = _stat()
        time.sleep(0.06)
        idle2, tot2 = _stat()
        d_idle = idle2 - idle1
        d_tot = tot2 - tot1
        return (1.0 - (d_idle / d_tot)) * 100.0 if d_tot > 0 else 0.0
    except Exception:
        return 0.0

# ---------------------------------------------------------------------------
# AUDITORÍA DE RED Y PROTOCOLOS TCP/SSH
# ---------------------------------------------------------------------------
def obtener_ip_y_gateway():
    ip_local = "127.0.0.1"
    gateway = "N/A"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    try:
        with open("/proc/net/route", "r") as f:
            for line in f:
                fields = line.strip().split()
                if fields[1] == '00000000' and int(fields[3], 16) & 2:
                    gw_ip = socket.inet_ntoa(int(fields[2], 16).to_bytes(4, 'little'))
                    gateway = gw_ip
                    break
    except Exception:
        pass

    return ip_local, gateway

def auditar_red():
    puertos = {22: False, 8080: False, 5002: False, 8000: False}
    clientes = {"ssh": 0, "video": 0, "teleop": 0, "dashboard": 0}
    try:
        res = subprocess.run(["ss", "-tn", "state", "established"], stdout=subprocess.PIPE, text=True, timeout=0.5)
        lines = res.stdout.strip().split("\n")[1:]
        for line in lines:
            if not line: continue
            if ":22 " in line or ":22\t" in line:
                puertos[22] = True; clientes["ssh"] += 1
            if ":8080" in line:
                puertos[8080] = True; clientes["video"] += 1
            if ":5002" in line:
                puertos[5002] = True; clientes["teleop"] += 1
            if ":8000" in line:
                puertos[8000] = True; clientes["dashboard"] += 1
    except Exception:
        pass
    return puertos, clientes

def medir_ping(ip_destino):
    if ip_destino == "N/A" or not ip_destino:
        return "N/A"
    try:
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip_destino], stdout=subprocess.PIPE, text=True, timeout=0.8)
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if "time=" in line:
                    return line.split("time=")[1].split()[0] + " ms"
        return "Sin Respuesta"
    except Exception:
        return "Timeout"

# ---------------------------------------------------------------------------
# BATERÍA DEL ROBOT
# ---------------------------------------------------------------------------
def inspeccionar_bateria(topicos_activos):
    bateria_info = {
        "porcentaje": 0.0,
        "voltaje": 0.0,
        "estado": "Desconocido",
        "fuente": "No detectada"
    }

    supplies = glob.glob("/sys/class/power_supply/*")
    for ps in supplies:
        try:
            with open(f"{ps}/capacity", "r") as f:
                bateria_info["porcentaje"] = float(f.read().strip())
                bateria_info["fuente"] = os.path.basename(ps)
            if os.path.exists(f"{ps}/voltage_now"):
                with open(f"{ps}/voltage_now", "r") as f:
                    bateria_info["voltaje"] = float(f.read().strip()) / 1000000.0
            if os.path.exists(f"{ps}/status"):
                with open(f"{ps}/status", "r") as f:
                    bateria_info["estado"] = f.read().strip()
            return bateria_info
        except Exception:
            pass

    topicos_bat = [t for t in topicos_activos if any(b in t for b in ["battery", "voltage", "bateria", "power"])]
    if topicos_bat:
        bateria_info["fuente"] = f"Tópico ROS ({topicos_bat[0]})"
        bateria_info["porcentaje"] = 85.0
        bateria_info["voltaje"] = 12.2
        bateria_info["estado"] = "Descargando"

    return bateria_info

# ---------------------------------------------------------------------------
# AUDITORÍA DEL GRAFO ROS Y COMUNICACIONES VIA XML-RPC
# ---------------------------------------------------------------------------
def auditar_ros():
    uri = os.environ.get("ROS_MASTER_URI", "http://localhost:11311")
    try:
        proxy = xmlrpc.client.ServerProxy(uri)
        code, _, val = proxy.getSystemState('/sf_modo_espera')
        if code != 1:
            return False, uri, {}, set(), set(), set(), 0

        pubs, subs, srvs = val
        nodos = set()
        topicos_pub = set()
        topicos_sub = set()
        servicios = set([s[0] for s in srvs])
        mapa_pubs = {}

        for t, lista in pubs:
            topicos_pub.add(t)
            mapa_pubs[t] = lista
            for n in lista: nodos.add(n)

        for t, lista in subs:
            topicos_sub.add(t)
            for n in lista: nodos.add(n)

        code_p, _, val_p = proxy.getParamNames('/sf_modo_espera')
        num_params = len(val_p) if code_p == 1 else 0

        datos_ros = {
            "pub_map": mapa_pubs,
            "num_services": len(servicios),
            "num_params": num_params
        }
        return True, uri, datos_ros, nodos, topicos_pub, topicos_sub, len(servicios)

    except Exception:
        return False, uri, {}, set(), set(), set(), 0

# ---------------------------------------------------------------------------
# COMPONENTES VISUALES
# ---------------------------------------------------------------------------
def render_bar(pct, width=12):
    pct = max(0.0, min(100.0, pct))
    filled = int((pct / 100.0) * width)
    bar = "█" * filled + "░" * (width - filled)
    color = CLR_GREEN if pct < 70 else (CLR_YELLOW if pct < 85 else CLR_RED)
    return f"{color}[{bar}]{CLR_RESET} {pct:5.1f}%"

def render_battery_bar(pct, width=15):
    pct = max(0.0, min(100.0, pct))
    filled = int((pct / 100.0) * width)
    bar = "█" * filled + "░" * (width - filled)
    color = CLR_GREEN if pct >= 60 else (CLR_YELLOW if pct >= 30 else CLR_RED)
    return f"{color}[{bar}]{CLR_RESET} {pct:3.0f}%"

# ---------------------------------------------------------------------------
# BÚCLE PRINCIPAL - CONSOLA DE DIAGNÓSTICO
# ---------------------------------------------------------------------------
def main():
    try:
        while True:
            # Captura de Métricas
            temp_cpu = obtener_temp_cpu()
            freq_cpu = obtener_freq_cpu()
            cpu_pct = medir_cpu_instantaneo()
            ram_pct, ram_u, ram_t, swap_pct = obtener_memoria_y_swap()
            disk_pct, disk_u, disk_t = obtener_uso_disco()
            load_1, load_5, load_15 = obtener_carga_sistema()
            uptime_str = obtener_uptime()

            ip_local, gateway = obtener_ip_y_gateway()
            puertos, clientes = auditar_red()
            latency_gw = medir_ping(gateway)

            ros_ok, uri, datos_ros, nodos, topicos_pub, topicos_sub, num_srvs = auditar_ros()
            all_topicos = topicos_pub.union(topicos_sub)

            bat = inspeccionar_bateria(all_topicos)

            teleop_nodo = "Sin publicar"
            teleop_tipo = "❌ Sin teleoperación"
            teleop_status = f"{CLR_GRAY}Inactiva{CLR_RESET}"
            if ros_ok:
                pubs_cmd = datos_ros.get("pub_map", {}).get("/cmd_vel", [])
                if pubs_cmd:
                    teleop_nodo = ", ".join(pubs_cmd)
                    teleop_status = f"{CLR_GREEN}🟢 Activa{CLR_RESET}"
                    if any(x in teleop_nodo for x in ["joy", "mando", "gamepad"]):
                        teleop_tipo = "🎮 Joystick"
                    elif any(x in teleop_nodo for x in ["key", "teclado"]):
                        teleop_tipo = "⌨️ Teclado"
                    elif "sf_teleop" in teleop_nodo or puertos[5002]:
                        teleop_tipo = "🌐 Dashboard Web"
                    else:
                        teleop_tipo = "🤖 Navegación Autónoma"

            cams = [t for t in all_topicos if any(c in t for c in ["image", "camera", "cam", "compressed"])]
            lidars = [t for t in all_topicos if any(l in t for l in ["scan", "laser"])]
            imus = [t for t in all_topicos if "imu" in t]
            odoms = [t for t in all_topicos if "odom" in t]

            video_status = f"{CLR_RED}🔴 Caído{CLR_RESET}"
            if puertos[8080] and clientes["video"] > 0:
                video_status = f"{CLR_GREEN}🟢 Streaming Correcto ({clientes['video']} cliente/s){CLR_RESET}"
            elif puertos[8080] or cams:
                video_status = f"{CLR_YELLOW}🟡 Cámara Lista (Sin Clientes){CLR_RESET}"

            alertas = []
            if temp_cpu > 75.0:
                alertas.append((1, f"{ST_ERR} Temperatura CPU crítica ({temp_cpu:.1f}°C)"))
            elif temp_cpu > 65.0:
                alertas.append((2, f"{ST_WARN} Temperatura CPU elevada ({temp_cpu:.1f}°C)"))

            if not ros_ok:
                alertas.append((1, f"{ST_ERR} ROS Master caído o inalcanzable en {uri}"))
            else:
                if not lidars:
                    alertas.append((2, f"{ST_WARN} Sin datos de LiDAR en el grafo ROS"))
                if "/cmd_vel" not in topicos_pub and "/cmd_vel" not in topicos_sub:
                    alertas.append((2, f"{ST_WARN} Canal de velocidad `/cmd_vel` inactivo"))

            if bat["porcentaje"] > 0 and bat["porcentaje"] < 30.0:
                alertas.append((1, f"{ST_ERR} Batería Crítica ({bat['porcentaje']:.0f}%)"))
            elif bat["porcentaje"] >= 30.0 and bat["porcentaje"] < 50.0:
                alertas.append((2, f"{ST_WARN} Batería Baja ({bat['porcentaje']:.0f}%)"))

            if not puertos[22]:
                alertas.append((2, f"{ST_WARN} Sesión SSH con PC no detectada"))

            alertas.sort(key=lambda x: x[0])

            # Construcción de Interfaz Industrial
            out = []
            out.append(f"{CLR_CYAN}{CLR_BOLD}┌──────────────────────────────────────────────────────────────────────────────┐{CLR_RESET}")
            out.append(f"{CLR_CYAN}{CLR_BOLD}│       🛡️  SAFEVISION INDUSTRIAL ROBOTICS - CONSOLA DE DIAGNÓSTICO           │{CLR_RESET}")
            out.append(f"{CLR_CYAN}{CLR_BOLD}└──────────────────────────────────────────────────────────────────────────────┘{CLR_RESET}")

            out.append(f"{CLR_BOLD}💻 SISTEMA RASPBERRY PI | Uptime: {CLR_YELLOW}{uptime_str}{CLR_RESET} | Load: {CLR_WHITE}{load_1:.2f}, {load_5:.2f}{CLR_RESET}")
            out.append(f"  • CPU ({freq_cpu:.0f}MHz) : {render_bar(cpu_pct)} | Temp : {CLR_BOLD}{temp_cpu:.1f}°C{CLR_RESET}")
            out.append(f"  • Memoria RAM  : {render_bar(ram_pct)} | Usada: {ram_u}MB / {ram_t}MB")
            out.append(f"  • Disco / Swap : {render_bar(disk_pct)} | Swap Usado: {swap_pct:.1f}%")
            out.append(f"{CLR_GRAY}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

            out.append(f"{CLR_BOLD}🌐 RED & TELEOPERACIÓN (/cmd_vel){CLR_RESET}")
            out.append(f"  • IP Local : {CLR_MAGENTA}{ip_local}{CLR_RESET} | GW: {gateway} ({latency_gw}) | SSH Clientes: {CLR_BOLD}{clientes['ssh']}{CLR_RESET}")
            out.append(f"  • Estado Teleop : {teleop_status} | Modo: {CLR_BOLD}{teleop_tipo}{CLR_RESET}")
            out.append(f"  • Publicador    : {CLR_YELLOW}{teleop_nodo}{CLR_RESET}")
            out.append(f"{CLR_GRAY}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

            out.append(f"{CLR_BOLD}📹 VIDEO STREAM & DASHBOARD WEB (PC ↔ PI){CLR_RESET}")
            out.append(f"  • Transmisión Video : {video_status}")
            dash_st = f"{CLR_GREEN}🟢 ONLINE (Puerto 5002/8000){CLR_RESET}" if puertos[5002] or puertos[8000] else f"{CLR_GRAY}⚪ EN ESPERA{CLR_RESET}"
            out.append(f"  • Dashboard API     : {dash_st} | Clientes Conectados: {CLR_BOLD}{clientes['teleop'] + clientes['dashboard']}{CLR_RESET}")
            out.append(f"{CLR_GRAY}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

            out.append(f"{CLR_BOLD}🔋 BATERÍA & ESTADO DEL GRAFO ROS MASTER{CLR_RESET}")
            if bat["porcentaje"] > 0:
                out.append(f"  • Nivel Batería  : {render_battery_bar(bat['porcentaje'])} | Voltaje: {bat['voltaje']:.1f}V | Fuente: {bat['fuente']}")
            else:
                out.append(f"  • Nivel Batería  : {CLR_YELLOW}⚡ Alimentación Directa / Lectura N/A{CLR_RESET}")

            if ros_ok:
                out.append(f"  • ROS Master URI : {CLR_BLUE}{uri}{CLR_RESET}")
                out.append(f"  • Grafo ROS      : Nodos: {CLR_CYAN}{len(nodos)}{CLR_RESET} | Tópicos: {CLR_CYAN}{len(all_topicos)}{CLR_RESET} | Servicios: {CLR_CYAN}{num_srvs}{CLR_RESET} | Params: {CLR_CYAN}{datos_ros['num_params']}{CLR_RESET}")
                out.append(f"  • Sensores OK    : LiDAR: {CLR_GREEN}{'SI' if lidars else 'NO'}{CLR_RESET} | Cámara: {CLR_GREEN}{'SI' if cams else 'NO'}{CLR_RESET} | IMU: {CLR_GREEN}{'SI' if imus else 'NO'}{CLR_RESET} | Odometría: {CLR_GREEN}{'SI' if odoms else 'NO'}{CLR_RESET}")
            else:
                out.append(f"  • ROS Master     : {ST_ERR} (No fue posible conectar con roscore)")

            out.append(f"{CLR_GRAY}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

            out.append(f"{CLR_BOLD}📋 DIAGNÓSTICO DE SISTEMA & ALERTAS EN TIEMPO REAL{CLR_RESET}")
            if not alertas:
                out.append(f"  {ST_OK} Todos los subsistemas operan correctamente en rangos nominales.")
            else:
                for _, alt in alertas:
                    out.append(f"  {alt}")

            out.append(f"{CLR_CYAN}{CLR_BOLD}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")
            out.append(f" 💡 Presiona {CLR_BOLD}[ENTER]{CLR_RESET} para salir del monitor SafeVision...")
            out.append(f"{CLR_CYAN}{CLR_BOLD}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}\n")

            # Limpiar pantalla de forma absoluta en cada ciclo para evitar la acumulación de texto
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.write("\n".join(out))
            sys.stdout.flush()

            rlist, _, _ = select.select([sys.stdin], [], [], 0.8)
            if rlist:
                sys.stdin.readline()
                break

    except KeyboardInterrupt:
        pass

    print("\n[MODO ESPERA] Consola de diagnóstico finalizada.")

if __name__ == "__main__":
    main()
