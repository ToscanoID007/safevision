#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko

class ConexionSSH:
    def __init__(self):
        self.cliente = None
        self.ip = None
        self.usuario = "pi"
        self.password = "yahboom"
        self.puerto = 22

    def conectar(self, ip_robot):
        """Abre el canal SSH permanente contra la Pi."""
        self.ip = ip_robot
        try:
            print(f"[SSH] 🔌 Intentando conectar a {self.ip}...")
            self.cliente = paramiko.SSHClient()
            self.cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.cliente.connect(
                hostname=self.ip,
                port=self.puerto,
                username=self.usuario,
                password=self.password,
                timeout=5
            )
            print("[SSH] 🟢 Conexión SSH establecida con éxito.")
            return True
        except Exception as e:
            print(f"[SSH] ❌ Error de conexión: {e}")
            self.cliente = None
            return False

    def ejecutar_comando_asincrono(self, comando):
        """Envía comandos en segundo plano para no congelar Flask."""
        if not self.cliente:
            print("[SSH] ⚠️ No hay conexión activa.")
            return False
        try:
            cmd_bg = f"nohup {comando} > /dev/null 2>&1 &"
            self.cliente.exec_command(cmd_bg)
            print(f"[SSH] 🚀 Comando enviado a la Pi: {comando}")
            return True
        except Exception as e:
            print(f"[SSH] ❌ Error al ejecutar comando: {e}")
            return False

    def ejecutar_comando_sincrono(self, comando):
        """Ejecuta comandos inmediatos (útil para pkills de limpieza)."""
        if not self.cliente:
            return False
        try:
            self.cliente.exec_command(comando)
            return True
        except Exception as e:
            print(f"[SSH] ❌ Error ejecutando {comando}: {e}")
            return False

    def iniciar_teleop_teclado(self):
        """Mata Mando, valida/enciende Cámara y lanza Teclado."""
        self.ejecutar_comando_sincrono("pkill -f sf_teleop_mando.py")
        cmd = ("pgrep -f transmisor_camara_pi.py > /dev/null || python3 /home/pi/robot_custom/api/transmisor_camara_pi.py & "
               "pgrep -f sf_teleop_teclado.py > /dev/null || python3 /home/pi/robot_custom/api/sf_teleop_teclado.py")
        return self.ejecutar_comando_asincrono(cmd)

    def iniciar_teleop_mando(self):
        """Mata Teclado, valida/enciende Cámara y lanza Mando."""
        self.ejecutar_comando_sincrono("pkill -f sf_teleop_teclado.py")
        cmd = ("pgrep -f transmisor_camara_pi.py > /dev/null || python3 /home/pi/robot_custom/api/transmisor_camara_pi.py & "
               "pgrep -f sf_teleop_mando.py > /dev/null || python3 /home/pi/robot_custom/api/sf_teleop_mando.py")
        return self.ejecutar_comando_asincrono(cmd)

    def encender_camara(self):
        """Modo Solo Video: Mata Teclado y Mando, asegura la Cámara."""
        self.ejecutar_comando_sincrono("pkill -f sf_teleop_teclado.py; pkill -f sf_teleop_mando.py")
        cmd = "pgrep -f transmisor_camara_pi.py > /dev/null || python3 /home/pi/robot_custom/api/transmisor_camara_pi.py"
        return self.ejecutar_comando_asincrono(cmd)

    def apagar_todo(self):
        """Modo Reposo Total: Mata Teclado, Mando y Cámara."""
        cmd = "pkill -f sf_teleop_teclado.py; pkill -f sf_teleop_mando.py; pkill -f transmisor_camara_pi.py"
        return self.ejecutar_comando_sincrono(cmd)

# Instancia global para ser usada por Flask
conexion_robot = ConexionSSH()
